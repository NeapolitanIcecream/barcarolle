#!/usr/bin/env python3
"""Summarize canonical Codex NFL Click RBench/RWork evidence matrices."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import codex_nfl_experiment_runner as batch
from _common import ToolError, emit_json, fail, iso_now, load_manifest


TOOL = "codex_nfl_canonical_matrix"
CORE_ACUTS = [
    "cheap-generic-swe",
    "cheap-click-specialist",
    "frontier-generic-swe",
    "frontier-click-specialist",
]
SCOREABLE_STATUSES = {"passed", "failed", "timeout", "invalid_submission"}
PRIMARY_METADATA_FIELDS = [
    "runner_id",
    "direct_runner_id",
    "acut_manifest_sha256",
    "task_manifest_sha256",
    "verifier_digest_sha256",
    "prompt_snapshot_sha256",
    "context_pack_digest",
    "raw_response_artifact",
    "direct_runner_cost_accounting",
    "clean_patch_replay",
]
FUTURE_METADATA_FIELDS = [
    *PRIMARY_METADATA_FIELDS,
    "direct_runner_cost_ledger_append",
    "direct_runner_budget_gate",
]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=sorted(batch.TASK_SPLIT_MANIFESTS), required=True)
    parser.add_argument("--task-split-manifest")
    parser.add_argument("--normalized-root", default=str(batch.NORMALIZED_ROOT))
    parser.add_argument("--output", required=True)
    return parser.parse_args(list(argv))


def load_tasks(split: str, manifest_override: str | None) -> list[str]:
    manifest_path = Path(manifest_override) if manifest_override else batch.task_split_manifest_path(split)
    manifest = load_manifest(manifest_path)
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ToolError("task split manifest has no tasks list", manifest_path=str(manifest_path))
    task_ids = [str(task["task_id"]) for task in tasks if isinstance(task, Mapping) and isinstance(task.get("task_id"), str)]
    if not task_ids:
        raise ToolError("task split manifest has no task ids", manifest_path=str(manifest_path))
    return task_ids


def candidate_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def is_live_batch_candidate(payload: Mapping[str, Any]) -> bool:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if metadata.get("runner_id") != batch.RUNNER_ID and metadata.get("batch_tool") != batch.TOOL:
        return False
    if metadata.get("direct_runner_status") == "dry_run_completed":
        return False
    return metadata.get("model_call_made") is True


def failure_label(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    failure_class = metadata.get("failure_class")
    status = str(payload.get("status"))
    if isinstance(failure_class, str) and failure_class:
        return f"{status}:{failure_class}"
    return status


def metadata_coverage(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    present_primary = {field: field in metadata for field in PRIMARY_METADATA_FIELDS}
    present_future = {field: field in metadata for field in FUTURE_METADATA_FIELDS}
    return {
        "primary_fields_present": present_primary,
        "future_fields_present": present_future,
        "missing_primary_fields": [field for field, present in present_primary.items() if not present],
        "missing_future_fields": [field for field, present in present_future.items() if not present],
    }


def summarize_payload(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "run_id": payload.get("run_id"),
        "acut_id": payload.get("acut_id"),
        "task_id": payload.get("task_id"),
        "split": str(payload.get("split", "")).lower(),
        "attempt": payload.get("attempt"),
        "status": payload.get("status"),
        "scoreable": payload.get("status") in SCOREABLE_STATUSES,
        "failure_label": failure_label(payload),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "mtime": file_mtime(path),
        "metadata_coverage": metadata_coverage(payload),
    }


def evidence_timestamp_key(value: Any) -> tuple[int, float | str]:
    if not isinstance(value, str) or not value:
        return (0, "")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return (0, value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return (1, parsed.timestamp())


def evidence_order_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        bool(record.get("scoreable")),
        evidence_timestamp_key(record.get("finished_at")),
        evidence_timestamp_key(record.get("started_at")),
        str(record.get("run_id") or ""),
        str(record.get("path") or ""),
    )


def better_attempt_record(current: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if current is None:
        return candidate
    current_scoreable = bool(current.get("scoreable"))
    candidate_scoreable = bool(candidate.get("scoreable"))
    if candidate_scoreable != current_scoreable:
        return candidate if candidate_scoreable else current
    return candidate if evidence_order_key(candidate) > evidence_order_key(current) else current


def canonical_latest(records: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    scoreable = [record for record in records if record.get("scoreable")]
    source = scoreable if scoreable else list(records)
    return sorted(source, key=lambda item: (int(item.get("attempt") or 0), evidence_order_key(item)))[-1]


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, float | None]:
    if total <= 0:
        return {"lower": None, "upper": None}
    phat = successes / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total) / denom
    return {"lower": max(0.0, center - margin), "upper": min(1.0, center + margin)}


def build_matrix(split: str, task_ids: Sequence[str], root: Path) -> dict[str, Any]:
    records_by_cell: dict[tuple[str, str], list[dict[str, Any]]] = {(acut, task): [] for acut in CORE_ACUTS for task in task_ids}
    ignored_count = 0
    for path in candidate_files(root):
        payload = read_json(path)
        if payload is None:
            ignored_count += 1
            continue
        acut = payload.get("acut_id")
        task = payload.get("task_id")
        if acut not in CORE_ACUTS or task not in task_ids or str(payload.get("split", "")).lower() != split:
            continue
        if not is_live_batch_candidate(payload):
            ignored_count += 1
            continue
        records_by_cell[(str(acut), str(task))].append(summarize_payload(path, payload))

    cells: dict[str, dict[str, Any]] = {}
    attempts_seen: set[int] = set()
    missing_attempt2: list[dict[str, str]] = []
    missing_canonical: list[dict[str, str]] = []
    status_counts: dict[str, int] = {}
    failure_label_counts: dict[str, int] = {}
    metadata_missing_counts: dict[str, int] = {}

    for acut in CORE_ACUTS:
        for task in task_ids:
            records = sorted(records_by_cell[(acut, task)], key=lambda item: (int(item.get("attempt") or 0), evidence_order_key(item)))
            by_attempt: dict[int, dict[str, Any]] = {}
            for record in records:
                attempt = record.get("attempt")
                if not isinstance(attempt, int):
                    continue
                attempts_seen.add(attempt)
                by_attempt[attempt] = better_attempt_record(by_attempt.get(attempt), record)
            latest = canonical_latest(list(by_attempt.values()))
            if 2 not in by_attempt:
                missing_attempt2.append({"acut_id": acut, "task_id": task})
            if latest is None:
                missing_canonical.append({"acut_id": acut, "task_id": task})
            if latest is not None:
                status = str(latest.get("status"))
                status_counts[status] = status_counts.get(status, 0) + 1
                label = str(latest.get("failure_label"))
                failure_label_counts[label] = failure_label_counts.get(label, 0) + 1
                coverage = latest.get("metadata_coverage") if isinstance(latest.get("metadata_coverage"), dict) else {}
                for field in coverage.get("missing_future_fields", []):
                    metadata_missing_counts[str(field)] = metadata_missing_counts.get(str(field), 0) + 1
            cells[f"{acut}::{task}"] = {
                "acut_id": acut,
                "task_id": task,
                "attempts": {str(attempt): by_attempt[attempt] for attempt in sorted(by_attempt)},
                "attempt1": by_attempt.get(1),
                "attempt2": by_attempt.get(2),
                "canonical_latest": latest,
            }

    by_acut: dict[str, Any] = {}
    for acut in CORE_ACUTS:
        canonical = [cells[f"{acut}::{task}"]["canonical_latest"] for task in task_ids]
        present = [record for record in canonical if isinstance(record, dict)]
        passed = sum(1 for record in present if record.get("status") == "passed")
        scoreable = sum(1 for record in present if record.get("scoreable"))
        fixed_denominator = len(task_ids)
        acut_status_counts: dict[str, int] = {}
        acut_failure_counts: dict[str, int] = {}
        for record in present:
            status = str(record.get("status"))
            acut_status_counts[status] = acut_status_counts.get(status, 0) + 1
            label = str(record.get("failure_label"))
            acut_failure_counts[label] = acut_failure_counts.get(label, 0) + 1
        by_acut[acut] = {
            "canonical_present": len(present),
            "canonical_missing": fixed_denominator - len(present),
            "passed": passed,
            "scoreable": scoreable,
            "fixed_denominator": fixed_denominator,
            "score_percent_fixed_denominator": 100.0 * passed / fixed_denominator if fixed_denominator else None,
            "scoreable_pass_rate": passed / scoreable if scoreable else None,
            "wilson_95_fixed_denominator": wilson_interval(passed, fixed_denominator),
            "status_counts": dict(sorted(acut_status_counts.items())),
            "failure_label_counts": dict(sorted(acut_failure_counts.items())),
        }

    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "split": split,
        "task_ids": list(task_ids),
        "acut_ids": CORE_ACUTS,
        "normalized_root": str(root),
        "candidate_policy": {
            "requires_batch_runner": batch.RUNNER_ID,
            "requires_model_call_made": True,
            "excludes_direct_runner_status": ["dry_run_completed"],
            "canonical_latest": "highest scoreable attempt number per ACUT/task; falls back to highest attempt only when no scoreable evidence exists",
            "duplicate_same_attempt_tiebreak": "scoreable evidence, payload finished_at, payload started_at, run_id, then artifact path; filesystem mtime is diagnostic only",
        },
        "matrix_shape": {
            "acuts": len(CORE_ACUTS),
            "tasks": len(task_ids),
            "expected_cells": len(CORE_ACUTS) * len(task_ids),
            "attempts_seen": sorted(attempts_seen),
        },
        "read_diagnostics": {"ignored_candidate_files": ignored_count},
        "missing": {
            "attempt2_cells": missing_attempt2,
            "canonical_cells": missing_canonical,
        },
        "status_counts_canonical": dict(sorted(status_counts.items())),
        "failure_label_counts_canonical": dict(sorted(failure_label_counts.items())),
        "metadata_missing_counts_canonical_future_contract": dict(sorted(metadata_missing_counts.items())),
        "by_acut": by_acut,
        "cells": cells,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(os.sys.argv[1:] if argv is None else argv)
    try:
        split = str(args.split).lower()
        task_ids = load_tasks(split, args.task_split_manifest)
        payload = build_matrix(split, task_ids, Path(args.normalized_root))
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
