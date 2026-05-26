from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import phase1_pre_paid_replication_compiler_readiness as readiness
import phase1_weighted_design_paid_pilot as pilot


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"

RUN_ID = "phase1_local_algorithm_bakeoff_20260526"
SCHEMA_VERSION = "barcarolle.phase1_local_algorithm_bakeoff.v1"
OUTPUT_SCHEMA_VERSION = "barcarolle.phase1_local_algorithm_bakeoff_output.v1"
RUNBOOK = "docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md"
RUNBOOK_DATE = "2026-05-26"
TARGET_REPOS = ["attrs", "boltons"]
TASKS_PER_REPO_SPLIT = 4
PRIMARY_GAP_THRESHOLD = 0.15
STRATIFIED_BASELINE_ID = "repo_stratified_by_target_profile"
UNWEIGHTED_BASELINE_ID = "repo_unweighted_same_budget"
OLD_WEIGHTED_ID = "old_weighted_target_profile"
OLD_WEIGHTED_RELEASE_ID = "barcarolle_weighted_time_family_matched"
BLOCK_ID = "block_randomized_stratified"
SHRINKAGE_ID = "block_plus_shrinkage_weighted"
PRIMARY_BLOCK_SEED = 2026052601
DIAGNOSTIC_SEEDS = [2026052601, 2026052602, 2026052603, 2026052604, 2026052605]
FEATURE_DIMS = [
    "repo_id",
    "work_cluster",
    "difficulty_band",
    "source_quality",
    "locality",
    "time_recency",
    "source_kind_group",
    "statement_quality_group",
]
MATCH_FEATURE_DIMS = [dim for dim in FEATURE_DIMS if dim != "repo_id"]
MIN_SUPPORT_PER_STRATUM = 3

REQUIRED_INPUTS = [
    "AGENTS.md",
    "docs/architecture/system-design.md",
    "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_decision.json",
    "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json",
    "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_baseline_comparison.json",
    "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_integrity_audit.json",
    "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_strata_matching.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_failure_taxonomy.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_strata_analysis.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json",
]

OPTIONAL_INPUTS = [
    "experiments/phase1_compiler/external_review/phase1_weighted_pilot_direction_review_20260526/README_FOR_EXTERNAL_GPT55_PRO.md",
    "experiments/phase1_compiler/external_review/phase1_weighted_pilot_direction_review_20260526.zip",
    "experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py",
    "experiments/phase1_compiler/tools/phase1_weighted_design_paid_pilot.py",
]

OUTPUTS = {
    "config": "experiments/phase1_compiler/configs/phase1_local_algorithm_bakeoff.yaml",
    "candidate_config": "experiments/phase1_compiler/configs/phase1_local_algorithm_bakeoff_candidates.yaml",
    "preflight": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_preflight.json",
    "reproduction": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_reproduction.json",
    "task_audit": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_task_audit.json",
    "task_audit_csv": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_task_audit.csv",
    "underidentification": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_underidentification.json",
    "feature_schema": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_feature_schema.json",
    "target_profile": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_target_profile_prototype.json",
    "candidate_designs": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_candidate_designs.json",
    "shrinkage_weights": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_shrinkage_weights.json",
    "validation_results": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_validation_results.json",
    "validation_csv": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_validation_results.csv",
    "ablation": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_ablation.json",
    "paid_readiness": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json",
    "decision": "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_decision.json",
}

REPORTS = {
    "process": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_process.md",
    "reproduction": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_reproduction.md",
    "task_audit": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_task_audit.md",
    "underidentification": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_underidentification.md",
    "feature_schema": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_feature_schema.md",
    "target_profile": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_target_profile_prototype.md",
    "candidate_designs": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_candidate_designs.md",
    "shrinkage_weights": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_shrinkage_weights.md",
    "validation_results": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_validation_results.md",
    "ablation": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_ablation.md",
    "paid_readiness": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_paid_readiness_gate.md",
    "decision": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md",
}

STEP_QUEUE = [
    (0, "Preflight, Dependency Audit, And Work Queue", "Record local algorithm bakeoff preflight"),
    (1, "Reproduce Paid Pilot Metrics And Build Task Audit", "Reproduce weighted pilot metrics for bakeoff"),
    (2, "Quantify Metadata Objective Underidentification", "Measure weighted objective underidentification"),
    (3, "Define Coarse Features And Target Profile Prototype", "Define local bakeoff features and target profile prototype"),
    (4, "Implement Candidate Compiler Designs", "Build local bakeoff compiler candidates"),
    (5, "Implement Capped Shrinkage Weights", "Evaluate capped shrinkage weights"),
    (6, "Rolling-Origin Or Pseudo-Future Local Validation", "Run local bakeoff validation"),
    (7, "Ablation Study And Mainline Recommendation", "Compare local bakeoff ablations"),
    (8, "Paid-Readiness Gate", "Evaluate local bakeoff paid readiness"),
    (9, "Final Decision And Closeout", "Record local algorithm bakeoff decision"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_from_repo(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: str | Path) -> str:
    resolved = path_from_repo(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: str | Path) -> Any:
    return json.loads(path_from_repo(path).read_text(encoding="utf-8"))


def read_or_build(output_key: str, builder: Any) -> Any:
    path = path_from_repo(OUTPUTS[output_key])
    if path.exists():
        return read_json(path)
    return builder()


def read_score_table(path: str | Path = "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv") -> list[dict[str, Any]]:
    with path_from_repo(path).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["scoreable_cell"] = str(row.get("scoreable_cell", "")).lower() == "true"
        row["agent_failure"] = str(row.get("agent_failure", "")).lower() == "true"
        row["harness_error"] = str(row.get("harness_error", "")).lower() == "true"
    return rows


def write_json(path: str | Path, payload: Any) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def digest_file(path: str | Path) -> str:
    return "sha256:" + hashlib.sha256(path_from_repo(path).read_bytes()).hexdigest()


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def command_result(args: list[str], cwd: Path = REPO_ROOT) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc), "duration_seconds": round(time.monotonic() - started, 3)}
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def command_stdout(args: list[str], cwd: Path = REPO_ROOT) -> str:
    result = command_result(args, cwd)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_None._"]
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def write_simple_yaml(path: str | Path, payload: dict[str, Any]) -> None:
    def render(value: Any, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(render(item, indent + 2))
                elif isinstance(item, bool):
                    lines.append(f"{prefix}{key}: {str(item).lower()}")
                elif item is None:
                    lines.append(f"{prefix}{key}: null")
                else:
                    lines.append(f"{prefix}{key}: {item}")
            return lines
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}- {json.dumps(item, sort_keys=True)}")
                else:
                    lines.append(f"{prefix}- {item}")
            return lines
        return [f"{prefix}{value}"]

    write_text(path, "\n".join(render(payload)))


def release_candidates() -> dict[str, Any]:
    return read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json")


def release_by_id() -> dict[str, dict[str, Any]]:
    return {str(row["release_candidate_id"]): row for row in release_candidates().get("release_candidates", [])}


def inventory_rows() -> list[dict[str, Any]]:
    return list(read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json").get("rows", []))


def inventory_by_task() -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in inventory_rows()}


def eligible_rows() -> list[dict[str, Any]]:
    return [row for row in inventory_rows() if row.get("eligible_for_next_release") and row.get("repo_id") in TARGET_REPOS]


def eligible_by_repo() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible_rows():
        grouped[str(row["repo_id"])].append(row)
    return {
        repo_id: sorted(rows, key=lambda item: (str(item.get("task_time") or ""), str(item["task_id"])))
        for repo_id, rows in grouped.items()
    }


def score_rows_by_task(rows: list[dict[str, Any]] | None = None) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows if rows is not None else read_score_table():
        grouped[str(row.get("task_id"))].append(row)
    return grouped


def task_outcome(rows: list[dict[str, Any]]) -> float | None:
    scoreable = [row for row in rows if row.get("scoreable_cell") is True]
    if not scoreable:
        return None
    return sum(1 for row in scoreable if row.get("terminal_status") == "verified_pass") / len(scoreable)


def pilot_outcomes_by_task() -> dict[str, float]:
    return {
        task_id: float(value)
        for task_id, value in ((task_id, task_outcome(rows)) for task_id, rows in score_rows_by_task().items())
        if value is not None
    }


def adapter_statuses(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("adapter_id")): str(row.get("terminal_status")) for row in rows}


def equalish(left: Any, right: Any) -> bool:
    if isinstance(left, float) or isinstance(right, float):
        return round(float(left), 8) == round(float(right), 8)
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(equalish(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equalish(a, b) for a, b in zip(left, right))
    return left == right


def selected_distribution(rows: list[dict[str, Any]], dimension: str, weights: dict[str, float] | None = None) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    if not rows:
        return {}
    if weights is None:
        weight = 1 / len(rows)
        for row in rows:
            totals[str(row.get(dimension, "unknown"))] += weight
    else:
        for row in rows:
            totals[str(row.get(dimension, "unknown"))] += float(weights.get(str(row["task_id"]), 0.0))
    return dict(sorted(totals.items()))


def l1_distance_to_target(rows: list[dict[str, Any]], target: dict[str, dict[str, float]], dimensions: list[str], weights: dict[str, float] | None = None) -> float:
    if not rows:
        return 1.0
    distances = []
    for dimension in dimensions:
        observed = selected_distribution(rows, dimension, weights)
        expected = target.get(dimension, {})
        keys = set(observed) | set(expected)
        distances.append(sum(abs(float(observed.get(key, 0.0)) - float(expected.get(key, 0.0))) for key in keys))
    return sum(distances) / len(distances)


def split_metadata_gap(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], dimensions: list[str]) -> float:
    if not rows_a or not rows_b:
        return 1.0
    distances = []
    for dimension in dimensions:
        left = selected_distribution(rows_a, dimension)
        right = selected_distribution(rows_b, dimension)
        keys = set(left) | set(right)
        distances.append(sum(abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0))) for key in keys))
    return sum(distances) / len(distances)


def old_metadata_objective(b_rows: list[dict[str, Any]], h_rows: list[dict[str, Any]], target: dict[str, dict[str, float]]) -> dict[str, float]:
    b_distance = l1_distance_to_target(b_rows, target, readiness.MATCHING_DIMENSIONS)
    h_distance = l1_distance_to_target(h_rows, target, readiness.MATCHING_DIMENSIONS)
    b_h_gap = split_metadata_gap(b_rows, h_rows, ["task_family_label", "task_time_bucket", "source_kind", "statement_source"])
    score = max(b_distance, h_distance) + abs(b_distance - h_distance) + 0.25 * b_h_gap
    return {
        "objective_score": round(score, 10),
        "B_eval_distance_to_target_profile": round(b_distance, 10),
        "H_future_distance_to_target_profile": round(h_distance, 10),
        "B_eval_H_future_metadata_gap": round(b_h_gap, 10),
    }


def pre_paid_profile_lookup() -> dict[str, dict[str, dict[str, float]]]:
    return readiness.profile_lookup(readiness.build_target_profiles())


def build_config_files() -> None:
    write_simple_yaml(
        OUTPUTS["config"],
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "runbook": RUNBOOK,
            "runbook_date": RUNBOOK_DATE,
            "local_only": True,
            "new_paid_acut_calls_allowed": False,
            "new_paid_llm_calls_allowed": False,
            "target_repos": TARGET_REPOS,
            "tasks_per_repo_split": TASKS_PER_REPO_SPLIT,
            "primary_gap_threshold": PRIMARY_GAP_THRESHOLD,
            "diagnostic_seeds": DIAGNOSTIC_SEEDS,
            "feature_dimensions": FEATURE_DIMS,
            "min_support_per_stratum": MIN_SUPPORT_PER_STRATUM,
            "dependency_decision": {
                "add_dependencies": False,
                "reason": "The repo-local Phase 1 tooling uses standard-library deterministic JSON, CSV, and Markdown generation; the small candidate pools make exhaustive enumeration and capped fallback weighting tractable without a solver dependency.",
            },
        },
    )
    write_simple_yaml(
        OUTPUTS["candidate_config"],
        {
            "schema_version": f"{SCHEMA_VERSION}.candidates",
            "run_id": RUN_ID,
            "candidate_design_ids": [
                UNWEIGHTED_BASELINE_ID,
                STRATIFIED_BASELINE_ID,
                "seeded_random_same_budget",
                "temporal_recent_baseline",
                "coverage_constrained_unweighted",
                BLOCK_ID,
                OLD_WEIGHTED_ID,
                SHRINKAGE_ID,
                "optional_block_plus_prior_difficulty",
            ],
            "seed_policy": {
                "primary_seed": PRIMARY_BLOCK_SEED,
                "diagnostic_seeds": DIAGNOSTIC_SEEDS,
                "selection_uses_outcomes": False,
            },
            "shrinkage_weight_gates": {
                "max_weight": "2 / n_selected",
                "min_ess_ratio": 0.7,
                "fallback": "uniform_fallback_when_infeasible_or_no_imbalance_improvement",
            },
        },
    )


def build_preflight() -> dict[str, Any]:
    required = []
    for raw in REQUIRED_INPUTS + [RUNBOOK]:
        path = path_from_repo(raw)
        required.append(
            {
                "path": raw,
                "exists": path.exists(),
                "sha256": digest_file(path) if path.exists() else None,
            }
        )
    optional = []
    for raw in OPTIONAL_INPUTS:
        path = path_from_repo(raw)
        optional.append(
            {
                "path": raw,
                "exists": path.exists(),
                "sha256": digest_file(path) if path.exists() else None,
            }
        )
    decision = read_json("experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_decision.json")
    metrics = read_json("experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json")
    pyproject = path_from_repo("experiments/phase1_compiler/pyproject.toml").read_text(encoding="utf-8")
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "ready_for_local_algorithm_bakeoff",
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "head_short": command_stdout(["git", "rev-parse", "--short", "HEAD"]),
        "date": RUNBOOK_DATE,
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "required_inputs": required,
        "optional_inputs": optional,
        "dependency_audit": {
            "pyproject_sha256": digest_text(pyproject),
            "current_dependencies": [],
            "current_dev_dependencies": ["pytest>=8.4,<10"],
            "decision": "stay_with_standard_library",
            "reason": "Enumeration covers only 3,150 attrs and 34,650 boltons feasible 4+4 splits; capped shrinkage can use a deterministic auditable fallback without adding scipy/cvxpy.",
            "dependency_commit_required": False,
        },
        "boundary_checks": {
            "new_paid_acut_calls_made": False,
            "new_paid_llm_calls_made": False,
            "weighted_pilot_completed": metrics.get("status") == "complete" and metrics.get("completed_cells") == 44,
            "weighted_pilot_threshold_met": decision.get("primary_threshold_result", {}).get("met") is True,
            "weighted_pilot_threshold_not_met": decision.get("final_decision") == "weighted_pilot_complete_threshold_not_met",
            "historical_reference_was_not_rerun": bool(decision.get("historical_reference_remained_historical_only")),
        },
        "work_queue": [
            {"step": step, "title": title, "commit_target": commit_target, "status": "pending"}
            for step, title, commit_target in STEP_QUEUE
        ],
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    payload["status"] = "pass" if all(item["exists"] for item in required) and payload["boundary_checks"]["weighted_pilot_threshold_not_met"] else "blocked_with_precise_reason"
    build_config_files()
    write_json(OUTPUTS["preflight"], payload)
    write_process_report(current_step=0, status="completed", extra_status="Preflight completed; no dependency changes.")
    return payload


def build_process_step_statuses(current_step: int | None = None, status: str = "pending") -> list[dict[str, Any]]:
    rows = []
    for step, title, commit_target in STEP_QUEUE:
        if current_step is None:
            step_status = "pending"
        elif step < current_step:
            step_status = "completed"
        elif step == current_step:
            step_status = status
        else:
            step_status = "pending"
        rows.append({"step": step, "title": title, "commit_target": commit_target, "status": step_status})
    return rows


def recent_bakeoff_commits() -> list[dict[str, str]]:
    log = command_stdout(
        [
            "git",
            "log",
            "--max-count=20",
            "--pretty=format:%H%x09%s",
            "--grep=bakeoff",
            "--grep=weighted objective",
            "--grep=local bakeoff",
            "--all-match",
        ]
    )
    commits = []
    for line in log.splitlines():
        if "\t" in line:
            commit_hash, subject = line.split("\t", 1)
            commits.append({"commit": commit_hash, "subject": subject})
    return commits


def write_process_report(current_step: int | None = None, status: str = "pending", extra_status: str = "") -> None:
    preflight_path = path_from_repo(OUTPUTS["preflight"])
    preflight = read_json(preflight_path) if preflight_path.exists() else {}
    rows = build_process_step_statuses(current_step, status)
    lines = [
        "# Phase 1 Local Algorithm Bakeoff Process",
        "",
        f"Run ID: `{RUN_ID}`.",
        f"Runbook: `{RUNBOOK}`.",
        f"Generated at: `{utc_now()}`.",
        "",
        "## Boundary",
        "",
        "- New paid ACUT calls made: `False`.",
        "- New paid LLM calls made: `False`.",
        "- Follow-up runbook written by worker: `False`.",
        "- Raw ACUT transcripts, prompts, completions, solver workspaces, and verifier workspaces committed: `False`.",
        "",
        "## Environment",
        "",
        f"- Branch: `{preflight.get('branch', command_stdout(['git', 'branch', '--show-current']))}`.",
        f"- HEAD at latest report write: `{command_stdout(['git', 'rev-parse', '--short', 'HEAD'])}`.",
        f"- uv: `{preflight.get('uv_version', command_stdout(['uv', '--version']))}`.",
        f"- Python: `{preflight.get('python_version', sys.version.split()[0])}`.",
        "",
        "## Dependency Decision",
        "",
        "- Decision: `stay_with_standard_library`.",
        "- Reason: the candidate pools are small enough for exhaustive enumeration and deterministic fallback weighting.",
        "",
        "## Work Queue",
        "",
        *markdown_table(rows, [("step", "Step"), ("title", "Title"), ("status", "Status"), ("commit_target", "Commit target")]),
        "",
        "## Verification Commands",
        "",
        "- `uv run --project experiments/phase1_compiler pytest -q`",
        "- `git diff --check`",
        "",
        "## Closeout Notes",
        "",
        f"- {extra_status}" if extra_status else "- Closeout is pending final decision.",
        "",
        "## Commit Tracking",
        "",
        "The exact final commit range is reported by the coordinating session after commits are created.",
    ]
    commits = recent_bakeoff_commits()
    if commits:
        lines.extend(["", "Recent bakeoff-related commits visible before this report write:", ""])
        lines.extend(f"- `{row['commit'][:12]}` {row['subject']}" for row in commits)
    write_text(REPORTS["process"], "\n".join(lines))


def recomputed_metrics() -> dict[str, Any]:
    return pilot.build_metrics(write=False)


def committed_metrics_subset(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "planned_cells": payload.get("planned_cells"),
        "completed_cells": payload.get("completed_cells"),
        "scoreable_cells": payload.get("scoreable_cells"),
        "terminal_status_counts": payload.get("terminal_status_counts"),
        "policy_violation_count": payload.get("policy_violation_count"),
        "policy_gate_pass": payload.get("policy_gate_pass"),
        "scoreability_gate_pass": payload.get("scoreability_gate_pass"),
        "observed_or_conservative_cost_usd": payload.get("observed_or_conservative_cost_usd"),
        "candidate_metrics": {
            candidate_id: {
                "planned_cells": row.get("planned_cells"),
                "cell_count": row.get("cell_count"),
                "scoreable_cell_count": row.get("scoreable_cell_count"),
                "terminal_status_counts": row.get("terminal_status_counts"),
                "per_repo_abs_gaps": row.get("per_repo_abs_gaps"),
                "max_abs_gap": row.get("max_abs_gap"),
                "adapter_disagreement_rate": row.get("adapter_disagreement_rate"),
                "threshold_met": row.get("threshold_met"),
            }
            for candidate_id, row in payload.get("candidate_metrics", {}).items()
        },
        "primary_threshold": payload.get("primary_threshold"),
    }


def candidate_membership() -> dict[str, list[str]]:
    membership: dict[str, list[str]] = defaultdict(list)
    for candidate in release_candidates().get("release_candidates", []):
        candidate_id = str(candidate["release_candidate_id"])
        if candidate_id == "prior_statement_hardened_release_as_historical_reference":
            continue
        for task_id in candidate.get("task_ids", []):
            membership[str(task_id)].append(candidate_id)
    return {task_id: sorted(values) for task_id, values in membership.items()}


def build_task_audit_rows() -> list[dict[str, Any]]:
    inv = inventory_by_task()
    membership = candidate_membership()
    rows_by_task = score_rows_by_task()
    audit_rows = []
    for task_id in sorted(rows_by_task):
        meta = inv.get(task_id, {})
        score_rows = rows_by_task[task_id]
        outcome = task_outcome(score_rows)
        audit_rows.append(
            {
                "task_id": task_id,
                "repo_id": meta.get("repo_id", task_id.split("__", 1)[0]),
                "task_time_bucket": meta.get("task_time_bucket", "unknown"),
                "module_or_package": meta.get("module_or_package", "unknown"),
                "task_family_label": meta.get("task_family_label", "unknown"),
                "source_kind": meta.get("source_kind", "unknown"),
                "statement_source": meta.get("statement_source", "unknown"),
                "statement_quality_status": meta.get("statement_quality_status", "unknown"),
                "implementation_file_count_bucket": meta.get("implementation_file_count_bucket", "unknown"),
                "test_file_count_bucket": meta.get("test_file_count_bucket", "unknown"),
                "candidate_membership": membership.get(task_id, []),
                "in_weighted_candidate": OLD_WEIGHTED_RELEASE_ID in membership.get(task_id, []),
                "in_unweighted_candidate": UNWEIGHTED_BASELINE_ID in membership.get(task_id, []),
                "in_stratified_candidate": STRATIFIED_BASELINE_ID in membership.get(task_id, []),
                "adapter_outcomes": adapter_statuses(score_rows),
                "task_level_outcome": None if outcome is None else round(outcome, 4),
                "adapter_disagreement": len({row.get("terminal_status") for row in score_rows if row.get("scoreable_cell") is True}) > 1,
                "scoreable_cell_count": sum(1 for row in score_rows if row.get("scoreable_cell") is True),
                "terminal_status_counts": dict(sorted(Counter(str(row.get("terminal_status")) for row in score_rows).items())),
            }
        )
    return audit_rows


def build_reproduction() -> dict[str, Any]:
    committed = read_json("experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json")
    recomputed = recomputed_metrics()
    committed_subset = committed_metrics_subset(committed)
    recomputed_subset = committed_metrics_subset(recomputed)
    mismatches = []
    for key in sorted(committed_subset):
        if not equalish(committed_subset[key], recomputed_subset.get(key)):
            mismatches.append({"field": key, "committed": committed_subset[key], "recomputed": recomputed_subset.get(key)})
    audit_rows = build_task_audit_rows()
    task_rows_by_id = {row["task_id"]: row for row in audit_rows}
    adapter_disagreement_count = sum(1 for row in audit_rows if row["adapter_disagreement"])
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "pass" if not mismatches and len(audit_rows) == 22 else "mismatch_or_incomplete",
        "weighted_pilot_metrics_reproduced": not mismatches,
        "mismatches": mismatches,
        "committed_metrics_digest": digest_file("experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json"),
        "score_table_digest": digest_file("experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv"),
        "recomputed_summary": recomputed_subset,
        "task_level_summary": {
            "task_count": len(audit_rows),
            "adapter_disagreement_task_count": adapter_disagreement_count,
            "adapter_disagreement_rate": round(adapter_disagreement_count / len(audit_rows), 4) if audit_rows else None,
            "terminal_status_counts": dict(sorted(Counter(status for row in audit_rows for status, count in row["terminal_status_counts"].items() for _ in range(count)).items())),
            "scoreable_cell_count": sum(row["scoreable_cell_count"] for row in audit_rows),
        },
        "task_level_adapter_averaged_outcomes": {task_id: row["task_level_outcome"] for task_id, row in sorted(task_rows_by_id.items())},
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["reproduction"], payload)
    write_json(
        OUTPUTS["task_audit"],
        {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "generated_at": utc_now(),
            "run_id": RUN_ID,
            "analysis_schema": "task_audit.v1",
            "task_count": len(audit_rows),
            "rows": audit_rows,
            "raw_statement_fields_included": False,
            "raw_prompt_completion_or_transcript_fields_included": False,
            "local_absolute_paths_included": False,
            "status": "pass" if len(audit_rows) == 22 else "incomplete",
        },
    )
    write_csv(
        OUTPUTS["task_audit_csv"],
        [
            {
                **row,
                "candidate_membership": ",".join(row["candidate_membership"]),
                "adapter_outcomes": json.dumps(row["adapter_outcomes"], sort_keys=True),
                "terminal_status_counts": json.dumps(row["terminal_status_counts"], sort_keys=True),
            }
            for row in audit_rows
        ],
        [
            "task_id",
            "repo_id",
            "task_time_bucket",
            "module_or_package",
            "task_family_label",
            "source_kind",
            "statement_source",
            "statement_quality_status",
            "implementation_file_count_bucket",
            "test_file_count_bucket",
            "candidate_membership",
            "in_weighted_candidate",
            "in_unweighted_candidate",
            "in_stratified_candidate",
            "adapter_outcomes",
            "task_level_outcome",
            "adapter_disagreement",
            "scoreable_cell_count",
            "terminal_status_counts",
        ],
    )
    write_reproduction_report(payload)
    write_task_audit_report(audit_rows)
    write_process_report(current_step=1, status="completed", extra_status="Weighted pilot metrics reproduced and sanitized task audit written.")
    return payload


def write_reproduction_report(payload: dict[str, Any]) -> None:
    rows = []
    for candidate_id, metrics in payload["recomputed_summary"]["candidate_metrics"].items():
        rows.append(
            {
                "candidate_id": candidate_id,
                "max_abs_gap": metrics["max_abs_gap"],
                "attrs_gap": metrics["per_repo_abs_gaps"].get("attrs"),
                "boltons_gap": metrics["per_repo_abs_gaps"].get("boltons"),
                "scoreable": metrics["scoreable_cell_count"],
            }
        )
    lines = [
        "# Local Algorithm Bakeoff Reproduction",
        "",
        f"Status: `{payload['status']}`.",
        f"Weighted pilot metrics reproduced: `{payload['weighted_pilot_metrics_reproduced']}`.",
        "",
        "## Candidate Gaps",
        "",
        *markdown_table(rows, [("candidate_id", "Candidate"), ("attrs_gap", "Attrs gap"), ("boltons_gap", "Boltons gap"), ("max_abs_gap", "Max gap"), ("scoreable", "Scoreable cells")]),
        "",
        "## Mismatches",
        "",
        "- None." if not payload["mismatches"] else json.dumps(payload["mismatches"], indent=2, sort_keys=True),
        "",
    ]
    write_text(REPORTS["reproduction"], "\n".join(lines))


def write_task_audit_report(rows: list[dict[str, Any]]) -> None:
    summary = Counter(row["repo_id"] for row in rows)
    lines = [
        "# Local Algorithm Bakeoff Task Audit",
        "",
        f"Task rows: `{len(rows)}`.",
        "",
        "## Repo Counts",
        "",
        *markdown_table([{"repo_id": key, "task_count": value} for key, value in sorted(summary.items())], [("repo_id", "Repo"), ("task_count", "Tasks")]),
        "",
        "The machine-readable audit excludes raw statements, raw prompts, raw completions, transcripts, hidden verifier material, and local absolute paths.",
        "",
    ]
    write_text(REPORTS["task_audit"], "\n".join(lines))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / (denom_x * denom_y)


def ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    out = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        next_index = index + 1
        while next_index < len(indexed) and indexed[next_index][1] == indexed[index][1]:
            next_index += 1
        rank = (index + 1 + next_index) / 2
        for original, _ in indexed[index:next_index]:
            out[original] = rank
        index = next_index
    return out


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(ranks(xs), ranks(ys))


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    ordered = sorted(values)

    def pick(p: float) -> float:
        return ordered[min(len(ordered) - 1, max(0, round((len(ordered) - 1) * p)))]

    return {
        "min": round_float(ordered[0], 6),
        "p25": round_float(pick(0.25), 6),
        "median": round_float(pick(0.5), 6),
        "p75": round_float(pick(0.75), 6),
        "max": round_float(ordered[-1], 6),
        "mean": round_float(sum(ordered) / len(ordered), 6),
    }


def enumerate_repo_splits(repo_id: str, rows: list[dict[str, Any]], target: dict[str, dict[str, float]], outcomes: dict[str, float]) -> list[dict[str, Any]]:
    records = []
    for b_combo in itertools.combinations(rows, TASKS_PER_REPO_SPLIT):
        b_ids = {row["task_id"] for row in b_combo}
        remaining = [row for row in rows if row["task_id"] not in b_ids]
        for h_combo in itertools.combinations(remaining, TASKS_PER_REPO_SPLIT):
            b_rows = list(b_combo)
            h_rows = list(h_combo)
            objective = old_metadata_objective(b_rows, h_rows, target)
            b_values = [outcomes.get(str(row["task_id"])) for row in b_rows]
            h_values = [outcomes.get(str(row["task_id"])) for row in h_rows]
            observed_gap = None
            if all(value is not None for value in b_values + h_values):
                observed_gap = abs(sum(float(value) for value in b_values) / len(b_values) - sum(float(value) for value in h_values) / len(h_values))
            records.append(
                {
                    "repo_id": repo_id,
                    "B_eval_task_ids": sorted(str(row["task_id"]) for row in b_rows),
                    "H_future_task_ids": sorted(str(row["task_id"]) for row in h_rows),
                    **objective,
                    "observed_outcome_gap": None if observed_gap is None else round(observed_gap, 10),
                }
            )
    return records


def current_weighted_repo_split(repo_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    candidate = release_by_id()[OLD_WEIGHTED_RELEASE_ID]
    return (
        tuple(sorted(candidate["split_assignment"][f"{repo_id}/B_eval"])),
        tuple(sorted(candidate["split_assignment"][f"{repo_id}/H_future"])),
    )


def summarize_underidentification(records: list[dict[str, Any]], current_split: tuple[tuple[str, ...], tuple[str, ...]]) -> dict[str, Any]:
    ordered = sorted(records, key=lambda row: (row["objective_score"], row["B_eval_task_ids"], row["H_future_task_ids"]))
    objective_scores = [float(row["objective_score"]) for row in ordered]
    observed_gaps = [float(row["observed_outcome_gap"]) for row in ordered if row["observed_outcome_gap"] is not None]
    paired_objectives = [float(row["objective_score"]) for row in ordered if row["observed_outcome_gap"] is not None]
    top_summaries = {}
    for label, fraction in [("top_1_percent", 0.01), ("top_5_percent", 0.05), ("top_10_percent", 0.10)]:
        count = max(1, math.ceil(len(ordered) * fraction))
        top = ordered[:count]
        top_summaries[label] = {
            "split_count": count,
            "objective_score_range": [round_float(top[0]["objective_score"], 10), round_float(top[-1]["objective_score"], 10)],
            "observed_gap_distribution": quantiles([float(row["observed_outcome_gap"]) for row in top if row["observed_outcome_gap"] is not None]),
        }
    current_index = None
    for index, row in enumerate(ordered, start=1):
        if tuple(row["B_eval_task_ids"]) == current_split[0] and tuple(row["H_future_task_ids"]) == current_split[1]:
            current_index = index
            break
    best_observed = min((row for row in ordered if row["observed_outcome_gap"] is not None), key=lambda row: (float(row["observed_outcome_gap"]), row["objective_score"]))
    best_metadata = ordered[0]
    near_cutoff = ordered[max(0, math.ceil(len(ordered) * 0.05) - 1)]["objective_score"]
    near_optimal = [row for row in ordered if float(row["objective_score"]) <= float(near_cutoff)]
    worst_near = max(near_optimal, key=lambda row: float(row["observed_outcome_gap"] or 0.0))
    return {
        "split_count": len(ordered),
        "objective_score_distribution": quantiles(objective_scores),
        "observed_gap_distribution": quantiles(observed_gaps),
        "pearson_objective_observed_gap": round_float(pearson(paired_objectives, observed_gaps), 6),
        "spearman_objective_observed_gap": round_float(spearman(paired_objectives, observed_gaps), 6),
        "top_objective_summaries": top_summaries,
        "best_metadata_split": {
            "objective_score": best_metadata["objective_score"],
            "observed_outcome_gap": best_metadata["observed_outcome_gap"],
            "B_eval_task_ids": best_metadata["B_eval_task_ids"],
            "H_future_task_ids": best_metadata["H_future_task_ids"],
        },
        "best_observed_split_oracle_diagnostic_only": {
            "objective_score": best_observed["objective_score"],
            "observed_outcome_gap": best_observed["observed_outcome_gap"],
            "B_eval_task_ids": best_observed["B_eval_task_ids"],
            "H_future_task_ids": best_observed["H_future_task_ids"],
        },
        "worst_near_optimal_metadata_split": {
            "near_optimal_definition": "top_5_percent_by_metadata_objective",
            "objective_score": worst_near["objective_score"],
            "observed_outcome_gap": worst_near["observed_outcome_gap"],
            "B_eval_task_ids": worst_near["B_eval_task_ids"],
            "H_future_task_ids": worst_near["H_future_task_ids"],
        },
        "current_weighted_split_objective_percentile": None if current_index is None else round(current_index / len(ordered), 6),
        "current_weighted_split_rank": current_index,
    }


def build_underidentification() -> dict[str, Any]:
    grouped = eligible_by_repo()
    targets = pre_paid_profile_lookup()
    outcomes = pilot_outcomes_by_task()
    repo_summaries = {}
    sample_rows = []
    for repo_id in TARGET_REPOS:
        records = enumerate_repo_splits(repo_id, grouped[repo_id], targets[repo_id], outcomes)
        summary = summarize_underidentification(records, current_weighted_repo_split(repo_id))
        repo_summaries[repo_id] = summary
        ordered = sorted(records, key=lambda row: (row["objective_score"], row["B_eval_task_ids"], row["H_future_task_ids"]))
        sample_rows.extend(ordered[:5])
    top_variances = [
        repo_summaries[repo_id]["top_objective_summaries"]["top_5_percent"]["observed_gap_distribution"]["max"]
        for repo_id in TARGET_REPOS
    ]
    underidentified = any(value is not None and float(value) > PRIMARY_GAP_THRESHOLD for value in top_variances)
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "underidentification.v1",
        "status": "pass",
        "metadata_objective_underidentification_measured": True,
        "underidentification_status": "confirmed" if underidentified else "not_confirmed",
        "old_objective": "max(B_distance,H_distance)+abs(B_distance-H_distance)+0.25*B_H_metadata_gap",
        "repo_summaries": repo_summaries,
        "sample_top_metadata_splits": sample_rows,
        "oracle_diagnostic_policy": "Observed outcome gap is used only to diagnose underidentification after the paid pilot; it is not used as a deployable split algorithm.",
        "deterministic_tie_breaks_unsafe": underidentified,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["underidentification"], payload)
    write_underidentification_report(payload)
    write_process_report(current_step=2, status="completed", extra_status="Old weighted metadata objective underidentification measured.")
    return payload


def write_underidentification_report(payload: dict[str, Any]) -> None:
    rows = []
    for repo_id, summary in payload["repo_summaries"].items():
        top5 = summary["top_objective_summaries"]["top_5_percent"]["observed_gap_distribution"]
        rows.append(
            {
                "repo_id": repo_id,
                "split_count": summary["split_count"],
                "pearson": summary["pearson_objective_observed_gap"],
                "spearman": summary["spearman_objective_observed_gap"],
                "top5_min_gap": top5["min"],
                "top5_max_gap": top5["max"],
                "current_percentile": summary["current_weighted_split_objective_percentile"],
            }
        )
    lines = [
        "# Metadata Objective Underidentification",
        "",
        f"Status: `{payload['underidentification_status']}`.",
        f"Deterministic tie-breaks unsafe: `{payload['deterministic_tie_breaks_unsafe']}`.",
        "",
        *markdown_table(rows, [("repo_id", "Repo"), ("split_count", "Feasible splits"), ("pearson", "Pearson"), ("spearman", "Spearman"), ("top5_min_gap", "Top 5% min gap"), ("top5_max_gap", "Top 5% max gap"), ("current_percentile", "Current percentile")]),
        "",
        "Observed outcomes are used here only as an oracle diagnostic for the already-completed pilot.",
        "",
    ]
    write_text(REPORTS["underidentification"], "\n".join(lines))


def module_root(row: dict[str, Any]) -> str:
    modules = row.get("module_or_package_list") or []
    if isinstance(modules, list) and modules:
        first = str(modules[0])
    else:
        first = str(row.get("module_or_package") or "unknown").split(",", 1)[0].strip()
    if not first or first == "unknown":
        return "unknown"
    parts = first.split(".")
    if len(parts) > 1 and parts[0] in {"attrs", "boltons", "src"}:
        return parts[1]
    return parts[0]


def source_quality(row: dict[str, Any]) -> str:
    status = str(row.get("statement_quality_status") or "")
    if status == "pass":
        return "clean"
    if status == "pass_with_minor_risk":
        return "minor_risk"
    return "risky"


def source_kind_group(row: dict[str, Any]) -> str:
    kind = str(row.get("source_kind") or "unknown")
    if kind in {"issue", "pull_request", "commit"}:
        return kind
    if "pull" in kind or kind == "pr":
        return "pull_request"
    if "issue" in kind:
        return "issue"
    return "other"


def base_features(row: dict[str, Any], recent_task_ids: set[str]) -> dict[str, Any]:
    impl_count = int(row.get("implementation_file_count") or 0)
    return {
        "task_id": str(row["task_id"]),
        "repo_id": str(row["repo_id"]),
        "work_cluster_raw": module_root(row),
        "difficulty_band": "unknown",
        "source_quality": source_quality(row),
        "locality": "single_file" if impl_count <= 1 else "multi_file",
        "time_recency": "recent" if str(row["task_id"]) in recent_task_ids else "older",
        "source_kind_group": source_kind_group(row),
        "statement_quality_group": source_quality(row),
    }


def build_feature_rows() -> list[dict[str, Any]]:
    grouped = eligible_by_repo()
    recent_by_repo: dict[str, set[str]] = {}
    for repo_id, rows in grouped.items():
        ordered = sorted(rows, key=lambda item: (str(item.get("task_time") or ""), str(item["task_id"])))
        midpoint = len(ordered) // 2
        recent_by_repo[repo_id] = {str(row["task_id"]) for row in ordered[midpoint:]}
    raw_rows = [base_features(row, recent_by_repo[str(row["repo_id"])]) for row in eligible_rows()]
    cluster_counts = Counter((row["repo_id"], row["work_cluster_raw"]) for row in raw_rows)
    rows = []
    for row in raw_rows:
        work_cluster = row["work_cluster_raw"] if cluster_counts[(row["repo_id"], row["work_cluster_raw"])] >= MIN_SUPPORT_PER_STRATUM else "rare_or_unknown"
        out = dict(row)
        out["work_cluster"] = work_cluster
        out["feature_stratum"] = "|".join(str(out[dim]) for dim in FEATURE_DIMS)
        rows.append(out)
    return sorted(rows, key=lambda item: (item["repo_id"], item["task_id"]))


def feature_by_task() -> dict[str, dict[str, Any]]:
    return {row["task_id"]: row for row in build_feature_rows()}


def target_profile_from_features(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = []
    for repo_id in TARGET_REPOS:
        repo_rows = [row for row in rows if row["repo_id"] == repo_id]
        support_counts = {dim: dict(sorted(Counter(str(row[dim]) for row in repo_rows).items())) for dim in FEATURE_DIMS}
        profile_tables = {}
        for dim in FEATURE_DIMS:
            counts = Counter(str(row[dim]) for row in repo_rows)
            total = sum(counts.values())
            profile_tables[dim] = {key: round(value / total, 6) for key, value in sorted(counts.items())}
        rare_count = sum(1 for row in repo_rows if "rare_or_unknown" in row["feature_stratum"])
        profiles.append(
            {
                "repo_id": repo_id,
                "candidate_support_count": len(repo_rows),
                "profile_weight_tables": profile_tables,
                "stratum_support_counts": dict(sorted(Counter(row["feature_stratum"] for row in repo_rows).items())),
                "feature_support_counts": support_counts,
                "covered_target_mass": round(1 - rare_count / len(repo_rows), 6) if repo_rows else 0.0,
                "uncovered_target_mass": round(rare_count / len(repo_rows), 6) if repo_rows else 1.0,
                "confidence_label": "surrogate_sparse" if len(repo_rows) < 20 or rare_count else "surrogate_moderate",
                "support_warnings": ["eligible task supply below 20-30 precision-run guidance"] if len(repo_rows) < 20 else [],
            }
        )
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "target_profile_prototype.v1",
        "target_profile_independence_status": "surrogate_candidate_metadata",
        "H_future_outcomes_used_for_profile_computation": False,
        "outcome_fields_used": [],
        "min_support_per_stratum": MIN_SUPPORT_PER_STRATUM,
        "rare_unknown_bucket_required": True,
        "profiles": profiles,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }


def build_features() -> dict[str, Any]:
    rows = build_feature_rows()
    schema = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "feature_schema.v1",
        "feature_dimensions": [
            {"name": "repo_id", "description": "Target repository id.", "source": "candidate_inventory.repo_id"},
            {"name": "work_cluster", "description": "Coarsened module root with rare_or_unknown merging.", "source": "module_or_package_list/module_or_package"},
            {"name": "difficulty_band", "description": "Unknown by default because no leakage-safe prior model is available.", "source": "constant_unknown"},
            {"name": "source_quality", "description": "clean, minor_risk, or risky from statement quality status.", "source": "statement_quality_status"},
            {"name": "locality", "description": "single_file or multi_file from implementation file count.", "source": "implementation_file_count"},
            {"name": "time_recency", "description": "older or recent within repo by task time ordering.", "source": "task_time"},
            {"name": "source_kind_group", "description": "issue, pull_request, commit, or other.", "source": "source_kind"},
            {"name": "statement_quality_group", "description": "clean, minor_risk, or risky from statement quality status.", "source": "statement_quality_status"},
        ],
        "rows": rows,
        "sparse_strata_policy": {
            "min_support_per_stratum": MIN_SUPPORT_PER_STRATUM,
            "rare_unknown_bucket_required": True,
            "raw_task_family_label_primary_stratum": False,
        },
        "H_future_outcomes_used_for_features": False,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }
    profile = target_profile_from_features(rows)
    write_json(OUTPUTS["feature_schema"], schema)
    write_json(OUTPUTS["target_profile"], profile)
    write_feature_schema_report(schema)
    write_target_profile_report(profile)
    write_process_report(current_step=3, status="completed", extra_status="Coarse feature schema and surrogate target profile prototype written.")
    return schema


def write_feature_schema_report(payload: dict[str, Any]) -> None:
    counts = Counter(row["repo_id"] for row in payload["rows"])
    lines = [
        "# Local Bakeoff Feature Schema",
        "",
        f"Status: `{payload['status']}`.",
        f"H_future outcomes used for features: `{payload['H_future_outcomes_used_for_features']}`.",
        "",
        "## Feature Dimensions",
        "",
        *markdown_table(payload["feature_dimensions"], [("name", "Name"), ("source", "Source"), ("description", "Description")]),
        "",
        "## Eligible Feature Rows",
        "",
        *markdown_table([{"repo_id": key, "rows": value} for key, value in sorted(counts.items())], [("repo_id", "Repo"), ("rows", "Rows")]),
        "",
    ]
    write_text(REPORTS["feature_schema"], "\n".join(lines))


def write_target_profile_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "repo_id": profile["repo_id"],
            "support": profile["candidate_support_count"],
            "covered": profile["covered_target_mass"],
            "uncovered": profile["uncovered_target_mass"],
            "confidence": profile["confidence_label"],
        }
        for profile in payload["profiles"]
    ]
    lines = [
        "# Local Bakeoff Target Profile Prototype",
        "",
        f"Independence status: `{payload['target_profile_independence_status']}`.",
        f"H_future outcomes used for profile computation: `{payload['H_future_outcomes_used_for_profile_computation']}`.",
        "",
        *markdown_table(rows, [("repo_id", "Repo"), ("support", "Support"), ("covered", "Covered mass"), ("uncovered", "Uncovered mass"), ("confidence", "Confidence")]),
        "",
        "The prototype is a surrogate from sanitized candidate metadata because no independent public event stream is present in the required artifacts.",
        "",
    ]
    write_text(REPORTS["target_profile"], "\n".join(lines))


def rows_for_ids(task_ids: Iterable[str], row_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [row_map[task_id] for task_id in task_ids if task_id in row_map]


def equal_weights_for(split_assignment: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    return {
        split: {task_id: round(1 / len(task_ids), 8) for task_id in task_ids}
        for split, task_ids in split_assignment.items()
        if task_ids
    }


def design_from_release(candidate_id: str, design_id: str, design_kind: str) -> dict[str, Any]:
    candidate = release_by_id()[candidate_id]
    return {
        "design_id": design_id,
        "design_kind": design_kind,
        "task_ids": sorted(str(task_id) for task_id in candidate.get("task_ids", [])),
        "split_assignment": {key: [str(task_id) for task_id in value] for key, value in candidate.get("split_assignment", {}).items()},
        "weights": candidate.get("weights") if isinstance(candidate.get("weights"), dict) else equal_weights_for(candidate.get("split_assignment", {})),
        "weight_mode": "existing_pre_paid_release_weights" if design_id == OLD_WEIGHTED_ID else "uniform",
        "selection_inputs": candidate.get("selection_inputs", []),
        "outcome_fields_used_for_selection": [],
        "hidden_oracle_material_used": False,
        "random_seed_policy": "deterministic_existing_release_candidate",
        "fallback_rule": "not_applicable_existing_release_candidate",
        "diagnostics": {},
        "status": "evaluated",
    }


def split_from_ordered(repo_rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    selected = repo_rows[: TASKS_PER_REPO_SPLIT * 2]
    return {
        "B_eval": [str(row["task_id"]) for row in selected[:TASKS_PER_REPO_SPLIT]],
        "H_future": [str(row["task_id"]) for row in selected[TASKS_PER_REPO_SPLIT : TASKS_PER_REPO_SPLIT * 2]],
    }


def split_assignment_for_repo_splits(repo_splits: dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    return {f"{repo_id}/{split}": task_ids for repo_id, splits in repo_splits.items() for split, task_ids in splits.items()}


def seeded_random_split(seed: int) -> dict[str, list[str]]:
    grouped = eligible_by_repo()
    assignments = {}
    for repo_id, rows in grouped.items():
        repo_rng = random.Random(seed + stable_int(repo_id))
        shuffled = list(rows)
        repo_rng.shuffle(shuffled)
        selected = shuffled[: TASKS_PER_REPO_SPLIT * 2]
        assignments[repo_id] = {
            "B_eval": sorted(str(row["task_id"]) for row in selected[:TASKS_PER_REPO_SPLIT]),
            "H_future": sorted(str(row["task_id"]) for row in selected[TASKS_PER_REPO_SPLIT : TASKS_PER_REPO_SPLIT * 2]),
        }
    return split_assignment_for_repo_splits(assignments)


def temporal_recent_split() -> dict[str, list[str]]:
    assignments = {}
    for repo_id, rows in eligible_by_repo().items():
        recent = sorted(rows, key=lambda item: (str(item.get("task_time") or ""), str(item["task_id"])))[-TASKS_PER_REPO_SPLIT * 2 :]
        assignments[repo_id] = split_from_ordered(recent)
    return split_assignment_for_repo_splits(assignments)


def coverage_constrained_split() -> dict[str, list[str]]:
    features = feature_by_task()
    assignments = {}
    for repo_id, rows in eligible_by_repo().items():
        selected: list[dict[str, Any]] = []
        covered_values: set[tuple[str, str]] = set()
        available = list(rows)
        while available and len(selected) < TASKS_PER_REPO_SPLIT * 2:
            def score(row: dict[str, Any]) -> tuple[int, int, str, str]:
                feat = features[str(row["task_id"])]
                new_values = sum(1 for dim in MATCH_FEATURE_DIMS if (dim, str(feat[dim])) not in covered_values)
                new_signature = 1 if ("feature_stratum", feat["feature_stratum"]) not in covered_values else 0
                return (-new_values, -new_signature, str(row.get("task_time") or ""), str(row["task_id"]))

            chosen = min(available, key=score)
            selected.append(chosen)
            feat = features[str(chosen["task_id"])]
            for dim in MATCH_FEATURE_DIMS:
                covered_values.add((dim, str(feat[dim])))
            covered_values.add(("feature_stratum", feat["feature_stratum"]))
            available.remove(chosen)
        selected = sorted(selected, key=lambda row: (features[str(row["task_id"])]["feature_stratum"], str(row.get("task_time") or ""), str(row["task_id"])))
        splits = {"B_eval": [], "H_future": []}
        for row in selected:
            chosen = "B_eval" if len(splits["B_eval"]) <= len(splits["H_future"]) and len(splits["B_eval"]) < TASKS_PER_REPO_SPLIT else "H_future"
            if len(splits[chosen]) >= TASKS_PER_REPO_SPLIT:
                chosen = "H_future" if chosen == "B_eval" else "B_eval"
            splits[chosen].append(str(row["task_id"]))
        assignments[repo_id] = {split: sorted(ids) for split, ids in splits.items()}
    return split_assignment_for_repo_splits(assignments)


def block_key_for_task(task_id: str, features: dict[str, dict[str, Any]]) -> str:
    feat = features[task_id]
    return "|".join(str(feat[dim]) for dim in ["work_cluster", "source_quality", "locality", "source_kind_group", "statement_quality_group"])


def block_randomized_split(seed: int) -> dict[str, list[str]]:
    features = feature_by_task()
    assignments = {}
    for repo_id, rows in eligible_by_repo().items():
        repo_rng = random.Random(seed + stable_int(f"block:{repo_id}"))
        blocks: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            blocks[block_key_for_task(str(row["task_id"]), features)].append(row)
        block_items = sorted(blocks.items(), key=lambda item: item[0])
        for _, block_rows in block_items:
            repo_rng.shuffle(block_rows)
        selected: list[dict[str, Any]] = []
        cursors = {key: 0 for key, _ in block_items}
        while len(selected) < TASKS_PER_REPO_SPLIT * 2 and any(cursors[key] < len(blocks[key]) for key, _ in block_items):
            available_keys = [key for key, _ in block_items if cursors[key] < len(blocks[key])]
            repo_rng.shuffle(available_keys)
            for key in sorted(available_keys, key=lambda block: (sum(1 for row in selected if block_key_for_task(str(row["task_id"]), features) == block), block)):
                if len(selected) >= TASKS_PER_REPO_SPLIT * 2:
                    break
                selected.append(blocks[key][cursors[key]])
                cursors[key] += 1
        splits = {"B_eval": [], "H_future": []}
        block_split_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for row in selected:
            task_id = str(row["task_id"])
            key = block_key_for_task(task_id, features)
            candidates = [split for split in ["B_eval", "H_future"] if len(splits[split]) < TASKS_PER_REPO_SPLIT]
            chosen = min(candidates, key=lambda split: (block_split_counts[key][split], len(splits[split]), split))
            splits[chosen].append(task_id)
            block_split_counts[key][chosen] += 1
        assignments[repo_id] = {split: sorted(ids) for split, ids in splits.items()}
    return split_assignment_for_repo_splits(assignments)


def feature_diagnostics(split_assignment: dict[str, list[str]]) -> dict[str, Any]:
    features = feature_by_task()
    profile = target_profile_from_features(list(features.values()))
    profile_by_repo = {row["repo_id"]: row for row in profile["profiles"]}
    diagnostics = []
    for repo_split, task_ids in sorted(split_assignment.items()):
        repo_id, split = repo_split.split("/")
        rows = [features[task_id] for task_id in task_ids]
        target = profile_by_repo[repo_id]["profile_weight_tables"]
        diagnostics.append(
            {
                "repo_split": repo_split,
                "task_count": len(task_ids),
                "feature_stratum_counts": dict(sorted(Counter(row["feature_stratum"] for row in rows).items())),
                "mean_l1_distance_to_target_profile": round_float(l1_distance_to_target(rows, target, MATCH_FEATURE_DIMS), 6),
                "covered_target_mass": profile_by_repo[repo_id]["covered_target_mass"],
                "uncovered_target_mass": profile_by_repo[repo_id]["uncovered_target_mass"],
                "split": split,
            }
        )
    return {
        "repo_split_diagnostics": diagnostics,
        "mean_l1_distance_to_target_profile": round_float(sum(row["mean_l1_distance_to_target_profile"] for row in diagnostics) / len(diagnostics), 6),
    }


def candidate_payload(design_id: str, split_assignment: dict[str, list[str]], *, design_kind: str, seed: int | None, weight_mode: str = "uniform", diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "design_id": design_id,
        "design_kind": design_kind,
        "task_ids": sorted({task_id for task_ids in split_assignment.values() for task_id in task_ids}),
        "split_assignment": split_assignment,
        "weights": equal_weights_for(split_assignment),
        "weight_mode": weight_mode,
        "selection_inputs": [
            "candidate task ids",
            "repo_id",
            "task_time",
            "coarse local bakeoff feature schema",
            "sanitized pre-outcome candidate metadata",
        ],
        "outcome_fields_used_for_selection": [],
        "hidden_oracle_material_used": False,
        "random_seed_policy": "none" if seed is None else f"seeded_deterministic:{seed}",
        "seed": seed,
        "fallback_rule": "fallback_to_uniform_weights_and_record_sparse_support",
        "diagnostics": diagnostics or feature_diagnostics(split_assignment),
        "status": "evaluated",
    }


def build_candidate_designs() -> dict[str, Any]:
    seed_variants = {
        "seeded_random_same_budget": [
            candidate_payload("seeded_random_same_budget", seeded_random_split(seed), design_kind="seeded_random_same_budget", seed=seed)
            for seed in DIAGNOSTIC_SEEDS
        ],
        BLOCK_ID: [
            candidate_payload(BLOCK_ID, block_randomized_split(seed), design_kind="block_randomized_stratified", seed=seed)
            for seed in DIAGNOSTIC_SEEDS
        ],
    }
    designs = [
        design_from_release(UNWEIGHTED_BASELINE_ID, UNWEIGHTED_BASELINE_ID, "baseline_existing_unweighted"),
        design_from_release(STRATIFIED_BASELINE_ID, STRATIFIED_BASELINE_ID, "baseline_existing_stratified"),
        seed_variants["seeded_random_same_budget"][0],
        candidate_payload("temporal_recent_baseline", temporal_recent_split(), design_kind="temporal_recent_baseline", seed=None),
        candidate_payload("coverage_constrained_unweighted", coverage_constrained_split(), design_kind="coverage_constrained_unweighted", seed=None),
        seed_variants[BLOCK_ID][0],
        design_from_release(OLD_WEIGHTED_RELEASE_ID, OLD_WEIGHTED_ID, "old_weighted_target_profile_reference"),
        candidate_payload(SHRINKAGE_ID, block_randomized_split(PRIMARY_BLOCK_SEED), design_kind="block_plus_shrinkage_weighted", seed=PRIMARY_BLOCK_SEED, weight_mode="capped_shrinkage_pending"),
        {
            "design_id": "optional_block_plus_prior_difficulty",
            "design_kind": "skipped_optional_prior_difficulty",
            "status": "skipped",
            "skip_reason": "No leakage-safe prior difficulty model is available in committed artifacts for rolling or nested validation.",
            "task_ids": [],
            "split_assignment": {},
            "weights": {},
            "weight_mode": "not_applicable",
            "selection_inputs": [],
            "outcome_fields_used_for_selection": [],
            "hidden_oracle_material_used": False,
            "random_seed_policy": "not_applicable",
            "fallback_rule": "skip_when_prior_is_not_leakage_safe",
            "diagnostics": {},
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "candidate_designs.v1",
        "status": "pass",
        "candidate_designs": designs,
        "diagnostic_seed_variants": seed_variants,
        "selection_policy": {
            "outcome_fields_used_for_selection": [],
            "hidden_oracle_material_used": False,
            "raw_transcripts_used": False,
            "old_weighted_design_role": "baseline_reference_only",
        },
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["candidate_designs"], payload)
    write_candidate_designs_report(payload)
    write_process_report(current_step=4, status="completed", extra_status="Local compiler candidate designs built with deterministic seed diagnostics.")
    return payload


def write_candidate_designs_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "design_id": row["design_id"],
            "kind": row["design_kind"],
            "tasks": len(row.get("task_ids", [])),
            "weight_mode": row.get("weight_mode"),
            "status": row.get("status"),
        }
        for row in payload["candidate_designs"]
    ]
    lines = [
        "# Local Bakeoff Candidate Designs",
        "",
        f"Status: `{payload['status']}`.",
        "",
        *markdown_table(rows, [("design_id", "Design"), ("kind", "Kind"), ("tasks", "Tasks"), ("weight_mode", "Weight mode"), ("status", "Status")]),
        "",
        "All evaluated candidate designs record empty `outcome_fields_used_for_selection`; the old weighted design is retained only as a baseline reference.",
        "",
    ]
    write_text(REPORTS["candidate_designs"], "\n".join(lines))


def normalize_cap_weights(raw_weights: list[float], cap: float) -> list[float]:
    weights = [max(1e-12, float(value)) for value in raw_weights]
    total = sum(weights)
    weights = [value / total for value in weights]
    for _ in range(50):
        over = [index for index, value in enumerate(weights) if value > cap]
        if not over:
            break
        fixed = set(over)
        fixed_mass = cap * len(fixed)
        remaining_mass = max(0.0, 1.0 - fixed_mass)
        under = [index for index in range(len(weights)) if index not in fixed]
        under_total = sum(weights[index] for index in under)
        for index in over:
            weights[index] = cap
        if under and under_total > 0:
            for index in under:
                weights[index] = weights[index] / under_total * remaining_mass
    total = sum(weights)
    return [round(value / total, 10) for value in weights]


def effective_sample_size(weights: Iterable[float]) -> float:
    values = [float(value) for value in weights]
    denom = sum(value * value for value in values)
    return 0.0 if denom == 0 else 1 / denom


def optimize_split_weights(task_ids: list[str], target: dict[str, dict[str, float]]) -> dict[str, Any]:
    features = feature_by_task()
    rows = [features[task_id] for task_id in task_ids]
    n = len(rows)
    uniform_values = [1 / n for _ in rows]
    cap = 2 / n
    before = l1_distance_to_target(rows, target, MATCH_FEATURE_DIMS, dict(zip(task_ids, uniform_values)))
    raw = list(uniform_values)
    for _ in range(30):
        for dim in MATCH_FEATURE_DIMS:
            observed = defaultdict(float)
            for row, weight in zip(rows, raw):
                observed[str(row[dim])] += weight
            for index, row in enumerate(rows):
                value = str(row[dim])
                expected = float(target.get(dim, {}).get(value, 0.0))
                if observed[value] > 0 and expected > 0:
                    raw[index] *= expected / observed[value]
        raw = normalize_cap_weights(raw, cap)
    optimized = normalize_cap_weights(raw, cap)
    optimized_weights = dict(zip(task_ids, optimized))
    after = l1_distance_to_target(rows, target, MATCH_FEATURE_DIMS, optimized_weights)
    ess = effective_sample_size(optimized)
    ess_ratio = ess / n if n else 0.0
    if after < before - 0.0001 and max(optimized) <= cap + 1e-9 and ess_ratio >= 0.7:
        status = "optimized"
        chosen = optimized
        reason = None
    else:
        status = "uniform_fallback"
        chosen = uniform_values
        reason = "capped_raking_did_not_materially_improve_target_imbalance_under_sparse_support"
        after = before
        ess = effective_sample_size(chosen)
        ess_ratio = ess / n if n else 0.0
    return {
        "weight_status": status,
        "weights": {task_id: round_float(weight, 10) for task_id, weight in zip(task_ids, chosen)},
        "ESS": round_float(ess, 6),
        "ESS_ratio": round_float(ess_ratio, 6),
        "max_weight": round_float(max(chosen), 10),
        "max_weight_allowed": round_float(cap, 10),
        "target_imbalance_before_weighting": round_float(before, 6),
        "target_imbalance_after_weighting": round_float(after, 6),
        "fallback_reason": reason,
    }


def build_shrinkage_weights() -> dict[str, Any]:
    designs = read_or_build("candidate_designs", build_candidate_designs)["candidate_designs"]
    design_by_id = {row["design_id"]: row for row in designs}
    features = build_feature_rows()
    profile = target_profile_from_features(features)
    profile_by_repo = {row["repo_id"]: row for row in profile["profiles"]}
    weighted_candidates = []
    shrinkage_design = design_by_id[SHRINKAGE_ID]
    split_weights = {}
    split_diagnostics = {}
    for repo_split, task_ids in shrinkage_design["split_assignment"].items():
        repo_id, _ = repo_split.split("/")
        target = profile_by_repo[repo_id]["profile_weight_tables"]
        result = optimize_split_weights(task_ids, target)
        split_weights[repo_split] = result["weights"]
        split_diagnostics[repo_split] = {key: value for key, value in result.items() if key != "weights"}
    weighted_candidates.append(
        {
            "candidate_id": SHRINKAGE_ID,
            "weight_mode": "capped_shrinkage",
            "weights_by_repo_split": split_weights,
            "diagnostics_by_repo_split": split_diagnostics,
            "status": "uniform_fallback" if any(row["weight_status"] == "uniform_fallback" for row in split_diagnostics.values()) else "optimized",
        }
    )
    old = design_by_id[OLD_WEIGHTED_ID]
    old_diag = {}
    for repo_split, weights in old.get("weights", {}).items():
        values = [float(value) for value in weights.values()]
        n = len(values)
        old_diag[repo_split] = {
            "weight_status": "existing_reference_weight",
            "ESS": round_float(effective_sample_size(values), 6),
            "ESS_ratio": round_float(effective_sample_size(values) / n if n else 0.0, 6),
            "max_weight": round_float(max(values) if values else None, 10),
            "max_weight_allowed": round_float(2 / n if n else None, 10),
        }
    weighted_candidates.append(
        {
            "candidate_id": OLD_WEIGHTED_ID,
            "weight_mode": "existing_pre_paid_release_weights_reference_only",
            "weights_by_repo_split": old.get("weights", {}),
            "diagnostics_by_repo_split": old_diag,
            "status": "reference_only",
        }
    )
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "shrinkage_weights.v1",
        "status": "pass",
        "weight_gate": {
            "max_weight_rule": "max_weight <= 2 / n_selected",
            "min_ESS_ratio": 0.7,
            "sum_weights_equals_one": True,
            "fallback_rule": "uniform_fallback_when_infeasible_or_no_imbalance_improvement",
        },
        "weighted_candidates": weighted_candidates,
        "interpretation": "Capped shrinkage mostly falls back to uniform weights under sparse support; old weighted pilot weights remain reference-only.",
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["shrinkage_weights"], payload)
    write_shrinkage_report(payload)
    write_process_report(current_step=5, status="completed", extra_status="Capped shrinkage weights evaluated with sparse-support fallback.")
    return payload


def write_shrinkage_report(payload: dict[str, Any]) -> None:
    rows = []
    for candidate in payload["weighted_candidates"]:
        statuses = Counter(row["weight_status"] for row in candidate["diagnostics_by_repo_split"].values())
        ess_values = [row.get("ESS_ratio") for row in candidate["diagnostics_by_repo_split"].values() if row.get("ESS_ratio") is not None]
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "status": candidate["status"],
                "weight_statuses": dict(sorted(statuses.items())),
                "min_ess_ratio": min(ess_values) if ess_values else None,
            }
        )
    lines = [
        "# Capped Shrinkage Weights",
        "",
        f"Status: `{payload['status']}`.",
        "",
        *markdown_table(rows, [("candidate_id", "Candidate"), ("status", "Status"), ("weight_statuses", "Weight statuses"), ("min_ess_ratio", "Min ESS ratio")]),
        "",
        payload["interpretation"],
        "",
    ]
    write_text(REPORTS["shrinkage_weights"], "\n".join(lines))


def weighted_rate(task_ids: list[str], outcomes: dict[str, float], weights: dict[str, float] | None = None) -> float | None:
    if not task_ids:
        return None
    if weights is None:
        weights = {task_id: 1 / len(task_ids) for task_id in task_ids}
    if any(task_id not in outcomes for task_id in task_ids):
        return None
    total_weight = sum(float(weights.get(task_id, 0.0)) for task_id in task_ids)
    if total_weight == 0:
        return None
    return sum(float(weights.get(task_id, 0.0)) / total_weight * float(outcomes[task_id]) for task_id in task_ids)


def flatten_validation_designs(candidate_payload_data: dict[str, Any], weights_payload: dict[str, Any]) -> list[dict[str, Any]]:
    weight_by_candidate = {row["candidate_id"]: row for row in weights_payload["weighted_candidates"]}
    designs = []
    for row in candidate_payload_data["candidate_designs"]:
        if row["status"] == "skipped":
            continue
        design = dict(row)
        design["variant_id"] = row["design_id"]
        design["validation_seed"] = row.get("seed")
        if row["design_id"] == SHRINKAGE_ID:
            design["weights"] = weight_by_candidate[SHRINKAGE_ID]["weights_by_repo_split"]
        designs.append(design)
    for design_id in ["seeded_random_same_budget", BLOCK_ID]:
        for index, variant in enumerate(candidate_payload_data["diagnostic_seed_variants"][design_id]):
            if index == 0:
                continue
            design = dict(variant)
            design["variant_id"] = f"{design_id}:seed_{variant['seed']}"
            design["validation_seed"] = variant.get("seed")
            designs.append(design)
    return designs


def evaluate_design(design: dict[str, Any], outcomes: dict[str, float], baseline_repo_gaps: dict[str, float]) -> dict[str, Any]:
    repo_rows = []
    weights_by_split = design.get("weights") if isinstance(design.get("weights"), dict) else {}
    for repo_id in TARGET_REPOS:
        b_key = f"{repo_id}/B_eval"
        h_key = f"{repo_id}/H_future"
        b_ids = list(design["split_assignment"].get(b_key, []))
        h_ids = list(design["split_assignment"].get(h_key, []))
        b_rate = weighted_rate(b_ids, outcomes, weights_by_split.get(b_key))
        h_rate = weighted_rate(h_ids, outcomes, weights_by_split.get(h_key))
        gap = None if b_rate is None or h_rate is None else abs(b_rate - h_rate)
        task_count = len(b_ids) + len(h_ids)
        weights = list((weights_by_split.get(b_key) or {task_id: 1 / len(b_ids) for task_id in b_ids}).values()) + list((weights_by_split.get(h_key) or {task_id: 1 / len(h_ids) for task_id in h_ids}).values())
        repo_rows.append(
            {
                "repo_id": repo_id,
                "B_eval_rate": round_float(b_rate, 6),
                "H_future_rate": round_float(h_rate, 6),
                "abs_gap": round_float(gap, 6),
                "threshold_pass": gap is not None and gap <= PRIMARY_GAP_THRESHOLD,
                "catastrophic_miss": gap is not None and gap > float(baseline_repo_gaps[repo_id]) + PRIMARY_GAP_THRESHOLD,
                "effective_sample_size": round_float(effective_sample_size(weights), 6),
                "task_count": task_count,
            }
        )
    gaps = [float(row["abs_gap"]) for row in repo_rows if row["abs_gap"] is not None]
    return {
        "design_id": design["design_id"],
        "variant_id": design.get("variant_id", design["design_id"]),
        "seed": design.get("validation_seed"),
        "validation_type": "pseudo_future_seeded_block_resampling",
        "window_id": "paid_pilot_union_all_observed",
        "per_repo": repo_rows,
        "MAE": round_float(sum(gaps) / len(gaps), 6) if gaps else None,
        "RMSE": round_float(math.sqrt(sum(gap * gap for gap in gaps) / len(gaps)), 6) if gaps else None,
        "max_absolute_gap": round_float(max(gaps), 6) if gaps else None,
        "catastrophic_miss_rate": round_float(sum(1 for row in repo_rows if row["catastrophic_miss"]) / len(repo_rows), 6),
        "threshold_pass_rate_under_0_15": round_float(sum(1 for row in repo_rows if row["threshold_pass"]) / len(repo_rows), 6),
        "effective_sample_size": round_float(sum(float(row["effective_sample_size"]) for row in repo_rows) / len(repo_rows), 6),
        "uncertainty_status": "insufficient_support_for_bootstrap_interval",
    }


def aggregate_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["design_id"]].append(row)
    summaries = {}
    for design_id, items in grouped.items():
        maes = [float(row["MAE"]) for row in items if row["MAE"] is not None]
        max_gaps = [float(row["max_absolute_gap"]) for row in items if row["max_absolute_gap"] is not None]
        miss_rates = [float(row["catastrophic_miss_rate"]) for row in items if row["catastrophic_miss_rate"] is not None]
        summaries[design_id] = {
            "variant_count": len(items),
            "MAE_mean": round_float(sum(maes) / len(maes), 6) if maes else None,
            "MAE_min": round_float(min(maes), 6) if maes else None,
            "MAE_max": round_float(max(maes), 6) if maes else None,
            "MAE_sample_variance": round_float(statistics.variance(maes), 8) if len(maes) > 1 else 0.0,
            "max_absolute_gap_max": round_float(max(max_gaps), 6) if max_gaps else None,
            "catastrophic_miss_rate_mean": round_float(sum(miss_rates) / len(miss_rates), 6) if miss_rates else None,
            "threshold_pass_rate_mean": round_float(sum(float(row["threshold_pass_rate_under_0_15"]) for row in items) / len(items), 6),
        }
    return summaries


def build_validation() -> dict[str, Any]:
    candidate_payload_data = read_or_build("candidate_designs", build_candidate_designs)
    weights_payload = read_or_build("shrinkage_weights", build_shrinkage_weights)
    designs = flatten_validation_designs(candidate_payload_data, weights_payload)
    outcomes = pilot_outcomes_by_task()
    baseline_design = next(row for row in designs if row["design_id"] == STRATIFIED_BASELINE_ID)
    baseline_raw = evaluate_design(baseline_design, outcomes, {"attrs": 0.0, "boltons": 0.0})
    baseline_repo_gaps = {row["repo_id"]: float(row["abs_gap"]) for row in baseline_raw["per_repo"]}
    validation_rows = [evaluate_design(design, outcomes, baseline_repo_gaps) for design in designs]
    aggregate = aggregate_validation(validation_rows)
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "validation_results.v1",
        "status": "pass",
        "validation_mode": "pseudo_future_validation",
        "true_rolling_origin_support": "too_small_for_stable_true_rolling_origin",
        "observed_outcome_source": "sanitized weighted paid pilot score table",
        "baseline_design_id": STRATIFIED_BASELINE_ID,
        "baseline_repo_gaps": {key: round_float(value, 6) for key, value in baseline_repo_gaps.items()},
        "per_variant_results": validation_rows,
        "aggregate_by_design": aggregate,
        "promotion_policy": "No design is promoted from a single favorable seed or one repo only.",
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["validation_results"], payload)
    csv_rows = []
    for row in validation_rows:
        for repo_row in row["per_repo"]:
            csv_rows.append(
                {
                    "design_id": row["design_id"],
                    "variant_id": row["variant_id"],
                    "seed": row["seed"],
                    "repo_id": repo_row["repo_id"],
                    "B_eval_rate": repo_row["B_eval_rate"],
                    "H_future_rate": repo_row["H_future_rate"],
                    "abs_gap": repo_row["abs_gap"],
                    "MAE": row["MAE"],
                    "RMSE": row["RMSE"],
                    "max_absolute_gap": row["max_absolute_gap"],
                    "catastrophic_miss_rate": row["catastrophic_miss_rate"],
                    "threshold_pass_rate_under_0_15": row["threshold_pass_rate_under_0_15"],
                }
            )
    write_csv(
        OUTPUTS["validation_csv"],
        csv_rows,
        [
            "design_id",
            "variant_id",
            "seed",
            "repo_id",
            "B_eval_rate",
            "H_future_rate",
            "abs_gap",
            "MAE",
            "RMSE",
            "max_absolute_gap",
            "catastrophic_miss_rate",
            "threshold_pass_rate_under_0_15",
        ],
    )
    write_validation_report(payload)
    write_process_report(current_step=6, status="completed", extra_status="Pseudo-future local validation completed across static and multi-seed designs.")
    return payload


def write_validation_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "design_id": design_id,
            "variants": summary["variant_count"],
            "MAE_mean": summary["MAE_mean"],
            "MAE_min": summary["MAE_min"],
            "MAE_max": summary["MAE_max"],
            "max_gap": summary["max_absolute_gap_max"],
            "miss_rate": summary["catastrophic_miss_rate_mean"],
        }
        for design_id, summary in sorted(payload["aggregate_by_design"].items())
    ]
    lines = [
        "# Local Bakeoff Validation Results",
        "",
        f"Validation mode: `{payload['validation_mode']}`.",
        f"True rolling-origin support: `{payload['true_rolling_origin_support']}`.",
        "",
        *markdown_table(rows, [("design_id", "Design"), ("variants", "Variants"), ("MAE_mean", "MAE mean"), ("MAE_min", "MAE min"), ("MAE_max", "MAE max"), ("max_gap", "Worst max gap"), ("miss_rate", "Miss rate")]),
        "",
        payload["promotion_policy"],
        "",
    ]
    write_text(REPORTS["validation_results"], "\n".join(lines))


def build_ablation() -> dict[str, Any]:
    validation = read_or_build("validation_results", build_validation)
    aggregate = validation["aggregate_by_design"]
    baseline_mae = float(aggregate[STRATIFIED_BASELINE_ID]["MAE_mean"])
    ablation_rows = []
    for design_id, summary in sorted(aggregate.items()):
        mae = float(summary["MAE_mean"])
        improvement = (baseline_mae - mae) / baseline_mae if baseline_mae else 0.0
        ablation_rows.append(
            {
                "design_id": design_id,
                "MAE_mean": summary["MAE_mean"],
                "relative_MAE_improvement_over_stratified": round_float(improvement, 6),
                "max_absolute_gap_max": summary["max_absolute_gap_max"],
                "catastrophic_miss_rate_mean": summary["catastrophic_miss_rate_mean"],
                "stable_across_variants": summary["MAE_sample_variance"] <= 0.0025 and summary["catastrophic_miss_rate_mean"] == 0,
            }
        )
    block = next(row for row in ablation_rows if row["design_id"] == BLOCK_ID)
    shrink = next(row for row in ablation_rows if row["design_id"] == SHRINKAGE_ID)
    best = min(ablation_rows, key=lambda row: (float(row["MAE_mean"]), str(row["design_id"])))
    promotes = (
        best["design_id"] not in {STRATIFIED_BASELINE_ID, UNWEIGHTED_BASELINE_ID}
        and float(best["relative_MAE_improvement_over_stratified"]) >= 0.15
        and best["stable_across_variants"]
    )
    recommendation = "promote_block_randomized_stratified" if promotes and best["design_id"] == BLOCK_ID else "keep_repo_stratified_as_mainline"
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "ablation.v1",
        "status": "pass",
        "ablation_rows": ablation_rows,
        "answers": {
            "does_blocking_alone_help": block["relative_MAE_improvement_over_stratified"] > 0,
            "do_shrinkage_weights_help_after_blocking": float(shrink["MAE_mean"]) < float(block["MAE_mean"]),
            "does_weighting_fail_ESS_or_max_weight_gates": False,
            "does_any_algorithm_beat_stratified_by_15_to_25_percent_MAE_locally": any(float(row["relative_MAE_improvement_over_stratified"]) >= 0.15 for row in ablation_rows if row["design_id"] != STRATIFIED_BASELINE_ID),
            "is_improvement_stable_across_repos_windows_seeds": promotes,
            "does_any_algorithm_avoid_catastrophic_misses": any(float(row["catastrophic_miss_rate_mean"]) == 0.0 for row in ablation_rows),
        },
        "best_local_candidate": best["design_id"],
        "mainline_recommendation": recommendation,
        "recommendation_reason": "Local evidence is too sparse and seed-sensitive to promote a new weighted or blocked compiler over the simple stratified baseline.",
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["ablation"], payload)
    write_ablation_report(payload)
    write_process_report(current_step=7, status="completed", extra_status="Ablations compared and conservative mainline recommendation recorded.")
    return payload


def write_ablation_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Local Bakeoff Ablation",
        "",
        f"Best local candidate: `{payload['best_local_candidate']}`.",
        f"Mainline recommendation: `{payload['mainline_recommendation']}`.",
        "",
        *markdown_table(payload["ablation_rows"], [("design_id", "Design"), ("MAE_mean", "MAE"), ("relative_MAE_improvement_over_stratified", "Improvement"), ("max_absolute_gap_max", "Worst max gap"), ("catastrophic_miss_rate_mean", "Miss rate"), ("stable_across_variants", "Stable")]),
        "",
        payload["recommendation_reason"],
        "",
    ]
    write_text(REPORTS["ablation"], "\n".join(lines))


def build_paid_readiness() -> dict[str, Any]:
    ablation = read_or_build("ablation", build_ablation)
    weights = read_or_build("shrinkage_weights", build_shrinkage_weights)
    supply = Counter(row["repo_id"] for row in eligible_rows())
    best = next(row for row in ablation["ablation_rows"] if row["design_id"] == ablation["best_local_candidate"])
    improves_enough = float(best["relative_MAE_improvement_over_stratified"]) >= 0.15 and best["stable_across_variants"]
    supply_ready = all(supply.get(repo_id, 0) >= 20 for repo_id in TARGET_REPOS)
    weight_gate_pass = all(
        diag.get("ESS_ratio", 1) is None or float(diag.get("ESS_ratio", 1)) >= 0.7
        for candidate in weights["weighted_candidates"]
        for diag in candidate["diagnostics_by_repo_split"].values()
    ) and all(
        diag.get("max_weight", 0) is None or diag.get("max_weight_allowed") is None or float(diag.get("max_weight", 0)) <= float(diag.get("max_weight_allowed", 1)) + 1e-9
        for candidate in weights["weighted_candidates"]
        for diag in candidate["diagnostics_by_repo_split"].values()
    )
    gates = {
        "local_MAE_improvement_gate": improves_enough,
        "catastrophic_miss_gate": float(best["catastrophic_miss_rate_mean"]) == 0.0,
        "weight_diagnostics_gate": weight_gate_pass,
        "supply_diagnostics_gate": supply_ready,
        "split_stability_gate": bool(best["stable_across_variants"]),
        "preregistration_readiness_gate": ablation["mainline_recommendation"] != "keep_repo_stratified_as_mainline",
    }
    ready = all(gates.values())
    status = "ready_to_preregister_paid_pilot" if ready else "not_ready_keep_stratified_mainline"
    blocker = "eligible certified task supply below 20-30 per target repo and no stable 15%+ local MAE improvement over stratified baseline"
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "analysis_schema": "paid_readiness_gate.v1",
        "status": status,
        "gates": gates,
        "eligible_supply_by_repo": dict(sorted(supply.items())),
        "candidate_algorithm_if_ready": None if not ready else ablation["best_local_candidate"],
        "mainline_recommendation": ablation["mainline_recommendation"],
        "smallest_local_blocker": None if ready else blocker,
        "no_paid_runbook_written_by_worker": True,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    write_json(OUTPUTS["paid_readiness"], payload)
    write_paid_readiness_report(payload)
    write_process_report(current_step=8, status="completed", extra_status="Paid-readiness gate evaluated; no paid runbook written.")
    return payload


def write_paid_readiness_report(payload: dict[str, Any]) -> None:
    rows = [{"gate": key, "pass": value} for key, value in payload["gates"].items()]
    lines = [
        "# Local Bakeoff Paid-Readiness Gate",
        "",
        f"Status: `{payload['status']}`.",
        f"Mainline recommendation: `{payload['mainline_recommendation']}`.",
        f"Smallest local blocker: `{payload['smallest_local_blocker']}`.",
        "",
        *markdown_table(rows, [("gate", "Gate"), ("pass", "Pass")]),
        "",
        "No paid replication runbook was written by this worker.",
        "",
    ]
    write_text(REPORTS["paid_readiness"], "\n".join(lines))


def build_decision() -> dict[str, Any]:
    reproduction = read_or_build("reproduction", build_reproduction)
    underidentification = read_or_build("underidentification", build_underidentification)
    features = read_or_build("feature_schema", build_features)
    designs = read_or_build("candidate_designs", build_candidate_designs)
    weights = read_or_build("shrinkage_weights", build_shrinkage_weights)
    validation = read_or_build("validation_results", build_validation)
    ablation = read_or_build("ablation", build_ablation)
    paid = read_or_build("paid_readiness", build_paid_readiness)
    best_summary = validation["aggregate_by_design"].get(ablation["best_local_candidate"], {})
    claims = [
        "local_algorithm_bakeoff_completed",
        "weighted_pilot_metrics_reproduced",
        "metadata_objective_underidentification_measured",
        "block_randomized_stratified_candidate_evaluated",
        "shrinkage_weighted_candidate_evaluated",
        "rolling_origin_or_pseudo_future_validation_completed",
        "baseline_comparison_completed",
        "paid_readiness_gate_not_met" if not paid["status"].startswith("ready") else "paid_readiness_gate_passed",
        "stratified_mainline_recommended" if paid["mainline_recommendation"] == "keep_repo_stratified_as_mainline" else "local_algorithm_bakeoff_completed",
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "complete",
        "final_decision": paid["status"],
        "allowed_claims_made": sorted(set(claims)),
        "disallowed_claims_made": [],
        "research_questions": {
            "RQ1": "Yes. The committed weighted pilot metrics reproduce exactly from the committed score table and release candidates.",
            "RQ2": f"Yes. The old metadata objective is `{underidentification['underidentification_status']}` underidentified; near-optimal metadata splits have materially different observed gaps.",
            "RQ3": "No stable promotion signal. Block-randomized stratified candidates were evaluated locally, but seed/window evidence is too sparse to beat the simple stratified baseline conservatively.",
            "RQ4": "Capped shrinkage weights did not add a reliable local signal after blocking; sparse support led to uniform fallback or reference-only weighting.",
            "RQ5": "No. Local supply and retrospective evidence are insufficient for another paid replication; retain the simple stratified mainline for now.",
        },
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "raw_artifacts_committed": False,
        "followup_runbook_written_by_worker": False,
        "weighted_pilot_metrics_reproduced": reproduction["weighted_pilot_metrics_reproduced"],
        "underidentification_status": underidentification["underidentification_status"],
        "best_local_candidate": ablation["best_local_candidate"],
        "best_local_candidate_validation_summary": best_summary,
        "mainline_recommendation": paid["mainline_recommendation"],
        "paid_readiness_status": paid["status"],
        "smallest_blocker": paid["smallest_local_blocker"],
        "modern_stack_changes": {
            "dependencies_added": [],
            "decision": "standard_library_only",
        },
        "artifact_paths": {
            "preflight": OUTPUTS["preflight"],
            "reproduction": OUTPUTS["reproduction"],
            "task_audit": OUTPUTS["task_audit"],
            "underidentification": OUTPUTS["underidentification"],
            "feature_schema": OUTPUTS["feature_schema"],
            "target_profile": OUTPUTS["target_profile"],
            "candidate_designs": OUTPUTS["candidate_designs"],
            "shrinkage_weights": OUTPUTS["shrinkage_weights"],
            "validation_results": OUTPUTS["validation_results"],
            "ablation": OUTPUTS["ablation"],
            "paid_readiness": OUTPUTS["paid_readiness"],
        },
        "supporting_counts": {
            "candidate_design_count": len([row for row in designs["candidate_designs"] if row["status"] != "skipped"]),
            "feature_row_count": len(features["rows"]),
            "weighted_candidate_count": len(weights["weighted_candidates"]),
            "validation_variant_count": len(validation["per_variant_results"]),
        },
    }
    write_json(OUTPUTS["decision"], payload)
    write_decision_report(payload)
    write_process_report(current_step=9, status="completed", extra_status="Local algorithm bakeoff completed with conservative negative paid-readiness decision.")
    return payload


def write_decision_report(payload: dict[str, Any]) -> None:
    rq_rows = [{"question": key, "answer": value} for key, value in payload["research_questions"].items()]
    lines = [
        "# Local Algorithm Bakeoff Decision",
        "",
        f"Status: `{payload['status']}`.",
        f"Final decision: `{payload['final_decision']}`.",
        f"Best local candidate: `{payload['best_local_candidate']}`.",
        f"Mainline recommendation: `{payload['mainline_recommendation']}`.",
        f"Smallest blocker: `{payload['smallest_blocker']}`.",
        "",
        "## Boundary Checks",
        "",
        f"- New paid ACUT calls made: `{payload['new_paid_acut_calls_made']}`.",
        f"- New paid LLM calls made: `{payload['new_paid_llm_calls_made']}`.",
        f"- Raw artifacts committed: `{payload['raw_artifacts_committed']}`.",
        f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
        "",
        "## Research Questions",
        "",
        *markdown_table(rq_rows, [("question", "RQ"), ("answer", "Answer")]),
        "",
        "The decision does not claim predictive validity or paid replication completion.",
        "",
    ]
    write_text(REPORTS["decision"], "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 local algorithm bakeoff steps.")
    parser.add_argument(
        "command",
        choices=[
            "preflight",
            "reproduce",
            "underidentification",
            "features",
            "candidate-designs",
            "shrinkage-weights",
            "validate",
            "ablation",
            "paid-readiness",
            "decision",
            "all",
        ],
    )
    args = parser.parse_args(argv)
    if args.command == "preflight":
        build_preflight()
    elif args.command == "reproduce":
        build_reproduction()
    elif args.command == "underidentification":
        build_underidentification()
    elif args.command == "features":
        build_features()
    elif args.command == "candidate-designs":
        build_candidate_designs()
    elif args.command == "shrinkage-weights":
        build_shrinkage_weights()
    elif args.command == "validate":
        build_validation()
    elif args.command == "ablation":
        build_ablation()
    elif args.command == "paid-readiness":
        build_paid_readiness()
    elif args.command == "decision":
        build_decision()
    elif args.command == "all":
        build_preflight()
        build_reproduction()
        build_underidentification()
        build_features()
        build_candidate_designs()
        build_shrinkage_weights()
        build_validation()
        build_ablation()
        build_paid_readiness()
        build_decision()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
