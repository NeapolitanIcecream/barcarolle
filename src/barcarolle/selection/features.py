"""Feature snapshots, leakage linting, and result provenance checks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    FeatureRecord,
    FeatureSnapshotRecord,
    ResultRecord,
    RollingOriginRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    agent_record_from_cache_identity,
    cache_identity_task_check_mismatches,
    canonical_digest,
    make_feature_snapshot_id,
    record_with_digest,
    validate_feature_snapshot,
    validate_result,
)

from .origin import _instant_gt, _task_known_at


_FEATURE_LEAKAGE_CLASS_BY_NAME = {
    "task_count": "task_metadata",
    "pre_origin_result_count": "pre_origin_result",
    "task_stratum": "task_metadata",
}
_TASK_METADATA_FEATURE_NAMES = frozenset(
    name
    for name, leakage_class in _FEATURE_LEAKAGE_CLASS_BY_NAME.items()
    if leakage_class == "task_metadata"
)


@dataclass(frozen=True)
class FeatureConfig:
    feature_names: tuple[str, ...] = ("task_count", "pre_origin_result_count")

    def __post_init__(self) -> None:
        if not self.feature_names:
            raise ValueError("feature_names must not be empty")
        if any(
            type(name) is not str or not name.strip() for name in self.feature_names
        ):
            raise ValueError("feature_names must contain non-empty strings")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature_names must be unique")
        unsupported = tuple(
            name
            for name in self.feature_names
            if name not in _FEATURE_LEAKAGE_CLASS_BY_NAME
        )
        if unsupported:
            raise ValueError("unsupported feature names: " + ", ".join(unsupported))
        canonical_names = tuple(
            name
            for name in _FEATURE_LEAKAGE_CLASS_BY_NAME
            if name in self.feature_names
        )
        object.__setattr__(self, "feature_names", canonical_names)

    @property
    def allowed_leakage_classes(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                _FEATURE_LEAKAGE_CLASS_BY_NAME[name] for name in self.feature_names
            )
        )

    @property
    def feature_config_digest(self) -> str:
        return canonical_digest(
            {
                "feature_extractor_version": 1,
                "feature_names": self.feature_names,
                "allowed_leakage_classes": self.allowed_leakage_classes,
            }
        )

    def leakage_policy(self, max_observed_at: str) -> LeakagePolicy:
        return LeakagePolicy(self.allowed_leakage_classes, max_observed_at)


@dataclass(frozen=True)
class LeakagePolicy:
    allowed_leakage_classes: tuple[str, ...]
    max_observed_at: str

    @property
    def leakage_policy_digest(self) -> str:
        return canonical_digest(
            {
                "allowed_leakage_classes": self.allowed_leakage_classes,
                "max_observed_at": self.max_observed_at,
            }
        )


def build_feature_snapshot(
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    pre_origin_results: Sequence[ResultRecord],
    feature_config: FeatureConfig,
) -> FeatureSnapshotRecord:
    _ensure_results_allowed(
        pre_origin_results, origin, task_pool, agents=None, tasks=tasks, checks=checks
    )
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
                source_artifact_digest=canonical_digest(
                    tuple(result.result_digest for result in pre_origin_results)
                ),
                leakage_class="pre_origin_result",
            )
        )
    if "task_stratum" in feature_config.feature_names:
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
                    feature_name="task_stratum",
                    value=task.sampling_stratum,
                    observed_at=_task_known_at(task),
                    source_artifact_digest=canonical_digest(task),
                    leakage_class="task_metadata",
                    task_id=task.task_id,
                    check_id=ref.check_id,
                )
            )
    feature_records_tuple = tuple(feature_records)
    result_view_digest = _result_view_digest(pre_origin_results)
    leakage_policy = feature_config.leakage_policy(origin.as_of_cutoff)
    snapshot = FeatureSnapshotRecord(
        feature_snapshot_id="",
        origin_id=origin.origin_id,
        feature_record_ids=tuple(record.feature_id for record in feature_records_tuple),
        feature_records_digest=canonical_digest(feature_records_tuple),
        leakage_policy_digest=leakage_policy.leakage_policy_digest,
        leakage_lint_status="not_run",
        feature_records=feature_records_tuple,
        result_view_digest=result_view_digest,
        feature_config_digest=feature_config.feature_config_digest,
        feature_snapshot_digest="",
    )
    snapshot = replace(
        snapshot,
        feature_snapshot_id=make_feature_snapshot_id(snapshot),
    )
    snapshot = record_with_digest(snapshot)
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        raise ValueError(f"feature snapshot is invalid: {', '.join(validation.errors)}")
    lint = lint_feature_snapshot(snapshot, leakage_policy)
    if not lint.ok:
        raise ValueError(
            f"feature snapshot failed leakage lint: {', '.join(lint.errors)}"
        )
    snapshot = record_with_digest(
        replace(
            snapshot,
            leakage_lint_status="passed",
            feature_snapshot_digest="",
        )
    )
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        raise ValueError(f"feature snapshot is invalid: {', '.join(validation.errors)}")
    ensure_feature_snapshot_task_metadata_provenance(
        snapshot,
        origin,
        task_pool,
        tasks,
    )
    return snapshot


def lint_feature_snapshot(
    snapshot: FeatureSnapshotRecord, policy: LeakagePolicy
) -> ValidationResult:
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
        origin_snapshot_digest=canonical_digest(
            (origin.origin_id, feature_config.feature_config_digest)
        ),
        leakage_class=leakage_class,
    )


def _ensure_feature_records_match_origin(
    snapshot: FeatureSnapshotRecord,
    origin: RollingOriginRecord,
    pre_origin_results: Sequence[ResultRecord],
) -> None:
    _ensure_feature_origin_snapshot_binding(snapshot, origin)
    if snapshot.result_view_digest != _result_view_digest(pre_origin_results):
        raise ValueError(
            "feature snapshot result provenance does not match selector input result view"
        )
    allowed_refs = {
        (ref.task_id, ref.check_id) for ref in origin.history_task_check_refs
    }
    history_task_ids = {task_id for task_id, _ in allowed_refs}
    result_by_id = {result.result_id: result for result in pre_origin_results}
    aggregate_result_digest = canonical_digest(
        tuple(result.result_digest for result in pre_origin_results)
    )
    for record in snapshot.feature_records:
        _ensure_feature_record_in_origin(
            record,
            history_task_ids,
            allowed_refs,
            origin.as_of_cutoff,
        )
        if record.leakage_class == "pre_origin_result":
            _ensure_feature_result_provenance(
                record,
                result_by_id,
                aggregate_result_digest,
                len(pre_origin_results),
            )


def ensure_feature_snapshot_task_metadata_provenance(
    snapshot: FeatureSnapshotRecord,
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
) -> None:
    """Replay Task Pool-backed feature values frozen in a FeatureSnapshot."""
    validation = validate_feature_snapshot(snapshot)
    if not validation.ok:
        raise ValueError("feature snapshot is invalid: " + ", ".join(validation.errors))
    if snapshot.origin_id != origin.origin_id:
        raise ValueError("feature snapshot does not match its origin")
    if (
        origin.task_pool_id != task_pool.task_pool_id
        or origin.task_pool_digest != task_pool.task_pool_digest
    ):
        raise ValueError("feature snapshot origin does not match Task Pool")
    _ensure_feature_origin_snapshot_binding(snapshot, origin)

    records_by_name: dict[str, list[FeatureRecord]] = {}
    for record in snapshot.feature_records:
        if record.feature_name in _TASK_METADATA_FEATURE_NAMES:
            if record.leakage_class != "task_metadata":
                raise ValueError(
                    f"{record.feature_name} feature must use task_metadata provenance"
                )
            records_by_name.setdefault(record.feature_name, []).append(record)
        elif record.leakage_class == "task_metadata":
            raise ValueError(
                "task_metadata provenance is unsupported for feature: "
                + record.feature_name
            )

    task_count_records = records_by_name.get("task_count", [])
    if task_count_records:
        _ensure_task_count_provenance(
            task_count_records,
            origin,
            task_pool,
        )
    task_stratum_records = records_by_name.get("task_stratum", [])
    if task_stratum_records:
        _ensure_task_stratum_provenance(
            task_stratum_records,
            origin,
            tasks,
        )


def _ensure_feature_origin_snapshot_binding(
    snapshot: FeatureSnapshotRecord,
    origin: RollingOriginRecord,
) -> None:
    expected = canonical_digest((origin.origin_id, snapshot.feature_config_digest))
    if any(
        record.origin_snapshot_digest != expected for record in snapshot.feature_records
    ):
        raise ValueError(
            "feature snapshot records do not match frozen Origin/config provenance"
        )


def _ensure_task_count_provenance(
    records: Sequence[FeatureRecord],
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
) -> None:
    if len(records) != 1:
        raise ValueError("task_count must have exactly one provenance record")
    record = records[0]
    expected = replace(
        record,
        feature_scope="origin",
        task_id=None,
        check_id=None,
        agent_id=None,
        result_id=None,
        result_cache_identity_digest=None,
        value=len(origin.history_task_check_refs),
        aggregation_window=None,
        aggregation_method=None,
        observed_at=origin.as_of_cutoff,
        source_artifact_digest=task_pool.task_pool_digest,
    )
    if type(record.value) is not int or record != expected:
        raise ValueError("task_count feature does not match frozen Task Pool")


def _ensure_task_stratum_provenance(
    records: Sequence[FeatureRecord],
    origin: RollingOriginRecord,
    tasks: Sequence[TaskRecord],
) -> None:
    expected_refs = set(origin.history_task_check_refs)
    refs = tuple(
        TaskCheckRef(record.task_id or "", record.check_id or "") for record in records
    )
    if len(set(refs)) != len(refs) or set(refs) != expected_refs:
        raise ValueError(
            "task_stratum features do not exactly cover frozen Origin history"
        )
    task_by_id = {task.task_id: task for task in tasks}
    for record, ref in zip(records, refs, strict=True):
        task = task_by_id.get(ref.task_id)
        if task is None:
            raise ValueError(
                "task_stratum feature does not match frozen Task record: "
                f"{ref.task_id}/{ref.check_id}"
            )
        expected = replace(
            record,
            feature_scope="task",
            agent_id=None,
            result_id=None,
            result_cache_identity_digest=None,
            value=task.sampling_stratum,
            aggregation_window=None,
            aggregation_method=None,
            observed_at=_task_known_at(task),
            source_artifact_digest=canonical_digest(task),
        )
        if record != expected:
            raise ValueError(
                "task_stratum feature does not match frozen Task record: "
                f"{ref.task_id}/{ref.check_id}"
            )


def _ensure_feature_record_in_origin(
    record: FeatureRecord,
    history_task_ids: set[str],
    allowed_refs: set[tuple[str, str]],
    cutoff: str,
) -> None:
    if record.task_id is not None and record.task_id not in history_task_ids:
        raise ValueError("feature snapshot includes task outside origin history")
    if (
        record.check_id is not None
        and (record.task_id, record.check_id) not in allowed_refs
    ):
        raise ValueError("feature snapshot includes check outside origin history")
    if _instant_gt(record.observed_at, cutoff):
        raise ValueError("feature snapshot includes post-origin feature")


def _ensure_feature_result_provenance(
    record: FeatureRecord,
    result_by_id: Mapping[str, ResultRecord],
    aggregate_result_digest: str,
    result_count: int,
) -> None:
    if record.result_id is None:
        if record.source_artifact_digest != aggregate_result_digest:
            raise ValueError(
                "feature snapshot result provenance does not match selector input"
            )
        if (
            record.feature_name == "pre_origin_result_count"
            and record.value != result_count
        ):
            raise ValueError(
                "feature snapshot result count does not match selector input"
            )
        return

    result = result_by_id.get(record.result_id)
    if result is None or record.source_artifact_digest != result.result_digest:
        raise ValueError("feature snapshot includes result outside selector input")
    if (
        (record.task_id is not None and record.task_id != result.task_id)
        or (record.check_id is not None and record.check_id != result.check_id)
        or (record.agent_id is not None and record.agent_id != result.agent_id)
    ):
        raise ValueError(
            "feature snapshot result linkage does not match selector input"
        )
    if (
        record.result_cache_identity_digest is not None
        and record.result_cache_identity_digest != result.cache_identity.identity_digest
    ):
        raise ValueError(
            "feature snapshot result identity does not match selector input"
        )


def _ensure_results_pre_origin(results: Sequence[ResultRecord], cutoff: str) -> None:
    leaked = [
        result.result_id
        for result in results
        if _instant_gt(result.result_available_at, cutoff)
    ]
    if leaked:
        raise ValueError("pre_origin_results include results after the origin cutoff")


def _ensure_results_allowed(
    results: Sequence[ResultRecord],
    origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    agents: Sequence[AgentRecord] | None,
    tasks: Sequence[TaskRecord] | None = None,
    checks: Mapping[str, CheckRecord] | None = None,
) -> None:
    _ensure_result_records_valid(results, "pre_origin_results")
    if tasks is not None and checks is not None:
        _ensure_result_identity_matches_current_records(
            results, tasks, checks, agents=None
        )
    if agents is not None:
        _ensure_result_identity_matches_agents(results, agents)
    _ensure_results_match_origin_scope(
        results,
        origin,
        allowed_agent_ids=(
            {agent.agent_id for agent in agents} if agents is not None else None
        ),
        task_pool=task_pool,
    )


def _ensure_results_match_origin_scope(
    results: Sequence[ResultRecord],
    origin: RollingOriginRecord,
    *,
    allowed_agent_ids: set[str] | None,
    task_pool: TaskPoolRecord | None = None,
) -> None:
    _ensure_results_pre_origin(results, origin.as_of_cutoff)
    allowed_refs = {
        (ref.task_id, ref.check_id) for ref in origin.history_task_check_refs
    }
    for result in results:
        if task_pool is not None and (
            result.task_id not in task_pool.task_ids
            or result.check_id not in task_pool.check_ids
        ):
            raise ValueError("pre_origin_results include off-pool results")
        if (result.task_id, result.check_id) not in allowed_refs:
            raise ValueError(
                "pre_origin_results include results outside origin history refs"
            )
        if allowed_agent_ids is not None and result.agent_id not in allowed_agent_ids:
            raise ValueError(
                "pre_origin_results include results outside candidate Agent set"
            )


def _ensure_result_records_valid(results: Sequence[ResultRecord], label: str) -> None:
    for result in results:
        validation = validate_result(result)
        if not validation.ok:
            raise ValueError(
                f"{label} include invalid ResultRecord: {', '.join(validation.errors)}"
            )


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
            raise ValueError(
                "results include Task/Check identity outside current records"
            )
        if cache_identity_task_check_mismatches(
            result.cache_identity,
            task,
            check,
        ):
            raise ValueError(
                "results include cache identity that does not match current Task/Check records"
            )
    if agents is not None:
        _ensure_result_identity_matches_agents(results, agents)


def _ensure_result_identity_matches_agents(
    results: Sequence[ResultRecord], agents: Sequence[AgentRecord]
) -> None:
    agent_by_id = {agent.agent_id: agent for agent in agents}
    for result in results:
        agent = agent_by_id.get(result.agent_id)
        if agent is None:
            raise ValueError(
                "results include cache identity outside candidate Agent records"
            )
        if (
            agent_record_from_cache_identity(result.agent_id, result.cache_identity)
            != agent
        ):
            raise ValueError(
                "results include cache identity that does not match candidate Agent records"
            )


def _result_view_digest(results: Sequence[ResultRecord]) -> str:
    return canonical_digest(
        tuple(
            (
                result.result_id,
                result.result_digest,
                result.cache_identity.identity_digest,
            )
            for result in results
        )
    )
