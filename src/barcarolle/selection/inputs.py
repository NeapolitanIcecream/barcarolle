"""Selector input construction and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from barcarolle.records import (
    AgentRecord,
    FeatureSnapshotRecord,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    TaskPoolRecord,
    agent_record_from_cache_identity,
    canonical_digest,
    make_selector_input_id,
    record_with_digest,
    validate_selector_input,
)
from .features import (
    LeakagePolicy,
    _ensure_feature_records_match_origin,
    _ensure_result_records_valid,
    _ensure_results_allowed,
    _ensure_results_match_origin_scope,
    lint_feature_snapshot,
)


@dataclass(frozen=True)
class SelectionBudget:
    max_task_checks: int

    def __post_init__(self) -> None:
        if type(self.max_task_checks) is not int or self.max_task_checks <= 0:
            raise ValueError("max_task_checks must be a positive integer")

    @property
    def budget_digest(self) -> str:
        return canonical_digest({"max_task_checks": self.max_task_checks})


def build_selector_input(
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    feature_snapshot: FeatureSnapshotRecord,
    pre_origin_results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    budget: SelectionBudget,
    leakage_policy: LeakagePolicy,
) -> SelectorInput:
    if (
        origin.task_pool_id != task_pool.task_pool_id
        or origin.task_pool_digest != task_pool.task_pool_digest
    ):
        raise ValueError("origin does not match task_pool")
    if feature_snapshot.origin_id != origin.origin_id:
        raise ValueError("feature snapshot origin_id does not match origin")
    if feature_snapshot.leakage_lint_status != "passed":
        raise ValueError("feature snapshot must persist a passed leakage lint status")
    _ensure_results_allowed(
        pre_origin_results,
        origin,
        task_pool,
        agents,
    )
    selector_input = SelectorInput(
        selector_input_id="",
        origin_id=origin.origin_id,
        task_pool_id=task_pool.task_pool_id,
        feature_snapshot_id=feature_snapshot.feature_snapshot_id,
        agent_ids=tuple(agent.agent_id for agent in agents),
        agent_record_digests=tuple(canonical_digest(agent) for agent in agents),
        eligible_task_check_refs=origin.history_task_check_refs,
        pre_origin_result_ids=tuple(result.result_id for result in pre_origin_results),
        pre_origin_result_digests=tuple(
            result.result_digest for result in pre_origin_results
        ),
        budget_digest=budget.budget_digest,
        leakage_policy_digest=leakage_policy.leakage_policy_digest,
        selector_input_digest="",
        task_pool_digest=task_pool.task_pool_digest,
        selection_budget_limit=budget.max_task_checks,
        feature_records_digest=feature_snapshot.feature_records_digest,
        feature_snapshot_lint_status="passed",
        origin_as_of_cutoff=origin.as_of_cutoff,
        origin_history_refs_digest=canonical_digest(origin.history_task_check_refs),
        eligibility_mode=origin.eligibility_mode,
    )
    selector_input = replace(
        selector_input, selector_input_id=make_selector_input_id(selector_input)
    )
    selector_input = record_with_digest(selector_input)
    ensure_selector_input_result_evidence(
        selector_input,
        origin,
        feature_snapshot,
        pre_origin_results,
    )
    lint = lint_feature_snapshot(feature_snapshot, leakage_policy)
    if not lint.ok:
        raise ValueError(
            f"feature snapshot failed leakage lint: {', '.join(lint.errors)}"
        )
    return selector_input


def ensure_selector_input_result_evidence(
    selector_input: SelectorInput,
    origin: RollingOriginRecord,
    feature_snapshot: FeatureSnapshotRecord,
    pre_origin_results: Sequence[ResultRecord],
) -> tuple[ResultRecord, ...]:
    """Replay the exact pre-origin Result view frozen by a SelectorInput."""
    _ensure_selector_input_valid(selector_input)
    if selector_input.origin_id != origin.origin_id:
        raise ValueError("selector input does not match its origin")
    if selector_input.eligible_task_check_refs != origin.history_task_check_refs:
        raise ValueError("selector input does not cover its exact origin history")
    if selector_input.origin_as_of_cutoff != origin.as_of_cutoff:
        raise ValueError("selector input cutoff does not match its origin")
    if selector_input.eligibility_mode != origin.eligibility_mode:
        raise ValueError("selector input eligibility mode does not match its origin")

    result_by_id: dict[str, ResultRecord] = {}
    for result in pre_origin_results:
        if result.result_id in result_by_id:
            raise ValueError(f"duplicate pre-origin Result record: {result.result_id}")
        result_by_id[result.result_id] = result
    bindings = tuple(
        zip(
            selector_input.pre_origin_result_ids,
            selector_input.pre_origin_result_digests,
            strict=True,
        )
    )
    if len(set(bindings)) != len(bindings):
        raise ValueError("selector input contains duplicate pre-origin Results")
    resolved_results: list[ResultRecord] = []
    for result_id, result_digest in bindings:
        result = result_by_id.get(result_id)
        if result is None:
            raise ValueError(
                "selector input Result binding is missing from pre_origin_results: "
                + result_id
            )
        if result.result_digest != result_digest:
            raise ValueError(
                "selector input Result digest does not match pre_origin_results: "
                + result_id
            )
        resolved_results.append(result)

    _ensure_result_records_valid(resolved_results, "pre_origin_results")
    _ensure_results_match_origin_scope(
        resolved_results,
        origin,
        allowed_agent_ids=set(selector_input.agent_ids),
    )
    frozen_agent_digests = dict(
        zip(
            selector_input.agent_ids,
            selector_input.agent_record_digests,
            strict=True,
        )
    )
    if any(
        canonical_digest(
            agent_record_from_cache_identity(
                result.agent_id,
                result.cache_identity,
            )
        )
        != frozen_agent_digests[result.agent_id]
        for result in resolved_results
    ):
        raise ValueError(
            "pre_origin_results include cache identity that does not match frozen Agent records"
        )
    _ensure_feature_records_match_origin(
        feature_snapshot,
        origin,
        resolved_results,
    )
    return tuple(resolved_results)


def _ensure_selector_input_valid(selector_input: SelectorInput) -> None:
    validation = validate_selector_input(selector_input)
    if not validation.ok:
        raise ValueError(f"selector input is invalid: {', '.join(validation.errors)}")
