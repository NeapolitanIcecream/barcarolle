#!/usr/bin/env python3
"""Run exact finite-horizon cached-target assembly experiments."""

from __future__ import annotations

# NumPy and SciPy are supplied by the execution lock's reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from importlib.metadata import version
import json
from math import comb
from pathlib import Path
import platform
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    _random_outcome_calibration,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    _frame_identity,
    _visible_task_priorities,
    adanormalhedge_forecast,
    create_adanormalhedge_state,
    load_addendum as load_parent_addendum,
    load_execution_amendment as load_parent_execution_amendment,
    load_execution_lock as load_parent_execution_lock,
    load_plan as load_parent_plan,
    response_expert_forecasts,
    select_cached_scalar_indices,
    update_adanormalhedge,
)
from examples.surrogate_gate_audit.study import (  # noqa: E402
    AuditInputs,
    _alg_007_memberships,
    _horizon_frame,
    _load_inputs,
    _loss_row,
    _number,
    _repository_bootstrap,
    _repository_summary,
    _summarize_rows,
    load_audit_plan,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_LOCK = HERE / "execution-lock.json"
PLAN_SCHEMA = "barcarolle_finite_horizon_cached_assembly_plan_v1"
LOCK_SCHEMA = "barcarolle_finite_horizon_cached_assembly_execution_lock_v1"
MEMBERSHIP_SCHEMA = "barcarolle_finite_horizon_cached_assembly_memberships_v1"
RESULT_SCHEMA = "barcarolle_finite_horizon_cached_assembly_results_v1"
ALGORITHM_IDS = ("ALG-018C", "ALG-018C-P")
BOUND_FILE_PATHS = frozenset(
    {
        "examples/finite_horizon_cached_assembly/plan.json",
        "examples/finite_horizon_cached_assembly/study.py",
        "examples/prequential_response_assembly/execution-lock.json",
        "tests/test_finite_horizon_cached_assembly.py",
    }
)


@dataclass(frozen=True)
class FiniteHorizonAction:
    """One exact finite-horizon success-count action."""

    q: int
    risk: Fraction
    weights: tuple[Fraction, ...]
    feasible_q: tuple[int, ...]


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and validate the frozen finite-horizon plan."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("finite-horizon cached assembly plan is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if payload.get("plan_digest") != expected:
        raise ValueError("finite-horizon cached assembly plan digest changed")
    contract = _mapping(payload, "research_contract")
    candidate = _mapping(payload, "candidate")
    ablation = _mapping(payload, "fixed_ablation")
    resources = _mapping(payload, "resource_boundary")
    if (
        payload.get("study_id") != "finite-horizon-cached-assembly-2026-07-29"
        or contract.get("selection_budget_tasks") != 10
        or contract.get("minimum_initial_history_tasks") != 20
        or candidate.get("algorithm_id") != ALGORITHM_IDS[0]
        or ablation.get("algorithm_id") != ALGORITHM_IDS[1]
        or tuple(
            _required_string(item, "name")
            for item in _mapping_sequence(payload, "golden_cases")
        )
        != (
            "symmetric_h5",
            "symmetric_h10",
            "jeffreys_plugin_separation",
            "complement_symmetry",
            "horizon_sensitivity",
            "inventory_clamp",
        )
    ):
        raise ValueError("finite-horizon cached assembly contract changed")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "embedding_api_calls",
        "sealed_holdout_reads",
        "core_schema_or_service_changes",
    ):
        if resources.get(key) != 0:
            raise ValueError("finite-horizon resource boundary changed")
    return payload


def load_execution_lock(
    path: Path = DEFAULT_LOCK,
    *,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Load the implementation and transitive parent-source lock."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != LOCK_SCHEMA:
        raise ValueError("finite-horizon execution lock is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "lock_digest"}
    )
    if payload.get("lock_digest") != expected:
        raise ValueError("finite-horizon execution lock digest changed")
    parent_plan = load_parent_plan()
    parent_addendum = load_parent_addendum(plan=parent_plan)
    parent_amendment = load_parent_execution_amendment(
        plan=parent_plan,
        addendum=parent_addendum,
    )
    parent_lock = load_parent_execution_lock(
        plan=parent_plan,
        addendum=parent_addendum,
        execution_amendment=parent_amendment,
    )
    if payload.get("plan_digest") != plan.get("plan_digest") or payload.get(
        "parent_execution_lock_digest"
    ) != parent_lock.get("lock_digest"):
        raise ValueError("finite-horizon execution lock binding changed")
    bound_files = _mapping_sequence(payload, "bound_files")
    paths = tuple(_required_string(item, "path") for item in bound_files)
    if len(paths) != len(set(paths)) or set(paths) != BOUND_FILE_PATHS:
        raise ValueError("finite-horizon bound-file set changed")
    for item in bound_files:
        relative = _required_string(item, "path")
        actual = hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest()
        if actual != _required_string(item, "sha256"):
            raise ValueError(f"finite-horizon bound file changed: {relative}")
    runtime = _mapping(payload, "runtime")
    actual_runtime = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy_version": version("numpy"),
        "scipy_version": version("scipy"),
    }
    if runtime != actual_runtime:
        raise ValueError("finite-horizon execution runtime changed")
    if _mapping(payload, "frames") != _mapping(parent_lock, "frames"):
        raise ValueError("finite-horizon execution frame changed")
    return payload


def jeffreys_weights(n: int, s: int, horizon: int) -> tuple[Fraction, ...]:
    """Return exact unnormalized Beta-Binomial predictive weights."""
    _validate_counts(n, s, horizon, 1)
    a = Fraction(2 * s + 1, 2)
    b = Fraction(2 * (n - s) + 1, 2)
    weights = [Fraction(1)]
    for k in range(horizon):
        weights.append(
            weights[-1] * Fraction(horizon - k, k + 1) * (a + k) / (b + horizon - k - 1)
        )
    return tuple(weights)


def plugin_weights(n: int, s: int, horizon: int) -> tuple[Fraction, ...]:
    """Return exact unnormalized Binomial plug-in predictive weights."""
    _validate_counts(n, s, horizon, 1)
    failures = n - s
    return tuple(
        Fraction(comb(horizon, k) * s**k * failures ** (horizon - k))
        for k in range(horizon + 1)
    )


def select_jeffreys_action(
    n: int,
    s: int,
    horizon: int,
    budget: int,
    *,
    ignore_inventory: bool = False,
) -> FiniteHorizonAction:
    """Choose the exact Jeffreys posterior-predictive absolute-loss action."""
    _validate_counts(n, s, horizon, budget)
    weights = jeffreys_weights(n, s, horizon)
    feasible = _feasible_q(n, s, budget, ignore_inventory=ignore_inventory)
    return _select_action(
        weights,
        feasible,
        horizon=horizon,
        budget=budget,
        tie_distance=lambda q: abs(2 * q * (n + 1) - budget * (2 * s + 1)),
    )


def select_plugin_action(
    n: int,
    s: int,
    horizon: int,
    budget: int,
    *,
    ignore_inventory: bool = False,
) -> FiniteHorizonAction:
    """Choose the exact plug-in Binomial absolute-loss action."""
    _validate_counts(n, s, horizon, budget)
    weights = plugin_weights(n, s, horizon)
    feasible = _feasible_q(n, s, budget, ignore_inventory=ignore_inventory)
    return _select_action(
        weights,
        feasible,
        horizon=horizon,
        budget=budget,
        tie_distance=lambda q: abs(q * n - budget * s),
    )


def select_fixed_success_count_indices(
    outcomes: Sequence[int],
    q: int,
    *,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> tuple[int, ...]:
    """Materialize an exact success count with the frozen visible priority."""
    values = tuple(outcomes)
    order = tuple(created_order)
    if (
        len(values) != len(order)
        or isinstance(q, bool)
        or not isinstance(q, int)
        or isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget <= 0
        or budget > len(values)
        or not 0 <= q <= budget
        or any(value not in (0, 1) for value in values)
    ):
        raise ValueError("fixed-success materializer inputs are invalid")
    priorities = _visible_task_priorities(order)

    def ranked(response: int) -> list[int]:
        return sorted(
            (index for index, value in enumerate(values) if value == response),
            key=lambda index: (priorities[index], order[index][1]),
            reverse=True,
        )

    successes = ranked(1)
    failures = ranked(0)
    if len(successes) < q or len(failures) < budget - q:
        raise ValueError("fixed-success materializer exceeds inventory")
    selected = tuple(sorted((*successes[:q], *failures[: budget - q])))
    if (
        len(selected) != budget
        or len(set(selected)) != budget
        or sum(values[index] for index in selected) != q
    ):
        raise RuntimeError("fixed-success materializer invariant failed")
    return selected


def materialize_memberships(
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Materialize frozen memberships without computing candidate losses."""
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    inputs = _load_inputs(load_audit_plan())
    _validate_source_bindings(plan, lock, inputs)
    horizons = _build_horizon_payloads(plan, inputs)
    artifact: dict[str, Any] = {
        "schema_version": MEMBERSHIP_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "algorithm_ids": list(ALGORITHM_IDS),
        "horizons": horizons,
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
        },
    }
    artifact["membership_digest"] = canonical_digest(artifact)
    return artifact


def verify_memberships(
    payload: Mapping[str, Any],
    *,
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> None:
    """Recompute and verify every finite-horizon membership."""
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    candidate = dict(payload)
    digest = candidate.pop("membership_digest", None)
    if canonical_digest(candidate) != digest:
        raise ValueError("finite-horizon membership digest changed")
    if (
        payload.get("schema_version") != MEMBERSHIP_SCHEMA
        or payload.get("study_id") != plan.get("study_id")
        or payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("execution_lock_digest") != lock.get("lock_digest")
        or tuple(payload.get("algorithm_ids", ())) != ALGORITHM_IDS
        or payload.get("resource_use")
        != {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
        }
    ):
        raise ValueError("finite-horizon membership binding changed")
    inputs = _load_inputs(load_audit_plan())
    _validate_source_bindings(plan, lock, inputs)
    expected = _build_horizon_payloads(plan, inputs)
    if payload.get("horizons") != expected:
        raise ValueError("finite-horizon membership replay changed")


def score_memberships(
    memberships: Mapping[str, Any],
    *,
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Score frozen memberships with repository-first pass-rate MAE."""
    verify_memberships(
        memberships,
        plan_path=plan_path,
        lock_path=lock_path,
    )
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    inputs = _load_inputs(load_audit_plan())
    protocol = _mapping(plan, "statistical_protocol")
    bootstrap_plan = _mapping(protocol, "repository_bootstrap")
    random_plan = _mapping(protocol, "random")
    results: dict[str, dict[str, Any]] = {
        algorithm_id: {} for algorithm_id in ALGORITHM_IDS
    }
    for horizon in (5, 10):
        origins_by_repository, repository_ids, deep_ids = _horizon_frame(
            inputs.data.tasks,
            inputs.selector_plan,
            horizon,
        )
        origin_lookup = {
            origin.origin_id: origin
            for repository_id in repository_ids
            for origin in origins_by_repository[repository_id]
        }
        raw_rows = _mapping_sequence(
            _mapping(_mapping(memberships, "horizons"), str(horizon)),
            "rows",
        )
        configuration_index = {
            value: index for index, value in enumerate(inputs.data.configuration_ids)
        }
        rows_by_algorithm: dict[str, list[Mapping[str, object]]] = {
            algorithm_id: [] for algorithm_id in ALGORITHM_IDS
        }
        for row in raw_rows:
            repository_id = _required_string(row, "repository_id")
            origin = origin_lookup[_required_string(row, "origin_id")]
            held_out = configuration_index[
                _required_string(row, "target_configuration_id")
            ]
            history_indices = tuple(
                inputs.data.task_index[task.instance_id] for task in origin.history
            )
            future_indices = tuple(
                inputs.data.task_index[task.instance_id] for task in origin.future
            )
            row_memberships = _mapping(row, "memberships")
            for algorithm_id in ALGORITHM_IDS:
                rows_by_algorithm[algorithm_id].append(
                    _loss_row(
                        inputs,
                        repository_id=repository_id,
                        origin=origin,
                        held_out=held_out,
                        candidate=tuple(
                            inputs.data.task_index[task_id]
                            for task_id in row_memberships[algorithm_id]
                        ),
                        full=history_indices,
                        controls={
                            control_id: tuple(
                                inputs.data.task_index[task_id]
                                for task_id in row_memberships[control_id]
                            )
                            for control_id in (
                                "cached_quantized_full",
                                "ALG-015C",
                                "ordinary_recency",
                                "ALG-007",
                            )
                        },
                        future=future_indices,
                    )
                )
        seed = int(bootstrap_plan["h5_seed" if horizon == 5 else "h10_seed"])
        random_seed = int(random_plan["h5_seed" if horizon == 5 else "h10_seed"])
        for algorithm_id, rows in rows_by_algorithm.items():
            summary = _summarize_rows(
                rows,
                repository_ids,
                deep_ids,
                inputs.configuration_metadata,
                inputs.selector_plan,
            )
            summary["repository_bootstrap_vs_full"] = _repository_bootstrap(
                rows,
                repository_ids,
                resamples=int(bootstrap_plan["resamples"]),
                seed=seed,
            )
            paired_rows = _rows_against_control(rows, "cached_quantized_full")
            summary["primary_control_paired"] = {
                "wide": _repository_summary(paired_rows, repository_ids),
                "deep": _repository_summary(paired_rows, deep_ids),
                "repository_bootstrap": _repository_bootstrap(
                    paired_rows,
                    repository_ids,
                    resamples=int(bootstrap_plan["resamples"]),
                    seed=seed,
                ),
            }
            wide = _mapping(summary, "wide")
            summary["random_calibration"] = _random_outcome_calibration(
                origins_by_repository,
                repository_ids,
                inputs.outcome_maps,
                inputs.data.configuration_ids,
                budget=10,
                draws=int(random_plan["draws"]),
                seed=random_seed,
                candidate_difference=float(wide["difference"]),
            )
            summary["q_diagnostics"] = _q_diagnostics(raw_rows, algorithm_id)
            results[algorithm_id][str(horizon)] = summary
        control_rows = _rows_against_full(
            rows_by_algorithm[ALGORITHM_IDS[0]],
            "cached_quantized_full",
        )
        control_replay = float(
            _repository_summary(control_rows, repository_ids)["difference"]
        )
        expected_control = float(
            _mapping(plan, "source_bindings")[
                "observed_cached_control_h5_difference"
                if horizon == 5
                else "observed_cached_control_h10_difference"
            ]
        )
        if abs(control_replay - expected_control) > 1e-12:
            raise ValueError("cached primary-control source replay changed")
        for algorithm_id in ALGORITHM_IDS:
            results[algorithm_id][str(horizon)]["primary_control_minus_full_replay"] = (
                control_replay
            )
    candidate_progress = all(
        float(
            _mapping(
                _mapping(results[ALGORITHM_IDS[0]], str(horizon)),
                "primary_control_paired",
            )["wide"]["difference"]
        )
        < 0.0
        for horizon in (5, 10)
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "membership_digest": memberships.get("membership_digest"),
        "algorithms": results,
        "decision": {
            "ALG-018C_beats_primary_control_both_horizons": candidate_progress,
            "terminal_state": (
                "finite_horizon_correction_retained"
                if candidate_progress
                else "finite_horizon_correction_closed"
            ),
            "ALG-018C-P_status": "required_mechanism_ablation",
        },
        "claim_boundary": plan.get("claim_boundary"),
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
        },
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _select_action(
    weights: tuple[Fraction, ...],
    feasible: tuple[int, ...],
    *,
    horizon: int,
    budget: int,
    tie_distance: Any,
) -> FiniteHorizonAction:
    candidates = []
    for q in feasible:
        risk = sum(
            (
                weight * abs(horizon * q - budget * k)
                for k, weight in enumerate(weights)
            ),
            Fraction(),
        )
        candidates.append((risk, tie_distance(q), q))
    risk, _, q = min(candidates)
    return FiniteHorizonAction(q=q, risk=risk, weights=weights, feasible_q=feasible)


def _validate_counts(n: int, s: int, horizon: int, budget: int) -> None:
    if (
        any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (n, s, horizon, budget)
        )
        or n <= 0
        or horizon <= 0
        or budget <= 0
        or budget > n
        or not 0 <= s <= n
    ):
        raise ValueError("finite-horizon counts are invalid")


def _feasible_q(
    n: int,
    s: int,
    budget: int,
    *,
    ignore_inventory: bool,
) -> tuple[int, ...]:
    if ignore_inventory:
        return tuple(range(budget + 1))
    return tuple(range(max(0, budget - (n - s)), min(budget, s) + 1))


def _fraction_payload(value: Fraction) -> Mapping[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _action_payload(
    action: FiniteHorizonAction,
    unconstrained: FiniteHorizonAction,
) -> Mapping[str, Any]:
    return {
        "q": action.q,
        "risk": _fraction_payload(action.risk),
        "feasible_q_min": action.feasible_q[0],
        "feasible_q_max": action.feasible_q[-1],
        "unconstrained_q": unconstrained.q,
        "inventory_changed_action": action.q != unconstrained.q,
        "at_lower_inventory_bound": action.q == action.feasible_q[0],
        "at_upper_inventory_bound": action.q == action.feasible_q[-1],
    }


def _build_horizon_payloads(
    plan: Mapping[str, Any],
    inputs: AuditInputs,
) -> Mapping[str, Any]:
    budget = int(_mapping(plan, "research_contract")["selection_budget_tasks"])
    horizon_payloads: dict[str, Any] = {}
    for horizon in (5, 10):
        origins_by_repository, repository_ids, deep_ids = _horizon_frame(
            inputs.data.tasks,
            inputs.selector_plan,
            horizon,
        )
        alg_007 = _alg_007_memberships(
            inputs.alg_007_task_space,
            horizon,
            repository_ids,
        )
        rows = []
        for repository_id in repository_ids:
            ada_state = create_adanormalhedge_state(len(inputs.data.configuration_ids))
            for origin in origins_by_repository[repository_id]:
                history_indices = tuple(
                    inputs.data.task_index[task.instance_id] for task in origin.history
                )
                future_indices = tuple(
                    inputs.data.task_index[task.instance_id] for task in origin.future
                )
                history = inputs.data.outcomes[list(history_indices), :]
                experts = response_expert_forecasts(history, horizon=horizon)
                ada_forecast, _ = adanormalhedge_forecast(ada_state, experts)
                created_order = tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                )
                history_ids = tuple(task.instance_id for task in origin.history)
                for target, configuration_id in enumerate(
                    inputs.data.configuration_ids
                ):
                    outcomes = tuple(int(value) for value in history[:, target])
                    n = len(outcomes)
                    s = sum(outcomes)
                    jeffreys = select_jeffreys_action(n, s, horizon, budget)
                    jeffreys_unconstrained = select_jeffreys_action(
                        n,
                        s,
                        horizon,
                        budget,
                        ignore_inventory=True,
                    )
                    plugin = select_plugin_action(n, s, horizon, budget)
                    plugin_unconstrained = select_plugin_action(
                        n,
                        s,
                        horizon,
                        budget,
                        ignore_inventory=True,
                    )
                    candidate_positions = select_fixed_success_count_indices(
                        outcomes,
                        jeffreys.q,
                        budget=budget,
                        created_order=created_order,
                    )
                    plugin_positions = select_fixed_success_count_indices(
                        outcomes,
                        plugin.q,
                        budget=budget,
                        created_order=created_order,
                    )
                    full_positions = select_cached_scalar_indices(
                        outcomes,
                        s / n,
                        budget=budget,
                        created_order=created_order,
                    )
                    ada_positions = select_cached_scalar_indices(
                        outcomes,
                        float(ada_forecast[target]),
                        budget=budget,
                        created_order=created_order,
                    )

                    def ids(positions: Sequence[int]) -> list[str]:
                        return [history_ids[position] for position in positions]

                    rows.append(
                        {
                            "repository_id": repository_id,
                            "origin_id": origin.origin_id,
                            "target_configuration_id": configuration_id,
                            "history_task_count": n,
                            "history_success_count": s,
                            "horizon": horizon,
                            "budget": budget,
                            "actions": {
                                ALGORITHM_IDS[0]: _action_payload(
                                    jeffreys,
                                    jeffreys_unconstrained,
                                ),
                                ALGORITHM_IDS[1]: _action_payload(
                                    plugin,
                                    plugin_unconstrained,
                                ),
                                "cached_quantized_full_q": sum(
                                    outcomes[index] for index in full_positions
                                ),
                            },
                            "memberships": {
                                ALGORITHM_IDS[0]: ids(candidate_positions),
                                ALGORITHM_IDS[1]: ids(plugin_positions),
                                "cached_quantized_full": ids(full_positions),
                                "ALG-015C": ids(ada_positions),
                                "ordinary_recency": list(history_ids[-budget:]),
                                "ALG-007": list(alg_007[origin.origin_id]),
                            },
                        }
                    )
                observed = inputs.data.outcomes[
                    list(future_indices),
                    :,
                ].mean(axis=0)
                update_adanormalhedge(ada_state, experts, observed)
        horizon_payloads[str(horizon)] = {
            "repository_ids": list(repository_ids),
            "deep_repository_ids": list(deep_ids),
            "origin_count": sum(
                len(origins_by_repository[repository_id])
                for repository_id in repository_ids
            ),
            "target_row_count": len(rows),
            "membership_digests": {
                algorithm_id: _algorithm_membership_digest(rows, algorithm_id)
                for algorithm_id in ALGORITHM_IDS
            },
            "rows": rows,
            "rows_digest": canonical_digest(rows),
        }
    return horizon_payloads


def _algorithm_membership_digest(
    rows: Sequence[Mapping[str, Any]],
    algorithm_id: str,
) -> str:
    return canonical_digest(
        [
            {
                "repository_id": row["repository_id"],
                "origin_id": row["origin_id"],
                "target_configuration_id": row["target_configuration_id"],
                "task_ids": _mapping(row, "memberships")[algorithm_id],
            }
            for row in rows
        ]
    )


def _rows_against_control(
    rows: Sequence[Mapping[str, object]],
    control_id: str,
) -> list[Mapping[str, object]]:
    transformed = []
    for row in rows:
        candidate_loss = _number(row["candidate_loss"], "candidate loss")
        control_loss = _number(
            _mapping(row, "control_losses")[control_id],
            f"{control_id} loss",
        )
        transformed.append(
            {
                "repository_id": row["repository_id"],
                "origin_id": row["origin_id"],
                "configuration_id": row["configuration_id"],
                "candidate_loss": candidate_loss,
                "full_loss": control_loss,
                "difference": candidate_loss - control_loss,
                "control_losses": {},
            }
        )
    return transformed


def _rows_against_full(
    rows: Sequence[Mapping[str, object]],
    control_id: str,
) -> list[Mapping[str, object]]:
    transformed = []
    for row in rows:
        control_loss = _number(
            _mapping(row, "control_losses")[control_id],
            f"{control_id} loss",
        )
        full_loss = _number(row["full_loss"], "full loss")
        transformed.append(
            {
                "repository_id": row["repository_id"],
                "origin_id": row["origin_id"],
                "configuration_id": row["configuration_id"],
                "candidate_loss": control_loss,
                "full_loss": full_loss,
                "difference": control_loss - full_loss,
                "control_losses": {},
            }
        )
    return transformed


def _q_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    algorithm_id: str,
) -> Mapping[str, Any]:
    q_values = []
    control_values = []
    changed_by_inventory = 0
    lower = 0
    upper = 0
    for row in rows:
        actions = _mapping(row, "actions")
        action = _mapping(actions, algorithm_id)
        q = int(action["q"])
        q_values.append(q)
        control_values.append(int(actions["cached_quantized_full_q"]))
        changed_by_inventory += bool(action["inventory_changed_action"])
        lower += bool(action["at_lower_inventory_bound"])
        upper += bool(action["at_upper_inventory_bound"])
    changes = [q - control for q, control in zip(q_values, control_values, strict=True)]
    return {
        "cell_count": len(q_values),
        "q_distribution": {
            str(q): count for q, count in sorted(Counter(q_values).items())
        },
        "q_changed_from_primary_control_count": sum(value != 0 for value in changes),
        "q_increased_count": sum(value > 0 for value in changes),
        "q_decreased_count": sum(value < 0 for value in changes),
        "inventory_changed_action_count": changed_by_inventory,
        "at_lower_inventory_bound_count": lower,
        "at_upper_inventory_bound_count": upper,
    }


def _validate_source_bindings(
    plan: Mapping[str, Any],
    lock: Mapping[str, Any],
    inputs: AuditInputs,
) -> None:
    source = _mapping(plan, "source_bindings")
    parent_plan = load_parent_plan()
    parent_addendum = load_parent_addendum(plan=parent_plan)
    parent_amendment = load_parent_execution_amendment(
        plan=parent_plan,
        addendum=parent_addendum,
    )
    parent_lock = load_parent_execution_lock(
        plan=parent_plan,
        addendum=parent_addendum,
        execution_amendment=parent_amendment,
    )
    logical = _mapping(parent_lock, "logical_bindings")
    if (
        source.get("parent_prequential_plan_digest") != parent_plan.get("plan_digest")
        or source.get("parent_prequential_execution_lock_digest")
        != parent_lock.get("lock_digest")
        or lock.get("parent_execution_lock_digest") != parent_lock.get("lock_digest")
        or source.get("multi_swe_contract_digest")
        != logical.get("multi_swe_contract_digest")
        or source.get("panel_digest") != logical.get("panel_digest")
        or source.get("resolved_outcome_digest")
        != logical.get("resolved_outcome_digest")
        or source.get("task_time_projection_digest")
        != logical.get("task_time_projection_digest")
    ):
        raise ValueError("finite-horizon source binding changed")
    for horizon in (5, 10):
        if _mapping(_mapping(lock, "frames"), str(horizon)) != _frame_identity(
            inputs, horizon
        ):
            raise ValueError(f"finite-horizon H{horizon} frame changed")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise ValueError(f"{key} must be an object")
    return item


def _mapping_sequence(
    value: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    items = value.get(key)
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise ValueError(f"{key} must be a list of objects")
    return tuple(items)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_plan = subparsers.add_parser("verify-plan")
    verify_plan.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    materialize.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    materialize.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify-memberships")
    verify.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    verify.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    verify.add_argument("--input", type=Path, required=True)
    score = subparsers.add_parser("score")
    score.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    score.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    score.add_argument("--memberships", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one finite-horizon study command."""
    args = _build_parser().parse_args(argv)
    if args.command == "verify-plan":
        print(load_plan(args.plan)["plan_digest"])
        return 0
    if args.command == "materialize":
        result = materialize_memberships(args.plan, args.lock)
        _write_json(args.output, result)
        print(result["membership_digest"])
        return 0
    if args.command == "verify-memberships":
        verify_memberships(
            _load_mapping(args.input),
            plan_path=args.plan,
            lock_path=args.lock,
        )
        print("memberships verified")
        return 0
    if args.command == "score":
        result = score_memberships(
            _load_mapping(args.memberships),
            plan_path=args.plan,
            lock_path=args.lock,
        )
        _write_json(args.output, result)
        print(result["result_digest"])
        return 0
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
