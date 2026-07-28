#!/usr/bin/env python3
"""Measure exact budget-ten hindsight support on the opened Multi-SWE panel."""

from __future__ import annotations

# SciPy is supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from importlib.metadata import version
import json
from math import fsum
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    load_content_manifest,
    load_embedding_manifest,
    load_public_outcomes,
    load_selector_plan,
    load_task_content,
    load_task_metadata,
    load_task_space_results,
    outcome_pass_rate_mae,
)


HERE = Path(__file__).resolve().parent
DEFAULT_DIAGNOSTIC_PLAN = HERE / "hindsight-plan.json"
PLAN_SCHEMA = "barcarolle_multi_swe_hindsight_plan_v1"
OUTCOME_SCHEMA = "barcarolle_multi_swe_semantic_outcome_results_v1"
RESULT_SCHEMA = "barcarolle_multi_swe_hindsight_results_v1"
SCIPY_VERSION = "1.16.3"


def load_hindsight_plan(
    path: Path = DEFAULT_DIAGNOSTIC_PLAN,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("hindsight plan schema is unsupported")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "hindsight_plan_digest"
        }
    )
    if payload.get("hindsight_plan_digest") != expected:
        raise ValueError("hindsight plan digest does not match")
    diagnostic = _mapping(payload, "diagnostic")
    if diagnostic.get("diagnostic_id") != "exact_hindsight_response_milp":
        raise ValueError("hindsight diagnostic changed")
    solver = _mapping(diagnostic, "solver")
    if (
        solver.get("package") != "scipy"
        or solver.get("version") != SCIPY_VERSION
        or solver.get("mip_rel_gap") != 0.0
        or solver.get("time_limit_seconds") is not None
    ):
        raise ValueError("hindsight solver contract changed")
    return payload


def load_outcome_results(
    path: Path,
    hindsight_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("outcome_results_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("outcome result digest does not match")
    payload["outcome_results_digest"] = digest
    source = _mapping(hindsight_plan, "source")
    if (
        payload.get("schema_version") != OUTCOME_SCHEMA
        or payload.get("selector_plan_digest")
        != source.get("selector_plan_digest")
        or payload.get("task_space_results_digest")
        != source.get("task_space_results_digest")
        or digest != source.get("outcome_results_digest")
    ):
        raise ValueError("outcome result does not bind hindsight plan")
    return payload


def load_hindsight_results(
    path: Path,
    hindsight_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("hindsight_results_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("hindsight result digest does not match")
    payload["hindsight_results_digest"] = digest
    source = _mapping(hindsight_plan, "source")
    if (
        payload.get("schema_version") != RESULT_SCHEMA
        or payload.get("hindsight_plan_digest")
        != hindsight_plan.get("hindsight_plan_digest")
        or payload.get("selector_plan_digest")
        != source.get("selector_plan_digest")
        or payload.get("task_space_results_digest")
        != source.get("task_space_results_digest")
        or payload.get("outcome_results_digest")
        != source.get("outcome_results_digest")
    ):
        raise ValueError("hindsight result does not bind frozen plan")
    return payload


def solve_exact_hindsight_subset(
    history_ids: Sequence[str],
    future_ids: Sequence[str],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
    *,
    budget: int,
) -> tuple[tuple[str, ...], Mapping[str, object]]:
    """Solve the exact response-vector subset problem for one Origin."""
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    history = tuple(history_ids)
    future = tuple(future_ids)
    configurations = tuple(configuration_ids)
    if (
        not history
        or not future
        or not configurations
        or len(history) != len(set(history))
        or isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget <= 0
        or budget > len(history)
    ):
        raise ValueError("hindsight solve input is invalid")

    required = set((*history, *future))
    for configuration_id in configurations:
        outcomes = outcomes_by_configuration.get(configuration_id)
        if outcomes is None or not required.issubset(outcomes):
            raise ValueError("hindsight outcomes do not cover Origin")

    groups: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for task_id in history:
        vector = tuple(
            int(outcomes_by_configuration[configuration_id][task_id])
            for configuration_id in configurations
        )
        if any(value not in (0, 1) for value in vector):
            raise ValueError("hindsight outcome is not binary")
        groups[vector].append(task_id)
    patterns = tuple(sorted(groups))
    pattern_count = len(patterns)
    configuration_count = len(configurations)
    variable_count = pattern_count + configuration_count

    objective = np.zeros(variable_count, dtype=np.float64)
    objective[pattern_count:] = 1.0 / configuration_count
    integrality = np.zeros(variable_count, dtype=np.int8)
    integrality[:pattern_count] = 1
    lower_bounds = np.zeros(variable_count, dtype=np.float64)
    upper_bounds = np.ones(variable_count, dtype=np.float64)
    upper_bounds[:pattern_count] = np.asarray(
        [min(len(groups[pattern]), budget) for pattern in patterns],
        dtype=np.float64,
    )

    future_rates = np.asarray(
        [
            fsum(
                outcomes_by_configuration[configuration_id][task_id]
                for task_id in future
            )
            / len(future)
            for configuration_id in configurations
        ],
        dtype=np.float64,
    )
    matrix = np.zeros(
        (1 + 2 * configuration_count, variable_count),
        dtype=np.float64,
    )
    constraint_lower = np.full(
        1 + 2 * configuration_count,
        -np.inf,
        dtype=np.float64,
    )
    constraint_upper = np.full(
        1 + 2 * configuration_count,
        np.inf,
        dtype=np.float64,
    )
    matrix[0, :pattern_count] = 1.0
    constraint_lower[0] = budget
    constraint_upper[0] = budget
    for offset in range(configuration_count):
        response = np.asarray(
            [pattern[offset] / budget for pattern in patterns],
            dtype=np.float64,
        )
        positive_row = 1 + 2 * offset
        negative_row = positive_row + 1
        matrix[positive_row, :pattern_count] = response
        matrix[positive_row, pattern_count + offset] = -1.0
        constraint_upper[positive_row] = future_rates[offset]
        matrix[negative_row, :pattern_count] = -response
        matrix[negative_row, pattern_count + offset] = -1.0
        constraint_upper[negative_row] = -future_rates[offset]

    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(
            lower_bounds,  # pyright: ignore[reportArgumentType]
            upper_bounds,  # pyright: ignore[reportArgumentType]
        ),
        constraints=LinearConstraint(
            matrix,
            constraint_lower,  # pyright: ignore[reportArgumentType]
            constraint_upper,  # pyright: ignore[reportArgumentType]
        ),
        options={"presolve": True, "mip_rel_gap": 0.0},
    )
    if not result.success or result.status != 0 or result.x is None:
        raise RuntimeError(
            "hindsight MILP did not return a certified optimum: "
            f"status={result.status}, message={result.message}"
        )

    raw_counts = result.x[:pattern_count]
    counts = tuple(int(round(float(value))) for value in raw_counts)
    if (
        sum(counts) != budget
        or any(abs(float(value) - count) > 1e-7 for value, count in zip(
            raw_counts,
            counts,
            strict=True,
        ))
        or any(
            count < 0 or count > len(groups[pattern])
            for pattern, count in zip(patterns, counts, strict=True)
        )
    ):
        raise RuntimeError("hindsight MILP returned invalid integer counts")

    selected = tuple(
        task_id
        for pattern, count in zip(patterns, counts, strict=True)
        for task_id in groups[pattern][:count]
    )
    recomputed = outcome_pass_rate_mae(
        selected,
        future,
        outcomes_by_configuration,
        configurations,
    )
    solver_objective = _finite_number(result.fun, "solver objective")
    objective_error = abs(recomputed - solver_objective)
    if objective_error > 1e-8:
        raise RuntimeError("recomputed hindsight objective changed")

    return selected, {
        "success": True,
        "status": int(result.status),
        "message": str(result.message),
        "solver_objective": solver_objective,
        "recomputed_objective": recomputed,
        "objective_error": objective_error,
        "response_pattern_count": pattern_count,
        "mip_gap": _optional_finite_number(getattr(result, "mip_gap", None)),
        "mip_node_count": _optional_integer(
            getattr(result, "mip_node_count", None)
        ),
    }


def run_hindsight_diagnostic(
    tasks: Sequence[TaskMetadata],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_metadata: Sequence[Mapping[str, str]],
    task_space_results: Mapping[str, object],
    outcome_results: Mapping[str, object],
    selector_plan: Mapping[str, object],
    hindsight_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the frozen exact support diagnostic for H5 and H10."""
    configuration_ids = tuple(
        _required_string(row, "configuration_id")
        for row in configuration_metadata
    )
    if (
        version("scipy") != SCIPY_VERSION
        or len(configuration_ids)
        != _positive_integer(_mapping(hindsight_plan, "source"), "configuration_count")
    ):
        raise ValueError("hindsight runtime does not match frozen plan")

    selector_rolling = _mapping(selector_plan, "rolling_origin")
    diagnostic_protocol = _mapping(hindsight_plan, "protocol")
    minimum_history = _positive_integer(
        diagnostic_protocol,
        "minimum_initial_history_tasks",
    )
    budget = _positive_integer(
        diagnostic_protocol,
        "selection_budget_tasks",
    )
    if (
        minimum_history
        != _positive_integer(
            selector_rolling,
            "minimum_initial_history_tasks",
        )
        or budget
        != _positive_integer(selector_rolling, "selection_budget_tasks")
    ):
        raise ValueError("hindsight protocol diverges from Selector plan")

    task_space_horizons = _mapping(task_space_results, "horizons")
    prior_outcome_horizons = _mapping(outcome_results, "horizons")
    horizon_results = {}
    total_origins = 0
    for horizon_spec in _mapping_sequence(diagnostic_protocol, "horizons"):
        horizon = _positive_integer(horizon_spec, "future_tasks")
        task_horizon = _mapping(task_space_horizons, str(horizon))
        repository_ids = _string_tuple(
            task_horizon.get("repository_ids"),
            "hindsight repositories",
        )
        deep_repository_ids = _string_tuple(
            task_horizon.get("deep_repository_ids"),
            "hindsight deep repositories",
        )
        origins_by_repository = build_repository_origins(
            tasks,
            minimum_initial_history_tasks=minimum_history,
            future_block_tasks=horizon,
        )
        expected_origins = {
            origin.origin_id
            for repository_id in repository_ids
            for origin in origins_by_repository[repository_id]
        }
        frozen_full_history = _mapping(
            _mapping(task_horizon, "memberships"),
            "full_history",
        )
        if (
            set(frozen_full_history) != expected_origins
            or len(expected_origins)
            != _positive_integer(horizon_spec, "origin_count")
            or len(repository_ids)
            != _positive_integer(horizon_spec, "repository_count")
            or len(deep_repository_ids)
            != _positive_integer(horizon_spec, "deep_repository_count")
        ):
            raise ValueError("hindsight Origin cohort changed")

        memberships: dict[str, tuple[str, ...]] = {}
        solver_rows: dict[str, Mapping[str, object]] = {}
        contrast_rows = []
        for repository_id in repository_ids:
            for origin in origins_by_repository[repository_id]:
                history_ids = tuple(
                    task.instance_id for task in origin.history
                )
                future_ids = tuple(task.instance_id for task in origin.future)
                if tuple(frozen_full_history[origin.origin_id]) != history_ids:
                    raise ValueError("frozen full-history membership changed")
                selected, solver = solve_exact_hindsight_subset(
                    history_ids,
                    future_ids,
                    outcomes_by_configuration,
                    configuration_ids,
                    budget=budget,
                )
                baseline_loss = outcome_pass_rate_mae(
                    history_ids,
                    future_ids,
                    outcomes_by_configuration,
                    configuration_ids,
                )
                loss = outcome_pass_rate_mae(
                    selected,
                    future_ids,
                    outcomes_by_configuration,
                    configuration_ids,
                )
                memberships[origin.origin_id] = selected
                solver_rows[origin.origin_id] = solver
                contrast_rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "loss": loss,
                        "baseline_loss": baseline_loss,
                        "difference": loss - baseline_loss,
                    }
                )

        wide = _repository_summary(contrast_rows, repository_ids)
        deep = _repository_summary(contrast_rows, deep_repository_ids)
        prior_horizon = _mapping(prior_outcome_horizons, str(horizon))
        prior_summaries = _mapping(prior_horizon, "summaries")
        controls = {
            selector_id: {
                "wide": _compact_loss_summary(
                    _mapping(_mapping(prior_summaries, selector_id), "wide")
                ),
                "deep": _compact_loss_summary(
                    _mapping(_mapping(prior_summaries, selector_id), "deep")
                ),
            }
            for selector_id in (
                "full_history",
                "recency",
                "stationary_semantic_herding",
                "alg_007_centroid_recent_15",
                "minimax_temporal_semantic_herding",
            )
        }
        max_error = max(
            _finite_number(row.get("objective_error"), "objective error")
            for row in solver_rows.values()
        )
        pattern_counts = tuple(
            _positive_integer(row, "response_pattern_count")
            for row in solver_rows.values()
        )
        horizon_results[str(horizon)] = {
            "repository_ids": repository_ids,
            "deep_repository_ids": deep_repository_ids,
            "memberships": dict(sorted(memberships.items())),
            "membership_digest": canonical_digest(
                tuple(sorted(memberships.items()))
            ),
            "solver_rows": dict(sorted(solver_rows.items())),
            "solver_summary": {
                "origin_count": len(solver_rows),
                "certified_optimum_count": sum(
                    row.get("success") is True and row.get("status") == 0
                    for row in solver_rows.values()
                ),
                "maximum_objective_error": max_error,
                "response_pattern_count": {
                    "minimum": min(pattern_counts),
                    "median": _median(pattern_counts),
                    "maximum": max(pattern_counts),
                },
            },
            "exact_hindsight": {
                "wide": wide,
                "deep": deep,
            },
            "frozen_controls": controls,
            "random_calibration": prior_horizon.get("random_calibration"),
        }
        total_origins += len(solver_rows)

    decision = _capacity_decision(horizon_results)
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": hindsight_plan.get("study_id"),
        "epistemic_status": hindsight_plan.get("epistemic_status"),
        "hindsight_plan_digest": hindsight_plan.get("hindsight_plan_digest"),
        "selector_plan_digest": selector_plan.get("selector_plan_digest"),
        "task_space_results_digest": task_space_results.get(
            "task_space_results_digest"
        ),
        "outcome_results_digest": outcome_results.get(
            "outcome_results_digest"
        ),
        "task_count": len(tasks),
        "configuration_count": len(configuration_ids),
        "origin_count": total_origins,
        "horizons": horizon_results,
        "capacity_decision": decision,
        "nomination": {
            "selector_nominated": False,
            "independent_confirmation_authorized": False,
            "production_promotion_allowed": False,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "sealed_swe_bench_holdout_agents_opened": 0,
        },
        "claim_boundary": _required_string(
            _mapping(hindsight_plan, "motivation"),
            "claim_boundary",
        ),
    }
    result["hindsight_results_digest"] = canonical_digest(result)
    return result


def _capacity_decision(
    horizons: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    h5_hindsight = _mapping(h5, "exact_hindsight")
    h10_hindsight = _mapping(h10, "exact_hindsight")
    h5_wide = _mapping(h5_hindsight, "wide")
    h5_deep = _mapping(h5_hindsight, "deep")
    h10_wide = _mapping(h10_hindsight, "wide")
    h10_deep = _mapping(h10_hindsight, "deep")
    solver_summaries = (
        _mapping(h5, "solver_summary"),
        _mapping(h10, "solver_summary"),
    )
    all_optimal = all(
        summary.get("origin_count") == summary.get("certified_optimum_count")
        for summary in solver_summaries
    )
    requirements = {
        "all_328_origin_solves_certified_optimal": all_optimal
        and sum(int(summary["origin_count"]) for summary in solver_summaries)
        == 328,
        "h5_difference_at_most_minus_0_01": (
            _finite_number(
                h5_wide.get("macro_repository_difference"),
                "H5 difference",
            )
            <= -0.01
        ),
        "h5_at_least_10_of_13_repositories_favorable": (
            int(h5_wide.get("favorable_repository_count", -1)) >= 10
        ),
        "h5_deep_negative": (
            _finite_number(
                h5_deep.get("macro_repository_difference"),
                "H5 deep difference",
            )
            < 0.0
        ),
        "h10_common_11_negative": (
            _finite_number(
                h10_wide.get("macro_repository_difference"),
                "H10 difference",
            )
            < 0.0
        ),
        "h10_at_least_8_of_11_repositories_favorable": (
            int(h10_wide.get("favorable_repository_count", -1)) >= 8
        ),
        "h10_deep_negative": (
            _finite_number(
                h10_deep.get("macro_repository_difference"),
                "H10 deep difference",
            )
            < 0.0
        ),
    }
    all_requirements_met = all(requirements.values())
    h5_difference = _finite_number(
        h5_wide.get("macro_repository_difference"),
        "H5 difference",
    )
    if all_requirements_met:
        decision = "budget_ten_representational_capacity_supported"
        interpretation = (
            "On this opened panel and estimand, ten historical Tasks can "
            "represent future Agent pass rates. Pre-Origin identification, "
            "not subset capacity, is the current bottleneck."
        )
    elif not all_optimal or h5_difference >= 0.0:
        decision = "budget_ten_capacity_not_demonstrated"
        interpretation = (
            "The diagnostic does not establish adequate budget-ten capacity."
        )
    else:
        decision = "budget_ten_capacity_mixed_or_limited"
        interpretation = (
            "Some budget-ten headroom exists, but it is not robust enough to "
            "separate capacity from prediction as the sole bottleneck."
        )
    return {
        "requirements": requirements,
        "all_requirements_met": all_requirements_met,
        "decision": decision,
        "interpretation": interpretation,
        "predictive_claim_allowed": False,
    }


def _repository_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> Mapping[str, object]:
    by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        if repository_id in repository_ids:
            by_repository[repository_id].append(row)
    if any(not by_repository[repository_id] for repository_id in repository_ids):
        raise ValueError("hindsight repository summary is incomplete")
    repository_rows = []
    for repository_id in repository_ids:
        repository_data = by_repository[repository_id]
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(repository_data),
                "mean_loss": _mean(
                    tuple(
                        _finite_number(row.get("loss"), "loss")
                        for row in repository_data
                    )
                ),
                "mean_baseline_loss": _mean(
                    tuple(
                        _finite_number(
                            row.get("baseline_loss"),
                            "baseline loss",
                        )
                        for row in repository_data
                    )
                ),
                "mean_difference": _mean(
                    tuple(
                        _finite_number(row.get("difference"), "difference")
                        for row in repository_data
                    )
                ),
            }
        )
    differences = tuple(
        _finite_number(row["mean_difference"], "repository difference")
        for row in repository_rows
    )
    return {
        "repository_count": len(repository_rows),
        "origin_count": sum(int(row["origin_count"]) for row in repository_rows),
        "macro_repository_loss": _mean(
            tuple(
                _finite_number(row["mean_loss"], "repository loss")
                for row in repository_rows
            )
        ),
        "macro_repository_baseline_loss": _mean(
            tuple(
                _finite_number(
                    row["mean_baseline_loss"],
                    "repository baseline loss",
                )
                for row in repository_rows
            )
        ),
        "macro_repository_difference": _mean(differences),
        "favorable_repository_count": sum(value < 0.0 for value in differences),
        "repository_rows": repository_rows,
    }


def _compact_loss_summary(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    return {
        key: payload.get(key)
        for key in (
            "repository_count",
            "origin_count",
            "macro_repository_loss",
            "macro_repository_baseline_loss",
            "macro_repository_difference",
            "favorable_repository_count",
        )
    }


def build_hindsight_evidence_summary(
    result: Mapping[str, object],
    hindsight_plan: Mapping[str, object],
    reproduction_result: Mapping[str, object],
) -> Mapping[str, object]:
    """Project a full raw result into the committed evidence summary."""
    _validate_in_memory_hindsight_result(result, hindsight_plan)
    _validate_in_memory_hindsight_result(reproduction_result, hindsight_plan)
    byte_identical = canonical_json(result) == canonical_json(
        reproduction_result
    )

    horizons = _mapping(result, "horizons")
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    all_solver_rows = (
        *_solver_rows(h5),
        *_solver_rows(h10),
    )
    mip_gaps = sorted(
        {
            _finite_number(row.get("mip_gap"), "MIP gap")
            for row in all_solver_rows
        }
    )
    node_counts = tuple(
        _positive_or_zero_integer(row, "mip_node_count")
        for row in all_solver_rows
    )
    maximum_error = max(
        _finite_number(row.get("objective_error"), "objective error")
        for row in all_solver_rows
    )

    h5_wide = _mapping(_mapping(h5, "exact_hindsight"), "wide")
    h5_deep = _mapping(_mapping(h5, "exact_hindsight"), "deep")
    h10_wide = _mapping(_mapping(h10, "exact_hindsight"), "wide")
    h10_deep = _mapping(_mapping(h10, "exact_hindsight"), "deep")
    source = _mapping(hindsight_plan, "source")
    protocol = _mapping(hindsight_plan, "protocol")
    diagnostic = _mapping(hindsight_plan, "diagnostic")
    solver = _mapping(diagnostic, "solver")
    capacity = _mapping(result, "capacity_decision")
    nomination = _mapping(result, "nomination")

    summary: dict[str, object] = {
        "schema_version": "barcarolle_multi_swe_hindsight_summary_v1",
        "study_id": result.get("study_id"),
        "epistemic_status": result.get("epistemic_status"),
        "identities": {
            "hindsight_plan_digest": result.get("hindsight_plan_digest"),
            "selector_plan_digest": result.get("selector_plan_digest"),
            "task_space_results_digest": result.get(
                "task_space_results_digest"
            ),
            "outcome_results_digest": result.get("outcome_results_digest"),
            "hindsight_results_digest": result.get(
                "hindsight_results_digest"
            ),
        },
        "protocol": {
            "task_count": result.get("task_count"),
            "configuration_count": source.get("configuration_count"),
            "origin_count": result.get("origin_count"),
            "selection_budget_tasks": protocol.get(
                "selection_budget_tasks"
            ),
            "loss": (
                "macro-repository mean of Origin-level 36-configuration "
                "pass-rate MAE"
            ),
            "baseline": "full eligible history",
            "solver": (
                f"scipy.optimize.milp {solver.get('version')} using "
                f"{solver.get('backend')}, presolve enabled, zero relative "
                "MIP gap"
            ),
            "claim_boundary": result.get("claim_boundary"),
        },
        "solver_evidence": {
            "certified_optimum_count": sum(
                row.get("success") is True and row.get("status") == 0
                for row in all_solver_rows
            ),
            "mip_gap_values": mip_gaps,
            "maximum_objective_recomputation_error": maximum_error,
            "mip_node_count_range": [
                min(node_counts),
                max(node_counts),
            ],
            "h5_response_pattern_count": _mapping(
                _mapping(h5, "solver_summary"),
                "response_pattern_count",
            ),
            "h10_response_pattern_count": _mapping(
                _mapping(h10, "solver_summary"),
                "response_pattern_count",
            ),
            "byte_identical_second_run": byte_identical,
        },
        "results": {
            "h5": _horizon_evidence_summary(h5, h5_wide, h5_deep),
            "h10": _horizon_evidence_summary(h10, h10_wide, h10_deep),
        },
        "decision": {
            "capacity_supported": capacity.get("all_requirements_met"),
            "decision": capacity.get("decision"),
            "interpretation": capacity.get("interpretation"),
            "predictive_selector_nominated": nomination.get(
                "selector_nominated"
            ),
            "independent_confirmation_authorized": nomination.get(
                "independent_confirmation_authorized"
            ),
            "production_promotion_allowed": nomination.get(
                "production_promotion_allowed"
            ),
            "next_research_constraint": (
                "Develop only a pre-Origin information mechanism with "
                "repository-held-out evaluation; do not tune the budget from "
                "this hindsight result and do not train on hindsight "
                "memberships."
            ),
        },
        "resource_use": result.get("resource_use"),
    }
    summary["hindsight_summary_digest"] = canonical_digest(summary)
    return summary


def _validate_in_memory_hindsight_result(
    result: Mapping[str, object],
    hindsight_plan: Mapping[str, object],
) -> None:
    digest = result.get("hindsight_results_digest")
    if canonical_digest(
        {
            key: value
            for key, value in result.items()
            if key != "hindsight_results_digest"
        }
    ) != digest:
        raise ValueError("in-memory hindsight result digest does not match")
    source = _mapping(hindsight_plan, "source")
    if (
        result.get("schema_version") != RESULT_SCHEMA
        or result.get("hindsight_plan_digest")
        != hindsight_plan.get("hindsight_plan_digest")
        or result.get("selector_plan_digest")
        != source.get("selector_plan_digest")
        or result.get("task_space_results_digest")
        != source.get("task_space_results_digest")
        or result.get("outcome_results_digest")
        != source.get("outcome_results_digest")
    ):
        raise ValueError("in-memory hindsight result does not bind plan")
    task_count = _positive_integer(source, "task_count")
    configuration_count = _positive_integer(source, "configuration_count")
    if (
        result.get("task_count") != task_count
        or result.get("configuration_count") != configuration_count
    ):
        raise ValueError("hindsight result source dimensions changed")

    protocol = _mapping(hindsight_plan, "protocol")
    budget = _positive_integer(protocol, "selection_budget_tasks")
    horizon_specs = _mapping_sequence(protocol, "horizons")
    horizons = _mapping(result, "horizons")
    if set(horizons) != {
        str(_positive_integer(spec, "future_tasks")) for spec in horizon_specs
    }:
        raise ValueError("hindsight result horizons changed")

    total_origins = 0
    for spec in horizon_specs:
        horizon_key = str(_positive_integer(spec, "future_tasks"))
        horizon = _mapping(horizons, horizon_key)
        expected_origins = _positive_integer(spec, "origin_count")
        expected_repositories = _positive_integer(spec, "repository_count")
        expected_deep_repositories = _positive_integer(
            spec,
            "deep_repository_count",
        )
        repository_ids = _string_tuple(
            horizon.get("repository_ids"),
            "hindsight result repositories",
        )
        deep_repository_ids = _string_tuple(
            horizon.get("deep_repository_ids"),
            "hindsight result deep repositories",
        )
        if (
            len(repository_ids) != expected_repositories
            or len(deep_repository_ids) != expected_deep_repositories
            or not set(deep_repository_ids) <= set(repository_ids)
        ):
            raise ValueError("hindsight result repository cohorts changed")

        solver_rows = _mapping(horizon, "solver_rows")
        memberships = _mapping(horizon, "memberships")
        if (
            len(solver_rows) != expected_origins
            or set(solver_rows) != set(memberships)
        ):
            raise ValueError("hindsight result Origin coverage changed")
        normalized_memberships = {}
        pattern_counts = []
        objective_errors = []
        for origin_id, row_value in solver_rows.items():
            if not isinstance(row_value, Mapping):
                raise ValueError("hindsight solver row is malformed")
            row = row_value
            if (
                row.get("success") is not True
                or row.get("status") != 0
                or _finite_number(row.get("mip_gap"), "MIP gap") != 0.0
            ):
                raise ValueError("hindsight solver row is not certified optimal")
            solver_objective = _finite_number(
                row.get("solver_objective"),
                "solver objective",
            )
            recomputed_objective = _finite_number(
                row.get("recomputed_objective"),
                "recomputed objective",
            )
            objective_error = _finite_number(
                row.get("objective_error"),
                "objective error",
            )
            if (
                objective_error > 1e-8
                or abs(
                    objective_error
                    - abs(solver_objective - recomputed_objective)
                )
                > 1e-12
            ):
                raise ValueError("hindsight solver objective verification failed")
            pattern_counts.append(
                _positive_integer(row, "response_pattern_count")
            )
            objective_errors.append(objective_error)
            selected = _string_tuple(
                memberships[origin_id],
                "hindsight membership",
            )
            if len(selected) != budget:
                raise ValueError("hindsight membership budget changed")
            normalized_memberships[origin_id] = selected
        if canonical_digest(tuple(sorted(normalized_memberships.items()))) != (
            horizon.get("membership_digest")
        ):
            raise ValueError("hindsight membership digest changed")

        solver_summary = _mapping(horizon, "solver_summary")
        expected_pattern_summary = {
            "minimum": min(pattern_counts),
            "median": _median(pattern_counts),
            "maximum": max(pattern_counts),
        }
        if (
            solver_summary.get("origin_count") != expected_origins
            or solver_summary.get("certified_optimum_count") != expected_origins
            or _finite_number(
                solver_summary.get("maximum_objective_error"),
                "maximum objective error",
            )
            != max(objective_errors)
            or _mapping(solver_summary, "response_pattern_count")
            != expected_pattern_summary
        ):
            raise ValueError("hindsight solver summary changed")

        exact_hindsight = _mapping(horizon, "exact_hindsight")
        _validate_repository_view(
            _mapping(exact_hindsight, "wide"),
            repository_ids,
            expected_origins,
        )
        _validate_repository_view(
            _mapping(exact_hindsight, "deep"),
            deep_repository_ids,
            None,
        )
        total_origins += expected_origins

    if result.get("origin_count") != total_origins:
        raise ValueError("hindsight total Origin count changed")
    recomputed_decision = _capacity_decision(horizons)
    if canonical_json(recomputed_decision) != canonical_json(
        _mapping(result, "capacity_decision")
    ):
        raise ValueError("hindsight capacity decision is not reproducible")
    nomination = _mapping(result, "nomination")
    if any(
        nomination.get(key) is not False
        for key in (
            "selector_nominated",
            "independent_confirmation_authorized",
            "production_promotion_allowed",
        )
    ):
        raise ValueError("hindsight result cannot nominate or promote")
    resource_use = _mapping(result, "resource_use")
    if any(
        resource_use.get(key) != 0
        for key in (
            "paid_api_calls",
            "embedding_api_calls",
            "sealed_swe_bench_holdout_agents_opened",
        )
    ):
        raise ValueError("hindsight resource boundary changed")


def _validate_repository_view(
    view: Mapping[str, object],
    repository_ids: Sequence[str],
    expected_origins: int | None,
) -> None:
    rows = _mapping_sequence(view, "repository_rows")
    observed_repositories = tuple(
        _required_string(row, "repository_id") for row in rows
    )
    if (
        len(rows) != len(repository_ids)
        or set(observed_repositories) != set(repository_ids)
        or view.get("repository_count") != len(repository_ids)
    ):
        raise ValueError("hindsight repository summary cohort changed")
    origin_count = sum(_positive_integer(row, "origin_count") for row in rows)
    if (
        view.get("origin_count") != origin_count
        or expected_origins is not None
        and origin_count != expected_origins
    ):
        raise ValueError("hindsight repository summary Origin count changed")
    mean_loss = _mean(
        tuple(_finite_number(row.get("mean_loss"), "mean loss") for row in rows)
    )
    mean_baseline = _mean(
        tuple(
            _finite_number(
                row.get("mean_baseline_loss"),
                "mean baseline loss",
            )
            for row in rows
        )
    )
    mean_difference = _mean(
        tuple(
            _finite_number(row.get("mean_difference"), "mean difference")
            for row in rows
        )
    )
    if (
        abs(
            _finite_number(view.get("macro_repository_loss"), "macro loss")
            - mean_loss
        )
        > 1e-12
        or abs(
            _finite_number(
                view.get("macro_repository_baseline_loss"),
                "macro baseline loss",
            )
            - mean_baseline
        )
        > 1e-12
        or abs(
            _finite_number(
                view.get("macro_repository_difference"),
                "macro difference",
            )
            - mean_difference
        )
        > 1e-12
        or view.get("favorable_repository_count")
        != sum(
            _finite_number(row.get("mean_difference"), "mean difference") < 0.0
            for row in rows
        )
    ):
        raise ValueError("hindsight repository summary values changed")


def _solver_rows(
    horizon: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(horizon, "solver_rows")
    if not rows or any(not isinstance(row, Mapping) for row in rows.values()):
        raise ValueError("hindsight solver rows are malformed")
    return tuple(rows.values())


def _horizon_evidence_summary(
    horizon: Mapping[str, object],
    wide: Mapping[str, object],
    deep: Mapping[str, object],
) -> Mapping[str, object]:
    baseline = _finite_number(
        wide.get("macro_repository_baseline_loss"),
        "baseline loss",
    )
    loss = _finite_number(wide.get("macro_repository_loss"), "hindsight loss")
    repository_count = _positive_integer(wide, "repository_count")
    deep_repository_count = _positive_integer(deep, "repository_count")
    return {
        "origin_count": _positive_integer(wide, "origin_count"),
        "repository_count": repository_count,
        "full_history_macro_mae": baseline,
        "exact_hindsight_macro_mae": loss,
        "exact_hindsight_minus_full_history": _finite_number(
            wide.get("macro_repository_difference"),
            "hindsight difference",
        ),
        "relative_loss_reduction": (baseline - loss) / baseline,
        "favorable_repositories": (
            f"{_positive_or_zero_integer(wide, 'favorable_repository_count')}/"
            f"{repository_count}"
        ),
        "deep_exact_hindsight_minus_full_history": _finite_number(
            deep.get("macro_repository_difference"),
            "deep hindsight difference",
        ),
        "deep_favorable_repositories": (
            f"{_positive_or_zero_integer(deep, 'favorable_repository_count')}/"
            f"{deep_repository_count}"
        ),
        "membership_digest": horizon.get("membership_digest"),
    }


def _result_summary(result: Mapping[str, object]) -> Mapping[str, object]:
    horizons = _mapping(result, "horizons")
    return {
        "schema_version": "barcarolle_multi_swe_hindsight_summary_v1",
        "study_id": result.get("study_id"),
        "hindsight_plan_digest": result.get("hindsight_plan_digest"),
        "hindsight_results_digest": result.get("hindsight_results_digest"),
        "origin_count": result.get("origin_count"),
        "horizons": {
            horizon: {
                "solver_summary": _mapping(
                    _mapping(horizons, horizon),
                    "solver_summary",
                ),
                "exact_hindsight": _mapping(
                    _mapping(horizons, horizon),
                    "exact_hindsight",
                ),
                "membership_digest": _mapping(horizons, horizon).get(
                    "membership_digest"
                ),
            }
            for horizon in ("5", "10")
        },
        "capacity_decision": result.get("capacity_decision"),
        "nomination": result.get("nomination"),
        "resource_use": result.get("resource_use"),
        "claim_boundary": result.get("claim_boundary"),
    }


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


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


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not (-float("inf") < result < float("inf")):
        raise ValueError(f"{label} must be finite")
    return result


def _optional_finite_number(value: object) -> float | None:
    if value is None:
        return None
    return _finite_number(value, "optional solver value")


def _optional_integer(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("optional solver count must be numeric")
    result = int(round(float(value)))
    if abs(float(value) - result) > 1e-7 or result < 0:
        raise ValueError("optional solver count must be a nonnegative integer")
    return result


def _positive_or_zero_integer(
    payload: Mapping[str, object],
    key: str,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{key} must be numeric")
    result = int(round(float(value)))
    if abs(float(value) - result) > 1e-7 or result < 0:
        raise ValueError(f"{key} must be a nonnegative integer")
    return result


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _median(values: Sequence[int]) -> float:
    if not values:
        raise ValueError("median requires values")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diagnostic-plan",
        type=Path,
        default=DEFAULT_DIAGNOSTIC_PLAN,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="solve the exact hindsight MILPs")
    run.add_argument("--task-content", type=Path, required=True)
    run.add_argument("--task-times", type=Path, required=True)
    run.add_argument("--task-space-results", type=Path, required=True)
    run.add_argument("--outcome-results", type=Path, required=True)
    run.add_argument("--panel-summary", type=Path, required=True)
    run.add_argument("--resolved-outcomes", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)

    summary = commands.add_parser(
        "verify-summary",
        help="rebuild and verify the committed compact summary",
    )
    summary.add_argument("--results", type=Path, required=True)
    summary.add_argument(
        "--reproduction-results",
        type=Path,
        required=True,
    )
    summary.add_argument("--summary", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    hindsight_plan = load_hindsight_plan(arguments.diagnostic_plan)
    if arguments.command == "verify-summary":
        result = load_hindsight_results(arguments.results, hindsight_plan)
        reproduction = load_hindsight_results(
            arguments.reproduction_results,
            hindsight_plan,
        )
        expected = build_hindsight_evidence_summary(
            result,
            hindsight_plan,
            reproduction,
        )
        observed = _load_mapping(arguments.summary)
        if canonical_json(expected) != canonical_json(observed):
            raise ValueError("committed hindsight summary does not match results")
        print(json.dumps(expected, indent=2, sort_keys=True))
        return 0
    if arguments.command != "run":
        raise AssertionError(arguments.command)
    if arguments.output.exists():
        raise FileExistsError(
            f"refusing to overwrite hindsight output: {arguments.output}"
        )
    selector_plan = load_selector_plan()
    source = _mapping(hindsight_plan, "source")
    if selector_plan.get("selector_plan_digest") != source.get(
        "selector_plan_digest"
    ):
        raise ValueError("hindsight plan does not bind Selector plan")
    content_manifest = load_content_manifest()
    if content_manifest.get("content_manifest_digest") != source.get(
        "content_manifest_digest"
    ):
        raise ValueError("hindsight plan does not bind Task content")
    embedding_manifest = load_embedding_manifest()
    task_space_results = load_task_space_results(
        arguments.task_space_results,
        selector_plan,
        embedding_manifest,
    )
    outcome_results = load_outcome_results(
        arguments.outcome_results,
        hindsight_plan,
    )
    content_rows = load_task_content(
        arguments.task_content,
        content_manifest,
    )
    tasks = load_task_metadata(
        content_rows,
        arguments.task_times,
        selector_plan,
    )
    task_ids = tuple(task.instance_id for task in tasks)
    outcomes, configuration_metadata, outcome_diagnostics = (
        load_public_outcomes(
            arguments.panel_summary,
            arguments.resolved_outcomes,
            task_ids,
            selector_plan,
        )
    )
    if outcome_diagnostics != outcome_results.get("outcome_diagnostics"):
        raise ValueError("hindsight public outcome panel changed")
    result = run_hindsight_diagnostic(
        tasks,
        outcomes,
        configuration_metadata,
        task_space_results,
        outcome_results,
        selector_plan,
        hindsight_plan,
    )
    arguments.output.write_text(
        canonical_json(result) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(_result_summary(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
