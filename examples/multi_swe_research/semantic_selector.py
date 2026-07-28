#!/usr/bin/env python3
"""Build and evaluate the frozen Multi-SWE semantic Selector."""

from __future__ import annotations

# The embedding command runs in an explicit optional-dependency environment.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
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
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_repository_study.semantic import SimilarityIndex  # noqa: E402


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "selector-plan.json"
DEFAULT_CONTENT_MANIFEST = HERE / "evidence" / "task-content-manifest.json"
DEFAULT_EMBEDDING_MANIFEST = HERE / "evidence" / "embedding-manifest.json"
PLAN_SCHEMA = "barcarolle_multi_swe_selector_plan_v1"
CONTENT_MANIFEST_SCHEMA = "barcarolle_multi_swe_task_content_manifest_v1"
EMBEDDING_SCHEMA = "barcarolle_multi_swe_task_embeddings_v1"
EMBEDDING_MANIFEST_SCHEMA = "barcarolle_multi_swe_embedding_manifest_v1"
TASK_SPACE_SCHEMA = "barcarolle_multi_swe_task_space_results_v1"
OUTCOME_SCHEMA = "barcarolle_multi_swe_semantic_outcome_results_v1"

SELECTOR_IDS = (
    "full_history",
    "recency",
    "stationary_semantic_herding",
    "alg_007_centroid_recent_15",
    "minimax_temporal_semantic_herding",
)


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


def select_minimax_temporal_semantic_herding(
    history_ids: Sequence[str],
    index: SimilarityIndex,
    *,
    horizon: int,
    budget: int,
) -> tuple[str, ...]:
    """Greedily hedge between full-history and recent semantic means."""
    task_ids = _selection_input(history_ids, budget)
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("semantic horizon must be positive")
    recent = task_ids[-min(horizon, len(task_ids)) :]
    full_scores, full_constant = _target_kernel_moments(task_ids, task_ids, index)
    recent_scores, recent_constant = _target_kernel_moments(
        task_ids,
        recent,
        index,
    )
    selected: list[str] = []
    pair_sum = 0.0
    full_sum = 0.0
    recent_sum = 0.0
    position = {task_id: offset for offset, task_id in enumerate(task_ids)}
    for count in range(1, budget + 1):
        candidates = []
        for task_id in task_ids:
            if task_id in selected:
                continue
            cross = fsum(index.similarity(task_id, item) for item in selected)
            candidate_pair = (
                pair_sum + 2.0 * cross + index.similarity(task_id, task_id)
            )
            full_distance = _kernel_mean_distance(
                candidate_pair,
                full_sum + full_scores[task_id],
                count,
                full_constant,
            )
            recent_distance = _kernel_mean_distance(
                candidate_pair,
                recent_sum + recent_scores[task_id],
                count,
                recent_constant,
            )
            candidates.append(
                (
                    max(full_distance, recent_distance),
                    position[task_id],
                    task_id,
                    candidate_pair,
                )
            )
        _, _, chosen, pair_sum = min(candidates)
        selected.append(chosen)
        full_sum += full_scores[chosen]
        recent_sum += recent_scores[chosen]
    return tuple(selected)


def select_kernel_mean_herding(
    history_ids: Sequence[str],
    target_ids: Sequence[str],
    index: SimilarityIndex,
    *,
    budget: int,
    swap_pass_limit: int,
) -> tuple[str, ...]:
    """Match one frozen kernel mean, with optional ALG-007 swaps."""
    task_ids = _selection_input(history_ids, budget)
    target = tuple(target_ids)
    if (
        not target
        or not set(target) <= set(task_ids)
        or isinstance(swap_pass_limit, bool)
        or not isinstance(swap_pass_limit, int)
        or swap_pass_limit < 0
    ):
        raise ValueError("kernel target or swap limit is invalid")
    target_scores, target_constant = _target_kernel_moments(
        task_ids,
        target,
        index,
    )
    selected: list[str] = []
    pair_sum = 0.0
    target_sum = 0.0
    position = {task_id: offset for offset, task_id in enumerate(task_ids)}
    for count in range(1, budget + 1):
        candidates = []
        for task_id in task_ids:
            if task_id in selected:
                continue
            cross = fsum(index.similarity(task_id, item) for item in selected)
            candidate_pair = (
                pair_sum + 2.0 * cross + index.similarity(task_id, task_id)
            )
            distance = _kernel_mean_distance(
                candidate_pair,
                target_sum + target_scores[task_id],
                count,
                target_constant,
            )
            candidates.append(
                (distance, position[task_id], task_id, candidate_pair)
            )
        _, _, chosen, pair_sum = min(candidates)
        selected.append(chosen)
        target_sum += target_scores[chosen]

    current = _kernel_mean_distance(
        pair_sum,
        target_sum,
        budget,
        target_constant,
    )
    for _ in range(swap_pass_limit):
        selected_set = set(selected)
        best_swap: tuple[float, int, int, str, float, float] | None = None
        for selected_position, old_id in enumerate(selected):
            remaining = tuple(
                item for item in selected if item != old_id
            )
            removed_pair = (
                pair_sum
                - 2.0
                * fsum(index.similarity(old_id, item) for item in selected)
                + index.similarity(old_id, old_id)
            )
            removed_target = target_sum - target_scores[old_id]
            for new_id in task_ids:
                if new_id in selected_set:
                    continue
                candidate_pair = (
                    removed_pair
                    + 2.0
                    * fsum(
                        index.similarity(new_id, item) for item in remaining
                    )
                    + index.similarity(new_id, new_id)
                )
                candidate_target = removed_target + target_scores[new_id]
                value = _kernel_mean_distance(
                    candidate_pair,
                    candidate_target,
                    budget,
                    target_constant,
                )
                candidate = (
                    value,
                    selected_position,
                    position[new_id],
                    new_id,
                    candidate_pair,
                    candidate_target,
                )
                if value < current - 1e-12 and (
                    best_swap is None or candidate[:3] < best_swap[:3]
                ):
                    best_swap = candidate
        if best_swap is None:
            break
        current, selected_position, _, new_id, pair_sum, target_sum = best_swap
        selected[selected_position] = new_id
    return tuple(selected)


def kernel_mmd_squared(
    left_ids: Sequence[str],
    right_ids: Sequence[str],
    index: SimilarityIndex,
) -> float:
    left = tuple(left_ids)
    right = tuple(right_ids)
    if not left or not right:
        raise ValueError("kernel MMD requires two nonempty samples")
    left_term = fsum(
        index.similarity(first, second)
        for first in left
        for second in left
    ) / (len(left) * len(left))
    right_term = fsum(
        index.similarity(first, second)
        for first in right
        for second in right
    ) / (len(right) * len(right))
    cross = fsum(
        index.similarity(first, second)
        for first in left
        for second in right
    ) / (len(left) * len(right))
    return max(0.0, left_term + right_term - 2.0 * cross)


def run_task_space_replay(
    tasks: Sequence[TaskMetadata],
    vectors: Mapping[str, tuple[float, ...]],
    plan: Mapping[str, object],
    embedding_manifest: Mapping[str, object],
) -> Mapping[str, Any]:
    """Materialize the frozen outcome-free memberships and task-space audit."""
    task_ids = tuple(task.instance_id for task in tasks)
    if set(vectors) != set(task_ids):
        raise ValueError("semantic vectors must cover the exact Task universe")
    rolling = _mapping(plan, "rolling_origin")
    minimum_history = _positive_integer(
        rolling,
        "minimum_initial_history_tasks",
    )
    budget = _positive_integer(rolling, "selection_budget_tasks")
    horizons = (
        _positive_integer(rolling, "primary_future_tasks"),
        _positive_integer(rolling, "sensitivity_future_tasks"),
    )
    repository_sets = {
        horizons[0]: _string_tuple(
            rolling.get("primary_repository_ids"),
            "primary repositories",
        ),
        horizons[1]: _string_tuple(
            rolling.get("sensitivity_common_repository_ids"),
            "sensitivity repositories",
        ),
    }
    deep_sets = {
        horizons[0]: _string_tuple(
            rolling.get("primary_deep_repository_ids"),
            "primary deep repositories",
        ),
        horizons[1]: _string_tuple(
            rolling.get("sensitivity_deep_repository_ids"),
            "sensitivity deep repositories",
        ),
    }
    index = SimilarityIndex(vectors)
    horizon_results = {}
    for horizon in horizons:
        origins_by_repository = build_repository_origins(
            tasks,
            minimum_initial_history_tasks=minimum_history,
            future_block_tasks=horizon,
        )
        repositories = repository_sets[horizon]
        if any(not origins_by_repository.get(repository) for repository in repositories):
            raise ValueError("planned repository has no complete Origin")
        memberships = _materialize_semantic_memberships(
            origins_by_repository,
            repositories,
            index,
            horizon=horizon,
            budget=budget,
        )
        rows = _feature_contrast_rows(
            origins_by_repository,
            repositories,
            memberships,
            index,
        )
        summaries = {
            selector_id: _feature_summary(
                selector_rows,
                repositories,
                deep_sets[horizon],
            )
            for selector_id, selector_rows in rows.items()
        }
        random_report = _random_feature_calibration(
            origins_by_repository,
            repositories,
            index,
            budget=budget,
            draws=_positive_integer(_mapping(plan, "diagnostics"), "random_draws"),
            seed=_positive_integer(_mapping(plan, "diagnostics"), "random_seed")
            + horizon,
            candidate_difference=float(
                summaries["minimax_temporal_semantic_herding"][
                    "wide"
                ]["macro_repository_difference"]
            ),
        )
        horizon_results[str(horizon)] = {
            "origin_counts": {
                repository: len(origins_by_repository[repository])
                for repository in repositories
            },
            "repository_ids": repositories,
            "deep_repository_ids": deep_sets[horizon],
            "memberships": memberships,
            "membership_digests": {
                selector_id: canonical_digest(tuple(sorted(values.items())))
                for selector_id, values in memberships.items()
            },
            "summaries": summaries,
            "random_calibration": random_report,
        }

    task_gate = _task_space_gate(horizon_results, plan)
    result: dict[str, Any] = {
        "schema_version": TASK_SPACE_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": "outcome_free_task_space_mechanism_audit",
        "selector_plan_digest": plan.get("selector_plan_digest"),
        "embedding_manifest_digest": embedding_manifest.get(
            "embedding_manifest_digest"
        ),
        "embedding_artifact_digest": embedding_manifest.get(
            "embedding_artifact_digest"
        ),
        "task_count": len(tasks),
        "horizons": horizon_results,
        "task_space_gate": task_gate,
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
        },
        "claim_boundary": (
            "This outcome-free replay tests semantic distribution tracking. "
            "It cannot establish Agent-outcome validity."
        ),
    }
    result["task_space_results_digest"] = canonical_digest(result)
    return result


def load_task_space_results(
    path: Path,
    plan: Mapping[str, object],
    embedding_manifest: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("task_space_results_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("task-space result digest does not match")
    payload["task_space_results_digest"] = digest
    if payload.get("schema_version") != TASK_SPACE_SCHEMA:
        raise ValueError("task-space result schema is unsupported")
    if payload.get("selector_plan_digest") != plan.get("selector_plan_digest"):
        raise ValueError("task-space result does not bind Selector plan")
    if payload.get("embedding_manifest_digest") != embedding_manifest.get(
        "embedding_manifest_digest"
    ):
        raise ValueError("task-space result does not bind embeddings")
    return payload


def load_public_outcomes(
    panel_path: Path,
    resolved_path: Path,
    task_ids: Sequence[str],
    plan: Mapping[str, object],
) -> tuple[
    Mapping[str, Mapping[str, int]],
    tuple[Mapping[str, str], ...],
    Mapping[str, Any],
]:
    panel = dict(_load_mapping(panel_path))
    panel_digest = panel.get("panel_digest")
    expected_panel = canonical_digest(
        {key: value for key, value in panel.items() if key != "panel_digest"}
    )
    if panel_digest != expected_panel or panel_digest != _mapping(
        plan, "source"
    ).get("panel_digest"):
        raise ValueError("public outcome panel identity changed")
    configurations = _mapping_sequence(panel, "configurations")
    configuration_metadata = tuple(
        {
            "configuration_id": _required_string(row, "configuration_id"),
            "harness_family": _required_string(row, "harness_family"),
            "model_family": _required_string(row, "model_family"),
        }
        for row in configurations
    )
    configuration_ids = tuple(
        row["configuration_id"] for row in configuration_metadata
    )
    if (
        len(configuration_ids) != 36
        or len(configuration_ids) != len(set(configuration_ids))
    ):
        raise ValueError("public outcome configurations changed")
    expected_tasks = set(task_ids)
    resolved = _load_jsonl(resolved_path)
    if canonical_digest(resolved) != panel.get("resolved_outcome_digest"):
        raise ValueError("sparse public outcomes changed")
    positive: dict[str, set[str]] = {
        configuration_id: set() for configuration_id in configuration_ids
    }
    seen: set[tuple[str, str]] = set()
    for row in resolved:
        configuration_id = _required_string(row, "configuration_id")
        instance_id = _required_string(row, "instance_id")
        if (
            configuration_id not in positive
            or instance_id not in expected_tasks
            or row.get("resolved") is not True
        ):
            raise ValueError("sparse public outcome identity changed")
        cell = (configuration_id, instance_id)
        if cell in seen:
            raise ValueError("sparse public outcome cell is duplicated")
        seen.add(cell)
        positive[configuration_id].add(instance_id)
    outcomes = {
        configuration_id: {
            task_id: int(task_id in positive[configuration_id])
            for task_id in task_ids
        }
        for configuration_id in configuration_ids
    }
    diagnostics = {
        "panel_digest": panel_digest,
        "resolved_outcome_digest": panel.get("resolved_outcome_digest"),
        "resolved_cell_count": len(resolved),
        "configuration_count": len(configuration_ids),
        "task_count": len(task_ids),
    }
    return outcomes, configuration_metadata, diagnostics


def outcome_pass_rate_mae(
    selected_ids: Sequence[str],
    future_ids: Sequence[str],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
) -> float:
    selected = tuple(selected_ids)
    future = tuple(future_ids)
    configurations = tuple(configuration_ids)
    if not selected or not future or not configurations:
        raise ValueError("outcome loss requires nonempty inputs")
    losses = []
    required = set((*selected, *future))
    for configuration_id in configurations:
        outcomes = outcomes_by_configuration.get(configuration_id)
        if outcomes is None or set(outcomes) < required:
            raise ValueError("outcome panel does not cover loss inputs")
        selected_rate = fsum(outcomes[task_id] for task_id in selected) / len(
            selected
        )
        future_rate = fsum(outcomes[task_id] for task_id in future) / len(
            future
        )
        losses.append(abs(selected_rate - future_rate))
    return _mean(tuple(losses))


def run_outcome_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_metadata: Sequence[Mapping[str, str]],
    task_space_results: Mapping[str, object],
    plan: Mapping[str, object],
    outcome_diagnostics: Mapping[str, object],
) -> Mapping[str, Any]:
    """Join the frozen memberships to the one opened Multi-SWE panel."""
    configuration_ids = tuple(
        _required_string(row, "configuration_id")
        for row in configuration_metadata
    )
    if set(configuration_ids) != set(outcomes_by_configuration):
        raise ValueError("configuration metadata and outcomes differ")
    rolling = _mapping(plan, "rolling_origin")
    minimum_history = _positive_integer(
        rolling,
        "minimum_initial_history_tasks",
    )
    budget = _positive_integer(rolling, "selection_budget_tasks")
    primary_horizon = _positive_integer(rolling, "primary_future_tasks")
    sensitivity_horizon = _positive_integer(
        rolling,
        "sensitivity_future_tasks",
    )
    deep_sets = {
        primary_horizon: _string_tuple(
            rolling.get("primary_deep_repository_ids"),
            "primary deep repositories",
        ),
        sensitivity_horizon: _string_tuple(
            rolling.get("sensitivity_deep_repository_ids"),
            "sensitivity deep repositories",
        ),
    }
    task_space_horizons = _mapping(task_space_results, "horizons")
    horizon_results = {}
    for horizon in (primary_horizon, sensitivity_horizon):
        origins_by_repository = build_repository_origins(
            tasks,
            minimum_initial_history_tasks=minimum_history,
            future_block_tasks=horizon,
        )
        task_horizon = _mapping(task_space_horizons, str(horizon))
        repository_ids = _string_tuple(
            task_horizon.get("repository_ids"),
            "task-space repositories",
        )
        memberships = _validated_memberships(
            task_horizon,
            origins_by_repository,
            repository_ids,
            budget,
        )
        rows = _outcome_contrast_rows(
            origins_by_repository,
            repository_ids,
            memberships,
            outcomes_by_configuration,
            configuration_ids,
        )
        summaries = {
            selector_id: _feature_summary(
                selector_rows,
                repository_ids,
                deep_sets[horizon],
            )
            for selector_id, selector_rows in rows.items()
        }
        candidate_rows = rows["minimax_temporal_semantic_herding"]
        transfer = _outcome_transfer_audits(
            origins_by_repository,
            repository_ids,
            memberships["minimax_temporal_semantic_herding"],
            memberships["full_history"],
            outcomes_by_configuration,
            configuration_metadata,
            plan,
        )
        random_report = _random_outcome_calibration(
            origins_by_repository,
            repository_ids,
            outcomes_by_configuration,
            configuration_ids,
            budget=budget,
            draws=_positive_integer(_mapping(plan, "diagnostics"), "random_draws"),
            seed=_positive_integer(_mapping(plan, "diagnostics"), "random_seed")
            + 100 + horizon,
            candidate_difference=float(
                summaries["minimax_temporal_semantic_herding"][
                    "wide"
                ]["macro_repository_difference"]
            ),
        )
        interval = _repository_bootstrap_interval(
            candidate_rows,
            repository_ids,
            resamples=_positive_integer(
                _mapping(plan, "diagnostics"),
                "bootstrap_resamples",
            ),
            seed=_positive_integer(
                _mapping(plan, "diagnostics"),
                "bootstrap_seed",
            )
            + horizon,
        )
        horizon_results[str(horizon)] = {
            "repository_ids": repository_ids,
            "deep_repository_ids": deep_sets[horizon],
            "summaries": summaries,
            "random_calibration": random_report,
            "transfer_audits": transfer,
            "repository_bootstrap_interval_95": interval,
        }

    outcome_gate = _outcome_gate(horizon_results, task_space_results, plan)
    result: dict[str, Any] = {
        "schema_version": OUTCOME_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": "opened_multi_swe_development_outcomes",
        "selector_plan_digest": plan.get("selector_plan_digest"),
        "task_space_results_digest": task_space_results.get(
            "task_space_results_digest"
        ),
        "task_space_gate": task_space_results.get("task_space_gate"),
        "outcome_diagnostics": outcome_diagnostics,
        "horizons": horizon_results,
        "outcome_gate": outcome_gate,
        "nomination": {
            "nominated": bool(
                outcome_gate["all_requirements_met"]
                and _mapping(task_space_results, "task_space_gate").get(
                    "all_requirements_met"
                )
            ),
            "selector_id": (
                "minimax_temporal_semantic_herding"
                if outcome_gate["all_requirements_met"]
                and _mapping(task_space_results, "task_space_gate").get(
                    "all_requirements_met"
                )
                else None
            ),
            "independent_confirmation_authorized": False,
            "production_promotion_allowed": False,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
        },
        "claim_boundary": (
            "Multi-SWE outcomes were open before the frozen study. Results "
            "can reject or nominate a mechanism, but cannot confirm validity."
        ),
    }
    result["outcome_results_digest"] = canonical_digest(result)
    return result


def _validated_memberships(
    task_horizon: Mapping[str, object],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    budget: int,
) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    payload = _mapping(task_horizon, "memberships")
    digests = _mapping(task_horizon, "membership_digests")
    expected_origins = {
        origin.origin_id: origin
        for repository_id in repository_ids
        for origin in origins_by_repository[repository_id]
    }
    result = {}
    for selector_id in SELECTOR_IDS:
        raw = _mapping(payload, selector_id)
        memberships = {
            origin_id: _string_tuple(value, f"{selector_id} membership")
            for origin_id, value in raw.items()
        }
        if set(memberships) != set(expected_origins):
            raise ValueError("task-space membership Origin coverage changed")
        for origin_id, selected in memberships.items():
            history_ids = {
                task.instance_id for task in expected_origins[origin_id].history
            }
            if not set(selected) <= history_ids:
                raise ValueError("task-space membership leaves Origin history")
            expected_size = (
                len(history_ids) if selector_id == "full_history" else budget
            )
            if len(selected) != expected_size:
                raise ValueError("task-space membership size changed")
        if canonical_digest(tuple(sorted(memberships.items()))) != digests.get(
            selector_id
        ):
            raise ValueError("task-space membership digest changed")
        result[selector_id] = memberships
    return result


def _outcome_contrast_rows(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    memberships: Mapping[str, Mapping[str, Sequence[str]]],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    rows: dict[str, list[Mapping[str, object]]] = {
        selector_id: [] for selector_id in memberships
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline = outcome_pass_rate_mae(
                memberships["full_history"][origin.origin_id],
                future_ids,
                outcomes_by_configuration,
                configuration_ids,
            )
            for selector_id, selections in memberships.items():
                loss = outcome_pass_rate_mae(
                    selections[origin.origin_id],
                    future_ids,
                    outcomes_by_configuration,
                    configuration_ids,
                )
                rows[selector_id].append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "loss": loss,
                        "baseline_loss": baseline,
                        "difference": loss - baseline,
                    }
                )
    return {
        selector_id: tuple(selector_rows)
        for selector_id, selector_rows in rows.items()
    }


def _outcome_transfer_audits(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    selected: Mapping[str, Sequence[str]],
    baseline: Mapping[str, Sequence[str]],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_metadata: Sequence[Mapping[str, str]],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    metadata_by_id = {
        _required_string(row, "configuration_id"): row
        for row in configuration_metadata
    }
    model_groups: dict[str, list[str]] = defaultdict(list)
    harness_groups: dict[str, list[str]] = defaultdict(list)
    for configuration_id, metadata in metadata_by_id.items():
        model_groups[_required_string(metadata, "model_family")].append(
            configuration_id
        )
        harness_groups[_required_string(metadata, "harness_family")].append(
            configuration_id
        )
    provider_plan = _mapping(_mapping(plan, "agent_groups"), "provider_families")
    provider_groups = {
        provider: tuple(
            configuration_id
            for model in _string_tuple(models, f"{provider} models")
            for configuration_id in model_groups.get(model, ())
        )
        for provider, models in provider_plan.items()
    }
    if (
        set().union(*(set(values) for values in provider_groups.values()))
        != set(metadata_by_id)
    ):
        raise ValueError("provider families do not cover configurations")
    configuration_rows = {
        configuration_id: _group_outcome_summary(
            origins_by_repository,
            repository_ids,
            selected,
            baseline,
            outcomes_by_configuration,
            (configuration_id,),
        )
        for configuration_id in sorted(metadata_by_id)
    }
    model_rows = {
        model: _group_outcome_summary(
            origins_by_repository,
            repository_ids,
            selected,
            baseline,
            outcomes_by_configuration,
            tuple(sorted(configurations)),
        )
        for model, configurations in sorted(model_groups.items())
    }
    harness_rows = {
        harness: _group_outcome_summary(
            origins_by_repository,
            repository_ids,
            selected,
            baseline,
            outcomes_by_configuration,
            tuple(sorted(configurations)),
        )
        for harness, configurations in sorted(harness_groups.items())
    }
    provider_rows = {
        provider: _group_outcome_summary(
            origins_by_repository,
            repository_ids,
            selected,
            baseline,
            outcomes_by_configuration,
            tuple(sorted(configurations)),
        )
        for provider, configurations in sorted(provider_groups.items())
    }
    language_by_repository = {
        _required_string(row, "repository_id"): _required_string(row, "language")
        for row in _mapping_sequence(plan, "lineage_and_language")
    }
    all_configuration_ids = tuple(sorted(metadata_by_id))
    repository_summary = _group_outcome_summary(
        origins_by_repository,
        repository_ids,
        selected,
        baseline,
        outcomes_by_configuration,
        all_configuration_ids,
    )
    repository_differences = {
        _required_string(row, "repository_id"): _number(
            row.get("mean_difference"),
            "repository transfer difference",
        )
        for row in _mapping_sequence(repository_summary, "repository_rows")
    }
    language_values: dict[str, list[float]] = defaultdict(list)
    for repository_id in repository_ids:
        language_values[language_by_repository[repository_id]].append(
            repository_differences[repository_id]
        )
    language_rows = {
        language: _mean(tuple(values))
        for language, values in sorted(language_values.items())
    }
    return {
        "selection_rematerialization": (
            "not applicable: frozen memberships accept no Agent outcomes; "
            "every group evaluates the exact same Selection"
        ),
        "configuration_differences": {
            key: value["macro_repository_difference"]
            for key, value in configuration_rows.items()
        },
        "model_differences": {
            key: value["macro_repository_difference"]
            for key, value in model_rows.items()
        },
        "harness_differences": {
            key: value["macro_repository_difference"]
            for key, value in harness_rows.items()
        },
        "provider_differences": {
            key: value["macro_repository_difference"]
            for key, value in provider_rows.items()
        },
        "language_differences": language_rows,
        "language_first_macro_difference": _mean(
            tuple(language_rows.values())
        ),
    }


def _group_outcome_summary(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    selected: Mapping[str, Sequence[str]],
    baseline: Mapping[str, Sequence[str]],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
) -> Mapping[str, Any]:
    rows = []
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline_loss = outcome_pass_rate_mae(
                baseline[origin.origin_id],
                future_ids,
                outcomes_by_configuration,
                configuration_ids,
            )
            loss = outcome_pass_rate_mae(
                selected[origin.origin_id],
                future_ids,
                outcomes_by_configuration,
                configuration_ids,
            )
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "loss": loss,
                    "baseline_loss": baseline_loss,
                    "difference": loss - baseline_loss,
                }
            )
    return _repository_macro_summary(rows, repository_ids)


def _random_outcome_calibration(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
    *,
    budget: int,
    draws: int,
    seed: int,
    candidate_difference: float,
) -> Mapping[str, Any]:
    import numpy as np

    generator = np.random.default_rng(seed)
    repository_draws = {
        repository_id: np.zeros(draws, dtype=np.float64)
        for repository_id in repository_ids
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            history = np.asarray(
                [
                    [
                        outcomes_by_configuration[configuration_id][task_id]
                        for configuration_id in configuration_ids
                    ]
                    for task_id in history_ids
                ],
                dtype=np.float64,
            )
            future = np.asarray(
                [
                    [
                        outcomes_by_configuration[configuration_id][task_id]
                        for configuration_id in configuration_ids
                    ]
                    for task_id in future_ids
                ],
                dtype=np.float64,
            ).mean(axis=0)
            baseline = float(np.abs(history.mean(axis=0) - future).mean())
            offset = 0
            while offset < draws:
                chunk = min(512, draws - offset)
                keys = generator.random((chunk, len(history_ids)))
                selected = np.argpartition(
                    keys,
                    budget - 1,
                    axis=1,
                )[:, :budget]
                selected_rates = history[selected].mean(axis=1)
                loss = np.abs(selected_rates - future).mean(axis=1)
                repository_draws[repository_id][offset : offset + chunk] += (
                    loss - baseline
                )
                offset += chunk
        repository_draws[repository_id] /= len(
            origins_by_repository[repository_id]
        )
    macro = np.mean(
        np.stack(
            [repository_draws[repository] for repository in repository_ids]
        ),
        axis=0,
    )
    better = int(np.sum(macro > candidate_difference))
    equal = int(np.sum(macro == candidate_difference))
    return {
        "draw_count": draws,
        "seed": seed,
        "generator": "numpy PCG64 random-key uniform subsets",
        "numpy_version": np.__version__,
        "mean_macro_repository_difference": float(macro.mean()),
        "quantiles": {
            "0.025": float(np.quantile(macro, 0.025)),
            "0.5": float(np.quantile(macro, 0.5)),
            "0.975": float(np.quantile(macro, 0.975)),
        },
        "candidate_macro_repository_difference": candidate_difference,
        "candidate_better_than_random_midrank": (
            better + 0.5 * equal
        )
        / draws,
        "random_as_good_or_better_rate": float(
            np.mean(macro <= candidate_difference)
        ),
    }


def _repository_bootstrap_interval(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    import numpy as np

    by_repository: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_repository[_required_string(row, "repository_id")].append(
            _number(row.get("difference"), "bootstrap difference")
        )
    values = np.asarray(
        [_mean(tuple(by_repository[repository])) for repository in repository_ids],
        dtype=np.float64,
    )
    generator = np.random.default_rng(seed)
    samples = values[
        generator.integers(
            0,
            len(values),
            size=(resamples, len(values)),
        )
    ].mean(axis=1)
    return {
        "resamples": resamples,
        "seed": seed,
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
    }


def _outcome_gate(
    horizons: Mapping[str, Mapping[str, object]],
    task_space_results: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    rolling = _mapping(plan, "rolling_origin")
    primary = _mapping(
        horizons,
        str(_positive_integer(rolling, "primary_future_tasks")),
    )
    sensitivity = _mapping(
        horizons,
        str(_positive_integer(rolling, "sensitivity_future_tasks")),
    )
    selector = "minimax_temporal_semantic_herding"
    primary_summaries = _mapping(primary, "summaries")
    sensitivity_summaries = _mapping(sensitivity, "summaries")
    wide = _mapping(_mapping(primary_summaries, selector), "wide")
    deep = _mapping(_mapping(primary_summaries, selector), "deep")
    sensitivity_wide = _mapping(
        _mapping(sensitivity_summaries, selector),
        "wide",
    )
    sensitivity_deep = _mapping(
        _mapping(sensitivity_summaries, selector),
        "deep",
    )
    transfer = _mapping(primary, "transfer_audits")
    languages = _number_mapping(transfer, "language_differences")
    models = _number_mapping(transfer, "model_differences")
    providers = _number_mapping(transfer, "provider_differences")
    harnesses = _number_mapping(transfer, "harness_differences")
    configurations = _number_mapping(transfer, "configuration_differences")
    primary_random = _mapping(primary, "random_calibration")
    sensitivity_random = _mapping(sensitivity, "random_calibration")
    alg_007_wide = _mapping(
        _mapping(primary_summaries, "alg_007_centroid_recent_15"),
        "wide",
    )
    requirements = {
        "primary_wide_at_most_minus_0_010": (
            _number(
                wide.get("macro_repository_difference"),
                "primary difference",
            )
            <= -0.010
        ),
        "primary_at_least_10_of_13_repositories_favorable": (
            int(wide.get("favorable_repository_count", -1)) >= 10
        ),
        "primary_every_leave_one_repository_out_negative": all(
            _number(row.get("macro_repository_difference"), "leave-one result")
            < 0.0
            for row in _mapping_sequence(wide, "leave_one_repository_out")
        ),
        "primary_deep_negative": (
            _number(
                deep.get("macro_repository_difference"),
                "primary deep difference",
            )
            < 0.0
        ),
        "sensitivity_common_11_negative": (
            _number(
                sensitivity_wide.get("macro_repository_difference"),
                "sensitivity difference",
            )
            < 0.0
        ),
        "sensitivity_at_least_8_of_11_repositories_favorable": (
            int(sensitivity_wide.get("favorable_repository_count", -1)) >= 8
        ),
        "sensitivity_deep_negative": (
            _number(
                sensitivity_deep.get("macro_repository_difference"),
                "sensitivity deep difference",
            )
            < 0.0
        ),
        "primary_random_midrank_at_least_0_75": (
            _number(
                primary_random.get("candidate_better_than_random_midrank"),
                "primary random midrank",
            )
            >= 0.75
        ),
        "sensitivity_not_below_random_median": (
            _number(
                sensitivity_random.get("candidate_better_than_random_midrank"),
                "sensitivity random midrank",
            )
            >= 0.5
        ),
        "language_transfer": (
            _number(
                transfer.get("language_first_macro_difference"),
                "language-first difference",
            )
            < 0.0
            and sum(value < 0.0 for value in languages.values()) >= 5
            and max(languages.values()) <= 0.020
        ),
        "model_transfer_at_least_9_of_12": (
            sum(value < 0.0 for value in models.values()) >= 9
        ),
        "provider_transfer": (
            _mean(tuple(providers.values())) < 0.0
            and sum(value < 0.0 for value in providers.values()) >= 5
            and max(providers.values()) <= 0.020
        ),
        "harness_transfer_3_of_3": all(
            value < 0.0 for value in harnesses.values()
        ),
        "configuration_directions_at_least_26_of_36": (
            sum(value < 0.0 for value in configurations.values()) >= 26
        ),
        "primary_better_than_unchanged_alg_007": (
            _number(wide.get("macro_repository_loss"), "candidate loss")
            < _number(
                alg_007_wide.get("macro_repository_loss"),
                "ALG-007 loss",
            )
        ),
    }
    task_gate_pass = bool(
        _mapping(task_space_results, "task_space_gate").get(
            "all_requirements_met"
        )
    )
    pre_null_pass = task_gate_pass and all(requirements.values())
    return {
        "requirements": {
            **requirements,
            "outcome_temporal_null_below_0_10": False,
        },
        "task_space_gate_met": task_gate_pass,
        "pre_null_requirements_met": pre_null_pass,
        "all_requirements_met": False,
        "temporal_null": {
            "status": (
                "required_not_yet_run"
                if pre_null_pass
                else "not_reached_by_frozen_decision_order"
            ),
            "permutations": 0,
        },
        "decision": "semantic_mechanism_fails_outcome_gate",
    }


def _number_mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, float]:
    value = _mapping(payload, key)
    return {
        item_key: _number(item_value, f"{key} value")
        for item_key, item_value in value.items()
    }


def _materialize_semantic_memberships(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    index: SimilarityIndex,
    *,
    horizon: int,
    budget: int,
) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    memberships: dict[str, dict[str, tuple[str, ...]]] = {
        selector_id: {} for selector_id in SELECTOR_IDS
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            memberships["full_history"][origin.origin_id] = history_ids
            memberships["recency"][origin.origin_id] = history_ids[-budget:]
            memberships["stationary_semantic_herding"][origin.origin_id] = (
                select_kernel_mean_herding(
                    history_ids,
                    history_ids,
                    index,
                    budget=budget,
                    swap_pass_limit=0,
                )
            )
            memberships["alg_007_centroid_recent_15"][
                origin.origin_id
            ] = select_kernel_mean_herding(
                history_ids,
                history_ids[-min(15, len(history_ids)) :],
                index,
                budget=budget,
                swap_pass_limit=20,
            )
            memberships["minimax_temporal_semantic_herding"][
                origin.origin_id
            ] = select_minimax_temporal_semantic_herding(
                history_ids,
                index,
                horizon=horizon,
                budget=budget,
            )
    return {
        selector_id: dict(sorted(values.items()))
        for selector_id, values in memberships.items()
    }


def _feature_contrast_rows(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    memberships: Mapping[str, Mapping[str, Sequence[str]]],
    index: SimilarityIndex,
) -> Mapping[str, tuple[Mapping[str, object], ...]]:
    rows: dict[str, list[Mapping[str, object]]] = {
        selector_id: [] for selector_id in memberships
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline = kernel_mmd_squared(
                memberships["full_history"][origin.origin_id],
                future_ids,
                index,
            )
            for selector_id, selections in memberships.items():
                loss = kernel_mmd_squared(
                    selections[origin.origin_id],
                    future_ids,
                    index,
                )
                rows[selector_id].append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "loss": loss,
                        "baseline_loss": baseline,
                        "difference": loss - baseline,
                    }
                )
    return {
        selector_id: tuple(selector_rows)
        for selector_id, selector_rows in rows.items()
    }


def _feature_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    return {
        "wide": _repository_macro_summary(rows, repository_ids),
        "deep": _repository_macro_summary(rows, deep_repository_ids),
    }


def _repository_macro_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        repository = _required_string(row, "repository_id")
        if repository in repository_ids:
            by_repository[repository].append(row)
    if set(by_repository) != set(repository_ids):
        raise ValueError("repository summary does not cover planned repositories")
    repository_rows = []
    for repository in repository_ids:
        repository_rows.append(
            {
                "repository_id": repository,
                "origin_count": len(by_repository[repository]),
                "mean_loss": _mean(
                    tuple(
                        _number(row.get("loss"), "feature loss")
                        for row in by_repository[repository]
                    )
                ),
                "mean_baseline_loss": _mean(
                    tuple(
                        _number(row.get("baseline_loss"), "baseline loss")
                        for row in by_repository[repository]
                    )
                ),
                "mean_difference": _mean(
                    tuple(
                        _number(row.get("difference"), "feature difference")
                        for row in by_repository[repository]
                    )
                ),
            }
        )
    differences = tuple(float(row["mean_difference"]) for row in repository_rows)
    return {
        "repository_count": len(repository_rows),
        "origin_count": sum(int(row["origin_count"]) for row in repository_rows),
        "macro_repository_loss": _mean(
            tuple(float(row["mean_loss"]) for row in repository_rows)
        ),
        "macro_repository_baseline_loss": _mean(
            tuple(float(row["mean_baseline_loss"]) for row in repository_rows)
        ),
        "macro_repository_difference": _mean(differences),
        "favorable_repository_count": sum(value < 0.0 for value in differences),
        "repository_rows": tuple(repository_rows),
        "leave_one_repository_out": tuple(
            {
                "omitted_repository_id": repository_rows[index][
                    "repository_id"
                ],
                "macro_repository_difference": _mean(
                    differences[:index] + differences[index + 1 :]
                ),
            }
            for index in range(len(repository_rows))
        ),
    }


def _random_feature_calibration(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    index: SimilarityIndex,
    *,
    budget: int,
    draws: int,
    seed: int,
    candidate_difference: float,
) -> Mapping[str, Any]:
    import numpy as np

    generator = np.random.default_rng(seed)
    repository_draws = {
        repository_id: np.zeros(draws, dtype=np.float64)
        for repository_id in repository_ids
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            history_vectors = np.asarray(
                [index.vectors[task_id] for task_id in history_ids],
                dtype=np.float64,
            )
            future_mean = np.asarray(
                [index.vectors[task_id] for task_id in future_ids],
                dtype=np.float64,
            ).mean(axis=0)
            baseline_mean = history_vectors.mean(axis=0)
            baseline = float(np.square(baseline_mean - future_mean).sum())
            offset = 0
            while offset < draws:
                chunk = min(512, draws - offset)
                keys = generator.random((chunk, len(history_ids)))
                selected = np.argpartition(
                    keys,
                    budget - 1,
                    axis=1,
                )[:, :budget]
                selected_mean = history_vectors[selected].mean(axis=1)
                loss = np.square(selected_mean - future_mean).sum(axis=1)
                repository_draws[repository_id][offset : offset + chunk] += (
                    loss - baseline
                )
                offset += chunk
        repository_draws[repository_id] /= len(
            origins_by_repository[repository_id]
        )
    macro = np.mean(
        np.stack(
            [repository_draws[repository] for repository in repository_ids]
        ),
        axis=0,
    )
    better = int(np.sum(macro > candidate_difference))
    equal = int(np.sum(macro == candidate_difference))
    return {
        "draw_count": draws,
        "seed": seed,
        "generator": "numpy PCG64 random-key uniform subsets",
        "numpy_version": np.__version__,
        "mean_macro_repository_difference": float(macro.mean()),
        "quantiles": {
            "0.025": float(np.quantile(macro, 0.025)),
            "0.5": float(np.quantile(macro, 0.5)),
            "0.975": float(np.quantile(macro, 0.975)),
        },
        "candidate_macro_repository_difference": candidate_difference,
        "candidate_better_than_random_midrank": (
            better + 0.5 * equal
        )
        / draws,
        "random_as_good_or_better_rate": float(
            np.mean(macro <= candidate_difference)
        ),
    }


def _task_space_gate(
    horizons: Mapping[str, Mapping[str, object]],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    rolling = _mapping(plan, "rolling_origin")
    primary_key = str(_positive_integer(rolling, "primary_future_tasks"))
    sensitivity_key = str(
        _positive_integer(rolling, "sensitivity_future_tasks")
    )
    primary = _mapping(horizons, primary_key)
    sensitivity = _mapping(horizons, sensitivity_key)
    primary_summaries = _mapping(primary, "summaries")
    sensitivity_summaries = _mapping(sensitivity, "summaries")
    selector_id = "minimax_temporal_semantic_herding"
    candidate_wide = _mapping(
        _mapping(primary_summaries, selector_id),
        "wide",
    )
    candidate_deep = _mapping(
        _mapping(primary_summaries, selector_id),
        "deep",
    )
    full_wide = _mapping(
        _mapping(primary_summaries, "full_history"),
        "wide",
    )
    sensitivity_wide = _mapping(
        _mapping(sensitivity_summaries, selector_id),
        "wide",
    )
    sensitivity_deep = _mapping(
        _mapping(sensitivity_summaries, selector_id),
        "deep",
    )
    controls_better = all(
        _number(candidate_wide.get("macro_repository_loss"), "candidate loss")
        < _number(
            _mapping(_mapping(primary_summaries, control), "wide").get(
                "macro_repository_loss"
            ),
            f"{control} loss",
        )
        for control in (
            "recency",
            "stationary_semantic_herding",
            "alg_007_centroid_recent_15",
        )
    )
    primary_random = _mapping(primary, "random_calibration")
    sensitivity_random = _mapping(sensitivity, "random_calibration")
    requirements = {
        "primary_relative_mmd_reduction_at_least_10_percent": (
            _number(
                candidate_wide.get("macro_repository_loss"),
                "candidate loss",
            )
            <= 0.9
            * _number(
                full_wide.get("macro_repository_loss"),
                "full-history loss",
            )
        ),
        "primary_at_least_10_of_13_repositories_favorable": (
            int(candidate_wide.get("favorable_repository_count", -1)) >= 10
        ),
        "primary_every_leave_one_repository_out_negative": all(
            _number(row.get("macro_repository_difference"), "leave-one result")
            < 0.0
            for row in _mapping_sequence(
                candidate_wide,
                "leave_one_repository_out",
            )
        ),
        "primary_deep_negative": (
            _number(
                candidate_deep.get("macro_repository_difference"),
                "primary deep difference",
            )
            < 0.0
        ),
        "primary_better_than_fixed_controls": controls_better,
        "primary_random_midrank_at_least_0_75": (
            _number(
                primary_random.get("candidate_better_than_random_midrank"),
                "primary random midrank",
            )
            >= 0.75
        ),
        "sensitivity_common_11_negative": (
            _number(
                sensitivity_wide.get("macro_repository_difference"),
                "sensitivity difference",
            )
            < 0.0
        ),
        "sensitivity_at_least_8_of_11_repositories_favorable": (
            int(sensitivity_wide.get("favorable_repository_count", -1)) >= 8
        ),
        "sensitivity_deep_negative": (
            _number(
                sensitivity_deep.get("macro_repository_difference"),
                "sensitivity deep difference",
            )
            < 0.0
        ),
        "sensitivity_not_below_random_median": (
            _number(
                sensitivity_random.get("candidate_better_than_random_midrank"),
                "sensitivity random midrank",
            )
            >= 0.5
        ),
    }
    pre_null_pass = all(requirements.values())
    return {
        "requirements": {
            **requirements,
            "task_space_temporal_null_below_0_10": False,
        },
        "pre_null_requirements_met": pre_null_pass,
        "all_requirements_met": False,
        "temporal_null": {
            "status": (
                "required_not_yet_run"
                if pre_null_pass
                else "not_reached_by_frozen_decision_order"
            ),
            "permutations": 0,
        },
        "decision": (
            "source_projection_or_runtime_blocker"
            if pre_null_pass
            else "semantic_mechanism_fails_task_space_gate"
        ),
    }


def load_task_metadata(
    content_rows: Sequence[Mapping[str, object]],
    time_path: Path,
    plan: Mapping[str, object],
) -> tuple[TaskMetadata, ...]:
    time_rows = _load_jsonl(time_path)
    if canonical_digest(time_rows) != _mapping(plan, "source").get(
        "task_time_projection_digest"
    ):
        raise ValueError("Task time projection does not match Selector plan")
    times = {
        _required_string(row, "instance_id"): _required_string(
            row,
            "created_at",
        )
        for row in time_rows
    }
    if len(times) != len(time_rows):
        raise ValueError("Task time projection contains duplicate IDs")
    content_ids = {
        _required_string(row, "instance_id") for row in content_rows
    }
    if set(times) != content_ids:
        raise ValueError("Task times and content cover different Tasks")
    return tuple(
        TaskMetadata(
            instance_id=_required_string(row, "instance_id"),
            repository_id=_required_string(row, "repository"),
            created_at=times[_required_string(row, "instance_id")],
            difficulty=_required_string(row, "language"),
            problem_statement=_required_string(row, "text"),
        )
        for row in content_rows
    )


def _selection_input(
    history_ids: Sequence[str],
    budget: int,
) -> tuple[str, ...]:
    task_ids = tuple(history_ids)
    if (
        not task_ids
        or len(task_ids) != len(set(task_ids))
        or isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget <= 0
        or budget > len(task_ids)
    ):
        raise ValueError("semantic selection input is invalid")
    return task_ids


def _target_kernel_moments(
    candidate_ids: Sequence[str],
    target_ids: Sequence[str],
    index: SimilarityIndex,
) -> tuple[Mapping[str, float], float]:
    target = tuple(target_ids)
    if not target:
        raise ValueError("kernel target must not be empty")
    scores = {
        candidate: _mean(
            tuple(index.similarity(candidate, item) for item in target)
        )
        for candidate in candidate_ids
    }
    constant = _mean(tuple(scores[item] for item in target))
    return scores, constant


def _kernel_mean_distance(
    pair_sum: float,
    target_sum: float,
    count: int,
    target_constant: float,
) -> float:
    return max(
        0.0,
        pair_sum / (count * count)
        - 2.0 * target_sum / count
        + target_constant,
    )


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


def _task_space_summary(
    result: Mapping[str, object],
) -> Mapping[str, object]:
    horizons = _mapping(result, "horizons")
    return {
        "schema_version": "barcarolle_multi_swe_task_space_summary_v1",
        "study_id": result.get("study_id"),
        "selector_plan_digest": result.get("selector_plan_digest"),
        "embedding_manifest_digest": result.get("embedding_manifest_digest"),
        "embedding_artifact_digest": result.get("embedding_artifact_digest"),
        "task_space_results_digest": result.get("task_space_results_digest"),
        "task_count": result.get("task_count"),
        "horizons": {
            horizon: {
                key: value
                for key, value in _mapping(horizons, horizon).items()
                if key != "memberships"
            }
            for horizon in sorted(horizons, key=int)
        },
        "task_space_gate": result.get("task_space_gate"),
        "resource_use": result.get("resource_use"),
        "claim_boundary": result.get("claim_boundary"),
    }


def _outcome_summary(
    result: Mapping[str, object],
) -> Mapping[str, object]:
    return {
        "schema_version": "barcarolle_multi_swe_semantic_outcome_summary_v1",
        "study_id": result.get("study_id"),
        "selector_plan_digest": result.get("selector_plan_digest"),
        "task_space_results_digest": result.get("task_space_results_digest"),
        "outcome_results_digest": result.get("outcome_results_digest"),
        "outcome_diagnostics": result.get("outcome_diagnostics"),
        "horizons": result.get("horizons"),
        "task_space_gate": result.get("task_space_gate"),
        "outcome_gate": result.get("outcome_gate"),
        "nomination": result.get("nomination"),
        "resource_use": result.get("resource_use"),
        "claim_boundary": result.get("claim_boundary"),
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


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{label} must be a nonempty string sequence")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicates")
    return result


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


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
    parser.add_argument(
        "--embedding-manifest",
        type=Path,
        default=DEFAULT_EMBEDDING_MANIFEST,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    embed = subparsers.add_parser("embed", help="build the ignored local vectors")
    embed.add_argument("--task-content", type=Path, required=True)
    embed.add_argument("--model-snapshot", type=Path, required=True)
    embed.add_argument("--output", type=Path, required=True)

    task_space = subparsers.add_parser(
        "task-space",
        help="materialize selections and evaluate future Task semantics",
    )
    task_space.add_argument("--task-content", type=Path, required=True)
    task_space.add_argument("--task-times", type=Path, required=True)
    task_space.add_argument("--embeddings", type=Path, required=True)
    task_space.add_argument("--output", type=Path, required=True)

    outcome = subparsers.add_parser(
        "outcome",
        help="join frozen memberships to the opened public outcome panel",
    )
    outcome.add_argument("--task-content", type=Path, required=True)
    outcome.add_argument("--task-times", type=Path, required=True)
    outcome.add_argument("--task-space-results", type=Path, required=True)
    outcome.add_argument("--panel-summary", type=Path, required=True)
    outcome.add_argument("--resolved-outcomes", type=Path, required=True)
    outcome.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    plan = load_selector_plan(arguments.plan)
    content_manifest = load_content_manifest(arguments.content_manifest)
    if arguments.command == "outcome":
        if arguments.output.exists():
            raise FileExistsError(
                f"refusing to overwrite outcome output: {arguments.output}"
            )
        embedding_manifest = load_embedding_manifest(
            arguments.embedding_manifest
        )
        task_space = load_task_space_results(
            arguments.task_space_results,
            plan,
            embedding_manifest,
        )
        rows = load_task_content(arguments.task_content, content_manifest)
        tasks = load_task_metadata(rows, arguments.task_times, plan)
        task_ids = tuple(task.instance_id for task in tasks)
        outcomes, configuration_metadata, diagnostics = load_public_outcomes(
            arguments.panel_summary,
            arguments.resolved_outcomes,
            task_ids,
            plan,
        )
        result = run_outcome_replay(
            tasks,
            outcomes,
            configuration_metadata,
            task_space,
            plan,
            diagnostics,
        )
        arguments.output.write_text(
            canonical_json(result) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(_outcome_summary(result), indent=2, sort_keys=True))
        return 0
    if arguments.command == "task-space":
        if arguments.output.exists():
            raise FileExistsError(
                f"refusing to overwrite task-space output: {arguments.output}"
            )
        embedding_manifest = load_embedding_manifest(
            arguments.embedding_manifest
        )
        if embedding_manifest.get("selector_plan_digest") != plan.get(
            "selector_plan_digest"
        ):
            raise ValueError("embedding manifest does not bind Selector plan")
        if embedding_manifest.get("content_manifest_digest") != (
            content_manifest.get("content_manifest_digest")
        ):
            raise ValueError("embedding manifest does not bind Task content")
        rows = load_task_content(arguments.task_content, content_manifest)
        tasks = load_task_metadata(rows, arguments.task_times, plan)
        task_ids = tuple(task.instance_id for task in tasks)
        vectors, raw_manifest = load_embedding_artifact(
            arguments.embeddings,
            plan,
            content_manifest,
            task_ids,
        )
        for key in (
            "embedding_artifact_digest",
            "vector_values_digest",
            "task_count",
            "dimensions",
        ):
            if raw_manifest.get(key) != embedding_manifest.get(key):
                raise ValueError(f"raw embedding artifact changed: {key}")
        result = run_task_space_replay(
            tasks,
            vectors,
            plan,
            embedding_manifest,
        )
        arguments.output.write_text(
            canonical_json(result) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(_task_space_summary(result), indent=2, sort_keys=True))
        return 0
    if arguments.command != "embed":
        raise AssertionError(arguments.command)
    if arguments.output.exists():
        raise FileExistsError(
            f"refusing to overwrite embedding output: {arguments.output}"
        )
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
