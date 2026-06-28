"""Selector construction, leakage-checked inputs, and rolling-origin metrics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureRecord,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    canonical_digest,
    make_selector_input_id,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_evaluation_cell_set,
    validate_feature_snapshot,
    validate_metric,
    validate_result,
    validate_result_matrix,
    validate_selector,
    validate_selector_input,
)
from barcarolle.task_pool import TimeRange


@dataclass(frozen=True)
class RollingOriginPolicy:
    policy_digest: str
    as_of_cutoff_rule: str
    embargo: str
    cluster_constraints_digest: str
    eligibility_mode: str
    holdout_overlap_policy: str
    future_holdout_known: bool
    allowed_cluster_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeatureConfig:
    feature_config_digest: str
    leakage_policy_digest: str
    feature_names: tuple[str, ...] = ("task_count", "pre_origin_result_count")
    allowed_leakage_classes: tuple[str, ...] = ("task_metadata", "pre_origin_result")


@dataclass(frozen=True)
class LeakagePolicy:
    leakage_policy_digest: str
    allowed_leakage_classes: tuple[str, ...]
    max_observed_at: str


@dataclass(frozen=True)
class SelectionBudget:
    budget_digest: str
    max_task_checks: int


@dataclass(frozen=True)
class SelectionConfig:
    selection_config_digest: str
    selector_id: str
    feature_snapshot_id: str
    eligibility_mode: str
    exposure_scope_digest: str | None = None


@dataclass(frozen=True)
class CoverageConfig:
    coverage_config_digest: str
    group_by_ref_key: Mapping[str, str]


@dataclass(frozen=True)
class FitConfig:
    fit_config_digest: str
    selector_family: str = "learned_mixture"


@dataclass(frozen=True)
class MetricConfig:
    metric_config_digest: str
    budget_digest: str | None = None


@dataclass(frozen=True)
class ControllerConfig:
    controller_config_digest: str
    fallback_selector_id: str | None = None
    selector_metric_selection_ids: Mapping[str, str] | None = None
    allowed_prior_origin_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelectorTrainingConfig:
    training_config_digest: str
    selector_family: str = "recency"


@dataclass(frozen=True)
class SelectorEvaluationConfig:
    evaluation_config_digest: str
    origin_ids: tuple[str, ...]
    selection_config: SelectionConfig
    budget: SelectionBudget


@dataclass(frozen=True)
class SelectorFeedbackConfig:
    feedback_config_digest: str
    selector_family: str = "adaptive_controller"


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
        return selector
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
        config_digest=canonical_digest(training_source_digests),
    )


def freeze_evaluation_selections(
    selector: SelectorRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    selector_inputs: Mapping[str, SelectorInput],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    evaluation_config: SelectorEvaluationConfig,
    rolling_policy: RollingOriginPolicy,
) -> Sequence[BenchmarkSelectionRecord]:
    _ensure_time_range_order(history_window)
    selections = []
    for origin_id in evaluation_config.origin_ids:
        selector_input = selector_inputs.get(origin_id)
        if selector_input is None:
            raise ValueError(f"selector_input is missing for origin {origin_id}")
        if selector_input.origin_id != origin_id:
            raise ValueError("selector_input origin_id does not match requested origin")
        _ensure_selector_input_matches_history(
            selector_input,
            task_pool,
            tasks,
            checks,
            agents,
            history_window,
            rolling_policy,
        )
        selection = select_with_selector(selector_input, selector, evaluation_config.selection_config)
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


def update_selector(
    selector: SelectorRecord,
    selection: BenchmarkSelectionRecord,
    metrics: Sequence[MetricRecord],
    feedback_config: SelectorFeedbackConfig,
) -> SelectorRecord:
    metric_digests = tuple(sorted(metric.metric_digest for metric in metrics))
    config_digest = canonical_digest(
        {
            "previous_selector": selector.selector_id,
            "selection": selection.selection_digest,
            "metrics": metric_digests,
            "feedback_config": feedback_config.feedback_config_digest,
        }
    )
    return _selector_record(
        selector_family=feedback_config.selector_family,
        selector_version=f"{selector.selector_version}+feedback",
        training_source_digests=(selector.config_digest, selection.selection_digest, *metric_digests),
        allowed_feature_classes=selector.allowed_feature_classes,
        config_digest=config_digest,
    )


def build_rolling_origin(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    origin_time: datetime,
    future_window: TimeRange,
    policy: RollingOriginPolicy,
) -> RollingOriginRecord:
    _ensure_time_range_order(future_window)
    origin_time_iso = _datetime_to_iso(origin_time)
    as_of_cutoff = origin_time_iso if policy.as_of_cutoff_rule == "origin_time" else policy.as_of_cutoff_rule
    history_cutoff = _apply_embargo(as_of_cutoff, policy.embargo)
    history_refs: list[TaskCheckRef] = []
    future_refs: list[TaskCheckRef] = []
    for task in tasks:
        if task.task_id not in task_pool.task_ids:
            continue
        if policy.allowed_cluster_ids and task.cluster_id not in policy.allowed_cluster_ids:
            continue
        for check_id in task.check_ids:
            if check_id not in task_pool.check_ids:
                continue
            check = checks.get(check_id)
            if check is None or check.task_id != task.task_id:
                continue
            known_at = _task_check_known_at(task, check)
            ref = TaskCheckRef(task.task_id, check.check_id)
            if _instant_lte(known_at, history_cutoff):
                history_refs.append(ref)
            elif policy.future_holdout_known and _instant_gt(known_at, as_of_cutoff) and _time_range_contains(future_window, known_at):
                if policy.holdout_overlap_policy == "disjoint" and ref in history_refs:
                    continue
                future_refs.append(ref)
    return RollingOriginRecord(
        origin_id=f"origin_{canonical_digest((task_pool.task_pool_id, origin_time_iso, policy.policy_digest))}",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time=origin_time_iso,
        policy_digest=policy.policy_digest,
        history_task_check_refs=tuple(history_refs),
        future_holdout_task_check_refs=tuple(future_refs),
        as_of_cutoff=as_of_cutoff,
        embargo=policy.embargo,
        cluster_constraints_digest=policy.cluster_constraints_digest,
        eligibility_mode=policy.eligibility_mode,
        holdout_overlap_policy=policy.holdout_overlap_policy,
    )


def build_feature_snapshot(
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    pre_origin_results: Sequence[ResultRecord],
    feature_config: FeatureConfig,
) -> FeatureSnapshotRecord:
    _ensure_results_allowed(pre_origin_results, origin, task_pool, agents=None, tasks=tasks, checks=checks)
    task_count = len(origin.history_task_check_refs)
    feature_records: list[FeatureRecord] = []
    if "task_count" in feature_config.feature_names:
        feature_records.append(
            _feature_record(
                origin,
                feature_config,
                feature_scope="origin",
                feature_name="task_count",
                value=task_count,
                observed_at=origin.as_of_cutoff,
                source_artifact_digest=task_pool.task_pool_digest,
                leakage_class="task_metadata",
            )
        )
    if "pre_origin_result_count" in feature_config.feature_names:
        feature_records.append(
            _feature_record(
                origin,
                feature_config,
                feature_scope="origin",
                feature_name="pre_origin_result_count",
                value=len(pre_origin_results),
                observed_at=origin.as_of_cutoff,
                source_artifact_digest=canonical_digest(tuple(result.result_digest for result in pre_origin_results)),
                leakage_class="pre_origin_result",
            )
        )
    if "task_cluster" in feature_config.feature_names:
        task_by_id = {task.task_id: task for task in tasks}
        for ref in origin.history_task_check_refs:
            task = task_by_id.get(ref.task_id)
            if task is None:
                continue
            feature_records.append(
                _feature_record(
                    origin,
                    feature_config,
                    feature_scope="task",
                    feature_name="task_cluster",
                    value=task.cluster_id,
                    observed_at=_task_known_at(task),
                    source_artifact_digest=canonical_digest(task),
                    leakage_class="task_metadata",
                    task_id=task.task_id,
                    check_id=ref.check_id,
                )
            )
    feature_records_tuple = tuple(feature_records)
    result_view_digest = _result_view_digest(pre_origin_results)
    snapshot = FeatureSnapshotRecord(
        feature_snapshot_id=f"feature_snapshot_{canonical_digest((origin.origin_id, feature_config.feature_config_digest, canonical_digest(feature_records_tuple), result_view_digest))}",
        origin_id=origin.origin_id,
        feature_record_ids=tuple(record.feature_id for record in feature_records_tuple),
        feature_records_digest=canonical_digest(feature_records_tuple),
        leakage_policy_digest=feature_config.leakage_policy_digest,
        leakage_lint_status="not_run",
        feature_records=feature_records_tuple,
        result_view_digest=result_view_digest,
    )
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        raise ValueError(f"feature snapshot is invalid: {', '.join(validation.errors)}")
    return snapshot


def lint_feature_snapshot(snapshot: FeatureSnapshotRecord, policy: LeakagePolicy) -> ValidationResult:
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        return validation
    records = snapshot.feature_records
    if not records:
        return ValidationResult.fail(("feature records are not available for linting",))
    errors: list[str] = []
    if snapshot.leakage_policy_digest != policy.leakage_policy_digest:
        errors.append("snapshot leakage_policy_digest does not match policy")
    if snapshot.feature_records_digest != canonical_digest(records):
        errors.append("feature_records_digest does not match feature records")
    for record in records:
        if _instant_gt(record.observed_at, policy.max_observed_at):
            errors.append("feature observed_at is after leakage cutoff")
        if record.leakage_class not in policy.allowed_leakage_classes:
            errors.append("feature leakage_class is not allowed")
    return ValidationResult.pass_() if not errors else ValidationResult.fail(errors)


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


def select_random(selector_input: SelectorInput, seed: int) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = list(selector_input.eligible_task_check_refs)
    Random(seed).shuffle(refs)
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_random",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="random",
        exposure_scope_digest=None,
    )


def select_recency(selector_input: SelectorInput) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = tuple(reversed(selector_input.eligible_task_check_refs))
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_recency",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="recency",
        exposure_scope_digest=None,
    )


def select_coverage(selector_input: SelectorInput, coverage_config: CoverageConfig) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = _coverage_order(selector_input.eligible_task_check_refs, coverage_config)
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_coverage",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="coverage",
        exposure_scope_digest=coverage_config.coverage_config_digest,
    )


def select_rule_mixture(
    selector_input: SelectorInput,
    expert_weights: Mapping[str, float],
    selection_config: SelectionConfig,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    if selection_config.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("selection_config feature_snapshot_id must match selector_input")
    scored = []
    total_weight = sum(max(0.0, weight) for weight in expert_weights.values()) or 1.0
    refs = selector_input.eligible_task_check_refs
    for index, ref in enumerate(refs):
        recency = (index + 1) / max(1, len(refs))
        randomish = int(canonical_digest((selection_config.selection_config_digest, task_check_ref_key(ref)))[:8], 16) / 0xFFFFFFFF
        score = (
            expert_weights.get("recency", 0.0) * recency
            + expert_weights.get("random", 0.0) * randomish
            + expert_weights.get("coverage", 0.0)
        ) / total_weight
        scored.append((score, ref))
    ordered_refs = tuple(ref for _, ref in sorted(scored, key=lambda item: (-item[0], item[1].task_id, item[1].check_id)))
    return _selection_from_refs(
        selector_input,
        ordered_refs[: _selection_count(selector_input)],
        selector_id=selection_config.selector_id,
        feature_snapshot_id=selection_config.feature_snapshot_id,
        eligibility_mode=selection_config.eligibility_mode,
        exposure_scope_digest=selection_config.exposure_scope_digest,
    )


def fit_learned_mixture(
    training_origins: Sequence[RollingOriginRecord],
    training_selector_inputs: Mapping[str, SelectorInput],
    baseline_selectors: Sequence[SelectorRecord],
    fit_config: FitConfig,
) -> SelectorRecord:
    ordered_inputs = _validated_training_selector_inputs(training_origins, training_selector_inputs)
    source_digests = (
        fit_config.fit_config_digest,
        canonical_digest(tuple(origin.origin_id for origin in training_origins)),
        canonical_digest(tuple(selector_input.selector_input_digest for selector_input in ordered_inputs)),
        canonical_digest(tuple(selector.config_digest for selector in baseline_selectors)),
    )
    return _selector_record(
        selector_family=fit_config.selector_family,
        selector_version="1",
        training_source_digests=source_digests,
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
        config_digest=canonical_digest(source_digests),
    )


def fit_calibrated_weighting(
    training_origins: Sequence[RollingOriginRecord],
    training_selector_inputs: Mapping[str, SelectorInput],
    selection_config: SelectionConfig,
) -> SelectorRecord:
    ordered_inputs = _validated_training_selector_inputs(training_origins, training_selector_inputs)
    source_digests = (
        selection_config.selection_config_digest,
        canonical_digest(tuple(origin.origin_id for origin in training_origins)),
        canonical_digest(tuple(selector_input.selector_input_digest for selector_input in ordered_inputs)),
    )
    return _selector_record(
        selector_family="calibrated_weighting",
        selector_version="1",
        training_source_digests=source_digests,
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
        config_digest=canonical_digest(source_digests),
    )


def select_with_selector(
    selector_input: SelectorInput,
    selector: SelectorRecord,
    selection_config: SelectionConfig,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    selector_validation = validate_selector(selector)
    if not selector_validation.ok:
        raise ValueError(f"selector is invalid: {', '.join(selector_validation.errors)}")
    if selection_config.selector_id != selector.selector_id:
        raise ValueError("selection_config selector_id must match selector")
    if selection_config.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("selection_config feature_snapshot_id must match selector_input")
    if selector.selector_family == "random":
        refs = list(selector_input.eligible_task_check_refs)
        Random(int(canonical_digest(selection_config.selection_config_digest)[:8], 16)).shuffle(refs)
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "coverage":
        refs = _coverage_order(selector_input.eligible_task_check_refs, CoverageConfig(selection_config.selection_config_digest, {}))
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "rule_mixture":
        return select_rule_mixture(selector_input, {"recency": 1.0, "coverage": 1.0}, selection_config)
    if selector.selector_family == "recency":
        refs = tuple(reversed(selector_input.eligible_task_check_refs))
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    raise ValueError(f"unsupported selector family for selection: {selector.selector_family}")


def evaluate_selection(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    metric_config: MetricConfig,
) -> Sequence[MetricRecord]:
    record_error = _record_validation_error(selection, origin, evaluation_cells, selected_matrix, future_matrix)
    if record_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=record_error,
            ),
        )
    alignment_error = _matrix_alignment_error(selection, origin, evaluation_cells, selected_matrix, future_matrix)
    if alignment_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=alignment_error,
            ),
        )
    completeness_error = _matrix_completeness_error(selected_matrix, future_matrix)
    if completeness_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="abstained",
                abstention_reason=completeness_error,
            ),
        )
    try:
        selected_rates = _pass_rates(selected_matrix, selection.selected_weights)
        future_rates = _pass_rates(future_matrix)
    except ValueError as exc:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=str(exc),
            ),
        )
    mae = _mean_absolute_error(selected_rates, future_rates)
    coverage = _coverage(future_matrix)
    invalid_rate = _invalid_rate(future_matrix)
    return (
        _metric_record(
            selection,
            origin,
            evaluation_cells,
            selected_matrix,
            future_matrix,
            metric_config,
            metric_scope="aggregate",
            metric_name="future_pass_rate_mae",
            metric_value=mae,
            completeness_state=future_matrix.scoreable_state,
            abstention_reason=future_matrix.abstention_reason,
        ),
        _metric_record(
            selection,
            origin,
            evaluation_cells,
            selected_matrix,
            future_matrix,
            metric_config,
            metric_scope="aggregate",
            metric_name="future_coverage",
            metric_value=coverage,
            completeness_state=future_matrix.scoreable_state,
            abstention_reason=future_matrix.abstention_reason,
        ),
        _metric_record(
            selection,
            origin,
            evaluation_cells,
            selected_matrix,
            future_matrix,
            metric_config,
            metric_scope="aggregate",
            metric_name="future_invalid_rate",
            metric_value=invalid_rate,
            completeness_state=future_matrix.scoreable_state,
            abstention_reason=future_matrix.abstention_reason,
        ),
    )


def choose_selector_for_origin(
    registered_selectors: Sequence[SelectorRecord],
    prior_metrics: Sequence[MetricRecord],
    origin: RollingOriginRecord,
    controller_config: ControllerConfig,
) -> SelectorRecord:
    if not registered_selectors:
        raise ValueError("registered_selectors must not be empty")
    selector_by_id = {selector.selector_id: selector for selector in registered_selectors}
    metric_map = controller_config.selector_metric_selection_ids or {}
    allowed_prior_origin_ids = set(controller_config.allowed_prior_origin_ids)
    if not allowed_prior_origin_ids:
        return _fallback_selector(registered_selectors, selector_by_id, controller_config)
    best_selector: SelectorRecord | None = None
    best_value: float | None = None
    for selector_id, selection_id in metric_map.items():
        selector = selector_by_id.get(selector_id)
        if selector is None:
            continue
        selector_metrics = [
            metric
            for metric in prior_metrics
            if metric.selection_id == selection_id
            and metric.metric_name == "future_pass_rate_mae"
            and validate_metric(metric).ok
            and metric.origin_id in allowed_prior_origin_ids
            and metric.origin_id != origin.origin_id
            and _instant_lte(metric.computed_at, origin.as_of_cutoff)
        ]
        if not selector_metrics:
            continue
        value = selector_metrics[-1].metric_value
        if best_value is None or value < best_value:
            best_selector = selector
            best_value = value
    if best_selector is not None:
        return best_selector
    return _fallback_selector(registered_selectors, selector_by_id, controller_config)


def _fallback_selector(
    registered_selectors: Sequence[SelectorRecord],
    selector_by_id: Mapping[str, SelectorRecord],
    controller_config: ControllerConfig,
) -> SelectorRecord:
    if controller_config.fallback_selector_id and controller_config.fallback_selector_id in selector_by_id:
        return selector_by_id[controller_config.fallback_selector_id]
    return registered_selectors[0]


def _selector_record(
    selector_family: str,
    selector_version: str,
    training_source_digests: tuple[str, ...],
    allowed_feature_classes: tuple[str, ...],
    config_digest: str,
) -> SelectorRecord:
    selector = SelectorRecord(
        selector_id=f"selector_{canonical_digest((selector_family, selector_version, config_digest))}",
        selector_family=selector_family,
        selector_version=selector_version,
        training_source_digests=training_source_digests,
        allowed_feature_classes=allowed_feature_classes,
        config_digest=config_digest,
        created_at=_now(),
    )
    validation = validate_selector(selector)
    if not validation.ok:
        raise ValueError(f"selector is invalid: {', '.join(validation.errors)}")
    return selector


def _feature_record(
    origin: RollingOriginRecord,
    feature_config: FeatureConfig,
    *,
    feature_scope: str,
    feature_name: str,
    value: object,
    observed_at: str,
    source_artifact_digest: str,
    leakage_class: str,
    task_id: str | None = None,
    check_id: str | None = None,
    agent_id: str | None = None,
    result_id: str | None = None,
    result_cache_identity_digest: str | None = None,
) -> FeatureRecord:
    feature_id = f"feature_{canonical_digest((origin.origin_id, feature_scope, task_id, check_id, agent_id, result_id, feature_name))}"
    return FeatureRecord(
        feature_id=feature_id,
        feature_scope=feature_scope,
        task_id=task_id,
        check_id=check_id,
        agent_id=agent_id,
        result_id=result_id,
        result_cache_identity_digest=result_cache_identity_digest,
        feature_name=feature_name,
        value=value,
        aggregation_window=None,
        aggregation_method=None,
        observed_at=observed_at,
        source_artifact_digest=source_artifact_digest,
        origin_snapshot_digest=canonical_digest((origin.origin_id, feature_config.feature_config_digest)),
        leakage_class=leakage_class,
    )


def _selection_from_refs(
    selector_input: SelectorInput,
    refs: Sequence[TaskCheckRef],
    *,
    selector_id: str,
    feature_snapshot_id: str,
    eligibility_mode: str,
    exposure_scope_digest: str | None,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    selected_refs = tuple(refs)
    if not selected_refs:
        raise ValueError("selection must include at least one Task/Check ref")
    eligible_refs = set(selector_input.eligible_task_check_refs)
    if any(ref not in eligible_refs for ref in selected_refs):
        raise ValueError("selection includes refs outside selector_input eligibility")
    if len(selected_refs) > _selection_count(selector_input):
        raise ValueError("selection exceeds selector_input budget")
    if feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("feature_snapshot_id must match selector_input")
    weights = {task_check_ref_key(ref): 1.0 for ref in selected_refs}
    selection = BenchmarkSelectionRecord(
        selection_id=f"selection_{canonical_digest((selector_input.selector_input_digest, selector_id, tuple(task_check_ref_key(ref) for ref in selected_refs)))}",
        task_pool_id=selector_input.task_pool_id,
        task_pool_digest=selector_input.task_pool_digest or "",
        origin_id=selector_input.origin_id,
        selector_id=selector_id,
        selected_task_check_refs=selected_refs,
        selected_weights=weights,
        budget_digest=selector_input.budget_digest,
        selection_input_digest=selector_input.selector_input_digest,
        feature_snapshot_id=feature_snapshot_id,
        eligibility_mode=eligibility_mode,
        exposure_state="frozen",
        exposed_at=None,
        exposure_scope_digest=exposure_scope_digest,
        created_at=_now(),
        selection_digest="",
    )
    selection = record_with_digest(selection)
    validation = validate_benchmark_selection(selection)
    if not validation.ok:
        raise ValueError(f"benchmark selection is invalid: {', '.join(validation.errors)}")
    return selection


def _selection_count(selector_input: SelectorInput) -> int:
    _ensure_selector_input_valid(selector_input)
    if selector_input.selection_budget_limit is None:
        raise ValueError("selector_input selection_budget_limit is required")
    limit = selector_input.selection_budget_limit
    return max(1, min(limit, len(selector_input.eligible_task_check_refs)))


def _coverage_order(refs: Sequence[TaskCheckRef], coverage_config: CoverageConfig) -> tuple[TaskCheckRef, ...]:
    grouped: dict[str, list[TaskCheckRef]] = {}
    for ref in refs:
        group = coverage_config.group_by_ref_key.get(task_check_ref_key(ref), ref.check_id)
        grouped.setdefault(group, []).append(ref)
    ordered: list[TaskCheckRef] = []
    while any(grouped.values()):
        for group in sorted(grouped):
            if grouped[group]:
                ordered.append(grouped[group].pop(0))
    return tuple(ordered)


def _matrix_alignment_error(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str | None:
    if selection.origin_id != origin.origin_id or evaluation_cells.origin_id != origin.origin_id:
        return "origin_mismatch"
    if evaluation_cells.selection_id != selection.selection_id:
        return "evaluation_cell_selection_mismatch"
    if selected_matrix.matrix_role != "selected" or future_matrix.matrix_role != "future_holdout":
        return "matrix_role_mismatch"
    if selected_matrix.origin_id != origin.origin_id or future_matrix.origin_id != origin.origin_id:
        return "matrix_origin_mismatch"
    if selected_matrix.selection_id != selection.selection_id or future_matrix.selection_id != selection.selection_id:
        return "matrix_selection_mismatch"
    if selected_matrix.agent_ids != future_matrix.agent_ids:
        return "agent_set_mismatch"
    if selected_matrix.join_policy_digest != future_matrix.join_policy_digest:
        return "join_policy_mismatch"
    if selected_matrix.denominator_policy_digest != future_matrix.denominator_policy_digest:
        return "denominator_policy_mismatch"
    if selected_matrix.task_check_refs != selection.selected_task_check_refs:
        return "selected_denominator_mismatch"
    if evaluation_cells.selected_task_check_refs != selection.selected_task_check_refs:
        return "evaluation_selected_denominator_mismatch"
    if future_matrix.task_check_refs != origin.future_holdout_task_check_refs:
        return "future_denominator_mismatch"
    if evaluation_cells.future_task_check_refs != origin.future_holdout_task_check_refs:
        return "evaluation_future_denominator_mismatch"
    if not _matrix_cells_match_cell_set(selected_matrix, evaluation_cells, selection.selected_task_check_refs):
        return "selected_matrix_cell_identity_mismatch"
    if not _matrix_cells_match_cell_set(future_matrix, evaluation_cells, origin.future_holdout_task_check_refs):
        return "future_matrix_cell_identity_mismatch"
    return None


def _matrix_cells_match_cell_set(
    matrix: ResultMatrix,
    evaluation_cells: EvaluationCellSet,
    refs: Sequence[TaskCheckRef],
) -> bool:
    allowed_refs = {(ref.task_id, ref.check_id) for ref in refs}
    expected = {
        (cell.agent_id, cell.task_id, cell.check_id): cell.required_identity_digest
        for cell in evaluation_cells.cells
        if (cell.task_id, cell.check_id) in allowed_refs
    }
    actual = {
        (cell.agent_id, cell.task_id, cell.check_id): cell.required_identity_digest
        for cell in matrix.cells
    }
    return actual == expected


def _record_validation_error(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str | None:
    selection_validation = validate_benchmark_selection(selection)
    if not selection_validation.ok:
        return f"selection_invalid:{'; '.join(selection_validation.errors)}"
    if selection.exposure_state != "frozen":
        return "selection_not_frozen"
    if selection.task_pool_id != origin.task_pool_id or selection.task_pool_digest != origin.task_pool_digest:
        return "selection_task_pool_mismatch"
    validations = (
        ("evaluation_cell_set", validate_evaluation_cell_set(evaluation_cells)),
        ("selected_matrix", validate_result_matrix(selected_matrix)),
        ("future_matrix", validate_result_matrix(future_matrix)),
    )
    for label, validation in validations:
        if not validation.ok:
            return f"{label}_invalid:{'; '.join(validation.errors)}"
    return None


def _ensure_feature_records_match_origin(
    snapshot: FeatureSnapshotRecord,
    origin: RollingOriginRecord,
    pre_origin_results: Sequence[ResultRecord],
) -> None:
    if snapshot.result_view_digest != _result_view_digest(pre_origin_results):
        raise ValueError("feature snapshot result view does not match selector input")
    allowed_refs = {(ref.task_id, ref.check_id) for ref in origin.history_task_check_refs}
    result_by_id = {result.result_id: result for result in pre_origin_results}
    result_digests = tuple(result.result_digest for result in pre_origin_results)
    aggregate_result_digest = canonical_digest(result_digests)
    for record in snapshot.feature_records:
        if record.task_id is not None and record.task_id not in {ref.task_id for ref in origin.history_task_check_refs}:
            raise ValueError("feature snapshot includes task outside origin history")
        if record.check_id is not None and (record.task_id, record.check_id) not in allowed_refs:
            raise ValueError("feature snapshot includes check outside origin history")
        if _instant_gt(record.observed_at, origin.as_of_cutoff):
            raise ValueError("feature snapshot includes post-origin feature")
        if record.leakage_class == "pre_origin_result":
            if record.result_id is None:
                if record.source_artifact_digest != aggregate_result_digest:
                    raise ValueError("feature snapshot result provenance does not match selector input")
                if record.feature_name == "pre_origin_result_count" and record.value != len(pre_origin_results):
                    raise ValueError("feature snapshot result count does not match selector input")
            else:
                result = result_by_id.get(record.result_id)
                if result is None or record.source_artifact_digest != result.result_digest:
                    raise ValueError("feature snapshot includes result outside selector input")
                if record.result_cache_identity_digest and record.result_cache_identity_digest != result.cache_identity.identity_digest:
                    raise ValueError("feature snapshot result identity does not match selector input")


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


def _matrix_completeness_error(selected_matrix: ResultMatrix, future_matrix: ResultMatrix) -> str | None:
    if selected_matrix.abstention_reason or future_matrix.abstention_reason:
        return selected_matrix.abstention_reason or future_matrix.abstention_reason
    if any(cell.cell_state == "missing" for cell in selected_matrix.cells + future_matrix.cells):
        return "missing_required_results"
    return None


def _pass_rates(matrix: ResultMatrix, weights: Mapping[str, float] | None = None) -> Mapping[str, float]:
    rates: dict[str, float] = {}
    for agent_id in matrix.agent_ids:
        cells = [cell for cell in matrix.cells if cell.agent_id == agent_id and cell.cell_state == "result"]
        if not cells:
            rates[agent_id] = 0.0
            continue
        if any(cell.outcome not in {"pass", "fail", "invalid"} for cell in cells):
            raise ValueError("result matrix cells must carry outcomes for metric computation")
        if weights is None:
            passed = sum(1 for cell in cells if cell.outcome == "pass")
            rates[agent_id] = passed / len(cells)
            continue
        weighted_total = 0.0
        weighted_passed = 0.0
        for cell in cells:
            weight = weights.get(task_check_ref_key(TaskCheckRef(cell.task_id, cell.check_id)))
            if weight is None:
                raise ValueError("selected matrix cells must have selection weights")
            weighted_total += weight
            if cell.outcome == "pass":
                weighted_passed += weight
        rates[agent_id] = 0.0 if weighted_total == 0.0 else weighted_passed / weighted_total
    return rates


def _mean_absolute_error(selected_rates: Mapping[str, float], future_rates: Mapping[str, float]) -> float:
    agent_ids = sorted(set(selected_rates) & set(future_rates))
    if not agent_ids:
        return 0.0
    return sum(abs(selected_rates[agent_id] - future_rates[agent_id]) for agent_id in agent_ids) / len(agent_ids)


def _coverage(matrix: ResultMatrix) -> float:
    if not matrix.cells:
        return 0.0
    covered = sum(1 for cell in matrix.cells if cell.cell_state == "result")
    return covered / len(matrix.cells)


def _invalid_rate(matrix: ResultMatrix) -> float:
    if not matrix.cells:
        return 0.0
    invalid = sum(
        1
        for cell in matrix.cells
        if cell.cell_state in {"missing", "excluded"} or (cell.cell_state == "result" and cell.outcome == "invalid")
    )
    return invalid / len(matrix.cells)


def _metric_record(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    metric_config: MetricConfig,
    *,
    metric_scope: str,
    metric_name: str,
    metric_value: float,
    completeness_state: str,
    abstention_reason: str | None,
) -> MetricRecord:
    metric = MetricRecord(
        metric_id=f"metric_{canonical_digest((origin.origin_id, selection.selection_id, evaluation_cells.cell_set_digest, selected_matrix.matrix_digest, future_matrix.matrix_digest, selected_matrix.join_policy_digest, selected_matrix.denominator_policy_digest, metric_scope, metric_name, metric_config.metric_config_digest, None, None, 'all_agents'))}",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        evaluation_cell_set_digest=evaluation_cells.cell_set_digest,
        selected_matrix_digest=selected_matrix.matrix_digest,
        future_matrix_digest=future_matrix.matrix_digest,
        join_policy_digest=selected_matrix.join_policy_digest,
        metric_config_digest=metric_config.metric_config_digest,
        metric_scope=metric_scope,
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest=metric_config.budget_digest,
        stratum_ref=None,
        metric_name=metric_name,
        metric_value=metric_value,
        denominator_policy_digest=selected_matrix.denominator_policy_digest,
        completeness_state=completeness_state,
        abstention_reason=abstention_reason,
        computed_at=_now(),
        metric_digest="",
    )
    metric = record_with_digest(metric)
    validation = validate_metric(metric)
    if not validation.ok:
        raise ValueError(f"metric is invalid: {', '.join(validation.errors)}")
    return metric


def _task_known_at(task: TaskRecord) -> str:
    return _max_timestamp(task.source_resolved_at, task.task_material_available_at, task.certified_at)


def _task_check_known_at(task: TaskRecord, check: CheckRecord) -> str:
    return _max_timestamp(_task_known_at(task), check.check_material_available_at, check.certified_at)


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


def _training_history_refs(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    history_window: TimeRange,
    rolling_policy: RollingOriginPolicy,
) -> tuple[TaskCheckRef, ...]:
    _ensure_time_range_order(history_window)
    history_cutoff = _apply_embargo(history_window.end, rolling_policy.embargo)
    allowed_window = TimeRange(history_window.start, history_cutoff)
    refs: list[TaskCheckRef] = []
    for task in tasks:
        if task.task_id not in task_pool.task_ids:
            continue
        if rolling_policy.allowed_cluster_ids and task.cluster_id not in rolling_policy.allowed_cluster_ids:
            continue
        for check_id in task.check_ids:
            if check_id not in task_pool.check_ids:
                continue
            check = checks.get(check_id)
            if check is None or check.task_id != task.task_id:
                continue
            if _time_range_contains(allowed_window, _task_check_known_at(task, check)):
                refs.append(TaskCheckRef(task.task_id, check.check_id))
    return tuple(refs)


def _ensure_results_pre_origin(results: Sequence[ResultRecord], cutoff: str) -> None:
    leaked = [result.result_id for result in results if _instant_gt(result.result_available_at, cutoff)]
    if leaked:
        raise ValueError("pre_origin_results include results after the origin cutoff")


def _ensure_results_allowed(
    results: Sequence[ResultRecord],
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord] | None,
    tasks: Sequence[TaskRecord] | None = None,
    checks: Mapping[str, CheckRecord] | None = None,
    expected_result_view_digest: str | None = None,
) -> None:
    _ensure_result_records_valid(results, "pre_origin_results")
    if tasks is not None and checks is not None:
        _ensure_result_identity_matches_current_records(results, tasks, checks, agents=None)
    if agents is not None:
        _ensure_result_identity_matches_agents(results, agents)
    _ensure_results_pre_origin(results, origin.as_of_cutoff)
    allowed_refs = {(ref.task_id, ref.check_id) for ref in origin.history_task_check_refs}
    allowed_agents = {agent.agent_id for agent in agents} if agents is not None else None
    for result in results:
        if result.task_id not in task_pool.task_ids or result.check_id not in task_pool.check_ids:
            raise ValueError("pre_origin_results include off-pool results")
        if (result.task_id, result.check_id) not in allowed_refs:
            raise ValueError("pre_origin_results include results outside origin history refs")
        if allowed_agents is not None and result.agent_id not in allowed_agents:
            raise ValueError("pre_origin_results include results outside candidate Agent set")
    if expected_result_view_digest is not None and _result_view_digest(results) != expected_result_view_digest:
        raise ValueError("pre_origin_results result provenance does not match validated feature snapshot result view")


def _ensure_result_records_valid(results: Sequence[ResultRecord], label: str) -> None:
    for result in results:
        validation = validate_result(result)
        if not validation.ok:
            raise ValueError(f"{label} include invalid ResultRecord: {', '.join(validation.errors)}")


def _ensure_result_identity_matches_current_records(
    results: Sequence[ResultRecord],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord] | None,
) -> None:
    task_by_id = {task.task_id: task for task in tasks}
    for result in results:
        task = task_by_id.get(result.task_id)
        check = checks.get(result.check_id)
        if task is None or check is None or check.task_id != task.task_id:
            raise ValueError("results include Task/Check identity outside current records")
        identity = result.cache_identity
        if (
            identity.repository_id != task.repository_id
            or identity.base_commit != task.base_commit
            or identity.solver_material_digest != task.solver_material_digest
            or identity.check_manifest_digest != check.check_manifest_digest
            or identity.hidden_check_bundle_digest != check.hidden_check_bundle_digest
            or identity.verifier_image_digest != check.verifier_image_digest
            or identity.verifier_deps_digest != check.verifier_deps_digest
        ):
            raise ValueError("results include cache identity that does not match current Task/Check records")
    if agents is not None:
        _ensure_result_identity_matches_agents(results, agents)


def _ensure_result_identity_matches_agents(results: Sequence[ResultRecord], agents: Sequence[AgentRecord]) -> None:
    agent_by_id = {agent.agent_id: agent for agent in agents}
    for result in results:
        agent = agent_by_id.get(result.agent_id)
        if agent is None:
            raise ValueError("results include cache identity outside candidate Agent records")
        identity = result.cache_identity
        if (
            identity.agent_manifest_digest != agent.agent_manifest_digest
            or identity.model_snapshot_id != agent.model_snapshot_id
            or identity.harness_digest != agent.harness_digest
            or identity.repository_instruction_digest != agent.repository_instruction_digest
            or identity.prompt_digest != agent.prompt_digest
            or identity.tools_digest != agent.tools_digest
            or identity.retrieval_digest != agent.retrieval_digest
            or identity.skills_digest != agent.skills_digest
            or identity.network_policy_digest != agent.network_policy_digest
            or identity.adapter_digest != agent.adapter_digest
        ):
            raise ValueError("results include cache identity that does not match candidate Agent records")


def _result_view_digest(results: Sequence[ResultRecord]) -> str:
    return canonical_digest(tuple((result.result_id, result.result_digest, result.cache_identity.identity_digest) for result in results))


def _ensure_time_range_order(time_range: TimeRange) -> None:
    if _instant_gt(time_range.start, time_range.end):
        raise ValueError("time range start must be before end")


def _apply_embargo(as_of_cutoff: str, embargo: str) -> str:
    if embargo in {"", "P0D", "PT0S"}:
        return _datetime_to_iso(_parse_timestamp_utc(as_of_cutoff))
    if embargo.startswith("P") and embargo.endswith("D"):
        days = int(embargo[1:-1])
        cutoff = _parse_timestamp_utc(as_of_cutoff) - timedelta(days=days)
        return _datetime_to_iso(cutoff)
    raise ValueError("only day-based embargo intervals are supported")


def _datetime_to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_timestamp_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _instant_lte(left: str, right: str) -> bool:
    return _parse_timestamp_utc(left) <= _parse_timestamp_utc(right)


def _instant_gt(left: str, right: str) -> bool:
    return _parse_timestamp_utc(left) > _parse_timestamp_utc(right)


def _time_range_contains(time_range: TimeRange, value: str) -> bool:
    instant = _parse_timestamp_utc(value)
    return _parse_timestamp_utc(time_range.start) <= instant <= _parse_timestamp_utc(time_range.end)


def _max_timestamp(*values: str) -> str:
    return max(values, key=_parse_timestamp_utc)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
