#!/usr/bin/env python3
"""Audit pinned benchmark metadata for repository-local rolling-Origin supply."""

from __future__ import annotations

# The extraction environment owns the optional DuckDB dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import Counter, defaultdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from statistics import median
import sys
from typing import Any, Mapping, Sequence
from urllib.parse import quote


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "inventory-plan.json"
DEFAULT_OUTPUT = HERE / "inventory-results.json"
DEFAULT_CACHE_DIR = (
    Path("outputs")
    / "research"
    / "2026-07-28-external-benchmark-inventory"
    / "metadata-projections"
)
PLAN_SCHEMA_VERSION = "barcarolle_external_benchmark_inventory_plan_v1"
RESULT_SCHEMA_VERSION = "barcarolle_external_benchmark_inventory_v1"
CACHE_SCHEMA_VERSION = "barcarolle_external_benchmark_projection_cache_v1"
TASK_COUNT_THRESHOLDS = (1, 5, 10, 15, 20, 25, 30, 50, 75, 100, 200, 500)
TOP_REPOSITORY_LIMIT = 25
_SQL_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def load_inventory_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("inventory plan must be a JSON object")
    if payload.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise ValueError("inventory plan schema is unsupported")
    digest = payload.get("inventory_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "inventory_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("inventory plan digest does not match")
    _protocols(payload)
    sources = _mapping_sequence(payload, "executable_sources")
    source_ids = tuple(_required_string(source, "source_id") for source in sources)
    if not source_ids or len(source_ids) != len(set(source_ids)):
        raise ValueError("executable source IDs must be nonempty and unique")
    return payload


def build_inventory(
    plan: Mapping[str, Any],
    rows_by_source: Mapping[str, Sequence[Mapping[str, object]]],
) -> Mapping[str, Any]:
    """Build a sanitized capacity result from source-projected metadata rows."""
    source_specs = {
        _required_string(source, "source_id"): source
        for source in _mapping_sequence(plan, "executable_sources")
    }
    if set(rows_by_source) != set(source_specs):
        raise ValueError("rows must exactly cover executable sources")

    normalized_by_source: dict[str, tuple[Mapping[str, object], ...]] = {}
    summaries = []
    for source_id, source in source_specs.items():
        normalized = _normalize_rows(
            rows_by_source[source_id],
            naive_timestamp_policy=_required_string(
                source,
                "naive_timestamp_policy",
            ),
        )
        normalized_by_source[source_id] = normalized
        summaries.append(_source_summary(source, normalized, _protocols(plan)))

    overlaps = []
    source_ids = tuple(sorted(normalized_by_source))
    for left_index, left_id in enumerate(source_ids):
        for right_id in source_ids[left_index + 1 :]:
            left_rows = normalized_by_source[left_id]
            right_rows = normalized_by_source[right_id]
            overlaps.append(
                {
                    "left_source_id": left_id,
                    "right_source_id": right_id,
                    "repository_overlap_count": len(
                        {str(row["repo"]) for row in left_rows}
                        & {str(row["repo"]) for row in right_rows}
                    ),
                    "instance_id_overlap_count": len(
                        {str(row["instance_id"]) for row in left_rows}
                        & {str(row["instance_id"]) for row in right_rows}
                    ),
                    "repository_base_commit_overlap_count": len(
                        {
                            (str(row["repo"]), str(row["base_commit"]))
                            for row in left_rows
                        }
                        & {
                            (str(row["repo"]), str(row["base_commit"]))
                            for row in right_rows
                        }
                    ),
                }
            )

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "study_id": plan.get("study_id"),
        "inventory_plan_digest": plan.get("inventory_plan_digest"),
        "origin_protocols": tuple(_protocols(plan)),
        "sources": tuple(summaries),
        "pairwise_source_overlaps": tuple(overlaps),
        "descriptor_only_sources": plan.get("descriptor_only_sources"),
        "claim_boundary": (
            "Projected metadata establishes source and repository-local Origin "
            "capacity only. It does not establish Task certification, repository "
            "independence, public Agent-result coverage, or future-Task validity."
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "coding_agent_calls": 0,
            "embedding_calls": 0,
            "agent_outcomes_opened": 0,
        },
    }
    result["inventory_digest"] = canonical_digest(result)
    return result


def query_source(
    source: Mapping[str, object],
    source_dir: Path | None = None,
) -> tuple[Mapping[str, object], ...]:
    """Project only identity and time columns from one pinned remote Parquet file."""
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError(
            "DuckDB is required for remote metadata projection; run with "
            "`uv run --with duckdb`"
        ) from error

    fields = {
        key: _sql_identifier(_required_string(source, key))
        for key in (
            "repo_field",
            "instance_field",
            "base_commit_field",
            "created_at_field",
        )
    }
    language_field = source.get("language_field")
    language_constant = source.get("language_constant")
    if isinstance(language_field, str) and language_field:
        language_expression = f"CAST({_sql_identifier(language_field)} AS VARCHAR)"
    elif isinstance(language_constant, str) and language_constant:
        language_expression = "'" + language_constant.replace("'", "''") + "'"
    else:
        raise ValueError("source must declare language_field or language_constant")

    if source_dir is None:
        repository = _required_string(
            source,
            "projection_repository"
            if "projection_repository" in source
            else "dataset_repository",
        )
        revision = _required_string(
            source,
            "projection_revision"
            if "projection_revision" in source
            else "dataset_revision",
        )
        path = _required_string(
            source,
            "projection_path" if "projection_path" in source else "data_path",
        )
        data_location = (
            f"https://huggingface.co/datasets/{quote(repository, safe='/')}/resolve/"
            f"{quote(revision, safe='')}/{quote(path, safe='/')}"
        )
    else:
        data_location = str(
            verify_local_source(source, source_dir).resolve()
        )
    query = f"""
        SELECT
            CAST({fields["repo_field"]} AS VARCHAR) AS repo,
            CAST({fields["instance_field"]} AS VARCHAR) AS instance_id,
            CAST({fields["base_commit_field"]} AS VARCHAR) AS base_commit,
            CAST({fields["created_at_field"]} AS VARCHAR) AS created_at,
            {language_expression} AS language
        FROM read_parquet(?)
        ORDER BY repo, created_at, instance_id
    """
    connection = duckdb.connect()
    connection.execute("SET enable_progress_bar=false")
    values = connection.execute(query, [data_location]).fetchall()
    return tuple(
        {
            "repo": row[0],
            "instance_id": row[1],
            "base_commit": row[2],
            "created_at": row[3],
            "language": row[4],
        }
        for row in values
    )


def load_or_query_source(
    source: Mapping[str, object],
    cache_dir: Path,
    source_dir: Path | None = None,
) -> tuple[Mapping[str, object], ...]:
    """Reuse an identity-bound ignored projection so a remote failure can resume."""
    source_id = _required_string(source, "source_id")
    identity = {
        key: source.get(key)
        for key in (
            "source_id",
            "dataset_repository",
            "dataset_revision",
            "data_path",
            "data_sha256",
            "projection_repository",
            "projection_revision",
            "projection_path",
            "projection_sha256",
        )
        if key in source
    }
    cache_path = (
        cache_dir / f"{source_id}-{canonical_digest(identity)[:16]}.json"
    )
    if cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"projection cache is not an object: {cache_path}")
        digest = payload.get("cache_digest")
        expected = canonical_digest(
            {key: value for key, value in payload.items() if key != "cache_digest"}
        )
        if (
            payload.get("schema_version") != CACHE_SCHEMA_VERSION
            or payload.get("source_identity") != identity
            or digest != expected
        ):
            raise ValueError(f"projection cache identity is invalid: {cache_path}")
        rows = payload.get("rows")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise ValueError(f"projection cache rows are invalid: {cache_path}")
        if any(not isinstance(row, Mapping) for row in rows):
            raise ValueError(f"projection cache row is invalid: {cache_path}")
        return tuple(rows)  # type: ignore[arg-type]

    rows = query_source(source, source_dir)
    payload: dict[str, object] = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "source_identity": identity,
        "rows": rows,
    }
    payload["cache_digest"] = canonical_digest(payload)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return rows


def verify_local_source(
    source: Mapping[str, object],
    source_dir: Path,
) -> Path:
    source_id = _required_string(source, "source_id")
    path = source_dir / f"{source_id}.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"local source file does not exist: {path}")
    expected_size_key = (
        "projection_size_bytes"
        if "projection_size_bytes" in source
        else "data_size_bytes"
    )
    expected_digest_key = (
        "projection_sha256" if "projection_sha256" in source else "data_sha256"
    )
    expected_size = source.get(expected_size_key)
    if (
        isinstance(expected_size, bool)
        or not isinstance(expected_size, int)
        or expected_size <= 0
    ):
        raise ValueError(f"{expected_size_key} must be a positive integer")
    if path.stat().st_size != expected_size:
        raise RuntimeError(f"local source size does not match plan: {path}")
    if _file_sha256(path) != _required_string(source, expected_digest_key):
        raise RuntimeError(f"local source digest does not match plan: {path}")
    return path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_summary(
    source: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    protocols: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    rows_by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_repository[str(row["repo"])].append(row)

    repository_rows = []
    for repository_id, repository_tasks in sorted(rows_by_repository.items()):
        ordered = sorted(
            repository_tasks,
            key=lambda row: (str(row["created_at"]), str(row["instance_id"])),
        )
        protocol_counts: dict[str, int] = {}
        protocol_spans: dict[str, tuple[float, ...]] = {}
        for protocol in protocols:
            protocol_id = _required_string(protocol, "protocol_id")
            origin_count, spans = _origin_capacity(ordered, protocol)
            protocol_counts[protocol_id] = origin_count
            protocol_spans[protocol_id] = spans
        repository_rows.append(
            {
                "repository_id": repository_id,
                "task_count": len(ordered),
                "first_task_at": ordered[0]["created_at"],
                "last_task_at": ordered[-1]["created_at"],
                "language_counts": dict(
                    sorted(Counter(str(row["language"]) for row in ordered).items())
                ),
                "origin_counts": protocol_counts,
                "_origin_spans": protocol_spans,
            }
        )

    protocol_summaries = []
    for protocol in protocols:
        protocol_id = _required_string(protocol, "protocol_id")
        deep_minimum = _positive_integer(protocol, "deep_minimum_origins")
        origin_counts = [
            int(repository["origin_counts"][protocol_id])
            for repository in repository_rows
        ]
        total_origins = sum(origin_counts)
        eligible_counts = [count for count in origin_counts if count > 0]
        spans = [
            span
            for repository in repository_rows
            for span in repository["_origin_spans"][protocol_id]
        ]
        top_origins = sorted(
            (
                {
                    "repository_id": repository["repository_id"],
                    "origin_count": repository["origin_counts"][protocol_id],
                }
                for repository in repository_rows
                if int(repository["origin_counts"][protocol_id]) > 0
            ),
            key=lambda row: (-int(row["origin_count"]), str(row["repository_id"])),
        )[:TOP_REPOSITORY_LIMIT]
        protocol_summaries.append(
            {
                "protocol_id": protocol_id,
                "potential_origin_count": total_origins,
                "wide_repository_count": len(eligible_counts),
                "deep_repository_count": sum(
                    count >= deep_minimum for count in origin_counts
                ),
                "median_origins_per_wide_repository": (
                    float(median(eligible_counts)) if eligible_counts else None
                ),
                "largest_repository_origin_share": (
                    max(origin_counts) / total_origins if total_origins else None
                ),
                "future_span_days": _numeric_summary(spans),
                "largest_origin_suppliers": tuple(top_origins),
            }
        )

    task_counts = [int(repository["task_count"]) for repository in repository_rows]
    largest_repositories = sorted(
        (
            {
                key: value
                for key, value in repository.items()
                if key != "_origin_spans"
            }
            for repository in repository_rows
        ),
        key=lambda row: (-int(row["task_count"]), str(row["repository_id"])),
    )[:TOP_REPOSITORY_LIMIT]
    summary: dict[str, object] = {
        "source_id": source.get("source_id"),
        "role": source.get("role"),
        "source_identity": {
            key: source.get(key)
            for key in (
                "dataset_repository",
                "dataset_revision",
                "data_path",
                "data_sha256",
                "data_size_bytes",
                "projection_revision",
                "projection_path",
                "projection_sha256",
            )
            if key in source
        },
        "task_count": len(rows),
        "repository_count": len(repository_rows),
        "first_task_at": min(str(row["created_at"]) for row in rows),
        "last_task_at": max(str(row["created_at"]) for row in rows),
        "language_task_counts": dict(
            sorted(Counter(str(row["language"]) for row in rows).items())
        ),
        "naive_timestamps_assumed_utc": sum(
            bool(row["timestamp_was_naive"]) for row in rows
        ),
        "repositories_at_least_task_count": {
            str(threshold): sum(count >= threshold for count in task_counts)
            for threshold in TASK_COUNT_THRESHOLDS
        },
        "repository_task_count": _numeric_summary(task_counts),
        "origin_capacity": tuple(protocol_summaries),
        "largest_repositories": tuple(largest_repositories),
    }
    summary["source_summary_digest"] = canonical_digest(summary)
    return summary


def _normalize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    naive_timestamp_policy: str,
) -> tuple[Mapping[str, object], ...]:
    if not rows:
        raise ValueError("source must contain at least one Task")
    if naive_timestamp_policy not in {
        "reject",
        "assume_utc_for_capacity_only",
    }:
        raise ValueError("naive timestamp policy is unsupported")
    normalized = []
    instance_ids: set[str] = set()
    for row in rows:
        repository_id = _required_string(row, "repo")
        instance_id = _required_string(row, "instance_id")
        if instance_id in instance_ids:
            raise ValueError(f"duplicate source instance: {instance_id}")
        instance_ids.add(instance_id)
        base_commit = _required_string(row, "base_commit")
        language = _required_string(row, "language")
        created_at = _required_string(row, "created_at")
        parsed, was_naive = _parse_source_time(
            created_at,
            naive_timestamp_policy=naive_timestamp_policy,
        )
        normalized.append(
            {
                "repo": repository_id,
                "instance_id": instance_id,
                "base_commit": base_commit,
                "created_at": format_utc_timestamp(parsed),
                "language": language,
                "timestamp_was_naive": was_naive,
            }
        )
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                str(row["repo"]),
                str(row["created_at"]),
                str(row["instance_id"]),
            ),
        )
    )


def _origin_capacity(
    ordered_rows: Sequence[Mapping[str, object]],
    protocol: Mapping[str, object],
) -> tuple[int, tuple[float, ...]]:
    minimum_history = _positive_integer(
        protocol,
        "minimum_initial_history_tasks",
    )
    future_block = _positive_integer(protocol, "future_block_tasks")
    task_count = len(ordered_rows)
    if task_count < minimum_history + future_block:
        return 0, ()
    initial_history = minimum_history + (
        (task_count - minimum_history) % future_block
    )
    origin_count = (task_count - initial_history) // future_block
    spans = []
    for future_start in range(initial_history, task_count, future_block):
        cutoff = _parsed_canonical_time(
            _required_string(ordered_rows[future_start - 1], "created_at")
        )
        future_end = _parsed_canonical_time(
            _required_string(
                ordered_rows[future_start + future_block - 1],
                "created_at",
            )
        )
        spans.append((future_end - cutoff).total_seconds() / 86400.0)
    if len(spans) != origin_count:
        raise AssertionError("Origin span count does not match capacity")
    return origin_count, tuple(spans)


def _parse_source_time(
    value: str,
    *,
    naive_timestamp_policy: str,
) -> tuple[datetime, bool]:
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"source timestamp is not ISO-8601: {value}") from error
    if parsed.utcoffset() is None:
        if naive_timestamp_policy == "reject":
            raise ValueError(f"source timestamp is timezone-naive: {value}")
        return parsed.replace(tzinfo=UTC), True
    return parsed.astimezone(UTC), False


def _parsed_canonical_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _numeric_summary(values: Sequence[int | float]) -> Mapping[str, float] | None:
    if not values:
        return None
    return {
        "minimum": float(min(values)),
        "median": float(median(values)),
        "maximum": float(max(values)),
    }


def _protocols(plan: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    protocols = _mapping_sequence(plan, "origin_protocols")
    protocol_ids = tuple(
        _required_string(protocol, "protocol_id") for protocol in protocols
    )
    if not protocol_ids or len(protocol_ids) != len(set(protocol_ids)):
        raise ValueError("Origin protocol IDs must be nonempty and unique")
    for protocol in protocols:
        _positive_integer(protocol, "minimum_initial_history_tasks")
        _positive_integer(protocol, "future_block_tasks")
        _positive_integer(protocol, "deep_minimum_origins")
    return protocols


def _sql_identifier(value: str) -> str:
    if not _SQL_IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe source field name: {value}")
    return f'"{value}"'


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    items = value.get(key)
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ValueError(f"{key} must be an array")
    if any(not isinstance(item, Mapping) for item in items):
        raise ValueError(f"{key} entries must be objects")
    return tuple(items)  # type: ignore[arg-type]


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
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument(
        "--source-dir",
        type=Path,
        help=(
            "Directory containing <source_id>.parquet files; each file is "
            "size- and SHA-256-verified against the plan before projection"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_inventory_plan(args.plan)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite inventory: {args.output}")
    rows_by_source = {
        _required_string(source, "source_id"): load_or_query_source(
            source,
            args.cache_dir,
            args.source_dir,
        )
        for source in _mapping_sequence(plan, "executable_sources")
    }
    result = build_inventory(plan, rows_by_source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "inventory_digest": result["inventory_digest"],
                "source_count": len(result["sources"]),
                "task_count": sum(
                    int(source["task_count"]) for source in result["sources"]
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
