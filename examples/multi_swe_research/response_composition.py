#!/usr/bin/env python3
"""Audit pre-Origin response-composition forecast signal."""

from __future__ import annotations

# NumPy is supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
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
from examples.multi_swe_research.response_signal import roc_auc  # noqa: E402
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    load_content_manifest,
    load_public_outcomes,
    load_selector_plan,
    load_task_content,
    load_task_metadata,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "response-composition-plan.json"
PLAN_SCHEMA = "barcarolle_multi_swe_response_composition_plan_v1"
RESULT_SCHEMA = "barcarolle_multi_swe_response_composition_results_v1"
NUMPY_VERSION = "2.5.1"


@dataclass(frozen=True)
class CompositionData:
    tasks: tuple[TaskMetadata, ...]
    task_ids: tuple[str, ...]
    outcomes: Any
    configuration_ids: tuple[str, ...]
    task_index: Mapping[str, int]
    repository_indices: Mapping[str, tuple[int, ...]]
    repository_times: Mapping[str, tuple[str, ...]]


def load_response_composition_plan(
    path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("response composition plan schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "response_composition_plan_digest"
        }
    )
    if payload.get("response_composition_plan_digest") != expected:
        raise ValueError("response composition plan digest does not match")
    candidate = _mapping(payload, "candidate")
    if (
        candidate.get("algorithm_id") != "ALG-014"
        or candidate.get("short_name") != "PRCS"
    ):
        raise ValueError("response composition candidate changed")
    boundary = _mapping(payload, "resource_boundary")
    if any(
        boundary.get(key) != 0
        for key in (
            "paid_api_calls",
            "embedding_api_calls",
            "sealed_holdout_reads",
        )
    ):
        raise ValueError("response composition resource boundary changed")
    return payload


def leave_one_configuration_difficulty(outcomes: Any) -> Any:
    """Return each Task's solved fraction excluding the evaluated config."""
    import numpy as np

    values = np.asarray(outcomes, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[1] < 2
        or not bool(np.all((values == 0.0) | (values == 1.0)))
    ):
        raise ValueError("response outcomes must be a binary Task matrix")
    return (values.sum(axis=1, keepdims=True) - values) / (values.shape[1] - 1)


def prequential_expert_forecast(
    history: Any,
    future: Any,
    *,
    horizon: int,
    earlier_full_loss_sum: Any,
    earlier_recent_loss_sum: Any,
    earlier_origin_count: int,
    global_prior: Any,
) -> tuple[Any, Any, Any, Any, Any]:
    """Choose stationary or recent independently per held-out config."""
    import numpy as np

    history_values = np.asarray(history, dtype=np.float64)
    future_values = np.asarray(future, dtype=np.float64)
    full_loss_sum = np.asarray(earlier_full_loss_sum, dtype=np.float64)
    recent_loss_sum = np.asarray(earlier_recent_loss_sum, dtype=np.float64)
    prior = np.asarray(global_prior, dtype=np.float64)
    if (
        history_values.ndim != 2
        or future_values.ndim != 2
        or history_values.shape[1] != future_values.shape[1]
        or history_values.shape[0] < horizon
        or future_values.shape[0] != horizon
        or full_loss_sum.shape != (history_values.shape[1],)
        or recent_loss_sum.shape != (history_values.shape[1],)
        or prior.shape != (history_values.shape[1],)
        or isinstance(earlier_origin_count, bool)
        or earlier_origin_count < 0
    ):
        raise ValueError("prequential forecast inputs are invalid")
    full = history_values.mean(axis=0)
    recent = history_values[-horizon:].mean(axis=0)
    if earlier_origin_count:
        choose_recent = recent_loss_sum < full_loss_sum
    else:
        choose_recent = np.zeros(history_values.shape[1], dtype=bool)
    local = np.where(choose_recent, recent, full)
    local_mass = np.where(
        choose_recent,
        float(horizon),
        float(len(history_values)),
    )
    forecast = (local_mass * local + prior) / (local_mass + 1.0)
    future_mean = future_values.mean(axis=0)
    return forecast, local, full, recent, future_mean


def run_composition_audit(
    *,
    task_content_path: Path,
    task_time_path: Path,
    panel_path: Path,
    resolved_path: Path,
    plan_path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    """Run the frozen response-composition signal cascade."""
    import numpy as np

    if np.__version__ != NUMPY_VERSION:
        raise ValueError(
            f"NumPy version changed: expected {NUMPY_VERSION}, got {np.__version__}"
        )
    selector_plan = load_selector_plan()
    plan = load_response_composition_plan(plan_path)
    _validate_bound_source(selector_plan, plan)
    content_manifest = load_content_manifest()
    content_rows = load_task_content(task_content_path, content_manifest)
    task_ids = tuple(_required_string(row, "instance_id") for row in content_rows)
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
    data = _build_composition_data(
        tasks,
        outcomes_by_configuration,
        configuration_ids,
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
    difficulty = leave_one_configuration_difficulty(data.outcomes)

    stage_a_rows = _stage_a_rows(
        data,
        difficulty,
        origins,
        primary_repositories,
    )
    diagnostics = _mapping(plan, "diagnostics")
    stage_a_summary = _auc_summary(
        stage_a_rows,
        primary_repositories,
        resamples=_positive_integer(diagnostics, "bootstrap_resamples"),
        seed=_positive_integer(diagnostics, "bootstrap_seed"),
    )
    stage_a_pre_null = _stage_a_pre_null_gate(stage_a_summary)
    if stage_a_pre_null:
        null_values = []
        for permutation_index in range(
            1,
            _positive_integer(diagnostics, "stage_a_null_permutations") + 1,
        ):
            permuted = _circular_shift_outcomes(
                data,
                permutation_index=permutation_index,
            )
            null_rows = _stage_a_rows(
                data,
                leave_one_configuration_difficulty(permuted),
                origins,
                primary_repositories,
                labels=permuted,
            )
            null_values.append(
                _number(
                    _auc_summary(
                        null_rows,
                        primary_repositories,
                        resamples=0,
                        seed=0,
                    ).get("macro_repository_auc"),
                    "Stage A null AUC",
                )
            )
        stage_a_null = _upper_tail_null(
            _number(
                stage_a_summary.get("macro_repository_auc"),
                "Stage A AUC",
            ),
            tuple(null_values),
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
        "response_composition_plan_digest": plan.get(
            "response_composition_plan_digest"
        ),
        "selector_plan_digest": selector_plan.get("selector_plan_digest"),
        "outcome_diagnostics": outcome_diagnostics,
        "epistemic_status": plan.get("epistemic_status"),
        "stage_a": {
            "horizon": primary_horizon,
            "summary": stage_a_summary,
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
            else "cross_agent_response_signal_rejected"
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "sealed_holdout_reads": 0,
        },
        "claim_boundary": _mapping(plan, "research_contract").get("claim_boundary"),
    }
    if stage_a_pass:
        stage_b = _run_stage_b(
            data,
            difficulty,
            selector_plan,
            plan,
            primary_deep=primary_deep,
        )
        result["stage_b"] = stage_b
        result["decision"] = stage_b["decision"]
    result["response_composition_results_digest"] = canonical_digest(result)
    return result


def _run_stage_b(
    data: CompositionData,
    difficulty: Any,
    selector_plan: Mapping[str, object],
    plan: Mapping[str, object],
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
        rows = _stage_b_rows(
            data,
            difficulty,
            origins,
            repository_sets[horizon],
            horizon=horizon,
        )
        horizon_results[str(horizon)] = {
            "summary": _forecast_summary(rows, repository_sets[horizon]),
            "deep": _forecast_summary(rows, deep_sets[horizon]),
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
        diagnostics = _mapping(plan, "diagnostics")
        observed = _number(
            _mapping(
                _mapping(
                    horizon_results[str(primary_horizon)],
                    "summary",
                ),
                "candidate",
            ).get("macro_repository_difference"),
            "Stage B observed difference",
        )
        null_values = []
        for permutation_index in range(
            1,
            _positive_integer(diagnostics, "stage_b_null_permutations") + 1,
        ):
            shifted = _circular_shift_outcomes(
                data,
                permutation_index=permutation_index,
                preserve_response_vectors=True,
            )
            shifted_difficulty = leave_one_configuration_difficulty(shifted)
            null_rows = _stage_b_rows(
                data,
                shifted_difficulty,
                _origins_for_horizon(
                    data.tasks,
                    primary_horizon,
                    selector_plan,
                ),
                repository_sets[primary_horizon],
                horizon=primary_horizon,
            )
            null_values.append(
                _number(
                    _mapping(
                        _forecast_summary(
                            null_rows,
                            repository_sets[primary_horizon],
                        ),
                        "candidate",
                    ).get("macro_repository_difference"),
                    "Stage B null difference",
                )
            )
        temporal_null = _lower_tail_null(observed, tuple(null_values))
    else:
        temporal_null = {
            "status": "not_reached_by_frozen_decision_order",
            "permutations": 0,
        }
    all_requirements = bool(gate["pre_null_requirements_met"]) and (
        _number(
            temporal_null.get("corrected_as_good_or_better_rate"),
            "Stage B null rate",
        )
        < 0.10
    )
    return {
        "horizons": horizon_results,
        "gate": {
            **gate,
            "temporal_null": temporal_null,
            "all_requirements_met": all_requirements,
        },
        "decision": (
            "alg_014_selection_required"
            if all_requirements
            else "target_future_increment_rejected"
        ),
    }


def _stage_a_rows(
    data: CompositionData,
    difficulty: Any,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    *,
    labels: Any | None = None,
) -> tuple[Mapping[str, object], ...]:
    label_matrix = data.outcomes if labels is None else labels
    rows = []
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_indices = [
                data.task_index[task.instance_id] for task in origin.history
            ]
            aucs = []
            for configuration_index in range(len(data.configuration_ids)):
                auc = roc_auc(
                    difficulty[history_indices, configuration_index].tolist(),
                    label_matrix[
                        history_indices,
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
                    "mean_auc": _mean(tuple(aucs)) if aucs else None,
                }
            )
    return tuple(rows)


def _stage_b_rows(
    data: CompositionData,
    difficulty: Any,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    *,
    horizon: int,
) -> tuple[Mapping[str, object], ...]:
    import numpy as np

    rows = []
    for repository_id in repository_ids:
        full_loss_sum = np.zeros(len(data.configuration_ids), dtype=np.float64)
        recent_loss_sum = np.zeros(
            len(data.configuration_ids),
            dtype=np.float64,
        )
        earlier_origin_count = 0
        for origin in origins_by_repository[repository_id]:
            history_indices = [
                data.task_index[task.instance_id] for task in origin.history
            ]
            future_indices = [
                data.task_index[task.instance_id] for task in origin.future
            ]
            history = difficulty[history_indices]
            future = difficulty[future_indices]
            cutoff = max(task.created_at for task in origin.history)
            global_prior = _global_prior(
                data,
                difficulty,
                target_repository_id=repository_id,
                cutoff=cutoff,
            )
            forecast, local, full, recent, future_mean = prequential_expert_forecast(
                history,
                future,
                horizon=horizon,
                earlier_full_loss_sum=full_loss_sum,
                earlier_recent_loss_sum=recent_loss_sum,
                earlier_origin_count=earlier_origin_count,
                global_prior=global_prior,
            )
            candidate_loss = np.abs(forecast - future_mean)
            baseline_loss = np.abs(full - future_mean)
            recent_loss = np.abs(recent - future_mean)
            local_loss = np.abs(local - future_mean)
            global_loss = np.abs(global_prior - future_mean)
            if earlier_origin_count:
                choose_recent = recent_loss_sum < full_loss_sum
            else:
                choose_recent = np.zeros(
                    len(data.configuration_ids),
                    dtype=bool,
                )
            span_days = (
                parse_utc_timestamp(origin.future[-1].created_at)
                - parse_utc_timestamp(origin.future[0].created_at)
            ).total_seconds() / 86400.0
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "candidate_loss": float(candidate_loss.mean()),
                    "baseline_loss": float(baseline_loss.mean()),
                    "difference": float(candidate_loss.mean() - baseline_loss.mean()),
                    "recent_loss": float(recent_loss.mean()),
                    "local_without_prior_loss": float(local_loss.mean()),
                    "global_only_loss": float(global_loss.mean()),
                    "recent_expert_selection_rate": float(choose_recent.mean()),
                    "global_training_repository_count": _eligible_other_repository_count(
                        data,
                        target_repository_id=repository_id,
                        cutoff=cutoff,
                    ),
                    "future_calendar_span_days": span_days,
                }
            )
            full_loss_sum += baseline_loss
            recent_loss_sum += recent_loss
            earlier_origin_count += 1
    return tuple(rows)


def _global_prior(
    data: CompositionData,
    difficulty: Any,
    *,
    target_repository_id: str,
    cutoff: str,
) -> Any:
    import numpy as np

    repository_means = []
    for repository_id in sorted(data.repository_indices):
        if repository_id == target_repository_id:
            continue
        count = bisect_right(data.repository_times[repository_id], cutoff)
        indices = data.repository_indices[repository_id][:count]
        if indices:
            repository_means.append(difficulty[list(indices)].mean(axis=0))
    if not repository_means:
        raise ValueError("global response-composition prior has no repositories")
    return np.stack(repository_means).mean(axis=0)


def _eligible_other_repository_count(
    data: CompositionData,
    *,
    target_repository_id: str,
    cutoff: str,
) -> int:
    return sum(
        repository_id != target_repository_id
        and bisect_right(data.repository_times[repository_id], cutoff) > 0
        for repository_id in data.repository_indices
    )


def _circular_shift_outcomes(
    data: CompositionData,
    *,
    permutation_index: int,
    preserve_response_vectors: bool = False,
) -> Any:
    import numpy as np

    if permutation_index <= 0:
        raise ValueError("circular-shift index must be positive")
    shifted = np.empty_like(data.outcomes)
    for repository_offset, repository_id in enumerate(sorted(data.repository_indices)):
        indices = data.repository_indices[repository_id]
        rows = data.outcomes[list(indices)]
        if preserve_response_vectors:
            shift = (
                permutation_index * (2 * repository_offset + 1) + repository_offset + 1
            ) % len(rows)
            if shift == 0 and len(rows) > 1:
                shift = 1
            shifted[list(indices)] = np.roll(rows, shift, axis=0)
            continue
        for configuration_index in range(len(data.configuration_ids)):
            shift = (
                permutation_index * (2 * configuration_index + 1)
                + repository_offset
                + configuration_index
                + 1
            ) % len(rows)
            if shift == 0 and len(rows) > 1:
                shift = 1
            shifted[list(indices), configuration_index] = np.roll(
                rows[:, configuration_index],
                shift,
            )
    return shifted


def _auc_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    by_repository: dict[str, list[float]] = defaultdict(list)
    invalid_by_repository: dict[str, int] = defaultdict(int)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
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
                "mean_auc": _mean(values) if values else None,
            }
        )
    if any(row["mean_auc"] is None for row in repository_rows):
        return {
            "repository_count": len(repository_ids),
            "origin_count": len(rows),
            "valid_origin_count": sum(
                int(row["valid_origin_count"]) for row in repository_rows
            ),
            "macro_repository_auc": None,
            "favorable_repository_count": 0,
            "repository_rows": tuple(repository_rows),
            "leave_one_repository_out": (),
            "repository_bootstrap_interval_95": {"status": "unavailable"},
        }
    values = tuple(float(row["mean_auc"]) for row in repository_rows)
    return {
        "repository_count": len(repository_ids),
        "origin_count": len(rows),
        "valid_origin_count": sum(
            int(row["valid_origin_count"]) for row in repository_rows
        ),
        "macro_repository_auc": _mean(values),
        "favorable_repository_count": sum(value > 0.5 for value in values),
        "repository_rows": tuple(repository_rows),
        "leave_one_repository_out": tuple(
            {
                "omitted_repository_id": repository_ids[index],
                "macro_repository_auc": _mean(values[:index] + values[index + 1 :]),
            }
            for index in range(len(values))
        ),
        "repository_bootstrap_interval_95": (
            _repository_bootstrap(
                values,
                resamples=resamples,
                seed=seed,
            )
            if resamples
            else {"status": "not_requested"}
        ),
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
        raise ValueError("composition summary does not cover repositories")
    repository_rows = []
    for repository_id in repository_ids:
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(by_repository[repository_id]),
                **{
                    key: _mean(
                        tuple(
                            _number(row.get(key), key)
                            for row in by_repository[repository_id]
                        )
                    )
                    for key in (
                        "candidate_loss",
                        "baseline_loss",
                        "difference",
                        "recent_loss",
                        "local_without_prior_loss",
                        "global_only_loss",
                        "recent_expert_selection_rate",
                    )
                },
                "minimum_global_training_repository_count": min(
                    _positive_integer(
                        row,
                        "global_training_repository_count",
                    )
                    for row in by_repository[repository_id]
                ),
            }
        )
    differences = tuple(float(row["difference"]) for row in repository_rows)
    candidate_loss = _mean(
        tuple(float(row["candidate_loss"]) for row in repository_rows)
    )
    baseline_loss = _mean(tuple(float(row["baseline_loss"]) for row in repository_rows))
    return {
        "candidate": {
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
        },
        "recent_macro_repository_loss": _mean(
            tuple(float(row["recent_loss"]) for row in repository_rows)
        ),
        "local_without_prior_macro_repository_loss": _mean(
            tuple(float(row["local_without_prior_loss"]) for row in repository_rows)
        ),
        "global_only_macro_repository_loss": _mean(
            tuple(float(row["global_only_loss"]) for row in repository_rows)
        ),
        "recent_expert_selection_rate": _mean(
            tuple(float(row["recent_expert_selection_rate"]) for row in repository_rows)
        ),
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
    result: dict[str, Any] = {"median_days": median}
    for name, predicate in (
        ("short", lambda value: value <= median),
        ("long", lambda value: value > median),
    ):
        group = tuple(
            row
            for row in rows
            if predicate(
                _number(
                    row.get("future_calendar_span_days"),
                    "calendar span",
                )
            )
        )
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
        and _integer(
            summary.get("favorable_repository_count"),
            "favorable repository count",
        )
        >= 9
        and all(
            _number(row.get("macro_repository_auc"), "leave-one AUC") > 0.5
            for row in _mapping_sequence(summary, "leave_one_repository_out")
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
        "primary loss ratio",
    )
    span = _mapping(primary, "calendar_span")
    recent_rate = _number(
        primary_summary.get("recent_expert_selection_rate"),
        "recent expert rate",
    )
    requirements = {
        "h5_relative_loss_reduction_at_least_10_percent": primary_ratio <= 0.90,
        "h5_at_least_10_of_13_repositories_favorable": (
            _integer(
                primary_candidate.get("favorable_repository_count"),
                "primary favorable count",
            )
            >= 10
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
        "h5_no_worse_than_recent": (
            _number(
                primary_candidate.get("macro_repository_loss"),
                "primary candidate loss",
            )
            <= _number(
                primary_summary.get("recent_macro_repository_loss"),
                "primary recent loss",
            )
        ),
        "h5_no_worse_than_local_without_prior": (
            _number(
                primary_candidate.get("macro_repository_loss"),
                "primary candidate loss",
            )
            <= _number(
                primary_summary.get("local_without_prior_macro_repository_loss"),
                "local without prior loss",
            )
        ),
        "h10_common_negative": (
            _number(
                sensitivity_candidate.get("macro_repository_difference"),
                "sensitivity difference",
            )
            < 0.0
        ),
        "h10_at_least_8_of_11_repositories_favorable": (
            _integer(
                sensitivity_candidate.get("favorable_repository_count"),
                "sensitivity favorable count",
            )
            >= 8
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
        "recent_expert_rate_between_0_10_and_0_90": (0.10 <= recent_rate <= 0.90),
    }
    return {
        "requirements": requirements,
        "pre_null_requirements_met": all(requirements.values()),
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


def _build_composition_data(
    tasks: Sequence[TaskMetadata],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
) -> CompositionData:
    import numpy as np

    task_rows = tuple(tasks)
    task_ids = tuple(task.instance_id for task in task_rows)
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
    return CompositionData(
        tasks=task_rows,
        task_ids=task_ids,
        outcomes=outcomes,
        configuration_ids=tuple(configuration_ids),
        task_index=task_index,
        repository_indices=ordered_indices,
        repository_times=repository_times,
    )


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
        raise ValueError("response composition source identity changed")


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
    parser.add_argument("--task-content", type=Path, required=True)
    parser.add_argument("--task-times", type=Path, required=True)
    parser.add_argument("--panel-summary", type=Path, required=True)
    parser.add_argument("--resolved-outcomes", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_composition_audit(
        task_content_path=args.task_content,
        task_time_path=args.task_times,
        panel_path=args.panel_summary,
        resolved_path=args.resolved_outcomes,
        plan_path=args.plan,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
