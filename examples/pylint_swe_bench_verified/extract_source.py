#!/usr/bin/env python3
"""Extract the fixed Pylint pilot inputs using the pinned SWE-bench environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import pyarrow.parquet as parquet  # pyright: ignore[reportMissingImports]
from swebench.harness.test_spec import (  # pyright: ignore[reportMissingImports]
    make_test_spec,
)


def extract(dataset: Path, task_sources: Path, output_dir: Path) -> Mapping[str, Any]:
    source = _load_object(task_sources)
    tasks = source.get("tasks")
    if not isinstance(tasks, list):
        raise RuntimeError("task_sources.json must contain a tasks list")
    requested_ids = tuple(_required_string(task, "instance_id") for task in tasks)
    if len(requested_ids) != 10 or len(set(requested_ids)) != 10:
        raise RuntimeError("the Pylint pilot requires exactly 10 unique instances")

    rows = {
        row["instance_id"]: row
        for row in parquet.read_table(dataset).to_pylist()
        if row.get("instance_id") in requested_ids
    }
    if set(rows) != set(requested_ids):
        missing = sorted(set(requested_ids) - set(rows))
        raise RuntimeError(f"dataset is missing fixed instances: {', '.join(missing)}")

    bundles_dir = output_dir / "hidden-checks"
    patches_dir = output_dir / "reference-patches"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    patches_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Mapping[str, Any]] = []
    for task_source in tasks:
        instance_id = _required_string(task_source, "instance_id")
        row = rows[instance_id]
        if row.get("repo") != "pylint-dev/pylint":
            raise RuntimeError(f"{instance_id} is not a pylint-dev/pylint task")
        spec = make_test_spec(row)
        spec_payload = {
            "instance_id": instance_id,
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "version": row["version"],
            "FAIL_TO_PASS": list(spec.FAIL_TO_PASS),
            "PASS_TO_PASS": list(spec.PASS_TO_PASS),
            "eval_script_list": list(spec.eval_script_list),
        }
        bundle = bundles_dir / instance_id
        bundle.mkdir(parents=True, exist_ok=True)
        _write_json(bundle / "spec.json", spec_payload)
        patch_path = patches_dir / f"{instance_id}.diff"
        patch_path.write_text(_required_string(row, "patch"), encoding="utf-8")
        extracted.append(
            {
                "instance_id": instance_id,
                "repo": row["repo"],
                "base_commit": row["base_commit"],
                "problem_statement": row["problem_statement"],
                "version": row["version"],
                "difficulty": row["difficulty"],
                "fail_to_pass_count": len(spec.FAIL_TO_PASS),
                "pass_to_pass_count": len(spec.PASS_TO_PASS),
                "bundle_ref": f"hidden-checks/{instance_id}",
                "reference_patch_ref": f"reference-patches/{instance_id}.diff",
            }
        )
    payload = {"tasks": extracted}
    _write_json(output_dir / "extracted-source.json", payload)
    return payload


def _load_object(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise RuntimeError(f"{key} must be a non-empty string")
    return item


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--task-sources", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = extract(args.dataset, args.task_sources, args.output_dir)
    print(json.dumps({"task_count": len(summary["tasks"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
