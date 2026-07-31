#!/usr/bin/env python3
"""Replay unchanged response Selectors on the modern Agent panels."""

from __future__ import annotations

# The reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.modern_agent_panel.study import (  # noqa: E402
    load_inputs,
    load_plan as load_population_plan,
    validate_summary as validate_population_summary,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    adanormalhedge_forecast,
    create_adanormalhedge_state,
    response_expert_forecasts,
    update_adanormalhedge,
)
from examples.swe_bench_full_development.study import (  # noqa: E402
    select_response_memberships,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "portability-plan.json"
DEFAULT_POPULATION_PLAN = HERE / "plan.json"
DEFAULT_POPULATION_SUMMARY = HERE / "evidence" / "summary.json"
DEFAULT_SUMMARY = HERE / "evidence" / "portability-summary.json"
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT / "outputs" / "research" / "2026-07-31-modern-agent-portability"
)
DEFAULT_RESULT_A = DEFAULT_OUTPUT_DIRECTORY / "result-a.json"
DEFAULT_RESULT_B = DEFAULT_OUTPUT_DIRECTORY / "result-b.json"

PLAN_SCHEMA = "barcarolle_modern_selector_portability_plan_v1"
RESULT_SCHEMA = "barcarolle_modern_selector_portability_result_v1"
SUMMARY_SCHEMA = "barcarolle_modern_selector_portability_summary_v1"
CANDIDATE_IDS = (
    "ordinary_recency",
    "stationary_response_match",
    "ALG-015U",
    "ALG-016U",
)


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the frozen unchanged-mechanism portability contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("modern portability plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("modern portability plan digest does not match")
    payload["plan_digest"] = digest

    candidates = _mapping_sequence(payload, "candidates")
    if tuple(_required_string(row, "selector_id") for row in candidates) != (
        CANDIDATE_IDS
    ):
        raise ValueError("modern portability candidate set changed")
    authority = _mapping(payload, "authority")
    for key in (
        "paid_api_calls",
        "new_agent_runs",
        "sealed_verified_full_system_agents_opened",
        "algorithm_changes",
        "parameter_searches",
        "core_schema_changes",
    ):
        if authority.get(key) != 0:
            raise ValueError("modern portability authority changed")
    if authority.get("generator_development") is not False:
        raise ValueError("modern portability Generator boundary changed")

    for binding in (
        *_mapping(payload, "bound_population").values(),
        *_mapping(payload, "bound_implementations").values(),
    ):
        if not isinstance(binding, Mapping):
            continue
        path_value = binding.get("path")
        file_sha = binding.get("file_sha256")
        if isinstance(path_value, str) and isinstance(file_sha, str):
            bound_path = REPOSITORY_ROOT / path_value
            if _file_sha256(bound_path) != file_sha:
                raise ValueError(f"bound portability input changed: {bound_path}")
            logical_key = binding.get("logical_digest_key")
            if logical_key is not None:
                bound = _load_mapping(bound_path)
                if not isinstance(logical_key, str) or bound.get(
                    logical_key
                ) != binding.get("logical_digest"):
                    raise ValueError(f"bound portability digest changed: {bound_path}")
    return payload


def materialize_horizon_memberships(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    horizon: int,
    minimum_history: int,
    budget: int,
) -> Mapping[str, Any]:
    """Materialize target-hidden memberships for one rolling horizon."""
    import numpy as np

    agent_ids = tuple(sorted(outcomes_by_agent))
    if len(agent_ids) < 2:
        raise ValueError("portability replay requires at least two Agents")
    task_ids = {task.instance_id for task in tasks}
    if any(set(outcomes_by_agent[agent_id]) != task_ids for agent_id in agent_ids):
        raise ValueError("portability outcome denominator changed")
    origins_by_repository = {
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
    rows = []
    for position, (repository_id, origins) in enumerate(
        origins_by_repository.items(),
        start=1,
    ):
        state = create_adanormalhedge_state(len(agent_ids))
        previous_experts = None
        previous_history_count = None
        for origin in origins:
            history_ids = tuple(task.instance_id for task in origin.history)
            history = np.asarray(
                [
                    [outcomes_by_agent[agent_id][task_id] for agent_id in agent_ids]
                    for task_id in history_ids
                ],
                dtype=np.float64,
            )
            if previous_experts is not None:
                if (
                    previous_history_count is None
                    or len(history) - previous_history_count != horizon
                ):
                    raise ValueError("prequential history update changed")
                update_adanormalhedge(
                    state,
                    previous_experts,
                    history[-horizon:].mean(axis=0),
                )
            experts = response_expert_forecasts(history, horizon=horizon)
            adaptive_forecast, _ = adanormalhedge_forecast(state, experts)
            memberships = select_response_memberships(
                history,
                adaptive_forecast,
                horizon=horizon,
                budget=budget,
                created_order=tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                ),
            )
            for held_out, target_agent_id in enumerate(agent_ids):
                rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "target_agent_id": target_agent_id,
                        "memberships": {
                            selector_id: tuple(
                                history_ids[index]
                                for index in memberships[held_out][selector_id]
                            )
                            for selector_id in CANDIDATE_IDS
                        },
                    }
                )
            previous_experts = experts
            previous_history_count = len(history)
        print(
            f"materialized H{horizon} repository "
            f"{position}/{len(origins_by_repository)} {repository_id}",
            flush=True,
        )
    return {
        "horizon": horizon,
        "repository_ids": tuple(origins_by_repository),
        "origin_count": sum(map(len, origins_by_repository.values())),
        "target_agent_count": len(agent_ids),
        "rows": tuple(rows),
        "rows_digest": canonical_digest(rows),
    }


def run_study(plan: Mapping[str, object]) -> Mapping[str, Any]:
    """Materialize and score both frozen modern-population lanes."""
    import numpy as np
    import pyarrow
    import scipy

    reproduction = _mapping(plan, "reproduction")
    if (
        sys.version.split()[0] != _required_string(reproduction, "python_version")
        or np.__version__ != _required_string(reproduction, "numpy_version")
        or scipy.__version__ != _required_string(reproduction, "scipy_version")
        or pyarrow.__version__ != _required_string(reproduction, "pyarrow_version")
    ):
        raise ValueError("modern portability runtime changed")

    population_plan = load_population_plan(DEFAULT_POPULATION_PLAN)
    population_summary = _load_mapping(DEFAULT_POPULATION_SUMMARY)
    validate_population_summary(population_summary, population_plan)
    frame = _mapping(plan, "frame")
    lanes = {}
    for lane_offset, (
        lane_id,
        tasks,
        outcomes,
        _,
        identities,
    ) in enumerate(load_inputs(population_plan)):
        horizon_results = {}
        for horizon in (5, 10):
            memberships = materialize_horizon_memberships(
                tasks,
                outcomes,
                horizon=horizon,
                minimum_history=_positive_integer(
                    frame,
                    "minimum_initial_history_tasks",
                ),
                budget=_positive_integer(
                    frame,
                    "selection_budget_tasks",
                ),
            )
            horizon_results[str(horizon)] = _score_horizon(
                np=np,
                lane_id=lane_id,
                tasks=tasks,
                outcomes_by_agent=outcomes,
                memberships=memberships,
                horizon=horizon,
                minimum_history=_positive_integer(
                    frame,
                    "minimum_initial_history_tasks",
                ),
                budget=_positive_integer(
                    frame,
                    "selection_budget_tasks",
                ),
                random_draws=_positive_integer(
                    _mapping(plan, "evaluation"),
                    "random_draws",
                ),
                random_seed=(
                    _positive_integer(
                        _mapping(plan, "evaluation"),
                        "random_seed",
                    )
                    + lane_offset * 1000
                    + horizon
                ),
                population_horizon=_mapping(
                    _mapping(
                        _mapping(population_summary, "lanes"),
                        lane_id,
                    ),
                    "horizons",
                )[str(horizon)],
                population_agent_ids=tuple(
                    sorted(
                        _required_string(row, "agent_id")
                        for row in _mapping_sequence(
                            _mapping(
                                _mapping(
                                    _mapping(
                                        _mapping(population_summary, "lanes"),
                                        lane_id,
                                    ),
                                    "horizons",
                                ),
                                str(horizon),
                            ),
                            "agent_rows",
                        )
                    )
                ),
            )
        lanes[lane_id] = {
            "lane_id": lane_id,
            "identities": dict(identities),
            "horizons": horizon_results,
        }

    primary_id = _required_string(
        _mapping(population_plan, "primary_lane"),
        "lane_id",
    )
    secondary_id = _required_string(
        _mapping(population_plan, "secondary_lane"),
        "lane_id",
    )
    candidate_decisions = {}
    retained = []
    for candidate_id in CANDIDATE_IDS:
        primary_both = all(
            _candidate_difference(lanes, primary_id, horizon, candidate_id) < 0.0
            for horizon in (5, 10)
        )
        secondary_no_reverse = all(
            _candidate_difference(
                lanes,
                secondary_id,
                horizon,
                candidate_id,
            )
            <= 0.0
            for horizon in (5, 10)
        )
        keep = primary_both and secondary_no_reverse
        candidate_decisions[candidate_id] = {
            "beats_full_at_both_primary_horizons": primary_both,
            "does_not_reverse_on_secondary": secondary_no_reverse,
            "retained": keep,
        }
        if keep:
            retained.append(candidate_id)
    terminal_state = (
        "existing_response_method_retained_as_modern_incumbent"
        if retained
        else "all_existing_response_methods_retired_on_modern_population"
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "epistemic_status": plan.get("epistemic_status"),
        "lanes": lanes,
        "decision": {
            "terminal_state": terminal_state,
            "retained_candidates": tuple(retained),
            "candidate_decisions": candidate_decisions,
            "selector_nominated_for_production": False,
        },
        "implementation": {
            "portability_file_sha256": _file_sha256(Path(__file__)),
        },
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_runs": 0,
            "sealed_verified_full_system_agents_opened": 0,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _score_horizon(
    *,
    np: Any,
    lane_id: str,
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    memberships: Mapping[str, object],
    horizon: int,
    minimum_history: int,
    budget: int,
    random_draws: int,
    random_seed: int,
    population_horizon: object,
    population_agent_ids: Sequence[str],
) -> Mapping[str, Any]:
    population = _mapping_value(population_horizon, "population horizon")
    agent_ids = tuple(sorted(outcomes_by_agent))
    origins_by_repository = {
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
    population_frame = _mapping(population, "frame")
    if (
        tuple(origins_by_repository)
        != _unique_strings(
            population_frame.get("repository_ids"),
            "population repository IDs",
        )
        or sum(map(len, origins_by_repository.values()))
        != _positive_integer(population_frame, "origin_count")
        or agent_ids != tuple(population_agent_ids)
        or horizon != _positive_integer(population_frame, "horizon")
        or budget
        != _positive_integer(
            population_frame,
            "selection_budget_tasks",
        )
    ):
        raise ValueError(f"{lane_id} H{horizon} population frame changed")
    origin_index = {
        origin.origin_id: origin
        for origins in origins_by_repository.values()
        for origin in origins
    }
    rows = _mapping_sequence(memberships, "rows")
    expected_rows = sum(map(len, origins_by_repository.values())) * len(agent_ids)
    if len(rows) != expected_rows:
        raise ValueError(f"{lane_id} H{horizon} membership row count changed")

    algorithm_ids = ("full_history", *CANDIDATE_IDS)
    repository_losses: dict[str, dict[str, list[float]]] = {
        repository_id: {algorithm_id: [] for algorithm_id in algorithm_ids}
        for repository_id in origins_by_repository
    }
    agent_repository_losses: dict[
        tuple[str, str],
        dict[str, list[float]],
    ] = {
        (agent_id, repository_id): {algorithm_id: [] for algorithm_id in algorithm_ids}
        for agent_id in agent_ids
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
            raise ValueError("portability membership identity changed")
        history_ids = tuple(task.instance_id for task in origin.history)
        future_ids = tuple(task.instance_id for task in origin.future)
        target_outcomes = outcomes_by_agent[target_agent_id]
        future_rate = _mean(target_outcomes[task_id] for task_id in future_ids)
        losses = {
            "full_history": abs(
                _mean(target_outcomes[task_id] for task_id in history_ids) - future_rate
            )
        }
        row_memberships = _mapping(row, "memberships")
        for candidate_id in CANDIDATE_IDS:
            selected = _unique_strings(
                row_memberships.get(candidate_id),
                f"{candidate_id} membership",
            )
            if len(selected) != budget or not set(selected) <= set(history_ids):
                raise ValueError("portability membership left history")
            losses[candidate_id] = abs(
                _mean(target_outcomes[task_id] for task_id in selected) - future_rate
            )
        score_rows.append(
            {
                "repository_id": repository_id,
                "origin_id": origin_id,
                "target_agent_id": target_agent_id,
                "losses": losses,
            }
        )
        for algorithm_id, loss in losses.items():
            repository_losses[repository_id][algorithm_id].append(loss)
            agent_repository_losses[(target_agent_id, repository_id)][
                algorithm_id
            ].append(loss)

    repository_rows = []
    for repository_id in origins_by_repository:
        mae = {
            algorithm_id: _mean(repository_losses[repository_id][algorithm_id])
            for algorithm_id in algorithm_ids
        }
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(origins_by_repository[repository_id]),
                "mae": mae,
                "candidate_minus_full": {
                    candidate_id: (mae[candidate_id] - mae["full_history"])
                    for candidate_id in CANDIDATE_IDS
                },
            }
        )
    macro = {
        algorithm_id: _mean(
            _mapping(row, "mae")[algorithm_id] for row in repository_rows
        )
        for algorithm_id in algorithm_ids
    }
    agent_rows = []
    for agent_id in agent_ids:
        agent_mae = {
            algorithm_id: _mean(
                _mean(agent_repository_losses[(agent_id, repository_id)][algorithm_id])
                for repository_id in origins_by_repository
            )
            for algorithm_id in algorithm_ids
        }
        agent_rows.append(
            {
                "agent_id": agent_id,
                "mae": agent_mae,
                "candidate_minus_full": {
                    candidate_id: (agent_mae[candidate_id] - agent_mae["full_history"])
                    for candidate_id in CANDIDATE_IDS
                },
            }
        )
    candidate_differences = {
        candidate_id: macro[candidate_id] - macro["full_history"]
        for candidate_id in CANDIDATE_IDS
    }
    random_positions = _random_positions(
        np=np,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        agent_ids=agent_ids,
        budget=budget,
        draws=random_draws,
        seed=random_seed,
        candidate_differences=candidate_differences,
    )
    population_controls = _mapping(population, "controls")
    reference_headroom = _finite_number(
        population_controls.get("reference_selection_headroom"),
        "reference selection headroom",
    )
    candidates = {}
    for candidate_id in CANDIDATE_IDS:
        difference = candidate_differences[candidate_id]
        candidates[candidate_id] = {
            "mae": macro[candidate_id],
            "candidate_minus_full": difference,
            "favorable_repository_count": sum(
                _finite_number(
                    _mapping(row, "candidate_minus_full").get(candidate_id),
                    "repository candidate difference",
                )
                < 0.0
                for row in repository_rows
            ),
            "repository_count": len(repository_rows),
            "favorable_agent_count": sum(
                _finite_number(
                    _mapping(row, "candidate_minus_full").get(candidate_id),
                    "Agent candidate difference",
                )
                < 0.0
                for row in agent_rows
            ),
            "agent_count": len(agent_rows),
            "reference_oracle_headroom_captured": (
                -difference / reference_headroom if reference_headroom > 0.0 else None
            ),
            "random_position": random_positions[candidate_id],
        }
    return {
        "frame": {
            "horizon": horizon,
            "repository_count": len(origins_by_repository),
            "origin_count": sum(map(len, origins_by_repository.values())),
            "target_agent_count": len(agent_ids),
        },
        "full_history_mae": macro["full_history"],
        "candidates": candidates,
        "repository_rows": tuple(repository_rows),
        "agent_rows": tuple(agent_rows),
        "membership_rows": rows,
        "membership_rows_digest": memberships.get("rows_digest"),
        "score_rows_digest": canonical_digest(score_rows),
        "random_distribution_digest": random_positions["distribution_digest"],
    }


def _random_positions(
    *,
    np: Any,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    budget: int,
    draws: int,
    seed: int,
    candidate_differences: Mapping[str, float],
) -> Mapping[str, Any]:
    generator = np.random.Generator(np.random.PCG64(seed))
    macro_differences = np.zeros(draws, dtype=np.float64)
    batch_size = 512
    for repository_id, origins in origins_by_repository.items():
        repository_differences = np.zeros(draws, dtype=np.float64)
        for origin in origins:
            history = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task.instance_id]
                        for agent_id in agent_ids
                    ]
                    for task in origin.history
                ],
                dtype=np.float64,
            )
            future_rate = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task.instance_id]
                        for agent_id in agent_ids
                    ]
                    for task in origin.future
                ],
                dtype=np.float64,
            ).mean(axis=0)
            baseline = float(np.abs(history.mean(axis=0) - future_rate).mean())
            for start in range(0, draws, batch_size):
                stop = min(start + batch_size, draws)
                keys = generator.random((stop - start, len(history)))
                indices = np.argpartition(
                    keys,
                    budget - 1,
                    axis=1,
                )[:, :budget]
                losses = np.abs(history[indices].mean(axis=1) - future_rate).mean(
                    axis=1
                )
                repository_differences[start:stop] += losses - baseline
        repository_differences /= len(origins)
        macro_differences += repository_differences
    macro_differences /= len(origins_by_repository)
    values = tuple(float(value) for value in macro_differences)
    result: dict[str, Any] = {
        candidate_id: {
            "random_as_good_or_better_share": (
                sum(value <= difference for value in values) / draws
            ),
            "candidate_better_than_random_midrank": (
                sum(value > difference for value in values)
                + 0.5 * sum(value == difference for value in values)
            )
            / draws,
        }
        for candidate_id, difference in candidate_differences.items()
    }
    result["distribution_digest"] = canonical_digest(values)
    return result


def _candidate_difference(
    lanes: Mapping[str, Any],
    lane_id: str,
    horizon: int,
    candidate_id: str,
) -> float:
    return _finite_number(
        _mapping(
            _mapping(
                _mapping(
                    _mapping(lanes, lane_id),
                    "horizons",
                ),
                str(horizon),
            ),
            "candidates",
        )[candidate_id]["candidate_minus_full"],
        "candidate difference",
    )


def build_summary(
    result_a: Mapping[str, object],
    result_b: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Commit identical compact portability evidence."""
    _validate_result(result_a, plan)
    _validate_result(result_b, plan)
    if canonical_json(result_a) != canonical_json(result_b):
        raise ValueError("modern portability reproduction differs")
    compact_lanes = {}
    for lane_id, lane_value in _mapping(result_a, "lanes").items():
        lane = _mapping_value(lane_value, f"{lane_id} lane")
        compact_horizons = {}
        for horizon, horizon_value in _mapping(lane, "horizons").items():
            payload = _mapping_value(
                horizon_value,
                f"{lane_id} H{horizon}",
            )
            compact_horizons[horizon] = {
                key: value
                for key, value in payload.items()
                if key
                not in (
                    "membership_rows",
                    "repository_rows",
                    "agent_rows",
                )
            }
        compact_lanes[lane_id] = {
            "lane_id": lane_id,
            "identities": dict(_mapping(lane, "identities")),
            "horizons": compact_horizons,
        }
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "reproduction": {
            "byte_identical_second_run": True,
            "result_digest": result_a.get("result_digest"),
        },
        "lanes": compact_lanes,
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
        raise ValueError("modern portability result is invalid")


def validate_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    body = {key: value for key, value in summary.items() if key != "summary_digest"}
    if (
        summary.get("schema_version") != SUMMARY_SCHEMA
        or summary.get("plan_digest") != plan.get("plan_digest")
        or summary.get("summary_digest") != canonical_digest(body)
        or _mapping(summary, "implementation").get("portability_file_sha256")
        != _file_sha256(Path(__file__))
    ):
        raise ValueError("modern portability summary is invalid")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_value(value: object, label: str) -> Mapping[str, Any]:
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


def _unique_strings(value: object, label: str) -> tuple[str, ...]:
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


def _mean(values: Any) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(float(value) for value in rows) / len(rows)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument("--output", type=Path, required=True)

    summary = subparsers.add_parser("summarize")
    summary.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summary.add_argument("--result-a", type=Path, default=DEFAULT_RESULT_A)
    summary.add_argument("--result-b", type=Path, default=DEFAULT_RESULT_B)
    summary.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
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
