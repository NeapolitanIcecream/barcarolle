#!/usr/bin/env python3
"""Summarize M2 scoreability-first evidence across submission paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now


TOOL = "m2_scoreability_summary"
PATCH_READY_STATUSES = {"passed", "failed", "timeout"}
INVALID_STATUS = "invalid_submission"
MISSING_STATUS = "missing"
BLOCKED_STATUS = "blocked"

PATCH_READY_THRESHOLD = 0.70
INVALID_RATE_THRESHOLD = 0.25
CLEAN_REPLAY_DISAGREEMENT_THRESHOLD = 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--acuts", nargs="+", required=True)
    parser.add_argument(
        "--evidence",
        action="append",
        nargs=4,
        metavar=("PATH_ID", "EXPECTED_CONTRACT", "KIND", "PATH"),
        required=True,
        help="Evidence set. KIND is batch or blocker.",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args(list(argv))


def read_json(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("evidence JSON root must be an object", path=path)
    return data


def bool_label(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def count_by(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def default_failure_owner(status: str) -> str:
    if status == "passed":
        return "none"
    if status == INVALID_STATUS:
        return "model_output"
    if status in {"failed", "timeout"}:
        return "candidate_patch"
    if status == MISSING_STATUS:
        return "missing"
    if status == BLOCKED_STATUS:
        return "blocked"
    if status == "infra_failed":
        return "infrastructure"
    return "unknown"


def first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def contract_markers(
    item: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner_result: Mapping[str, Any],
) -> list[str]:
    markers: list[str] = []
    for source in (item, metadata, runner_result):
        for key in ("submission_contract", "output_contract"):
            value = source.get(key)
            if isinstance(value, str) and value:
                markers.append(value)
    return markers


def contract_matches(
    item: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner_result: Mapping[str, Any],
    expected_contract: str,
) -> tuple[bool, list[str]]:
    markers = contract_markers(item, metadata, runner_result)
    if not markers:
        return False, markers
    return all(marker == expected_contract for marker in markers), markers


def model_call_made_from(
    item: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner_result: Mapping[str, Any],
) -> bool | None:
    for source in (metadata, runner_result, item):
        value = source.get("model_call_made")
        if value is True or value is False:
            return bool(value)
    return None


def clean_replay_attempted(metadata: Mapping[str, Any]) -> bool:
    readiness = metadata.get("patch_readiness") if isinstance(metadata.get("patch_readiness"), Mapping) else {}
    replay = metadata.get("clean_patch_replay") if isinstance(metadata.get("clean_patch_replay"), Mapping) else {}
    return bool(readiness.get("clean_replay_attempted") or replay.get("attempted"))


def verifier_exit_code(normalized: Mapping[str, Any]) -> int | None:
    verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
    value = verification.get("exit_code")
    return int(value) if isinstance(value, int) else None


def record_from_batch_item(
    *,
    path_id: str,
    expected_contract: str,
    item: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = item.get("normalized") if isinstance(item.get("normalized"), Mapping) else {}
    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
    runner_result = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
    status = str(item.get("status") or normalized.get("status") or "unknown")
    readiness = metadata.get("patch_readiness") if isinstance(metadata.get("patch_readiness"), Mapping) else {}
    patch_ready = (
        item.get("patch_ready") is True
        or readiness.get("verifier_ready_patch_available") is True
        or status in PATCH_READY_STATUSES
    )
    replay_attempted = clean_replay_attempted(metadata)
    replay_success = replay_attempted and status in PATCH_READY_STATUSES
    clean_replay_disagreement = bool(patch_ready and not replay_success)
    failure_class = first_string(
        metadata.get("failure_class"),
        runner_result.get("failure_class"),
        (runner_result.get("details") or {}).get("failure_class") if isinstance(runner_result.get("details"), Mapping) else None,
    )
    failure_owner = first_string(metadata.get("failure_owner")) or default_failure_owner(status)
    if status == INVALID_STATUS and failure_owner == "infrastructure":
        failure_owner = "model_output"
    return {
        "path_id": path_id,
        "contract": expected_contract,
        "acut_id": item.get("acut_id"),
        "task_id": item.get("task_id"),
        "run_id": item.get("run_id"),
        "status": status,
        "failure_owner": failure_owner,
        "failure_class": failure_class,
        "patch_ready": patch_ready,
        "clean_replay_attempted": replay_attempted,
        "clean_replay_success": replay_success,
        "clean_replay_disagreement": clean_replay_disagreement,
        "verifier_exit_code": verifier_exit_code(normalized),
        "model_call_made": model_call_made_from(item, metadata, runner_result),
        "normalized_result": item.get("normalized_result"),
        "prompt_snapshot": metadata.get("prompt_snapshot") or runner_result.get("prompt_snapshot"),
        "raw_response_artifact": metadata.get("raw_response_artifact") or runner_result.get("raw_response_artifact"),
    }


def missing_record(*, path_id: str, contract: str, acut_id: str, task_id: str) -> dict[str, Any]:
    return {
        "path_id": path_id,
        "contract": contract,
        "acut_id": acut_id,
        "task_id": task_id,
        "run_id": None,
        "status": MISSING_STATUS,
        "failure_owner": "missing",
        "failure_class": None,
        "patch_ready": False,
        "clean_replay_attempted": False,
        "clean_replay_success": False,
        "clean_replay_disagreement": False,
        "verifier_exit_code": None,
        "model_call_made": None,
        "normalized_result": None,
        "prompt_snapshot": None,
        "raw_response_artifact": None,
    }


def blocked_record(
    *,
    path_id: str,
    contract: str,
    acut_id: str,
    task_id: str,
    blocker: Mapping[str, Any],
) -> dict[str, Any]:
    blockers = blocker.get("blockers") if isinstance(blocker.get("blockers"), list) else []
    failure_class = first_string(*(item for item in blockers if isinstance(item, str))) or first_string(blocker.get("reason"))
    model_call = blocker.get("model_call_made")
    return {
        "path_id": path_id,
        "contract": contract,
        "acut_id": acut_id,
        "task_id": task_id,
        "run_id": None,
        "status": BLOCKED_STATUS,
        "failure_owner": "blocked",
        "failure_class": failure_class,
        "patch_ready": False,
        "clean_replay_attempted": False,
        "clean_replay_success": False,
        "clean_replay_disagreement": False,
        "verifier_exit_code": None,
        "model_call_made": bool(model_call) if model_call in (True, False) else False,
        "normalized_result": None,
        "prompt_snapshot": None,
        "raw_response_artifact": None,
    }


def batch_records(
    *,
    path_id: str,
    expected_contract: str,
    batch: Mapping[str, Any],
    tasks: Sequence[str],
    acuts: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    wanted = {(acut_id, task_id) for acut_id in acuts for task_id in tasks}
    seen: set[tuple[str, str]] = set()
    records: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for index, item in enumerate(batch.get("results", [])):
        if not isinstance(item, Mapping):
            continue
        acut_id = item.get("acut_id")
        task_id = item.get("task_id")
        if not isinstance(acut_id, str) or not isinstance(task_id, str):
            excluded.append({"index": index, "reason": "missing_cell_identity"})
            continue
        if (acut_id, task_id) not in wanted:
            continue
        normalized = item.get("normalized") if isinstance(item.get("normalized"), Mapping) else {}
        metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
        runner_result = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
        matches, markers = contract_matches(item, metadata, runner_result, expected_contract)
        if not matches:
            excluded.append(
                {
                    "index": index,
                    "reason": "wrong_or_missing_contract",
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "contract_markers": markers,
                    "expected_contract": expected_contract,
                }
            )
            continue
        cell = (acut_id, task_id)
        if cell in seen:
            excluded.append({"index": index, "reason": "duplicate_cell", "acut_id": acut_id, "task_id": task_id})
            continue
        seen.add(cell)
        records.append(record_from_batch_item(path_id=path_id, expected_contract=expected_contract, item=item))

    for acut_id in acuts:
        for task_id in tasks:
            if (acut_id, task_id) not in seen:
                records.append(missing_record(path_id=path_id, contract=expected_contract, acut_id=acut_id, task_id=task_id))
    return records, excluded


def blocker_records(
    *,
    path_id: str,
    expected_contract: str,
    blocker: Mapping[str, Any],
    tasks: Sequence[str],
    acuts: Sequence[str],
) -> list[dict[str, Any]]:
    return [
        blocked_record(path_id=path_id, contract=expected_contract, acut_id=acut_id, task_id=task_id, blocker=blocker)
        for acut_id in acuts
        for task_id in tasks
    ]


def gate_for_path(summary: Mapping[str, Any], *, has_blocker: bool) -> dict[str, Any]:
    patch_ready = summary.get("patch_ready_coverage")
    invalid = summary.get("invalid_submission_rate")
    missing = int(summary.get("missing_cell_count") or 0)
    disagreements = int(summary.get("clean_replay_disagreement_count") or 0)
    patch_ready_pass = isinstance(patch_ready, (int, float)) and float(patch_ready) >= PATCH_READY_THRESHOLD
    invalid_pass = isinstance(invalid, (int, float)) and float(invalid) <= INVALID_RATE_THRESHOLD
    disagreement_pass = disagreements <= CLEAN_REPLAY_DISAGREEMENT_THRESHOLD
    if has_blocker:
        status = "blocked"
    elif missing:
        status = "incomplete"
    elif patch_ready_pass and invalid_pass and disagreement_pass:
        status = "passed"
    else:
        status = "failed"
    return {
        "status": status,
        "thresholds": {
            "patch_ready_coverage_min": PATCH_READY_THRESHOLD,
            "invalid_submission_rate_max": INVALID_RATE_THRESHOLD,
            "clean_replay_disagreement_count_max": CLEAN_REPLAY_DISAGREEMENT_THRESHOLD,
        },
        "checks": {
            "patch_ready_coverage": patch_ready_pass,
            "invalid_submission_rate": invalid_pass,
            "clean_replay_disagreement_count": disagreement_pass,
            "complete_fixed_denominator": missing == 0,
        },
    }


def summarize_path(records: Sequence[Mapping[str, Any]], *, excluded_rows: Sequence[Mapping[str, Any]], has_blocker: bool) -> dict[str, Any]:
    total = len(records)
    invalid = sum(1 for record in records if record.get("status") == INVALID_STATUS)
    patch_ready = sum(1 for record in records if record.get("patch_ready") is True)
    replay_attempted = sum(1 for record in records if record.get("clean_replay_attempted") is True)
    replay_success = sum(1 for record in records if record.get("clean_replay_success") is True)
    disagreements = [
        {"acut_id": record.get("acut_id"), "task_id": record.get("task_id"), "status": record.get("status")}
        for record in records
        if record.get("clean_replay_disagreement") is True
    ]
    missing = [
        {"acut_id": record.get("acut_id"), "task_id": record.get("task_id")}
        for record in records
        if record.get("status") == MISSING_STATUS
    ]
    blocked = [
        {"acut_id": record.get("acut_id"), "task_id": record.get("task_id"), "failure_class": record.get("failure_class")}
        for record in records
        if record.get("status") == BLOCKED_STATUS
    ]
    model_call_counts: dict[str, int] = {"false": 0, "true": 0, "unknown": 0}
    for record in records:
        model_call_counts[bool_label(record.get("model_call_made"))] += 1
    summary = {
        "total": total,
        "status_counts": count_by(records, "status"),
        "failure_owner_counts": count_by(records, "failure_owner"),
        "failure_class_counts": count_by(records, "failure_class"),
        "invalid_submission_count": invalid,
        "invalid_submission_rate": rate(invalid, total),
        "patch_ready_count": patch_ready,
        "patch_ready_coverage": rate(patch_ready, total),
        "clean_replay_attempted_count": replay_attempted,
        "clean_replay_success_count": replay_success,
        "clean_replay_success_rate": rate(replay_success, total),
        "clean_replay_disagreement_count": len(disagreements),
        "clean_replay_disagreement_cells": disagreements,
        "missing_cell_count": len(missing),
        "missing_cells": missing,
        "blocked_cell_count": len(blocked),
        "blocked_cells": blocked,
        "model_call_made_counts": model_call_counts,
        "excluded_row_count": len(excluded_rows),
        "excluded_rows": list(excluded_rows),
    }
    summary["gate"] = gate_for_path(summary, has_blocker=has_blocker)
    return summary


def claim_status(path_summaries: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = {
        str(summary.get("gate", {}).get("status"))
        for summary in path_summaries.values()
        if isinstance(summary.get("gate"), Mapping)
    }
    if "blocked" in statuses:
        return "blocked"
    if statuses and all(status == "passed" for status in statuses):
        return "scoreability_gate_passed"
    return "scoreability_gate_not_met"


def claim_wording(status: str) -> str:
    if status == "blocked":
        prefix = "M2 scoreability evidence is blocked for at least one requested path."
    elif status == "scoreability_gate_passed":
        prefix = "M2 scoreability readiness gate passed on the fixed 2 ACUT x 3 RWork smoke."
    else:
        prefix = "M2 scoreability readiness gate did not pass on the fixed 2 ACUT x 3 RWork smoke."
    return (
        f"{prefix} This is measurement-readiness evidence only: it makes no capability uplift claim, "
        "no task-solving improvement claim, and no ranking reversal claim."
    )


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    path_summaries: dict[str, dict[str, Any]] = {}
    records_by_path: dict[str, list[dict[str, Any]]] = {}
    evidence_inputs: dict[str, dict[str, Any]] = {}
    for raw_path_id, expected_contract, kind, path in args.evidence:
        if raw_path_id in path_summaries:
            raise ToolError("duplicate evidence path id", path_id=raw_path_id)
        if kind not in {"batch", "blocker"}:
            raise ToolError("unsupported evidence kind", path_id=raw_path_id, kind=kind)
        data = read_json(path)
        if kind == "batch":
            records, excluded = batch_records(
                path_id=raw_path_id,
                expected_contract=expected_contract,
                batch=data,
                tasks=args.tasks,
                acuts=args.acuts,
            )
            has_blocker = False
        else:
            records = blocker_records(
                path_id=raw_path_id,
                expected_contract=expected_contract,
                blocker=data,
                tasks=args.tasks,
                acuts=args.acuts,
            )
            excluded = []
            has_blocker = True
        records_by_path[raw_path_id] = records
        path_summaries[raw_path_id] = summarize_path(records, excluded_rows=excluded, has_blocker=has_blocker)
        evidence_inputs[raw_path_id] = {
            "contract": expected_contract,
            "kind": kind,
            "path": path,
        }
    status = claim_status(path_summaries)
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "research_question": (
            "Whether the selected RWork smoke is scoreable across multiple submission paths "
            "before making G/R/W predictivity claims."
        ),
        "tasks": list(args.tasks),
        "acuts": list(args.acuts),
        "fixed_denominator": len(args.tasks) * len(args.acuts),
        "success_criteria": {
            "patch_ready_coverage_min": PATCH_READY_THRESHOLD,
            "invalid_submission_rate_max": INVALID_RATE_THRESHOLD,
            "clean_replay_disagreement_count_max": CLEAN_REPLAY_DISAGREEMENT_THRESHOLD,
            "claim_boundary": "scoreability/measurement readiness only; no capability uplift or ranking reversal",
        },
        "evidence_inputs": evidence_inputs,
        "paths": path_summaries,
        "records": records_by_path,
        "claim_status": status,
        "claim_wording": claim_wording(status),
        "prohibited_claims": {
            "capability_uplift": False,
            "task_solving_improvement": False,
            "ranking_reversal": False,
            "g_score_predictivity": False,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_summary(args)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
