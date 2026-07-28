#!/usr/bin/env python3
"""Evaluate an Origin-local prequential difficulty-model choice."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite, log, sqrt
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
from examples.multi_repository_study.agent_invariant import (  # noqa: E402
    evaluate_memberships,
    fit_cutoff_repository_equal_markov,
    forecast_difficulty_markov,
    load_agent_invariant_execution_amendment,
    load_agent_invariant_plan,
    materialize_selections,
    select_state_histogram_match,
    task_difficulty_state,
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
    build_repository_origins,
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
DEFAULT_PLAN = HERE / "adaptive-difficulty-plan.json"
DEFAULT_AGENT_PLAN = HERE / "agent-invariant-plan.json"
DEFAULT_EXECUTION_AMENDMENT = HERE / "agent-invariant-execution-amendment.json"
DEFAULT_AGENT_RESULTS = HERE / "agent-invariant-results.json"
DEFAULT_EXTENSION_PLAN = HERE / "agent-panel-extension-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "adaptive-difficulty-results.json"

SELECTOR_IDS = (
    "history_match",
    "difficulty_markov_match",
    "stationary_difficulty_match",
    "adaptive_prequential_difficulty_match",
)
ADAPTIVE_SELECTOR_ID = "adaptive_prequential_difficulty_match"


def load_adaptive_difficulty_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("adaptive difficulty plan must be an object")
    if payload.get("schema_version") != "barcarolle_adaptive_difficulty_selector_plan_v1":
        raise ValueError("adaptive difficulty plan schema is unsupported")
    digest = payload.get("adaptive_difficulty_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "adaptive_difficulty_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("adaptive difficulty plan digest does not match")
    return payload


def forecast_stationary_difficulty(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    state_count: int,
    cell_prior_mass: float,
) -> tuple[float, ...]:
    if (
        not history
        or not isfinite(cell_prior_mass)
        or cell_prior_mass <= 0.0
    ):
        raise ValueError("stationary difficulty forecast input is invalid")
    counts = [0] * state_count
    for task in history:
        counts[
            task_difficulty_state(
                task.instance_id,
                outcomes_by_agent,
                state_count=state_count,
            )
        ] += 1
    denominator = len(history) + cell_prior_mass * state_count
    return tuple(
        (counts[state] + cell_prior_mass) / denominator
        for state in range(state_count)
    )


def choose_prequential_difficulty_model(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    global_transition: Sequence[Sequence[float]],
    *,
    state_count: int,
    cell_prior_mass: float,
    local_prior_strength: float,
) -> Mapping[str, float | str]:
    if len(history) < 2:
        raise ValueError("prequential model choice needs two history Tasks")
    states = tuple(
        task_difficulty_state(
            task.instance_id,
            outcomes_by_agent,
            state_count=state_count,
        )
        for task in history
    )
    transition = _transition_matrix(global_transition, state_count)
    local_counts = [[0] * state_count for _ in range(state_count)]
    stationary_counts = [0] * state_count
    stationary_counts[states[0]] = 1
    markov_loss = 0.0
    stationary_loss = 0.0
    for index in range(1, len(states)):
        previous = states[index - 1]
        observed = states[index]
        markov_probability = (
            local_counts[previous][observed]
            + local_prior_strength * transition[previous][observed]
        ) / (sum(local_counts[previous]) + local_prior_strength)
        stationary_probability = (
            stationary_counts[observed] + cell_prior_mass
        ) / (index + cell_prior_mass * state_count)
        markov_loss -= log(markov_probability)
        stationary_loss -= log(stationary_probability)
        local_counts[previous][observed] += 1
        stationary_counts[observed] += 1
    transitions = len(states) - 1
    markov_mean = markov_loss / transitions
    stationary_mean = stationary_loss / transitions
    return {
        "selected_model": (
            "markov" if markov_mean < stationary_mean else "stationary"
        ),
        "markov_mean_negative_log_likelihood": markov_mean,
        "stationary_mean_negative_log_likelihood": stationary_mean,
    }


def materialize_adaptive_selections(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    history_match_outcomes: Mapping[str, Mapping[str, int]],
    adaptive_plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    *,
    include_controls: bool,
) -> tuple[
    Mapping[str, tuple[RepositoryOrigin, ...]],
    Mapping[str, Mapping[str, tuple[str, ...]]],
    Mapping[str, Mapping[str, float | int | str]],
]:
    rolling = _mapping(agent_plan, "rolling_origin")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(rolling, "future_block_tasks"),
    )
    public_portfolio = _mapping(public_plan, "portfolio")
    repository_ids = _string_tuple(
        public_portfolio.get("wide_repository_ids"),
        "wide repository IDs",
    )
    if include_controls:
        control_origins, control_memberships, _, _ = materialize_selections(
            tasks,
            outcomes_by_agent,
            agent_plan,
            public_plan,
            history_match_outcomes=history_match_outcomes,
            selector_ids=("history_match", "difficulty_markov_match"),
        )
        if {
            repository_id: tuple(origin.origin_id for origin in origins)
            for repository_id, origins in control_origins.items()
        } != {
            repository_id: tuple(origin.origin_id for origin in origins)
            for repository_id, origins in origins_by_repository.items()
        }:
            raise AssertionError("control Origins differ from adaptive Origins")
        memberships = {
            selector_id: dict(rows)
            for selector_id, rows in control_memberships.items()
        }
    else:
        memberships = {}
    memberships["stationary_difficulty_match"] = {}
    memberships[ADAPTIVE_SELECTOR_ID] = {}

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
    representation = _mapping(agent_plan, "difficulty_representation")
    state_count = _positive_integer(representation, "state_count")
    markov = {
        _required_string(row, "selector_id"): row
        for row in _mapping_sequence(agent_plan, "fixed_algorithms")
    }["difficulty_markov_match"]
    cell_prior_mass = _number(
        markov.get("training_symmetric_dirichlet_cell_mass"),
        "Markov cell prior mass",
    )
    local_prior_strength = _number(
        markov.get("target_local_transition_prior_total_mass_per_row"),
        "local Markov prior strength",
    )
    adaptive_algorithms = {
        _required_string(row, "selector_id"): row
        for row in _mapping_sequence(adaptive_plan, "fixed_algorithms")
    }
    stationary = adaptive_algorithms["stationary_difficulty_match"]
    stationary_cell_prior_mass = _number(
        stationary.get("symmetric_dirichlet_cell_mass"),
        "stationary cell prior mass",
    )
    block_size = _positive_integer(rolling, "future_block_tasks")
    budget = _positive_integer(rolling, "selection_budget_tasks")
    choices = {}
    for target_repository_id in repository_ids:
        training_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id != target_repository_id
        )
        for origin in origins_by_repository[target_repository_id]:
            transition, _ = fit_cutoff_repository_equal_markov(
                training_repository_ids,
                tasks_by_repository,
                outcomes_by_agent,
                cutoff=origin.history[-1].created_at,
                state_count=state_count,
                cell_prior_mass=cell_prior_mass,
            )
            markov_forecast = forecast_difficulty_markov(
                origin.history,
                outcomes_by_agent,
                transition,
                state_count=state_count,
                horizon=block_size,
                local_prior_strength=local_prior_strength,
            )
            stationary_forecast = forecast_stationary_difficulty(
                origin.history,
                outcomes_by_agent,
                state_count=state_count,
                cell_prior_mass=stationary_cell_prior_mass,
            )
            choice = choose_prequential_difficulty_model(
                origin.history,
                outcomes_by_agent,
                transition,
                state_count=state_count,
                cell_prior_mass=stationary_cell_prior_mass,
                local_prior_strength=local_prior_strength,
            )
            choices[origin.origin_id] = {
                **choice,
                "repository_id": target_repository_id,
                "history_task_count": len(origin.history),
            }
            memberships["stationary_difficulty_match"][
                origin.origin_id
            ] = select_state_histogram_match(
                origin.history,
                outcomes_by_agent,
                stationary_forecast,
                state_count=state_count,
                budget=budget,
            )
            adaptive_forecast = (
                markov_forecast
                if choice["selected_model"] == "markov"
                else stationary_forecast
            )
            memberships[ADAPTIVE_SELECTOR_ID][
                origin.origin_id
            ] = select_state_histogram_match(
                origin.history,
                outcomes_by_agent,
                adaptive_forecast,
                state_count=state_count,
                budget=budget,
            )
    return (
        origins_by_repository,
        {
            selector_id: dict(sorted(rows.items()))
            for selector_id, rows in memberships.items()
        },
        dict(sorted(choices.items())),
    )


def run_adaptive_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int]],
    adaptive_plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    execution_amendment: Mapping[str, object],
    agent_results: Mapping[str, object],
    extension_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    source = _mapping(adaptive_plan, "source")
    expected_bindings = {
        "agent_panel_extension_plan_digest": extension_plan.get(
            "agent_panel_extension_plan_digest"
        ),
        "agent_invariant_plan_digest": agent_plan.get(
            "agent_invariant_plan_digest"
        ),
        "agent_invariant_execution_amendment_digest": execution_amendment.get(
            "agent_invariant_execution_amendment_digest"
        ),
        "agent_invariant_results_digest": agent_results.get(
            "agent_invariant_results_digest"
        ),
    }
    if any(source.get(key) != value for key, value in expected_bindings.items()):
        raise ValueError("adaptive plan does not bind its source evidence")
    task_ids = tuple(task.instance_id for task in tasks)
    if any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values()):
        raise ValueError("adaptive development Agents must cover the denominator")
    if len(outcomes_by_agent) != _positive_integer(
        source,
        "development_agent_count",
    ):
        raise ValueError("adaptive development Agent count does not match")
    history_match_agent_ids = tuple(
        _required_string(row, "agent_id")
        for row in _mapping_sequence(
            extension_plan,
            "existing_opened_development_panel",
        )
    )
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
    aggregation = _mapping(
        _mapping(adaptive_plan, "diagnostics"),
        "aggregation",
    )
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )
    origins, memberships, choices = materialize_adaptive_selections(
        tasks,
        outcomes_by_agent,
        history_match_outcomes,
        adaptive_plan,
        agent_plan,
        public_plan,
        include_controls=True,
    )
    membership_digests = {
        selector_id: canonical_digest(tuple(sorted(rows.items())))
        for selector_id, rows in memberships.items()
    }
    prior_membership_digests = _mapping(
        agent_results,
        "selection_membership_digests",
    )
    for selector_id in ("history_match", "difficulty_markov_match"):
        if membership_digests[selector_id] != prior_membership_digests.get(
            selector_id
        ):
            raise ValueError(f"adaptive control changed: {selector_id}")
    rows = evaluate_memberships(
        origins,
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
    prior_markov = _mapping(_mapping(agent_results, "summaries"), "wide")
    if _number(
        summaries["wide"]["difficulty_markov_match"].get(
            "macro_repository_difference"
        ),
        "replayed fixed Markov difference",
    ) != _number(
        _mapping(prior_markov, "difficulty_markov_match").get(
            "macro_repository_difference"
        ),
        "committed fixed Markov difference",
    ):
        raise ValueError("fixed Markov summary changed")
    random_config = _mapping(
        _mapping(adaptive_plan, "diagnostics"),
        "random_calibration",
    )
    random_reports = {
        portfolio_name: random_calibration(
            selected_repositories,
            origins,
            outcomes_by_agent,
            budget=_positive_integer(
                _mapping(agent_plan, "selection_rule"),
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
        history_match_agent_ids,
        adaptive_plan,
        agent_plan,
        public_plan,
        portfolio,
        repository_ids,
        deep_repository_ids,
        cluster_by_repository,
        bootstrap_seed,
        bootstrap_resamples,
    )
    null_config = _mapping(
        _mapping(adaptive_plan, "diagnostics"),
        "temporal_null",
    )
    temporal_null = run_temporal_null(
        tasks,
        outcomes_by_agent,
        adaptive_plan,
        agent_plan,
        public_plan,
        origins,
        repository_ids,
        cluster_by_repository,
        observed=float(
            summaries["wide"][ADAPTIVE_SELECTOR_ID][
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
        adaptive_plan,
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_adaptive_difficulty_selector_results_v1",
        "study_id": adaptive_plan.get("study_id"),
        "epistemic_status": "opened_development_panel_with_sealed_agent_holdout",
        "adaptive_difficulty_plan_digest": adaptive_plan.get(
            "adaptive_difficulty_plan_digest"
        ),
        **expected_bindings,
        "public_panel_plan_digest": public_plan.get("public_panel_plan_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins[repository_id])
            for repository_id in repository_ids
        },
        "agent_outcome_diagnostics": dict(sorted(outcome_diagnostics.items())),
        "selection_membership_digests": membership_digests,
        "model_choice_diagnostics": _choice_diagnostics(choices),
        "summaries": summaries,
        "random_calibration": random_reports,
        "leave_one_agent_out": leave_one_agent,
        "temporal_null": temporal_null,
        "decision": decision,
        "claim_boundary": (
            "This final current-pool candidate was designed after opening the "
            "eleven-Agent development results. Only the preserved six-Agent "
            "panel could test unseen-Agent transfer, and it remains sealed "
            "unless every frozen gate passes."
        ),
    }
    result["adaptive_difficulty_results_digest"] = canonical_digest(result)
    return result


def run_leave_one_agent_out(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    history_match_agent_ids: Sequence[str],
    adaptive_plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    cluster_by_repository: Mapping[str, str],
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Any]:
    del portfolio
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
        origins, memberships, _ = materialize_adaptive_selections(
            tasks,
            reference_outcomes,
            history_match_outcomes,
            adaptive_plan,
            agent_plan,
            public_plan,
            include_controls=True,
        )
        rows = evaluate_memberships(
            origins,
            memberships,
            {held_out_agent_id: outcomes_by_agent[held_out_agent_id]},
            repository_ids,
            cluster_by_repository,
        )
        by_agent[held_out_agent_id] = _compact_agent_summaries(
            _summaries(
                rows,
                repository_ids,
                deep_repository_ids,
                bootstrap_seed,
                bootstrap_resamples,
            )
        )
        membership_digests[held_out_agent_id] = {
            selector_id: canonical_digest(tuple(sorted(items.items())))
            for selector_id, items in memberships.items()
        }
    aggregate = {}
    for selector_id in SELECTOR_IDS:
        wide_values = tuple(
            float(agent["wide"][selector_id]["macro_repository_difference"])
            for agent in by_agent.values()
        )
        deep_values = tuple(
            float(agent["deep"][selector_id]["macro_repository_difference"])
            for agent in by_agent.values()
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


def run_temporal_null(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    adaptive_plan: Mapping[str, object],
    agent_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    origins: Mapping[str, Sequence[RepositoryOrigin]],
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
        _, memberships, _ = materialize_adaptive_selections(
            tasks,
            permuted,
            {},
            adaptive_plan,
            agent_plan,
            public_plan,
            include_controls=False,
        )
        rows = evaluate_memberships(
            origins,
            {ADAPTIVE_SELECTOR_ID: memberships[ADAPTIVE_SELECTOR_ID]},
            permuted,
            repository_ids,
            cluster_by_repository,
        )
        null_values.append(
            _macro_repository_difference(
                rows[ADAPTIVE_SELECTOR_ID],
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
    wide = summaries["wide"][ADAPTIVE_SELECTOR_ID]
    deep = summaries["deep"][ADAPTIVE_SELECTOR_ID]
    random_position = _number(
        _mapping(
            _mapping(random_reports["wide"], "candidate_positions"),
            ADAPTIVE_SELECTOR_ID,
        ).get("candidate_better_than_random_midrank"),
        "random percentile",
    )
    agent_transfer = _mapping(
        _mapping(leave_one_agent, "aggregate_by_selector"),
        ADAPTIVE_SELECTOR_ID,
    )
    candidate = float(wide["macro_repository_difference"])
    requirements = {
        "wide_at_most_minus_0_01": candidate <= -0.01,
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
        "better_than_history_match": candidate
        < float(
            summaries["wide"]["history_match"]["macro_repository_difference"]
        ),
        "better_than_fixed_markov": candidate
        < float(
            summaries["wide"]["difficulty_markov_match"][
                "macro_repository_difference"
            ]
        ),
        "better_than_stationary_ablation": candidate
        < float(
            summaries["wide"]["stationary_difficulty_match"][
                "macro_repository_difference"
            ]
        ),
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
            "open_sealed_agent_holdout_for_adaptive_candidate"
            if passed
            else "retire_adaptive_candidate_and_close_current_pool_algorithm_search"
        ),
        "requirements": requirements,
        "all_requirements_met": passed,
        "sealed_holdout_open_allowed": passed,
        "production_promotion_allowed": False,
        "plan_gate_digest": canonical_digest(_mapping(plan, "holdout_open_gate")),
    }


def _choice_diagnostics(
    choices: Mapping[str, Mapping[str, float | int | str]],
) -> Mapping[str, Any]:
    overall = defaultdict(int)
    by_repository: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    by_history_count: dict[int, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    markov_losses = []
    stationary_losses = []
    for choice in choices.values():
        selected = str(choice["selected_model"])
        repository_id = str(choice["repository_id"])
        history_count = int(choice["history_task_count"])
        overall[selected] += 1
        by_repository[repository_id][selected] += 1
        by_history_count[history_count][selected] += 1
        markov_losses.append(
            float(choice["markov_mean_negative_log_likelihood"])
        )
        stationary_losses.append(
            float(choice["stationary_mean_negative_log_likelihood"])
        )
    return {
        "overall": dict(sorted(overall.items())),
        "by_repository": {
            repository_id: dict(sorted(counts.items()))
            for repository_id, counts in sorted(by_repository.items())
        },
        "by_history_task_count": {
            str(history_count): dict(sorted(counts.items()))
            for history_count, counts in sorted(by_history_count.items())
        },
        "mean_prequential_negative_log_likelihood": {
            "markov": _mean(markov_losses),
            "stationary": _mean(stationary_losses),
        },
        "choice_digest": canonical_digest(tuple(sorted(choices.items()))),
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


def _compact_agent_summaries(
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


def _macro_repository_difference(
    rows: Sequence[ContrastRow],
    repository_ids: Sequence[str],
) -> float:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        values[row.repository_id].append(row.difference)
    return _mean(
        tuple(_mean(values[repository_id]) for repository_id in repository_ids)
    )


def _transition_matrix(
    transition: Sequence[Sequence[float]],
    state_count: int,
) -> tuple[tuple[float, ...], ...]:
    if len(transition) != state_count:
        raise ValueError("transition row count is invalid")
    rows = []
    for row in transition:
        values = tuple(float(value) for value in row)
        if (
            len(values) != state_count
            or any(not isfinite(value) or value <= 0.0 for value in values)
            or abs(fsum(values) - 1.0) > 1e-9
        ):
            raise ValueError("transition row is invalid")
        rows.append(values)
    return tuple(rows)


def _load_bound_result(
    path: Path,
    *,
    digest_field: str,
    expected_digest: object,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be an object")
    digest = payload.get(digest_field)
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != digest_field}
    )
    if digest != expected or digest != expected_digest:
        raise ValueError(f"{path.name} does not match the adaptive plan")
    return payload


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


def _mean(values: Sequence[float]) -> float:
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
    parser.add_argument("--agent-plan", type=Path, default=DEFAULT_AGENT_PLAN)
    parser.add_argument(
        "--execution-amendment",
        type=Path,
        default=DEFAULT_EXECUTION_AMENDMENT,
    )
    parser.add_argument(
        "--agent-results",
        type=Path,
        default=DEFAULT_AGENT_RESULTS,
    )
    parser.add_argument("--extension-plan", type=Path, default=DEFAULT_EXTENSION_PLAN)
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    adaptive_plan = load_adaptive_difficulty_plan(args.plan)
    agent_plan = load_agent_invariant_plan(args.agent_plan)
    execution_amendment = load_agent_invariant_execution_amendment(
        args.execution_amendment
    )
    source = _mapping(adaptive_plan, "source")
    agent_results = _load_bound_result(
        args.agent_results,
        digest_field="agent_invariant_results_digest",
        expected_digest=source.get("agent_invariant_results_digest"),
    )
    extension_plan = load_agent_panel_extension_plan(args.extension_plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    if _file_sha256(args.dataset) != _required_string(
        _mapping(public_plan, "task_source"),
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
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite adaptive replay: {args.output}")
    result = run_adaptive_replay(
        tasks,
        {**original_outcomes, **extension_outcomes},
        {**original_diagnostics, **extension_diagnostics},
        adaptive_plan,
        agent_plan,
        execution_amendment,
        agent_results,
        extension_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "adaptive_difficulty_results_digest": result[
                    "adaptive_difficulty_results_digest"
                ],
                "decision": result["decision"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
