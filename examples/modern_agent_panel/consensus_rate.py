#!/usr/bin/env python3
"""Evaluate the frozen consensus-rate budget-ten Selector."""

from __future__ import annotations

# The reproduction command supplies NumPy and PyArrow.
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

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.modern_agent_panel import study as population_study  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "consensus-rate-plan.json"
DEFAULT_POPULATION_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT / "outputs" / "research" / "2026-07-31-consensus-rate-selector"
)
DEFAULT_RESULT_A = DEFAULT_OUTPUT_DIRECTORY / "result-a.json"
DEFAULT_RESULT_B = DEFAULT_OUTPUT_DIRECTORY / "result-b.json"
DEFAULT_SUMMARY = DEFAULT_OUTPUT_DIRECTORY / "summary.json"

PLAN_SCHEMA = "barcarolle_consensus_rate_selector_plan_v1"
RESULT_SCHEMA = "barcarolle_consensus_rate_selector_result_v1"
SUMMARY_SCHEMA = "barcarolle_consensus_rate_selector_summary_v1"
SELECTOR_ID = "consensus_rate_match"
ALGORITHM_IDS = (
    "full_history",
    SELECTOR_ID,
    "rate_only_ablation",
    "consensus_first_ablation",
)


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the frozen post-search candidate contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("consensus-rate plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("consensus-rate plan digest does not match")
    payload["plan_digest"] = digest

    candidate = _mapping(payload, "candidate")
    frame = _mapping(payload, "frame")
    reproduction = _mapping(payload, "reproduction")
    authority = _mapping(payload, "authority")
    if (
        candidate.get("selector_id") != SELECTOR_ID
        or frame.get("primary_lane") != "verified-mini-swe-agent-v2"
        or _positive_integer(frame, "minimum_initial_history_tasks") != 20
        or _positive_integer(frame, "selection_budget_tasks") != 10
        or frame.get("horizons") != [5, 10]
        or _positive_integer(reproduction, "complete_runs") != 2
        or _positive_integer(reproduction, "random_draws") != 20000
        or _required_string(reproduction, "python_version") != "3.14.0"
    ):
        raise ValueError("consensus-rate frozen frame changed")
    for key in (
        "paid_api_calls",
        "new_agent_runs",
        "sealed_verified_full_system_agents_opened",
        "core_schema_changes",
    ):
        if authority.get(key) != 0:
            raise ValueError("consensus-rate authority changed")
    if authority.get("generator_development") is not False:
        raise ValueError("consensus-rate Generator boundary changed")
    return payload


def load_primary_inputs(
    plan: Mapping[str, object],
) -> tuple[
    str,
    tuple[TaskMetadata, ...],
    Mapping[str, Mapping[str, int]],
    Mapping[str, Mapping[str, object]],
    Mapping[str, object],
]:
    """Reuse the population parser while opening only its primary sources."""
    primary = population_study._mapping(plan, "primary_lane")
    task_source = population_study._mapping(primary, "task_source")
    task_path = REPOSITORY_ROOT / population_study._required_string(
        task_source,
        "local_path",
    )
    tasks = population_study._load_tasks(
        task_path,
        expected_sha256=population_study._required_string(
            task_source,
            "sha256",
        ),
        expected_count=population_study._positive_integer(
            task_source,
            "task_count",
        ),
    )
    task_ids = tuple(task.instance_id for task in tasks)
    result_source = population_study._mapping(primary, "result_source")
    result_path = REPOSITORY_ROOT / population_study._required_string(
        result_source,
        "local_path",
    )
    population_study._require_file_identity(
        result_path,
        expected_size=population_study._positive_integer(
            result_source,
            "size_bytes",
        ),
        expected_sha256=population_study._required_string(
            result_source,
            "sha256",
        ),
        expected_git_blob=population_study._required_string(
            result_source,
            "git_blob_sha",
        ),
    )
    cohort = population_study._mapping(primary, "cohort_rule")
    rows = population_study.select_fixed_harness_rows(
        population_study._load_mapping(result_path),
        leaderboard_name=population_study._required_string(
            result_source,
            "leaderboard_name",
        ),
        folders=population_study._string_sequence(
            primary.get("folders"),
            "Agent folders",
        ),
        version=population_study._required_string(
            cohort,
            "mini_swe_agent_version",
        ),
        task_ids=task_ids,
    )
    outcomes, metadata = population_study.normalize_fixed_harness_outcomes(
        rows,
        task_ids,
    )
    if len(outcomes) != population_study._positive_integer(
        cohort,
        "expected_agent_count",
    ):
        raise ValueError("fixed-harness normalized Agent count changed")
    identities = {
        "dataset_sha256": population_study._file_sha256(task_path),
        "result_source_sha256": population_study._file_sha256(result_path),
        "agent_ids": tuple(sorted(outcomes)),
        "outcome_matrix_digest": canonical_digest(outcomes),
    }
    return (
        population_study._required_string(primary, "lane_id"),
        tasks,
        outcomes,
        metadata,
        identities,
    )


def select_consensus_rate_membership(
    reference_history: Any,
    *,
    budget: int,
) -> tuple[int, ...]:
    """Exactly match pooled rate, then minimize reference disagreement."""
    counts, reference_count = _response_counts(reference_history, budget)
    history_count = len(counts)
    full_response_sum = sum(counts)
    frontier = _composition_frontier(
        counts,
        reference_count=reference_count,
        budget=budget,
        consensus_secondary=True,
    )
    return min(
        frontier.items(),
        key=lambda item: (
            abs(item[0] * history_count - full_response_sum * budget),
            item[1][0],
            _recent_key(item[1][1]),
        ),
    )[1][1]


def select_rate_only_membership(
    reference_history: Any,
    *,
    budget: int,
) -> tuple[int, ...]:
    """Ablation: match pooled rate without the consensus objective."""
    counts, reference_count = _response_counts(reference_history, budget)
    history_count = len(counts)
    full_response_sum = sum(counts)
    frontier = _composition_frontier(
        counts,
        reference_count=reference_count,
        budget=budget,
        consensus_secondary=False,
    )
    return min(
        frontier.items(),
        key=lambda item: (
            abs(item[0] * history_count - full_response_sum * budget),
            _recent_key(item[1][1]),
        ),
    )[1][1]


def select_consensus_first_membership(
    reference_history: Any,
    *,
    budget: int,
) -> tuple[int, ...]:
    """Ablation: minimize disagreement without preserving pooled rate."""
    counts, reference_count = _response_counts(reference_history, budget)
    ranked = sorted(
        range(len(counts)),
        key=lambda index: (
            counts[index] * (reference_count - counts[index]),
            -index,
        ),
    )
    return tuple(sorted(ranked[:budget]))


def _response_counts(
    reference_history: Any,
    budget: int,
) -> tuple[tuple[int, ...], int]:
    import numpy as np

    history = np.asarray(reference_history)
    if (
        isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget <= 0
        or history.ndim != 2
        or len(history) < budget
        or history.shape[1] < 2
        or not np.all((history == 0) | (history == 1))
    ):
        raise ValueError("consensus-rate history is invalid")
    return (
        tuple(int(value) for value in history.sum(axis=1).tolist()),
        int(history.shape[1]),
    )


def _composition_frontier(
    counts: Sequence[int],
    *,
    reference_count: int,
    budget: int,
    consensus_secondary: bool,
) -> Mapping[int, tuple[int, tuple[int, ...]]]:
    groups: dict[int, list[int]] = defaultdict(list)
    for index, count in enumerate(counts):
        groups[count].append(index)
    for indices in groups.values():
        indices.sort(reverse=True)

    states: dict[tuple[int, int], tuple[int, tuple[int, ...]]] = {(0, 0): (0, ())}
    for response_count in range(reference_count + 1):
        indices = groups.get(response_count, [])
        if not indices:
            continue
        next_states = dict(states)
        for (chosen, response_sum), (disagreement, selected) in states.items():
            maximum = min(len(indices), budget - chosen)
            for take in range(1, maximum + 1):
                key = (chosen + take, response_sum + take * response_count)
                candidate = (
                    disagreement
                    + take * response_count * (reference_count - response_count),
                    tuple(sorted((*selected, *indices[:take]))),
                )
                incumbent = next_states.get(key)
                if incumbent is None or _frontier_key(
                    candidate,
                    consensus_secondary=consensus_secondary,
                ) < _frontier_key(
                    incumbent,
                    consensus_secondary=consensus_secondary,
                ):
                    next_states[key] = candidate
        states = next_states
    frontier = {
        response_sum: value
        for (chosen, response_sum), value in states.items()
        if chosen == budget
    }
    if not frontier:
        raise ValueError("consensus-rate frontier is empty")
    return frontier


def _frontier_key(
    state: tuple[int, tuple[int, ...]],
    *,
    consensus_secondary: bool,
) -> tuple[Any, ...]:
    disagreement, selected = state
    if consensus_secondary:
        return disagreement, _recent_key(selected)
    return (_recent_key(selected),)


def _recent_key(indices: Sequence[int]) -> tuple[int, ...]:
    return tuple(-index for index in reversed(indices))


def materialize_horizon_memberships(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    horizon: int,
    minimum_history: int,
    budget: int,
) -> Mapping[str, Any]:
    """Materialize target-hidden candidate and ablation memberships."""
    agent_ids = tuple(sorted(outcomes_by_agent))
    task_ids = {task.instance_id for task in tasks}
    if len(agent_ids) < 3 or any(
        set(outcomes_by_agent[agent_id]) != task_ids for agent_id in agent_ids
    ):
        raise ValueError("consensus-rate outcome denominator changed")
    origins_by_repository = _origins_by_repository(
        tasks,
        horizon=horizon,
        minimum_history=minimum_history,
    )
    rows = []
    for repository_id, origins in origins_by_repository.items():
        for origin in origins:
            history_ids = tuple(task.instance_id for task in origin.history)
            for target_agent_id in agent_ids:
                reference_agents = tuple(
                    agent_id for agent_id in agent_ids if agent_id != target_agent_id
                )
                history = _outcome_matrix(
                    outcomes_by_agent,
                    reference_agents,
                    history_ids,
                )
                selected_indices = select_consensus_rate_membership(
                    history,
                    budget=budget,
                )
                ablations = {
                    "rate_only_ablation": select_rate_only_membership(
                        history,
                        budget=budget,
                    ),
                    "consensus_first_ablation": (
                        select_consensus_first_membership(
                            history,
                            budget=budget,
                        )
                    ),
                }
                rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "target_agent_id": target_agent_id,
                        "selected_task_ids": tuple(
                            history_ids[index] for index in selected_indices
                        ),
                        "ablation_memberships": {
                            algorithm_id: tuple(history_ids[index] for index in indices)
                            for algorithm_id, indices in ablations.items()
                        },
                    }
                )
    return {
        "horizon": horizon,
        "repository_ids": tuple(origins_by_repository),
        "origin_count": sum(len(origins) for origins in origins_by_repository.values()),
        "target_agent_count": len(agent_ids),
        "rows": tuple(rows),
        "rows_digest": canonical_digest(rows),
    }


def run_study(plan: Mapping[str, object]) -> Mapping[str, Any]:
    """Run the frozen primary-lane evaluation without opening another lane."""
    import numpy as np
    import pyarrow

    reproduction = _mapping(plan, "reproduction")
    if (
        sys.version.split()[0] != _required_string(
            reproduction,
            "python_version",
        )
        or np.__version__ != _required_string(reproduction, "numpy")
        or pyarrow.__version__ != _required_string(reproduction, "pyarrow")
    ):
        raise ValueError("consensus-rate reproduction runtime changed")
    population_plan = population_study.load_plan(DEFAULT_POPULATION_PLAN)
    lane_id, tasks, outcomes, _, identities = load_primary_inputs(population_plan)
    frame = _mapping(plan, "frame")
    if lane_id != frame.get("primary_lane"):
        raise ValueError("consensus-rate primary lane changed")

    horizons = {}
    for horizon in (5, 10):
        memberships = materialize_horizon_memberships(
            tasks,
            outcomes,
            horizon=horizon,
            minimum_history=_positive_integer(
                frame,
                "minimum_initial_history_tasks",
            ),
            budget=_positive_integer(frame, "selection_budget_tasks"),
        )
        horizon_result = _score_horizon(
            np=np,
            tasks=tasks,
            outcomes_by_agent=outcomes,
            memberships=memberships,
            horizon=horizon,
            minimum_history=_positive_integer(
                frame,
                "minimum_initial_history_tasks",
            ),
            budget=_positive_integer(frame, "selection_budget_tasks"),
            random_draws=_positive_integer(
                reproduction,
                "random_draws",
            ),
            random_seed=_integer(
                _mapping(reproduction, "random_seeds"),
                str(horizon),
            ),
        )
        horizon_result["audits"] = _audit_memberships(
            tasks=tasks,
            outcomes_by_agent=outcomes,
            memberships=memberships,
            horizon=horizon,
            minimum_history=_positive_integer(
                frame,
                "minimum_initial_history_tasks",
            ),
            budget=_positive_integer(frame, "selection_budget_tasks"),
        )
        horizons[str(horizon)] = horizon_result

    beats_full = all(
        _finite_number(
            _mapping(horizons, str(horizon)).get("candidate_minus_full"),
            "candidate difference",
        )
        < 0.0
        for horizon in (5, 10)
    )
    audits_pass = all(
        bool(
            _mapping(
                _mapping(horizons, str(horizon)),
                "audits",
            ).get("passed")
        )
        for horizon in (5, 10)
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "epistemic_status": plan.get("epistemic_status"),
        "lane_id": lane_id,
        "identities": dict(identities),
        "horizons": horizons,
        "decision": {
            "beats_full_at_both_horizons": beats_full,
            "information_audits_pass": audits_pass,
            "development_candidate_verified": beats_full and audits_pass,
            "production_selector_nominated": False,
        },
        "implementation": {
            "consensus_rate_file_sha256": _file_sha256(Path(__file__)),
            "population_parser_file_sha256": _file_sha256(HERE / "study.py"),
            "population_plan_file_sha256": _file_sha256(DEFAULT_POPULATION_PLAN),
            "population_plan_digest": population_plan.get("plan_digest"),
        },
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_runs": 0,
            "sealed_verified_full_system_agents_opened": 0,
            "secondary_lane_outcomes_opened_by_this_run": 0,
        },
        "claim_boundary": _mapping(
            plan,
            "research_contract",
        ).get("claim_boundary"),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _score_horizon(
    *,
    np: Any,
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    memberships: Mapping[str, object],
    horizon: int,
    minimum_history: int,
    budget: int,
    random_draws: int,
    random_seed: int,
) -> dict[str, Any]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    origins_by_repository = _origins_by_repository(
        tasks,
        horizon=horizon,
        minimum_history=minimum_history,
    )
    origin_index = {
        origin.origin_id: origin
        for origins in origins_by_repository.values()
        for origin in origins
    }
    rows = _mapping_sequence(memberships, "rows")
    expected_rows = sum(
        len(origins) for origins in origins_by_repository.values()
    ) * len(agent_ids)
    if len(rows) != expected_rows:
        raise ValueError("consensus-rate membership row count changed")

    repository_losses = {
        repository_id: {algorithm_id: [] for algorithm_id in ALGORITHM_IDS}
        for repository_id in origins_by_repository
    }
    agent_repository_losses = {
        (agent_id, repository_id): {algorithm_id: [] for algorithm_id in ALGORITHM_IDS}
        for agent_id in agent_ids
        for repository_id in origins_by_repository
    }
    origin_losses: dict[
        tuple[str, str],
        dict[str, list[float]],
    ] = {}
    repository_diagnostics: dict[
        str,
        dict[str, list[float]],
    ] = {
        repository_id: {
            "selected_to_full_pooled_rate_error": [],
            "selected_disagreement": [],
            "full_history_disagreement": [],
            "selected_minus_full_disagreement": [],
            "reference_to_target_transfer_error": [],
        }
        for repository_id in origins_by_repository
    }
    score_rows = []

    for row in rows:
        repository_id = _required_string(row, "repository_id")
        origin_id = _required_string(row, "origin_id")
        target_agent_id = _required_string(row, "target_agent_id")
        origin = origin_index.get(origin_id)
        if (
            origin is None
            or origin.repository_id != repository_id
            or target_agent_id not in outcomes_by_agent
        ):
            raise ValueError("consensus-rate membership identity changed")
        history_ids = tuple(task.instance_id for task in origin.history)
        future_ids = tuple(task.instance_id for task in origin.future)
        target_outcomes = outcomes_by_agent[target_agent_id]
        future_rate = _mean([target_outcomes[task_id] for task_id in future_ids])
        selected_by_algorithm = {
            SELECTOR_ID: _selected_ids(
                row.get("selected_task_ids"),
                history_ids=history_ids,
                budget=budget,
                label=SELECTOR_ID,
            )
        }
        ablations = _mapping(row, "ablation_memberships")
        for algorithm_id in (
            "rate_only_ablation",
            "consensus_first_ablation",
        ):
            selected_by_algorithm[algorithm_id] = _selected_ids(
                ablations.get(algorithm_id),
                history_ids=history_ids,
                budget=budget,
                label=algorithm_id,
            )
        losses = {
            "full_history": abs(
                _mean([target_outcomes[task_id] for task_id in history_ids])
                - future_rate
            )
        }
        for algorithm_id, selected_ids in selected_by_algorithm.items():
            losses[algorithm_id] = abs(
                _mean([target_outcomes[task_id] for task_id in selected_ids])
                - future_rate
            )

        reference_agents = tuple(
            agent_id for agent_id in agent_ids if agent_id != target_agent_id
        )
        reference_history = _outcome_matrix(
            outcomes_by_agent,
            reference_agents,
            history_ids,
        )
        counts = reference_history.sum(axis=1)
        reference_count = len(reference_agents)
        selected_indices = [
            history_ids.index(task_id) for task_id in selected_by_algorithm[SELECTOR_ID]
        ]
        full_pooled_rate = float(reference_history.mean())
        selected_pooled_rate = float(reference_history[selected_indices].mean())
        disagreement = counts * (reference_count - counts) / reference_count**2
        full_disagreement = float(disagreement.mean())
        selected_disagreement = float(disagreement[selected_indices].mean())
        selected_target_rate = _mean(
            [target_outcomes[task_id] for task_id in selected_by_algorithm[SELECTOR_ID]]
        )
        diagnostics = {
            "selected_to_full_pooled_rate_error": abs(
                selected_pooled_rate - full_pooled_rate
            ),
            "selected_disagreement": selected_disagreement,
            "full_history_disagreement": full_disagreement,
            "selected_minus_full_disagreement": (
                selected_disagreement - full_disagreement
            ),
            "reference_to_target_transfer_error": abs(
                selected_target_rate - selected_pooled_rate
            ),
        }
        score_rows.append(
            {
                "repository_id": repository_id,
                "origin_id": origin_id,
                "target_agent_id": target_agent_id,
                "losses": losses,
                "diagnostics": diagnostics,
            }
        )
        origin_key = (repository_id, origin_id)
        if origin_key not in origin_losses:
            origin_losses[origin_key] = {
                algorithm_id: [] for algorithm_id in ALGORITHM_IDS
            }
        for algorithm_id, loss in losses.items():
            repository_losses[repository_id][algorithm_id].append(loss)
            agent_repository_losses[(target_agent_id, repository_id)][
                algorithm_id
            ].append(loss)
            origin_losses[origin_key][algorithm_id].append(loss)
        for diagnostic_id, value in diagnostics.items():
            repository_diagnostics[repository_id][diagnostic_id].append(value)

    repository_rows = tuple(
        _repository_row(
            repository_id,
            origins_by_repository[repository_id],
            repository_losses[repository_id],
        )
        for repository_id in origins_by_repository
    )
    macro = {
        algorithm_id: _mean(
            [_mapping(row, "mae")[algorithm_id] for row in repository_rows]
        )
        for algorithm_id in ALGORITHM_IDS
    }
    agent_rows = tuple(
        _agent_row(
            agent_id,
            origins_by_repository,
            agent_repository_losses,
        )
        for agent_id in agent_ids
    )
    origin_rows = tuple(
        _origin_row(repository_id, origin_id, losses)
        for (repository_id, origin_id), losses in sorted(origin_losses.items())
    )
    candidate_difference = macro[SELECTOR_ID] - macro["full_history"]
    return {
        "frame": {
            "horizon": horizon,
            "repository_ids": tuple(origins_by_repository),
            "repository_count": len(origins_by_repository),
            "origin_count": sum(
                len(origins) for origins in origins_by_repository.values()
            ),
            "target_agent_count": len(agent_ids),
            "minimum_initial_history_tasks": minimum_history,
            "selection_budget_tasks": budget,
        },
        "full_history_mae": macro["full_history"],
        "candidate_mae": macro[SELECTOR_ID],
        "candidate_minus_full": candidate_difference,
        "directions": {
            "repository": _direction_counts(
                [
                    _mapping(row, "candidate_minus_full")[SELECTOR_ID]
                    for row in repository_rows
                ]
            ),
            "agent": _direction_counts(
                [
                    _mapping(row, "candidate_minus_full")[SELECTOR_ID]
                    for row in agent_rows
                ]
            ),
            "origin": _direction_counts(
                [
                    _mapping(row, "candidate_minus_full")[SELECTOR_ID]
                    for row in origin_rows
                ]
            ),
        },
        "ablations": {
            algorithm_id: {
                "mae": macro[algorithm_id],
                "candidate_minus_full": (macro[algorithm_id] - macro["full_history"]),
            }
            for algorithm_id in (
                "rate_only_ablation",
                "consensus_first_ablation",
            )
        },
        "diagnostics": _summarize_diagnostics(repository_diagnostics),
        "sensitivity": _sensitivity(
            repository_rows=repository_rows,
            origin_rows=origin_rows,
        ),
        "random_calibration": _random_calibration(
            np=np,
            origins_by_repository=origins_by_repository,
            outcomes_by_agent=outcomes_by_agent,
            agent_ids=agent_ids,
            budget=budget,
            draws=random_draws,
            seed=random_seed,
            full_history_mae=macro["full_history"],
            candidate_difference=candidate_difference,
        ),
        "repository_rows": repository_rows,
        "agent_rows": agent_rows,
        "origin_rows": origin_rows,
        "membership_rows": rows,
        "membership_rows_digest": memberships.get("rows_digest"),
        "score_rows": tuple(score_rows),
        "score_rows_digest": canonical_digest(score_rows),
    }


def _repository_row(
    repository_id: str,
    origins: Sequence[RepositoryOrigin],
    losses: Mapping[str, Sequence[float]],
) -> Mapping[str, Any]:
    mae = {algorithm_id: _mean(losses[algorithm_id]) for algorithm_id in ALGORITHM_IDS}
    return {
        "repository_id": repository_id,
        "origin_count": len(origins),
        "mae": mae,
        "candidate_minus_full": {
            algorithm_id: mae[algorithm_id] - mae["full_history"]
            for algorithm_id in ALGORITHM_IDS
            if algorithm_id != "full_history"
        },
    }


def _agent_row(
    agent_id: str,
    origins_by_repository: Mapping[
        str,
        Sequence[RepositoryOrigin],
    ],
    losses: Mapping[
        tuple[str, str],
        Mapping[str, Sequence[float]],
    ],
) -> Mapping[str, Any]:
    mae = {
        algorithm_id: _mean(
            [
                _mean(losses[(agent_id, repository_id)][algorithm_id])
                for repository_id in origins_by_repository
            ]
        )
        for algorithm_id in ALGORITHM_IDS
    }
    return {
        "agent_id": agent_id,
        "mae": mae,
        "candidate_minus_full": {
            algorithm_id: mae[algorithm_id] - mae["full_history"]
            for algorithm_id in ALGORITHM_IDS
            if algorithm_id != "full_history"
        },
    }


def _origin_row(
    repository_id: str,
    origin_id: str,
    losses: Mapping[str, Sequence[float]],
) -> Mapping[str, Any]:
    mae = {algorithm_id: _mean(losses[algorithm_id]) for algorithm_id in ALGORITHM_IDS}
    return {
        "repository_id": repository_id,
        "origin_id": origin_id,
        "mae": mae,
        "candidate_minus_full": {
            algorithm_id: mae[algorithm_id] - mae["full_history"]
            for algorithm_id in ALGORITHM_IDS
            if algorithm_id != "full_history"
        },
    }


def _summarize_diagnostics(
    repository_values: Mapping[
        str,
        Mapping[str, Sequence[float]],
    ],
) -> Mapping[str, Any]:
    repository_rows = tuple(
        {
            "repository_id": repository_id,
            "mean": {
                diagnostic_id: _mean(values)
                for diagnostic_id, values in diagnostics.items()
            },
        }
        for repository_id, diagnostics in repository_values.items()
    )
    return {
        "semantics": {
            "disagreement": "mean c*(m-c)/m^2 over Tasks",
            "reference_to_target_transfer_error": (
                "absolute selected target rate minus selected reference pooled rate"
            ),
        },
        "repository_equal_mean": {
            diagnostic_id: _mean(
                [_mapping(row, "mean")[diagnostic_id] for row in repository_rows]
            )
            for diagnostic_id in next(iter(repository_values.values()))
        },
        "repository_rows": repository_rows,
    }


def _sensitivity(
    *,
    repository_rows: Sequence[Mapping[str, object]],
    origin_rows: Sequence[Mapping[str, object]],
) -> Mapping[str, Any]:
    leave_one_out = []
    for excluded in repository_rows:
        included = [
            row
            for row in repository_rows
            if row["repository_id"] != excluded["repository_id"]
        ]
        leave_one_out.append(
            {
                "excluded_repository_id": excluded["repository_id"],
                **_aggregate_repository_rows(included),
            }
        )
    multi_origin = [
        row for row in repository_rows if _positive_integer(row, "origin_count") > 1
    ]
    origin_weighted_full = _mean(
        [_mapping(row, "mae")["full_history"] for row in origin_rows]
    )
    origin_weighted_candidate = _mean(
        [_mapping(row, "mae")[SELECTOR_ID] for row in origin_rows]
    )
    return {
        "leave_one_repository_out": tuple(leave_one_out),
        "origin_weighted": {
            "repository_count": len(repository_rows),
            "origin_count": len(origin_rows),
            "full_history_mae": origin_weighted_full,
            "candidate_mae": origin_weighted_candidate,
            "candidate_minus_full": (origin_weighted_candidate - origin_weighted_full),
        },
        "repositories_with_more_than_one_origin": {
            "repository_ids": tuple(row["repository_id"] for row in multi_origin),
            **_aggregate_repository_rows(multi_origin),
        },
    }


def _aggregate_repository_rows(
    rows: Sequence[Mapping[str, object]],
) -> Mapping[str, Any]:
    if not rows:
        return {
            "repository_count": 0,
            "full_history_mae": None,
            "candidate_mae": None,
            "candidate_minus_full": None,
        }
    full = _mean([_mapping(row, "mae")["full_history"] for row in rows])
    candidate = _mean([_mapping(row, "mae")[SELECTOR_ID] for row in rows])
    return {
        "repository_count": len(rows),
        "full_history_mae": full,
        "candidate_mae": candidate,
        "candidate_minus_full": candidate - full,
    }


def _random_calibration(
    *,
    np: Any,
    origins_by_repository: Mapping[
        str,
        Sequence[RepositoryOrigin],
    ],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    budget: int,
    draws: int,
    seed: int,
    full_history_mae: float,
    candidate_difference: float,
) -> Mapping[str, Any]:
    generator = np.random.Generator(np.random.PCG64(seed))
    macro_differences = np.zeros(draws, dtype=np.float64)
    repository_mean_differences = {}
    batch_size = 512
    for repository_id, origins in origins_by_repository.items():
        repository_differences = np.zeros(draws, dtype=np.float64)
        for origin in origins:
            history = _outcome_matrix(
                outcomes_by_agent,
                agent_ids,
                tuple(task.instance_id for task in origin.history),
            )
            future = _outcome_matrix(
                outcomes_by_agent,
                agent_ids,
                tuple(task.instance_id for task in origin.future),
            ).mean(axis=0)
            baseline = float(np.abs(history.mean(axis=0) - future).mean())
            for start in range(0, draws, batch_size):
                stop = min(start + batch_size, draws)
                keys = generator.random((stop - start, len(history)))
                indices = np.argpartition(
                    keys,
                    budget - 1,
                    axis=1,
                )[:, :budget]
                losses = np.abs(history[indices].mean(axis=1) - future).mean(axis=1)
                repository_differences[start:stop] += losses - baseline
        repository_differences /= len(origins)
        repository_mean_differences[repository_id] = float(
            repository_differences.mean()
        )
        macro_differences += repository_differences
    macro_differences /= len(origins_by_repository)
    values = tuple(float(value) for value in macro_differences)
    ordered = tuple(sorted(values))
    mean_difference = _mean(values)
    return {
        "draws": draws,
        "seed": seed,
        "mean_random_mae": full_history_mae + mean_difference,
        "mean_random_minus_full": mean_difference,
        "repository_mean_random_minus_full": (repository_mean_differences),
        "random_as_good_or_better_than_candidate_share": (
            sum(value <= candidate_difference for value in values) / draws
        ),
        "candidate_better_than_random_midrank": (
            sum(value > candidate_difference for value in values)
            + 0.5 * sum(value == candidate_difference for value in values)
        )
        / draws,
        "random_as_good_or_better_than_full_share": (
            sum(value <= 0.0 for value in values) / draws
        ),
        "quantiles": {
            "0.025": _quantile(ordered, 0.025),
            "0.5": _quantile(ordered, 0.5),
            "0.975": _quantile(ordered, 0.975),
        },
        "macro_differences_digest": canonical_digest(values),
    }


def _audit_memberships(
    *,
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    memberships: Mapping[str, object],
    horizon: int,
    minimum_history: int,
    budget: int,
) -> Mapping[str, Any]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    origins = {
        origin.origin_id: origin
        for repository_origins in _origins_by_repository(
            tasks,
            horizon=horizon,
            minimum_history=minimum_history,
        ).values()
        for origin in repository_origins
    }
    membership_violations = []
    target_mismatches = []
    future_mismatches = []
    for row in _mapping_sequence(memberships, "rows"):
        origin_id = _required_string(row, "origin_id")
        target_agent_id = _required_string(row, "target_agent_id")
        origin = origins[origin_id]
        history_ids = tuple(task.instance_id for task in origin.history)
        future_ids = {task.instance_id for task in origin.future}
        selected_ids = _selected_ids(
            row.get("selected_task_ids"),
            history_ids=history_ids,
            budget=budget,
            label=SELECTOR_ID,
        )
        if set(selected_ids) & future_ids:
            membership_violations.append((origin_id, target_agent_id))
        reference_agents = tuple(
            agent_id for agent_id in agent_ids if agent_id != target_agent_id
        )
        target_flipped_history = _outcome_matrix(
            outcomes_by_agent,
            reference_agents,
            history_ids,
            flip_agents={target_agent_id},
        )
        target_flipped_indices = select_consensus_rate_membership(
            target_flipped_history,
            budget=budget,
        )
        if (
            tuple(history_ids[index] for index in target_flipped_indices)
            != selected_ids
        ):
            target_mismatches.append((origin_id, target_agent_id))
        future_flipped_history = _outcome_matrix(
            outcomes_by_agent,
            reference_agents,
            history_ids,
            flip_task_ids=future_ids,
        )
        future_flipped_indices = select_consensus_rate_membership(
            future_flipped_history,
            budget=budget,
        )
        if (
            tuple(history_ids[index] for index in future_flipped_indices)
            != selected_ids
        ):
            future_mismatches.append((origin_id, target_agent_id))
    passed = not (membership_violations or target_mismatches or future_mismatches)
    return {
        "membership_cell_count": len(_mapping_sequence(memberships, "rows")),
        "selected_membership_outside_history_count": len(membership_violations),
        "target_complete_column_flip_mismatch_count": len(target_mismatches),
        "current_future_all_columns_flip_mismatch_count": len(future_mismatches),
        "target_complete_column_flip_passed": not target_mismatches,
        "current_future_all_columns_flip_passed": not future_mismatches,
        "passed": passed,
    }


def _origins_by_repository(
    tasks: Sequence[TaskMetadata],
    *,
    horizon: int,
    minimum_history: int,
) -> Mapping[str, tuple[RepositoryOrigin, ...]]:
    return {
        repository_id: origins
        for repository_id, origins in sorted(
            build_repository_origins(
                tasks,
                minimum_initial_history_tasks=minimum_history,
                future_block_tasks=horizon,
            ).items()
        )
        if origins
    }


def _outcome_matrix(
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    task_ids: Sequence[str],
    *,
    flip_agents: set[str] | None = None,
    flip_task_ids: set[str] | None = None,
) -> Any:
    import numpy as np

    agents_to_flip = flip_agents or set()
    tasks_to_flip = flip_task_ids or set()
    return np.asarray(
        [
            [
                (
                    1 - outcomes_by_agent[agent_id][task_id]
                    if (agent_id in agents_to_flip or task_id in tasks_to_flip)
                    else outcomes_by_agent[agent_id][task_id]
                )
                for agent_id in agent_ids
            ]
            for task_id in task_ids
        ],
        dtype=np.float64,
    )


def _selected_ids(
    value: object,
    *,
    history_ids: Sequence[str],
    budget: int,
    label: str,
) -> tuple[str, ...]:
    selected = _unique_strings(value, f"{label} membership")
    if len(selected) != budget or not set(selected) <= set(history_ids):
        raise ValueError(f"{label} membership left eligible history")
    return selected


def _direction_counts(values: Sequence[float]) -> Mapping[str, int]:
    return {
        "favorable": sum(value < 0.0 for value in values),
        "tied": sum(value == 0.0 for value in values),
        "unfavorable": sum(value > 0.0 for value in values),
        "total": len(values),
    }


def build_summary(
    result_a: Mapping[str, object],
    result_b: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Build compact evidence only from two identical complete runs."""
    _validate_result(result_a, plan)
    _validate_result(result_b, plan)
    if canonical_json(result_a) != canonical_json(result_b):
        raise ValueError("consensus-rate reproduction differs")
    compact_horizons = {}
    for horizon, value in _mapping(result_a, "horizons").items():
        payload = _mapping_value(value, f"H{horizon} result")
        compact_horizons[horizon] = {
            key: item
            for key, item in payload.items()
            if key not in ("membership_rows", "score_rows")
        }
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "reproduction": {
            "byte_identical_second_run": True,
            "result_digest": result_a.get("result_digest"),
        },
        "lane_id": result_a.get("lane_id"),
        "identities": dict(_mapping(result_a, "identities")),
        "horizons": compact_horizons,
        "decision": dict(_mapping(result_a, "decision")),
        "implementation": dict(_mapping(result_a, "implementation")),
        "resource_use": dict(_mapping(result_a, "resource_use")),
        "claim_boundary": result_a.get("claim_boundary"),
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary


def _validate_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    body = {key: value for key, value in result.items() if key != "result_digest"}
    if (
        result.get("schema_version") != RESULT_SCHEMA
        or result.get("plan_digest") != plan.get("plan_digest")
        or result.get("result_digest") != canonical_digest(body)
    ):
        raise ValueError("consensus-rate result is invalid")


def validate_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    body = {key: value for key, value in summary.items() if key != "summary_digest"}
    implementation = _mapping(summary, "implementation")
    if (
        summary.get("schema_version") != SUMMARY_SCHEMA
        or summary.get("plan_digest") != plan.get("plan_digest")
        or summary.get("summary_digest") != canonical_digest(body)
        or implementation.get("consensus_rate_file_sha256")
        != _file_sha256(Path(__file__))
        or implementation.get("population_parser_file_sha256")
        != _file_sha256(HERE / "study.py")
        or implementation.get("population_plan_file_sha256")
        != _file_sha256(DEFAULT_POPULATION_PLAN)
        or implementation.get("population_plan_digest")
        != population_study.load_plan(DEFAULT_POPULATION_PLAN).get("plan_digest")
    ):
        raise ValueError("consensus-rate summary is invalid")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _write_json(
    path: Path,
    payload: Mapping[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_value(
    value: object,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise ValueError(f"{key} must contain objects")
    return tuple(value)


def _required_string(
    payload: Mapping[str, object],
    key: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _positive_integer(
    payload: Mapping[str, object],
    key: str,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return value


def _integer(
    payload: Mapping[str, object],
    key: str,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _unique_strings(
    value: object,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array")
    result = tuple(value)
    if any(not isinstance(item, str) or not item for item in result) or len(
        result
    ) != len(set(result)):
        raise ValueError(f"{label} must contain unique strings")
    return result  # type: ignore[return-value]


def _finite_number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
    ):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _mean(values: Sequence[float] | Any) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(float(value) for value in rows) / len(rows)


def _quantile(
    ordered: Sequence[float],
    probability: float,
) -> float:
    if not ordered or not 0.0 <= probability <= 1.0:
        raise ValueError("quantile inputs are invalid")
    index = probability * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument("--output", type=Path, required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summarize.add_argument(
        "--result-a",
        type=Path,
        default=DEFAULT_RESULT_A,
    )
    summarize.add_argument(
        "--result-b",
        type=Path,
        default=DEFAULT_RESULT_B,
    )
    summarize.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SUMMARY,
    )

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_plan(args.plan)
    if args.command == "run":
        _write_json(args.output, run_study(plan))
    elif args.command == "summarize":
        _write_json(
            args.output,
            build_summary(
                _load_mapping(args.result_a),
                _load_mapping(args.result_b),
                plan,
            ),
        )
    else:
        validate_summary(_load_mapping(args.summary), plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
