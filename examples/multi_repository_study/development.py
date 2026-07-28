#!/usr/bin/env python3
"""Develop tiny cross-repository forecast corrections on opened public outcomes."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from functools import lru_cache
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
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


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "development-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_PUBLIC_RESULTS = HERE / "public-panel-results.json"
DEFAULT_OUTPUT = HERE / "development-results.json"


def load_development_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("development plan must be a JSON object")
    if (
        payload.get("schema_version")
        != "barcarolle_multi_repository_development_plan_v1"
    ):
        raise ValueError("development plan schema is unsupported")
    digest = payload.get("development_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "development_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("development plan digest does not match")
    return payload


def select_outcome_match(
    history: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    target_rates: Mapping[str, float],
    *,
    budget: int,
) -> tuple[str, ...]:
    """Choose a stable subset whose historical outcome vector matches a target."""
    if budget <= 0 or budget > len(history):
        raise ValueError("selection budget must fit history")
    agent_ids = tuple(sorted(outcomes_by_agent))
    if not agent_ids or set(target_rates) != set(agent_ids):
        raise ValueError("target rates must cover the exact Agent panel")
    normalized_targets = tuple(
        _bounded_number(target_rates[agent_id], f"target rate for {agent_id}")
        for agent_id in agent_ids
    )
    task_ids = tuple(task.instance_id for task in history)
    if (
        len(task_ids) != len(set(task_ids))
        or any(not task_id for task_id in task_ids)
    ):
        raise ValueError("history Task IDs must be nonempty and unique")
    vectors = tuple(
        tuple(
            _binary_outcome(
                outcomes_by_agent[agent_id].get(task_id),
                agent_id,
                task_id,
            )
            for agent_id in agent_ids
        )
        for task_id in task_ids
    )
    candidates = _outcome_subset_states(vectors, budget)
    _, selected_indices = min(
        (
            fsum(
                abs(outcome_sum / budget - target)
                for outcome_sum, target in zip(sums, normalized_targets, strict=True)
            )
            / len(agent_ids),
            indices,
        )
        for sums, indices in candidates
    )
    return tuple(task_ids[index] for index in selected_indices)


@lru_cache(maxsize=512)
def _outcome_subset_states(
    vectors: tuple[tuple[int, ...], ...],
    budget: int,
) -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    if not vectors or budget <= 0 or budget > len(vectors):
        raise ValueError("outcome subset state input is invalid")
    agent_count = len(vectors[0])
    if agent_count == 0 or any(
        len(vector) != agent_count or any(value not in (0, 1) for value in vector)
        for vector in vectors
    ):
        raise ValueError("outcome vectors must have one stable binary width")
    indices_by_vector: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for index, vector in enumerate(vectors):
        indices_by_vector[vector].append(index)
    categories = tuple(sorted(indices_by_vector))
    best_indices_by_sums: dict[tuple[int, ...], tuple[int, ...]] = {}

    def visit(
        category_index: int,
        remaining: int,
        sums: tuple[int, ...],
        selected_indices: tuple[int, ...],
    ) -> None:
        if category_index == len(categories):
            if remaining == 0:
                ordered = tuple(sorted(selected_indices))
                existing = best_indices_by_sums.get(sums)
                if existing is None or ordered < existing:
                    best_indices_by_sums[sums] = ordered
            return
        vector = categories[category_index]
        available_indices = indices_by_vector[vector]
        maximum = min(len(available_indices), remaining)
        for count in range(maximum + 1):
            visit(
                category_index + 1,
                remaining - count,
                tuple(
                    value + count * component
                    for value, component in zip(sums, vector, strict=True)
                ),
                (*selected_indices, *available_indices[:count]),
            )

    visit(0, budget, (0,) * agent_count, ())
    if not best_indices_by_sums:
        raise ValueError("no feasible outcome-matching subset")
    return tuple(sorted(best_indices_by_sums.items()))


def estimate_repository_equal_drift(
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> Mapping[str, float]:
    """Estimate future-minus-history drift with repositories weighted equally."""
    repositories = _unique_strings(repository_ids, "training repositories")
    agent_ids = tuple(sorted(outcomes_by_agent))
    if not agent_ids:
        raise ValueError("drift estimation requires Agent outcomes")
    repository_drifts = []
    for repository_id in repositories:
        origins = origins_by_repository.get(repository_id)
        if not origins:
            raise ValueError(f"training repository has no Origins: {repository_id}")
        origin_drifts = []
        for origin in origins:
            history_rates = _agent_rates(
                tuple(task.instance_id for task in origin.history),
                outcomes_by_agent,
            )
            future_rates = _agent_rates(
                tuple(task.instance_id for task in origin.future),
                outcomes_by_agent,
            )
            origin_drifts.append(
                {
                    agent_id: future_rates[agent_id] - history_rates[agent_id]
                    for agent_id in agent_ids
                }
            )
        repository_drifts.append(
            {
                agent_id: _mean(
                    tuple(row[agent_id] for row in origin_drifts)
                )
                for agent_id in agent_ids
            }
        )
    return {
        agent_id: _mean(tuple(row[agent_id] for row in repository_drifts))
        for agent_id in agent_ids
    }


def run_development_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    development_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the frozen opened-development outer-repository evaluation."""
    source_results = _mapping(development_plan, "source_results")
    if source_results.get("public_panel_plan_digest") != public_plan.get(
        "public_panel_plan_digest"
    ):
        raise ValueError("development plan does not bind the public panel plan")
    if source_results.get("portfolio_digest") != portfolio.get("portfolio_digest"):
        raise ValueError("development plan does not bind the portfolio")
    rolling = _mapping(public_plan, "rolling_origin")
    budget = _positive_integer(rolling, "selection_budget_task_checks")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(rolling, "future_block_tasks"),
    )
    task_ids = {task.instance_id for task in tasks}
    if not task_ids or any(set(outcomes) != task_ids for outcomes in outcomes_by_agent.values()):
        raise ValueError("every Agent must cover the exact Task denominator")

    outer = _mapping(development_plan, "outer_evaluation")
    repository_ids = _unique_strings(
        outer.get("repository_ids"),
        "outer repositories",
    )
    deep_repository_ids = _unique_strings(
        outer.get("deep_repository_ids"),
        "deep repositories",
    )
    if not set(deep_repository_ids) <= set(repository_ids):
        raise ValueError("deep repositories must be part of the outer portfolio")
    if len(repository_ids) < 3:
        raise ValueError("nested repository evaluation requires at least three repos")
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    if any(
        repository_id not in cluster_by_repository
        or not origins_by_repository.get(repository_id)
        for repository_id in repository_ids
    ):
        raise ValueError("every outer repository needs lineage and complete Origins")

    candidate_rows: dict[str, list[ContrastRow]] = {
        "history_match": [],
        "cross_repository_drift_match": [],
        "local_trend_match": [],
    }
    support_rows: list[ContrastRow] = []
    outer_fold_parameters: dict[str, Mapping[str, Any]] = {}
    drift_grid, alpha_grid = _candidate_grids(development_plan)

    for outer_repository_id in repository_ids:
        training_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id != outer_repository_id
        )
        shrinkage, shrinkage_scores = _choose_drift_shrinkage(
            training_repository_ids,
            origins_by_repository,
            outcomes_by_agent,
            drift_grid,
            budget,
        )
        fitted_drift = estimate_repository_equal_drift(
            training_repository_ids,
            origins_by_repository,
            outcomes_by_agent,
        )
        alpha, alpha_scores = _choose_local_trend_alpha(
            training_repository_ids,
            origins_by_repository,
            outcomes_by_agent,
            alpha_grid,
            budget,
        )
        outer_fold_parameters[outer_repository_id] = {
            "training_repository_ids": training_repository_ids,
            "cross_repository_drift_match": {
                "chosen_shrinkage": shrinkage,
                "inner_macro_repository_losses": shrinkage_scores,
                "fitted_drift_by_agent": dict(sorted(fitted_drift.items())),
            },
            "local_trend_match": {
                "chosen_alpha": alpha,
                "training_macro_repository_losses": alpha_scores,
            },
        }
        for origin in origins_by_repository[outer_repository_id]:
            baseline_loss = _baseline_loss(origin, outcomes_by_agent)
            history_rates = _agent_rates(
                tuple(task.instance_id for task in origin.history),
                outcomes_by_agent,
            )
            recent_rates = _agent_rates(
                tuple(task.instance_id for task in origin.history[-budget:]),
                outcomes_by_agent,
            )
            future_rates = _agent_rates(
                tuple(task.instance_id for task in origin.future),
                outcomes_by_agent,
            )
            forecasts = {
                "history_match": history_rates,
                "cross_repository_drift_match": {
                    agent_id: _clip(
                        history_rates[agent_id]
                        + shrinkage * fitted_drift[agent_id]
                    )
                    for agent_id in history_rates
                },
                "local_trend_match": {
                    agent_id: _clip(
                        history_rates[agent_id]
                        + alpha * (recent_rates[agent_id] - history_rates[agent_id])
                    )
                    for agent_id in history_rates
                },
            }
            for selector_id, forecast in forecasts.items():
                candidate_rows[selector_id].append(
                    _contrast_for_forecast(
                        selector_id,
                        origin,
                        outcomes_by_agent,
                        forecast,
                        baseline_loss,
                        cluster_by_repository[outer_repository_id],
                        budget,
                    )
                )
            support_rows.append(
                _contrast_for_forecast(
                    "hindsight_support",
                    origin,
                    outcomes_by_agent,
                    future_rates,
                    baseline_loss,
                    cluster_by_repository[outer_repository_id],
                    budget,
                )
            )

    aggregation = _mapping(public_plan, "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(aggregation, "bootstrap_resamples")
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
            for selector_id, rows in candidate_rows.items()
        }
        for portfolio_name, selected_repositories in (
            ("wide", set(repository_ids)),
            ("deep", set(deep_repository_ids)),
        )
    }
    support_summaries = {
        portfolio_name: summarize_contrasts(
            tuple(
                _with_portfolio(row, portfolio_name)
                for row in support_rows
                if row.repository_id in selected_repositories
            ),
            bootstrap_seed=bootstrap_seed,
            bootstrap_resamples=bootstrap_resamples,
        )
        for portfolio_name, selected_repositories in (
            ("wide", set(repository_ids)),
            ("deep", set(deep_repository_ids)),
        )
    }
    random_config = _mapping(public_plan, "random_calibration")
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
        "schema_version": "barcarolle_multi_repository_development_results_v1",
        "study_id": development_plan.get("study_id"),
        "epistemic_status": development_plan.get("epistemic_status"),
        "development_plan_digest": development_plan.get("development_plan_digest"),
        "public_panel_results_digest": source_results.get(
            "public_panel_results_digest"
        ),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        },
        "outer_fold_parameters": outer_fold_parameters,
        "summaries": summaries,
        "random_calibration": random_reports,
        "hindsight_support": support_summaries,
        "nomination": nomination,
        "claim_boundary": (
            "These outcomes were open before the development plan. Nested "
            "repository folds can screen mechanisms, but cannot confirm a "
            "Selector, establish unseen-Agent transfer, or promote a Runner default."
        ),
    }
    result["development_results_digest"] = canonical_digest(result)
    return result


def _candidate_grids(
    plan: Mapping[str, object],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    candidates = {
        _required_string(row, "selector_id"): row
        for row in _mapping_sequence(plan, "candidates")
    }
    if set(candidates) != {
        "history_match",
        "cross_repository_drift_match",
        "local_trend_match",
    }:
        raise ValueError("development candidate set does not match implementation")
    drift_grid = _number_tuple(
        candidates["cross_repository_drift_match"].get("shrinkage_grid"),
        "shrinkage grid",
    )
    alpha_grid = _number_tuple(
        candidates["local_trend_match"].get("alpha_grid"),
        "alpha grid",
    )
    return drift_grid, alpha_grid


def _choose_drift_shrinkage(
    training_repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    grid: Sequence[float],
    budget: int,
) -> tuple[float, Mapping[str, float]]:
    scores = {}
    for shrinkage in grid:
        repository_losses = []
        for validation_repository_id in training_repository_ids:
            fit_repository_ids = tuple(
                repository_id
                for repository_id in training_repository_ids
                if repository_id != validation_repository_id
            )
            drift = estimate_repository_equal_drift(
                fit_repository_ids,
                origins_by_repository,
                outcomes_by_agent,
            )
            repository_losses.append(
                _mean(
                    tuple(
                        _forecast_loss(
                            origin,
                            outcomes_by_agent,
                            {
                                agent_id: _clip(
                                    history_rate + shrinkage * drift[agent_id]
                                )
                                for agent_id, history_rate in _agent_rates(
                                    tuple(
                                        task.instance_id
                                        for task in origin.history
                                    ),
                                    outcomes_by_agent,
                                ).items()
                            },
                            budget,
                        )
                        for origin in origins_by_repository[
                            validation_repository_id
                        ]
                    )
                )
            )
        scores[_number_key(shrinkage)] = _mean(tuple(repository_losses))
    chosen = min(grid, key=lambda value: (scores[_number_key(value)], value))
    return chosen, scores


def _choose_local_trend_alpha(
    training_repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    grid: Sequence[float],
    budget: int,
) -> tuple[float, Mapping[str, float]]:
    scores = {}
    for alpha in grid:
        repository_losses = []
        for repository_id in training_repository_ids:
            repository_losses.append(
                _mean(
                    tuple(
                        _forecast_loss(
                            origin,
                            outcomes_by_agent,
                            _local_trend_forecast(
                                origin,
                                outcomes_by_agent,
                                alpha,
                                budget,
                            ),
                            budget,
                        )
                        for origin in origins_by_repository[repository_id]
                    )
                )
            )
        scores[_number_key(alpha)] = _mean(tuple(repository_losses))
    chosen = min(grid, key=lambda value: (scores[_number_key(value)], value))
    return chosen, scores


def _local_trend_forecast(
    origin: RepositoryOrigin,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    alpha: float,
    budget: int,
) -> Mapping[str, float]:
    history_rates = _agent_rates(
        tuple(task.instance_id for task in origin.history),
        outcomes_by_agent,
    )
    recent_rates = _agent_rates(
        tuple(task.instance_id for task in origin.history[-budget:]),
        outcomes_by_agent,
    )
    return {
        agent_id: _clip(
            history_rate + alpha * (recent_rates[agent_id] - history_rate)
        )
        for agent_id, history_rate in history_rates.items()
    }


def _forecast_loss(
    origin: RepositoryOrigin,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    forecast: Mapping[str, float],
    budget: int,
) -> float:
    selected = select_outcome_match(
        origin.history,
        outcomes_by_agent,
        forecast,
        budget=budget,
    )
    return future_pass_rate_mae(
        selected,
        tuple(task.instance_id for task in origin.future),
        outcomes_by_agent,
    )


def _contrast_for_forecast(
    selector_id: str,
    origin: RepositoryOrigin,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    forecast: Mapping[str, float],
    baseline_loss: float,
    cluster_id: str,
    budget: int,
) -> ContrastRow:
    return ContrastRow(
        selector_id=selector_id,
        portfolio="wide",
        repository_id=origin.repository_id,
        repository_cluster_id=cluster_id,
        origin_id=origin.origin_id,
        difference=(
            _forecast_loss(origin, outcomes_by_agent, forecast, budget)
            - baseline_loss
        ),
    )


def _baseline_loss(
    origin: RepositoryOrigin,
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> float:
    return future_pass_rate_mae(
        tuple(task.instance_id for task in origin.history),
        tuple(task.instance_id for task in origin.future),
        outcomes_by_agent,
    )


def _with_portfolio(row: ContrastRow, portfolio: str) -> ContrastRow:
    return ContrastRow(
        selector_id=row.selector_id,
        portfolio=portfolio,
        repository_id=row.repository_id,
        repository_cluster_id=row.repository_cluster_id,
        origin_id=row.origin_id,
        difference=row.difference,
    )


def _nominate(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    random_reports: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    history_difference = float(
        summaries["wide"]["history_match"]["macro_repository_difference"]
    )
    assessments = {}
    for selector_id in (
        "cross_repository_drift_match",
        "local_trend_match",
    ):
        wide = summaries["wide"][selector_id]
        deep = summaries["deep"][selector_id]
        random_position = _bounded_number(
            _mapping(
                _mapping(
                    _mapping(random_reports, "wide"),
                    "candidate_positions",
                ),
                selector_id,
            )["candidate_better_than_random_midrank"],
            "candidate random midrank",
        )
        requirements = {
            "wide_at_most_minus_0_01": (
                float(wide["macro_repository_difference"]) <= -0.01
            ),
            "at_least_five_favorable_repositories": (
                int(wide["favorable_repository_count"]) >= 5
            ),
            "every_leave_one_repository_out_favorable": not bool(
                wide["leave_one_cluster_out_has_nonnegative_difference"]
            ),
            "deep_direction_favorable": (
                float(deep["macro_repository_difference"]) < 0.0
            ),
            "better_than_at_least_75_percent_random": random_position >= 0.75,
            "improves_history_match": (
                float(wide["macro_repository_difference"]) < history_difference
            ),
        }
        assessments[selector_id] = {
            "requirements": requirements,
            "all_requirements_met": all(requirements.values()),
        }
    eligible = tuple(
        selector_id
        for selector_id, assessment in assessments.items()
        if assessment["all_requirements_met"]
    )
    nominated = (
        min(
            eligible,
            key=lambda selector_id: (
                float(
                    summaries["wide"][selector_id][
                        "macro_repository_difference"
                    ]
                ),
                selector_id,
            ),
        )
        if eligible
        else None
    )
    return {
        "status": (
            "freeze_one_simple_candidate_for_independent_validation"
            if nominated is not None
            else "no_simple_cross_repository_route_warrants_paid_validation"
        ),
        "nominated_selector_id": nominated,
        "candidate_assessments": assessments,
        "production_promotion_allowed": False,
    }


def _agent_rates(
    task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> Mapping[str, float]:
    tasks = tuple(task_ids)
    if not tasks:
        raise ValueError("Agent rates require Tasks")
    rates = {}
    for agent_id, outcomes in sorted(outcomes_by_agent.items()):
        values = tuple(
            _binary_outcome(outcomes.get(task_id), agent_id, task_id)
            for task_id in tasks
        )
        rates[agent_id] = fsum(values) / len(values)
    if not rates:
        raise ValueError("Agent rates require an Agent panel")
    return rates


def _binary_outcome(value: object, agent_id: str, task_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
        raise ValueError(f"Agent {agent_id} has no binary outcome for {task_id}")
    return value


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def _bounded_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return result


def _number_tuple(value: object, name: str) -> tuple[float, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
    ):
        raise ValueError(f"{name} must be a nonempty array")
    result = tuple(_bounded_number(item, name) for item in value)
    if tuple(sorted(set(result))) != result:
        raise ValueError(f"{name} must be sorted and unique")
    return result


def _number_key(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _unique_strings(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be a nonempty string array")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must be unique")
    return result


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
        raise ValueError(f"{key} must be a positive integer")
    return item


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


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
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument(
        "--public-results",
        type=Path,
        default=DEFAULT_PUBLIC_RESULTS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    development_plan = load_development_plan(args.plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(source, "dataset_sha256"):
        raise RuntimeError("dataset digest does not match the public plan")
    committed_public_results = json.loads(
        args.public_results.read_text(encoding="utf-8")
    )
    if not isinstance(committed_public_results, dict):
        raise ValueError("committed public results must be an object")
    public_results_digest = committed_public_results.pop(
        "public_panel_results_digest",
        None,
    )
    if (
        canonical_digest(committed_public_results) != public_results_digest
        or public_results_digest
        != _mapping(development_plan, "source_results").get(
            "public_panel_results_digest"
        )
    ):
        raise ValueError("development plan does not bind valid public results")
    tasks = load_dataset_tasks(args.dataset)
    outcomes, _ = load_public_outcomes(
        args.result_dir,
        public_plan,
        tuple(task.instance_id for task in tasks),
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite development replay: {args.output}")
    result = run_development_replay(
        tasks,
        outcomes,
        development_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "nomination": result["nomination"],
                "development_results_digest": result[
                    "development_results_digest"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
