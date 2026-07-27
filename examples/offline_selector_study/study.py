#!/usr/bin/env python3
"""Run the zero-call historical Task-order Selector diagnostic."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import NormalDist, pstdev
import sys
from typing import Any, cast


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (
    AgentRecord,
    ResultRecord,
    TaskRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    parse_utc_timestamp,
    task_check_ref_key,
    TaskCheckRef,
    validate_agent,
    validate_result,
)
from barcarolle.selection import RollingOriginPolicy, build_rolling_origin
from barcarolle.task_pool import TaskPoolBundle, TimeRange, open_task_pool_bundle
from examples.pylint_swe_bench_verified.replicate_schedule import (
    ReplicateSchedule,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "study-plan.json"
DEFAULT_AMENDMENT = HERE / "study-amendment-1.json"
DEFAULT_CORRECTION = HERE / "study-amendment-2.json"
DEFAULT_RESULTS = HERE / "study-results.json"
DEFAULT_SOURCE_ROOT = (
    REPOSITORY_ROOT / "outputs/research/2026-07-25-model-agent-study"
)
DEFAULT_TASK_POOL = (
    DEFAULT_SOURCE_ROOT
    / "sympy/artifacts/task-pools"
    / "5abe65a19bf6e9eaf50864618488f1f14834cdd8e6171a454c093b72c99576bb"
    / "task-pool.jsonl"
)
DEFAULT_MAIN_RECORDS = (
    DEFAULT_SOURCE_ROOT
    / "main/model-main-sympy-2026-07-25/records"
)
DEFAULT_MODEL_STUDY_RESULTS = (
    REPOSITORY_ROOT / "examples/model_agent_study/study-results.json"
)
AGENT_KEY_BY_MODEL = {
    "gpt-5.6-terra": "gpt-5.6-terra-high",
    "gpt-5.4-mini": "gpt-5.4-mini-high",
}
PRIMARY_SELECTOR_NAMES = (
    "coverage",
    "random_seed_5",
    "recency",
    "stratified_unweighted",
    "stratified_weighted",
    "rank_mixture_equal",
)
ADAPTIVE_CANDIDATE_NAMES = (
    "coverage",
    "random_seed_5",
    "recency",
    "stratified_unweighted",
    "stratified_weighted",
)
BOOTSTRAP_SEED = 20_260_722
BOOTSTRAP_RESAMPLES = 10_000


@dataclass(frozen=True)
class StudyPaths:
    plan: Path = DEFAULT_PLAN
    amendment: Path = DEFAULT_AMENDMENT
    correction: Path = DEFAULT_CORRECTION
    task_pool: Path = DEFAULT_TASK_POOL
    main_records: Path = DEFAULT_MAIN_RECORDS
    model_study_results: Path = DEFAULT_MODEL_STUDY_RESULTS
    output: Path = DEFAULT_RESULTS


@dataclass(frozen=True)
class Metadata:
    bundle: TaskPoolBundle
    agents: tuple[AgentRecord, ...]
    schedule: ReplicateSchedule
    ordered_tasks: tuple[TaskRecord, ...]
    agent_key_by_id: Mapping[str, str]


@dataclass(frozen=True)
class SelectorSpec:
    name: str
    family: str
    parameters: Mapping[str, object]


@dataclass(frozen=True)
class DiagnosticSelection:
    selector_name: str
    task_ids: tuple[str, ...]
    weights: Mapping[str, float]
    diagnostics: Mapping[str, object]


@dataclass(frozen=True)
class DiagnosticOrigin:
    origin_number: int
    history: tuple[TaskRecord, ...]
    future: tuple[TaskRecord, ...]
    selections: Mapping[str, DiagnosticSelection]


@dataclass(frozen=True)
class DiagnosticDesign:
    origins: tuple[DiagnosticOrigin, ...]
    specs: Mapping[str, SelectorSpec]
    design_digest: str


@dataclass(frozen=True)
class Outcomes:
    base: Mapping[str, Mapping[str, int]]
    scoreable_replicates: Mapping[str, Mapping[str, tuple[int, ...]]]
    result_count: int
    scoreable_result_count: int


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    return _load_self_digested_json(
        path,
        digest_field="study_plan_digest",
        expected_schema="barcarolle_offline_selector_study_plan_v1",
    )


def load_amendment(
    path: Path,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    amendment = _load_self_digested_json(
        path,
        digest_field="amendment_digest",
        expected_schema="barcarolle_offline_selector_study_amendment_v1",
    )
    if amendment.get("base_study_plan_digest") != plan["study_plan_digest"]:
        raise ValueError("study amendment does not bind the frozen plan")
    return amendment


def load_correction(
    path: Path,
    plan: Mapping[str, Any],
    amendment: Mapping[str, Any],
) -> Mapping[str, Any]:
    correction = _load_self_digested_json(
        path,
        digest_field="amendment_digest",
        expected_schema="barcarolle_offline_selector_study_amendment_v2",
    )
    if (
        correction.get("base_study_plan_digest") != plan["study_plan_digest"]
        or correction.get("previous_amendment_digest")
        != amendment["amendment_digest"]
    ):
        raise ValueError("study correction does not bind the amendment chain")
    return correction


def load_metadata(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    correction: Mapping[str, Any],
) -> Metadata:
    bindings = _mapping(plan, "source_bindings")
    corrected_binding = _mapping(correction, "correction")
    if (
        corrected_binding.get("field")
        != "source_bindings.task_pool_manifest_sha256"
        or corrected_binding.get("incorrect")
        != bindings["task_pool_manifest_sha256"]
    ):
        raise ValueError("source correction does not match the frozen bad binding")
    _require_sha256(
        paths.task_pool,
        _string(corrected_binding, "correct"),
    )
    agents_path = paths.main_records / "agents.jsonl"
    schedule_path = paths.main_records / "replicate-schedule.jsonl"
    _require_sha256(
        agents_path,
        _string(bindings, "agent_records_sha256"),
    )
    _require_sha256(
        schedule_path,
        _string(bindings, "replicate_schedule_sha256"),
    )
    bundle = open_task_pool_bundle(paths.task_pool)
    if (
        bundle.task_pool.task_pool_id != bindings["task_pool_id"]
        or bundle.task_pool.task_pool_digest != bindings["task_pool_digest"]
    ):
        raise ValueError("Task Pool does not match the frozen source binding")
    agents = tuple(load_jsonl_records(agents_path, AgentRecord))
    if any(not validate_agent(agent).ok for agent in agents):
        raise ValueError("main source contains an invalid Agent record")
    schedules = tuple(load_jsonl_records(schedule_path, ReplicateSchedule))
    if len(schedules) != 1:
        raise ValueError("main source must contain exactly one replicate schedule")
    key_by_id: dict[str, str] = {}
    for agent in agents:
        key = AGENT_KEY_BY_MODEL.get(agent.requested_model_id)
        if key is None or key in key_by_id.values():
            raise ValueError("main Agent set does not match the frozen study")
        key_by_id[agent.agent_id] = key
    declared_agents = tuple(cast(Sequence[str], bindings["agents"]))
    if tuple(key_by_id[agent.agent_id] for agent in agents) != declared_agents:
        raise ValueError("main Agent ordering does not match the frozen plan")
    ordered_tasks = tuple(
        sorted(
            bundle.tasks,
            key=lambda task: (
                parse_utc_timestamp(task.task_material_available_at),
                task.task_id,
            ),
        )
    )
    if len(ordered_tasks) != 75:
        raise ValueError("frozen diagnostic requires exactly 75 Tasks")
    return Metadata(bundle, agents, schedules[0], ordered_tasks, key_by_id)


def build_design(
    metadata: Metadata,
    plan: Mapping[str, Any],
) -> DiagnosticDesign:
    rolling = _mapping(plan, "rolling_origin")
    initial = _integer(rolling, "initial_history_task_count")
    block_size = _integer(rolling, "future_block_task_count")
    origin_count = _integer(rolling, "origin_count")
    budget = _integer(rolling, "selection_budget_task_checks")
    blocks = chronological_blocks(
        metadata.ordered_tasks,
        initial_history_count=initial,
        future_block_count=block_size,
    )
    if len(blocks) != origin_count:
        raise ValueError("Task chronology does not yield the frozen Origin count")
    specs = selector_specs(plan)
    origins: list[DiagnosticOrigin] = []
    for number, (history, future) in enumerate(blocks, start=1):
        selections = {
            name: select_tasks(spec, history, budget)
            for name, spec in specs.items()
        }
        origins.append(DiagnosticOrigin(number, history, future, selections))
    digest_payload = {
        "origin_membership": tuple(
            {
                "origin_number": origin.origin_number,
                "history_task_ids": tuple(task.task_id for task in origin.history),
                "future_task_ids": tuple(task.task_id for task in origin.future),
                "selections": {
                    name: {
                        "task_ids": selection.task_ids,
                        "weights": selection.weights,
                    }
                    for name, selection in sorted(origin.selections.items())
                },
            }
            for origin in origins
        )
    }
    return DiagnosticDesign(
        tuple(origins),
        specs,
        canonical_digest(digest_payload),
    )


def chronological_blocks(
    ordered_tasks: Sequence[TaskRecord],
    *,
    initial_history_count: int,
    future_block_count: int,
) -> tuple[tuple[tuple[TaskRecord, ...], tuple[TaskRecord, ...]], ...]:
    if initial_history_count < 1 or future_block_count < 1:
        raise ValueError("history and future block counts must be positive")
    remaining = len(ordered_tasks) - initial_history_count
    if remaining < future_block_count or remaining % future_block_count:
        raise ValueError("Task count does not tile the declared future blocks")
    blocks = []
    for start in range(
        initial_history_count,
        len(ordered_tasks),
        future_block_count,
    ):
        blocks.append(
            (
                tuple(ordered_tasks[:start]),
                tuple(ordered_tasks[start : start + future_block_count]),
            )
        )
    return tuple(blocks)


def selector_specs(plan: Mapping[str, Any]) -> Mapping[str, SelectorSpec]:
    primary = _mapping(plan, "primary_selectors")
    specs: dict[str, SelectorSpec] = {}
    for name, value in primary.items():
        if not isinstance(value, Mapping):
            raise ValueError("primary Selector definitions must be objects")
        family = _string(value, "family")
        parameters = {
            key: item
            for key, item in value.items()
            if key not in {"family", "groups"}
        }
        specs[name] = SelectorSpec(name, family, parameters)
    sensitivity = _mapping(plan, "sensitivity_analyses")
    for seed in _integer_sequence(sensitivity, "random_seed_bank"):
        name = f"random_seed_{seed}"
        specs.setdefault(name, SelectorSpec(name, "random", {"seed": seed}))
    for seed in _integer_sequence(sensitivity, "stratified_seed_bank"):
        name = f"stratified_weighted_seed_{seed}"
        specs[name] = SelectorSpec(
            name,
            "stratified_forecast",
            {
                "alpha": 1.0,
                "trailing_ref_count": 15,
                "seed": seed,
                "weight_cap": 3.0,
            },
        )
    grid = _mapping(sensitivity, "stratified_parameter_grid")
    for alpha in _number_sequence(grid, "alpha", allow_none=False):
        for window in _integer_sequence(grid, "trailing_ref_count"):
            for cap in _number_sequence(grid, "weight_cap", allow_none=True):
                name = (
                    f"stratified_grid_a{_slug(alpha)}_w{window}"
                    f"_c{_slug(cap)}_s5"
                )
                specs[name] = SelectorSpec(
                    name,
                    "stratified_forecast",
                    {
                        "alpha": alpha,
                        "trailing_ref_count": window,
                        "seed": 5,
                        "weight_cap": cap,
                    },
                )
    for seed in _integer_sequence(sensitivity, "rank_mixture_seed_bank"):
        for coverage_units in range(4):
            for random_units in range(4 - coverage_units):
                recency_units = 3 - coverage_units - random_units
                name = (
                    f"mixture_s{seed}_c{coverage_units}"
                    f"_r{random_units}_t{recency_units}"
                )
                specs[name] = SelectorSpec(
                    name,
                    "rule_mixture",
                    {
                        "expert_weights": {
                            "coverage": coverage_units / 3,
                            "random": random_units / 3,
                            "recency": recency_units / 3,
                        },
                        "random_seed": seed,
                    },
                )
    return dict(sorted(specs.items()))


def select_tasks(
    spec: SelectorSpec,
    history: Sequence[TaskRecord],
    budget: int,
) -> DiagnosticSelection:
    count = min(budget, len(history))
    if count < 1:
        raise ValueError("diagnostic Selection requires eligible history")
    diagnostics: dict[str, object] = {}
    weights: dict[str, float]
    if spec.family == "coverage":
        ordered = _coverage_order(history)
        selected = ordered[:count]
        weights = {task.task_id: 1.0 for task in selected}
    elif spec.family == "random":
        ordered = list(history)
        random.Random(_integer(spec.parameters, "seed")).shuffle(ordered)
        selected = tuple(ordered[:count])
        weights = {task.task_id: 1.0 for task in selected}
    elif spec.family == "recency":
        selected = tuple(reversed(history))[:count]
        weights = {task.task_id: 1.0 for task in selected}
    elif spec.family == "rule_mixture":
        ordered = _rule_mixture_order(history, spec.parameters)
        selected = ordered[:count]
        weights = {task.task_id: 1.0 for task in selected}
    elif spec.family == "stratified_forecast":
        selected, weights, diagnostics = _stratified_selection(
            history,
            count,
            spec.parameters,
        )
    else:
        raise ValueError(f"unsupported diagnostic Selector: {spec.family}")
    if len({task.task_id for task in selected}) != count:
        raise ValueError("diagnostic Selection contains duplicate Tasks")
    return DiagnosticSelection(
        spec.name,
        tuple(task.task_id for task in selected),
        weights,
        diagnostics,
    )


def _coverage_order(history: Sequence[TaskRecord]) -> tuple[TaskRecord, ...]:
    grouped: dict[str, deque[TaskRecord]] = {}
    for task in history:
        grouped.setdefault(task.sampling_stratum, deque()).append(task)
    active = deque(sorted(grouped))
    ordered: list[TaskRecord] = []
    while active:
        group = active.popleft()
        ordered.append(grouped[group].popleft())
        if grouped[group]:
            active.append(group)
    return tuple(ordered)


def _rule_mixture_order(
    history: Sequence[TaskRecord],
    parameters: Mapping[str, object],
) -> tuple[TaskRecord, ...]:
    weights = _mapping(parameters, "expert_weights")
    seed = _integer(parameters, "random_seed")
    total = sum(_number(weights, family) for family in ("coverage", "random", "recency"))
    if not math.isclose(total, 1.0):
        raise ValueError("rank-mixture weights must sum to one")
    coverage = _coverage_order(history)
    coverage_scores = {
        task.task_id: (len(coverage) - rank) / len(coverage)
        for rank, task in enumerate(coverage)
    }
    randomized = list(history)
    random.Random(seed).shuffle(randomized)
    random_scores = {
        task.task_id: (len(randomized) - rank) / len(randomized)
        for rank, task in enumerate(randomized)
    }
    scored = []
    for index, task in enumerate(history):
        score = (
            _number(weights, "coverage") * coverage_scores[task.task_id]
            + _number(weights, "random") * random_scores[task.task_id]
            + _number(weights, "recency") * ((index + 1) / len(history))
        )
        scored.append((score, task))
    return tuple(
        task
        for _, task in sorted(
            scored,
            key=lambda item: (-item[0], item[1].task_id),
        )
    )


def _stratified_selection(
    history: Sequence[TaskRecord],
    count: int,
    parameters: Mapping[str, object],
) -> tuple[tuple[TaskRecord, ...], dict[str, float], dict[str, object]]:
    alpha = _number(parameters, "alpha")
    window = _integer(parameters, "trailing_ref_count")
    seed = _integer(parameters, "seed")
    cap_value = parameters.get("weight_cap")
    cap = None if cap_value is None else _finite_number(cap_value, "weight_cap")
    strata = tuple(sorted({task.sampling_stratum for task in history}))
    trailing = tuple(history)[-min(window, len(history)) :]
    trailing_counts = Counter(task.sampling_stratum for task in trailing)
    denominator = len(trailing) + alpha * len(strata)
    forecast = {
        stratum: (trailing_counts[stratum] + alpha) / denominator
        for stratum in strata
    }
    by_stratum = {
        stratum: tuple(
            task for task in history if task.sampling_stratum == stratum
        )
        for stratum in strata
    }
    quotas = _allocate_quotas(
        count,
        forecast,
        {stratum: len(tasks) for stratum, tasks in by_stratum.items()},
    )
    selected = tuple(
        task
        for stratum in strata
        for task in sorted(
            by_stratum[stratum],
            key=lambda item: (
                canonical_digest(
                    (
                        seed,
                        task_check_ref_key(
                            TaskCheckRef(item.task_id, item.check_ids[0])
                        ),
                    )
                ),
                item.task_id,
            ),
        )[: quotas[stratum]]
    )
    selected_share = {
        stratum: quotas[stratum] / count
        for stratum in strata
        if quotas[stratum]
    }
    raw_weight = {
        stratum: forecast[stratum] / selected_share[stratum]
        for stratum in selected_share
    }
    weights = {
        task.task_id: (
            1.0
            if cap is None
            else min(cap, raw_weight[task.sampling_stratum])
        )
        for task in selected
    }
    capped_count = sum(
        cap is not None
        and raw_weight[task.sampling_stratum] > cap
        for task in selected
    )
    weight_values = tuple(weights.values())
    effective_size = sum(weight_values) ** 2 / sum(
        value * value for value in weight_values
    )
    return (
        selected,
        weights,
        {
            "forecast_proportions": forecast,
            "quota_by_stratum": quotas,
            "maximum_selected_weight": max(weight_values),
            "effective_sample_size": effective_size,
            "capped_selected_fraction": capped_count / len(selected),
        },
    )


def _allocate_quotas(
    count: int,
    proportions: Mapping[str, float],
    capacities: Mapping[str, int],
) -> dict[str, int]:
    exact = {stratum: count * value for stratum, value in proportions.items()}
    quotas = {
        stratum: min(capacities[stratum], math.floor(exact[stratum]))
        for stratum in proportions
    }
    while sum(quotas.values()) < count:
        available = tuple(
            stratum
            for stratum in proportions
            if quotas[stratum] < capacities[stratum]
        )
        if not available:
            raise ValueError("stratified diagnostic exceeds history capacity")
        chosen = min(
            available,
            key=lambda stratum: (
                -(exact[stratum] - quotas[stratum]),
                -proportions[stratum],
                stratum,
            ),
        )
        quotas[chosen] += 1
    return quotas


def audit_core_maturity(
    metadata: Metadata,
    design: DiagnosticDesign,
) -> Mapping[str, object]:
    checks = {check.check_id: check for check in metadata.bundle.checks}
    policy = RollingOriginPolicy(
        as_of_cutoff_rule="origin_time",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        future_holdout_known=True,
    )
    rows = []
    for diagnostic in design.origins:
        cutoff = diagnostic.history[-1].task_material_available_at
        origin = build_rolling_origin(
            metadata.bundle.task_pool,
            metadata.bundle.tasks,
            checks,
            parse_utc_timestamp(cutoff),
            TimeRange(
                diagnostic.future[0].task_material_available_at,
                diagnostic.future[-1].task_material_available_at,
            ),
            policy,
        )
        rows.append(
            {
                "origin_number": diagnostic.origin_number,
                "history_mature_count": len(origin.history_task_check_refs),
                "history_censored_count": len(
                    origin.history_censored_task_check_refs
                ),
                "future_mature_count": len(
                    origin.future_holdout_task_check_refs
                ),
                "future_censored_count": len(
                    origin.future_censored_task_check_refs
                ),
                "origin_digest": origin.origin_digest,
            }
        )
    all_checks = tuple(metadata.bundle.checks)
    return {
        "status": "planned_core_evidence_path_invalid",
        "reason": "historical Task/Check labels are not mature at historical cutoffs",
        "check_material_available_at": {
            "minimum": min(
                check.check_material_available_at for check in all_checks
            ),
            "maximum": max(
                check.check_material_available_at for check in all_checks
            ),
            "distinct_count": len(
                {check.check_material_available_at for check in all_checks}
            ),
        },
        "origins": rows,
        "all_history_mature_counts_zero": all(
            row["history_mature_count"] == 0 for row in rows
        ),
        "all_future_mature_counts_zero": all(
            row["future_mature_count"] == 0 for row in rows
        ),
    }


def load_outcomes(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    metadata: Metadata,
) -> Outcomes:
    results_path = paths.main_records / "results.jsonl"
    bindings = _mapping(plan, "source_bindings")
    _require_sha256(results_path, _string(bindings, "result_records_sha256"))
    results = tuple(load_jsonl_records(results_path, ResultRecord))
    if any(not validate_result(result).ok for result in results):
        raise ValueError("source contains an invalid Result record")
    by_execution = {
        (
            result.agent_id,
            result.task_id,
            result.cache_identity.runtime_config_digest,
        ): result
        for result in results
    }
    if len(by_execution) != len(results):
        raise ValueError("source Result records have duplicate execution identities")
    by_replicate: dict[str, dict[str, dict[int, ResultRecord]]] = {}
    consumed_execution_keys: set[tuple[str, str, str]] = set()
    for cell in metadata.schedule.cells:
        execution_key = (
            cell.agent_id,
            cell.task_id,
            cell.runtime_config_digest,
        )
        result = by_execution.get(
            execution_key
        )
        if result is None or result.check_id != cell.check_id:
            raise ValueError("replicate schedule does not bind every Result")
        if execution_key in consumed_execution_keys:
            raise ValueError("replicate schedule repeats an execution identity")
        consumed_execution_keys.add(execution_key)
        key = metadata.agent_key_by_id[cell.agent_id]
        by_replicate.setdefault(key, {}).setdefault(cell.task_id, {})[
            cell.replicate_index
        ] = result
    base: dict[str, dict[str, int]] = {}
    scoreable_replicates: dict[str, dict[str, tuple[int, ...]]] = {}
    for key in metadata.agent_key_by_id.values():
        base[key] = {}
        scoreable_replicates[key] = {}
        for task in metadata.ordered_tasks:
            task_results = by_replicate.get(key, {}).get(task.task_id, {})
            base_result = task_results.get(0)
            if base_result is None or base_result.scoreable_state != "scoreable":
                raise ValueError("every Agent/Task base Result must be scoreable")
            base[key][task.task_id] = int(base_result.outcome == "pass")
            available = tuple(
                int(result.outcome == "pass")
                for _, result in sorted(task_results.items())
                if result.scoreable_state == "scoreable"
            )
            if not available:
                raise ValueError("every Agent/Task needs a scoreable outcome")
            scoreable_replicates[key][task.task_id] = available
    if len(consumed_execution_keys) != len(results):
        raise ValueError("source contains a Result outside the frozen schedule")
    return Outcomes(
        base,
        scoreable_replicates,
        len(results),
        sum(result.scoreable_state == "scoreable" for result in results),
    )


def run_study(paths: StudyPaths = StudyPaths()) -> Mapping[str, object]:
    plan = load_plan(paths.plan)
    amendment = load_amendment(paths.amendment, plan)
    correction = load_correction(paths.correction, plan, amendment)
    metadata = load_metadata(paths, plan, correction)
    design = build_design(metadata, plan)
    maturity = audit_core_maturity(metadata, design)
    outcomes = load_outcomes(paths, plan, metadata)
    fixed = fixed_selector_analysis(design, outcomes)
    adaptive = adaptive_analysis(design, outcomes)
    composition = composition_analysis(design, outcomes)
    sensitivity = sensitivity_analysis(
        metadata,
        design,
        outcomes,
        plan,
    )
    headroom = headroom_analysis(design, outcomes)
    power_budget = power_and_budget_analysis(
        fixed,
        paths.model_study_results,
        design,
    )
    audit = audit_diagnostic(
        metadata,
        design,
        outcomes,
        maturity,
        fixed,
    )
    diagnostic_status = _diagnostic_status(fixed)
    payload: dict[str, object] = {
        "schema_version": "barcarolle_offline_selector_study_results_v1",
        "study_id": plan["study_id"],
        "status": "complete",
        "study_plan_digest": plan["study_plan_digest"],
        "study_amendment_digests": (
            amendment["amendment_digest"],
            correction["amendment_digest"],
        ),
        "authority": {
            "new_paid_calls": 0,
            "network_calls": 0,
        },
        "claim": {
            "core_rolling_origin": "invalid_or_insufficient_evidence",
            "historical_task_order_diagnostic": diagnostic_status,
            "boundary": amendment["claim_boundary"],
        },
        "source": {
            "task_pool_id": metadata.bundle.task_pool.task_pool_id,
            "task_pool_digest": metadata.bundle.task_pool.task_pool_digest,
            "task_count": len(metadata.ordered_tasks),
            "agent_count": len(metadata.agents),
            "result_count": outcomes.result_count,
            "scoreable_result_count": outcomes.scoreable_result_count,
            "dependency_cluster_count": len(
                {task.dependency_cluster_id for task in metadata.ordered_tasks}
            ),
            "task_time_range": {
                "start": metadata.ordered_tasks[0].task_material_available_at,
                "end": metadata.ordered_tasks[-1].task_material_available_at,
            },
        },
        "core_maturity_audit": maturity,
        "diagnostic_design": {
            "eligibility": "historical_task_order_projection_not_core_evidence",
            "design_digest": design.design_digest,
            "origin_count": len(design.origins),
            "initial_history_task_count": len(design.origins[0].history),
            "future_block_task_count": len(design.origins[0].future),
            "selection_budget_task_count": len(
                design.origins[0]
                .selections["stratified_weighted"]
                .task_ids
            ),
        },
        "fixed_selectors": fixed,
        "adaptive_rules": adaptive,
        "composition": composition,
        "sensitivity": sensitivity,
        "headroom": headroom,
        "power_and_budget": power_budget,
        "audit": audit,
        "approach_registry": (
            {
                "approach": "core_contract_replay",
                "status": "falsified_by_check_maturity",
                "decisive_evidence": "core_maturity_audit",
            },
            {
                "approach": "transparent_independent_recalculation",
                "status": "completed",
                "decisive_evidence": "audit.independent_metric_recalculation",
            },
            {
                "approach": "adversarial_noise_headroom_and_power",
                "status": "completed",
                "decisive_evidence": "sensitivity, headroom, power_and_budget",
            },
        ),
        "study_results_digest": "",
    }
    payload["study_results_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "study_results_digest"}
    )
    return payload


def fixed_selector_analysis(
    design: DiagnosticDesign,
    outcomes: Outcomes,
) -> Mapping[str, object]:
    rows = loss_rows(design, outcomes.base, PRIMARY_SELECTOR_NAMES)
    selector_summary = {
        name: _loss_summary(tuple(row[name] for row in rows))
        for name in PRIMARY_SELECTOR_NAMES
    }
    by_agent = {
        agent: {
            name: _loss_summary(
                tuple(
                    diagnostic_mae(
                        origin.selections[name],
                        origin.future,
                        {agent: outcomes.base[agent]},
                    )
                    for origin in design.origins
                )
            )
            for name in PRIMARY_SELECTOR_NAMES
        }
        for agent in outcomes.base
    }
    differences = tuple(
        row["stratified_weighted"] - row["coverage"] for row in rows
    )
    coverage_contrasts = {
        other: _difference_summary(
            tuple(row["coverage"] - row[other] for row in rows)
        )
        for other in (
            "random_seed_5",
            "recency",
            "stratified_weighted",
        )
    }
    random_bank_names = tuple(
        sorted(
            (
                name
                for name in design.specs
                if name.startswith("random_seed_")
            ),
            key=lambda name: int(name.removeprefix("random_seed_")),
        )
    )
    random_bank_rows = loss_rows(design, outcomes.base, random_bank_names)
    coverage_random_bank = _difference_summary(
        tuple(
            rows[index]["coverage"]
            - sum(row[name] for name in random_bank_names)
            / len(random_bank_names)
            for index, row in enumerate(random_bank_rows)
        )
    )
    return {
        "origin_count": len(rows),
        "selectors": selector_summary,
        "by_agent": by_agent,
        "primary_contrast": {
            "selector_a": "stratified_weighted",
            "selector_b": "coverage",
            "difference_direction": "selector_a_minus_selector_b",
            **_difference_summary(differences),
        },
        "exploratory_coverage_contrasts": coverage_contrasts,
        "coverage_minus_random_seed_bank_mean": {
            "seed_count": len(random_bank_names),
            "seeds": tuple(
                int(name.removeprefix("random_seed_"))
                for name in random_bank_names
            ),
            **coverage_random_bank,
        },
        "prospective_candidate_nomination": (
            "Coverage is eligible for a future preregistered comparison only; "
            "it was the predeclared fallback, not the primary candidate."
        ),
        "origin_losses": tuple(
            {
                "origin_number": index,
                "mae_by_selector": dict(sorted(row.items())),
            }
            for index, row in enumerate(rows, start=1)
        ),
    }


def loss_rows(
    design: DiagnosticDesign,
    outcomes: Mapping[str, Mapping[str, int]],
    selector_names: Sequence[str],
) -> tuple[Mapping[str, float], ...]:
    return tuple(
        {
            name: diagnostic_mae(
                origin.selections[name],
                origin.future,
                outcomes,
            )
            for name in selector_names
        }
        for origin in design.origins
    )


def diagnostic_mae(
    selection: DiagnosticSelection,
    future: Sequence[TaskRecord],
    outcomes: Mapping[str, Mapping[str, int]],
) -> float:
    weights = tuple(selection.weights[task_id] for task_id in selection.task_ids)
    denominator = sum(weights)
    losses = []
    for agent_outcomes in outcomes.values():
        selected_rate = sum(
            agent_outcomes[task_id] * weight
            for task_id, weight in zip(selection.task_ids, weights, strict=True)
        ) / denominator
        future_rate = sum(
            agent_outcomes[task.task_id] for task in future
        ) / len(future)
        losses.append(abs(selected_rate - future_rate))
    return sum(losses) / len(losses)


def independent_diagnostic_mae(
    selection: DiagnosticSelection,
    future: Sequence[TaskRecord],
    outcomes: Mapping[str, Mapping[str, int]],
) -> float:
    total = 0.0
    agent_count = 0
    for agent in sorted(outcomes):
        selected_numerator = 0.0
        selected_denominator = 0.0
        for task_id in selection.task_ids:
            weight = selection.weights[task_id]
            selected_numerator += outcomes[agent][task_id] * weight
            selected_denominator += weight
        future_passes = 0
        for task in future:
            future_passes += outcomes[agent][task.task_id]
        total += abs(
            selected_numerator / selected_denominator
            - future_passes / len(future)
        )
        agent_count += 1
    return total / agent_count


def adaptive_analysis(
    design: DiagnosticDesign,
    outcomes: Outcomes,
) -> Mapping[str, object]:
    candidate_rows = loss_rows(design, outcomes.base, ADAPTIVE_CANDIDATE_NAMES)
    grid_names = tuple(
        name
        for name in design.specs
        if name.startswith("mixture_s5_")
    )
    grid_rows = loss_rows(design, outcomes.base, grid_names)
    strategy_losses: dict[str, list[float]] = {
        "raw_mean_choice": [],
        "ALG-001": [],
        "ALG-003": [],
        "ALG-004": [],
    }
    choices: dict[str, list[str]] = {name: [] for name in strategy_losses}
    fallback_losses: list[float] = []
    hindsight_losses: list[float] = []
    for outer_index in range(4, len(design.origins)):
        prior_candidates = candidate_rows[:outer_index]
        current_candidates = candidate_rows[outer_index]
        raw = _choose_mean(ADAPTIVE_CANDIDATE_NAMES, prior_candidates)
        safe = _choose_safe(
            ADAPTIVE_CANDIDATE_NAMES,
            prior_candidates,
            fallback="coverage",
        )
        ewma = _choose_ewma_guard(
            ADAPTIVE_CANDIDATE_NAMES,
            prior_candidates,
            fallback="coverage",
            half_life=2.0,
        )
        mixture = _choose_grid_one_se(grid_names, grid_rows[:outer_index])
        chosen = {
            "raw_mean_choice": raw,
            "ALG-001": safe,
            "ALG-003": mixture,
            "ALG-004": ewma,
        }
        for strategy, selector_name in chosen.items():
            source_row = (
                grid_rows[outer_index]
                if strategy == "ALG-003"
                else current_candidates
            )
            strategy_losses[strategy].append(source_row[selector_name])
            choices[strategy].append(selector_name)
        fallback_losses.append(current_candidates["coverage"])
        hindsight_losses.append(min(current_candidates.values()))
    result: dict[str, object] = {}
    for strategy, values in strategy_losses.items():
        differences = tuple(
            value - fallback
            for value, fallback in zip(values, fallback_losses, strict=True)
        )
        result[strategy] = {
            **_loss_summary(tuple(values)),
            "choice_counts": dict(sorted(Counter(choices[strategy]).items())),
            "difference_from_coverage": _difference_summary(differences),
        }
    return {
        "outer_origin_count": len(fallback_losses),
        "strategies": result,
        "coverage_fallback": _loss_summary(tuple(fallback_losses)),
        "hindsight_fixed_candidate_oracle": _loss_summary(
            tuple(hindsight_losses)
        ),
    }


def _choose_mean(
    names: Sequence[str],
    prior_rows: Sequence[Mapping[str, float]],
) -> str:
    means = {
        name: sum(row[name] for row in prior_rows) / len(prior_rows)
        for name in names
    }
    return min(names, key=lambda name: (means[name], name))


def _choose_safe(
    names: Sequence[str],
    prior_rows: Sequence[Mapping[str, float]],
    *,
    fallback: str,
    prior_strength: float = 2.0,
    uncertainty_multiplier: float = 1.0,
) -> str:
    if len(prior_rows) < 4:
        return fallback
    qualified: list[tuple[float, float, str]] = []
    for name in names:
        if name == fallback:
            continue
        improvements = tuple(row[fallback] - row[name] for row in prior_rows)
        shrunk = sum(improvements) / (len(improvements) + prior_strength)
        conservative = (
            shrunk
            - uncertainty_multiplier * _sample_standard_error(improvements)
        )
        if conservative > 0:
            qualified.append((conservative, shrunk, name))
    if not qualified:
        return fallback
    return min(
        qualified,
        key=lambda item: (-item[0], -item[1], item[2]),
    )[2]


def _choose_ewma_guard(
    names: Sequence[str],
    prior_rows: Sequence[Mapping[str, float]],
    *,
    fallback: str,
    half_life: float,
) -> str:
    newest = len(prior_rows) - 1
    weights = tuple(
        0.5 ** ((newest - index) / half_life)
        for index in range(len(prior_rows))
    )
    means = {
        name: sum(
            row[name] * weight
            for row, weight in zip(prior_rows, weights, strict=True)
        )
        / sum(weights)
        for name in names
    }
    candidate = min(names, key=lambda name: (means[name], name))
    if candidate == fallback:
        return fallback
    return _choose_safe(
        (fallback, candidate),
        prior_rows,
        fallback=fallback,
    )


def _choose_grid_one_se(
    names: Sequence[str],
    prior_rows: Sequence[Mapping[str, float]],
) -> str:
    means = {
        name: sum(row[name] for row in prior_rows) / len(prior_rows)
        for name in names
    }
    best = min(names, key=lambda name: (means[name], name))
    limit = means[best] + _sample_standard_error(
        tuple(row[best] for row in prior_rows)
    )
    eligible = tuple(name for name in names if means[name] <= limit)
    return min(
        eligible,
        key=lambda name: (
            _mixture_distance_from_equal(name),
            means[name],
            name,
        ),
    )


def _mixture_distance_from_equal(name: str) -> float:
    units = {
        part[0]: int(part[1:])
        for part in name.split("_")
        if part and part[0] in {"c", "r", "t"} and part[1:].isdigit()
    }
    if set(units) != {"c", "r", "t"}:
        raise ValueError("mixture Selector name does not encode its grid point")
    return sum((units[key] / 3 - 1 / 3) ** 2 for key in ("c", "r", "t"))


def composition_analysis(
    design: DiagnosticDesign,
    outcomes: Outcomes,
) -> Mapping[str, object]:
    rows = []
    selected_tv_by_selector: dict[str, list[float]] = {
        name: [] for name in PRIMARY_SELECTOR_NAMES
    }
    for origin in design.origins:
        future_proportions = _proportions(
            task.sampling_stratum for task in origin.future
        )
        row: dict[str, object] = {"origin_number": origin.origin_number}
        task_by_id = {task.task_id: task for task in origin.history}
        for name in PRIMARY_SELECTOR_NAMES:
            selection = origin.selections[name]
            selected_proportions = _proportions(
                task_by_id[task_id].sampling_stratum
                for task_id in selection.task_ids
            )
            selected_tv_by_selector[name].append(
                _tv(selected_proportions, future_proportions)
            )
        for name in ("stratified_unweighted", "stratified_weighted"):
            selection = origin.selections[name]
            selected = _proportions(
                task_by_id[task_id].sampling_stratum
                for task_id in selection.task_ids
            )
            weighted: dict[str, float] = {}
            for task_id in selection.task_ids:
                stratum = task_by_id[task_id].sampling_stratum
                weighted[stratum] = (
                    weighted.get(stratum, 0.0) + selection.weights[task_id]
                )
            total = sum(weighted.values())
            weighted_proportions = {
                key: value / total for key, value in weighted.items()
            }
            forecast = cast(
                Mapping[str, float],
                selection.diagnostics["forecast_proportions"],
            )
            row[name] = {
                "forecast_future_tv": _tv(forecast, future_proportions),
                "selected_future_tv": _tv(selected, future_proportions),
                "weighted_future_tv": _tv(
                    weighted_proportions,
                    future_proportions,
                ),
                "maximum_selected_weight": selection.diagnostics[
                    "maximum_selected_weight"
                ],
                "effective_sample_size": selection.diagnostics[
                    "effective_sample_size"
                ],
                "capped_selected_fraction": selection.diagnostics[
                    "capped_selected_fraction"
                ],
            }
        rows.append(row)
    weighted_rows = [
        cast(Mapping[str, float], row["stratified_weighted"])
        for row in rows
    ]
    all_tasks = {
        task.task_id: task
        for origin in design.origins
        for task in (*origin.history, *origin.future)
    }
    strata = tuple(
        sorted({task.sampling_stratum for task in all_tasks.values()})
    )
    return {
        "origins": tuple(rows),
        "mean_unweighted_selected_future_tv_by_selector": {
            name: sum(values) / len(values)
            for name, values in selected_tv_by_selector.items()
        },
        "source_strata": {
            stratum: {
                "task_count": sum(
                    task.sampling_stratum == stratum
                    for task in all_tasks.values()
                ),
                "pass_rate_by_agent": {
                    agent: sum(
                        agent_outcomes[task.task_id]
                        for task in all_tasks.values()
                        if task.sampling_stratum == stratum
                    )
                    / sum(
                        task.sampling_stratum == stratum
                        for task in all_tasks.values()
                    )
                    for agent, agent_outcomes in outcomes.base.items()
                },
            }
            for stratum in strata
        },
        "weighted_means": {
            key: sum(row[key] for row in weighted_rows) / len(weighted_rows)
            for key in (
                "forecast_future_tv",
                "selected_future_tv",
                "weighted_future_tv",
                "maximum_selected_weight",
                "effective_sample_size",
                "capped_selected_fraction",
            )
        },
        "mechanism_check": (
            "Composition fidelity and outcome MAE diverge: compare the TV table "
            "with fixed_selectors. The stratum forecast is not validated as the "
            "mechanism behind lower future-pass-rate error."
        ),
    }


def sensitivity_analysis(
    metadata: Metadata,
    design: DiagnosticDesign,
    outcomes: Outcomes,
    plan: Mapping[str, Any],
) -> Mapping[str, object]:
    sensitivity = _mapping(plan, "sensitivity_analyses")
    random_names = tuple(
        f"random_seed_{seed}"
        for seed in _integer_sequence(sensitivity, "random_seed_bank")
    )
    stratified_names = tuple(
        f"stratified_weighted_seed_{seed}"
        for seed in _integer_sequence(sensitivity, "stratified_seed_bank")
    )
    grid_names = tuple(
        name
        for name in design.specs
        if name.startswith("stratified_grid_")
    )
    random_macros = _macro_by_selector(design, outcomes.base, random_names)
    stratified_macros = _macro_by_selector(
        design,
        outcomes.base,
        stratified_names,
    )
    grid_macros = _macro_by_selector(design, outcomes.base, grid_names)
    grid_behavior_digests = {
        canonical_digest(
            tuple(
                (
                    origin.selections[name].task_ids,
                    origin.selections[name].weights,
                )
                for origin in design.origins
            )
        )
        for name in grid_names
    }
    mixture = mixture_seed_sensitivity(design, outcomes)
    repeat = repeat_noise_analysis(
        design,
        outcomes,
        resamples=_integer(
            _mapping(sensitivity, "repeat_noise_views"),
            "resamples",
        ),
        seed=_integer(
            _mapping(sensitivity, "repeat_noise_views"),
            "seed",
        ),
    )
    dependency = dependency_sensitivity(metadata, outcomes, design.specs)
    return {
        "random_seed_bank": _seed_bank_summary(random_macros),
        "stratified_seed_bank": _seed_bank_summary(stratified_macros),
        "stratified_parameter_grid": {
            "variant_count": len(grid_macros),
            "unique_realized_behavior_count": len(grid_behavior_digests),
            "minimum_macro_mae": min(grid_macros.values()),
            "maximum_macro_mae": max(grid_macros.values()),
            "population_stddev": pstdev(grid_macros.values()),
            "primary_weighted_macro_mae": _macro_by_selector(
                design,
                outcomes.base,
                ("stratified_weighted",),
            )["stratified_weighted"],
            "interpretation": "exploratory_only_no_default_selected",
        },
        "repeat_noise": repeat,
        "dependency_first_task_per_cluster": dependency,
        "block_size": block_size_sensitivity(
            metadata,
            outcomes,
            design.specs,
        ),
        "rank_mixture_seed_bank": mixture,
    }


def _macro_by_selector(
    design: DiagnosticDesign,
    outcomes: Mapping[str, Mapping[str, int]],
    names: Sequence[str],
) -> Mapping[str, float]:
    rows = loss_rows(design, outcomes, names)
    return {
        name: sum(row[name] for row in rows) / len(rows)
        for name in names
    }


def _seed_bank_summary(values: Mapping[str, float]) -> Mapping[str, object]:
    ordered = tuple(values[name] for name in sorted(values))
    return {
        "variant_count": len(values),
        "macro_mae_by_selector": dict(sorted(values.items())),
        "mean_macro_mae": sum(ordered) / len(ordered),
        "population_stddev": pstdev(ordered),
        "minimum_macro_mae": min(ordered),
        "maximum_macro_mae": max(ordered),
    }


def mixture_seed_sensitivity(
    design: DiagnosticDesign,
    outcomes: Outcomes,
) -> Mapping[str, object]:
    candidate_rows = loss_rows(
        design,
        outcomes.base,
        ADAPTIVE_CANDIDATE_NAMES,
    )
    rows: dict[str, object] = {}
    for seed in (5, 17, 29):
        names = tuple(
            name
            for name in design.specs
            if name.startswith(f"mixture_s{seed}_")
        )
        losses = loss_rows(design, outcomes.base, names)
        macro = {
            name: sum(row[name] for row in losses) / len(losses)
            for name in names
        }
        outer_losses = []
        coverage_losses = []
        choices = []
        for outer_index in range(4, len(losses)):
            chosen = _choose_grid_one_se(names, losses[:outer_index])
            choices.append(chosen)
            outer_losses.append(losses[outer_index][chosen])
            coverage_losses.append(candidate_rows[outer_index]["coverage"])
        rows[str(seed)] = {
            "minimum_fixed_macro_mae": min(macro.values()),
            "maximum_fixed_macro_mae": max(macro.values()),
            "equal_weight_macro_mae": macro[
                f"mixture_s{seed}_c1_r1_t1"
            ],
            "one_se_outer_macro_mae": sum(outer_losses) / len(outer_losses),
            "one_se_difference_from_coverage": sum(
                value - fallback
                for value, fallback in zip(
                    outer_losses,
                    coverage_losses,
                    strict=True,
                )
            )
            / len(outer_losses),
            "one_se_choice_counts": dict(sorted(Counter(choices).items())),
        }
    differences = tuple(
        cast(float, cast(Mapping[str, object], row)["one_se_difference_from_coverage"])
        for row in rows.values()
    )
    return {
        "seeds": rows,
        "one_se_difference_range": {
            "minimum": min(differences),
            "maximum": max(differences),
        },
        "decision": "seed_instability_dominates_any_observed_gain",
    }


def block_size_sensitivity(
    metadata: Metadata,
    outcomes: Outcomes,
    specs: Mapping[str, SelectorSpec],
) -> Mapping[str, object]:
    configurations = ((3, 15), (4, 15), (5, 15), (6, 15), (8, 11))
    rows: dict[str, object] = {}
    for block_size, initial in configurations:
        blocks = chronological_blocks(
            metadata.ordered_tasks,
            initial_history_count=initial,
            future_block_count=block_size,
        )
        origins = tuple(
            DiagnosticOrigin(
                index,
                history,
                future,
                {
                    name: select_tasks(specs[name], history, 10)
                    for name in ADAPTIVE_CANDIDATE_NAMES
                },
            )
            for index, (history, future) in enumerate(blocks, start=1)
        )
        diagnostic = DiagnosticDesign(
            origins,
            specs,
            canonical_digest((block_size, initial)),
        )
        losses = loss_rows(
            diagnostic,
            outcomes.base,
            ADAPTIVE_CANDIDATE_NAMES,
        )
        rows[str(block_size)] = {
            "initial_history_task_count": initial,
            "origin_count": len(origins),
            "coverage_minus_random_seed_5": sum(
                row["coverage"] - row["random_seed_5"] for row in losses
            )
            / len(losses),
            "coverage_minus_recency": sum(
                row["coverage"] - row["recency"] for row in losses
            )
            / len(losses),
            "coverage_minus_stratified_weighted": sum(
                row["coverage"] - row["stratified_weighted"]
                for row in losses
            )
            / len(losses),
        }
    return {
        "status": "post_primary_adversarial_diagnostic",
        "configurations": rows,
        "interpretation": (
            "Coverage beats random seed 5 and weighted stratification at every "
            "listed block size; its comparison with recency changes sign once."
        ),
    }


def repeat_noise_analysis(
    design: DiagnosticDesign,
    outcomes: Outcomes,
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, object]:
    rng = random.Random(seed)
    primary_differences: list[float] = []
    adaptive_differences: list[float] = []
    coverage_random_differences: list[float] = []
    coverage_random_bank_differences: list[float] = []
    coverage_recency_differences: list[float] = []
    random_bank_names = tuple(
        sorted(
            (
                name
                for name in design.specs
                if name.startswith("random_seed_")
            ),
            key=lambda name: int(name.removeprefix("random_seed_")),
        )
    )
    evaluated_names = tuple(
        dict.fromkeys((*ADAPTIVE_CANDIDATE_NAMES, *random_bank_names))
    )
    repeated_task_count = sum(
        len(values) > 1
        for values in next(iter(outcomes.scoreable_replicates.values())).values()
    )
    for _ in range(resamples):
        view = {
            agent: {
                task_id: (
                    rng.choice(replicates)
                    if len(replicates) > 1
                    else outcomes.base[agent][task_id]
                )
                for task_id, replicates in tasks.items()
            }
            for agent, tasks in outcomes.scoreable_replicates.items()
        }
        rows = loss_rows(design, view, evaluated_names)
        primary_differences.append(
            sum(
                row["stratified_weighted"] - row["coverage"]
                for row in rows
            )
            / len(rows)
        )
        coverage_random_differences.append(
            sum(row["coverage"] - row["random_seed_5"] for row in rows)
            / len(rows)
        )
        coverage_random_bank_differences.append(
            sum(
                row["coverage"]
                - sum(row[name] for name in random_bank_names)
                / len(random_bank_names)
                for row in rows
            )
            / len(rows)
        )
        coverage_recency_differences.append(
            sum(row["coverage"] - row["recency"] for row in rows)
            / len(rows)
        )
        safe_losses = []
        fallback_losses = []
        for outer_index in range(4, len(rows)):
            chosen = _choose_safe(
                ADAPTIVE_CANDIDATE_NAMES,
                rows[:outer_index],
                fallback="coverage",
            )
            safe_losses.append(rows[outer_index][chosen])
            fallback_losses.append(rows[outer_index]["coverage"])
        adaptive_differences.append(
            sum(
                value - fallback
                for value, fallback in zip(
                    safe_losses,
                    fallback_losses,
                    strict=True,
                )
            )
            / len(safe_losses)
        )
    return {
        "resamples": resamples,
        "seed": seed,
        "replicated_task_count": repeated_task_count,
        "primary_difference": _resample_summary(primary_differences),
        "coverage_minus_random_seed_5": _resample_summary(
            coverage_random_differences
        ),
        "coverage_minus_random_seed_bank_mean": _resample_summary(
            coverage_random_bank_differences
        ),
        "coverage_minus_recency": _resample_summary(
            coverage_recency_differences
        ),
        "ALG-001_difference_from_coverage": _resample_summary(
            adaptive_differences
        ),
        "interpretation": (
            "conditional sensitivity over the preselected repeat subset, "
            "not an independent sampling interval"
        ),
    }


def _resample_summary(values: Sequence[float]) -> Mapping[str, float]:
    ordered = sorted(values)
    return {
        "mean": sum(values) / len(values),
        "lower_2_5_percentile": _percentile(ordered, 0.025),
        "median": _percentile(ordered, 0.5),
        "upper_97_5_percentile": _percentile(ordered, 0.975),
        "fraction_below_zero": sum(value < 0 for value in values) / len(values),
        "fraction_at_most_minus_0_02": sum(value <= -0.02 for value in values)
        / len(values),
    }


def dependency_sensitivity(
    metadata: Metadata,
    outcomes: Outcomes,
    specs: Mapping[str, SelectorSpec],
) -> Mapping[str, object]:
    first_by_cluster: dict[str, TaskRecord] = {}
    for task in metadata.ordered_tasks:
        first_by_cluster.setdefault(task.dependency_cluster_id, task)
    tasks = tuple(first_by_cluster.values())
    blocks = chronological_blocks(
        tasks,
        initial_history_count=14,
        future_block_count=5,
    )
    origins = tuple(
        DiagnosticOrigin(
            index,
            history,
            future,
            {
                name: select_tasks(specs[name], history, 10)
                for name in PRIMARY_SELECTOR_NAMES
            },
        )
        for index, (history, future) in enumerate(blocks, start=1)
    )
    design = DiagnosticDesign(origins, specs, canonical_digest(tuple(tasks)))
    rows = loss_rows(design, outcomes.base, PRIMARY_SELECTOR_NAMES)
    differences = tuple(
        row["stratified_weighted"] - row["coverage"] for row in rows
    )
    return {
        "task_count": len(tasks),
        "origin_count": len(origins),
        "cluster_recurrence": 0,
        "primary_contrast": _difference_summary(differences),
        "macro_mae_by_selector": {
            name: sum(row[name] for row in rows) / len(rows)
            for name in PRIMARY_SELECTOR_NAMES
        },
    }


def headroom_analysis(
    design: DiagnosticDesign,
    outcomes: Outcomes,
) -> Mapping[str, object]:
    all_history_losses = []
    registered_oracle_losses = []
    subset_oracle_losses = []
    for origin in design.origins:
        all_history = DiagnosticSelection(
            "all_history",
            tuple(task.task_id for task in origin.history),
            {task.task_id: 1.0 for task in origin.history},
            {},
        )
        all_history_losses.append(
            diagnostic_mae(all_history, origin.future, outcomes.base)
        )
        registered_oracle_losses.append(
            min(
                diagnostic_mae(
                    origin.selections[name],
                    origin.future,
                    outcomes.base,
                )
                for name in PRIMARY_SELECTOR_NAMES
            )
        )
        subset_oracle_losses.append(
            _outcome_subset_oracle(origin, outcomes.base, budget=10)
        )
    return {
        "all_history_no_budget_baseline": _loss_summary(
            tuple(all_history_losses)
        ),
        "hindsight_registered_selector_oracle": _loss_summary(
            tuple(registered_oracle_losses)
        ),
        "hindsight_outcome_subset_oracle": _loss_summary(
            tuple(subset_oracle_losses)
        ),
        "interpretation": "Both oracle rows use future outcomes and are not deployable.",
    }


def _outcome_subset_oracle(
    origin: DiagnosticOrigin,
    outcomes: Mapping[str, Mapping[str, int]],
    *,
    budget: int,
) -> float:
    agents = tuple(outcomes)
    if len(agents) != 2:
        raise ValueError("joint outcome oracle requires exactly two Agents")
    counts = Counter(
        (
            outcomes[agents[0]][task.task_id],
            outcomes[agents[1]][task.task_id],
        )
        for task in origin.history
    )
    future_rates = tuple(
        sum(outcomes[agent][task.task_id] for task in origin.future)
        / len(origin.future)
        for agent in agents
    )
    best = math.inf
    categories = ((0, 0), (0, 1), (1, 0), (1, 1))
    for first in range(min(counts[categories[0]], budget) + 1):
        for second in range(min(counts[categories[1]], budget - first) + 1):
            for third in range(
                min(counts[categories[2]], budget - first - second) + 1
            ):
                fourth = budget - first - second - third
                if fourth < 0 or fourth > counts[categories[3]]:
                    continue
                selected_rates = (
                    (third + fourth) / budget,
                    (second + fourth) / budget,
                )
                loss = sum(
                    abs(selected - future)
                    for selected, future in zip(
                        selected_rates,
                        future_rates,
                        strict=True,
                    )
                ) / 2
                best = min(best, loss)
    if not math.isfinite(best):
        raise ValueError("outcome oracle could not form a budgeted subset")
    return best


def power_and_budget_analysis(
    fixed: Mapping[str, object],
    model_study_results_path: Path,
    design: DiagnosticDesign,
) -> Mapping[str, object]:
    contrast = cast(Mapping[str, object], fixed["primary_contrast"])
    differences = tuple(cast(Sequence[float], contrast["origin_differences"]))
    observed = sum(differences) / len(differences)
    standard_deviation = _sample_standard_deviation(differences)
    target_half_width = 0.02
    half_width_origins = math.ceil(
        (NormalDist().inv_cdf(0.975) * standard_deviation / target_half_width)
        ** 2
    )
    power_origins = (
        _normal_power_origin_count(standard_deviation, abs(observed))
        if observed < 0 and not math.isclose(observed, 0.0)
        else None
    )
    empirical_power_origins = (
        _empirical_power_origin_count(differences)
        if observed < 0
        else None
    )
    exploratory = cast(
        Mapping[str, Mapping[str, object]],
        fixed["exploratory_coverage_contrasts"],
    )
    candidate_power = {
        name: _contrast_power(
            tuple(cast(Sequence[float], contrast["origin_differences"]))
        )
        for name, contrast in exploratory.items()
    }
    random_bank_contrast = cast(
        Mapping[str, object],
        fixed["coverage_minus_random_seed_bank_mean"],
    )
    candidate_power["random_seed_bank_mean"] = _contrast_power(
        tuple(cast(Sequence[float], random_bank_contrast["origin_differences"]))
    )
    model_results = _load_json(model_study_results_path)
    operations = cast(Sequence[Mapping[str, object]], model_results["operations"])
    median_per_task = sum(
        _number(
            cast(Mapping[str, object], operation["per_call_exact_cost_usd"]),
            "median",
        )
        for operation in operations
    )
    p90_per_task = sum(
        _number(
            cast(Mapping[str, object], operation["per_call_exact_cost_usd"]),
            "p90_nearest_rank",
        )
        for operation in operations
    )
    coverage_random = cast(
        Mapping[str, object],
        candidate_power["random_seed_bank_mean"],
    )
    candidate_counts = tuple(
        value
        for key in (
            "normal_approx_origins_for_80_percent_power",
            "empirical_resampling_origins_for_80_percent_power",
        )
        if isinstance((value := coverage_random[key]), int)
    )
    projected_origins = max(candidate_counts) if candidate_counts else half_width_origins
    random_names = tuple(
        name
        for name in design.specs
        if name.startswith("random_seed_")
    )
    initial_origin = design.origins[0]
    initial_task_count = len(
        set(initial_origin.selections["coverage"].task_ids).union(
            *(
                set(initial_origin.selections[name].task_ids)
                for name in random_names
            )
        )
    )
    return {
        "observed_primary_difference": observed,
        "sample_standard_deviation": standard_deviation,
        "target_mae_half_width": target_half_width,
        "normal_approx_origins_for_target_half_width": half_width_origins,
        "normal_approx_origins_for_80_percent_power_at_observed_effect": (
            power_origins
        ),
        "empirical_resampling_origins_for_80_percent_power": (
            empirical_power_origins
        ),
        "exploratory_coverage_candidate_contrasts": candidate_power,
        "future_nomination": (
            "Preregister coverage versus a random seed bank in new mature "
            "Origins. This nomination is post-primary and not confirmatory "
            "evidence from the current data."
        ),
        "cost_projection": {
            "assumptions": (
                "two frozen Agents; initial union of coverage plus five random "
                "Selections; five new future Tasks per Origin; prior Results cached"
            ),
            "initial_unique_task_count": initial_task_count,
            "initial_panel_median_usd": initial_task_count * median_per_task,
            "initial_panel_p90_usd": initial_task_count * p90_per_task,
            "one_five_task_origin_median_usd": 5 * median_per_task,
            "one_five_task_origin_p90_usd": 5 * p90_per_task,
            "projected_origin_count": projected_origins,
            "projected_contrast": "coverage_minus_random_seed_bank_mean",
            "projected_total_median_usd": (
                (initial_task_count + 5 * projected_origins) * median_per_task
            ),
            "projected_total_p90_usd": (
                (initial_task_count + 5 * projected_origins) * p90_per_task
            ),
            "basis": "existing exact attributed per-call median and p90; not a quote",
        },
    }


def _contrast_power(differences: tuple[float, ...]) -> Mapping[str, object]:
    observed = sum(differences) / len(differences)
    standard_deviation = _sample_standard_deviation(differences)
    return {
        "observed_macro_difference": observed,
        "sample_standard_deviation": standard_deviation,
        "origin_block_interval_95": _bootstrap_interval(differences),
        "normal_approx_origins_for_80_percent_power": (
            _normal_power_origin_count(standard_deviation, abs(observed))
            if observed < 0 and not math.isclose(observed, 0.0)
            else None
        ),
        "empirical_resampling_origins_for_80_percent_power": (
            _empirical_power_origin_count(differences)
            if observed < 0
            else None
        ),
    }


def _normal_power_origin_count(standard_deviation: float, effect: float) -> int:
    if standard_deviation == 0:
        return 1
    z_alpha = NormalDist().inv_cdf(0.975)
    z_power = NormalDist().inv_cdf(0.8)
    return math.ceil(((z_alpha + z_power) * standard_deviation / effect) ** 2)


def _empirical_power_origin_count(differences: Sequence[float]) -> int | None:
    rng = random.Random(20_260_727)
    for count in range(8, 201):
        successes = 0
        for _ in range(2_000):
            sample = tuple(rng.choice(differences) for _ in range(count))
            mean = sum(sample) / count
            standard_error = _sample_standard_deviation(sample) / math.sqrt(count)
            successes += mean + 1.96 * standard_error < 0
        if successes / 2_000 >= 0.8:
            return count
    return None


def audit_diagnostic(
    metadata: Metadata,
    design: DiagnosticDesign,
    outcomes: Outcomes,
    maturity: Mapping[str, object],
    fixed: Mapping[str, object],
) -> Mapping[str, object]:
    future_ids = [
        task.task_id
        for origin in design.origins
        for task in origin.future
    ]
    independent_checks = 0
    for origin in design.origins:
        history_ids = {task.task_id for task in origin.history}
        for selection in origin.selections.values():
            if not set(selection.task_ids) <= history_ids:
                raise ValueError("diagnostic Selection leaks future Tasks")
            direct = diagnostic_mae(selection, origin.future, outcomes.base)
            independent = independent_diagnostic_mae(
                selection,
                origin.future,
                outcomes.base,
            )
            if not math.isclose(direct, independent, abs_tol=1e-15):
                raise ValueError("independent metric recalculation disagrees")
            independent_checks += 1
    times = tuple(
        task.task_material_available_at for task in metadata.ordered_tasks
    )
    future_blocks_by_cluster: dict[str, set[int]] = {}
    future_tasks_with_cluster_in_history = 0
    for origin in design.origins:
        history_clusters = {
            task.dependency_cluster_id for task in origin.history
        }
        for task in origin.future:
            future_blocks_by_cluster.setdefault(
                task.dependency_cluster_id,
                set(),
            ).add(origin.origin_number)
            future_tasks_with_cluster_in_history += (
                task.dependency_cluster_id in history_clusters
            )
    contrast = cast(Mapping[str, object], fixed["primary_contrast"])
    return {
        "source_record_validation": "passed",
        "source_sha256_bindings": "passed",
        "selection_frozen_before_outcome_load": True,
        "task_time_count": len(times),
        "distinct_task_time_count": len(set(times)),
        "future_task_count": len(future_ids),
        "future_task_ids_unique": len(future_ids) == len(set(future_ids)),
        "dependency": {
            "future_distinct_cluster_count": len(future_blocks_by_cluster),
            "clusters_spanning_multiple_future_blocks": sum(
                len(blocks) > 1
                for blocks in future_blocks_by_cluster.values()
            ),
            "maximum_future_blocks_per_cluster": max(
                len(blocks)
                for blocks in future_blocks_by_cluster.values()
            ),
            "future_tasks_with_cluster_already_in_history": (
                future_tasks_with_cluster_in_history
            ),
            "origin_bootstrap_limitation": (
                "Primary Origin blocks are disjoint in Tasks but not independent "
                "in dependency clusters; use the first-task-per-cluster "
                "sensitivity as the adversarial check."
            ),
        },
        "selection_history_membership": "passed",
        "independent_metric_recalculation": {
            "status": "passed",
            "cell_count": independent_checks,
        },
        "bootstrap_protocol": {
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
        },
        "primary_origin_difference_digest": canonical_digest(
            contrast["origin_differences"]
        ),
        "core_maturity_failure_retained": (
            maturity["status"] == "planned_core_evidence_path_invalid"
        ),
        "per_task_outcomes_persisted": False,
        "raw_prompts_or_completions_read": False,
        "new_paid_calls": 0,
        "network_calls": 0,
    }


def _diagnostic_status(fixed: Mapping[str, object]) -> str:
    contrast = cast(Mapping[str, object], fixed["primary_contrast"])
    mean = cast(float, contrast["macro_origin_mae_difference"])
    interval = cast(Mapping[str, object], contrast["origin_block_interval_95"])
    if mean <= -0.02 and cast(float, interval["upper"]) < 0:
        return "historical_order_signal_present"
    if mean < 0:
        return "historical_order_signal_inconclusive"
    return "historical_order_signal_absent"


def _loss_summary(values: tuple[float, ...]) -> Mapping[str, object]:
    return {
        "macro_origin_mae": sum(values) / len(values),
        "origin_block_interval_95": _bootstrap_interval(values),
    }


def _difference_summary(values: tuple[float, ...]) -> Mapping[str, object]:
    return {
        "macro_origin_mae_difference": sum(values) / len(values),
        "origin_block_interval_95": _bootstrap_interval(values),
        "origins_favoring_selector_a": sum(value < 0 for value in values),
        "origins_tied": sum(math.isclose(value, 0.0) for value in values),
        "origins_favoring_selector_b": sum(value > 0 for value in values),
        "origin_differences": values,
    }


def _bootstrap_interval(values: Sequence[float]) -> Mapping[str, object]:
    if len(values) < 8:
        return {
            "status": "insufficient_origin_blocks",
            "block_count": len(values),
            "lower": None,
            "upper": None,
        }
    rng = random.Random(BOOTSTRAP_SEED)
    sampled = sorted(
        sum(rng.choice(values) for _ in values) / len(values)
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return {
        "status": "available",
        "block_count": len(values),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "lower": _percentile(sampled, 0.025),
        "upper": _percentile(sampled, 0.975),
    }


def _sample_standard_error(values: Sequence[float]) -> float:
    return _sample_standard_deviation(values) / math.sqrt(len(values))


def _sample_standard_deviation(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise ValueError("sample deviation requires at least two values")
    mean = sum(values) / len(values)
    return math.sqrt(
        sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    )


def _percentile(values: Sequence[float], quantile: float) -> float:
    position = (len(values) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


def _proportions(values: Sequence[str] | Any) -> Mapping[str, float]:
    sequence = tuple(values)
    counts = Counter(sequence)
    return {
        key: count / len(sequence)
        for key, count in sorted(counts.items())
    }


def _tv(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    return 0.5 * sum(
        abs(left.get(key, 0.0) - right.get(key, 0.0))
        for key in set(left) | set(right)
    )


def _load_self_digested_json(
    path: Path,
    *,
    digest_field: str,
    expected_schema: str,
) -> Mapping[str, Any]:
    value = _load_json(path)
    digest = _string(value, digest_field)
    payload = dict(value)
    payload.pop(digest_field)
    if canonical_digest(payload) != digest:
        raise ValueError(f"{path.name} digest does not match")
    if value.get("schema_version") != expected_schema:
        raise ValueError(f"{path.name} schema is unsupported")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _require_sha256(path: Path, expected: str) -> None:
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        raise ValueError(f"source digest mismatch: {path}")


def _mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return cast(Mapping[str, Any], item)


def _string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _integer(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _number(value: Mapping[str, Any], key: str) -> float:
    return _finite_number(value.get(key), key)


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be a finite number")
    return normalized


def _integer_sequence(value: Mapping[str, Any], key: str) -> tuple[int, ...]:
    items = value.get(key)
    if not isinstance(items, list) or any(
        isinstance(item, bool) or not isinstance(item, int) for item in items
    ):
        raise ValueError(f"{key} must be an integer array")
    return tuple(cast(list[int], items))


def _number_sequence(
    value: Mapping[str, Any],
    key: str,
    *,
    allow_none: bool,
) -> tuple[float | None, ...]:
    items = value.get(key)
    if not isinstance(items, list):
        raise ValueError(f"{key} must be a number array")
    normalized: list[float | None] = []
    for item in items:
        if item is None and allow_none:
            normalized.append(None)
        else:
            normalized.append(_finite_number(item, key))
    return tuple(normalized)


def _slug(value: object) -> str:
    if value is None:
        return "none"
    return str(value).replace(".", "p")


def write_results(path: Path, results: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{canonical_json(results)}\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--amendment", type=Path, default=DEFAULT_AMENDMENT)
    parser.add_argument("--correction", type=Path, default=DEFAULT_CORRECTION)
    parser.add_argument("--task-pool", type=Path, default=DEFAULT_TASK_POOL)
    parser.add_argument("--main-records", type=Path, default=DEFAULT_MAIN_RECORDS)
    parser.add_argument(
        "--model-study-results",
        type=Path,
        default=DEFAULT_MODEL_STUDY_RESULTS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS)
    return parser


def main() -> int:
    args = _parser().parse_args()
    paths = StudyPaths(
        plan=args.plan,
        amendment=args.amendment,
        correction=args.correction,
        task_pool=args.task_pool,
        main_records=args.main_records,
        model_study_results=args.model_study_results,
        output=args.output,
    )
    results = run_study(paths)
    write_results(paths.output, results)
    print(canonical_json(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
