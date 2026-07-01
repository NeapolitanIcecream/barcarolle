"""Rolling-origin construction for Selection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Mapping, Sequence

from barcarolle.records import CheckRecord, RollingOriginRecord, TaskCheckRef, TaskPoolRecord, TaskRecord, canonical_digest
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


def _task_known_at(task: TaskRecord) -> str:
    return _max_timestamp(task.source_resolved_at, task.task_material_available_at, task.certified_at)


def _task_check_known_at(task: TaskRecord, check: CheckRecord) -> str:
    return _max_timestamp(_task_known_at(task), check.check_material_available_at, check.certified_at)


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
