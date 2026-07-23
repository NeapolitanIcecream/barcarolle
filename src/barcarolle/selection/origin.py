"""Rolling-origin construction for Selection."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    CheckRecord,
    RollingOriginRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    format_utc_timestamp,
    make_rolling_origin_id,
    make_rolling_origin_policy_digest,
    parse_utc_timestamp,
    record_with_digest,
    validate_rolling_origin,
    validate_benchmark_selection,
    utc_now_timestamp,
)
from barcarolle.task_pool import TimeRange


@dataclass(frozen=True)
class RollingOriginPolicy:
    as_of_cutoff_rule: str
    eligibility_mode: str
    holdout_overlap_policy: str
    future_holdout_known: bool
    maturity_lag_seconds: int = 0
    allowed_dependency_cluster_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.future_holdout_known) is not bool:
            raise ValueError("future_holdout_known must be a boolean")
        if self.eligibility_mode not in {"strict_prospective", "counterfactual_replay"}:
            raise ValueError(
                "eligibility_mode must be strict_prospective or counterfactual_replay"
            )
        if self.holdout_overlap_policy not in {
            "allow_cluster_overlap",
            "disjoint_clusters",
        }:
            raise ValueError(
                "holdout_overlap_policy must be allow_cluster_overlap or disjoint_clusters"
            )
        if self.eligibility_mode == "strict_prospective" and self.future_holdout_known:
            raise ValueError("strict_prospective must not know future holdout refs")
        if (
            isinstance(self.maturity_lag_seconds, bool)
            or not isinstance(self.maturity_lag_seconds, int)
            or self.maturity_lag_seconds < 0
        ):
            raise ValueError("maturity_lag_seconds must be a nonnegative integer")
        if type(self.allowed_dependency_cluster_ids) is not tuple or any(
            type(cluster_id) is not str or not cluster_id
            for cluster_id in self.allowed_dependency_cluster_ids
        ):
            raise ValueError(
                "allowed_dependency_cluster_ids must be a tuple of nonempty strings"
            )
        if len(self.allowed_dependency_cluster_ids) != len(
            set(self.allowed_dependency_cluster_ids)
        ):
            raise ValueError(
                "allowed_dependency_cluster_ids must not contain duplicates"
            )
        object.__setattr__(
            self,
            "allowed_dependency_cluster_ids",
            tuple(sorted(self.allowed_dependency_cluster_ids)),
        )

    @property
    def policy_digest(self) -> str:
        return make_rolling_origin_policy_digest(
            as_of_cutoff_rule=self.as_of_cutoff_rule,
            eligibility_mode=self.eligibility_mode,
            holdout_overlap_policy=self.holdout_overlap_policy,
            future_holdout_known=self.future_holdout_known,
            allowed_dependency_cluster_ids=self.allowed_dependency_cluster_ids,
            maturity_lag_seconds=self.maturity_lag_seconds,
        )


def build_rolling_origin(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    origin_time: datetime,
    future_window: TimeRange,
    policy: RollingOriginPolicy,
    *,
    history_window: TimeRange | None = None,
) -> RollingOriginRecord:
    _ensure_origin_member_records(task_pool, tasks, checks)
    _ensure_time_range_order(future_window)
    origin_time_iso = format_utc_timestamp(origin_time)
    as_of_cutoff = (
        origin_time_iso
        if policy.as_of_cutoff_rule == "origin_time"
        else policy.as_of_cutoff_rule
    )
    if _instant_gt(as_of_cutoff, origin_time_iso):
        raise ValueError("as_of_cutoff must not be after origin_time")
    as_of_cutoff = format_utc_timestamp(parse_utc_timestamp(as_of_cutoff))
    effective_history_window: TimeRange | None = None
    history_window_start: str | None = None
    if history_window is not None:
        _ensure_time_range_order(history_window)
        if not _time_range_contains(history_window, as_of_cutoff):
            raise ValueError("as_of_cutoff must be inside history_window")
        history_window_start = format_utc_timestamp(
            parse_utc_timestamp(history_window.start)
        )
        effective_history_window = TimeRange(history_window_start, as_of_cutoff)
    label_maturity_cutoff = format_utc_timestamp(
        parse_utc_timestamp(future_window.end)
        + timedelta(seconds=policy.maturity_lag_seconds)
    )
    (
        ordered_history_refs,
        ordered_history_censored_refs,
        ordered_future_refs,
        ordered_censored_refs,
    ) = _rolling_origin_cohorts(
        task_pool,
        tasks,
        checks,
        as_of_cutoff,
        effective_history_window,
        future_window,
        label_maturity_cutoff,
        policy,
    )
    _enforce_holdout_overlap_policy(
        (*ordered_history_refs, *ordered_history_censored_refs),
        (*ordered_future_refs, *ordered_censored_refs),
        tasks,
        policy,
    )
    origin = RollingOriginRecord(
        origin_id="",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time=origin_time_iso,
        policy_digest=policy.policy_digest,
        history_task_check_refs=ordered_history_refs,
        history_censored_task_check_refs=ordered_history_censored_refs,
        future_holdout_task_check_refs=ordered_future_refs,
        future_censored_task_check_refs=ordered_censored_refs,
        as_of_cutoff=as_of_cutoff,
        eligibility_mode=policy.eligibility_mode,
        holdout_overlap_policy=policy.holdout_overlap_policy,
        as_of_cutoff_rule=policy.as_of_cutoff_rule,
        history_window_start=history_window_start,
        future_window_start=format_utc_timestamp(
            parse_utc_timestamp(future_window.start)
        ),
        future_window_end=format_utc_timestamp(parse_utc_timestamp(future_window.end)),
        future_cohort_time_basis="task_material_available_at",
        maturity_lag_seconds=policy.maturity_lag_seconds,
        label_maturity_cutoff=label_maturity_cutoff,
        future_holdout_known=policy.future_holdout_known,
        allowed_dependency_cluster_ids=policy.allowed_dependency_cluster_ids,
        origin_digest="",
    )
    origin = replace(origin, origin_id=make_rolling_origin_id(origin))
    origin = record_with_digest(origin)
    validation = validate_rolling_origin(origin)
    if not validation.ok:
        raise ValueError(f"rolling origin is invalid: {', '.join(validation.errors)}")
    return origin


def materialize_prospective_future_cohort(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    selection_task_pool: TaskPoolRecord,
    future_task_pool: TaskPoolRecord,
    selection_tasks: Sequence[TaskRecord],
    selection_checks: Mapping[str, CheckRecord],
    future_tasks: Sequence[TaskRecord],
    future_checks: Mapping[str, CheckRecord],
) -> tuple[tuple[TaskCheckRef, ...], tuple[TaskCheckRef, ...]]:
    selection_validation = validate_benchmark_selection(selection)
    origin_validation = validate_rolling_origin(origin)
    if not selection_validation.ok:
        raise ValueError(
            "benchmark selection is invalid: " + ", ".join(selection_validation.errors)
        )
    if not origin_validation.ok:
        raise ValueError(
            "rolling origin is invalid: " + ", ".join(origin_validation.errors)
        )
    _ensure_origin_member_records(
        selection_task_pool, selection_tasks, selection_checks
    )
    _ensure_origin_member_records(future_task_pool, future_tasks, future_checks)
    if (
        selection.origin_id != origin.origin_id
        or selection.task_pool_id != selection_task_pool.task_pool_id
        or selection.task_pool_digest != selection_task_pool.task_pool_digest
        or origin.task_pool_id != selection_task_pool.task_pool_id
        or origin.task_pool_digest != selection_task_pool.task_pool_digest
    ):
        raise ValueError("selection, origin, and selection Task Pool do not match")
    if selection.eligibility_mode != "strict_prospective" or (
        origin.eligibility_mode != "strict_prospective"
    ):
        raise ValueError(
            "prospective future cohort requires strict_prospective evidence"
        )
    if (
        origin.future_holdout_known
        or origin.future_holdout_task_check_refs
        or (origin.future_censored_task_check_refs)
    ):
        raise ValueError("strict-prospective Origin must not contain future refs")
    if selection_task_pool.repository_id != future_task_pool.repository_id:
        raise ValueError(
            "future Task Pool repository does not match selection Task Pool"
        )
    if selection_task_pool.generator_config_digest != (
        future_task_pool.generator_config_digest
    ):
        raise ValueError("future Task Pool generator config has changed")
    if selection_task_pool.certification_config_digest != (
        future_task_pool.certification_config_digest
    ):
        raise ValueError("future Task Pool certification config has changed")
    if (
        selection_task_pool.task_pool_id == future_task_pool.task_pool_id
        or selection_task_pool.task_pool_digest == future_task_pool.task_pool_digest
    ):
        raise ValueError("prospective evaluation requires a later Task Pool snapshot")
    _validate_prospective_times(
        selection, origin, selection_task_pool, future_task_pool
    )
    _validate_prospective_source_windows(origin, selection_task_pool, future_task_pool)
    merged_tasks = _merged_snapshot_tasks(selection_tasks, future_tasks)
    _validate_shared_snapshot_checks(selection_checks, future_checks)
    policy = RollingOriginPolicy(
        as_of_cutoff_rule=origin.as_of_cutoff_rule,
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy=origin.holdout_overlap_policy,
        future_holdout_known=True,
        maturity_lag_seconds=origin.maturity_lag_seconds,
        allowed_dependency_cluster_ids=origin.allowed_dependency_cluster_ids,
    )
    _, _, future_refs, censored_refs = _rolling_origin_cohorts(
        future_task_pool,
        future_tasks,
        future_checks,
        origin.as_of_cutoff,
        None,
        TimeRange(origin.future_window_start, origin.future_window_end),
        origin.label_maturity_cutoff,
        policy,
    )
    _enforce_holdout_overlap_policy(
        (*origin.history_task_check_refs, *origin.history_censored_task_check_refs),
        (*future_refs, *censored_refs),
        merged_tasks,
        policy,
    )
    return future_refs, censored_refs


def _validate_prospective_times(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    selection_task_pool: TaskPoolRecord,
    future_task_pool: TaskPoolRecord,
) -> None:
    selection_time = parse_utc_timestamp(selection.created_at)
    if parse_utc_timestamp(selection_task_pool.created_at) > selection_time:
        raise ValueError("selection Task Pool was created after the Selection")
    if selection_time >= parse_utc_timestamp(origin.future_window_start):
        raise ValueError("Selection must predate the prospective future window")
    if parse_utc_timestamp(future_task_pool.created_at) <= selection_time:
        raise ValueError("future Task Pool must be created after the Selection")
    if parse_utc_timestamp(future_task_pool.created_at) < parse_utc_timestamp(
        origin.label_maturity_cutoff
    ):
        raise ValueError("future Task Pool predates the label-maturity cutoff")


def _validate_prospective_source_windows(
    origin: RollingOriginRecord,
    selection_task_pool: TaskPoolRecord,
    future_task_pool: TaskPoolRecord,
) -> None:
    selection_start = selection_task_pool.source_window_start
    selection_end = selection_task_pool.source_window_end
    future_start = future_task_pool.source_window_start
    future_end = future_task_pool.source_window_end
    if not all(
        isinstance(value, str) and value
        for value in (selection_start, selection_end, future_start, future_end)
    ):
        raise ValueError("prospective evaluation requires Task Pool source windows")
    assert isinstance(selection_start, str)
    assert isinstance(future_start, str)
    assert isinstance(future_end, str)
    if parse_utc_timestamp(future_start) > parse_utc_timestamp(selection_start):
        raise ValueError("future Task Pool source window drops prior source coverage")
    if parse_utc_timestamp(future_end) < parse_utc_timestamp(origin.future_window_end):
        raise ValueError(
            "future Task Pool does not cover the prospective future window"
        )


def _merged_snapshot_tasks(
    selection_tasks: Sequence[TaskRecord],
    future_tasks: Sequence[TaskRecord],
) -> tuple[TaskRecord, ...]:
    merged = {task.task_id: task for task in selection_tasks}
    for task in future_tasks:
        existing = merged.get(task.task_id)
        if existing is not None and existing != task:
            raise ValueError("Task record changed across Task Pool snapshots")
        merged[task.task_id] = task
    return tuple(merged.values())


def _validate_shared_snapshot_checks(
    selection_checks: Mapping[str, CheckRecord],
    future_checks: Mapping[str, CheckRecord],
) -> None:
    for check_id in set(selection_checks) & set(future_checks):
        if selection_checks[check_id] != future_checks[check_id]:
            raise ValueError("Check record changed across Task Pool snapshots")


def _ensure_origin_member_records(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    task_by_id = {task.task_id: task for task in tasks}
    if len(task_by_id) != len(tasks):
        raise ValueError("rolling-origin inputs contain duplicate TaskRecord IDs")
    missing_task_ids = sorted(set(task_pool.task_ids) - set(task_by_id))
    if missing_task_ids:
        raise ValueError(
            "rolling-origin inputs are missing TaskPoolRecord task IDs: "
            + ", ".join(missing_task_ids)
        )
    missing_check_ids = sorted(set(task_pool.check_ids) - set(checks))
    if missing_check_ids:
        raise ValueError(
            "rolling-origin inputs are missing TaskPoolRecord check IDs: "
            + ", ".join(missing_check_ids)
        )
    task_pool_task_ids = set(task_pool.task_ids)
    for check_id in task_pool.check_ids:
        check = checks[check_id]
        task = task_by_id.get(check.task_id)
        if (
            check.check_id != check_id
            or check.task_id not in task_pool_task_ids
            or task is None
            or check_id not in task.check_ids
        ):
            raise ValueError(
                "rolling-origin Task/Check linkage does not match TaskPoolRecord"
            )


def _rolling_origin_cohorts(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    as_of_cutoff: str,
    effective_history_window: TimeRange | None,
    future_window: TimeRange,
    label_maturity_cutoff: str,
    policy: RollingOriginPolicy,
) -> tuple[
    tuple[TaskCheckRef, ...],
    tuple[TaskCheckRef, ...],
    tuple[TaskCheckRef, ...],
    tuple[TaskCheckRef, ...],
]:
    history_refs: list[tuple[datetime, TaskCheckRef]] = []
    history_censored_refs: list[tuple[datetime, TaskCheckRef]] = []
    future_refs: list[tuple[datetime, TaskCheckRef]] = []
    censored_refs: list[tuple[datetime, TaskCheckRef]] = []
    for task in tasks:
        if task.task_id not in task_pool.task_ids:
            continue
        if (
            policy.allowed_dependency_cluster_ids
            and task.dependency_cluster_id not in policy.allowed_dependency_cluster_ids
        ):
            continue
        for check_id in task.check_ids:
            if check_id not in task_pool.check_ids:
                continue
            check = checks[check_id]
            arrived_at = task.task_material_available_at
            label_known_at = _task_check_known_at_for_policy(
                task, check, task_pool, policy
            )
            ref = TaskCheckRef(task.task_id, check.check_id)
            in_history_cohort = _instant_lte(arrived_at, as_of_cutoff) and (
                effective_history_window is None
                or _time_range_contains(effective_history_window, arrived_at)
            )
            if in_history_cohort:
                target = (
                    history_refs
                    if _instant_lte(label_known_at, as_of_cutoff)
                    else history_censored_refs
                )
                target.append((parse_utc_timestamp(arrived_at), ref))
            elif (
                policy.future_holdout_known
                and _instant_gt(arrived_at, as_of_cutoff)
                and _time_range_contains(future_window, arrived_at)
            ):
                target = (
                    future_refs
                    if _instant_lte(label_known_at, label_maturity_cutoff)
                    else censored_refs
                )
                target.append((parse_utc_timestamp(arrived_at), ref))
    return (
        _chronological_refs(history_refs),
        _chronological_refs(history_censored_refs),
        _chronological_refs(future_refs),
        _chronological_refs(censored_refs),
    )


def validate_rolling_origin_against_records(
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> ValidationResult:
    errors = list(validate_rolling_origin(origin).errors)
    if (
        origin.task_pool_id != task_pool.task_pool_id
        or origin.task_pool_digest != task_pool.task_pool_digest
    ):
        errors.append("origin does not match TaskPoolRecord")
    if set(task_pool.task_ids) != {task.task_id for task in tasks}:
        errors.append("Task records do not exactly match TaskPoolRecord")
    if set(task_pool.check_ids) != set(checks):
        errors.append("Check records do not exactly match TaskPoolRecord")
    if errors:
        return ValidationResult.fail(errors)
    try:
        policy = RollingOriginPolicy(
            as_of_cutoff_rule=origin.as_of_cutoff_rule,
            eligibility_mode=origin.eligibility_mode,
            holdout_overlap_policy=origin.holdout_overlap_policy,
            future_holdout_known=origin.future_holdout_known,
            maturity_lag_seconds=origin.maturity_lag_seconds,
            allowed_dependency_cluster_ids=origin.allowed_dependency_cluster_ids,
        )
        history_window = (
            None
            if origin.history_window_start is None
            else TimeRange(origin.history_window_start, origin.as_of_cutoff)
        )
        expected = build_rolling_origin(
            task_pool,
            tasks,
            checks,
            parse_utc_timestamp(origin.origin_time),
            TimeRange(origin.future_window_start, origin.future_window_end),
            policy,
            history_window=history_window,
        )
    except ValueError as exc:
        return ValidationResult.fail((f"origin policy cannot be replayed: {exc}",))
    if expected.history_task_check_refs != origin.history_task_check_refs:
        errors.append("history refs do not match rolling-origin policy and records")
    if (
        expected.history_censored_task_check_refs
        != origin.history_censored_task_check_refs
    ):
        errors.append("history censored refs do not match policy and records")
    if expected.future_holdout_task_check_refs != origin.future_holdout_task_check_refs:
        errors.append("future refs do not match rolling-origin policy and records")
    if (
        expected.future_censored_task_check_refs
        != origin.future_censored_task_check_refs
    ):
        errors.append("censored refs do not match rolling-origin policy and records")
    return ValidationResult.fail(errors) if errors else ValidationResult.pass_()


def compare_arrival_and_label_time_cohorts(
    origin: RollingOriginRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> Mapping[str, Any]:
    validation = validate_rolling_origin(origin)
    if not validation.ok:
        raise ValueError("rolling origin is invalid: " + ", ".join(validation.errors))
    if not origin.future_holdout_known:
        raise ValueError("cohort comparison requires a known future holdout")
    arrival_refs = (
        *origin.future_holdout_task_check_refs,
        *origin.future_censored_task_check_refs,
    )
    arrival_keys = {(ref.task_id, ref.check_id) for ref in arrival_refs}
    label_time_keys: set[tuple[str, str]] = set()
    tasks_by_id = {task.task_id: task for task in tasks}
    for task in tasks:
        if (
            origin.allowed_dependency_cluster_ids
            and task.dependency_cluster_id not in origin.allowed_dependency_cluster_ids
        ):
            continue
        for check_id in task.check_ids:
            check = checks.get(check_id)
            if check is None or check.task_id != task.task_id:
                continue
            label_time = _task_check_known_at(task, check)
            if _instant_gt(label_time, origin.as_of_cutoff) and _time_range_contains(
                TimeRange(origin.future_window_start, origin.future_window_end),
                label_time,
            ):
                label_time_keys.add((task.task_id, check.check_id))
    label_delays = sorted(
        (
            parse_utc_timestamp(
                _task_check_known_at(
                    tasks_by_id[ref.task_id],
                    checks[ref.check_id],
                )
            )
            - parse_utc_timestamp(tasks_by_id[ref.task_id].task_material_available_at)
        ).total_seconds()
        for ref in arrival_refs
    )
    future_count = len(arrival_refs)
    mature_count = len(origin.future_holdout_task_check_refs)
    return {
        "origin_id": origin.origin_id,
        "future_cohort_time_basis": origin.future_cohort_time_basis,
        "maturity_lag_seconds": origin.maturity_lag_seconds,
        "label_maturity_cutoff": origin.label_maturity_cutoff,
        "arrival_cohort_count": future_count,
        "arrival_mature_count": mature_count,
        "arrival_censored_count": len(origin.future_censored_task_check_refs),
        "mature_inclusion_rate": (
            mature_count / future_count if future_count else None
        ),
        "legacy_label_time_cohort_count": len(label_time_keys),
        "shared_cohort_count": len(arrival_keys & label_time_keys),
        "arrival_only_count": len(arrival_keys - label_time_keys),
        "label_time_only_count": len(label_time_keys - arrival_keys),
        "label_delay_seconds": _distribution_summary(label_delays),
    }


def _task_known_at(task: TaskRecord) -> str:
    return _max_timestamp(task.source_resolved_at, task.task_material_available_at)


def _distribution_summary(values: Sequence[float]) -> Mapping[str, float | int]:
    if not values:
        return {}
    ordered = tuple(sorted(values))
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": median,
        "max": ordered[-1],
    }


def _task_check_known_at(task: TaskRecord, check: CheckRecord) -> str:
    return _max_timestamp(_task_known_at(task), check.check_material_available_at)


def _task_check_known_at_for_policy(
    task: TaskRecord,
    check: CheckRecord,
    task_pool: TaskPoolRecord,
    policy: RollingOriginPolicy,
) -> str:
    material_known_at = _task_check_known_at(task, check)
    if policy.eligibility_mode == "counterfactual_replay":
        return material_known_at
    return _max_timestamp(material_known_at, task_pool.created_at)


def _chronological_refs(
    entries: Sequence[tuple[datetime, TaskCheckRef]],
) -> tuple[TaskCheckRef, ...]:
    return tuple(
        ref
        for _, ref in sorted(
            entries,
            key=lambda entry: (entry[0], entry[1].task_id, entry[1].check_id),
        )
    )


def _enforce_holdout_overlap_policy(
    history_refs: Sequence[TaskCheckRef],
    future_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    policy: RollingOriginPolicy,
) -> None:
    if policy.holdout_overlap_policy == "allow_cluster_overlap":
        return
    cluster_by_task_id = {task.task_id: task.dependency_cluster_id for task in tasks}
    referenced_task_ids = {ref.task_id for ref in (*history_refs, *future_refs)}
    missing_clusters = tuple(
        sorted(
            task_id
            for task_id in referenced_task_ids
            if not cluster_by_task_id.get(task_id)
        )
    )
    if missing_clusters:
        raise ValueError(
            "disjoint_clusters requires dependency_cluster_id for: "
            + ", ".join(missing_clusters)
        )
    history_clusters = {cluster_by_task_id[ref.task_id] for ref in history_refs}
    future_clusters = {cluster_by_task_id[ref.task_id] for ref in future_refs}
    overlap = tuple(sorted(history_clusters & future_clusters))
    if overlap:
        raise ValueError("history and future clusters overlap: " + ", ".join(overlap))


def _ensure_time_range_order(time_range: TimeRange) -> None:
    if _instant_gt(time_range.start, time_range.end):
        raise ValueError("time range start must be before end")


def _instant_lte(left: str, right: str) -> bool:
    return parse_utc_timestamp(left) <= parse_utc_timestamp(right)


def _instant_gt(left: str, right: str) -> bool:
    return parse_utc_timestamp(left) > parse_utc_timestamp(right)


def _time_range_contains(time_range: TimeRange, value: str) -> bool:
    instant = parse_utc_timestamp(value)
    return (
        parse_utc_timestamp(time_range.start)
        <= instant
        <= parse_utc_timestamp(time_range.end)
    )


def _max_timestamp(*values: str) -> str:
    return max(values, key=parse_utc_timestamp)


def _now() -> str:
    return utc_now_timestamp()
