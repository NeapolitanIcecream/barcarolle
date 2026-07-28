from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.external_benchmark_inventory.inventory import (  # noqa: E402
    build_inventory,
    load_or_query_source,
    load_inventory_plan,
    verify_local_source,
)
from examples.external_benchmark_inventory import inventory  # noqa: E402


def test_inventory_keeps_repositories_local_and_measures_overlap() -> None:
    plan = _plan(
        (
            _source("reference", "reject"),
            _source("candidate", "assume_utc_for_capacity_only"),
        )
    )
    reference_rows = tuple(
        _row(
            repo="owner/reference",
            number=index,
            created_at=f"2020-01-{index + 1:02d}T00:00:00Z",
        )
        for index in range(25)
    )
    candidate_rows = tuple(
        _row(
            repo="owner/candidate",
            number=index,
            created_at=f"2021-02-{index + 1:02d} 00:00:00",
        )
        for index in range(26)
    )
    candidate_rows = (
        {
            **candidate_rows[0],
            "instance_id": reference_rows[0]["instance_id"],
            "base_commit": reference_rows[0]["base_commit"],
        },
        *candidate_rows[1:],
    )

    result = build_inventory(
        plan,
        {
            "reference": reference_rows,
            "candidate": candidate_rows,
        },
    )

    sources = {source["source_id"]: source for source in result["sources"]}
    assert sources["reference"]["repository_count"] == 1
    assert sources["candidate"]["repository_count"] == 1
    assert sources["reference"]["origin_capacity"][0]["potential_origin_count"] == 2
    assert sources["candidate"]["origin_capacity"][0]["potential_origin_count"] == 2
    assert sources["candidate"]["naive_timestamps_assumed_utc"] == 26
    overlap = result["pairwise_source_overlaps"][0]
    assert overlap["repository_overlap_count"] == 0
    assert overlap["instance_id_overlap_count"] == 1
    assert overlap["repository_base_commit_overlap_count"] == 0
    assert result["resource_use"]["paid_api_calls"] == 0


def test_inventory_rejects_naive_time_without_source_policy() -> None:
    plan = _plan((_source("candidate", "reject"),))
    with pytest.raises(ValueError, match="timezone-naive"):
        build_inventory(
            plan,
            {
                "candidate": (
                    _row(
                        repo="owner/repo",
                        number=1,
                        created_at="2021-01-01 00:00:00",
                    ),
                )
            },
        )


def test_inventory_rejects_duplicate_source_instances() -> None:
    plan = _plan((_source("candidate", "reject"),))
    repeated = _row(
        repo="owner/repo",
        number=1,
        created_at="2021-01-01T00:00:00Z",
    )
    with pytest.raises(ValueError, match="duplicate source instance"):
        build_inventory(
            plan,
            {"candidate": (repeated, repeated)},
        )


def test_inventory_plan_is_digest_bound(tmp_path: Path) -> None:
    plan = _plan((_source("candidate", "reject"),))
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    loaded = load_inventory_plan(path)
    assert loaded["study_id"] == plan["study_id"]
    assert loaded["inventory_plan_digest"] == plan["inventory_plan_digest"]

    changed = dict(plan)
    changed["study_id"] = "changed"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        load_inventory_plan(path)


def test_local_source_rejects_partial_or_changed_bytes(tmp_path: Path) -> None:
    source = _source("candidate", "reject")
    source["data_sha256"] = hashlib.sha256(b"complete").hexdigest()
    source["data_size_bytes"] = len(b"complete")
    path = tmp_path / "candidate.parquet"
    path.write_bytes(b"partial!")

    with pytest.raises(RuntimeError, match="digest"):
        verify_local_source(source, tmp_path)


def test_projection_cache_rejects_modified_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source("candidate", "reject")
    projected = (
        _row(
            repo="owner/repo",
            number=1,
            created_at="2021-01-01T00:00:00Z",
        ),
    )
    monkeypatch.setattr(inventory, "query_source", lambda source, source_dir: projected)
    assert load_or_query_source(source, tmp_path) == projected
    cache_path = next(tmp_path.glob("*.json"))
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    payload["rows"][0]["repo"] = "changed/repo"
    cache_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cache identity"):
        load_or_query_source(source, tmp_path)


def _plan(
    sources: tuple[dict[str, object], ...],
) -> dict[str, object]:
    plan: dict[str, object] = {
        "schema_version": "barcarolle_external_benchmark_inventory_plan_v1",
        "study_id": "fixture",
        "origin_protocols": [
            {
                "protocol_id": "fixture-h5",
                "minimum_initial_history_tasks": 15,
                "future_block_tasks": 5,
                "deep_minimum_origins": 5,
            }
        ],
        "executable_sources": sources,
        "descriptor_only_sources": [],
    }
    plan["inventory_plan_digest"] = canonical_digest(plan)
    return plan


def _source(source_id: str, timestamp_policy: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "role": "candidate",
        "dataset_repository": "owner/dataset",
        "dataset_revision": "a" * 40,
        "data_path": "data.parquet",
        "data_sha256": "b" * 64,
        "data_size_bytes": 1,
        "format": "parquet",
        "repo_field": "repo",
        "instance_field": "instance_id",
        "base_commit_field": "base_commit",
        "created_at_field": "created_at",
        "language_constant": "Python",
        "naive_timestamp_policy": timestamp_policy,
    }


def _row(
    *,
    repo: str,
    number: int,
    created_at: str,
) -> dict[str, object]:
    return {
        "repo": repo,
        "instance_id": f"{repo}-task-{number}",
        "base_commit": f"{number:040x}",
        "created_at": created_at,
        "language": "Python",
    }
