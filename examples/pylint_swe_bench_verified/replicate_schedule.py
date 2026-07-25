#!/usr/bin/env python3
"""Freeze a deterministic paired-replicate schedule before paid execution."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, replace
import math
from pathlib import Path
import sys
from typing import Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    CheckRecord,
    ResultCellRef,
    RuntimeConfig,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    WorkspaceConfig,
    canonical_digest,
    load_jsonl_records,
    record_with_digest,
    validate_agent,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultCacheConfig,
    ResultStore,
    ResultStoreSession,
    ScoringConfig,
    open_result_store_session,
    resolve_result_cells,
)
from barcarolle.task_pool import validate_task_pool_members  # noqa: E402


SCHEDULE_SCHEMA_VERSION = "paired_replicate_schedule_v1"
SINGLE_AGENT_CANARY_SCHEMA_VERSION = "single_agent_canary_schedule_v1"
RUNTIME_SLOT_VERSION = "experiment_replicate_runtime_slot_v1"


@dataclass(frozen=True)
class ReplicateScheduleCell:
    sequence_index: int
    block_index: int
    within_block_index: int
    task_id: str
    check_id: str
    agent_id: str
    replicate_index: int
    runtime_config_id: str
    runtime_config_digest: str


@dataclass(frozen=True)
class ReplicateSchedule:
    schema_version: str
    campaign_id: str
    task_pool_id: str
    task_pool_digest: str
    task_records_digest: str
    check_records_digest: str
    agent_records_digest: str
    base_runtime_config_digest: str
    seed: int
    requested_replicate_fraction: float
    actual_replicate_fraction: float
    replicate_count: int
    replicated_task_ids: tuple[str, ...]
    runtime_configs: tuple[RuntimeConfig, ...]
    cells: tuple[ReplicateScheduleCell, ...]
    schedule_digest: str


@dataclass(frozen=True)
class ResolvedReplicateScheduleCell:
    """One frozen schedule cell joined to its exact Result Store state."""

    schedule_cell: ReplicateScheduleCell
    result_cell: ResultCellRef


def build_replicate_schedule(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    *,
    campaign_id: str,
    seed: int,
    replicate_fraction: float = 0.25,
    replicate_count: int = 3,
) -> ReplicateSchedule:
    """Build the exact paired cell order without opening Result evidence."""
    task_by_id = {task.task_id: task for task in tasks}
    check_by_id = {check.check_id: check for check in checks}
    if len(task_by_id) != len(tasks) or set(task_by_id) != set(task_pool.task_ids):
        raise ValueError("tasks must exactly match the frozen Task Pool")
    if len(check_by_id) != len(checks) or set(check_by_id) != set(task_pool.check_ids):
        raise ValueError("checks must exactly match the frozen Task Pool")
    normalized_tasks = tuple(task_by_id[task_id] for task_id in task_pool.task_ids)
    normalized_checks = tuple(check_by_id[check_id] for check_id in task_pool.check_ids)
    normalized_agents = tuple(sorted(agents, key=lambda agent: agent.agent_id))
    _validate_inputs(
        task_pool,
        normalized_tasks,
        normalized_checks,
        normalized_agents,
        base_runtime_config,
        campaign_id=campaign_id,
        seed=seed,
        replicate_fraction=replicate_fraction,
        replicate_count=replicate_count,
    )
    target_count = _replicate_task_count(len(normalized_tasks), replicate_fraction)
    replicated_task_ids = _select_stratified_tasks(
        normalized_tasks,
        target_count,
        seed,
    )
    runtime_configs = tuple(
        _runtime_config_for_slot(base_runtime_config, campaign_id, replicate_index)
        for replicate_index in range(replicate_count)
    )
    runtime_by_index = {
        replicate_index: runtime
        for replicate_index, runtime in enumerate(runtime_configs)
    }
    check_by_task_id = {check.task_id: check for check in normalized_checks}
    replicated = set(replicated_task_ids)
    blocks = [
        (task, replicate_index)
        for task in normalized_tasks
        for replicate_index in range(
            replicate_count if task.task_id in replicated else 1
        )
    ]
    blocks.sort(
        key=lambda block: (
            _rank(
                seed,
                "block_order",
                block[0].task_id,
                str(block[1]),
            ),
            block[0].task_id,
            block[1],
        )
    )
    cells: list[ReplicateScheduleCell] = []
    for block_index, (task, replicate_index) in enumerate(blocks):
        ordered_agents = tuple(
            sorted(
                normalized_agents,
                key=lambda agent: (
                    _rank(
                        seed,
                        "agent_order",
                        task.task_id,
                        str(replicate_index),
                        agent.agent_id,
                    ),
                    agent.agent_id,
                ),
            )
        )
        runtime = runtime_by_index[replicate_index]
        runtime_digest = canonical_digest(runtime)
        check = check_by_task_id[task.task_id]
        for within_block_index, agent in enumerate(ordered_agents):
            cells.append(
                ReplicateScheduleCell(
                    sequence_index=len(cells),
                    block_index=block_index,
                    within_block_index=within_block_index,
                    task_id=task.task_id,
                    check_id=check.check_id,
                    agent_id=agent.agent_id,
                    replicate_index=replicate_index,
                    runtime_config_id=runtime.runtime_config_id,
                    runtime_config_digest=runtime_digest,
                )
            )
    return record_with_digest(
        ReplicateSchedule(
            schema_version=SCHEDULE_SCHEMA_VERSION,
            campaign_id=campaign_id,
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            task_records_digest=canonical_digest(normalized_tasks),
            check_records_digest=canonical_digest(normalized_checks),
            agent_records_digest=canonical_digest(normalized_agents),
            base_runtime_config_digest=canonical_digest(base_runtime_config),
            seed=seed,
            requested_replicate_fraction=replicate_fraction,
            actual_replicate_fraction=target_count / len(normalized_tasks),
            replicate_count=replicate_count,
            replicated_task_ids=replicated_task_ids,
            runtime_configs=runtime_configs,
            cells=tuple(cells),
            schedule_digest="",
        ),
        "schedule_digest",
    )


def build_single_agent_canary_schedule(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    *,
    campaign_id: str,
    seed: int,
    task_id: str,
) -> ReplicateSchedule:
    """Build one exact protocol canary cell without authorizing a paired block."""
    task_by_id = {task.task_id: task for task in tasks}
    check_by_id = {check.check_id: check for check in checks}
    if len(task_by_id) != len(tasks) or set(task_by_id) != set(task_pool.task_ids):
        raise ValueError("tasks must exactly match the frozen Task Pool")
    if len(check_by_id) != len(checks) or set(check_by_id) != set(task_pool.check_ids):
        raise ValueError("checks must exactly match the frozen Task Pool")
    normalized_tasks = tuple(task_by_id[item] for item in task_pool.task_ids)
    normalized_checks = tuple(check_by_id[item] for item in task_pool.check_ids)
    normalized_agents = tuple(sorted(agents, key=lambda agent: agent.agent_id))
    _validate_canary_inputs(
        task_pool,
        normalized_tasks,
        normalized_checks,
        normalized_agents,
        base_runtime_config,
        campaign_id=campaign_id,
        seed=seed,
        task_id=task_id,
    )
    task = task_by_id[task_id]
    check_by_task_id = {check.task_id: check for check in normalized_checks}
    check = check_by_task_id[task.task_id]
    runtime = _runtime_config_for_slot(base_runtime_config, campaign_id, 0)
    runtime_digest = canonical_digest(runtime)
    return record_with_digest(
        ReplicateSchedule(
            schema_version=SINGLE_AGENT_CANARY_SCHEMA_VERSION,
            campaign_id=campaign_id,
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            task_records_digest=canonical_digest(normalized_tasks),
            check_records_digest=canonical_digest(normalized_checks),
            agent_records_digest=canonical_digest(normalized_agents),
            base_runtime_config_digest=canonical_digest(base_runtime_config),
            seed=seed,
            requested_replicate_fraction=0.0,
            actual_replicate_fraction=0.0,
            replicate_count=1,
            replicated_task_ids=(),
            runtime_configs=(runtime,),
            cells=(
                ReplicateScheduleCell(
                    sequence_index=0,
                    block_index=0,
                    within_block_index=0,
                    task_id=task.task_id,
                    check_id=check.check_id,
                    agent_id=normalized_agents[0].agent_id,
                    replicate_index=0,
                    runtime_config_id=runtime.runtime_config_id,
                    runtime_config_digest=runtime_digest,
                ),
            ),
            schedule_digest="",
        ),
        "schedule_digest",
    )


def validate_replicate_schedule(
    schedule: ReplicateSchedule,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
) -> ValidationResult:
    try:
        if schedule.schema_version == SCHEDULE_SCHEMA_VERSION:
            expected = build_replicate_schedule(
                task_pool,
                tasks,
                checks,
                agents,
                base_runtime_config,
                campaign_id=schedule.campaign_id,
                seed=schedule.seed,
                replicate_fraction=schedule.requested_replicate_fraction,
                replicate_count=schedule.replicate_count,
            )
        elif schedule.schema_version == SINGLE_AGENT_CANARY_SCHEMA_VERSION:
            if len(schedule.cells) != 1:
                raise ValueError("single-Agent canary schedule must contain one cell")
            expected = build_single_agent_canary_schedule(
                task_pool,
                tasks,
                checks,
                agents,
                base_runtime_config,
                campaign_id=schedule.campaign_id,
                seed=schedule.seed,
                task_id=schedule.cells[0].task_id,
            )
        else:
            raise ValueError(
                f"unsupported replicate schedule schema: {schedule.schema_version}"
            )
    except (TypeError, ValueError) as exc:
        return ValidationResult.fail((f"schedule inputs are invalid: {exc}",))
    if schedule != expected:
        return ValidationResult.fail(
            ("replicate schedule does not replay from its frozen inputs",)
        )
    return ValidationResult.pass_()


def resolve_replicate_schedule_cells(
    schedule: ReplicateSchedule,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    workspace_config: WorkspaceConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    scoring_config: ScoringConfig | None = None,
    *,
    session: ResultStoreSession | None = None,
) -> tuple[ResolvedReplicateScheduleCell, ...]:
    """Resolve the frozen cell order using each cell's exact Runtime slot."""
    validation = validate_replicate_schedule(
        schedule,
        task_pool,
        tasks,
        checks,
        agents,
        base_runtime_config,
    )
    if not validation.ok:
        raise ValueError(
            f"replicate schedule is invalid: {', '.join(validation.errors)}"
        )
    if session is None:
        with open_result_store_session(store) as owned_session:
            return _resolve_validated_replicate_schedule_cells(
                schedule,
                tasks,
                checks,
                agents,
                workspace_config,
                store,
                cache_config,
                scoring_config,
                owned_session,
            )
    return _resolve_validated_replicate_schedule_cells(
        schedule,
        tasks,
        checks,
        agents,
        workspace_config,
        store,
        cache_config,
        scoring_config,
        session,
    )


def _resolve_validated_replicate_schedule_cells(
    schedule: ReplicateSchedule,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    scoring_config: ScoringConfig | None,
    session: ResultStoreSession,
) -> tuple[ResolvedReplicateScheduleCell, ...]:
    task_by_id = {task.task_id: task for task in tasks}
    check_by_id = {check.check_id: check for check in checks}
    agent_by_id = {agent.agent_id: agent for agent in agents}
    runtime_by_id = {
        runtime.runtime_config_id: runtime for runtime in schedule.runtime_configs
    }
    resolved: list[ResolvedReplicateScheduleCell] = []
    for schedule_cell in schedule.cells:
        runtime = runtime_by_id[schedule_cell.runtime_config_id]
        (result_cell,) = resolve_result_cells(
            (TaskCheckRef(schedule_cell.task_id, schedule_cell.check_id),),
            (task_by_id[schedule_cell.task_id],),
            {schedule_cell.check_id: check_by_id[schedule_cell.check_id]},
            (agent_by_id[schedule_cell.agent_id],),
            workspace_config,
            runtime,
            store,
            cache_config,
            scoring_config,
            session=session,
        )
        resolved.append(
            ResolvedReplicateScheduleCell(
                schedule_cell=schedule_cell,
                result_cell=result_cell,
            )
        )
    return tuple(resolved)


def find_next_missing_replicate_schedule_cell(
    schedule: ReplicateSchedule,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    workspace_config: WorkspaceConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    scoring_config: ScoringConfig | None = None,
    *,
    session: ResultStoreSession | None = None,
) -> ResolvedReplicateScheduleCell | None:
    """Return at most the first missing cell in frozen schedule order."""
    return next(
        (
            resolved
            for resolved in resolve_replicate_schedule_cells(
                schedule,
                task_pool,
                tasks,
                checks,
                agents,
                base_runtime_config,
                workspace_config,
                store,
                cache_config,
                scoring_config,
                session=session,
            )
            if resolved.result_cell.cell_state == "missing"
        ),
        None,
    )


def _validate_inputs(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    *,
    campaign_id: str,
    seed: int,
    replicate_fraction: float,
    replicate_count: int,
) -> None:
    _validate_schedule_parameters(
        campaign_id=campaign_id,
        seed=seed,
        replicate_fraction=replicate_fraction,
        replicate_count=replicate_count,
    )
    _validate_schedule_members(task_pool, tasks, checks)
    _validate_schedule_agents(agents, campaign_id)
    _validate_base_runtime_config(base_runtime_config)


def _validate_canary_inputs(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    agents: Sequence[AgentRecord],
    base_runtime_config: RuntimeConfig,
    *,
    campaign_id: str,
    seed: int,
    task_id: str,
) -> None:
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ValueError("campaign_id must be a nonempty string")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    _validate_schedule_members(task_pool, tasks, checks)
    _validate_canary_agent(agents, campaign_id)
    _validate_base_runtime_config(base_runtime_config)
    if not isinstance(task_id, str) or task_id not in set(task_pool.task_ids):
        raise ValueError("canary task_id must identify one Task Pool member")


def _validate_schedule_parameters(
    *,
    campaign_id: str,
    seed: int,
    replicate_fraction: float,
    replicate_count: int,
) -> None:
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ValueError("campaign_id must be a nonempty string")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if (
        isinstance(replicate_fraction, bool)
        or not isinstance(replicate_fraction, int | float)
        or not math.isfinite(float(replicate_fraction))
        or not 0.20 <= replicate_fraction <= 0.30
    ):
        raise ValueError("replicate_fraction must be between 0.20 and 0.30")
    if (
        isinstance(replicate_count, bool)
        or not isinstance(replicate_count, int)
        or replicate_count not in {2, 3}
    ):
        raise ValueError("replicate_count must be 2 or 3")


def _validate_schedule_members(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
) -> None:
    if not tasks or len({task.task_id for task in tasks}) != len(tasks):
        raise ValueError("tasks must be nonempty with unique task_id values")
    if len({check.check_id for check in checks}) != len(checks):
        raise ValueError("checks must have unique check_id values")
    pool_validation = validate_task_pool_members(task_pool, tasks, checks)
    if not pool_validation.ok:
        raise ValueError(
            f"Task Pool members are invalid: {', '.join(pool_validation.errors)}"
        )
    for task in tasks:
        if len(task.check_ids) != 1:
            raise ValueError("Pylint replicate scheduling requires one Check per Task")
    check_by_task_id: dict[str, CheckRecord] = {}
    for check in checks:
        if check.task_id in check_by_task_id:
            raise ValueError("Pylint replicate scheduling requires one Check per Task")
        check_by_task_id[check.task_id] = check
    if set(check_by_task_id) != {task.task_id for task in tasks}:
        raise ValueError("checks must cover every scheduled Task exactly once")
    for task in tasks:
        if check_by_task_id[task.task_id].check_id != task.check_ids[0]:
            raise ValueError("Task and Check records do not match")


def _validate_schedule_agents(
    agents: Sequence[AgentRecord],
    campaign_id: str,
) -> None:
    if len(agents) != 2 or len({agent.agent_id for agent in agents}) != 2:
        raise ValueError("paired replicate scheduling requires two unique Agents")
    _validate_agent_records(agents, campaign_id)
    configuration_digests = {
        canonical_digest(replace(agent, agent_id="")) for agent in agents
    }
    if len(configuration_digests) != 2:
        raise ValueError(
            "paired replicate scheduling requires two distinct Agent configurations"
        )


def _validate_canary_agent(
    agents: Sequence[AgentRecord],
    campaign_id: str,
) -> None:
    if len(agents) != 1:
        raise ValueError("single-Agent canary scheduling requires exactly one Agent")
    _validate_agent_records(agents, campaign_id)


def _validate_agent_records(
    agents: Sequence[AgentRecord],
    campaign_id: str,
) -> None:
    if len({agent.agent_id for agent in agents}) != len(agents):
        raise ValueError("scheduled Agents must have unique agent_id values")
    for agent in agents:
        validation = validate_agent(agent)
        if not validation.ok:
            raise ValueError(
                f"invalid Agent {agent.agent_id}: {', '.join(validation.errors)}"
            )
        if (
            agent.model_snapshot_id is None
            and agent.model_resolution_scope_id != campaign_id
        ):
            raise ValueError(
                "unresolved Agent model scope must equal the schedule campaign_id"
            )


def _validate_base_runtime_config(base_runtime_config: RuntimeConfig) -> None:
    if (
        not base_runtime_config.runtime_config_id
        or not base_runtime_config.budget_digest
        or not base_runtime_config.retry_policy_digest
        or not base_runtime_config.stochastic_settings_digest
        or isinstance(base_runtime_config.timeout_seconds, bool)
        or not isinstance(base_runtime_config.timeout_seconds, int)
        or base_runtime_config.timeout_seconds <= 0
    ):
        raise ValueError("base RuntimeConfig is incomplete or invalid")


def _replicate_task_count(task_count: int, requested_fraction: float) -> int:
    candidates = tuple(
        count
        for count in range(1, task_count + 1)
        if 0.20 <= count / task_count <= 0.30
    )
    if not candidates:
        raise ValueError(
            "task count cannot realize a 20 to 30 percent replicate subset"
        )
    return min(
        candidates,
        key=lambda count: (abs(count / task_count - requested_fraction), count),
    )


def _select_stratified_tasks(
    tasks: Sequence[TaskRecord],
    target_count: int,
    seed: int,
) -> tuple[str, ...]:
    tasks_by_stratum: dict[str, list[TaskRecord]] = defaultdict(list)
    for task in tasks:
        tasks_by_stratum[task.sampling_stratum].append(task)
    task_count = len(tasks)
    quotas: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    for stratum, stratum_tasks in tasks_by_stratum.items():
        exact = target_count * len(stratum_tasks) / task_count
        quota = math.floor(exact)
        quotas[stratum] = quota
        remainders.append((exact - quota, stratum))
    remaining = target_count - sum(quotas.values())
    for _, stratum in sorted(remainders, key=lambda item: (-item[0], item[1])):
        if not remaining:
            break
        if quotas[stratum] < len(tasks_by_stratum[stratum]):
            quotas[stratum] += 1
            remaining -= 1
    if remaining:
        raise RuntimeError("stratified replicate quota allocation is incomplete")
    selected: list[str] = []
    for stratum in sorted(tasks_by_stratum):
        ranked = sorted(
            tasks_by_stratum[stratum],
            key=lambda task: (
                _rank(seed, "replicate_subset", stratum, task.task_id),
                task.task_id,
            ),
        )
        selected.extend(task.task_id for task in ranked[: quotas[stratum]])
    return tuple(sorted(selected))


def _runtime_config_for_slot(
    base: RuntimeConfig,
    campaign_id: str,
    replicate_index: int,
) -> RuntimeConfig:
    slot_payload = {
        "slot_version": RUNTIME_SLOT_VERSION,
        "campaign_id": campaign_id,
        "replicate_index": replicate_index,
        "base_runtime_config_digest": canonical_digest(base),
        "base_stochastic_settings_digest": base.stochastic_settings_digest,
    }
    slot_digest = canonical_digest(slot_payload)
    return replace(
        base,
        runtime_config_id=f"runtime_{slot_digest}",
        stochastic_settings_digest=slot_digest,
    )


def _rank(seed: int, phase: str, *values: str) -> str:
    return canonical_digest(
        {
            "seed": seed,
            "phase": phase,
            "values": values,
        }
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-pool", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--agents", type=Path, required=True)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--replicate-fraction", type=float, default=0.25)
    parser.add_argument("--replicate-count", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite schedule: {args.output}")
    (task_pool,) = load_jsonl_records(args.task_pool, TaskPoolRecord)
    tasks = tuple(load_jsonl_records(args.tasks, TaskRecord))
    checks = tuple(load_jsonl_records(args.checks, CheckRecord))
    agents = tuple(load_jsonl_records(args.agents, AgentRecord))
    (runtime_config,) = load_jsonl_records(args.runtime_config, RuntimeConfig)
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime_config,
        campaign_id=args.campaign_id,
        seed=args.seed,
        replicate_fraction=args.replicate_fraction,
        replicate_count=args.replicate_count,
    )
    write_jsonl_records(args.output, (schedule,))
    print(
        f"wrote {len(schedule.cells)} cells with "
        f"{len(schedule.replicated_task_ids)} replicated Tasks to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
