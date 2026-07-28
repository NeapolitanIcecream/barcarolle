#!/usr/bin/env python3
"""Build and evaluate the frozen Multi-SWE semantic Selector."""

from __future__ import annotations

# The embedding command runs in an explicit optional-dependency environment.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from importlib.metadata import version
import json
from math import fsum, sqrt
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "selector-plan.json"
DEFAULT_CONTENT_MANIFEST = HERE / "evidence" / "task-content-manifest.json"
DEFAULT_EMBEDDING_MANIFEST = HERE / "evidence" / "embedding-manifest.json"
PLAN_SCHEMA = "barcarolle_multi_swe_selector_plan_v1"
CONTENT_MANIFEST_SCHEMA = "barcarolle_multi_swe_task_content_manifest_v1"
EMBEDDING_SCHEMA = "barcarolle_multi_swe_task_embeddings_v1"
EMBEDDING_MANIFEST_SCHEMA = "barcarolle_multi_swe_embedding_manifest_v1"


def load_selector_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Multi-SWE Selector plan schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "selector_plan_digest"
        }
    )
    if payload.get("selector_plan_digest") != expected:
        raise ValueError("Multi-SWE Selector plan digest does not match")
    candidate = _mapping(payload, "candidate")
    if (
        candidate.get("algorithm_id") != "ALG-012"
        or candidate.get("selector_id")
        != "minimax_temporal_semantic_herding"
        or candidate.get("fitting") != "none"
    ):
        raise ValueError("Multi-SWE Selector candidate changed")
    return payload


def load_content_manifest(
    path: Path = DEFAULT_CONTENT_MANIFEST,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != CONTENT_MANIFEST_SCHEMA:
        raise ValueError("Task content manifest schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "content_manifest_digest"
        }
    )
    if payload.get("content_manifest_digest") != expected:
        raise ValueError("Task content manifest digest does not match")
    return payload


def load_embedding_manifest(
    path: Path = DEFAULT_EMBEDDING_MANIFEST,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != EMBEDDING_MANIFEST_SCHEMA:
        raise ValueError("embedding manifest schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "embedding_manifest_digest"
        }
    )
    if payload.get("embedding_manifest_digest") != expected:
        raise ValueError("embedding manifest digest does not match")
    return payload


def load_task_content(
    path: Path,
    manifest: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = _load_jsonl(path)
    if len(rows) != _positive_integer(manifest, "task_count"):
        raise ValueError("Task content count does not match manifest")
    if canonical_digest(rows) != manifest.get("projection_digest"):
        raise ValueError("Task content projection digest does not match")
    identities = tuple(_required_string(row, "instance_id") for row in rows)
    if len(identities) != len(set(identities)) or identities != tuple(
        sorted(identities)
    ):
        raise ValueError("Task content identities must be unique and sorted")
    text_digest = canonical_digest(
        tuple(
            (
                _required_string(row, "instance_id"),
                _required_string(row, "text"),
            )
            for row in rows
        )
    )
    if text_digest != manifest.get("task_text_digest"):
        raise ValueError("Task content text digest does not match")
    if any(row.get("has_content") is not True for row in rows):
        raise ValueError("Task content contains an empty projection")
    return rows


def build_embedding_artifact(
    task_ids: Sequence[str],
    texts: Sequence[str],
    vectors: Sequence[Sequence[float]],
    *,
    plan: Mapping[str, object],
    content_manifest: Mapping[str, object],
    package_version: str,
) -> Mapping[str, Any]:
    if (
        not task_ids
        or len(task_ids) != len(texts)
        or len(task_ids) != len(vectors)
        or len(task_ids) != len(set(task_ids))
    ):
        raise ValueError("embedding inputs must align one-to-one")
    embedding_plan = _mapping(plan, "embedding")
    if package_version != _required_string(
        embedding_plan,
        "sentence_transformers_version",
    ):
        raise ValueError("sentence-transformers version does not match plan")
    normalized_vectors = tuple(
        tuple(_number(value, "embedding value") for value in vector)
        for vector in vectors
    )
    dimensions = len(normalized_vectors[0])
    if dimensions == 0 or any(
        len(vector) != dimensions for vector in normalized_vectors
    ):
        raise ValueError("embedding vectors have inconsistent dimensions")
    for vector in normalized_vectors:
        norm = sqrt(fsum(value * value for value in vector))
        if abs(norm - 1.0) > 1e-4:
            raise ValueError("embedding vectors must be L2 normalized")
    if canonical_digest(tuple(zip(task_ids, texts, strict=True))) != (
        content_manifest.get("task_text_digest")
    ):
        raise ValueError("embedding text does not match content manifest")

    vector_values_digest = canonical_digest(
        tuple(zip(task_ids, normalized_vectors, strict=True))
    )
    result: dict[str, Any] = {
        "schema_version": EMBEDDING_SCHEMA,
        "selector_plan_digest": plan.get("selector_plan_digest"),
        "content_manifest_digest": content_manifest.get(
            "content_manifest_digest"
        ),
        "task_text_digest": content_manifest.get("task_text_digest"),
        "model": {
            "model_id": embedding_plan.get("model_id"),
            "model_revision": embedding_plan.get("model_revision"),
            "sentence_transformers_version": package_version,
            "device": embedding_plan.get("device"),
            "normalization": embedding_plan.get("normalization"),
        },
        "task_count": len(task_ids),
        "dimensions": dimensions,
        "vector_values_digest": vector_values_digest,
        "items": tuple(
            {"task_id": task_id, "embedding": vector}
            for task_id, vector in zip(
                task_ids,
                normalized_vectors,
                strict=True,
            )
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
        },
    }
    result["embedding_artifact_digest"] = canonical_digest(result)
    return result


def load_embedding_artifact(
    path: Path,
    plan: Mapping[str, object],
    content_manifest: Mapping[str, object],
    task_ids: Sequence[str],
) -> tuple[Mapping[str, tuple[float, ...]], Mapping[str, Any]]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("embedding_artifact_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("embedding artifact digest does not match")
    if payload.get("schema_version") != EMBEDDING_SCHEMA:
        raise ValueError("embedding artifact schema is unsupported")
    if payload.get("selector_plan_digest") != plan.get("selector_plan_digest"):
        raise ValueError("embedding artifact does not bind Selector plan")
    if payload.get("content_manifest_digest") != content_manifest.get(
        "content_manifest_digest"
    ):
        raise ValueError("embedding artifact does not bind Task content")
    embedding_plan = _mapping(plan, "embedding")
    model = _mapping(payload, "model")
    for key in (
        "model_id",
        "model_revision",
        "sentence_transformers_version",
        "normalization",
    ):
        if model.get(key) != embedding_plan.get(key):
            raise ValueError(f"embedding artifact does not bind {key}")
    dimensions = _positive_integer(payload, "dimensions")
    items = _mapping_sequence(payload, "items")
    observed_ids = tuple(_required_string(item, "task_id") for item in items)
    if observed_ids != tuple(task_ids):
        raise ValueError("embedding artifact does not match Task order")
    vectors = {}
    for item in items:
        vector = item.get("embedding")
        if (
            not isinstance(vector, Sequence)
            or isinstance(vector, str)
            or len(vector) != dimensions
        ):
            raise ValueError("embedding vector is malformed")
        normalized = tuple(_number(value, "embedding value") for value in vector)
        norm = sqrt(fsum(value * value for value in normalized))
        if abs(norm - 1.0) > 1e-4:
            raise ValueError("embedding vector is not L2 normalized")
        vectors[_required_string(item, "task_id")] = normalized
    expected_vector_digest = canonical_digest(
        tuple((task_id, vectors[task_id]) for task_id in task_ids)
    )
    if payload.get("vector_values_digest") != expected_vector_digest:
        raise ValueError("embedding vector values digest does not match")
    manifest = {key: value for key, value in payload.items() if key != "items"}
    manifest["embedding_artifact_digest"] = digest
    return vectors, manifest


def _embedding_summary(
    artifact: Mapping[str, object],
) -> Mapping[str, object]:
    return {
        "schema_version": "barcarolle_multi_swe_embedding_summary_v1",
        "selector_plan_digest": artifact.get("selector_plan_digest"),
        "content_manifest_digest": artifact.get("content_manifest_digest"),
        "task_text_digest": artifact.get("task_text_digest"),
        "embedding_artifact_digest": artifact.get("embedding_artifact_digest"),
        "vector_values_digest": artifact.get("vector_values_digest"),
        "task_count": artifact.get("task_count"),
        "dimensions": artifact.get("dimensions"),
        "model": artifact.get("model"),
        "resource_use": artifact.get("resource_use"),
    }


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _load_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                raise ValueError(f"JSONL row {line_number} must be an object")
            rows.append(payload)
    return tuple(rows)


def _mapping(payload: Mapping[str, object], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, Mapping) for item in value)
    ):
        raise ValueError(f"{key} must be an object sequence")
    return tuple(value)


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _positive_integer(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be numeric")
    normalized = float(value)
    if not (-float("inf") < normalized < float("inf")):
        raise ValueError(f"{label} must be finite")
    return normalized


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--content-manifest",
        type=Path,
        default=DEFAULT_CONTENT_MANIFEST,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    embed = subparsers.add_parser("embed", help="build the ignored local vectors")
    embed.add_argument("--task-content", type=Path, required=True)
    embed.add_argument("--model-snapshot", type=Path, required=True)
    embed.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command != "embed":
        raise AssertionError(arguments.command)
    if arguments.output.exists():
        raise FileExistsError(
            f"refusing to overwrite embedding output: {arguments.output}"
        )
    plan = load_selector_plan(arguments.plan)
    content_manifest = load_content_manifest(arguments.content_manifest)
    rows = load_task_content(arguments.task_content, content_manifest)
    embedding_plan = _mapping(plan, "embedding")
    snapshot = arguments.model_snapshot.resolve()
    if (
        not snapshot.is_dir()
        or snapshot.name != _required_string(
            embedding_plan,
            "model_revision",
        )
    ):
        raise ValueError("local model snapshot does not match plan")
    package_version = version("sentence-transformers")
    if package_version != _required_string(
        embedding_plan,
        "sentence_transformers_version",
    ):
        raise RuntimeError("sentence-transformers version does not match plan")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        str(snapshot),
        device=_required_string(embedding_plan, "device"),
        local_files_only=True,
    )
    task_ids = tuple(_required_string(row, "instance_id") for row in rows)
    texts = tuple(_required_string(row, "text") for row in rows)
    raw_vectors = model.encode(
        texts,
        batch_size=_positive_integer(embedding_plan, "batch_size"),
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    artifact = build_embedding_artifact(
        task_ids,
        texts,
        raw_vectors,
        plan=plan,
        content_manifest=content_manifest,
        package_version=package_version,
    )
    arguments.output.write_text(
        canonical_json(artifact) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_embedding_summary(artifact), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
