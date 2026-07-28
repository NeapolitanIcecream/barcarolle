#!/usr/bin/env python3
"""Audit pre-Origin response representation and future-state signal."""

from __future__ import annotations

# NumPy is supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from math import fsum
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    load_content_manifest,
    load_embedding_artifact,
    load_embedding_manifest,
    load_public_outcomes,
    load_selector_plan,
    load_task_content,
    load_task_metadata,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "response-signal-plan.json"
DEFAULT_AMENDMENT = HERE / "response-signal-amendment-1.json"
DEFAULT_DIAGNOSTIC_PLAN = HERE / "response-signal-diagnostic-1.json"
PLAN_SCHEMA = "barcarolle_multi_swe_response_signal_plan_v1"
AMENDMENT_SCHEMA = "barcarolle_multi_swe_response_signal_amendment_v1"
DIAGNOSTIC_PLAN_SCHEMA = "barcarolle_multi_swe_response_signal_diagnostic_plan_v1"
RESULT_SCHEMA = "barcarolle_multi_swe_response_signal_results_v1"
DIAGNOSTIC_RESULT_SCHEMA = "barcarolle_multi_swe_response_signal_diagnostic_results_v1"
NUMPY_VERSION = "2.5.1"


@dataclass(frozen=True)
class StudyData:
    tasks: tuple[TaskMetadata, ...]
    task_ids: tuple[str, ...]
    embeddings: Any
    outcomes: Any
    configuration_ids: tuple[str, ...]
    task_index: Mapping[str, int]
    repository_indices: Mapping[str, tuple[int, ...]]
    repository_times: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class ResponseProjection:
    configuration_indices: tuple[int, ...]
    directions: Any
    centers: Any
    scales: Any
    training_repository_ids: tuple[str, ...]
    training_task_count: int
    training_task_digest: str
    maximum_training_time: str
    projection_digest: str


def load_response_signal_plan(
    path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("response signal plan schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "response_signal_plan_digest"
        }
    )
    if payload.get("response_signal_plan_digest") != expected:
        raise ValueError("response signal plan digest does not match")
    candidate = _mapping(payload, "candidate")
    if (
        candidate.get("algorithm_id") != "ALG-013"
        or candidate.get("short_name") != "RCP"
    ):
        raise ValueError("response signal candidate changed")
    boundary = _mapping(payload, "resource_boundary")
    if any(
        boundary.get(key) != 0
        for key in (
            "paid_api_calls",
            "embedding_api_calls",
            "coding_agent_calls",
            "sealed_holdout_reads",
        )
    ):
        raise ValueError("response signal resource boundary changed")
    return payload


def load_response_signal_amendment(
    path: Path = DEFAULT_AMENDMENT,
    *,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != AMENDMENT_SCHEMA:
        raise ValueError("response signal amendment schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "amendment_digest"}
    )
    if payload.get("amendment_digest") != expected:
        raise ValueError("response signal amendment digest does not match")
    if payload.get("response_signal_plan_digest") != plan.get(
        "response_signal_plan_digest"
    ):
        raise ValueError("response signal amendment does not bind plan")
    if payload.get("status") != "pre_run_measurement_unit_correction":
        raise ValueError("response signal amendment status changed")
    return payload


def load_response_signal_diagnostic_plan(
    path: Path = DEFAULT_DIAGNOSTIC_PLAN,
    *,
    plan: Mapping[str, object],
    amendment: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != DIAGNOSTIC_PLAN_SCHEMA:
        raise ValueError("response signal diagnostic plan schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "diagnostic_plan_digest"
        }
    )
    if payload.get("diagnostic_plan_digest") != expected:
        raise ValueError("response signal diagnostic plan digest does not match")
    if (
        payload.get("response_signal_plan_digest")
        != plan.get("response_signal_plan_digest")
        or payload.get("amendment_digest") != amendment.get("amendment_digest")
        or payload.get("status") != "post_decision_diagnostic_cannot_rescue_alg_013"
    ):
        raise ValueError("response signal diagnostic plan binding changed")
    return payload


def load_response_signal_results(
    path: Path,
    *,
    plan: Mapping[str, object],
    diagnostic_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("response_signal_results_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("response signal result digest does not match")
    payload["response_signal_results_digest"] = digest
    if (
        payload.get("schema_version") != RESULT_SCHEMA
        or payload.get("response_signal_plan_digest")
        != plan.get("response_signal_plan_digest")
        or digest != diagnostic_plan.get("rejected_results_digest")
        or payload.get("decision") != "response_representation_signal_rejected"
    ):
        raise ValueError("diagnostic does not bind rejected ALG-013 result")
    raw_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if raw_digest != diagnostic_plan.get("rejected_raw_sha256"):
        raise ValueError("diagnostic rejected raw artifact identity changed")
    return payload


def fit_response_contrast_projection(
    data: StudyData,
    *,
    target_repository_id: str,
    cutoff: str,
    tolerance: float,
    permutation_index: int = 0,
    retained_configuration_indices: Sequence[int] | None = None,
) -> ResponseProjection:
    """Fit repository-centered response directions without target-repo rows."""
    import numpy as np

    if (
        not target_repository_id
        or not cutoff
        or tolerance <= 0.0
        or isinstance(permutation_index, bool)
        or permutation_index < 0
    ):
        raise ValueError("response projection inputs are invalid")
    retained = (
        tuple(range(len(data.configuration_ids)))
        if retained_configuration_indices is None
        else tuple(retained_configuration_indices)
    )
    if (
        not retained
        or len(retained) != len(set(retained))
        or any(index < 0 or index >= len(data.configuration_ids) for index in retained)
    ):
        raise ValueError("retained response configurations are invalid")

    repository_rows: list[tuple[str, tuple[int, ...], Any, Any]] = []
    for repository_id in sorted(data.repository_indices):
        if repository_id == target_repository_id:
            continue
        count = bisect_right(data.repository_times[repository_id], cutoff)
        indices = data.repository_indices[repository_id][:count]
        if not indices:
            continue
        embeddings = data.embeddings[list(indices)]
        outcomes = data.outcomes[np.ix_(list(indices), list(retained))]
        if permutation_index:
            outcomes = _permute_outcomes(
                outcomes,
                permutation_index=permutation_index,
            )
        repository_rows.append((repository_id, indices, embeddings, outcomes))
    if not repository_rows:
        raise ValueError("response projection has no fitting repositories")

    direction_sum = np.zeros(
        (len(retained), data.embeddings.shape[1]),
        dtype=np.float64,
    )
    for _, _, embeddings, outcomes in repository_rows:
        centered_embeddings = embeddings - embeddings.mean(axis=0)
        centered_outcomes = outcomes - outcomes.mean(axis=0)
        direction_sum += (centered_outcomes.T @ centered_embeddings) / len(embeddings)
    directions = direction_sum / len(repository_rows)
    norms = np.linalg.norm(directions, axis=1)
    active = norms > tolerance
    if not bool(np.any(active)):
        raise ValueError("response projection has no nonzero covariance direction")
    directions = directions[active] / norms[active, None]
    active_indices = tuple(
        index for index, keep in zip(retained, active.tolist(), strict=True) if keep
    )

    repository_coordinate_rows = [
        embeddings @ directions.T for _, _, embeddings, _ in repository_rows
    ]
    centers = np.mean(
        np.stack(
            [coordinates.mean(axis=0) for coordinates in repository_coordinate_rows]
        ),
        axis=0,
    )
    variances = np.mean(
        np.stack(
            [
                np.square(coordinates - centers).mean(axis=0)
                for coordinates in repository_coordinate_rows
            ]
        ),
        axis=0,
    )
    scales = np.sqrt(variances)
    scaled = scales > tolerance
    if not bool(np.any(scaled)):
        raise ValueError("response projection has no variable coordinate")
    directions = directions[scaled]
    centers = centers[scaled]
    scales = scales[scaled]
    active_indices = tuple(
        index
        for index, keep in zip(active_indices, scaled.tolist(), strict=True)
        if keep
    )

    training_ids = tuple(
        data.task_ids[index]
        for _, indices, _, _ in repository_rows
        for index in indices
    )
    training_times = tuple(
        data.tasks[index].created_at
        for _, indices, _, _ in repository_rows
        for index in indices
    )
    projection_digest = _array_digest(
        (
            np.asarray(active_indices, dtype=np.int64),
            directions,
            centers,
            scales,
        ),
        prefix=(
            target_repository_id,
            cutoff,
            str(permutation_index),
            canonical_digest(training_ids),
        ),
    )
    return ResponseProjection(
        configuration_indices=active_indices,
        directions=directions,
        centers=centers,
        scales=scales,
        training_repository_ids=tuple(
            repository_id for repository_id, _, _, _ in repository_rows
        ),
        training_task_count=len(training_ids),
        training_task_digest=canonical_digest(training_ids),
        maximum_training_time=max(training_times),
        projection_digest=projection_digest,
    )


def transform_response_projection(
    embeddings: Any,
    projection: ResponseProjection,
) -> Any:
    import numpy as np

    values = np.asarray(embeddings, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != projection.directions.shape[1]:
        raise ValueError("response projection embedding shape changed")
    return (values @ projection.directions.T - projection.centers) / projection.scales


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> float | None:
    if len(scores) != len(labels) or not scores:
        raise ValueError("ROC AUC inputs must align and be nonempty")
    positives = [
        float(score) for score, label in zip(scores, labels, strict=True) if label == 1
    ]
    negatives = [
        float(score) for score, label in zip(scores, labels, strict=True) if label == 0
    ]
    if any(label not in (0, 1) for label in labels):
        raise ValueError("ROC AUC labels must be binary")
    if not positives or not negatives:
        return None
    wins = fsum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def ols_next_block_mean(values: Any, *, horizon: int) -> Any:
    """Forecast the next complete block centroid with per-coordinate OLS."""
    import numpy as np

    matrix = np.asarray(values, dtype=np.float64)
    if (
        matrix.ndim != 2
        or matrix.shape[0] < 2 * horizon
        or isinstance(horizon, bool)
        or horizon <= 0
    ):
        raise ValueError("OLS block forecast requires two complete blocks")
    complete_count = matrix.shape[0] // horizon
    blocks = (
        matrix[-complete_count * horizon :]
        .reshape(
            complete_count,
            horizon,
            matrix.shape[1],
        )
        .mean(axis=1)
    )
    x = np.arange(complete_count, dtype=np.float64)
    centered_x = x - x.mean()
    denominator = float(np.square(centered_x).sum())
    if denominator <= 0.0:
        raise ValueError("OLS block forecast has no index variation")
    slope = (centered_x[:, None] * blocks).sum(axis=0) / denominator
    intercept = blocks.mean(axis=0) - slope * x.mean()
    return intercept + slope * complete_count


def _load_bound_study(
    *,
    task_content_path: Path,
    task_time_path: Path,
    embedding_path: Path,
    panel_path: Path,
    resolved_path: Path,
    plan_path: Path,
    amendment_path: Path,
) -> tuple[
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
    StudyData,
    Mapping[str, Any],
    Mapping[str, Any],
]:
    import numpy as np

    if np.__version__ != NUMPY_VERSION:
        raise ValueError(
            f"NumPy version changed: expected {NUMPY_VERSION}, got {np.__version__}"
        )
    selector_plan = load_selector_plan()
    plan = load_response_signal_plan(plan_path)
    amendment = load_response_signal_amendment(amendment_path, plan=plan)
    _validate_bound_source(selector_plan, plan)
    content_manifest = load_content_manifest()
    embedding_manifest = load_embedding_manifest()
    content_rows = load_task_content(task_content_path, content_manifest)
    task_ids = tuple(_required_string(row, "instance_id") for row in content_rows)
    vectors, embedding_artifact = load_embedding_artifact(
        embedding_path,
        selector_plan,
        content_manifest,
        task_ids,
    )
    if embedding_manifest.get("embedding_manifest_digest") != _mapping(
        plan, "source"
    ).get("embedding_manifest_digest") or embedding_artifact.get(
        "embedding_artifact_digest"
    ) != _mapping(plan, "source").get("embedding_artifact_digest"):
        raise ValueError("response signal plan does not bind embeddings")
    tasks = load_task_metadata(content_rows, task_time_path, selector_plan)
    outcomes_by_configuration, configuration_metadata, outcome_diagnostics = (
        load_public_outcomes(
            panel_path,
            resolved_path,
            task_ids,
            selector_plan,
        )
    )
    configuration_ids = tuple(
        _required_string(row, "configuration_id") for row in configuration_metadata
    )
    data = _build_study_data(
        tasks,
        vectors,
        outcomes_by_configuration,
        configuration_ids,
    )
    return (
        selector_plan,
        plan,
        amendment,
        data,
        outcome_diagnostics,
        embedding_artifact,
    )


def run_signal_audit(
    *,
    task_content_path: Path,
    task_time_path: Path,
    embedding_path: Path,
    panel_path: Path,
    resolved_path: Path,
    plan_path: Path = DEFAULT_PLAN,
    amendment_path: Path = DEFAULT_AMENDMENT,
) -> Mapping[str, Any]:
    """Run the frozen signal cascade, stopping at the first failed stage."""
    (
        selector_plan,
        plan,
        amendment,
        data,
        outcome_diagnostics,
        embedding_artifact,
    ) = _load_bound_study(
        task_content_path=task_content_path,
        task_time_path=task_time_path,
        embedding_path=embedding_path,
        panel_path=panel_path,
        resolved_path=resolved_path,
        plan_path=plan_path,
        amendment_path=amendment_path,
    )
    rolling = _mapping(selector_plan, "rolling_origin")
    primary_horizon = _positive_integer(rolling, "primary_future_tasks")
    primary_repositories = _string_tuple(
        rolling.get("primary_repository_ids"),
        "primary repositories",
    )
    primary_deep = _string_tuple(
        rolling.get("primary_deep_repository_ids"),
        "primary deep repositories",
    )
    origins = _origins_for_horizon(data.tasks, primary_horizon, selector_plan)
    projection_cache: dict[tuple[str, str, int], ResponseProjection] = {}

    stage_a_rows, stage_a_audits = _stage_a_rows(
        data,
        origins,
        primary_repositories,
        plan,
        permutation_index=0,
        projection_cache=projection_cache,
    )
    stage_a_summary = _auc_summary(
        stage_a_rows,
        primary_repositories,
        resamples=_positive_integer(
            _mapping(plan, "diagnostics"),
            "bootstrap_resamples",
        ),
        seed=_positive_integer(
            _mapping(plan, "diagnostics"),
            "bootstrap_seed",
        ),
    )
    stage_a_pre_null = _stage_a_pre_null_gate(stage_a_summary)
    stage_a_null: Mapping[str, Any]
    if stage_a_pre_null:
        null_values = []
        for permutation_index in range(
            1,
            _positive_integer(
                _mapping(plan, "diagnostics"),
                "representation_null_permutations",
            )
            + 1,
        ):
            null_rows, _ = _stage_a_rows(
                data,
                origins,
                primary_repositories,
                plan,
                permutation_index=permutation_index,
                projection_cache={},
            )
            null_values.append(
                _auc_summary(
                    null_rows,
                    primary_repositories,
                    resamples=0,
                    seed=0,
                )["macro_repository_auc"]
            )
        stage_a_null = _upper_tail_null(
            float(stage_a_summary["macro_repository_auc"]),
            tuple(float(value) for value in null_values),
        )
    else:
        stage_a_null = {
            "status": "not_reached_by_frozen_decision_order",
            "permutations": 0,
        }
    stage_a_pass = stage_a_pre_null and (
        _number(
            stage_a_null.get("corrected_as_good_or_better_rate"),
            "Stage A null rate",
        )
        < 0.10
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "response_signal_plan_digest": plan.get("response_signal_plan_digest"),
        "amendment_digest": amendment.get("amendment_digest"),
        "selector_plan_digest": selector_plan.get("selector_plan_digest"),
        "embedding_artifact_digest": embedding_artifact.get(
            "embedding_artifact_digest"
        ),
        "outcome_diagnostics": outcome_diagnostics,
        "epistemic_status": plan.get("epistemic_status"),
        "stage_a": {
            "horizon": primary_horizon,
            "summary": stage_a_summary,
            "projection_audits": stage_a_audits,
            "null": stage_a_null,
            "pre_null_requirements_met": stage_a_pre_null,
            "all_requirements_met": stage_a_pass,
        },
        "stage_b": {
            "status": (
                "required_not_yet_run"
                if stage_a_pass
                else "not_reached_by_frozen_decision_order"
            )
        },
        "stage_c": {"status": "not_reached_by_frozen_decision_order"},
        "decision": (
            "target_future_increment_required"
            if stage_a_pass
            else "response_representation_signal_rejected"
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "coding_agent_calls": 0,
            "sealed_holdout_reads": 0,
        },
        "claim_boundary": _mapping(plan, "research_contract").get("claim_boundary"),
    }
    if stage_a_pass:
        stage_b = _run_stage_b(
            data,
            selector_plan,
            plan,
            projection_cache,
            primary_deep=primary_deep,
        )
        result["stage_b"] = stage_b
        result["decision"] = stage_b["decision"]
    result["response_signal_results_digest"] = canonical_digest(result)
    return result


def run_history_auc_diagnostic(
    *,
    task_content_path: Path,
    task_time_path: Path,
    embedding_path: Path,
    panel_path: Path,
    resolved_path: Path,
    rejected_results_path: Path,
    plan_path: Path = DEFAULT_PLAN,
    amendment_path: Path = DEFAULT_AMENDMENT,
    diagnostic_plan_path: Path = DEFAULT_DIAGNOSTIC_PLAN,
) -> Mapping[str, Any]:
    """Diagnose Stage A precision without reopening the rejected candidate."""
    (
        selector_plan,
        plan,
        amendment,
        data,
        outcome_diagnostics,
        embedding_artifact,
    ) = _load_bound_study(
        task_content_path=task_content_path,
        task_time_path=task_time_path,
        embedding_path=embedding_path,
        panel_path=panel_path,
        resolved_path=resolved_path,
        plan_path=plan_path,
        amendment_path=amendment_path,
    )
    diagnostic_plan = load_response_signal_diagnostic_plan(
        diagnostic_plan_path,
        plan=plan,
        amendment=amendment,
    )
    rejected = load_response_signal_results(
        rejected_results_path,
        plan=plan,
        diagnostic_plan=diagnostic_plan,
    )
    rolling = _mapping(selector_plan, "rolling_origin")
    horizon = _positive_integer(rolling, "primary_future_tasks")
    repositories = _string_tuple(
        rolling.get("primary_repository_ids"),
        "primary repositories",
    )
    origins = _origins_for_horizon(data.tasks, horizon, selector_plan)
    rows, audits = _stage_a_rows(
        data,
        origins,
        repositories,
        plan,
        permutation_index=0,
        projection_cache={},
        evaluation_scope="history",
    )
    diagnostics = _mapping(plan, "diagnostics")
    summary = _auc_summary(
        rows,
        repositories,
        resamples=_positive_integer(diagnostics, "bootstrap_resamples"),
        seed=_positive_integer(diagnostics, "bootstrap_seed"),
    )
    null_values = []
    for permutation_index in range(
        1,
        _positive_integer(
            diagnostics,
            "representation_null_permutations",
        )
        + 1,
    ):
        null_rows, _ = _stage_a_rows(
            data,
            origins,
            repositories,
            plan,
            permutation_index=permutation_index,
            projection_cache={},
            evaluation_scope="history",
        )
        null_summary = _auc_summary(
            null_rows,
            repositories,
            resamples=0,
            seed=0,
        )
        null_values.append(
            _number(
                null_summary.get("macro_repository_auc"),
                "history AUC null value",
            )
        )
    null = {
        **_upper_tail_null(
            _number(summary.get("macro_repository_auc"), "history AUC"),
            tuple(null_values),
        ),
        "construction": "deterministic within-repository circular row shift",
        "preserves_complete_task_response_vectors": True,
    }
    requirements_without_null = _stage_a_pre_null_gate(summary)
    all_requirements = requirements_without_null and (
        _number(
            null.get("corrected_as_good_or_better_rate"),
            "history AUC null rate",
        )
        < 0.10
    )
    result: dict[str, Any] = {
        "schema_version": DIAGNOSTIC_RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "diagnostic_id": diagnostic_plan.get("diagnostic_id"),
        "diagnostic_plan_digest": diagnostic_plan.get("diagnostic_plan_digest"),
        "response_signal_plan_digest": plan.get("response_signal_plan_digest"),
        "amendment_digest": amendment.get("amendment_digest"),
        "rejected_results_digest": rejected.get("response_signal_results_digest"),
        "selector_plan_digest": selector_plan.get("selector_plan_digest"),
        "embedding_artifact_digest": embedding_artifact.get(
            "embedding_artifact_digest"
        ),
        "outcome_diagnostics": outcome_diagnostics,
        "horizon": horizon,
        "summary": summary,
        "projection_audits": audits,
        "permutation_null": null,
        "requirements_without_null_met": requirements_without_null,
        "all_diagnostic_requirements_met": all_requirements,
        "alg_013_decision": "response_representation_signal_rejected",
        "decision": (
            "static_response_signal_supported_but_alg_013_remains_rejected"
            if all_requirements
            else "response_contrast_representation_closed"
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "sealed_holdout_reads": 0,
        },
        "claim_boundary": (
            "Post-rejection precision diagnostic only. It cannot reopen ALG-013, "
            "unlock its forecast or Selection, or provide confirmation."
        ),
    }
    result["diagnostic_results_digest"] = canonical_digest(result)
    return result


def _run_stage_b(
    data: StudyData,
    selector_plan: Mapping[str, object],
    plan: Mapping[str, object],
    projection_cache: dict[tuple[str, str, int], ResponseProjection],
    *,
    primary_deep: Sequence[str],
) -> Mapping[str, Any]:
    rolling = _mapping(selector_plan, "rolling_origin")
    primary_horizon = _positive_integer(rolling, "primary_future_tasks")
    sensitivity_horizon = _positive_integer(
        rolling,
        "sensitivity_future_tasks",
    )
    repository_sets = {
        primary_horizon: _string_tuple(
            rolling.get("primary_repository_ids"),
            "primary repositories",
        ),
        sensitivity_horizon: _string_tuple(
            rolling.get("sensitivity_common_repository_ids"),
            "sensitivity repositories",
        ),
    }
    deep_sets = {
        primary_horizon: tuple(primary_deep),
        sensitivity_horizon: _string_tuple(
            rolling.get("sensitivity_deep_repository_ids"),
            "sensitivity deep repositories",
        ),
    }
    horizon_results = {}
    for horizon in (primary_horizon, sensitivity_horizon):
        origins = _origins_for_horizon(data.tasks, horizon, selector_plan)
        rows, audits = _stage_b_rows(
            data,
            origins,
            repository_sets[horizon],
            plan,
            horizon=horizon,
            projection_cache=projection_cache,
        )
        horizon_results[str(horizon)] = {
            "summary": _forecast_summary(rows, repository_sets[horizon]),
            "deep": _forecast_summary(rows, deep_sets[horizon]),
            "projection_audits": audits,
            "calendar_span": (
                _calendar_span_summary(rows)
                if horizon == primary_horizon
                else {"status": "primary_horizon_only"}
            ),
        }
    gate = _stage_b_pre_null_gate(
        horizon_results,
        primary_horizon=primary_horizon,
        sensitivity_horizon=sensitivity_horizon,
    )
    if gate["pre_null_requirements_met"]:
        null = _stage_b_temporal_null(
            data,
            selector_plan,
            plan,
            horizon=primary_horizon,
            repository_ids=repository_sets[primary_horizon],
            projection_cache=projection_cache,
            observed_difference=_number(
                _mapping(
                    _mapping(horizon_results[str(primary_horizon)], "summary"),
                    "candidate",
                ).get("macro_repository_difference"),
                "observed Stage B difference",
            ),
        )
    else:
        null = {
            "status": "not_reached_by_frozen_decision_order",
            "permutations": 0,
        }
    all_requirements = bool(gate["pre_null_requirements_met"]) and (
        _number(
            null.get("corrected_as_good_or_better_rate"),
            "Stage B null rate",
        )
        < 0.10
    )
    return {
        "horizons": horizon_results,
        "gate": {
            **gate,
            "temporal_null": null,
            "all_requirements_met": all_requirements,
        },
        "decision": (
            "alg_013_selection_required"
            if all_requirements
            else "target_future_increment_rejected"
        ),
    }


def _stage_a_rows(
    data: StudyData,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    plan: Mapping[str, object],
    *,
    permutation_index: int,
    projection_cache: dict[tuple[str, str, int], ResponseProjection],
    evaluation_scope: str = "future",
) -> tuple[
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
]:
    rows = []
    audits = []
    tolerance = _number(
        _mapping(plan, "diagnostics").get("numerical_tolerance"),
        "numerical tolerance",
    )
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            cutoff = max(task.created_at for task in origin.history)
            cache_key = (repository_id, cutoff, permutation_index)
            projection = projection_cache.get(cache_key)
            if projection is None:
                projection = fit_response_contrast_projection(
                    data,
                    target_repository_id=repository_id,
                    cutoff=cutoff,
                    tolerance=tolerance,
                    permutation_index=permutation_index,
                )
                projection_cache[cache_key] = projection
            if evaluation_scope not in {"future", "history"}:
                raise ValueError("Stage A evaluation scope is unsupported")
            evaluation_tasks = (
                origin.future if evaluation_scope == "future" else origin.history
            )
            evaluation_indices = [
                data.task_index[task.instance_id] for task in evaluation_tasks
            ]
            coordinates = transform_response_projection(
                data.embeddings[evaluation_indices],
                projection,
            )
            aucs = []
            for column, configuration_index in enumerate(
                projection.configuration_indices
            ):
                auc = roc_auc(
                    coordinates[:, column].tolist(),
                    data.outcomes[
                        evaluation_indices,
                        configuration_index,
                    ].tolist(),
                )
                if auc is not None:
                    aucs.append(auc)
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "valid_configuration_count": len(aucs),
                    "active_configuration_count": len(projection.configuration_indices),
                    "mean_auc": _mean(tuple(aucs)) if aucs else None,
                }
            )
            if permutation_index == 0:
                audits.append(
                    _projection_audit_row(
                        origin,
                        cutoff,
                        projection,
                    )
                )
    return tuple(rows), tuple(audits)


def _stage_b_rows(
    data: StudyData,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    plan: Mapping[str, object],
    *,
    horizon: int,
    projection_cache: dict[tuple[str, str, int], ResponseProjection],
) -> tuple[
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
]:
    import numpy as np

    rows = []
    audits = []
    tolerance = _number(
        _mapping(plan, "diagnostics").get("numerical_tolerance"),
        "numerical tolerance",
    )
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            cutoff = max(task.created_at for task in origin.history)
            cache_key = (repository_id, cutoff, 0)
            projection = projection_cache.get(cache_key)
            if projection is None:
                projection = fit_response_contrast_projection(
                    data,
                    target_repository_id=repository_id,
                    cutoff=cutoff,
                    tolerance=tolerance,
                )
                projection_cache[cache_key] = projection
            history_indices = [
                data.task_index[task.instance_id] for task in origin.history
            ]
            future_indices = [
                data.task_index[task.instance_id] for task in origin.future
            ]
            history = transform_response_projection(
                data.embeddings[history_indices],
                projection,
            )
            future = transform_response_projection(
                data.embeddings[future_indices],
                projection,
            ).mean(axis=0)
            forecast = ols_next_block_mean(history, horizon=horizon)
            baseline = history.mean(axis=0)
            recent = history[-horizon:].mean(axis=0)
            candidate_loss = float(np.square(forecast - future).mean())
            baseline_loss = float(np.square(baseline - future).mean())
            recent_loss = float(np.square(recent - future).mean())

            raw_history = data.embeddings[history_indices]
            raw_future = data.embeddings[future_indices].mean(axis=0)
            raw_forecast = ols_next_block_mean(raw_history, horizon=horizon)
            raw_baseline = raw_history.mean(axis=0)
            raw_candidate_loss = float(np.square(raw_forecast - raw_future).mean())
            raw_baseline_loss = float(np.square(raw_baseline - raw_future).mean())
            span_days = (
                parse_utc_timestamp(origin.future[-1].created_at)
                - parse_utc_timestamp(origin.future[0].created_at)
            ).total_seconds() / 86400.0
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "candidate_loss": candidate_loss,
                    "baseline_loss": baseline_loss,
                    "difference": candidate_loss - baseline_loss,
                    "recent_loss": recent_loss,
                    "raw_candidate_loss": raw_candidate_loss,
                    "raw_baseline_loss": raw_baseline_loss,
                    "future_calendar_span_days": span_days,
                }
            )
            audits.append(_projection_audit_row(origin, cutoff, projection))
    return tuple(rows), tuple(audits)


def _auc_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    by_repository: dict[str, list[float]] = defaultdict(list)
    invalid_by_repository: dict[str, int] = defaultdict(int)
    active_by_repository: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        active_by_repository[repository_id].append(
            _positive_integer(row, "active_configuration_count")
        )
        value = row.get("mean_auc")
        if value is None:
            invalid_by_repository[repository_id] += 1
        else:
            by_repository[repository_id].append(_number(value, "mean AUC"))
    repository_rows = []
    for repository_id in repository_ids:
        values = tuple(by_repository.get(repository_id, ()))
        repository_rows.append(
            {
                "repository_id": repository_id,
                "valid_origin_count": len(values),
                "invalid_origin_count": invalid_by_repository[repository_id],
                "mean_active_configuration_count": _mean(
                    tuple(active_by_repository[repository_id])
                ),
                "mean_auc": _mean(values) if values else None,
            }
        )
    if any(row["mean_auc"] is None for row in repository_rows):
        macro_auc = None
        leave_one = ()
        favorable = 0
        interval: Mapping[str, Any] = {"status": "unavailable"}
    else:
        values = tuple(float(row["mean_auc"]) for row in repository_rows)
        macro_auc = _mean(values)
        leave_one = tuple(
            {
                "omitted_repository_id": repository_ids[index],
                "macro_repository_auc": _mean(values[:index] + values[index + 1 :]),
            }
            for index in range(len(values))
        )
        favorable = sum(value > 0.5 for value in values)
        interval = (
            _repository_bootstrap(
                values,
                resamples=resamples,
                seed=seed,
            )
            if resamples
            else {"status": "not_requested"}
        )
    return {
        "repository_count": len(repository_ids),
        "origin_count": len(rows),
        "valid_origin_count": sum(
            int(row["valid_origin_count"]) for row in repository_rows
        ),
        "macro_repository_auc": macro_auc,
        "favorable_repository_count": favorable,
        "repository_rows": tuple(repository_rows),
        "leave_one_repository_out": leave_one,
        "repository_bootstrap_interval_95": interval,
    }


def _forecast_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        if repository_id in repository_ids:
            by_repository[repository_id].append(row)
    if set(by_repository) != set(repository_ids):
        raise ValueError("forecast summary does not cover planned repositories")
    repository_rows = []
    for repository_id in repository_ids:
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(by_repository[repository_id]),
                "candidate_loss": _mean(
                    tuple(
                        _number(row.get("candidate_loss"), "candidate loss")
                        for row in by_repository[repository_id]
                    )
                ),
                "baseline_loss": _mean(
                    tuple(
                        _number(row.get("baseline_loss"), "baseline loss")
                        for row in by_repository[repository_id]
                    )
                ),
                "difference": _mean(
                    tuple(
                        _number(row.get("difference"), "forecast difference")
                        for row in by_repository[repository_id]
                    )
                ),
                "recent_loss": _mean(
                    tuple(
                        _number(row.get("recent_loss"), "recent loss")
                        for row in by_repository[repository_id]
                    )
                ),
                "raw_candidate_loss": _mean(
                    tuple(
                        _number(row.get("raw_candidate_loss"), "raw candidate")
                        for row in by_repository[repository_id]
                    )
                ),
                "raw_baseline_loss": _mean(
                    tuple(
                        _number(row.get("raw_baseline_loss"), "raw baseline")
                        for row in by_repository[repository_id]
                    )
                ),
            }
        )
    differences = tuple(float(row["difference"]) for row in repository_rows)
    candidate_loss = _mean(
        tuple(float(row["candidate_loss"]) for row in repository_rows)
    )
    baseline_loss = _mean(tuple(float(row["baseline_loss"]) for row in repository_rows))
    raw_candidate_loss = _mean(
        tuple(float(row["raw_candidate_loss"]) for row in repository_rows)
    )
    raw_baseline_loss = _mean(
        tuple(float(row["raw_baseline_loss"]) for row in repository_rows)
    )
    candidate = {
        "macro_repository_loss": candidate_loss,
        "macro_repository_baseline_loss": baseline_loss,
        "macro_repository_difference": _mean(differences),
        "forecast_to_baseline_loss_ratio": (
            candidate_loss / baseline_loss if baseline_loss > 0.0 else None
        ),
        "relative_loss_reduction": (
            1.0 - candidate_loss / baseline_loss if baseline_loss > 0.0 else None
        ),
        "favorable_repository_count": sum(value < 0.0 for value in differences),
        "repository_rows": tuple(repository_rows),
        "leave_one_repository_out": tuple(
            {
                "omitted_repository_id": repository_ids[index],
                "macro_repository_difference": _mean(
                    differences[:index] + differences[index + 1 :]
                ),
            }
            for index in range(len(repository_rows))
        ),
    }
    return {
        "candidate": candidate,
        "recent_macro_repository_loss": _mean(
            tuple(float(row["recent_loss"]) for row in repository_rows)
        ),
        "raw_embedding": {
            "macro_repository_forecast_loss": raw_candidate_loss,
            "macro_repository_baseline_loss": raw_baseline_loss,
            "forecast_to_baseline_loss_ratio": (
                raw_candidate_loss / raw_baseline_loss
                if raw_baseline_loss > 0.0
                else None
            ),
        },
    }


def _calendar_span_summary(
    rows: Sequence[Mapping[str, object]],
) -> Mapping[str, Any]:
    spans = sorted(
        _number(row.get("future_calendar_span_days"), "calendar span") for row in rows
    )
    median = (
        spans[len(spans) // 2]
        if len(spans) % 2
        else (spans[len(spans) // 2 - 1] + spans[len(spans) // 2]) / 2.0
    )
    groups = {
        "short": tuple(
            row
            for row in rows
            if _number(row.get("future_calendar_span_days"), "calendar span") <= median
        ),
        "long": tuple(
            row
            for row in rows
            if _number(row.get("future_calendar_span_days"), "calendar span") > median
        ),
    }
    result: dict[str, Any] = {"median_days": median}
    for name, group in groups.items():
        repositories = tuple(
            sorted({_required_string(row, "repository_id") for row in group})
        )
        result[name] = {
            "origin_count": len(group),
            "repository_count": len(repositories),
            "macro_repository_difference": _mean(
                tuple(
                    _mean(
                        tuple(
                            _number(row.get("difference"), "span difference")
                            for row in group
                            if row.get("repository_id") == repository
                        )
                    )
                    for repository in repositories
                )
            ),
        }
    return result


def _stage_a_pre_null_gate(summary: Mapping[str, object]) -> bool:
    macro = summary.get("macro_repository_auc")
    if macro is None:
        return False
    interval = _mapping(summary, "repository_bootstrap_interval_95")
    return (
        _number(macro, "Stage A macro AUC") > 0.5
        and interval.get("status") == "available"
        and _number(interval.get("lower"), "Stage A interval lower") > 0.5
        and _integer(summary.get("favorable_repository_count"), "favorable count") >= 9
        and all(
            _number(row.get("macro_repository_auc"), "leave-one AUC") > 0.5
            for row in _mapping_sequence(summary, "leave_one_repository_out")
        )
        and all(
            _integer(row.get("valid_origin_count"), "valid Origin count") > 0
            and _number(
                row.get("mean_active_configuration_count"),
                "active configurations",
            )
            >= 1.0
            for row in _mapping_sequence(summary, "repository_rows")
        )
    )


def _stage_b_pre_null_gate(
    horizons: Mapping[str, Mapping[str, object]],
    *,
    primary_horizon: int,
    sensitivity_horizon: int,
) -> Mapping[str, Any]:
    primary = _mapping(horizons, str(primary_horizon))
    sensitivity = _mapping(horizons, str(sensitivity_horizon))
    primary_summary = _mapping(primary, "summary")
    primary_candidate = _mapping(primary_summary, "candidate")
    primary_deep = _mapping(_mapping(primary, "deep"), "candidate")
    sensitivity_candidate = _mapping(
        _mapping(sensitivity, "summary"),
        "candidate",
    )
    sensitivity_deep = _mapping(
        _mapping(sensitivity, "deep"),
        "candidate",
    )
    primary_ratio = _number(
        primary_candidate.get("forecast_to_baseline_loss_ratio"),
        "primary RCP loss ratio",
    )
    raw_ratio = _number(
        _mapping(primary_summary, "raw_embedding").get(
            "forecast_to_baseline_loss_ratio"
        ),
        "raw embedding loss ratio",
    )
    span = _mapping(primary, "calendar_span")
    requirements = {
        "h5_relative_loss_reduction_at_least_10_percent": primary_ratio <= 0.90,
        "h5_at_least_10_of_13_repositories_favorable": (
            int(primary_candidate.get("favorable_repository_count", -1)) >= 10
        ),
        "h5_every_leave_one_repository_out_negative": all(
            _number(row.get("macro_repository_difference"), "leave-one difference")
            < 0.0
            for row in _mapping_sequence(
                primary_candidate,
                "leave_one_repository_out",
            )
        ),
        "h5_deep_negative": (
            _number(
                primary_deep.get("macro_repository_difference"),
                "primary deep difference",
            )
            < 0.0
        ),
        "h5_better_than_recent": (
            _number(
                primary_candidate.get("macro_repository_loss"),
                "primary candidate loss",
            )
            < _number(
                primary_summary.get("recent_macro_repository_loss"),
                "primary recent loss",
            )
        ),
        "h5_relative_gain_better_than_raw_embedding_ols": (primary_ratio < raw_ratio),
        "h10_common_negative": (
            _number(
                sensitivity_candidate.get("macro_repository_difference"),
                "sensitivity difference",
            )
            < 0.0
        ),
        "h10_at_least_8_of_11_repositories_favorable": (
            int(sensitivity_candidate.get("favorable_repository_count", -1)) >= 8
        ),
        "h10_deep_negative": (
            _number(
                sensitivity_deep.get("macro_repository_difference"),
                "sensitivity deep difference",
            )
            < 0.0
        ),
        "short_calendar_span_negative": (
            _number(
                _mapping(span, "short").get("macro_repository_difference"),
                "short span difference",
            )
            < 0.0
        ),
        "long_calendar_span_negative": (
            _number(
                _mapping(span, "long").get("macro_repository_difference"),
                "long span difference",
            )
            < 0.0
        ),
    }
    return {
        "requirements": requirements,
        "pre_null_requirements_met": all(requirements.values()),
    }


def _stage_b_temporal_null(
    data: StudyData,
    selector_plan: Mapping[str, object],
    plan: Mapping[str, object],
    *,
    horizon: int,
    repository_ids: Sequence[str],
    projection_cache: dict[tuple[str, str, int], ResponseProjection],
    observed_difference: float,
) -> Mapping[str, Any]:
    import numpy as np

    origins = _origins_for_horizon(data.tasks, horizon, selector_plan)
    permutations = _positive_integer(
        _mapping(plan, "diagnostics"),
        "forecast_null_permutations",
    )
    null_values = []
    for permutation_index in range(1, permutations + 1):
        repository_differences = []
        for repository_id in repository_ids:
            ordered_indices = data.repository_indices[repository_id]
            shift = permutation_index % len(ordered_indices)
            if shift == 0:
                shift = 1
            shifted_indices = tuple(np.roll(ordered_indices, shift).tolist())
            origin_differences = []
            for origin in origins[repository_id]:
                cutoff = max(task.created_at for task in origin.history)
                projection = projection_cache[(repository_id, cutoff, 0)]
                history_count = len(origin.history)
                future_count = len(origin.future)
                history_indices = shifted_indices[:history_count]
                future_indices = shifted_indices[
                    history_count : history_count + future_count
                ]
                history = transform_response_projection(
                    data.embeddings[list(history_indices)],
                    projection,
                )
                future = transform_response_projection(
                    data.embeddings[list(future_indices)],
                    projection,
                ).mean(axis=0)
                forecast = ols_next_block_mean(history, horizon=horizon)
                baseline = history.mean(axis=0)
                origin_differences.append(
                    float(
                        np.square(forecast - future).mean()
                        - np.square(baseline - future).mean()
                    )
                )
            repository_differences.append(_mean(tuple(origin_differences)))
        null_values.append(_mean(tuple(repository_differences)))
    return _lower_tail_null(observed_difference, tuple(null_values))


def _origins_for_horizon(
    tasks: Sequence[TaskMetadata],
    horizon: int,
    selector_plan: Mapping[str, object],
) -> Mapping[str, tuple[RepositoryOrigin, ...]]:
    rolling = _mapping(selector_plan, "rolling_origin")
    return build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=horizon,
    )


def _build_study_data(
    tasks: Sequence[TaskMetadata],
    vectors: Mapping[str, Sequence[float]],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
) -> StudyData:
    import numpy as np

    task_rows = tuple(tasks)
    task_ids = tuple(task.instance_id for task in task_rows)
    if set(vectors) != set(task_ids):
        raise ValueError("response signal embeddings do not cover Tasks")
    embeddings = np.asarray(
        [vectors[task_id] for task_id in task_ids],
        dtype=np.float64,
    )
    outcomes = np.asarray(
        [
            [
                outcomes_by_configuration[configuration_id][task_id]
                for configuration_id in configuration_ids
            ]
            for task_id in task_ids
        ],
        dtype=np.float64,
    )
    task_index = {task_id: index for index, task_id in enumerate(task_ids)}
    repository_indices: dict[str, list[int]] = defaultdict(list)
    for index, task in enumerate(task_rows):
        repository_indices[task.repository_id].append(index)
    ordered_indices = {
        repository_id: tuple(
            sorted(
                indices,
                key=lambda index: (
                    task_rows[index].created_at,
                    task_rows[index].instance_id,
                ),
            )
        )
        for repository_id, indices in repository_indices.items()
    }
    repository_times = {
        repository_id: tuple(task_rows[index].created_at for index in indices)
        for repository_id, indices in ordered_indices.items()
    }
    return StudyData(
        tasks=task_rows,
        task_ids=task_ids,
        embeddings=embeddings,
        outcomes=outcomes,
        configuration_ids=tuple(configuration_ids),
        task_index=task_index,
        repository_indices=ordered_indices,
        repository_times=repository_times,
    )


def _permute_outcomes(
    outcomes: Any,
    *,
    permutation_index: int,
) -> Any:
    import numpy as np

    values = np.asarray(outcomes, dtype=np.float64)
    if values.ndim != 2 or permutation_index <= 0:
        raise ValueError("outcome permutation input is invalid")
    if len(values) == 1:
        return values.copy()
    shift = permutation_index % len(values)
    if shift == 0:
        shift = 1
    return np.roll(values, shift, axis=0)


def _projection_audit_row(
    origin: RepositoryOrigin,
    cutoff: str,
    projection: ResponseProjection,
) -> Mapping[str, object]:
    if (
        origin.repository_id in projection.training_repository_ids
        or projection.maximum_training_time > cutoff
    ):
        raise ValueError("response projection violates outer holdout or cutoff")
    return {
        "repository_id": origin.repository_id,
        "origin_id": origin.origin_id,
        "cutoff": cutoff,
        "training_repository_count": len(projection.training_repository_ids),
        "training_repository_ids": projection.training_repository_ids,
        "training_task_count": projection.training_task_count,
        "training_task_digest": projection.training_task_digest,
        "maximum_training_time": projection.maximum_training_time,
        "active_configuration_count": len(projection.configuration_indices),
        # The frozen v1 artifact named this field before the audit clarified
        # that its values are panel-column indices. Retain it byte-for-byte;
        # consumers must interpret it as indices, not configuration IDs.
        "active_configuration_ids": tuple(
            str(index) for index in projection.configuration_indices
        ),
        "projection_digest": projection.projection_digest,
    }


def _repository_bootstrap(
    values: Sequence[float],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    import numpy as np

    if not values or resamples <= 0:
        raise ValueError("repository bootstrap input is invalid")
    array = np.asarray(values, dtype=np.float64)
    generator = np.random.default_rng(seed)
    samples = array[
        generator.integers(
            0,
            len(array),
            size=(resamples, len(array)),
        )
    ].mean(axis=1)
    return {
        "status": "available",
        "resamples": resamples,
        "seed": seed,
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
    }


def _upper_tail_null(
    observed: float,
    null_values: Sequence[float],
) -> Mapping[str, Any]:
    as_good = sum(value >= observed for value in null_values)
    return {
        "status": "available",
        "permutations": len(null_values),
        "observed": observed,
        "null_values": tuple(null_values),
        "raw_as_good_or_better_rate": as_good / len(null_values),
        "corrected_as_good_or_better_rate": (as_good + 1) / (len(null_values) + 1),
    }


def _lower_tail_null(
    observed: float,
    null_values: Sequence[float],
) -> Mapping[str, Any]:
    as_good = sum(value <= observed for value in null_values)
    return {
        "status": "available",
        "permutations": len(null_values),
        "observed": observed,
        "null_values": tuple(null_values),
        "raw_as_good_or_better_rate": as_good / len(null_values),
        "corrected_as_good_or_better_rate": (as_good + 1) / (len(null_values) + 1),
    }


def _array_digest(
    arrays: Sequence[Any],
    *,
    prefix: Sequence[str],
) -> str:
    digest = hashlib.sha256()
    for value in prefix:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    for array in arrays:
        contiguous = array.astype(array.dtype.newbyteorder("<"), copy=False)
        shape = canonical_json(tuple(contiguous.shape)).encode("utf-8")
        dtype = str(contiguous.dtype).encode("ascii")
        digest.update(len(shape).to_bytes(8, "big"))
        digest.update(shape)
        digest.update(len(dtype).to_bytes(8, "big"))
        digest.update(dtype)
        digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _validate_bound_source(
    selector_plan: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    source = _mapping(plan, "source")
    selector_source = _mapping(selector_plan, "source")
    if (
        source.get("selector_plan_digest") != selector_plan.get("selector_plan_digest")
        or source.get("contract_digest") != selector_source.get("contract_digest")
        or source.get("panel_digest") != selector_source.get("panel_digest")
        or source.get("task_time_projection_digest")
        != selector_source.get("task_time_projection_digest")
        or source.get("task_count") != selector_source.get("task_count")
        or source.get("configuration_count")
        != selector_source.get("configuration_count")
    ):
        raise ValueError("response signal plan source identity changed")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _mapping(
    value: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, Mapping):
        raise ValueError(f"{key} must be an object")
    return nested


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    rows = value.get(key)
    if not isinstance(rows, Sequence) or isinstance(rows, str):
        raise ValueError(f"{key} must be an array")
    result = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"{key} rows must be objects")
        result.append(row)
    return tuple(result)


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{label} must be an array")
    result = tuple(value)
    if (
        not result
        or any(not isinstance(item, str) or not item for item in result)
        or len(result) != len(set(result))
    ):
        raise ValueError(f"{label} must contain unique nonempty strings")
    return result


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


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a number")
    return float(value)


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return fsum(values) / len(values)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("run", "diagnose-history"),
        default="run",
    )
    parser.add_argument("--task-content", type=Path, required=True)
    parser.add_argument("--task-times", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--panel-summary", type=Path, required=True)
    parser.add_argument("--resolved-outcomes", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--amendment", type=Path, default=DEFAULT_AMENDMENT)
    parser.add_argument(
        "--diagnostic-plan",
        type=Path,
        default=DEFAULT_DIAGNOSTIC_PLAN,
    )
    parser.add_argument("--rejected-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    common = {
        "task_content_path": args.task_content,
        "task_time_path": args.task_times,
        "embedding_path": args.embeddings,
        "panel_path": args.panel_summary,
        "resolved_path": args.resolved_outcomes,
        "plan_path": args.plan,
        "amendment_path": args.amendment,
    }
    if args.mode == "diagnose-history":
        if args.rejected_results is None:
            parser.error("--rejected-results is required for diagnose-history")
        result = run_history_auc_diagnostic(
            **common,
            rejected_results_path=args.rejected_results,
            diagnostic_plan_path=args.diagnostic_plan,
        )
    else:
        result = run_signal_audit(**common)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
