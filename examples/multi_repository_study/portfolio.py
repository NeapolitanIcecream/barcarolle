#!/usr/bin/env python3
"""Audit a pinned task source into repository-local wide and deep portfolios."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    parse_utc_timestamp,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "portfolio-plan.json"
DEFAULT_OUTPUT = HERE / "portfolio.json"


def load_portfolio_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("portfolio plan must be a JSON object")
    if payload.get("schema_version") != "barcarolle_repository_portfolio_plan_v1":
        raise ValueError("portfolio plan schema is unsupported")
    digest = payload.get("portfolio_plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "portfolio_plan_digest"}
    )
    if digest != expected:
        raise ValueError("portfolio plan digest does not match")
    return payload


def build_portfolio(
    dataset_rows: Sequence[Mapping[str, object]],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Return a sanitized capacity audit without Task text, patches, or outcomes."""
    if not dataset_rows:
        raise ValueError("dataset must contain at least one Task")
    protocol = _mapping(plan, "origin_protocol")
    minimum_history = _positive_integer(
        protocol,
        "minimum_initial_history_tasks",
    )
    future_block = _positive_integer(protocol, "future_block_tasks")
    deep_minimum = _positive_integer(protocol, "deep_minimum_origins")
    lineage = _mapping(plan, "repository_lineage")

    rows_by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    seen_instances: set[str] = set()
    for row in dataset_rows:
        repository_id = _required_string(row, "repo")
        instance_id = _required_string(row, "instance_id")
        if instance_id in seen_instances:
            raise ValueError(f"duplicate dataset instance: {instance_id}")
        seen_instances.add(instance_id)
        created_at = _required_string(row, "created_at")
        format_utc_timestamp(parse_utc_timestamp(created_at))
        _required_string(row, "difficulty")
        rows_by_repository[repository_id].append(row)

    if set(lineage) != set(rows_by_repository):
        raise ValueError("repository lineage must exactly cover dataset repositories")

    repository_rows = []
    for repository_id, rows in sorted(rows_by_repository.items()):
        lineage_row = _mapping(lineage, repository_id)
        cluster_id = _required_string(lineage_row, "repository_cluster_id")
        fork = lineage_row.get("fork")
        if not isinstance(fork, bool):
            raise ValueError("repository fork must be a boolean")
        times = tuple(
            sorted(
                format_utc_timestamp(
                    parse_utc_timestamp(_required_string(row, "created_at"))
                )
                for row in rows
            )
        )
        task_count = len(rows)
        if task_count >= minimum_history + future_block:
            initial_history = minimum_history + (
                (task_count - minimum_history) % future_block
            )
            origin_count = (task_count - initial_history) // future_block
            exclusion_reason = None
        else:
            initial_history = None
            origin_count = 0
            exclusion_reason = "fewer_than_one_complete_origin"
        repository_rows.append(
            {
                "repository_id": repository_id,
                "repository_cluster_id": cluster_id,
                "fork": fork,
                "task_count": task_count,
                "initial_history_task_count": initial_history,
                "future_block_task_count": future_block,
                "origin_count": origin_count,
                "first_task_at": times[0],
                "last_task_at": times[-1],
                "difficulty_counts": dict(
                    sorted(
                        Counter(
                            _required_string(row, "difficulty") for row in rows
                        ).items()
                    )
                ),
                "wide_eligible": origin_count >= 1,
                "deep_eligible": origin_count >= deep_minimum,
                "exclusion_reason": exclusion_reason,
            }
        )

    wide_ids = tuple(
        row["repository_id"] for row in repository_rows if row["wide_eligible"]
    )
    deep_ids = tuple(
        row["repository_id"] for row in repository_rows if row["deep_eligible"]
    )
    total_origins = sum(int(row["origin_count"]) for row in repository_rows)
    largest_origin_share = (
        max(int(row["origin_count"]) for row in repository_rows) / total_origins
        if total_origins
        else None
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_repository_portfolio_v1",
        "source": plan.get("source"),
        "origin_protocol": dict(protocol),
        "repository_count": len(repository_rows),
        "task_count": len(dataset_rows),
        "potential_origin_count": total_origins,
        "largest_repository_origin_share": largest_origin_share,
        "wide_repository_ids": wide_ids,
        "deep_repository_ids": deep_ids,
        "repositories": tuple(repository_rows),
        "limitations": (
            "Task and Origin counts are source-capacity evidence, not certified "
            "Task Pool or Agent-outcome evidence.",
            "Current GitHub fork metadata is a lineage check, not proof of "
            "statistical independence.",
            "The source is Python-heavy and cannot establish language-level "
            "portability.",
        ),
    }
    result["portfolio_digest"] = canonical_digest(result)
    return result


def _dataset_rows(path: Path) -> tuple[Mapping[str, object], ...]:
    # The extraction environment owns this optional dependency.
    import pyarrow.parquet as parquet

    return tuple(
        parquet.read_table(
            path,
            columns=["repo", "instance_id", "created_at", "difficulty"],
        ).to_pylist()
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _positive_integer(value: Mapping[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return item


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_portfolio_plan(args.plan)
    source = _mapping(plan, "source")
    if _file_sha256(args.dataset) != _required_string(source, "dataset_sha256"):
        raise RuntimeError("dataset digest does not match portfolio plan")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite portfolio: {args.output}")
    result = build_portfolio(_dataset_rows(args.dataset), plan)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "portfolio_digest": result["portfolio_digest"],
                "repository_count": result["repository_count"],
                "wide_repository_count": len(result["wide_repository_ids"]),
                "deep_repository_count": len(result["deep_repository_ids"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
