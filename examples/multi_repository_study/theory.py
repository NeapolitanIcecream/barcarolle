#!/usr/bin/env python3
"""Replay four frozen theory-driven Selector mechanisms on opened outcomes."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from itertools import product
import hashlib
import json
from math import fsum, isfinite, sqrt
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence, TypeVar


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.development import (  # noqa: E402
    select_outcome_match,
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
from examples.multi_repository_study.semantic import (  # noqa: E402
    load_embedding_artifact,
    load_semantic_plan,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "theory-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_PUBLIC_RESULTS = HERE / "public-panel-results.json"
DEFAULT_DEVELOPMENT_RESULTS = HERE / "development-results.json"
DEFAULT_SEMANTIC_PLAN = HERE / "semantic-plan.json"
DEFAULT_SEMANTIC_RESULTS = HERE / "semantic-results.json"
DEFAULT_OUTPUT = HERE / "theory-results.json"

PRIMARY_SELECTORS = (
    "block_median_match",
    "joint_markov_match",
    "repository_analog_match",
    "semantic_trend_match",
)
OUTCOME_FORECAST_SELECTORS = (
    "history_match",
    "block_median_match",
    "joint_markov_match",
    "joint_markov_global_match",
    "repository_analog_match",
)

T = TypeVar("T")


def load_theory_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("theory plan must be a JSON object")
    if payload.get("schema_version") != "barcarolle_theory_driven_selector_plan_v1":
        raise ValueError("theory plan schema is unsupported")
    digest = payload.get("theory_plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "theory_plan_digest"}
    )
    if digest != expected:
        raise ValueError("theory plan digest does not match")
    candidates = tuple(
        _required_string(candidate, "selector_id")
        for candidate in _mapping_sequence(payload, "candidates")
    )
    if candidates != PRIMARY_SELECTORS:
        raise ValueError("theory plan candidate set does not match implementation")
    return payload


def complete_trailing_blocks(
    items: Sequence[T],
    block_size: int,
) -> tuple[tuple[T, ...], ...]:
    if (
        isinstance(block_size, bool)
        or not isinstance(block_size, int)
        or block_size <= 0
        or len(items) < block_size
    ):
        raise ValueError("complete trailing blocks require a valid block size")
    complete_count = len(items) // block_size
    start = len(items) - complete_count * block_size
    return tuple(
        tuple(items[offset : offset + block_size])
        for offset in range(start, len(items), block_size)
    )


def forecast_block_median(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    block_size: int,
) -> Mapping[str, float]:
    agent_ids = _agent_ids(outcomes_by_agent)
    blocks = complete_trailing_blocks(history, block_size)
    block_rates = tuple(
        _agent_rate_tuple(
            tuple(task.instance_id for task in block),
            outcomes_by_agent,
            agent_ids,
        )
        for block in blocks
    )
    return {
        agent_id: _median(tuple(row[index] for row in block_rates))
        for index, agent_id in enumerate(agent_ids)
    }


def fit_repository_equal_markov(
    training_repository_ids: Sequence[str],
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    cell_prior_mass: float,
) -> tuple[tuple[float, ...], ...]:
    repository_ids = _unique_strings(
        training_repository_ids,
        "Markov training repositories",
    )
    agent_ids = _agent_ids(outcomes_by_agent)
    states = _joint_states(len(agent_ids))
    matrices = []
    for repository_id in repository_ids:
        tasks = tasks_by_repository.get(repository_id)
        if tasks is None or len(tasks) < 2:
            raise ValueError(f"Markov training repository is empty: {repository_id}")
        state_rows = tuple(
            _task_state(task.instance_id, outcomes_by_agent, agent_ids)
            for task in tasks
        )
        matrices.append(
            _transition_matrix(
                state_rows,
                states,
                cell_prior_mass=cell_prior_mass,
            )
        )
    return tuple(
        tuple(
            _mean(tuple(matrix[row][column] for matrix in matrices))
            for column in range(len(states))
        )
        for row in range(len(states))
    )


def forecast_joint_markov(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    global_transition: Sequence[Sequence[float]],
    *,
    horizon: int,
    local_prior_strength: float,
    include_local_transitions: bool,
) -> Mapping[str, float]:
    if (
        isinstance(horizon, bool)
        or not isinstance(horizon, int)
        or horizon <= 0
        or not isfinite(local_prior_strength)
        or local_prior_strength <= 0.0
        or not history
    ):
        raise ValueError("Markov forecast configuration is invalid")
    agent_ids = _agent_ids(outcomes_by_agent)
    states = _joint_states(len(agent_ids))
    global_matrix = _validated_transition_matrix(global_transition, len(states))
    state_index = {state: index for index, state in enumerate(states)}
    local_counts = [[0] * len(states) for _ in states]
    history_states = tuple(
        _task_state(task.instance_id, outcomes_by_agent, agent_ids)
        for task in history
    )
    for left, right in zip(history_states, history_states[1:]):
        local_counts[state_index[left]][state_index[right]] += 1
    if include_local_transitions:
        transition = tuple(
            tuple(
                (
                    local_counts[row][column]
                    + local_prior_strength * global_matrix[row][column]
                )
                / (sum(local_counts[row]) + local_prior_strength)
                for column in range(len(states))
            )
            for row in range(len(states))
        )
    else:
        transition = global_matrix

    distribution = [0.0] * len(states)
    distribution[state_index[history_states[-1]]] = 1.0
    step_rates = []
    for _ in range(horizon):
        distribution = [
            fsum(
                distribution[source] * transition[source][target]
                for source in range(len(states))
            )
            for target in range(len(states))
        ]
        step_rates.append(
            tuple(
                fsum(
                    distribution[state_offset] * state[agent_offset]
                    for state_offset, state in enumerate(states)
                )
                for agent_offset in range(len(agent_ids))
            )
        )
    return {
        agent_id: _mean(tuple(row[index] for row in step_rates))
        for index, agent_id in enumerate(agent_ids)
    }


def forecast_repository_analog(
    target_origin: RepositoryOrigin,
    training_repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    block_size: int,
) -> tuple[Mapping[str, float], Mapping[str, str]]:
    repository_ids = _unique_strings(
        training_repository_ids,
        "analog training repositories",
    )
    if target_origin.repository_id in repository_ids:
        raise ValueError("target repository cannot train its own analog forecast")
    agent_ids = _agent_ids(outcomes_by_agent)
    target_state = _origin_response_state(
        target_origin,
        outcomes_by_agent,
        agent_ids,
        block_size,
    )
    residuals = []
    selected_analogs = {}
    for repository_id in repository_ids:
        origins = origins_by_repository.get(repository_id)
        if not origins:
            raise ValueError(f"analog repository has no Origins: {repository_id}")
        analog = min(
            origins,
            key=lambda origin: (
                _mean_absolute_distance(
                    target_state,
                    _origin_response_state(
                        origin,
                        outcomes_by_agent,
                        agent_ids,
                        block_size,
                    ),
                ),
                origin.origin_id,
            ),
        )
        blocks = complete_trailing_blocks(analog.history, block_size)
        latest_rates = _agent_rate_tuple(
            tuple(task.instance_id for task in blocks[-1]),
            outcomes_by_agent,
            agent_ids,
        )
        future_rates = _agent_rate_tuple(
            tuple(task.instance_id for task in analog.future),
            outcomes_by_agent,
            agent_ids,
        )
        residuals.append(
            tuple(
                future - latest
                for future, latest in zip(
                    future_rates,
                    latest_rates,
                    strict=True,
                )
            )
        )
        selected_analogs[repository_id] = analog.origin_id
    target_blocks = complete_trailing_blocks(target_origin.history, block_size)
    target_latest_rates = _agent_rate_tuple(
        tuple(task.instance_id for task in target_blocks[-1]),
        outcomes_by_agent,
        agent_ids,
    )
    forecast = {
        agent_id: _clip(
            target_latest_rates[index]
            + _median(tuple(row[index] for row in residuals))
        )
        for index, agent_id in enumerate(agent_ids)
    }
    return forecast, dict(sorted(selected_analogs.items()))


def forecast_semantic_trend(
    history_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
    *,
    block_size: int,
) -> tuple[float, ...]:
    blocks = complete_trailing_blocks(history_ids, block_size)
    if len(blocks) < 2:
        raise ValueError("semantic trend needs at least two complete blocks")
    centroids = tuple(_embedding_centroid(block, vectors) for block in blocks)
    dimensions = len(centroids[0])
    x_mean = (len(blocks) - 1) / 2.0
    denominator = fsum(
        (index - x_mean) ** 2 for index in range(len(blocks))
    )
    if denominator <= 0.0:
        raise ValueError("semantic regression has no time variation")
    target = []
    for dimension in range(dimensions):
        y_mean = _mean(tuple(row[dimension] for row in centroids))
        slope = (
            fsum(
                (index - x_mean) * (row[dimension] - y_mean)
                for index, row in enumerate(centroids)
            )
            / denominator
        )
        target.append(y_mean + slope * (len(blocks) - x_mean))
    return tuple(target)


def select_embedding_mean_match(
    history_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
    target: Sequence[float],
    *,
    budget: int,
    swap_pass_limit: int,
) -> tuple[str, ...]:
    task_ids = tuple(history_ids)
    if (
        not task_ids
        or len(task_ids) != len(set(task_ids))
        or isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget <= 0
        or budget > len(task_ids)
        or isinstance(swap_pass_limit, bool)
        or not isinstance(swap_pass_limit, int)
        or swap_pass_limit < 0
    ):
        raise ValueError("semantic selection shape is invalid")
    normalized_vectors = _validated_embedding_rows(task_ids, vectors)
    normalized_target = tuple(
        _finite_number(value, "semantic target value") for value in target
    )
    dimensions = len(normalized_vectors[0])
    if len(normalized_target) != dimensions:
        raise ValueError("semantic target dimensions do not match vectors")

    selected: list[int] = []
    selected_sum = [0.0] * dimensions

    def objective(candidate_sum: Sequence[float], count: int) -> float:
        return fsum(
            (candidate_sum[index] / count - normalized_target[index]) ** 2
            for index in range(dimensions)
        )

    for count in range(1, budget + 1):
        selected_set = set(selected)
        best = min(
            (
                objective(
                    tuple(
                        selected_sum[dimension]
                        + normalized_vectors[index][dimension]
                        for dimension in range(dimensions)
                    ),
                    count,
                ),
                index,
            )
            for index in range(len(task_ids))
            if index not in selected_set
        )
        selected.append(best[1])
        vector = normalized_vectors[best[1]]
        for dimension in range(dimensions):
            selected_sum[dimension] += vector[dimension]

    current = objective(selected_sum, budget)
    for _ in range(swap_pass_limit):
        selected_set = set(selected)
        best_swap: tuple[float, int, int] | None = None
        for selected_position, old_index in enumerate(selected):
            old_vector = normalized_vectors[old_index]
            for new_index, new_vector in enumerate(normalized_vectors):
                if new_index in selected_set:
                    continue
                value = objective(
                    tuple(
                        selected_sum[dimension]
                        - old_vector[dimension]
                        + new_vector[dimension]
                        for dimension in range(dimensions)
                    ),
                    budget,
                )
                candidate = (value, selected_position, new_index)
                if value < current - 1e-15 and (
                    best_swap is None or candidate < best_swap
                ):
                    best_swap = candidate
        if best_swap is None:
            break
        _, selected_position, new_index = best_swap
        old_index = selected[selected_position]
        old_vector = normalized_vectors[old_index]
        new_vector = normalized_vectors[new_index]
        selected[selected_position] = new_index
        for dimension in range(dimensions):
            selected_sum[dimension] += (
                new_vector[dimension] - old_vector[dimension]
            )
        current = objective(selected_sum, budget)
    return tuple(task_ids[index] for index in sorted(selected))


def run_theory_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    vectors: Mapping[str, Sequence[float]],
    embedding_manifest: Mapping[str, object],
    theory_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    source = _mapping(theory_plan, "source_results")
    if source.get("public_panel_plan_digest") != public_plan.get(
        "public_panel_plan_digest"
    ):
        raise ValueError("theory plan does not bind the public plan")
    if source.get("portfolio_digest") != portfolio.get("portfolio_digest"):
        raise ValueError("theory plan does not bind the portfolio")
    task_ids = tuple(task.instance_id for task in tasks)
    if not task_ids or len(task_ids) != len(set(task_ids)):
        raise ValueError("Task denominator must be nonempty and unique")
    if set(vectors) != set(task_ids) or any(
        set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values()
    ):
        raise ValueError("outcomes and embeddings must cover the Task denominator")

    rolling = _mapping(theory_plan, "rolling_origin")
    block_size = _positive_integer(rolling, "future_block_tasks")
    budget = _positive_integer(rolling, "selection_budget_tasks")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=block_size,
    )
    outer = _mapping(theory_plan, "outer_evaluation")
    repository_ids = _unique_strings(
        outer.get("repository_ids"),
        "outer repositories",
    )
    deep_repository_ids = _unique_strings(
        outer.get("deep_repository_ids"),
        "deep repositories",
    )
    if len(repository_ids) < 3 or not set(deep_repository_ids) <= set(repository_ids):
        raise ValueError("outer repository portfolios are invalid")
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    if any(
        not origins_by_repository.get(repository_id)
        or repository_id not in cluster_by_repository
        for repository_id in repository_ids
    ):
        raise ValueError("every outer repository needs Origins and lineage")
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    for repository_tasks in tasks_by_repository.values():
        repository_tasks.sort(
            key=lambda task: (task.created_at, task.instance_id)
        )

    constants = _mapping(theory_plan, "fixed_algorithm_constants")
    cell_prior_mass = _finite_number(
        constants.get("training_transition_dirichlet_cell_mass"),
        "training transition cell mass",
    )
    local_prior_strength = _finite_number(
        constants.get("target_local_transition_prior_total_mass_per_row"),
        "target local Markov prior strength",
    )
    horizon = _positive_integer(constants, "markov_forecast_steps")
    swap_pass_limit = _nonnegative_integer(constants, "semantic_swap_pass_limit")

    selector_ids = (
        "history_match",
        *PRIMARY_SELECTORS,
        "joint_markov_global_match",
    )
    contrast_rows = {selector_id: [] for selector_id in selector_ids}
    forecast_errors: dict[str, dict[str, list[float]]] = {
        selector_id: defaultdict(list)
        for selector_id in OUTCOME_FORECAST_SELECTORS
    }
    representation_errors: dict[str, dict[str, list[float]]] = {
        selector_id: defaultdict(list)
        for selector_id in OUTCOME_FORECAST_SELECTORS
    }
    per_agent_differences: dict[
        str,
        dict[str, dict[str, list[float]]],
    ] = {
        selector_id: {
            agent_id: defaultdict(list) for agent_id in _agent_ids(outcomes_by_agent)
        }
        for selector_id in selector_ids
    }
    semantic_distances: dict[str, dict[str, list[float]]] = {
        "full_history": defaultdict(list),
        "semantic_trend_match": defaultdict(list),
    }
    selection_memberships: dict[str, dict[str, tuple[str, ...]]] = {
        selector_id: {} for selector_id in selector_ids
    }
    outer_fit_digests: dict[str, Mapping[str, Any]] = {}

    for outer_repository_id in repository_ids:
        training_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id != outer_repository_id
        )
        global_transition = fit_repository_equal_markov(
            training_repository_ids,
            tasks_by_repository,
            outcomes_by_agent,
            cell_prior_mass=cell_prior_mass,
        )
        analog_memberships = {}
        for origin in origins_by_repository[outer_repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            forecasts: dict[str, Mapping[str, float]] = {
                "history_match": _agent_rates(
                    history_ids,
                    outcomes_by_agent,
                ),
                "block_median_match": forecast_block_median(
                    origin.history,
                    outcomes_by_agent,
                    block_size=block_size,
                ),
                "joint_markov_match": forecast_joint_markov(
                    origin.history,
                    outcomes_by_agent,
                    global_transition,
                    horizon=horizon,
                    local_prior_strength=local_prior_strength,
                    include_local_transitions=True,
                ),
                "joint_markov_global_match": forecast_joint_markov(
                    origin.history,
                    outcomes_by_agent,
                    global_transition,
                    horizon=horizon,
                    local_prior_strength=local_prior_strength,
                    include_local_transitions=False,
                ),
            }
            analog_forecast, analogs = forecast_repository_analog(
                origin,
                training_repository_ids,
                origins_by_repository,
                outcomes_by_agent,
                block_size=block_size,
            )
            forecasts["repository_analog_match"] = analog_forecast
            analog_memberships[origin.origin_id] = analogs

            selected_by_selector = {
                selector_id: select_outcome_match(
                    origin.history,
                    outcomes_by_agent,
                    forecast,
                    budget=budget,
                )
                for selector_id, forecast in forecasts.items()
            }
            semantic_target = forecast_semantic_trend(
                history_ids,
                vectors,
                block_size=block_size,
            )
            selected_by_selector["semantic_trend_match"] = (
                select_embedding_mean_match(
                    history_ids,
                    vectors,
                    semantic_target,
                    budget=budget,
                    swap_pass_limit=swap_pass_limit,
                )
            )

            # Target-future outcomes are first consumed after every Selection
            # for this Origin has been materialized.
            future_ids = tuple(task.instance_id for task in origin.future)
            future_rates = _agent_rates(future_ids, outcomes_by_agent)
            baseline_loss = future_pass_rate_mae(
                history_ids,
                future_ids,
                outcomes_by_agent,
            )
            semantic_distances["full_history"][outer_repository_id].append(
                _cosine_centroid_distance(history_ids, future_ids, vectors)
            )
            for selector_id, selected_ids in selected_by_selector.items():
                selected_loss = future_pass_rate_mae(
                    selected_ids,
                    future_ids,
                    outcomes_by_agent,
                )
                contrast_rows[selector_id].append(
                    ContrastRow(
                        selector_id=selector_id,
                        portfolio="wide",
                        repository_id=outer_repository_id,
                        repository_cluster_id=cluster_by_repository[
                            outer_repository_id
                        ],
                        origin_id=origin.origin_id,
                        difference=selected_loss - baseline_loss,
                    )
                )
                selection_memberships[selector_id][origin.origin_id] = selected_ids
                selected_rates = _agent_rates(selected_ids, outcomes_by_agent)
                baseline_rates = _agent_rates(history_ids, outcomes_by_agent)
                for agent_id in _agent_ids(outcomes_by_agent):
                    per_agent_differences[selector_id][agent_id][
                        outer_repository_id
                    ].append(
                        abs(selected_rates[agent_id] - future_rates[agent_id])
                        - abs(baseline_rates[agent_id] - future_rates[agent_id])
                    )
                if selector_id in forecasts:
                    forecast = forecasts[selector_id]
                    forecast_errors[selector_id][outer_repository_id].append(
                        _rate_mae(forecast, future_rates)
                    )
                    representation_errors[selector_id][
                        outer_repository_id
                    ].append(_rate_mae(selected_rates, forecast))
            semantic_distances["semantic_trend_match"][
                outer_repository_id
            ].append(
                _cosine_centroid_distance(
                    selected_by_selector["semantic_trend_match"],
                    future_ids,
                    vectors,
                )
            )
        outer_fit_digests[outer_repository_id] = {
            "training_repository_ids": training_repository_ids,
            "joint_markov_transition_digest": canonical_digest(
                global_transition
            ),
            "repository_analog_membership_digest": canonical_digest(
                tuple(sorted(analog_memberships.items()))
            ),
        }

    aggregation = _mapping(_mapping(theory_plan, "diagnostics"), "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )
    summaries = {
        portfolio_name: {
            selector_id: summarize_contrasts(
                tuple(
                    _with_portfolio(row, portfolio_name)
                    for row in rows
                    if row.repository_id in selected_repositories
                ),
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )
            for selector_id, rows in contrast_rows.items()
        }
        for portfolio_name, selected_repositories in (
            ("wide", set(repository_ids)),
            ("deep", set(deep_repository_ids)),
        )
    }
    random_config = _mapping(_mapping(theory_plan, "diagnostics"), "random_calibration")
    random_reports = {
        portfolio_name: random_calibration(
            selected_repositories,
            origins_by_repository,
            outcomes_by_agent,
            budget=budget,
            draws=_positive_integer(random_config, "draws"),
            seed=_integer(random_config, "seed"),
            observed_summaries=summaries[portfolio_name],
        )
        for portfolio_name, selected_repositories in (
            ("wide", repository_ids),
            ("deep", deep_repository_ids),
        )
    }
    nomination = _nominate(summaries, random_reports)
    result: dict[str, Any] = {
        "schema_version": "barcarolle_theory_driven_selector_results_v1",
        "study_id": theory_plan.get("study_id"),
        "epistemic_status": theory_plan.get("epistemic_status"),
        "theory_plan_digest": theory_plan.get("theory_plan_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "public_panel_results_digest": source.get("public_panel_results_digest"),
        "development_results_digest": source.get("development_results_digest"),
        "semantic_results_digest": source.get("semantic_results_digest"),
        "embedding_manifest": embedding_manifest,
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        },
        "outer_fit_digests": outer_fit_digests,
        "summaries": summaries,
        "random_calibration": random_reports,
        "forecast_decomposition": {
            "forecast_vs_future": _summarize_scalar_diagnostics(
                forecast_errors,
                repository_ids,
                deep_repository_ids,
            ),
            "selected_vs_forecast": _summarize_scalar_diagnostics(
                representation_errors,
                repository_ids,
                deep_repository_ids,
            ),
        },
        "per_agent_diagnostic": _summarize_per_agent(
            per_agent_differences,
            repository_ids,
            deep_repository_ids,
        ),
        "semantic_alignment_diagnostic": {
            selector_id: _summarize_repository_values(
                by_repository,
                repository_ids,
                deep_repository_ids,
            )
            for selector_id, by_repository in semantic_distances.items()
        },
        "selection_membership_digests": {
            selector_id: canonical_digest(tuple(sorted(rows.items())))
            for selector_id, rows in selection_memberships.items()
        },
        "nomination": nomination,
        "claim_boundary": (
            "All Agent outcomes were open before this theory plan. Results "
            "screen prespecified mechanisms only; they cannot confirm a "
            "Selector, establish strict prospectivity or unseen-Agent transfer, "
            "or promote a Runner default."
        ),
    }
    result["theory_results_digest"] = canonical_digest(result)
    return result


def _transition_matrix(
    state_rows: Sequence[tuple[int, ...]],
    states: Sequence[tuple[int, ...]],
    *,
    cell_prior_mass: float,
) -> tuple[tuple[float, ...], ...]:
    if (
        len(state_rows) < 2
        or not isfinite(cell_prior_mass)
        or cell_prior_mass <= 0.0
    ):
        raise ValueError("transition input is invalid")
    state_index = {state: index for index, state in enumerate(states)}
    if len(state_index) != len(states) or any(state not in state_index for state in state_rows):
        raise ValueError("transition state is outside the declared state space")
    counts = [[0] * len(states) for _ in states]
    for left, right in zip(state_rows, state_rows[1:]):
        counts[state_index[left]][state_index[right]] += 1
    return tuple(
        tuple(
            (counts[row][column] + cell_prior_mass)
            / (sum(counts[row]) + cell_prior_mass * len(states))
            for column in range(len(states))
        )
        for row in range(len(states))
    )


def _validated_transition_matrix(
    matrix: Sequence[Sequence[float]],
    state_count: int,
) -> tuple[tuple[float, ...], ...]:
    if len(matrix) != state_count:
        raise ValueError("transition matrix row count is invalid")
    normalized = tuple(
        tuple(_finite_number(value, "transition probability") for value in row)
        for row in matrix
    )
    if any(
        len(row) != state_count
        or any(value < 0.0 or value > 1.0 for value in row)
        or abs(fsum(row) - 1.0) > 1e-9
        for row in normalized
    ):
        raise ValueError("transition matrix is not row stochastic")
    return normalized


def _joint_states(agent_count: int) -> tuple[tuple[int, ...], ...]:
    if agent_count <= 0 or agent_count > 8:
        raise ValueError("joint state width is invalid")
    return tuple(product((0, 1), repeat=agent_count))


def _task_state(
    task_id: str,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
) -> tuple[int, ...]:
    return tuple(
        _binary_outcome(outcomes_by_agent[agent_id].get(task_id), agent_id, task_id)
        for agent_id in agent_ids
    )


def _origin_response_state(
    origin: RepositoryOrigin,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    block_size: int,
) -> tuple[float, ...]:
    blocks = complete_trailing_blocks(origin.history, block_size)
    if len(blocks) < 2:
        raise ValueError("analog state needs two complete historical blocks")
    full = _agent_rate_tuple(
        tuple(task.instance_id for task in origin.history),
        outcomes_by_agent,
        agent_ids,
    )
    penultimate = _agent_rate_tuple(
        tuple(task.instance_id for task in blocks[-2]),
        outcomes_by_agent,
        agent_ids,
    )
    latest = _agent_rate_tuple(
        tuple(task.instance_id for task in blocks[-1]),
        outcomes_by_agent,
        agent_ids,
    )
    return (*full, *penultimate, *latest)


def _agent_rates(
    task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> Mapping[str, float]:
    agent_ids = _agent_ids(outcomes_by_agent)
    values = _agent_rate_tuple(task_ids, outcomes_by_agent, agent_ids)
    return dict(zip(agent_ids, values, strict=True))


def _agent_rate_tuple(
    task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
) -> tuple[float, ...]:
    if not task_ids:
        raise ValueError("Agent rates require Tasks")
    return tuple(
        _mean(
            tuple(
                _binary_outcome(
                    outcomes_by_agent[agent_id].get(task_id),
                    agent_id,
                    task_id,
                )
                for task_id in task_ids
            )
        )
        for agent_id in agent_ids
    )


def _agent_ids(
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> tuple[str, ...]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    if not agent_ids:
        raise ValueError("at least one Agent outcome vector is required")
    return agent_ids


def _embedding_centroid(
    task_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
) -> tuple[float, ...]:
    rows = _validated_embedding_rows(task_ids, vectors)
    return tuple(
        _mean(tuple(row[dimension] for row in rows))
        for dimension in range(len(rows[0]))
    )


def _validated_embedding_rows(
    task_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
) -> tuple[tuple[float, ...], ...]:
    if not task_ids:
        raise ValueError("embedding rows require Tasks")
    rows = []
    dimensions = None
    for task_id in task_ids:
        vector = vectors.get(task_id)
        if vector is None or not vector:
            raise ValueError("embedding vector is missing")
        row = tuple(_finite_number(value, "embedding value") for value in vector)
        if dimensions is None:
            dimensions = len(row)
        if len(row) != dimensions:
            raise ValueError("embedding dimensions are inconsistent")
        rows.append(row)
    return tuple(rows)


def _cosine_centroid_distance(
    left_ids: Sequence[str],
    right_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
) -> float:
    left = _embedding_centroid(left_ids, vectors)
    right = _embedding_centroid(right_ids, vectors)
    dot = fsum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(fsum(value * value for value in left))
    right_norm = sqrt(fsum(value * value for value in right))
    if left_norm <= 0.0 or right_norm <= 0.0:
        raise ValueError("embedding centroid has zero norm")
    cosine = dot / (left_norm * right_norm)
    return 1.0 - max(-1.0, min(1.0, cosine))


def _rate_mae(
    left: Mapping[str, float],
    right: Mapping[str, float],
) -> float:
    if set(left) != set(right) or not left:
        raise ValueError("rate vectors must cover the same Agents")
    return _mean(tuple(abs(float(left[key]) - float(right[key])) for key in left))


def _summarize_scalar_diagnostics(
    values: Mapping[str, Mapping[str, Sequence[float]]],
    wide_repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    return {
        selector_id: _summarize_repository_values(
            by_repository,
            wide_repository_ids,
            deep_repository_ids,
        )
        for selector_id, by_repository in values.items()
    }


def _summarize_repository_values(
    values: Mapping[str, Sequence[float]],
    wide_repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    return {
        portfolio: {
            "macro_repository_mean": _mean(
                tuple(_mean(tuple(values[repository_id])) for repository_id in ids)
            ),
            "repository_means": {
                repository_id: _mean(tuple(values[repository_id]))
                for repository_id in ids
            },
        }
        for portfolio, ids in (
            ("wide", wide_repository_ids),
            ("deep", deep_repository_ids),
        )
    }


def _summarize_per_agent(
    values: Mapping[str, Mapping[str, Mapping[str, Sequence[float]]]],
    wide_repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    return {
        selector_id: {
            agent_id: _summarize_repository_values(
                by_repository,
                wide_repository_ids,
                deep_repository_ids,
            )
            for agent_id, by_repository in by_agent.items()
        }
        for selector_id, by_agent in values.items()
    }


def _nominate(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    random_reports: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    history_match = float(
        summaries["wide"]["history_match"]["macro_repository_difference"]
    )
    assessments = {}
    qualifying = []
    for selector_id in PRIMARY_SELECTORS:
        wide = summaries["wide"][selector_id]
        deep = summaries["deep"][selector_id]
        random_position = float(
            random_reports["wide"]["candidate_positions"][selector_id][
                "candidate_better_than_random_midrank"
            ]
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
            "every_leave_one_repository_out_favorable": not bool(
                wide["leave_one_cluster_out_has_nonnegative_difference"]
            ),
            "deep_direction_favorable": float(
                deep["macro_repository_difference"]
            )
            < 0.0,
            "better_than_at_least_75_percent_random": random_position >= 0.75,
            "improves_history_match_when_required": (
                selector_id == "semantic_trend_match"
                or float(wide["macro_repository_difference"]) < history_match
            ),
        }
        passed = all(requirements.values())
        assessments[selector_id] = {
            "requirements": requirements,
            "all_requirements_met": passed,
        }
        if passed:
            qualifying.append(selector_id)
    nominated = (
        min(
            qualifying,
            key=lambda selector_id: (
                float(
                    summaries["wide"][selector_id][
                        "macro_repository_difference"
                    ]
                ),
                selector_id,
            ),
        )
        if qualifying
        else None
    )
    return {
        "status": (
            "freeze_one_theory_candidate_for_independent_validation"
            if nominated
            else "no_theory_candidate_warrants_independent_or_paid_validation"
        ),
        "nominated_selector_id": nominated,
        "candidate_assessments": assessments,
        "production_promotion_allowed": False,
    }


def _with_portfolio(row: ContrastRow, portfolio: str) -> ContrastRow:
    return ContrastRow(
        selector_id=row.selector_id,
        portfolio=portfolio,
        repository_id=row.repository_id,
        repository_cluster_id=row.repository_cluster_id,
        origin_id=row.origin_id,
        difference=row.difference,
    )


def _mean_absolute_distance(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("state vectors must have one nonempty shape")
    return _mean(
        tuple(abs(a - b) for a, b in zip(left, right, strict=True))
    )


def _median(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("median requires values")
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def _binary_outcome(value: object, agent_id: str, task_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
        raise ValueError(f"invalid binary outcome for {agent_id}/{task_id}")
    return value


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    normalized = float(value)
    if not isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _unique_strings(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be nonempty strings")
    normalized = tuple(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must be unique")
    return normalized


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


def _nonnegative_integer(value: Mapping[str, object], key: str) -> int:
    item = _integer(value, key)
    if item < 0:
        raise ValueError(f"{key} must be nonnegative")
    return item


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_bound_result(
    path: Path,
    *,
    digest_field: str,
    expected_digest: object,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be an object")
    digest = payload.pop(digest_field, None)
    if canonical_digest(payload) != digest or digest != expected_digest:
        raise ValueError(f"{path.name} does not match the theory plan")
    return payload


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument(
        "--public-results",
        type=Path,
        default=DEFAULT_PUBLIC_RESULTS,
    )
    parser.add_argument(
        "--development-results",
        type=Path,
        default=DEFAULT_DEVELOPMENT_RESULTS,
    )
    parser.add_argument(
        "--semantic-plan",
        type=Path,
        default=DEFAULT_SEMANTIC_PLAN,
    )
    parser.add_argument(
        "--semantic-results",
        type=Path,
        default=DEFAULT_SEMANTIC_RESULTS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    theory_plan = load_theory_plan(args.plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    source = _mapping(theory_plan, "source_results")
    public_source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(
        public_source,
        "dataset_sha256",
    ):
        raise RuntimeError("dataset digest does not match the public plan")
    _load_bound_result(
        args.public_results,
        digest_field="public_panel_results_digest",
        expected_digest=source.get("public_panel_results_digest"),
    )
    _load_bound_result(
        args.development_results,
        digest_field="development_results_digest",
        expected_digest=source.get("development_results_digest"),
    )
    _load_bound_result(
        args.semantic_results,
        digest_field="semantic_results_digest",
        expected_digest=source.get("semantic_results_digest"),
    )
    semantic_plan = load_semantic_plan(args.semantic_plan)
    if semantic_plan.get("semantic_plan_digest") != source.get(
        "semantic_plan_digest"
    ):
        raise ValueError("semantic plan does not match theory plan")
    tasks = load_dataset_tasks(args.dataset)
    task_ids = tuple(task.instance_id for task in tasks)
    outcomes, _ = load_public_outcomes(
        args.result_dir,
        public_plan,
        task_ids,
    )
    vectors, embedding_manifest = load_embedding_artifact(
        args.embeddings,
        semantic_plan,
        task_ids,
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite theory replay: {args.output}")
    result = run_theory_replay(
        tasks,
        outcomes,
        vectors,
        embedding_manifest,
        theory_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "nomination": result["nomination"],
                "theory_results_digest": result["theory_results_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
