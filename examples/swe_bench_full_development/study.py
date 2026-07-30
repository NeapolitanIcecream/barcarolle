#!/usr/bin/env python3
"""Run an outcome-open SWE-bench Full Selector development portfolio."""

from __future__ import annotations

# The reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite
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
from examples.multi_repository_study.agent_invariant import (  # noqa: E402
    fit_cutoff_repository_equal_markov,
    forecast_difficulty_markov,
    select_state_histogram_match,
)
from examples.multi_repository_study.public_replay import TaskMetadata  # noqa: E402
from examples.multi_swe_research.suitability_audit import (  # noqa: E402
    _bootstrap_interval,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    adanormalhedge_forecast,
    create_adanormalhedge_state,
    response_expert_forecasts,
    shared_bocpd_forecast,
    solve_exact_l1_assembly,
    update_adanormalhedge,
)
from examples.swe_bench_full_transfer.study import (  # noqa: E402
    _origins_for_horizon,
    load_full_inputs,
    load_plan as load_source_plan,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-development"
)
DEFAULT_MEMBERSHIP_A = DEFAULT_OUTPUT_DIRECTORY / "memberships-a.json"
DEFAULT_MEMBERSHIP_B = DEFAULT_OUTPUT_DIRECTORY / "memberships-b.json"
DEFAULT_RESULT_A = DEFAULT_OUTPUT_DIRECTORY / "result-a.json"
DEFAULT_RESULT_B = DEFAULT_OUTPUT_DIRECTORY / "result-b.json"
DEFAULT_SUMMARY = HERE / "evidence" / "summary.json"

PLAN_SCHEMA = "barcarolle_swe_bench_full_development_plan_v1"
MEMBERSHIP_SCHEMA = "barcarolle_swe_bench_full_memberships_v1"
RESULT_SCHEMA = "barcarolle_swe_bench_full_development_result_v1"
SUMMARY_SCHEMA = "barcarolle_swe_bench_full_development_summary_v1"
PLAN_DIGEST_KEY = "plan_digest"
MEMBERSHIP_DIGEST_KEY = "membership_digest"
RESULT_DIGEST_KEY = "result_digest"
SUMMARY_DIGEST_KEY = "summary_digest"

CANDIDATE_IDS = (
    "ordinary_recency",
    "stationary_response_match",
    "ALG-010",
    "ALG-015U",
    "ALG-016U",
)
ALGORITHM_IDS = ("full_history", *CANDIDATE_IDS)


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and validate the frozen development contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop(PLAN_DIGEST_KEY, None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Full development plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("Full development plan digest does not match")
    payload[PLAN_DIGEST_KEY] = digest

    candidates = tuple(
        _required_string(row, "selector_id")
        for row in _mapping_sequence(payload, "candidates")
    )
    if candidates != CANDIDATE_IDS:
        raise ValueError("Full development candidate portfolio changed")
    frame = _mapping(payload, "frame")
    if (
        _positive_integer(frame, "selection_budget_tasks") != 10
        or _positive_integer(frame, "minimum_initial_history_tasks") != 20
        or tuple(frame.get("horizons", ())) != (5, 10)
    ):
        raise ValueError("Full development frame changed")
    authority = _mapping(payload, "authority")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "sealed_swe_bench_verified_agent_reads",
        "generator_development",
        "core_schema_changes",
    ):
        if authority.get(key) not in (0, False):
            raise ValueError("Full development authority changed")

    for binding in _mapping(payload, "bound_artifacts").values():
        if not isinstance(binding, Mapping):
            raise ValueError("bound artifact must be an object")
        bound_path = REPOSITORY_ROOT / _required_string(binding, "path")
        if _file_sha256(bound_path) != _required_string(binding, "file_sha256"):
            raise ValueError(f"bound artifact changed: {bound_path}")
        logical_key = binding.get("logical_digest_key")
        logical_digest = binding.get("logical_digest")
        if logical_key is not None:
            bound_payload = _load_mapping(bound_path)
            if (
                not isinstance(logical_key, str)
                or not isinstance(logical_digest, str)
                or bound_payload.get(logical_key) != logical_digest
            ):
                raise ValueError(f"bound logical digest changed: {bound_path}")
    implementation_sha = _required_string(
        _mapping(payload, "implementation"),
        "study_file_sha256",
    )
    if _file_sha256(Path(__file__)) != implementation_sha:
        raise ValueError("Full development implementation changed")
    return payload


def select_response_memberships(
    history: Any,
    ada_forecast: Any,
    *,
    horizon: int,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> Mapping[int, Mapping[str, tuple[int, ...]]]:
    """Select response-based memberships while holding out each target Agent."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    adaptive = np.asarray(ada_forecast, dtype=np.float64)
    order = tuple(created_order)
    if (
        values.ndim != 2
        or values.shape[1] < 2
        or values.shape[0] != len(order)
        or adaptive.shape != (values.shape[1],)
        or isinstance(horizon, bool)
        or horizon <= 0
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(values)
        or not np.all((values == 0.0) | (values == 1.0))
        or not np.all(np.isfinite(adaptive))
        or np.any(adaptive < 0.0)
        or np.any(adaptive > 1.0)
    ):
        raise ValueError("response membership inputs are invalid")

    result = {}
    recency = tuple(range(len(values) - budget, len(values)))
    for held_out in range(values.shape[1]):
        visible = tuple(
            index for index in range(values.shape[1]) if index != held_out
        )
        visible_history = values[:, list(visible)]
        stationary = solve_exact_l1_assembly(
            visible_history,
            visible_history.mean(axis=0),
            budget=budget,
            created_order=order,
        )
        adaptive_selection = solve_exact_l1_assembly(
            visible_history,
            adaptive[list(visible)],
            budget=budget,
            created_order=order,
        )
        change_point = shared_bocpd_forecast(
            visible_history,
            horizon=horizon,
        )
        change_point_selection = solve_exact_l1_assembly(
            visible_history,
            change_point.mixture,
            budget=budget,
            created_order=order,
        )
        result[held_out] = {
            "ordinary_recency": recency,
            "stationary_response_match": stationary.indices,
            "ALG-015U": adaptive_selection.indices,
            "ALG-016U": change_point_selection.indices,
        }
    return result


def select_difficulty_markov_membership(
    history: Sequence[TaskMetadata],
    *,
    target_agent_id: str,
    agent_ids: Sequence[str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    target_repository_id: str,
    repository_ids: Sequence[str],
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    horizon: int,
    budget: int,
    state_count: int,
    cell_prior_mass: float,
    local_prior_strength: float,
) -> tuple[str, ...]:
    """Run ALG-010 without reading the target Agent's outcome column."""
    visible_outcomes = {
        agent_id: outcomes_by_agent[agent_id]
        for agent_id in agent_ids
        if agent_id != target_agent_id
    }
    if target_agent_id not in agent_ids or len(visible_outcomes) < 1:
        raise ValueError("difficulty Markov target Agent is invalid")
    training_repository_ids = tuple(
        repository_id
        for repository_id in repository_ids
        if repository_id != target_repository_id
    )
    transition, _ = fit_cutoff_repository_equal_markov(
        training_repository_ids,
        tasks_by_repository,
        visible_outcomes,
        cutoff=history[-1].created_at,
        state_count=state_count,
        cell_prior_mass=cell_prior_mass,
    )
    forecast = forecast_difficulty_markov(
        history,
        visible_outcomes,
        transition,
        state_count=state_count,
        horizon=horizon,
        local_prior_strength=local_prior_strength,
    )
    return select_state_histogram_match(
        history,
        visible_outcomes,
        forecast,
        state_count=state_count,
        budget=budget,
    )


def materialize_portfolio(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    identities: Mapping[str, object],
    plan: Mapping[str, object],
    source_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Materialize every membership before target-Agent future scoring."""
    import numpy as np

    agent_ids = tuple(sorted(outcomes_by_agent))
    if len(agent_ids) != 11:
        raise ValueError("Full development Agent panel changed")
    budget = _positive_integer(_mapping(plan, "frame"), "selection_budget_tasks")
    difficulty = _mapping(plan, "difficulty_markov")
    state_count = _positive_integer(difficulty, "state_count")
    cell_prior_mass = _finite_number(
        difficulty.get("cell_prior_mass"),
        "difficulty Markov cell prior mass",
    )
    local_prior_strength = _finite_number(
        difficulty.get("local_prior_strength"),
        "difficulty Markov local prior strength",
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

    horizon_payloads = {}
    for horizon in (5, 10):
        origins_by_repository, repository_ids = _origins_for_horizon(
            tasks,
            source_plan,
            horizon,
        )
        rows = []
        for position, repository_id in enumerate(repository_ids, start=1):
            state = create_adanormalhedge_state(len(agent_ids))
            previous_experts = None
            previous_history_count = None
            for origin in origins_by_repository[repository_id]:
                history_ids = tuple(
                    task.instance_id for task in origin.history
                )
                history = np.asarray(
                    [
                        [
                            outcomes_by_agent[agent_id][task_id]
                            for agent_id in agent_ids
                        ]
                        for task_id in history_ids
                    ],
                    dtype=np.float64,
                )
                if previous_experts is not None:
                    if (
                        previous_history_count is None
                        or len(history) - previous_history_count != horizon
                    ):
                        raise ValueError("prequential history blocks changed")
                    observed_previous_block = history[-horizon:].mean(axis=0)
                    update_adanormalhedge(
                        state,
                        previous_experts,
                        observed_previous_block,
                    )
                experts = response_expert_forecasts(history, horizon=horizon)
                ada_forecast, _ = adanormalhedge_forecast(state, experts)
                created_order = tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                )
                response_memberships = select_response_memberships(
                    history,
                    ada_forecast,
                    horizon=horizon,
                    budget=budget,
                    created_order=created_order,
                )
                for held_out, target_agent_id in enumerate(agent_ids):
                    memberships = {
                        selector_id: tuple(
                            history_ids[index]
                            for index in indices
                        )
                        for selector_id, indices in response_memberships[
                            held_out
                        ].items()
                    }
                    memberships["ALG-010"] = (
                        select_difficulty_markov_membership(
                            origin.history,
                            target_agent_id=target_agent_id,
                            agent_ids=agent_ids,
                            outcomes_by_agent=outcomes_by_agent,
                            target_repository_id=repository_id,
                            repository_ids=repository_ids,
                            tasks_by_repository=tasks_by_repository,
                            horizon=horizon,
                            budget=budget,
                            state_count=state_count,
                            cell_prior_mass=cell_prior_mass,
                            local_prior_strength=local_prior_strength,
                        )
                    )
                    if tuple(memberships) != (
                        "ordinary_recency",
                        "stationary_response_match",
                        "ALG-015U",
                        "ALG-016U",
                        "ALG-010",
                    ):
                        raise AssertionError("membership portfolio changed")
                    rows.append(
                        {
                            "repository_id": repository_id,
                            "origin_id": origin.origin_id,
                            "target_agent_id": target_agent_id,
                            "history_task_count": len(history_ids),
                            "memberships": {
                                selector_id: memberships[selector_id]
                                for selector_id in CANDIDATE_IDS
                            },
                        }
                    )
                previous_experts = experts
                previous_history_count = len(history)
            print(
                f"materialized H{horizon} repository "
                f"{position}/{len(repository_ids)} {repository_id}",
                flush=True,
            )
        expected_rows = sum(
            len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        ) * len(agent_ids)
        if len(rows) != expected_rows:
            raise RuntimeError("Full development membership row count changed")
        horizon_payloads[str(horizon)] = {
            "repository_ids": repository_ids,
            "origin_count": expected_rows // len(agent_ids),
            "target_row_count": len(rows),
            "rows": tuple(rows),
            "rows_digest": canonical_digest(rows),
        }
    artifact: dict[str, Any] = {
        "schema_version": MEMBERSHIP_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "input_identities": dict(identities),
        "candidate_ids": CANDIDATE_IDS,
        "horizons": horizon_payloads,
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
        },
    }
    artifact[MEMBERSHIP_DIGEST_KEY] = canonical_digest(artifact)
    return artifact


def score_portfolio(
    membership: Mapping[str, object],
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    identities: Mapping[str, object],
    audit_result: Mapping[str, object],
    plan: Mapping[str, object],
    source_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Score frozen memberships with direct future pass-rate MAE."""
    _validate_self_digest(
        membership,
        schema=MEMBERSHIP_SCHEMA,
        digest_key=MEMBERSHIP_DIGEST_KEY,
    )
    if (
        membership.get("plan_digest") != plan.get("plan_digest")
        or canonical_digest(_mapping(membership, "input_identities"))
        != canonical_digest(identities)
        or _unique_string_tuple(
            membership.get("candidate_ids"),
            "candidate IDs",
        )
        != CANDIDATE_IDS
    ):
        raise ValueError("membership artifact does not bind scoring inputs")
    agent_ids = tuple(sorted(outcomes_by_agent))
    horizon_payloads = {}
    evaluation = _mapping(plan, "evaluation")
    bootstrap_resamples = _positive_integer(
        evaluation,
        "repository_bootstrap_resamples",
    )
    bootstrap_seed = _positive_integer(evaluation, "repository_bootstrap_seed")
    for horizon in (5, 10):
        origins_by_repository, repository_ids = _origins_for_horizon(
            tasks,
            source_plan,
            horizon,
        )
        origin_lookup = {
            origin.origin_id: origin
            for repository_id in repository_ids
            for origin in origins_by_repository[repository_id]
        }
        membership_horizon = _mapping(
            _mapping(membership, "horizons"),
            str(horizon),
        )
        score_rows = []
        for row in _mapping_sequence(membership_horizon, "rows"):
            repository_id = _required_string(row, "repository_id")
            origin_id = _required_string(row, "origin_id")
            target_agent_id = _required_string(row, "target_agent_id")
            origin = origin_lookup.get(origin_id)
            if (
                origin is None
                or origin.repository_id != repository_id
                or target_agent_id not in outcomes_by_agent
            ):
                raise ValueError("membership row identity changed")
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            future_rate = _mean(
                tuple(
                    float(outcomes_by_agent[target_agent_id][task_id])
                    for task_id in future_ids
                )
            )
            losses = {
                "full_history": abs(
                    _mean(
                        tuple(
                            float(outcomes_by_agent[target_agent_id][task_id])
                            for task_id in history_ids
                        )
                    )
                    - future_rate
                )
            }
            memberships = _mapping(row, "memberships")
            history_set = set(history_ids)
            for selector_id in CANDIDATE_IDS:
                selected = _unique_string_tuple(
                    memberships.get(selector_id),
                    f"{selector_id} membership",
                )
                if len(selected) != 10 or not set(selected) <= history_set:
                    raise ValueError("membership is not an exact history subset")
                selected_rate = _mean(
                    tuple(
                        float(outcomes_by_agent[target_agent_id][task_id])
                        for task_id in selected
                    )
                )
                losses[selector_id] = abs(selected_rate - future_rate)
            score_rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin_id,
                    "target_agent_id": target_agent_id,
                    "losses": losses,
                }
            )
        random_differences = _number_tuple(
            _mapping(
                _mapping(_mapping(audit_result, "horizons"), str(horizon)),
                "random_calibration",
            ).get("macro_differences"),
            "random macro differences",
        )
        horizon_payloads[str(horizon)] = summarize_horizon(
            score_rows,
            repository_ids=repository_ids,
            agent_ids=agent_ids,
            random_differences=random_differences,
            bootstrap_resamples=bootstrap_resamples,
            bootstrap_seed=bootstrap_seed + horizon,
        )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "membership_digest": membership.get("membership_digest"),
        "input_identities": dict(identities),
        "horizons": horizon_payloads,
        "decision": _development_decision(horizon_payloads),
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result[RESULT_DIGEST_KEY] = canonical_digest(result)
    return result


def summarize_horizon(
    score_rows: Sequence[Mapping[str, Any]],
    *,
    repository_ids: Sequence[str],
    agent_ids: Sequence[str],
    random_differences: Sequence[float],
    bootstrap_resamples: int,
    bootstrap_seed: int,
) -> Mapping[str, Any]:
    """Aggregate Agents and Origins within repository, then repositories."""
    rows = tuple(score_rows)
    by_repository: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_agent_repository: dict[
        tuple[str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        agent_id = _required_string(row, "target_agent_id")
        by_repository[repository_id].append(row)
        by_agent_repository[(agent_id, repository_id)].append(row)
    repository_rows = []
    for repository_id in repository_ids:
        source_rows = by_repository[repository_id]
        if not source_rows:
            raise ValueError("repository has no score rows")
        mae = {
            algorithm_id: _mean(
                tuple(
                    _finite_number(
                        _mapping(row, "losses").get(algorithm_id),
                        f"{algorithm_id} loss",
                    )
                    for row in source_rows
                )
            )
            for algorithm_id in ALGORITHM_IDS
        }
        repository_rows.append(
            {
                "repository_id": repository_id,
                "mae": mae,
                "candidate_minus_full": {
                    candidate_id: mae[candidate_id] - mae["full_history"]
                    for candidate_id in CANDIDATE_IDS
                },
            }
        )
    macro_mae = {
        algorithm_id: _mean(
            tuple(
                _finite_number(
                    _mapping(row, "mae").get(algorithm_id),
                    f"{algorithm_id} repository MAE",
                )
                for row in repository_rows
            )
        )
        for algorithm_id in ALGORITHM_IDS
    }
    agent_rows = []
    for agent_id in agent_ids:
        repository_mae = {}
        for repository_id in repository_ids:
            source_rows = by_agent_repository[(agent_id, repository_id)]
            if not source_rows:
                raise ValueError("Agent-repository cell has no score rows")
            repository_mae[repository_id] = {
                algorithm_id: _mean(
                    tuple(
                        _finite_number(
                            _mapping(row, "losses").get(algorithm_id),
                            f"{algorithm_id} loss",
                        )
                        for row in source_rows
                    )
                )
                for algorithm_id in ALGORITHM_IDS
            }
        agent_macro = {
            algorithm_id: _mean(
                tuple(
                    repository_mae[repository_id][algorithm_id]
                    for repository_id in repository_ids
                )
            )
            for algorithm_id in ALGORITHM_IDS
        }
        agent_rows.append(
            {
                "target_agent_id": agent_id,
                "mae": agent_macro,
                "candidate_minus_full": {
                    candidate_id: (
                        agent_macro[candidate_id] - agent_macro["full_history"]
                    )
                    for candidate_id in CANDIDATE_IDS
                },
            }
        )

    candidates = {}
    for candidate_id in CANDIDATE_IDS:
        repository_differences = tuple(
            _finite_number(
                _mapping(row, "candidate_minus_full").get(candidate_id),
                f"{candidate_id} repository difference",
            )
            for row in repository_rows
        )
        agent_differences = tuple(
            _finite_number(
                _mapping(row, "candidate_minus_full").get(candidate_id),
                f"{candidate_id} Agent difference",
            )
            for row in agent_rows
        )
        difference = macro_mae[candidate_id] - macro_mae["full_history"]
        bootstrap = _bootstrap_interval(
            repository_differences,
            resamples=bootstrap_resamples,
            seed=bootstrap_seed,
        )
        better = sum(value > difference for value in random_differences)
        equal = sum(value == difference for value in random_differences)
        candidates[candidate_id] = {
            "mae": macro_mae[candidate_id],
            "candidate_minus_full": difference,
            "repository_bootstrap_interval_95": {
                "lower": bootstrap["lower"],
                "upper": bootstrap["upper"],
            },
            "favorable_repository_count": sum(
                value < 0.0 for value in repository_differences
            ),
            "favorable_target_agent_count": sum(
                value < 0.0 for value in agent_differences
            ),
            "random_midrank": (better + 0.5 * equal)
            / len(random_differences),
        }
    return {
        "repository_count": len(repository_ids),
        "origin_count": len(rows) // len(agent_ids),
        "target_agent_count": len(agent_ids),
        "mae": macro_mae,
        "candidates": candidates,
        "repository_rows": tuple(repository_rows),
        "target_agent_rows": tuple(agent_rows),
        "score_rows_digest": canonical_digest(rows),
        "score_rows": rows,
    }


def build_summary(
    membership_a: Mapping[str, object],
    result_a: Mapping[str, object],
    membership_b: Mapping[str, object],
    result_b: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Build compact committed evidence from two identical executions."""
    for membership in (membership_a, membership_b):
        _validate_self_digest(
            membership,
            schema=MEMBERSHIP_SCHEMA,
            digest_key=MEMBERSHIP_DIGEST_KEY,
        )
    for result in (result_a, result_b):
        _validate_self_digest(
            result,
            schema=RESULT_SCHEMA,
            digest_key=RESULT_DIGEST_KEY,
        )
    memberships_identical = canonical_json(membership_a) == canonical_json(
        membership_b
    )
    results_identical = canonical_json(result_a) == canonical_json(result_b)
    if not memberships_identical or not results_identical:
        raise ValueError("Full development reproduction is not identical")
    if (
        membership_a.get("plan_digest") != plan.get("plan_digest")
        or result_a.get("plan_digest") != plan.get("plan_digest")
        or result_a.get("membership_digest")
        != membership_a.get("membership_digest")
    ):
        raise ValueError("Full development summary bindings changed")

    compact_horizons = {}
    for horizon, payload in sorted(_mapping(result_a, "horizons").items()):
        compact_horizons[horizon] = {
            key: payload.get(key)
            for key in (
                "repository_count",
                "origin_count",
                "target_agent_count",
                "mae",
                "candidates",
                "repository_rows",
                "target_agent_rows",
                "score_rows_digest",
            )
        }
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "input_identities": dict(_mapping(result_a, "input_identities")),
        "reproduction": {
            "memberships_byte_identical": memberships_identical,
            "results_byte_identical": results_identical,
            "membership_digest": membership_a.get("membership_digest"),
            "result_digest": result_a.get("result_digest"),
        },
        "horizons": compact_horizons,
        "decision": dict(_mapping(result_a, "decision")),
        "resource_use": dict(_mapping(result_a, "resource_use")),
        "claim_boundary": plan.get("claim_boundary"),
    }
    summary[SUMMARY_DIGEST_KEY] = canonical_digest(summary)
    return summary


def run_once(
    *,
    plan_path: Path,
    membership_output: Path,
    result_output: Path,
) -> None:
    """Materialize and score one deterministic development execution."""
    plan = load_plan(plan_path)
    source_plan, tasks, outcomes, identities, audit_result = _load_inputs(plan)
    membership = materialize_portfolio(
        tasks,
        outcomes,
        identities,
        plan,
        source_plan,
    )
    _write_json(membership_output, membership)
    result = score_portfolio(
        membership,
        tasks,
        outcomes,
        identities,
        audit_result,
        plan,
        source_plan,
    )
    _write_json(result_output, result)


def _load_inputs(
    plan: Mapping[str, object],
) -> tuple[
    Mapping[str, Any],
    tuple[TaskMetadata, ...],
    Mapping[str, Mapping[str, int]],
    Mapping[str, object],
    Mapping[str, Any],
]:
    bindings = _mapping(plan, "bound_artifacts")
    source_binding = _mapping(bindings, "source_plan")
    source_plan = load_source_plan(
        REPOSITORY_ROOT / _required_string(source_binding, "path")
    )
    source = _mapping(plan, "source")
    tasks, outcomes, _, _, identities = load_full_inputs(
        plan=source_plan,
        dataset_path=REPOSITORY_ROOT
        / _required_string(source, "dataset_path"),
        result_directory=REPOSITORY_ROOT
        / _required_string(source, "result_directory"),
    )
    if (
        identities.get("normalized_outcome_matrix_digest")
        != source.get("normalized_outcome_matrix_digest")
    ):
        raise ValueError("Full development outcome matrix changed")
    audit_binding = _mapping(bindings, "suitability_result")
    audit_result = _load_mapping(
        REPOSITORY_ROOT / _required_string(audit_binding, "path")
    )
    _validate_self_digest(
        audit_result,
        schema="barcarolle_swe_bench_full_suitability_result_v1",
        digest_key="suitability_result_digest",
    )
    if (
        audit_result.get("plan_digest") != source_plan.get("plan_digest")
        or canonical_digest(_mapping(audit_result, "identities"))
        != canonical_digest(identities)
    ):
        raise ValueError("Full development suitability evidence changed")
    return source_plan, tasks, outcomes, identities, audit_result


def _development_decision(
    horizons: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    best_by_horizon = {}
    for horizon, payload in sorted(horizons.items()):
        mae = _mapping(payload, "mae")
        best_by_horizon[horizon] = min(
            CANDIDATE_IDS,
            key=lambda candidate_id: (
                _finite_number(mae.get(candidate_id), "candidate MAE"),
                candidate_id,
            ),
        )
    better_both = tuple(
        candidate_id
        for candidate_id in CANDIDATE_IDS
        if all(
            _finite_number(
                _mapping(
                    _mapping(payload, "candidates"),
                    candidate_id,
                ).get("candidate_minus_full"),
                "candidate difference",
            )
            < 0.0
            for payload in horizons.values()
        )
    )
    return {
        "best_candidate_by_horizon": best_by_horizon,
        "candidates_better_than_full_at_both_horizons": better_both,
        "selector_nominated": False,
        "production_promotion_allowed": False,
        "interpretation": (
            "Outcome-open Full development evidence may retain or discard "
            "mechanisms; it cannot independently confirm the selected winner."
        ),
    }


def _validate_self_digest(
    payload: Mapping[str, object],
    *,
    schema: str,
    digest_key: str,
) -> None:
    if payload.get("schema_version") != schema:
        raise ValueError("artifact schema is unsupported")
    digest = payload.get(digest_key)
    body = {key: value for key, value in payload.items() if key != digest_key}
    if digest != canonical_digest(body):
        raise ValueError("artifact digest does not match")


def _load_artifact(
    path: Path,
    *,
    schema: str,
    digest_key: str,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    _validate_self_digest(payload, schema=schema, digest_key=digest_key)
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _mapping(
    value: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    result = value.get(key)
    if not isinstance(result, Mapping):
        raise ValueError(f"{key} must be an object")
    return result


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    result = value.get(key)
    if not isinstance(result, Sequence) or isinstance(result, (str, bytes)):
        raise ValueError(f"{key} must be an array")
    if not all(isinstance(row, Mapping) for row in result):
        raise ValueError(f"{key} entries must be objects")
    return tuple(result)  # pyright: ignore[reportReturnType]


def _required_string(value: Mapping[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ValueError(f"{key} must be a non-empty string")
    return result


def _positive_integer(value: Mapping[str, object], key: str) -> int:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return result


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _number_tuple(value: object, name: str) -> tuple[float, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an array")
    result = tuple(_finite_number(row, name) for row in value)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _unique_string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an array")
    result = tuple(value)
    if (
        not result
        or any(not isinstance(row, str) or not row for row in result)
        or len(result) != len(set(result))
    ):
        raise ValueError(f"{name} must contain unique non-empty strings")
    return result  # pyright: ignore[reportReturnType]


def _mean(values: Sequence[float]) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(rows) / len(rows)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary_command(args: argparse.Namespace) -> None:
    plan = load_plan(args.plan)
    membership_a = _load_artifact(
        args.membership_a,
        schema=MEMBERSHIP_SCHEMA,
        digest_key=MEMBERSHIP_DIGEST_KEY,
    )
    membership_b = _load_artifact(
        args.membership_b,
        schema=MEMBERSHIP_SCHEMA,
        digest_key=MEMBERSHIP_DIGEST_KEY,
    )
    result_a = _load_artifact(
        args.result_a,
        schema=RESULT_SCHEMA,
        digest_key=RESULT_DIGEST_KEY,
    )
    result_b = _load_artifact(
        args.result_b,
        schema=RESULT_SCHEMA,
        digest_key=RESULT_DIGEST_KEY,
    )
    _write_json(
        args.output,
        build_summary(
            membership_a,
            result_a,
            membership_b,
            result_b,
            plan,
        ),
    )


def _validate_command(args: argparse.Namespace) -> None:
    plan = load_plan(args.plan)
    summary = _load_artifact(
        args.summary,
        schema=SUMMARY_SCHEMA,
        digest_key=SUMMARY_DIGEST_KEY,
    )
    if summary.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("summary does not bind the development plan")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument(
        "--membership-output",
        type=Path,
        required=True,
    )
    run.add_argument("--result-output", type=Path, required=True)

    summary = subparsers.add_parser("summarize")
    summary.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summary.add_argument(
        "--membership-a",
        type=Path,
        default=DEFAULT_MEMBERSHIP_A,
    )
    summary.add_argument(
        "--membership-b",
        type=Path,
        default=DEFAULT_MEMBERSHIP_B,
    )
    summary.add_argument("--result-a", type=Path, default=DEFAULT_RESULT_A)
    summary.add_argument("--result-b", type=Path, default=DEFAULT_RESULT_B)
    summary.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)

    args = parser.parse_args(argv)
    if args.command == "run":
        run_once(
            plan_path=args.plan,
            membership_output=args.membership_output,
            result_output=args.result_output,
        )
    elif args.command == "summarize":
        _summary_command(args)
    else:
        _validate_command(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
