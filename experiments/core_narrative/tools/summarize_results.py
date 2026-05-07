#!/usr/bin/env python3
"""Summarize normalized core narrative run-result JSON files."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any

from _common import ToolError, emit_json, fail


TOOL = "summarize_results"
SCOREABLE_STATUSES = {"passed", "failed", "timeout", "invalid_submission"}
KNOWN_STATUSES = SCOREABLE_STATUSES | {"infra_failed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read normalized run-result JSON files and emit aggregate counts and "
            "pass rates by ACUT and split."
        )
    )
    parser.add_argument("paths", nargs="+", help="Result JSON files or directories to scan recursively.")
    parser.add_argument("--output", help="Optional path for the structured JSON summary.")
    parser.add_argument("--fail-on-empty", action="store_true", help="Exit non-zero when no result files are found.")
    return parser.parse_args()


def iter_result_paths(paths: list[str]) -> list[Path]:
    result_paths: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            result_paths.extend(sorted(candidate for candidate in path.rglob("*.json") if candidate.is_file()))
        elif path.is_file():
            result_paths.append(path)
        else:
            raise ToolError("result path does not exist", path=str(path))
    return result_paths


def load_result(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ToolError("failed to parse result JSON", path=str(path), cause=str(exc)) from exc
    if not isinstance(data, dict):
        raise ToolError("result JSON root must be an object", path=str(path))
    required = {"run_id", "acut_id", "task_id", "split", "status"}
    missing = sorted(required - set(data))
    if missing:
        raise ToolError("result JSON is missing required fields", path=str(path), missing=missing)
    return data


def empty_bucket() -> dict[str, Any]:
    return {
        "total": 0,
        "scoreable": 0,
        "passed": 0,
        "pass_rate": None,
        "status_counts": collections.Counter(),
    }


def add_to_bucket(bucket: dict[str, Any], status: str) -> None:
    bucket["total"] += 1
    bucket["status_counts"][status] += 1
    if status in SCOREABLE_STATUSES:
        bucket["scoreable"] += 1
    if status == "passed":
        bucket["passed"] += 1


def finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    scoreable = bucket["scoreable"]
    pass_rate = None if scoreable == 0 else round(bucket["passed"] / scoreable, 4)
    return {
        "total": bucket["total"],
        "scoreable": scoreable,
        "passed": bucket["passed"],
        "pass_rate": pass_rate,
        "status_counts": dict(sorted(bucket["status_counts"].items())),
    }


def main() -> int:
    args = parse_args()
    try:
        result_paths = iter_result_paths(args.paths)
        if not result_paths and args.fail_on_empty:
            raise ToolError("no result JSON files found")

        results = [load_result(path) for path in result_paths]
        warnings: list[str] = []
        total_status_counts: collections.Counter[str] = collections.Counter()
        by_acut: dict[str, dict[str, Any]] = collections.defaultdict(empty_bucket)
        by_split: dict[str, dict[str, Any]] = collections.defaultdict(empty_bucket)
        by_acut_split: dict[str, dict[str, dict[str, Any]]] = collections.defaultdict(
            lambda: collections.defaultdict(empty_bucket)
        )

        for result in results:
            status = str(result["status"])
            if status not in KNOWN_STATUSES:
                warnings.append(f"unknown status {status!r} in {result['run_id']}")
            acut_id = str(result["acut_id"])
            split = str(result["split"])
            total_status_counts[status] += 1
            add_to_bucket(by_acut[acut_id], status)
            add_to_bucket(by_split[split], status)
            add_to_bucket(by_acut_split[acut_id][split], status)

        payload = {
            "tool": TOOL,
            "status": "summarized",
            "result_count": len(results),
            "input_count": len(result_paths),
            "status_counts": dict(sorted(total_status_counts.items())),
            "by_split": {key: finalize_bucket(value) for key, value in sorted(by_split.items())},
            "by_acut": {key: finalize_bucket(value) for key, value in sorted(by_acut.items())},
            "by_acut_split": {
                acut_id: {split: finalize_bucket(bucket) for split, bucket in sorted(split_map.items())}
                for acut_id, split_map in sorted(by_acut_split.items())
            },
            "warnings": warnings,
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
