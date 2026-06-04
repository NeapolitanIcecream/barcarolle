from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import workspace_acut_run as workspace_acut  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_statement_hardened_after_canonical_repair_paid_validation.yaml"
SCHEMA_VERSION = "barcarolle.phase1_statement_hardened_after_canonical_repair_paid_validation.v1"
EXPECTED_GROUPS: dict[str, list[str]] = {
    "attrs/B_eval": [
        "attrs__hist__001",
        "attrs__hist__003",
        "attrs__hist__004",
        "attrs__hist__008",
    ],
    "attrs/H_future": [
        "attrs__hist__012",
        "attrs__hist__013",
        "attrs__hist__023",
        "attrs__hist__027",
    ],
    "boltons/B_eval": [
        "boltons__clean_ext__001",
        "boltons__clean_ext__008",
        "boltons__clean_ext__010",
        "boltons__hist__011",
    ],
    "boltons/H_future": [
        "boltons__clean_ext__017",
        "boltons__hist__022",
        "boltons__hist__023",
        "boltons__hist__027",
    ],
}
FORBIDDEN_STATEMENT_PATTERNS: dict[str, str] = {
    "diff --git": "raw_diff_marker",
    "\n@@": "raw_diff_hunk_marker",
    "verified_pass": "paid_outcome_status_text",
    "verified_fail": "paid_outcome_status_text",
    "policy_violation": "policy_status_text",
    "hidden verifier": "hidden_verifier_marker",
    "raw test assertion": "raw_test_assertion_label",
}
RAW_TEST_ASSERTION_RE = re.compile(r"\bassert\s+")
TARGET_COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")
TERMINAL_STATUSES = {"verified_pass", "verified_fail", "policy_violation", "invalid_output", "acut_harness_error", "harness_error", "timeout"}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def config_path(raw: Any) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected paid validation config schema_version")
    config["_path"] = str(path)
    return config


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["output_paths"][key])


def source_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["source_artifacts"][key])


def matrix_config_path(config: dict[str, Any]) -> Path:
    return config_path(config["workspace_runner"]["matrix_config"])


def result_prefixes(config: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in config["workspace_runner"]["result_prefixes"].items()}


def expected_task_ids() -> list[str]:
    ordered: list[str] = []
    for group in ["attrs/B_eval", "attrs/H_future", "boltons/B_eval", "boltons/H_future"]:
        ordered.extend(EXPECTED_GROUPS[group])
    return ordered


def package_map(config: dict[str, Any]) -> dict[str, workspace_acut.TaskPackage]:
    packages = workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=matrix_config_path(config))
    return {package.task_id: package for package in packages}


def statement_findings(text: str) -> list[str]:
    findings = [label for pattern, label in FORBIDDEN_STATEMENT_PATTERNS.items() if pattern in text.lower()]
    if RAW_TEST_ASSERTION_RE.search(text):
        findings.append("raw_test_assertion")
    if TARGET_COMMIT_RE.search(text):
        findings.append("target_commit_hash")
    return sorted(set(findings))


def wilson_interval(pass_count: int, total: int, z: float = 1.96) -> dict[str, float | None]:
    if total == 0:
        return {"low": None, "high": None}
    phat = pass_count / total
    denominator = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total) / denominator
    return {"low": round(max(0.0, center - margin), 4), "high": round(min(1.0, center + margin), 4)}


def validate_tooling(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    manifest = read_json(source_path(config, "release_manifest"))
    preview = read_json(source_path(config, "release_preview"))
    inventory = read_json(source_path(config, "inventory"))
    screen = read_json(source_path(config, "screen"))
    decision = read_json(source_path(config, "validation_decision"))
    packages = package_map(config)
    preview_by_id = {str(row["task_id"]): row for row in preview.get("previews", [])}
    manifest_groups = manifest.get("canonical_selected_task_ids_by_repo_split", {})
    expected_ids = expected_task_ids()
    package_rows: list[dict[str, Any]] = []
    for task_id in expected_ids:
        package = packages.get(task_id)
        preview_row = preview_by_id.get(task_id, {})
        digest = digest_text(package.solver_facing_statement) if package else None
        package_rows.append(
            {
                "task_id": task_id,
                "repo_id": None if package is None else package.repo_id,
                "split": None if package is None else package.split,
                "allowed_code_paths": [] if package is None else package.allowed_code_paths,
                "test_paths": [] if package is None else package.test_paths,
                "statement_digest": digest,
                "frozen_statement_digest": manifest.get("statement_digests", {}).get(task_id),
                "statement_digest_matches_frozen": digest == manifest.get("statement_digests", {}).get(task_id),
                "statement_findings": [] if package is None else statement_findings(package.solver_facing_statement),
                "tests_non_editable": False
                if package is None
                else not set(package.allowed_code_paths).intersection(set(package.test_paths))
                and all(workspace_acut.is_test_path(path) for path in package.test_paths),
                "preview_statement_source": preview_row.get("statement_source"),
            }
        )

    actual_groups: dict[str, list[str]] = defaultdict(list)
    for package in packages.values():
        actual_groups[f"{package.repo_id}/{package.split}"].append(package.task_id)
    blockers: list[str] = []
    if manifest.get("status") != "frozen":
        blockers.append("release_manifest_not_frozen")
    if decision.get("primary_decision") != "ready_for_user_approved_paid_validation":
        blockers.append("validation_decision_not_ready")
    if sorted(packages) != sorted(expected_ids):
        blockers.append("package_task_ids_do_not_match_frozen_selection")
    if {key: sorted(value) for key, value in actual_groups.items()} != {key: sorted(value) for key, value in manifest_groups.items()}:
        blockers.append("package_repo_split_groups_do_not_match_manifest")
    if any(not row["statement_digest_matches_frozen"] for row in package_rows):
        blockers.append("statement_digest_mismatch")
    if any(row["statement_findings"] for row in package_rows):
        blockers.append("solver_visible_statement_forbidden_material")
    if any(not row["tests_non_editable"] for row in package_rows):
        blockers.append("tests_not_non_editable")
    if inventory.get("summary", {}).get("current_inventory_split_used_for_selection") is not False:
        blockers.append("inventory_summary_allows_current_split_selection")
    if screen.get("current_inventory_split_used_for_selection") is not False:
        blockers.append("screen_allows_current_split_selection")

    payload = {
        "schema_version": "barcarolle.phase1_statement_hardened_paid_tooling_check.v1",
        "generated_at": iso_now(),
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "config": rel(config_path),
        "matrix_config": rel(matrix_config_path(config)),
        "release_id": manifest.get("release_id"),
        "selected_task_count": len(packages),
        "selected_task_ids": [task_id for task_id in expected_ids if task_id in packages],
        "expected_task_ids": expected_ids,
        "canonical_selected_task_ids_by_repo_split": manifest_groups,
        "actual_task_ids_by_repo_split": {key: sorted(value) for key, value in actual_groups.items()},
        "boltons_clean_ext_017_split": None if "boltons__clean_ext__017" not in packages else packages["boltons__clean_ext__017"].split,
        "current_inventory_split_used_for_selection": False,
        "paid_outcomes_used_for_package_loading": False,
        "followup_runbook_written_by_worker": False,
        "package_rows": package_rows,
        "input_artifact_digests": {
            rel(path): digest_file(path)
            for path in [
                source_path(config, "release_manifest"),
                source_path(config, "release_preview"),
                source_path(config, "inventory"),
                source_path(config, "screen"),
            ]
        },
    }
    write_json(output_path(config, "tooling_check"), payload)
    write_tooling_report(config, payload)
    return payload


def write_tooling_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Paid Tooling Check",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Matrix config: `{payload['matrix_config']}`.",
        f"- Selected task count: `{payload['selected_task_count']}`.",
        f"- `boltons__clean_ext__017` split: `{payload['boltons_clean_ext_017_split']}`.",
        f"- Current inventory split used for selection: `{payload['current_inventory_split_used_for_selection']}`.",
        f"- Paid outcomes used for package loading: `{payload['paid_outcomes_used_for_package_loading']}`.",
        f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
        "",
        "## Blockers",
        "",
        *(f"- `{blocker}`" for blocker in payload["blockers"]),
        "" if payload["blockers"] else "- None.",
        "",
    ]
    write_text(output_path(config, "tooling_check_report"), "\n".join(lines))


def read_score_table(prefix: str) -> list[dict[str, Any]]:
    path = PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["scoreable_cell"] = str(row.get("scoreable_cell", "")).lower() == "true"
    return rows


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_cost_summary(prefix: str) -> dict[str, Any]:
    path = PHASE0_ROOT / "results" / f"{prefix}_cost_summary.json"
    return read_json(path) if path.exists() else {}


def cost_value(summary: dict[str, Any]) -> float:
    for key in ["observed_or_conservative_estimated_cost_usd", "conservative_estimated_cost_usd", "estimated_cost_usd"]:
        if summary.get(key) is not None:
            return float(summary.get(key) or 0.0)
    return 0.0


def group_from_prefix_key(key: str) -> str:
    parts = key.split("_")
    return f"{parts[0]}/{'B_eval' if parts[-2:] == ['b', 'eval'] else 'H_future'}"


def score_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_counts = Counter(str(row.get("terminal_status") or "") for row in rows)
    scoreable = [row for row in rows if row.get("scoreable_cell") is True]
    pass_count = sum(1 for row in scoreable if row.get("terminal_status") == "verified_pass")
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "verified_pass_count": pass_count,
        "verified_fail_count": sum(1 for row in scoreable if row.get("terminal_status") == "verified_fail"),
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "wilson_95": wilson_interval(pass_count, len(scoreable)),
    }


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return round(ordered[middle], 3)
    return round((ordered[middle - 1] + ordered[middle]) / 2, 3)


def conservative_cost_by_run_id(prefixes: list[str]) -> dict[str, float]:
    costs: dict[str, float] = {}
    for prefix in prefixes:
        for row in read_jsonl(PHASE0_ROOT / "results" / f"{prefix}_cost_ledger.jsonl"):
            if row.get("run_id"):
                costs[str(row["run_id"])] = float(row.get("estimated_cost_usd") or 0.0)
    return costs


def usage_rows_for_prefixes(prefixes: list[str]) -> list[dict[str, Any]]:
    wanted = set(prefixes)
    return [row for row in read_jsonl(PHASE0_ROOT / "results" / "workspace_usage_ledger.jsonl") if row.get("result_prefix") in wanted]


def adapter_cost_latency(prefixes: list[str]) -> dict[str, dict[str, Any]]:
    conservative_by_run_id = conservative_cost_by_run_id(prefixes)
    usage_rows = usage_rows_for_prefixes(prefixes)
    by_adapter: dict[str, dict[str, Any]] = {}
    for row in usage_rows:
        adapter = str(row.get("adapter_id") or row.get("harness_name") or "unknown")
        bucket = by_adapter.setdefault(
            adapter,
            {
                "observed_token_cost_usd": 0.0,
                "conservative_fallback_cost_usd": 0.0,
                "usage_observed_count": 0,
                "cell_count": 0,
                "latencies": [],
            },
        )
        bucket["cell_count"] += 1
        if row.get("usage_observed") is True:
            bucket["usage_observed_count"] += 1
            bucket["observed_token_cost_usd"] += float(row.get("estimated_cost_usd") or 0.0)
        else:
            bucket["conservative_fallback_cost_usd"] += conservative_by_run_id.get(str(row.get("run_id")), 0.0)
        if row.get("latency_seconds") is not None:
            bucket["latencies"].append(float(row["latency_seconds"]))
    return {
        adapter: {
            "observed_token_cost_usd": round(values["observed_token_cost_usd"], 8),
            "conservative_fallback_cost_usd": round(values["conservative_fallback_cost_usd"], 8),
            "observed_or_conservative_cost_usd": round(values["observed_token_cost_usd"] + values["conservative_fallback_cost_usd"], 8),
            "usage_observed_count": values["usage_observed_count"],
            "usage_observed_rate": None if values["cell_count"] == 0 else round(values["usage_observed_count"] / values["cell_count"], 4),
            "median_latency_seconds": median(values["latencies"]),
        }
        for adapter, values in by_adapter.items()
    }


def adapter_disagreement_rate(rows: list[dict[str, Any]]) -> float | None:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row.get("task_id"))].append(row)
    comparable = 0
    disagree = 0
    for task_rows in by_task.values():
        scoreable = [row for row in task_rows if row.get("scoreable_cell") is True]
        if len(scoreable) < 2:
            continue
        comparable += 1
        outcomes = {row.get("terminal_status") for row in scoreable}
        if len(outcomes) > 1:
            disagree += 1
    return None if comparable == 0 else round(disagree / comparable, 4)


def compute_metrics(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    prefixes = result_prefixes(config)
    prefix_values = list(prefixes.values())
    per_group: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    total_cost = 0.0
    for key, prefix in prefixes.items():
        rows = read_score_table(prefix)
        all_rows.extend({**row, "repo_split": group_from_prefix_key(key), "result_prefix": prefix} for row in rows)
        cost = read_cost_summary(prefix)
        prefix_cost = cost_value(cost)
        total_cost += prefix_cost
        per_group[group_from_prefix_key(key)] = {
            **score_metrics(rows),
            "result_prefix": prefix,
            "observed_or_conservative_cost_usd": prefix_cost,
            "median_latency_seconds": cost.get("median_latency_seconds"),
        }

    by_adapter: dict[str, Any] = {}
    adapter_costs = adapter_cost_latency(prefix_values)
    for adapter in sorted({str(row.get("adapter_id")) for row in all_rows if row.get("adapter_id")}):
        adapter_rows = [row for row in all_rows if row.get("adapter_id") == adapter]
        by_adapter[adapter] = {**score_metrics(adapter_rows), **adapter_costs.get(adapter, {})}

    policy_violations = sum(1 for row in all_rows if row.get("terminal_status") == "policy_violation")
    completed = len(all_rows) == int(float(config["budget"]["planned_cells"]))
    enough_scoreable = all(group.get("scoreable_cell_count", 0) >= int(config["acceptance"]["min_scoreable_cells_per_batch"]) for group in per_group.values())
    cost_bounded = total_cost <= float(config["budget"]["incremental_hard_cap_usd"])
    gates_clean = completed and enough_scoreable and policy_violations <= int(config["acceptance"]["policy_violations_max"]) and cost_bounded
    metrics = {
        "schema_version": "barcarolle.phase1_statement_hardened_paid_metrics.v1",
        "generated_at": iso_now(),
        "status": "complete" if completed else "incomplete",
        "planned_cells": int(float(config["budget"]["planned_cells"])),
        "total_cells": len(all_rows),
        "scoreable_cell_count": sum(1 for row in all_rows if row.get("scoreable_cell") is True),
        "terminal_status_counts": dict(sorted(Counter(str(row.get("terminal_status") or "") for row in all_rows).items())),
        "policy_violation_count": policy_violations,
        "policy_violation_rate": None if not all_rows else round(policy_violations / len(all_rows), 4),
        "observed_or_conservative_cost_usd": round(total_cost, 8),
        "adapter_disagreement_rate": adapter_disagreement_rate(all_rows),
        "per_repo_split": per_group,
        "by_adapter": by_adapter,
        "b_eval_to_h_future_gap": gap_metrics(per_group),
        "old_score_tables_merged": False,
    }
    decision_status = (
        "statement_hardened_paid_validation_complete_threshold_not_met"
        if gates_clean
        else "statement_hardened_paid_validation_blocked_policy_or_cost"
        if policy_violations or not cost_bounded
        else "statement_hardened_paid_validation_blocked_non_scoreable_cells"
        if completed and not enough_scoreable
        else "statement_hardened_paid_validation_blocked_tooling"
    )
    decision = {
        "schema_version": "barcarolle.phase1_statement_hardened_paid_decision.v1",
        "generated_at": metrics["generated_at"],
        "primary_decision": decision_status,
        "predictive_validity_established": False,
        "reason": "No preregistered quantitative predictive-validity success threshold beyond scoreability, policy, and cost gates is recorded for this runbook."
        if gates_clean
        else "Paid validation gates are incomplete or blocked.",
        "evidence": {
            "planned_cells_completed": completed,
            "scoreability_gate_met": enough_scoreable,
            "policy_violation_count": policy_violations,
            "cost_bounded": cost_bounded,
            "observed_or_conservative_cost_usd": metrics["observed_or_conservative_cost_usd"],
            "repo_split_pass_rates": {
                repo_split: row.get("pass_rate") for repo_split, row in sorted(per_group.items())
            },
            "b_eval_to_h_future_gap": metrics["b_eval_to_h_future_gap"],
        },
        "recommended_next_action": "Use this paid run as bounded evidence and have the coordinating session decide any follow-up runbook.",
        "followup_runbook_written_by_worker": False,
        "old_paid_result_repaired": False,
        "attrs_hist_027_old_policy_violation_repaired": False,
        "generated_statement_is_scoreable_result": False,
    }
    write_json(output_path(config, "metrics"), metrics)
    write_json(output_path(config, "decision"), decision)
    write_metrics_report(config, metrics)
    write_decision_report(config, decision)
    return metrics, decision


def gap_metrics(per_group: dict[str, Any]) -> dict[str, Any]:
    gaps: dict[str, Any] = {}
    for repo in ["attrs", "boltons"]:
        b_eval = per_group.get(f"{repo}/B_eval", {}).get("pass_rate")
        h_future = per_group.get(f"{repo}/H_future", {}).get("pass_rate")
        gaps[repo] = None if b_eval is None or h_future is None else round(b_eval - h_future, 4)
    return gaps


def write_metrics_report(config: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Paid Metrics",
        "",
        f"Status: `{metrics['status']}`.",
        "",
        f"- Total cells: `{metrics['total_cells']}` of `{metrics['planned_cells']}`.",
        f"- Scoreable cells: `{metrics['scoreable_cell_count']}`.",
        f"- Policy violations: `{metrics['policy_violation_count']}`.",
        f"- Observed-or-conservative cost: `${metrics['observed_or_conservative_cost_usd']}`.",
        f"- Adapter disagreement rate: `{metrics['adapter_disagreement_rate']}`.",
        "- Old score tables merged: `false`.",
        "",
        "## Repo Splits",
        "",
    ]
    for repo_split, row in sorted(metrics["per_repo_split"].items()):
        lines.append(
            f"- `{repo_split}`: scoreable `{row['scoreable_cell_count']}/{row['cell_count']}`, pass rate `{row['pass_rate']}`, statuses `{row['terminal_status_counts']}`."
        )
    lines.extend(["", "## Adapters", ""])
    for adapter_id, row in sorted(metrics["by_adapter"].items()):
        lines.append(
            f"- `{adapter_id}`: scoreable `{row['scoreable_cell_count']}/{row['cell_count']}`, pass rate `{row['pass_rate']}`, observed-or-conservative cost `${row.get('observed_or_conservative_cost_usd')}`, median latency `{row.get('median_latency_seconds')}` seconds."
        )
    write_text(output_path(config, "metrics_report"), "\n".join(lines))


def write_decision_report(config: dict[str, Any], decision: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Paid Decision",
        "",
        f"Primary decision: `{decision['primary_decision']}`.",
        "",
        f"- Predictive validity established: `{decision['predictive_validity_established']}`.",
        f"- Reason: {decision['reason']}",
        f"- Repo/split pass rates: `{decision['evidence'].get('repo_split_pass_rates')}`.",
        f"- B_eval to H_future gaps: `{decision['evidence'].get('b_eval_to_h_future_gap')}`.",
        f"- Recommended next action: {decision['recommended_next_action']}",
        f"- Follow-up runbook written by worker: `{decision['followup_runbook_written_by_worker']}`.",
        "- Old paid result repaired: `false`.",
        "- `attrs__hist__027` old policy violation repaired: `false`.",
    ]
    write_text(output_path(config, "decision_report"), "\n".join(lines))


def run_command(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {"returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def write_entry_gate(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    prefixes = result_prefixes(config)
    inspect_path = PHASE0_ROOT / "results" / "phase1_statement_hardened_after_canonical_repair_inspect_package_inspection.json"
    codex_path = PHASE0_ROOT / "results" / "phase1_statement_hardened_after_canonical_repair_codex_preflight_preflight.json"
    kilo_path = PHASE0_ROOT / "results" / "phase1_statement_hardened_after_canonical_repair_kilo_preflight_preflight.json"
    inspect_payload = read_json(inspect_path) if inspect_path.exists() else {}
    codex_payload = read_json(codex_path) if codex_path.exists() else {}
    kilo_payload = read_json(kilo_path) if kilo_path.exists() else {}
    existing_paid_files = sorted(
        rel(path)
        for prefix in prefixes.values()
        for path in (PHASE0_ROOT / "results").glob(f"{prefix}_*")
        if path.is_file()
    )
    endpoint_present = run_command(["zsh", "-lc", 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'])[
        "returncode"
    ] == 0
    projected_total = float(config["budget"]["conservative_cell_estimate_usd"]) * float(config["budget"]["planned_cells"])
    projected_batch = float(config["budget"]["conservative_cell_estimate_usd"]) * 8
    blockers: list[str] = []
    if inspect_payload.get("status") != "ready":
        blockers.append("package_inspection_not_ready")
    if codex_payload.get("status") != "ready":
        blockers.append("codex_preflight_not_ready")
    if kilo_payload.get("status") != "ready":
        blockers.append("kilo_preflight_not_ready")
    if not endpoint_present:
        blockers.append("endpoint_env_missing")
    if existing_paid_files:
        blockers.append("paid_prefix_outputs_already_exist")
    if projected_total > float(config["budget"]["incremental_hard_cap_usd"]):
        blockers.append("projected_total_cost_exceeds_cap")
    if projected_batch > float(config["budget"]["per_batch_projected_cap_usd"]):
        blockers.append("projected_batch_cost_exceeds_cap")
    payload = {
        "schema_version": "barcarolle.phase1_statement_hardened_paid_entry_gate.v1",
        "generated_at": iso_now(),
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "endpoint_env_present_after_zshrc": endpoint_present,
        "selected_task_ids": inspect_payload.get("selected_task_ids", []),
        "selected_task_ids_match_expected": inspect_payload.get("selected_task_ids", []) == expected_task_ids(),
        "codex_preflight_status": codex_payload.get("status"),
        "kilo_preflight_status": kilo_payload.get("status"),
        "existing_paid_prefix_files": existing_paid_files,
        "projected_incremental_cost_usd": projected_total,
        "projected_batch_cost_usd": projected_batch,
        "paid_acut_concurrency": config["workspace_runner"]["paid_acut_concurrency"],
        "allow_cross_harness_paid_parallelism": config["workspace_runner"]["allow_cross_harness_paid_parallelism"],
    }
    write_json(output_path(config, "entry_gate"), payload)
    write_entry_gate_report(config, payload)
    return payload


def write_entry_gate_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Statement-Hardened Paid Entry Gate",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Endpoint env present: `{payload['endpoint_env_present_after_zshrc']}`.",
        f"- Selected task IDs match expected: `{payload['selected_task_ids_match_expected']}`.",
        f"- Codex preflight: `{payload['codex_preflight_status']}`.",
        f"- Kilo preflight: `{payload['kilo_preflight_status']}`.",
        f"- Projected incremental cost: `${payload['projected_incremental_cost_usd']}`.",
        f"- Projected batch cost: `${payload['projected_batch_cost_usd']}`.",
        f"- Paid ACUT concurrency: `{payload['paid_acut_concurrency']}`.",
        f"- Cross-harness paid parallelism: `{payload['allow_cross_harness_paid_parallelism']}`.",
        "",
        "## Blockers",
        "",
        *(f"- `{blocker}`" for blocker in payload["blockers"]),
        "" if payload["blockers"] else "- None.",
        "",
    ]
    write_text(output_path(config, "entry_gate_report"), "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage statement-hardened paid validation artifacts.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("tooling-check")
    subcommands.add_parser("entry-gate")
    subcommands.add_parser("metrics")
    args = parser.parse_args()
    config_path = Path(args.config)
    if args.command == "tooling-check":
        validate_tooling(config_path)
    elif args.command == "entry-gate":
        write_entry_gate(config_path)
    elif args.command == "metrics":
        compute_metrics(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
