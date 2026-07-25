#!/usr/bin/env python3
"""Freeze one repository slice of a pinned SWE-bench dataset and its images."""

from __future__ import annotations

# The extraction environment owns these optional dependencies.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
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


SOURCE_MANIFEST_SCHEMA_VERSION = "swe_bench_static_source_v1"
DEFAULT_IMAGE_PREFIX = "ghcr.io/epoch-research/swe-bench.eval.arm64."


def freeze_source(
    *,
    dataset: Path,
    dataset_repository: str,
    dataset_revision: str,
    dataset_sha256: str,
    repository_id: str,
    source_family: str,
    harness_repository: str,
    harness_revision: str,
    observed_at: str,
    output_path: Path,
    image_prefix: str = DEFAULT_IMAGE_PREFIX,
) -> Mapping[str, Any]:
    """Write an immutable source/image manifest without pulling image layers."""
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite source manifest: {output_path}")
    actual_dataset_digest = _file_sha256(dataset)
    if actual_dataset_digest != dataset_sha256:
        raise RuntimeError("dataset digest does not match the requested revision")
    canonical_observed_at = format_utc_timestamp(parse_utc_timestamp(observed_at))
    rows = _repository_rows(dataset, repository_id)
    instances: list[Mapping[str, Any]] = []
    for row in rows:
        instance_id = _required_string(row, "instance_id")
        tagged_ref = f"{image_prefix}{instance_id}:latest"
        raw_manifest = _remote_manifest(tagged_ref)
        image_digest = "sha256:" + hashlib.sha256(raw_manifest).hexdigest()
        manifest = json.loads(raw_manifest)
        if not isinstance(manifest, Mapping):
            raise RuntimeError(f"image manifest is not an object: {instance_id}")
        layers = manifest.get("layers")
        if not isinstance(layers, list) or any(
            not isinstance(layer, Mapping)
            or isinstance(layer.get("size"), bool)
            or not isinstance(layer.get("size"), int)
            or layer["size"] < 0
            for layer in layers
        ):
            raise RuntimeError(f"image layers are invalid: {instance_id}")
        instances.append(
            {
                "instance_id": instance_id,
                "image_digest": image_digest,
                "compressed_layer_bytes": sum(layer["size"] for layer in layers),
            }
        )
    payload: dict[str, Any] = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "dataset": {
            "repository": dataset_repository,
            "revision": dataset_revision,
            "parquet_sha256": dataset_sha256,
        },
        "repository_id": repository_id,
        "source_family": source_family,
        "harness": {
            "repository": harness_repository,
            "revision": harness_revision,
        },
        "image_prefix": image_prefix,
        "observed_at": canonical_observed_at,
        "sampling": {
            "mode": "all_repository_rows",
            "order": "instance_id_ascending",
        },
        "instances": instances,
    }
    payload["source_manifest_digest"] = canonical_digest(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return payload


def load_source_manifest(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("source manifest must be an object")
    expected_fields = {
        "schema_version",
        "dataset",
        "repository_id",
        "source_family",
        "harness",
        "image_prefix",
        "observed_at",
        "sampling",
        "instances",
        "source_manifest_digest",
    }
    if set(value) != expected_fields:
        raise ValueError("source manifest fields are invalid")
    if value.get("schema_version") != SOURCE_MANIFEST_SCHEMA_VERSION:
        raise ValueError("source manifest schema is unsupported")
    digest = value.get("source_manifest_digest")
    payload = dict(value)
    payload.pop("source_manifest_digest")
    if digest != canonical_digest(payload):
        raise ValueError("source manifest digest does not match")
    observed_at = _required_string(value, "observed_at")
    if observed_at != format_utc_timestamp(parse_utc_timestamp(observed_at)):
        raise ValueError("source manifest observed_at is not canonical UTC")
    sampling = _required_mapping(value, "sampling")
    if sampling != {
        "mode": "all_repository_rows",
        "order": "instance_id_ascending",
    }:
        raise ValueError("source manifest sampling protocol is unsupported")
    instances = value.get("instances")
    if not isinstance(instances, Sequence) or isinstance(instances, str):
        raise ValueError("source manifest instances must be an array")
    instance_ids: list[str] = []
    for item in instances:
        if not isinstance(item, Mapping) or set(item) != {
            "instance_id",
            "image_digest",
            "compressed_layer_bytes",
        }:
            raise ValueError("source manifest instance fields are invalid")
        instance_id = _required_string(item, "instance_id")
        image_digest = _required_string(item, "image_digest")
        compressed = item.get("compressed_layer_bytes")
        if (
            not image_digest.startswith("sha256:")
            or len(image_digest) != 71
            or any(
                character not in "0123456789abcdef" for character in image_digest[7:]
            )
            or isinstance(compressed, bool)
            or not isinstance(compressed, int)
            or compressed < 0
        ):
            raise ValueError(f"source manifest image is invalid: {instance_id}")
        instance_ids.append(instance_id)
    if not instance_ids or instance_ids != sorted(set(instance_ids)):
        raise ValueError("source manifest instances must be unique and sorted")
    return value


def _repository_rows(
    dataset: Path, repository_id: str
) -> tuple[Mapping[str, Any], ...]:
    import pyarrow.parquet as parquet

    rows = tuple(
        row
        for row in parquet.read_table(
            dataset,
            columns=["repo", "instance_id"],
        ).to_pylist()
        if row.get("repo") == repository_id
    )
    rows = tuple(sorted(rows, key=lambda row: _required_string(row, "instance_id")))
    instance_ids = tuple(_required_string(row, "instance_id") for row in rows)
    if not instance_ids or len(instance_ids) != len(set(instance_ids)):
        raise RuntimeError(
            "dataset repository slice is empty or has duplicate instances"
        )
    return rows


def _remote_manifest(tagged_ref: str) -> bytes:
    completed = subprocess.run(
        ("docker", "buildx", "imagetools", "inspect", tagged_ref, "--raw"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise RuntimeError(f"could not resolve pinned verifier image: {tagged_ref}")
    return completed.stdout


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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-repository", required=True)
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--source-family", required=True)
    parser.add_argument("--harness-repository", required=True)
    parser.add_argument("--harness-revision", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-prefix", default=DEFAULT_IMAGE_PREFIX)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = freeze_source(
        dataset=args.dataset,
        dataset_repository=args.dataset_repository,
        dataset_revision=args.dataset_revision,
        dataset_sha256=args.dataset_sha256,
        repository_id=args.repository_id,
        source_family=args.source_family,
        harness_repository=args.harness_repository,
        harness_revision=args.harness_revision,
        observed_at=args.observed_at,
        output_path=args.output,
        image_prefix=args.image_prefix,
    )
    print(
        json.dumps(
            {
                "repository_id": summary["repository_id"],
                "instance_count": len(summary["instances"]),
                "source_manifest_digest": summary["source_manifest_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
