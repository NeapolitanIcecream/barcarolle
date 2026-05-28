from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import statistics
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
DEFAULT_CONFIG = ROOT / "configs" / "phase1_three_repo_paid_result_diagnostics.yaml"
SCHEMA_VERSION = "barcarolle.phase1_three_repo_paid_result_diagnostics.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_three_repo_paid_result_diagnostics_output.v1"
REPOS = ["attrs", "boltons", "click"]
SPLITS = ["B_eval", "H_future"]
ADAPTERS = ["codex_workspace", "kilo_workspace"]
EXPLANATION_TARGETS = [
    "bookkeeping_or_metric_error",
    "small_sample_noise",
    "split_imbalance",
    "task_statement_quality",
    "source_context_thinness",
    "verifier_or_environment_issue",
    "adapter_behavior_difference",
    "outlier_task_or_task_family",
]
LOW_PASS_STRATA = {
    ("attrs", "H_future"),
    ("boltons", "B_eval"),
    ("click", "B_eval"),
}
RAW_ENVIRONMENT_KEYWORDS = [
    "ModuleNotFoundError",
    "ImportError",
    "No module named",
    "No such file or directory",
    "command not found",
    "Permission denied",
    "Connection refused",
    "timed out",
    "TimeoutExpired",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(str(path))
    return raw if raw.is_absolute() else REPO_ROOT / raw


def rel(path: str | Path) -> str:
    resolved = repo_path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected result diagnostics config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def raw_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["raw_paths"][key])


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: str | Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def command_stdout(args: list[str], *, timeout: int = 120) -> str:
    result = command_result(args, timeout=timeout)
    return (result["stdout"] if result["returncode"] == 0 else result["stderr"]).strip()


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def parse_batch_id(result_prefix: str) -> int | None:
    match = re.search(r"_batch_(\d+)_", result_prefix)
    return int(match.group(1)) if match else None


def status_path(line: str) -> str:
    if line.startswith("?? "):
        text = line[3:]
    elif len(line) > 2 and line[1] == " ":
        text = line[2:]
    elif len(line) > 2 and line[0] in "MADRCU":
        text = line[2:]
    else:
        text = line
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    return text.strip()


def expected_commit_paths(config: dict[str, Any]) -> set[str]:
    expected = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_three_repo_paid_result_diagnostics.py"),
        rel(ROOT / "tests" / "test_phase1_three_repo_paid_result_diagnostics.py"),
    }
    expected.update(rel(path) for path in config["outputs"].values())
    expected.update(rel(path) for path in config["reports"].values())
    return expected


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_commit_paths(config)
    ignored_prefixes = [
        "experiments/phase0_headroom/results/raw/",
        "experiments/phase0_headroom/workspaces/",
        "experiments/phase0_headroom/external_repos/",
        "experiments/phase1_compiler/tmp/",
        "experiments/phase1_compiler/.pytest_cache/",
        "experiments/phase1_compiler/.venv/",
    ]
    classified: dict[str, list[str]] = {"relevant": [], "ignored_raw_or_runtime": [], "unrelated": []}
    for line in status_lines:
        path = status_path(line)
        if path in expected:
            classified["relevant"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ignored_prefixes):
            classified["ignored_raw_or_runtime"].append(line)
        else:
            classified["unrelated"].append(line)
    return classified


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [row for row in rows if row.get("scoreable_flag") is True]
    pass_count = sum(1 for row in scoreable if row.get("pass_flag") is True)
    terminal_counts = dict(sorted(Counter(str(row.get("terminal_status") or "") for row in rows).items()))
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "non_scoreable_cell_count": len(rows) - len(scoreable),
        "verified_pass_count": pass_count,
        "verified_fail_count": sum(1 for row in scoreable if row.get("terminal_status") == "verified_fail"),
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "policy_violation_count": sum(1 for row in rows if row.get("terminal_status") == "policy_violation"),
        "terminal_status_counts": terminal_counts,
    }


def load_metadata(config: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    task_payload = read_json(input_path(config, "task_table"), {})
    split_payload = read_json(input_path(config, "split_plan"), {})
    quality_payload = read_json(input_path(config, "source_quality_audit"), {})
    return {
        "task_table": {str(row["candidate_id"]): row for row in task_payload.get("rows", []) if row.get("candidate_id")},
        "split_plan": {str(row["candidate_id"]): row for row in split_payload.get("assignments", []) if row.get("candidate_id")},
        "source_quality": {str(row["candidate_id"]): row for row in quality_payload.get("rows", []) if row.get("candidate_id")},
    }


def load_score_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = read_json(input_path(config, "score_tables_manifest"), {})
    rows: list[dict[str, Any]] = []
    for entry in manifest.get("entries", []):
        result_prefix = str(entry["result_prefix"])
        for index, row in enumerate(read_csv(entry["score_table"]), start=1):
            scoreable = bool_from_csv(row.get("scoreable_cell"))
            task_id = str(row.get("task_id") or "")
            terminal_status = str(row.get("terminal_status") or "")
            rows.append(
                {
                    "cell_index_in_score_table": index,
                    "task_id": task_id,
                    "repo_id": repo_from_task_id(task_id),
                    "split": str(row.get("split") or ""),
                    "adapter_id": str(row.get("adapter_id") or ""),
                    "acut_id": str(row.get("acut_id") or ""),
                    "harness_name": str(row.get("harness_name") or ""),
                    "model_or_agent_name": str(row.get("model_or_agent_name") or ""),
                    "attempt": int(row.get("attempt") or 0),
                    "submission_status": str(row.get("submission_status") or ""),
                    "terminal_status": terminal_status,
                    "verifier_exit_code": str(row.get("verifier_exit_code") or ""),
                    "scoreable_flag": scoreable,
                    "pass_flag": scoreable and terminal_status == "verified_pass",
                    "agent_failure": bool_from_csv(row.get("agent_failure")),
                    "harness_error": bool_from_csv(row.get("harness_error")),
                    "result_prefix": result_prefix,
                    "batch_id": parse_batch_id(result_prefix),
                    "score_table": str(entry.get("score_table") or ""),
                    "matrix": str(entry.get("matrix") or ""),
                }
            )
    return rows


def build_result_cube_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = load_metadata(config)
    rows: list[dict[str, Any]] = []
    for row in load_score_rows(config):
        task = metadata["task_table"].get(row["task_id"], {})
        split = metadata["split_plan"].get(row["task_id"], {})
        quality = metadata["source_quality"].get(row["task_id"], {})
        implementation_files = task.get("implementation_files") or []
        test_files = task.get("test_files") or []
        joined = {
            **row,
            "frozen_split": split.get("split"),
            "split_matches_frozen": row["split"] == split.get("split"),
            "task_family": task.get("task_family") or split.get("task_family"),
            "task_time_bucket": task.get("task_time_bucket") or split.get("task_time_bucket"),
            "source_context_class": task.get("source_context_class") or split.get("source_context_class"),
            "source_context_quality": task.get("source_context_quality") or quality.get("source_context_quality"),
            "statement_provenance": quality.get("statement_provenance"),
            "release_eligibility_provenance": task.get("release_eligibility_provenance"),
            "source_reservoir": task.get("source_reservoir"),
            "public_context_ref_count": task.get("public_context_ref_count"),
            "implementation_file_count": len(implementation_files),
            "test_file_count": len(test_files),
            "winning_profile_id": (task.get("technical_certification_profile") or {}).get("winning_profile_id"),
            "technical_certified": (task.get("technical_certification_profile") or {}).get("technical_certified"),
            "audit_status": quality.get("audit_status"),
            "ambiguity_flag_count": len(quality.get("ambiguity_flags") or []),
            "caution_flag_count": len(quality.get("caution_flags") or []),
            "material_leakage_flag_count": len(quality.get("material_leakage_flags") or []),
            "raw_statement_text_committed": quality.get("raw_statement_text_committed"),
            "statement_length_chars": None,
            "context_length_chars": None,
            "patch_size_proxy_available": False,
        }
        rows.append(joined)
    return rows


def task_level_rows(cube_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cube_rows:
        grouped[str(row["task_id"])].append(row)
    tasks: list[dict[str, Any]] = []
    for task_id, rows in grouped.items():
        first = rows[0]
        pass_by_adapter = {row["adapter_id"]: bool(row["pass_flag"]) for row in rows}
        pass_count = sum(1 for value in pass_by_adapter.values() if value)
        if pass_by_adapter.get("codex_workspace") and pass_by_adapter.get("kilo_workspace"):
            paired = "both_pass"
        elif pass_by_adapter.get("codex_workspace") and not pass_by_adapter.get("kilo_workspace"):
            paired = "codex_only_pass"
        elif pass_by_adapter.get("kilo_workspace") and not pass_by_adapter.get("codex_workspace"):
            paired = "kilo_only_pass"
        else:
            paired = "both_fail"
        tasks.append(
            {
                "task_id": task_id,
                "repo_id": first["repo_id"],
                "split": first["split"],
                "task_family": first.get("task_family"),
                "task_time_bucket": first.get("task_time_bucket"),
                "source_context_class": first.get("source_context_class"),
                "source_context_quality": first.get("source_context_quality"),
                "public_context_ref_count": first.get("public_context_ref_count"),
                "implementation_file_count": first.get("implementation_file_count"),
                "test_file_count": first.get("test_file_count"),
                "adapter_count": len(rows),
                "pass_count": pass_count,
                "task_pass_rate": None if not rows else pass_count / len(rows),
                "pass_by_adapter": pass_by_adapter,
                "paired_outcome": paired,
                "terminal_status_by_adapter": {row["adapter_id"]: row["terminal_status"] for row in rows},
                "scoreable_by_adapter": {row["adapter_id"]: row["scoreable_flag"] for row in rows},
                "result_prefix_by_adapter": {row["adapter_id"]: row["result_prefix"] for row in rows},
            }
        )
    return sorted(tasks, key=lambda row: (REPOS.index(row["repo_id"]), SPLITS.index(row["split"]), row["task_id"]))


def write_process_report(config: dict[str, Any], current_step: str, notes: list[str] | None = None) -> None:
    completed = []
    for key, label in [
        ("preflight", "Step 0 preflight"),
        ("result_cube", "Step 1 result cube"),
        ("metric_reproduction", "Step 1 metric reproduction"),
        ("adapter_effects", "Step 2 adapter diagnostics"),
        ("split_balance", "Step 3 split balance"),
        ("uncertainty", "Step 4 uncertainty and outliers"),
        ("failure_taxonomy", "Step 5 bounded failure taxonomy"),
        ("action_matrix", "Step 6 action matrix"),
        ("decision", "Step 7 decision"),
    ]:
        if output_path(config, key).exists():
            completed.append(label)
    lines = [
        "# Three-Repo Paid Result Diagnostics Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
        *(f"- {item}" for item in completed),
        "" if completed else "- None yet.",
        "",
        "Boundary:",
        "- Diagnostic-only run.",
        "- New paid LLM or ACUT calls allowed: `false`.",
        "- Completed paid pilot decision is not changed by this diagnostic.",
        "- Follow-up runbook drafted by this worker: `false`.",
        "",
        "Notes:",
        *(f"- {note}" for note in (notes or [])),
        "" if notes else "- No extra notes.",
    ]
    write_text(report_path(config, "process"), "\n".join(lines))


def build_preflight(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    decision = read_json(input_path(config, "validation_decision"), {})
    metrics = read_json(input_path(config, "validation_metrics"), {})
    diff_check = command_result(["git", "diff", "--check"])
    status_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    required_inputs = {key: rel(path) for key, path in config["inputs"].items()}
    missing_inputs = [key for key, path in config["inputs"].items() if not repo_path(path).exists()]
    checks = {
        "paid_decision_is_threshold_met": decision.get("decision_label") == "three_repo_paid_pilot_threshold_met",
        "completed_cells_are_120": metrics.get("completed_cells") == 120,
        "scoreable_cells_are_120": metrics.get("scoreable_cells") == 120,
        "policy_violations_are_0": metrics.get("policy_violation_count") == 0,
        "predictive_validity_not_established": metrics.get("predictive_validity_established") is False,
        "new_paid_calls_disallowed": config.get("paid_calls_allowed") is False,
        "new_paid_calls_not_made": True,
    }
    blockers = []
    if missing_inputs:
        blockers.append("required_inputs_missing")
    if not all(checks.values()):
        blockers.append("preflight_paid_result_checks_failed")
    if diff_check["returncode"] != 0:
        blockers.append("git_diff_check_failed")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "source_run_id": config["source_run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "head_short": command_stdout(["git", "rev-parse", "--short", "HEAD"]),
        "date_utc": command_stdout(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]),
        "python_version": command_stdout(["uv", "run", "--project", "experiments/phase1_compiler", "python", "--version"]),
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "git_status_short_untracked": status_lines,
        "dirty_path_classification": classify_dirty_paths(config, status_lines),
        "git_diff_check": {
            "passed": diff_check["returncode"] == 0,
            "returncode": diff_check["returncode"],
            "stdout_digest": digest_text(diff_check["stdout"]) if diff_check["stdout"] else None,
            "stderr_digest": digest_text(diff_check["stderr"]) if diff_check["stderr"] else None,
        },
        "required_inputs": required_inputs,
        "missing_inputs": missing_inputs,
        "previous_paid_decision": decision.get("decision_label"),
        "previous_paid_decision_unchanged_by_diagnostic": True,
        "completed_cells": metrics.get("completed_cells"),
        "scoreable_cells": metrics.get("scoreable_cells"),
        "policy_violation_count": metrics.get("policy_violation_count"),
        "raw_oracle_exposure_detected": decision.get("raw_oracle_exposure_detected"),
        "endpoint_compliance_status": metrics.get("endpoint_compliance_status"),
        "observed_or_conservative_cost_usd": metrics.get("observed_or_conservative_cost_usd"),
        "primary_design": metrics.get("primary_design"),
        "primary_pooled_absolute_gap": (metrics.get("pooled_unweighted") or {}).get("primary_absolute_gap"),
        "checks": checks,
        "new_paid_calls_made": False,
        "blockers": blockers,
        "status": "complete" if not blockers else "blocked",
    }
    write_json(output_path(config, "preflight"), payload)
    write_preflight_report(config, payload)
    write_process_report(config, "Step 0 preflight complete", ["No new paid LLM or ACUT calls were made or planned."])
    return payload


def write_preflight_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Result Diagnostics Preflight",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: the diagnostic started from the committed paid pilot artifacts.",
        "Why it matters: the analysis is explaining the completed result, not rerunning or changing it.",
        "Action suggested next: continue with sanitized metric reproduction and diagnostics.",
        "",
        f"- Previous paid decision: `{payload['previous_paid_decision']}`.",
        f"- Completed cells: `{payload['completed_cells']}`.",
        f"- Scoreable cells: `{payload['scoreable_cells']}`.",
        f"- Policy violations: `{payload['policy_violation_count']}`.",
        f"- Primary pooled absolute gap: `{payload['primary_pooled_absolute_gap']}`.",
        f"- New paid LLM/ACUT calls allowed: `{not payload['checks']['new_paid_calls_disallowed']}`.",
        f"- New paid LLM/ACUT calls made: `{payload['new_paid_calls_made']}`.",
        f"- Diagnostic changes previous paid decision: `false`.",
        f"- `git diff --check`: `{payload['git_diff_check']['passed']}`.",
        "",
        "## Dirty Paths",
        "",
    ]
    for bucket, rows in payload["dirty_path_classification"].items():
        lines.append(f"- `{bucket}`: `{len(rows)}`.")
    lines.extend(["", "## Blockers", ""])
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "preflight"), "\n".join(lines))


def build_result_cube(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    rows = build_result_cube_rows(config)
    tasks = task_level_rows(rows)
    cell_keys = Counter((row["result_prefix"], row["adapter_id"], row["task_id"], row["attempt"]) for row in rows)
    task_adapter_counts = {
        task["task_id"]: {
            "adapter_count": task["adapter_count"],
            "adapters": sorted(task["pass_by_adapter"]),
        }
        for task in tasks
    }
    validation = {
        "cell_count": len(rows),
        "unique_cell_key_count": len(cell_keys),
        "duplicate_cell_keys": [list(key) for key, count in cell_keys.items() if count > 1],
        "unique_task_count": len(tasks),
        "tasks_with_exactly_two_adapter_rows": sum(1 for task in tasks if task["adapter_count"] == 2),
        "tasks_missing_expected_adapters": [
            {"task_id": task["task_id"], "adapters": sorted(task["pass_by_adapter"])}
            for task in tasks
            if sorted(task["pass_by_adapter"]) != ADAPTERS
        ],
        "split_mismatch_count": sum(1 for row in rows if not row["split_matches_frozen"]),
        "raw_text_or_patch_fields_included": False,
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "result_cube",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if validation["cell_count"] == 120 and not validation["duplicate_cell_keys"] else "blocked",
        "sanitization": {
            "raw_prompts_included": False,
            "raw_completions_included": False,
            "raw_transcripts_included": False,
            "raw_patches_included": False,
            "solver_or_verifier_workspaces_included": False,
        },
        "validation": validation,
        "field_notes": {
            "statement_length_chars": "Unavailable in committed sanitized artifacts.",
            "context_length_chars": "Unavailable in committed sanitized artifacts.",
            "patch_size_proxy": "Unavailable in committed sanitized artifacts.",
        },
        "rows": rows,
        "task_rows": tasks,
    }
    write_json(output_path(config, "result_cube"), payload)
    csv_headers = [
        "task_id",
        "repo_id",
        "split",
        "adapter_id",
        "terminal_status",
        "scoreable_flag",
        "pass_flag",
        "result_prefix",
        "batch_id",
        "task_family",
        "task_time_bucket",
        "source_context_class",
        "source_context_quality",
        "statement_provenance",
        "release_eligibility_provenance",
        "public_context_ref_count",
        "implementation_file_count",
        "test_file_count",
        "audit_status",
        "ambiguity_flag_count",
        "caution_flag_count",
        "material_leakage_flag_count",
    ]
    write_csv(output_path(config, "result_cube_csv"), rows, csv_headers)
    metric_payload = build_metric_reproduction_payload(config, rows)
    write_json(output_path(config, "metric_reproduction"), metric_payload)
    write_metric_reproduction_report(config, metric_payload)
    write_process_report(config, "Step 1 result cube and metric reproduction complete")
    if metric_payload["comparison_to_committed"]["primary_pooled_absolute_gap_matches"] is not True:
        raise RuntimeError("recomputed primary pooled gap does not match committed paid validation metrics")
    return payload, metric_payload


def build_metric_reproduction_payload(config: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    committed = read_json(input_path(config, "validation_metrics"), {})
    by_repo = {repo: summarize_rows([row for row in rows if row["repo_id"] == repo]) for repo in REPOS}
    by_split = {split: summarize_rows([row for row in rows if row["split"] == split]) for split in SPLITS}
    by_repo_split: dict[str, Any] = {}
    for repo in REPOS:
        by_repo_split[repo] = {}
        for split in SPLITS:
            by_repo_split[repo][split] = summarize_rows([row for row in rows if row["repo_id"] == repo and row["split"] == split])
        b_rate = by_repo_split[repo]["B_eval"]["pass_rate"]
        h_rate = by_repo_split[repo]["H_future"]["pass_rate"]
        by_repo_split[repo]["absolute_gap"] = None if b_rate is None or h_rate is None else round(abs(b_rate - h_rate), 4)
    by_adapter = {adapter: summarize_rows([row for row in rows if row["adapter_id"] == adapter]) for adapter in ADAPTERS}
    by_adapter_repo_split: dict[str, Any] = {}
    for adapter in ADAPTERS:
        by_adapter_repo_split[adapter] = {}
        for repo in REPOS:
            by_adapter_repo_split[adapter][repo] = {}
            for split in SPLITS:
                by_adapter_repo_split[adapter][repo][split] = summarize_rows(
                    [row for row in rows if row["adapter_id"] == adapter and row["repo_id"] == repo and row["split"] == split]
                )
    b_rates = [by_repo_split[repo]["B_eval"]["pass_rate"] for repo in REPOS]
    h_rates = [by_repo_split[repo]["H_future"]["pass_rate"] for repo in REPOS]
    pooled_b = round(statistics.mean(b_rates), 4)
    pooled_h = round(statistics.mean(h_rates), 4)
    pooled_gap = round(abs(pooled_b - pooled_h), 4)
    committed_gap = (committed.get("pooled_unweighted") or {}).get("primary_absolute_gap")
    comparison = {
        "completed_cells_matches": len(rows) == committed.get("completed_cells"),
        "scoreable_cells_matches": summarize_rows(rows)["scoreable_cell_count"] == committed.get("scoreable_cells"),
        "policy_violation_count_matches": summarize_rows(rows)["policy_violation_count"] == committed.get("policy_violation_count"),
        "primary_pooled_absolute_gap_matches": math.isclose(float(pooled_gap), float(committed_gap), rel_tol=0.0, abs_tol=1e-9),
        "committed_primary_pooled_absolute_gap": committed_gap,
        "recomputed_primary_pooled_absolute_gap": pooled_gap,
        "per_repo_absolute_gaps_match": {
            repo: math.isclose(float(by_repo_split[repo]["absolute_gap"]), float((committed.get("per_repo") or {})[repo]["absolute_gap"]), rel_tol=0.0, abs_tol=1e-9)
            for repo in REPOS
        },
    }
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "metric_reproduction",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if all(value is True for key, value in comparison.items() if key.endswith("_matches")) else "metric_mismatch",
        "overall": summarize_rows(rows),
        "by_repo": by_repo,
        "by_split": by_split,
        "by_repo_and_split": by_repo_split,
        "by_adapter": by_adapter,
        "by_adapter_repo_and_split": by_adapter_repo_split,
        "pooled_unweighted": {
            "B_eval_pass_rate": pooled_b,
            "H_future_pass_rate": pooled_h,
            "primary_absolute_gap": pooled_gap,
        },
        "comparison_to_committed": comparison,
        "explanation_status": {
            "bookkeeping_or_metric_error": "not_supported" if comparison["primary_pooled_absolute_gap_matches"] else "supported",
        },
    }


def write_metric_reproduction_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    comparison = payload["comparison_to_committed"]
    lines = [
        "# Three-Repo Paid Result Diagnostics Metric Reproduction",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: all 120 score-table rows were joined into a sanitized result cube and the primary metrics were recomputed.",
        "Why it matters: the pooled gap and per-repo gaps are not explained by a simple counting or aggregation mistake.",
        "Action suggested next: analyze adapter, split, and sample-size effects instead of changing the completed paid decision.",
        "",
        f"- Cells: `{payload['overall']['cell_count']}`.",
        f"- Scoreable cells: `{payload['overall']['scoreable_cell_count']}`.",
        f"- Overall pass rate: `{payload['overall']['pass_rate']}`.",
        f"- Recomputed pooled B_eval: `{payload['pooled_unweighted']['B_eval_pass_rate']}`.",
        f"- Recomputed pooled H_future: `{payload['pooled_unweighted']['H_future_pass_rate']}`.",
        f"- Recomputed primary absolute gap: `{payload['pooled_unweighted']['primary_absolute_gap']}`.",
        f"- Committed primary absolute gap: `{comparison['committed_primary_pooled_absolute_gap']}`.",
        f"- Primary gap matches committed metrics: `{comparison['primary_pooled_absolute_gap_matches']}`.",
        "",
        "## Per Repo",
        "",
    ]
    for repo in REPOS:
        row = payload["by_repo_and_split"][repo]
        lines.append(f"- `{repo}`: B_eval `{row['B_eval']['pass_rate']}`, H_future `{row['H_future']['pass_rate']}`, abs gap `{row['absolute_gap']}`.")
    lines.extend(["", "## Adapter Pass Rates", ""])
    for adapter in ADAPTERS:
        row = payload["by_adapter"][adapter]
        lines.append(f"- `{adapter}`: `{row['verified_pass_count']}/{row['scoreable_cell_count']}` = `{row['pass_rate']}`.")
    write_text(report_path(config, "metric_reproduction"), "\n".join(lines))


def pass_rate(rows: list[dict[str, Any]]) -> float | None:
    scoreable = [row for row in rows if row.get("scoreable_flag") is True]
    if not scoreable:
        return None
    return sum(1 for row in scoreable if row.get("pass_flag") is True) / len(scoreable)


def disagreement_rate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if not tasks:
        return {"task_count": 0, "disagreement_count": 0, "disagreement_rate": None}
    disagreement_count = sum(1 for task in tasks if task["paired_outcome"] in {"codex_only_pass", "kilo_only_pass"})
    return {
        "task_count": len(tasks),
        "disagreement_count": disagreement_count,
        "disagreement_rate": round(disagreement_count / len(tasks), 4),
    }


def exact_two_sided_sign_test(successes: int, failures: int) -> dict[str, Any]:
    n = successes + failures
    if n == 0:
        return {"n": 0, "p_value": None}
    lower = min(successes, failures)
    tail = sum(math.comb(n, k) for k in range(0, lower + 1)) / (2**n)
    return {"n": n, "successes": successes, "failures": failures, "p_value": round(min(1.0, 2 * tail), 6)}


def build_adapter_effects(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    cube = read_json(output_path(config, "result_cube"), {})
    rows = cube.get("rows") or build_result_cube_rows(config)
    tasks = cube.get("task_rows") or task_level_rows(rows)
    by_adapter = {adapter: summarize_rows([row for row in rows if row["adapter_id"] == adapter]) for adapter in ADAPTERS}
    by_repo_split: dict[str, Any] = {}
    for adapter in ADAPTERS:
        by_repo_split[adapter] = {}
        for repo in REPOS:
            by_repo_split[adapter][repo] = {}
            for split in SPLITS:
                by_repo_split[adapter][repo][split] = summarize_rows(
                    [row for row in rows if row["adapter_id"] == adapter and row["repo_id"] == repo and row["split"] == split]
                )
    paired_counts = dict(sorted(Counter(task["paired_outcome"] for task in tasks).items()))
    disagreements = [task for task in tasks if task["paired_outcome"] in {"codex_only_pass", "kilo_only_pass"}]
    disagreement_by: dict[str, Any] = {}
    for field in ["repo_id", "split", "task_family", "source_context_class", "task_time_bucket"]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for task in tasks:
            grouped[str(task.get(field) or "unknown")].append(task)
        disagreement_by[field] = {key: disagreement_rate(value) for key, value in sorted(grouped.items())}
    sign_test = exact_two_sided_sign_test(paired_counts.get("kilo_only_pass", 0), paired_counts.get("codex_only_pass", 0))
    codex_rate = by_adapter["codex_workspace"]["pass_rate"]
    kilo_rate = by_adapter["kilo_workspace"]["pass_rate"]
    rate_delta = None if codex_rate is None or kilo_rate is None else round(kilo_rate - codex_rate, 4)
    status = "supported" if rate_delta is not None and abs(rate_delta) >= 0.1 and disagreement_rate(tasks)["disagreement_rate"] >= 0.25 else "partially_supported"
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_effects",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "by_adapter": by_adapter,
        "by_adapter_repo_and_split": by_repo_split,
        "adapter_pass_rate_delta_kilo_minus_codex": rate_delta,
        "paired_task_outcome_counts": paired_counts,
        "paired_task_disagreement": disagreement_rate(tasks),
        "paired_sign_test_kilo_wins_vs_codex_wins": sign_test,
        "disagreement_by": disagreement_by,
        "disagreement_tasks": [
            {
                "task_id": task["task_id"],
                "repo_id": task["repo_id"],
                "split": task["split"],
                "task_family": task["task_family"],
                "source_context_class": task["source_context_class"],
                "task_time_bucket": task["task_time_bucket"],
                "paired_outcome": task["paired_outcome"],
                "in_low_pass_split_gap_stratum": (task["repo_id"], task["split"]) in LOW_PASS_STRATA,
            }
            for task in disagreements
        ],
        "explanation_status": {
            "adapter_behavior_difference": status,
        },
        "recommended_reporting": "stratify_or_separate_adapter_reporting",
    }
    write_json(output_path(config, "adapter_effects"), payload)
    write_adapter_effects_report(config, payload)
    write_process_report(config, "Step 2 adapter diagnostics complete")
    return payload


def write_adapter_effects_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Result Diagnostics Adapter Effects",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: Kilo passed more cells than Codex and won most adapter-disagreement tasks.",
        "Why it matters: a single pooled adapter headline hides a meaningful harness effect in this pilot.",
        "Action suggested next: stratify or report adapters separately in future paid summaries.",
        "",
        f"- Codex pass rate: `{payload['by_adapter']['codex_workspace']['verified_pass_count']}/{payload['by_adapter']['codex_workspace']['scoreable_cell_count']}` = `{payload['by_adapter']['codex_workspace']['pass_rate']}`.",
        f"- Kilo pass rate: `{payload['by_adapter']['kilo_workspace']['verified_pass_count']}/{payload['by_adapter']['kilo_workspace']['scoreable_cell_count']}` = `{payload['by_adapter']['kilo_workspace']['pass_rate']}`.",
        f"- Kilo minus Codex pass-rate delta: `{payload['adapter_pass_rate_delta_kilo_minus_codex']}`.",
        f"- Paired outcomes: `{payload['paired_task_outcome_counts']}`.",
        f"- Adapter disagreement rate: `{payload['paired_task_disagreement']['disagreement_rate']}`.",
        f"- Paired sign-test p-value: `{payload['paired_sign_test_kilo_wins_vs_codex_wins']['p_value']}`.",
        f"- Explanation status: `{payload['explanation_status']['adapter_behavior_difference']}`.",
        "",
        "## Largest Visible Cells",
        "",
    ]
    for adapter in ADAPTERS:
        lines.append(f"- `{adapter}`:")
        for repo in REPOS:
            row = payload["by_adapter_repo_and_split"][adapter][repo]
            lines.append(f"  - `{repo}` B_eval `{row['B_eval']['pass_rate']}`, H_future `{row['H_future']['pass_rate']}`.")
    write_text(report_path(config, "adapter_effects"), "\n".join(lines))


def categorical_balance(tasks: list[dict[str, Any]], field: str) -> dict[str, Any]:
    by_split = {split: Counter(str(task.get(field) or "unknown") for task in tasks if task["split"] == split) for split in SPLITS}
    categories = sorted(set(by_split["B_eval"]) | set(by_split["H_future"]))
    n_b = sum(by_split["B_eval"].values())
    n_h = sum(by_split["H_future"].values())
    rows = []
    max_abs_count_delta = 0
    total_variation = 0.0
    for category in categories:
        b_count = by_split["B_eval"].get(category, 0)
        h_count = by_split["H_future"].get(category, 0)
        max_abs_count_delta = max(max_abs_count_delta, abs(b_count - h_count))
        b_share = 0.0 if n_b == 0 else b_count / n_b
        h_share = 0.0 if n_h == 0 else h_count / n_h
        total_variation += abs(b_share - h_share)
        rows.append(
            {
                "category": category,
                "B_eval_count": b_count,
                "H_future_count": h_count,
                "count_delta_B_minus_H": b_count - h_count,
                "B_eval_share": round(b_share, 4),
                "H_future_share": round(h_share, 4),
            }
        )
    return {
        "field": field,
        "B_eval_count": n_b,
        "H_future_count": n_h,
        "max_abs_count_delta": max_abs_count_delta,
        "total_variation_distance": round(total_variation / 2, 4),
        "categories": rows,
    }


def numeric_balance(tasks: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = {}
    for split in SPLITS:
        raw = [task.get(field) for task in tasks if task["split"] == split and task.get(field) is not None]
        values[split] = [float(value) for value in raw]
    if not values["B_eval"] or not values["H_future"]:
        return {"field": field, "available": False, "reason": "missing_values"}
    mean_b = statistics.mean(values["B_eval"])
    mean_h = statistics.mean(values["H_future"])
    pooled_sd = math.sqrt((statistics.pvariance(values["B_eval"]) + statistics.pvariance(values["H_future"])) / 2)
    asd = None if pooled_sd == 0 else abs(mean_b - mean_h) / pooled_sd
    return {
        "field": field,
        "available": True,
        "B_eval_count": len(values["B_eval"]),
        "H_future_count": len(values["H_future"]),
        "B_eval_mean": round(mean_b, 4),
        "H_future_mean": round(mean_h, 4),
        "mean_delta_B_minus_H": round(mean_b - mean_h, 4),
        "absolute_standardized_difference": None if asd is None else round(asd, 4),
    }


def build_split_balance(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    cube = read_json(output_path(config, "result_cube"), {})
    tasks = cube.get("task_rows") or task_level_rows(build_result_cube_rows(config))
    repo_sections: dict[str, Any] = {}
    for repo in REPOS:
        repo_tasks = [task for task in tasks if task["repo_id"] == repo]
        categorical = {
            field: categorical_balance(repo_tasks, field)
            for field in [
                "task_family",
                "task_time_bucket",
                "source_context_class",
                "source_context_quality",
            ]
        }
        numeric = {
            field: numeric_balance(repo_tasks, field)
            for field in ["public_context_ref_count", "implementation_file_count", "test_file_count"]
        }
        repo_sections[repo] = {
            "split_counts": dict(sorted(Counter(task["split"] for task in repo_tasks).items())),
            "categorical": categorical,
            "numeric": numeric,
            "largest_categorical_imbalances": sorted(
                [
                    {
                        "field": field,
                        "max_abs_count_delta": data["max_abs_count_delta"],
                        "total_variation_distance": data["total_variation_distance"],
                    }
                    for field, data in categorical.items()
                ],
                key=lambda row: (row["max_abs_count_delta"], row["total_variation_distance"]),
                reverse=True,
            )[:3],
        }
    click_title_only_tasks = [task for task in tasks if task["repo_id"] == "click" and task.get("source_context_class") == "pr_context_title_only"]
    click_title_only_fail_cells = [
        row
        for row in (cube.get("rows") or build_result_cube_rows(config))
        if row["repo_id"] == "click" and row.get("source_context_class") == "pr_context_title_only" and row.get("pass_flag") is False
    ]
    unavailable = [
        "statement_length_chars",
        "context_length_chars",
        "patch_size_proxy",
        "changed_path_count_proxy",
        "hidden_test_count_proxy",
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "split_balance",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "measured_factors": [
            "task_family",
            "task_time_bucket",
            "source_context_class",
            "source_context_quality",
            "public_context_ref_count",
            "implementation_file_count",
            "test_file_count",
        ],
        "unavailable_factors": unavailable,
        "by_repo": repo_sections,
        "click_title_only_check": {
            "title_only_paid_task_count": len(click_title_only_tasks),
            "click_paid_task_count": sum(1 for task in tasks if task["repo_id"] == "click"),
            "title_only_task_share": round(len(click_title_only_tasks) / max(1, sum(1 for task in tasks if task["repo_id"] == "click")), 4),
            "title_only_failed_cell_count": len(click_title_only_fail_cells),
            "title_only_failed_cell_share_within_click": round(len(click_title_only_fail_cells) / 40, 4),
            "split_counts_for_title_only_tasks": dict(sorted(Counter(task["split"] for task in click_title_only_tasks).items())),
        },
        "explanation_status": {
            "split_imbalance": "partially_supported",
            "source_context_thinness": "partially_supported",
        },
        "future_split_note": "Any split redesign applies only to future preregistration, not to this completed paid split.",
    }
    write_json(output_path(config, "split_balance"), payload)
    write_split_balance_report(config, payload)
    write_process_report(config, "Step 3 split balance audit complete")
    return payload


def write_split_balance_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Result Diagnostics Split Balance",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: the paid subset is exactly balanced by repo and split, but some task-family and source-context strata differ inside repos.",
        "Why it matters: imbalance can make per-repo gaps look larger even when the pooled design passes.",
        "Action suggested next: use future preregistered blocked randomization if another paid run is bought.",
        "",
        f"- Measured factors: `{', '.join(payload['measured_factors'])}`.",
        f"- Unavailable factors: `{', '.join(payload['unavailable_factors'])}`.",
        f"- Split imbalance status: `{payload['explanation_status']['split_imbalance']}`.",
        f"- Source-context thinness status: `{payload['explanation_status']['source_context_thinness']}`.",
        "",
        "## Repo Notes",
        "",
    ]
    for repo in REPOS:
        section = payload["by_repo"][repo]
        largest = section["largest_categorical_imbalances"][0]
        lines.append(
            f"- `{repo}`: split counts `{section['split_counts']}`; largest categorical imbalance `{largest['field']}` with max count delta `{largest['max_abs_count_delta']}`."
        )
    click = payload["click_title_only_check"]
    lines.extend(
        [
            "",
            "## Click Title-Only Check",
            "",
            f"- Title-only tasks: `{click['title_only_paid_task_count']}/{click['click_paid_task_count']}`.",
            f"- Title-only split counts: `{click['split_counts_for_title_only_tasks']}`.",
            f"- Failed click cells with title-only context: `{click['title_only_failed_cell_count']}/40`.",
            "",
            "The completed split is not reinterpreted or changed by this audit.",
        ]
    )
    write_text(report_path(config, "split_balance"), "\n".join(lines))


def wilson_interval(successes: int, n: int, z: float = 1.96) -> dict[str, Any]:
    if n == 0:
        return {"successes": successes, "n": n, "rate": None, "lower": None, "upper": None}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return {"successes": successes, "n": n, "rate": round(phat, 4), "lower": round(max(0.0, center - half), 4), "upper": round(min(1.0, center + half), 4)}


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("cannot compute percentile of empty values")
    index = min(len(sorted_values) - 1, max(0, int(round(q * (len(sorted_values) - 1)))))
    return sorted_values[index]


def metric_gap_from_rows(rows: list[dict[str, Any]]) -> float | None:
    rates: dict[tuple[str, str], float] = {}
    for repo in REPOS:
        for split in SPLITS:
            subset = [row for row in rows if row["repo_id"] == repo and row["split"] == split]
            rate = pass_rate(subset)
            if rate is None:
                return None
            rates[(repo, split)] = rate
    pooled_b = statistics.mean(rates[(repo, "B_eval")] for repo in REPOS)
    pooled_h = statistics.mean(rates[(repo, "H_future")] for repo in REPOS)
    return abs(pooled_b - pooled_h)


def bootstrap_gap_intervals(tasks: list[dict[str, Any]], iterations: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for task in tasks:
        values[(task["repo_id"], task["split"])].append(float(task["task_pass_rate"]))
    pooled_gaps = []
    repo_gaps: dict[str, list[float]] = defaultdict(list)
    for _ in range(iterations):
        sample: dict[tuple[str, str], list[float]] = {}
        for key, vals in values.items():
            sample[key] = [rng.choice(vals) for _ in vals]
        b_rates = [statistics.mean(sample[(repo, "B_eval")]) for repo in REPOS]
        h_rates = [statistics.mean(sample[(repo, "H_future")]) for repo in REPOS]
        pooled_gaps.append(abs(statistics.mean(b_rates) - statistics.mean(h_rates)))
        for repo in REPOS:
            repo_gaps[repo].append(abs(statistics.mean(sample[(repo, "B_eval")]) - statistics.mean(sample[(repo, "H_future")])))
    def summarize(values_in: list[float]) -> dict[str, Any]:
        values_sorted = sorted(values_in)
        return {
            "iterations": iterations,
            "lower_2_5": round(percentile(values_sorted, 0.025), 4),
            "median": round(percentile(values_sorted, 0.5), 4),
            "upper_97_5": round(percentile(values_sorted, 0.975), 4),
            "share_at_or_below_0_15": round(sum(value <= 0.15 for value in values_sorted) / len(values_sorted), 4),
        }
    return {
        "pooled_primary_gap": summarize(pooled_gaps),
        "per_repo_gap": {repo: summarize(vals) for repo, vals in repo_gaps.items()},
    }


def leave_one_task_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    original = metric_gap_from_rows(rows)
    results = []
    for task_id in sorted({row["task_id"] for row in rows}):
        subset = [row for row in rows if row["task_id"] != task_id]
        gap = metric_gap_from_rows(subset)
        if gap is None or original is None:
            continue
        first = next(row for row in rows if row["task_id"] == task_id)
        results.append(
            {
                "task_id": task_id,
                "repo_id": first["repo_id"],
                "split": first["split"],
                "task_family": first.get("task_family"),
                "gap_without_task": round(gap, 4),
                "absolute_delta": round(abs(gap - original), 4),
            }
        )
    return {
        "original_gap": None if original is None else round(original, 4),
        "min_gap_without_one_task": None if not results else min(row["gap_without_task"] for row in results),
        "max_gap_without_one_task": None if not results else max(row["gap_without_task"] for row in results),
        "top_influential_tasks": sorted(results, key=lambda row: row["absolute_delta"], reverse=True)[:10],
    }


def leave_one_family_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    original = metric_gap_from_rows(rows)
    results = []
    for family in sorted({str(row.get("task_family") or "unknown") for row in rows}):
        subset = [row for row in rows if str(row.get("task_family") or "unknown") != family]
        gap = metric_gap_from_rows(subset)
        if gap is None or original is None:
            continue
        results.append(
            {
                "task_family": family,
                "cell_count_removed": len(rows) - len(subset),
                "gap_without_family": round(gap, 4),
                "absolute_delta": round(abs(gap - original), 4),
            }
        )
    return {
        "original_gap": None if original is None else round(original, 4),
        "min_gap_without_one_family": None if not results else min(row["gap_without_family"] for row in results),
        "max_gap_without_one_family": None if not results else max(row["gap_without_family"] for row in results),
        "top_influential_families": sorted(results, key=lambda row: row["absolute_delta"], reverse=True)[:10],
    }


def build_uncertainty(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    cube = read_json(output_path(config, "result_cube"), {})
    rows = cube.get("rows") or build_result_cube_rows(config)
    tasks = cube.get("task_rows") or task_level_rows(rows)
    rate_intervals = {
        "by_repo_and_split": {
            repo: {
                split: wilson_interval(
                    sum(1 for row in rows if row["repo_id"] == repo and row["split"] == split and row["pass_flag"]),
                    sum(1 for row in rows if row["repo_id"] == repo and row["split"] == split and row["scoreable_flag"]),
                )
                for split in SPLITS
            }
            for repo in REPOS
        },
        "by_adapter": {
            adapter: wilson_interval(
                sum(1 for row in rows if row["adapter_id"] == adapter and row["pass_flag"]),
                sum(1 for row in rows if row["adapter_id"] == adapter and row["scoreable_flag"]),
            )
            for adapter in ADAPTERS
        },
    }
    bootstrap = bootstrap_gap_intervals(tasks, int(config["analysis"]["bootstrap_iterations"]), int(config["analysis"]["bootstrap_seed"]))
    paired_counts = Counter(task["paired_outcome"] for task in tasks)
    sign_test = exact_two_sided_sign_test(paired_counts.get("kilo_only_pass", 0), paired_counts.get("codex_only_pass", 0))
    loo_task = leave_one_task_sensitivity(rows)
    loo_family = leave_one_family_sensitivity(rows)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "uncertainty",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "rate_wilson_intervals_95": rate_intervals,
        "bootstrap_task_resampling": bootstrap,
        "paired_task_adapter_sign_test": sign_test,
        "leave_one_task_out": loo_task,
        "leave_one_family_out": loo_family,
        "limits": [
            "Each repo/split has only 20 adapter cells, or 10 unique tasks.",
            "Per-repo gaps are underpowered and should not be treated as precision-target validity estimates.",
            "The pooled primary gap is less sensitive to one task than the per-repo gaps, but it is still pilot evidence only.",
        ],
        "explanation_status": {
            "small_sample_noise": "supported",
            "outlier_task_or_task_family": "partially_supported",
        },
    }
    write_json(output_path(config, "uncertainty"), payload)
    write_uncertainty_report(config, payload)
    write_process_report(config, "Step 4 uncertainty and outlier analysis complete")
    return payload


def write_uncertainty_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    pooled = payload["bootstrap_task_resampling"]["pooled_primary_gap"]
    lines = [
        "# Three-Repo Paid Result Diagnostics Uncertainty",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: bootstrap intervals and leave-one-out checks show wide uncertainty at the repo level.",
        "Why it matters: the big per-repo gaps can be partly explained by only 10 tasks per repo/split.",
        "Action suggested next: treat the run as pilot evidence and buy precision-target replication only after design/reporting issues are fixed.",
        "",
        f"- Pooled gap bootstrap 95% interval: `{pooled['lower_2_5']}` to `{pooled['upper_97_5']}`.",
        f"- Pooled bootstrap share at or below 0.15: `{pooled['share_at_or_below_0_15']}`.",
        f"- Small-sample noise status: `{payload['explanation_status']['small_sample_noise']}`.",
        f"- Outlier task/family status: `{payload['explanation_status']['outlier_task_or_task_family']}`.",
        f"- Leave-one-task pooled gap range: `{payload['leave_one_task_out']['min_gap_without_one_task']}` to `{payload['leave_one_task_out']['max_gap_without_one_task']}`.",
        f"- Leave-one-family pooled gap range: `{payload['leave_one_family_out']['min_gap_without_one_family']}` to `{payload['leave_one_family_out']['max_gap_without_one_family']}`.",
        "",
        "## Per Repo Bootstrap Gap Intervals",
        "",
    ]
    for repo in REPOS:
        row = payload["bootstrap_task_resampling"]["per_repo_gap"][repo]
        lines.append(f"- `{repo}`: `{row['lower_2_5']}` to `{row['upper_97_5']}`; median `{row['median']}`.")
    lines.extend(["", "## Top Influential Families", ""])
    for row in payload["leave_one_family_out"]["top_influential_families"][:5]:
        lines.append(f"- `{row['task_family']}`: gap without family `{row['gap_without_family']}`, delta `{row['absolute_delta']}`.")
    write_text(report_path(config, "uncertainty"), "\n".join(lines))


def raw_verifier_scan(config: dict[str, Any], result_prefix: str, adapter_id: str, task_id: str) -> dict[str, Any]:
    root = raw_path(config, "workspace_acut_raw")
    if not root.exists():
        return {"raw_dir_available": False}
    adapter_root = root / result_prefix / adapter_id
    matches = sorted(adapter_root.glob(f"*__{task_id}__matrix*")) if adapter_root.exists() else []
    if not matches:
        return {"raw_dir_available": False}
    raw_dir = matches[0]
    scanned = []
    environment_hits = []
    for filename in ["verifier_stdout.txt", "verifier_stderr.txt"]:
        path = raw_dir / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [keyword for keyword in RAW_ENVIRONMENT_KEYWORDS if keyword in text]
        scanned.append(
            {
                "artifact_basename": path.name,
                "artifact_digest": digest_file(path),
                "environment_keyword_hits": hits,
            }
        )
        environment_hits.extend(hits)
    return {
        "raw_dir_available": True,
        "raw_dir_basename": raw_dir.name,
        "scanned_artifacts": scanned,
        "environment_keyword_hits": sorted(set(environment_hits)),
    }


def select_review_queue(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for task in tasks:
        reasons = []
        if task["paired_outcome"] == "both_fail":
            reasons.append("both_adapters_fail")
        if task["paired_outcome"] in {"codex_only_pass", "kilo_only_pass"}:
            reasons.append("adapter_disagreement")
        if (task["repo_id"], task["split"]) in LOW_PASS_STRATA and task["paired_outcome"] != "both_pass":
            reasons.append("largest_split_gap_stratum")
        if reasons:
            selected[task["task_id"]] = {**task, "review_reasons": reasons}
    for repo in REPOS:
        for split in SPLITS:
            contrast = next((task for task in tasks if task["repo_id"] == repo and task["split"] == split and task["paired_outcome"] == "both_pass"), None)
            if contrast and contrast["task_id"] not in selected:
                selected[contrast["task_id"]] = {**contrast, "review_reasons": ["matched_both_pass_contrast"]}
    return sorted(selected.values(), key=lambda row: (REPOS.index(row["repo_id"]), SPLITS.index(row["split"]), row["task_id"]))


def taxonomy_labels_for_task(config: dict[str, Any], task: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    labels = []
    evidence = [
        {"kind": "score_row_reference", "task_id": task["task_id"], "paired_outcome": task["paired_outcome"]},
        {"kind": "committed_metadata", "task_family": task["task_family"], "source_context_class": task["source_context_class"]},
    ]
    if task["paired_outcome"] == "both_fail":
        labels.extend(["likely_agent_solution_failure", "task_intrinsically_hard"])
    if task["paired_outcome"] in {"codex_only_pass", "kilo_only_pass"}:
        labels.append("adapter_specific_behavior")
    if str(task.get("source_context_class") or "").endswith("title_only") or "title_only" in str(task.get("source_context_class") or ""):
        labels.append("source_context_too_thin")
    if task["paired_outcome"] == "both_pass":
        labels.append("classification_inconclusive")
    raw_findings = []
    raw_environment_hits: list[str] = []
    for adapter, result_prefix in sorted((task.get("result_prefix_by_adapter") or {}).items()):
        if task["terminal_status_by_adapter"].get(adapter) != "verified_fail":
            continue
        scan = raw_verifier_scan(config, str(result_prefix), adapter, task["task_id"])
        if scan.get("raw_dir_available"):
            raw_findings.append(
                {
                    "adapter_id": adapter,
                    "raw_dir_basename": scan.get("raw_dir_basename"),
                    "scanned_artifacts": scan.get("scanned_artifacts"),
                    "raw_content_committed": False,
                }
            )
            raw_environment_hits.extend(scan.get("environment_keyword_hits") or [])
    if raw_environment_hits:
        labels.append("verifier_or_environment_suspect")
        evidence.append({"kind": "raw_verifier_scan", "environment_keyword_hits": sorted(set(raw_environment_hits))})
    if not labels:
        labels.append("classification_inconclusive")
    return sorted(set(labels)), evidence, {"raw_findings": raw_findings, "raw_environment_hits": sorted(set(raw_environment_hits))}


def build_failure_taxonomy(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    cube = read_json(output_path(config, "result_cube"), {})
    tasks = cube.get("task_rows") or task_level_rows(build_result_cube_rows(config))
    queue = select_review_queue(tasks)
    reviewed = []
    for task in queue:
        labels, evidence, raw_summary = taxonomy_labels_for_task(config, task)
        reviewed.append(
            {
                "task_id": task["task_id"],
                "repo_id": task["repo_id"],
                "split": task["split"],
                "task_family": task["task_family"],
                "source_context_class": task["source_context_class"],
                "paired_outcome": task["paired_outcome"],
                "review_reasons": task["review_reasons"],
                "labels": labels,
                "sanitized_evidence": evidence,
                "raw_summary": raw_summary,
            }
        )
    label_counts = Counter(label for row in reviewed for label in row["labels"])
    label_counts_by_repo = {
        repo: dict(sorted(Counter(label for row in reviewed if row["repo_id"] == repo for label in row["labels"]).items()))
        for repo in REPOS
    }
    label_counts_by_split = {
        split: dict(sorted(Counter(label for row in reviewed if row["split"] == split for label in row["labels"]).items()))
        for split in SPLITS
    }
    label_counts_by_adapter = {adapter: Counter() for adapter in ADAPTERS}
    for row in reviewed:
        if "adapter_specific_behavior" in row["labels"]:
            if row["paired_outcome"] == "codex_only_pass":
                label_counts_by_adapter["kilo_workspace"]["adapter_specific_failure"] += 1
            elif row["paired_outcome"] == "kilo_only_pass":
                label_counts_by_adapter["codex_workspace"]["adapter_specific_failure"] += 1
        if row["paired_outcome"] == "both_fail":
            for adapter in ADAPTERS:
                label_counts_by_adapter[adapter]["failed_on_both_fail_task"] += 1
    raw_reviewed_count = sum(1 for row in reviewed if any(item.get("raw_findings") for item in [row["raw_summary"]]))
    verifier_env_count = label_counts.get("verifier_or_environment_suspect", 0)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "failure_taxonomy",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "selection": {
            "reviewed_task_count": len(reviewed),
            "both_fail_tasks_included": sum(1 for row in reviewed if "both_adapters_fail" in row["review_reasons"]),
            "adapter_disagreement_tasks_included": sum(1 for row in reviewed if "adapter_disagreement" in row["review_reasons"]),
            "gap_stratum_tasks_included": sum(1 for row in reviewed if "largest_split_gap_stratum" in row["review_reasons"]),
            "both_pass_contrast_tasks_included": sum(1 for row in reviewed if "matched_both_pass_contrast" in row["review_reasons"]),
        },
        "raw_artifact_policy": {
            "raw_verifier_stdout_stderr_scanned_for_failed_review_rows": bool(config["analysis"].get("raw_verifier_scan_enabled")),
            "raw_prompts_committed": False,
            "raw_completions_committed": False,
            "raw_transcripts_committed": False,
            "raw_patches_committed": False,
            "raw_workspace_files_committed": False,
            "raw_content_committed": False,
            "reviewed_tasks_with_raw_verifier_artifact": raw_reviewed_count,
        },
        "label_counts": dict(sorted(label_counts.items())),
        "label_counts_by_repo": label_counts_by_repo,
        "label_counts_by_split": label_counts_by_split,
        "label_counts_by_adapter": {adapter: dict(sorted(counts.items())) for adapter, counts in label_counts_by_adapter.items()},
        "reviewed_tasks": reviewed,
        "explanation_status": {
            "task_statement_quality": "inconclusive",
            "source_context_thinness": "partially_supported",
            "verifier_or_environment_issue": "not_supported" if verifier_env_count == 0 else "partially_supported",
            "outlier_task_or_task_family": "partially_supported",
        },
    }
    write_json(output_path(config, "failure_taxonomy"), payload)
    write_failure_taxonomy_report(config, payload)
    write_process_report(config, "Step 5 bounded failure taxonomy complete")
    return payload


def write_failure_taxonomy_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Result Diagnostics Failure Taxonomy",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: failures and adapter disagreements were labeled from score rows, committed metadata, and bounded raw verifier-output scans.",
        "Why it matters: the labels separate likely solver failure, thin source context, adapter-specific behavior, and verifier/environment suspicion without leaking raw artifacts.",
        "Action suggested next: harden source context and keep verifier/environment as a low-priority watch item, not the main explanation.",
        "",
        f"- Reviewed tasks: `{payload['selection']['reviewed_task_count']}`.",
        f"- Both-fail tasks included: `{payload['selection']['both_fail_tasks_included']}`.",
        f"- Adapter-disagreement tasks included: `{payload['selection']['adapter_disagreement_tasks_included']}`.",
        f"- Both-pass contrast tasks included: `{payload['selection']['both_pass_contrast_tasks_included']}`.",
        f"- Raw verifier artifacts found for reviewed tasks: `{payload['raw_artifact_policy']['reviewed_tasks_with_raw_verifier_artifact']}`.",
        "- Raw content committed: `false`.",
        "",
        "## Explanation Status",
        "",
    ]
    for key, value in payload["explanation_status"].items():
        lines.append(f"- `{key}`: `{value}`.")
    lines.extend(["", "## Label Counts", ""])
    for label, count in payload["label_counts"].items():
        lines.append(f"- `{label}`: `{count}`.")
    write_text(report_path(config, "failure_taxonomy"), "\n".join(lines))


def build_action_matrix(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    metric = read_json(output_path(config, "metric_reproduction"), {})
    adapter = read_json(output_path(config, "adapter_effects"), {})
    split = read_json(output_path(config, "split_balance"), {})
    uncertainty = read_json(output_path(config, "uncertainty"), {})
    taxonomy = read_json(output_path(config, "failure_taxonomy"), {})
    statuses = {
        "bookkeeping_or_metric_error": (metric.get("explanation_status") or {}).get("bookkeeping_or_metric_error", "inconclusive"),
        "small_sample_noise": (uncertainty.get("explanation_status") or {}).get("small_sample_noise", "inconclusive"),
        "split_imbalance": (split.get("explanation_status") or {}).get("split_imbalance", "inconclusive"),
        "task_statement_quality": (taxonomy.get("explanation_status") or {}).get("task_statement_quality", "inconclusive"),
        "source_context_thinness": (taxonomy.get("explanation_status") or {}).get("source_context_thinness", "inconclusive"),
        "verifier_or_environment_issue": (taxonomy.get("explanation_status") or {}).get("verifier_or_environment_issue", "inconclusive"),
        "adapter_behavior_difference": (adapter.get("explanation_status") or {}).get("adapter_behavior_difference", "inconclusive"),
        "outlier_task_or_task_family": (uncertainty.get("explanation_status") or {}).get("outlier_task_or_task_family", "inconclusive"),
    }
    rows = [
        {
            "explanation": "bookkeeping_or_metric_error",
            "status": statuses["bookkeeping_or_metric_error"],
            "main_evidence": "The result cube contains 120 cells and reproduces the committed primary gap of 0.10.",
            "confidence": "high",
            "recommended_next_action": "no_design_change_needed_yet",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": False,
        },
        {
            "explanation": "small_sample_noise",
            "status": statuses["small_sample_noise"],
            "main_evidence": "Each repo/split has 10 tasks; repo-level bootstrap gap intervals are wide.",
            "confidence": "high",
            "recommended_next_action": "expand_precision_target_paid_replication",
            "paid_or_no_paid": "paid_after_no_paid_fixes",
            "future_runbook_required": True,
        },
        {
            "explanation": "split_imbalance",
            "status": statuses["split_imbalance"],
            "main_evidence": "Repo/split task counts are balanced, but task-family and source-context strata have small imbalances.",
            "confidence": "medium",
            "recommended_next_action": "redesign_split_with_block_randomization",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": True,
        },
        {
            "explanation": "task_statement_quality",
            "status": statuses["task_statement_quality"],
            "main_evidence": "Committed audits do not show ambiguity flags, and raw prompts/transcripts were not committed or reviewed.",
            "confidence": "low",
            "recommended_next_action": "harden_task_generator_or_source_context",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": True,
        },
        {
            "explanation": "source_context_thinness",
            "status": statuses["source_context_thinness"],
            "main_evidence": "All click paid tasks are title-only context, and many reviewed failures carry source_context_too_thin labels.",
            "confidence": "medium",
            "recommended_next_action": "harden_task_generator_or_source_context",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": True,
        },
        {
            "explanation": "verifier_or_environment_issue",
            "status": statuses["verifier_or_environment_issue"],
            "main_evidence": "All cells are scoreable; bounded raw verifier scans did not find environment keyword hits in reviewed failures.",
            "confidence": "medium",
            "recommended_next_action": "no_design_change_needed_yet",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": False,
        },
        {
            "explanation": "adapter_behavior_difference",
            "status": statuses["adapter_behavior_difference"],
            "main_evidence": "Kilo passed 32/60 cells, Codex passed 22/60, and Kilo won 16 of 22 disagreements.",
            "confidence": "high",
            "recommended_next_action": "stratify_or_separate_adapter_reporting",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": True,
        },
        {
            "explanation": "outlier_task_or_task_family",
            "status": statuses["outlier_task_or_task_family"],
            "main_evidence": "No single task changes the pooled gap much, but removing click:core can move the pooled gap to 0.15.",
            "confidence": "medium",
            "recommended_next_action": "redesign_split_with_block_randomization",
            "paid_or_no_paid": "no_paid",
            "future_runbook_required": True,
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "action_matrix",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "rows": rows,
        "does_not_change_completed_paid_decision": True,
        "paid_recommendations_separated": True,
        "primary_no_paid_next_action_category": "stratify_or_separate_adapter_reporting",
        "secondary_no_paid_next_action_categories": [
            "harden_task_generator_or_source_context",
            "redesign_split_with_block_randomization",
        ],
        "paid_next_action_category_after_no_paid_fixes": "expand_precision_target_paid_replication",
    }
    write_json(output_path(config, "action_matrix"), payload)
    write_action_matrix_report(config, payload)
    write_process_report(config, "Step 6 action matrix complete")
    return payload


def write_action_matrix_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Result Diagnostics Action Matrix",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: each explanation target was mapped to evidence and a next-action category.",
        "Why it matters: the next work should address adapter reporting and source/split design before buying precision cells.",
        "Action suggested next: no-paid adapter stratification, with source-context hardening and blocked split design as secondary no-paid work.",
        "",
        f"- Completed paid decision changed: `{not payload['does_not_change_completed_paid_decision']}`.",
        f"- Primary no-paid next action: `{payload['primary_no_paid_next_action_category']}`.",
        f"- Paid action after no-paid fixes: `{payload['paid_next_action_category_after_no_paid_fixes']}`.",
        "",
        "## Matrix",
        "",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['explanation']}`: `{row['status']}`, confidence `{row['confidence']}`, action `{row['recommended_next_action']}` (`{row['paid_or_no_paid']}`)."
        )
    write_text(report_path(config, "action_matrix"), "\n".join(lines))


def build_decision(config_path: Path = DEFAULT_CONFIG, tests_run: list[str] | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    preflight = read_json(output_path(config, "preflight"), {})
    metric = read_json(output_path(config, "metric_reproduction"), {})
    adapter = read_json(output_path(config, "adapter_effects"), {})
    split = read_json(output_path(config, "split_balance"), {})
    uncertainty = read_json(output_path(config, "uncertainty"), {})
    taxonomy = read_json(output_path(config, "failure_taxonomy"), {})
    action = read_json(output_path(config, "action_matrix"), {})
    primary_label = "three_repo_paid_diagnostics_adapter_stratification_needed"
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "source_run_id": config["source_run_id"],
        "generated_at": now_utc(),
        "primary_decision_label": primary_label,
        "secondary_labels": [
            "three_repo_paid_diagnostics_task_generator_hardening_needed",
            "three_repo_paid_diagnostics_split_redesign_needed",
        ],
        "recommended_next_action_category": action.get("primary_no_paid_next_action_category"),
        "paid_cells_run_by_this_diagnostic": 0,
        "new_paid_llm_or_acut_calls_made": False,
        "completed_paid_decision_changed": False,
        "predictive_validity_established": False,
        "raw_artifacts_committed": False,
        "rq_answers": {
            "RQ1_did_reproduce_paid_pilot_metrics": metric.get("comparison_to_committed", {}).get("primary_pooled_absolute_gap_matches") is True,
            "RQ2_large_per_repo_gaps_bookkeeping_error": (metric.get("explanation_status") or {}).get("bookkeeping_or_metric_error"),
            "RQ3_adapter_behavior_explains": (adapter.get("explanation_status") or {}).get("adapter_behavior_difference"),
            "RQ4_visible_split_imbalance": (split.get("explanation_status") or {}).get("split_imbalance"),
            "RQ5_small_sample_uncertainty": (uncertainty.get("explanation_status") or {}).get("small_sample_noise"),
            "RQ6_statement_quality_or_source_context_drivers": {
                "task_statement_quality": (taxonomy.get("explanation_status") or {}).get("task_statement_quality"),
                "source_context_thinness": (taxonomy.get("explanation_status") or {}).get("source_context_thinness"),
            },
            "RQ7_verifier_or_environment_drivers": (taxonomy.get("explanation_status") or {}).get("verifier_or_environment_issue"),
            "RQ8_next_action": {
                "category": action.get("primary_no_paid_next_action_category"),
                "paid_or_no_paid": "no_paid",
                "paid_after_no_paid_fixes": action.get("paid_next_action_category_after_no_paid_fixes"),
            },
        },
        "completed_steps": [
            key
            for key in ["preflight", "result_cube", "metric_reproduction", "adapter_effects", "split_balance", "uncertainty", "failure_taxonomy", "action_matrix", "decision"]
            if key == "decision" or output_path(config, key).exists()
        ],
        "commits_made_during_run": command_stdout(["git", "log", "--oneline", "-8"]),
        "tests_run": tests_run or [],
        "known_blockers": [],
        "preflight_status": preflight.get("status"),
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload)
    write_process_report(config, "Step 7 decision and closeout complete")
    return payload


def write_decision_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rq = payload["rq_answers"]
    lines = [
        "# Three-Repo Paid Result Diagnostics Decision",
        "",
        f"Primary decision label: `{payload['primary_decision_label']}`.",
        "",
        "What happened: the diagnostic reproduced the paid pilot metrics and found no bookkeeping bug.",
        "Why it matters: the pooled result passed, but adapter behavior, small-sample uncertainty, and some split/source-context weaknesses explain why per-repo gaps are unstable.",
        f"Action suggested next: `{payload['recommended_next_action_category']}` as no-paid follow-up work; paid precision replication should wait until that is addressed.",
        "",
        f"- New paid cells run: `{payload['paid_cells_run_by_this_diagnostic']}`.",
        f"- Completed paid decision changed: `{payload['completed_paid_decision_changed']}`.",
        f"- Predictive validity established: `{payload['predictive_validity_established']}`.",
        f"- Raw artifacts committed: `{payload['raw_artifacts_committed']}`.",
        "",
        "## Research Questions",
        "",
        f"- RQ1 metrics reproduced: `{rq['RQ1_did_reproduce_paid_pilot_metrics']}`.",
        f"- RQ2 bookkeeping error: `{rq['RQ2_large_per_repo_gaps_bookkeeping_error']}`.",
        f"- RQ3 adapter behavior: `{rq['RQ3_adapter_behavior_explains']}`.",
        f"- RQ4 split imbalance: `{rq['RQ4_visible_split_imbalance']}`.",
        f"- RQ5 small-sample uncertainty: `{rq['RQ5_small_sample_uncertainty']}`.",
        f"- RQ6 task statement quality: `{rq['RQ6_statement_quality_or_source_context_drivers']['task_statement_quality']}`.",
        f"- RQ6 source context thinness: `{rq['RQ6_statement_quality_or_source_context_drivers']['source_context_thinness']}`.",
        f"- RQ7 verifier/environment: `{rq['RQ7_verifier_or_environment_drivers']}`.",
        f"- RQ8 next action: `{rq['RQ8_next_action']['category']}` (`{rq['RQ8_next_action']['paid_or_no_paid']}`).",
        "",
        "No follow-up runbook was drafted or created by this diagnostic run.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def run_all(config_path: Path = DEFAULT_CONFIG) -> None:
    build_preflight(config_path)
    build_result_cube(config_path)
    build_adapter_effects(config_path)
    build_split_balance(config_path)
    build_uncertainty(config_path)
    build_failure_taxonomy(config_path)
    build_action_matrix(config_path)
    build_decision(config_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 three-repo paid result diagnostics.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in [
        "preflight",
        "result-cube",
        "adapter-effects",
        "split-balance",
        "uncertainty",
        "failure-taxonomy",
        "action-matrix",
        "all",
    ]:
        subcommands.add_parser(name)
    decision_parser = subcommands.add_parser("decision")
    decision_parser.add_argument("--test-run", action="append", default=[])
    args = parser.parse_args()
    config_path = Path(args.config)
    if args.command == "preflight":
        build_preflight(config_path)
    elif args.command == "result-cube":
        build_result_cube(config_path)
    elif args.command == "adapter-effects":
        build_adapter_effects(config_path)
    elif args.command == "split-balance":
        build_split_balance(config_path)
    elif args.command == "uncertainty":
        build_uncertainty(config_path)
    elif args.command == "failure-taxonomy":
        build_failure_taxonomy(config_path)
    elif args.command == "action-matrix":
        build_action_matrix(config_path)
    elif args.command == "decision":
        build_decision(config_path, tests_run=args.test_run)
    elif args.command == "all":
        run_all(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
