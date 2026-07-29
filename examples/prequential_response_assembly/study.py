#!/usr/bin/env python3
"""Run cutoff-safe response forecasting and budget-ten assembly experiments."""

from __future__ import annotations

# NumPy and SciPy are supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
from math import expm1, isfinite, log, log1p
from numbers import Real
from pathlib import Path
import platform
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.surrogate_gate_audit.study import (  # noqa: E402
    AuditInputs,
    _alg_007_memberships,
    _horizon_frame,
    _load_inputs,
    _loss_row,
    _repository_bootstrap,
    _summarize_rows,
    load_audit_plan,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    _random_outcome_calibration,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_ADDENDUM = HERE / "plan-addendum-1.json"
DEFAULT_EXECUTION_AMENDMENT = HERE / "execution-amendment-1.json"
DEFAULT_LOCK = HERE / "execution-lock.json"
PLAN_SCHEMA = "barcarolle_prequential_response_assembly_plan_v1"
ADDENDUM_SCHEMA = "barcarolle_prequential_response_assembly_addendum_v1"
EXECUTION_AMENDMENT_SCHEMA = (
    "barcarolle_prequential_response_assembly_execution_amendment_v1"
)
LOCK_SCHEMA = "barcarolle_prequential_response_assembly_execution_lock_v1"
MEMBERSHIP_SCHEMA = "barcarolle_prequential_response_assembly_memberships_v1"
RESULT_SCHEMA = "barcarolle_prequential_response_assembly_results_v1"
NUMPY_VERSION = "2.5.1"
SCIPY_VERSION = "1.16.3"
OBJECTIVE_REPLAY_TOLERANCE = 1e-7
EXPERT_IDS = (
    "full_history",
    "latest_H",
    "latest_2H",
    "linear_drift",
)
VISIBLE_ALGORITHMS = ("ALG-015C", "ALG-015U", "ALG-016U")
BOUND_FILE_PATHS = frozenset(
    {
        "examples/prequential_response_assembly/plan.json",
        "examples/prequential_response_assembly/plan-addendum-1.json",
        "examples/prequential_response_assembly/execution-amendment-1.json",
        "examples/prequential_response_assembly/study.py",
        "tests/test_prequential_response_assembly.py",
        "examples/surrogate_gate_audit/plan.json",
        "examples/surrogate_gate_audit/plan-amendment-1.json",
        "examples/surrogate_gate_audit/plan-amendment-2.json",
        "examples/surrogate_gate_audit/study.py",
        "examples/multi_swe_research/contract.json",
        "examples/multi_swe_research/selector-plan.json",
        "examples/multi_swe_research/semantic_selector.py",
        "examples/multi_repository_study/public_replay.py",
        "examples/multi_swe_research/evidence/task-times.jsonl",
        "examples/multi_swe_research/evidence/panel-summary.json",
        "examples/multi_swe_research/evidence/resolved-outcomes.jsonl",
        "outputs/research/2026-07-28-multi-swe-task-space-results.json",
    }
)


@dataclass
class AdaNormalHedgeState:
    """Coordinate-wise AdaNormalHedge state."""

    regret: Any
    absolute_regret: Any


@dataclass(frozen=True)
class ExactAssembly:
    """One exact response-pattern assembly and its solver diagnostics."""

    indices: tuple[int, ...]
    objective: float
    response_pattern_count: int
    mip_node_count: int | None
    mip_gap: float | None


@dataclass(frozen=True)
class ChangePointForecast:
    """Posterior predictive response rates and compact diagnostics."""

    mixture: Any
    map_run: Any
    anchor: Any
    run_length_probabilities: Any
    map_run_length: int


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and validate the frozen research contract."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("prequential response plan schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if payload.get("plan_digest") != expected:
        raise ValueError("prequential response plan digest does not match")
    resources = _mapping(payload, "resource_boundary")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "embedding_api_calls",
        "sealed_holdout_reads",
        "core_schema_or_service_changes",
    ):
        if resources.get(key) != 0:
            raise ValueError("prequential response resource boundary changed")
    if (
        tuple(
            _required_string(item, "algorithm_id")
            for item in _mapping_sequence(payload, "portfolio")
            if item.get("algorithm_id") in VISIBLE_ALGORITHMS
        )
        != VISIBLE_ALGORITHMS
    ):
        raise ValueError("prequential response visible portfolio changed")
    fixed = _mapping(payload, "fixed_facts")
    if (
        fixed.get("task_count") != 1632
        or fixed.get("configuration_count") != 36
        or fixed.get("h5_origin_count") != 221
        or fixed.get("h10_origin_count") != 107
        or fixed.get("selection_budget_tasks") != 10
    ):
        raise ValueError("prequential response fixed facts changed")
    return payload


def load_addendum(
    path: Path = DEFAULT_ADDENDUM,
    *,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Load the pre-score semantic closure."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != ADDENDUM_SCHEMA:
        raise ValueError("prequential response addendum schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "addendum_digest"}
    )
    if payload.get("addendum_digest") != expected:
        raise ValueError("prequential response addendum digest changed")
    if (
        payload.get("parent_plan_digest") != plan.get("plan_digest")
        or payload.get("status") != "pre_score_semantic_closure"
        or _mapping(payload, "result_visibility").get("new_candidate_scores_read")
        is not False
        or _mapping(payload, "alg_017_decision").get("status")
        != "deferred_before_any_new_candidate_score"
    ):
        raise ValueError("prequential response addendum binding changed")
    return payload


def load_execution_lock(
    path: Path = DEFAULT_LOCK,
    *,
    plan: Mapping[str, Any],
    addendum: Mapping[str, Any] | None = None,
    execution_amendment: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Load the implementation/source lock created before scoring."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != LOCK_SCHEMA:
        raise ValueError("prequential response execution lock is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "lock_digest"}
    )
    if payload.get("lock_digest") != expected:
        raise ValueError("prequential response execution lock digest changed")
    active_addendum = load_addendum(plan=plan) if addendum is None else addendum
    active_execution_amendment = (
        load_execution_amendment(
            plan=plan,
            addendum=active_addendum,
        )
        if execution_amendment is None
        else execution_amendment
    )
    if (
        payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("addendum_digest") != active_addendum.get("addendum_digest")
        or payload.get("execution_amendment_digest")
        != active_execution_amendment.get("amendment_digest")
        or payload.get("supersedes_lock_digest")
        != active_execution_amendment.get("parent_lock_digest")
    ):
        raise ValueError("execution lock does not bind the frozen contract")
    bound_files = _mapping_sequence(payload, "bound_files")
    paths = tuple(_required_string(item, "path") for item in bound_files)
    if len(paths) != len(set(paths)) or set(paths) != BOUND_FILE_PATHS:
        raise ValueError("execution-lock bound-file set changed")
    for item in bound_files:
        relative = _required_string(item, "path")
        actual = hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest()
        if actual != _required_string(item, "sha256"):
            raise ValueError(f"execution-lock file changed: {relative}")
    runtime = _mapping(payload, "runtime")
    actual_runtime = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy_version": version("numpy"),
        "scipy_version": version("scipy"),
    }
    if runtime != actual_runtime:
        raise ValueError("execution-lock runtime changed")
    frames = _mapping(payload, "frames")
    if set(frames) != {"5", "10"}:
        raise ValueError("execution-lock frame set changed")
    return payload


def load_execution_amendment(
    path: Path = DEFAULT_EXECUTION_AMENDMENT,
    *,
    plan: Mapping[str, Any],
    addendum: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Load the pre-score numerical replay correction."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != EXECUTION_AMENDMENT_SCHEMA:
        raise ValueError("execution amendment schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "amendment_digest"}
    )
    correction = _mapping(payload, "correction")
    visibility = _mapping(payload, "resource_visibility")
    if (
        payload.get("amendment_digest") != expected
        or payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("addendum_digest") != addendum.get("addendum_digest")
        or payload.get("status") != "pre_score_primary_replay_numeric_correction"
        or correction.get("primary_replay_tolerance") != OBJECTIVE_REPLAY_TOLERANCE
        or correction.get("secondary_replay_tolerance") != OBJECTIVE_REPLAY_TOLERANCE
        or visibility.get("membership_artifacts_written") != 0
        or visibility.get("candidate_scores_read") != 0
    ):
        raise ValueError("execution amendment binding changed")
    return payload


def create_adanormalhedge_state(coordinate_count: int) -> AdaNormalHedgeState:
    """Create zero-regret state for a fixed response-coordinate panel."""
    import numpy as np

    if (
        isinstance(coordinate_count, bool)
        or not isinstance(coordinate_count, int)
        or coordinate_count <= 0
    ):
        raise ValueError("AdaNormalHedge coordinate count is invalid")
    shape = (len(EXPERT_IDS), coordinate_count)
    return AdaNormalHedgeState(
        regret=np.zeros(shape, dtype=np.float64),
        absolute_regret=np.zeros(shape, dtype=np.float64),
    )


def adanormalhedge_weights(state: AdaNormalHedgeState) -> Any:
    """Return normalized parameter-free expert weights per coordinate."""
    import numpy as np

    regret = np.asarray(state.regret, dtype=np.float64)
    absolute = np.asarray(state.absolute_regret, dtype=np.float64)
    if (
        regret.shape != absolute.shape
        or regret.ndim != 2
        or regret.shape[0] != len(EXPERT_IDS)
        or np.any(absolute < 0.0)
        or not np.all(np.isfinite(regret))
        or not np.all(np.isfinite(absolute))
        or np.any(np.abs(regret) > absolute + 1e-10)
    ):
        raise ValueError("AdaNormalHedge state is invalid")

    log_weights = np.full(regret.shape, -np.inf, dtype=np.float64)
    for expert in range(regret.shape[0]):
        for coordinate in range(regret.shape[1]):
            r_value = float(regret[expert, coordinate])
            c_value = float(absolute[expert, coordinate])
            positive = max(r_value + 1.0, 0.0) ** 2 / (3.0 * (c_value + 1.0))
            negative = max(r_value - 1.0, 0.0) ** 2 / (3.0 * (c_value + 1.0))
            if positive <= negative:
                continue
            log_weights[expert, coordinate] = (
                positive + log(-expm1(negative - positive)) - log(2.0)
            )

    weights = np.zeros_like(log_weights)
    for coordinate in range(log_weights.shape[1]):
        values = log_weights[:, coordinate]
        finite = np.isfinite(values)
        if not bool(np.any(finite)):
            weights[:, coordinate] = 1.0 / len(EXPERT_IDS)
            continue
        maximum = float(values[finite].max())
        scaled = np.zeros(len(EXPERT_IDS), dtype=np.float64)
        scaled[finite] = np.exp(values[finite] - maximum)
        weights[:, coordinate] = scaled / scaled.sum()
    return weights


def response_expert_forecasts(history: Any, *, horizon: int) -> Any:
    """Build the four fixed scalar experts for each response coordinate."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    if (
        values.ndim != 2
        or len(values) < 2 * horizon
        or isinstance(horizon, bool)
        or horizon <= 0
        or not np.all((values == 0.0) | (values == 1.0))
    ):
        raise ValueError("response expert history is invalid")
    full = values.mean(axis=0)
    recent = values[-horizon:].mean(axis=0)
    recent_two = values[-2 * horizon :].mean(axis=0)
    previous = values[-2 * horizon : -horizon].mean(axis=0)
    linear = np.clip(recent + (recent - previous), 0.0, 1.0)
    return np.stack((full, recent, recent_two, linear), axis=0)


def adanormalhedge_forecast(
    state: AdaNormalHedgeState,
    expert_forecasts: Any,
) -> tuple[Any, Any]:
    """Combine fixed expert predictions without a learning-rate parameter."""
    import numpy as np

    experts = np.asarray(expert_forecasts, dtype=np.float64)
    weights = adanormalhedge_weights(state)
    if (
        experts.shape != weights.shape
        or np.any(experts < 0.0)
        or np.any(experts > 1.0)
        or not np.all(np.isfinite(experts))
    ):
        raise ValueError("AdaNormalHedge forecasts are invalid")
    return (weights * experts).sum(axis=0), weights


def update_adanormalhedge(
    state: AdaNormalHedgeState,
    expert_forecasts: Any,
    observed: Any,
) -> None:
    """Update coordinate-wise regrets after an earlier future block completes."""
    import numpy as np

    experts = np.asarray(expert_forecasts, dtype=np.float64)
    truth = np.asarray(observed, dtype=np.float64)
    weights = adanormalhedge_weights(state)
    if (
        experts.shape != weights.shape
        or truth.shape != (experts.shape[1],)
        or np.any(truth < 0.0)
        or np.any(truth > 1.0)
        or not np.all(np.isfinite(experts))
        or not np.all(np.isfinite(truth))
    ):
        raise ValueError("AdaNormalHedge update is invalid")
    expert_losses = np.abs(experts - truth[None, :])
    mixture_losses = (weights * expert_losses).sum(axis=0)
    instantaneous = mixture_losses[None, :] - expert_losses
    state.regret += instantaneous
    state.absolute_regret += np.abs(instantaneous)


def select_cached_scalar_indices(
    outcomes: Sequence[int],
    forecast: float,
    *,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> tuple[int, ...]:
    """Exactly match one cached Agent's scalar forecast at budget ten."""
    values = tuple(outcomes)
    order = tuple(created_order)
    if (
        len(values) != len(order)
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(values)
        or not isfinite(forecast)
        or not 0.0 <= forecast <= 1.0
        or any(value not in (0, 1) for value in values)
    ):
        raise ValueError("cached scalar selection inputs are invalid")
    priorities = _visible_task_priorities(order)
    cells = {
        response: sorted(
            (index for index, value in enumerate(values) if value == response),
            key=lambda index: (priorities[index], order[index][1]),
            reverse=True,
        )
        for response in (0, 1)
    }
    minimum_successes = max(0, budget - len(cells[0]))
    maximum_successes = min(budget, len(cells[1]))
    candidates = []
    for successes in range(minimum_successes, maximum_successes + 1):
        selected = tuple(
            sorted(
                (
                    *cells[1][:successes],
                    *cells[0][: budget - successes],
                )
            )
        )
        candidates.append(
            (
                abs(successes / budget - forecast),
                -sum(priorities[index] for index in selected),
                tuple(sorted(order[index][1] for index in selected)),
                selected,
            )
        )
    if not candidates:
        raise ValueError("cached scalar selection has no feasible composition")
    return min(candidates)[3]


def solve_exact_l1_assembly(
    visible_outcomes: Any,
    target: Any,
    *,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> ExactAssembly:
    """Solve exact response-vector assembly after pattern compression."""
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    values = np.asarray(visible_outcomes, dtype=np.float64)
    forecast = np.asarray(target, dtype=np.float64)
    order = tuple(created_order)
    if (
        values.ndim != 2
        or values.shape[0] != len(order)
        or forecast.shape != (values.shape[1],)
        or not values.shape[1]
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(values)
        or not np.all((values == 0.0) | (values == 1.0))
        or not np.all(np.isfinite(forecast))
        or np.any(forecast < 0.0)
        or np.any(forecast > 1.0)
    ):
        raise ValueError("exact L1 assembly inputs are invalid")

    priorities = _visible_task_priorities(order)
    groups: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for index, row in enumerate(values.astype(np.int8).tolist()):
        groups[tuple(int(value) for value in row)].append(index)
    for group in groups.values():
        group.sort(
            key=lambda index: (priorities[index], order[index][1]),
            reverse=True,
        )
    patterns = tuple(sorted(groups))
    eligible = tuple(
        index for pattern in patterns for index in groups[pattern][:budget]
    )
    response_patterns = tuple(
        tuple(int(value) for value in values[index]) for index in eligible
    )
    task_count = len(eligible)
    coordinate_count = values.shape[1]
    variable_count = task_count + coordinate_count

    objective = np.zeros(variable_count, dtype=np.float64)
    objective[task_count:] = 1.0 / coordinate_count
    integrality = np.zeros(variable_count, dtype=np.int8)
    integrality[:task_count] = 1
    lower = np.zeros(variable_count, dtype=np.float64)
    upper = np.full(variable_count, np.inf, dtype=np.float64)
    upper[:task_count] = 1.0
    matrix = np.zeros(
        (1 + 2 * coordinate_count, variable_count),
        dtype=np.float64,
    )
    constraint_lower = np.full(len(matrix), -np.inf, dtype=np.float64)
    constraint_upper = np.full(len(matrix), np.inf, dtype=np.float64)
    matrix[0, :task_count] = 1.0
    constraint_lower[0] = float(budget)
    constraint_upper[0] = float(budget)
    pattern_matrix = np.asarray(response_patterns, dtype=np.float64)
    for coordinate in range(coordinate_count):
        response = pattern_matrix[:, coordinate] / budget
        positive = 1 + 2 * coordinate
        negative = positive + 1
        matrix[positive, :task_count] = response
        matrix[positive, task_count + coordinate] = -1.0
        constraint_upper[positive] = forecast[coordinate]
        matrix[negative, :task_count] = -response
        matrix[negative, task_count + coordinate] = -1.0
        constraint_upper[negative] = -forecast[coordinate]

    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),  # pyright: ignore[reportArgumentType]
        constraints=LinearConstraint(
            matrix,
            constraint_lower,  # pyright: ignore[reportArgumentType]
            constraint_upper,  # pyright: ignore[reportArgumentType]
        ),
        options={"presolve": True, "mip_rel_gap": 0.0},
    )
    if not result.success or result.status != 0 or result.x is None:
        raise RuntimeError(
            "exact L1 assembly did not return a certified optimum: "
            f"status={result.status}, message={result.message}"
        )
    raw_flags = result.x[:task_count]
    flags = tuple(int(round(float(value))) for value in raw_flags)
    if sum(flags) != budget or any(
        abs(float(value) - flag) > 1e-5
        for value, flag in zip(raw_flags, flags, strict=True)
    ):
        raise RuntimeError("exact L1 assembly returned invalid binary flags")
    solver_objective = float(result.fun)
    primary_selected = tuple(
        eligible[position] for position, flag in enumerate(flags) if flag
    )
    primary_recomputed = float(
        np.abs(values[list(primary_selected)].mean(axis=0) - forecast).mean()
    )
    primary_objective = _certified_primary_objective(
        solver_objective,
        primary_recomputed,
    )

    secondary_matrix = np.vstack(
        (
            matrix,
            np.concatenate(
                (
                    np.zeros(task_count, dtype=np.float64),
                    np.ones(coordinate_count, dtype=np.float64),
                )
            )[None, :],
        )
    )
    secondary_lower = np.concatenate((constraint_lower, [-np.inf]))
    secondary_upper = np.concatenate(
        (
            constraint_upper,
            [coordinate_count * primary_objective],
        )
    )
    secondary_objective = np.zeros(variable_count, dtype=np.float64)
    secondary_objective[:task_count] = -np.asarray(
        [priorities[index] for index in eligible],
        dtype=np.float64,
    )
    secondary = milp(
        c=secondary_objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),  # pyright: ignore[reportArgumentType]
        constraints=LinearConstraint(
            secondary_matrix,
            secondary_lower,  # pyright: ignore[reportArgumentType]
            secondary_upper,  # pyright: ignore[reportArgumentType]
        ),
        options={"presolve": True, "mip_rel_gap": 0.0},
    )
    if not secondary.success or secondary.status != 0 or secondary.x is None:
        raise RuntimeError(
            "exact L1 secondary assembly did not return an optimum: "
            f"status={secondary.status}, message={secondary.message}"
        )
    secondary_flags = tuple(
        int(round(float(value))) for value in secondary.x[:task_count]
    )
    if sum(secondary_flags) != budget or any(
        abs(float(value) - flag) > 1e-5
        for value, flag in zip(
            secondary.x[:task_count],
            secondary_flags,
            strict=True,
        )
    ):
        maximum_error = max(
            abs(float(value) - flag)
            for value, flag in zip(
                secondary.x[:task_count],
                secondary_flags,
                strict=True,
            )
        )
        raise RuntimeError(
            "exact L1 secondary assembly returned invalid flags: "
            f"sum={sum(secondary_flags)}, maximum_error={maximum_error}, "
            f"message={secondary.message}"
        )
    selected = tuple(
        sorted(
            eligible[position] for position, flag in enumerate(secondary_flags) if flag
        )
    )
    recomputed = float(np.abs(values[list(selected)].mean(axis=0) - forecast).mean())
    if abs(recomputed - primary_objective) > OBJECTIVE_REPLAY_TOLERANCE:
        raise RuntimeError("exact L1 assembly objective changed after replay")
    gap_value = getattr(secondary, "mip_gap", None)
    node_value = getattr(secondary, "mip_node_count", None)
    return ExactAssembly(
        indices=selected,
        objective=recomputed,
        response_pattern_count=len(patterns),
        mip_node_count=(
            int(node_value)
            if node_value is not None and isfinite(float(node_value))
            else None
        ),
        mip_gap=(
            float(gap_value)
            if gap_value is not None and isfinite(float(gap_value))
            else None
        ),
    )


def _certified_primary_objective(
    solver_objective: float,
    feasible_recomputed: float,
) -> float:
    if (
        not isfinite(solver_objective)
        or not isfinite(feasible_recomputed)
        or abs(solver_objective - feasible_recomputed) > OBJECTIVE_REPLAY_TOLERANCE
    ):
        raise RuntimeError("exact L1 primary objective changed after replay")
    return feasible_recomputed


def shared_bocpd_forecast(
    history: Any,
    *,
    horizon: int,
) -> ChangePointForecast:
    """Forecast a visible response vector with empirical-Bayes BOCPD."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    if (
        values.ndim != 2
        or not len(values)
        or not values.shape[1]
        or isinstance(horizon, bool)
        or horizon <= 0
        or not np.all((values == 0.0) | (values == 1.0))
    ):
        raise ValueError("shared BOCPD history is invalid")
    anchor = (values.sum(axis=0) + 0.5) / (len(values) + 1.0)
    prior_mass = 10.0
    return shared_bocpd_forecast_with_prior(
        values,
        horizon=horizon,
        hazard=1.0 / (4.0 * horizon),
        alpha0=prior_mass * anchor,
        beta0=prior_mass * (1.0 - anchor),
        anchor=anchor,
    )


def shared_bocpd_forecast_with_prior(
    history: Any,
    *,
    horizon: int,
    hazard: float,
    alpha0: Any,
    beta0: Any,
    anchor: Any,
) -> ChangePointForecast:
    """Run the inclusive shared-run-length Beta-Bernoulli recursion."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    prior_alpha = np.asarray(alpha0, dtype=np.float64)
    prior_beta = np.asarray(beta0, dtype=np.float64)
    base_mean = np.asarray(anchor, dtype=np.float64)
    if (
        values.ndim != 2
        or not len(values)
        or prior_alpha.shape != (values.shape[1],)
        or prior_beta.shape != prior_alpha.shape
        or base_mean.shape != prior_alpha.shape
        or isinstance(horizon, bool)
        or horizon <= 0
        or not 0.0 <= hazard <= 1.0
        or np.any(prior_alpha <= 0.0)
        or np.any(prior_beta <= 0.0)
        or np.any(base_mean < 0.0)
        or np.any(base_mean > 1.0)
        or not np.all((values == 0.0) | (values == 1.0))
    ):
        raise ValueError("shared BOCPD prior inputs are invalid")

    first = values[0]
    log_probabilities = np.asarray([0.0], dtype=np.float64)
    alpha = (prior_alpha + first)[None, :]
    beta = (prior_beta + 1.0 - first)[None, :]
    for current in values[1:]:
        prior_total = prior_alpha + prior_beta
        change_log_likelihood = float(
            (
                current * np.log(prior_alpha / prior_total)
                + (1.0 - current) * np.log(prior_beta / prior_total)
            ).sum()
        )
        totals = alpha + beta
        growth_log_likelihood = (
            current[None, :] * np.log(alpha / totals)
            + (1.0 - current[None, :]) * np.log(beta / totals)
        ).sum(axis=1)
        log_masses = np.empty(len(log_probabilities) + 1, dtype=np.float64)
        log_masses[0] = (
            -np.inf if hazard == 0.0 else log(hazard)
        ) + change_log_likelihood
        log_masses[1:] = (
            (-np.inf if hazard == 1.0 else log1p(-hazard))
            + log_probabilities
            + growth_log_likelihood
        )
        maximum = float(log_masses.max())
        normalizer = maximum + log(float(np.exp(log_masses - maximum).sum()))
        log_probabilities = log_masses - normalizer
        alpha = np.vstack((prior_alpha + current, alpha + current))
        beta = np.vstack((prior_beta + 1.0 - current, beta + 1.0 - current))

    probabilities = np.exp(log_probabilities)
    if (
        not np.all(np.isfinite(probabilities))
        or abs(float(probabilities.sum()) - 1.0) > 1e-10
        or np.any(alpha <= 0.0)
        or np.any(beta <= 0.0)
    ):
        raise RuntimeError("shared BOCPD posterior is invalid")
    state_means = alpha / (alpha + beta)
    mixture_current = (probabilities[:, None] * state_means).sum(axis=0)
    maximum_probability = float(probabilities.max())
    map_index = int(
        np.flatnonzero(np.abs(probabilities - maximum_probability) <= 1e-15)[0]
    )
    map_current = state_means[map_index]
    if hazard == 0.0:
        horizon_weight = 1.0
    else:
        horizon_weight = (
            (1.0 - hazard) * (1.0 - (1.0 - hazard) ** horizon) / (horizon * hazard)
        )
    mixture = horizon_weight * mixture_current + (1.0 - horizon_weight) * base_mean
    map_forecast = horizon_weight * map_current + (1.0 - horizon_weight) * base_mean
    return ChangePointForecast(
        mixture=mixture,
        map_run=map_forecast,
        anchor=base_mean,
        run_length_probabilities=probabilities,
        map_run_length=map_index + 1,
    )


def _visible_task_priorities(
    order: Sequence[tuple[str, str]],
) -> tuple[float, ...]:
    ordered = sorted(
        range(len(order)),
        key=lambda index: order[index],
    )
    ranks = {index: rank + 1 for rank, index in enumerate(ordered)}
    denominator = float(len(order) + 1)
    return tuple(
        ranks[index]
        + (
            int(
                hashlib.sha256(order[index][1].encode("utf-8")).hexdigest()[:12],
                16,
            )
            / float(16**12)
        )
        / denominator
        for index in range(len(order))
    )


def select_greedy_l1_indices(
    visible_outcomes: Any,
    target: Any,
    *,
    budget: int,
    created_order: Sequence[tuple[str, str]],
    swap_pass_limit: int = 20,
    tolerance: float = 1e-15,
) -> tuple[int, ...]:
    """Greedy L1 response matching with deterministic best swaps."""
    import numpy as np

    values = np.asarray(visible_outcomes, dtype=np.float64)
    forecast = np.asarray(target, dtype=np.float64)
    order = tuple(created_order)
    if (
        values.ndim != 2
        or values.shape[0] != len(order)
        or forecast.shape != (values.shape[1],)
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(values)
        or isinstance(swap_pass_limit, bool)
        or swap_pass_limit < 0
        or tolerance <= 0.0
    ):
        raise ValueError("greedy L1 selection inputs are invalid")
    priorities = _visible_task_priorities(order)
    selected: list[int] = []
    selected_sum = np.zeros(values.shape[1], dtype=np.float64)
    for count in range(1, budget + 1):
        candidates = []
        selected_set = set(selected)
        for index in range(len(values)):
            if index in selected_set:
                continue
            candidate_objective = float(
                np.abs((selected_sum + values[index]) / count - forecast).mean()
            )
            candidates.append(
                (
                    candidate_objective,
                    -priorities[index],
                    order[index][1],
                    index,
                )
            )
        chosen = min(candidates)[3]
        selected.append(chosen)
        selected_sum += values[chosen]

    def objective(total: Any) -> float:
        return float(np.abs(total / budget - forecast).mean())

    current = objective(selected_sum)
    for _ in range(swap_pass_limit):
        selected_set = set(selected)
        best: tuple[float, float, str, float, str, int, int] | None = None
        for position, outgoing in enumerate(selected):
            for incoming in range(len(values)):
                if incoming in selected_set:
                    continue
                candidate_sum = selected_sum - values[outgoing] + values[incoming]
                candidate_objective = objective(candidate_sum)
                if candidate_objective >= current - tolerance:
                    continue
                candidate = (
                    candidate_objective,
                    priorities[outgoing],
                    order[outgoing][1],
                    -priorities[incoming],
                    order[incoming][1],
                    position,
                    incoming,
                )
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            break
        *_, position, incoming = best
        outgoing = selected[position]
        selected_sum += values[incoming] - values[outgoing]
        selected[position] = incoming
        current = objective(selected_sum)
    return tuple(sorted(selected))


def materialize_memberships(
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Materialize every frozen membership without scoring target futures."""
    _verify_runtime()
    plan = load_plan(plan_path)
    addendum = load_addendum(plan=plan)
    lock = load_execution_lock(
        lock_path,
        plan=plan,
        addendum=addendum,
    )
    audit_plan = load_audit_plan()
    inputs = _load_inputs(audit_plan)
    _validate_source_bindings(plan, addendum, lock, inputs)
    budget = int(_mapping(plan, "fixed_facts")["selection_budget_tasks"])
    horizon_payloads: dict[str, Any] = {}
    solver_calls = 0
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
        for repository_position, repository_id in enumerate(repository_ids):
            state = create_adanormalhedge_state(len(inputs.data.configuration_ids))
            for origin in origins_by_repository[repository_id]:
                history_indices = tuple(
                    inputs.data.task_index[task.instance_id] for task in origin.history
                )
                future_indices = tuple(
                    inputs.data.task_index[task.instance_id] for task in origin.future
                )
                history = inputs.data.outcomes[list(history_indices), :]
                experts = response_expert_forecasts(
                    history,
                    horizon=horizon,
                )
                ada_forecast, _ = adanormalhedge_forecast(state, experts)
                created_order = tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                )
                history_ids = tuple(
                    inputs.data.task_ids[index] for index in history_indices
                )
                common = {
                    "ordinary_recency": list(history_ids[-budget:]),
                    "ALG-007": list(alg_007[origin.origin_id]),
                }
                for held_out, configuration_id in enumerate(
                    inputs.data.configuration_ids
                ):
                    visible = tuple(
                        index
                        for index in range(len(inputs.data.configuration_ids))
                        if index != held_out
                    )
                    visible_history = history[:, list(visible)]
                    ada_visible = ada_forecast[list(visible)]
                    bocpd = shared_bocpd_forecast(
                        visible_history,
                        horizon=horizon,
                    )
                    cached_positions = select_cached_scalar_indices(
                        tuple(int(value) for value in history[:, held_out]),
                        float(ada_forecast[held_out]),
                        budget=budget,
                        created_order=created_order,
                    )
                    cached_full_positions = select_cached_scalar_indices(
                        tuple(int(value) for value in history[:, held_out]),
                        float(history[:, held_out].mean()),
                        budget=budget,
                        created_order=created_order,
                    )
                    ada_assembly = solve_exact_l1_assembly(
                        visible_history,
                        ada_visible,
                        budget=budget,
                        created_order=created_order,
                    )
                    bocpd_assembly = solve_exact_l1_assembly(
                        visible_history,
                        bocpd.mixture,
                        budget=budget,
                        created_order=created_order,
                    )
                    full_assembly = solve_exact_l1_assembly(
                        visible_history,
                        visible_history.mean(axis=0),
                        budget=budget,
                        created_order=created_order,
                    )
                    solver_calls += 3
                    greedy_positions = select_greedy_l1_indices(
                        visible_history,
                        bocpd.mixture,
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
                            "history_task_count": len(history_ids),
                            "memberships": {
                                **common,
                                "ALG-015C": ids(cached_positions),
                                "ALG-015U": ids(ada_assembly.indices),
                                "ALG-016U": ids(bocpd_assembly.indices),
                                "ALG-016U_greedy": ids(greedy_positions),
                                "cached_full_target": ids(cached_full_positions),
                                "unseen_full_target": ids(full_assembly.indices),
                            },
                            "forecasts": {
                                "ALG-015C": float(ada_forecast[held_out]),
                                "ALG-015U": [float(value) for value in ada_visible],
                                "ALG-016U": [float(value) for value in bocpd.mixture],
                                "ALG-016U_map": [
                                    float(value) for value in bocpd.map_run
                                ],
                                "visible_configuration_ids": [
                                    inputs.data.configuration_ids[index]
                                    for index in visible
                                ],
                            },
                            "materialization": {
                                "ALG-015C_l1": float(
                                    abs(
                                        history[
                                            list(cached_positions),
                                            held_out,
                                        ].mean()
                                        - ada_forecast[held_out]
                                    )
                                ),
                                "ALG-015U_l1": ada_assembly.objective,
                                "ALG-016U_l1": bocpd_assembly.objective,
                                "ALG-016U_greedy_l1": float(
                                    abs(
                                        visible_history[list(greedy_positions)].mean(
                                            axis=0
                                        )
                                        - bocpd.mixture
                                    ).mean()
                                ),
                                "unseen_full_target_l1": (full_assembly.objective),
                                "ALG-015U_patterns": (
                                    ada_assembly.response_pattern_count
                                ),
                                "ALG-016U_patterns": (
                                    bocpd_assembly.response_pattern_count
                                ),
                                "ALG-016U_map_run_length": (bocpd.map_run_length),
                            },
                        }
                    )
                observed = inputs.data.outcomes[
                    list(future_indices),
                    :,
                ].mean(axis=0)
                update_adanormalhedge(state, experts, observed)
            print(
                f"materialized H{horizon} repository "
                f"{repository_position + 1}/{len(repository_ids)} "
                f"{repository_id}",
                flush=True,
            )
        expected_rows = sum(
            len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        ) * len(inputs.data.configuration_ids)
        if len(rows) != expected_rows:
            raise RuntimeError("materialized membership row count changed")
        horizon_payloads[str(horizon)] = {
            "repository_ids": list(repository_ids),
            "deep_repository_ids": list(deep_ids),
            "origin_count": expected_rows // len(inputs.data.configuration_ids),
            "target_row_count": len(rows),
            "rows": rows,
            "rows_digest": canonical_digest(rows),
        }
    artifact: dict[str, Any] = {
        "schema_version": MEMBERSHIP_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "addendum_digest": addendum.get("addendum_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "algorithm_ids": list(VISIBLE_ALGORITHMS),
        "horizons": horizon_payloads,
        "solver_calls": solver_calls,
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
    """Verify identities and local-history boundaries before outcome scoring."""
    import numpy as np

    plan = load_plan(plan_path)
    addendum = load_addendum(plan=plan)
    lock = load_execution_lock(
        lock_path,
        plan=plan,
        addendum=addendum,
    )
    candidate = dict(payload)
    digest = candidate.pop("membership_digest", None)
    if canonical_digest(candidate) != digest:
        raise ValueError("prequential response membership digest changed")
    if (
        payload.get("schema_version") != MEMBERSHIP_SCHEMA
        or payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("addendum_digest") != addendum.get("addendum_digest")
        or payload.get("execution_lock_digest") != lock.get("lock_digest")
        or tuple(payload.get("algorithm_ids", ())) != VISIBLE_ALGORITHMS
    ):
        raise ValueError("prequential response membership binding changed")
    inputs = _load_inputs(load_audit_plan())
    _validate_source_bindings(plan, addendum, lock, inputs)
    for horizon in (5, 10):
        horizon_payload = _mapping(
            _mapping(payload, "horizons"),
            str(horizon),
        )
        origins_by_repository, repository_ids, _ = _horizon_frame(
            inputs.data.tasks,
            inputs.selector_plan,
            horizon,
        )
        origin_lookup = {
            origin.origin_id: origin
            for repository_id in repository_ids
            for origin in origins_by_repository[repository_id]
        }
        alg_007 = _alg_007_memberships(
            inputs.alg_007_task_space,
            horizon,
            repository_ids,
        )
        rows = _mapping_sequence(horizon_payload, "rows")
        if (
            tuple(horizon_payload.get("repository_ids", ())) != repository_ids
            or tuple(horizon_payload.get("deep_repository_ids", ()))
            != tuple(_frame_identity(inputs, horizon)["deep_repository_ids"])
            or horizon_payload.get("origin_count")
            != sum(
                len(origins_by_repository[repository_id])
                for repository_id in repository_ids
            )
            or horizon_payload.get("target_row_count") != len(rows)
            or horizon_payload.get("rows_digest")
            != canonical_digest(horizon_payload.get("rows"))
        ):
            raise ValueError("membership horizon identity changed")
        expected_keys = {
            (origin.origin_id, configuration_id)
            for repository_id in repository_ids
            for origin in origins_by_repository[repository_id]
            for configuration_id in inputs.data.configuration_ids
        }
        actual_key_rows = [
            (
                _required_string(row, "origin_id"),
                _required_string(row, "target_configuration_id"),
            )
            for row in rows
        ]
        if (
            set(actual_key_rows) != expected_keys
            or len(actual_key_rows) != len(expected_keys)
            or len(set(actual_key_rows)) != len(actual_key_rows)
        ):
            raise ValueError("membership target frame changed")
        for row in rows:
            origin = origin_lookup[_required_string(row, "origin_id")]
            repository_id = _required_string(row, "repository_id")
            target_configuration_id = _required_string(
                row,
                "target_configuration_id",
            )
            if (
                repository_id != origin.repository_id
                or target_configuration_id not in inputs.data.configuration_ids
                or row.get("history_task_count") != len(origin.history)
            ):
                raise ValueError("membership row identity changed")
            history_ordered = tuple(task.instance_id for task in origin.history)
            history_ids = set(history_ordered)
            future_ids = {task.instance_id for task in origin.future}
            memberships = _mapping(row, "memberships")
            expected_memberships = (
                "ALG-015C",
                "ALG-015U",
                "ALG-016U",
                "ALG-016U_greedy",
                "cached_full_target",
                "unseen_full_target",
                "ordinary_recency",
                "ALG-007",
            )
            if set(memberships) != set(expected_memberships):
                raise ValueError("membership algorithm set changed")
            for membership_id in expected_memberships:
                selected = memberships.get(membership_id)
                if (
                    not isinstance(selected, list)
                    or len(selected) != 10
                    or len(set(selected)) != 10
                    or not set(selected) <= history_ids
                    or set(selected) & future_ids
                ):
                    raise ValueError(f"{membership_id} leaves local history boundary")
            if tuple(memberships["ordinary_recency"]) != history_ordered[-10:] or tuple(
                memberships["ALG-007"]
            ) != tuple(alg_007[origin.origin_id]):
                raise ValueError("membership frozen control changed")
            held_out = inputs.data.configuration_ids.index(target_configuration_id)
            expected_visible = tuple(
                configuration_id
                for index, configuration_id in enumerate(inputs.data.configuration_ids)
                if index != held_out
            )
            forecasts = _mapping(row, "forecasts")
            if (
                set(forecasts)
                != {
                    "ALG-015C",
                    "ALG-015U",
                    "ALG-016U",
                    "ALG-016U_map",
                    "visible_configuration_ids",
                }
                or tuple(forecasts.get("visible_configuration_ids", ()))
                != expected_visible
                or not _unit_number(forecasts.get("ALG-015C"))
                or any(
                    not _unit_number(value)
                    for key in (
                        "ALG-015U",
                        "ALG-016U",
                        "ALG-016U_map",
                    )
                    for value in _number_list(
                        forecasts.get(key),
                        expected_length=35,
                    )
                )
            ):
                raise ValueError("membership forecast schema changed")
            materialization = _mapping(row, "materialization")
            expected_materialization = {
                "ALG-015C_l1",
                "ALG-015U_l1",
                "ALG-016U_l1",
                "ALG-016U_greedy_l1",
                "unseen_full_target_l1",
                "ALG-015U_patterns",
                "ALG-016U_patterns",
                "ALG-016U_map_run_length",
            }
            if set(materialization) != expected_materialization:
                raise ValueError("membership materialization schema changed")
            for key in (
                "ALG-015C_l1",
                "ALG-015U_l1",
                "ALG-016U_l1",
                "ALG-016U_greedy_l1",
                "unseen_full_target_l1",
            ):
                value = materialization.get(key)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, Real)
                    or not isfinite(float(value))
                    or float(value) < 0.0
                ):
                    raise ValueError("membership materialization value changed")
            for key in (
                "ALG-015U_patterns",
                "ALG-016U_patterns",
                "ALG-016U_map_run_length",
            ):
                value = materialization.get(key)
                if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                    raise ValueError("membership materialization count changed")
            history_indices = tuple(
                inputs.data.task_index[task_id] for task_id in history_ordered
            )
            history_outcomes = inputs.data.outcomes[
                list(history_indices),
                :,
            ]
            visible_indices = tuple(
                index
                for index in range(len(inputs.data.configuration_ids))
                if index != held_out
            )
            visible_history = history_outcomes[:, list(visible_indices)]

            def selected_outcomes(membership_id: str) -> Any:
                indices = tuple(
                    inputs.data.task_index[task_id]
                    for task_id in memberships[membership_id]
                )
                return inputs.data.outcomes[list(indices), :]

            recomputed_materialization = {
                "ALG-015C_l1": float(
                    abs(
                        selected_outcomes("ALG-015C")[
                            :,
                            held_out,
                        ].mean()
                        - float(forecasts["ALG-015C"])
                    )
                ),
                "ALG-015U_l1": float(
                    np.abs(
                        selected_outcomes("ALG-015U")[
                            :,
                            list(visible_indices),
                        ].mean(axis=0)
                        - np.asarray(
                            forecasts["ALG-015U"],
                            dtype=np.float64,
                        )
                    ).mean()
                ),
                "ALG-016U_l1": float(
                    np.abs(
                        selected_outcomes("ALG-016U")[
                            :,
                            list(visible_indices),
                        ].mean(axis=0)
                        - np.asarray(
                            forecasts["ALG-016U"],
                            dtype=np.float64,
                        )
                    ).mean()
                ),
                "ALG-016U_greedy_l1": float(
                    np.abs(
                        selected_outcomes("ALG-016U_greedy")[
                            :,
                            list(visible_indices),
                        ].mean(axis=0)
                        - np.asarray(
                            forecasts["ALG-016U"],
                            dtype=np.float64,
                        )
                    ).mean()
                ),
                "unseen_full_target_l1": float(
                    np.abs(
                        selected_outcomes("unseen_full_target")[
                            :,
                            list(visible_indices),
                        ].mean(axis=0)
                        - visible_history.mean(axis=0)
                    ).mean()
                ),
            }
            if any(
                abs(float(materialization[key]) - recomputed) > 1e-12
                for key, recomputed in recomputed_materialization.items()
            ):
                raise ValueError("membership materialization replay changed")


def score_memberships(
    memberships: Mapping[str, Any],
    *,
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Join frozen memberships to target outcomes and compute direct MAE."""
    import numpy as np

    _verify_runtime()
    verify_memberships(
        memberships,
        plan_path=plan_path,
        lock_path=lock_path,
    )
    plan = load_plan(plan_path)
    addendum = load_addendum(plan=plan)
    lock = load_execution_lock(
        lock_path,
        plan=plan,
        addendum=addendum,
    )
    inputs = _load_inputs(load_audit_plan())
    algorithm_results: dict[str, dict[str, Any]] = {
        algorithm_id: {} for algorithm_id in (*VISIBLE_ALGORITHMS, "ALG-016U_greedy")
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
        rows_by_algorithm: dict[str, list[Mapping[str, object]]] = {
            algorithm_id: []
            for algorithm_id in (
                *VISIBLE_ALGORITHMS,
                "ALG-016U_greedy",
            )
        }
        forecast_diagnostics: dict[str, list[Mapping[str, object]]] = {
            "ALG-015C": [],
            "ALG-015U": [],
            "ALG-016U": [],
            "ALG-016U_map": [],
        }
        materialization_diagnostics: dict[
            str,
            list[Mapping[str, object]],
        ] = {
            "ALG-015C": [],
            "ALG-015U": [],
            "ALG-016U": [],
            "ALG-016U_greedy": [],
        }
        configuration_index = {
            value: index for index, value in enumerate(inputs.data.configuration_ids)
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
            memberships_row = _mapping(row, "memberships")
            for algorithm_id in rows_by_algorithm:
                control_id = (
                    "cached_full_target"
                    if algorithm_id == "ALG-015C"
                    else "unseen_full_target"
                )
                rows_by_algorithm[algorithm_id].append(
                    _loss_row(
                        inputs,
                        repository_id=repository_id,
                        origin=origin,
                        held_out=held_out,
                        candidate=tuple(
                            inputs.data.task_index[task_id]
                            for task_id in memberships_row[algorithm_id]
                        ),
                        full=history_indices,
                        controls={
                            "exact_full_target": tuple(
                                inputs.data.task_index[task_id]
                                for task_id in memberships_row[control_id]
                            ),
                            "ordinary_recency": tuple(
                                inputs.data.task_index[task_id]
                                for task_id in memberships_row["ordinary_recency"]
                            ),
                            "ALG-007": tuple(
                                inputs.data.task_index[task_id]
                                for task_id in memberships_row["ALG-007"]
                            ),
                        },
                        future=future_indices,
                    )
                )
            history = inputs.data.outcomes[list(history_indices), :]
            future = inputs.data.outcomes[list(future_indices), :]
            forecasts = _mapping(row, "forecasts")
            materialization = _mapping(row, "materialization")
            for algorithm_id, field in (
                ("ALG-015C", "ALG-015C_l1"),
                ("ALG-015U", "ALG-015U_l1"),
                ("ALG-016U", "ALG-016U_l1"),
                ("ALG-016U_greedy", "ALG-016U_greedy_l1"),
            ):
                materialization_diagnostics[algorithm_id].append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "difference": float(materialization[field]),
                    }
                )
            cached_forecast = float(forecasts["ALG-015C"])
            cached_future = float(future[:, held_out].mean())
            forecast_diagnostics["ALG-015C"].append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "difference": abs(cached_forecast - cached_future)
                    - abs(float(history[:, held_out].mean()) - cached_future),
                }
            )
            visible_ids = tuple(forecasts["visible_configuration_ids"])
            visible_indices = tuple(configuration_index[value] for value in visible_ids)
            visible_future = future[:, list(visible_indices)].mean(axis=0)
            visible_full = history[:, list(visible_indices)].mean(axis=0)
            for algorithm_id in (
                "ALG-015U",
                "ALG-016U",
                "ALG-016U_map",
            ):
                forecast = np.asarray(
                    forecasts[algorithm_id],
                    dtype=np.float64,
                )
                forecast_diagnostics[algorithm_id].append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "difference": float(
                            np.abs(forecast - visible_future).mean()
                            - np.abs(visible_full - visible_future).mean()
                        ),
                    }
                )
        for algorithm_id, rows in rows_by_algorithm.items():
            summary = _summarize_rows(
                rows,
                repository_ids,
                deep_ids,
                inputs.configuration_metadata,
                inputs.selector_plan,
            )
            wide = _mapping(summary, "wide")
            seed = 20260733 if horizon == 5 else 20260738
            summary["repository_bootstrap"] = _repository_bootstrap(
                rows,
                repository_ids,
                resamples=10000,
                seed=seed,
            )
            random_seed = 20260833 if horizon == 5 else 20260838
            summary["random_calibration"] = _random_outcome_calibration(
                origins_by_repository,
                repository_ids,
                inputs.outcome_maps,
                inputs.data.configuration_ids,
                budget=10,
                draws=20000,
                seed=random_seed,
                candidate_difference=float(wide["difference"]),
            )
            forecast_id = (
                "ALG-016U" if algorithm_id == "ALG-016U_greedy" else algorithm_id
            )
            summary["continuous_forecast_minus_full"] = _repository_first_difference(
                forecast_diagnostics[forecast_id],
                repository_ids,
            )
            summary["forecast_to_selection_l1"] = _repository_first_difference(
                materialization_diagnostics[algorithm_id],
                repository_ids,
            )
            algorithm_results[algorithm_id][str(horizon)] = summary
        algorithm_results["ALG-016U"][str(horizon)][
            "map_continuous_forecast_minus_full"
        ] = _repository_first_difference(
            forecast_diagnostics["ALG-016U_map"],
            repository_ids,
        )
        print(f"scored H{horizon}", flush=True)
    decisions = {}
    alg_007_limit = float(
        _mapping(plan, "fixed_facts")["standard_h5_alg_007_difference"]
    )
    for algorithm_id, horizons in algorithm_results.items():
        h5 = _mapping(_mapping(horizons, "5"), "wide")
        h10 = _mapping(_mapping(horizons, "10"), "wide")
        eligible_winner = algorithm_id in VISIBLE_ALGORITHMS
        numeric_progress = eligible_winner and (
            float(h5["difference"]) < alg_007_limit and float(h10["difference"]) <= 0.0
        )
        decisions[algorithm_id] = {
            "eligible_portfolio_winner": eligible_winner,
            "beats_full_h5": float(h5["difference"]) < 0.0,
            "beats_alg_007_h5": float(h5["difference"]) < alg_007_limit,
            "beats_full_h10": float(h10["difference"]) <= 0.0,
            "numeric_progress": numeric_progress,
            "development_nomination_compatibility": (
                _development_nomination_compatibility(
                    _mapping(horizons, "5"),
                    _mapping(horizons, "10"),
                )
                if eligible_winner
                else {
                    "available": False,
                    "reason": "diagnostic-only materializer ablation",
                }
            ),
            "terminal_state": (
                "numeric_progress"
                if numeric_progress
                else ("bounded_inconclusive" if eligible_winner else "diagnostic_only")
            ),
        }
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "addendum_digest": addendum.get("addendum_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "membership_digest": memberships.get("membership_digest"),
        "algorithms": algorithm_results,
        "decisions": decisions,
        "multiple_comparisons": _mapping(
            addendum,
            "statistical_protocol",
        ).get("multiple_comparisons"),
        "claim_boundary": plan.get("claim_boundary"),
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
        },
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _development_nomination_compatibility(
    h5: Mapping[str, Any],
    h10: Mapping[str, Any],
) -> Mapping[str, Any]:
    h5_wide = _mapping(h5, "wide")
    h10_wide = _mapping(h10, "wide")
    requirements = {
        "h5_difference_at_most_minus_0_010": (float(h5_wide["difference"]) <= -0.010),
        "h5_at_least_10_favorable_repositories": (
            int(h5_wide["favorable_repository_count"]) >= 10
        ),
        "h5_every_leave_one_repository_out_favorable": all(
            float(item["difference"]) < 0.0
            for item in _mapping_sequence(
                h5_wide,
                "leave_one_repository_out",
            )
        ),
        "h5_deep_favorable": float(_mapping(h5, "deep")["difference"]) < 0.0,
        "h5_bootstrap_upper_below_zero": float(
            _mapping(h5, "repository_bootstrap")["upper"]
        )
        < 0.0,
        "h5_random_midrank_at_least_0_90": float(
            _mapping(h5, "random_calibration")["candidate_better_than_random_midrank"]
        )
        >= 0.90,
        "h10_difference_below_zero": (float(h10_wide["difference"]) < 0.0),
        "h10_at_least_8_favorable_repositories": (
            int(h10_wide["favorable_repository_count"]) >= 8
        ),
        "h10_deep_favorable": float(_mapping(h10, "deep")["difference"]) < 0.0,
    }
    return {
        "available": False,
        "threshold_compatibility": requirements,
        "all_reported_thresholds_met": all(requirements.values()),
        "reason": (
            "development nomination is unavailable because no temporal-null "
            "construction was frozen"
        ),
    }


def _repository_first_difference(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> float:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        repository_id = str(row["repository_id"])
        difference = row["difference"]
        if isinstance(difference, bool) or not isinstance(difference, Real):
            raise ValueError("forecast diagnostic difference is invalid")
        values[repository_id].append(float(difference))
    if set(values) != set(repository_ids):
        raise ValueError("forecast diagnostic repository frame changed")
    return sum(
        sum(values[repository_id]) / len(values[repository_id])
        for repository_id in repository_ids
    ) / len(repository_ids)


def _validate_source_bindings(
    plan: Mapping[str, Any],
    addendum: Mapping[str, Any],
    lock: Mapping[str, Any],
    inputs: AuditInputs,
) -> None:
    source = _mapping(plan, "source_bindings")
    if (
        source.get("selector_plan_digest")
        != inputs.selector_plan.get("selector_plan_digest")
        or source.get("panel_digest")
        != _mapping(inputs.plan, "logical_bindings").get("panel_digest")
        or source.get("resolved_outcome_digest")
        != _mapping(inputs.plan, "logical_bindings").get("resolved_outcome_digest")
        or source.get("surrogate_gate_plan_digest") != inputs.plan.get("plan_digest")
    ):
        raise ValueError("prequential response source binding changed")
    expected = _mapping(addendum, "execution_identity_requirements")
    task_space = inputs.alg_007_task_space
    if task_space.get("task_space_results_digest") != expected.get(
        "alg_007_task_space_logical_digest"
    ):
        raise ValueError("ALG-007 task-space identity changed")
    if _mapping(inputs.selector_plan, "source").get(
        "task_time_projection_digest"
    ) != expected.get("task_time_projection_digest"):
        raise ValueError("task-time projection identity changed")
    for horizon, prefix in ((5, "h5"), (10, "h10")):
        horizon_payload = _mapping(
            _mapping(task_space, "horizons"),
            str(horizon),
        )
        digests = _mapping(horizon_payload, "membership_digests")
        if digests.get("full_history") != expected.get(
            f"{prefix}_full_membership_digest"
        ) or digests.get("alg_007_centroid_recent_15") != expected.get(
            f"{prefix}_alg_007_membership_digest"
        ):
            raise ValueError(f"H{horizon} source membership identity changed")
        frame = _frame_identity(inputs, horizon)
        if _mapping(_mapping(lock, "frames"), str(horizon)) != frame:
            raise ValueError(f"H{horizon} execution frame changed")


def _frame_identity(
    inputs: AuditInputs,
    horizon: int,
) -> Mapping[str, Any]:
    origins_by_repository, repository_ids, deep_ids = _horizon_frame(
        inputs.data.tasks,
        inputs.selector_plan,
        horizon,
    )
    rows = []
    full: dict[str, tuple[str, ...]] = {}
    recency: dict[str, tuple[str, ...]] = {}
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "history_task_ids": history_ids,
                    "future_task_ids": future_ids,
                }
            )
            full[origin.origin_id] = history_ids
            recency[origin.origin_id] = history_ids[-10:]
    alg_007 = _alg_007_memberships(
        inputs.alg_007_task_space,
        horizon,
        repository_ids,
    )
    return {
        "repository_ids": list(repository_ids),
        "repository_ids_digest": canonical_digest(repository_ids),
        "deep_repository_ids": list(deep_ids),
        "deep_repository_ids_digest": canonical_digest(deep_ids),
        "origin_count": len(rows),
        "origin_rows_digest": canonical_digest(rows),
        "full_membership_digest_recomputed": canonical_digest(full),
        "recency_membership_digest_recomputed": canonical_digest(recency),
        "alg_007_membership_digest_recomputed": canonical_digest(alg_007),
    }


def _verify_runtime() -> None:
    import numpy as np

    if np.__version__ != NUMPY_VERSION or version("scipy") != SCIPY_VERSION:
        raise ValueError(
            "prequential response runtime changed: "
            f"numpy={np.__version__}, scipy={version('scipy')}"
        )


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
    if not isinstance(items, (list, tuple)) or any(
        not isinstance(item, dict) for item in items
    ):
        raise ValueError(f"{key} must be a sequence of objects")
    return tuple(items)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _unit_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and isfinite(float(value))
        and 0.0 <= float(value) <= 1.0
    )


def _number_list(
    value: object,
    *,
    expected_length: int,
) -> tuple[object, ...]:
    if not isinstance(value, list) or len(value) != expected_length:
        raise ValueError("numeric list shape changed")
    return tuple(value)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify-plan")
    verify.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    verify.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    materialize.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    materialize.add_argument("--output", type=Path, required=True)
    verify_membership = subparsers.add_parser("verify-memberships")
    verify_membership.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    verify_membership.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    verify_membership.add_argument("--input", type=Path, required=True)
    score = subparsers.add_parser("score")
    score.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    score.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    score.add_argument("--memberships", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a study command."""
    args = _build_parser().parse_args(argv)
    if args.command == "verify-plan":
        plan = load_plan(args.plan)
        addendum = load_addendum(args.addendum, plan=plan)
        print(f"{plan['plan_digest']} {addendum['addendum_digest']}")
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
