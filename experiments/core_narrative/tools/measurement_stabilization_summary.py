#!/usr/bin/env python3
"""Summarize M1 submission-contract measurement-stabilization evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import emit_json, fail, iso_now


TOOL = "measurement_stabilization_summary"
ANCHOR_CONTRACT = "anchored-search-replace-json-v3"
STRUCTURED_CONTRACT = "structured-files-json-v1"
PATCH_READY_STATUSES = {"passed", "failed", "timeout"}
CANONICAL_SCOREABLE_STATUSES = PATCH_READY_STATUSES | {"invalid_submission"}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchored-baseline", required=True, help="Existing canonical matrix JSON for anchored baseline.")
    parser.add_argument("--structured-batch", help="Batch output JSON from a structured-files-json-v1 run.")
    parser.add_argument("--blocker", help="Optional blocker JSON when live/no-model execution could not run.")
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--acuts", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(list(argv))


def read_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def failure_class_from_label(label: object) -> str | None:
    if not isinstance(label, str) or ":" not in label:
        return None
    return label.split(":", 1)[1] or None


def failure_owner(status: str, metadata: Mapping[str, Any] | None = None) -> str:
    if metadata is not None:
        owner = metadata.get("failure_owner")
        if isinstance(owner, str) and owner:
            return owner
    if status == "passed":
        return "none"
    if status == "invalid_submission":
        return "model_output"
    if status in {"failed", "timeout"}:
        return "candidate_patch"
    if status == "missing":
        return "missing"
    return "infrastructure"


def matrix_records(matrix: Mapping[str, Any], *, tasks: Sequence[str], acuts: Sequence[str]) -> list[dict[str, Any]]:
    cells = matrix.get("cells") if isinstance(matrix.get("cells"), dict) else {}
    records: list[dict[str, Any]] = []
    for acut_id in acuts:
        for task_id in tasks:
            cell = cells.get(f"{acut_id}::{task_id}")
            latest = cell.get("canonical_latest") if isinstance(cell, dict) else None
            if not isinstance(latest, dict):
                records.append(
                    {
                        "contract": ANCHOR_CONTRACT,
                        "acut_id": acut_id,
                        "task_id": task_id,
                        "status": "missing",
                        "failure_class": None,
                        "failure_owner": "missing",
                        "patch_ready": False,
                        "model_call_made": None,
                        "path": None,
                    }
                )
                continue
            status = str(latest.get("status"))
            records.append(
                {
                    "contract": ANCHOR_CONTRACT,
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "status": status,
                    "failure_class": failure_class_from_label(latest.get("failure_label")),
                    "failure_owner": failure_owner(status),
                    "patch_ready": status in PATCH_READY_STATUSES,
                    "model_call_made": True,
                    "path": latest.get("path"),
                    "run_id": latest.get("run_id"),
                    "failure_label": latest.get("failure_label"),
                }
            )
    return records


def structured_contract_from_batch_item(item: Mapping[str, Any], metadata: Mapping[str, Any]) -> str | None:
    contracts: list[str] = []
    for source in (item, metadata):
        contract = source.get("submission_contract")
        if isinstance(contract, str) and contract:
            contracts.append(contract)
    if not contracts:
        return None
    if any(contract != STRUCTURED_CONTRACT for contract in contracts):
        return None
    return STRUCTURED_CONTRACT


def batch_records(batch: Mapping[str, Any] | None, *, tasks: Sequence[str], acuts: Sequence[str]) -> list[dict[str, Any]]:
    if not isinstance(batch, dict):
        return []
    wanted = {(acut_id, task_id) for acut_id in acuts for task_id in tasks}
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in batch.get("results", []):
        if not isinstance(item, dict):
            continue
        acut_id = item.get("acut_id")
        task_id = item.get("task_id")
        if (acut_id, task_id) not in wanted:
            continue
        if not isinstance(acut_id, str) or not isinstance(task_id, str):
            continue
        normalized = item.get("normalized") if isinstance(item.get("normalized"), dict) else {}
        metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
        submission_contract = structured_contract_from_batch_item(item, metadata)
        if submission_contract != STRUCTURED_CONTRACT:
            continue
        seen.add((acut_id, task_id))
        runner_result = item.get("runner_result") if isinstance(item.get("runner_result"), dict) else {}
        patch_artifact = runner_result.get("patch_artifact") if isinstance(runner_result.get("patch_artifact"), dict) else {}
        status = str(item.get("status") or normalized.get("status") or "unknown")
        failure_class = metadata.get("failure_class")
        owner = failure_owner(status, metadata)
        if patch_artifact.get("unsafe_content_detected") is True:
            status = "invalid_submission"
            failure_class = "unsafe_generated_text"
            owner = "model_output"
        readiness = metadata.get("patch_readiness") if isinstance(metadata.get("patch_readiness"), dict) else {}
        patch_ready = bool(readiness.get("verifier_ready_patch_available")) or status in PATCH_READY_STATUSES
        records.append(
            {
                "contract": submission_contract,
                "acut_id": acut_id,
                "task_id": task_id,
                "status": status,
                "failure_class": failure_class,
                "failure_owner": owner,
                "patch_ready": patch_ready,
                "model_call_made": metadata.get("model_call_made"),
                "path": item.get("normalized_result"),
                "run_id": item.get("run_id"),
                "prompt_snapshot": metadata.get("prompt_snapshot"),
                "raw_response_artifact": metadata.get("raw_response_artifact"),
            }
        )
    for acut_id in acuts:
        for task_id in tasks:
            if (acut_id, task_id) in seen:
                continue
            records.append(
                {
                    "contract": STRUCTURED_CONTRACT,
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "status": "missing",
                    "failure_class": None,
                    "failure_owner": "missing",
                    "patch_ready": False,
                    "model_call_made": None,
                    "path": None,
                    "run_id": None,
                    "prompt_snapshot": None,
                    "raw_response_artifact": None,
                }
            )
    return records


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


def summarize_contract(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(records)
    invalid = sum(1 for record in records if record.get("status") == "invalid_submission")
    patch_ready = sum(1 for record in records if record.get("patch_ready") is True)
    canonical_scoreable = sum(1 for record in records if record.get("status") in CANONICAL_SCOREABLE_STATUSES)
    model_calls = sum(1 for record in records if record.get("model_call_made") is True)
    return {
        "total": total,
        "status_counts": count_by(records, "status"),
        "failure_owner_counts": count_by(records, "failure_owner"),
        "failure_class_counts": count_by(records, "failure_class"),
        "invalid_submission_count": invalid,
        "invalid_submission_rate": rate(invalid, total),
        "patch_ready_count": patch_ready,
        "patch_ready_coverage": rate(patch_ready, total),
        "canonical_scoreable_count": canonical_scoreable,
        "canonical_scoreable_coverage": rate(canonical_scoreable, total),
        "model_call_made_count": model_calls,
    }


def claim_status(*, anchored: Mapping[str, Any], structured: Mapping[str, Any], blocker: Mapping[str, Any] | None) -> str:
    if blocker:
        return "blocked"
    if structured.get("total", 0) == 0:
        return "blocked"
    structured_status_counts = structured.get("status_counts") if isinstance(structured.get("status_counts"), Mapping) else {}
    if structured_status_counts.get("missing", 0):
        return "not yet testable"
    anchored_invalid = anchored.get("invalid_submission_rate")
    structured_invalid = structured.get("invalid_submission_rate")
    anchored_ready = anchored.get("patch_ready_coverage")
    structured_ready = structured.get("patch_ready_coverage")
    if None in {anchored_invalid, structured_invalid, anchored_ready, structured_ready}:
        return "not yet testable"
    invalid_delta = float(anchored_invalid) - float(structured_invalid)
    ready_delta = float(structured_ready) - float(anchored_ready)
    if invalid_delta >= 0.25 and ready_delta >= 0.25:
        return "supported"
    if invalid_delta <= 0 and ready_delta <= 0:
        return "weakened"
    return "not yet testable"


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    anchored_matrix = read_json(args.anchored_baseline) or {}
    structured_batch = read_json(args.structured_batch)
    blocker = read_json(args.blocker)
    anchored_records = matrix_records(anchored_matrix, tasks=args.tasks, acuts=args.acuts)
    structured_records = batch_records(structured_batch, tasks=args.tasks, acuts=args.acuts)
    anchored_summary = summarize_contract(anchored_records)
    structured_summary = summarize_contract(structured_records)
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "research_question": (
            "Whether RWork invalid_submission-heavy evidence is primarily caused by anchored "
            "search/replace output fragility, and whether structured file-level submission "
            "improves patch-ready coverage enough for later G/R/W predictivity experiments."
        ),
        "success_criteria": {
            "minimum_smoke_shape": "2 ACUTs x 3 RWork tasks for structured-files-json-v1, or structured blocker",
            "supported_threshold": (
                "structured invalid_submission rate at least 25 percentage points lower than anchored baseline "
                "and patch-ready coverage at least 25 percentage points higher on the selected cells"
            ),
        },
        "tasks": list(args.tasks),
        "acuts": list(args.acuts),
        "contracts": {
            ANCHOR_CONTRACT: anchored_summary,
            STRUCTURED_CONTRACT: structured_summary,
        },
        "effect": {
            "invalid_submission_rate_delta_structured_minus_anchored": None
            if anchored_summary["invalid_submission_rate"] is None or structured_summary["invalid_submission_rate"] is None
            else round(float(structured_summary["invalid_submission_rate"]) - float(anchored_summary["invalid_submission_rate"]), 6),
            "patch_ready_coverage_delta_structured_minus_anchored": None
            if anchored_summary["patch_ready_coverage"] is None or structured_summary["patch_ready_coverage"] is None
            else round(float(structured_summary["patch_ready_coverage"]) - float(anchored_summary["patch_ready_coverage"]), 6),
        },
        "claim_status": claim_status(anchored=anchored_summary, structured=structured_summary, blocker=blocker),
        "blocker": blocker,
        "record_paths": {
            "anchored_baseline": args.anchored_baseline,
            "structured_batch": args.structured_batch,
            "blocker": args.blocker,
        },
        "records": {
            ANCHOR_CONTRACT: anchored_records,
            STRUCTURED_CONTRACT: structured_records,
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
