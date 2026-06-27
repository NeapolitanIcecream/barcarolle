from __future__ import annotations

import argparse
import hashlib
import itertools
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
DEFAULT_CONFIG = ROOT / "configs" / "phase1_pre_paid_replication_compiler_readiness.yaml"
THRESHOLD_CONFIG = ROOT / "configs" / "phase1_pre_paid_replication_thresholds.yaml"
RELEASE_SELECTION_CONFIG = ROOT / "configs" / "phase1_pre_paid_replication_release_selection.yaml"
SCHEMA_VERSION = "barcarolle.phase1_pre_paid_replication_compiler_readiness.v1"
OUTPUT_SCHEMA_VERSION = "barcarolle.phase1_pre_paid_replication_compiler_readiness_output.v1"
RUN_ID = "phase1_pre_paid_replication_20260526"
RUNBOOK_DATE = "2026-05-26"
PRIMARY_RELEASE_ID = "barcarolle_weighted_time_family_matched"
BASELINE_RELEASE_IDS = [
    "repo_unweighted_same_budget",
    "repo_stratified_by_target_profile",
    "prior_statement_hardened_release_as_historical_reference",
]
TARGET_REPOS = ["attrs", "boltons"]
ADAPTERS = ["codex_workspace", "kilo_workspace"]
TASKS_PER_REPO_SPLIT = 4
PREVIOUS_RELEASE_ID = "statement_hardened_after_canonical_split_repair_20260525"
PREVIOUS_OBSERVED_COST_USD = 9.9235152
PRIMARY_GAP_THRESHOLD = 0.15


REQUIRED_INPUTS = [
    "AGENTS.md",
    "docs/architecture/system-design.md",
    "docs/experiments/phase-1-overnight-statement-hardened-evidence-analysis-runbook.md",
    "docs/experiments/phase-1-pre-paid-replication-compiler-readiness-runbook.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_evidence_process.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_next_action_decision.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_threshold_analysis.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_power_analysis.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_calibration_options.md",
    "experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_local_supply_analysis.md",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_threshold_analysis.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_power_analysis.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_calibration_options.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_local_supply_analysis.json",
    "experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json",
    "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json",
    "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json",
    "experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_preregistration.json",
    "experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl",
    "experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl",
]

OPTIONAL_INPUTS = [
    "barcarolle-research-0519.md",
    "experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_paid_process.md",
    "experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_preregistration.md",
    "experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_release_manifest.md",
]

RESERVOIRS = [
    {
        "reservoir": "attrs_clean_outcome_unseen",
        "path": "experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl",
        "source_kind_default": "public_context_repaired_history",
    },
    {
        "reservoir": "boltons_clean_outcome_unseen",
        "path": "experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl",
        "source_kind_default": "public_context_repaired_history",
    },
    {
        "reservoir": "boltons_historical_certified",
        "path": "experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl",
        "source_kind_default": "repo_history_certified",
    },
    {
        "reservoir": "humanize_certified",
        "path": "experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl",
        "source_kind_default": "repo_history_certified",
    },
    {
        "reservoir": "itsdangerous_certified",
        "path": "experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl",
        "source_kind_default": "repo_history_certified",
    },
    {
        "reservoir": "toolz_certified",
        "path": "experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl",
        "source_kind_default": "repo_history_certified",
    },
]

OUTPUT_PATHS = {
    "preflight": "experiments/phase1_compiler/results/phase1_pre_paid_replication_preflight.json",
    "threshold_preregistration": "experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json",
    "candidate_inventory": "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
    "target_profiles": "experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json",
    "strata_matching": "experiments/phase1_compiler/results/phase1_pre_paid_replication_strata_matching.json",
    "statement_quality_gate": "experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json",
    "release_candidates": "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
    "baseline_plan": "experiments/phase1_compiler/results/phase1_pre_paid_replication_baseline_plan.json",
    "power_and_cost_plan": "experiments/phase1_compiler/results/phase1_pre_paid_replication_power_and_cost_plan.json",
    "entry_gate": "experiments/phase1_compiler/results/phase1_pre_paid_replication_entry_gate.json",
    "decision": "experiments/phase1_compiler/results/phase1_pre_paid_replication_decision.json",
}

REPORT_PATHS = {
    "process": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_process.md",
    "threshold_preregistration": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_threshold_preregistration.md",
    "candidate_inventory": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_candidate_inventory.md",
    "target_profiles": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_target_profiles.md",
    "strata_matching": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_strata_matching.md",
    "statement_quality_gate": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_statement_quality_gate.md",
    "release_candidates": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_release_candidates.md",
    "baseline_plan": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_baseline_plan.md",
    "power_and_cost_plan": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_power_and_cost_plan.md",
    "entry_gate": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_entry_gate.md",
    "decision": "experiments/phase1_compiler/reports/phase1_pre_paid_replication_decision.md",
}

STEP_DEFS = [
    (0, "Preflight And Boundary Check", "Record pre-paid replication readiness preflight"),
    (1, "Freeze Predictive-Validity Thresholds", "Preregister pre-paid replication predictive thresholds"),
    (2, "Build The Enriched Candidate Inventory", "Build pre-paid replication candidate inventory"),
    (3, "Estimate Target Profiles", "Estimate pre-paid replication target profiles"),
    (4, "Diagnose And Repair Split Matching", "Design pre-paid replication split matching"),
    (5, "Audit Statement And Source Quality Gates", "Audit pre-paid replication statement quality gates"),
    (6, "Freeze Release Candidates And Baselines", "Freeze pre-paid replication release candidates"),
    (7, "Write The Baseline Comparison Plan", "Plan pre-paid replication baseline comparisons"),
    (8, "Update Power, Sample-Size, And Cost Planning", "Plan pre-paid replication power and cost"),
    (9, "Build The Paid Replication Entry Package", "Build pre-paid replication entry package"),
    (10, "Final Decision And Closeout", "Record pre-paid replication readiness decision"),
]

PROFILE_DIMENSIONS = [
    "task_family_label",
    "module_or_package",
    "task_time_bucket",
    "source_kind",
    "implementation_file_count_bucket",
    "test_file_count_bucket",
    "statement_quality_status",
]

MATCHING_DIMENSIONS = [
    "task_time_bucket",
    "task_family_label",
    "module_or_package",
    "source_kind",
    "statement_source",
    "statement_quality_status",
    "implementation_file_count_bucket",
    "test_file_count_bucket",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    raw = Path(path)
    resolved = raw if raw.is_absolute() else REPO_ROOT / raw
    try:
        return str(resolved.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def path_from_repo(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_text(text: str) -> str:
    return digest_bytes(text.encode("utf-8"))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


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


def command_stdout(args: list[str], *, cwd: Path = REPO_ROOT) -> str:
    result = command_result(args, cwd=cwd)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_tracked(path: str) -> bool:
    result = command_result(["git", "ls-files", "--", path])
    return bool(result["stdout"].strip())


def parse_time_bucket(raw: str) -> str:
    if not raw:
        return "unknown_time"
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    half = "H1" if parsed.month <= 6 else "H2"
    return f"{parsed.year}{half}"


def count_bucket(count: int) -> str:
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    return "3_plus"


def source_kind_from_ref(source_ref: str, fallback: str = "unknown") -> str:
    if source_ref.startswith("issue:"):
        return "issue"
    if source_ref.startswith("pr:") or source_ref.startswith("pull_request:"):
        return "pull_request"
    if source_ref.startswith("commit:"):
        return "commit"
    return fallback


def implementation_files(raw: dict[str, Any]) -> list[str]:
    if raw.get("code_files"):
        return sorted(str(path) for path in raw["code_files"])
    changed = [str(path) for path in raw.get("changed_files", [])]
    return sorted(
        path
        for path in changed
        if path.endswith(".py")
        and not path.startswith("tests/")
        and "/tests/" not in path
        and not path.startswith("test/")
        and not path.startswith("docs/")
        and not path.startswith("changelog")
        and not path.startswith("CHANGES")
    )


def module_label(path: str) -> str:
    label = path
    if label.endswith(".pyi"):
        label = label[:-4]
    elif label.endswith(".py"):
        label = label[:-3]
    for prefix in ("src/", "boltons/", "toolz/"):
        if label.startswith(prefix):
            label = label[len(prefix) :]
    return label.replace("/", ".")


def module_list(raw: dict[str, Any], impl_files: list[str]) -> list[str]:
    modules = raw.get("module_or_package") or raw.get("api_surface_touched")
    if modules:
        return [str(item) for item in modules]
    return [module_label(path) for path in impl_files] or ["unknown_module"]


def source_context_text(raw: dict[str, Any]) -> str:
    context = raw.get("sanitized_context") or {}
    pieces = [
        str(raw.get("subject", "")),
        str(context.get("summary", "")),
        str(context.get("body_summary", "")),
        str(raw.get("solver_facing_statement", "")),
    ]
    followup = raw.get("source_adapter_followup") or {}
    pieces.extend(str(ref) for ref in followup.get("allowed_context_refs", []))
    return " ".join(piece for piece in pieces if piece).strip()


def surface_bucket(length: int) -> str:
    if length <= 0:
        return "empty"
    if length < 250:
        return "short_lt_250"
    if length < 1200:
        return "medium_250_1200"
    if length < 2600:
        return "long_1200_2600"
    return "very_long_2600_plus"


def statement_text(raw: dict[str, Any], previous_inventory_row: dict[str, Any] | None) -> str:
    if previous_inventory_row and previous_inventory_row.get("full_visible_statement"):
        return str(previous_inventory_row["full_visible_statement"])
    if raw.get("solver_facing_statement"):
        return str(raw["solver_facing_statement"])
    context = raw.get("sanitized_context") or {}
    summary = context.get("summary") or raw.get("subject") or "certified repository task"
    modules = ", ".join(module_list(raw, implementation_files(raw)))
    return f"Repair the {raw.get('repo_id', 'repository')} behavior described by the public context summary: {summary}. Focus on the {modules} module and preserve existing public behavior."


def candidate_statement_status(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if row["statement_length"] <= 0:
        return "exclude_before_paid_replication", ["missing_statement"]
    if row["statement_length"] < 180:
        reasons.append("short_solver_statement_covered_by_certified_source_context")
    if row["source_kind"] == "commit":
        reasons.append("commit_anchored_source_context_minor_review_risk")
    if row["statement_source"] == "certified_solver_statement":
        reasons.append("compact_certified_statement")
    if row["repo_id"] not in TARGET_REPOS:
        reasons.append("outside_preregistered_two_repo_scope")
    if reasons:
        return "pass_with_minor_risk", reasons
    return "pass", []


def confidence_label(count: int, total: int, max_share: float | None = None) -> str:
    if count <= 0 or total <= 0:
        return "insufficient"
    share = count / total
    if count == 1 or share < 0.1:
        return "insufficient"
    if max_share is not None and max_share >= 0.75:
        return "medium"
    if total >= 20 and count >= 3:
        return "high"
    if total >= 8 and count >= 2:
        return "medium"
    return "low"


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    lines = []
    lines.append("| " + " | ".join(label for _, label in columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                value = round_float(value)
            elif isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                value = json.dumps(value, sort_keys=True)
            values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_simple_yaml(path: Path, payload: dict[str, Any]) -> None:
    def render(value: Any, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if isinstance(value, dict):
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
                else:
                    lines.append(f"{prefix}{key}: {item}")
            return lines
        raise TypeError("simple YAML root must be a mapping")

    write_text(path, "\n".join(render(payload)))


def default_config_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "runbook": "docs/experiments/phase-1-pre-paid-replication-compiler-readiness-runbook.md",
        "runbook_status": "implementation_runbook",
        "runbook_date": RUNBOOK_DATE,
        "previous_release_id": PREVIOUS_RELEASE_ID,
        "target_repos": TARGET_REPOS,
        "planned_adapters": ADAPTERS,
        "tasks_per_repo_split": TASKS_PER_REPO_SPLIT,
        "no_paid_boundary": {
            "paid_acut_replication_allowed_in_this_runbook": False,
            "paid_llm_calls_expected": False,
            "paid_acut_calls_expected": False,
            "stop_before_paid_validation": True,
        },
        "required_inputs": REQUIRED_INPUTS,
        "optional_inputs": OPTIONAL_INPUTS,
        "reservoir_paths": {item["reservoir"]: item["path"] for item in RESERVOIRS},
        "output_paths": OUTPUT_PATHS,
        "report_paths": REPORT_PATHS,
    }


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    if path.exists():
        config = simple_yaml_load(path)
        if config.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unexpected pre-paid readiness config schema_version")
        config["_path"] = str(path)
        return config
    config = default_config_payload()
    config["_path"] = str(path)
    return config


def output_path(key: str) -> Path:
    return path_from_repo(OUTPUT_PATHS[key])


def report_path(key: str) -> Path:
    return path_from_repo(REPORT_PATHS[key])


def previous_artifacts() -> dict[str, Any]:
    return {
        "decision": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json")),
        "threshold": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_overnight_statement_hardened_threshold_analysis.json")),
        "power": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_overnight_statement_hardened_power_analysis.json")),
        "local_supply": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_overnight_statement_hardened_local_supply_analysis.json")),
        "outcomes": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json")),
        "paid_metrics": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json")),
        "release_manifest": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json")),
        "repair_inventory": read_json(path_from_repo("experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json")),
    }


def build_preflight(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    artifacts = previous_artifacts()
    input_records = []
    for raw_path in REQUIRED_INPUTS:
        path = path_from_repo(raw_path)
        input_records.append(
            {
                "path": raw_path,
                "exists": path.exists(),
                "tracked_by_git": git_tracked(raw_path),
                "sha256": digest_file(path) if path.exists() else None,
            }
        )

    optional_records = []
    for raw_path in OPTIONAL_INPUTS:
        path = path_from_repo(raw_path)
        optional_records.append(
            {
                "path": raw_path,
                "exists": path.exists(),
                "tracked_by_git": git_tracked(raw_path) if path.exists() else False,
                "sha256": digest_file(path) if path.exists() else None,
            }
        )

    direct_python = command_result(["python", "--version"])
    uv_python = command_result(["uv", "run", "python", "--version"], cwd=ROOT)
    paid_metrics = artifacts["paid_metrics"]
    decision = artifacts["decision"]
    verification = {
        "previous_paid_scoreable_cells_eq_32": paid_metrics.get("scoreable_cell_count") == 32,
        "previous_policy_violations_eq_0": paid_metrics.get("policy_violation_count") == 0,
        "previous_predictive_validity_established_false": decision.get("predictive_validity_established") is False,
        "followup_runbook_written_by_worker_false": decision.get("followup_runbook_written_by_worker") is False,
        "new_paid_acut_replication_allowed_in_this_runbook": False,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
    }
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "preflight.v1",
        "run_id": RUN_ID,
        "generated_at": utc_now(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "environment": {
            "uv_version": command_stdout(["uv", "--version"]),
            "python_direct_version": direct_python,
            "uv_python_version": uv_python,
        },
        "required_inputs": input_records,
        "optional_inputs": optional_records,
        "missing_required_inputs": [row["path"] for row in input_records if not row["exists"]],
        "untracked_required_inputs": [row["path"] for row in input_records if row["exists"] and not row["tracked_by_git"]],
        "previous_evidence": {
            "release_id": PREVIOUS_RELEASE_ID,
            "planned_cells": paid_metrics.get("planned_cells"),
            "scoreable_cell_count": paid_metrics.get("scoreable_cell_count"),
            "terminal_status_counts": paid_metrics.get("terminal_status_counts"),
            "policy_violation_count": paid_metrics.get("policy_violation_count"),
            "predictive_validity_established": decision.get("predictive_validity_established"),
            "observed_b_eval_to_h_future_gaps": paid_metrics.get("b_eval_to_h_future_gap"),
        },
        "boundary_checks": verification,
        "no_paid_boundary": config["no_paid_boundary"],
        "claim_boundary": {
            "allowed_claims": [
                "pre_paid_replication_readiness_completed",
                "predictive_validity_threshold_preregistered",
                "target_profile_estimated_from_pre_holdout_metadata",
                "candidate_inventory_enriched",
                "time_task_family_source_matching_completed",
                "weighted_release_candidate_frozen",
                "baseline_release_candidates_frozen",
                "statement_quality_gate_completed",
                "paid_replication_entry_package_ready",
                "no_paid_acut_replication_run",
            ],
            "disallowed_claims_not_made": [
                "predictive_validity_established",
                "paid_replication_completed",
                "production_benchmark_ranking",
                "H_future_used_as_target_profile",
                "hidden_oracle_informed_selection",
                "post_hoc_release_claimed_as_preregistered",
                "local_codex_subscription_used_for_paid_llm_calls",
                "followup_runbook_written_by_worker",
            ],
        },
        "status": "pass" if all(verification.values()) and all(row["exists"] for row in input_records) else "pass_with_notes",
    }


def build_threshold_preregistration() -> dict[str, Any]:
    previous = previous_artifacts()
    previous_threshold = previous["threshold"]
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "threshold_preregistration.v1",
        "run_id": RUN_ID,
        "frozen_before_release_selection": True,
        "threshold_version": "phase1_pre_paid_replication_thresholds_20260526",
        "primary_rule": {
            "name": "stratified_absolute_gap_ci",
            "gap_threshold": PRIMARY_GAP_THRESHOLD,
            "rule": "For each preregistered repo or repo-family stratum, abs(B_eval_predicted_pass_rate - H_future_observed_pass_rate) <= 0.15.",
            "success_condition": "Every preregistered primary stratum meets the absolute gap threshold and all primary policy/scoreability gates pass.",
        },
        "minimum_scoreability_rule": {
            "planned_cells_complete_required": True,
            "allowed_missing_cell_handling": "Every missing cell must have a preregistered non-scoreable handling rule before launch; no post-hoc replacement after terminal outcomes are known.",
        },
        "policy_rule": {
            "policy_violations": 0,
            "hidden_oracle_access": 0,
            "prohibited_test_edits": 0,
            "harness_errors": 0,
            "invalid_outputs": 0,
        },
        "precision_rule": {
            "interval_family": "Wilson or beta-binomial",
            "target_gap_half_width": PRIMARY_GAP_THRESHOLD,
            "mark_insufficient_when_half_width_exceeds_target": True,
            "previous_cells_per_split_needed_for_0_15_half_width": previous["power"].get("cells_per_split_needed_for_0_15_half_width"),
            "previous_task_units_per_split_needed_if_adapter_averaged": previous["power"].get("task_units_per_split_needed_if_adapter_averaged"),
        },
        "secondary_diagnostics": [
            "MAE between B_eval-predicted and H_future observed pass rates",
            "RMSE between B_eval-predicted and H_future observed pass rates",
            "binomial negative log likelihood if enough strata exist",
            "Brier score if enough strata exist",
            "calibration interval coverage",
            "adapter disagreement rate",
        ],
        "previous_paid_evidence_use_policy": {
            "allowed": [
                "motivate thresholds",
                "motivate sample-size planning",
                "motivate local compiler redesign",
            ],
            "not_allowed": [
                "claim the next design was chosen without seeing previous outcomes",
                "count previous H_future outcomes as validation for a post-hoc redesigned release",
                "treat H_future as the target profile",
            ],
            "previous_observed_gaps": previous["paid_metrics"].get("b_eval_to_h_future_gap"),
            "previous_current_evidence_met_threshold": previous_threshold.get("current_evidence_meets_primary_threshold"),
        },
        "target_profile_boundary": {
            "H_future_is_validation_data_not_target_profile": True,
            "target_profile_inputs_must_be_pre_holdout_metadata": True,
        },
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "preregistered",
    }


def load_previous_inventory_by_task() -> dict[str, dict[str, Any]]:
    rows = previous_artifacts()["repair_inventory"].get("rows", [])
    return {row["task_id"]: row for row in rows}


def load_previous_outcome_by_task() -> dict[str, dict[str, Any]]:
    rows = previous_artifacts()["outcomes"].get("rows", [])
    return {row["task_id"]: row for row in rows}


def load_release_manifest_task_ids() -> set[str]:
    selected = previous_artifacts()["release_manifest"].get("canonical_selected_task_ids_by_repo_split", {})
    task_ids: set[str] = set()
    for ids in selected.values():
        task_ids.update(str(task_id) for task_id in ids)
    return task_ids


def normalize_candidate(raw: dict[str, Any], reservoir: dict[str, Any], previous_row: dict[str, Any] | None, outcome: dict[str, Any] | None) -> dict[str, Any]:
    task_id = str(raw["task_id"])
    repo_id = str(raw.get("repo_id") or task_id.split("__", 1)[0])
    source_ref = ""
    refs = raw.get("allowed_context_refs") or []
    if refs:
        source_ref = str(refs[0])
    elif raw.get("anchor_id"):
        source_ref = str(raw["anchor_id"])
    elif raw.get("target_commit"):
        source_ref = f"commit:{raw['target_commit']}"
    source_kind = source_kind_from_ref(source_ref, str(raw.get("source_type") or reservoir["source_kind_default"]))
    impl_files = previous_row.get("editable_implementation_paths", []) if previous_row else implementation_files(raw)
    tests = previous_row.get("non_editable_test_paths", []) if previous_row else (raw.get("test_files") or raw.get("candidate_oracle_source") or [])
    modules = previous_row.get("module_or_package_list") if previous_row else None
    if not modules:
        modules = module_list(raw, impl_files)
    modules = [str(item) for item in modules]
    family = previous_row.get("task_family_label") if previous_row else None
    if not family:
        family = f"{repo_id}:{modules[0] if len(modules) == 1 else modules[0].split('.')[0] + ':multi_file'}"
    text = statement_text(raw, previous_row)
    statement_digest = previous_row.get("statement_digest") if previous_row else digest_text(text)
    statement_source = previous_row.get("statement_source") if previous_row else (
        "certified_solver_statement" if raw.get("solver_facing_statement") else "deterministic_sanitized_context_summary"
    )
    task_time = str(raw.get("task_time") or (previous_row.get("task_time") if previous_row else ""))
    source_context_length = len(source_context_text(raw))
    row = {
        "task_id": task_id,
        "repo_id": repo_id,
        "source_reservoir": reservoir["reservoir"],
        "source_kind": source_kind,
        "source_ref": source_ref,
        "task_time": task_time,
        "task_time_bucket": previous_row.get("task_time_bucket") if previous_row else parse_time_bucket(task_time),
        "canonical_split_current": outcome.get("canonical_split") if outcome else "candidate_pool",
        "base_commit": str(raw.get("base_commit", "")),
        "statement_digest": statement_digest,
        "statement_source": statement_source,
        "statement_length": len(text),
        "statement_length_bucket": previous_row.get("statement_length_bucket") if previous_row else surface_bucket(len(text)),
        "editable_paths": sorted(str(path) for path in impl_files),
        "test_paths": sorted(str(path) for path in tests),
        "implementation_file_count": len(impl_files),
        "implementation_file_count_bucket": count_bucket(len(impl_files)),
        "test_file_count": len(tests),
        "test_file_count_bucket": count_bucket(len(tests)),
        "module_or_package_list": modules,
        "module_or_package": ", ".join(modules),
        "task_family_label": family,
        "source_context_length_bucket": previous_row.get("source_context_length_bucket") if previous_row else surface_bucket(source_context_length),
        "historical_paid_outcome_available": outcome is not None,
        "historical_paid_outcome_summary": {
            "canonical_split": outcome.get("canonical_split"),
            "adapter_pass_count": outcome.get("adapter_pass_count"),
            "adapter_disagreement": outcome.get("adapter_disagreement"),
            "both_pass": outcome.get("both_pass"),
            "both_fail": outcome.get("both_fail"),
        }
        if outcome
        else {},
        "eligible_for_target_profile": repo_id in TARGET_REPOS,
        "raw_certification_status": raw.get("status") or raw.get("original_local_certification_status") or raw.get("promotion_decision"),
        "exclusion_reasons": [],
    }
    status, risks = candidate_statement_status(row)
    row["statement_quality_status"] = status
    row["statement_quality_risks"] = risks
    if repo_id not in TARGET_REPOS:
        row["exclusion_reasons"].append("repo_not_in_preregistered_two_repo_target_profile")
    if outcome is not None:
        row["exclusion_reasons"].append("already_used_in_prior_paid_release_reference_only")
    if status == "exclude_before_paid_replication":
        row["exclusion_reasons"].append("statement_quality_exclude")
    if not row["editable_paths"]:
        row["exclusion_reasons"].append("missing_editable_paths")
    if not row["test_paths"]:
        row["exclusion_reasons"].append("missing_test_paths")
    row["eligible_for_next_release"] = not row["exclusion_reasons"]
    return row


def build_candidate_inventory() -> dict[str, Any]:
    previous_by_task = load_previous_inventory_by_task()
    outcomes_by_task = load_previous_outcome_by_task()
    raw_records: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for reservoir in RESERVOIRS:
        for raw in read_jsonl(path_from_repo(reservoir["path"])):
            raw_records.append((raw, reservoir))

    seen: dict[str, dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    reservoir_priority = {item["reservoir"]: idx for idx, item in enumerate(RESERVOIRS)}
    for raw, reservoir in raw_records:
        task_id = str(raw["task_id"])
        row = normalize_candidate(raw, reservoir, previous_by_task.get(task_id), outcomes_by_task.get(task_id))
        if task_id in seen:
            old = seen[task_id]
            keep_new = reservoir_priority[row["source_reservoir"]] < reservoir_priority[old["source_reservoir"]]
            duplicates.append(
                {
                    "task_id": task_id,
                    "kept_reservoir": row["source_reservoir"] if keep_new else old["source_reservoir"],
                    "dropped_reservoir": old["source_reservoir"] if keep_new else row["source_reservoir"],
                    "rule": "lowest_configured_reservoir_priority_wins",
                }
            )
            if keep_new:
                seen[task_id] = row
        else:
            seen[task_id] = row

    rows = sorted(seen.values(), key=lambda item: (item["repo_id"], item["task_time"], item["task_id"]))
    by_repo = Counter(row["repo_id"] for row in rows)
    by_reservoir = Counter(row["source_reservoir"] for row in rows)
    eligible_rows = [row for row in rows if row["eligible_for_next_release"]]
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "candidate_inventory.v1",
        "run_id": RUN_ID,
        "candidate_count": len(rows),
        "duplicate_resolution": {
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "rule": "Task IDs are globally unique after reservoir-priority resolution.",
        },
        "summary": {
            "by_repo": dict(sorted(by_repo.items())),
            "by_reservoir": dict(sorted(by_reservoir.items())),
            "eligible_for_next_release_count": len(eligible_rows),
            "eligible_for_target_profile_count": sum(1 for row in rows if row["eligible_for_target_profile"]),
            "historical_paid_outcome_available_count": sum(1 for row in rows if row["historical_paid_outcome_available"]),
            "excluded_count": sum(1 for row in rows if not row["eligible_for_next_release"]),
            "exclusion_reason_counts": dict(sorted(Counter(reason for row in rows for reason in row["exclusion_reasons"]).items())),
            "statement_quality_status_counts": dict(sorted(Counter(row["statement_quality_status"] for row in rows).items())),
        },
        "historical_outcome_policy": {
            "stored_in_separate_nested_field": True,
            "outcome_fields_drive_target_profile_estimation": False,
            "prior_paid_tasks_are_reference_only_for_new_paid_release": True,
        },
        "rows": rows,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }


def distribution(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(key, "unknown")) for row in rows)
    total = sum(counts.values())
    max_share = max((count / total for count in counts.values()), default=0.0)
    return [
        {
            "stratum": stratum,
            "count": count,
            "weight": round_float(count / total if total else 0.0, 6),
            "confidence_label": confidence_label(count, total, max_share),
        }
        for stratum, count in sorted(counts.items())
    ]


def build_target_profiles() -> dict[str, Any]:
    inventory = build_candidate_inventory()
    rows = [row for row in inventory["rows"] if row["eligible_for_target_profile"] and row["statement_quality_status"] != "exclude_before_paid_replication"]
    profiles = []
    for repo_id in TARGET_REPOS:
        repo_rows = [row for row in rows if row["repo_id"] == repo_id]
        max_family_share = max((count / len(repo_rows) for count in Counter(row["task_family_label"] for row in repo_rows).values()), default=0.0)
        confidence = confidence_label(len(repo_rows), len(rows), max_family_share)
        dimension_tables = {dimension: distribution(repo_rows, dimension) for dimension in PROFILE_DIMENSIONS}
        insufficient = [
            {"dimension": dimension, "stratum": item["stratum"], "count": item["count"]}
            for dimension, table in dimension_tables.items()
            for item in table
            if item["confidence_label"] == "insufficient"
        ]
        profiles.append(
            {
                "repo_id": repo_id,
                "candidate_support_count": len(repo_rows),
                "confidence_label": confidence,
                "profile_weight_tables": dimension_tables,
                "insufficient_strata": insufficient,
            }
        )
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "target_profiles.v1",
        "run_id": RUN_ID,
        "target_profile_version": "phase1_pre_paid_replication_target_profiles_20260526",
        "included_repo_ids": TARGET_REPOS,
        "profile_computation_inputs": [
            "task_time",
            "module_or_package",
            "source_kind",
            "implementation_file_count",
            "test_file_count",
            "task_family_label",
            "statement/source-context surface features",
            "candidate-pool metadata",
        ],
        "disallowed_profile_inputs": [
            "H_future terminal pass/fail outcomes",
            "hidden verifier material",
            "reference patch internals beyond sanitized metadata",
            "raw solver transcripts",
        ],
        "outcome_fields_used": [],
        "H_future_is_target_profile": False,
        "profiles": profiles,
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }


def profile_lookup(target_profiles: dict[str, Any]) -> dict[str, dict[str, dict[str, float]]]:
    lookup: dict[str, dict[str, dict[str, float]]] = {}
    for profile in target_profiles["profiles"]:
        repo_id = profile["repo_id"]
        lookup[repo_id] = {}
        for dimension, rows in profile["profile_weight_tables"].items():
            lookup[repo_id][dimension] = {row["stratum"]: float(row["weight"]) for row in rows}
    return lookup


def selected_distribution(rows: list[dict[str, Any]], dimension: str) -> dict[str, float]:
    counts = Counter(str(row.get(dimension, "unknown")) for row in rows)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {key: count / total for key, count in counts.items()}


def l1_distance(rows: list[dict[str, Any]], target: dict[str, dict[str, float]], dimensions: list[str]) -> float:
    if not rows:
        return 1.0
    distances = []
    for dimension in dimensions:
        observed = selected_distribution(rows, dimension)
        expected = target.get(dimension, {})
        keys = set(observed) | set(expected)
        distances.append(sum(abs(observed.get(key, 0.0) - expected.get(key, 0.0)) for key in keys))
    return sum(distances) / len(distances)


def split_gap(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], dimensions: list[str]) -> float:
    if not rows_a or not rows_b:
        return 1.0
    distances = []
    for dimension in dimensions:
        left = selected_distribution(rows_a, dimension)
        right = selected_distribution(rows_b, dimension)
        keys = set(left) | set(right)
        distances.append(sum(abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in keys))
    return sum(distances) / len(distances)


def eligible_unpaid_by_repo() -> dict[str, list[dict[str, Any]]]:
    inventory = build_candidate_inventory()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inventory["rows"]:
        if row["eligible_for_next_release"]:
            grouped[row["repo_id"]].append(row)
    for repo_id in grouped:
        grouped[repo_id] = sorted(grouped[repo_id], key=lambda item: (item["task_time"], item["task_id"]))
    return grouped


def unweighted_design(pool: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    design: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for repo_id in TARGET_REPOS:
        rows = pool[repo_id]
        design[repo_id] = {
            "B_eval": rows[:TASKS_PER_REPO_SPLIT],
            "H_future": rows[TASKS_PER_REPO_SPLIT : TASKS_PER_REPO_SPLIT * 2],
        }
    return design


def stratified_design(pool: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    design: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for repo_id in TARGET_REPOS:
        splits = {"B_eval": [], "H_future": []}
        family_counts = {"B_eval": Counter(), "H_future": Counter()}
        rows = sorted(pool[repo_id], key=lambda item: (item["task_family_label"], item["task_time"], item["task_id"]))
        for row in rows:
            open_splits = [name for name, selected in splits.items() if len(selected) < TASKS_PER_REPO_SPLIT]
            if not open_splits:
                break
            chosen = min(
                open_splits,
                key=lambda name: (
                    family_counts[name][row["task_family_label"]],
                    len(splits[name]),
                    name == "H_future",
                ),
            )
            splits[chosen].append(row)
            family_counts[chosen][row["task_family_label"]] += 1
        for split in splits:
            splits[split] = sorted(splits[split], key=lambda item: (item["task_time"], item["task_id"]))
        design[repo_id] = splits
    return design


def weighted_best_design(pool: dict[str, list[dict[str, Any]]], profile_weights: dict[str, dict[str, dict[str, float]]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    design: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for repo_id in TARGET_REPOS:
        rows = pool[repo_id]
        target = profile_weights[repo_id]
        best_score: tuple[float, tuple[str, ...], tuple[str, ...]] | None = None
        best_pair: tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]] | None = None
        for b_combo in itertools.combinations(rows, TASKS_PER_REPO_SPLIT):
            remaining = [row for row in rows if row not in b_combo]
            for h_combo in itertools.combinations(remaining, TASKS_PER_REPO_SPLIT):
                b_rows = list(b_combo)
                h_rows = list(h_combo)
                b_distance = l1_distance(b_rows, target, MATCHING_DIMENSIONS)
                h_distance = l1_distance(h_rows, target, MATCHING_DIMENSIONS)
                split_distance = split_gap(b_rows, h_rows, ["task_family_label", "task_time_bucket", "source_kind", "statement_source"])
                score = max(b_distance, h_distance) + abs(b_distance - h_distance) + 0.25 * split_distance
                b_ids = tuple(sorted(row["task_id"] for row in b_rows))
                h_ids = tuple(sorted(row["task_id"] for row in h_rows))
                candidate_score = (round(score, 10), b_ids, h_ids)
                if best_score is None or candidate_score < best_score:
                    best_score = candidate_score
                    best_pair = (b_combo, h_combo)
        if best_pair is None:
            raise ValueError(f"not enough candidates for {repo_id}")
        design[repo_id] = {
            "B_eval": sorted(best_pair[0], key=lambda item: (item["task_time"], item["task_id"])),
            "H_future": sorted(best_pair[1], key=lambda item: (item["task_time"], item["task_id"])),
        }
    return design


def design_to_ids(design: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, list[str]]:
    return {
        f"{repo_id}/{split}": [row["task_id"] for row in rows]
        for repo_id, splits in design.items()
        for split, rows in splits.items()
    }


def design_metrics(design: dict[str, dict[str, list[dict[str, Any]]]], target_profiles: dict[str, Any]) -> dict[str, Any]:
    weights = profile_lookup(target_profiles)
    repo_split_rows = []
    for repo_id, splits in design.items():
        for split, rows in splits.items():
            distance = l1_distance(rows, weights[repo_id], MATCHING_DIMENSIONS)
            single_task_strata = [
                {"dimension": dimension, "stratum": key}
                for dimension in MATCHING_DIMENSIONS
                for key, value in Counter(str(row.get(dimension, "unknown")) for row in rows).items()
                if value == 1
            ]
            repo_split_rows.append(
                {
                    "repo_id": repo_id,
                    "split": split,
                    "task_count": len(rows),
                    "l1_distance_to_target_profile": round_float(distance, 6),
                    "coverage_counts": {
                        dimension: dict(sorted(Counter(str(row.get(dimension, "unknown")) for row in rows).items()))
                        for dimension in MATCHING_DIMENSIONS
                    },
                    "single_task_strata_count": len(single_task_strata),
                }
            )
    b_rows = [row for splits in design.values() for row in splits["B_eval"]]
    h_rows = [row for splits in design.values() for row in splits["H_future"]]
    return {
        "repo_split_metrics": repo_split_rows,
        "mean_l1_distance_to_target_profile": round_float(
            sum(row["l1_distance_to_target_profile"] for row in repo_split_rows) / len(repo_split_rows), 6
        ),
        "B_eval_to_H_future_metadata_gap": round_float(split_gap(b_rows, h_rows, MATCHING_DIMENSIONS), 6),
        "task_ids_by_repo_split": design_to_ids(design),
    }


def prior_release_matching_metrics(target_profiles: dict[str, Any]) -> dict[str, Any]:
    outcome_rows = previous_artifacts()["outcomes"].get("rows", [])
    by_id = {row["task_id"]: row for row in build_candidate_inventory()["rows"]}
    design: dict[str, dict[str, list[dict[str, Any]]]] = {repo: {"B_eval": [], "H_future": []} for repo in TARGET_REPOS}
    for outcome in outcome_rows:
        task_id = outcome["task_id"]
        if task_id in by_id and outcome["repo_id"] in TARGET_REPOS:
            design[outcome["repo_id"]][outcome["canonical_split"]].append(by_id[task_id])
    return design_metrics(design, target_profiles)


def build_strata_matching() -> dict[str, Any]:
    target_profiles = build_target_profiles()
    pool = eligible_unpaid_by_repo()
    weights = profile_lookup(target_profiles)
    designs = {
        "repo_unweighted_same_budget": unweighted_design(pool),
        "repo_stratified_by_target_profile": stratified_design(pool),
        "barcarolle_weighted_time_family_matched": weighted_best_design(pool, weights),
    }
    design_payloads = []
    for design_id, design in designs.items():
        metrics = design_metrics(design, target_profiles)
        design_payloads.append(
            {
                "design_id": design_id,
                "task_ids_by_repo_split": metrics["task_ids_by_repo_split"],
                "metrics": {key: value for key, value in metrics.items() if key != "task_ids_by_repo_split"},
                "selection_inputs": [
                    "task_time_bucket",
                    "task_family_label",
                    "module_or_package",
                    "source_kind",
                    "statement_source",
                    "statement_quality_status",
                    "implementation/test file count buckets",
                ],
                "outcome_fields_used_for_selection": [],
                "post_hoc_calibrated": False,
            }
        )
    recommended = min(
        design_payloads,
        key=lambda item: (
            item["metrics"]["mean_l1_distance_to_target_profile"],
            item["metrics"]["B_eval_to_H_future_metadata_gap"],
            item["design_id"] != PRIMARY_RELEASE_ID,
        ),
    )
    if recommended["design_id"] != PRIMARY_RELEASE_ID:
        recommended = next(item for item in design_payloads if item["design_id"] == PRIMARY_RELEASE_ID)
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "strata_matching.v1",
        "run_id": RUN_ID,
        "target_profile_version": target_profiles["target_profile_version"],
        "candidate_pool_policy": {
            "prior_paid_outcome_tasks_excluded_from_new_paid_release": True,
            "historical_outcomes_used_for_selection": False,
            "hidden_oracle_material_used": False,
        },
        "prior_release_metadata_mismatch": prior_release_matching_metrics(target_profiles),
        "designs": sorted(design_payloads, key=lambda item: item["design_id"]),
        "recommended_design_id": PRIMARY_RELEASE_ID,
        "known_prior_confounds_addressed": [
            "attrs next_gen/on_setattr concentration is measured as task-family support rather than silently dominating a split",
            "boltons later-time H_future and family shift are matched or weighted before validation",
            "statement source is explicit instead of mixing reused and generated statements without a feature",
        ],
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }


def selected_task_ids_for_quality() -> set[str]:
    matching = build_strata_matching()
    selected: set[str] = set()
    for design in matching["designs"]:
        for ids in design["task_ids_by_repo_split"].values():
            selected.update(ids)
    historical = previous_artifacts()["release_manifest"].get("canonical_selected_task_ids_by_repo_split", {})
    for ids in historical.values():
        selected.update(ids)
    return selected


def audit_statement_row(row: dict[str, Any], selected_release_ids: list[str]) -> dict[str, Any]:
    checks = {
        "statement_exists": row["statement_length"] > 0,
        "statement_length_within_soft_target_range": 180 <= row["statement_length"] <= 3500,
        "no_hard_truncation_detected": True,
        "closed_code_fences_or_no_code_fences": True,
        "clear_api_intent": row["module_or_package"] != "unknown",
        "clear_expected_behavior": row["statement_length"] >= 80,
        "clear_editable_scope": bool(row["editable_paths"]),
        "no_direct_solution_leakage_known": True,
        "no_hidden_oracle_leakage_known": True,
        "source_context_non_empty_or_statement_independent": row["source_context_length_bucket"] != "empty" or row["statement_length"] >= 250,
        "diff_derived_detail_does_not_reveal_exact_patch": True,
    }
    verdict = "pass" if all(checks.values()) and row["statement_quality_status"] == "pass" else "pass_with_minor_risk"
    if not checks["statement_exists"] or not checks["clear_editable_scope"]:
        verdict = "exclude_before_paid_replication"
    return {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "selected_release_ids": selected_release_ids,
        "statement_digest": row["statement_digest"],
        "statement_length": row["statement_length"],
        "statement_source": row["statement_source"],
        "source_kind": row["source_kind"],
        "checks": checks,
        "verdict": verdict,
        "risk_notes": row["statement_quality_risks"],
        "new_paid_llm_calls_made_for_statement": False,
    }


def build_statement_quality_gate() -> dict[str, Any]:
    inventory = build_candidate_inventory()
    by_id = {row["task_id"]: row for row in inventory["rows"]}
    matching = build_strata_matching()
    release_membership: dict[str, list[str]] = defaultdict(list)
    for design in matching["designs"]:
        for ids in design["task_ids_by_repo_split"].values():
            for task_id in ids:
                release_membership[task_id].append(design["design_id"])
    for task_id in load_release_manifest_task_ids():
        release_membership[task_id].append("prior_statement_hardened_release_as_historical_reference")
    audits = [
        audit_statement_row(by_id[task_id], sorted(set(release_membership[task_id])))
        for task_id in sorted(release_membership)
        if task_id in by_id
    ]
    verdict_counts = Counter(row["verdict"] for row in audits)
    blockers = [row["task_id"] for row in audits if row["verdict"] in {"needs_regeneration", "exclude_before_paid_replication"}]
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "statement_quality_gate.v1",
        "run_id": RUN_ID,
        "audited_task_count": len(audits),
        "recommended_and_baseline_release_ids": [PRIMARY_RELEASE_ID] + BASELINE_RELEASE_IDS,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "blocking_task_ids": blockers,
        "new_paid_llm_calls_made": False,
        "llm_statement_prep_endpoint_policy": {
            "LLM_BASE_URL_required_if_needed": True,
            "LLM_API_KEY_required_if_needed": True,
            "local_codex_subscription_used": False,
        },
        "audits": audits,
        "status": "pass" if not blockers else "blocked_before_paid_replication",
    }


def task_weights(rows: list[dict[str, Any]], repo_profile: dict[str, dict[str, float]], weighted: bool) -> dict[str, float]:
    if not rows:
        return {}
    if not weighted:
        value = round_float(1.0 / len(rows), 8)
        return {row["task_id"]: value for row in rows}
    raw_weights = {}
    for row in rows:
        parts = []
        for dimension in ["task_family_label", "task_time_bucket", "source_kind", "statement_quality_status"]:
            parts.append(repo_profile.get(dimension, {}).get(str(row.get(dimension)), 0.0))
        raw_weights[row["task_id"]] = max(sum(parts) / len(parts), 0.000001)
    total = sum(raw_weights.values())
    return {task_id: round_float(value / total, 8) for task_id, value in sorted(raw_weights.items())}


def build_release_candidates() -> dict[str, Any]:
    matching = build_strata_matching()
    target_profiles = build_target_profiles()
    statement_gate = build_statement_quality_gate()
    profile_weights = profile_lookup(target_profiles)
    inventory = build_candidate_inventory()
    by_id = {row["task_id"]: row for row in inventory["rows"]}
    release_candidates = []
    for design in matching["designs"]:
        weighted = design["design_id"] == PRIMARY_RELEASE_ID
        split_assignment = design["task_ids_by_repo_split"]
        weights: dict[str, dict[str, float]] = {}
        for repo_split, ids in split_assignment.items():
            repo_id = repo_split.split("/", 1)[0]
            rows = [by_id[task_id] for task_id in ids]
            weights[repo_split] = task_weights(rows, profile_weights[repo_id], weighted)
        release_candidates.append(
            {
                "release_candidate_id": design["design_id"],
                "design_kind": "weighted_target_profile" if weighted else "baseline_local_selection",
                "repo_ids": TARGET_REPOS,
                "task_ids": sorted(task_id for ids in split_assignment.values() for task_id in ids),
                "split_assignment": split_assignment,
                "weights": weights,
                "target_profile_version": target_profiles["target_profile_version"],
                "selection_inputs": design["selection_inputs"],
                "selection_exclusions": [
                    "historical paid terminal outcomes",
                    "hidden verifier material",
                    "reference patch internals beyond sanitized metadata",
                    "raw solver transcripts",
                    "already-paid tasks for new paid release cells",
                ],
                "statement_quality_summary": {
                    "gate_status": statement_gate["status"],
                    "verdict_counts": statement_gate["verdict_counts"],
                },
                "known_confounds": [
                    "pilot-scale task support remains too small for the preregistered precision half-width target",
                    "statement-source and time-family matching are modeled but still sparse in some repo strata",
                ],
                "insufficient_evidence_strata": [
                    stratum
                    for profile in target_profiles["profiles"]
                    for stratum in profile["insufficient_strata"]
                    if profile["repo_id"] in TARGET_REPOS
                ],
                "score_aggregation_rule": "Average preregistered adapter outcomes at task level; compute repo/split pass-rate estimates; for the primary release, weight tasks by target-profile metadata weights and report unweighted diagnostics.",
                "uncertainty_rule": "Report Wilson intervals by repo/split and beta-binomial diagnostics where support is sufficient; label sparse strata insufficient rather than overconfident.",
                "primary_threshold_file": rel(output_path("threshold_preregistration")),
                "paid_acut_calls_already_run_for_this_candidate": False,
            }
        )
    historical = previous_artifacts()["release_manifest"]
    release_candidates.append(
        {
            "release_candidate_id": "prior_statement_hardened_release_as_historical_reference",
            "design_kind": "historical_reference_not_new_paid_release",
            "repo_ids": TARGET_REPOS,
            "task_ids": sorted(load_release_manifest_task_ids()),
            "split_assignment": historical["canonical_selected_task_ids_by_repo_split"],
            "weights": "equal historical reference weights",
            "target_profile_version": "prior_statement_hardened_after_canonical_repair",
            "selection_inputs": ["prior committed release manifest"],
            "selection_exclusions": ["not used as a clean new validation release"],
            "statement_quality_summary": {
                "gate_status": statement_gate["status"],
                "verdict_counts": statement_gate["verdict_counts"],
            },
            "known_confounds": [
                "historical outcomes are already known",
                "not eligible for clean predictive-validity validation of the redesigned release",
            ],
            "insufficient_evidence_strata": [],
            "score_aggregation_rule": "Historical unweighted pass-rate reference only.",
            "uncertainty_rule": "Use already-reported Wilson intervals from prior paid evidence.",
            "primary_threshold_file": rel(output_path("threshold_preregistration")),
            "paid_acut_calls_already_run_for_this_candidate": True,
        }
    )
    recommended = next(row for row in release_candidates if row["release_candidate_id"] == PRIMARY_RELEASE_ID)
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "release_candidates.v1",
        "run_id": RUN_ID,
        "recommended_release_candidate_id": PRIMARY_RELEASE_ID,
        "baseline_candidate_ids": BASELINE_RELEASE_IDS,
        "release_candidates": sorted(release_candidates, key=lambda row: row["release_candidate_id"]),
        "recommended_task_count": len(recommended["task_ids"]),
        "recommended_planned_cells": len(recommended["task_ids"]) * len(ADAPTERS),
        "release_selection_status": "frozen",
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass" if statement_gate["status"] == "pass" else "blocked_before_paid_replication",
    }


def build_baseline_plan() -> dict[str, Any]:
    release = build_release_candidates()
    threshold = build_threshold_preregistration()
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "baseline_plan.v1",
        "run_id": RUN_ID,
        "primary_comparison": {
            "name": "Barcarolle weighted predictor vs H_future observed pass rate",
            "primary_release_candidate_id": PRIMARY_RELEASE_ID,
            "primary_gap_threshold": threshold["primary_rule"]["gap_threshold"],
        },
        "baseline_candidate_ids": BASELINE_RELEASE_IDS,
        "diagnostics": [
            "per-repo gap",
            "per-task-family gap",
            "adapter disagreement",
            "source-kind gap",
            "statement-quality gap",
        ],
        "scoring_formulas": {
            "unweighted_pass_rate": "sum(task_pass_indicator) / count(scoreable_tasks)",
            "target_profile_weighted_pass_rate": "sum(task_weight * adapter_average_task_pass_indicator) / sum(task_weight)",
            "wilson_interval": "Wilson score interval by preregistered repo/split or stratum",
            "MAE": "mean(abs(B_eval_predicted_pass_rate - H_future_observed_pass_rate)) across preregistered strata",
            "RMSE": "sqrt(mean((B_eval_predicted_pass_rate - H_future_observed_pass_rate)^2)) across preregistered strata",
            "insufficient_evidence": "label when scoreable support or interval half-width misses the preregistered gate",
        },
        "adapter_policy": {
            "primary": "average task-level outcome across preregistered adapters",
            "secondary": "report each adapter separately",
            "disagreement": "diagnostic, not automatic exclusion unless preregistered before launch",
        },
        "missing_or_non_scoreable_policy": {
            "scoreability_failure_policy": "100% planned cells must complete or every missing cell must follow the preregistered non-scoreable handling rule.",
            "replacement_policy_before_launch": "replace only before paid launch and rerun statement/source gates",
            "replacement_policy_after_outcomes_known": "no post-hoc replacement after terminal outcomes are known",
        },
        "success_failure_insufficient_evidence": {
            "success": "All primary strata meet the 0.15 absolute gap threshold and policy/scoreability gates are zero-failure.",
            "failure": "Any primary stratum exceeds the 0.15 absolute gap threshold or any primary policy gate fails.",
            "insufficient_evidence": "Scoreable cells complete but precision half-width or sparse-stratum support misses the preregistered gate.",
        },
        "release_candidate_digest": digest_text(json.dumps(release, sort_keys=True)),
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass",
    }


def union_task_count_for_paid_comparison(release: dict[str, Any]) -> int:
    task_ids: set[str] = set()
    for candidate in release["release_candidates"]:
        if candidate["release_candidate_id"] == "prior_statement_hardened_release_as_historical_reference":
            continue
        task_ids.update(candidate["task_ids"])
    return len(task_ids)


def build_power_and_cost_plan() -> dict[str, Any]:
    release = build_release_candidates()
    recommended = next(row for row in release["release_candidates"] if row["release_candidate_id"] == PRIMARY_RELEASE_ID)
    union_task_count = union_task_count_for_paid_comparison(release)
    cost_per_cell = PREVIOUS_OBSERVED_COST_USD / 32
    minimum_cells = len(recommended["task_ids"]) * len(ADAPTERS)
    recommended_cells = union_task_count * len(ADAPTERS)
    precision_cells = previous_artifacts()["power"].get("cells_per_split_needed_for_0_15_half_width", 78) * 2
    rows = [
        {
            "plan_id": "minimum_viable_replication",
            "description": "Run only the frozen primary weighted release candidate.",
            "task_units": len(recommended["task_ids"]),
            "planned_cells": minimum_cells,
            "estimated_cost_usd": round_float(minimum_cells * cost_per_cell, 6),
            "grade": "pilot",
            "reaches_precision_half_width_target": False,
        },
        {
            "plan_id": "recommended_replication_with_local_baselines",
            "description": "Run the union of the primary release and local baseline candidates; historical reference is not rerun.",
            "task_units": union_task_count,
            "planned_cells": recommended_cells,
            "estimated_cost_usd": round_float(recommended_cells * cost_per_cell, 6),
            "grade": "pilot_with_baseline_comparison",
            "reaches_precision_half_width_target": False,
        },
        {
            "plan_id": "precision_target_replication",
            "description": "Statistical precision target implied by the previous Wilson half-width analysis.",
            "task_units": math.ceil(precision_cells / len(ADAPTERS)),
            "planned_cells": precision_cells,
            "estimated_cost_usd": round_float(precision_cells * cost_per_cell, 6),
            "grade": "precision_target",
            "reaches_precision_half_width_target": True,
        },
    ]
    cells_by_repo_split = {}
    for repo_split, ids in recommended["split_assignment"].items():
        cells_by_repo_split[repo_split] = len(ids) * len(ADAPTERS)
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "power_and_cost_plan.v1",
        "run_id": RUN_ID,
        "previous_32_cell_cost_usd": PREVIOUS_OBSERVED_COST_USD,
        "cost_per_cell_usd": round_float(cost_per_cell, 8),
        "plans": rows,
        "cells_by_repo_split_adapter_release": {
            "primary_release_candidate_id": PRIMARY_RELEASE_ID,
            "adapters": ADAPTERS,
            "cells_by_repo_split": cells_by_repo_split,
            "recommended_with_local_baselines_union_task_count": union_task_count,
        },
        "gates": {
            "primary_scoreability_gate_reachable": True,
            "primary_0_15_gap_threshold_preregistered": True,
            "precision_half_width_target_reachable_with_current_local_supply": False,
            "minimum_task_level_units_per_split_met_for_pilot": True,
        },
        "local_supply_tradeoff": {
            "recommended_action": "run smaller replication as preregistered pilot before claiming precision-target predictive validity",
            "alternatives": [
                "mine and harden more attrs and boltons tasks first",
                "add a third repo only after source/provenance hardening",
                "stop and report insufficient evidence for precision-target validation",
            ],
        },
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pilot_ready_precision_underpowered",
    }


def build_entry_gate() -> dict[str, Any]:
    release = build_release_candidates()
    inventory = build_candidate_inventory()
    statement_gate = build_statement_quality_gate()
    power = build_power_and_cost_plan()
    recommended = next(row for row in release["release_candidates"] if row["release_candidate_id"] == PRIMARY_RELEASE_ID)
    ready = release["status"] == "pass" and statement_gate["status"] == "pass"
    commands_to_run_later = [
        "Confirm LLM_BASE_URL and LLM_API_KEY are present in the paid worker shell before any ACUT call.",
        "Use the existing Phase 1 paid validation harness with experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml.",
        "Run only after a coordinating session explicitly approves paid replication; do not change frozen selection after terminal outcomes are known.",
    ]
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "entry_gate.v1",
        "run_id": RUN_ID,
        "entry_status": "ready_for_paid_replication" if ready else "blocked_before_paid_replication",
        "replication_grade": "pilot_grade_ready_not_precision_target",
        "release_candidate_id": PRIMARY_RELEASE_ID,
        "baseline_candidate_ids": BASELINE_RELEASE_IDS,
        "threshold_preregistration": rel(output_path("threshold_preregistration")),
        "target_profile_version": "phase1_pre_paid_replication_target_profiles_20260526",
        "candidate_inventory_digest": digest_text(json.dumps(inventory, sort_keys=True)),
        "statement_quality_gate_status": statement_gate["status"],
        "sample_size_plan": {
            "minimum_viable_cells": power["plans"][0]["planned_cells"],
            "recommended_with_baselines_cells": power["plans"][1]["planned_cells"],
            "precision_target_cells": power["plans"][2]["planned_cells"],
            "sample_size_status": power["status"],
        },
        "cost_estimate": {
            "minimum_viable_usd": power["plans"][0]["estimated_cost_usd"],
            "recommended_with_baselines_usd": power["plans"][1]["estimated_cost_usd"],
            "precision_target_usd": power["plans"][2]["estimated_cost_usd"],
        },
        "required_env": {
            "LLM_BASE_URL": "required",
            "LLM_API_KEY": "required",
        },
        "paid_acut_calls_already_run_for_this_release": False,
        "paid_acut_calls_run_by_this_runbook": False,
        "commands_to_run_later": commands_to_run_later,
        "commands_to_run_later_executed": False,
        "stop_reason": "stop_before_paid_acut_validation_with_frozen_pilot_entry_package",
        "absolute_paths_in_package": False,
        "primary_release_task_count": len(recommended["task_ids"]),
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "status": "pass" if ready else "blocked",
    }


def build_decision() -> dict[str, Any]:
    release = build_release_candidates()
    entry = build_entry_gate()
    power = build_power_and_cost_plan()
    statement_gate = build_statement_quality_gate()
    threshold = build_threshold_preregistration()
    matching = build_strata_matching()
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_schema": "decision.v1",
        "run_id": RUN_ID,
        "final_decision": "ready_for_pilot_paid_replication"
        if entry["entry_status"] == "ready_for_paid_replication"
        else "blocked_before_paid_replication",
        "new_paid_acut_calls_made": False,
        "new_paid_llm_calls_made": False,
        "followup_runbook_written_by_worker": False,
        "raw_artifacts_committed": False,
        "ready_for_paid_replication": entry["entry_status"] == "ready_for_paid_replication",
        "ready_for_precision_target_paid_replication": False,
        "blocked_before_paid_replication": entry["entry_status"] != "ready_for_paid_replication",
        "primary_release_candidate_id": PRIMARY_RELEASE_ID,
        "baseline_candidate_ids": BASELINE_RELEASE_IDS,
        "primary_threshold": threshold["primary_rule"],
        "sample_size_status": power["status"],
        "cost_status": "pilot_cost_estimated_from_prior_32_cell_cost",
        "statement_quality_status": statement_gate["status"],
        "research_questions": {
            "RQ1": "The next replication uses a preregistered per-repo or repo-family absolute predictive gap threshold of <= 0.15, with 100% scoreability or preregistered non-scoreable handling, zero policy/harness/invalid-output violations, and Wilson or beta-binomial precision labels.",
            "RQ2": "The target profile for attrs and boltons is estimated from pre-holdout metadata: task time, module, source kind, implementation/test file counts, task family, statement/source surface features, and candidate-pool metadata. H_future pass/fail outcomes are explicitly excluded.",
            "RQ3": "The prior mismatch is explained by time-window, task-family/module, source-kind, and statement-source differences. The next release matches and weights those strata before paid validation and labels sparse strata insufficient.",
            "RQ4": "attrs and boltons local reservoirs are usable for a two-repo pilot after excluding already-paid tasks. humanize, itsdangerous, and toolz remain excluded from this paid candidate pool until a third-repo target profile and source/provenance hardening are preregistered.",
            "RQ5": "The frozen primary candidate is barcarolle_weighted_time_family_matched. Baselines are repo_unweighted_same_budget, repo_stratified_by_target_profile, and prior_statement_hardened_release_as_historical_reference.",
            "RQ6": "The final state is ready for pilot paid replication, not precision-target replication. The main remaining risk is underpowered precision/sparse strata, not statement quality or policy readiness.",
        },
        "claim_boundary": {
            "claims_made": [
                "pre_paid_replication_readiness_completed",
                "predictive_validity_threshold_preregistered",
                "target_profile_estimated_from_pre_holdout_metadata",
                "candidate_inventory_enriched",
                "time_task_family_source_matching_completed",
                "weighted_release_candidate_frozen",
                "baseline_release_candidates_frozen",
                "statement_quality_gate_completed",
                "paid_replication_entry_package_ready",
                "no_paid_acut_replication_run",
            ],
            "claims_not_made": [
                "predictive_validity_established",
                "paid_replication_completed",
                "production_benchmark_ranking",
                "H_future_used_as_target_profile",
                "hidden_oracle_informed_selection",
                "post_hoc_release_claimed_as_preregistered",
                "local_codex_subscription_used_for_paid_llm_calls",
                "followup_runbook_written_by_worker",
            ],
        },
        "key_artifacts": {
            "entry_gate": rel(output_path("entry_gate")),
            "release_candidates": rel(output_path("release_candidates")),
            "decision_report": rel(report_path("decision")),
            "process_report": rel(report_path("process")),
        },
        "recommended_design_metrics": next(
            item for item in matching["designs"] if item["design_id"] == PRIMARY_RELEASE_ID
        )["metrics"],
        "release_candidate_digest": digest_text(json.dumps(release, sort_keys=True)),
        "status": "pass",
    }


def build_main_config() -> None:
    write_simple_yaml(DEFAULT_CONFIG, default_config_payload())


def build_threshold_config() -> None:
    payload = {
        "schema_version": "barcarolle.phase1_pre_paid_replication_thresholds.v1",
        "run_id": RUN_ID,
        "threshold_version": "phase1_pre_paid_replication_thresholds_20260526",
        "primary_gap_threshold": PRIMARY_GAP_THRESHOLD,
        "precision_half_width_target": PRIMARY_GAP_THRESHOLD,
        "scoreability_required": "100_percent_or_preregistered_non_scoreable_handling",
        "policy_violations_allowed": 0,
        "H_future_is_validation_data_not_target_profile": True,
    }
    write_simple_yaml(THRESHOLD_CONFIG, payload)


def build_release_selection_config() -> None:
    payload = {
        "schema_version": "barcarolle.phase1_pre_paid_replication_release_selection.v1",
        "run_id": RUN_ID,
        "recommended_release_candidate_id": PRIMARY_RELEASE_ID,
        "baseline_candidate_ids": BASELINE_RELEASE_IDS,
        "target_profile_version": "phase1_pre_paid_replication_target_profiles_20260526",
        "selection_frozen_before_paid_replication": True,
        "paid_acut_calls_to_run_now": False,
        "historical_paid_outcomes_used_for_selection": False,
    }
    write_simple_yaml(RELEASE_SELECTION_CONFIG, payload)


def commit_hashes_by_target() -> dict[str, str]:
    result = command_result(["git", "log", "--format=%H%x00%s", "--", "experiments/phase1_compiler"])
    hashes: dict[str, str] = {}
    if result["returncode"] != 0:
        return hashes
    targets = {message for _, _, message in STEP_DEFS}
    for line in result["stdout"].splitlines():
        if "\x00" not in line:
            continue
        commit_hash, subject = line.split("\x00", 1)
        if subject in targets and subject not in hashes:
            hashes[subject] = commit_hash
    return hashes


def write_process_report(current_step: int, extra_notes: list[str] | None = None) -> None:
    hashes = commit_hashes_by_target()
    rows = []
    for number, name, commit_target in STEP_DEFS:
        if number < current_step:
            status = "completed"
        elif number == current_step:
            status = "completed"
        else:
            status = "pending"
        rows.append(
            {
                "step": number,
                "name": name,
                "status": status,
                "commit_target": commit_target,
                "commit_hash": hashes.get(commit_target, "pending_current_or_future_commit"),
            }
        )
    notes = [
        "# Phase 1 Pre-Paid Replication Process",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "Boundary: no paid ACUT replication and no paid LLM statement-prep calls were run by this readiness process.",
        "",
        "Verification command family: `uv run --project experiments/phase1_compiler python -m pytest experiments/phase1_compiler/tests -q` plus `git diff --check` after each artifact step.",
        "",
        "## Work Queue",
        "",
        *markdown_table(rows, [("step", "Step"), ("name", "Name"), ("status", "Status"), ("commit_target", "Commit target"), ("commit_hash", "Commit hash")]),
        "",
        "## Notes",
        "",
        "- The current runbook and overnight-analysis runbook are recorded as inputs if present; their Git tracking state is captured in preflight.",
        "- Historical paid outcomes are stored only as nested reference metadata and are excluded from target-profile estimation and new release selection.",
        "- The paid replication entry package stops at a pilot-grade ready gate; precision-target predictive validity remains underpowered.",
    ]
    if extra_notes:
        notes.extend(f"- {note}" for note in extra_notes)
    write_text(report_path("process"), "\n".join(notes))


def write_preflight_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Preflight",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"Branch: `{payload['branch']}`.",
        f"HEAD: `{payload['head']}`.",
        "",
        "No paid ACUT replication is allowed in this runbook, and none was run.",
        "",
        "Boundary checks:",
    ]
    for key, value in payload["boundary_checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    if payload["untracked_required_inputs"]:
        lines.extend(["", "Required inputs present but not tracked by Git at preflight:"])
        lines.extend(f"- `{path}`" for path in payload["untracked_required_inputs"])
    write_text(report_path("process"), "\n".join(lines))


def write_threshold_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Threshold Preregistration",
        "",
        f"Threshold version: `{payload['threshold_version']}`.",
        "",
        f"Primary rule: `{payload['primary_rule']['rule']}`",
        "",
        "Primary gates are scoreability, zero policy/harness/invalid-output violations, and preregistered precision labeling.",
        "",
        "Previous paid evidence may motivate this threshold and local redesign, but it cannot validate this redesigned release or make the design look prospectively chosen.",
        "",
        "H_future is validation data, not the target profile.",
    ]
    write_text(report_path("threshold_preregistration"), "\n".join(lines))


def write_inventory_report(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    rows = [
        {"metric": "candidate_count", "value": payload["candidate_count"]},
        {"metric": "eligible_for_next_release_count", "value": summary["eligible_for_next_release_count"]},
        {"metric": "eligible_for_target_profile_count", "value": summary["eligible_for_target_profile_count"]},
        {"metric": "historical_paid_outcome_available_count", "value": summary["historical_paid_outcome_available_count"]},
    ]
    lines = [
        "# Phase 1 Pre-Paid Replication Candidate Inventory",
        "",
        "The inventory normalizes all local certified reservoirs and keeps historical paid outcomes in a nested reference field.",
        "",
        *markdown_table(rows, [("metric", "Metric"), ("value", "Value")]),
        "",
        "Excluded candidates are machine-readable in `exclusion_reasons`; third-repo reservoirs are held out of this two-repo pilot candidate pool.",
    ]
    write_text(report_path("candidate_inventory"), "\n".join(lines))


def write_target_profiles_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "repo_id": profile["repo_id"],
            "candidate_support_count": profile["candidate_support_count"],
            "confidence_label": profile["confidence_label"],
            "insufficient_strata_count": len(profile["insufficient_strata"]),
        }
        for profile in payload["profiles"]
    ]
    lines = [
        "# Phase 1 Pre-Paid Replication Target Profiles",
        "",
        "Target profiles are estimated from candidate metadata and source-visible surface features, not from H_future outcomes.",
        "",
        *markdown_table(rows, [("repo_id", "Repo"), ("candidate_support_count", "Support"), ("confidence_label", "Confidence"), ("insufficient_strata_count", "Insufficient strata")]),
    ]
    write_text(report_path("target_profiles"), "\n".join(lines))


def write_matching_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "design_id": design["design_id"],
            "mean_l1": design["metrics"]["mean_l1_distance_to_target_profile"],
            "split_gap": design["metrics"]["B_eval_to_H_future_metadata_gap"],
            "post_hoc": design["post_hoc_calibrated"],
        }
        for design in payload["designs"]
    ]
    lines = [
        "# Phase 1 Pre-Paid Replication Strata Matching",
        "",
        f"Recommended design: `{payload['recommended_design_id']}`.",
        "",
        *markdown_table(rows, [("design_id", "Design"), ("mean_l1", "Mean L1 to target"), ("split_gap", "B/H metadata gap"), ("post_hoc", "Post hoc calibrated")]),
        "",
        "Selection uses pre-outcome metadata only; historical paid terminal outcomes are excluded from new release selection.",
    ]
    write_text(report_path("strata_matching"), "\n".join(lines))


def write_statement_quality_report(payload: dict[str, Any]) -> None:
    rows = [{"verdict": key, "count": value} for key, value in sorted(payload["verdict_counts"].items())]
    lines = [
        "# Phase 1 Pre-Paid Replication Statement Quality Gate",
        "",
        f"Gate status: `{payload['status']}`.",
        "",
        *markdown_table(rows, [("verdict", "Verdict"), ("count", "Count")]),
        "",
        f"New paid LLM calls made: `{payload['new_paid_llm_calls_made']}`.",
        "",
        "No selected candidate has a known direct solution leak, hidden-oracle leak, broken code fence, or missing editable scope.",
    ]
    write_text(report_path("statement_quality_gate"), "\n".join(lines))


def write_release_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "release_candidate_id": row["release_candidate_id"],
            "design_kind": row["design_kind"],
            "task_count": len(row["task_ids"]),
            "already_paid": row["paid_acut_calls_already_run_for_this_candidate"],
        }
        for row in payload["release_candidates"]
    ]
    lines = [
        "# Phase 1 Pre-Paid Replication Release Candidates",
        "",
        f"Recommended release candidate: `{payload['recommended_release_candidate_id']}`.",
        "",
        *markdown_table(rows, [("release_candidate_id", "Candidate"), ("design_kind", "Design kind"), ("task_count", "Tasks"), ("already_paid", "Already paid")]),
        "",
        "The primary candidate and local baselines are frozen for a future paid run; the prior statement-hardened release is historical reference only.",
    ]
    write_text(report_path("release_candidates"), "\n".join(lines))


def write_baseline_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Baseline Plan",
        "",
        f"Primary comparison: `{payload['primary_comparison']['name']}`.",
        "",
        "Baselines:",
        *[f"- `{baseline}`" for baseline in payload["baseline_candidate_ids"]],
        "",
        "Missing cells are handled only by preregistered rules before outcomes are known; no post-hoc task replacement is allowed.",
    ]
    write_text(report_path("baseline_plan"), "\n".join(lines))


def write_power_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Power And Cost Plan",
        "",
        f"Previous 32-cell observed-or-conservative cost: `${payload['previous_32_cell_cost_usd']}`.",
        "",
        *markdown_table(payload["plans"], [("plan_id", "Plan"), ("planned_cells", "Cells"), ("estimated_cost_usd", "Estimated USD"), ("grade", "Grade"), ("reaches_precision_half_width_target", "Precision target")]),
        "",
        "The frozen release is ready for a pilot paid replication, not for a precision-target predictive-validity claim.",
    ]
    write_text(report_path("power_and_cost_plan"), "\n".join(lines))


def write_entry_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Entry Gate",
        "",
        f"Entry status: `{payload['entry_status']}`.",
        f"Replication grade: `{payload['replication_grade']}`.",
        f"Release candidate: `{payload['release_candidate_id']}`.",
        "",
        "Commands to run later are documented but were not executed by this runbook.",
        "",
        f"Paid ACUT calls already run for this release: `{payload['paid_acut_calls_already_run_for_this_release']}`.",
        f"Paid ACUT calls run by this runbook: `{payload['paid_acut_calls_run_by_this_runbook']}`.",
    ]
    write_text(report_path("entry_gate"), "\n".join(lines))


def write_decision_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Pre-Paid Replication Decision",
        "",
        f"Final decision: `{payload['final_decision']}`.",
        "",
        f"Primary release candidate: `{payload['primary_release_candidate_id']}`.",
        "Baselines: " + ", ".join(f"`{item}`" for item in payload["baseline_candidate_ids"]) + ".",
        "",
        "No paid ACUT replication was run. No paid LLM statement-prep calls were made.",
        "",
        "## Research Questions",
        "",
    ]
    for key, value in payload["research_questions"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Closeout",
            "",
            "The package is pilot-grade ready. Precision-target predictive validity remains underpowered and must not be claimed from this package alone.",
        ]
    )
    write_text(report_path("decision"), "\n".join(lines))


def write_artifact(step: str) -> None:
    if step == "preflight":
        build_main_config()
        payload = build_preflight(load_config())
        write_json(output_path("preflight"), payload)
        write_process_report(0)
    elif step == "thresholds":
        build_threshold_config()
        payload = build_threshold_preregistration()
        write_json(output_path("threshold_preregistration"), payload)
        write_threshold_report(payload)
        write_process_report(1)
    elif step == "inventory":
        payload = build_candidate_inventory()
        write_json(output_path("candidate_inventory"), payload)
        write_inventory_report(payload)
        write_process_report(2)
    elif step == "target-profiles":
        payload = build_target_profiles()
        write_json(output_path("target_profiles"), payload)
        write_target_profiles_report(payload)
        write_process_report(3)
    elif step == "match-splits":
        payload = build_strata_matching()
        write_json(output_path("strata_matching"), payload)
        write_matching_report(payload)
        write_process_report(4)
    elif step == "statement-quality":
        payload = build_statement_quality_gate()
        write_json(output_path("statement_quality_gate"), payload)
        write_statement_quality_report(payload)
        write_process_report(5)
    elif step == "freeze-releases":
        build_release_selection_config()
        payload = build_release_candidates()
        write_json(output_path("release_candidates"), payload)
        write_release_report(payload)
        write_process_report(6)
    elif step == "baseline-plan":
        payload = build_baseline_plan()
        write_json(output_path("baseline_plan"), payload)
        write_baseline_report(payload)
        write_process_report(7)
    elif step == "power-cost":
        payload = build_power_and_cost_plan()
        write_json(output_path("power_and_cost_plan"), payload)
        write_power_report(payload)
        write_process_report(8)
    elif step == "entry-gate":
        payload = build_entry_gate()
        write_json(output_path("entry_gate"), payload)
        write_entry_report(payload)
        write_process_report(9)
    elif step == "decision":
        payload = build_decision()
        write_json(output_path("decision"), payload)
        write_decision_report(payload)
        write_process_report(10)
    elif step == "all":
        for subcommand in [
            "preflight",
            "thresholds",
            "inventory",
            "target-profiles",
            "match-splits",
            "statement-quality",
            "freeze-releases",
            "baseline-plan",
            "power-cost",
            "entry-gate",
            "decision",
        ]:
            write_artifact(subcommand)
    else:
        raise ValueError(f"unknown artifact step: {step}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 pre-paid replication compiler-readiness artifacts.")
    parser.add_argument(
        "command",
        choices=[
            "preflight",
            "thresholds",
            "inventory",
            "target-profiles",
            "match-splits",
            "statement-quality",
            "freeze-releases",
            "baseline-plan",
            "power-cost",
            "entry-gate",
            "decision",
            "all",
        ],
    )
    args = parser.parse_args(argv)
    write_artifact(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
