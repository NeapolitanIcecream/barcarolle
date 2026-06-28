"""Append-only Result Store contracts and joins."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    EvaluationCellSet,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RuntimeConfig,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_result_cache_identity,
    make_result_cache_key,
    record_with_digest,
    validate_evaluation_cell_set,
    validate_result,
    validate_result_cache_identity,
    validate_result_matrix,
    validate_workspace_run,
)


@dataclass(frozen=True)
class ScoringConfig:
    scoring_config_digest: str
    pricing_version: str
    usage_coverage: str
    cost_rates: Mapping[str, float]


@dataclass(frozen=True)
class ResultStore:
    path: Path


@dataclass(frozen=True)
class ResultQuery:
    task_ids: tuple[str, ...] = ()
    check_ids: tuple[str, ...] = ()
    agent_ids: tuple[str, ...] = ()
    result_ids: tuple[str, ...] = ()
    cache_identity_digests: tuple[str, ...] = ()
    scoring_config_digests: tuple[str, ...] = ()
    result_available_after: str | None = None
    result_available_before: str | None = None


@dataclass(frozen=True)
class ResultCacheConfig:
    reuse_policy: str = "exact_identity"
    require_valid_result: bool = True


@dataclass(frozen=True)
class ResultJoinConfig:
    join_policy_digest: str
    denominator_policy_digest: str
    missing_cell_policy: str = "mark_missing"
    agent_invalid_policy: str = "count_as_failure"
    benchmark_invalid_policy: str = "exclude_task_check"
    abstention_policy: str = "abstain_on_missing"


def build_result_record(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_run: WorkspaceRunRecord,
    cache_identity: ResultCacheIdentity,
    scoring_config: ScoringConfig,
) -> ResultRecord:
    _validate_task_check_agent_linkage(task, check, agent, workspace_run)
    validation = validate_workspace_run(workspace_run)
    if not validation.ok:
        raise ValueError(f"workspace_run is invalid: {', '.join(validation.errors)}")
    _validate_cache_identity_inputs(task, check, agent, cache_identity, scoring_config)
    scoreable_state, outcome, invalid_owner = _normalize_result_state(workspace_run)
    result = ResultRecord(
        result_id=f"result_{canonical_digest((cache_identity.identity_digest, workspace_run.workspace_run_id, scoring_config.scoring_config_digest))}",
        result_digest="",
        cache_identity=cache_identity,
        agent_id=agent.agent_id,
        task_id=task.task_id,
        check_id=check.check_id,
        terminal_status=workspace_run.terminal_status,
        scoreable_state=scoreable_state,
        outcome=outcome,
        invalid_owner=invalid_owner,
        failure_label=workspace_run.failure_label,
        cost=_cost_from_usage(workspace_run.usage, scoring_config),
        pricing_version=scoring_config.pricing_version,
        usage=workspace_run.usage,
        usage_coverage=scoring_config.usage_coverage,
        latency=_latency_from_workspace_run(workspace_run),
        diff_digest=workspace_run.diff_digest,
        verifier_metadata_digest=_verifier_metadata_digest(workspace_run),
        started_at=workspace_run.started_at,
        finished_at=workspace_run.finished_at,
        result_available_at=max(_now(), workspace_run.finished_at),
    )
    result = record_with_digest(result)
    result_validation = validate_result(result)
    if not result_validation.ok:
        raise ValueError(f"result record is invalid: {', '.join(result_validation.errors)}")
    return result


def compute_result_cache_identity(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
) -> ResultCacheIdentity:
    if not scoring_config.scoring_config_digest:
        raise ValueError("scoring_config_digest is required")
    return make_result_cache_identity(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config.scoring_config_digest,
    )


def compute_result_cache_key(identity: ResultCacheIdentity) -> str:
    return make_result_cache_key(identity)


def store_result(result: ResultRecord, store: ResultStore) -> ResultRecord:
    validation = validate_result(result)
    if not validation.ok:
        raise ValueError(f"result record is invalid: {', '.join(validation.errors)}")
    store.path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_results(store, ResultQuery(result_ids=(result.result_id,)))
    for stored in existing:
        if stored.result_digest != result.result_digest:
            raise ValueError("result_id already exists with a different digest")
        return stored
    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(result))
        handle.write("\n")
    return result


def load_results(store: ResultStore, query: ResultQuery) -> Sequence[ResultRecord]:
    if not store.path.exists():
        return ()
    results = tuple(load_jsonl_records(store.path, ResultRecord))
    return tuple(result for result in results if _matches_query(result, query))


def find_missing_results(
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
) -> Sequence[ResultCellRef]:
    if cache_config.reuse_policy != "exact_identity":
        raise ValueError("Result Store only supports exact_identity cache reuse")
    task_by_id = {task.task_id: task for task in tasks}
    stored_results = load_results(store, ResultQuery(scoring_config_digests=(scoring_config.scoring_config_digest,)))
    missing: list[ResultCellRef] = []
    for ref in task_check_refs:
        task = _task_for_ref(ref, task_by_id)
        check = _check_for_ref(ref, task, checks)
        for agent in agents:
            identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config, scoring_config)
            reusable = _find_reusable_result(stored_results, identity, cache_config, agent.agent_id, task.task_id, check.check_id)
            if reusable is None:
                missing.append(
                    ResultCellRef(
                        agent_id=agent.agent_id,
                        task_id=task.task_id,
                        check_id=check.check_id,
                        required_identity_digest=identity.identity_digest,
                        result_id=None,
                        result_digest=None,
                        cell_state="missing",
                        exclusion_reason=None,
                        outcome=None,
                    )
                )
    return tuple(missing)


def build_result_matrix(
    evaluation_cells: EvaluationCellSet,
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    results: Sequence[ResultRecord],
    matrix_role: str,
    join_config: ResultJoinConfig,
) -> ResultMatrix:
    cell_validation = validate_evaluation_cell_set(evaluation_cells)
    if not cell_validation.ok:
        raise ValueError(f"evaluation cell set is invalid: {', '.join(cell_validation.errors)}")
    expected_refs = _matrix_refs(evaluation_cells, matrix_role)
    requested_refs = tuple(task_check_refs)
    if requested_refs != expected_refs:
        raise ValueError("task_check_refs must exactly match the evaluation subset for matrix_role")
    task_by_id = {task.task_id: task for task in tasks}
    for ref in requested_refs:
        task = _task_for_ref(ref, task_by_id)
        _check_for_ref(ref, task, checks)
    result_by_cell = _results_by_cell(results)
    required_cells = _required_cells_by_key(evaluation_cells.cells, requested_refs, agents)
    task_exclusions = _task_check_exclusions(required_cells, result_by_cell, join_config)
    matrix_cells: list[ResultCellRef] = []
    for agent in agents:
        for ref in requested_refs:
            required = required_cells.get((agent.agent_id, ref.task_id, ref.check_id))
            if required is None:
                raise ValueError("evaluation_cells must include every matrix Agent/Task/Check cell")
            result = result_by_cell.get((required.agent_id, required.task_id, required.check_id, required.required_identity_digest))
            exclusion_reason = task_exclusions.get((ref.task_id, ref.check_id))
            matrix_cells.append(_matrix_cell(required, result, join_config, exclusion_reason))
    abstention_reason = _abstention_reason(matrix_cells, join_config)
    matrix = ResultMatrix(
        matrix_id=f"matrix_{canonical_digest((evaluation_cells.cell_set_id, matrix_role, join_config.join_policy_digest, tuple(task_check_refs)))}",
        matrix_role=matrix_role,
        origin_id=evaluation_cells.origin_id,
        selection_id=evaluation_cells.selection_id,
        agent_ids=tuple(agent.agent_id for agent in agents),
        task_check_refs=requested_refs,
        cells=tuple(matrix_cells),
        join_policy_digest=join_config.join_policy_digest,
        denominator_policy_digest=join_config.denominator_policy_digest,
        abstention_reason=abstention_reason,
        scoreable_state="abstained" if abstention_reason else _matrix_scoreable_state(matrix_cells),
        matrix_digest="",
    )
    matrix = record_with_digest(matrix)
    matrix_validation = validate_result_matrix(matrix)
    if not matrix_validation.ok:
        raise ValueError(f"result matrix is invalid: {', '.join(matrix_validation.errors)}")
    return matrix


def _validate_task_check_agent_linkage(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_run: WorkspaceRunRecord,
) -> None:
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        raise ValueError("check must be linked to task")
    if workspace_run.task_id != task.task_id or workspace_run.check_id != check.check_id:
        raise ValueError("workspace_run task/check does not match result inputs")
    if workspace_run.agent_id != agent.agent_id:
        raise ValueError("workspace_run agent does not match result inputs")


def _validate_cache_identity_inputs(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    identity: ResultCacheIdentity,
    scoring_config: ScoringConfig,
) -> None:
    validation = validate_result_cache_identity(identity)
    if not validation.ok:
        raise ValueError(f"cache identity is invalid: {', '.join(validation.errors)}")
    expected_fields = {
        "task_id": task.task_id,
        "check_id": check.check_id,
        "repository_id": task.repository_id,
        "base_commit": task.base_commit,
        "solver_material_digest": task.solver_material_digest,
        "check_manifest_digest": check.check_manifest_digest,
        "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
        "verifier_image_digest": check.verifier_image_digest,
        "verifier_deps_digest": check.verifier_deps_digest,
        "agent_manifest_digest": agent.agent_manifest_digest,
        "model_snapshot_id": agent.model_snapshot_id,
        "harness_digest": agent.harness_digest,
        "repository_instruction_digest": agent.repository_instruction_digest,
        "prompt_digest": agent.prompt_digest,
        "tools_digest": agent.tools_digest,
        "retrieval_digest": agent.retrieval_digest,
        "skills_digest": agent.skills_digest,
        "network_policy_digest": agent.network_policy_digest,
        "adapter_digest": agent.adapter_digest,
        "scoring_config_digest": scoring_config.scoring_config_digest,
    }
    mismatched = [field for field, expected in expected_fields.items() if getattr(identity, field) != expected]
    if mismatched:
        raise ValueError(f"cache identity does not match result inputs: {', '.join(mismatched)}")


def _normalize_result_state(workspace_run: WorkspaceRunRecord) -> tuple[str, str, str | None]:
    if workspace_run.terminal_status == "passed" and workspace_run.check_outcome == "pass":
        return ("scoreable", "pass", None)
    if workspace_run.terminal_status == "failed" or workspace_run.check_outcome == "fail":
        return ("scoreable", "fail", None)
    invalid_owner = workspace_run.invalid_owner
    if workspace_run.terminal_status in {"error", "timeout"}:
        invalid_owner = invalid_owner or "agent"
    if invalid_owner == "agent":
        return ("agent_invalid", "invalid", "agent")
    return ("benchmark_invalid", "invalid", invalid_owner or "benchmark")


def _cost_from_usage(usage: Mapping[str, Any], scoring_config: ScoringConfig) -> Mapping[str, Any]:
    costs: dict[str, Any] = {}
    total = 0.0
    for key, rate in scoring_config.cost_rates.items():
        value = usage.get(key)
        if isinstance(value, int | float):
            amount = float(value) * float(rate)
            costs[f"{key}_cost"] = amount
            total += amount
    costs["total_cost"] = total
    return costs


def _latency_from_workspace_run(workspace_run: WorkspaceRunRecord) -> Mapping[str, Any]:
    return {"workspace_seconds": _timestamp_delta_seconds(workspace_run.started_at, workspace_run.finished_at)}


def _timestamp_delta_seconds(started_at: str, finished_at: str) -> float:
    started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    return max(0.0, (finished - started).total_seconds())


def _verifier_metadata_digest(workspace_run: WorkspaceRunRecord) -> str:
    return canonical_digest(
        {
            "workspace_run_id": workspace_run.workspace_run_id,
            "solver_workspace_digest": workspace_run.solver_workspace_digest,
            "verifier_workspace_digest": workspace_run.verifier_workspace_digest,
            "replay_status": workspace_run.replay_status,
            "check_outcome": workspace_run.check_outcome,
        }
    )


def _matches_query(result: ResultRecord, query: ResultQuery) -> bool:
    if query.task_ids and result.task_id not in query.task_ids:
        return False
    if query.check_ids and result.check_id not in query.check_ids:
        return False
    if query.agent_ids and result.agent_id not in query.agent_ids:
        return False
    if query.result_ids and result.result_id not in query.result_ids:
        return False
    if query.cache_identity_digests and result.cache_identity.identity_digest not in query.cache_identity_digests:
        return False
    if query.scoring_config_digests and result.cache_identity.scoring_config_digest not in query.scoring_config_digests:
        return False
    if query.result_available_after and result.result_available_at < query.result_available_after:
        return False
    if query.result_available_before and result.result_available_at > query.result_available_before:
        return False
    return True


def _find_reusable_result(
    results: Sequence[ResultRecord],
    identity: ResultCacheIdentity,
    cache_config: ResultCacheConfig,
    agent_id: str,
    task_id: str,
    check_id: str,
) -> ResultRecord | None:
    identity_validation = validate_result_cache_identity(identity)
    if not identity_validation.ok:
        return None
    for result in results:
        if result.agent_id != agent_id or result.task_id != task_id or result.check_id != check_id:
            continue
        if result.cache_identity != identity:
            continue
        if cache_config.require_valid_result and not validate_result(result).ok:
            continue
        return result
    return None


def _task_for_ref(ref: TaskCheckRef, tasks: Mapping[str, TaskRecord]) -> TaskRecord:
    task = tasks.get(ref.task_id)
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


def _matrix_refs(evaluation_cells: EvaluationCellSet, matrix_role: str) -> tuple[TaskCheckRef, ...]:
    if matrix_role == "selected":
        return evaluation_cells.selected_task_check_refs
    if matrix_role == "future_holdout":
        return evaluation_cells.future_task_check_refs
    raise ValueError("matrix_role is not normalized")


def _results_by_cell(results: Sequence[ResultRecord]) -> Mapping[tuple[str, str, str, str], ResultRecord]:
    by_cell: dict[tuple[str, str, str, str], ResultRecord] = {}
    for result in results:
        validation = validate_result(result)
        if not validation.ok:
            continue
        by_cell[(result.agent_id, result.task_id, result.check_id, result.cache_identity.identity_digest)] = result
    return by_cell


def _required_cells_by_key(
    cells: Sequence[ResultCellRef],
    refs: Sequence[TaskCheckRef],
    agents: Sequence[AgentRecord],
) -> Mapping[tuple[str, str, str], ResultCellRef]:
    allowed_refs = {(ref.task_id, ref.check_id) for ref in refs}
    allowed_agents = {agent.agent_id for agent in agents}
    by_key: dict[tuple[str, str, str], ResultCellRef] = {}
    for cell in cells:
        if cell.agent_id in allowed_agents and (cell.task_id, cell.check_id) in allowed_refs:
            by_key[(cell.agent_id, cell.task_id, cell.check_id)] = cell
    return by_key


def _task_check_exclusions(
    required_cells: Mapping[tuple[str, str, str], ResultCellRef],
    result_by_cell: Mapping[tuple[str, str, str, str], ResultRecord],
    join_config: ResultJoinConfig,
) -> Mapping[tuple[str, str], str]:
    if join_config.benchmark_invalid_policy != "exclude_task_check":
        return {}
    exclusions: dict[tuple[str, str], str] = {}
    for required in required_cells.values():
        result = result_by_cell.get((required.agent_id, required.task_id, required.check_id, required.required_identity_digest))
        if result is None or result.invalid_owner != "benchmark":
            continue
        reason = result.failure_label or "benchmark_invalid"
        exclusions[(required.task_id, required.check_id)] = (
            f"task_check_infrastructure_failure:{reason}:{result.result_digest}"
        )
    return exclusions


def _matrix_cell(
    required: ResultCellRef,
    result: ResultRecord | None,
    join_config: ResultJoinConfig,
    task_exclusion_reason: str | None,
) -> ResultCellRef:
    if task_exclusion_reason is not None:
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=result.result_id if result is not None else None,
            result_digest=result.result_digest if result is not None else None,
            cell_state="excluded",
            exclusion_reason=task_exclusion_reason,
            outcome=result.outcome if result is not None else None,
        )
    if result is None:
        if join_config.missing_cell_policy == "error":
            raise ValueError("missing required result cell")
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=None,
            result_digest=None,
            cell_state="missing",
            exclusion_reason=None,
            outcome=None,
        )
    if result.invalid_owner == "agent" and join_config.agent_invalid_policy == "exclude":
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=result.result_id,
            result_digest=result.result_digest,
            cell_state="excluded",
            exclusion_reason=result.failure_label or "agent_invalid",
            outcome=result.outcome,
        )
    return ResultCellRef(
        agent_id=required.agent_id,
        task_id=required.task_id,
        check_id=required.check_id,
        required_identity_digest=required.required_identity_digest,
        result_id=result.result_id,
        result_digest=result.result_digest,
        cell_state="result",
        exclusion_reason=None,
        outcome=result.outcome,
    )


def _abstention_reason(cells: Sequence[ResultCellRef], join_config: ResultJoinConfig) -> str | None:
    if join_config.abstention_policy == "abstain_on_missing" and any(cell.cell_state == "missing" for cell in cells):
        return "missing_required_results"
    return None


def _matrix_scoreable_state(cells: Sequence[ResultCellRef]) -> str:
    if any(cell.cell_state == "missing" for cell in cells):
        return "incomplete"
    if any(cell.cell_state == "excluded" for cell in cells):
        return "complete_with_exclusions"
    return "complete"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
