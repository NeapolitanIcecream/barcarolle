#!/usr/bin/env python3
"""Evaluate a cutoff-aware, Agent-invariant difficulty-state Selector."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
from itertools import product
import json
from math import floor, fsum, isfinite, sqrt
from pathlib import Path
import random
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
)
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.development import (  # noqa: E402
    select_outcome_match,
)
from examples.multi_repository_study.panel_extension import (  # noqa: E402
    load_agent_panel_extension_plan,
    load_allocated_outcomes,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
    future_pass_rate_mae,
    load_dataset_tasks,
    load_portfolio,
    load_public_outcomes,
    load_public_panel_plan,
    random_calibration,
)
from examples.multi_repository_study.theory_audit import (  # noqa: E402
    permute_joint_outcomes,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "agent-invariant-plan.json"
DEFAULT_EXECUTION_AMENDMENT = HERE / "agent-invariant-execution-amendment.json"
DEFAULT_EXTENSION_PLAN = HERE / "agent-panel-extension-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "agent-invariant-results.json"

SELECTOR_IDS = (
    "history_match",
    "difficulty_persistence_match",
    "difficulty_markov_match",
)
DIFFICULTY_SELECTOR_IDS = (
    "difficulty_persistence_match",
    "difficulty_markov_match",
)


def load_agent_invariant_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Agent-invariant plan must be an object")
    if payload.get("schema_version") != "barcarolle_agent_invariant_selector_plan_v1":
        raise ValueError("Agent-invariant plan schema is unsupported")
    digest = payload.get("agent_invariant_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "agent_invariant_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("Agent-invariant plan digest does not match")
    return payload


def load_agent_invariant_execution_amendment(
    path: Path = DEFAULT_EXECUTION_AMENDMENT,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Agent-invariant execution amendment must be an object")
    if (
        payload.get("schema_version")
        != "barcarolle_agent_invariant_execution_amendment_v1"
    ):
        raise ValueError("Agent-invariant execution amendment is unsupported")
    digest = payload.get("agent_invariant_execution_amendment_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "agent_invariant_execution_amendment_digest"
        }
    )
    if digest != expected:
        raise ValueError("Agent-invariant execution amendment digest does not match")
    return payload


def task_difficulty_state(
    task_id: str,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    state_count: int,
) -> int:
    if (
        not task_id
        or isinstance(state_count, bool)
        or not isinstance(state_count, int)
        or state_count < 2
        or not outcomes_by_agent
    ):
        raise ValueError("difficulty state input is invalid")
    values = []
    for agent_id, outcomes in sorted(outcomes_by_agent.items()):
        value = outcomes.get(task_id)
        if value not in (0, 1):
            raise ValueError(f"Agent outcome is not binary: {agent_id}/{task_id}")
        values.append(value)
    solved_fraction = fsum(values) / len(values)
    return min(state_count - 1, floor(state_count * solved_fraction))


def fit_cutoff_repository_equal_markov(
    training_repository_ids: Sequence[str],
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    cutoff: str,
    state_count: int,
    cell_prior_mass: float,
) -> tuple[tuple[tuple[float, ...], ...], Mapping[str, Any]]:
    repository_ids = _string_tuple(
        training_repository_ids,
        "training repository IDs",
    )
    cutoff_time = parse_utc_timestamp(cutoff)
    matrices = []
    included_repositories = []
    included_task_count = 0
    excluded_later_task_count = 0
    for repository_id in repository_ids:
        repository_tasks = tasks_by_repository.get(repository_id)
        if repository_tasks is None:
            raise ValueError(f"training repository is missing: {repository_id}")
        available = tuple(
            task
            for task in repository_tasks
            if parse_utc_timestamp(task.created_at) <= cutoff_time
        )
        excluded_later_task_count += len(repository_tasks) - len(available)
        if len(available) < 2:
            continue
        states = tuple(
            task_difficulty_state(
                task.instance_id,
                outcomes_by_agent,
                state_count=state_count,
            )
            for task in available
        )
        matrices.append(
            _transition_matrix(
                states,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
            )
        )
        included_repositories.append(repository_id)
        included_task_count += len(available)
    if matrices:
        transition = tuple(
            tuple(
                _mean(tuple(matrix[row][column] for matrix in matrices))
                for column in range(state_count)
            )
            for row in range(state_count)
        )
    else:
        transition = tuple(
            tuple(1.0 / state_count for _ in range(state_count))
            for _ in range(state_count)
        )
    return transition, {
        "included_repository_count": len(included_repositories),
        "included_repository_ids": tuple(included_repositories),
        "included_task_count": included_task_count,
        "excluded_later_task_count": excluded_later_task_count,
        "used_symmetric_fallback": not matrices,
    }


def forecast_difficulty_markov(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    global_transition: Sequence[Sequence[float]],
    *,
    state_count: int,
    horizon: int,
    local_prior_strength: float,
) -> tuple[float, ...]:
    if (
        not history
        or isinstance(horizon, bool)
        or not isinstance(horizon, int)
        or horizon <= 0
        or not isfinite(local_prior_strength)
        or local_prior_strength <= 0.0
    ):
        raise ValueError("difficulty Markov forecast input is invalid")
    global_matrix = _validated_transition_matrix(global_transition, state_count)
    history_states = tuple(
        task_difficulty_state(
            task.instance_id,
            outcomes_by_agent,
            state_count=state_count,
        )
        for task in history
    )
    local_counts = [[0] * state_count for _ in range(state_count)]
    for left, right in zip(history_states, history_states[1:]):
        local_counts[left][right] += 1
    transition = tuple(
        tuple(
            (
                local_counts[row][column]
                + local_prior_strength * global_matrix[row][column]
            )
            / (sum(local_counts[row]) + local_prior_strength)
            for column in range(state_count)
        )
        for row in range(state_count)
    )
    distribution = [0.0] * state_count
    distribution[history_states[-1]] = 1.0
    steps = []
    for _ in range(horizon):
        distribution = [
            fsum(
                distribution[source] * transition[source][target]
                for source in range(state_count)
            )
            for target in range(state_count)
        ]
        steps.append(tuple(distribution))
    return tuple(
        _mean(tuple(step[state] for step in steps)) for state in range(state_count)
    )


def forecast_difficulty_persistence(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    state_count: int,
    block_size: int,
) -> tuple[float, ...]:
    if not history or block_size <= 0 or len(history) < block_size:
        raise ValueError("difficulty persistence input is invalid")
    states = tuple(
        task_difficulty_state(
            task.instance_id,
            outcomes_by_agent,
            state_count=state_count,
        )
        for task in history[-block_size:]
    )
    return tuple(states.count(state) / len(states) for state in range(state_count))


def select_state_histogram_match(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    forecast: Sequence[float],
    *,
    state_count: int,
    budget: int,
) -> tuple[str, ...]:
    if (
        not history
        or budget <= 0
        or budget > len(history)
        or len(forecast) != state_count
    ):
        raise ValueError("state histogram Selection input is invalid")
    normalized_forecast = _probability_vector(forecast, state_count)
    grouped: list[list[TaskMetadata]] = [[] for _ in range(state_count)]
    for task in history:
        grouped[
            task_difficulty_state(
                task.instance_id,
                outcomes_by_agent,
                state_count=state_count,
            )
        ].append(task)
    ranges = tuple(
        range(min(len(tasks), budget) + 1) for tasks in grouped
    )
    feasible = (
        counts for counts in product(*ranges) if sum(counts) == budget
    )
    try:
        best_counts = min(
            feasible,
            key=lambda counts: (
                fsum(
                    abs(counts[state] / budget - normalized_forecast[state])
                    for state in range(state_count)
                ),
                counts,
            ),
        )
    except ValueError as error:
        raise ValueError("no feasible state allocation") from error
    selected = {
        task.instance_id
        for state, count in enumerate(best_counts)
        for task in (grouped[state][-count:] if count else ())
    }
    if len(selected) != budget:
        raise AssertionError("state allocation did not fill the budget")
    return tuple(task.instance_id for task in history if task.instance_id in selected)


def materialize_selections(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    *,
    history_match_outcomes: Mapping[str, Mapping[str, int]] | None = None,
    selector_ids: Sequence[str] = SELECTOR_IDS,
) -> tuple[
    Mapping[str, tuple[RepositoryOrigin, ...]],
    Mapping[str, Mapping[str, tuple[str, ...]]],
    Mapping[str, Mapping[str, tuple[float, ...]]],
    Mapping[str, Any],
]:
    selected_selector_ids = _string_tuple(selector_ids, "Selector IDs")
    if not set(selected_selector_ids) <= set(SELECTOR_IDS):
        raise ValueError("unsupported materialized Selector")
    history_outcomes = (
        outcomes_by_agent
        if history_match_outcomes is None
        else history_match_outcomes
    )
    if "history_match" in selected_selector_ids and not history_outcomes:
        raise ValueError("history_match requires reference Agent outcomes")
    rolling = _mapping(plan, "rolling_origin")
    minimum_history = _positive_integer(rolling, "minimum_initial_history_tasks")
    block_size = _positive_integer(rolling, "future_block_tasks")
    budget = _positive_integer(rolling, "selection_budget_tasks")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=minimum_history,
        future_block_tasks=block_size,
    )
    public_portfolio = _mapping(public_plan, "portfolio")
    repository_ids = _string_tuple(
        public_portfolio.get("wide_repository_ids"),
        "wide repository IDs",
    )
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    for repository_tasks in tasks_by_repository.values():
        repository_tasks.sort(
            key=lambda task: (
                parse_utc_timestamp(task.created_at),
                task.instance_id,
            )
        )

    representation = _mapping(plan, "difficulty_representation")
    state_count = _positive_integer(representation, "state_count")
    algorithms = {
        _required_string(row, "selector_id"): row
        for row in _mapping_sequence(plan, "fixed_algorithms")
    }
    markov = algorithms["difficulty_markov_match"]
    cell_prior_mass = _number(
        markov.get("training_symmetric_dirichlet_cell_mass"),
        "Markov cell prior mass",
    )
    local_prior_strength = _number(
        markov.get("target_local_transition_prior_total_mass_per_row"),
        "local Markov prior strength",
    )

    memberships: dict[str, dict[str, tuple[str, ...]]] = {
        selector_id: {} for selector_id in selected_selector_ids
    }
    forecasts: dict[str, dict[str, tuple[float, ...]]] = {
        selector_id: {}
        for selector_id in selected_selector_ids
        if selector_id in DIFFICULTY_SELECTOR_IDS
    }
    transition_digests = {}
    fit_rows = []
    for outer_repository_id in repository_ids:
        training_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id != outer_repository_id
        )
        for origin in origins_by_repository[outer_repository_id]:
            transition, fit_diagnostic = fit_cutoff_repository_equal_markov(
                training_repository_ids,
                tasks_by_repository,
                outcomes_by_agent,
                cutoff=origin.history[-1].created_at,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
            )
            transition_digests[origin.origin_id] = canonical_digest(transition)
            fit_rows.append(fit_diagnostic)
            difficulty_forecasts = {}
            if "difficulty_persistence_match" in selected_selector_ids:
                difficulty_forecasts["difficulty_persistence_match"] = (
                    forecast_difficulty_persistence(
                        origin.history,
                        outcomes_by_agent,
                        state_count=state_count,
                        block_size=block_size,
                    )
                )
            if "difficulty_markov_match" in selected_selector_ids:
                difficulty_forecasts["difficulty_markov_match"] = (
                    forecast_difficulty_markov(
                        origin.history,
                        outcomes_by_agent,
                        transition,
                        state_count=state_count,
                        horizon=block_size,
                        local_prior_strength=local_prior_strength,
                    )
                )
            for selector_id, forecast in difficulty_forecasts.items():
                forecasts[selector_id][origin.origin_id] = forecast
                memberships[selector_id][origin.origin_id] = (
                    select_state_histogram_match(
                        origin.history,
                        outcomes_by_agent,
                        forecast,
                        state_count=state_count,
                        budget=budget,
                    )
                )
            if "history_match" in selected_selector_ids:
                history_ids = tuple(task.instance_id for task in origin.history)
                history_rates = _agent_rates(history_ids, history_outcomes)
                memberships["history_match"][
                    origin.origin_id
                ] = select_outcome_match(
                    origin.history,
                    history_outcomes,
                    history_rates,
                    budget=budget,
                )
    fit_repository_counts = tuple(
        int(row["included_repository_count"]) for row in fit_rows
    )
    fit_task_counts = tuple(int(row["included_task_count"]) for row in fit_rows)
    fit_diagnostics = {
        "origin_count": len(fit_rows),
        "symmetric_fallback_origin_count": sum(
            bool(row["used_symmetric_fallback"]) for row in fit_rows
        ),
        "included_repository_count": {
            "minimum": min(fit_repository_counts),
            "mean": _mean(fit_repository_counts),
            "maximum": max(fit_repository_counts),
        },
        "included_task_count": {
            "minimum": min(fit_task_counts),
            "mean": _mean(fit_task_counts),
            "maximum": max(fit_task_counts),
        },
        "excluded_later_task_uses": sum(
            int(row["excluded_later_task_count"]) for row in fit_rows
        ),
        "transition_digest": canonical_digest(
            tuple(sorted(transition_digests.items()))
        ),
    }
    return (
        origins_by_repository,
        {
            selector_id: dict(sorted(rows.items()))
            for selector_id, rows in memberships.items()
        },
        {
            selector_id: dict(sorted(rows.items()))
            for selector_id, rows in forecasts.items()
        },
        fit_diagnostics,
    )


def run_agent_invariant_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    execution_amendment: Mapping[str, object],
    extension_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    source = _mapping(plan, "source")
    if source.get("agent_panel_extension_plan_digest") != extension_plan.get(
        "agent_panel_extension_plan_digest"
    ):
        raise ValueError("Agent-invariant plan does not bind the extension plan")
    if source.get("public_panel_plan_digest") != public_plan.get(
        "public_panel_plan_digest"
    ):
        raise ValueError("Agent-invariant plan does not bind the public plan")
    if execution_amendment.get("agent_invariant_plan_digest") != plan.get(
        "agent_invariant_plan_digest"
    ):
        raise ValueError("execution amendment does not bind the plan")
    task_ids = tuple(task.instance_id for task in tasks)
    if (
        not task_ids
        or len(task_ids) != len(set(task_ids))
        or any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values())
    ):
        raise ValueError("development Agents must cover the Task denominator")
    expected_agent_count = _positive_integer(
        source,
        "opened_development_agent_count_after_extension",
    )
    if len(outcomes_by_agent) != expected_agent_count:
        raise ValueError("development Agent count does not match the plan")
    history_match_agent_ids = tuple(
        _required_string(row, "agent_id")
        for row in _mapping_sequence(
            extension_plan,
            "existing_opened_development_panel",
        )
    )
    if not set(history_match_agent_ids) <= set(outcomes_by_agent):
        raise ValueError("history_match reference Agents are unavailable")
    history_match_outcomes = {
        agent_id: outcomes_by_agent[agent_id]
        for agent_id in history_match_agent_ids
    }

    public_portfolio = _mapping(public_plan, "portfolio")
    repository_ids = _string_tuple(
        public_portfolio.get("wide_repository_ids"),
        "wide repository IDs",
    )
    deep_repository_ids = _string_tuple(
        public_portfolio.get("deep_repository_ids"),
        "deep repository IDs",
    )
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    diagnostics = _mapping(plan, "diagnostics")
    aggregation = _mapping(diagnostics, "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )
    origins_by_repository, memberships, forecasts, fit_diagnostics = (
        materialize_selections(
            tasks,
            outcomes_by_agent,
            plan,
            public_plan,
            history_match_outcomes=history_match_outcomes,
        )
    )
    rows = evaluate_memberships(
        origins_by_repository,
        memberships,
        outcomes_by_agent,
        repository_ids,
        cluster_by_repository,
    )
    summaries = _summaries(
        rows,
        repository_ids,
        deep_repository_ids,
        bootstrap_seed,
        bootstrap_resamples,
    )
    per_agent_summaries = {
        agent_id: _summaries(
            evaluate_memberships(
                origins_by_repository,
                memberships,
                {agent_id: outcomes},
                repository_ids,
                cluster_by_repository,
            ),
            repository_ids,
            deep_repository_ids,
            bootstrap_seed,
            bootstrap_resamples,
        )
        for agent_id, outcomes in sorted(outcomes_by_agent.items())
    }
    forecast_diagnostics = evaluate_difficulty_forecasts(
        origins_by_repository,
        memberships,
        forecasts,
        outcomes_by_agent,
        repository_ids,
        deep_repository_ids,
        state_count=_positive_integer(
            _mapping(plan, "difficulty_representation"),
            "state_count",
        ),
    )

    random_config = _mapping(diagnostics, "random_calibration")
    random_reports = {
        portfolio_name: random_calibration(
            selected_repositories,
            origins_by_repository,
            outcomes_by_agent,
            budget=_positive_integer(
                _mapping(plan, "selection_rule"),
                "budget",
            ),
            draws=_positive_integer(random_config, "draws"),
            seed=_integer(random_config, "seed"),
            observed_summaries=summaries[portfolio_name],
        )
        for portfolio_name, selected_repositories in (
            ("wide", repository_ids),
            ("deep", deep_repository_ids),
        )
    }
    leave_one_agent = run_leave_one_agent_out(
        tasks,
        outcomes_by_agent,
        plan,
        public_plan,
        portfolio,
        repository_ids,
        deep_repository_ids,
        cluster_by_repository,
        bootstrap_seed,
        bootstrap_resamples,
        history_match_agent_ids,
    )
    null_config = _mapping(diagnostics, "temporal_null")
    temporal_null = run_temporal_null(
        tasks,
        outcomes_by_agent,
        plan,
        public_plan,
        origins_by_repository,
        repository_ids,
        cluster_by_repository,
        observed=float(
            summaries["wide"]["difficulty_markov_match"][
                "macro_repository_difference"
            ]
        ),
        permutations=_positive_integer(null_config, "permutations"),
        seed=_integer(null_config, "seed"),
    )
    decision = holdout_decision(
        summaries,
        random_reports,
        temporal_null,
        leave_one_agent,
        plan,
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_agent_invariant_selector_results_v1",
        "study_id": plan.get("study_id"),
        "epistemic_status": "opened_development_panel_with_sealed_agent_holdout",
        "agent_invariant_plan_digest": plan.get("agent_invariant_plan_digest"),
        "agent_invariant_execution_amendment_digest": execution_amendment.get(
            "agent_invariant_execution_amendment_digest"
        ),
        "agent_panel_extension_plan_digest": extension_plan.get(
            "agent_panel_extension_plan_digest"
        ),
        "public_panel_plan_digest": public_plan.get("public_panel_plan_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        },
        "agent_outcome_diagnostics": dict(sorted(outcome_diagnostics.items())),
        "fit_diagnostics": fit_diagnostics,
        "selection_membership_digests": {
            selector_id: canonical_digest(tuple(sorted(rows.items())))
            for selector_id, rows in memberships.items()
        },
        "summaries": summaries,
        "per_agent_summaries": per_agent_summaries,
        "difficulty_forecast_diagnostics": forecast_diagnostics,
        "random_calibration": random_reports,
        "leave_one_agent_out": leave_one_agent,
        "temporal_null": temporal_null,
        "decision": decision,
        "claim_boundary": (
            "The eleven-Agent outcomes are opened development evidence. "
            "Calendar cutoffs and Agent cross-validation remove two known "
            "leakage routes, but only the still-sealed six-Agent panel can "
            "provide a one-shot unseen-Agent check. history_match retains its "
            "previously frozen three-Agent reference panel."
        ),
    }
    result["agent_invariant_results_digest"] = canonical_digest(result)
    return result


def evaluate_memberships(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    memberships: Mapping[str, Mapping[str, Sequence[str]]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    repository_ids: Sequence[str],
    cluster_by_repository: Mapping[str, str],
) -> Mapping[str, tuple[ContrastRow, ...]]:
    rows: dict[str, list[ContrastRow]] = {
        selector_id: [] for selector_id in memberships
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline_loss = future_pass_rate_mae(
                history_ids,
                future_ids,
                outcomes_by_agent,
            )
            for selector_id, selector_memberships in memberships.items():
                selected_ids = selector_memberships[origin.origin_id]
                rows[selector_id].append(
                    ContrastRow(
                        selector_id,
                        "wide",
                        repository_id,
                        cluster_by_repository[repository_id],
                        origin.origin_id,
                        future_pass_rate_mae(
                            selected_ids,
                            future_ids,
                            outcomes_by_agent,
                        )
                        - baseline_loss,
                    )
                )
    return {
        selector_id: tuple(selector_rows)
        for selector_id, selector_rows in rows.items()
    }


def evaluate_difficulty_forecasts(
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    memberships: Mapping[str, Mapping[str, Sequence[str]]],
    forecasts: Mapping[str, Mapping[str, Sequence[float]]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    *,
    state_count: int,
) -> Mapping[str, Any]:
    values: dict[str, dict[str, dict[str, list[float]]]] = {
        selector_id: {
            "forecast_vs_future": defaultdict(list),
            "selected_vs_forecast": defaultdict(list),
        }
        for selector_id in DIFFICULTY_SELECTOR_IDS
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            future_distribution = _state_distribution(
                tuple(task.instance_id for task in origin.future),
                outcomes_by_agent,
                state_count,
            )
            for selector_id in DIFFICULTY_SELECTOR_IDS:
                forecast = forecasts[selector_id][origin.origin_id]
                selected_distribution = _state_distribution(
                    memberships[selector_id][origin.origin_id],
                    outcomes_by_agent,
                    state_count,
                )
                values[selector_id]["forecast_vs_future"][
                    repository_id
                ].append(_total_variation(forecast, future_distribution))
                values[selector_id]["selected_vs_forecast"][
                    repository_id
                ].append(_total_variation(selected_distribution, forecast))
    return {
        selector_id: {
            metric: _repository_value_summary(
                by_repository,
                repository_ids,
                deep_repository_ids,
            )
            for metric, by_repository in metrics.items()
        }
        for selector_id, metrics in values.items()
    }


def run_leave_one_agent_out(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    cluster_by_repository: Mapping[str, str],
    bootstrap_seed: int,
    bootstrap_resamples: int,
    history_match_agent_ids: Sequence[str],
) -> Mapping[str, Any]:
    by_agent = {}
    membership_digests = {}
    for held_out_agent_id in sorted(outcomes_by_agent):
        reference_outcomes = {
            agent_id: outcomes
            for agent_id, outcomes in outcomes_by_agent.items()
            if agent_id != held_out_agent_id
        }
        history_match_outcomes = {
            agent_id: outcomes_by_agent[agent_id]
            for agent_id in history_match_agent_ids
            if agent_id != held_out_agent_id
        }
        origins, memberships, _, _ = materialize_selections(
            tasks,
            reference_outcomes,
            plan,
            public_plan,
            history_match_outcomes=history_match_outcomes,
        )
        rows = evaluate_memberships(
            origins,
            memberships,
            {held_out_agent_id: outcomes_by_agent[held_out_agent_id]},
            repository_ids,
            cluster_by_repository,
        )
        by_agent[held_out_agent_id] = _summaries(
            rows,
            repository_ids,
            deep_repository_ids,
            bootstrap_seed,
            bootstrap_resamples,
        )
        membership_digests[held_out_agent_id] = {
            selector_id: canonical_digest(tuple(sorted(items.items())))
            for selector_id, items in memberships.items()
        }
    by_selector = {}
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
        by_selector[selector_id] = {
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
        "aggregate_by_selector": by_selector,
        "selection_membership_digests": membership_digests,
    }


def run_temporal_null(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
    cluster_by_repository: Mapping[str, str],
    *,
    observed: float,
    permutations: int,
    seed: int,
) -> Mapping[str, Any]:
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    for repository_tasks in tasks_by_repository.values():
        repository_tasks.sort(
            key=lambda task: (
                parse_utc_timestamp(task.created_at),
                task.instance_id,
            )
        )
    generator = random.Random(seed)
    null_values = []
    for _ in range(permutations):
        permuted = permute_joint_outcomes(
            tasks_by_repository,
            outcomes_by_agent,
            generator,
        )
        _, memberships, _, _ = materialize_selections(
            tasks,
            permuted,
            plan,
            public_plan,
            selector_ids=("difficulty_markov_match",),
        )
        rows = evaluate_memberships(
            origins_by_repository,
            {"difficulty_markov_match": memberships["difficulty_markov_match"]},
            permuted,
            repository_ids,
            cluster_by_repository,
        )
        null_values.append(
            _macro_repository_difference(
                rows["difficulty_markov_match"],
                repository_ids,
            )
        )
    null_values.sort()
    rate = sum(value <= observed for value in null_values) / permutations
    return {
        "permutations": permutations,
        "seed": seed,
        "observed_wide_macro_repository_difference": observed,
        "as_good_or_better_rate": rate,
        "monte_carlo_standard_error_at_observed_rate": sqrt(
            rate * (1.0 - rate) / permutations
        ),
        "null_mean": _mean(null_values),
        "null_population_standard_deviation": _population_standard_deviation(
            null_values
        ),
        "quantiles": {
            "0.025": _empirical_quantile(null_values, 0.025),
            "0.5": _empirical_quantile(null_values, 0.5),
            "0.975": _empirical_quantile(null_values, 0.975),
        },
        "minimum": null_values[0],
        "maximum": null_values[-1],
        "null_statistics_digest": canonical_digest(tuple(null_values)),
    }


def holdout_decision(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    random_reports: Mapping[str, Mapping[str, Any]],
    temporal_null: Mapping[str, object],
    leave_one_agent: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    wide = summaries["wide"]["difficulty_markov_match"]
    deep = summaries["deep"]["difficulty_markov_match"]
    history = summaries["wide"]["history_match"]
    persistence = summaries["wide"]["difficulty_persistence_match"]
    random_position = _number(
        _mapping(
            _mapping(random_reports["wide"], "candidate_positions"),
            "difficulty_markov_match",
        ).get("candidate_better_than_random_midrank"),
        "random percentile",
    )
    agent_transfer = _mapping(
        _mapping(leave_one_agent, "aggregate_by_selector"),
        "difficulty_markov_match",
    )
    requirements = {
        "wide_at_most_minus_0_01": float(
            wide["macro_repository_difference"]
        )
        <= -0.01,
        "at_least_five_favorable_repositories": int(
            wide["favorable_repository_count"]
        )
        >= 5,
        "every_leave_one_repository_out_negative": not bool(
            wide["leave_one_cluster_out_has_nonnegative_difference"]
        ),
        "deep_direction_negative": float(
            deep["macro_repository_difference"]
        )
        < 0.0,
        "better_than_at_least_75_percent_random": random_position >= 0.75,
        "better_than_history_match": float(
            wide["macro_repository_difference"]
        )
        < float(history["macro_repository_difference"]),
        "better_than_persistence_ablation": float(
            wide["macro_repository_difference"]
        )
        < float(persistence["macro_repository_difference"]),
        "temporal_null_rate_below_0_10": _number(
            temporal_null.get("as_good_or_better_rate"),
            "temporal null rate",
        )
        < 0.1,
        "leave_one_agent_macro_negative": _number(
            agent_transfer.get("wide_macro_over_held_out_agents"),
            "leave-one-Agent macro",
        )
        < 0.0,
        "at_least_eight_favorable_held_out_agents": _integer(
            agent_transfer,
            "wide_favorable_held_out_agent_count",
        )
        >= 8,
    }
    passed = all(requirements.values())
    return {
        "status": (
            "open_sealed_agent_holdout_for_one_frozen_candidate"
            if passed
            else "retire_agent_invariant_markov_on_development_panel"
        ),
        "requirements": requirements,
        "all_requirements_met": passed,
        "sealed_holdout_open_allowed": passed,
        "production_promotion_allowed": False,
        "plan_gate_digest": canonical_digest(_mapping(plan, "holdout_open_gate")),
    }


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


def _repository_value_summary(
    values: Mapping[str, Sequence[float]],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    return {
        portfolio_name: {
            "macro_repository_mean": _mean(
                tuple(_mean(tuple(values[repository_id])) for repository_id in ids)
            ),
            "repository_means": {
                repository_id: _mean(tuple(values[repository_id]))
                for repository_id in ids
            },
        }
        for portfolio_name, ids in (
            ("wide", repository_ids),
            ("deep", deep_repository_ids),
        )
    }


def _state_distribution(
    task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    state_count: int,
) -> tuple[float, ...]:
    states = tuple(
        task_difficulty_state(
            task_id,
            outcomes_by_agent,
            state_count=state_count,
        )
        for task_id in task_ids
    )
    return tuple(states.count(state) / len(states) for state in range(state_count))


def _agent_rates(
    task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> Mapping[str, float]:
    return {
        agent_id: _mean(tuple(outcomes[task_id] for task_id in task_ids))
        for agent_id, outcomes in sorted(outcomes_by_agent.items())
    }


def _transition_matrix(
    states: Sequence[int],
    *,
    state_count: int,
    cell_prior_mass: float,
) -> tuple[tuple[float, ...], ...]:
    if (
        len(states) < 2
        or not isfinite(cell_prior_mass)
        or cell_prior_mass <= 0.0
        or any(state < 0 or state >= state_count for state in states)
    ):
        raise ValueError("transition input is invalid")
    counts = [[0] * state_count for _ in range(state_count)]
    for left, right in zip(states, states[1:]):
        counts[left][right] += 1
    return tuple(
        tuple(
            (counts[row][column] + cell_prior_mass)
            / (sum(counts[row]) + cell_prior_mass * state_count)
            for column in range(state_count)
        )
        for row in range(state_count)
    )


def _validated_transition_matrix(
    transition: Sequence[Sequence[float]],
    state_count: int,
) -> tuple[tuple[float, ...], ...]:
    if len(transition) != state_count:
        raise ValueError("transition row count is invalid")
    rows = []
    for row in transition:
        if len(row) != state_count:
            raise ValueError("transition column count is invalid")
        values = tuple(float(value) for value in row)
        if any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError("transition values are invalid")
        if abs(fsum(values) - 1.0) > 1e-9:
            raise ValueError("transition row does not sum to one")
        rows.append(values)
    return tuple(rows)


def _probability_vector(
    values: Sequence[float],
    state_count: int,
) -> tuple[float, ...]:
    if len(values) != state_count:
        raise ValueError("probability vector dimensions are invalid")
    result = tuple(float(value) for value in values)
    if any(not isfinite(value) or value < 0.0 for value in result):
        raise ValueError("probability vector values are invalid")
    if abs(fsum(result) - 1.0) > 1e-9:
        raise ValueError("probability vector does not sum to one")
    return result


def _total_variation(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("distribution dimensions differ")
    return 0.5 * fsum(abs(a - b) for a, b in zip(left, right, strict=True))


def _macro_repository_difference(
    rows: Sequence[ContrastRow],
    repository_ids: Sequence[str],
) -> float:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        values[row.repository_id].append(row.difference)
    if set(values) != set(repository_ids):
        raise ValueError("contrast rows do not cover the repository portfolio")
    return _mean(
        tuple(_mean(tuple(values[repository_id])) for repository_id in repository_ids)
    )


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


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must contain nonempty strings")
    result = tuple(value)
    if not result or len(result) != len(set(result)):
        raise ValueError(f"{name} must be nonempty and unique")
    return result


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


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


def _mean(values: Sequence[float | int]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _population_standard_deviation(values: Sequence[float]) -> float:
    mean = _mean(values)
    return sqrt(fsum((value - mean) ** 2 for value in values) / len(values))


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 <= probability <= 1.0:
        raise ValueError("quantile input is invalid")
    return values[round(probability * (len(values) - 1))]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--execution-amendment",
        type=Path,
        default=DEFAULT_EXECUTION_AMENDMENT,
    )
    parser.add_argument("--extension-plan", type=Path, default=DEFAULT_EXTENSION_PLAN)
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_agent_invariant_plan(args.plan)
    execution_amendment = load_agent_invariant_execution_amendment(
        args.execution_amendment
    )
    extension_plan = load_agent_panel_extension_plan(args.extension_plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    public_source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(
        public_source,
        "dataset_sha256",
    ):
        raise RuntimeError("dataset digest does not match the public plan")
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
    outcomes = {**original_outcomes, **extension_outcomes}
    outcome_diagnostics = {**original_diagnostics, **extension_diagnostics}
    if args.output.exists():
        raise FileExistsError(
            f"refusing to overwrite Agent-invariant replay: {args.output}"
        )
    result = run_agent_invariant_replay(
        tasks,
        outcomes,
        outcome_diagnostics,
        plan,
        execution_amendment,
        extension_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "agent_invariant_results_digest": result[
                    "agent_invariant_results_digest"
                ],
                "decision": result["decision"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
