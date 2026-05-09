#!/usr/bin/env python3
"""Build Scorecard v0 from already-materialized core narrative evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now


TOOL = "scorecard_v0_from_existing_matrices"
SCHEMA_VERSION = "core-narrative.scorecard-v0-existing-matrices.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-09_scorecard_v0_existing_matrices_report.md"
DEFAULT_OUTPUT = DEFAULT_RESULTS_ROOT / "scorecard_v0_existing_matrices_20260509.json"

INPUT_FILES = {
    "rbench_canonical_matrix": "codex_nfl_rbench_canonical_matrix_20260508.json",
    "rwork_canonical_matrix": "codex_nfl_rwork_canonical_matrix_20260508.json",
    "measurement_stabilization_m1_1_summary": "measurement_stabilization_m1_1_summary_20260509.json",
    "m2_scoreability_summary": "m2_scoreability_summary_20260509.json",
    "unsafe_generated_text_triage": "unsafe_generated_text_triage_20260509.json",
    "gscore_gold_patch_smoke": "gscore_gold_patch_smoke_20260509.json",
}
MATRIX_INPUTS = {"rbench_canonical_matrix", "rwork_canonical_matrix"}
OUTCOME_BUCKETS = ("passed", "failed", "timeout", "invalid_submission", "infra_failed", "missing", "blocked", "other")
SCOREABLE_STATUSES = {"passed", "failed", "timeout", "invalid_submission"}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--rbench-matrix")
    parser.add_argument("--rwork-matrix")
    parser.add_argument("--m1-summary")
    parser.add_argument("--m2-summary")
    parser.add_argument("--unsafe-triage")
    parser.add_argument("--gscore-smoke")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv))


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def as_sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def as_count_map(value: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(value, Mapping):
        return counts
    for key, count in value.items():
        if not isinstance(key, str):
            continue
        if isinstance(count, bool):
            continue
        if isinstance(count, int):
            counts[key] = count
        elif isinstance(count, float) and count.is_integer():
            counts[key] = int(count)
    return dict(sorted(counts.items()))


def increment(counts: dict[str, int], key: str, amount: int = 1) -> None:
    counts[key] = counts.get(key, 0) + amount


def merge_counts(target: dict[str, int], source: Mapping[str, int]) -> None:
    for key, count in source.items():
        increment(target, key, int(count))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_input_paths(results_root: str | Path = DEFAULT_RESULTS_ROOT) -> dict[str, Path]:
    root = Path(results_root)
    return {key: root / filename for key, filename in INPUT_FILES.items()}


def load_input(input_key: str, path_value: str | Path | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if path_value is None:
        return {
            "path": None,
            "present": False,
            "status": "missing_input",
            "required_for_scorecard_v0": input_key != "gscore_gold_patch_smoke",
        }, None
    path = Path(path_value)
    info: dict[str, Any] = {
        "path": str(path),
        "present": False,
        "status": "missing_input",
        "required_for_scorecard_v0": input_key != "gscore_gold_patch_smoke",
    }
    if not path.exists():
        return info, None
    try:
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        info["status"] = "invalid_json"
        info["error"] = str(exc)
        return info, None
    except OSError as exc:
        info["status"] = "read_error"
        info["error"] = str(exc)
        return info, None
    if not isinstance(payload, dict):
        info["status"] = "invalid_json_root"
        return info, None
    info.update(
        {
            "present": True,
            "status": "loaded",
            "sha256": sha256_file(path),
            "byte_count": path.stat().st_size,
            "tool": payload.get("tool"),
            "schema_version": payload.get("schema_version"),
            "payload_status": payload.get("status"),
            "generated_at": payload.get("generated_at"),
        }
    )
    return info, payload


def outcome_bucket(status: str) -> str:
    return status if status in OUTCOME_BUCKETS else "other"


def failure_class_from_label(status: str, label: object) -> str:
    if isinstance(label, str) and ":" in label:
        parsed = label.split(":", 1)[1].strip()
        if parsed:
            return parsed
    if status == "passed":
        return "none"
    if status == "failed":
        return "unclassified_verifier_failure"
    if status == "timeout":
        return "agent_timeout"
    if status == "invalid_submission":
        return "malformed_submission"
    if status == "infra_failed":
        return "infrastructure"
    if status in {"missing", "blocked"}:
        return status
    return "unknown_unclassified"


def failure_owner(status: str) -> str:
    if status == "passed":
        return "none"
    if status in {"failed", "timeout"}:
        return "candidate_patch"
    if status == "invalid_submission":
        return "model_output"
    if status == "infra_failed":
        return "infrastructure"
    if status == "missing":
        return "missing"
    if status == "blocked":
        return "blocked"
    return "unknown"


def empty_outcome_counts() -> dict[str, int]:
    return {bucket: 0 for bucket in OUTCOME_BUCKETS}


def matrix_task_ids(matrix: Mapping[str, Any]) -> list[str]:
    tasks = [str(item) for item in as_sequence(matrix.get("task_ids")) if isinstance(item, str)]
    if tasks:
        return tasks
    cells = as_mapping(matrix.get("cells"))
    return sorted({key.split("::", 1)[1] for key in cells if isinstance(key, str) and "::" in key})


def matrix_acut_ids(matrix: Mapping[str, Any]) -> list[str]:
    acuts = [str(item) for item in as_sequence(matrix.get("acut_ids")) if isinstance(item, str)]
    if acuts:
        return acuts
    cells = as_mapping(matrix.get("cells"))
    return sorted({key.split("::", 1)[0] for key in cells if isinstance(key, str) and "::" in key})


def matrix_expected_cells(matrix: Mapping[str, Any], acuts: Sequence[str], tasks: Sequence[str]) -> int:
    shape = as_mapping(matrix.get("matrix_shape"))
    expected = shape.get("expected_cells")
    if isinstance(expected, int):
        return expected
    return len(acuts) * len(tasks)


def canonical_matrix_entries(input_key: str, matrix: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    split = str(matrix.get("split") or input_key.replace("_canonical_matrix", ""))
    acuts = matrix_acut_ids(matrix)
    tasks = matrix_task_ids(matrix)
    expected_cells = matrix_expected_cells(matrix, acuts, tasks)
    cells = as_mapping(matrix.get("cells"))
    entries: list[dict[str, Any]] = []
    outcome_counts = empty_outcome_counts()
    owner_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    scoreable_count = 0
    passed_count = 0
    present_count = 0

    for acut_id in acuts:
        for task_id in tasks:
            cell = as_mapping(cells.get(f"{acut_id}::{task_id}"))
            latest = cell.get("canonical_latest") if isinstance(cell.get("canonical_latest"), Mapping) else None
            present = isinstance(latest, Mapping)
            status = str(latest.get("status")) if present else "missing"
            label = latest.get("failure_label") if present else "missing"
            bucket = outcome_bucket(status)
            owner = failure_owner(bucket)
            failure_class = failure_class_from_label(bucket, label)
            scoreable = bool(latest.get("scoreable")) if present and latest.get("scoreable") in (True, False) else bucket in SCOREABLE_STATUSES
            if present:
                present_count += 1
            if scoreable:
                scoreable_count += 1
            if bucket == "passed":
                passed_count += 1
            increment(outcome_counts, bucket)
            increment(owner_counts, owner)
            increment(class_counts, failure_class)
            entries.append(
                {
                    "source_input": input_key,
                    "entry_type": "canonical_matrix_cell",
                    "split": split,
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "present": present,
                    "status": status,
                    "outcome_bucket": bucket,
                    "scoreable": scoreable,
                    "failure_label": label,
                    "failure_owner": owner,
                    "failure_class": failure_class,
                    "attempt": latest.get("attempt") if present else None,
                    "run_id": latest.get("run_id") if present else None,
                }
            )

    missing = as_mapping(matrix.get("missing"))
    attempt2_missing = [item for item in as_sequence(missing.get("attempt2_cells")) if isinstance(item, Mapping)]
    canonical_missing = [item for item in as_sequence(missing.get("canonical_cells")) if isinstance(item, Mapping)]
    fixed_denominator = {
        "split": split,
        "acut_count": len(acuts),
        "task_count": len(tasks),
        "expected_cells": expected_cells,
        "canonical_present": present_count,
        "canonical_missing": max(expected_cells - present_count, 0),
        "scoreable_count": scoreable_count,
    }
    summary = {
        "input_key": input_key,
        "split": split,
        "task_ids": list(tasks),
        "acut_ids": list(acuts),
        "fixed_denominator": fixed_denominator,
        "missing_run_summary": {
            "canonical_missing_count": max(expected_cells - present_count, 0),
            "attempt2_missing_count": len(attempt2_missing),
            "canonical_missing_cells": [dict(item) for item in canonical_missing],
            "attempt2_missing_cells": [dict(item) for item in attempt2_missing],
        },
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "failure_owner_counts": dict(sorted(owner_counts.items())),
        "failure_class_counts": dict(sorted(class_counts.items())),
        "rates": {
            "pass_rate_fixed_denominator": rate(passed_count, expected_cells),
            "scoreable_pass_rate": rate(passed_count, scoreable_count),
        },
    }
    return summary, entries


def summarize_canonical_matrices(payloads: Mapping[str, dict[str, Any] | None]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_split: dict[str, Any] = {}
    entries: list[dict[str, Any]] = []
    total_expected = 0
    total_present = 0
    total_scoreable = 0
    total_passed = 0
    total_outcomes = empty_outcome_counts()
    total_owner_counts: dict[str, int] = {}
    total_class_counts: dict[str, int] = {}
    missing_by_split: dict[str, Any] = {}

    for input_key in ("rbench_canonical_matrix", "rwork_canonical_matrix"):
        payload = payloads.get(input_key)
        if not isinstance(payload, Mapping):
            continue
        split_summary, split_entries = canonical_matrix_entries(input_key, payload)
        split = str(split_summary["split"])
        by_split[split] = split_summary
        missing_by_split[split] = split_summary["missing_run_summary"]
        entries.extend(split_entries)
        denom = split_summary["fixed_denominator"]
        total_expected += int(denom["expected_cells"])
        total_present += int(denom["canonical_present"])
        total_scoreable += int(denom["scoreable_count"])
        total_passed += int(split_summary["outcome_counts"].get("passed", 0))
        merge_counts(total_outcomes, split_summary["outcome_counts"])
        merge_counts(total_owner_counts, split_summary["failure_owner_counts"])
        merge_counts(total_class_counts, split_summary["failure_class_counts"])

    overall = {
        "fixed_denominator": {
            "expected_cells": total_expected,
            "canonical_present": total_present,
            "canonical_missing": max(total_expected - total_present, 0),
            "scoreable_count": total_scoreable,
        },
        "outcome_counts": dict(sorted(total_outcomes.items())),
        "failure_owner_counts": dict(sorted(total_owner_counts.items())),
        "failure_class_counts": dict(sorted(total_class_counts.items())),
        "rates": {
            "pass_rate_fixed_denominator": rate(total_passed, total_expected),
            "scoreable_pass_rate": rate(total_passed, total_scoreable),
        },
    }
    return {
        "overall": overall,
        "by_split": by_split,
        "missing_by_split": missing_by_split,
    }, entries


def summarize_m1(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"present": False}
    contracts: dict[str, Any] = {}
    for contract, summary in as_mapping(payload.get("contracts")).items():
        if not isinstance(contract, str) or not isinstance(summary, Mapping):
            continue
        contracts[contract] = {
            "total": summary.get("total"),
            "status_counts": as_count_map(summary.get("status_counts")),
            "failure_owner_counts": as_count_map(summary.get("failure_owner_counts")),
            "failure_class_counts": as_count_map(summary.get("failure_class_counts")),
            "invalid_submission_count": summary.get("invalid_submission_count"),
            "invalid_submission_rate": summary.get("invalid_submission_rate"),
            "patch_ready_count": summary.get("patch_ready_count"),
            "patch_ready_coverage": summary.get("patch_ready_coverage"),
            "canonical_scoreable_count": summary.get("canonical_scoreable_count"),
            "canonical_scoreable_coverage": summary.get("canonical_scoreable_coverage"),
            "model_call_made_count": summary.get("model_call_made_count"),
        }
    return {
        "present": True,
        "tool_status": payload.get("status"),
        "tasks": as_sequence(payload.get("tasks")),
        "acuts": as_sequence(payload.get("acuts")),
        "fixed_denominator_by_contract": {key: value.get("total") for key, value in contracts.items()},
        "claim_status": payload.get("claim_status"),
        "effect": as_mapping(payload.get("effect")),
        "contracts": contracts,
    }


def summarize_m2(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"present": False}
    evidence_inputs = as_mapping(payload.get("evidence_inputs"))
    paths: dict[str, Any] = {}
    for path_id, summary in as_mapping(payload.get("paths")).items():
        if not isinstance(path_id, str) or not isinstance(summary, Mapping):
            continue
        gate = as_mapping(summary.get("gate"))
        input_info = as_mapping(evidence_inputs.get(path_id))
        paths[path_id] = {
            "contract": input_info.get("contract"),
            "kind": input_info.get("kind"),
            "total": summary.get("total"),
            "status_counts": as_count_map(summary.get("status_counts")),
            "failure_owner_counts": as_count_map(summary.get("failure_owner_counts")),
            "failure_class_counts": as_count_map(summary.get("failure_class_counts")),
            "invalid_submission_count": summary.get("invalid_submission_count"),
            "invalid_submission_rate": summary.get("invalid_submission_rate"),
            "patch_ready_count": summary.get("patch_ready_count"),
            "patch_ready_coverage": summary.get("patch_ready_coverage"),
            "clean_replay_attempted_count": summary.get("clean_replay_attempted_count"),
            "clean_replay_success_count": summary.get("clean_replay_success_count"),
            "clean_replay_success_rate": summary.get("clean_replay_success_rate"),
            "clean_replay_disagreement_count": summary.get("clean_replay_disagreement_count"),
            "missing_cell_count": summary.get("missing_cell_count"),
            "blocked_cell_count": summary.get("blocked_cell_count"),
            "excluded_row_count": summary.get("excluded_row_count"),
            "model_call_made_counts": as_count_map(summary.get("model_call_made_counts")),
            "gate_status": gate.get("status"),
            "gate_checks": as_mapping(gate.get("checks")),
            "gate_thresholds": as_mapping(gate.get("thresholds")),
        }
    return {
        "present": True,
        "tool_status": payload.get("status"),
        "tasks": as_sequence(payload.get("tasks")),
        "acuts": as_sequence(payload.get("acuts")),
        "fixed_denominator": payload.get("fixed_denominator"),
        "claim_status": payload.get("claim_status"),
        "paths": paths,
        "prohibited_claims": as_mapping(payload.get("prohibited_claims")),
    }


def summarize_unsafe(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"present": False}
    return {
        "present": True,
        "tool_status": payload.get("status"),
        "schema_version": payload.get("schema_version"),
        "model_or_api_budget_spent": payload.get("model_or_api_budget_spent"),
        "fixed_denominator": as_mapping(payload.get("fixed_denominator")),
        "summary": as_mapping(payload.get("summary")),
        "output_leakage_guard": as_mapping(payload.get("output_leakage_guard")),
    }


def blocker_counts(blockers: Sequence[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in blockers:
        if not isinstance(item, Mapping):
            continue
        label = item.get("blocker")
        if isinstance(label, str) and label:
            increment(counts, label)
    return dict(sorted(counts.items()))


def summarize_gscore(payload: Mapping[str, Any] | None, input_info: Mapping[str, Any]) -> dict[str, Any]:
    if not input_info.get("present") or not isinstance(payload, Mapping):
        return {
            "present": False,
            "available": False,
            "blocked": True,
            "availability_status": "unavailable_missing_evidence",
            "proxy_status": "not_proxy",
            "public_leaderboard_proxy_used": False,
            "reason": "G_score smoke artifact was not present; Scorecard v0 does not substitute proxy scores.",
        }
    direct = as_mapping(payload.get("direct_acut_scoring"))
    gold_path = as_mapping(payload.get("gold_patch_path"))
    blockers = [item for item in as_sequence(payload.get("blockers")) if isinstance(item, Mapping)]
    public_proxy = payload.get("public_leaderboard_proxy_used") is True
    available = direct.get("g_score_available") is True
    blocked = "blocked" in str(payload.get("status") or "") or bool(blockers)
    if public_proxy:
        availability = "unavailable_proxy_rejected"
        proxy_status = "proxy_input_rejected"
    elif available:
        availability = "available_reported_not_consumed_by_scorecard_v0"
        proxy_status = "not_proxy"
    elif blocked:
        availability = "unavailable_blocked"
        proxy_status = "not_proxy"
    else:
        availability = "unavailable_not_executed"
        proxy_status = "not_proxy"
    pinned = as_mapping(as_mapping(payload.get("checks")).get("pinned_config"))
    return {
        "present": True,
        "available": available,
        "blocked": blocked or not available,
        "availability_status": availability,
        "proxy_status": proxy_status,
        "public_leaderboard_proxy_used": public_proxy,
        "gold_patch_smoke_status": payload.get("status"),
        "gold_patch_basis_proven": gold_path.get("basis_proven") is True,
        "gold_patch_ran": gold_path.get("ran") is True,
        "direct_acut_scoring_attempted": direct.get("attempted") is True,
        "blocker_counts": blocker_counts(blockers),
        "check_statuses": {
            key: as_mapping(value).get("status")
            for key, value in as_mapping(payload.get("checks")).items()
            if isinstance(value, Mapping)
        },
        "fixed_denominator": as_mapping(pinned.get("denominator")),
    }


def fixed_denominators(
    matrix_summary: Mapping[str, Any],
    m1: Mapping[str, Any],
    m2: Mapping[str, Any],
    unsafe: Mapping[str, Any],
    g_score: Mapping[str, Any],
) -> dict[str, Any]:
    matrix_by_split = {
        split: as_mapping(summary).get("fixed_denominator")
        for split, summary in as_mapping(matrix_summary.get("by_split")).items()
    }
    m2_paths = {
        path_id: {"total": summary.get("total"), "contract": summary.get("contract"), "kind": summary.get("kind")}
        for path_id, summary in as_mapping(m2.get("paths")).items()
        if isinstance(summary, Mapping)
    }
    return {
        "canonical_matrices": {
            "overall": as_mapping(matrix_summary.get("overall")).get("fixed_denominator"),
            "by_split": matrix_by_split,
        },
        "measurement_stabilization_m1_1": {
            "present": m1.get("present") is True,
            "tasks": m1.get("tasks", []),
            "acuts": m1.get("acuts", []),
            "by_contract": m1.get("fixed_denominator_by_contract", {}),
        },
        "m2_scoreability": {
            "present": m2.get("present") is True,
            "fixed_denominator": m2.get("fixed_denominator"),
            "paths": m2_paths,
        },
        "unsafe_generated_text_triage": {
            "present": unsafe.get("present") is True,
            "fixed_denominator": unsafe.get("fixed_denominator", {}),
        },
        "g_score_basis": {
            "present": g_score.get("present") is True,
            "availability_status": g_score.get("availability_status"),
            "fixed_denominator": g_score.get("fixed_denominator", {}),
        },
    }


def claim_boundaries() -> dict[str, Any]:
    return {
        "evidence_consumer_only": True,
        "model_or_api_budget_spent": False,
        "proves": [
            "Existing RBench/RWork canonical matrices can be converted into fixed-denominator evidence states.",
            "Pass, fail, invalid-submission, infrastructure, missing, and blocked evidence are not interchangeable.",
            "Existing M1.1, M2, unsafe triage, and gold-patch smoke artifacts can be consumed without new live model calls.",
        ],
        "does_not_prove": [
            "direct G_score ACUT performance",
            "capability uplift",
            "task-solving improvement",
            "ranking reversal",
            "G_score predictivity",
            "license or admission decision",
        ],
        "prohibited_claims": {
            "capability_uplift": False,
            "task_solving_improvement": False,
            "ranking_reversal": False,
            "g_score_predictivity": False,
            "license_or_admission_output": False,
        },
    }


def not_authorization_summary() -> dict[str, Any]:
    return {
        "not_authorization": True,
        "role": "diagnostic_scorecard_v0_from_existing_evidence",
        "emits_license_or_admission_output": False,
        "emits_authorization_tier": False,
        "emits_repository_permission": False,
        "simulated_policy_inputs": "not_emitted",
    }


def evidence_digest_material(evidence_inputs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    material: dict[str, Any] = {}
    for key in sorted(evidence_inputs):
        info = evidence_inputs[key]
        material[key] = {
            "present": info.get("present") is True,
            "sha256": info.get("sha256"),
            "tool": info.get("tool"),
            "schema_version": info.get("schema_version"),
            "payload_status": info.get("payload_status"),
            "status": info.get("status"),
        }
    return material


def build_scorecard(input_paths: Mapping[str, str | Path | None] | None = None) -> dict[str, Any]:
    resolved_paths: dict[str, str | Path | None]
    if input_paths is None:
        resolved_paths = default_input_paths()
    else:
        resolved_paths = {key: input_paths.get(key) for key in INPUT_FILES}

    evidence_inputs: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any] | None] = {}
    for input_key in INPUT_FILES:
        info, payload = load_input(input_key, resolved_paths.get(input_key))
        evidence_inputs[input_key] = info
        payloads[input_key] = payload

    matrix_summary, matrix_entries = summarize_canonical_matrices(payloads)
    m1 = summarize_m1(payloads.get("measurement_stabilization_m1_1_summary"))
    m2 = summarize_m2(payloads.get("m2_scoreability_summary"))
    unsafe = summarize_unsafe(payloads.get("unsafe_generated_text_triage"))
    g_score = summarize_gscore(payloads.get("gscore_gold_patch_smoke"), evidence_inputs["gscore_gold_patch_smoke"])
    boundaries = claim_boundaries()
    not_authorization = not_authorization_summary()
    fixed = fixed_denominators(matrix_summary, m1, m2, unsafe, g_score)

    score_input_material = {
        "schema_version": SCHEMA_VERSION,
        "evidence_inputs": evidence_digest_material(evidence_inputs),
        "canonical_matrix_entries": matrix_entries,
        "contract_scoreability": {"m1_1": m1, "m2": m2},
        "unsafe_generated_text": unsafe,
        "g_score": g_score,
        "not_authorization": not_authorization,
    }

    payload = {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "scorecard_version": "scorecard_v0_from_existing_matrices",
        "generated_at": iso_now(),
        "status": "completed",
        "model_or_api_budget_spent": False,
        "input_policy": {
            "mode": "existing_artifacts_only",
            "no_live_model_calls": True,
            "default_inputs": INPUT_FILES,
        },
        "evidence_inputs": evidence_inputs,
        "evidence_input_set_digest": digest_payload(evidence_digest_material(evidence_inputs)),
        "score_input_set_digest": digest_payload(score_input_material),
        "score_input_entry_count": len(matrix_entries),
        "score_input_entries": matrix_entries,
        "fixed_denominators": fixed,
        "missing_run_summary": {
            "canonical_matrices": matrix_summary["missing_by_split"],
            "m2_scoreability": {
                path_id: {
                    "missing_cell_count": summary.get("missing_cell_count"),
                    "blocked_cell_count": summary.get("blocked_cell_count"),
                    "excluded_row_count": summary.get("excluded_row_count"),
                }
                for path_id, summary in as_mapping(m2.get("paths")).items()
                if isinstance(summary, Mapping)
            },
            "g_score": {
                "availability_status": g_score.get("availability_status"),
                "blocked": g_score.get("blocked"),
                "blocker_counts": g_score.get("blocker_counts", {}),
            },
        },
        "outcome_counts": {
            "canonical_matrices": {
                "overall": matrix_summary["overall"]["outcome_counts"],
                "by_split": {
                    split: summary["outcome_counts"]
                    for split, summary in as_mapping(matrix_summary.get("by_split")).items()
                    if isinstance(summary, Mapping)
                },
            }
        },
        "rates": {
            "canonical_matrices": {
                "overall": matrix_summary["overall"]["rates"],
                "by_split": {
                    split: summary["rates"]
                    for split, summary in as_mapping(matrix_summary.get("by_split")).items()
                    if isinstance(summary, Mapping)
                },
            }
        },
        "failure_distributions": {
            "canonical_matrices": {
                "failure_owner_counts": matrix_summary["overall"]["failure_owner_counts"],
                "failure_class_counts": matrix_summary["overall"]["failure_class_counts"],
                "by_split": {
                    split: {
                        "failure_owner_counts": summary["failure_owner_counts"],
                        "failure_class_counts": summary["failure_class_counts"],
                    }
                    for split, summary in as_mapping(matrix_summary.get("by_split")).items()
                    if isinstance(summary, Mapping)
                },
            },
            "measurement_stabilization_m1_1": {
                contract: {
                    "failure_owner_counts": summary.get("failure_owner_counts"),
                    "failure_class_counts": summary.get("failure_class_counts"),
                }
                for contract, summary in as_mapping(m1.get("contracts")).items()
                if isinstance(summary, Mapping)
            },
            "m2_scoreability": {
                path_id: {
                    "failure_owner_counts": summary.get("failure_owner_counts"),
                    "failure_class_counts": summary.get("failure_class_counts"),
                }
                for path_id, summary in as_mapping(m2.get("paths")).items()
                if isinstance(summary, Mapping)
            },
            "unsafe_generated_text": as_mapping(as_mapping(unsafe.get("summary")).get("classification_counts")),
        },
        "contract_scoreability": {
            "measurement_stabilization_m1_1": m1,
            "m1_1": m1,
            "m2": m2,
        },
        "unsafe_generated_text": unsafe,
        "g_score": g_score,
        "not_authorization": not_authorization,
        "claim_boundaries": boundaries,
    }
    return payload


def flatten_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(flatten_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(flatten_keys(child))
    return keys


def fmt_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{100 * float(value):.1f}%"
    return "n/a"


def fmt_counts(value: object) -> str:
    counts = as_count_map(value)
    if not counts:
        return "none"
    return ", ".join(f"`{key}`: {count}" for key, count in counts.items() if count)


def report_markdown(payload: Mapping[str, Any]) -> str:
    matrices = as_mapping(payload.get("fixed_denominators")).get("canonical_matrices")
    matrix_denoms = as_mapping(as_mapping(matrices).get("by_split"))
    matrix_counts = as_mapping(as_mapping(payload.get("outcome_counts")).get("canonical_matrices")).get("by_split")
    matrix_rates = as_mapping(as_mapping(payload.get("rates")).get("canonical_matrices")).get("by_split")
    failure = as_mapping(as_mapping(payload.get("failure_distributions")).get("canonical_matrices"))
    m2 = as_mapping(as_mapping(payload.get("contract_scoreability")).get("m2"))
    unsafe = as_mapping(payload.get("unsafe_generated_text"))
    g_score = as_mapping(payload.get("g_score"))

    rows: list[str] = []
    for split in sorted(matrix_denoms):
        denom = as_mapping(matrix_denoms.get(split))
        counts = as_mapping(as_mapping(matrix_counts).get(split))
        rates = as_mapping(as_mapping(matrix_rates).get(split))
        rows.append(
            "| "
            + " | ".join(
                [
                    f"`{split}`",
                    str(denom.get("expected_cells")),
                    fmt_rate(rates.get("pass_rate_fixed_denominator")),
                    fmt_counts(counts),
                    str(denom.get("canonical_missing")),
                ]
            )
            + " |"
        )
    if not rows:
        rows.append("| none | 0 | n/a | none | 0 |")

    m2_rows: list[str] = []
    for path_id, summary in as_mapping(m2.get("paths")).items():
        if not isinstance(summary, Mapping):
            continue
        m2_rows.append(
            "| "
            + " | ".join(
                [
                    f"`{path_id}`",
                    f"`{summary.get('contract')}`",
                    str(summary.get("total")),
                    fmt_counts(summary.get("status_counts")),
                    fmt_rate(summary.get("patch_ready_coverage")),
                    fmt_rate(summary.get("invalid_submission_rate")),
                    f"`{summary.get('gate_status')}`",
                ]
            )
            + " |"
        )
    if not m2_rows:
        m2_rows.append("| none | none | 0 | none | n/a | n/a | n/a |")

    input_lines = []
    for key, info in as_mapping(payload.get("evidence_inputs")).items():
        if not isinstance(info, Mapping):
            continue
        sha = str(info.get("sha256") or "missing")
        input_lines.append(
            f"- `{key}`: present `{info.get('present')}`, status `{info.get('status')}`, digest `{sha[:16]}`"
        )

    return f"""# Scorecard v0 From Existing Matrices

Date: 2026-05-09

## Scope

Scorecard v0 is a no-model consumer of existing evidence artifacts. It reads the canonical RBench/RWork matrices, M1.1 measurement-stabilization summary, M2 scoreability summary, unsafe-generated-text triage, and G_score gold-patch smoke when present. It does not call a model or provider API.

Machine-readable output:

- `experiments/core_narrative/results/scorecard_v0_existing_matrices_20260509.json`

## Inputs

{chr(10).join(input_lines)}

Score input set digest: `{payload.get("score_input_set_digest")}`  
Evidence input set digest: `{payload.get("evidence_input_set_digest")}`

## Canonical Matrix Evidence

| Split | Fixed cells | Bare pass rate | Evidence states | Missing canonical cells |
| --- | ---: | ---: | --- | ---: |
{chr(10).join(rows)}

Overall failure-owner counts: {fmt_counts(failure.get("failure_owner_counts"))}.  
Overall failure-class counts: {fmt_counts(failure.get("failure_class_counts"))}.

The bare pass rate is only one view. The same denominator also contains verifier failures, invalid submissions, infrastructure evidence, and missing-run accounting. RWork in particular should not be read as only a lower pass rate; much of its evidence is invalid-submission/output-contract failure rather than clean verifier failure.

## Contract And Scoreability Evidence

M1.1 claim status: `{as_mapping(as_mapping(payload.get("contract_scoreability")).get("m1_1")).get("claim_status")}`.  
M2 claim status: `{m2.get("claim_status")}`.

| Path | Contract | Cells | Status counts | Patch-ready | Invalid rate | Gate |
| --- | --- | ---: | --- | ---: | ---: | --- |
{chr(10).join(m2_rows)}

Unsafe triage classification counts: {fmt_counts(as_mapping(as_mapping(unsafe.get("summary")).get("classification_counts")))}.  
Unsafe triage output leakage guard: `{as_mapping(unsafe.get("output_leakage_guard")).get("contains_raw_unsafe_text")}`.

## G_score Availability

Availability: `{g_score.get("availability_status")}`.  
Gold-patch basis proven: `{g_score.get("gold_patch_basis_proven")}`.  
Public leaderboard proxy used: `{g_score.get("public_leaderboard_proxy_used")}`.  
Blockers: {fmt_counts(g_score.get("blocker_counts"))}.

G_score remains unavailable in this scorecard when the gold-patch smoke is blocked or missing. Scorecard v0 does not substitute public leaderboard scores and does not treat unavailable G_score as zero.

## Claim Boundary

This artifact proves that existing result matrices and summaries can be assembled into a digest-addressed, fixed-denominator diagnostic scorecard. It preserves pass/fail/invalid/infra/missing distinctions, failure owner/class distributions, contract fields, scoreability gates, unsafe triage categories, and G_score availability state.

It does not prove capability uplift, task-solving improvement, ranking reversal, G_score predictivity, or any license/admission decision. It also does not change the M2 conclusion: live scoreability is not yet restored on the selected RWork smoke.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/scorecard_v0_from_existing_matrices.py \\
  --output experiments/core_narrative/results/scorecard_v0_existing_matrices_20260509.json \\
  --report experiments/core_narrative/reports/2026-05-09_scorecard_v0_existing_matrices_report.md
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def input_paths_from_args(args: argparse.Namespace) -> dict[str, Path]:
    paths = default_input_paths(args.results_root)
    overrides = {
        "rbench_canonical_matrix": args.rbench_matrix,
        "rwork_canonical_matrix": args.rwork_matrix,
        "measurement_stabilization_m1_1_summary": args.m1_summary,
        "m2_scoreability_summary": args.m2_summary,
        "unsafe_generated_text_triage": args.unsafe_triage,
        "gscore_gold_patch_smoke": args.gscore_smoke,
    }
    for key, value in overrides.items():
        if value:
            paths[key] = Path(value)
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_scorecard(input_paths_from_args(args))
        if args.report:
            write_report(args.report, payload)
        emit_json(payload, args.output)
        return 0
    except ToolError as exc:
        return fail(TOOL, exc)
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
