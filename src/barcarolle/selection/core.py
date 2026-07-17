"""High-level Selection orchestration APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    JSONValue,
    ResultRecord,
    SelectorInput,
    SelectorRecord,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    task_check_ref_key,
    validate_selector,
)
from barcarolle.task_pool import TimeRange

from .algorithms import (
    SelectionConfig,
    _selector_record,
    ensure_selector_executable,
    ensure_selector_family_executable,
    select_with_selector,
)
from .features import FeatureConfig, LeakagePolicy, build_feature_snapshot
from .inputs import SelectionBudget, _ensure_selector_input_matches_history, _ensure_training_results_allowed, build_selector_input
from .origin import RollingOriginPolicy, _datetime_to_iso, _ensure_time_range_order, build_rolling_origin


@dataclass(frozen=True)
class SelectorTrainingConfig:
    training_config_digest: str
    selector_family: str = "recency"
    parameters: Mapping[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True)
class SelectorEvaluationConfig:
    origin_times: tuple[str, ...]
    selection_config: SelectionConfig
    budget: SelectionBudget


def train_selector(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    candidate_selectors: Sequence[SelectorRecord],
    training_config: SelectorTrainingConfig,
    rolling_policy: RollingOriginPolicy,
    feature_config: FeatureConfig,
) -> SelectorRecord:
    training_refs = _ensure_training_results_allowed(
        results,
        task_pool,
        tasks,
        checks,
        agents,
        history_window,
        rolling_policy,
    )
    if candidate_selectors:
        selector = candidate_selectors[0]
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(f"candidate selector is invalid: {', '.join(validation.errors)}")
        ensure_selector_executable(selector)
        return selector
    ensure_selector_family_executable(training_config.selector_family)
    training_source_digests = (
        task_pool.task_pool_digest,
        canonical_digest(tuple(task_check_ref_key(ref) for ref in training_refs)),
        canonical_digest(tuple(sorted(result.result_digest for result in results))),
        rolling_policy.policy_digest,
        feature_config.feature_config_digest,
        training_config.training_config_digest,
    )
    return _selector_record(
        selector_family=training_config.selector_family,
        selector_version="1",
        training_source_digests=training_source_digests,
        allowed_feature_classes=feature_config.allowed_leakage_classes,
        parameters=training_config.parameters,
    )


def freeze_evaluation_selections(
    selector: SelectorRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    selector_inputs: Sequence[SelectorInput],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    selection_config: SelectionConfig,
    rolling_policy: RollingOriginPolicy,
) -> Sequence[BenchmarkSelectionRecord]:
    _ensure_time_range_order(history_window)
    selections = []
    for selector_input in selector_inputs:
        _ensure_selector_input_matches_history(
            selector_input,
            task_pool,
            tasks,
            checks,
            agents,
            history_window,
            rolling_policy,
        )
        selection = select_with_selector(selector_input, selector, selection_config)
        selections.append(selection)
    return tuple(selections)


def select_benchmark(
    selector: SelectorRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    pre_origin_results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    origin_time: datetime,
    budget: SelectionBudget,
    selection_config: SelectionConfig,
    rolling_policy: RollingOriginPolicy,
    feature_config: FeatureConfig,
) -> BenchmarkSelectionRecord:
    origin = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        origin_time,
        TimeRange(start=_datetime_to_iso(origin_time), end=_datetime_to_iso(origin_time)),
        rolling_policy,
    )
    snapshot = build_feature_snapshot(origin, task_pool, tasks, checks, pre_origin_results, feature_config)
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        pre_origin_results,
        agents,
        budget,
        LeakagePolicy(feature_config.leakage_policy_digest, feature_config.allowed_leakage_classes, origin.as_of_cutoff),
    )
    config = SelectionConfig(
        selection_config_digest=selection_config.selection_config_digest,
        selector_id=selection_config.selector_id or selector.selector_id,
        feature_snapshot_id=snapshot.feature_snapshot_id,
        eligibility_mode=selection_config.eligibility_mode,
        exposure_scope_digest=selection_config.exposure_scope_digest,
    )
    return select_with_selector(selector_input, selector, config)
