"""Selector input construction and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    FeatureSnapshotRecord,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    make_selector_input_id,
    record_with_digest,
    task_check_ref_key,
    validate_selector_input,
)
from barcarolle.task_pool import TimeRange

from .features import (
    LeakagePolicy,
    _ensure_feature_records_match_origin,
    _ensure_result_identity_matches_agents,
    _ensure_result_identity_matches_current_records,
    _ensure_result_records_valid,
    _ensure_results_allowed,
    lint_feature_snapshot,
)
from .origin import RollingOriginPolicy, _apply_embargo, _instant_gt, _task_check_known_at, _time_range_contains, _training_history_refs


@dataclass(frozen=True)
class SelectionBudget:
    budget_digest: str
    max_task_checks: int


def build_selector_input(
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    feature_snapshot: FeatureSnapshotRecord,
    pre_origin_results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    budget: SelectionBudget,
    leakage_policy: LeakagePolicy,
) -> SelectorInput:
    if origin.task_pool_id != task_pool.task_pool_id or origin.task_pool_digest != task_pool.task_pool_digest:
        raise ValueError("origin does not match task_pool")
    if feature_snapshot.origin_id != origin.origin_id:
        raise ValueError("feature snapshot origin_id does not match origin")
    _ensure_results_allowed(pre_origin_results, origin, task_pool, agents, expected_result_view_digest=feature_snapshot.result_view_digest)
    _ensure_feature_records_match_origin(feature_snapshot, origin, pre_origin_results)
    lint = lint_feature_snapshot(feature_snapshot, leakage_policy)
    if not lint.ok:
        raise ValueError(f"feature snapshot failed leakage lint: {', '.join(lint.errors)}")
    selector_input = SelectorInput(
        selector_input_id="",
        origin_id=origin.origin_id,
        task_pool_id=task_pool.task_pool_id,
        feature_snapshot_id=feature_snapshot.feature_snapshot_id,
        agent_ids=tuple(agent.agent_id for agent in agents),
        eligible_task_check_refs=origin.history_task_check_refs,
        pre_origin_result_ids=tuple(result.result_id for result in pre_origin_results),
        pre_origin_result_digests=tuple(result.result_digest for result in pre_origin_results),
        budget_digest=budget.budget_digest,
        leakage_policy_digest=leakage_policy.leakage_policy_digest,
        selector_input_digest="",
        task_pool_digest=task_pool.task_pool_digest,
        selection_budget_limit=budget.max_task_checks,
        feature_records_digest=feature_snapshot.feature_records_digest,
        feature_snapshot_lint_status="passed",
        origin_as_of_cutoff=origin.as_of_cutoff,
        origin_history_refs_digest=canonical_digest(origin.history_task_check_refs),
    )
    selector_input = replace(selector_input, selector_input_id=make_selector_input_id(selector_input))
    selector_input = record_with_digest(selector_input)
    validation = validate_selector_input(selector_input)
    if not validation.ok:
        raise ValueError(f"selector input is invalid: {', '.join(validation.errors)}")
    return selector_input


def _ensure_selector_input_valid(selector_input: SelectorInput) -> None:
    validation = validate_selector_input(selector_input)
    if not validation.ok:
        raise ValueError(f"selector input is invalid: {', '.join(validation.errors)}")
    if len(set(selector_input.agent_ids)) != len(selector_input.agent_ids):
        raise ValueError("selector input agent_ids must be unique")
    ref_keys = tuple(task_check_ref_key(ref) for ref in selector_input.eligible_task_check_refs)
    if len(set(ref_keys)) != len(ref_keys):
        raise ValueError("selector input eligible_task_check_refs must be unique")


def _ensure_selector_input_matches_history(
    selector_input: SelectorInput,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    rolling_policy: RollingOriginPolicy,
) -> None:
    _ensure_selector_input_valid(selector_input)
    if selector_input.task_pool_id != task_pool.task_pool_id or selector_input.task_pool_digest != task_pool.task_pool_digest:
        raise ValueError("selector input task pool binding does not match task_pool")
    if set(selector_input.agent_ids) != {agent.agent_id for agent in agents}:
        raise ValueError("selector input Agent set does not match candidate Agents")
    task_by_id = {task.task_id: task for task in tasks}
    if selector_input.origin_as_of_cutoff is None:
        raise ValueError("selector input origin cutoff is required")
    if not _time_range_contains(history_window, selector_input.origin_as_of_cutoff):
        raise ValueError("selector input origin cutoff is outside history window")
    origin_history_window = TimeRange(history_window.start, selector_input.origin_as_of_cutoff)
    history_cutoff = _apply_embargo(selector_input.origin_as_of_cutoff, rolling_policy.embargo)
    for ref in selector_input.eligible_task_check_refs:
        if ref.task_id not in task_pool.task_ids or ref.check_id not in task_pool.check_ids:
            raise ValueError("selector input includes refs outside task_pool")
        task = task_by_id.get(ref.task_id)
        check = checks.get(ref.check_id)
        if task is None or check is None or check.task_id != task.task_id or ref.check_id not in task.check_ids:
            raise ValueError("selector input includes refs missing from Task/Check records")
        if rolling_policy.allowed_cluster_ids and task.cluster_id not in rolling_policy.allowed_cluster_ids:
            raise ValueError("selector input includes refs outside cluster constraints")
        known_at = _task_check_known_at(task, check)
        if not _time_range_contains(origin_history_window, known_at) or _instant_gt(known_at, history_cutoff):
            raise ValueError("selector input includes refs outside history window")


def _validated_training_selector_inputs(
    training_origins: Sequence[RollingOriginRecord],
    training_selector_inputs: Mapping[str, SelectorInput],
) -> tuple[SelectorInput, ...]:
    origin_ids = tuple(origin.origin_id for origin in training_origins)
    if set(training_selector_inputs) != set(origin_ids):
        raise ValueError("training selector input origin keys must match training origins")
    ordered_inputs = []
    for origin in training_origins:
        selector_input = training_selector_inputs[origin.origin_id]
        _ensure_selector_input_valid(selector_input)
        if selector_input.origin_id != origin.origin_id:
            raise ValueError("training selector input origin_id does not match origin")
        if selector_input.task_pool_id != origin.task_pool_id or selector_input.task_pool_digest != origin.task_pool_digest:
            raise ValueError("training selector input task pool binding does not match origin")
        if selector_input.origin_as_of_cutoff != origin.as_of_cutoff:
            raise ValueError("training selector input origin cutoff does not match origin")
        if selector_input.eligible_task_check_refs != origin.history_task_check_refs:
            raise ValueError("training selector input eligible refs do not match origin history")
        ordered_inputs.append(selector_input)
    return tuple(ordered_inputs)


def _ensure_training_results_allowed(
    results: Sequence[ResultRecord],
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    rolling_policy: RollingOriginPolicy,
) -> tuple[TaskCheckRef, ...]:
    _ensure_result_records_valid(results, "training results")
    _ensure_result_identity_matches_current_records(results, tasks, checks, agents)
    history_refs = _training_history_refs(task_pool, tasks, checks, history_window, rolling_policy)
    history_ref_keys = {(ref.task_id, ref.check_id) for ref in history_refs}
    allowed_agents = {agent.agent_id for agent in agents}
    history_cutoff = _apply_embargo(history_window.end, rolling_policy.embargo)
    leaked = [result.result_id for result in results if _instant_gt(result.result_available_at, history_cutoff)]
    if leaked:
        raise ValueError("training results include results after the origin cutoff")
    for result in results:
        if result.task_id not in task_pool.task_ids or result.check_id not in task_pool.check_ids:
            raise ValueError("training results include off-pool results")
        if (result.task_id, result.check_id) not in history_ref_keys:
            raise ValueError("training results include results outside rolling-origin history")
        if result.agent_id not in allowed_agents:
            raise ValueError("training results include results outside candidate Agent set")
    return history_refs
