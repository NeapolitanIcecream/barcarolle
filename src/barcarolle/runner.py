"""Command-level orchestration across Barcarolle owner modules."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TypeVar, cast
import os

from barcarolle import reporting as reporting_module
from barcarolle import result_store as result_store_module
from barcarolle import selection as selection_module
from barcarolle import task_pool as task_pool_module
from barcarolle import workspace as workspace_module
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    RuntimeConfig,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    cache_identity_task_check_mismatches,
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    load_jsonl_records,
    parse_utc_timestamp,
    record_with_digest,
    result_cell_record_mismatches,
    validate_benchmark_selection,
    validate_check,
    validate_evaluation_cell_set,
    validate_feature_snapshot,
    validate_metric,
    validate_result_matrix,
    validate_rolling_origin,
    validate_runtime_config,
    validate_selector,
    validate_selector_input,
    validate_task,
    validate_workspace_config,
    utc_now_timestamp,
)
from barcarolle.task_pool import TimeRange


_RecordT = TypeVar("_RecordT")


@dataclass(frozen=True)
class TaskPoolConfig:
    repository_id: str
    repository_path: Path
    artifact_root: Path
    workspace_config: WorkspaceConfig
    runtime_config: RuntimeConfig
    reference_patches: Mapping[str, workspace_module.CapturedDiff]
    check_commands: Mapping[str, tuple[str, ...]]
    hidden_material_paths: Mapping[str, Path]
    check_manifests: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    time_range: TimeRange | None = None
    task_source_config: task_pool_module.TaskSourceConfig | None = None
    import_path: Path | None = None
    import_config: task_pool_module.ImportConfig = field(
        default_factory=task_pool_module.ImportConfig
    )
    certification_config: task_pool_module.CertificationConfig = field(
        default_factory=task_pool_module.CertificationConfig
    )
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportConfig:
    output_dir: Path
    agents: tuple[AgentRecord, ...] = ()
    artifact_root: Path | None = None
    markdown_filename: str = "report.md"
    json_filename: str = "report.json"
    claim_config: reporting_module.ClaimConfig = field(
        default_factory=reporting_module.ClaimConfig
    )

    def __post_init__(self) -> None:
        for field_name, suffix in (
            ("markdown_filename", ".md"),
            ("json_filename", ".json"),
        ):
            value = getattr(self, field_name)
            if (
                type(value) is not str
                or not value
                or value.strip() != value
                or "/" in value
                or "\\" in value
                or Path(value).suffix != suffix
            ):
                raise ValueError(
                    f"{field_name} must be a direct {suffix} filename under output_dir"
                )


@dataclass(frozen=True)
class _EvaluationCellSetPlan:
    selection: BenchmarkSelectionRecord
    origin: RollingOriginRecord
    future_task_pool_id: str
    future_task_pool_digest: str
    future_task_check_refs: tuple[TaskCheckRef, ...]
    future_censored_task_check_refs: tuple[TaskCheckRef, ...]
    tasks: tuple[TaskRecord, ...]
    checks: Mapping[str, CheckRecord]


def build_task_pool(config: TaskPoolConfig) -> TaskPoolRecord:
    if not config.repository_id:
        raise ValueError("repository_id must not be empty")
    _validate_task_pool_configs(config)
    source_window = _canonical_source_window(config.time_range)
    batch = _resolved_task_pool_candidate_batch(config)
    certified = _certify_task_pool_candidates(config, batch.candidates)
    return _publish_task_pool(config, source_window, batch, certified)


def _validate_task_pool_configs(config: TaskPoolConfig) -> None:
    for config_name, validation in (
        ("workspace_config", validate_workspace_config(config.workspace_config)),
        ("runtime_config", validate_runtime_config(config.runtime_config)),
    ):
        if not validation.ok:
            raise ValueError(
                f"{config_name} is invalid: {', '.join(validation.errors)}"
            )


def _resolved_task_pool_candidate_batch(
    config: TaskPoolConfig,
) -> task_pool_module.CandidateBatch:
    batch = _candidate_batch(config)
    candidates = batch.candidates
    mismatched_repositories = tuple(
        candidate.candidate_id
        for candidate in candidates
        if candidate.repository_id != config.repository_id
    )
    if mismatched_repositories:
        raise ValueError(
            "candidate repository_id does not match TaskPoolConfig for: "
            + ", ".join(mismatched_repositories)
        )
    resolved_commits: dict[str, str] = {}
    resolved_candidates = []
    for candidate in candidates:
        if candidate.base_commit not in resolved_commits:
            resolved_commits[candidate.base_commit] = (
                workspace_module.resolve_repository_commit(
                    config.repository_path,
                    candidate.base_commit,
                )
            )
        resolved_candidates.append(
            replace(candidate, base_commit=resolved_commits[candidate.base_commit])
        )
    candidates = tuple(resolved_candidates)
    _require_candidate_inputs(
        candidates,
        config.reference_patches,
        "reference patch is missing for candidates",
    )
    _require_candidate_inputs(
        candidates,
        config.check_commands,
        "check command is missing for candidates",
    )
    _require_candidate_inputs(
        candidates,
        config.hidden_material_paths,
        "hidden check material is missing for candidates",
    )
    return replace(batch, candidates=candidates)


def _require_candidate_inputs(
    candidates: Sequence[task_pool_module.TaskCandidate],
    values: Mapping[str, object],
    message: str,
) -> None:
    missing_ids = tuple(
        candidate.candidate_id
        for candidate in candidates
        if candidate.candidate_id not in values
    )
    if missing_ids:
        raise ValueError(f"{message}: " + ", ".join(missing_ids))


def _certify_task_pool_candidates(
    config: TaskPoolConfig,
    candidates: Sequence[task_pool_module.TaskCandidate],
) -> tuple[task_pool_module.CertificationResult, ...]:
    run_context = workspace_module.bind_repository_source(
        workspace_module.WorkspaceRunContext(),
        config.workspace_config,
        config.repository_path,
    )
    for candidate in candidates:
        run_context = workspace_module.bind_check_material(
            run_context,
            task_pool_module.build_check_candidate(candidate),
            config.check_commands[candidate.candidate_id],
            config.hidden_material_paths[candidate.candidate_id],
            check_manifest=config.check_manifests.get(candidate.candidate_id),
        )
    certified = tuple(
        task_pool_module.certify_task_candidate(
            candidate,
            config.certification_config,
            config.workspace_config,
            config.runtime_config,
            config.reference_patches[candidate.candidate_id],
            run_context,
        )
        for candidate in candidates
    )
    return certified


def _publish_task_pool(
    config: TaskPoolConfig,
    source_window: tuple[str | None, str | None],
    batch: task_pool_module.CandidateBatch,
    certified: Sequence[task_pool_module.CertificationResult],
) -> TaskPoolRecord:
    accepted_tasks = tuple(
        result.task
        for result in certified
        if result.accepted and result.task is not None
    )
    accepted_checks = tuple(
        result.check
        for result in certified
        if result.accepted and result.check is not None
    )
    metadata = _task_pool_metadata(config, source_window)
    evidence = task_pool_module.certification_evidence_records(certified)
    source_events = task_pool_module.finalize_source_event_records(batch, certified)
    bundle_digest = canonical_digest(
        {
            "repository_id": config.repository_id,
            "tasks": accepted_tasks,
            "checks": accepted_checks,
            "certification_evidence": evidence,
            "source_events": source_events,
            "generator_config_digest": metadata["generator_config_digest"],
            "certification_config_digest": metadata["certification_config_digest"],
            "created_at": metadata["created_at"],
            "source_window_start": metadata["source_window_start"],
            "source_window_end": metadata["source_window_end"],
            "task_pool_id": metadata.get("task_pool_id", ""),
        }
    )
    bundle_dir = Path("task-pools") / bundle_digest
    metadata.update(
        {
            "task_records_ref": (bundle_dir / "tasks.jsonl").as_posix(),
            "check_records_ref": (bundle_dir / "checks.jsonl").as_posix(),
            "certification_evidence_ref": (
                bundle_dir / "certification-evidence.jsonl"
            ).as_posix(),
            "source_event_records_ref": (bundle_dir / "source-events.jsonl").as_posix(),
        }
    )
    task_pool = task_pool_module.freeze_task_pool(
        accepted_tasks,
        accepted_checks,
        certified,
        source_events,
        metadata,
    )
    bundle = task_pool_module.validated_task_pool_bundle(
        task_pool,
        accepted_tasks,
        accepted_checks,
        evidence,
        source_events,
    )
    task_pool_module.publish_task_pool_bundle(bundle, config.artifact_root)
    return task_pool


def train_selector(
    selector_family: str,
    *,
    deployment_origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    expert_selectors: Sequence[SelectorRecord],
    training_selection_ids: Sequence[str],
    result_store: result_store_module.ResultStore,
    artifact_root: Path | None = None,
) -> SelectorRecord:
    if not training_selection_ids:
        raise ValueError("training_selection_ids must not be empty")
    if len(set(training_selection_ids)) != len(training_selection_ids):
        raise ValueError("training_selection_ids must be unique")
    task_pool_bundle = _load_task_pool_bundle(task_pool, artifact_root)
    tasks = task_pool_bundle.tasks
    checks = task_pool_bundle.checks_by_id
    selections, training_origins, feature_snapshots, selector_inputs = (
        _load_training_selection_records(training_selection_ids, result_store)
    )
    matrices, metrics = _load_training_outcome_records(
        training_selection_ids,
        result_store,
    )
    pre_origin_results, training_results = _load_bound_training_results(
        selector_inputs,
        matrices,
        result_store,
    )
    selector = selection_module.train_selector(
        selector_family,
        deployment_origin=deployment_origin,
        task_pool=task_pool,
        tasks=tasks,
        checks=checks,
        training_origins=training_origins,
        feature_snapshots=feature_snapshots,
        selector_inputs=selector_inputs,
        expert_selectors=expert_selectors,
        selections=selections,
        result_matrices=matrices,
        metrics=metrics,
        pre_origin_results=pre_origin_results,
        training_results=training_results,
    )
    _append_origin_record(deployment_origin, result_store)
    for expert in expert_selectors:
        _append_selector_record(expert, result_store)
    return _append_selector_record(selector, result_store)


def select_benchmark(
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    origin_time: datetime,
    budget: selection_module.SelectionBudget,
    selector: SelectorRecord,
    rolling_policy: selection_module.RollingOriginPolicy,
    feature_config: selection_module.FeatureConfig,
    result_store: result_store_module.ResultStore,
    artifact_root: Path | None = None,
    future_window: TimeRange | None = None,
) -> BenchmarkSelectionRecord:
    task_pool_bundle = _load_task_pool_bundle(task_pool, artifact_root)
    tasks = task_pool_bundle.tasks
    checks = task_pool_bundle.checks_by_id
    origin = selection_module.build_rolling_origin(
        task_pool,
        tasks,
        checks,
        origin_time,
        future_window
        or TimeRange(
            start=format_utc_timestamp(origin_time),
            end=format_utc_timestamp(origin_time),
        ),
        rolling_policy,
    )
    selector = _append_selector_record(selector, result_store)
    _append_origin_record(origin, result_store)
    pre_origin_results = _load_pre_origin_results(
        result_store,
        origin,
        agents,
        result_available_after=None,
    )
    snapshot = selection_module.build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        checks,
        pre_origin_results,
        feature_config,
    )
    selector_input = selection_module.build_selector_input(
        origin,
        task_pool,
        snapshot,
        pre_origin_results,
        agents,
        budget,
        feature_config.leakage_policy(origin.as_of_cutoff),
    )
    _append_feature_snapshot_record(snapshot, result_store)
    _append_selector_input_record(selector_input, result_store)
    selection = selection_module.select_with_selector(
        selector_input, snapshot, selector
    )
    return _append_selection_record(selection, result_store)


def evaluate_selector(
    selector: SelectorRecord,
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    evaluation_config: selection_module.SelectorEvaluationConfig,
    rolling_policy: selection_module.RollingOriginPolicy,
    feature_config: selection_module.FeatureConfig,
    result_store: result_store_module.ResultStore,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
    artifact_root: Path | None = None,
) -> tuple[
    tuple[BenchmarkSelectionRecord, ...],
    tuple[EvaluationCellSet, ...],
    tuple[ResultMatrix, ...],
    tuple[MetricRecord, ...],
]:
    return evaluate_selectors(
        (selector,),
        task_pool,
        agents,
        history_window,
        evaluation_config,
        rolling_policy,
        feature_config,
        result_store,
        workspace_config,
        runtime_config,
        scoring_config,
        cache_config,
        join_config,
        run_context,
        artifact_root,
    )


def evaluate_selectors(
    selectors: Sequence[SelectorRecord],
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    evaluation_config: selection_module.SelectorEvaluationConfig,
    rolling_policy: selection_module.RollingOriginPolicy,
    feature_config: selection_module.FeatureConfig,
    result_store: result_store_module.ResultStore,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
    artifact_root: Path | None = None,
) -> tuple[
    tuple[BenchmarkSelectionRecord, ...],
    tuple[EvaluationCellSet, ...],
    tuple[ResultMatrix, ...],
    tuple[MetricRecord, ...],
]:
    selectors = _validated_selector_batch(selectors)
    agent_ids = tuple(agent.agent_id for agent in agents)
    if not agent_ids:
        raise ValueError("agents must not be empty")
    if len(set(agent_ids)) != len(agent_ids):
        raise ValueError("duplicate Agent IDs are not allowed")
    origin_times = _counterfactual_evaluation_origin_times(
        evaluation_config,
        rolling_policy,
    )
    task_pool_bundle = _load_task_pool_bundle(task_pool, artifact_root)
    tasks = task_pool_bundle.tasks
    checks = task_pool_bundle.checks_by_id
    future_window_ends = (
        *(format_utc_timestamp(value) for value in origin_times[1:]),
        history_window.end,
    )
    origins = tuple(
        selection_module.build_rolling_origin(
            task_pool,
            tasks,
            checks,
            origin_time,
            TimeRange(start=format_utc_timestamp(origin_time), end=future_window_end),
            rolling_policy,
            history_window=history_window,
        )
        for origin_time, future_window_end in zip(
            origin_times, future_window_ends, strict=True
        )
    )
    selectors = tuple(
        _append_selector_record(selector, result_store) for selector in selectors
    )
    for origin in origins:
        _append_origin_record(origin, result_store)
    origin_material: dict[str, tuple[FeatureSnapshotRecord, SelectorInput]] = {}
    for origin in origins:
        pre_origin_results = _load_pre_origin_results(
            result_store,
            origin,
            agents,
            result_available_after=history_window.start,
        )
        snapshot = selection_module.build_feature_snapshot(
            origin, task_pool, tasks, checks, pre_origin_results, feature_config
        )
        selector_input = selection_module.build_selector_input(
            origin,
            task_pool,
            snapshot,
            pre_origin_results,
            agents,
            evaluation_config.budget,
            feature_config.leakage_policy(origin.as_of_cutoff),
        )
        _append_feature_snapshot_record(snapshot, result_store)
        _append_selector_input_record(selector_input, result_store)
        origin_material[origin.origin_id] = (snapshot, selector_input)
    frozen_selections = tuple(
        selection_module.select_with_selector(
            origin_material[origin.origin_id][1],
            origin_material[origin.origin_id][0],
            selector,
        )
        for selector in selectors
        for origin in origins
    )
    selections = tuple(
        _append_selection_record(selection, result_store)
        for selection in frozen_selections
    )
    origin_by_id = {origin.origin_id: origin for origin in origins}
    cell_sets = _prepare_evaluation_cell_sets(
        tuple(
            (selection, origin_by_id[selection.origin_id]) for selection in selections
        ),
        task_pool,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        cache_config,
        result_store,
        join_config,
        run_context,
    )
    matrices: list[ResultMatrix] = []
    metrics: list[MetricRecord] = []
    for selection, cell_set in zip(selections, cell_sets, strict=True):
        origin = origin_by_id[selection.origin_id]
        _, selected_matrix, future_matrix, selection_metrics = score_selection(
            selection,
            origin,
            task_pool_bundle,
            agents,
            cell_set,
            result_store,
            join_config,
        )
        matrices.extend((selected_matrix, future_matrix))
        metrics.extend(selection_metrics)
    return selections, tuple(cell_sets), tuple(matrices), tuple(metrics)


def _validated_selector_batch(
    selectors: Sequence[SelectorRecord],
) -> tuple[SelectorRecord, ...]:
    selectors = tuple(selectors)
    if not selectors:
        raise ValueError("selectors must not be empty")
    selector_ids = tuple(selector.selector_id for selector in selectors)
    if len(set(selector_ids)) != len(selector_ids):
        raise ValueError("selector IDs must be unique")
    for selector in selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(
                f"selector record is invalid: {', '.join(validation.errors)}"
            )
        selection_module.ensure_selector_executable(selector)
    return selectors


def _counterfactual_evaluation_origin_times(
    evaluation_config: selection_module.SelectorEvaluationConfig,
    rolling_policy: selection_module.RollingOriginPolicy,
) -> tuple[datetime, ...]:
    if (
        rolling_policy.eligibility_mode != "counterfactual_replay"
        or not rolling_policy.future_holdout_known
    ):
        raise ValueError(
            "selector evaluation requires counterfactual_replay with a "
            "predeclared future holdout; strict_prospective evaluation needs "
            "separately linked future Task Pool evidence"
        )
    try:
        origin_times = tuple(
            parse_utc_timestamp(value) for value in evaluation_config.origin_times
        )
    except ValueError as exc:
        raise ValueError(
            "evaluation origin_times entries must be timezone-aware ISO datetime strings"
        ) from exc
    if not origin_times:
        raise ValueError("evaluation origin_times must not be empty")
    if any(
        current >= following
        for current, following in zip(origin_times, origin_times[1:], strict=False)
    ):
        raise ValueError(
            "evaluation origin_times must be strictly increasing UTC instants"
        )
    return origin_times


def evaluate_prospective_selection(
    selection_id: str,
    selection_task_pool: TaskPoolRecord,
    future_task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    result_store: result_store_module.ResultStore,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
    artifact_root: Path | None = None,
) -> tuple[EvaluationCellSet, ResultMatrix, ResultMatrix, tuple[MetricRecord, ...]]:
    selection, origin, snapshot, pre_origin_results = (
        _load_replayed_prospective_selection(
            selection_id,
            agents,
            result_store,
        )
    )
    selection_tasks, selection_checks = _load_task_pool_records(
        selection_task_pool, artifact_root
    )
    _ensure_selection_origin(
        selection,
        origin,
        selection_task_pool,
        selection_tasks,
        selection_checks,
    )
    selection_module.ensure_feature_snapshot_task_metadata_provenance(
        snapshot,
        origin,
        selection_task_pool,
        selection_tasks,
    )
    _ensure_pre_origin_result_task_check_identities(
        pre_origin_results,
        selection_tasks,
        selection_checks,
    )
    future_tasks, future_checks = _load_task_pool_records(
        future_task_pool, artifact_root
    )
    future_refs, future_censored_refs = (
        selection_module.materialize_prospective_future_cohort(
            selection,
            origin,
            selection_task_pool,
            future_task_pool,
            selection_tasks,
            selection_checks,
            future_tasks,
            future_checks,
        )
    )
    tasks, checks = _merge_task_pool_snapshots(
        selection_tasks,
        selection_checks,
        future_tasks,
        future_checks,
    )
    plan = _EvaluationCellSetPlan(
        selection=selection,
        origin=origin,
        future_task_pool_id=future_task_pool.task_pool_id,
        future_task_pool_digest=future_task_pool.task_pool_digest,
        future_task_check_refs=future_refs,
        future_censored_task_check_refs=future_censored_refs,
        tasks=tasks,
        checks=checks,
    )
    (cell_set,) = _resolve_evaluation_cell_sets(
        (plan,),
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        cache_config,
        result_store,
        join_config,
        run_context,
    )
    return _score_evaluation_cell_set(
        selection,
        origin,
        tasks,
        checks,
        agents,
        cell_set,
        result_store,
        join_config,
    )


def _load_replayed_prospective_selection(
    selection_id: str,
    agents: Sequence[AgentRecord],
    result_store: result_store_module.ResultStore,
) -> tuple[
    BenchmarkSelectionRecord,
    RollingOriginRecord,
    FeatureSnapshotRecord,
    tuple[ResultRecord, ...],
]:
    (selection,) = _load_records_by_ids(
        _selection_log_path(result_store),
        BenchmarkSelectionRecord,
        "selection_id",
        (selection_id,),
        "prospective Selection",
    )
    (origin,) = _load_records_by_ids(
        _origin_log_path(result_store),
        RollingOriginRecord,
        "origin_id",
        (selection.origin_id,),
        "prospective Origin",
    )
    (selector_input,) = _load_records_by_ids(
        _selector_input_log_path(result_store),
        SelectorInput,
        "selector_input_digest",
        (selection.selection_input_digest,),
        "prospective SelectorInput",
    )
    (selector,) = _load_records_by_ids(
        _selector_log_path(result_store),
        SelectorRecord,
        "selector_id",
        (selection.selector_id,),
        "prospective Selector",
    )
    (snapshot,) = _load_records_by_ids(
        _feature_snapshot_log_path(result_store),
        FeatureSnapshotRecord,
        "feature_snapshot_id",
        (selection.feature_snapshot_id,),
        "prospective FeatureSnapshot",
    )
    origin_validation = validate_rolling_origin(origin)
    if not origin_validation.ok:
        raise ValueError(
            "prospective Origin is invalid: " + ", ".join(origin_validation.errors)
        )
    if (
        selection.origin_id != origin.origin_id
        or selection.eligibility_mode != "strict_prospective"
        or origin.eligibility_mode != "strict_prospective"
    ):
        raise ValueError("prospective Selection does not match a strict Origin")
    if tuple(agent.agent_id for agent in agents) != selector_input.agent_ids:
        raise ValueError("prospective Agent set does not match frozen SelectorInput")
    if tuple(canonical_digest(agent) for agent in agents) != (
        selector_input.agent_record_digests
    ):
        raise ValueError(
            "prospective Agent identities do not match frozen SelectorInput"
        )
    selection_module.ensure_selection_replay(
        selector_input,
        snapshot,
        selector,
        selection,
    )
    pre_origin_results = (
        ()
        if not selector_input.pre_origin_result_ids
        else tuple(
            result_store_module.load_results(
                result_store,
                result_store_module.ResultQuery(
                    result_ids=selector_input.pre_origin_result_ids,
                ),
            )
        )
    )
    resolved_pre_origin_results = (
        selection_module.ensure_selector_input_result_evidence(
            selector_input, origin, snapshot, pre_origin_results
        )
    )
    return selection, origin, snapshot, resolved_pre_origin_results


def _ensure_pre_origin_result_task_check_identities(
    results: Sequence[ResultRecord],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    task_by_id = {task.task_id: task for task in tasks}
    for result in results:
        task = task_by_id.get(result.task_id)
        check = checks.get(result.check_id)
        if (
            task is None
            or check is None
            or check.task_id != task.task_id
            or check.check_id not in task.check_ids
        ):
            raise ValueError(
                "pre_origin_results include identity outside selection Task Pool records"
            )
        mismatched = cache_identity_task_check_mismatches(
            result.cache_identity,
            task,
            check,
        )
        if mismatched:
            raise ValueError(
                "pre_origin_results include cache identity that does not match "
                "selection Task/Check records: " + ", ".join(mismatched)
            )


def run_agents(
    task_pool_bundle: task_pool_module.TaskPoolBundle,
    task_check_refs: Sequence[TaskCheckRef],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    result_store: result_store_module.ResultStore,
    run_context: workspace_module.WorkspaceRunContext,
) -> tuple[ResultRecord, ...]:
    bundle = _validated_task_pool_bundle(task_pool_bundle)
    task_pool = bundle.task_pool
    tasks = bundle.tasks
    checks = bundle.checks_by_id
    _ensure_refs_in_task_pool(task_check_refs, task_pool)
    cells: list[ResultCellRef] = []
    for ref in task_check_refs:
        task = _task_for_ref(ref, tasks)
        check = _check_for_ref(ref, task, checks)
        for agent in agents:
            identity = result_store_module.compute_result_cache_identity(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
            )
            cells.append(_missing_cell(agent, task, check, identity.identity_digest))
    return _run_agent_cells(
        cells,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        result_store,
        run_context,
    )


def fill_results(
    selection: BenchmarkSelectionRecord,
    task_pool_bundle: task_pool_module.TaskPoolBundle,
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    result_store: result_store_module.ResultStore,
    run_context: workspace_module.WorkspaceRunContext,
) -> tuple[ResultRecord, ...]:
    bundle = _validated_task_pool_bundle(task_pool_bundle)
    task_pool = bundle.task_pool
    tasks = bundle.tasks
    checks = bundle.checks_by_id
    _ensure_selection_matches_task_pool(selection, task_pool)
    with result_store_module.open_result_store_session(result_store) as session:
        missing = result_store_module.find_missing_results(
            selection.selected_task_check_refs,
            tasks,
            checks,
            agents,
            workspace_config,
            runtime_config,
            result_store,
            cache_config,
            session=session,
        )
        executed = _run_agent_cells(
            missing,
            tasks,
            checks,
            agents,
            workspace_config,
            runtime_config,
            scoring_config,
            result_store,
            run_context,
            result_session=session,
        )
        repriced = result_store_module.reprice_cached_results(
            selection.selected_task_check_refs,
            tasks,
            checks,
            agents,
            workspace_config,
            runtime_config,
            result_store,
            cache_config,
            scoring_config,
            session=session,
        )
    return (*executed, *repriced)


def prepare_evaluation_cells(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    task_pool_bundle: task_pool_module.TaskPoolBundle,
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
) -> EvaluationCellSet:
    bundle = _validated_task_pool_bundle(task_pool_bundle)
    return _prepare_evaluation_cell_sets(
        ((selection, origin),),
        bundle.task_pool,
        bundle.tasks,
        bundle.checks_by_id,
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        cache_config,
        result_store,
        join_config,
        run_context,
    )[0]


def _prepare_evaluation_cell_sets(
    selection_origins: Sequence[tuple[BenchmarkSelectionRecord, RollingOriginRecord]],
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
) -> tuple[EvaluationCellSet, ...]:
    _validate_task_pool_members(task_pool, tasks, checks)
    plans: list[_EvaluationCellSetPlan] = []
    for selection, origin in selection_origins:
        _ensure_selection_origin(selection, origin, task_pool, tasks, checks)
        plans.append(
            _EvaluationCellSetPlan(
                selection=selection,
                origin=origin,
                future_task_pool_id=task_pool.task_pool_id,
                future_task_pool_digest=task_pool.task_pool_digest,
                future_task_check_refs=origin.future_holdout_task_check_refs,
                future_censored_task_check_refs=origin.future_censored_task_check_refs,
                tasks=tuple(tasks),
                checks=checks,
            )
        )
    return _resolve_evaluation_cell_sets(
        plans,
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        cache_config,
        result_store,
        join_config,
        run_context,
    )


def _resolve_evaluation_cell_sets(
    plans: Sequence[_EvaluationCellSetPlan],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
    run_context: workspace_module.WorkspaceRunContext,
) -> tuple[EvaluationCellSet, ...]:
    if not plans:
        return ()
    agent_ids = tuple(agent.agent_id for agent in agents)
    if not agent_ids:
        raise ValueError("agents must not be empty")
    if len(set(agent_ids)) != len(agent_ids):
        raise ValueError("duplicate Agent IDs are not allowed")

    cell_set_ids, plan_by_cell_set_id, requested_refs_by_cell_set_id = (
        _evaluation_cell_set_plan_index(plans, join_config, agents)
    )

    existing_by_id = _load_existing_evaluation_cell_sets(result_store)
    resolved_cell_sets: dict[str, EvaluationCellSet] = {}
    pending_ids: list[str] = []
    for cell_set_id, requested_refs in requested_refs_by_cell_set_id.items():
        existing = existing_by_id.get(cell_set_id)
        if existing is None:
            pending_ids.append(cell_set_id)
            continue
        _validate_reusable_evaluation_cell_set(
            existing,
            plan_by_cell_set_id[cell_set_id],
            agents,
            workspace_config,
            runtime_config,
            join_config,
        )
        resolved_cell_sets[cell_set_id] = existing

    _ensure_evaluation_cell_set_result_bindings(
        tuple(resolved_cell_sets.values()),
        result_store,
    )
    union_refs, union_tasks, union_checks = _pending_evaluation_union(
        pending_ids,
        requested_refs_by_cell_set_id,
        plan_by_cell_set_id,
    )
    union_cells: tuple[ResultCellRef, ...] = ()
    if union_refs:
        with result_store_module.open_result_store_session(result_store) as session:
            missing = result_store_module.find_missing_results(
                union_refs,
                union_tasks,
                union_checks,
                agents,
                workspace_config,
                runtime_config,
                result_store,
                cache_config,
                session=session,
            )
            _run_agent_cells(
                missing,
                union_tasks,
                union_checks,
                agents,
                workspace_config,
                runtime_config,
                scoring_config,
                result_store,
                run_context,
                result_session=session,
            )
            result_store_module.reprice_cached_results(
                union_refs,
                union_tasks,
                union_checks,
                agents,
                workspace_config,
                runtime_config,
                result_store,
                cache_config,
                scoring_config,
                session=session,
            )
            union_cells = tuple(
                result_store_module.resolve_result_cells(
                    union_refs,
                    union_tasks,
                    union_checks,
                    agents,
                    workspace_config,
                    runtime_config,
                    result_store,
                    cache_config,
                    scoring_config,
                    session=session,
                )
            )

    union_cell_by_key = _result_cell_index(union_cells)
    new_cell_sets = tuple(
        _build_evaluation_cell_set(
            plan_by_cell_set_id[cell_set_id],
            union_cell_by_key,
            agents,
            join_config,
        )
        for cell_set_id in pending_ids
    )

    for cell_set in new_cell_sets:
        _append_evaluation_cell_set_record(cell_set, result_store)
        resolved_cell_sets[cell_set.cell_set_id] = cell_set
    return tuple(resolved_cell_sets[cell_set_id] for cell_set_id in cell_set_ids)


def _evaluation_cell_set_plan_index(
    plans: Sequence[_EvaluationCellSetPlan],
    join_config: result_store_module.ResultJoinConfig,
    agents: Sequence[AgentRecord],
) -> tuple[
    tuple[str, ...],
    Mapping[str, _EvaluationCellSetPlan],
    Mapping[str, tuple[TaskCheckRef, ...]],
]:
    requested_refs_by_cell_set_id: dict[str, tuple[TaskCheckRef, ...]] = {}
    plan_by_cell_set_id: dict[str, _EvaluationCellSetPlan] = {}
    cell_set_ids: list[str] = []
    for plan in plans:
        requested_refs = _plan_requested_refs(plan)
        cell_set_id = _evaluation_cell_set_id(plan, join_config, agents)
        if cell_set_id in requested_refs_by_cell_set_id:
            raise ValueError("duplicate evaluation cell-set identity")
        requested_refs_by_cell_set_id[cell_set_id] = requested_refs
        plan_by_cell_set_id[cell_set_id] = plan
        cell_set_ids.append(cell_set_id)
    return (
        tuple(cell_set_ids),
        plan_by_cell_set_id,
        requested_refs_by_cell_set_id,
    )


def _pending_evaluation_union(
    pending_ids: Sequence[str],
    requested_refs_by_cell_set_id: Mapping[str, tuple[TaskCheckRef, ...]],
    plan_by_cell_set_id: Mapping[str, _EvaluationCellSetPlan],
) -> tuple[tuple[TaskCheckRef, ...], tuple[TaskRecord, ...], Mapping[str, CheckRecord]]:
    union_refs = _unique_refs(
        tuple(
            ref
            for cell_set_id in pending_ids
            for ref in requested_refs_by_cell_set_id[cell_set_id]
        )
    )
    union_tasks, union_checks = _evaluation_plan_records(
        tuple(plan_by_cell_set_id[cell_set_id] for cell_set_id in pending_ids)
    )
    return union_refs, union_tasks, union_checks


def _result_cell_index(
    cells: Sequence[ResultCellRef],
) -> Mapping[tuple[str, str, str], ResultCellRef]:
    cell_by_key: dict[tuple[str, str, str], ResultCellRef] = {}
    for cell in cells:
        key = (cell.agent_id, cell.task_id, cell.check_id)
        if key in cell_by_key:
            raise ValueError("resolved Result cells contain duplicate identities")
        cell_by_key[key] = cell
    return cell_by_key


def _build_evaluation_cell_set(
    plan: _EvaluationCellSetPlan,
    cell_by_key: Mapping[tuple[str, str, str], ResultCellRef],
    agents: Sequence[AgentRecord],
    join_config: result_store_module.ResultJoinConfig,
) -> EvaluationCellSet:
    selection = plan.selection
    origin = plan.origin
    cells = tuple(
        cell_by_key[(agent.agent_id, ref.task_id, ref.check_id)]
        for ref in _plan_requested_refs(plan)
        for agent in agents
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id=_evaluation_cell_set_id(plan, join_config, agents),
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=selection.selected_task_check_refs,
            future_task_check_refs=plan.future_task_check_refs,
            future_censored_task_check_refs=plan.future_censored_task_check_refs,
            future_task_pool_id=plan.future_task_pool_id,
            future_task_pool_digest=plan.future_task_pool_digest,
            cells=cells,
            abstention_reason=_cell_set_abstention(cells, join_config),
            cell_set_digest="",
        )
    )
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise ValueError(
            f"evaluation cell set is invalid: {', '.join(validation.errors)}"
        )
    return cell_set


def _evaluation_cell_set_id(
    plan: _EvaluationCellSetPlan,
    join_config: result_store_module.ResultJoinConfig,
    agents: Sequence[AgentRecord],
) -> str:
    requested_refs = _plan_requested_refs(plan)
    return f"cell_set_{canonical_digest((plan.selection.selection_digest, plan.origin.origin_id, plan.future_task_pool_digest, join_config.join_policy_digest, tuple(_ref_key(ref) for ref in requested_refs), tuple(_ref_key(ref) for ref in plan.future_censored_task_check_refs), tuple(agent.agent_id for agent in agents)))}"


def _plan_requested_refs(
    plan: _EvaluationCellSetPlan,
) -> tuple[TaskCheckRef, ...]:
    return _unique_refs(
        (*plan.selection.selected_task_check_refs, *plan.future_task_check_refs)
    )


def _evaluation_plan_records(
    plans: Sequence[_EvaluationCellSetPlan],
) -> tuple[tuple[TaskRecord, ...], Mapping[str, CheckRecord]]:
    task_by_id: dict[str, TaskRecord] = {}
    check_by_id: dict[str, CheckRecord] = {}
    ordered_task_ids: list[str] = []
    for plan in plans:
        for ref in _plan_requested_refs(plan):
            task = _task_for_ref(ref, plan.tasks)
            check = _check_for_ref(ref, task, plan.checks)
            existing_task = task_by_id.get(task.task_id)
            if existing_task is not None and existing_task != task:
                raise ValueError("evaluation plans disagree on a Task record")
            if existing_task is None:
                task_by_id[task.task_id] = task
                ordered_task_ids.append(task.task_id)
            existing_check = check_by_id.get(check.check_id)
            if existing_check is not None and existing_check != check:
                raise ValueError("evaluation plans disagree on a Check record")
            check_by_id[check.check_id] = check
    return tuple(task_by_id[task_id] for task_id in ordered_task_ids), check_by_id


def _merge_task_pool_snapshots(
    selection_tasks: Sequence[TaskRecord],
    selection_checks: Mapping[str, CheckRecord],
    future_tasks: Sequence[TaskRecord],
    future_checks: Mapping[str, CheckRecord],
) -> tuple[tuple[TaskRecord, ...], Mapping[str, CheckRecord]]:
    task_by_id = {task.task_id: task for task in selection_tasks}
    ordered_task_ids = [task.task_id for task in selection_tasks]
    for task in future_tasks:
        existing = task_by_id.get(task.task_id)
        if existing is not None and existing != task:
            raise ValueError("Task record changed across Task Pool snapshots")
        if existing is None:
            ordered_task_ids.append(task.task_id)
        task_by_id[task.task_id] = task
    checks = dict(selection_checks)
    for check_id, check in future_checks.items():
        existing = checks.get(check_id)
        if existing is not None and existing != check:
            raise ValueError("Check record changed across Task Pool snapshots")
        checks[check_id] = check
    return tuple(task_by_id[task_id] for task_id in ordered_task_ids), checks


def _load_existing_evaluation_cell_sets(
    result_store: result_store_module.ResultStore,
) -> Mapping[str, EvaluationCellSet]:
    path = _evaluation_cell_set_log_path(result_store)
    if not path.exists():
        return {}
    by_id: dict[str, EvaluationCellSet] = {}
    for cell_set in load_jsonl_records(path, EvaluationCellSet):
        if cell_set.cell_set_id in by_id:
            raise ValueError(
                "evaluation cell-set log contains duplicate cell_set_id: "
                + cell_set.cell_set_id
            )
        by_id[cell_set.cell_set_id] = cell_set
    return by_id


def _validate_reusable_evaluation_cell_set(
    cell_set: EvaluationCellSet,
    plan: _EvaluationCellSetPlan,
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    join_config: result_store_module.ResultJoinConfig,
) -> None:
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise ValueError(
            "persisted evaluation cell set is invalid: " + ", ".join(validation.errors)
        )
    selection = plan.selection
    origin = plan.origin
    requested_refs = _plan_requested_refs(plan)
    if (
        cell_set.origin_id != origin.origin_id
        or cell_set.selection_id != selection.selection_id
        or cell_set.selected_task_check_refs != selection.selected_task_check_refs
        or cell_set.future_task_check_refs != plan.future_task_check_refs
        or cell_set.future_censored_task_check_refs
        != plan.future_censored_task_check_refs
        or cell_set.future_task_pool_id != plan.future_task_pool_id
        or cell_set.future_task_pool_digest != plan.future_task_pool_digest
    ):
        raise ValueError("persisted evaluation cell set provenance has changed")
    expected_cells = []
    for ref in requested_refs:
        task = _task_for_ref(ref, plan.tasks)
        check = _check_for_ref(ref, task, plan.checks)
        for agent in agents:
            identity = result_store_module.compute_result_cache_identity(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
            )
            expected_cells.append(
                (agent.agent_id, ref.task_id, ref.check_id, identity.identity_digest)
            )
    actual_cells = tuple(
        (cell.agent_id, cell.task_id, cell.check_id, cell.required_identity_digest)
        for cell in cell_set.cells
    )
    if actual_cells != tuple(expected_cells):
        raise ValueError("persisted evaluation cell set execution identity has changed")
    if cell_set.abstention_reason != _cell_set_abstention(cell_set.cells, join_config):
        raise ValueError("persisted evaluation cell set abstention state has changed")


def score_selection(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    task_pool_bundle: task_pool_module.TaskPoolBundle,
    agents: Sequence[AgentRecord],
    evaluation_cells: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
) -> tuple[EvaluationCellSet, ResultMatrix, ResultMatrix, tuple[MetricRecord, ...]]:
    bundle = _validated_task_pool_bundle(task_pool_bundle)
    task_pool = bundle.task_pool
    tasks = bundle.tasks
    checks = bundle.checks_by_id
    _ensure_selection_origin(selection, origin, task_pool, tasks, checks)
    if (
        evaluation_cells.future_task_pool_id != task_pool.task_pool_id
        or evaluation_cells.future_task_pool_digest != task_pool.task_pool_digest
        or evaluation_cells.future_task_check_refs
        != origin.future_holdout_task_check_refs
        or evaluation_cells.future_censored_task_check_refs
        != origin.future_censored_task_check_refs
    ):
        raise ValueError("evaluation cell set does not match rolling-origin Task Pool")
    return _score_evaluation_cell_set(
        selection,
        origin,
        tasks,
        checks,
        agents,
        evaluation_cells,
        result_store,
        join_config,
    )


def _score_evaluation_cell_set(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    evaluation_cells: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
) -> tuple[EvaluationCellSet, ResultMatrix, ResultMatrix, tuple[MetricRecord, ...]]:
    results = _results_bound_to_evaluation_cells(evaluation_cells, result_store)
    selected_matrix = result_store_module.build_result_matrix(
        evaluation_cells,
        selection.selected_task_check_refs,
        tasks,
        checks,
        agents,
        results,
        "selected",
        join_config,
    )
    future_matrix = result_store_module.build_result_matrix(
        evaluation_cells,
        evaluation_cells.future_task_check_refs,
        tasks,
        checks,
        agents,
        results,
        "future_holdout",
        join_config,
    )
    metrics = tuple(
        selection_module.evaluate_selection(
            selection,
            origin,
            evaluation_cells,
            selected_matrix,
            future_matrix,
        )
    )
    _append_result_matrix_records((selected_matrix, future_matrix), result_store)
    metrics = _append_metric_records(metrics, result_store)
    return evaluation_cells, selected_matrix, future_matrix, metrics


def write_report(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    results: Sequence[ResultRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    report_config: ReportConfig,
    *,
    origins: Sequence[RollingOriginRecord] = (),
    feature_snapshots: Sequence[FeatureSnapshotRecord] = (),
    selector_inputs: Sequence[SelectorInput] = (),
    selectors: Sequence[SelectorRecord] = (),
    future_task_pools: Sequence[TaskPoolRecord] = (),
) -> Mapping[str, object]:
    sections = (
        reporting_module.build_task_pool_report(
            task_pool,
            artifact_root=report_config.artifact_root,
        ),
        reporting_module.build_result_report(results, report_config.agents),
        reporting_module.build_selector_report(
            selections,
            cell_sets,
            result_matrices,
            metrics,
            origins=origins,
            feature_snapshots=feature_snapshots,
            selector_inputs=selector_inputs,
            selectors=selectors,
            agents=report_config.agents,
            results=results,
            task_pool=task_pool,
            future_task_pools=future_task_pools,
            artifact_root=report_config.artifact_root,
        ),
        reporting_module.build_claim_boundary(
            task_pool,
            selections,
            cell_sets,
            result_matrices,
            metrics,
            report_config.claim_config,
            results=results,
            artifact_root=report_config.artifact_root,
            origins=origins,
            feature_snapshots=feature_snapshots,
            selector_inputs=selector_inputs,
            selectors=selectors,
            agents=report_config.agents,
            future_task_pools=future_task_pools,
        ),
    )
    markdown_path = report_config.output_dir / report_config.markdown_filename
    json_path = report_config.output_dir / report_config.json_filename
    reporting_module.write_report(
        sections,
        markdown_path,
        artifact_root=report_config.artifact_root,
    )
    reporting_module.write_report(
        sections,
        json_path,
        artifact_root=report_config.artifact_root,
    )
    return {
        "report_paths": {"markdown": str(markdown_path), "json": str(json_path)},
        "section_ids": tuple(section.section_id for section in sections),
        "source_digests": {
            section.section_id: section.source_digests for section in sections
        },
    }


def _candidate_batch(
    config: TaskPoolConfig,
) -> task_pool_module.CandidateBatch:
    if config.import_path is not None and (
        config.time_range is not None or config.task_source_config is not None
    ):
        raise ValueError(
            "TaskPoolConfig import_path and history generation inputs are mutually exclusive"
        )
    if config.import_path is not None:
        return task_pool_module.import_task_candidates(
            config.import_path,
            config.import_config,
        )
    if config.time_range is None or config.task_source_config is None:
        raise ValueError(
            "TaskPoolConfig requires either import_path or time_range with task_source_config"
        )
    return task_pool_module.filter_history_candidates(
        config.repository_id,
        config.time_range,
        config.task_source_config,
    )


def _task_pool_metadata(
    config: TaskPoolConfig,
    source_window: tuple[str | None, str | None],
) -> dict[str, object]:
    metadata = dict(config.metadata)
    metadata["repository_id"] = config.repository_id
    metadata["generator_config_digest"] = _generator_config_digest(config)
    metadata["certification_config_digest"] = canonical_digest(
        config.certification_config
    )
    metadata["source_window_start"], metadata["source_window_end"] = source_window
    metadata.setdefault("created_at", _now())
    return metadata


def _canonical_source_window(
    time_range: TimeRange | None,
) -> tuple[str | None, str | None]:
    if time_range is None:
        return None, None
    start = format_utc_timestamp(parse_utc_timestamp(time_range.start))
    end = format_utc_timestamp(parse_utc_timestamp(time_range.end))
    if parse_utc_timestamp(start) > parse_utc_timestamp(end):
        raise ValueError("Task Pool source window start must not be after end")
    return start, end


def _generator_config_digest(config: TaskPoolConfig) -> str:
    if config.import_path is not None:
        return canonical_digest(
            {
                "mode": "import",
                "source_family": config.import_config.source_family,
            }
        )
    if config.task_source_config is None:
        raise ValueError("task_source_config is required for source-event generation")
    return canonical_digest(
        {
            "mode": "source_events",
            "source_family": config.task_source_config.source_family,
        }
    )


def _load_task_pool_records(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None = None,
) -> tuple[tuple[TaskRecord, ...], Mapping[str, CheckRecord]]:
    bundle = _load_task_pool_bundle(task_pool, artifact_root)
    return bundle.tasks, bundle.checks_by_id


def _load_task_pool_bundle(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None = None,
) -> task_pool_module.TaskPoolBundle:
    refs = (
        task_pool.task_records_ref,
        task_pool.check_records_ref,
        task_pool.certification_evidence_ref,
        task_pool.source_event_records_ref,
    )
    if artifact_root is None:
        if not all(
            Path(ref[5:] if ref.startswith("path:") else ref).is_absolute()
            for ref in refs
        ):
            raise ValueError("artifact_root is required for relative Task Pool refs")
        artifact_root = Path("/")
    bundle = task_pool_module.load_validated_task_pool_bundle(
        task_pool,
        artifact_root,
    )
    return bundle


def _load_training_selection_records(
    training_selection_ids: Sequence[str],
    result_store: result_store_module.ResultStore,
) -> tuple[
    tuple[BenchmarkSelectionRecord, ...],
    tuple[RollingOriginRecord, ...],
    tuple[FeatureSnapshotRecord, ...],
    tuple[SelectorInput, ...],
]:
    selections = _load_records_by_ids(
        _selection_log_path(result_store),
        BenchmarkSelectionRecord,
        "selection_id",
        training_selection_ids,
        "training selections",
    )
    origin_ids = tuple(dict.fromkeys(selection.origin_id for selection in selections))
    training_origins = _load_records_by_ids(
        _origin_log_path(result_store),
        RollingOriginRecord,
        "origin_id",
        origin_ids,
        "training origins",
    )
    feature_snapshot_ids = tuple(
        dict.fromkeys(selection.feature_snapshot_id for selection in selections)
    )
    feature_snapshots = _load_records_by_ids(
        _feature_snapshot_log_path(result_store),
        FeatureSnapshotRecord,
        "feature_snapshot_id",
        feature_snapshot_ids,
        "training feature snapshots",
    )
    selector_input_digests = tuple(
        dict.fromkeys(selection.selection_input_digest for selection in selections)
    )
    selector_inputs = _load_records_by_ids(
        _selector_input_log_path(result_store),
        SelectorInput,
        "selector_input_digest",
        selector_input_digests,
        "training selector inputs",
    )
    return selections, training_origins, feature_snapshots, selector_inputs


def _load_training_outcome_records(
    training_selection_ids: Sequence[str],
    result_store: result_store_module.ResultStore,
) -> tuple[tuple[ResultMatrix, ...], tuple[MetricRecord, ...]]:
    selection_id_set = set(training_selection_ids)
    matrices = tuple(
        matrix
        for matrix in _load_record_log(
            _result_matrix_log_path(result_store),
            ResultMatrix,
            "training result matrices",
        )
        if matrix.selection_id in selection_id_set
    )
    metrics = tuple(
        metric
        for metric in _load_record_log(
            _metric_log_path(result_store),
            MetricRecord,
            "training metrics",
        )
        if metric.selection_id in selection_id_set
        and metric.metric_name == "future_pass_rate_mae"
    )
    return matrices, metrics


def _load_bound_training_results(
    selector_inputs: Sequence[SelectorInput],
    matrices: Sequence[ResultMatrix],
    result_store: result_store_module.ResultStore,
) -> tuple[tuple[ResultRecord, ...], tuple[ResultRecord, ...]]:
    training_bindings = {
        (cell.result_id, cell.result_digest)
        for matrix in matrices
        for cell in matrix.cells
        if cell.result_id is not None and cell.result_digest is not None
    }
    pre_origin_bindings = {
        binding
        for selector_input in selector_inputs
        for binding in zip(
            selector_input.pre_origin_result_ids,
            selector_input.pre_origin_result_digests,
            strict=True,
        )
    }
    all_bindings = training_bindings | pre_origin_bindings
    result_ids = tuple(sorted({result_id for result_id, _ in all_bindings}))
    loaded_results = (
        ()
        if not result_ids
        else result_store_module.load_results(
            result_store,
            result_store_module.ResultQuery(result_ids=result_ids),
        )
    )
    pre_origin_results = tuple(
        result
        for result in loaded_results
        if (result.result_id, result.result_digest) in pre_origin_bindings
    )
    training_results = tuple(
        result
        for result in loaded_results
        if (result.result_id, result.result_digest) in training_bindings
    )
    return pre_origin_results, training_results


def _load_record_log(
    path: Path,
    record_type: type[_RecordT],
    label: str,
) -> tuple[_RecordT, ...]:
    if not path.exists():
        raise ValueError(f"{label} log does not exist: {path}")
    return tuple(load_jsonl_records(path, record_type))


def _load_records_by_ids(
    path: Path,
    record_type: type[_RecordT],
    id_attr: str,
    required_ids: Sequence[str],
    label: str,
) -> tuple[_RecordT, ...]:
    records = _load_record_log(path, record_type, label)
    records_by_id: dict[str, _RecordT] = {}
    for record in records:
        record_id = cast(str, getattr(record, id_attr))
        if record_id in records_by_id:
            raise ValueError(f"{label} log contains duplicate {id_attr}: {record_id}")
        records_by_id[record_id] = record
    missing = tuple(
        record_id for record_id in required_ids if record_id not in records_by_id
    )
    if missing:
        raise ValueError(f"{label} are missing: {', '.join(missing)}")
    return tuple(records_by_id[record_id] for record_id in required_ids)


def _run_agent_cells(
    cells: Sequence[ResultCellRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    result_store: result_store_module.ResultStore,
    run_context: workspace_module.WorkspaceRunContext,
    *,
    result_session: result_store_module.ResultStoreSession | None = None,
) -> tuple[ResultRecord, ...]:
    result_store_module.validate_scoring_config(scoring_config)
    runtime_validation = validate_runtime_config(runtime_config)
    if not runtime_validation.ok:
        raise ValueError(
            f"runtime_config is invalid: {', '.join(runtime_validation.errors)}"
        )
    agent_ids = tuple(agent.agent_id for agent in agents)
    if len(set(agent_ids)) != len(agent_ids):
        raise ValueError("duplicate Agent IDs are not allowed")
    cell_keys = tuple((cell.agent_id, cell.task_id, cell.check_id) for cell in cells)
    if len(set(cell_keys)) != len(cell_keys):
        raise ValueError("duplicate Agent/task/check run cells are not allowed")
    if not cells:
        return ()
    agent_by_id = {agent.agent_id: agent for agent in agents}
    plans = []
    for cell in cells:
        if (
            cell.cell_state != "missing"
            or cell.result_id is not None
            or cell.result_digest is not None
            or cell.exclusion_reason is not None
            or cell.outcome is not None
        ):
            raise ValueError("run cells must be unbound missing cells")
        task = _task_for_ref(TaskCheckRef(cell.task_id, cell.check_id), tasks)
        check = _check_for_ref(TaskCheckRef(cell.task_id, cell.check_id), task, checks)
        task_validation = validate_task(task)
        if not task_validation.ok:
            raise ValueError(f"task is invalid: {', '.join(task_validation.errors)}")
        check_validation = validate_check(check)
        if not check_validation.ok:
            raise ValueError(f"check is invalid: {', '.join(check_validation.errors)}")
        agent = agent_by_id.get(cell.agent_id)
        if agent is None:
            raise ValueError(f"agent is missing for cell {cell.agent_id}")
        identity = result_store_module.compute_result_cache_identity(
            task,
            check,
            agent,
            workspace_config,
            runtime_config,
        )
        if identity.identity_digest != cell.required_identity_digest:
            raise ValueError(
                "missing cell required identity does not match current run config"
            )
        plans.append((task, check, agent, identity))
    workspace_module.preflight_run_bindings(
        run_context,
        tuple((task, check, agent) for task, check, agent, _ in plans),
        workspace_config,
        runtime_config,
    )
    if result_session is None:
        with result_store_module.open_result_store_session(
            result_store
        ) as opened_session:
            return _execute_agent_plans(
                plans,
                workspace_config,
                runtime_config,
                scoring_config,
                opened_session,
                run_context,
            )
    if result_session.store.path.resolve() != result_store.path.resolve():
        raise ValueError("ResultStoreSession does not match ResultStore")
    return _execute_agent_plans(
        plans,
        workspace_config,
        runtime_config,
        scoring_config,
        result_session,
        run_context,
    )


def _execute_agent_plans(
    plans: Sequence[tuple[TaskRecord, CheckRecord, AgentRecord, ResultCacheIdentity]],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    result_session: result_store_module.ResultStoreSession,
    run_context: workspace_module.WorkspaceRunContext,
) -> tuple[ResultRecord, ...]:
    results: list[ResultRecord] = []
    for task, check, agent, identity in plans:
        workspace_run = workspace_module.run_agent_on_task(
            task, check, agent, workspace_config, runtime_config, run_context
        )
        result = result_store_module.build_result_record(
            task, check, agent, workspace_run, identity, scoring_config
        )
        results.append(result_session.append(result))
    return tuple(results)


def _load_results_for_refs(
    result_store: result_store_module.ResultStore,
    refs: Sequence[TaskCheckRef],
    agents: Sequence[AgentRecord],
    *,
    result_available_after: str | None,
    result_available_before: str,
) -> tuple[ResultRecord, ...]:
    task_ids, check_ids = _refs_query_parts(refs)
    if not task_ids or not agents:
        return ()
    allowed_refs = {_ref_key(ref) for ref in refs}
    loaded = result_store_module.load_results(
        result_store,
        result_store_module.ResultQuery(
            task_ids=task_ids,
            check_ids=check_ids,
            agent_ids=tuple(agent.agent_id for agent in agents),
            result_available_after=result_available_after,
            result_available_before=result_available_before,
        ),
    )
    distinct_executions: list[ResultRecord] = []
    seen_execution_digests: set[str] = set()
    for result in loaded:
        if (result.task_id, result.check_id) not in allowed_refs:
            continue
        execution_digest = result_store_module.result_execution_digest(result)
        if execution_digest in seen_execution_digests:
            continue
        seen_execution_digests.add(execution_digest)
        distinct_executions.append(result)
    return tuple(distinct_executions)


def _load_pre_origin_results(
    result_store: result_store_module.ResultStore,
    origin: RollingOriginRecord,
    agents: Sequence[AgentRecord],
    *,
    result_available_after: str | None,
) -> tuple[ResultRecord, ...]:
    return _load_results_for_refs(
        result_store,
        origin.history_task_check_refs,
        agents,
        result_available_after=result_available_after,
        result_available_before=origin.as_of_cutoff,
    )


def _refs_query_parts(
    refs: Sequence[TaskCheckRef],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(dict.fromkeys(ref.task_id for ref in refs)),
        tuple(dict.fromkeys(ref.check_id for ref in refs)),
    )


def _append_selection_record(
    selection: BenchmarkSelectionRecord, result_store: result_store_module.ResultStore
) -> BenchmarkSelectionRecord:
    validation = validate_benchmark_selection(selection)
    if not validation.ok:
        raise ValueError(f"selection record is invalid: {', '.join(validation.errors)}")
    return _append_record_once(
        _selection_log_path(result_store),
        selection,
        BenchmarkSelectionRecord,
        "selection_id",
        "selection_digest",
        observation_fields=("created_at",),
    )


def _append_selector_record(
    selector: SelectorRecord, result_store: result_store_module.ResultStore
) -> SelectorRecord:
    validation = validate_selector(selector)
    if not validation.ok:
        raise ValueError(f"selector record is invalid: {', '.join(validation.errors)}")
    return _append_record_once(
        _selector_log_path(result_store),
        selector,
        SelectorRecord,
        "selector_id",
        "selector_digest",
        observation_fields=("created_at",),
    )


def _append_origin_record(
    origin: RollingOriginRecord, result_store: result_store_module.ResultStore
) -> None:
    validation = validate_rolling_origin(origin)
    if not validation.ok:
        raise ValueError(f"origin record is invalid: {', '.join(validation.errors)}")
    _append_record_once(
        _origin_log_path(result_store),
        origin,
        RollingOriginRecord,
        "origin_id",
        "origin_digest",
    )


def _append_feature_snapshot_record(
    snapshot: FeatureSnapshotRecord,
    result_store: result_store_module.ResultStore,
) -> None:
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        raise ValueError(
            f"feature snapshot record is invalid: {', '.join(validation.errors)}"
        )
    _append_record_once(
        _feature_snapshot_log_path(result_store),
        snapshot,
        FeatureSnapshotRecord,
        "feature_snapshot_id",
        "feature_snapshot_digest",
    )


def _append_selector_input_record(
    selector_input: SelectorInput,
    result_store: result_store_module.ResultStore,
) -> None:
    validation = validate_selector_input(selector_input)
    if not validation.ok:
        raise ValueError(
            f"selector input record is invalid: {', '.join(validation.errors)}"
        )
    _append_record_once(
        _selector_input_log_path(result_store),
        selector_input,
        SelectorInput,
        "selector_input_id",
        "selector_input_digest",
    )


def _append_evaluation_cell_set_record(
    cell_set: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
) -> None:
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise ValueError(
            f"evaluation cell set is invalid: {', '.join(validation.errors)}"
        )
    _append_record_once(
        _evaluation_cell_set_log_path(result_store),
        cell_set,
        EvaluationCellSet,
        "cell_set_id",
        "cell_set_digest",
    )


def _append_result_matrix_records(
    matrices: Sequence[ResultMatrix],
    result_store: result_store_module.ResultStore,
) -> None:
    for matrix in matrices:
        validation = validate_result_matrix(matrix)
        if not validation.ok:
            raise ValueError(
                f"result matrix is invalid: {', '.join(validation.errors)}"
            )
        _append_record_once(
            _result_matrix_log_path(result_store),
            matrix,
            ResultMatrix,
            "matrix_id",
            "matrix_digest",
        )


def _append_metric_records(
    metrics: Sequence[MetricRecord], result_store: result_store_module.ResultStore
) -> tuple[MetricRecord, ...]:
    persisted: list[MetricRecord] = []
    for metric in metrics:
        validation = validate_metric(metric)
        if not validation.ok:
            raise ValueError(
                f"metric record is invalid: {', '.join(validation.errors)}"
            )
        persisted.append(
            _append_record_once(
                _metric_log_path(result_store),
                metric,
                MetricRecord,
                "metric_id",
                "metric_digest",
                observation_fields=("computed_at",),
            )
        )
    return tuple(persisted)


def _append_record_once(
    path: Path,
    record: _RecordT,
    record_type: type[_RecordT],
    id_attr: str,
    digest_attr: str,
    *,
    observation_fields: tuple[str, ...] = (),
) -> _RecordT:
    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    record_id = cast(str, getattr(record, id_attr))
    record_digest = getattr(record, digest_attr)
    matching_record: _RecordT | None = None
    if path.exists():
        seen_ids: set[str] = set()
        for existing in load_jsonl_records(path, record_type):
            existing_id = cast(str, getattr(existing, id_attr))
            if existing_id in seen_ids:
                raise ValueError(
                    f"{path.name} contains duplicate {id_attr}: {existing_id}"
                )
            seen_ids.add(existing_id)
            if existing_id == record_id:
                matching_record = existing
    if matching_record is not None:
        if getattr(matching_record, digest_attr) == record_digest:
            return matching_record
        if observation_fields:
            normalized = replace(
                cast(Any, record),
                **{
                    **{
                        field_name: getattr(matching_record, field_name)
                        for field_name in observation_fields
                    },
                    digest_attr: getattr(matching_record, digest_attr),
                },
            )
            if normalized == matching_record:
                return matching_record
        raise ValueError(f"{id_attr} already exists with a different digest")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(record))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    if created:
        _fsync_directory(path.parent)
    return record


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _selection_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("selections.jsonl")


def _selector_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("selectors.jsonl")


def _origin_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("origins.jsonl")


def _feature_snapshot_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("feature-snapshots.jsonl")


def _selector_input_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("selector-inputs.jsonl")


def _evaluation_cell_set_log_path(
    result_store: result_store_module.ResultStore,
) -> Path:
    return result_store.path.with_name("evaluation-cell-sets.jsonl")


def _result_matrix_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("result-matrices.jsonl")


def _metric_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("metrics.jsonl")


def _results_bound_to_evaluation_cells(
    evaluation_cells: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
) -> tuple[ResultRecord, ...]:
    results_by_id = _load_evaluation_cell_results((evaluation_cells,), result_store)
    return _validated_evaluation_cell_results(evaluation_cells, results_by_id)


def _ensure_evaluation_cell_set_result_bindings(
    cell_sets: Sequence[EvaluationCellSet],
    result_store: result_store_module.ResultStore,
) -> None:
    results_by_id = _load_evaluation_cell_results(cell_sets, result_store)
    for cell_set in cell_sets:
        _validated_evaluation_cell_results(cell_set, results_by_id)


def _load_evaluation_cell_results(
    cell_sets: Sequence[EvaluationCellSet],
    result_store: result_store_module.ResultStore,
) -> Mapping[str, ResultRecord]:
    bound_ids = tuple(
        dict.fromkeys(
            cell.result_id
            for cell_set in cell_sets
            for cell in cell_set.cells
            if cell.result_id is not None
        )
    )
    if not bound_ids:
        return {}
    loaded = result_store_module.load_results(
        result_store, result_store_module.ResultQuery(result_ids=bound_ids)
    )
    return {result.result_id: result for result in loaded}


def _validated_evaluation_cell_results(
    evaluation_cells: EvaluationCellSet,
    results_by_id: Mapping[str, ResultRecord],
) -> tuple[ResultRecord, ...]:
    ordered: list[ResultRecord] = []
    seen: set[str] = set()
    for cell in evaluation_cells.cells:
        if cell.result_id is None and cell.result_digest is None:
            continue
        if cell.result_id is None or cell.result_digest is None:
            raise ValueError(
                "evaluation cell result binding must include both result_id and result_digest"
            )
        result = results_by_id.get(cell.result_id)
        if result is None:
            raise ValueError(
                f"evaluation cell references missing result_id {cell.result_id}"
            )
        mismatches = result_cell_record_mismatches(cell, result)
        if mismatches:
            raise ValueError(
                "evaluation cell does not match result_id "
                f"{cell.result_id}: {', '.join(mismatches)}"
            )
        if result.result_id not in seen:
            seen.add(result.result_id)
            ordered.append(result)
    return tuple(ordered)


def _missing_cell(
    agent: AgentRecord, task: TaskRecord, check: CheckRecord, identity_digest: str
) -> ResultCellRef:
    return ResultCellRef(
        agent_id=agent.agent_id,
        task_id=task.task_id,
        check_id=check.check_id,
        required_identity_digest=identity_digest,
        result_id=None,
        result_digest=None,
        cell_state="missing",
        exclusion_reason=None,
        outcome=None,
    )


def _cell_set_abstention(
    cells: Sequence[ResultCellRef], join_config: result_store_module.ResultJoinConfig
) -> str | None:
    if join_config.abstention_policy == "abstain_on_missing" and any(
        cell.cell_state == "missing" for cell in cells
    ):
        return "missing_required_results"
    return None


def _ensure_refs_in_task_pool(
    refs: Sequence[TaskCheckRef], task_pool: TaskPoolRecord
) -> None:
    task_ids = set(task_pool.task_ids)
    check_ids = set(task_pool.check_ids)
    for ref in refs:
        if ref.task_id not in task_ids or ref.check_id not in check_ids:
            raise ValueError("task_check_refs must be in TaskPoolRecord")


def _validate_task_pool_members(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    if set(checks) != set(task_pool.check_ids):
        raise ValueError("checks must exactly match TaskPoolRecord check_ids")
    ordered_checks = tuple(checks[check_id] for check_id in task_pool.check_ids)
    validation = task_pool_module.validate_task_pool_members(
        task_pool,
        tasks,
        ordered_checks,
    )
    if not validation.ok:
        raise ValueError(
            "task pool members are invalid: " + "; ".join(validation.errors)
        )


def _validated_task_pool_bundle(
    bundle: task_pool_module.TaskPoolBundle,
) -> task_pool_module.TaskPoolBundle:
    if not isinstance(bundle, task_pool_module.TaskPoolBundle):
        raise TypeError("task_pool_bundle must be a TaskPoolBundle")
    return task_pool_module.validated_task_pool_bundle(
        bundle.task_pool,
        bundle.tasks,
        bundle.checks,
        bundle.certification_evidence,
        bundle.source_events,
    )


def _ensure_selection_matches_task_pool(
    selection: BenchmarkSelectionRecord, task_pool: TaskPoolRecord
) -> None:
    if (
        selection.task_pool_id != task_pool.task_pool_id
        or selection.task_pool_digest != task_pool.task_pool_digest
    ):
        raise ValueError("selection does not match TaskPoolRecord")


def _ensure_selection_origin(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    _ensure_selection_matches_task_pool(selection, task_pool)
    origin_validation = selection_module.validate_rolling_origin_against_records(
        origin,
        task_pool,
        tasks,
        checks,
    )
    if not origin_validation.ok:
        raise ValueError("origin is invalid: " + "; ".join(origin_validation.errors))
    if selection.origin_id != origin.origin_id:
        raise ValueError("selection does not match origin")
    if selection.eligibility_mode != origin.eligibility_mode:
        raise ValueError("selection eligibility mode does not match origin")
    history_refs = set(origin.history_task_check_refs)
    if any(ref not in history_refs for ref in selection.selected_task_check_refs):
        raise ValueError("selection includes refs outside origin history")


def _task_for_ref(ref: TaskCheckRef, tasks: Sequence[TaskRecord]) -> TaskRecord:
    task_by_id = {task.task_id: task for task in tasks}
    task = task_by_id.get(ref.task_id)
    if task is None:
        raise ValueError(f"task is missing for ref {ref.task_id}")
    return task


def _check_for_ref(
    ref: TaskCheckRef, task: TaskRecord, checks: Mapping[str, CheckRecord]
) -> CheckRecord:
    check = checks.get(ref.check_id)
    if check is None:
        raise ValueError(f"check is missing for ref {ref.check_id}")
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        raise ValueError("check must be linked to task")
    return check


def _unique_refs(refs: Sequence[TaskCheckRef]) -> tuple[TaskCheckRef, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[TaskCheckRef] = []
    for ref in refs:
        key = _ref_key(ref)
        if key not in seen:
            seen.add(key)
            unique.append(ref)
    return tuple(unique)


def _ref_key(ref: TaskCheckRef) -> tuple[str, str]:
    return (ref.task_id, ref.check_id)


def _now() -> str:
    return utc_now_timestamp()
