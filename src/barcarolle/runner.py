"""Command-level orchestration across Barcarolle owner modules."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

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
    MetricRecord,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    RuntimeConfig,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    record_with_digest,
    validate_benchmark_selection,
    validate_evaluation_cell_set,
    validate_metric,
    write_jsonl_records,
)
from barcarolle.task_pool import TimeRange


@dataclass(frozen=True)
class TaskPoolConfig:
    repository_url_or_path: str
    workspace_config: WorkspaceConfig
    runtime_config: RuntimeConfig
    reference_patches: Mapping[str, workspace_module.CapturedDiff]
    time_range: TimeRange | None = None
    task_source_config: task_pool_module.TaskSourceConfig | None = None
    import_path: Path | None = None
    import_config: task_pool_module.ImportConfig = field(default_factory=task_pool_module.ImportConfig)
    certification_config: task_pool_module.CertificationConfig = field(default_factory=task_pool_module.CertificationConfig)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportConfig:
    output_dir: Path
    agents: tuple[AgentRecord, ...] = ()
    markdown_filename: str = "report.md"
    json_filename: str = "report.json"
    claim_config: reporting_module.ClaimConfig = field(
        default_factory=lambda: reporting_module.ClaimConfig("default_claim_boundary")
    )


def build_task_pool(config: TaskPoolConfig) -> TaskPoolRecord:
    candidates = _task_candidates(config)
    missing_patches = tuple(
        candidate.candidate_id for candidate in candidates if candidate.candidate_id not in config.reference_patches
    )
    if missing_patches:
        raise ValueError("reference patch is missing for candidates: " + ", ".join(missing_patches))
    certified = tuple(
        task_pool_module.certify_task_candidate(
            candidate,
            config.certification_config,
            config.workspace_config,
            config.runtime_config,
            config.reference_patches[candidate.candidate_id],
        )
        for candidate in candidates
    )
    accepted_tasks = tuple(result.task for result in certified if result.accepted and result.task is not None)
    accepted_checks = tuple(result.check for result in certified if result.accepted and result.check is not None)
    rejected = tuple(result for result in certified if not result.accepted)
    metadata = _task_pool_metadata(config, candidates, certified)
    task_pool = task_pool_module.freeze_task_pool(accepted_tasks, accepted_checks, rejected, metadata)
    write_jsonl_records(_ref_path(task_pool.task_records_ref), accepted_tasks)
    write_jsonl_records(_ref_path(task_pool.check_records_ref), accepted_checks)
    return task_pool


def train_selector(
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    candidate_selectors: Sequence[SelectorRecord],
    training_config: selection_module.SelectorTrainingConfig,
    rolling_policy: selection_module.RollingOriginPolicy,
    feature_config: selection_module.FeatureConfig,
    result_store: result_store_module.ResultStore,
) -> SelectorRecord:
    tasks, checks = _load_task_pool_records(task_pool)
    results = _load_training_results(result_store, task_pool, tasks, checks, agents, history_window, rolling_policy)
    return selection_module.train_selector(
        task_pool,
        tasks,
        checks,
        results,
        agents,
        history_window,
        candidate_selectors,
        training_config,
        rolling_policy,
        feature_config,
    )


def select_benchmark(
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord],
    origin_time: datetime,
    budget: selection_module.SelectionBudget,
    selector: SelectorRecord,
    selection_config: selection_module.SelectionConfig,
    rolling_policy: selection_module.RollingOriginPolicy,
    feature_config: selection_module.FeatureConfig,
    result_store: result_store_module.ResultStore,
) -> BenchmarkSelectionRecord:
    tasks, checks = _load_task_pool_records(task_pool)
    origin = selection_module.build_rolling_origin(
        task_pool,
        tasks,
        checks,
        origin_time,
        TimeRange(start=_datetime_to_iso(origin_time), end=_datetime_to_iso(origin_time)),
        rolling_policy,
    )
    pre_origin_results = _load_pre_origin_results(result_store, origin, agents, TimeRange("", origin.as_of_cutoff))
    selection = selection_module.select_benchmark(
        selector,
        task_pool,
        tasks,
        checks,
        pre_origin_results,
        agents,
        origin_time,
        budget,
        selection_config,
        rolling_policy,
        feature_config,
    )
    _append_selection_record(selection, result_store)
    return selection


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
    metric_config: selection_module.MetricConfig,
) -> tuple[
    tuple[BenchmarkSelectionRecord, ...],
    tuple[EvaluationCellSet, ...],
    tuple[ResultMatrix, ...],
    tuple[MetricRecord, ...],
]:
    tasks, checks = _load_task_pool_records(task_pool)
    try:
        origin_times = tuple(_parse_datetime(value) for value in evaluation_config.origin_times)
    except ValueError as exc:
        raise ValueError("evaluation origin_times entries must be ISO datetime strings") from exc
    origins = tuple(
        selection_module.build_rolling_origin(
            task_pool,
            tasks,
            checks,
            origin_time,
            TimeRange(start=_datetime_to_iso(origin_time), end=history_window.end),
            rolling_policy,
        )
        for origin_time in origin_times
    )
    selections: list[BenchmarkSelectionRecord] = []
    for origin in origins:
        pre_origin_results = _load_pre_origin_results(result_store, origin, agents, history_window)
        snapshot = selection_module.build_feature_snapshot(origin, task_pool, tasks, checks, pre_origin_results, feature_config)
        selector_input = selection_module.build_selector_input(
            origin,
            task_pool,
            snapshot,
            pre_origin_results,
            agents,
            evaluation_config.budget,
            selection_module.LeakagePolicy(
                feature_config.leakage_policy_digest,
                feature_config.allowed_leakage_classes,
                origin.as_of_cutoff,
            ),
        )
        selection_config = replace(
            evaluation_config.selection_config,
            selector_id=evaluation_config.selection_config.selector_id or selector.selector_id,
            feature_snapshot_id=selector_input.feature_snapshot_id,
        )
        frozen = tuple(
            selection_module.freeze_evaluation_selections(
                selector,
                task_pool,
                tasks,
                checks,
                (selector_input,),
                agents,
                history_window,
                selection_config,
                rolling_policy,
            )
        )
        for selection in frozen:
            _append_selection_record(selection, result_store)
        selections.extend(frozen)
    cell_sets: list[EvaluationCellSet] = []
    matrices: list[ResultMatrix] = []
    metrics: list[MetricRecord] = []
    origin_by_id = {origin.origin_id: origin for origin in origins}
    for selection in selections:
        origin = origin_by_id[selection.origin_id]
        cell_set = prepare_evaluation_cells(
            selection,
            origin,
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
        )
        scored_cell_set, selected_matrix, future_matrix, selection_metrics = score_selection(
            selection,
            origin,
            task_pool,
            tasks,
            checks,
            agents,
            cell_set,
            result_store,
            join_config,
            metric_config,
        )
        cell_sets.append(scored_cell_set)
        matrices.extend((selected_matrix, future_matrix))
        metrics.extend(selection_metrics)
    return tuple(selections), tuple(cell_sets), tuple(matrices), tuple(metrics)


def run_agents(
    task_pool: TaskPoolRecord,
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    result_store: result_store_module.ResultStore,
) -> tuple[ResultRecord, ...]:
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
    return _run_agent_cells(cells, tasks, checks, agents, workspace_config, runtime_config, scoring_config, result_store)


def fill_results(
    selection: BenchmarkSelectionRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    cache_config: result_store_module.ResultCacheConfig,
    result_store: result_store_module.ResultStore,
) -> tuple[ResultRecord, ...]:
    _ensure_selection_matches_task_pool(selection, task_pool)
    missing = result_store_module.find_missing_results(
        selection.selected_task_check_refs,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        result_store,
        cache_config,
    )
    return _run_agent_cells(missing, tasks, checks, agents, workspace_config, runtime_config, scoring_config, result_store)


def prepare_evaluation_cells(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
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
) -> EvaluationCellSet:
    _ensure_selection_origin(selection, origin, task_pool)
    requested_refs = _unique_refs((*selection.selected_task_check_refs, *origin.future_holdout_task_check_refs))
    missing = result_store_module.find_missing_results(
        requested_refs,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        result_store,
        cache_config,
    )
    _run_agent_cells(missing, tasks, checks, agents, workspace_config, runtime_config, scoring_config, result_store)
    cells = list(
        result_store_module.resolve_result_cells(
            requested_refs,
            tasks,
            checks,
            agents,
            workspace_config,
            runtime_config,
            result_store,
            cache_config,
        )
    )
    cell_set = EvaluationCellSet(
        cell_set_id=f"cell_set_{canonical_digest((selection.selection_digest, origin.origin_id, join_config.join_policy_digest, tuple(_ref_key(ref) for ref in requested_refs), tuple(agent.agent_id for agent in agents)))}",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        selected_task_check_refs=selection.selected_task_check_refs,
        future_task_check_refs=origin.future_holdout_task_check_refs,
        cells=tuple(cells),
        abstention_reason=_cell_set_abstention(cells, join_config),
        cell_set_digest="",
    )
    cell_set = record_with_digest(cell_set)
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise ValueError(f"evaluation cell set is invalid: {', '.join(validation.errors)}")
    return cell_set


def score_selection(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    evaluation_cells: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
    join_config: result_store_module.ResultJoinConfig,
    metric_config: selection_module.MetricConfig,
) -> tuple[EvaluationCellSet, ResultMatrix, ResultMatrix, tuple[MetricRecord, ...]]:
    _ensure_selection_origin(selection, origin, task_pool)
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
        origin.future_holdout_task_check_refs,
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
            metric_config,
        )
    )
    _append_metric_records(metrics, result_store)
    return evaluation_cells, selected_matrix, future_matrix, metrics


def write_report(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    results: Sequence[ResultRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    report_config: ReportConfig,
) -> Mapping[str, object]:
    sections = (
        reporting_module.build_task_pool_report(task_pool),
        reporting_module.build_result_report(results, report_config.agents),
        reporting_module.build_selector_report(selections, cell_sets, result_matrices, metrics),
        reporting_module.build_claim_boundary(
            task_pool,
            selections,
            cell_sets,
            result_matrices,
            metrics,
            report_config.claim_config,
            results=results,
        ),
    )
    markdown_path = report_config.output_dir / report_config.markdown_filename
    json_path = report_config.output_dir / report_config.json_filename
    reporting_module.write_report(sections, markdown_path)
    reporting_module.write_report(sections, json_path)
    return {
        "report_paths": {"markdown": str(markdown_path), "json": str(json_path)},
        "section_ids": tuple(section.section_id for section in sections),
        "source_digests": {section.section_id: section.source_digests for section in sections},
    }


def _task_candidates(config: TaskPoolConfig) -> tuple[task_pool_module.TaskCandidate, ...]:
    if config.import_path is not None:
        return tuple(task_pool_module.import_task_pool(config.import_path, config.import_config))
    if config.time_range is None or config.task_source_config is None:
        raise ValueError("TaskPoolConfig requires either import_path or time_range with task_source_config")
    return tuple(
        task_pool_module.generate_history_candidates(
            config.repository_url_or_path,
            config.time_range,
            config.task_source_config,
        )
    )


def _task_pool_metadata(
    config: TaskPoolConfig,
    candidates: Sequence[task_pool_module.TaskCandidate],
    certified: Sequence[task_pool_module.CertificationResult],
) -> Mapping[str, object]:
    metadata = dict(config.metadata)
    metadata.setdefault("repository_id", _repository_id(config, candidates))
    metadata.setdefault("accepted_certification_results", tuple(result for result in certified if result.accepted))
    metadata.setdefault("task_records_ref", "records/tasks.jsonl")
    metadata.setdefault("check_records_ref", "records/checks.jsonl")
    metadata.setdefault("source_event_inventory_digest", canonical_digest(tuple(candidate.source_ref for candidate in candidates)))
    metadata.setdefault("generator_config_digest", _generator_config_digest(config))
    metadata.setdefault("certification_config_digest", canonical_digest(config.certification_config))
    metadata.setdefault("created_at", _now())
    return metadata


def _repository_id(config: TaskPoolConfig, candidates: Sequence[task_pool_module.TaskCandidate]) -> str:
    if candidates:
        return candidates[0].repository_id
    return config.repository_url_or_path


def _generator_config_digest(config: TaskPoolConfig) -> str:
    if config.import_path is not None:
        return canonical_digest((str(config.import_path), config.import_config))
    return canonical_digest(config.task_source_config)


def _load_task_pool_records(task_pool: TaskPoolRecord) -> tuple[tuple[TaskRecord, ...], Mapping[str, CheckRecord]]:
    tasks = tuple(load_jsonl_records(_ref_path(task_pool.task_records_ref), TaskRecord))
    checks_tuple = tuple(load_jsonl_records(_ref_path(task_pool.check_records_ref), CheckRecord))
    if canonical_digest(tasks) != task_pool.task_records_digest:
        raise ValueError("task_records_digest does not match TaskPoolRecord")
    if canonical_digest(checks_tuple) != task_pool.check_records_digest:
        raise ValueError("check_records_digest does not match TaskPoolRecord")
    task_ids = {task.task_id for task in tasks}
    check_ids = {check.check_id for check in checks_tuple}
    if set(task_pool.task_ids) - task_ids:
        raise ValueError("TaskPoolRecord references missing Task records")
    if set(task_pool.check_ids) - check_ids:
        raise ValueError("TaskPoolRecord references missing Check records")
    return tasks, {check.check_id: check for check in checks_tuple}


def _ref_path(ref: str) -> Path:
    normalized = ref[5:] if ref.startswith("path:") else ref
    path = Path(normalized)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _run_agent_cells(
    cells: Sequence[ResultCellRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: result_store_module.ScoringConfig,
    result_store: result_store_module.ResultStore,
) -> tuple[ResultRecord, ...]:
    if not cells:
        return ()
    agent_by_id = {agent.agent_id: agent for agent in agents}
    results: list[ResultRecord] = []
    for cell in cells:
        task = _task_for_ref(TaskCheckRef(cell.task_id, cell.check_id), tasks)
        check = _check_for_ref(TaskCheckRef(cell.task_id, cell.check_id), task, checks)
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
            raise ValueError("missing cell required identity does not match current run config")
        workspace_run = workspace_module.run_agent_on_task(task, check, agent, workspace_config, runtime_config)
        result = result_store_module.build_result_record(task, check, agent, workspace_run, identity, scoring_config)
        results.append(result_store_module.store_result(result, result_store))
    return tuple(results)


def _load_training_results(
    result_store: result_store_module.ResultStore,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
    rolling_policy: selection_module.RollingOriginPolicy,
) -> tuple[ResultRecord, ...]:
    origin = selection_module.build_rolling_origin(
        task_pool,
        tasks,
        checks,
        _parse_datetime(history_window.end),
        history_window,
        rolling_policy,
    )
    task_ids, check_ids = _refs_query_parts(origin.history_task_check_refs)
    if not task_ids or not agents:
        return ()
    return _load_results_for_refs(
        result_store,
        origin.history_task_check_refs,
        agents,
        result_available_after=history_window.start,
        result_available_before=history_window.end,
    )


def _load_results_for_refs(
    result_store: result_store_module.ResultStore,
    refs: Sequence[TaskCheckRef],
    agents: Sequence[AgentRecord],
    *,
    result_available_after: str,
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
        )
    )
    return tuple(result for result in loaded if (result.task_id, result.check_id) in allowed_refs)


def _load_pre_origin_results(
    result_store: result_store_module.ResultStore,
    origin: RollingOriginRecord,
    agents: Sequence[AgentRecord],
    history_window: TimeRange,
) -> tuple[ResultRecord, ...]:
    return _load_results_for_refs(
        result_store,
        origin.history_task_check_refs,
        agents,
        result_available_after=history_window.start,
        result_available_before=origin.as_of_cutoff,
    )


def _refs_query_parts(refs: Sequence[TaskCheckRef]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(dict.fromkeys(ref.task_id for ref in refs)),
        tuple(dict.fromkeys(ref.check_id for ref in refs)),
    )


def _append_selection_record(selection: BenchmarkSelectionRecord, result_store: result_store_module.ResultStore) -> None:
    validation = validate_benchmark_selection(selection)
    if not validation.ok:
        raise ValueError(f"selection record is invalid: {', '.join(validation.errors)}")
    _append_record_once(_selection_log_path(result_store), selection, BenchmarkSelectionRecord, "selection_id", "selection_digest")


def _append_metric_records(metrics: Sequence[MetricRecord], result_store: result_store_module.ResultStore) -> None:
    for metric in metrics:
        validation = validate_metric(metric)
        if not validation.ok:
            raise ValueError(f"metric record is invalid: {', '.join(validation.errors)}")
        _append_record_once(_metric_log_path(result_store), metric, MetricRecord, "metric_id", "metric_digest")


def _append_record_once(path: Path, record: object, record_type: type, id_attr: str, digest_attr: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record_id = getattr(record, id_attr)
    record_digest = getattr(record, digest_attr)
    if path.exists():
        for existing in load_jsonl_records(path, record_type):
            if getattr(existing, id_attr) != record_id:
                continue
            if getattr(existing, digest_attr) != record_digest:
                raise ValueError(f"{id_attr} already exists with a different digest")
            return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(record))
        handle.write("\n")


def _selection_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("selections.jsonl")


def _metric_log_path(result_store: result_store_module.ResultStore) -> Path:
    return result_store.path.with_name("metrics.jsonl")


def _results_bound_to_evaluation_cells(
    evaluation_cells: EvaluationCellSet,
    result_store: result_store_module.ResultStore,
) -> tuple[ResultRecord, ...]:
    bound_ids = tuple(dict.fromkeys(cell.result_id for cell in evaluation_cells.cells if cell.result_id is not None))
    if not bound_ids:
        return ()
    loaded = result_store_module.load_results(result_store, result_store_module.ResultQuery(result_ids=bound_ids))
    result_by_id = {result.result_id: result for result in loaded}
    ordered: list[ResultRecord] = []
    seen: set[str] = set()
    for cell in evaluation_cells.cells:
        if cell.result_id is None and cell.result_digest is None:
            continue
        if cell.result_id is None or cell.result_digest is None:
            raise ValueError("evaluation cell result binding must include both result_id and result_digest")
        result = result_by_id.get(cell.result_id)
        if result is None:
            raise ValueError(f"evaluation cell references missing result_id {cell.result_id}")
        if result.result_digest != cell.result_digest:
            raise ValueError(f"evaluation cell result_digest does not match result_id {cell.result_id}")
        if result.agent_id != cell.agent_id or result.task_id != cell.task_id or result.check_id != cell.check_id:
            raise ValueError(f"evaluation cell Agent/Task/Check does not match result_id {cell.result_id}")
        if result.cache_identity.identity_digest != cell.required_identity_digest:
            raise ValueError(f"evaluation cell required identity does not match result_id {cell.result_id}")
        if result.result_id not in seen:
            seen.add(result.result_id)
            ordered.append(result)
    return tuple(ordered)


def _missing_cell(agent: AgentRecord, task: TaskRecord, check: CheckRecord, identity_digest: str) -> ResultCellRef:
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


def _cell_set_abstention(cells: Sequence[ResultCellRef], join_config: result_store_module.ResultJoinConfig) -> str | None:
    if join_config.abstention_policy == "abstain_on_missing" and any(cell.cell_state == "missing" for cell in cells):
        return "missing_required_results"
    return None


def _ensure_refs_in_task_pool(refs: Sequence[TaskCheckRef], task_pool: TaskPoolRecord) -> None:
    task_ids = set(task_pool.task_ids)
    check_ids = set(task_pool.check_ids)
    for ref in refs:
        if ref.task_id not in task_ids or ref.check_id not in check_ids:
            raise ValueError("task_check_refs must be in TaskPoolRecord")


def _ensure_selection_matches_task_pool(selection: BenchmarkSelectionRecord, task_pool: TaskPoolRecord) -> None:
    if selection.task_pool_id != task_pool.task_pool_id or selection.task_pool_digest != task_pool.task_pool_digest:
        raise ValueError("selection does not match TaskPoolRecord")


def _ensure_selection_origin(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
) -> None:
    _ensure_selection_matches_task_pool(selection, task_pool)
    if origin.task_pool_id != task_pool.task_pool_id or origin.task_pool_digest != task_pool.task_pool_digest:
        raise ValueError("origin does not match TaskPoolRecord")
    if selection.origin_id != origin.origin_id:
        raise ValueError("selection does not match origin")


def _task_for_ref(ref: TaskCheckRef, tasks: Sequence[TaskRecord]) -> TaskRecord:
    task_by_id = {task.task_id: task for task in tasks}
    task = task_by_id.get(ref.task_id)
    if task is None:
        raise ValueError(f"task is missing for ref {ref.task_id}")
    return task


def _check_for_ref(ref: TaskCheckRef, task: TaskRecord, checks: Mapping[str, CheckRecord]) -> CheckRecord:
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


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _datetime_to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
