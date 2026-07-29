#!/usr/bin/env python3
"""Run the matched finite-horizon budget-grid mechanism audit."""

from __future__ import annotations

# NumPy and SciPy are supplied by the execution lock's reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.finite_horizon_cached_assembly.study import (  # noqa: E402
    FiniteHorizonAction,
    load_execution_lock as load_parent_execution_lock,
    load_plan as load_parent_plan,
    select_fixed_success_count_indices,
    select_jeffreys_action,
    select_plugin_action,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    _frame_identity,
)
from examples.surrogate_gate_audit.study import (  # noqa: E402
    AuditInputs,
    _horizon_frame,
    _load_inputs,
    _number,
    _repository_bootstrap,
    _repository_summary,
    load_audit_plan,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_LOCK = HERE / "execution-lock.json"
PLAN_SCHEMA = "barcarolle_finite_horizon_grid_audit_plan_v1"
LOCK_SCHEMA = "barcarolle_finite_horizon_grid_audit_execution_lock_v1"
MEMBERSHIP_SCHEMA = "barcarolle_finite_horizon_grid_audit_memberships_v1"
RESULT_SCHEMA = "barcarolle_finite_horizon_grid_audit_results_v1"
METHOD_IDS = ("ALG-018C-P", "ALG-018C", "h_blind_control")
CELL_SPECS = (
    ("B5_H5", 5, 5),
    ("B5_H10", 5, 10),
    ("B10_H5", 10, 5),
    ("B10_H10", 10, 10),
)
BOUND_FILE_PATHS = frozenset(
    {
        "examples/finite_horizon_grid_audit/plan.json",
        "examples/finite_horizon_grid_audit/study.py",
        "tests/test_finite_horizon_grid_audit.py",
        "examples/finite_horizon_cached_assembly/plan.json",
        "examples/finite_horizon_cached_assembly/study.py",
        "examples/finite_horizon_cached_assembly/execution-lock.json",
    }
)


@dataclass(frozen=True)
class HBlindAction:
    """One exact same-budget stationary action."""

    q: int
    risk: int
    feasible_q: tuple[int, ...]


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and validate the frozen grid-audit contract."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("finite-horizon grid-audit plan is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if payload.get("plan_digest") != expected:
        raise ValueError("finite-horizon grid-audit plan digest changed")
    contract = _mapping(payload, "research_contract")
    resources = _mapping(payload, "resource_boundary")
    if (
        payload.get("study_id") != "finite-horizon-grid-audit-2026-07-29"
        or tuple(contract.get("budgets", ())) != (5, 10)
        or tuple(contract.get("future_counts", ())) != (5, 10)
        or tuple(contract.get("required_cells", ()))
        != tuple(cell_id for cell_id, _, _ in CELL_SPECS)
        or contract.get("minimum_initial_history_tasks") != 20
    ):
        raise ValueError("finite-horizon grid-audit contract changed")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "embedding_api_calls",
        "sealed_holdout_reads",
        "core_schema_or_service_changes",
    ):
        if resources.get(key) != 0:
            raise ValueError("finite-horizon grid-audit resource boundary changed")
    return payload


def load_execution_lock(
    path: Path = DEFAULT_LOCK,
    *,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Load the grid implementation and parent-evidence lock."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != LOCK_SCHEMA:
        raise ValueError("finite-horizon grid execution lock is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "lock_digest"}
    )
    if payload.get("lock_digest") != expected:
        raise ValueError("finite-horizon grid execution lock digest changed")
    parent_plan = load_parent_plan()
    parent_lock = load_parent_execution_lock(plan=parent_plan)
    source = _mapping(plan, "source_bindings")
    if (
        payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("parent_plan_digest") != parent_plan.get("plan_digest")
        or payload.get("parent_execution_lock_digest") != parent_lock.get("lock_digest")
        or payload.get("parent_result_digest") != source.get("parent_result_digest")
        or payload.get("parent_result_raw_sha256")
        != source.get("parent_result_raw_sha256")
    ):
        raise ValueError("finite-horizon grid execution binding changed")
    bound_files = _mapping_sequence(payload, "bound_files")
    paths = tuple(_required_string(item, "path") for item in bound_files)
    if len(paths) != len(set(paths)) or set(paths) != BOUND_FILE_PATHS:
        raise ValueError("finite-horizon grid bound-file set changed")
    for item in bound_files:
        relative = _required_string(item, "path")
        actual = hashlib.sha256((REPOSITORY_ROOT / relative).read_bytes()).hexdigest()
        if actual != _required_string(item, "sha256"):
            raise ValueError(f"finite-horizon grid bound file changed: {relative}")
    actual_runtime = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy_version": version("numpy"),
        "scipy_version": version("scipy"),
    }
    if _mapping(payload, "runtime") != actual_runtime:
        raise ValueError("finite-horizon grid runtime changed")
    if _mapping(payload, "matched_h10_frame") != _mapping(parent_lock, "frames")["10"]:
        raise ValueError("finite-horizon grid matched frame changed")
    return payload


def select_h_blind_action(n: int, s: int, budget: int) -> HBlindAction:
    """Choose feasible q nearest s/n, breaking exact ties toward lower q."""
    if (
        any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (n, s, budget)
        )
        or n <= 0
        or budget <= 0
        or budget > n
        or not 0 <= s <= n
    ):
        raise ValueError("H-blind action counts are invalid")
    feasible = tuple(range(max(0, budget - (n - s)), min(budget, s) + 1))
    risk, q = min((abs(q * n - budget * s), q) for q in feasible)
    return HBlindAction(q=q, risk=risk, feasible_q=feasible)


def materialize_memberships(
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Materialize all four cells without reading future outcomes."""
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    inputs = _load_inputs(load_audit_plan())
    _validate_source_bindings(plan, lock, inputs)
    cells = _build_cell_payloads(inputs)
    artifact: dict[str, Any] = {
        "schema_version": MEMBERSHIP_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "method_ids": list(METHOD_IDS),
        "cell_ids": [cell_id for cell_id, _, _ in CELL_SPECS],
        "cells": cells,
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
    """Recompute every action and membership from matched history."""
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    candidate = dict(payload)
    digest = candidate.pop("membership_digest", None)
    if canonical_digest(candidate) != digest:
        raise ValueError("finite-horizon grid membership digest changed")
    if (
        payload.get("schema_version") != MEMBERSHIP_SCHEMA
        or payload.get("study_id") != plan.get("study_id")
        or payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("execution_lock_digest") != lock.get("lock_digest")
        or tuple(payload.get("method_ids", ())) != METHOD_IDS
        or tuple(payload.get("cell_ids", ()))
        != tuple(cell_id for cell_id, _, _ in CELL_SPECS)
        or payload.get("resource_use")
        != {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
        }
    ):
        raise ValueError("finite-horizon grid membership binding changed")
    inputs = _load_inputs(load_audit_plan())
    _validate_source_bindings(plan, lock, inputs)
    if payload.get("cells") != _build_cell_payloads(inputs):
        raise ValueError("finite-horizon grid membership replay changed")


def score_memberships(
    memberships: Mapping[str, Any],
    *,
    plan_path: Path = DEFAULT_PLAN,
    lock_path: Path = DEFAULT_LOCK,
) -> Mapping[str, Any]:
    """Score all matched cells with repository-first direct MAE."""
    verify_memberships(
        memberships,
        plan_path=plan_path,
        lock_path=lock_path,
    )
    plan = load_plan(plan_path)
    lock = load_execution_lock(lock_path, plan=plan)
    inputs = _load_inputs(load_audit_plan())
    origins_by_repository, repository_ids, deep_ids = _matched_frame(inputs)
    protocol = _mapping(plan, "statistical_protocol")
    bootstrap = _mapping(protocol, "repository_bootstrap")
    random_plan = _mapping(protocol, "random")
    score_cells: dict[str, Any] = {}
    for cell_id, budget, future_count in CELL_SPECS:
        cell = _mapping(_mapping(memberships, "cells"), cell_id)
        rows = _mapping_sequence(cell, "rows")
        loss_rows = _score_cell_rows(
            rows,
            inputs=inputs,
            origins_by_repository=origins_by_repository,
            repository_ids=repository_ids,
            future_count=future_count,
        )
        method_summaries = {
            method_id: {
                "wide": _direction_summary(method_rows, repository_ids),
                "deep": _direction_summary(method_rows, deep_ids),
            }
            for method_id, method_rows in loss_rows.items()
        }
        seed = int(_mapping(bootstrap, "seed_by_cell")[cell_id])
        paired = {}
        for method_id in ("ALG-018C-P", "ALG-018C"):
            paired_rows = _rows_against_control(
                loss_rows[method_id],
                "h_blind_control",
            )
            paired[method_id] = {
                "wide": _direction_summary(paired_rows, repository_ids),
                "deep": _direction_summary(paired_rows, deep_ids),
                "repository_bootstrap": _repository_bootstrap(
                    paired_rows,
                    repository_ids,
                    resamples=int(bootstrap["resamples"]),
                    seed=seed,
                ),
            }
        random = _matched_random_calibration(
            origins_by_repository,
            repository_ids,
            inputs,
            budget=budget,
            future_count=future_count,
            draws=int(random_plan["draws"]),
            seed=int(_mapping(random_plan, "seed_by_cell")[cell_id]),
            method_differences={
                method_id: float(
                    _mapping(method_summaries[method_id], "wide")["difference"]
                )
                for method_id in ("ALG-018C-P", "h_blind_control")
            },
        )
        score_cells[cell_id] = {
            "budget": budget,
            "future_count": future_count,
            "methods": method_summaries,
            "paired_vs_h_blind": paired,
            "random_calibration": random,
            "q_diagnostics": _q_diagnostics(rows),
        }
    horizon_swap = _horizon_swap_diagnostic(
        memberships,
        inputs=inputs,
        origins_by_repository=origins_by_repository,
        repository_ids=repository_ids,
        deep_ids=deep_ids,
    )
    plugin_contrasts = {
        cell_id: float(
            _mapping(
                _mapping(
                    _mapping(score_cells[cell_id], "paired_vs_h_blind"),
                    "ALG-018C-P",
                ),
                "wide",
            )["difference"]
        )
        for cell_id, _, _ in CELL_SPECS
    }
    general_support = all(
        float(
            _mapping(
                _mapping(
                    _mapping(score_cells[cell_id], "paired_vs_h_blind"),
                    "ALG-018C-P",
                ),
                "repository_bootstrap",
            )["upper"]
        )
        < 0.0
        for cell_id in ("B5_H5", "B10_H10")
    )
    grid_dominant = (
        not general_support
        and float(
            _mapping(
                _mapping(
                    _mapping(score_cells["B10_H5"], "paired_vs_h_blind"),
                    "ALG-018C-P",
                ),
                "repository_bootstrap",
            )["upper"]
        )
        < 0.0
        and abs(plugin_contrasts["B10_H5"])
        > 2.0
        * max(
            abs(value)
            for cell_id, value in plugin_contrasts.items()
            if cell_id != "B10_H5"
        )
    )
    interpretation = (
        "general_support"
        if general_support
        else ("grid_dominant" if grid_dominant else "mixed")
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "execution_lock_digest": lock.get("lock_digest"),
        "membership_digest": memberships.get("membership_digest"),
        "cells": score_cells,
        "horizon_swap": horizon_swap,
        "interpretation": {
            "general_support": general_support,
            "grid_dominant": grid_dominant,
            "terminal_state": interpretation,
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


def _build_cell_payloads(inputs: AuditInputs) -> Mapping[str, Any]:
    origins_by_repository, repository_ids, deep_ids = _matched_frame(inputs)
    cells: dict[str, Any] = {}
    for cell_id, budget, future_count in CELL_SPECS:
        rows = []
        for repository_id in repository_ids:
            for origin in origins_by_repository[repository_id]:
                history_indices = tuple(
                    inputs.data.task_index[task.instance_id] for task in origin.history
                )
                history = inputs.data.outcomes[list(history_indices), :]
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
                    plugin = select_plugin_action(n, s, future_count, budget)
                    plugin_unconstrained = select_plugin_action(
                        n,
                        s,
                        future_count,
                        budget,
                        ignore_inventory=True,
                    )
                    jeffreys = select_jeffreys_action(n, s, future_count, budget)
                    jeffreys_unconstrained = select_jeffreys_action(
                        n,
                        s,
                        future_count,
                        budget,
                        ignore_inventory=True,
                    )
                    h_blind = select_h_blind_action(n, s, budget)
                    method_actions = {
                        "ALG-018C-P": plugin,
                        "ALG-018C": jeffreys,
                    }
                    memberships = {
                        method_id: _membership_ids(
                            history_ids,
                            select_fixed_success_count_indices(
                                outcomes,
                                action.q,
                                budget=budget,
                                created_order=created_order,
                            ),
                        )
                        for method_id, action in method_actions.items()
                    }
                    memberships["h_blind_control"] = _membership_ids(
                        history_ids,
                        select_fixed_success_count_indices(
                            outcomes,
                            h_blind.q,
                            budget=budget,
                            created_order=created_order,
                        ),
                    )
                    rows.append(
                        {
                            "repository_id": repository_id,
                            "origin_id": origin.origin_id,
                            "target_configuration_id": configuration_id,
                            "history_task_count": n,
                            "history_success_count": s,
                            "budget": budget,
                            "future_count": future_count,
                            "actions": {
                                "ALG-018C-P": _finite_action_payload(
                                    plugin,
                                    plugin_unconstrained,
                                ),
                                "ALG-018C": _finite_action_payload(
                                    jeffreys,
                                    jeffreys_unconstrained,
                                ),
                                "h_blind_control": {
                                    "q": h_blind.q,
                                    "risk": h_blind.risk,
                                    "feasible_q_min": h_blind.feasible_q[0],
                                    "feasible_q_max": h_blind.feasible_q[-1],
                                },
                            },
                            "memberships": memberships,
                        }
                    )
        cells[cell_id] = {
            "budget": budget,
            "future_count": future_count,
            "repository_ids": list(repository_ids),
            "deep_repository_ids": list(deep_ids),
            "origin_count": sum(
                len(origins_by_repository[repository_id])
                for repository_id in repository_ids
            ),
            "target_row_count": len(rows),
            "membership_digests": {
                method_id: _algorithm_membership_digest(rows, method_id)
                for method_id in METHOD_IDS
            },
            "rows": rows,
            "rows_digest": canonical_digest(rows),
        }
    return cells


def _score_cell_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    inputs: AuditInputs,
    origins_by_repository: Mapping[str, Sequence[Any]],
    repository_ids: Sequence[str],
    future_count: int,
) -> dict[str, list[Mapping[str, object]]]:
    origin_lookup = {
        origin.origin_id: origin
        for repository_id in repository_ids
        for origin in origins_by_repository[repository_id]
    }
    configuration_index = {
        value: index for index, value in enumerate(inputs.data.configuration_ids)
    }
    result: dict[str, list[Mapping[str, object]]] = {
        method_id: [] for method_id in METHOD_IDS
    }
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        origin = origin_lookup[_required_string(row, "origin_id")]
        target = configuration_index[_required_string(row, "target_configuration_id")]
        history_indices = tuple(
            inputs.data.task_index[task.instance_id] for task in origin.history
        )
        future_indices = tuple(
            inputs.data.task_index[task.instance_id]
            for task in origin.future[:future_count]
        )
        memberships = _mapping(row, "memberships")
        control = tuple(
            inputs.data.task_index[task_id]
            for task_id in memberships["h_blind_control"]
        )
        for method_id in METHOD_IDS:
            result[method_id].append(
                _grid_loss_row(
                    inputs,
                    repository_id=repository_id,
                    origin_id=origin.origin_id,
                    target=target,
                    candidate=tuple(
                        inputs.data.task_index[task_id]
                        for task_id in memberships[method_id]
                    ),
                    full=history_indices,
                    control=control,
                    future=future_indices,
                    budget=int(row["budget"]),
                )
            )
    return result


def _grid_loss_row(
    inputs: AuditInputs,
    *,
    repository_id: str,
    origin_id: str,
    target: int,
    candidate: Sequence[int],
    full: Sequence[int],
    control: Sequence[int],
    future: Sequence[int],
    budget: int,
) -> Mapping[str, object]:
    if (
        len(candidate) != budget
        or len(candidate) != len(set(candidate))
        or len(control) != budget
        or len(control) != len(set(control))
        or not full
        or not future
    ):
        raise ValueError("grid pass-rate MAE membership is invalid")
    outcomes = inputs.data.outcomes[:, target]
    future_rate = float(outcomes[list(future)].mean())

    def loss(indices: Sequence[int]) -> float:
        return abs(float(outcomes[list(indices)].mean()) - future_rate)

    candidate_loss = loss(candidate)
    full_loss = loss(full)
    return {
        "repository_id": repository_id,
        "origin_id": origin_id,
        "configuration_id": inputs.data.configuration_ids[target],
        "candidate_loss": candidate_loss,
        "full_loss": full_loss,
        "difference": candidate_loss - full_loss,
        "control_losses": {"h_blind_control": loss(control)},
    }


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


def _matched_random_calibration(
    origins_by_repository: Mapping[str, Sequence[Any]],
    repository_ids: Sequence[str],
    inputs: AuditInputs,
    *,
    budget: int,
    future_count: int,
    draws: int,
    seed: int,
    method_differences: Mapping[str, float],
) -> Mapping[str, Any]:
    import numpy as np

    generator = np.random.default_rng(seed)
    repository_draws = {
        repository_id: np.zeros(draws, dtype=np.float64)
        for repository_id in repository_ids
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_indices = [
                inputs.data.task_index[task.instance_id] for task in origin.history
            ]
            future_indices = [
                inputs.data.task_index[task.instance_id]
                for task in origin.future[:future_count]
            ]
            history = inputs.data.outcomes[history_indices, :]
            future = inputs.data.outcomes[future_indices, :].mean(axis=0)
            full_loss = float(np.abs(history.mean(axis=0) - future).mean())
            offset = 0
            while offset < draws:
                chunk = min(512, draws - offset)
                keys = generator.random((chunk, len(history_indices)))
                selected = np.argpartition(keys, budget - 1, axis=1)[:, :budget]
                selected_rates = history[selected].mean(axis=1)
                losses = np.abs(selected_rates - future).mean(axis=1)
                repository_draws[repository_id][offset : offset + chunk] += (
                    losses - full_loss
                )
                offset += chunk
        repository_draws[repository_id] /= len(origins_by_repository[repository_id])
    macro = np.mean(
        np.stack([repository_draws[value] for value in repository_ids]),
        axis=0,
    )
    methods = {}
    for method_id, difference in method_differences.items():
        greater = int(np.sum(macro > difference))
        equal = int(np.sum(macro == difference))
        methods[method_id] = {
            "candidate_macro_repository_difference": difference,
            "candidate_better_than_random_midrank": (greater + 0.5 * equal) / draws,
            "random_as_good_or_better_rate": float(np.mean(macro <= difference)),
        }
    return {
        "draw_count": draws,
        "seed": seed,
        "generator": "numpy PCG64 random-key uniform subsets",
        "mean_macro_repository_difference": float(macro.mean()),
        "quantiles": {
            "0.025": float(np.quantile(macro, 0.025)),
            "0.5": float(np.quantile(macro, 0.5)),
            "0.975": float(np.quantile(macro, 0.975)),
        },
        "methods": methods,
    }


def _horizon_swap_diagnostic(
    memberships: Mapping[str, Any],
    *,
    inputs: AuditInputs,
    origins_by_repository: Mapping[str, Sequence[Any]],
    repository_ids: Sequence[str],
    deep_ids: Sequence[str],
) -> Mapping[str, Any]:
    h5_rows = _mapping_sequence(
        _mapping(_mapping(memberships, "cells"), "B10_H5"),
        "rows",
    )
    h10_rows = _mapping_sequence(
        _mapping(_mapping(memberships, "cells"), "B10_H10"),
        "rows",
    )
    h10_lookup = {
        (
            _required_string(row, "origin_id"),
            _required_string(row, "target_configuration_id"),
        ): row
        for row in h10_rows
    }
    configuration_index = {
        value: index for index, value in enumerate(inputs.data.configuration_ids)
    }
    origin_lookup = {
        origin.origin_id: origin
        for repository_id in repository_ids
        for origin in origins_by_repository[repository_id]
    }
    results = {}
    for evaluation_horizon in (5, 10):
        rows = []
        for h5_row in h5_rows:
            key = (
                _required_string(h5_row, "origin_id"),
                _required_string(h5_row, "target_configuration_id"),
            )
            h10_row = h10_lookup[key]
            matched_row = h10_row if evaluation_horizon == 10 else h5_row
            wrong_row = h5_row if evaluation_horizon == 10 else h10_row
            origin = origin_lookup[key[0]]
            target = configuration_index[key[1]]
            outcomes = inputs.data.outcomes[:, target]
            future_indices = [
                inputs.data.task_index[task.instance_id]
                for task in origin.future[:evaluation_horizon]
            ]
            future_rate = float(outcomes[future_indices].mean())

            def loss(row: Mapping[str, Any]) -> float:
                selected = [
                    inputs.data.task_index[task_id]
                    for task_id in _mapping(row, "memberships")["ALG-018C-P"]
                ]
                return abs(float(outcomes[selected].mean()) - future_rate)

            matched_loss = loss(matched_row)
            wrong_loss = loss(wrong_row)
            rows.append(
                {
                    "repository_id": origin.repository_id,
                    "origin_id": origin.origin_id,
                    "configuration_id": key[1],
                    "candidate_loss": wrong_loss,
                    "full_loss": matched_loss,
                    "difference": wrong_loss - matched_loss,
                    "control_losses": {},
                }
            )
        results[f"H{evaluation_horizon}"] = {
            "wrong_action_source_horizon": 10 if evaluation_horizon == 5 else 5,
            "wide": _direction_summary(rows, repository_ids),
            "deep": _direction_summary(rows, deep_ids),
        }
    return results


def _q_diagnostics(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    method_q: dict[str, list[int]] = {method_id: [] for method_id in METHOD_IDS}
    inventory_changes = {"ALG-018C-P": 0, "ALG-018C": 0}
    for row in rows:
        actions = _mapping(row, "actions")
        for method_id in METHOD_IDS:
            method_q[method_id].append(int(_mapping(actions, method_id)["q"]))
        for method_id in inventory_changes:
            inventory_changes[method_id] += bool(
                _mapping(actions, method_id)["inventory_changed_action"]
            )
    plugin = method_q["ALG-018C-P"]
    jeffreys = method_q["ALG-018C"]
    control = method_q["h_blind_control"]
    return {
        "cell_count": len(rows),
        "q_distribution": {
            method_id: {str(q): count for q, count in sorted(Counter(values).items())}
            for method_id, values in method_q.items()
        },
        "changed_from_h_blind_count": {
            method_id: sum(
                q != baseline
                for q, baseline in zip(
                    method_q[method_id],
                    control,
                    strict=True,
                )
            )
            for method_id in ("ALG-018C-P", "ALG-018C")
        },
        "plugin_vs_jeffreys_action_difference_count": sum(
            first != second for first, second in zip(plugin, jeffreys, strict=True)
        ),
        "inventory_changed_action_count": inventory_changes,
    }


def _direction_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    summary = dict(_repository_summary(rows, repository_ids))
    leave_one_out = summary["leave_one_repository_out"]
    if not isinstance(leave_one_out, Sequence):
        raise ValueError("repository leave-one-out summary is invalid")
    summary["every_leave_one_repository_out_negative"] = all(
        isinstance(item, Mapping)
        and _number(item.get("difference"), "LOO difference") < 0
        for item in leave_one_out
    )
    return summary


def _finite_action_payload(
    action: FiniteHorizonAction,
    unconstrained: FiniteHorizonAction,
) -> Mapping[str, Any]:
    return {
        "q": action.q,
        "risk": {
            "numerator": action.risk.numerator,
            "denominator": action.risk.denominator,
        },
        "feasible_q_min": action.feasible_q[0],
        "feasible_q_max": action.feasible_q[-1],
        "unconstrained_q": unconstrained.q,
        "inventory_changed_action": action.q != unconstrained.q,
    }


def _matched_frame(
    inputs: AuditInputs,
) -> tuple[Mapping[str, Sequence[Any]], tuple[str, ...], tuple[str, ...]]:
    return _horizon_frame(
        inputs.data.tasks,
        inputs.selector_plan,
        10,
    )


def _membership_ids(
    history_ids: Sequence[str],
    positions: Sequence[int],
) -> list[str]:
    return [history_ids[position] for position in positions]


def _algorithm_membership_digest(
    rows: Sequence[Mapping[str, Any]],
    method_id: str,
) -> str:
    return canonical_digest(
        [
            {
                "repository_id": row["repository_id"],
                "origin_id": row["origin_id"],
                "target_configuration_id": row["target_configuration_id"],
                "task_ids": _mapping(row, "memberships")[method_id],
            }
            for row in rows
        ]
    )


def _validate_source_bindings(
    plan: Mapping[str, Any],
    lock: Mapping[str, Any],
    inputs: AuditInputs,
) -> None:
    source = _mapping(plan, "source_bindings")
    parent_plan = load_parent_plan()
    parent_lock = load_parent_execution_lock(plan=parent_plan)
    parent_source = _mapping(parent_plan, "source_bindings")
    if (
        source.get("parent_plan_digest") != parent_plan.get("plan_digest")
        or source.get("parent_execution_lock_digest") != parent_lock.get("lock_digest")
        or lock.get("parent_result_digest") != source.get("parent_result_digest")
        or lock.get("parent_result_raw_sha256")
        != source.get("parent_result_raw_sha256")
        or source.get("resolved_outcome_digest")
        != parent_source.get("resolved_outcome_digest")
        or source.get("task_time_projection_digest")
        != parent_source.get("task_time_projection_digest")
        or _mapping(lock, "matched_h10_frame") != _frame_identity(inputs, 10)
    ):
        raise ValueError("finite-horizon grid source binding changed")


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
    """Run one matched grid-audit command."""
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
