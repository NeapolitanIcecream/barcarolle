"""Feature snapshots, leakage linting, and result provenance checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    FeatureRecord,
    FeatureSnapshotRecord,
    ResultRecord,
    RollingOriginRecord,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    canonical_digest,
    make_check_digest,
    validate_feature_snapshot,
    validate_result,
)

from .origin import _instant_gt, _task_known_at


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
            or identity.check_digest != make_check_digest(check)
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
