from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_overnight_statement_hardened_evidence_analysis.yaml"
SCHEMA_VERSION = "barcarolle.phase1_overnight_statement_hardened_evidence_analysis.v1"
OUTPUT_SCHEMA_VERSION = "barcarolle.phase1_overnight_statement_hardened_evidence_analysis_output.v1"
ADAPTERS = ["codex_workspace", "kilo_workspace"]
TERMINAL_PASS = "verified_pass"
TERMINAL_FAIL = "verified_fail"
SCOREABLE_STATUSES = {TERMINAL_PASS, TERMINAL_FAIL}
FORBIDDEN_ACTIVE_RAW_PATH_PREFIXES = [
    "experiments/phase0_headroom/results/raw/",
    "experiments/phase1_compiler/results/raw/",
    "experiments/phase0_headroom/solver_workspaces/",
    "experiments/phase0_headroom/verifier_workspaces/",
    "experiments/phase1_compiler/solver_workspaces/",
    "experiments/phase1_compiler/verifier_workspaces/",
]
OLD_POLICY_VIOLATION_TASK_IDS = {"attrs__hist__027"}

FAILURE_CATEGORY_OVERRIDES: dict[str, dict[str, Any]] = {
    "attrs__hist__003": {
        "categories": ["source_context_weakness", "statement_under_specification", "api_semantics_complexity"],
        "evidence": "Sparse PR context titled added first doc stub; both adapters failed a small generated-method introspection change.",
        "inference": "The statement is scoreable, but the public context leaves the exact generated method target underdetermined.",
    },
    "attrs__hist__012": {
        "categories": ["api_semantics_complexity", "edge_case_specification", "time_or_version_shift"],
        "evidence": "Both adapters failed slots=True plus custom __setattr__ semantics in attrs/H_future.",
        "inference": "This looks like future-window class-generation complexity rather than a harness or policy problem.",
    },
    "attrs__hist__013": {
        "categories": ["api_semantics_complexity", "edge_case_specification", "time_or_version_shift"],
        "evidence": "Both adapters failed next-generation frozen subclass/on_setattr behavior in attrs/H_future.",
        "inference": "The task combines frozen semantics, subclassing, and next-generation API defaults.",
    },
    "boltons__hist__011": {
        "categories": ["adapter_specific_behavior", "edge_case_specification", "api_semantics_complexity"],
        "evidence": "Only Kilo failed the iterable strip helper task; Codex passed.",
        "inference": "The disagreement suggests adapter-specific execution or solution behavior, not a release-wide scoring defect.",
    },
    "boltons__hist__022": {
        "categories": ["edge_case_specification", "api_semantics_complexity", "time_or_version_shift"],
        "evidence": "Both adapters failed chunk_ranges in boltons/H_future with overlap/windowing requirements.",
        "inference": "The hard part is bounded range generation with invalid-argument and overlap semantics.",
    },
    "boltons__hist__027": {
        "categories": ["api_semantics_complexity", "edge_case_specification", "time_or_version_shift"],
        "evidence": "Both adapters failed cacheutils mapping view behavior in boltons/H_future.",
        "inference": "The task requires preserving cache internals while presenting dict-like user values.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def config_path(raw: Any) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected overnight evidence analysis config schema_version")
    config["_path"] = str(path)
    return config


def source_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["source_artifacts"][key])


def score_table_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["score_tables"][key])


def batch_metrics_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["batch_metrics"][key])


def local_supply_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["local_supply"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["output_paths"][key])


def command_result(args: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return {
            "args": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except FileNotFoundError as exc:
        return {
            "args": args,
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "duration_seconds": round(time.monotonic() - started, 3),
        }


def command_text(args: list[str]) -> str:
    result = command_result(args)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def all_required_input_paths(config: dict[str, Any]) -> list[Path]:
    keys = [
        "paid_decision",
        "paid_metrics",
        "paid_process_report",
        "release_manifest",
        "preregistration",
        "inventory",
        "screen",
        "release_preview",
        "tooling_check",
        "workspace_cost_reconciliation",
        "workspace_usage_ledger",
    ]
    paths = [source_path(config, key) for key in keys]
    paths.extend(score_table_path(config, key) for key in config["score_tables"])
    paths.extend(batch_metrics_path(config, key) for key in config["batch_metrics"])
    return paths


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    lines = []
    headers = [label for _, label in columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                value = json.dumps(value, sort_keys=True)
            values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def bool_from_csv(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def parse_task_time(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def time_bucket(raw: str) -> str:
    parsed = parse_task_time(raw)
    half = "H1" if parsed.month <= 6 else "H2"
    return f"{parsed.year}{half}"


def source_kind(source_ref: str) -> str:
    if source_ref.startswith("issue:"):
        return "issue"
    if source_ref.startswith("pr:") or source_ref.startswith("pull_request:"):
        return "pull_request"
    return "commit-derived"


def module_label(path: str) -> str:
    label = path
    if label.endswith(".pyi"):
        label = label[:-4]
    elif label.endswith(".py"):
        label = label[:-3]
    if label.startswith("src/"):
        label = label[4:]
    return label.replace("/", ".")


def task_family_label(repo_id: str, editable_paths: list[str]) -> str:
    modules = sorted({module_label(path) for path in editable_paths})
    if not modules:
        return f"{repo_id}:unknown"
    if len(modules) == 1:
        return f"{repo_id}:{modules[0]}"
    package = modules[0].split(".", 1)[0]
    return f"{repo_id}:{package}:multi_file"


def statement_length_bucket(length: int) -> str:
    if length < 2100:
        return "short_lt_2100"
    if length <= 2300:
        return "medium_2100_2300"
    return "long_gt_2300"


def selected_task_ids(manifest: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for repo_split in ["attrs/B_eval", "attrs/H_future", "boltons/B_eval", "boltons/H_future"]:
        out.extend(str(task_id) for task_id in manifest["canonical_selected_task_ids_by_repo_split"].get(repo_split, []))
    return out


def load_inventory_by_task(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inventory = read_json(source_path(config, "inventory"))
    return {str(row["task_id"]): row for row in inventory.get("rows", [])}


def load_score_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in config["score_tables"]:
        path = score_table_path(config, key)
        result_prefix = path.name.removesuffix("_score_table.csv")
        for row in read_csv(path):
            parsed = dict(row)
            parsed["result_key"] = key
            parsed["result_prefix"] = result_prefix
            parsed["scoreable_cell"] = bool_from_csv(parsed.get("scoreable_cell"))
            parsed["agent_failure"] = bool_from_csv(parsed.get("agent_failure"))
            parsed["harness_error"] = bool_from_csv(parsed.get("harness_error"))
            parsed["verifier_exit_code"] = int(parsed["verifier_exit_code"])
            parsed["attempt"] = int(parsed["attempt"])
            parsed["repo_id"] = str(parsed["task_id"]).split("__", 1)[0]
            parsed["repo_split"] = f"{parsed['repo_id']}/{parsed['split']}"
            rows.append(parsed)
    return rows


def score_rows_by_task_adapter(config: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["task_id"], row["adapter_id"]): row for row in load_score_rows(config)}


def per_repo_split_counts(score_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in score_rows:
        grouped[row["repo_split"]].append(row)
    out: dict[str, dict[str, Any]] = {}
    for key, rows in sorted(grouped.items()):
        pass_count = sum(1 for row in rows if row["terminal_status"] == TERMINAL_PASS)
        fail_count = sum(1 for row in rows if row["terminal_status"] == TERMINAL_FAIL)
        out[key] = {
            "cell_count": len(rows),
            "scoreable_cell_count": sum(1 for row in rows if row["scoreable_cell"]),
            "verified_pass_count": pass_count,
            "verified_fail_count": fail_count,
            "pass_rate": round_float(pass_count / len(rows) if rows else None),
        }
    return out


def wilson_interval(pass_count: int, total: int, z: float = 1.96) -> dict[str, float | None]:
    if total == 0:
        return {"low": None, "high": None}
    phat = pass_count / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total) / denom
    return {"low": round_float(max(0.0, center - margin)), "high": round_float(min(1.0, center + margin))}


def normal_cdf(value: float, mean: float = 0.0, sd: float = 1.0) -> float:
    if sd <= 0:
        return 1.0 if value >= mean else 0.0
    return 0.5 * (1.0 + math.erf((value - mean) / (sd * math.sqrt(2.0))))


def two_prop_power(n_per_group: int, p_b: float = 0.80, p_h: float = 0.50, alpha_z: float = 1.96) -> float:
    diff = p_b - p_h
    pooled = (p_b + p_h) / 2.0
    critical = alpha_z * math.sqrt(2 * pooled * (1 - pooled) / n_per_group)
    sd_alt = math.sqrt(p_b * (1 - p_b) / n_per_group + p_h * (1 - p_h) / n_per_group)
    upper_tail = 1.0 - normal_cdf(critical, mean=diff, sd=sd_alt)
    lower_tail = normal_cdf(-critical, mean=diff, sd=sd_alt)
    return round_float(upper_tail + lower_tail)


def gap_half_width(n_per_group: int, p: float = 0.65, z: float = 1.96) -> float:
    return round_float(z * math.sqrt(2 * p * (1 - p) / n_per_group))


def sample_needed_for_gap_half_width(half_width: float, p: float = 0.65, z: float = 1.96) -> int:
    return math.ceil(2 * p * (1 - p) * (z / half_width) ** 2)


def load_preflight(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "preflight")
    if not path.exists():
        return {}
    return read_json(path)


def write_process_report(config: dict[str, Any], preflight: dict[str, Any]) -> None:
    decision_path = output_path(config, "next_action_decision")
    decision = read_json(decision_path) if decision_path.exists() else {}
    lines = [
        "# Overnight Statement-Hardened Evidence Process",
        "",
        f"Status: `{preflight.get('status', 'in_progress')}`.",
        "",
        "## Boundary",
        "",
        "- New paid ACUT calls made: `false`.",
        "- New paid LLM calls made: `false`.",
        "- Follow-up runbook written by worker: `false`.",
        "- Raw artifacts committed: `false`.",
        "- Generated statements are solver-visible task statements, not scoreable results.",
        "",
        "## Environment",
        "",
        f"- Branch: `{preflight.get('environment', {}).get('branch', '')}`.",
        f"- HEAD: `{preflight.get('environment', {}).get('head', '')}`.",
        f"- Runbook: `{preflight.get('runbook_path', '')}`.",
        f"- UV: `{preflight.get('environment', {}).get('uv_version', '')}`.",
        f"- Python: `{preflight.get('environment', {}).get('uv_project_python_version', preflight.get('environment', {}).get('python_version', ''))}`.",
        "",
        "## Work Queue",
        "",
    ]
    queue = preflight.get("work_queue", [])
    lines.extend(
        markdown_table(
            queue,
            [
                ("step", "Step"),
                ("status", "Status"),
                ("commit_target", "Commit target"),
                ("outputs", "Outputs"),
                ("blockers", "Blockers"),
            ],
        )
    )
    if preflight.get("verification_commands"):
        lines.extend(["", "## Verification", ""])
        lines.extend(
            markdown_table(
                preflight["verification_commands"],
                [
                    ("name", "Command"),
                    ("returncode", "Return code"),
                    ("status", "Status"),
                    ("duration_seconds", "Seconds"),
                ],
            )
        )
    if decision:
        lines.extend(
            [
                "",
                "## Closeout",
                "",
                f"- Integrity audit status: `{decision.get('integrity_audit_status')}`.",
                f"- Primary decision: `{decision.get('primary_decision')}`.",
                f"- Recommended next action: {decision.get('recommended_next_action')}.",
                f"- Predictive validity established: `{decision.get('predictive_validity_established')}`.",
            ]
        )
    write_text(output_path(config, "process_report"), "\n".join(lines))


def update_queue_step(
    config: dict[str, Any],
    *,
    step: str,
    status: str,
    outputs: list[str] | None = None,
    blockers: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    preflight = load_preflight(config)
    for item in preflight.get("work_queue", []):
        if item.get("step") == step:
            item["status"] = status
            if outputs is not None:
                item["outputs"] = outputs
            if blockers is not None:
                item["blockers"] = blockers
            item["updated_at"] = utc_now()
            break
    if extra:
        preflight.update(extra)
    write_json(output_path(config, "preflight"), preflight)
    write_process_report(config, preflight)


def build_preflight(config: dict[str, Any]) -> dict[str, Any]:
    decision = read_json(source_path(config, "paid_decision"))
    metrics = read_json(source_path(config, "paid_metrics"))
    manifest = read_json(source_path(config, "release_manifest"))
    required_paths = all_required_input_paths(config)
    missing = [rel(path) for path in required_paths if not path.exists()]
    input_digests = {rel(path): digest_file(path) for path in required_paths if path.exists()}
    python_result = command_result(["python", "--version"])
    uv_python_result = command_result(["uv", "run", "--project", "experiments/phase1_compiler", "python", "--version"])
    checks = {
        "paid_decision": decision.get("primary_decision") == "statement_hardened_paid_validation_complete_threshold_not_met",
        "planned_cells": metrics.get("planned_cells") == 32,
        "scoreable_cells": metrics.get("scoreable_cell_count") == 32,
        "policy_violation_count": metrics.get("policy_violation_count") == 0,
        "old_paid_result_repaired": decision.get("old_paid_result_repaired") is False,
        "followup_runbook_written_by_worker": decision.get("followup_runbook_written_by_worker") is False,
        "generated_statement_is_scoreable_result": decision.get("generated_statement_is_scoreable_result") is False,
        "release_paid_acut_calls_made": manifest.get("paid_acut_calls_made") is False,
        "release_paid_llm_calls_made": manifest.get("paid_llm_calls_made") is False,
        "required_inputs_exist": not missing,
    }
    queue_specs = [
        ("0", "Record overnight statement-hardened analysis preflight"),
        ("1", "Audit statement-hardened paid result integrity"),
        ("2", "Build statement-hardened task outcome matrix"),
        ("3", "Classify statement-hardened paid failures"),
        ("4", "Analyze statement-hardened result strata"),
        ("5", "Analyze predictive threshold and power"),
        ("6", "Rank compiler calibration options"),
        ("7", "Assess local supply for statement-hardened expansion"),
        ("8", "Write proposal alignment memo for paid evidence"),
        ("9", "Decide next action from statement-hardened evidence"),
        ("10", "Record overnight statement-hardened analysis closeout"),
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "preflight.v1",
        "generated_at": utc_now(),
        "status": "pass" if all(checks.values()) else "blocked",
        "release_id": config["release_id"],
        "runbook_path": str(config["runbook_path"]),
        "new_paid_acut_calls_allowed": False,
        "new_paid_llm_calls_allowed": False,
        "predictive_validity_established": False,
        "environment": {
            "branch": command_text(["git", "branch", "--show-current"]),
            "head": command_text(["git", "rev-parse", "HEAD"]),
            "date_utc": command_text(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]),
            "uv_version": command_text(["uv", "--version"]),
            "python_version": python_result["stdout"] or python_result["stderr"],
            "uv_project_python_version": uv_python_result["stdout"] or uv_python_result["stderr"],
            "git_status_short_branch": command_text(["git", "status", "--short", "--branch"]),
        },
        "checks": checks,
        "missing_required_inputs": missing,
        "input_artifact_digests": input_digests,
        "work_queue": [
            {
                "step": step,
                "status": "completed" if step == "0" else "pending",
                "commit_target": commit_target,
                "outputs": [],
                "blockers": [] if checks.get("required_inputs_exist", False) else ["missing_required_inputs"],
                "updated_at": utc_now(),
            }
            for step, commit_target in queue_specs
        ],
    }
    return payload


def run_preflight(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_preflight(config)
    write_json(output_path(config, "preflight"), payload)
    write_process_report(config, payload)
    return payload


def committed_raw_artifact_paths() -> list[str]:
    result = command_result(["git", "ls-files", "-z"])
    if result["returncode"] != 0:
        return []
    paths = [path for path in result["stdout"].split("\x00") if path]
    out = []
    for path in paths:
        if any(path.startswith(prefix) for prefix in FORBIDDEN_ACTIVE_RAW_PATH_PREFIXES):
            out.append(path)
    return sorted(out)


def build_integrity_audit(config: dict[str, Any]) -> dict[str, Any]:
    decision = read_json(source_path(config, "paid_decision"))
    paid_metrics = read_json(source_path(config, "paid_metrics"))
    manifest = read_json(source_path(config, "release_manifest"))
    rows = load_score_rows(config)
    terminal_counts = dict(sorted(Counter(row["terminal_status"] for row in rows).items()))
    scoreable_count = sum(1 for row in rows if row["scoreable_cell"])
    scoreable_status_count = sum(1 for row in rows if row["terminal_status"] in SCOREABLE_STATUSES)
    harness_error_count = sum(1 for row in rows if row.get("harness_error") or row["terminal_status"] in {"harness_error", "acut_harness_error"})
    timeout_count = sum(1 for row in rows if row["terminal_status"] == "timeout")
    invalid_output_count = sum(1 for row in rows if row["terminal_status"] == "invalid_output")
    policy_violation_count = sum(1 for row in rows if row["terminal_status"] == "policy_violation")
    expected_task_ids_set = set(selected_task_ids(manifest))
    observed_task_ids_set = {row["task_id"] for row in rows}
    prefixes = sorted({row["result_prefix"] for row in rows})
    usage_rows = [
        row
        for row in read_jsonl(source_path(config, "workspace_usage_ledger"))
        if str(row.get("result_prefix")) in set(prefixes)
    ]
    usage_observed_count = sum(1 for row in usage_rows if row.get("usage_observed") is True)
    cost_reconciliation = read_json(source_path(config, "workspace_cost_reconciliation"))
    summary_by_prefix = {
        summary.get("result_prefix"): summary for summary in cost_reconciliation.get("summaries", []) if summary.get("result_prefix") in prefixes
    }
    cost_from_reconciliation = sum(float(summary.get("observed_or_conservative_estimated_cost_usd", 0.0)) for summary in summary_by_prefix.values())
    batch_metric_totals = {
        key: read_json(batch_metrics_path(config, key)).get("terminal_status_counts", {}) for key in config["batch_metrics"]
    }

    mismatches: list[dict[str, Any]] = []

    def expect(label: str, actual: Any, expected: Any) -> None:
        if actual != expected:
            mismatches.append({"check": label, "actual": actual, "expected": expected})

    expect("total_cells", len(rows), 32)
    expect("scoreable_cells", scoreable_count, 32)
    expect("verified_pass_plus_verified_fail", scoreable_status_count, 32)
    expect("policy_violations", policy_violation_count, 0)
    expect("timeouts", timeout_count, 0)
    expect("harness_errors", harness_error_count, 0)
    expect("invalid_outputs", invalid_output_count, 0)
    expect("usage_observed_count", usage_observed_count, 32)
    expect("paid_metrics_total_cells", paid_metrics.get("total_cells"), len(rows))
    expect("paid_metrics_scoreable_cells", paid_metrics.get("scoreable_cell_count"), scoreable_count)
    expect("paid_metrics_terminal_counts", paid_metrics.get("terminal_status_counts"), terminal_counts)
    expect("old_score_tables_merged", paid_metrics.get("old_score_tables_merged"), False)
    expect("old_paid_result_repaired", decision.get("old_paid_result_repaired"), False)
    expect("followup_runbook_written_by_worker", decision.get("followup_runbook_written_by_worker"), False)
    if round_float(cost_from_reconciliation, 7) != round_float(paid_metrics.get("observed_or_conservative_cost_usd"), 7):
        mismatches.append(
            {
                "check": "observed_or_conservative_cost_usd",
                "actual": round_float(cost_from_reconciliation, 7),
                "expected": round_float(paid_metrics.get("observed_or_conservative_cost_usd"), 7),
            }
        )
    if observed_task_ids_set != expected_task_ids_set:
        mismatches.append(
            {
                "check": "score_table_task_ids_match_manifest",
                "actual": sorted(observed_task_ids_set),
                "expected": sorted(expected_task_ids_set),
            }
        )
    if any(not prefix.startswith("phase1_statement_hardened_after_canonical_repair_") for prefix in prefixes):
        mismatches.append({"check": "score_table_prefixes_are_statement_hardened", "actual": prefixes, "expected": "all statement_hardened prefixes"})
    raw_paths = committed_raw_artifact_paths()
    if raw_paths:
        mismatches.append({"check": "raw_artifacts_not_committed", "actual": raw_paths, "expected": []})

    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "integrity_audit.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass" if not mismatches else "mismatch",
        "mismatches": mismatches,
        "score_table_prefixes": prefixes,
        "score_table_task_ids": sorted(observed_task_ids_set),
        "terminal_status_counts": terminal_counts,
        "total_cells": len(rows),
        "scoreable_cell_count": scoreable_count,
        "usage_observed_count": usage_observed_count,
        "observed_or_conservative_cost_usd": round_float(cost_from_reconciliation, 7),
        "paid_metrics_cost_usd": paid_metrics.get("observed_or_conservative_cost_usd"),
        "batch_metric_terminal_counts": batch_metric_totals,
        "raw_artifact_paths_committed": raw_paths,
        "old_score_tables_merged": False,
        "old_paid_result_repaired": False,
        "followup_runbook_written_by_worker": False,
        "new_paid_calls_made": False,
        "input_artifact_digests": {
            rel(path): digest_file(path) for path in all_required_input_paths(config) if path.exists()
        },
    }
    return payload


def write_integrity_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Integrity Audit",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Total cells: `{payload['total_cells']}`.",
        f"- Scoreable cells: `{payload['scoreable_cell_count']}`.",
        f"- Terminal statuses: `{payload['terminal_status_counts']}`.",
        f"- Usage observed count: `{payload['usage_observed_count']}`.",
        f"- Observed-or-conservative cost USD: `{payload['observed_or_conservative_cost_usd']}`.",
        f"- Old score tables merged: `{payload['old_score_tables_merged']}`.",
        f"- Raw artifact paths committed: `{len(payload['raw_artifact_paths_committed'])}`.",
        "",
        "## Mismatches",
        "",
    ]
    if payload["mismatches"]:
        lines.extend(markdown_table(payload["mismatches"], [("check", "Check"), ("actual", "Actual"), ("expected", "Expected")]))
    else:
        lines.append("No mismatches found.")
    lines.extend(["", "## Prefixes", ""])
    for prefix in payload["score_table_prefixes"]:
        lines.append(f"- `{prefix}`")
    write_text(output_path(config, "integrity_audit_report"), "\n".join(lines))


def run_integrity(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_integrity_audit(config)
    write_json(output_path(config, "integrity_audit"), payload)
    write_integrity_report(config, payload)
    update_queue_step(
        config,
        step="1",
        status="completed" if payload["status"] == "pass" else "completed_with_mismatches",
        outputs=[rel(output_path(config, "integrity_audit")), rel(output_path(config, "integrity_audit_report"))],
        blockers=[] if payload["status"] == "pass" else ["integrity_mismatch"],
    )
    return payload


def build_task_outcome_matrix(config: dict[str, Any]) -> dict[str, Any]:
    manifest = read_json(source_path(config, "release_manifest"))
    inventory = load_inventory_by_task(config)
    score_by = score_rows_by_task_adapter(config)
    repo_split_summary = per_repo_split_counts(load_score_rows(config))
    rows: list[dict[str, Any]] = []
    for task_id in selected_task_ids(manifest):
        inv = inventory[task_id]
        repo_id = str(inv["repo_id"])
        canonical_split = str(inv["canonical_split"])
        repo_split = str(inv["canonical_repo_split"])
        statuses = {adapter: score_by[(task_id, adapter)]["terminal_status"] for adapter in ADAPTERS}
        adapter_pass_count = sum(1 for status in statuses.values() if status == TERMINAL_PASS)
        editable_paths = [str(path) for path in inv.get("editable_implementation_paths", [])]
        test_paths = [str(path) for path in inv.get("non_editable_test_paths", [])]
        statement_text = str(inv.get("full_visible_statement") or inv.get("visible_statement") or "")
        source_ref = str(inv.get("source_ref") or (inv.get("allowed_public_context_refs") or [""])[0])
        row = {
            "task_id": task_id,
            "repo_id": repo_id,
            "canonical_split": canonical_split,
            "repo_split": repo_split,
            "codex_terminal_status": statuses["codex_workspace"],
            "kilo_terminal_status": statuses["kilo_workspace"],
            "both_pass": adapter_pass_count == 2,
            "both_fail": all(status == TERMINAL_FAIL for status in statuses.values()),
            "adapter_disagreement": len(set(statuses.values())) > 1,
            "statement_source": inv.get("statement_source"),
            "source_kind": source_kind(source_ref),
            "module_or_package": ", ".join(sorted({module_label(path) for path in editable_paths})),
            "module_or_package_list": sorted({module_label(path) for path in editable_paths}),
            "editable_paths": editable_paths,
            "test_paths": test_paths,
            "task_time": inv.get("task_time"),
            "task_time_bucket": time_bucket(str(inv.get("task_time"))),
            "statement_digest": inv.get("statement_digest"),
            "adapter_pass_count": adapter_pass_count,
            "repo_split_pass_count": repo_split_summary[repo_split]["verified_pass_count"],
            "task_family_label": task_family_label(repo_id, editable_paths),
            "implementation_file_count": len(editable_paths),
            "test_file_count": len(test_paths),
            "statement_length": len(statement_text),
            "statement_length_bucket": statement_length_bucket(len(statement_text)),
            "source_context_length_bucket": f"{len(inv.get('allowed_public_context_refs', []))}_public_ref_{statement_length_bucket(len(statement_text))}",
            "historical_old_policy_violation_flag": task_id in OLD_POLICY_VIOLATION_TASK_IDS,
            "source_ref": source_ref,
        }
        rows.append(row)
    both_failed = [row["task_id"] for row in rows if row["both_fail"]]
    disagreements = [row["task_id"] for row in rows if row["adapter_disagreement"]]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "task_outcome_matrix.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass" if len(rows) == 16 and sum(2 for _ in rows) == 32 else "mismatch",
        "task_count": len(rows),
        "cell_count": len(rows) * len(ADAPTERS),
        "rows": rows,
        "summary": {
            "both_failed_task_ids": both_failed,
            "adapter_disagreement_task_ids": disagreements,
            "h_future_failure_task_ids": [row["task_id"] for row in rows if row["canonical_split"] == "H_future" and not row["both_pass"]],
            "b_eval_failure_task_ids": [row["task_id"] for row in rows if row["canonical_split"] == "B_eval" and not row["both_pass"]],
            "repo_split_summary": repo_split_summary,
        },
        "new_paid_calls_made": False,
        "followup_runbook_written_by_worker": False,
    }
    return payload


def write_matrix_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    lines = [
        "# Statement-Hardened Task Outcome Matrix",
        "",
        f"Task count: `{payload['task_count']}`. Cell count: `{payload['cell_count']}`.",
        "",
        f"- Both-adapter failures: `{payload['summary']['both_failed_task_ids']}`.",
        f"- Adapter disagreements: `{payload['summary']['adapter_disagreement_task_ids']}`.",
        "",
        "## Both Adapters Failed",
        "",
    ]
    table_cols = [
        ("task_id", "Task"),
        ("repo_split", "Repo split"),
        ("task_family_label", "Family"),
        ("source_kind", "Source"),
        ("statement_source", "Statement source"),
        ("codex_terminal_status", "Codex"),
        ("kilo_terminal_status", "Kilo"),
    ]
    lines.extend(markdown_table([row for row in rows if row["both_fail"]], table_cols))
    lines.extend(["", "## Adapter Disagreement", ""])
    lines.extend(markdown_table([row for row in rows if row["adapter_disagreement"]], table_cols))
    lines.extend(["", "## H Future Failures", ""])
    lines.extend(markdown_table([row for row in rows if row["canonical_split"] == "H_future" and not row["both_pass"]], table_cols))
    lines.extend(["", "## B Eval Failures", ""])
    lines.extend(markdown_table([row for row in rows if row["canonical_split"] == "B_eval" and not row["both_pass"]], table_cols))
    lines.extend(["", "## Full Matrix", ""])
    lines.extend(
        markdown_table(
            rows,
            [
                ("task_id", "Task"),
                ("repo_split", "Repo split"),
                ("task_time_bucket", "Time"),
                ("module_or_package", "Module"),
                ("adapter_pass_count", "Adapter passes"),
                ("both_pass", "Both pass"),
                ("both_fail", "Both fail"),
                ("adapter_disagreement", "Disagreement"),
                ("historical_old_policy_violation_flag", "Old policy flag"),
            ],
        )
    )
    write_text(output_path(config, "task_outcome_matrix_report"), "\n".join(lines))


def run_matrix(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_task_outcome_matrix(config)
    write_json(output_path(config, "task_outcome_matrix"), payload)
    write_matrix_report(config, payload)
    update_queue_step(
        config,
        step="2",
        status="completed",
        outputs=[rel(output_path(config, "task_outcome_matrix")), rel(output_path(config, "task_outcome_matrix_report"))],
        blockers=[],
    )
    return payload


def build_failure_taxonomy(config: dict[str, Any]) -> dict[str, Any]:
    matrix_payload = build_task_outcome_matrix(config)
    matrix_by_task = {row["task_id"]: row for row in matrix_payload["rows"]}
    failed_cells: list[dict[str, Any]] = []
    for row in load_score_rows(config):
        if row["terminal_status"] != TERMINAL_FAIL:
            continue
        matrix_row = matrix_by_task[row["task_id"]]
        override = FAILURE_CATEGORY_OVERRIDES[row["task_id"]]
        categories = sorted(set(override["categories"] + (["adapter_specific_behavior"] if matrix_row["adapter_disagreement"] else [])))
        failed_cells.append(
            {
                "task_id": row["task_id"],
                "adapter_id": row["adapter_id"],
                "repo_split": matrix_row["repo_split"],
                "terminal_status": row["terminal_status"],
                "categories": categories,
                "evidence": override["evidence"],
                "inference": override["inference"],
                "both_adapter_failure": matrix_row["both_fail"],
                "adapter_disagreement": matrix_row["adapter_disagreement"],
                "task_family_label": matrix_row["task_family_label"],
                "source_kind": matrix_row["source_kind"],
                "statement_source": matrix_row["statement_source"],
            }
        )
    task_rollup: dict[str, dict[str, Any]] = {}
    for cell in failed_cells:
        item = task_rollup.setdefault(
            cell["task_id"],
            {
                "task_id": cell["task_id"],
                "repo_split": cell["repo_split"],
                "failed_adapters": [],
                "categories": [],
                "evidence": cell["evidence"],
                "inference": cell["inference"],
                "both_adapter_failure": cell["both_adapter_failure"],
                "adapter_disagreement": cell["adapter_disagreement"],
                "task_family_label": cell["task_family_label"],
            },
        )
        item["failed_adapters"].append(cell["adapter_id"])
        item["categories"] = sorted(set(item["categories"] + cell["categories"]))
    category_counts = Counter(category for cell in failed_cells for category in cell["categories"])
    failed_by_module = Counter(matrix_by_task[cell["task_id"]]["module_or_package"] for cell in failed_cells)
    failed_by_split = Counter(matrix_by_task[cell["task_id"]]["repo_split"] for cell in failed_cells)
    passed_tasks_same_repo_split: dict[str, list[str]] = {}
    for repo_split in sorted({row["repo_split"] for row in matrix_payload["rows"]}):
        passed_tasks_same_repo_split[repo_split] = [
            row["task_id"] for row in matrix_payload["rows"] if row["repo_split"] == repo_split and row["both_pass"]
        ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "failure_taxonomy.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "failed_cell_count": len(failed_cells),
        "failed_task_count": len(task_rollup),
        "failed_cells": failed_cells,
        "task_rollup": sorted(task_rollup.values(), key=lambda item: item["task_id"]),
        "category_counts": dict(sorted(category_counts.items())),
        "concentration": {
            "failed_cells_by_module": dict(sorted(failed_by_module.items())),
            "failed_cells_by_repo_split": dict(sorted(failed_by_split.items())),
            "passed_tasks_in_same_repo_split": passed_tasks_same_repo_split,
            "both_adapter_failure_task_ids": matrix_payload["summary"]["both_failed_task_ids"],
            "adapter_disagreement_task_ids": matrix_payload["summary"]["adapter_disagreement_task_ids"],
        },
        "evidence_boundary": "Taxonomy uses committed score tables, inventory statements, and sanitized score/verifier summaries only; raw transcript and hidden verifier material were not inspected.",
        "new_paid_calls_made": False,
    }
    return payload


def write_failure_taxonomy_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Failure Taxonomy",
        "",
        f"Failed cells: `{payload['failed_cell_count']}`. Failed tasks: `{payload['failed_task_count']}`.",
        "",
        payload["evidence_boundary"],
        "",
        "## Failed Tasks",
        "",
    ]
    lines.extend(
        markdown_table(
            payload["task_rollup"],
            [
                ("task_id", "Task"),
                ("repo_split", "Repo split"),
                ("failed_adapters", "Failed adapters"),
                ("categories", "Categories"),
                ("both_adapter_failure", "Both failed"),
                ("adapter_disagreement", "Disagreement"),
                ("evidence", "Evidence"),
                ("inference", "Inference"),
            ],
        )
    )
    lines.extend(["", "## Category Counts", ""])
    lines.extend(markdown_table([{"category": key, "count": value} for key, value in payload["category_counts"].items()], [("category", "Category"), ("count", "Count")]))
    lines.extend(["", "## Concentration", ""])
    lines.append(f"- Failed cells by repo/split: `{payload['concentration']['failed_cells_by_repo_split']}`.")
    lines.append(f"- Failed cells by module: `{payload['concentration']['failed_cells_by_module']}`.")
    lines.append(f"- Adapter disagreement task IDs: `{payload['concentration']['adapter_disagreement_task_ids']}`.")
    write_text(output_path(config, "failure_taxonomy_report"), "\n".join(lines))


def run_taxonomy(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_failure_taxonomy(config)
    write_json(output_path(config, "failure_taxonomy"), payload)
    write_failure_taxonomy_report(config, payload)
    update_queue_step(
        config,
        step="3",
        status="completed",
        outputs=[rel(output_path(config, "failure_taxonomy")), rel(output_path(config, "failure_taxonomy_report"))],
        blockers=[],
    )
    return payload


def group_cell_stats(cells: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        grouped[str(cell.get(field))].append(cell)
    rows = []
    for key, values in sorted(grouped.items()):
        pass_count = sum(1 for cell in values if cell["terminal_status"] == TERMINAL_PASS)
        rows.append(
            {
                "stratum": key,
                "cell_count": len(values),
                "task_count": len({cell["task_id"] for cell in values}),
                "verified_pass_count": pass_count,
                "verified_fail_count": len(values) - pass_count,
                "pass_rate": round_float(pass_count / len(values) if values else None),
            }
        )
    return rows


def build_strata_analysis(config: dict[str, Any]) -> dict[str, Any]:
    matrix = build_task_outcome_matrix(config)
    matrix_by_task = {row["task_id"]: row for row in matrix["rows"]}
    cells: list[dict[str, Any]] = []
    for score in load_score_rows(config):
        task = matrix_by_task[score["task_id"]]
        cell = {
            "task_id": score["task_id"],
            "adapter_id": score["adapter_id"],
            "terminal_status": score["terminal_status"],
            "repo_id": task["repo_id"],
            "canonical_split": task["canonical_split"],
            "repo_split": task["repo_split"],
            "task_family_label": task["task_family_label"],
            "statement_source": task["statement_source"],
            "source_kind": task["source_kind"],
            "task_time_bucket": task["task_time_bucket"],
            "implementation_file_count": task["implementation_file_count"],
            "test_file_count": task["test_file_count"],
        }
        cells.append(cell)
    dimensions = [
        "repo_id",
        "canonical_split",
        "repo_split",
        "adapter_id",
        "task_family_label",
        "statement_source",
        "source_kind",
        "task_time_bucket",
        "implementation_file_count",
        "test_file_count",
    ]
    strata = {dimension: group_cell_stats(cells, dimension) for dimension in dimensions}
    split_stats = {row["stratum"]: row for row in strata["canonical_split"]}
    pooled_gap = round_float(split_stats["B_eval"]["pass_rate"] - split_stats["H_future"]["pass_rate"])
    paid_metrics = read_json(source_path(config, "paid_metrics"))
    repo_gaps = paid_metrics["b_eval_to_h_future_gap"]
    manifest = read_json(source_path(config, "release_manifest"))
    inventory = read_json(source_path(config, "inventory"))
    split_time_ranges = {}
    for repo_split, task_ids in manifest["canonical_selected_task_ids_by_repo_split"].items():
        times = [parse_task_time(load_inventory_by_task(config)[task_id]["task_time"]) for task_id in task_ids]
        split_time_ranges[repo_split] = {
            "min_task_time": min(times).isoformat(),
            "max_task_time": max(times).isoformat(),
        }
    statement_source_rates = {row["stratum"]: row for row in strata["statement_source"]}
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "strata_analysis.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "strata": strata,
        "pooled_b_eval_to_h_future_gap": pooled_gap,
        "repo_b_eval_to_h_future_gaps": repo_gaps,
        "h_future_drop_same_direction": all(float(gap) > 0 for gap in repo_gaps.values()),
        "split_time_ranges": split_time_ranges,
        "canonical_split_repair_check": {
            "manifest_status": read_json(source_path(config, "release_manifest")).get("status"),
            "inventory_current_split_used_for_selection": inventory.get("summary", {}).get("current_inventory_split_used_for_selection"),
            "manifest_selected_counts": {key: len(value) for key, value in manifest["canonical_selected_task_ids_by_repo_split"].items()},
            "old_mapping_bug_reintroduced": False,
        },
        "strongest_plausible_explanation": "future_holdout_hardness_with_time_window_and_task_family_shift_under_small_n",
        "main_uncertainty": "Only 4 tasks per repo/split and 2 adapters per task; statement source and time/task-family strata are confounded in boltons H_future.",
        "statement_source_rates": statement_source_rates,
        "new_paid_calls_made": False,
    }
    return payload


def write_strata_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Strata Analysis",
        "",
        f"Pooled B_eval to H_future gap: `{payload['pooled_b_eval_to_h_future_gap']}`.",
        f"Repo gaps: `{payload['repo_b_eval_to_h_future_gaps']}`.",
        f"H_future drop same direction across attrs and boltons: `{payload['h_future_drop_same_direction']}`.",
        "",
        "The strongest plausible explanation is future-holdout hardness with time-window and task-family shift under small-N evidence. The main uncertainty is that statement source, task family, and time are confounded in the small boltons H_future slice.",
        "",
        "## Repo/Split Strata",
        "",
    ]
    lines.extend(markdown_table(payload["strata"]["repo_split"], [("stratum", "Repo split"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Adapter Strata", ""])
    lines.extend(markdown_table(payload["strata"]["adapter_id"], [("stratum", "Adapter"), ("cell_count", "Cells"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Task Family Strata", ""])
    lines.extend(markdown_table(payload["strata"]["task_family_label"], [("stratum", "Family"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Statement Source Strata", ""])
    lines.extend(markdown_table(payload["strata"]["statement_source"], [("stratum", "Statement source"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Source Kind Strata", ""])
    lines.extend(markdown_table(payload["strata"]["source_kind"], [("stratum", "Source kind"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Time Bucket Strata", ""])
    lines.extend(markdown_table(payload["strata"]["task_time_bucket"], [("stratum", "Time bucket"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## File Count Strata", ""])
    lines.extend(markdown_table(payload["strata"]["implementation_file_count"], [("stratum", "Implementation files"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(markdown_table(payload["strata"]["test_file_count"], [("stratum", "Test files"), ("cell_count", "Cells"), ("task_count", "Tasks"), ("verified_pass_count", "Pass"), ("verified_fail_count", "Fail"), ("pass_rate", "Pass rate")]))
    lines.extend(["", "## Split Repair Check", ""])
    for key, value in payload["canonical_split_repair_check"].items():
        lines.append(f"- {key}: `{value}`.")
    write_text(output_path(config, "strata_analysis_report"), "\n".join(lines))


def run_strata(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_strata_analysis(config)
    write_json(output_path(config, "strata_analysis"), payload)
    write_strata_report(config, payload)
    update_queue_step(
        config,
        step="4",
        status="completed",
        outputs=[rel(output_path(config, "strata_analysis")), rel(output_path(config, "strata_analysis_report"))],
        blockers=[],
    )
    return payload


def build_threshold_analysis(config: dict[str, Any]) -> dict[str, Any]:
    paid_metrics = read_json(source_path(config, "paid_metrics"))
    decision = read_json(source_path(config, "paid_decision"))
    repo_split_intervals = {}
    for repo_split, data in paid_metrics["per_repo_split"].items():
        repo_split_intervals[repo_split] = {
            "pass_rate": data["pass_rate"],
            "verified_pass_count": data["verified_pass_count"],
            "scoreable_cell_count": data["scoreable_cell_count"],
            "wilson_95": wilson_interval(data["verified_pass_count"], data["scoreable_cell_count"]),
        }
    gap_intervals = {}
    for repo in ["attrs", "boltons"]:
        b = repo_split_intervals[f"{repo}/B_eval"]
        h = repo_split_intervals[f"{repo}/H_future"]
        gap_intervals[repo] = {
            "observed_gap": round_float(b["pass_rate"] - h["pass_rate"]),
            "conservative_wilson_gap_interval": {
                "low": round_float(b["wilson_95"]["low"] - h["wilson_95"]["high"]),
                "high": round_float(b["wilson_95"]["high"] - h["wilson_95"]["low"]),
            },
        }
    score_rows = load_score_rows(config)
    split_counts = Counter()
    split_pass = Counter()
    for row in score_rows:
        split_counts[row["split"]] += 1
        if row["terminal_status"] == TERMINAL_PASS:
            split_pass[row["split"]] += 1
    pooled = {
        split: {
            "pass_rate": round_float(split_pass[split] / split_counts[split]),
            "verified_pass_count": split_pass[split],
            "scoreable_cell_count": split_counts[split],
            "wilson_95": wilson_interval(split_pass[split], split_counts[split]),
        }
        for split in sorted(split_counts)
    }
    primary_gap_threshold = float(config["analysis"]["primary_gap_threshold"])
    threshold_candidates = [
        {
            "name": "stratified_absolute_gap_ci",
            "rule": "For each preregistered repo/split stratum, abs(B_eval pass rate - H_future pass rate) <= 0.15, with a preregistered confidence interval or precision rule and minimum scoreable cells.",
            "compatible_with_proposal": True,
            "too_weak_or_gameable": False,
            "current_result": "fails_observed_gap_and_was_not_preregistered",
            "rationale": "This directly tests whether benchmark selection predicts future target-repo outcomes without changing the ACUT harness.",
        },
        {
            "name": "repo_or_task_family_rank_correlation",
            "rule": "Across at least four repos or six task-family strata, rank correlation between B_eval and H_future pass rates >= 0.60.",
            "compatible_with_proposal": True,
            "too_weak_or_gameable": True,
            "current_result": "not_applicable_two_repos",
            "rationale": "Useful as a secondary diagnostic, but too easy to satisfy with only two repos or unstable strata.",
        },
        {
            "name": "calibration_error_threshold",
            "rule": "Mean absolute calibration error between B_eval-predicted and H_future pass rates <= 0.10, with a preregistered uncertainty rule.",
            "compatible_with_proposal": True,
            "too_weak_or_gameable": False,
            "current_result": "fails_observed_error",
            "rationale": "Matches the benchmark-compiler claim, but needs enough strata to avoid fitting noise.",
        },
        {
            "name": "conditional_holdout_lower_bound",
            "rule": "H_future pass rate must be at least max(0.55, B_eval pass rate - 0.15) in every preregistered repo.",
            "compatible_with_proposal": True,
            "too_weak_or_gameable": False,
            "current_result": "fails_attrs_and_boltons",
            "rationale": "Simple to audit, but should be paired with scoreable-cell minimums and no post-hoc resplitting.",
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "threshold_analysis.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "predictive_validity_established": False,
        "reason_predictive_validity_not_established": decision.get("reason"),
        "repo_split_intervals": repo_split_intervals,
        "pooled_split_intervals": pooled,
        "gap_intervals": gap_intervals,
        "primary_threshold_recommendation": "stratified_absolute_gap_ci",
        "primary_gap_threshold": primary_gap_threshold,
        "candidate_thresholds": threshold_candidates,
        "current_evidence_meets_primary_threshold": False,
        "current_evidence_failure_reasons": [
            "threshold_not_preregistered_before_paid_run",
            "attrs_observed_gap_0.25_exceeds_0.15",
            "boltons_observed_gap_0.375_exceeds_0.15",
            "confidence_intervals_are_wide_under_8_cells_per_repo_split",
        ],
        "new_paid_calls_made": False,
    }
    return payload


def build_power_analysis(config: dict[str, Any]) -> dict[str, Any]:
    target_half_width = float(config["analysis"]["target_gap_half_width"])
    designs = [
        {"name": "current_design", "repos": 2, "tasks_per_repo_split": 4, "adapters": 2},
        {"name": "expanded_tasks", "repos": 2, "tasks_per_repo_split": 8, "adapters": 2},
        {"name": "expanded_repos", "repos": 3, "tasks_per_repo_split": 4, "adapters": 2},
        {"name": "expanded_repos_and_tasks", "repos": 3, "tasks_per_repo_split": 8, "adapters": 2},
        {"name": "single_adapter_current", "repos": 2, "tasks_per_repo_split": 4, "adapters": 1},
        {"name": "adapter_averaged_current_task_units", "repos": 2, "tasks_per_repo_split": 4, "adapters": 1, "effective_unit": "task_average"},
    ]
    rows = []
    for design in designs:
        n = int(design["repos"]) * int(design["tasks_per_repo_split"]) * int(design["adapters"])
        rows.append(
            {
                **design,
                "cells_per_split": n,
                "task_units_per_split": int(design["repos"]) * int(design["tasks_per_repo_split"]),
                "approx_gap_95_half_width_at_p_0_65": gap_half_width(n),
                "approx_power_to_detect_0_30_gap": two_prop_power(n),
                "meets_0_15_precision_target": gap_half_width(n) <= target_half_width,
            }
        )
    cells_needed = sample_needed_for_gap_half_width(target_half_width)
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "power_analysis.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "target_gap_half_width": target_half_width,
        "designs": rows,
        "cells_per_split_needed_for_0_15_half_width": cells_needed,
        "task_units_per_split_needed_if_adapter_averaged": cells_needed,
        "tasks_per_split_needed_if_two_independent_adapters": math.ceil(cells_needed / 2),
        "recommended_minimum_task_level_tasks_per_split": int(config["analysis"]["min_task_level_tasks_per_split_for_primary_threshold"]),
        "interpretation": "The current 16 cells per split have useful scoreability evidence but are underpowered for a 0.15 predictive gap rule; adapter correlation makes the effective sample closer to tasks than cells.",
        "new_paid_calls_made": False,
    }
    return payload


def write_threshold_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Threshold Analysis",
        "",
        f"Predictive validity established: `{payload['predictive_validity_established']}`.",
        f"Primary recommendation: `{payload['primary_threshold_recommendation']}` with gap threshold `{payload['primary_gap_threshold']}`.",
        "",
        "The current run cannot establish predictive validity because no quantitative success rule was preregistered, and the observed repo gaps exceed the candidate 0.15 absolute-gap rule.",
        "",
        "## Repo/Split Intervals",
        "",
    ]
    lines.extend(
        markdown_table(
            [{"repo_split": key, **value} for key, value in payload["repo_split_intervals"].items()],
            [("repo_split", "Repo split"), ("verified_pass_count", "Pass"), ("scoreable_cell_count", "Cells"), ("pass_rate", "Pass rate"), ("wilson_95", "Wilson 95")],
        )
    )
    lines.extend(["", "## Candidate Thresholds", ""])
    lines.extend(markdown_table(payload["candidate_thresholds"], [("name", "Name"), ("rule", "Rule"), ("current_result", "Current result"), ("rationale", "Rationale")]))
    write_text(output_path(config, "threshold_analysis_report"), "\n".join(lines))


def write_power_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Power Analysis",
        "",
        payload["interpretation"],
        "",
        f"Cells per split needed for approximate 0.15 half-width: `{payload['cells_per_split_needed_for_0_15_half_width']}`.",
        f"Recommended minimum task-level tasks per split: `{payload['recommended_minimum_task_level_tasks_per_split']}`.",
        "",
        "## Designs",
        "",
    ]
    lines.extend(
        markdown_table(
            payload["designs"],
            [
                ("name", "Design"),
                ("repos", "Repos"),
                ("tasks_per_repo_split", "Tasks/repo/split"),
                ("adapters", "Adapters"),
                ("cells_per_split", "Cells/split"),
                ("approx_gap_95_half_width_at_p_0_65", "Approx 95 half-width"),
                ("approx_power_to_detect_0_30_gap", "Power for 0.30 gap"),
                ("meets_0_15_precision_target", "Meets 0.15 precision"),
            ],
        )
    )
    write_text(output_path(config, "power_analysis_report"), "\n".join(lines))


def run_threshold_power(config: dict[str, Any]) -> dict[str, Any]:
    threshold = build_threshold_analysis(config)
    power = build_power_analysis(config)
    write_json(output_path(config, "threshold_analysis"), threshold)
    write_json(output_path(config, "power_analysis"), power)
    write_threshold_report(config, threshold)
    write_power_report(config, power)
    update_queue_step(
        config,
        step="5",
        status="completed",
        outputs=[
            rel(output_path(config, "threshold_analysis")),
            rel(output_path(config, "threshold_analysis_report")),
            rel(output_path(config, "power_analysis")),
            rel(output_path(config, "power_analysis_report")),
        ],
        blockers=[],
    )
    return {"threshold": threshold, "power": power}


def build_calibration_options(config: dict[str, Any]) -> dict[str, Any]:
    options = [
        {
            "option": "time_stratified_b_eval_matching",
            "expected_benefit": "Reduces the observed B_eval/H_future time-window mismatch before paid validation.",
            "cost": "local analysis plus possible remanifesting",
            "risk_of_overfitting": "medium",
            "data_needed": "task_time, module, source kind, statement source for candidate pools",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 1,
        },
        {
            "option": "difficulty_balanced_b_eval_selection",
            "expected_benefit": "Keeps B_eval from being easier than H_future by balancing implementation/test surface and module family.",
            "cost": "local scoring and selection work",
            "risk_of_overfitting": "medium",
            "data_needed": "local certification metadata and sanitized statement surface metrics",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 2,
        },
        {
            "option": "expanded_holdout_with_minimum_scoreable_cells",
            "expected_benefit": "Improves uncertainty enough for a preregistered threshold to mean something.",
            "cost": "more local supply and later paid validation if approved",
            "risk_of_overfitting": "low",
            "data_needed": "additional clean outcome-unseen tasks and frozen preregistration",
            "respects_acut_boundary": True,
            "requires_paid_validation": True,
            "rank": 3,
        },
        {
            "option": "module_task_family_weighting",
            "expected_benefit": "Addresses boltons H_future family shift and attrs next_gen/setattr concentration.",
            "cost": "local weighting design and preregistration",
            "risk_of_overfitting": "high",
            "data_needed": "enough tasks per family to avoid single-task weights",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 4,
        },
        {
            "option": "adapter_disagreement_weighting",
            "expected_benefit": "Could downweight unstable adapter-specific cells.",
            "cost": "low local analysis",
            "risk_of_overfitting": "medium",
            "data_needed": "larger disagreement sample",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 5,
        },
        {
            "option": "statement_quality_confidence_weighting",
            "expected_benefit": "Separates residual statement risk from task difficulty.",
            "cost": "review rubric and possibly another local review pass",
            "risk_of_overfitting": "medium",
            "data_needed": "pre-outcome statement QA features only",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 6,
        },
        {
            "option": "negative_evidence_reporting_without_further_paid_runs",
            "expected_benefit": "Honest paper/prototype result: clean scoreable evidence but no predictive-validity claim.",
            "cost": "report writing",
            "risk_of_overfitting": "low",
            "data_needed": "current artifacts only",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 7,
        },
        {
            "option": "per_repo_calibration_using_local_historical_dry_run_metadata",
            "expected_benefit": "May improve expected future pass-rate estimates.",
            "cost": "local calibration design",
            "risk_of_overfitting": "high",
            "data_needed": "strictly pre-paid, non-oracle local dry-run metadata",
            "respects_acut_boundary": True,
            "requires_paid_validation": False,
            "rank": 8,
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "calibration_options.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "ranked_options": sorted(options, key=lambda item: item["rank"]),
        "recommendation": "Before any more paid validation, preregister a quantitative threshold and rebuild the release with time-stratified and difficulty-balanced B_eval matching.",
        "acut_boundary_check": "All ranked options are benchmark-compiler changes; none reimplements file search, editing, retry, or reasoning internals of the ACUT harness.",
        "new_paid_calls_made": False,
    }
    return payload


def write_calibration_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Calibration Options",
        "",
        payload["recommendation"],
        "",
        payload["acut_boundary_check"],
        "",
        "## Ranked Options",
        "",
    ]
    lines.extend(
        markdown_table(
            payload["ranked_options"],
            [
                ("rank", "Rank"),
                ("option", "Option"),
                ("expected_benefit", "Expected benefit"),
                ("cost", "Cost"),
                ("risk_of_overfitting", "Overfit risk"),
                ("requires_paid_validation", "Requires paid validation"),
            ],
        )
    )
    write_text(output_path(config, "calibration_options_report"), "\n".join(lines))


def run_calibration(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_calibration_options(config)
    write_json(output_path(config, "calibration_options"), payload)
    write_calibration_report(config, payload)
    update_queue_step(
        config,
        step="6",
        status="completed",
        outputs=[rel(output_path(config, "calibration_options")), rel(output_path(config, "calibration_options_report"))],
        blockers=[],
    )
    return payload


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def task_ids_from_jsonl(path: Path) -> list[str]:
    ids = []
    for row in read_jsonl(path):
        if row.get("task_id"):
            ids.append(str(row["task_id"]))
    return ids


def build_local_supply_analysis(config: dict[str, Any]) -> dict[str, Any]:
    manifest = read_json(source_path(config, "release_manifest"))
    selected = set(selected_task_ids(manifest))
    reservoirs = []
    for key in [
        "attrs_clean_outcome_unseen",
        "boltons_clean_outcome_unseen",
        "boltons_historical_certified",
        "humanize_certified",
        "itsdangerous_certified",
        "toolz_certified",
    ]:
        path = local_supply_path(config, key)
        ids = task_ids_from_jsonl(path)
        reservoirs.append(
            {
                "reservoir": key,
                "path": rel(path),
                "task_count": len(ids),
                "already_selected_count": len(set(ids) & selected),
                "remaining_count": len([task_id for task_id in ids if task_id not in selected]),
                "remaining_task_ids": [task_id for task_id in ids if task_id not in selected],
            }
        )
    threshold = build_power_analysis(config)
    current_task_units_per_split = 2 * 4
    needed_task_units = int(config["analysis"]["min_task_level_tasks_per_split_for_primary_threshold"])
    decision_second = read_json(local_supply_path(config, "second_repo_clean_supply_decision"))
    decision_third = read_json(local_supply_path(config, "third_repo_replacement_selection_decision"))
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "local_supply_analysis.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "status": "pass",
        "reservoirs": reservoirs,
        "current_task_units_per_split": current_task_units_per_split,
        "recommended_task_units_per_split_for_primary_threshold": needed_task_units,
        "additional_task_units_per_split_needed": max(0, needed_task_units - current_task_units_per_split),
        "additional_cells_per_split_needed_for_precision_target": max(0, threshold["cells_per_split_needed_for_0_15_half_width"] - 16),
        "expansion_preference": "First design a threshold, then prefer better B_eval/H_future matching and additional tasks per existing repo; add a third repo only after source provenance and statement hardening are locally clean.",
        "most_promising_local_reservoir": "attrs_clean_outcome_unseen for existing-repo expansion; humanize_certified is the largest third-repo pool but needs validation-grade source/provenance hardening before paid use.",
        "second_repo_context": {
            "selected_repo_id": decision_second.get("selected_repo_id"),
            "promoted_task_count": decision_second.get("promoted_task_count"),
            "clean_supply_ready": decision_second.get("clean_supply_ready"),
        },
        "third_repo_context": {
            "selected_repo_id": decision_third.get("selected_repo_id"),
            "ready_for_paid_smoke": decision_third.get("ready_for_paid_smoke"),
            "release_status": decision_third.get("release_status"),
        },
        "local_task_preparation_distinguished_from_paid_validation": True,
        "new_paid_calls_made": False,
    }
    return payload


def write_local_supply_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Local Supply Analysis",
        "",
        payload["expansion_preference"],
        "",
        f"Most promising local reservoir: {payload['most_promising_local_reservoir']}",
        "",
        f"Additional task units per split needed for the recommended threshold: `{payload['additional_task_units_per_split_needed']}`.",
        f"Additional cells per split needed for the precision target: `{payload['additional_cells_per_split_needed_for_precision_target']}`.",
        "",
        "## Reservoirs",
        "",
    ]
    lines.extend(markdown_table(payload["reservoirs"], [("reservoir", "Reservoir"), ("task_count", "Tasks"), ("already_selected_count", "Selected"), ("remaining_count", "Remaining"), ("path", "Path")]))
    lines.extend(["", "## Boundary", ""])
    lines.append("- This is local task preparation analysis, not paid validation.")
    lines.append("- No new task mining was performed.")
    write_text(output_path(config, "local_supply_analysis_report"), "\n".join(lines))


def run_local_supply(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_local_supply_analysis(config)
    write_json(output_path(config, "local_supply_analysis"), payload)
    write_local_supply_report(config, payload)
    update_queue_step(
        config,
        step="7",
        status="completed",
        outputs=[rel(output_path(config, "local_supply_analysis")), rel(output_path(config, "local_supply_analysis_report"))],
        blockers=[],
    )
    return payload


def build_proposal_alignment(config: dict[str, Any]) -> dict[str, Any]:
    proposal_path = REPO_ROOT / "barcarolle-research-0519.md"
    architecture_path = source_path(config, "architecture_proposal")
    source_used = proposal_path if proposal_path.exists() else architecture_path
    source_text = source_used.read_text(encoding="utf-8") if source_used.exists() else ""
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "proposal_alignment.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "source_used": rel(source_used),
        "proposal_file_available": proposal_path.exists(),
        "source_digest": digest_text(source_text) if source_text else None,
        "still_aligned_with_target_repository_benchmark_compiler": True,
        "latest_result_effect_on_core_claim": "weakens_predictive_validity_claim_but_strengthens_scoreability_policy_cost_claims",
        "claim_can_be_made_now": "A canonical-split statement-hardened two-repo release produced clean 32-cell scoreable evidence with no policy violations and bounded cost, but it did not establish predictive validity.",
        "claim_must_not_be_made": [
            "predictive_validity_established",
            "production_benchmark_ranking",
            "old_paid_result_repaired",
            "generated_statement_as_scoreable_result",
        ],
        "most_direct_next_work": "analysis_and_compiler_design_before_paid_scale_up",
        "most_direct_experiment": "preregister a quantitative predictive-validity threshold and locally rebuild a time/task-family balanced release before any bounded paid replication.",
        "current_evidence_is_bounded_not_predictive_validity": True,
        "new_paid_calls_made": False,
    }
    return payload


def write_proposal_alignment_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Proposal Alignment Memo",
        "",
        f"Source used: `{payload['source_used']}`.",
        f"Original proposal file available: `{payload['proposal_file_available']}`.",
        "",
        "The project is still aligned with the target-repository benchmark compiler boundary if this result is reported as bounded evidence, not as predictive validity. The clean scoreability, policy, and cost gates strengthen the operational compiler story. The H_future drop and missing threshold weaken the stronger claim that B_eval currently predicts future target-repo work.",
        "",
        "## Current Claim",
        "",
        payload["claim_can_be_made_now"],
        "",
        "## Claims To Avoid",
        "",
    ]
    for claim in payload["claim_must_not_be_made"]:
        lines.append(f"- `{claim}`")
    lines.extend(["", "## Next Work", "", payload["most_direct_experiment"]])
    write_text(output_path(config, "proposal_alignment_report"), "\n".join(lines))


def run_proposal_alignment(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_proposal_alignment(config)
    write_proposal_alignment_report(config, payload)
    update_queue_step(
        config,
        step="8",
        status="completed",
        outputs=[rel(output_path(config, "proposal_alignment_report"))],
        blockers=[],
    )
    return payload


def build_final_decision(config: dict[str, Any]) -> dict[str, Any]:
    integrity = read_json(output_path(config, "integrity_audit")) if output_path(config, "integrity_audit").exists() else build_integrity_audit(config)
    matrix = read_json(output_path(config, "task_outcome_matrix")) if output_path(config, "task_outcome_matrix").exists() else build_task_outcome_matrix(config)
    strata = read_json(output_path(config, "strata_analysis")) if output_path(config, "strata_analysis").exists() else build_strata_analysis(config)
    threshold = read_json(output_path(config, "threshold_analysis")) if output_path(config, "threshold_analysis").exists() else build_threshold_analysis(config)
    power = read_json(output_path(config, "power_analysis")) if output_path(config, "power_analysis").exists() else build_power_analysis(config)
    calibration = read_json(output_path(config, "calibration_options")) if output_path(config, "calibration_options").exists() else build_calibration_options(config)
    supply = read_json(output_path(config, "local_supply_analysis")) if output_path(config, "local_supply_analysis").exists() else build_local_supply_analysis(config)
    primary_decision = "design_new_predictive_threshold_before_more_paid_validation"
    if integrity["status"] != "pass":
        primary_decision = "blocked_on_integrity_or_tooling"
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "next_action_decision.v1",
        "generated_at": utc_now(),
        "release_id": config["release_id"],
        "primary_decision": primary_decision,
        "confidence": "medium_high" if integrity["status"] == "pass" else "low",
        "integrity_audit_status": integrity["status"],
        "main_evidence": [
            "32 planned cells completed and scoreable",
            "21 verified_pass and 11 verified_fail",
            "policy violations, timeouts, harness errors, and invalid outputs were all zero",
            "attrs gap 0.25 and boltons gap 0.375 both show H_future lower than B_eval",
            "adapter disagreement was 1 of 16 tasks",
        ],
        "main_uncertainty": [
            "no preregistered quantitative predictive-validity threshold",
            "4 tasks per repo/split leaves wide intervals",
            "boltons H_future confounds time window, task family, and statement source",
        ],
        "recommended_next_action": "Do not run more paid validation until a quantitative predictive-validity threshold and a better matched local design are preregistered.",
        "suggested_followup_category": "threshold_and_stratified_resplit_design",
        "followup_runbook_written_by_worker": False,
        "new_paid_calls_made": False,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "research_questions": {
            "RQ1": "Yes for scoreable evidence: statement hardening produced clean scoreable 32-cell evidence with no policy violations. It did not by itself produce predictive validity.",
            "RQ2": "No. B_eval did not predict H_future well enough under the current split; observed gaps were 0.25 for attrs and 0.375 for boltons.",
            "RQ3": "The H_future drop is best read as a combination of future-holdout/task-family hardness and small-N uncertainty, with residual statement-source risk in boltons and low adapter variance.",
            "RQ4": "Future preregistrations should use a stratified absolute B_eval-H_future gap rule, primarily <=0.15 with minimum scoreable cells and a confidence/precision rule.",
            "RQ5": "Next, design the quantitative threshold and locally resplit/reweight for time and task family. Enlarge local supply before any paid replication; do not report a production benchmark ranking.",
        },
        "allowed_claims": [
            "statement_hardened_paid_evidence_analyzed",
            "scoreability_gate_passed",
            "policy_gate_passed",
            "cost_gate_passed",
            "predictive_validity_threshold_missing",
            "predictive_validity_not_established",
            "task_difficulty_shift_evidence",
            "adapter_disagreement_low",
            "sample_size_underpowered",
            "threshold_options_proposed",
            "compiler_design_options_ranked",
            "bounded_negative_or_inconclusive_evidence_reported",
        ],
        "disallowed_claims_not_made": [
            "predictive_validity_established_without_threshold",
            "production_benchmark_ranking",
            "old_paid_result_repaired",
            "attrs_policy_violation_repaired",
            "hidden_oracle_informed_statement_rewrite",
            "new_paid_validation_completed",
            "followup_runbook_written_by_worker",
        ],
        "key_artifacts": {
            "matrix": rel(output_path(config, "task_outcome_matrix")),
            "strata": rel(output_path(config, "strata_analysis")),
            "threshold": rel(output_path(config, "threshold_analysis")),
            "power": rel(output_path(config, "power_analysis")),
            "calibration": rel(output_path(config, "calibration_options")),
            "local_supply": rel(output_path(config, "local_supply_analysis")),
        },
        "summary_metrics": {
            "both_failed_task_ids": matrix["summary"]["both_failed_task_ids"],
            "adapter_disagreement_task_ids": matrix["summary"]["adapter_disagreement_task_ids"],
            "pooled_b_eval_to_h_future_gap": strata["pooled_b_eval_to_h_future_gap"],
            "repo_b_eval_to_h_future_gaps": strata["repo_b_eval_to_h_future_gaps"],
            "current_evidence_meets_primary_threshold": threshold["current_evidence_meets_primary_threshold"],
            "recommended_minimum_task_level_tasks_per_split": power["recommended_minimum_task_level_tasks_per_split"],
            "top_calibration_option": calibration["ranked_options"][0]["option"],
            "most_promising_local_reservoir": supply["most_promising_local_reservoir"],
        },
    }
    return payload


def write_final_decision_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Next Action Decision",
        "",
        f"Primary decision: `{payload['primary_decision']}`.",
        f"Confidence: `{payload['confidence']}`.",
        f"Predictive validity established: `{payload['predictive_validity_established']}`.",
        "",
        "## Research Questions",
        "",
    ]
    for key, value in payload["research_questions"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Main Evidence", ""])
    for item in payload["main_evidence"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Main Uncertainty", ""])
    for item in payload["main_uncertainty"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Action", "", payload["recommended_next_action"], "", "No follow-up runbook was written by this worker."])
    write_text(output_path(config, "next_action_decision_report"), "\n".join(lines))


def run_final_decision(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_final_decision(config)
    write_json(output_path(config, "next_action_decision"), payload)
    write_final_decision_report(config, payload)
    update_queue_step(
        config,
        step="9",
        status="completed",
        outputs=[rel(output_path(config, "next_action_decision")), rel(output_path(config, "next_action_decision_report"))],
        blockers=[] if payload["primary_decision"] != "blocked_on_integrity_or_tooling" else ["integrity_or_tooling_blocker"],
    )
    return payload


def verification_commands() -> list[tuple[str, list[str]]]:
    return [
        ("git diff --check", ["git", "diff", "--check"]),
        (
            "overnight evidence tests",
            [
                "uv",
                "run",
                "--project",
                "experiments/phase1_compiler",
                "pytest",
                "-q",
                "experiments/phase1_compiler/tests/test_phase1_overnight_statement_hardened_evidence_analysis.py",
            ],
        ),
        (
            "paid validation regression tests",
            [
                "uv",
                "run",
                "--project",
                "experiments/phase1_compiler",
                "pytest",
                "-q",
                "experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_paid_validation.py",
                "experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py",
                "experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py",
            ],
        ),
        (
            "diff assisted codex loop regression tests",
            [
                "uv",
                "run",
                "--project",
                "experiments/phase1_compiler",
                "pytest",
                "-q",
                "experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py",
            ],
        ),
    ]


def run_closeout(config: dict[str, Any]) -> dict[str, Any]:
    results = []
    for name, args in verification_commands():
        result = command_result(args)
        results.append(
            {
                "name": name,
                "args": args,
                "returncode": result["returncode"],
                "status": "pass" if result["returncode"] == 0 else "fail",
                "duration_seconds": result["duration_seconds"],
                "stdout_tail": result["stdout"][-1200:],
                "stderr_tail": result["stderr"][-1200:],
            }
        )
    status = "completed" if all(item["returncode"] == 0 for item in results) else "verification_failed"
    update_queue_step(
        config,
        step="10",
        status=status,
        outputs=[rel(output_path(config, "process_report"))],
        blockers=[] if status == "completed" else ["verification_failed"],
        extra={
            "status": status,
            "verification_commands": results,
            "closeout": {
                "steps_completed": [str(i) for i in range(11)],
                "new_paid_acut_calls_made": False,
                "new_paid_llm_calls_made": False,
                "raw_artifacts_committed": False,
                "followup_runbook_written_by_worker": False,
                "integrity_audit_status": read_json(output_path(config, "integrity_audit")).get("status")
                if output_path(config, "integrity_audit").exists()
                else None,
                "primary_decision": read_json(output_path(config, "next_action_decision")).get("primary_decision")
                if output_path(config, "next_action_decision").exists()
                else None,
            },
        },
    )
    return {"schema_version": OUTPUT_SCHEMA_VERSION, "analysis_schema": "closeout.v1", "status": status, "verification_commands": results}


MODES = {
    "preflight": run_preflight,
    "integrity": run_integrity,
    "matrix": run_matrix,
    "taxonomy": run_taxonomy,
    "strata": run_strata,
    "threshold-power": run_threshold_power,
    "calibration": run_calibration,
    "local-supply": run_local_supply,
    "proposal-alignment": run_proposal_alignment,
    "decision": run_final_decision,
    "closeout": run_closeout,
}


def run_all(config: dict[str, Any]) -> None:
    for mode in MODES:
        MODES[mode](config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=sorted(list(MODES) + ["all"]))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.mode == "all":
        run_all(config)
        return 0
    payload = MODES[args.mode](config)
    if args.mode == "closeout" and payload.get("status") != "completed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
