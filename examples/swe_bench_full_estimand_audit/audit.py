#!/usr/bin/env python3
"""Audit what SWE-bench Full rolling-origin pass-rate MAE measures."""

from __future__ import annotations

# The reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false
import argparse
import json
import random
import sys
from collections.abc import Mapping, Sequence
from hashlib import sha256
from itertools import pairwise
from math import fsum, isfinite, sqrt
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest
from examples.multi_repository_study.public_replay import (
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.swe_bench_full_development.diagnostic import (
    select_future_oracle_memberships,
)
from examples.swe_bench_full_transfer.study import (
    DEFAULT_RESULT_DIRECTORY as SOURCE_RESULT_DIRECTORY,
)
from examples.swe_bench_full_transfer.study import (
    load_full_inputs,
)
from examples.swe_bench_full_transfer.study import (
    load_plan as load_source_plan,
)

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT = HERE / "evidence" / "summary.json"

PLAN_SCHEMA = "barcarolle_swe_bench_full_estimand_audit_plan_v1"
SUMMARY_SCHEMA = "barcarolle_swe_bench_full_estimand_audit_summary_v1"
SUMMARY_DIGEST_KEY = "summary_digest"

ALGORITHM_IDS = (
    "full_history",
    "ordinary_recency",
    "stationary_response_match",
    "ALG-010",
    "ALG-015U",
    "ALG-016U",
)
CANDIDATE_IDS = ALGORITHM_IDS[1:]


def load_plan(
    path: Path = DEFAULT_PLAN,
    *,
    verify_bindings: bool = True,
) -> Mapping[str, Any]:
    """Load the outcome-open audit contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("estimand audit plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("estimand audit plan digest does not match")
    payload["plan_digest"] = digest

    frame = _mapping(payload, "frame")
    if (
        tuple(frame.get("horizons", ())) != (5, 10, 20, 40)
        or _positive_integer(frame, "minimum_initial_history_tasks") != 20
        or _positive_integer(frame, "selection_budget_tasks") != 10
    ):
        raise ValueError("estimand audit frame changed")
    diagnostics = _mapping(payload, "diagnostics")
    if _positive_integer(diagnostics, "permutation_replicates") != 2000:
        raise ValueError("estimand audit permutation count changed")
    authority = _mapping(payload, "authority")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "sealed_swe_bench_verified_agent_reads",
        "algorithm_changes",
        "core_schema_changes",
    ):
        if authority.get(key) != 0:
            raise ValueError("estimand audit authority changed")

    if verify_bindings:
        for binding in _mapping(payload, "bound_artifacts").values():
            if not isinstance(binding, Mapping):
                raise ValueError("bound artifact must be an object")
            bound_path = REPOSITORY_ROOT / _required_string(binding, "path")
            if _file_sha256(bound_path) != _required_string(
                binding,
                "file_sha256",
            ):
                raise ValueError(f"bound artifact changed: {bound_path}")
            logical_key = binding.get("logical_digest_key")
            if logical_key is not None:
                bound_payload = _load_mapping(bound_path)
                if not isinstance(logical_key, str) or bound_payload.get(
                    logical_key
                ) != binding.get("logical_digest"):
                    raise ValueError(f"bound logical digest changed: {bound_path}")
        implementation = _mapping(payload, "implementation")
        if _file_sha256(Path(__file__)) != _required_string(
            implementation,
            "audit_file_sha256",
        ):
            raise ValueError("estimand audit implementation changed")
    return payload


def run_audit(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    """Run all diagnostics from the already-open Task and outcome matrix."""
    source_plan_path = _bound_path(plan, "source_plan")
    source_plan = load_source_plan(source_plan_path)
    source = _mapping(source_plan, "source")
    tasks, outcomes, _, metadata, identities = load_full_inputs(
        plan=source_plan,
        dataset_path=REPOSITORY_ROOT / _required_string(source, "local_path"),
        result_directory=SOURCE_RESULT_DIRECTORY,
    )
    development_result = _load_mapping(_bound_path(plan, "development_result"))
    _validate_development_result(development_result, plan, identities)
    diagnostic_result = _load_mapping(_bound_path(plan, "diagnostic_result"))
    _validate_diagnostic_result(diagnostic_result, plan, identities)

    repository_ids = _repository_ids(source_plan)
    frame = _mapping(plan, "frame")
    minimum_history = _positive_integer(
        frame,
        "minimum_initial_history_tasks",
    )
    budget = _positive_integer(frame, "selection_budget_tasks")
    permutation_replicates = _positive_integer(
        _mapping(plan, "diagnostics"),
        "permutation_replicates",
    )
    permutation_seed = _positive_integer(
        _mapping(plan, "diagnostics"),
        "permutation_seed",
    )

    tasks_by_repository: dict[str, tuple[TaskMetadata, ...]] = {}
    for repository_id in repository_ids:
        tasks_by_repository[repository_id] = tuple(
            sorted(
                (task for task in tasks if task.repository_id == repository_id),
                key=lambda task: (task.created_at, task.instance_id),
            )
        )

    agent_groups = _agent_groups(metadata)
    denominator = summarize_denominator(
        tasks_by_repository,
        outcomes,
        agent_groups,
    )
    horizons = {}
    rows_by_horizon: dict[int, tuple[Mapping[str, Any], ...]] = {}
    for horizon in tuple(frame["horizons"]):
        horizon_origins = build_repository_origins(
            tuple(
                task
                for repository_id in repository_ids
                for task in tasks_by_repository[repository_id]
            ),
            minimum_initial_history_tasks=minimum_history,
            future_block_tasks=horizon,
        )
        eligible_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id in horizon_origins
        )
        origins = {
            repository_id: horizon_origins[repository_id]
            for repository_id in eligible_repository_ids
        }
        rows = build_horizon_rows(origins, outcomes)
        rows_by_horizon[horizon] = rows
        horizon_summary: dict[str, Any] = {
            "horizon": horizon,
            "repository_count": len(eligible_repository_ids),
            "repository_ids": eligible_repository_ids,
            "origin_count": sum(len(origins[row]) for row in origins),
            "agent_origin_row_count": len(rows),
            "future_blocks": summarize_future_blocks(
                rows,
                repository_ids=eligible_repository_ids,
                budget=budget,
            ),
            "variance_decomposition": variance_decomposition(
                rows,
                repository_ids=eligible_repository_ids,
            ),
            "temporal_reliability": temporal_reliability(
                rows,
                origins,
                outcomes,
                repository_ids=eligible_repository_ids,
                horizon=horizon,
                permutation_replicates=permutation_replicates,
                permutation_seed=permutation_seed + horizon,
            ),
            "cell_rows": summarize_cells(
                rows,
                denominator,
                repository_ids=eligible_repository_ids,
            ),
        }
        if str(horizon) in _mapping(development_result, "horizons"):
            horizon_summary["candidate_audit"] = summarize_candidates(
                _mapping(
                    _mapping(development_result, "horizons"),
                    str(horizon),
                ),
                horizon_summary["cell_rows"],
                agent_groups,
                repository_ids=eligible_repository_ids,
            )
            horizon_summary["future_open_oracle_audit"] = summarize_oracles(
                origins,
                outcomes,
                _mapping(
                    _mapping(diagnostic_result, "horizons"),
                    str(horizon),
                ),
                repository_ids=eligible_repository_ids,
                budget=budget,
            )
        horizons[str(horizon)] = horizon_summary

    common_repositories = tuple(
        repository_id
        for repository_id in repository_ids
        if all(
            any(
                row["repository_id"] == repository_id
                for row in rows_by_horizon[horizon]
            )
            for horizon in rows_by_horizon
        )
    )
    horizon_scaling = summarize_horizon_scaling(
        rows_by_horizon,
        common_repositories,
    )

    result: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "epistemic_status": (
            "outcome-open post-anomaly estimand and reliability audit"
        ),
        "input_identities": dict(identities),
        "agent_groups": agent_groups,
        "denominator": denominator,
        "horizons": horizons,
        "horizon_scaling": horizon_scaling,
        "diagnosis": diagnose(horizons),
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result[SUMMARY_DIGEST_KEY] = canonical_digest(result)
    return result


def summarize_denominator(
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    outcomes: Mapping[str, Mapping[str, int]],
    agent_groups: Mapping[str, Sequence[str]],
) -> Mapping[str, Any]:
    """Describe fixed Agent-by-repository pass-rate heterogeneity."""
    cell_rows = []
    for repository_id, tasks in tasks_by_repository.items():
        task_ids = tuple(task.instance_id for task in tasks)
        for agent_id in sorted(outcomes):
            rate = _mean(tuple(outcomes[agent_id][task_id] for task_id in task_ids))
            cell_rows.append(
                {
                    "repository_id": repository_id,
                    "target_agent_id": agent_id,
                    "task_count": len(task_ids),
                    "pass_rate": rate,
                }
            )
    rates = tuple(row["pass_rate"] for row in cell_rows)
    repository_rows = []
    for repository_id in tasks_by_repository:
        source = tuple(
            row["pass_rate"]
            for row in cell_rows
            if row["repository_id"] == repository_id
        )
        repository_rows.append(
            {
                "repository_id": repository_id,
                "agent_mean_pass_rate": _mean(source),
                "minimum_agent_pass_rate": min(source),
                "maximum_agent_pass_rate": max(source),
            }
        )
    group_rows = {}
    for group_id, agent_ids in agent_groups.items():
        group_rates = tuple(
            row["pass_rate"] for row in cell_rows if row["target_agent_id"] in agent_ids
        )
        group_rows[group_id] = {
            "agent_count": len(agent_ids),
            "cell_count": len(group_rates),
            "mean_pass_rate": _mean(group_rates),
            "minimum_pass_rate": min(group_rates),
            "maximum_pass_rate": max(group_rates),
            "cells_below_0_10": sum(value < 0.10 for value in group_rates),
            "cells_above_0_50": sum(value > 0.50 for value in group_rates),
        }
    return {
        "repository_count": len(tasks_by_repository),
        "target_agent_count": len(outcomes),
        "cell_count": len(cell_rows),
        "cell_pass_rate": {
            "minimum": min(rates),
            "median": _quantile(rates, 0.5),
            "maximum": max(rates),
            "cells_below_0_10": sum(value < 0.10 for value in rates),
            "cells_above_0_50": sum(value > 0.50 for value in rates),
        },
        "group_rows": group_rows,
        "repository_rows": tuple(repository_rows),
        "cell_rows": tuple(cell_rows),
    }


def build_horizon_rows(
    origins: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes: Mapping[str, Mapping[str, int]],
) -> tuple[Mapping[str, Any], ...]:
    """Build direct-rate rows without running a Selector."""
    rows = []
    for repository_id, repository_origins in origins.items():
        for origin_index, origin in enumerate(repository_origins):
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            horizon = len(future_ids)
            for agent_id in sorted(outcomes):
                history_values = tuple(
                    outcomes[agent_id][task_id] for task_id in history_ids
                )
                future_values = tuple(
                    outcomes[agent_id][task_id] for task_id in future_ids
                )
                future_rate = _mean(future_values)
                full_rate = _mean(history_values)
                previous_rate = (
                    _mean(history_values[-horizon:])
                    if len(history_values) >= horizon
                    else None
                )
                rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "origin_index": origin_index,
                        "target_agent_id": agent_id,
                        "history_task_count": len(history_values),
                        "future_rate": future_rate,
                        "full_history_rate": full_rate,
                        "full_history_loss": abs(full_rate - future_rate),
                        "previous_block_rate": previous_rate,
                        "previous_block_loss": (
                            abs(previous_rate - future_rate)
                            if previous_rate is not None
                            else None
                        ),
                        "zero_loss": future_rate,
                        "one_loss": 1.0 - future_rate,
                    }
                )
    return tuple(rows)


def summarize_future_blocks(
    rows: Sequence[Mapping[str, Any]],
    *,
    repository_ids: Sequence[str],
    budget: int,
) -> Mapping[str, Any]:
    """Report direct-MAE baselines and the future-block outcome landscape."""
    future_rates = tuple(_number(row["future_rate"]) for row in rows)
    previous_rows = tuple(row for row in rows if row["previous_block_loss"] is not None)
    metrics = {
        "mean_future_pass_rate": _macro_mean(
            rows,
            "future_rate",
            repository_ids,
        ),
        "zero_future_block_share": _macro_indicator(
            rows,
            "future_rate",
            0.0,
            repository_ids,
        ),
        "one_future_block_share": _macro_indicator(
            rows,
            "future_rate",
            1.0,
            repository_ids,
        ),
        "always_zero_mae": _macro_mean(
            rows,
            "zero_loss",
            repository_ids,
        ),
        "always_one_mae": _macro_mean(
            rows,
            "one_loss",
            repository_ids,
        ),
        "full_history_mae": _macro_mean(
            rows,
            "full_history_loss",
            repository_ids,
        ),
        "previous_block_mae": (
            _macro_mean(
                previous_rows,
                "previous_block_loss",
                repository_ids,
            )
            if previous_rows
            else None
        ),
        "previous_block_row_count": len(previous_rows),
        "selection_rate_grid_lower_bound_mae": _macro_callable(
            rows,
            lambda row: min(
                abs(_number(row["future_rate"]) - successes / budget)
                for successes in range(budget + 1)
            ),
            repository_ids,
        ),
    }
    return {
        **metrics,
        "pooled_future_pass_rate": _mean(future_rates),
        "pooled_zero_future_block_share": _mean(
            tuple(value == 0.0 for value in future_rates)
        ),
        "pooled_one_future_block_share": _mean(
            tuple(value == 1.0 for value in future_rates)
        ),
    }


def variance_decomposition(
    rows: Sequence[Mapping[str, Any]],
    *,
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Decompose realized future-block rates with future-open static means."""
    import numpy as np

    agent_ids = tuple(sorted({str(row["target_agent_id"]) for row in rows}))
    repository_ids = tuple(repository_ids)
    weights = _repository_equal_weights(rows, repository_ids)
    values = np.asarray(
        [_number(row["future_rate"]) for row in rows],
        dtype=np.float64,
    )
    weight_array = np.asarray(weights, dtype=np.float64)
    global_mean = float(np.sum(weight_array * values))

    agent_means = {
        agent_id: _weighted_group_mean(
            rows,
            weights,
            values,
            lambda row, value=agent_id: row["target_agent_id"] == value,
        )
        for agent_id in agent_ids
    }
    repository_means = {
        repository_id: _weighted_group_mean(
            rows,
            weights,
            values,
            lambda row, value=repository_id: row["repository_id"] == value,
        )
        for repository_id in repository_ids
    }
    cell_means = {
        (agent_id, repository_id): _weighted_group_mean(
            rows,
            weights,
            values,
            lambda row, a=agent_id, r=repository_id: (
                row["target_agent_id"] == a and row["repository_id"] == r
            ),
        )
        for agent_id in agent_ids
        for repository_id in repository_ids
    }

    design = np.ones(
        (len(rows), 1 + len(agent_ids) - 1 + len(repository_ids) - 1),
        dtype=np.float64,
    )
    for index, row in enumerate(rows):
        for offset, agent_id in enumerate(agent_ids[1:], start=1):
            design[index, offset] = float(row["target_agent_id"] == agent_id)
        start = len(agent_ids)
        for offset, repository_id in enumerate(repository_ids[1:], start=start):
            design[index, offset] = float(row["repository_id"] == repository_id)
    root_weights = np.sqrt(weight_array)
    coefficients, *_ = np.linalg.lstsq(
        design * root_weights[:, None],
        values * root_weights,
        rcond=None,
    )
    predictions = {
        "global": np.full(len(rows), global_mean, dtype=np.float64),
        "agent": np.asarray(
            [agent_means[str(row["target_agent_id"])] for row in rows],
            dtype=np.float64,
        ),
        "repository": np.asarray(
            [repository_means[str(row["repository_id"])] for row in rows],
            dtype=np.float64,
        ),
        "agent_plus_repository": design @ coefficients,
        "agent_by_repository": np.asarray(
            [
                cell_means[
                    (
                        str(row["target_agent_id"]),
                        str(row["repository_id"]),
                    )
                ]
                for row in rows
            ],
            dtype=np.float64,
        ),
        "expanding_full_history": np.asarray(
            [_number(row["full_history_rate"]) for row in rows],
            dtype=np.float64,
        ),
    }
    mse = {
        model_id: float(np.sum(weight_array * np.square(values - prediction)))
        for model_id, prediction in predictions.items()
    }
    global_mse = mse["global"]
    return {
        "status": (
            "future-open descriptive variance attribution; these are not "
            "deployable forecasts"
        ),
        "orthogonal_components": _orthogonal_variance_components(
            rows,
            repository_ids,
        ),
        "future_open_static_model_mse": {
            "weighted_mse": mse,
            "fraction_below_global_mse": {
                model_id: (1.0 - value / global_mse if global_mse > 0.0 else None)
                for model_id, value in mse.items()
            },
        },
    }


def summarize_horizon_scaling(
    rows_by_horizon: Mapping[int, Sequence[Mapping[str, Any]]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Check whether within-cell block variance scales approximately as 1/H."""
    points = []
    for horizon in sorted(rows_by_horizon):
        rows = tuple(
            row
            for row in rows_by_horizon[horizon]
            if row["repository_id"] in repository_ids
        )
        components = _orthogonal_variance_components(rows, repository_ids)
        common_block = _number(components["component_variance"]["common_block"])
        residual = _number(components["component_variance"]["agent_by_block_residual"])
        points.append(
            {
                "horizon": horizon,
                "inverse_horizon": 1.0 / horizon,
                "common_block_variance": common_block,
                "agent_by_block_residual_variance": residual,
                "within_cell_dynamic_variance": common_block + residual,
            }
        )
    dynamic_fit = _linear_fit(
        tuple(_number(row["inverse_horizon"]) for row in points),
        tuple(_number(row["within_cell_dynamic_variance"]) for row in points),
    )
    common_fit = _linear_fit(
        tuple(_number(row["inverse_horizon"]) for row in points),
        tuple(_number(row["common_block_variance"]) for row in points),
    )
    residual_fit = _linear_fit(
        tuple(_number(row["inverse_horizon"]) for row in points),
        tuple(_number(row["agent_by_block_residual_variance"]) for row in points),
    )
    return {
        "repository_ids": tuple(repository_ids),
        "repository_count": len(repository_ids),
        "points": tuple(points),
        "within_cell_dynamic_variance_fit": dynamic_fit,
        "common_block_variance_fit": common_fit,
        "agent_by_block_residual_variance_fit": residual_fit,
        "interpretation": (
            "A near-linear relation with 1/H is consistent with finite-block "
            "averaging dominating the within-cell variation. The four nested "
            "coarsenings are descriptive, not independent observations or an "
            "IID noise proof."
        ),
    }


def _orthogonal_variance_components(
    rows: Sequence[Mapping[str, Any]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Decompose future block rates under the repository-equal measure."""
    agent_ids = tuple(sorted({str(row["target_agent_id"]) for row in rows}))
    repository_ids = tuple(repository_ids)
    origin_ids = {
        repository_id: tuple(
            dict.fromkeys(
                str(row["origin_id"])
                for row in rows
                if row["repository_id"] == repository_id
            )
        )
        for repository_id in repository_ids
    }
    value_lookup = {
        (
            str(row["repository_id"]),
            str(row["origin_id"]),
            str(row["target_agent_id"]),
        ): _number(row["future_rate"])
        for row in rows
    }
    grand = _mean(
        tuple(
            _mean(
                tuple(
                    value_lookup[(repository_id, origin_id, agent_id)]
                    for origin_id in origin_ids[repository_id]
                    for agent_id in agent_ids
                )
            )
            for repository_id in repository_ids
        )
    )
    agent_mean = {
        agent_id: _mean(
            tuple(
                _mean(
                    tuple(
                        value_lookup[(repository_id, origin_id, agent_id)]
                        for origin_id in origin_ids[repository_id]
                    )
                )
                for repository_id in repository_ids
            )
        )
        for agent_id in agent_ids
    }
    repository_mean = {
        repository_id: _mean(
            tuple(
                value_lookup[(repository_id, origin_id, agent_id)]
                for origin_id in origin_ids[repository_id]
                for agent_id in agent_ids
            )
        )
        for repository_id in repository_ids
    }
    cell_mean = {
        (repository_id, agent_id): _mean(
            tuple(
                value_lookup[(repository_id, origin_id, agent_id)]
                for origin_id in origin_ids[repository_id]
            )
        )
        for repository_id in repository_ids
        for agent_id in agent_ids
    }
    block_mean = {
        (repository_id, origin_id): _mean(
            tuple(
                value_lookup[(repository_id, origin_id, agent_id)]
                for agent_id in agent_ids
            )
        )
        for repository_id in repository_ids
        for origin_id in origin_ids[repository_id]
    }

    agent_variance = _mean(
        tuple((agent_mean[agent_id] - grand) ** 2 for agent_id in agent_ids)
    )
    repository_variance = _mean(
        tuple(
            (repository_mean[repository_id] - grand) ** 2
            for repository_id in repository_ids
        )
    )
    interaction_variance = _mean(
        tuple(
            (
                cell_mean[(repository_id, agent_id)]
                - agent_mean[agent_id]
                - repository_mean[repository_id]
                + grand
            )
            ** 2
            for repository_id in repository_ids
            for agent_id in agent_ids
        )
    )
    common_block_variance = _mean(
        tuple(
            _mean(
                tuple(
                    (
                        block_mean[(repository_id, origin_id)]
                        - repository_mean[repository_id]
                    )
                    ** 2
                    for origin_id in origin_ids[repository_id]
                )
            )
            for repository_id in repository_ids
        )
    )
    residual_variance = _mean(
        tuple(
            _mean(
                tuple(
                    (
                        value_lookup[(repository_id, origin_id, agent_id)]
                        - cell_mean[(repository_id, agent_id)]
                        - block_mean[(repository_id, origin_id)]
                        + repository_mean[repository_id]
                    )
                    ** 2
                    for origin_id in origin_ids[repository_id]
                    for agent_id in agent_ids
                )
            )
            for repository_id in repository_ids
        )
    )
    total_variance = _macro_callable(
        rows,
        lambda row: (_number(row["future_rate"]) - grand) ** 2,
        repository_ids,
    )
    components = {
        "agent": agent_variance,
        "repository": repository_variance,
        "agent_by_repository": interaction_variance,
        "common_block": common_block_variance,
        "agent_by_block_residual": residual_variance,
    }
    component_sum = fsum(components.values())
    stable = agent_variance + repository_variance + interaction_variance
    dynamic = common_block_variance + residual_variance
    return {
        "grand_mean": grand,
        "total_variance": total_variance,
        "component_variance": components,
        "component_share": {
            key: value / total_variance if total_variance > 0.0 else None
            for key, value in components.items()
        },
        "stable_agent_repository_fraction": (
            stable / total_variance if total_variance > 0.0 else None
        ),
        "within_cell_block_fraction": (
            dynamic / total_variance if total_variance > 0.0 else None
        ),
        "absolute_additivity_error": abs(total_variance - component_sum),
        "component_semantics": {
            "common_block": (
                "panel-wide fluctuation shared by Agents inside a repository "
                "block; not a causal calendar trend"
            ),
            "agent_by_block_residual": (
                "remaining Agent-specific block variation; not identified as "
                "sampling noise"
            ),
        },
    }


def temporal_reliability(
    rows: Sequence[Mapping[str, Any]],
    origins: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes: Mapping[str, Mapping[str, int]],
    *,
    repository_ids: Sequence[str],
    horizon: int,
    permutation_replicates: int,
    permutation_seed: int,
) -> Mapping[str, Any]:
    """Measure block stability without presenting it as the primary outcome."""
    sequences: dict[tuple[str, str], tuple[float, ...]] = {}
    for repository_id in repository_ids:
        for agent_id in sorted(outcomes):
            sequences[(repository_id, agent_id)] = tuple(
                _number(row["future_rate"])
                for row in rows
                if row["repository_id"] == repository_id
                and row["target_agent_id"] == agent_id
            )

    adjacent_x = []
    adjacent_y = []
    centered_x = []
    centered_y = []
    for sequence in sequences.values():
        cell_mean = _mean(sequence)
        for left, right in pairwise(sequence):
            adjacent_x.append(left)
            adjacent_y.append(right)
            centered_x.append(left - cell_mean)
            centered_y.append(right - cell_mean)

    observed_covariance = _repository_equal_adjacent_covariance(
        sequences,
        repository_ids,
    )
    generator = random.Random(permutation_seed)
    null_values = []
    for _ in range(permutation_replicates):
        permuted = {}
        for key, sequence in sequences.items():
            values = list(sequence)
            generator.shuffle(values)
            permuted[key] = tuple(values)
        null_values.append(
            _repository_equal_adjacent_covariance(
                permuted,
                repository_ids,
            )
        )
    as_large = (1 + sum(value >= observed_covariance for value in null_values)) / (
        permutation_replicates + 1
    )

    split_rows = []
    origin_lookup = {
        origin.origin_id: origin
        for repository_origins in origins.values()
        for origin in repository_origins
    }
    for row in rows:
        origin = origin_lookup[str(row["origin_id"])]
        future_ids = tuple(task.instance_id for task in origin.future)
        agent_id = str(row["target_agent_id"])
        left = tuple(
            outcomes[agent_id][task_id]
            for index, task_id in enumerate(future_ids)
            if index % 2 == 0
        )
        right = tuple(
            outcomes[agent_id][task_id]
            for index, task_id in enumerate(future_ids)
            if index % 2 == 1
        )
        if left and right:
            split_rows.append(
                {
                    "repository_id": row["repository_id"],
                    "target_agent_id": agent_id,
                    "left": _mean(left),
                    "right": _mean(right),
                }
            )
    split_left = tuple(_number(row["left"]) for row in split_rows)
    split_right = tuple(_number(row["right"]) for row in split_rows)
    split_centered_left = []
    split_centered_right = []
    for repository_id in repository_ids:
        for agent_id in sorted(outcomes):
            cell = tuple(
                row
                for row in split_rows
                if row["repository_id"] == repository_id
                and row["target_agent_id"] == agent_id
            )
            if not cell:
                continue
            left_mean = _mean(tuple(_number(row["left"]) for row in cell))
            right_mean = _mean(tuple(_number(row["right"]) for row in cell))
            split_centered_left.extend(_number(row["left"]) - left_mean for row in cell)
            split_centered_right.extend(
                _number(row["right"]) - right_mean for row in cell
            )

    observed_variances = []
    binomial_variances = []
    for sequence in sequences.values():
        if len(sequence) < 2:
            continue
        cell_mean = _mean(sequence)
        observed_variances.append(_sample_variance(sequence))
        binomial_variances.append(cell_mean * (1.0 - cell_mean) / horizon)
    observed_variance = _mean(tuple(observed_variances))
    binomial_variance = _mean(tuple(binomial_variances))
    residual_signal = _cross_agent_residual_signal(rows, repository_ids)

    return {
        "adjacent_pair_count": len(adjacent_x),
        "raw_adjacent_block_correlation": _correlation(
            adjacent_x,
            adjacent_y,
        ),
        "within_cell_adjacent_block_correlation": _correlation(
            centered_x,
            centered_y,
        ),
        "repository_equal_within_cell_adjacent_covariance": (observed_covariance),
        "order_permutation_null": {
            "replicates": permutation_replicates,
            "seed": permutation_seed,
            "as_large_or_larger_rate": as_large,
            "null_mean": _mean(tuple(null_values)),
            "null_quantiles": {
                "0.025": _quantile(tuple(null_values), 0.025),
                "0.5": _quantile(tuple(null_values), 0.5),
                "0.975": _quantile(tuple(null_values), 0.975),
            },
        },
        "alternating_split_half": {
            "row_count": len(split_rows),
            "raw_correlation": _correlation(split_left, split_right),
            "within_cell_correlation": _correlation(
                split_centered_left,
                split_centered_right,
            ),
        },
        "stationary_binomial_variance_diagnostic": {
            "mean_observed_between_block_variance": observed_variance,
            "mean_binomial_sampling_variance": binomial_variance,
            "observed_minus_binomial": (observed_variance - binomial_variance),
            "observed_to_binomial_ratio": (
                observed_variance / binomial_variance
                if binomial_variance > 0.0
                else None
            ),
            "status": (
                "descriptive only; deterministic Tasks need not be IID Bernoulli draws"
            ),
        },
        "cross_agent_residual_signal": residual_signal,
    }


def _cross_agent_residual_signal(
    rows: Sequence[Mapping[str, Any]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Compare contemporaneous cross-Agent capacity with lagged availability."""
    by_repository_origin: dict[
        tuple[str, int],
        dict[str, float],
    ] = {}
    for row in rows:
        key = (str(row["repository_id"]), int(row["origin_index"]))
        by_repository_origin.setdefault(key, {})[str(row["target_agent_id"])] = _number(
            row["future_rate"]
        ) - _number(row["full_history_rate"])
    agent_ids = tuple(sorted({str(row["target_agent_id"]) for row in rows}))
    own_lag = []
    reference_lag = []
    same_future = []
    for repository_id in repository_ids:
        origin_indexes = tuple(
            sorted(
                origin_index
                for row_repository_id, origin_index in by_repository_origin
                if row_repository_id == repository_id
            )
        )
        for origin_index in origin_indexes:
            current = by_repository_origin[(repository_id, origin_index)]
            for agent_id in agent_ids:
                reference = _mean(
                    tuple(
                        value
                        for other_agent_id, value in current.items()
                        if other_agent_id != agent_id
                    )
                )
                same_future.append((repository_id, reference, current[agent_id]))
            next_key = (repository_id, origin_index + 1)
            if next_key not in by_repository_origin:
                continue
            following = by_repository_origin[next_key]
            for agent_id in agent_ids:
                reference = _mean(
                    tuple(
                        value
                        for other_agent_id, value in current.items()
                        if other_agent_id != agent_id
                    )
                )
                own_lag.append((repository_id, current[agent_id], following[agent_id]))
                reference_lag.append((repository_id, reference, following[agent_id]))
    return {
        "own_previous_block_to_next_target_correlation": (
            _repository_equal_weighted_correlation(
                own_lag,
                repository_ids,
            )
        ),
        "previous_reference_to_next_target_correlation": (
            _repository_equal_weighted_correlation(
                reference_lag,
                repository_ids,
            )
        ),
        "same_future_reference_to_target_correlation": (
            _repository_equal_weighted_correlation(
                same_future,
                repository_ids,
            )
        ),
        "lag_pair_count": len(own_lag),
        "lag_repository_count": len({row[0] for row in own_lag}),
        "same_future_pair_count": len(same_future),
        "same_future_repository_count": len({row[0] for row in same_future}),
        "interpretation": (
            "Same-future correlation is future-open capacity. Only lagged "
            "correlations respect the forecast timing, and even they may "
            "reflect slow correction of the expanding history estimate."
        ),
    }


def summarize_cells(
    rows: Sequence[Mapping[str, Any]],
    denominator: Mapping[str, Any],
    *,
    repository_ids: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    """Keep the deployment-level Agent-by-repository units visible."""
    denominator_rates = {
        (str(row["repository_id"]), str(row["target_agent_id"])): _number(
            row["pass_rate"]
        )
        for row in denominator["cell_rows"]
    }
    result = []
    agent_ids = tuple(sorted({str(row["target_agent_id"]) for row in rows}))
    for repository_id in repository_ids:
        for agent_id in agent_ids:
            cell = tuple(
                row
                for row in rows
                if row["repository_id"] == repository_id
                and row["target_agent_id"] == agent_id
            )
            result.append(
                {
                    "repository_id": repository_id,
                    "target_agent_id": agent_id,
                    "origin_count": len(cell),
                    "denominator_pass_rate": denominator_rates[
                        (repository_id, agent_id)
                    ],
                    "future_mean_pass_rate": _mean(
                        tuple(_number(row["future_rate"]) for row in cell)
                    ),
                    "zero_future_block_share": _mean(
                        tuple(_number(row["future_rate"]) == 0.0 for row in cell)
                    ),
                    "full_history_mae": _mean(
                        tuple(_number(row["full_history_loss"]) for row in cell)
                    ),
                }
            )
    return tuple(result)


def summarize_candidates(
    horizon_result: Mapping[str, Any],
    cell_context: Sequence[Mapping[str, Any]],
    agent_groups: Mapping[str, Sequence[str]],
    *,
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Expose paired candidate effects instead of only one panel average."""
    score_rows = _mapping_sequence(horizon_result, "score_rows")
    if horizon_result.get("score_rows_digest") != canonical_digest(score_rows):
        raise ValueError("development score rows digest does not match")
    context = {
        (str(row["repository_id"]), str(row["target_agent_id"])): row
        for row in cell_context
    }
    cell_rows = []
    agent_ids = tuple(sorted({str(row["target_agent_id"]) for row in score_rows}))
    for repository_id in repository_ids:
        for agent_id in agent_ids:
            rows = tuple(
                row
                for row in score_rows
                if row["repository_id"] == repository_id
                and row["target_agent_id"] == agent_id
            )
            mae = {
                algorithm_id: _mean(
                    tuple(
                        _number(_mapping(row, "losses")[algorithm_id]) for row in rows
                    )
                )
                for algorithm_id in ALGORITHM_IDS
            }
            cell_rows.append(
                {
                    **context[(repository_id, agent_id)],
                    "mae": mae,
                    "candidate_minus_full": {
                        candidate_id: (mae[candidate_id] - mae["full_history"])
                        for candidate_id in CANDIDATE_IDS
                    },
                }
            )

    panel = _candidate_group_summary(
        score_rows,
        agent_ids,
        repository_ids,
    )
    groups = {
        group_id: _candidate_group_summary(
            score_rows,
            tuple(agent_ids),
            repository_ids,
        )
        for group_id, agent_ids in agent_groups.items()
    }
    prevalence_strata = {
        "below_0_10": _candidate_cell_stratum(
            cell_rows,
            lambda row: _number(row["denominator_pass_rate"]) < 0.10,
        ),
        "at_least_0_10": _candidate_cell_stratum(
            cell_rows,
            lambda row: _number(row["denominator_pass_rate"]) >= 0.10,
        ),
    }
    per_candidate = {}
    for candidate_id in CANDIDATE_IDS:
        differences = tuple(
            _number(row["candidate_minus_full"][candidate_id]) for row in cell_rows
        )
        prevalence = tuple(_number(row["denominator_pass_rate"]) for row in cell_rows)
        per_candidate[candidate_id] = {
            "favorable_cell_count": sum(value < 0.0 for value in differences),
            "cell_count": len(differences),
            "median_cell_difference": _quantile(differences, 0.5),
            "cell_difference_quantiles": {
                "0.1": _quantile(differences, 0.1),
                "0.9": _quantile(differences, 0.9),
            },
            "spearman_difference_vs_denominator_pass_rate": _spearman(
                prevalence,
                differences,
            ),
        }
    return {
        "panel_macro": panel,
        "agent_group_macro": groups,
        "outcome_defined_prevalence_strata": prevalence_strata,
        "per_candidate": per_candidate,
        "cell_rows": tuple(cell_rows),
    }


def summarize_oracles(
    origins: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes: Mapping[str, Mapping[str, int]],
    committed_horizon: Mapping[str, Any],
    *,
    repository_ids: Sequence[str],
    budget: int,
) -> Mapping[str, Any]:
    """Recover the Agent-by-repository cells omitted by the Oracle summary."""
    import numpy as np

    agent_ids = tuple(sorted(outcomes))
    score_rows = []
    for repository_id in repository_ids:
        for origin in origins[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            history = np.asarray(
                [
                    [outcomes[agent_id][task_id] for agent_id in agent_ids]
                    for task_id in history_ids
                ],
                dtype=np.float64,
            )
            future = np.asarray(
                [
                    [outcomes[agent_id][task_id] for agent_id in agent_ids]
                    for task_id in future_ids
                ],
                dtype=np.float64,
            )
            memberships = select_future_oracle_memberships(
                history,
                future,
                budget=budget,
                created_order=tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                ),
            )
            future_rates = future.mean(axis=0)
            for held_out, agent_id in enumerate(agent_ids):
                losses = {
                    "full_history": float(
                        abs(history[:, held_out].mean() - future_rates[held_out])
                    )
                }
                for oracle_id, indices in memberships[held_out].items():
                    losses[oracle_id] = float(
                        abs(
                            history[list(indices), held_out].mean()
                            - future_rates[held_out]
                        )
                    )
                score_rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "target_agent_id": agent_id,
                        "losses": losses,
                    }
                )

    oracle_ids = ("reference_future_oracle", "target_future_oracle")
    panel = _loss_group_summary(
        score_rows,
        agent_ids,
        repository_ids,
        algorithm_ids=("full_history", *oracle_ids),
        delta_ids=oracle_ids,
    )
    committed_mae = _mapping(committed_horizon, "mae")
    for algorithm_id, value in panel["mae"].items():
        if abs(value - _number(committed_mae[algorithm_id])) > 1e-12:
            raise ValueError("recovered Oracle macro MAE changed")

    cell_rows = []
    for repository_id in repository_ids:
        for agent_id in agent_ids:
            rows = tuple(
                row
                for row in score_rows
                if row["repository_id"] == repository_id
                and row["target_agent_id"] == agent_id
            )
            mae = {
                algorithm_id: _mean(
                    tuple(
                        _number(_mapping(row, "losses")[algorithm_id]) for row in rows
                    )
                )
                for algorithm_id in ("full_history", *oracle_ids)
            }
            cell_rows.append(
                {
                    "repository_id": repository_id,
                    "target_agent_id": agent_id,
                    "origin_count": len(rows),
                    "mae": mae,
                    "oracle_minus_full": {
                        oracle_id: mae[oracle_id] - mae["full_history"]
                        for oracle_id in oracle_ids
                    },
                }
            )
    oracle_rows = {}
    for oracle_id in oracle_ids:
        differences = tuple(
            _number(row["oracle_minus_full"][oracle_id]) for row in cell_rows
        )
        worst = max(
            cell_rows,
            key=lambda row: _number(row["oracle_minus_full"][oracle_id]),
        )
        oracle_rows[oracle_id] = {
            "favorable_cell_count": sum(value < 0.0 for value in differences),
            "harmful_cell_count": sum(value > 0.0 for value in differences),
            "tie_cell_count": sum(value == 0.0 for value in differences),
            "cell_count": len(differences),
            "difference_quantiles": {
                "0.1": _quantile(differences, 0.1),
                "0.5": _quantile(differences, 0.5),
                "0.9": _quantile(differences, 0.9),
            },
            "worst_harm_cell": worst,
        }
    return {
        "status": (
            "future-open macro and joint-cell capacity diagnostic; not an "
            "implementable Selector or forecastability result"
        ),
        "panel_macro": panel,
        "oracles": oracle_rows,
        "cell_rows": tuple(cell_rows),
    }


def diagnose(horizons: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    """State only conclusions directly supported by the audit."""
    candidate_horizons = tuple(
        payload for payload in horizons.values() if "candidate_audit" in payload
    )
    no_panel_candidate_beats_full = all(
        all(
            _number(
                _mapping(
                    _mapping(payload, "candidate_audit")["panel_macro"],
                    "candidate_minus_full",
                )[candidate_id]
            )
            >= 0.0
            for candidate_id in CANDIDATE_IDS
        )
        for payload in candidate_horizons
    )
    group_reversal = any(
        any(
            _number(
                payload["candidate_audit"]["agent_group_macro"]["legacy_rag"][
                    "candidate_minus_full"
                ][candidate_id]
            )
            < 0.0
            and _number(
                payload["candidate_audit"]["agent_group_macro"]["later_non_rag"][
                    "candidate_minus_full"
                ][candidate_id]
            )
            > 0.0
            for candidate_id in CANDIDATE_IDS
        )
        for payload in candidate_horizons
    )
    return {
        "cross_repository_aggregate_is_single_repository_estimate": False,
        "current_selection_claim_supported": False,
        "no_panel_candidate_beats_full": no_panel_candidate_beats_full,
        "agent_group_direction_reversal_present": group_reversal,
        "algorithm_route": (
            "pause new candidate optimization until the estimand and "
            "future-block reliability are resolved"
        ),
        "supported_interpretation": (
            "The current headline is a panel summary. It mixes static "
            "Agent-by-repository prevalence, temporal variation, and finite-"
            "block noise; it is not a pass-rate estimate for one deployment "
            "Agent and repository."
        ),
        "not_established": (
            "The audit does not establish that future within-repository "
            "deviations from Full history are predictably selectable."
        ),
    }


def _candidate_group_summary(
    rows: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    selected = tuple(row for row in rows if row["target_agent_id"] in agent_ids)
    mae = {
        algorithm_id: _macro_callable(
            selected,
            lambda row, key=algorithm_id: _number(_mapping(row, "losses")[key]),
            repository_ids,
        )
        for algorithm_id in ALGORITHM_IDS
    }
    return {
        "agent_count": len(agent_ids),
        "mae": mae,
        "candidate_minus_full": {
            candidate_id: mae[candidate_id] - mae["full_history"]
            for candidate_id in CANDIDATE_IDS
        },
    }


def _loss_group_summary(
    rows: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    repository_ids: Sequence[str],
    *,
    algorithm_ids: Sequence[str],
    delta_ids: Sequence[str],
) -> Mapping[str, Any]:
    selected = tuple(row for row in rows if row["target_agent_id"] in agent_ids)
    mae = {
        algorithm_id: _macro_callable(
            selected,
            lambda row, key=algorithm_id: _number(_mapping(row, "losses")[key]),
            repository_ids,
        )
        for algorithm_id in algorithm_ids
    }
    return {
        "agent_count": len(agent_ids),
        "mae": mae,
        "algorithm_minus_full": {
            algorithm_id: mae[algorithm_id] - mae["full_history"]
            for algorithm_id in delta_ids
        },
    }


def _candidate_cell_stratum(
    rows: Sequence[Mapping[str, Any]],
    predicate: Any,
) -> Mapping[str, Any]:
    selected = tuple(row for row in rows if predicate(row))
    return {
        "cell_count": len(selected),
        "mean_candidate_minus_full": {
            candidate_id: (
                _mean(
                    tuple(
                        _number(row["candidate_minus_full"][candidate_id])
                        for row in selected
                    )
                )
                if selected
                else None
            )
            for candidate_id in CANDIDATE_IDS
        },
    }


def _agent_groups(
    metadata: Mapping[str, Mapping[str, str]],
) -> Mapping[str, tuple[str, ...]]:
    legacy = tuple(
        agent_id
        for agent_id in sorted(metadata)
        if metadata[agent_id]["mechanism_family"] == "RAG"
    )
    later = tuple(agent_id for agent_id in sorted(metadata) if agent_id not in legacy)
    if len(legacy) != 6 or len(later) != 5:
        raise ValueError("SWE-bench Full descriptive Agent groups changed")
    return {
        "legacy_rag": legacy,
        "later_non_rag": later,
    }


def _repository_ids(
    source_plan: Mapping[str, Any],
) -> tuple[str, ...]:
    horizons = _mapping(_mapping(source_plan, "frame"), "horizons")
    h5 = _mapping(horizons, "5")
    result = _string_tuple(h5.get("repository_ids"), "repository IDs")
    h10 = _string_tuple(
        _mapping(horizons, "10").get("repository_ids"),
        "H10 repository IDs",
    )
    if result != h10:
        raise ValueError("H5 and H10 repository sets differ")
    return result


def _validate_development_result(
    result: Mapping[str, Any],
    plan: Mapping[str, Any],
    identities: Mapping[str, Any],
) -> None:
    if (
        result.get("schema_version")
        != "barcarolle_swe_bench_full_development_result_v1"
    ):
        raise ValueError("development result schema changed")
    digest = result.get("result_digest")
    body = {key: value for key, value in result.items() if key != "result_digest"}
    if digest != canonical_digest(body):
        raise ValueError("development result digest does not match")
    binding = _mapping(_mapping(plan, "bound_artifacts"), "development_result")
    if digest != binding.get("logical_digest"):
        raise ValueError("development result logical digest changed")
    if canonical_digest(_mapping(result, "input_identities")) != canonical_digest(
        identities
    ):
        raise ValueError("development result input identities changed")


def _validate_diagnostic_result(
    result: Mapping[str, Any],
    plan: Mapping[str, Any],
    identities: Mapping[str, Any],
) -> None:
    if result.get("schema_version") != "barcarolle_swe_bench_full_diagnostic_result_v1":
        raise ValueError("diagnostic result schema changed")
    digest = result.get("diagnostic_result_digest")
    body = {
        key: value for key, value in result.items() if key != "diagnostic_result_digest"
    }
    if digest != canonical_digest(body):
        raise ValueError("diagnostic result digest does not match")
    binding = _mapping(_mapping(plan, "bound_artifacts"), "diagnostic_result")
    if digest != binding.get("logical_digest"):
        raise ValueError("diagnostic result logical digest changed")
    if canonical_digest(_mapping(result, "input_identities")) != canonical_digest(
        identities
    ):
        raise ValueError("diagnostic result input identities changed")


def _repository_equal_weights(
    rows: Sequence[Mapping[str, Any]],
    repository_ids: Sequence[str],
) -> tuple[float, ...]:
    counts = {
        repository_id: sum(row["repository_id"] == repository_id for row in rows)
        for repository_id in repository_ids
    }
    if any(count == 0 for count in counts.values()):
        raise ValueError("repository has no rows")
    return tuple(
        1.0 / (len(repository_ids) * counts[str(row["repository_id"])]) for row in rows
    )


def _weighted_group_mean(
    rows: Sequence[Mapping[str, Any]],
    weights: Sequence[float],
    values: Any,
    predicate: Any,
) -> float:
    indexes = tuple(index for index, row in enumerate(rows) if predicate(row))
    denominator = fsum(weights[index] for index in indexes)
    if denominator <= 0.0:
        raise ValueError("weighted group is empty")
    return (
        fsum(weights[index] * float(values[index]) for index in indexes) / denominator
    )


def _repository_equal_adjacent_covariance(
    sequences: Mapping[tuple[str, str], Sequence[float]],
    repository_ids: Sequence[str],
) -> float:
    repository_values = []
    for repository_id in repository_ids:
        products = []
        for (row_repository_id, _), sequence in sequences.items():
            if row_repository_id != repository_id or len(sequence) < 2:
                continue
            cell_mean = _mean(tuple(sequence))
            products.extend(
                (left - cell_mean) * (right - cell_mean)
                for left, right in pairwise(sequence)
            )
        if products:
            repository_values.append(_mean(tuple(products)))
    return _mean(tuple(repository_values))


def _macro_mean(
    rows: Sequence[Mapping[str, Any]],
    key: str,
    repository_ids: Sequence[str],
) -> float:
    return _macro_callable(
        rows,
        lambda row: _number(row[key]),
        repository_ids,
    )


def _macro_indicator(
    rows: Sequence[Mapping[str, Any]],
    key: str,
    target: float,
    repository_ids: Sequence[str],
) -> float:
    return _macro_callable(
        rows,
        lambda row: float(_number(row[key]) == target),
        repository_ids,
    )


def _macro_callable(
    rows: Sequence[Mapping[str, Any]],
    function: Any,
    repository_ids: Sequence[str],
) -> float:
    repository_values = []
    for repository_id in repository_ids:
        values = tuple(
            function(row) for row in rows if row["repository_id"] == repository_id
        )
        if not values:
            raise ValueError(f"repository has no rows: {repository_id}")
        repository_values.append(_mean(values))
    return _mean(tuple(repository_values))


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = _mean(tuple(left))
    right_mean = _mean(tuple(right))
    numerator = fsum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    left_scale = sqrt(fsum((value - left_mean) ** 2 for value in left))
    right_scale = sqrt(fsum((value - right_mean) ** 2 for value in right))
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    return numerator / (left_scale * right_scale)


def _repository_equal_weighted_correlation(
    rows: Sequence[tuple[str, float, float]],
    repository_ids: Sequence[str],
) -> float | None:
    if len(rows) < 2:
        return None
    counts = {
        repository_id: sum(row[0] == repository_id for row in rows)
        for repository_id in repository_ids
    }
    active_repository_ids = tuple(
        repository_id for repository_id in repository_ids if counts[repository_id] > 0
    )
    if not active_repository_ids:
        return None
    weights = tuple(
        1.0 / (len(active_repository_ids) * counts[repository_id])
        for repository_id, _, _ in rows
    )
    left_mean = fsum(
        weight * left for weight, (_, left, _) in zip(weights, rows, strict=True)
    )
    right_mean = fsum(
        weight * right for weight, (_, _, right) in zip(weights, rows, strict=True)
    )
    covariance = fsum(
        weight * (left - left_mean) * (right - right_mean)
        for weight, (_, left, right) in zip(weights, rows, strict=True)
    )
    left_variance = fsum(
        weight * (left - left_mean) ** 2
        for weight, (_, left, _) in zip(weights, rows, strict=True)
    )
    right_variance = fsum(
        weight * (right - right_mean) ** 2
        for weight, (_, _, right) in zip(weights, rows, strict=True)
    )
    if left_variance <= 0.0 or right_variance <= 0.0:
        return None
    return covariance / sqrt(left_variance * right_variance)


def _spearman(left: Sequence[float], right: Sequence[float]) -> float | None:
    return _correlation(_ranks(left), _ranks(right))


def _ranks(values: Sequence[float]) -> tuple[float, ...]:
    ordered = sorted(enumerate(values), key=lambda row: row[1])
    result = [0.0] * len(ordered)
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        rank = (position + 1 + end) / 2.0
        for original_index, _ in ordered[position:end]:
            result[original_index] = rank
        position = end
    return tuple(result)


def _sample_variance(values: Sequence[float]) -> float:
    mean = _mean(tuple(values))
    return fsum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _linear_fit(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> Mapping[str, float | None]:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise ValueError("linear fit requires paired values")
    x_mean = _mean(tuple(x_values))
    y_mean = _mean(tuple(y_values))
    denominator = fsum((value - x_mean) ** 2 for value in x_values)
    if denominator == 0.0:
        raise ValueError("linear fit x values are constant")
    slope = (
        fsum(
            (x_value - x_mean) * (y_value - y_mean)
            for x_value, y_value in zip(x_values, y_values, strict=True)
        )
        / denominator
    )
    intercept = y_mean - slope * x_mean
    residual_sum = fsum(
        (y_value - (intercept + slope * x_value)) ** 2
        for x_value, y_value in zip(x_values, y_values, strict=True)
    )
    total_sum = fsum((value - y_mean) ** 2 for value in y_values)
    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": (1.0 - residual_sum / total_sum if total_sum > 0.0 else None),
    }


def _quantile(values: Sequence[float], probability: float) -> float:
    rows = tuple(sorted(float(value) for value in values))
    if not rows:
        raise ValueError("quantile requires values")
    if probability < 0.0 or probability > 1.0:
        raise ValueError("quantile probability is invalid")
    position = probability * (len(rows) - 1)
    lower = int(position)
    upper = min(lower + 1, len(rows) - 1)
    fraction = position - lower
    return rows[lower] * (1.0 - fraction) + rows[upper] * fraction


def _mean(values: Sequence[float | int | bool]) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(float(value) for value in rows) / len(rows)


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("value must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError("value must be finite")
    return result


def _mapping(
    value: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    result = value.get(key)
    if not isinstance(result, Mapping):
        raise ValueError(f"{key} must be an object")
    return result


def _mapping_sequence(
    value: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    result = value.get(key)
    if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
        raise ValueError(f"{key} must be an array")
    if not all(isinstance(row, Mapping) for row in result):
        raise ValueError(f"{key} entries must be objects")
    return tuple(result)  # pyright: ignore[reportReturnType]


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an array")
    result = tuple(value)
    if (
        not result
        or any(not isinstance(row, str) or not row for row in result)
        or len(result) != len(set(result))
    ):
        raise ValueError(f"{name} must contain unique nonempty strings")
    return result  # pyright: ignore[reportReturnType]


def _positive_integer(value: Mapping[str, Any], key: str) -> int:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return result


def _required_string(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ValueError(f"{key} must be a nonempty string")
    return result


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _bound_path(plan: Mapping[str, Any], binding_id: str) -> Path:
    binding = _mapping(_mapping(plan, "bound_artifacts"), binding_id)
    return REPOSITORY_ROOT / _required_string(binding, "path")


def validate_summary(
    plan: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> None:
    body = {key: value for key, value in summary.items() if key != SUMMARY_DIGEST_KEY}
    if (
        summary.get("schema_version") != SUMMARY_SCHEMA
        or summary.get("plan_digest") != plan.get("plan_digest")
        or summary.get(SUMMARY_DIGEST_KEY) != canonical_digest(body)
    ):
        raise ValueError("estimand audit summary is invalid")
    resource_use = _mapping(summary, "resource_use")
    if any(resource_use.get(key) != 0 for key in resource_use):
        raise ValueError("estimand audit used a forbidden resource")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument("--summary", type=Path, default=DEFAULT_OUTPUT)
    validate.add_argument("--verify-inputs", action="store_true")

    arguments = parser.parse_args(argv)
    if arguments.command == "run":
        plan = load_plan(arguments.plan, verify_bindings=True)
        _write_json(arguments.output, run_audit(plan))
        return 0
    plan = load_plan(
        arguments.plan,
        verify_bindings=arguments.verify_inputs,
    )
    validate_summary(plan, _load_mapping(arguments.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
