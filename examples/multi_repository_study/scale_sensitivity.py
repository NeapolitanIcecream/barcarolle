#!/usr/bin/env python3
"""Audit Selection-budget and future-horizon sensitivity on one Origin cohort."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from datetime import timedelta
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path
from statistics import median
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
)
from examples.multi_repository_study.adaptive_difficulty import (  # noqa: E402
    forecast_stationary_difficulty,
    load_adaptive_difficulty_plan,
)
from examples.multi_repository_study.agent_invariant import (  # noqa: E402
    evaluate_memberships,
    fit_cutoff_repository_equal_markov,
    forecast_difficulty_markov,
    load_agent_invariant_plan,
    select_state_histogram_match,
)
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.panel_extension import (  # noqa: E402
    load_agent_panel_extension_plan,
    load_allocated_outcomes,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    future_pass_rate_mae,
    load_dataset_tasks,
    load_portfolio,
    load_public_outcomes,
    load_public_panel_plan,
    random_calibration,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "scale-sensitivity-plan.json"
DEFAULT_AGENT_PLAN = HERE / "agent-invariant-plan.json"
DEFAULT_ADAPTIVE_PLAN = HERE / "adaptive-difficulty-plan.json"
DEFAULT_ADAPTIVE_RESULTS = HERE / "adaptive-difficulty-results.json"
DEFAULT_EXTENSION_PLAN = HERE / "agent-panel-extension-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "scale-sensitivity-results.json"

SELECTOR_IDS = (
    "recency",
    "stationary_difficulty_match",
    "difficulty_markov_match",
)


def load_scale_sensitivity_plan(
    path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("scale-sensitivity plan must be an object")
    if (
        payload.get("schema_version")
        != "barcarolle_budget_horizon_sensitivity_plan_v1"
    ):
        raise ValueError("scale-sensitivity plan schema is unsupported")
    digest = payload.get("scale_sensitivity_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "scale_sensitivity_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("scale-sensitivity plan digest does not match")
    return payload


def build_common_scale_origins(
    tasks: Sequence[TaskMetadata],
    repository_ids: Sequence[str],
    *,
    minimum_history_tasks: int,
    origin_step_tasks: int,
    maximum_task_count_horizon: int,
    task_count_horizon: int,
) -> Mapping[str, tuple[RepositoryOrigin, ...]]:
    """Build horizon-nested Origins without changing cutoffs between cells."""
    if (
        minimum_history_tasks <= 0
        or origin_step_tasks <= 0
        or maximum_task_count_horizon <= 0
        or not 0 < task_count_horizon <= maximum_task_count_horizon
    ):
        raise ValueError("common Origin dimensions must be positive and nested")
    selected_repositories = _string_tuple(repository_ids, "repository IDs")
    tasks_by_repository = _ordered_tasks_by_repository(tasks)
    result = {}
    for repository_id in selected_repositories:
        repository_tasks = tasks_by_repository.get(repository_id, ())
        origins = []
        for history_count in range(
            minimum_history_tasks,
            len(repository_tasks) - maximum_task_count_horizon + 1,
            origin_step_tasks,
        ):
            origins.append(
                RepositoryOrigin(
                    repository_id=repository_id,
                    origin_id=(
                        f"{repository_id}:scale-origin-{history_count:03d}"
                    ),
                    history=repository_tasks[:history_count],
                    future=repository_tasks[
                        history_count : history_count + task_count_horizon
                    ],
                )
            )
        if origins:
            result[repository_id] = tuple(origins)
    return result


def materialize_scale_selections(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    evaluation_repository_ids: Sequence[str],
    training_repository_ids: Sequence[str],
    *,
    selection_budget: int,
    task_count_horizon: int,
    state_count: int,
    cell_prior_mass: float,
    local_prior_strength: float,
) -> tuple[Mapping[str, Mapping[str, tuple[str, ...]]], Mapping[str, Any]]:
    """Materialize the three frozen controls for one response-surface cell."""
    if selection_budget <= 0 or task_count_horizon <= 0:
        raise ValueError("cell budget and horizon must be positive")
    evaluation_ids = _string_tuple(
        evaluation_repository_ids,
        "evaluation repository IDs",
    )
    training_ids = _string_tuple(
        training_repository_ids,
        "training repository IDs",
    )
    tasks_by_repository = _ordered_tasks_by_repository(tasks)
    memberships: dict[str, dict[str, tuple[str, ...]]] = {
        selector_id: {} for selector_id in SELECTOR_IDS
    }
    fit_rows = []
    transition_digests = {}
    for target_repository_id in evaluation_ids:
        if target_repository_id not in origins_by_repository:
            raise ValueError(f"evaluation repository has no Origins: {target_repository_id}")
        non_target_training_ids = tuple(
            repository_id
            for repository_id in training_ids
            if repository_id != target_repository_id
        )
        for origin in origins_by_repository[target_repository_id]:
            if (
                len(origin.history) < selection_budget
                or len(origin.future) != task_count_horizon
            ):
                raise ValueError("cell dimensions do not fit the common Origin")
            transition, fit_diagnostic = fit_cutoff_repository_equal_markov(
                non_target_training_ids,
                tasks_by_repository,
                outcomes_by_agent,
                cutoff=origin.history[-1].created_at,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
            )
            fit_rows.append(fit_diagnostic)
            transition_digests[origin.origin_id] = canonical_digest(transition)
            stationary_forecast = forecast_stationary_difficulty(
                origin.history,
                outcomes_by_agent,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
            )
            markov_forecast = forecast_difficulty_markov(
                origin.history,
                outcomes_by_agent,
                transition,
                state_count=state_count,
                horizon=task_count_horizon,
                local_prior_strength=local_prior_strength,
            )
            memberships["recency"][origin.origin_id] = tuple(
                task.instance_id
                for task in origin.history[-selection_budget:]
            )
            memberships["stationary_difficulty_match"][
                origin.origin_id
            ] = select_state_histogram_match(
                origin.history,
                outcomes_by_agent,
                stationary_forecast,
                state_count=state_count,
                budget=selection_budget,
            )
            memberships["difficulty_markov_match"][
                origin.origin_id
            ] = select_state_histogram_match(
                origin.history,
                outcomes_by_agent,
                markov_forecast,
                state_count=state_count,
                budget=selection_budget,
            )
    return (
        {
            selector_id: dict(sorted(rows.items()))
            for selector_id, rows in memberships.items()
        },
        _fit_summary(fit_rows, transition_digests),
    )


def horizon_diagnostics(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    common_origins_by_horizon: Mapping[
        int,
        Mapping[str, Sequence[RepositoryOrigin]],
    ],
    evaluation_repository_ids: Sequence[str],
    source_repository_ids: Sequence[str],
    *,
    nonoverlap_minimum_history_tasks: int,
    nonoverlap_horizons: Sequence[int],
    nested_pairs: Sequence[Sequence[int]],
    calendar_duration_days: Sequence[int],
) -> Mapping[str, Any]:
    """Separate task-count target instability from source calendar capacity."""
    evaluation_ids = _string_tuple(
        evaluation_repository_ids,
        "evaluation repository IDs",
    )
    source_ids = _string_tuple(source_repository_ids, "source repository IDs")
    tasks_by_repository = _ordered_tasks_by_repository(tasks)
    nonoverlap = {}
    for horizon in _positive_integer_tuple(
        nonoverlap_horizons,
        "non-overlap horizons",
    ):
        rows = {
            repository_id: max(
                0,
                (
                    len(tasks_by_repository.get(repository_id, ()))
                    - nonoverlap_minimum_history_tasks
                )
                // horizon,
            )
            for repository_id in source_ids
        }
        nonoverlap[str(horizon)] = {
            "origin_count": sum(rows.values()),
            "eligible_repository_count": sum(value > 0 for value in rows.values()),
            "origin_counts": rows,
        }

    nested = {}
    for pair in nested_pairs:
        if (
            len(pair) != 2
            or isinstance(pair[0], bool)
            or isinstance(pair[1], bool)
            or not isinstance(pair[0], int)
            or not isinstance(pair[1], int)
        ):
            raise ValueError("nested horizon pair is invalid")
        left, right = pair
        left_origins = common_origins_by_horizon[left]
        right_origins = common_origins_by_horizon[right]
        by_repository = {}
        for repository_id in evaluation_ids:
            right_by_id = {
                origin.origin_id: origin
                for origin in right_origins[repository_id]
            }
            values = tuple(
                future_pass_rate_mae(
                    tuple(task.instance_id for task in origin.future),
                    tuple(
                        task.instance_id
                        for task in right_by_id[origin.origin_id].future
                    ),
                    outcomes_by_agent,
                )
                for origin in left_origins[repository_id]
            )
            by_repository[repository_id] = _numeric_summary(values)
        nested[f"{left}_vs_{right}"] = {
            "macro_repository_mean_absolute_target_difference": _mean(
                tuple(
                    float(summary["mean"])
                    for summary in by_repository.values()
                )
            ),
            "repository_summaries": by_repository,
        }

    calendar_spans = {}
    for horizon, origins_by_repository in sorted(
        common_origins_by_horizon.items()
    ):
        by_repository = {}
        for repository_id in evaluation_ids:
            spans = tuple(
                (
                    parse_utc_timestamp(origin.future[-1].created_at)
                    - parse_utc_timestamp(origin.history[-1].created_at)
                ).total_seconds()
                / 86_400.0
                for origin in origins_by_repository[repository_id]
            )
            by_repository[repository_id] = _numeric_summary(spans)
        all_spans = tuple(
            (
                parse_utc_timestamp(origin.future[-1].created_at)
                - parse_utc_timestamp(origin.history[-1].created_at)
            ).total_seconds()
            / 86_400.0
            for repository_id in evaluation_ids
            for origin in origins_by_repository[repository_id]
        )
        calendar_spans[str(horizon)] = {
            "all_origin_days": _numeric_summary(all_spans),
            "repository_summaries": by_repository,
        }

    maximum_horizon = max(common_origins_by_horizon)
    reference_origins = common_origins_by_horizon[maximum_horizon]
    calendar_capacity = {}
    for duration_days in _positive_integer_tuple(
        calendar_duration_days,
        "calendar duration days",
    ):
        counts_by_repository = {}
        for repository_id in evaluation_ids:
            repository_tasks = tasks_by_repository[repository_id]
            counts = []
            for origin in reference_origins[repository_id]:
                cutoff = parse_utc_timestamp(origin.history[-1].created_at)
                end = cutoff + timedelta(days=duration_days)
                counts.append(
                    sum(
                        parse_utc_timestamp(task.created_at) <= end
                        for task in repository_tasks[len(origin.history) :]
                    )
                )
            counts_by_repository[repository_id] = tuple(counts)
        all_counts = tuple(
            value
            for repository_counts in counts_by_repository.values()
            for value in repository_counts
        )
        calendar_capacity[str(duration_days)] = {
            "all_origin_task_count": _numeric_summary(all_counts),
            "zero_task_origin_count": sum(value == 0 for value in all_counts),
            "repository_summaries": {
                repository_id: _numeric_summary(counts)
                for repository_id, counts in counts_by_repository.items()
            },
        }

    return {
        "nonoverlapping_source_capacity": {
            "minimum_history_tasks": nonoverlap_minimum_history_tasks,
            "by_task_count_horizon": nonoverlap,
        },
        "nested_future_target_disagreement": nested,
        "task_count_horizon_calendar_span_days": calendar_spans,
        "fixed_calendar_duration_source_capacity": calendar_capacity,
    }


def run_scale_sensitivity(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    adaptive_plan: Mapping[str, object],
    extension_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the complete frozen grid without touching the sealed Agent panel."""
    _validate_sources(
        tasks,
        outcomes_by_agent,
        plan,
        agent_plan,
        adaptive_plan,
        extension_plan,
        public_plan,
        portfolio,
    )
    cohort = _mapping(plan, "common_origin_cohort")
    response = _mapping(plan, "response_surface")
    diagnostics_plan = _mapping(plan, "horizon_diagnostics")
    budgets = _positive_integer_tuple(
        response.get("selection_budgets"),
        "selection budgets",
    )
    horizons = _positive_integer_tuple(
        response.get("task_count_horizons"),
        "task-count horizons",
    )
    evaluation_repository_ids = _string_tuple(
        cohort.get("expected_repository_ids"),
        "expected repository IDs",
    )
    public_portfolio = _mapping(public_plan, "portfolio")
    training_repository_ids = _string_tuple(
        public_portfolio.get("wide_repository_ids"),
        "wide repository IDs",
    )
    deep_repository_ids = tuple(
        repository_id
        for repository_id in _string_tuple(
            public_portfolio.get("deep_repository_ids"),
            "deep repository IDs",
        )
        if repository_id in set(evaluation_repository_ids)
    )
    common_origins_by_horizon = {
        horizon: build_common_scale_origins(
            tasks,
            evaluation_repository_ids,
            minimum_history_tasks=_positive_integer(
                cohort,
                "minimum_history_tasks",
            ),
            origin_step_tasks=_positive_integer(cohort, "origin_step_tasks"),
            maximum_task_count_horizon=_positive_integer(
                cohort,
                "maximum_task_count_horizon",
            ),
            task_count_horizon=horizon,
        )
        for horizon in horizons
    }
    _validate_common_cohort(common_origins_by_horizon, cohort, budgets)

    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    aggregation = _mapping(response, "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )
    random_plan = _mapping(response, "random_calibration")
    random_draws = _positive_integer(random_plan, "draws")
    random_seed = _integer(random_plan, "seed")
    agent_algorithm = _mapping_sequence(agent_plan, "fixed_algorithms")[1]
    state_count = _positive_integer(
        _mapping(agent_plan, "difficulty_representation"),
        "state_count",
    )
    cell_prior_mass = _number(
        agent_algorithm.get("training_symmetric_dirichlet_cell_mass"),
        "cell prior mass",
    )
    local_prior_strength = _number(
        agent_algorithm.get("target_local_transition_prior_total_mass_per_row"),
        "local prior strength",
    )

    cells = {}
    for budget in budgets:
        for horizon in horizons:
            cell_id = f"budget-{budget:02d}_horizon-{horizon:02d}"
            origins = common_origins_by_horizon[horizon]
            memberships, fit_diagnostics = materialize_scale_selections(
                tasks,
                outcomes_by_agent,
                origins,
                evaluation_repository_ids,
                training_repository_ids,
                selection_budget=budget,
                task_count_horizon=horizon,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
                local_prior_strength=local_prior_strength,
            )
            rows = evaluate_memberships(
                origins,
                memberships,
                outcomes_by_agent,
                evaluation_repository_ids,
                cluster_by_repository,
            )
            summaries = _summaries(
                rows,
                evaluation_repository_ids,
                deep_repository_ids,
                bootstrap_seed,
                bootstrap_resamples,
            )
            cell_seed = random_seed + 100 * budget + horizon
            random_reports = {
                portfolio_name: random_calibration(
                    selected_repositories,
                    origins,
                    outcomes_by_agent,
                    budget=budget,
                    draws=random_draws,
                    seed=cell_seed,
                    observed_summaries=summaries[portfolio_name],
                )
                for portfolio_name, selected_repositories in (
                    ("wide", evaluation_repository_ids),
                    ("deep", deep_repository_ids),
                )
            }
            leave_one_agent = _run_leave_one_agent_out(
                tasks,
                outcomes_by_agent,
                origins,
                evaluation_repository_ids,
                training_repository_ids,
                deep_repository_ids,
                cluster_by_repository,
                selection_budget=budget,
                task_count_horizon=horizon,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
                local_prior_strength=local_prior_strength,
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )
            cells[cell_id] = {
                "selection_budget": budget,
                "task_count_horizon": horizon,
                "origin_schedule_digest": canonical_digest(
                    _origin_schedule_identity(origins)
                ),
                "selection_membership_digests": {
                    selector_id: canonical_digest(tuple(sorted(rows.items())))
                    for selector_id, rows in memberships.items()
                },
                "fit_diagnostics": fit_diagnostics,
                "summaries": summaries,
                "random_calibration": random_reports,
                "leave_one_agent_out": leave_one_agent,
            }

    decision = _development_decision(cells, plan, budgets, horizons)
    diagnostic_result = horizon_diagnostics(
        tasks,
        outcomes_by_agent,
        common_origins_by_horizon,
        evaluation_repository_ids,
        training_repository_ids,
        nonoverlap_minimum_history_tasks=_positive_integer(
            diagnostics_plan,
            "nonoverlapping_capacity_minimum_history_tasks",
        ),
        nonoverlap_horizons=_positive_integer_tuple(
            diagnostics_plan.get("nonoverlapping_capacity_horizons"),
            "non-overlap capacity horizons",
        ),
        nested_pairs=_sequence(diagnostics_plan, "nested_task_count_pairs"),
        calendar_duration_days=_positive_integer_tuple(
            diagnostics_plan.get("calendar_duration_days"),
            "calendar duration days",
        ),
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_budget_horizon_sensitivity_results_v1",
        "study_id": plan.get("study_id"),
        "epistemic_status": "opened_development_estimand_sensitivity",
        "scale_sensitivity_plan_digest": plan.get(
            "scale_sensitivity_plan_digest"
        ),
        "source": {
            "dataset_sha256": _mapping(plan, "source").get("dataset_sha256"),
            "portfolio_digest": portfolio.get("portfolio_digest"),
            "public_panel_plan_digest": public_plan.get(
                "public_panel_plan_digest"
            ),
            "agent_panel_extension_plan_digest": extension_plan.get(
                "agent_panel_extension_plan_digest"
            ),
            "agent_invariant_plan_digest": agent_plan.get(
                "agent_invariant_plan_digest"
            ),
            "adaptive_difficulty_plan_digest": adaptive_plan.get(
                "adaptive_difficulty_plan_digest"
            ),
            "task_count": len(tasks),
            "development_agent_count": len(outcomes_by_agent),
            "holdout_result_blob_reads": 0,
        },
        "common_origin_cohort": {
            "repository_ids": evaluation_repository_ids,
            "deep_repository_ids": deep_repository_ids,
            "origin_counts": {
                repository_id: len(
                    common_origins_by_horizon[horizons[0]][repository_id]
                )
                for repository_id in evaluation_repository_ids
            },
            "origin_count": sum(
                len(common_origins_by_horizon[horizons[0]][repository_id])
                for repository_id in evaluation_repository_ids
            ),
            "common_cutoff_digest": canonical_digest(
                tuple(
                    (
                        origin.repository_id,
                        origin.origin_id,
                        origin.history[-1].created_at,
                    )
                    for repository_id in evaluation_repository_ids
                    for origin in common_origins_by_horizon[horizons[0]][
                        repository_id
                    ]
                )
            ),
        },
        "agent_outcome_diagnostics": dict(sorted(outcome_diagnostics.items())),
        "cells": dict(sorted(cells.items())),
        "horizon_diagnostics": diagnostic_result,
        "decision": decision,
        "time_semantics": {
            "executed_mode": "source_time_cutoff_safe_counterfactual",
            "task_time_role": (
                "created_at orders local Tasks, defines the target cutoff, and "
                "filters cross-repository training Tasks"
            ),
            "result_availability_role": (
                "not represented by this public panel; projected labels cannot "
                "support a strict historical deployability claim"
            ),
            "product_boundary": (
                "Task time is configurable import metadata. Strict Result "
                "availability is an optional evidence mode, not a prerequisite "
                "for running Selection."
            ),
        },
        "claim_boundary": (
            "This complete opened-development grid diagnoses scale and target "
            "sensitivity. It cannot promote a Selector, choose an observed cell "
            "as a default, or authorize reading the six-Agent holdout."
        ),
    }
    result["scale_sensitivity_results_digest"] = canonical_digest(result)
    return result


def _run_leave_one_agent_out(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    evaluation_repository_ids: Sequence[str],
    training_repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    cluster_by_repository: Mapping[str, str],
    *,
    selection_budget: int,
    task_count_horizon: int,
    state_count: int,
    cell_prior_mass: float,
    local_prior_strength: float,
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Any]:
    by_agent = {}
    membership_digests = {}
    for held_out_agent_id in sorted(outcomes_by_agent):
        reference_outcomes = {
            agent_id: outcomes
            for agent_id, outcomes in outcomes_by_agent.items()
            if agent_id != held_out_agent_id
        }
        memberships, _ = materialize_scale_selections(
            tasks,
            reference_outcomes,
            origins_by_repository,
            evaluation_repository_ids,
            training_repository_ids,
            selection_budget=selection_budget,
            task_count_horizon=task_count_horizon,
            state_count=state_count,
            cell_prior_mass=cell_prior_mass,
            local_prior_strength=local_prior_strength,
        )
        rows = evaluate_memberships(
            origins_by_repository,
            memberships,
            {held_out_agent_id: outcomes_by_agent[held_out_agent_id]},
            evaluation_repository_ids,
            cluster_by_repository,
        )
        summaries = _summaries(
            rows,
            evaluation_repository_ids,
            deep_repository_ids,
            bootstrap_seed,
            bootstrap_resamples,
        )
        by_agent[held_out_agent_id] = _compact_summaries(summaries)
        membership_digests[held_out_agent_id] = {
            selector_id: canonical_digest(tuple(sorted(items.items())))
            for selector_id, items in memberships.items()
        }
    aggregate = {}
    for selector_id in SELECTOR_IDS:
        wide_values = tuple(
            float(agent_summaries["wide"][selector_id][
                "macro_repository_difference"
            ])
            for agent_summaries in by_agent.values()
        )
        deep_values = tuple(
            float(agent_summaries["deep"][selector_id][
                "macro_repository_difference"
            ])
            for agent_summaries in by_agent.values()
        )
        aggregate[selector_id] = {
            "wide_macro_over_held_out_agents": _mean(wide_values),
            "deep_macro_over_held_out_agents": _mean(deep_values),
            "wide_favorable_held_out_agent_count": sum(
                value < 0.0 for value in wide_values
            ),
            "deep_favorable_held_out_agent_count": sum(
                value < 0.0 for value in deep_values
            ),
        }
    return {
        "by_held_out_agent": by_agent,
        "aggregate_by_selector": aggregate,
        "selection_membership_digests": membership_digests,
    }


def _development_decision(
    cells: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, object],
    budgets: Sequence[int],
    horizons: Sequence[int],
) -> Mapping[str, Any]:
    requirements_plan = _mapping(
        _mapping(plan, "development_decision_rule"),
        "cell_requirements",
    )
    cell_decisions = {}
    passed_cells = set()
    for cell_id, cell in sorted(cells.items()):
        summaries = _mapping(cell, "summaries")
        wide = _mapping(_mapping(summaries, "wide"), "difficulty_markov_match")
        deep = _mapping(_mapping(summaries, "deep"), "difficulty_markov_match")
        recency = _mapping(_mapping(summaries, "wide"), "recency")
        stationary = _mapping(
            _mapping(summaries, "wide"),
            "stationary_difficulty_match",
        )
        random_position = _number(
            _mapping(
                _mapping(
                    _mapping(
                        _mapping(cell, "random_calibration"),
                        "wide",
                    ),
                    "candidate_positions",
                ),
                "difficulty_markov_match",
            ).get("candidate_better_than_random_midrank"),
            "random percentile",
        )
        agent_transfer = _mapping(
            _mapping(
                _mapping(cell, "leave_one_agent_out"),
                "aggregate_by_selector",
            ),
            "difficulty_markov_match",
        )
        requirements = {
            "wide_macro_at_most_threshold": (
                _number(
                    wide.get("macro_repository_difference"),
                    "wide macro difference",
                )
                <= _number(
                    requirements_plan.get(
                        "wide_macro_repository_difference_at_most"
                    ),
                    "wide threshold",
                )
            ),
            "minimum_wide_favorable_repositories": (
                _integer(wide, "favorable_repository_count")
                >= _integer(
                    requirements_plan,
                    "minimum_wide_favorable_repositories",
                )
            ),
            "deep_macro_negative": (
                _number(
                    deep.get("macro_repository_difference"),
                    "deep macro difference",
                )
                < 0.0
            ),
            "minimum_random_percentile": (
                random_position
                >= _number(
                    requirements_plan.get("minimum_random_percentile"),
                    "minimum random percentile",
                )
            ),
            "better_than_recency": (
                _number(
                    wide.get("macro_repository_difference"),
                    "Markov difference",
                )
                < _number(
                    recency.get("macro_repository_difference"),
                    "recency difference",
                )
            ),
            "better_than_stationary": (
                _number(
                    wide.get("macro_repository_difference"),
                    "Markov difference",
                )
                < _number(
                    stationary.get("macro_repository_difference"),
                    "stationary difference",
                )
            ),
            "leave_one_agent_wide_macro_negative": (
                _number(
                    agent_transfer.get("wide_macro_over_held_out_agents"),
                    "leave-one-Agent macro",
                )
                < 0.0
            ),
            "minimum_favorable_leave_one_agent_count": (
                _integer(
                    agent_transfer,
                    "wide_favorable_held_out_agent_count",
                )
                >= _integer(
                    requirements_plan,
                    "minimum_favorable_leave_one_agent_count",
                )
            ),
        }
        passed = all(requirements.values())
        if passed:
            passed_cells.add(
                (
                    _integer(cell, "selection_budget"),
                    _integer(cell, "task_count_horizon"),
                )
            )
        cell_decisions[cell_id] = {
            "requirements": requirements,
            "all_requirements_met": passed,
        }
    stable_rectangles = []
    for budget_left, budget_right in zip(budgets, budgets[1:]):
        for horizon_left, horizon_right in zip(horizons, horizons[1:]):
            rectangle = (
                (budget_left, horizon_left),
                (budget_left, horizon_right),
                (budget_right, horizon_left),
                (budget_right, horizon_right),
            )
            if set(rectangle) <= passed_cells:
                stable_rectangles.append(
                    {
                        "selection_budgets": (budget_left, budget_right),
                        "task_count_horizons": (
                            horizon_left,
                            horizon_right,
                        ),
                    }
                )
    if stable_rectangles:
        status = "stable_scale_region_found_for_new_prespecified_study_only"
    elif passed_cells:
        status = "isolated_favorable_cells_do_not_reopen_candidate"
    else:
        status = "scale_sensitivity_does_not_reopen_candidate"
    return {
        "status": status,
        "cell_decisions": cell_decisions,
        "passing_cells": tuple(sorted(passed_cells)),
        "stable_rectangles": tuple(stable_rectangles),
        "holdout_open_allowed": False,
        "production_promotion_allowed": False,
    }


def _validate_sources(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    adaptive_plan: Mapping[str, object],
    extension_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> None:
    source = _mapping(plan, "source")
    expected = {
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "public_panel_plan_digest": public_plan.get("public_panel_plan_digest"),
        "agent_panel_extension_plan_digest": extension_plan.get(
            "agent_panel_extension_plan_digest"
        ),
        "agent_invariant_plan_digest": agent_plan.get(
            "agent_invariant_plan_digest"
        ),
        "adaptive_difficulty_plan_digest": adaptive_plan.get(
            "adaptive_difficulty_plan_digest"
        ),
    }
    if any(source.get(key) != value for key, value in expected.items()):
        raise ValueError("scale-sensitivity plan does not bind source plans")
    task_ids = tuple(task.instance_id for task in tasks)
    if (
        not task_ids
        or len(task_ids) != len(set(task_ids))
        or any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values())
    ):
        raise ValueError("development Agents must cover the exact Task denominator")
    if len(outcomes_by_agent) != _positive_integer(
        source,
        "development_agent_count",
    ):
        raise ValueError("development Agent count does not match plan")


def _validate_common_cohort(
    origins_by_horizon: Mapping[
        int,
        Mapping[str, Sequence[RepositoryOrigin]],
    ],
    cohort: Mapping[str, object],
    budgets: Sequence[int],
) -> None:
    expected_counts = _mapping(cohort, "expected_origin_counts")
    expected_total = _positive_integer(cohort, "expected_origin_count")
    reference_identity = None
    for horizon, origins_by_repository in sorted(origins_by_horizon.items()):
        counts = {
            repository_id: len(origins)
            for repository_id, origins in origins_by_repository.items()
        }
        if counts != {
            repository_id: _integer(expected_counts, repository_id)
            for repository_id in expected_counts
        }:
            raise ValueError(f"common Origin count changed at horizon {horizon}")
        if sum(counts.values()) != expected_total:
            raise ValueError("common Origin total does not match plan")
        identity = tuple(
            (
                origin.repository_id,
                origin.origin_id,
                tuple(task.instance_id for task in origin.history),
            )
            for repository_id in sorted(origins_by_repository)
            for origin in origins_by_repository[repository_id]
        )
        if reference_identity is None:
            reference_identity = identity
        elif identity != reference_identity:
            raise ValueError("Origin histories changed between horizons")
        for origins in origins_by_repository.values():
            for origin in origins:
                if max(budgets) >= len(origin.history):
                    raise ValueError("Selection budget is not a strict compression")


def _summaries(
    rows: Mapping[str, Sequence[ContrastRow]],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Mapping[str, Mapping[str, Any]]]:
    return {
        portfolio_name: {
            selector_id: summarize_contrasts(
                tuple(
                    ContrastRow(
                        row.selector_id,
                        portfolio_name,
                        row.repository_id,
                        row.repository_cluster_id,
                        row.origin_id,
                        row.difference,
                    )
                    for row in selector_rows
                    if row.repository_id in selected_repositories
                ),
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )
            for selector_id, selector_rows in rows.items()
        }
        for portfolio_name, selected_repositories in (
            ("wide", set(repository_ids)),
            ("deep", set(deep_repository_ids)),
        )
    }


def _compact_summaries(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> Mapping[str, Mapping[str, Mapping[str, float | int]]]:
    return {
        portfolio_name: {
            selector_id: {
                "macro_repository_difference": _number(
                    summary.get("macro_repository_difference"),
                    "macro repository difference",
                ),
                "favorable_repository_count": _integer(
                    summary,
                    "favorable_repository_count",
                ),
            }
            for selector_id, summary in selector_summaries.items()
        }
        for portfolio_name, selector_summaries in summaries.items()
    }


def _fit_summary(
    rows: Sequence[Mapping[str, Any]],
    transition_digests: Mapping[str, str],
) -> Mapping[str, Any]:
    repository_counts = tuple(
        _integer(row, "included_repository_count") for row in rows
    )
    task_counts = tuple(_integer(row, "included_task_count") for row in rows)
    return {
        "origin_count": len(rows),
        "symmetric_fallback_origin_count": sum(
            bool(row["used_symmetric_fallback"]) for row in rows
        ),
        "included_repository_count": _numeric_summary(repository_counts),
        "included_task_count": _numeric_summary(task_counts),
        "excluded_later_task_uses": sum(
            _integer(row, "excluded_later_task_count") for row in rows
        ),
        "transition_digest": canonical_digest(
            tuple(sorted(transition_digests.items()))
        ),
    }


def _origin_schedule_identity(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            origin.repository_id,
            origin.origin_id,
            tuple(task.instance_id for task in origin.history),
            tuple(task.instance_id for task in origin.future),
        )
        for repository_id in sorted(origins_by_repository)
        for origin in origins_by_repository[repository_id]
    )


def _ordered_tasks_by_repository(
    tasks: Sequence[TaskMetadata],
) -> Mapping[str, tuple[TaskMetadata, ...]]:
    by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    seen = set()
    for task in tasks:
        if not task.instance_id or task.instance_id in seen:
            raise ValueError("Task instance IDs must be nonempty and unique")
        if not task.repository_id:
            raise ValueError("Task repository ID must be nonempty")
        parse_utc_timestamp(task.created_at)
        seen.add(task.instance_id)
        by_repository[task.repository_id].append(task)
    return {
        repository_id: tuple(
            sorted(
                repository_tasks,
                key=lambda task: (
                    parse_utc_timestamp(task.created_at),
                    task.instance_id,
                ),
            )
        )
        for repository_id, repository_tasks in sorted(by_repository.items())
    }


def _numeric_summary(values: Sequence[int | float]) -> Mapping[str, Any]:
    if not values:
        raise ValueError("numeric summary requires values")
    numeric = tuple(float(value) for value in values)
    return {
        "count": len(numeric),
        "minimum": min(numeric),
        "median": median(numeric),
        "mean": _mean(numeric),
        "maximum": max(numeric),
    }


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    item = value.get(key)
    if (
        not isinstance(item, Sequence)
        or isinstance(item, str)
        or any(not isinstance(row, Mapping) for row in item)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(item)


def _sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Sequence[Any], ...]:
    item = value.get(key)
    if (
        not isinstance(item, Sequence)
        or isinstance(item, str)
        or any(not isinstance(row, Sequence) or isinstance(row, str) for row in item)
    ):
        raise ValueError(f"{key} must be an array of arrays")
    return tuple(item)


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be an array of nonempty strings")
    result = tuple(value)
    if not result or len(result) != len(set(result)):
        raise ValueError(f"{name} must be nonempty and unique")
    return result


def _positive_integer_tuple(value: object, name: str) -> tuple[int, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0
            for item in value
        )
    ):
        raise ValueError(f"{name} must be positive integers")
    result = tuple(value)
    if not result or len(result) != len(set(result)):
        raise ValueError(f"{name} must be nonempty and unique")
    return result


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _integer(value: Mapping[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _positive_integer(value: Mapping[str, object], key: str) -> int:
    item = _integer(value, key)
    if item <= 0:
        raise ValueError(f"{key} must be positive")
    return item


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _load_bound_result(
    path: Path,
    *,
    digest_field: str,
    expected_digest: object,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("bound result must be an object")
    digest = payload.get(digest_field)
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != digest_field}
    )
    if digest != expected or digest != expected_digest:
        raise ValueError("bound result digest does not match the plan")
    return payload


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--agent-plan", type=Path, default=DEFAULT_AGENT_PLAN)
    parser.add_argument(
        "--adaptive-plan",
        type=Path,
        default=DEFAULT_ADAPTIVE_PLAN,
    )
    parser.add_argument(
        "--adaptive-results",
        type=Path,
        default=DEFAULT_ADAPTIVE_RESULTS,
    )
    parser.add_argument(
        "--extension-plan",
        type=Path,
        default=DEFAULT_EXTENSION_PLAN,
    )
    parser.add_argument(
        "--public-plan",
        type=Path,
        default=DEFAULT_PUBLIC_PLAN,
    )
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_scale_sensitivity_plan(args.plan)
    agent_plan = load_agent_invariant_plan(args.agent_plan)
    adaptive_plan = load_adaptive_difficulty_plan(args.adaptive_plan)
    _load_bound_result(
        args.adaptive_results,
        digest_field="adaptive_difficulty_results_digest",
        expected_digest=_mapping(plan, "source").get(
            "adaptive_difficulty_results_digest"
        ),
    )
    extension_plan = load_agent_panel_extension_plan(args.extension_plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    if _file_sha256(args.dataset) != _required_string(
        _mapping(plan, "source"),
        "dataset_sha256",
    ):
        raise RuntimeError("dataset digest does not match scale-sensitivity plan")
    tasks = load_dataset_tasks(args.dataset)
    task_ids = tuple(task.instance_id for task in tasks)
    original_outcomes, original_diagnostics = load_public_outcomes(
        args.result_dir,
        public_plan,
        task_ids,
    )
    extension_outcomes, extension_diagnostics = load_allocated_outcomes(
        args.result_dir,
        extension_plan,
        task_ids,
        allocation_key="development_allocation",
    )
    if args.output.exists():
        raise FileExistsError(
            f"refusing to overwrite scale-sensitivity replay: {args.output}"
        )
    result = run_scale_sensitivity(
        tasks,
        {**original_outcomes, **extension_outcomes},
        {**original_diagnostics, **extension_diagnostics},
        plan,
        agent_plan,
        adaptive_plan,
        extension_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "scale_sensitivity_results_digest": result[
                    "scale_sensitivity_results_digest"
                ],
                "decision": result["decision"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
