from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from barcarolle.task_pool import load_prepared_candidate_package  # noqa: E402
from examples.swe_bench_static import (  # noqa: E402
    freeze_source,
    prepare_package,
)


def test_freeze_source_writes_digest_bound_sorted_repository_frame(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = tmp_path / "dataset.parquet"
    dataset.write_bytes(b"fixture")
    output = tmp_path / "source.json"
    monkeypatch.setattr(
        freeze_source,
        "_repository_rows",
        lambda path, repository_id: (
            {"instance_id": "repo__repo-1"},
            {"instance_id": "repo__repo-2"},
        ),
    )
    raw_manifest = json.dumps(
        {
            "schemaVersion": 2,
            "layers": [
                {"size": 10},
                {"size": 20},
            ],
        },
        separators=(",", ":"),
    ).encode()
    monkeypatch.setattr(
        freeze_source,
        "_remote_manifest",
        lambda tagged_ref: raw_manifest,
    )

    frozen = freeze_source.freeze_source(
        dataset=dataset,
        dataset_repository="owner/dataset",
        dataset_revision="a" * 40,
        dataset_sha256=hashlib.sha256(b"fixture").hexdigest(),
        repository_id="owner/repo",
        source_family="fixture",
        harness_repository="owner/harness",
        harness_revision="b" * 40,
        observed_at="2026-07-25T00:00:00Z",
        output_path=output,
    )

    loaded = freeze_source.load_source_manifest(output)
    assert loaded == frozen
    assert [item["instance_id"] for item in loaded["instances"]] == [
        "repo__repo-1",
        "repo__repo-2",
    ]
    assert all(item["compressed_layer_bytes"] == 30 for item in loaded["instances"])
    assert all(
        item["image_digest"] == "sha256:" + hashlib.sha256(raw_manifest).hexdigest()
        for item in loaded["instances"]
    )


def test_prepare_package_emits_replayable_full_frame_and_dependency_clusters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = tmp_path / "dataset.parquet"
    dataset.write_bytes(b"fixture dataset")
    dataset_digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    source_path = tmp_path / "source.json"
    source_payload = {
        "schema_version": freeze_source.SOURCE_MANIFEST_SCHEMA_VERSION,
        "dataset": {
            "repository": "owner/dataset",
            "revision": "a" * 40,
            "parquet_sha256": dataset_digest,
        },
        "repository_id": "owner/repo",
        "source_family": "fixture",
        "harness": {
            "repository": "owner/harness",
            "revision": "b" * 40,
        },
        "image_prefix": freeze_source.DEFAULT_IMAGE_PREFIX,
        "observed_at": "2026-07-25T00:00:00.000000Z",
        "sampling": {
            "mode": "all_repository_rows",
            "order": "instance_id_ascending",
        },
        "instances": [
            {
                "instance_id": "repo__repo-1",
                "image_digest": "sha256:" + "1" * 64,
                "compressed_layer_bytes": 10,
            },
            {
                "instance_id": "repo__repo-2",
                "image_digest": "sha256:" + "2" * 64,
                "compressed_layer_bytes": 20,
            },
        ],
    }
    source_payload["source_manifest_digest"] = canonical_digest(source_payload)
    source_path.write_text(canonical_json(source_payload) + "\n", encoding="utf-8")
    rows = (
        _row("repo__repo-1", "1" * 40, "a.py", "easy"),
        _row("repo__repo-2", "2" * 40, "a.py", "hard"),
    )
    monkeypatch.setattr(
        prepare_package,
        "_selected_rows",
        lambda path, source: rows,
    )

    def write_spec(path: Path, row: dict[str, object]) -> None:
        path.write_text(
            canonical_json({"instance_id": row["instance_id"]}) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(prepare_package, "_write_check_spec", write_spec)
    output = tmp_path / "package"
    summary = prepare_package.prepare_package(
        dataset=dataset,
        source_manifest_path=source_path,
        output_dir=output,
        harness_python=Path(sys.executable),
        raw_check_output_dir=tmp_path / "raw-checks",
        check_material_availability_basis="source_observed_at",
    )

    package = load_prepared_candidate_package(
        output / "prepared-candidate-package.jsonl"
    )
    assert summary["candidate_count"] == 2
    assert summary["dependency_cluster_count"] == 1
    assert len(package.batch.candidates) == 2
    assert {
        candidate.oracle_source for candidate in package.batch.candidates
    } == {"fixture_hidden_tests"}
    assert (
        len({candidate.dependency_cluster_id for candidate in package.batch.candidates})
        == 1
    )
    assert package.manifest.source_protocol is not None
    assert package.manifest.observed_frame is not None
    assert package.manifest.observed_frame["coverage_mode"] == (
        "one_source_event_per_frame_unit_v1"
    )
    assert len(package.observed_frame_events) == 2
    assert package.adapter_evidence is not None
    assert (
        package.adapter_evidence["source_manifest_digest"]
        == (source_payload["source_manifest_digest"])
    )


@pytest.mark.parametrize(
    ("basis", "expected_check_time"),
    (
        ("source_observed_at", "2026-07-25T00:00:00.000000Z"),
        ("task_material_available_at", "2020-01-01T00:00:00.000000Z"),
    ),
)
def test_prepare_package_binds_explicit_check_availability_basis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    basis: str,
    expected_check_time: str,
) -> None:
    dataset = tmp_path / "dataset.parquet"
    dataset.write_bytes(b"fixture dataset")
    source_path = tmp_path / "source.json"
    source_payload = {
        "schema_version": freeze_source.SOURCE_MANIFEST_SCHEMA_VERSION,
        "dataset": {
            "repository": "owner/dataset",
            "revision": "a" * 40,
            "parquet_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        },
        "repository_id": "owner/repo",
        "source_family": "swe_bench_verified",
        "harness": {
            "repository": "owner/harness",
            "revision": "b" * 40,
        },
        "image_prefix": freeze_source.DEFAULT_IMAGE_PREFIX,
        "observed_at": "2026-07-25T00:00:00.000000Z",
        "sampling": {
            "mode": "all_repository_rows",
            "order": "instance_id_ascending",
        },
        "instances": [
            {
                "instance_id": "repo__repo-1",
                "image_digest": "sha256:" + "1" * 64,
                "compressed_layer_bytes": 10,
            },
        ],
    }
    source_payload["source_manifest_digest"] = canonical_digest(source_payload)
    source_path.write_text(canonical_json(source_payload) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        prepare_package,
        "_selected_rows",
        lambda path, source: (
            _row("repo__repo-1", "1" * 40, "a.py", "easy"),
        ),
    )
    monkeypatch.setattr(
        prepare_package,
        "_write_check_spec",
        lambda path, row: path.write_text(
            canonical_json({"instance_id": row["instance_id"]}) + "\n",
            encoding="utf-8",
        ),
    )

    prepare_package.prepare_package(
        dataset=dataset,
        source_manifest_path=source_path,
        output_dir=tmp_path / "package",
        harness_python=Path(sys.executable),
        raw_check_output_dir=tmp_path / "raw-checks",
        check_material_availability_basis=basis,
    )

    package = load_prepared_candidate_package(
        tmp_path / "package" / "prepared-candidate-package.jsonl"
    )
    assert package.batch.candidates[0].check_material_available_at == (
        expected_check_time
    )
    assert package.manifest.generator_behavior is not None
    assert package.manifest.generator_behavior["behavior_config"][
        "check_material_availability_basis"
    ] == basis


def _row(
    instance_id: str,
    base_commit: str,
    changed_path: str,
    difficulty: str,
) -> dict[str, object]:
    patch = (
        f"diff --git a/{changed_path} b/{changed_path}\n"
        f"--- a/{changed_path}\n"
        f"+++ b/{changed_path}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": base_commit,
        "patch": patch,
        "problem_statement": f"Fix {instance_id}.",
        "created_at": "2020-01-01T00:00:00Z",
        "version": "1",
        "difficulty": difficulty,
    }
