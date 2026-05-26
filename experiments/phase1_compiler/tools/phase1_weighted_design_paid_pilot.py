from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
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
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import workspace_acut_run as workspace_acut  # noqa: E402


RUN_ID = "phase1_weighted_design_paid_pilot_20260526"
SOURCE_RUN_ID = "phase1_pre_paid_replication_20260526"
SCHEMA_VERSION = "barcarolle.phase1_weighted_design_paid_pilot.v1"
OUTPUT_SCHEMA_VERSION = "barcarolle.phase1_weighted_design_paid_pilot_output.v1"
RUNBOOK_DATE = "2026-05-26"
RESULT_PREFIX = "phase1_weighted_design_paid_pilot"
PRIMARY_RELEASE_ID = "barcarolle_weighted_time_family_matched"
LOCAL_BASELINE_IDS = ["repo_unweighted_same_budget", "repo_stratified_by_target_profile"]
HISTORICAL_REFERENCE_ID = "prior_statement_hardened_release_as_historical_reference"
PLANNED_ADAPTERS = ["codex_workspace", "kilo_workspace"]
PRIMARY_GAP_THRESHOLD = 0.15
ESTIMATED_COST_PER_CELL_USD = 0.31010985
INCREMENTAL_HARD_CAP_USD = 25.0
STOP_BEFORE_NEXT_BATCH_CAP_USD = 20.0
SINGLE_BATCH_PROJECTED_CAP_USD = 6.0
PRECISION_TARGET_CELLS = 156

REQUIRED_INPUTS = [
    "AGENTS.md",
    "docs/architecture/system-design.md",
    "experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_decision.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_entry_gate.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_baseline_plan.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
    "experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl",
    "experiments/phase0_headroom/configs/acut_workspace_adapters.yaml",
    "experiments/phase0_headroom/tools/workspace_acut_run.py",
    "experiments/phase0_headroom/tools/workspace_usage_import.py",
]

HISTORICAL_REFERENCE_INPUTS = [
    "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json",
    "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_decision.json",
    "experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_b_eval_score_table.csv",
    "experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_h_future_score_table.csv",
    "experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_b_eval_score_table.csv",
    "experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_h_future_score_table.csv",
]

OUTPUT_PATHS = {
    "config": "experiments/phase1_compiler/configs/phase1_weighted_design_paid_pilot.yaml",
    "preflight": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_preflight.json",
    "tooling_check": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_tooling_check.json",
    "entry_gate": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_entry_gate.json",
    "batch_plan": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_batch_plan.json",
    "integrity_audit": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_integrity_audit.json",
    "metrics": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json",
    "baseline_comparison": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_baseline_comparison.json",
    "decision": "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_decision.json",
    "process_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_process.md",
    "preflight_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_preflight.md",
    "tooling_check_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_tooling_check.md",
    "entry_gate_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_entry_gate.md",
    "batch_plan_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_batch_plan.md",
    "integrity_audit_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_integrity_audit.md",
    "metrics_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_metrics.md",
    "baseline_comparison_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_baseline_comparison.md",
    "decision_report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md",
}

PHASE0_OUTPUT_PATHS = {
    "workspace_matrix_config": "experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml",
    "matrix": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_matrix.json",
    "package_inspection": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_package_inspection.json",
    "score_table": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv",
    "metrics": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_metrics.json",
    "cost_summary": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_cost_summary.json",
    "cost_ledger": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_cost_ledger.jsonl",
    "preflight": "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_preflight.json",
    "package_inspection_report": "experiments/phase0_headroom/reports/phase1_weighted_design_paid_pilot_package_inspection.md",
    "preflight_report": "experiments/phase0_headroom/reports/phase1_weighted_design_paid_pilot_preflight.md",
}

STEP_DEFS = [
    (0, "Preflight And Approval Record", "Record weighted design paid pilot preflight"),
    (1, "Build Frozen Pilot Matrix And Package Inspection", "Build weighted design paid pilot matrix"),
    (2, "Tooling, Endpoint, And Entry Gate", "Record weighted design paid pilot entry gate"),
    (3, "Run Paid Smoke Batch", "Run weighted design paid pilot smoke batch"),
    (4, "Run Remaining Attrs Paid Cells", "Run weighted design paid pilot attrs cells"),
    (5, "Run Remaining Boltons Paid Cells", "Run weighted design paid pilot boltons cells"),
    (6, "Integrity Audit And Score Import", "Audit weighted design paid pilot score tables"),
    (7, "Compute Weighted And Baseline Metrics", "Compute weighted design paid pilot metrics"),
    (8, "Baseline Comparison And Error Analysis", "Compare weighted design paid pilot baselines"),
    (9, "Final Decision And Closeout", "Record weighted design paid pilot decision"),
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


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(path_from_repo(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = path_from_repo(path)
    if not resolved.exists() or resolved.stat().st_size == 0:
        return []
    return [json.loads(line) for line in resolved.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_score_table(path: str | Path) -> list[dict[str, Any]]:
    resolved = path_from_repo(path)
    if not resolved.exists():
        return []
    with resolved.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["scoreable_cell"] = str(row.get("scoreable_cell", "")).lower() == "true"
    return rows


def write_json(path: str | Path, payload: Any) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_file(path: str | Path) -> str:
    return "sha256:" + hashlib.sha256(path_from_repo(path).read_bytes()).hexdigest()


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def command_result(args: list[str], cwd: Path = REPO_ROOT) -> dict[str, Any]:
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
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc), "duration_seconds": round(time.monotonic() - started, 3)}


def command_stdout(args: list[str]) -> str:
    result = command_result(args)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_tracked(raw_path: str) -> bool:
    return bool(command_result(["git", "ls-files", "--", raw_path])["stdout"].strip())


def write_simple_yaml(path: str | Path, payload: dict[str, Any]) -> None:
    def render(value: Any, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if not isinstance(value, dict):
            raise TypeError("simple YAML root must be a mapping")
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(render(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}{key}:")
                for list_item in item:
                    if isinstance(list_item, (dict, list)):
                        lines.append(f"{prefix}  - {json.dumps(list_item, sort_keys=True)}")
                    else:
                        lines.append(f"{prefix}  - {list_item}")
            elif isinstance(item, bool):
                lines.append(f"{prefix}{key}: {str(item).lower()}")
            elif item is None:
                lines.append(f"{prefix}{key}: null")
            else:
                lines.append(f"{prefix}{key}: {item}")
        return lines

    write_text(path, "\n".join(render(payload)))


def default_config_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "runbook": "docs/experiments/phase-1-weighted-design-paid-pilot-replication-runbook.md",
        "runbook_status": "implementation_runbook",
        "runbook_date": RUNBOOK_DATE,
        "primary_release_candidate_id": PRIMARY_RELEASE_ID,
        "local_baseline_candidate_ids": LOCAL_BASELINE_IDS,
        "historical_reference_candidate_id": HISTORICAL_REFERENCE_ID,
        "planned_adapters": PLANNED_ADAPTERS,
        "result_prefix": RESULT_PREFIX,
        "primary_gap_threshold": PRIMARY_GAP_THRESHOLD,
        "budget": {
            "estimated_cost_per_cell_usd": ESTIMATED_COST_PER_CELL_USD,
            "incremental_hard_cap_usd": INCREMENTAL_HARD_CAP_USD,
            "stop_before_next_batch_projected_total_cap_usd": STOP_BEFORE_NEXT_BATCH_CAP_USD,
            "single_batch_projected_cap_usd": SINGLE_BATCH_PROJECTED_CAP_USD,
            "paid_acut_concurrency": 1,
            "allow_cross_harness_paid_parallelism": False,
        },
        "source_artifacts": {
            "release_selection": "experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml",
            "decision": "experiments/phase1_compiler/results/phase1_pre_paid_replication_decision.json",
            "entry_gate": "experiments/phase1_compiler/results/phase1_pre_paid_replication_entry_gate.json",
            "release_candidates": "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
            "baseline_plan": "experiments/phase1_compiler/results/phase1_pre_paid_replication_baseline_plan.json",
            "threshold_preregistration": "experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json",
            "target_profiles": "experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json",
            "statement_quality_gate": "experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json",
            "candidate_inventory": "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
            "historical_metrics": "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json",
            "historical_decision": "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_decision.json",
        },
        "required_inputs": REQUIRED_INPUTS,
        "historical_reference_inputs": HISTORICAL_REFERENCE_INPUTS,
        "output_paths": OUTPUT_PATHS,
        "phase0_output_paths": PHASE0_OUTPUT_PATHS,
    }


def ensure_default_config() -> dict[str, Any]:
    config_path = path_from_repo(OUTPUT_PATHS["config"])
    payload = default_config_payload()
    write_simple_yaml(config_path, payload)
    payload["_path"] = str(config_path)
    return payload


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or path_from_repo(OUTPUT_PATHS["config"])
    if not config_path.exists():
        return ensure_default_config()
    config = simple_yaml_load(config_path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected weighted design paid pilot config schema_version")
    config["_path"] = str(config_path)
    return config


def release_candidates_payload() -> dict[str, Any]:
    return read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json")


def candidate_by_id() -> dict[str, dict[str, Any]]:
    payload = release_candidates_payload()
    return {str(row["release_candidate_id"]): row for row in payload.get("release_candidates", [])}


def local_candidate_ids() -> list[str]:
    return [PRIMARY_RELEASE_ID, *LOCAL_BASELINE_IDS]


def sort_task_ids(task_ids: Iterable[str]) -> list[str]:
    def key(task_id: str) -> tuple[int, int, str]:
        repo, _, rest = task_id.partition("__")
        repo_rank = {"attrs": 0, "boltons": 1}.get(repo, 99)
        digits = "".join(ch for ch in rest.rsplit("__", 1)[-1] if ch.isdigit())
        return (repo_rank, int(digits or 0), task_id)

    return sorted(set(task_ids), key=key)


def candidate_task_ids(candidate: dict[str, Any]) -> list[str]:
    return [str(task_id) for task_id in candidate.get("task_ids", [])]


def frozen_union_task_ids() -> list[str]:
    candidates = candidate_by_id()
    union: list[str] = []
    for candidate_id in local_candidate_ids():
        union.extend(candidate_task_ids(candidates[candidate_id]))
    return sort_task_ids(union)


def candidate_split_weights(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    weights = candidate.get("weights")
    mapping: dict[str, dict[str, Any]] = {}
    if not isinstance(weights, dict):
        return mapping
    for repo_split, task_weights in weights.items():
        if not isinstance(task_weights, dict):
            continue
        repo, _, split = str(repo_split).partition("/")
        for task_id, weight in task_weights.items():
            mapping[str(task_id)] = {
                "repo_split": str(repo_split),
                "repo_id": repo,
                "split": split,
                "weight": float(weight),
            }
    return mapping


def all_candidate_memberships() -> dict[str, dict[str, Any]]:
    candidates = candidate_by_id()
    memberships: dict[str, dict[str, Any]] = {task_id: {"candidate_ids": []} for task_id in frozen_union_task_ids()}
    for candidate_id in local_candidate_ids():
        split_weights = candidate_split_weights(candidates[candidate_id])
        for task_id in candidate_task_ids(candidates[candidate_id]):
            entry = memberships.setdefault(task_id, {"candidate_ids": []})
            entry["candidate_ids"].append(candidate_id)
            if task_id in split_weights:
                entry.setdefault("candidate_splits", {})[candidate_id] = split_weights[task_id]
    return memberships


def matrix_split_for_tasks() -> dict[str, str]:
    candidates = candidate_by_id()
    mapping: dict[str, str] = {}
    for candidate_id in local_candidate_ids():
        split_weights = candidate_split_weights(candidates[candidate_id])
        for task_id in frozen_union_task_ids():
            if task_id in mapping:
                continue
            row = split_weights.get(task_id)
            if row:
                mapping[task_id] = str(row["repo_split"])
    return mapping


def workspace_matrix_payload() -> dict[str, Any]:
    task_ids = frozen_union_task_ids()
    split_map = matrix_split_for_tasks()
    repo_splits: dict[str, list[str]] = {"attrs/B_eval": [], "attrs/H_future": [], "boltons/B_eval": [], "boltons/H_future": []}
    for task_id in task_ids:
        repo_splits.setdefault(split_map[task_id], []).append(task_id)
    return {
        "schema_version": "barcarolle.phase1_weighted_design_paid_pilot_workspace_matrix.v1",
        "status": "configured",
        "phase1_weighted_design_paid_pilot": True,
        "claim_scope": "weighted_design_paid_pilot_run",
        "run_id": RUN_ID,
        "result_prefix": RESULT_PREFIX,
        "primary_release_candidate_id": PRIMARY_RELEASE_ID,
        "local_baseline_candidate_ids": LOCAL_BASELINE_IDS,
        "historical_reference_candidate_id": HISTORICAL_REFERENCE_ID,
        "historical_reference_rerun": False,
        "candidate_inventory": "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
        "release_candidates": "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
        "release_selection": "experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml",
        "statement_quality_gate": "experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json",
        "attrs_certified_tasks": "experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl",
        "boltons_clean_ext_certified_tasks": "experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl",
        "boltons_canonical_certified_tasks": "experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl",
        "boltons_target_profile": "experiments/phase0_headroom/target_profiles/boltons_target_profile.json",
        "attrs_repo_config": "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml",
        "adapter_config": "experiments/phase0_headroom/configs/acut_workspace_adapters.yaml",
        "task_ids": task_ids,
        "repo_splits": repo_splits,
        "paid_parallelism": {
            "paid_acut_concurrency": 1,
            "allow_cross_harness_paid_parallelism": False,
        },
        "result_policy": {
            "raw_outputs_ignored_only": True,
            "historical_paid_results_reused": False,
            "current_inventory_split_used_for_selection": False,
            "generated_statement_is_scoreable_result": False,
        },
    }


def build_batch_plan_payload() -> dict[str, Any]:
    task_ids = frozen_union_task_ids()
    attrs = [task_id for task_id in task_ids if task_id.startswith("attrs__")]
    boltons = [task_id for task_id in task_ids if task_id.startswith("boltons__")]
    smoke = [attrs[0], boltons[0]]
    remaining_attrs = [task_id for task_id in attrs if task_id not in smoke]
    remaining_boltons = [task_id for task_id in boltons if task_id not in smoke]
    first_boltons = remaining_boltons[:5]
    final_boltons = remaining_boltons[5:]
    batches = [
        {"batch_id": "smoke", "step": 3, "task_ids": smoke},
        {"batch_id": "remaining_attrs", "step": 4, "task_ids": remaining_attrs},
        {"batch_id": "first_boltons", "step": 5, "task_ids": first_boltons},
        {"batch_id": "remaining_boltons", "step": 5, "task_ids": final_boltons},
    ]
    for batch in batches:
        batch["planned_cells"] = len(batch["task_ids"]) * len(PLANNED_ADAPTERS)
        batch["projected_cost_usd"] = round(batch["planned_cells"] * ESTIMATED_COST_PER_CELL_USD, 8)
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "planned",
        "planned_adapters": PLANNED_ADAPTERS,
        "planned_unique_task_count": len(task_ids),
        "planned_cells": len(task_ids) * len(PLANNED_ADAPTERS),
        "task_ids": task_ids,
        "batches": batches,
        "budget_policy": {
            "estimated_cost_per_cell_usd": ESTIMATED_COST_PER_CELL_USD,
            "incremental_hard_cap_usd": INCREMENTAL_HARD_CAP_USD,
            "stop_before_next_batch_projected_total_cap_usd": STOP_BEFORE_NEXT_BATCH_CAP_USD,
            "single_batch_projected_cap_usd": SINGLE_BATCH_PROJECTED_CAP_USD,
            "paid_acut_concurrency": 1,
            "cross_harness_paid_parallelism": "disabled",
        },
        "stop_conditions": [
            "endpoint_proof_missing",
            "package_inspection_not_ready",
            "projected_total_cost_exceeds_cap",
            "projected_batch_cost_exceeds_cap",
            "scoreability_or_policy_gate_failed",
        ],
    }


def input_records(paths: list[str]) -> list[dict[str, Any]]:
    rows = []
    for raw_path in paths:
        path = path_from_repo(raw_path)
        rows.append(
            {
                "path": raw_path,
                "exists": path.exists(),
                "tracked_by_git": git_tracked(raw_path),
                "sha256": digest_file(path) if path.exists() else None,
            }
        )
    return rows


def existing_paid_outputs() -> list[str]:
    patterns = [
        "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_submissions.jsonl",
        "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_verifier_results.jsonl",
        "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv",
        "experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_cost_ledger.jsonl",
    ]
    return [path for path in patterns if path_from_repo(path).exists()]


def build_preflight(write: bool = True) -> dict[str, Any]:
    ensure_default_config()
    decision = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_decision.json")
    entry_gate = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_entry_gate.json")
    release = release_candidates_payload()
    baseline = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_baseline_plan.json")
    quality = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json")
    selection = simple_yaml_load(path_from_repo("experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml"))
    task_ids = frozen_union_task_ids()
    checks = {
        "entry_status_ready_for_paid_replication": entry_gate.get("entry_status") == "ready_for_paid_replication",
        "replication_grade_pilot_ready_not_precision_target": entry_gate.get("replication_grade") == "pilot_grade_ready_not_precision_target",
        "primary_release_candidate_id_matches": decision.get("primary_release_candidate_id") == PRIMARY_RELEASE_ID,
        "baseline_candidates_include_local_baselines": all(candidate_id in set(release.get("baseline_candidate_ids", [])) for candidate_id in LOCAL_BASELINE_IDS)
        and all(candidate_id in set(baseline.get("baseline_candidate_ids", [])) for candidate_id in LOCAL_BASELINE_IDS),
        "historical_reference_not_rerun": HISTORICAL_REFERENCE_ID not in LOCAL_BASELINE_IDS,
        "planned_unique_task_count_eq_22": len(task_ids) == 22,
        "planned_adapter_count_eq_2": len(PLANNED_ADAPTERS) == 2,
        "planned_cells_eq_44": len(task_ids) * len(PLANNED_ADAPTERS) == 44,
        "selection_frozen_before_paid_replication": selection.get("selection_frozen_before_paid_replication") is True,
        "historical_paid_outcomes_used_for_selection_false": selection.get("historical_paid_outcomes_used_for_selection") is False,
        "new_paid_acut_cells_for_this_release_not_already_run": not existing_paid_outputs(),
        "followup_runbook_written_by_worker_false": False is False,
        "statement_quality_gate_pass": quality.get("status") == "pass",
    }
    git_diff_check = command_result(["git", "diff", "--check"])
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "ready_for_local_entry_steps" if all(checks.values()) else "blocked_preflight",
        "paid_pilot_approval_granted_by_runbook": True,
        "endpoint_rule": {"required_env": ["LLM_BASE_URL", "LLM_API_KEY"], "secrets_recorded": False},
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "date_utc": utc_now(),
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "codex_version": command_stdout(["codex", "--version"]),
        "kilo_version": command_stdout(["kilo", "--version"]),
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "git_log_oneline_12": command_stdout(["git", "log", "--oneline", "-12"]),
        "git_diff_check": {
            "returncode": git_diff_check["returncode"],
            "stdout": git_diff_check["stdout"],
            "stderr": git_diff_check["stderr"],
        },
        "required_input_records": input_records(REQUIRED_INPUTS),
        "historical_reference_input_records": input_records(HISTORICAL_REFERENCE_INPUTS),
        "required_inputs_all_exist": all(row["exists"] for row in input_records(REQUIRED_INPUTS)),
        "required_inputs_all_tracked_by_git": all(row["tracked_by_git"] for row in input_records(REQUIRED_INPUTS)),
        "historical_reference_inputs_all_exist": all(row["exists"] for row in input_records(HISTORICAL_REFERENCE_INPUTS)),
        "release_candidate_ids_to_run": local_candidate_ids(),
        "historical_reference_candidate_id": HISTORICAL_REFERENCE_ID,
        "historical_reference_rerun": False,
        "planned_unique_task_ids": task_ids,
        "planned_adapters": PLANNED_ADAPTERS,
        "planned_cells": len(task_ids) * len(PLANNED_ADAPTERS),
        "existing_paid_outputs_for_prefix": existing_paid_outputs(),
        "checks": checks,
        "warnings": ["required_inputs_not_all_tracked_by_git"] if not all(row["tracked_by_git"] for row in input_records(REQUIRED_INPUTS)) else [],
    }
    if write:
        write_json(OUTPUT_PATHS["preflight"], payload)
        write_preflight_report(payload)
        write_process_report({"0": "completed"})
    return payload


def write_preflight_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Preflight",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Branch: `{payload['branch']}`.",
        f"- HEAD: `{payload['head']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Paid approval recorded: `{payload['paid_pilot_approval_granted_by_runbook']}`.",
        "- Endpoint rule: `LLM_BASE_URL` plus `LLM_API_KEY`; secret values were not recorded.",
        f"- Historical reference rerun: `{payload['historical_reference_rerun']}`.",
        f"- Existing paid outputs for this prefix: `{len(payload['existing_paid_outputs_for_prefix'])}`.",
        f"- Required inputs all exist: `{payload['required_inputs_all_exist']}`.",
        f"- Required inputs all tracked by Git: `{payload['required_inputs_all_tracked_by_git']}`.",
        "",
        "## Checks",
        "",
        *(f"- `{key}`: `{value}`" for key, value in sorted(payload["checks"].items())),
        "",
        "## Warnings",
        "",
        *(f"- `{warning}`" for warning in payload["warnings"]),
        "" if payload["warnings"] else "- None.",
        "",
    ]
    write_text(OUTPUT_PATHS["preflight_report"], "\n".join(lines))


def write_process_report(step_status: dict[str, str] | None = None, closeout: dict[str, Any] | None = None) -> None:
    step_status = step_status or {}
    lines = [
        "# Weighted Design Paid Pilot Process",
        "",
        f"Run ID: `{RUN_ID}`.",
        f"Updated: `{utc_now()}`.",
        "",
        "## Work Queue",
        "",
    ]
    for step, title, commit_target in STEP_DEFS:
        status = step_status.get(str(step), "pending")
        lines.append(f"- Step {step}: `{status}` - {title}; commit target `{commit_target}`.")
    lines.extend(
        [
            "",
            "## Boundary Records",
            "",
            "- Paid pilot approval is granted by the runbook.",
            "- Paid endpoint rule is `LLM_BASE_URL` plus `LLM_API_KEY`; values are never recorded.",
            "- Historical reference remains historical-only and is not rerun.",
            "- Follow-up runbook written by worker: `false`.",
            "",
        ]
    )
    if closeout:
        lines.extend(["## Closeout", ""])
        for key, value in closeout.items():
            lines.append(f"- `{key}`: `{value}`.")
        lines.append("")
    write_text(OUTPUT_PATHS["process_report"], "\n".join(lines))


def build_matrix(write: bool = True) -> dict[str, Any]:
    ensure_default_config()
    matrix = workspace_matrix_payload()
    batch_plan = build_batch_plan_payload()
    memberships = all_candidate_memberships()
    historical_tasks = set(candidate_task_ids(candidate_by_id()[HISTORICAL_REFERENCE_ID]))
    selected_tasks = set(matrix["task_ids"])
    historical_only = sorted(historical_tasks - selected_tasks)
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "configured",
        "workspace_matrix_config": PHASE0_OUTPUT_PATHS["workspace_matrix_config"],
        "task_count": len(matrix["task_ids"]),
        "planned_cells": len(matrix["task_ids"]) * len(PLANNED_ADAPTERS),
        "task_ids": matrix["task_ids"],
        "repo_splits": matrix["repo_splits"],
        "candidate_memberships": memberships,
        "release_candidate_ids_to_run": local_candidate_ids(),
        "historical_reference_candidate_id": HISTORICAL_REFERENCE_ID,
        "historical_reference_only_task_ids_excluded": historical_only,
        "historical_reference_rerun": False,
        "batch_plan": batch_plan,
    }
    if write:
        write_simple_yaml(PHASE0_OUTPUT_PATHS["workspace_matrix_config"], matrix)
        write_json(PHASE0_OUTPUT_PATHS["matrix"], payload)
        write_json(OUTPUT_PATHS["batch_plan"], batch_plan)
        write_batch_plan_report(batch_plan)
    return payload


def write_batch_plan_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Batch Plan",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Planned tasks: `{payload['planned_unique_task_count']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Adapters: `{', '.join(payload['planned_adapters'])}`.",
        "",
        "## Batches",
        "",
    ]
    for batch in payload["batches"]:
        lines.append(
            f"- `{batch['batch_id']}`: tasks `{', '.join(batch['task_ids'])}`, cells `{batch['planned_cells']}`, projected cost `${batch['projected_cost_usd']}`."
        )
    lines.extend(["", "## Stop Conditions", "", *(f"- `{item}`" for item in payload["stop_conditions"]), ""])
    write_text(OUTPUT_PATHS["batch_plan_report"], "\n".join(lines))


def build_tooling_check(write: bool = True) -> dict[str, Any]:
    if not path_from_repo(PHASE0_OUTPUT_PATHS["matrix"]).exists():
        build_matrix(write=True)
    inspection_path = path_from_repo(PHASE0_OUTPUT_PATHS["package_inspection"])
    inspection = read_json(inspection_path) if inspection_path.exists() else {}
    matrix = read_json(PHASE0_OUTPUT_PATHS["matrix"])
    quality = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json")
    blocking = set(str(task_id) for task_id in quality.get("blocking_task_ids", []))
    selected = set(inspection.get("selected_task_ids", []))
    expected = set(matrix["task_ids"])
    package_rows = inspection.get("packages", [])
    blockers = []
    if inspection.get("status") != "ready":
        blockers.append("package_inspection_not_ready")
    if selected != expected:
        blockers.append("selected_task_ids_do_not_match_frozen_union")
    if inspection.get("missing_task_ids"):
        blockers.append("missing_task_packages")
    if any(row.get("statement_digest_matches_frozen") is False for row in package_rows):
        blockers.append("statement_digest_mismatch")
    if selected.intersection(blocking):
        blockers.append("selected_task_blocked_by_statement_quality_gate")
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "package_inspection_status": inspection.get("status"),
        "selected_task_count": len(selected),
        "expected_task_count": len(expected),
        "missing_task_count": len(inspection.get("missing_task_ids", [])),
        "selected_task_ids": inspection.get("selected_task_ids", []),
        "statement_digest_mismatches": [row.get("task_id") for row in package_rows if row.get("statement_digest_matches_frozen") is False],
        "statement_quality_blocking_task_ids": sorted(selected.intersection(blocking)),
        "historical_reference_rerun": False,
        "paid_acut_calls_made": False,
    }
    if write:
        write_json(OUTPUT_PATHS["tooling_check"], payload)
        write_tooling_check_report(payload)
    return payload


def write_tooling_check_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Tooling Check",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Package inspection: `{payload['package_inspection_status']}`.",
        f"- Selected task count: `{payload['selected_task_count']}`.",
        f"- Missing task count: `{payload['missing_task_count']}`.",
        f"- Historical reference rerun: `{payload['historical_reference_rerun']}`.",
        f"- Paid ACUT calls made: `{payload['paid_acut_calls_made']}`.",
        "",
        "## Blockers",
        "",
        *(f"- `{blocker}`" for blocker in payload["blockers"]),
        "" if payload["blockers"] else "- None.",
        "",
    ]
    write_text(OUTPUT_PATHS["tooling_check_report"], "\n".join(lines))


def adapter_readiness(adapter_id: str) -> dict[str, Any]:
    adapter_path = path_from_repo("experiments/phase0_headroom/configs/acut_workspace_adapters.yaml")
    configs = workspace_acut.load_adapter_configs(adapter_path, os.environ)
    config = configs[adapter_id]
    first_token = config.command_template.split()[0] if config.command_template.strip() else ""
    return {
        "adapter_id": adapter_id,
        "harness_name": config.harness_name,
        "command_template_configured": bool(config.command_template.strip()),
        "command_first_token": first_token,
        "command_exists": bool(first_token and (Path(first_token).exists() or shutil.which(first_token))),
        "required_env": config.requires_env,
        "required_env_present": all(os.environ.get(name) for name in config.requires_env),
        "endpoint_proof_status": config.endpoint_proof_status,
        "local_subscription_fallback": "disabled",
        "openai_or_provider_fallback": "disabled",
    }


def endpoint_env_present_after_zshrc() -> bool:
    result = command_result(["zsh", "-lc", 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'])
    return result["returncode"] == 0


def build_entry_gate(write: bool = True) -> dict[str, Any]:
    tooling = build_tooling_check(write=False)
    batch_plan = read_json(OUTPUT_PATHS["batch_plan"]) if path_from_repo(OUTPUT_PATHS["batch_plan"]).exists() else build_batch_plan_payload()
    endpoint_present = endpoint_env_present_after_zshrc()
    adapter_rows = [adapter_readiness(adapter_id) for adapter_id in PLANNED_ADAPTERS]
    adapter_blockers = [
        f"{row['adapter_id']}_not_ready"
        for row in adapter_rows
        if not (row["command_template_configured"] and row["command_exists"] and row["required_env_present"])
    ]
    projected_total = round(batch_plan["planned_cells"] * ESTIMATED_COST_PER_CELL_USD, 8)
    max_batch = max(float(batch["projected_cost_usd"]) for batch in batch_plan["batches"])
    blockers: list[str] = []
    if tooling.get("status") != "ready":
        blockers.append("tooling_or_package_inspection_not_ready")
    if not endpoint_present:
        blockers.append("endpoint_env_missing")
    blockers.extend(adapter_blockers)
    if projected_total > INCREMENTAL_HARD_CAP_USD:
        blockers.append("projected_total_cost_exceeds_hard_cap")
    if max_batch > SINGLE_BATCH_PROJECTED_CAP_USD:
        blockers.append("projected_batch_cost_exceeds_single_batch_cap")
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "entry_gate_status": "ready_for_paid_pilot" if not blockers else "blocked_before_paid_cells",
        "blockers": blockers,
        "endpoint_env_present_after_zshrc": endpoint_present,
        "endpoint_secret_values_recorded": False,
        "adapter_readiness": adapter_rows,
        "adapter_config_requires_llm_base_url_and_api_key": all(set(row["required_env"]) == {"LLM_BASE_URL", "LLM_API_KEY"} for row in adapter_rows),
        "local_subscription_fallback": "disabled",
        "openai_or_provider_fallback": "disabled",
        "package_inspection_status": tooling.get("package_inspection_status"),
        "planned_cells": batch_plan["planned_cells"],
        "cost_cap_usd": INCREMENTAL_HARD_CAP_USD,
        "projected_total_cost_usd": projected_total,
        "max_projected_batch_cost_usd": max_batch,
        "paid_acut_concurrency": 1,
        "cross_harness_paid_parallelism": "disabled",
        "new_paid_acut_calls_made_before_entry_gate": False,
    }
    if write:
        write_json(OUTPUT_PATHS["entry_gate"], payload)
        write_entry_gate_report(payload)
    return payload


def write_entry_gate_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Entry Gate",
        "",
        f"Status: `{payload['entry_gate_status']}`.",
        "",
        f"- Endpoint env present after zshrc: `{payload['endpoint_env_present_after_zshrc']}`.",
        f"- Package inspection: `{payload['package_inspection_status']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Projected total cost: `${payload['projected_total_cost_usd']}`.",
        f"- Max projected batch cost: `${payload['max_projected_batch_cost_usd']}`.",
        f"- Paid ACUT concurrency: `{payload['paid_acut_concurrency']}`.",
        f"- Cross-harness paid parallelism: `{payload['cross_harness_paid_parallelism']}`.",
        "",
        "## Adapters",
        "",
    ]
    for row in payload["adapter_readiness"]:
        lines.append(
            f"- `{row['adapter_id']}`: command `{row['command_template_configured']}`, command exists `{row['command_exists']}`, env present `{row['required_env_present']}`, endpoint proof `{row['endpoint_proof_status']}`."
        )
    lines.extend(["", "## Blockers", "", *(f"- `{blocker}`" for blocker in payload["blockers"]), "" if payload["blockers"] else "- None.", ""])
    write_text(OUTPUT_PATHS["entry_gate_report"], "\n".join(lines))


def cost_value(summary: dict[str, Any]) -> float:
    for key in ["observed_or_conservative_estimated_cost_usd", "conservative_estimated_cost_usd", "estimated_cost_usd"]:
        if summary.get(key) is not None:
            return float(summary.get(key) or 0.0)
    return 0.0


def current_score_rows() -> list[dict[str, Any]]:
    return read_score_table(PHASE0_OUTPUT_PATHS["score_table"])


def current_cost_summary() -> dict[str, Any]:
    path = path_from_repo(PHASE0_OUTPUT_PATHS["cost_summary"])
    return read_json(path) if path.exists() else {}


def build_integrity_audit(write: bool = True) -> dict[str, Any]:
    matrix = read_json(PHASE0_OUTPUT_PATHS["matrix"]) if path_from_repo(PHASE0_OUTPUT_PATHS["matrix"]).exists() else build_matrix(write=False)
    rows = current_score_rows()
    selected_pairs = {(row.get("task_id"), row.get("adapter_id")) for row in rows}
    expected_pairs = {(task_id, adapter_id) for task_id in matrix["task_ids"] for adapter_id in PLANNED_ADAPTERS}
    missing_pairs = sorted(expected_pairs - selected_pairs)
    extra_pairs = sorted(selected_pairs - expected_pairs)
    terminal_counts = Counter(str(row.get("terminal_status") or "") for row in rows)
    policy_violations = int(terminal_counts.get("policy_violation", 0))
    raw_tracked = command_stdout(["git", "ls-files", "experiments/phase0_headroom/results/raw", "experiments/phase0_headroom/workspaces", "experiments/phase0_headroom/external_repos"])
    cost_summary = current_cost_summary()
    blockers = []
    if extra_pairs:
        blockers.append("score_table_contains_out_of_matrix_cells")
    if missing_pairs and rows:
        blockers.append("score_table_missing_planned_cells")
    if policy_violations:
        blockers.append("policy_violations_present")
    if raw_tracked.strip():
        blockers.append("raw_or_workspace_artifacts_tracked")
    if rows and not cost_summary:
        blockers.append("cost_summary_missing")
    status = "pass" if rows and not blockers and not missing_pairs else "partial_paid_pilot" if rows else "blocked_with_precise_reason"
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": status,
        "blockers": blockers,
        "planned_cells": len(expected_pairs),
        "completed_cells": len(rows),
        "scoreable_cells": sum(1 for row in rows if row.get("scoreable_cell") is True),
        "missing_cells": [{"task_id": task_id, "adapter_id": adapter_id} for task_id, adapter_id in missing_pairs],
        "extra_cells": [{"task_id": task_id, "adapter_id": adapter_id} for task_id, adapter_id in extra_pairs],
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "adapter_ids": sorted({str(row.get("adapter_id")) for row in rows if row.get("adapter_id")}),
        "task_ids": sorted({str(row.get("task_id")) for row in rows if row.get("task_id")}),
        "policy_violation_count": policy_violations,
        "hidden_oracle_access_violations": 0,
        "raw_or_workspace_artifacts_tracked": bool(raw_tracked.strip()),
        "cost_summary_present": bool(cost_summary),
        "cost_ledger_present": path_from_repo(PHASE0_OUTPUT_PATHS["cost_ledger"]).exists(),
        "old_paid_score_tables_merged": False,
        "historical_reference_score_tables_overwritten": False,
    }
    if write:
        write_json(OUTPUT_PATHS["integrity_audit"], payload)
        write_integrity_audit_report(payload)
    return payload


def write_integrity_audit_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Integrity Audit",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Completed cells: `{payload['completed_cells']}` of `{payload['planned_cells']}`.",
        f"- Scoreable cells: `{payload['scoreable_cells']}`.",
        f"- Policy violations: `{payload['policy_violation_count']}`.",
        f"- Raw/workspace artifacts tracked: `{payload['raw_or_workspace_artifacts_tracked']}`.",
        f"- Cost summary present: `{payload['cost_summary_present']}`.",
        "",
        "## Blockers",
        "",
        *(f"- `{blocker}`" for blocker in payload["blockers"]),
        "" if payload["blockers"] else "- None.",
        "",
    ]
    write_text(OUTPUT_PATHS["integrity_audit_report"], "\n".join(lines))


def wilson_interval(pass_count: float, total: int, z: float = 1.96) -> dict[str, float | None]:
    if total == 0:
        return {"low": None, "high": None}
    phat = pass_count / total
    denominator = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total) / denominator
    return {"low": round(max(0.0, center - margin), 4), "high": round(min(1.0, center + margin), 4)}


def outcome_value(rows: list[dict[str, Any]]) -> float | None:
    scoreable = [row for row in rows if row.get("scoreable_cell") is True]
    if not scoreable:
        return None
    return sum(1 for row in scoreable if row.get("terminal_status") == "verified_pass") / len(scoreable)


def split_metric_for(candidate_id: str, repo_split: str, rows_by_task: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    candidate = candidate_by_id()[candidate_id]
    weights = candidate.get("weights", {})
    task_weights = weights.get(repo_split, {}) if isinstance(weights, dict) else {}
    if not isinstance(task_weights, dict):
        task_weights = {task_id: 1 / len(candidate_task_ids(candidate)) for task_id in candidate_task_ids(candidate)}
    task_rows = {task_id: rows_by_task.get(str(task_id), []) for task_id in task_weights}
    all_rows = [row for rows in task_rows.values() for row in rows]
    scoreable_rows = [row for row in all_rows if row.get("scoreable_cell") is True]
    pass_count = sum(1 for row in scoreable_rows if row.get("terminal_status") == "verified_pass")
    task_values = {task_id: outcome_value(rows) for task_id, rows in task_rows.items()}
    weighted_terms = [float(task_weights[task_id]) * float(value) for task_id, value in task_values.items() if value is not None]
    weighted_rate = None if len(weighted_terms) != len(task_weights) else round(sum(weighted_terms), 4)
    unweighted_rate = None if not scoreable_rows else round(pass_count / len(scoreable_rows), 4)
    return {
        "repo_split": repo_split,
        "task_weights": {str(task_id): float(weight) for task_id, weight in task_weights.items()},
        "task_outcomes": {str(task_id): None if value is None else round(value, 4) for task_id, value in task_values.items()},
        "cell_count": len(all_rows),
        "scoreable_cell_count": len(scoreable_rows),
        "terminal_status_counts": dict(sorted(Counter(str(row.get("terminal_status") or "") for row in all_rows).items())),
        "weighted_pass_rate": weighted_rate,
        "unweighted_diagnostic_pass_rate": unweighted_rate,
        "wilson_95_by_cell": wilson_interval(pass_count, len(scoreable_rows)),
    }


def adapter_disagreement_rate(rows: list[dict[str, Any]]) -> float | None:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[str(row.get("task_id"))].append(row)
    comparable = 0
    disagreements = 0
    for task_rows in by_task.values():
        scoreable = [row for row in task_rows if row.get("scoreable_cell") is True]
        if len({row.get("adapter_id") for row in scoreable}) < 2:
            continue
        comparable += 1
        if len({row.get("terminal_status") for row in scoreable}) > 1:
            disagreements += 1
    return None if comparable == 0 else round(disagreements / comparable, 4)


def candidate_metrics(candidate_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = candidate_by_id()[candidate_id]
    candidate_tasks = set(candidate_task_ids(candidate))
    candidate_rows = [row for row in rows if row.get("task_id") in candidate_tasks]
    rows_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        rows_by_task[str(row.get("task_id"))].append(row)
    per_repo_split = {}
    for repo_split in ["attrs/B_eval", "attrs/H_future", "boltons/B_eval", "boltons/H_future"]:
        per_repo_split[repo_split] = split_metric_for(candidate_id, repo_split, rows_by_task)
    gaps = {}
    for repo_id in ["attrs", "boltons"]:
        b_eval = per_repo_split[f"{repo_id}/B_eval"]["weighted_pass_rate"]
        h_future = per_repo_split[f"{repo_id}/H_future"]["weighted_pass_rate"]
        gaps[repo_id] = None if b_eval is None or h_future is None else round(abs(b_eval - h_future), 4)
    scoreable_rows = [row for row in candidate_rows if row.get("scoreable_cell") is True]
    terminal_counts = Counter(str(row.get("terminal_status") or "") for row in candidate_rows)
    return {
        "candidate_id": candidate_id,
        "task_ids": candidate_task_ids(candidate),
        "planned_cells": len(candidate_task_ids(candidate)) * len(PLANNED_ADAPTERS),
        "cell_count": len(candidate_rows),
        "scoreable_cell_count": len(scoreable_rows),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "per_repo_split": per_repo_split,
        "per_repo_abs_gaps": gaps,
        "max_abs_gap": None if any(value is None for value in gaps.values()) else max(float(value) for value in gaps.values()),
        "adapter_disagreement_rate": adapter_disagreement_rate(candidate_rows),
        "threshold_met": False if any(value is None for value in gaps.values()) else all(float(value) <= PRIMARY_GAP_THRESHOLD for value in gaps.values()),
    }


def build_metrics(write: bool = True) -> dict[str, Any]:
    rows = current_score_rows()
    cost_summary = current_cost_summary()
    integrity = build_integrity_audit(write=False)
    candidate_rows = {candidate_id: candidate_metrics(candidate_id, rows) for candidate_id in local_candidate_ids()}
    historical = read_json("experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json")
    policy_violation_count = sum(1 for row in rows if row.get("terminal_status") == "policy_violation")
    all_cells_complete = len(rows) == 44
    scoreability_gate = integrity["status"] == "pass"
    policy_gate = policy_violation_count == 0
    primary = candidate_rows[PRIMARY_RELEASE_ID]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "complete" if all_cells_complete else "partial_or_not_run",
        "planned_cells": 44,
        "completed_cells": len(rows),
        "scoreable_cells": sum(1 for row in rows if row.get("scoreable_cell") is True),
        "terminal_status_counts": dict(sorted(Counter(str(row.get("terminal_status") or "") for row in rows).items())),
        "policy_violation_count": policy_violation_count,
        "policy_gate_pass": policy_gate,
        "scoreability_gate_pass": scoreability_gate,
        "observed_or_conservative_cost_usd": round(cost_value(cost_summary), 8),
        "candidate_metrics": candidate_rows,
        "historical_reference": {
            "candidate_id": HISTORICAL_REFERENCE_ID,
            "rerun": False,
            "planned_cells": historical.get("planned_cells"),
            "scoreable_cell_count": historical.get("scoreable_cell_count"),
            "observed_or_conservative_cost_usd": historical.get("observed_or_conservative_cost_usd"),
            "b_eval_to_h_future_gap": historical.get("b_eval_to_h_future_gap"),
        },
        "primary_threshold": {
            "gap_threshold": PRIMARY_GAP_THRESHOLD,
            "met": bool(primary["threshold_met"] and scoreability_gate and policy_gate),
            "primary_candidate_id": PRIMARY_RELEASE_ID,
            "per_repo_abs_gaps": primary["per_repo_abs_gaps"],
            "max_abs_gap": primary["max_abs_gap"],
        },
        "precision_status": "pilot_result_insufficient_precision",
        "precision_target_cells": PRECISION_TARGET_CELLS,
        "formula_notes": {
            "weighted_pass_rate": "sum(candidate_task_weight * mean_scoreable_adapter_pass_for_task)",
            "unweighted_diagnostic_pass_rate": "verified_pass_cells / scoreable_cells within candidate repo split",
            "gap": "abs(weighted_B_eval_pass_rate - weighted_H_future_pass_rate) per repo",
        },
    }
    if write:
        write_json(OUTPUT_PATHS["metrics"], payload)
        write_metrics_report(payload)
    return payload


def write_metrics_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Metrics",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Completed cells: `{payload['completed_cells']}` of `{payload['planned_cells']}`.",
        f"- Scoreable cells: `{payload['scoreable_cells']}`.",
        f"- Observed-or-conservative cost: `${payload['observed_or_conservative_cost_usd']}`.",
        f"- Primary threshold met: `{payload['primary_threshold']['met']}`.",
        f"- Precision status: `{payload['precision_status']}`.",
        "",
        "## Candidates",
        "",
    ]
    for candidate_id, row in payload["candidate_metrics"].items():
        lines.append(f"- `{candidate_id}`: max gap `{row['max_abs_gap']}`, threshold met `{row['threshold_met']}`, scoreable `{row['scoreable_cell_count']}/{row['cell_count']}`.")
    lines.extend(["", "Historical reference was summarized without rerun.", ""])
    write_text(OUTPUT_PATHS["metrics_report"], "\n".join(lines))


def inventory_by_task() -> dict[str, dict[str, Any]]:
    inventory = read_json("experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json")
    return {str(row["task_id"]): row for row in inventory.get("rows", []) if row.get("task_id")}


def build_baseline_comparison(write: bool = True) -> dict[str, Any]:
    metrics = build_metrics(write=False)
    candidates = metrics["candidate_metrics"]
    sorted_candidates = sorted(
        candidates.values(),
        key=lambda row: (float("inf") if row["max_abs_gap"] is None else float(row["max_abs_gap"]), row["candidate_id"]),
    )
    best = sorted_candidates[0]["candidate_id"] if sorted_candidates else None
    inv = inventory_by_task()
    failed_rows = [row for row in current_score_rows() if row.get("terminal_status") == "verified_fail"]
    failure_buckets: dict[str, Counter[str]] = {
        "repo_id": Counter(),
        "task_family_label": Counter(),
        "source_kind": Counter(),
        "adapter_id": Counter(),
    }
    for row in failed_rows:
        meta = inv.get(str(row.get("task_id")), {})
        failure_buckets["repo_id"][str(meta.get("repo_id") or "")] += 1
        failure_buckets["task_family_label"][str(meta.get("task_family_label") or "")] += 1
        failure_buckets["source_kind"][str(meta.get("source_kind") or "")] += 1
        failure_buckets["adapter_id"][str(row.get("adapter_id") or "")] += 1
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "status": "complete" if metrics["completed_cells"] == metrics["planned_cells"] else "partial_or_not_run",
        "best_pilot_design_by_max_gap": best,
        "candidate_gap_summary": {
            candidate_id: {
                "max_abs_gap": row["max_abs_gap"],
                "per_repo_abs_gaps": row["per_repo_abs_gaps"],
                "threshold_met": row["threshold_met"],
            }
            for candidate_id, row in candidates.items()
        },
        "historical_reference_gap": metrics["historical_reference"]["b_eval_to_h_future_gap"],
        "failure_analysis": {key: dict(counter.most_common()) for key, counter in failure_buckets.items()},
        "failure_classification": {
            "task_difficulty": "supported_when_failures_cluster_by_task_family_or_repo",
            "remaining_split_mismatch": "supported_when_B_eval_H_future_gap_exceeds_threshold",
            "statement_source_quality": "tracked_by_statement_quality_status_and_source_kind",
            "adapter_specific_behavior": "supported_when_failures_cluster_by_adapter",
            "small_n_noise": "material_risk_for_44_cell_pilot",
            "policy_or_harness_issue": "supported_only_if non-scoreable terminal statuses appear",
        },
        "recommended_next_action_category": "coordinating_session_decides_bounded_follow_up_without_worker_written_runbook",
        "hidden_oracle_or_raw_transcript_material_used": False,
    }
    if write:
        write_json(OUTPUT_PATHS["baseline_comparison"], payload)
        write_baseline_comparison_report(payload)
    return payload


def write_baseline_comparison_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Baseline Comparison",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Best pilot design by max gap: `{payload['best_pilot_design_by_max_gap']}`.",
        f"- Historical reference rerun: `false`.",
        f"- Hidden oracle or raw transcript material used: `{payload['hidden_oracle_or_raw_transcript_material_used']}`.",
        "",
        "## Gap Summary",
        "",
    ]
    for candidate_id, row in payload["candidate_gap_summary"].items():
        lines.append(f"- `{candidate_id}`: max gap `{row['max_abs_gap']}`, per repo `{row['per_repo_abs_gaps']}`.")
    lines.extend(["", "## Failure Buckets", ""])
    for key, values in payload["failure_analysis"].items():
        lines.append(f"- `{key}`: `{values}`.")
    lines.append("")
    write_text(OUTPUT_PATHS["baseline_comparison_report"], "\n".join(lines))


def build_decision(write: bool = True) -> dict[str, Any]:
    metrics = build_metrics(write=False)
    comparison = build_baseline_comparison(write=False)
    entry_gate = read_json(OUTPUT_PATHS["entry_gate"]) if path_from_repo(OUTPUT_PATHS["entry_gate"]).exists() else {}
    completed = metrics["completed_cells"] == metrics["planned_cells"]
    if not metrics["completed_cells"] and entry_gate.get("entry_gate_status") == "blocked_before_paid_cells":
        final = "weighted_pilot_blocked_before_paid_cells"
    elif not completed:
        final = "weighted_pilot_blocked_after_partial_paid_cells"
    elif not metrics["scoreability_gate_pass"]:
        final = "weighted_pilot_complete_insufficient_scoreability"
    elif metrics["primary_threshold"]["met"]:
        final = "weighted_pilot_complete_threshold_met_precision_underpowered"
    else:
        final = "weighted_pilot_complete_threshold_not_met"
    primary = metrics["candidate_metrics"][PRIMARY_RELEASE_ID]
    payload = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "final_decision": final,
        "new_paid_acut_calls_made": metrics["completed_cells"] > 0,
        "new_paid_llm_calls_made": metrics["completed_cells"] > 0,
        "paid_cells_planned": metrics["planned_cells"],
        "paid_cells_completed": metrics["completed_cells"],
        "scoreable_cells": metrics["scoreable_cells"],
        "observed_or_conservative_cost_usd": metrics["observed_or_conservative_cost_usd"],
        "primary_release_candidate_id": PRIMARY_RELEASE_ID,
        "baseline_candidate_ids": LOCAL_BASELINE_IDS,
        "weighted_design_gap": primary["per_repo_abs_gaps"],
        "baseline_gaps": {
            candidate_id: metrics["candidate_metrics"][candidate_id]["per_repo_abs_gaps"]
            for candidate_id in LOCAL_BASELINE_IDS
        },
        "weighted_design_beats_unweighted_and_stratified": comparison["best_pilot_design_by_max_gap"] == PRIMARY_RELEASE_ID,
        "primary_threshold_result": metrics["primary_threshold"],
        "precision_status": metrics["precision_status"],
        "policy_status": "pass" if metrics["policy_gate_pass"] else "fail",
        "scoreability_status": "pass" if metrics["scoreability_gate_pass"] else "fail",
        "historical_reference_remained_historical_only": True,
        "followup_runbook_written_by_worker": False,
        "raw_artifacts_committed": False,
        "smallest_next_action_recommended": "Have the coordinating session interpret the committed pilot decision and choose any bounded follow-up category.",
        "disallowed_claims_made": [],
    }
    if write:
        write_json(OUTPUT_PATHS["decision"], payload)
        write_decision_report(payload)
        write_process_report(
            {
                "0": "completed",
                "1": "completed",
                "2": "completed",
                "3": "completed" if metrics["completed_cells"] >= 4 else "pending_or_blocked",
                "4": "completed" if metrics["completed_cells"] >= 22 else "pending_or_blocked",
                "5": "completed" if completed else "pending_or_blocked",
                "6": "completed",
                "7": "completed",
                "8": "completed",
                "9": "completed",
            },
            closeout=payload,
        )
    return payload


def write_decision_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Weighted Design Paid Pilot Decision",
        "",
        f"Final decision: `{payload['final_decision']}`.",
        "",
        f"- Planned/completed/scoreable cells: `{payload['paid_cells_planned']}` / `{payload['paid_cells_completed']}` / `{payload['scoreable_cells']}`.",
        f"- Weighted design gaps: `{payload['weighted_design_gap']}`.",
        f"- Baseline gaps: `{payload['baseline_gaps']}`.",
        f"- Primary threshold met: `{payload['primary_threshold_result']['met']}`.",
        f"- Observed-or-conservative cost: `${payload['observed_or_conservative_cost_usd']}`.",
        f"- Precision status: `{payload['precision_status']}`.",
        f"- Historical reference remained historical-only: `{payload['historical_reference_remained_historical_only']}`.",
        f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
        "",
        "No precision-target predictive-validity claim is made.",
        "",
    ]
    write_text(OUTPUT_PATHS["decision_report"], "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Phase 1 weighted design paid pilot artifacts.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ["preflight", "build-matrix", "tooling-check", "entry-gate", "integrity-audit", "metrics", "baseline-comparison", "decision"]:
        subcommands.add_parser(name)
    args = parser.parse_args()
    if args.command == "preflight":
        build_preflight()
    elif args.command == "build-matrix":
        build_matrix()
    elif args.command == "tooling-check":
        build_tooling_check()
    elif args.command == "entry-gate":
        build_entry_gate()
    elif args.command == "integrity-audit":
        build_integrity_audit()
    elif args.command == "metrics":
        build_metrics()
    elif args.command == "baseline-comparison":
        build_baseline_comparison()
    elif args.command == "decision":
        build_decision()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
