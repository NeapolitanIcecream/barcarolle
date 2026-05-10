#!/usr/bin/env python3
"""Assess M2 fixed-grid scoreability gates from an existing replay matrix.

This tool is intentionally no-call: it consumes already-recorded matrix JSON
and companion summary metadata only. It does not invoke providers, rerun ACUTs,
or mutate the cost ledger.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now
from _llm_budget import unsafe_text_findings


TOOL = "m2_fixed_grid_gate_assessment"
SCHEMA_VERSION = "core-narrative.m2-fixed-grid-gate-assessment.v1"

DEFAULT_MATRIX = (
    "experiments/core_narrative/results/"
    "m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap_20260510.json"
)
DEFAULT_OUTPUT = "experiments/core_narrative/results/m2_fixed_grid_gate_assessment_20260510.json"
DEFAULT_REPORT = "experiments/core_narrative/reports/2026-05-10_m2_fixed_grid_gate_assessment.md"

PATCH_OR_FILES_CONTRACT = "patch-or-files-v1"
ANCHORED_CONTRACT = "anchored-search-replace-json-v3"
PATCH_READY_COVERAGE_MIN = 0.70
INVALID_SUBMISSION_RATE_MAX = 0.25
CLEAN_REPLAY_DISAGREEMENT_COUNT_MAX = 0
ATTEMPTABLE_CATEGORIES = {
    "verifier_ready_persisted_patch_artifact",
    "nonpersistent_verifier_attempt",
}
PROHIBITED_CLAIMS = {
    "m2_passed": False,
    "ranking_reversal": False,
    "task_solving_improvement": False,
    "capability_uplift": False,
    "g_score_predictivity": False,
    "g0_g5": False,
    "license": False,
    "admission": False,
    "authorization": False,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    return parser.parse_args(list(argv))


def read_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("JSON root must be an object", path=str(path))
    return data


def maybe_read_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return {}
    try:
        return read_json(candidate)
    except (json.JSONDecodeError, ToolError):
        return {}


def count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def cell_key(row: Mapping[str, Any]) -> tuple[str, str] | None:
    acut_id = row.get("acut_id")
    task_id = row.get("task_id")
    if isinstance(acut_id, str) and acut_id and isinstance(task_id, str) and task_id:
        return acut_id, task_id
    return None


def expected_cells(section: Mapping[str, Any]) -> list[tuple[str, str]]:
    cells = section.get("expected_cells") if isinstance(section.get("expected_cells"), list) else []
    parsed: list[tuple[str, str]] = []
    for item in cells:
        if not isinstance(item, Mapping):
            continue
        acut_id = item.get("acut_id")
        task_id = item.get("task_id")
        if isinstance(acut_id, str) and isinstance(task_id, str):
            parsed.append((acut_id, task_id))
    return parsed


def row_category(row: Mapping[str, Any]) -> str:
    value = row.get("stable_category")
    return str(value) if value is not None else "unknown"


def is_attemptable(row: Mapping[str, Any]) -> bool:
    return row_category(row) in ATTEMPTABLE_CATEGORIES


def is_missing_raw(row: Mapping[str, Any] | None) -> bool:
    if row is None:
        return True
    if row_category(row) == "missing_raw_artifact":
        return True
    presence = row.get("artifact_presence") if isinstance(row.get("artifact_presence"), Mapping) else {}
    return presence.get("raw_response_artifact_exists") is not True


def rows_from_matrix(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = matrix.get("matrix") if isinstance(matrix.get("matrix"), list) else []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def first_by_cell(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    by_cell: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        key = cell_key(row)
        if key is not None and key not in by_cell:
            by_cell[key] = row
    return by_cell


def copy_selected_row(row: Mapping[str, Any] | None, *, acut_id: str, task_id: str, role: str) -> dict[str, Any]:
    if row is None:
        return {
            "acut_id": acut_id,
            "task_id": task_id,
            "assessment_evidence_role": role,
            "stable_category": "missing_input_record",
            "stable_failure_owner": "infrastructure",
            "stable_failure_class": "missing_fixed_grid_input_record",
            "verifier_attempt_channel": "not_attempted",
            "verifier_attemptable_after_replay": False,
        }
    selected = dict(row)
    selected["assessment_evidence_role"] = role
    return selected


def select_patch_or_files_effective_cells(matrix: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    patch_gap = matrix.get("patch_or_files_gap_acquisition")
    patch_gap = patch_gap if isinstance(patch_gap, Mapping) else {}
    cells = expected_cells(patch_gap)
    live = [
        row
        for row in rows
        if row.get("contract") == PATCH_OR_FILES_CONTRACT
        and row.get("source_label") == "patch_or_files_v1_live"
    ]
    acquisitions = [
        row
        for row in rows
        if row.get("contract") == PATCH_OR_FILES_CONTRACT
        and row.get("matrix_source") == "patch_or_files_acquisition_batch"
    ]
    live_by_cell = first_by_cell(live)
    acquisition_by_cell = first_by_cell(
        [row for row in acquisitions if row.get("acquired_raw_input") is True]
    )
    selected: list[dict[str, Any]] = []
    for acut_id, task_id in cells:
        key = (acut_id, task_id)
        historical = live_by_cell.get(key)
        acquisition = acquisition_by_cell.get(key)
        if historical is not None and is_missing_raw(historical) and acquisition is not None:
            row = copy_selected_row(
                acquisition,
                acut_id=acut_id,
                task_id=task_id,
                role="gap_acquisition_replaces_historical_missing_raw_input_for_gate_assessment",
            )
            row["historical_missing_raw_artifact_preserved"] = True
            row["historical_missing_run_id"] = historical.get("run_id")
            row["historical_missing_failure_class"] = historical.get("stable_failure_class")
        elif historical is not None:
            row = copy_selected_row(
                historical,
                acut_id=acut_id,
                task_id=task_id,
                role="historical_live_replay_matrix_row",
            )
            row["historical_missing_raw_artifact_preserved"] = False
        elif acquisition is not None:
            row = copy_selected_row(
                acquisition,
                acut_id=acut_id,
                task_id=task_id,
                role="gap_acquisition_without_historical_live_row",
            )
            row["historical_missing_raw_artifact_preserved"] = False
        else:
            row = copy_selected_row(
                None,
                acut_id=acut_id,
                task_id=task_id,
                role="missing_effective_patch_or_files_cell",
            )
            row["historical_missing_raw_artifact_preserved"] = False
        selected.append(row)
    return selected


def choose_anchored_cell_row(candidates: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any] | None, str]:
    if not candidates:
        return None, "missing_effective_anchored_cell"

    def first_matching(predicate: Callable[[Mapping[str, Any]], bool]) -> Mapping[str, Any] | None:
        for row in candidates:
            if predicate(row):
                return row
        return None

    preferred = first_matching(lambda row: is_attemptable(row) and row.get("evidence_mode") == "fixed_grid_acquisition_live")
    if preferred is not None:
        return preferred, "fixed_grid_acquisition_attemptable_row"
    preferred = first_matching(lambda row: is_attemptable(row) and row.get("evidence_mode") == "no_model_replay")
    if preferred is not None:
        return preferred, "nonpersistent_no_model_replay_attemptable_row"
    preferred = first_matching(is_attemptable)
    if preferred is not None:
        return preferred, "attemptable_row"
    preferred = first_matching(lambda row: row.get("evidence_mode") == "fixed_grid_acquisition_live")
    if preferred is not None:
        return preferred, "fixed_grid_acquisition_live_row"
    return candidates[0], "available_historical_row"


def select_anchored_effective_cells(matrix: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fixed_grid = matrix.get("anchored_fixed_grid")
    fixed_grid = fixed_grid if isinstance(fixed_grid, Mapping) else {}
    cells = expected_cells(fixed_grid)
    anchored_rows = [
        row
        for row in rows
        if row.get("contract") == ANCHORED_CONTRACT and cell_key(row) is not None
    ]
    by_cell: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in anchored_rows:
        key = cell_key(row)
        if key is not None:
            by_cell.setdefault(key, []).append(row)
    selected: list[dict[str, Any]] = []
    for acut_id, task_id in cells:
        candidates = by_cell.get((acut_id, task_id), [])
        chosen, role = choose_anchored_cell_row(candidates)
        row = copy_selected_row(chosen, acut_id=acut_id, task_id=task_id, role=role)
        row["supporting_record_count"] = len(candidates)
        row["supporting_source_labels"] = sorted({str(item.get("source_label")) for item in candidates})
        row["supporting_evidence_mode_counts"] = count_by(candidates, "evidence_mode")
        row["supporting_category_counts"] = count_by(candidates, "stable_category")
        selected.append(row)
    return selected


def select_no_model_control_cells(matrix: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    patch_gap = matrix.get("patch_or_files_gap_acquisition")
    patch_gap = patch_gap if isinstance(patch_gap, Mapping) else {}
    cells = expected_cells(patch_gap)
    control_rows = [
        row
        for row in rows
        if row.get("contract") == PATCH_OR_FILES_CONTRACT
        and row.get("source_label") == "patch_or_files_v1_no_model"
    ]
    by_cell = first_by_cell(control_rows)
    return [
        copy_selected_row(
            by_cell.get((acut_id, task_id)),
            acut_id=acut_id,
            task_id=task_id,
            role="existing_no_model_control_row",
        )
        for acut_id, task_id in cells
    ]


def source_clean_replay_disagreements(matrix: Mapping[str, Any], path_id: str) -> int | None:
    inputs = matrix.get("inputs") if isinstance(matrix.get("inputs"), Mapping) else {}
    summary = maybe_read_json(inputs.get("m2_summary") if isinstance(inputs.get("m2_summary"), str) else None)
    paths = summary.get("paths") if isinstance(summary.get("paths"), Mapping) else {}
    path = paths.get(path_id) if isinstance(paths.get(path_id), Mapping) else {}
    value = path.get("clean_replay_disagreement_count")
    return int(value) if isinstance(value, int) else None


def blocker_id_for(path_id: str, row: Mapping[str, Any]) -> str:
    category = row_category(row)
    if category == "missing_raw_artifact" or row.get("stable_failure_class") == "missing_fixed_grid_input_record":
        return f"{path_id}.missing_input"
    if category == "infra_failure":
        return f"{path_id}.infrastructure_failure"
    if category == "cleanup_blocker":
        return f"{path_id}.cleanup_blocker"
    if category == "model_output_invalid_submission":
        return f"{path_id}.model_output_not_verifier_attemptable"
    return f"{path_id}.not_verifier_attemptable"


def exact_cell_blockers(path_id: str, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in rows:
        if is_attemptable(row):
            continue
        blockers.append(
            {
                "blocker_id": blocker_id_for(path_id, row),
                "acut_id": row.get("acut_id"),
                "task_id": row.get("task_id"),
                "stable_category": row_category(row),
                "failure_owner": row.get("stable_failure_owner"),
                "failure_class": row.get("stable_failure_class"),
                "attemptability_channel": row.get("verifier_attempt_channel"),
                "source_label": row.get("source_label"),
                "run_id": row.get("run_id"),
                "assessment_evidence_role": row.get("assessment_evidence_role"),
            }
        )
    return blockers


def gate_checks(
    *,
    denominator: int,
    selected_rows: Sequence[Mapping[str, Any]],
    clean_replay_disagreement_count: int | None,
    raw_input_gap_count: int,
) -> dict[str, Any]:
    attemptable = sum(1 for row in selected_rows if is_attemptable(row))
    invalid = sum(1 for row in selected_rows if row_category(row) == "model_output_invalid_submission")
    fixed_complete = len(selected_rows) == denominator and denominator > 0
    attemptability_rate = rate(attemptable, denominator)
    invalid_rate = rate(invalid, denominator)
    clean_replay_pass = (
        clean_replay_disagreement_count <= CLEAN_REPLAY_DISAGREEMENT_COUNT_MAX
        if clean_replay_disagreement_count is not None
        else None
    )
    return {
        "complete_fixed_denominator": fixed_complete,
        "raw_input_gap_closed": raw_input_gap_count == 0,
        "attemptability_coverage": (
            isinstance(attemptability_rate, (int, float))
            and attemptability_rate >= PATCH_READY_COVERAGE_MIN
        ),
        "model_output_invalid_submission_rate": (
            isinstance(invalid_rate, (int, float))
            and invalid_rate <= INVALID_SUBMISSION_RATE_MAX
        ),
        "clean_replay_disagreement_count": clean_replay_pass,
    }


def path_gate_status(checks: Mapping[str, Any]) -> str:
    if checks.get("complete_fixed_denominator") is not True or checks.get("raw_input_gap_closed") is not True:
        return "blocked"
    decisive = [
        checks.get("attemptability_coverage"),
        checks.get("model_output_invalid_submission_rate"),
    ]
    if checks.get("clean_replay_disagreement_count") is not None:
        decisive.append(checks.get("clean_replay_disagreement_count"))
    if all(item is True for item in decisive):
        return "passed"
    return "failed"


def assess_path(
    *,
    path_id: str,
    contract: str,
    denominator: int,
    selected_rows: Sequence[Mapping[str, Any]],
    clean_replay_disagreement_count: int | None,
    raw_input_gap_count: int,
    role: str,
) -> dict[str, Any]:
    attemptable = sum(1 for row in selected_rows if is_attemptable(row))
    invalid = sum(1 for row in selected_rows if row_category(row) == "model_output_invalid_submission")
    checks = gate_checks(
        denominator=denominator,
        selected_rows=selected_rows,
        clean_replay_disagreement_count=clean_replay_disagreement_count,
        raw_input_gap_count=raw_input_gap_count,
    )
    return {
        "path_id": path_id,
        "contract": contract,
        "role": role,
        "gate_status": path_gate_status(checks),
        "thresholds": {
            "attemptability_coverage_min": PATCH_READY_COVERAGE_MIN,
            "model_output_invalid_submission_rate_max": INVALID_SUBMISSION_RATE_MAX,
            "clean_replay_disagreement_count_max": CLEAN_REPLAY_DISAGREEMENT_COUNT_MAX,
        },
        "checks": checks,
        "fixed_denominator": denominator,
        "selected_cell_count": len(selected_rows),
        "attemptable_cell_count": attemptable,
        "attemptability_coverage": rate(attemptable, denominator),
        "model_output_invalid_submission_count": invalid,
        "model_output_invalid_submission_rate": rate(invalid, denominator),
        "clean_replay_disagreement_count": clean_replay_disagreement_count,
        "raw_input_gap_count": raw_input_gap_count,
        "category_counts": count_by(selected_rows, "stable_category"),
        "failure_owner_counts": count_by(selected_rows, "stable_failure_owner"),
        "failure_class_counts": count_by(selected_rows, "stable_failure_class"),
        "attemptability_channel_counts": count_by(selected_rows, "verifier_attempt_channel"),
        "model_call_made_counts": count_by(selected_rows, "historical_model_call_made"),
        "exact_cell_blockers": exact_cell_blockers(path_id, selected_rows),
        "selected_cells": [
            {
                "acut_id": row.get("acut_id"),
                "task_id": row.get("task_id"),
                "stable_category": row_category(row),
                "failure_owner": row.get("stable_failure_owner"),
                "failure_class": row.get("stable_failure_class"),
                "attemptability_channel": row.get("verifier_attempt_channel"),
                "source_label": row.get("source_label"),
                "run_id": row.get("run_id"),
                "assessment_evidence_role": row.get("assessment_evidence_role"),
                "supporting_record_count": row.get("supporting_record_count"),
                "supporting_category_counts": row.get("supporting_category_counts"),
                "historical_missing_raw_artifact_preserved": row.get("historical_missing_raw_artifact_preserved"),
                "historical_missing_run_id": row.get("historical_missing_run_id"),
            }
            for row in selected_rows
        ],
    }


def no_raw_unsafe_policy(matrix: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    matrix_guard = matrix.get("output_leakage_guard") if isinstance(matrix.get("output_leakage_guard"), Mapping) else {}
    violations: list[dict[str, Any]] = []
    for row in rows:
        shape = row.get("response_shape") if isinstance(row.get("response_shape"), Mapping) else {}
        if (
            row.get("content_recorded") is not False
            or shape.get("content_recorded") is not False
            or shape.get("contains_raw_url_like") is True
        ):
            violations.append(
                {
                    "source_label": row.get("source_label"),
                    "acut_id": row.get("acut_id"),
                    "task_id": row.get("task_id"),
                    "run_id": row.get("run_id"),
                    "content_recorded": row.get("content_recorded"),
                    "response_shape_content_recorded": shape.get("content_recorded"),
                    "contains_raw_url_like": shape.get("contains_raw_url_like"),
                }
            )
    passed = matrix_guard.get("contains_raw_unsafe_text") is False and not violations
    return {
        "status": "passed" if passed else "failed",
        "matrix_output_leakage_guard": matrix_guard,
        "row_policy_violation_count": len(violations),
        "row_policy_violations": violations,
        "policy": "assessment records metadata, hashes, counts, and paths only; raw provider text is not copied",
    }


def fixed_denominator_summary(matrix: Mapping[str, Any]) -> dict[str, Any]:
    scope = matrix.get("scope") if isinstance(matrix.get("scope"), Mapping) else {}
    fixed = scope.get("fixed_denominators") if isinstance(scope.get("fixed_denominators"), Mapping) else {}
    patch_gap = matrix.get("patch_or_files_gap_acquisition")
    patch_gap = patch_gap if isinstance(patch_gap, Mapping) else {}
    anchored = matrix.get("anchored_fixed_grid")
    anchored = anchored if isinstance(anchored, Mapping) else {}
    return {
        "m2_scoreability_fixed_grid_cells": scope.get("m2_fixed_denominator"),
        "patch_or_files_live_fixed_denominator": patch_gap.get("expected_live_fixed_denominator"),
        "patch_or_files_historical_live_input_records": patch_gap.get("historical_live_input_record_count"),
        "patch_or_files_historical_missing_raw_artifacts_preserved": patch_gap.get("historical_missing_raw_artifact_count"),
        "patch_or_files_acquisition_input_records": patch_gap.get("acquisition_input_record_count"),
        "patch_or_files_acquired_raw_input_records": patch_gap.get("acquired_raw_input_count"),
        "patch_or_files_remaining_raw_input_gaps_after_acquisition": patch_gap.get("remaining_missing_cell_count"),
        "patch_or_files_no_model_control_denominator": fixed.get("patch_or_files_v1_no_model"),
        "anchored_search_replace_expected_fixed_grid_cells": anchored.get("expected_fixed_denominator"),
        "anchored_search_replace_observed_unique_cells": anchored.get("observed_unique_cell_count"),
        "anchored_search_replace_input_records": anchored.get("input_record_count"),
        "anchored_search_replace_duplicate_input_records": anchored.get("duplicate_input_record_count"),
        "anchored_search_replace_remaining_missing_cells": anchored.get("remaining_missing_cell_count"),
    }


def coverage_gate_summary(fixed: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    checks = {
        "patch_or_files_raw_gap_closed": fixed.get("patch_or_files_remaining_raw_input_gaps_after_acquisition") == 0,
        "anchored_fixed_grid_complete": (
            fixed.get("anchored_search_replace_expected_fixed_grid_cells")
            == fixed.get("anchored_search_replace_observed_unique_cells")
            and fixed.get("anchored_search_replace_remaining_missing_cells") == 0
        ),
        "no_raw_unsafe_policy_passed": policy.get("status") == "passed",
    }
    return {
        "gate_status": "passed" if all(checks.values()) else "blocked",
        "checks": checks,
    }


def hard_blocker_summary(path_assessments: Mapping[str, Mapping[str, Any]], coverage_gate: Mapping[str, Any]) -> dict[str, Any]:
    live_paths = [
        item
        for key, item in path_assessments.items()
        if key in {"patch_or_files_v1_live_after_gap_closure", "anchored_search_replace_fixed_grid"}
    ]
    live_failures = [item for item in live_paths if item.get("gate_status") != "passed"]
    if coverage_gate.get("gate_status") == "passed" and live_failures:
        return {
            "status": "hard_blocked_for_m2_pass_or_predictivity_claims",
            "blocker_id": "live_model_output_scoreability_thresholds_not_met_after_fixed_grid_gap_closure",
            "code_addressable_blocker_identified": False,
            "next_code_addressable_blocker": None,
            "reason": (
                "Fixed denominator and raw-input acquisition gaps are closed, but live evidence remains below "
                "attemptability coverage thresholds and above model-output invalid-submission thresholds. "
                "The assessment found no single safe code-addressable next experiment that is directly supported "
                "by this evidence and would not require new approved model calls."
            ),
            "blocked_path_ids": [str(item.get("path_id")) for item in live_failures],
        }
    if coverage_gate.get("gate_status") != "passed":
        return {
            "status": "blocked_on_evidence_integrity_gate",
            "blocker_id": "fixed_grid_or_no_raw_policy_gate_not_closed",
            "code_addressable_blocker_identified": True,
            "next_code_addressable_blocker": "repair fixed-grid coverage, raw-input acquisition, or no-raw-unsafe reporting before scoreability assessment",
            "reason": "Evidence-integrity gates did not pass.",
            "blocked_path_ids": [],
        }
    return {
        "status": "no_hard_blocker_recorded",
        "blocker_id": None,
        "code_addressable_blocker_identified": False,
        "next_code_addressable_blocker": None,
        "reason": "Coverage and live scoreability gates passed in this assessment.",
        "blocked_path_ids": [],
    }


def attach_assessment_leakage_guard(payload: dict[str, Any]) -> None:
    findings = unsafe_text_findings(json.dumps(payload, sort_keys=True))
    payload["assessment_output_leakage_guard"] = {
        "contains_raw_unsafe_text": bool(findings["unsafe"]),
        "reason_counts": findings["reason_counts"],
    }
    final_findings = unsafe_text_findings(json.dumps(payload, sort_keys=True))
    payload["assessment_output_leakage_guard"] = {
        "contains_raw_unsafe_text": bool(final_findings["unsafe"]),
        "reason_counts": final_findings["reason_counts"],
    }
    if final_findings["unsafe"]:
        raise ToolError(
            "fixed-grid gate assessment output would contain raw unsafe text",
            reason_counts=final_findings["reason_counts"],
        )


def build_assessment(args: argparse.Namespace) -> dict[str, Any]:
    matrix = read_json(args.matrix)
    rows = rows_from_matrix(matrix)
    fixed = fixed_denominator_summary(matrix)
    policy = no_raw_unsafe_policy(matrix, rows)
    coverage_gate = coverage_gate_summary(fixed, policy)

    patch_rows = select_patch_or_files_effective_cells(matrix, rows)
    anchored_rows = select_anchored_effective_cells(matrix, rows)
    no_model_rows = select_no_model_control_cells(matrix, rows)

    patch_gap = matrix.get("patch_or_files_gap_acquisition")
    patch_gap = patch_gap if isinstance(patch_gap, Mapping) else {}
    anchored_grid = matrix.get("anchored_fixed_grid")
    anchored_grid = anchored_grid if isinstance(anchored_grid, Mapping) else {}

    path_assessments = {
        "patch_or_files_v1_live_after_gap_closure": assess_path(
            path_id="patch_or_files_v1_live_after_gap_closure",
            contract=PATCH_OR_FILES_CONTRACT,
            denominator=int(patch_gap.get("expected_live_fixed_denominator") or len(patch_rows)),
            selected_rows=patch_rows,
            clean_replay_disagreement_count=source_clean_replay_disagreements(matrix, "patch_or_files_v1_live"),
            raw_input_gap_count=int(patch_gap.get("remaining_missing_cell_count") or 0),
            role="live patch-or-files cells after replacing only the historical missing-raw cell with the acquired raw input row",
        ),
        "anchored_search_replace_fixed_grid": assess_path(
            path_id="anchored_search_replace_fixed_grid",
            contract=ANCHORED_CONTRACT,
            denominator=int(anchored_grid.get("expected_fixed_denominator") or len(anchored_rows)),
            selected_rows=anchored_rows,
            clean_replay_disagreement_count=None,
            raw_input_gap_count=int(anchored_grid.get("remaining_missing_cell_count") or 0),
            role="anchored-search-replace fixed grid using attemptable row per ACUT/task when present",
        ),
        "patch_or_files_v1_no_model_control": assess_path(
            path_id="patch_or_files_v1_no_model_control",
            contract=PATCH_OR_FILES_CONTRACT,
            denominator=int(fixed.get("patch_or_files_no_model_control_denominator") or len(no_model_rows)),
            selected_rows=no_model_rows,
            clean_replay_disagreement_count=source_clean_replay_disagreements(matrix, "patch_or_files_v1_no_model"),
            raw_input_gap_count=0,
            role="instrumentation control only; not evidence of live ACUT capability",
        ),
    }
    hard_blocker = hard_blocker_summary(path_assessments, coverage_gate)
    live_statuses = {
        str(item.get("gate_status"))
        for key, item in path_assessments.items()
        if key in {"patch_or_files_v1_live_after_gap_closure", "anchored_search_replace_fixed_grid"}
    }
    scoreability_status = (
        "passed"
        if coverage_gate.get("gate_status") == "passed" and live_statuses == {"passed"}
        else "blocked"
        if coverage_gate.get("gate_status") != "passed"
        else "failed"
    )
    inputs = matrix.get("inputs") if isinstance(matrix.get("inputs"), Mapping) else {}
    payload: dict[str, Any] = {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "matrix": args.matrix,
            "matrix_report": "experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap.md",
            "m2_summary": inputs.get("m2_summary"),
            "companion_reports": [
                "experiments/core_narrative/reports/2026-05-09_m2_scoreability_stabilization_report.md",
                "experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition.md",
                "experiments/core_narrative/reports/2026-05-10_m2_patch_or_files_gap_acquisition.md",
            ],
            "output": args.output,
            "report": args.report,
        },
        "method": {
            "model_calls_made_by_assessment": 0,
            "uses_existing_matrix_only": True,
            "cost_ledger_mutated_by_assessment": False,
            "raw_provider_text_copied": False,
            "historical_missing_raw_artifact_preserved": True,
            "gate_threshold_basis": "M2 scoreability stabilization thresholds from m2_scoreability_summary",
            "scoreability_boundary": (
                "attemptability/patch-artifact scoreability only; verifier pass/fail, task solving, "
                "ranking reversal, G-score predictivity, authorization, admission, and license outcomes are not measured"
            ),
        },
        "thresholds": {
            "attemptability_coverage_min": PATCH_READY_COVERAGE_MIN,
            "model_output_invalid_submission_rate_max": INVALID_SUBMISSION_RATE_MAX,
            "clean_replay_disagreement_count_max": CLEAN_REPLAY_DISAGREEMENT_COUNT_MAX,
        },
        "fixed_denominators": fixed,
        "coverage_and_policy_gate": coverage_gate,
        "scoreability_gate_status": scoreability_status,
        "path_assessments": path_assessments,
        "cost_model_call_accounting": {
            "assessment_generation": {
                "new_model_call_made_count": 0,
                "live_api_calls": False,
                "canonical_cost_ledger_mutated": False,
                "estimated_cost_usd": 0.0,
            },
            "input_matrix_package": matrix.get("cost_model_call_accounting"),
        },
        "failure_owner_class_accounting": {
            key: {
                "failure_owner_counts": item.get("failure_owner_counts"),
                "failure_class_counts": item.get("failure_class_counts"),
                "category_counts": item.get("category_counts"),
            }
            for key, item in path_assessments.items()
        },
        "attemptability_channels": {
            key: item.get("attemptability_channel_counts")
            for key, item in path_assessments.items()
        },
        "no_raw_unsafe_policy_status": policy,
        "hard_blocker_summary": hard_blocker,
        "claim_status": "m2_scoreability_gate_not_met_after_fixed_grid_gap_closure"
        if scoreability_status != "passed"
        else "m2_scoreability_gate_passed_on_fixed_grid",
        "claim_boundaries": {
            **PROHIBITED_CLAIMS,
            "new_model_calls_by_assessment": False,
            "verifier_or_task_success_measured_by_assessment": False,
            "fixed_grid_coverage_closed": coverage_gate.get("gate_status") == "passed",
        },
        "prohibited_claims": dict(PROHIBITED_CLAIMS),
    }
    attach_assessment_leakage_guard(payload)
    return payload


def pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def report_value(value: Any, *, none_label: str = "none") -> str:
    return none_label if value is None else str(value)


def write_report(payload: Mapping[str, Any], path: str) -> None:
    report_date_match = re.search(r"\d{4}-\d{2}-\d{2}", str(path))
    report_date = report_date_match.group(0) if report_date_match else str(payload.get("generated_at", ""))[:10]
    fixed = payload.get("fixed_denominators") if isinstance(payload.get("fixed_denominators"), Mapping) else {}
    coverage = payload.get("coverage_and_policy_gate") if isinstance(payload.get("coverage_and_policy_gate"), Mapping) else {}
    paths = payload.get("path_assessments") if isinstance(payload.get("path_assessments"), Mapping) else {}
    cost = payload.get("cost_model_call_accounting") if isinstance(payload.get("cost_model_call_accounting"), Mapping) else {}
    input_cost = cost.get("input_matrix_package") if isinstance(cost.get("input_matrix_package"), Mapping) else {}
    acquisition_cost = input_cost.get("acquisition") if isinstance(input_cost.get("acquisition"), Mapping) else {}
    policy = payload.get("no_raw_unsafe_policy_status") if isinstance(payload.get("no_raw_unsafe_policy_status"), Mapping) else {}
    hard = payload.get("hard_blocker_summary") if isinstance(payload.get("hard_blocker_summary"), Mapping) else {}

    lines = [
        "# M2 Fixed-Grid Gate Assessment",
        "",
        f"Date: {report_date}",
        "",
        "## Verdict",
        "",
        f"- Coverage/raw-input/no-raw policy gate: `{coverage.get('gate_status')}`.",
        f"- M2 scoreability gate status: `{payload.get('scoreability_gate_status')}`.",
        f"- Claim status: `{payload.get('claim_status')}`.",
        "- Assessment model calls: `0`; cost ledger mutated by assessment: `false`.",
        "- This is scoreability and artifact-channel accounting only.",
        "",
        "## Fixed Denominators",
        "",
        f"- Patch-or-files live fixed denominator: `{fixed.get('patch_or_files_live_fixed_denominator')}`.",
        f"- Patch-or-files historical missing raw artifacts preserved: `{fixed.get('patch_or_files_historical_missing_raw_artifacts_preserved')}`.",
        f"- Patch-or-files acquired raw inputs: `{fixed.get('patch_or_files_acquired_raw_input_records')}`; remaining raw-input gaps: `{fixed.get('patch_or_files_remaining_raw_input_gaps_after_acquisition')}`.",
        f"- Patch-or-files no-model control denominator: `{fixed.get('patch_or_files_no_model_control_denominator')}`.",
        f"- Anchored fixed-grid cells: `{fixed.get('anchored_search_replace_observed_unique_cells')}` observed of `{fixed.get('anchored_search_replace_expected_fixed_grid_cells')}` expected; input records: `{fixed.get('anchored_search_replace_input_records')}`.",
        "",
        "## Scoreability Gates",
        "",
        "| Path | Gate | Denom | Attemptable | Attemptability | Model invalid | Invalid rate | Clean replay disagreements |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in (
        "patch_or_files_v1_live_after_gap_closure",
        "anchored_search_replace_fixed_grid",
        "patch_or_files_v1_no_model_control",
    ):
        item = paths.get(key) if isinstance(paths.get(key), Mapping) else {}
        lines.append(
            f"| `{key}` | `{item.get('gate_status')}` | {item.get('fixed_denominator')} | "
            f"{item.get('attemptable_cell_count')} | {pct(item.get('attemptability_coverage'))} | "
            f"{item.get('model_output_invalid_submission_count')} | {pct(item.get('model_output_invalid_submission_rate'))} | "
            f"{report_value(item.get('clean_replay_disagreement_count'), none_label='not_measured')} |"
        )
    lines.extend(
        [
            "",
            "## Failure And Channels",
            "",
        ]
    )
    for key, item in paths.items():
        if not isinstance(item, Mapping):
            continue
        lines.extend(
            [
                f"- `{key}` owner counts: `{item.get('failure_owner_counts')}`.",
                f"- `{key}` class counts: `{item.get('failure_class_counts')}`.",
                f"- `{key}` attemptability channels: `{item.get('attemptability_channel_counts')}`.",
            ]
        )
    lines.extend(["", "## Exact ACUT/Task Blockers", ""])
    for key in (
        "patch_or_files_v1_live_after_gap_closure",
        "anchored_search_replace_fixed_grid",
    ):
        item = paths.get(key) if isinstance(paths.get(key), Mapping) else {}
        blockers = item.get("exact_cell_blockers") if isinstance(item.get("exact_cell_blockers"), list) else []
        lines.append(f"### `{key}`")
        if not blockers:
            lines.append("- None.")
            continue
        for blocker in blockers:
            if not isinstance(blocker, Mapping):
                continue
            lines.append(
                f"- `{blocker.get('acut_id')}` / `{blocker.get('task_id')}`: "
                f"`{blocker.get('stable_category')}`, owner `{blocker.get('failure_owner')}`, "
                f"class `{report_value(blocker.get('failure_class'))}`, "
                f"channel `{blocker.get('attemptability_channel')}`."
            )
    lines.extend(
        [
            "",
            "## Cost And Model Calls",
            "",
            "- Assessment generation: `0` new model calls, `0.0` USD estimated cost.",
            f"- Input acquisition rows: `{acquisition_cost.get('input_record_count')}`; acquisition model calls: `{acquisition_cost.get('new_model_call_made_count')}`.",
            f"- Acquisition provider usage observed sum: `{acquisition_cost.get('provider_usage_cost_usd_observed_sum')}` USD.",
            f"- Acquisition ledger estimated sum: `{acquisition_cost.get('ledger_estimated_cost_usd_sum')}` USD.",
            "",
            "## No-Raw-Unsafe Policy",
            "",
            f"- Status: `{policy.get('status')}`.",
            f"- Matrix leakage guard: `{policy.get('matrix_output_leakage_guard')}`.",
            f"- Row policy violations: `{policy.get('row_policy_violation_count')}`.",
            f"- Assessment leakage guard: `{payload.get('assessment_output_leakage_guard')}`.",
            "",
            "## Hard Blocker Summary",
            "",
            f"- Status: `{hard.get('status')}`.",
            f"- Blocker: `{hard.get('blocker_id')}`.",
            f"- Code-addressable blocker identified: `{hard.get('code_addressable_blocker_identified')}`.",
            f"- Next code-addressable blocker: `{hard.get('next_code_addressable_blocker')}`.",
            f"- Reason: {hard.get('reason')}",
            "",
            "## Reproduction",
            "",
            "```bash",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_fixed_grid_gate_assessment.py \\",
            f"  --matrix {payload.get('inputs', {}).get('matrix')} \\",
            f"  --output {payload.get('inputs', {}).get('output')} \\",
            f"  --report {payload.get('inputs', {}).get('report')}",
            "```",
            "",
            "## Claim Boundaries",
            "",
            "This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_assessment(args)
        emit_json(payload, args.output)
        write_report(payload, args.report)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
