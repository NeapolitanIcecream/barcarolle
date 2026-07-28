#!/usr/bin/env python3
"""Replay fixed Selectors on pinned public SWE-bench resolution outcomes."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
from math import fsum, isfinite, sqrt
from pathlib import Path
import random
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    parse_utc_timestamp,
)
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "public-panel-results.json"


@dataclass(frozen=True)
class TaskMetadata:
    instance_id: str
    repository_id: str
    created_at: str
    difficulty: str
    problem_statement: str


@dataclass(frozen=True)
class RepositoryOrigin:
    repository_id: str
    origin_id: str
    history: tuple[TaskMetadata, ...]
    future: tuple[TaskMetadata, ...]


def load_public_panel_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("public panel plan must be a JSON object")
    if (
        payload.get("schema_version")
        != "barcarolle_public_multi_repository_replay_plan_v1"
    ):
        raise ValueError("public panel plan schema is unsupported")
    digest = payload.get("public_panel_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "public_panel_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("public panel plan digest does not match")
    return payload


def load_portfolio(path: Path = DEFAULT_PORTFOLIO) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("portfolio must be a JSON object")
    if payload.get("schema_version") != "barcarolle_repository_portfolio_v1":
        raise ValueError("portfolio schema is unsupported")
    digest = payload.get("portfolio_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "portfolio_digest"}
    )
    if digest != expected:
        raise ValueError("portfolio digest does not match")
    return payload


def build_repository_origins(
    tasks: Sequence[TaskMetadata],
    *,
    minimum_initial_history_tasks: int,
    future_block_tasks: int,
) -> Mapping[str, tuple[RepositoryOrigin, ...]]:
    """Build complete non-overlapping future blocks inside each repository."""
    if minimum_initial_history_tasks <= 0 or future_block_tasks <= 0:
        raise ValueError("history and future block sizes must be positive")
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    seen_instances: set[str] = set()
    for task in tasks:
        if (
            not task.instance_id
            or not task.repository_id
            or not task.difficulty
            or not task.problem_statement
        ):
            raise ValueError("Task metadata strings must not be empty")
        if task.instance_id in seen_instances:
            raise ValueError(f"duplicate Task instance: {task.instance_id}")
        seen_instances.add(task.instance_id)
        canonical_time = format_utc_timestamp(parse_utc_timestamp(task.created_at))
        tasks_by_repository[task.repository_id].append(
            TaskMetadata(
                task.instance_id,
                task.repository_id,
                canonical_time,
                task.difficulty,
                task.problem_statement,
            )
        )

    result: dict[str, tuple[RepositoryOrigin, ...]] = {}
    for repository_id, repository_tasks in sorted(tasks_by_repository.items()):
        ordered = tuple(
            sorted(
                repository_tasks,
                key=lambda task: (
                    parse_utc_timestamp(task.created_at),
                    task.instance_id,
                ),
            )
        )
        if len(ordered) < minimum_initial_history_tasks + future_block_tasks:
            continue
        initial_history = minimum_initial_history_tasks + (
            (len(ordered) - minimum_initial_history_tasks) % future_block_tasks
        )
        origins = []
        for future_start in range(
            initial_history,
            len(ordered),
            future_block_tasks,
        ):
            future = ordered[future_start : future_start + future_block_tasks]
            if len(future) != future_block_tasks:
                raise ValueError("repository Tasks do not form complete future blocks")
            origins.append(
                RepositoryOrigin(
                    repository_id=repository_id,
                    origin_id=f"{repository_id}:origin-{len(origins) + 1:03d}",
                    history=ordered[:future_start],
                    future=future,
                )
            )
        result[repository_id] = tuple(origins)
    return result


def official_binary_outcomes(
    task_denominator: Sequence[str],
    result_payload: Mapping[str, object],
) -> tuple[Mapping[str, int], Mapping[str, int]]:
    """Normalize the official resolved list against the pinned Task denominator."""
    expected_fields = {"resolved", "no_generation", "no_logs"}
    if set(result_payload) != expected_fields:
        raise ValueError("official result fields are unsupported")
    denominator = tuple(task_denominator)
    if (
        not denominator
        or len(denominator) != len(set(denominator))
        or any(not isinstance(item, str) or not item for item in denominator)
    ):
        raise ValueError("Task denominator must contain unique nonempty IDs")
    denominator_set = set(denominator)
    categories = {
        field: _string_set(result_payload.get(field), field)
        for field in sorted(expected_fields)
    }
    listed = set().union(*categories.values())
    if listed - denominator_set:
        raise ValueError("official result refers outside the Task denominator")
    if sum(len(values) for values in categories.values()) != len(listed):
        raise ValueError("official result categories overlap")
    outcomes = {
        task_id: int(task_id in categories["resolved"]) for task_id in denominator
    }
    diagnostics = {
        "resolved_count": len(categories["resolved"]),
        "no_generation_count": len(categories["no_generation"]),
        "no_logs_count": len(categories["no_logs"]),
        "ordinary_unresolved_count": len(denominator_set - listed),
    }
    return outcomes, diagnostics


def select_history_task_ids(
    selector_id: str,
    history: Sequence[TaskMetadata],
    budget: int,
) -> tuple[str, ...]:
    if budget <= 0 or budget > len(history):
        raise ValueError("selection budget must fit history")
    if selector_id == "full_history":
        return tuple(task.instance_id for task in history)
    if selector_id == "recency":
        return tuple(task.instance_id for task in reversed(history))[:budget]
    if selector_id == "difficulty_coverage":
        grouped: dict[str, deque[TaskMetadata]] = {}
        for task in history:
            grouped.setdefault(task.difficulty, deque()).append(task)
        active = deque(sorted(grouped))
        ordered = []
        while active:
            group = active.popleft()
            ordered.append(grouped[group].popleft())
            if grouped[group]:
                active.append(group)
        return tuple(task.instance_id for task in ordered[:budget])
    raise ValueError(f"unsupported public replay Selector: {selector_id}")


def future_pass_rate_mae(
    selected_task_ids: Sequence[str],
    future_task_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
) -> float:
    if not selected_task_ids or not future_task_ids or not outcomes_by_agent:
        raise ValueError("loss requires selected, future, and Agent evidence")
    selected = tuple(selected_task_ids)
    future = tuple(future_task_ids)
    losses = []
    for agent_id, outcomes in sorted(outcomes_by_agent.items()):
        required = set((*selected, *future))
        if set(outcomes) < required:
            raise ValueError(f"Agent {agent_id} does not cover required Tasks")
        if any(outcomes[task_id] not in (0, 1) for task_id in required):
            raise ValueError("public replay outcomes must be binary")
        selected_rate = fsum(outcomes[task_id] for task_id in selected) / len(selected)
        future_rate = fsum(outcomes[task_id] for task_id in future) / len(future)
        losses.append(abs(selected_rate - future_rate))
    return fsum(losses) / len(losses)


def run_public_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int]],
    plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the frozen fixed-rule, random, and permutation comparisons."""
    plan_portfolio = _mapping(plan, "portfolio")
    if portfolio.get("portfolio_digest") != _required_string(
        plan_portfolio,
        "portfolio_digest",
    ):
        raise ValueError("public panel plan does not bind the portfolio")
    rolling = _mapping(plan, "rolling_origin")
    minimum_history = _positive_integer(
        rolling,
        "minimum_initial_history_tasks",
    )
    future_block = _positive_integer(rolling, "future_block_tasks")
    budget = _positive_integer(rolling, "selection_budget_task_checks")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=minimum_history,
        future_block_tasks=future_block,
    )
    task_ids = tuple(task.instance_id for task in tasks)
    if any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values()):
        raise ValueError("every public Agent must cover the exact Task denominator")

    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    portfolio_repositories = {
        "wide": _string_tuple(plan_portfolio.get("wide_repository_ids"), "wide"),
        "deep": _string_tuple(plan_portfolio.get("deep_repository_ids"), "deep"),
    }
    selectors = tuple(
        _required_string(row, "selector_id")
        for row in _mapping_sequence(plan, "selectors")
        if row.get("selector_id") != "full_history"
    )
    aggregation = _mapping(plan, "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )

    contrast_rows: dict[tuple[str, str], tuple[ContrastRow, ...]] = {}
    summaries: dict[str, dict[str, Mapping[str, Any]]] = {}
    for portfolio_name, repository_ids in portfolio_repositories.items():
        summaries[portfolio_name] = {}
        for selector_id in selectors:
            rows = _contrast_rows(
                selector_id,
                portfolio_name,
                repository_ids,
                origins_by_repository,
                outcomes_by_agent,
                cluster_by_repository,
                budget,
            )
            contrast_rows[(portfolio_name, selector_id)] = rows
            summaries[portfolio_name][selector_id] = summarize_contrasts(
                rows,
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )

    random_config = _mapping(plan, "random_calibration")
    random_reports = {
        portfolio_name: random_calibration(
            repository_ids,
            origins_by_repository,
            outcomes_by_agent,
            budget=budget,
            draws=_positive_integer(random_config, "draws"),
            seed=_integer(random_config, "seed"),
            observed_summaries=summaries[portfolio_name],
        )
        for portfolio_name, repository_ids in portfolio_repositories.items()
    }
    null_config = _mapping(plan, "null_control")
    null_reports = _permutation_control(
        tasks,
        outcomes_by_agent,
        origins_by_repository,
        portfolio_repositories,
        cluster_by_repository,
        selectors,
        observed_summaries=summaries,
        budget=budget,
        permutations=_positive_integer(
            null_config,
            "within_repository_outcome_permutations",
        ),
        seed=_integer(null_config, "seed"),
    )
    decisions = {
        selector_id: _nomination_decision(
            summaries,
            null_reports,
            selector_id,
        )
        for selector_id in selectors
    }

    result: dict[str, Any] = {
        "schema_version": "barcarolle_public_multi_repository_replay_v1",
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "public_panel_plan_digest": plan.get("public_panel_plan_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "agent_outcome_diagnostics": dict(sorted(outcome_diagnostics.items())),
        "origin_counts": {
            repository_id: len(origins)
            for repository_id, origins in sorted(origins_by_repository.items())
        },
        "summaries": summaries,
        "random_calibration": random_reports,
        "permutation_control": null_reports,
        "decisions": decisions,
        "claim_boundary": (
            "Public official resolution outcomes and projected Check maturity "
            "support counterfactual exploratory method screening only. They "
            "cannot promote a Runner default or establish strict-prospective "
            "Agent, repository, or source validity."
        ),
    }
    result["public_panel_results_digest"] = canonical_digest(result)
    return result


def _contrast_rows(
    selector_id: str,
    portfolio_name: str,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    cluster_by_repository: Mapping[str, str],
    budget: int,
) -> tuple[ContrastRow, ...]:
    rows = []
    for repository_id in repository_ids:
        origins = origins_by_repository.get(repository_id)
        if not origins:
            raise ValueError(
                f"portfolio repository has no complete Origins: {repository_id}"
            )
        for origin in origins:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline_loss = future_pass_rate_mae(
                history_ids,
                future_ids,
                outcomes_by_agent,
            )
            selected_ids = select_history_task_ids(
                selector_id,
                origin.history,
                budget,
            )
            selector_loss = future_pass_rate_mae(
                selected_ids,
                future_ids,
                outcomes_by_agent,
            )
            rows.append(
                ContrastRow(
                    selector_id,
                    portfolio_name,
                    repository_id,
                    cluster_by_repository[repository_id],
                    origin.origin_id,
                    selector_loss - baseline_loss,
                )
            )
    return tuple(rows)


def random_calibration(
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    budget: int,
    draws: int,
    seed: int,
    observed_summaries: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    generator = random.Random(f"{seed}:{','.join(repository_ids)}")
    baseline_loss_by_origin = {
        origin.origin_id: future_pass_rate_mae(
            tuple(task.instance_id for task in origin.history),
            tuple(task.instance_id for task in origin.future),
            outcomes_by_agent,
        )
        for repository_id in repository_ids
        for origin in origins_by_repository[repository_id]
    }
    macro_draws = []
    for _ in range(draws):
        repository_differences = []
        for repository_id in repository_ids:
            origin_differences = []
            for origin in origins_by_repository[repository_id]:
                selected = generator.sample(
                    tuple(task.instance_id for task in origin.history),
                    budget,
                )
                random_loss = future_pass_rate_mae(
                    selected,
                    tuple(task.instance_id for task in origin.future),
                    outcomes_by_agent,
                )
                origin_differences.append(
                    random_loss - baseline_loss_by_origin[origin.origin_id]
                )
            repository_differences.append(_mean(origin_differences))
        macro_draws.append(_mean(repository_differences))
    macro_draws.sort()
    standard_deviation = _population_standard_deviation(macro_draws)
    candidate_positions = {}
    for selector_id, summary in sorted(observed_summaries.items()):
        candidate = float(summary["macro_repository_difference"])
        better = sum(value > candidate for value in macro_draws)
        equal = sum(value == candidate for value in macro_draws)
        candidate_positions[selector_id] = {
            "candidate_macro_repository_difference": candidate,
            "candidate_better_than_random_midrank": (
                better + 0.5 * equal
            )
            / draws,
            "random_as_good_or_better_rate": sum(
                value <= candidate for value in macro_draws
            )
            / draws,
        }
    return {
        "draw_count": draws,
        "mean_macro_repository_difference": _mean(macro_draws),
        "population_standard_deviation": standard_deviation,
        "mean_monte_carlo_standard_error": standard_deviation / sqrt(draws),
        "quantiles": {
            "0.025": _empirical_quantile(macro_draws, 0.025),
            "0.5": _empirical_quantile(macro_draws, 0.5),
            "0.975": _empirical_quantile(macro_draws, 0.975),
        },
        "candidate_positions": candidate_positions,
    }


def _permutation_control(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    portfolio_repositories: Mapping[str, Sequence[str]],
    cluster_by_repository: Mapping[str, str],
    selectors: Sequence[str],
    *,
    observed_summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    budget: int,
    permutations: int,
    seed: int,
) -> Mapping[str, Mapping[str, Any]]:
    task_ids_by_repository: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        task_ids_by_repository[task.repository_id].append(task.instance_id)
    agent_ids = tuple(sorted(outcomes_by_agent))
    joint_outcomes_by_repository = {
        repository_id: tuple(
            tuple(outcomes_by_agent[agent_id][task_id] for agent_id in agent_ids)
            for task_id in task_ids
        )
        for repository_id, task_ids in task_ids_by_repository.items()
    }
    values: dict[tuple[str, str], list[float]] = {
        (portfolio_name, selector_id): []
        for portfolio_name in portfolio_repositories
        for selector_id in selectors
    }
    generator = random.Random(seed)
    for _ in range(permutations):
        permuted_by_agent = {agent_id: {} for agent_id in agent_ids}
        for repository_id, task_ids in sorted(task_ids_by_repository.items()):
            vectors = list(joint_outcomes_by_repository[repository_id])
            generator.shuffle(vectors)
            for task_id, vector in zip(task_ids, vectors, strict=True):
                for index, agent_id in enumerate(agent_ids):
                    permuted_by_agent[agent_id][task_id] = vector[index]
        for portfolio_name, repository_ids in portfolio_repositories.items():
            for selector_id in selectors:
                rows = _contrast_rows(
                    selector_id,
                    portfolio_name,
                    repository_ids,
                    origins_by_repository,
                    permuted_by_agent,
                    cluster_by_repository,
                    budget,
                )
                repository_values: dict[str, list[float]] = defaultdict(list)
                for row in rows:
                    repository_values[row.repository_id].append(row.difference)
                values[(portfolio_name, selector_id)].append(
                    _mean(
                        tuple(
                            _mean(repository_values[repository_id])
                            for repository_id in sorted(repository_values)
                        )
                    )
                )
    reports: dict[str, dict[str, Any]] = {}
    for portfolio_name in portfolio_repositories:
        reports[portfolio_name] = {}
        for selector_id in selectors:
            null_values = sorted(values[(portfolio_name, selector_id)])
            observed = float(
                observed_summaries[portfolio_name][selector_id][
                    "macro_repository_difference"
                ]
            )
            reports[portfolio_name][selector_id] = {
                "permutation_count": permutations,
                "null_mean_macro_repository_difference": _mean(null_values),
                "null_quantiles": {
                    "0.025": _empirical_quantile(null_values, 0.025),
                    "0.5": _empirical_quantile(null_values, 0.5),
                    "0.975": _empirical_quantile(null_values, 0.975),
                },
                "observed_macro_repository_difference": observed,
                "null_as_good_or_better_rate": sum(
                    value <= observed for value in null_values
                )
                / permutations,
            }
    return reports


def _nomination_decision(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    null_reports: Mapping[str, Mapping[str, Any]],
    selector_id: str,
) -> Mapping[str, Any]:
    wide = summaries["wide"][selector_id]
    deep = summaries["deep"][selector_id]
    null_wide = _mapping(_mapping(null_reports, "wide"), selector_id)
    nominated = (
        float(wide["macro_repository_difference"]) < 0.0
        and not bool(wide["leave_one_cluster_out_has_nonnegative_difference"])
        and _number(
            null_wide["null_as_good_or_better_rate"],
            "null_as_good_or_better_rate",
        )
        < 0.1
        and float(deep["macro_repository_difference"]) < 0.0
    )
    return {
        "status": (
            "fixed_route_nominated_for_later_confirmation"
            if nominated
            else "no_exploratory_nomination"
        ),
        "wide_direction_favorable": float(wide["macro_repository_difference"]) < 0.0,
        "wide_leave_one_cluster_out_all_favorable": not bool(
            wide["leave_one_cluster_out_has_nonnegative_difference"]
        ),
        "wide_permutation_rate_below_0_10": _number(
            null_wide["null_as_good_or_better_rate"],
            "null_as_good_or_better_rate",
        )
        < 0.1,
        "deep_direction_favorable": float(deep["macro_repository_difference"]) < 0.0,
        "promotion_allowed": False,
    }


def load_dataset_tasks(path: Path) -> tuple[TaskMetadata, ...]:
    # The extraction environment owns this optional dependency.
    import pyarrow.parquet as parquet

    return tuple(
        TaskMetadata(
            instance_id=row["instance_id"],
            repository_id=row["repo"],
            created_at=row["created_at"],
            difficulty=row["difficulty"],
            problem_statement=row["problem_statement"],
        )
        for row in parquet.read_table(
            path,
            columns=[
                "instance_id",
                "repo",
                "created_at",
                "difficulty",
                "problem_statement",
            ],
        ).to_pylist()
    )


def load_public_outcomes(
    result_dir: Path,
    plan: Mapping[str, object],
    task_ids: Sequence[str],
) -> tuple[Mapping[str, Mapping[str, int]], Mapping[str, Mapping[str, int]]]:
    outcomes = {}
    diagnostics = {}
    for agent in _mapping_sequence(plan, "agent_panel"):
        agent_id = _required_string(agent, "agent_id")
        submission = _required_string(agent, "submission")
        path = result_dir / f"{submission}.json"
        raw = path.read_bytes()
        if _git_blob_sha(raw) != _required_string(agent, "result_blob_sha"):
            raise ValueError(f"public result blob does not match plan: {submission}")
        payload = json.loads(raw)
        if not isinstance(payload, Mapping):
            raise ValueError("public result must be a JSON object")
        agent_outcomes, agent_diagnostics = official_binary_outcomes(task_ids, payload)
        outcomes[agent_id] = agent_outcomes
        diagnostics[agent_id] = agent_diagnostics
    return outcomes, diagnostics


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
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
        raise ValueError(f"{key} must be a positive integer")
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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_public_panel_plan(args.plan)
    portfolio = load_portfolio(args.portfolio)
    source = _mapping(plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(source, "dataset_sha256"):
        raise RuntimeError("dataset digest does not match public panel plan")
    tasks = load_dataset_tasks(args.dataset)
    outcomes, diagnostics = load_public_outcomes(
        args.result_dir,
        plan,
        tuple(task.instance_id for task in tasks),
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite public replay: {args.output}")
    result = run_public_replay(tasks, outcomes, diagnostics, plan, portfolio)
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decisions": result["decisions"],
                "public_panel_results_digest": result[
                    "public_panel_results_digest"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


def _string_set(value: object, field: str) -> set[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{field} must be an array of nonempty strings")
    items = tuple(value)
    if len(items) != len(set(items)):
        raise ValueError(f"{field} must not contain duplicates")
    return set(items)


if __name__ == "__main__":
    raise SystemExit(main())
