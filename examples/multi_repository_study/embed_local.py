#!/usr/bin/env python3
"""Create the ignored, pinned local embedding input for the semantic replay."""

from __future__ import annotations

# This script runs in an explicit optional-dependency environment.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    load_dataset_tasks,
)
from examples.multi_repository_study.semantic import (  # noqa: E402
    DEFAULT_PLAN,
    load_semantic_plan,
)


def build_embedding_artifact(
    task_ids: Sequence[str],
    texts: Sequence[str],
    vectors: Sequence[Sequence[float]],
    *,
    plan: Mapping[str, object],
    dataset_sha256: str,
    package_version: str,
) -> Mapping[str, Any]:
    if (
        not task_ids
        or len(task_ids) != len(texts)
        or len(task_ids) != len(vectors)
        or len(task_ids) != len(set(task_ids))
    ):
        raise ValueError("embedding rows must align one-to-one")
    embedding_plan = _mapping(plan, "embedding")
    if package_version != _required_string(
        embedding_plan,
        "sentence_transformers_version",
    ):
        raise ValueError("sentence-transformers version does not match plan")
    normalized_vectors = tuple(
        tuple(float(value) for value in vector) for vector in vectors
    )
    dimensions = len(normalized_vectors[0])
    if dimensions == 0 or any(len(vector) != dimensions for vector in normalized_vectors):
        raise ValueError("embedding vectors have inconsistent dimensions")
    result: dict[str, Any] = {
        "schema_version": "barcarolle_local_task_embeddings_v1",
        "semantic_plan_digest": plan.get("semantic_plan_digest"),
        "dataset_sha256": dataset_sha256,
        "model": {
            "model_id": embedding_plan.get("model_id"),
            "model_revision": embedding_plan.get("model_revision"),
            "sentence_transformers_version": package_version,
            "device": embedding_plan.get("device"),
        },
        "input": {
            "field": embedding_plan.get("input_field"),
            "task_count": len(task_ids),
            "task_text_digest": canonical_digest(
                tuple(zip(task_ids, texts, strict=True))
            ),
        },
        "dimensions": dimensions,
        "items": tuple(
            {
                "task_id": task_id,
                "embedding": vector,
            }
            for task_id, vector in zip(
                task_ids,
                normalized_vectors,
                strict=True,
            )
        ),
    }
    result["embedding_artifact_digest"] = canonical_digest(result)
    return result


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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--model-snapshot", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite embeddings: {args.output}")
    if _file_sha256(args.dataset) != args.dataset_sha256:
        raise RuntimeError("dataset digest does not match command authority")
    plan = load_semantic_plan(args.plan)
    embedding_plan = _mapping(plan, "embedding")
    snapshot = args.model_snapshot.resolve()
    if (
        not snapshot.is_dir()
        or snapshot.name != _required_string(embedding_plan, "model_revision")
    ):
        raise ValueError("local model snapshot does not match semantic plan")
    package_version = version("sentence-transformers")
    if package_version != _required_string(
        embedding_plan,
        "sentence_transformers_version",
    ):
        raise RuntimeError("sentence-transformers package version does not match plan")

    from sentence_transformers import SentenceTransformer

    tasks = load_dataset_tasks(args.dataset)
    model = SentenceTransformer(
        str(snapshot),
        device="cpu",
        local_files_only=True,
    )
    texts = tuple(task.problem_statement for task in tasks)
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    artifact = build_embedding_artifact(
        tuple(task.instance_id for task in tasks),
        texts,
        vectors,
        plan=plan,
        dataset_sha256=args.dataset_sha256,
        package_version=package_version,
    )
    args.output.write_text(canonical_json(artifact) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "dimensions": artifact["dimensions"],
                "embedding_artifact_digest": artifact[
                    "embedding_artifact_digest"
                ],
                "task_count": len(tasks),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
