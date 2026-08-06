#!/usr/bin/env python3
"""Prepare a strict Barcarolle package from one frozen SWE-bench repository slice."""

from __future__ import annotations

# The extraction environment owns these optional dependencies.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    ObservedFrameEventRecord,
    PreparedCandidateMaterialRecord,
    PreparedCandidatePackageManifest,
    canonical_data,
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    make_source_event_id,
    parse_utc_timestamp,
    record_with_digest,
    utc_now_timestamp,
    write_jsonl_records,
)
from barcarolle.task_pool import (  # noqa: E402
    PREPARED_CANDIDATE_PACKAGE_SCHEMA_VERSION,
    TaskCandidate,
)
from barcarolle.verification import hidden_material_digest  # noqa: E402
from examples.swe_bench_static.freeze_source import (  # noqa: E402
    load_source_manifest,
)


HERE = Path(__file__).resolve().parent
CHECK = (HERE / "check.py").resolve()
ADAPTER_VERSION = "swe_bench_static_dataset_import_v2"
DEPENDENCY_PROTOCOL_VERSION = "trusted_reference_patch_path_overlap_v1"
CHECK_MATERIAL_AVAILABILITY_BASES = (
    "source_observed_at",
    "task_material_available_at",
)


def prepare_package(
    *,
    dataset: Path,
    source_manifest_path: Path,
    output_dir: Path,
    harness_python: Path,
    raw_check_output_dir: Path,
    check_material_availability_basis: str,
    check_timeout_seconds: int = 900,
) -> Mapping[str, Any]:
    """Materialize a strict package; do not run a Generator or hidden check."""
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite prepared package: {output_dir}")
    if check_material_availability_basis not in CHECK_MATERIAL_AVAILABILITY_BASES:
        raise ValueError(
            "check_material_availability_basis must be one of "
            f"{CHECK_MATERIAL_AVAILABILITY_BASES}"
        )
    if (
        isinstance(check_timeout_seconds, bool)
        or not isinstance(check_timeout_seconds, int)
        or check_timeout_seconds <= 0
    ):
        raise ValueError("check_timeout_seconds must be a positive integer")
    source = load_source_manifest(source_manifest_path)
    dataset_config = _required_mapping(source, "dataset")
    expected_dataset_digest = _required_string(dataset_config, "parquet_sha256")
    if _file_sha256(dataset) != expected_dataset_digest:
        raise RuntimeError("dataset digest does not match the source manifest")
    if not harness_python.is_file() or not harness_python.stat().st_mode & 0o111:
        raise RuntimeError("harness_python must be an executable file")
    rows = _selected_rows(dataset, source)
    started_at = utc_now_timestamp()
    output_dir.mkdir(parents=True)

    repository_id = _required_string(source, "repository_id")
    source_family = _required_string(source, "source_family")
    observed_at = _required_string(source, "observed_at")
    harness = _required_mapping(source, "harness")
    harness_revision = _required_string(harness, "revision")
    image_prefix = _required_string(source, "image_prefix")
    image_by_instance = {
        _required_string(item, "instance_id"): _required_string(item, "image_digest")
        for item in _required_mapping_sequence(source, "instances")
    }
    source_ref_by_instance = {
        _required_string(row, "instance_id"): _source_ref(source, row) for row in rows
    }
    reference_patch_by_source_event: dict[str, str] = {}
    for row in rows:
        instance_id = _required_string(row, "instance_id")
        source_event_id = make_source_event_id(
            repository_id,
            source_family,
            source_ref_by_instance[instance_id],
        )
        reference_patch_by_source_event[source_event_id] = _required_string(
            row, "patch"
        )
    dependency = _dependency_evidence(
        repository_id,
        reference_patch_by_source_event,
    )

    candidates: list[TaskCandidate] = []
    materials: list[PreparedCandidateMaterialRecord] = []
    frame_events: list[ObservedFrameEventRecord] = []
    for row in rows:
        instance_id = _required_string(row, "instance_id")
        source_ref = source_ref_by_instance[instance_id]
        source_event_id = make_source_event_id(
            repository_id,
            source_family,
            source_ref,
        )
        candidate_id = f"candidate-{instance_id}"
        image_ref = f"{image_prefix}{instance_id}@{image_by_instance[instance_id]}"
        check_manifest = {
            "check_implementation_sha256": _file_sha256(CHECK),
            "swe_bench_harness_revision": harness_revision,
            "bundle_destination": ".barcarolle/check_bundle",
            "image_ref": image_ref,
            "timeout_seconds": check_timeout_seconds,
        }
        reference_patch = _required_string(row, "patch")
        task_material_available_at = _canonical_time(
            _required_string(row, "created_at")
        )
        check_material_available_at = (
            observed_at
            if check_material_availability_basis == "source_observed_at"
            else task_material_available_at
        )
        patch_ref = f"reference-patches/{instance_id}.diff"
        patch_path = output_dir / patch_ref
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(reference_patch, encoding="utf-8")

        bundle_ref = f"hidden-checks/{instance_id}"
        bundle_path = output_dir / bundle_ref
        bundle_path.mkdir(parents=True)
        _write_check_spec(bundle_path / "spec.json", row)

        manifest_ref = f"check-manifests/{instance_id}.json"
        manifest_path = output_dir / manifest_ref
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            canonical_json(check_manifest) + "\n",
            encoding="utf-8",
        )
        check_manifest_digest = canonical_digest(check_manifest)
        hidden_digest = hidden_material_digest(bundle_path)
        candidates.append(
            TaskCandidate(
                candidate_id=candidate_id,
                repository_id=repository_id,
                base_commit=_required_string(row, "base_commit"),
                source_family=source_family,
                source_ref=source_ref,
                source_resolved_at=task_material_available_at,
                task_material_available_at=task_material_available_at,
                check_material_available_at=check_material_available_at,
                task_text=_required_string(row, "problem_statement"),
                solver_material_refs=(),
                dependency_cluster_id=dependency["cluster_by_source_event_id"][
                    source_event_id
                ],
                sampling_stratum=_sampling_stratum(row),
                check_manifest_digest=check_manifest_digest,
                hidden_check_bundle_digest=hidden_digest,
                resource_limits={"timeout_seconds": check_timeout_seconds},
                oracle_source=f"{source_family}_hidden_tests",
                check_type="swe_bench",
            )
        )
        command = (
            "env",
            f"BARCAROLLE_CHECK_IMPLEMENTATION_SHA256={_file_sha256(CHECK)}",
            f"BARCAROLLE_SWEBENCH_HARNESS_REVISION={harness_revision}",
            str(harness_python.absolute()),
            str(CHECK),
            "--bundle",
            ".barcarolle/check_bundle",
            "--image-ref",
            image_ref,
            "--raw-output-dir",
            str(raw_check_output_dir.resolve()),
            "--timeout-seconds",
            str(check_timeout_seconds),
        )
        materials.append(
            record_with_digest(
                PreparedCandidateMaterialRecord(
                    candidate_id=candidate_id,
                    reference_patch_ref=patch_ref,
                    reference_patch_digest=hashlib.sha256(
                        reference_patch.encode("utf-8")
                    ).hexdigest(),
                    check_command=command,
                    check_manifest_ref=manifest_ref,
                    check_manifest_digest=check_manifest_digest,
                    hidden_material_ref=bundle_ref,
                    hidden_material_digest=hidden_digest,
                    material_digest="",
                )
            )
        )
        frame_events.append(
            record_with_digest(
                ObservedFrameEventRecord(
                    source_event_id=source_event_id,
                    repository_id=repository_id,
                    source_family=source_family,
                    source_ref=source_ref,
                    observed_at=observed_at,
                    frame_event_digest="",
                )
            )
        )

    candidates_tuple = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    materials_tuple = tuple(sorted(materials, key=lambda item: item.candidate_id))
    frame_events_tuple = tuple(
        sorted(frame_events, key=lambda item: item.source_event_id)
    )
    adapter_evidence = {
        "schema_version": "swe_bench_static_adapter_evidence_v1",
        "source_manifest_digest": source["source_manifest_digest"],
        "dependency_evidence": dependency,
    }
    behavior = {
        "generator_family": "classic_dataset_import",
        "adapter_version": ADAPTER_VERSION,
        "implementation_digest": _implementation_digest(),
        "behavior_config": {
            "repository_id": repository_id,
            "dataset_revision": _required_string(dataset_config, "revision"),
            "sampling": canonical_data(source["sampling"]),
            "check_material_availability_basis": (
                check_material_availability_basis
            ),
        },
    }
    protocol = {
        "source_kind": "pinned_dataset_repository_slice",
        "target_definition": "all rows for one repository in a pinned dataset split",
        "query_semantics": {
            "dataset_repository": _required_string(dataset_config, "repository"),
            "dataset_revision": _required_string(dataset_config, "revision"),
            "repo_equals": repository_id,
        },
        "sampling_policy": canonical_data(source["sampling"]),
        "deduplication_policy": {"key": "instance_id"},
    }
    protocol_digest = canonical_digest(protocol)
    frame = {
        "frame_id": (f"swe_bench_frame_{str(source['source_manifest_digest'])[:24]}"),
        "source_protocol_digest": protocol_digest,
        "source_revision": _required_string(dataset_config, "revision"),
        "window_start": min(
            candidate.task_material_available_at for candidate in candidates_tuple
        ),
        "window_end": observed_at,
        "event_inventory_ref": "observed-frame-events.jsonl",
        "event_inventory_digest": canonical_digest(frame_events_tuple),
        "observation_authority": "producer_attested",
        "observation_receipt_digest": canonical_digest(
            {
                "source_manifest_digest": source["source_manifest_digest"],
                "dataset_sha256": expected_dataset_digest,
            }
        ),
        "known_blind_spots": [
            "frame covers the pinned dataset repository slice, not all repository issues"
        ],
        "coverage_mode": "one_source_event_per_frame_unit_v1",
    }
    finished_at = utc_now_timestamp()
    run = {
        "run_id": f"swe_bench_static_{str(source['source_manifest_digest'])[:24]}",
        "producer_id": "barcarolle_swe_bench_static_adapter",
        "authority_kind": "external_attested",
        "authority_digest": source["source_manifest_digest"],
        "started_at": started_at,
        "finished_at": finished_at,
        "input_snapshot_digest": canonical_digest(
            {
                "dataset_sha256": expected_dataset_digest,
                "source_manifest_digest": source["source_manifest_digest"],
            }
        ),
    }
    manifest = record_with_digest(
        PreparedCandidatePackageManifest(
            schema_version=PREPARED_CANDIDATE_PACKAGE_SCHEMA_VERSION,
            repository_id=repository_id,
            candidate_records_ref="candidates.jsonl",
            candidate_records_digest=canonical_digest(candidates_tuple),
            excluded_source_event_records_ref="excluded-source-events.jsonl",
            excluded_source_event_records_digest=canonical_digest(()),
            material_records_ref="materials.jsonl",
            material_records_digest=canonical_digest(materials_tuple),
            generator_behavior=behavior,
            generator_behavior_digest=canonical_digest(behavior),
            source_protocol=protocol,
            source_protocol_digest=protocol_digest,
            observed_frame=frame,
            observed_frame_digest=canonical_digest(frame),
            run=run,
            run_digest=canonical_digest(run),
            adapter_evidence_ref="adapter-evidence.jsonl",
            adapter_evidence_digest=canonical_digest(adapter_evidence),
            manifest_digest="",
        )
    )
    write_jsonl_records(output_dir / "candidates.jsonl", candidates_tuple)
    write_jsonl_records(output_dir / "excluded-source-events.jsonl", ())
    write_jsonl_records(output_dir / "materials.jsonl", materials_tuple)
    write_jsonl_records(
        output_dir / "observed-frame-events.jsonl",
        frame_events_tuple,
    )
    write_jsonl_records(
        output_dir / "adapter-evidence.jsonl",
        (adapter_evidence,),
    )
    write_jsonl_records(
        output_dir / "prepared-candidate-package.jsonl",
        (manifest,),
    )
    return {
        "repository_id": repository_id,
        "candidate_count": len(candidates_tuple),
        "dependency_cluster_count": len(
            set(dependency["cluster_by_source_event_id"].values())
        ),
        "source_manifest_digest": source["source_manifest_digest"],
        "prepared_package_digest": manifest.manifest_digest,
        "check_material_availability_basis": check_material_availability_basis,
    }


def _selected_rows(
    dataset: Path,
    source: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    import pyarrow.parquet as parquet

    repository_id = _required_string(source, "repository_id")
    expected_ids = tuple(
        _required_string(item, "instance_id")
        for item in _required_mapping_sequence(source, "instances")
    )
    rows = tuple(
        sorted(
            (
                row
                for row in parquet.read_table(dataset).to_pylist()
                if row.get("repo") == repository_id
            ),
            key=lambda row: _required_string(row, "instance_id"),
        )
    )
    observed_ids = tuple(_required_string(row, "instance_id") for row in rows)
    if observed_ids != expected_ids:
        raise RuntimeError(
            "source manifest must exactly enumerate the dataset repository slice"
        )
    return rows


def _write_check_spec(path: Path, row: Mapping[str, Any]) -> None:
    from swebench.harness.test_spec import make_test_spec

    spec = make_test_spec(dict(row))
    payload = {
        "instance_id": _required_string(row, "instance_id"),
        "repo": _required_string(row, "repo"),
        "base_commit": _required_string(row, "base_commit"),
        "version": _required_string(row, "version"),
        "FAIL_TO_PASS": list(spec.FAIL_TO_PASS),
        "PASS_TO_PASS": list(spec.PASS_TO_PASS),
        "eval_script_list": list(spec.eval_script_list),
    }
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _dependency_evidence(
    repository_id: str,
    patches: Mapping[str, str],
) -> Mapping[str, Any]:
    changed_paths_by_event = {
        source_event_id: _changed_paths(patch)
        for source_event_id, patch in sorted(patches.items())
    }
    parents = {source_event_id: source_event_id for source_event_id in patches}

    def find(item: str) -> str:
        while parents[item] != item:
            parents[item] = parents[parents[item]]
            item = parents[item]
        return item

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        lower, upper = sorted((left_root, right_root))
        parents[upper] = lower

    events_by_path: dict[str, list[str]] = defaultdict(list)
    for source_event_id, paths in changed_paths_by_event.items():
        for path in paths:
            events_by_path[path].append(source_event_id)
    for events in events_by_path.values():
        first, *remaining = sorted(events)
        for event in remaining:
            union(first, event)
    members_by_root: dict[str, list[str]] = defaultdict(list)
    for source_event_id in sorted(patches):
        members_by_root[find(source_event_id)].append(source_event_id)
    cluster_by_event: dict[str, str] = {}
    for members in members_by_root.values():
        cluster_id = "dependency_cluster_" + canonical_digest(
            {
                "protocol_version": DEPENDENCY_PROTOCOL_VERSION,
                "repository_id": repository_id,
                "source_event_ids": members,
            }
        )
        for source_event_id in members:
            cluster_by_event[source_event_id] = cluster_id
    evidence: dict[str, Any] = {
        "protocol_version": DEPENDENCY_PROTOCOL_VERSION,
        "repository_id": repository_id,
        "patch_footprints": [
            {
                "source_event_id": source_event_id,
                "reference_patch_digest": hashlib.sha256(
                    patches[source_event_id].encode("utf-8")
                ).hexdigest(),
                "changed_paths": list(changed_paths_by_event[source_event_id]),
            }
            for source_event_id in sorted(patches)
        ],
        "cluster_by_source_event_id": {
            source_event_id: cluster_by_event[source_event_id]
            for source_event_id in sorted(cluster_by_event)
        },
    }
    evidence["dependency_evidence_digest"] = canonical_digest(evidence)
    return evidence


def _changed_paths(patch: str) -> tuple[str, ...]:
    paths: set[str] = set()
    for line in patch.splitlines():
        if not line.startswith("diff --git a/"):
            continue
        _, separator, right = line.removeprefix("diff --git a/").partition(" b/")
        if not separator or not right:
            raise ValueError("reference patch has an unsupported diff header")
        path = PurePosixPath(right)
        if (
            path.is_absolute()
            or right != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts)
            or "\\" in right
        ):
            raise ValueError("reference patch path is not repository-relative")
        paths.add(right)
    if not paths:
        raise ValueError("reference patch contains no changed paths")
    return tuple(sorted(paths))


def _source_ref(
    source: Mapping[str, Any],
    row: Mapping[str, Any],
) -> str:
    dataset = _required_mapping(source, "dataset")
    return (
        f"hf://datasets/{_required_string(dataset, 'repository')}"
        f"@{_required_string(dataset, 'revision')}"
        f"/test#{_required_string(row, 'instance_id')}"
    )


def _sampling_stratum(row: Mapping[str, Any]) -> str:
    difficulty = row.get("difficulty")
    if not isinstance(difficulty, str) or not difficulty.strip():
        difficulty = "not rated"
    return f"difficulty:{difficulty.strip()}"


def _implementation_digest() -> str:
    return canonical_digest(
        {
            "adapter_version": ADAPTER_VERSION,
            "prepare_package_sha256": _file_sha256(Path(__file__).resolve()),
            "freeze_source_sha256": _file_sha256(HERE / "freeze_source.py"),
            "check_sha256": _file_sha256(CHECK),
        }
    )


def _canonical_time(value: str) -> str:
    return format_utc_timestamp(parse_utc_timestamp(value))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _required_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _required_mapping_sequence(
    value: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    items = value.get(key)
    if (
        not isinstance(items, Sequence)
        or isinstance(items, str)
        or any(not isinstance(item, Mapping) for item in items)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(items)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--harness-python", type=Path, required=True)
    parser.add_argument("--raw-check-output-dir", type=Path, required=True)
    parser.add_argument(
        "--check-material-availability-basis",
        choices=CHECK_MATERIAL_AVAILABILITY_BASES,
        required=True,
    )
    parser.add_argument("--check-timeout-seconds", type=int, default=900)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = prepare_package(
        dataset=args.dataset,
        source_manifest_path=args.source_manifest,
        output_dir=args.output_dir,
        harness_python=args.harness_python,
        raw_check_output_dir=args.raw_check_output_dir,
        check_material_availability_basis=(
            args.check_material_availability_basis
        ),
        check_timeout_seconds=args.check_timeout_seconds,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
