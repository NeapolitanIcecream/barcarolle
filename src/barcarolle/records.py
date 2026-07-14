"""Shared record contracts for Barcarolle module boundaries."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import UnionType
from typing import Any, Mapping, Sequence, Union, get_args, get_origin, get_type_hints
import hashlib
import json
import math
import os


JSONValue = Any


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()

    @classmethod
    def pass_(cls) -> "ValidationResult":
        return cls(ok=True)

    @classmethod
    def fail(cls, errors: Sequence[str]) -> "ValidationResult":
        return cls(ok=False, errors=tuple(errors))


@dataclass(frozen=True)
class TaskCheckRef:
    task_id: str
    check_id: str


@dataclass(frozen=True)
class ResultCellRef:
    agent_id: str
    task_id: str
    check_id: str
    required_identity_digest: str
    result_id: str | None
    result_digest: str | None
    cell_state: str
    exclusion_reason: str | None
    outcome: str | None = None


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    repository_id: str
    base_commit: str
    source_family: str
    source_ref: str
    source_resolved_at: str
    task_material_available_at: str
    certified_at: str
    solver_material_digest: str
    solver_material_refs: tuple[str, ...]
    check_ids: tuple[str, ...]
    cluster_id: str


@dataclass(frozen=True)
class CheckRecord:
    check_id: str
    task_id: str
    check_type: str
    check_manifest_digest: str
    hidden_check_bundle_digest: str
    verifier_image_digest: str
    verifier_deps_digest: str
    resource_limits: Mapping[str, JSONValue]
    oracle_source: str
    check_material_available_at: str
    certified_at: str


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    agent_manifest_digest: str
    model_snapshot_id: str
    harness_digest: str
    repository_instruction_digest: str
    prompt_digest: str
    tools_digest: str
    retrieval_digest: str
    skills_digest: str
    network_policy_digest: str
    adapter_digest: str


@dataclass(frozen=True)
class WorkspaceConfig:
    workspace_config_id: str
    repository_checkout_config_digest: str
    submodule_state_digest: str
    base_image_digest: str
    dependency_lock_digest: str


@dataclass(frozen=True)
class RuntimeConfig:
    runtime_config_id: str
    budget_digest: str
    retry_policy_digest: str
    stochastic_settings_digest: str
    timeout_seconds: int
    hardware_profile_digest: str | None


@dataclass(frozen=True)
class ResultCacheIdentity:
    task_id: str
    check_id: str
    repository_id: str
    base_commit: str
    submodule_state_digest: str
    solver_material_digest: str
    check_digest: str
    agent_manifest_digest: str
    model_snapshot_id: str
    harness_digest: str
    repository_instruction_digest: str
    prompt_digest: str
    tools_digest: str
    retrieval_digest: str
    skills_digest: str
    network_policy_digest: str
    budget_digest: str
    retry_policy_digest: str
    stochastic_settings_digest: str
    adapter_digest: str
    workspace_config_digest: str
    runtime_config_digest: str
    hardware_profile_digest: str | None
    identity_digest: str


@dataclass(frozen=True)
class WorkspaceRunRecord:
    workspace_run_id: str
    task_id: str
    check_id: str
    agent_id: str
    solver_workspace_digest: str
    verifier_workspace_digest: str
    terminal_status: str
    diff_digest: str
    replay_status: str
    check_outcome: str
    invalid_owner: str | None
    failure_label: str | None
    usage: Mapping[str, JSONValue]
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class ResultRecord:
    result_id: str
    result_digest: str
    cache_identity: ResultCacheIdentity
    agent_id: str
    task_id: str
    check_id: str
    terminal_status: str
    scoreable_state: str
    outcome: str
    invalid_owner: str | None
    failure_label: str | None
    cost: Mapping[str, JSONValue]
    scoring_config_digest: str
    pricing_version: str
    usage: Mapping[str, JSONValue]
    latency: Mapping[str, JSONValue]
    diff_digest: str
    verifier_metadata_digest: str
    started_at: str
    finished_at: str
    result_available_at: str


@dataclass(frozen=True)
class FeatureRecord:
    feature_id: str
    feature_scope: str
    task_id: str | None
    check_id: str | None
    agent_id: str | None
    result_id: str | None
    result_cache_identity_digest: str | None
    feature_name: str
    value: JSONValue
    aggregation_window: str | None
    aggregation_method: str | None
    observed_at: str
    source_artifact_digest: str
    origin_snapshot_digest: str
    leakage_class: str


@dataclass(frozen=True)
class FeatureSnapshotRecord:
    feature_snapshot_id: str
    origin_id: str
    feature_record_ids: tuple[str, ...]
    feature_records_digest: str
    leakage_policy_digest: str
    leakage_lint_status: str
    feature_records: tuple[FeatureRecord, ...] = ()
    result_view_digest: str | None = None


@dataclass(frozen=True)
class SelectorRecord:
    selector_id: str
    selector_family: str
    selector_version: str
    training_source_digests: tuple[str, ...]
    allowed_feature_classes: tuple[str, ...]
    parameters: Mapping[str, JSONValue]
    config_digest: str
    created_at: str


@dataclass(frozen=True)
class SelectorInput:
    selector_input_id: str
    origin_id: str
    task_pool_id: str
    feature_snapshot_id: str
    agent_ids: tuple[str, ...]
    eligible_task_check_refs: tuple[TaskCheckRef, ...]
    pre_origin_result_ids: tuple[str, ...]
    pre_origin_result_digests: tuple[str, ...]
    budget_digest: str
    leakage_policy_digest: str
    selector_input_digest: str
    task_pool_digest: str | None = None
    selection_budget_limit: int | None = None
    feature_records_digest: str | None = None
    feature_snapshot_lint_status: str | None = None
    origin_as_of_cutoff: str | None = None
    origin_history_refs_digest: str | None = None


@dataclass(frozen=True)
class TaskPoolRecord:
    task_pool_id: str
    task_pool_digest: str
    repository_id: str
    task_ids: tuple[str, ...]
    check_ids: tuple[str, ...]
    task_records_ref: str
    task_records_digest: str
    check_records_ref: str
    check_records_digest: str
    rejected_candidate_ids: tuple[str, ...]
    rejection_summary_digest: str
    certification_evidence_digest: str
    source_event_inventory_digest: str
    generator_config_digest: str
    certification_config_digest: str
    created_at: str


@dataclass(frozen=True)
class RollingOriginRecord:
    origin_id: str
    task_pool_id: str
    task_pool_digest: str
    origin_time: str
    policy_digest: str
    history_task_check_refs: tuple[TaskCheckRef, ...]
    future_holdout_task_check_refs: tuple[TaskCheckRef, ...]
    as_of_cutoff: str
    cluster_constraints_digest: str
    eligibility_mode: str
    holdout_overlap_policy: str


@dataclass(frozen=True)
class BenchmarkSelectionRecord:
    selection_id: str
    task_pool_id: str
    task_pool_digest: str
    origin_id: str
    selector_id: str
    selected_task_check_refs: tuple[TaskCheckRef, ...]
    selected_weights: Mapping[str, float]
    budget_digest: str
    selection_input_digest: str
    feature_snapshot_id: str
    eligibility_mode: str
    exposure_state: str
    exposed_at: str | None
    exposure_scope_digest: str | None
    created_at: str
    selection_digest: str


@dataclass(frozen=True)
class ResultMatrix:
    matrix_id: str
    matrix_role: str
    origin_id: str
    selection_id: str
    agent_ids: tuple[str, ...]
    task_check_refs: tuple[TaskCheckRef, ...]
    cells: tuple[ResultCellRef, ...]
    join_policy_digest: str
    denominator_policy_digest: str
    abstention_reason: str | None
    scoreable_state: str
    matrix_digest: str


@dataclass(frozen=True)
class EvaluationCellSet:
    cell_set_id: str
    origin_id: str
    selection_id: str
    selected_task_check_refs: tuple[TaskCheckRef, ...]
    future_task_check_refs: tuple[TaskCheckRef, ...]
    cells: tuple[ResultCellRef, ...]
    abstention_reason: str | None
    cell_set_digest: str


@dataclass(frozen=True)
class MetricRecord:
    metric_id: str
    origin_id: str
    selection_id: str
    evaluation_cell_set_digest: str
    selected_matrix_digest: str
    future_matrix_digest: str
    join_policy_digest: str
    metric_config_digest: str
    metric_scope: str
    agent_id: str | None
    agent_pair: tuple[str, str] | None
    aggregation_level: str | None
    budget_digest: str | None
    stratum_ref: str | None
    metric_name: str
    metric_value: float
    denominator_policy_digest: str
    completeness_state: str
    abstention_reason: str | None
    computed_at: str
    metric_digest: str


SELF_DIGEST_FIELDS = {
    ResultCacheIdentity: "identity_digest",
    ResultRecord: "result_digest",
    SelectorInput: "selector_input_digest",
    TaskPoolRecord: "task_pool_digest",
    BenchmarkSelectionRecord: "selection_digest",
    ResultMatrix: "matrix_digest",
    EvaluationCellSet: "cell_set_digest",
    MetricRecord: "metric_digest",
}

_WORKSPACE_TERMINAL_STATUSES = frozenset({"passed", "failed", "invalid", "error", "timeout"})
_WORKSPACE_REPLAY_STATUSES = frozenset({"applied", "failed", "invalid", "skipped"})
_WORKSPACE_CHECK_OUTCOMES = frozenset({"pass", "fail", "invalid"})
_INVALID_OWNERS = frozenset({"agent", "benchmark"})
_WORKSPACE_RUN_STATES = frozenset(
    {
        ("passed", "applied", "pass", None),
        ("failed", "applied", "fail", None),
    }
    | {
        (terminal_status, "applied", check_outcome, None)
        for terminal_status in ("error", "timeout")
        for check_outcome in _WORKSPACE_CHECK_OUTCOMES
    }
    | {
        (terminal_status, replay_status, "invalid", None)
        for terminal_status in ("error", "timeout")
        for replay_status in _WORKSPACE_REPLAY_STATUSES - {"applied"}
    }
    | {
        ("invalid", "applied", check_outcome, invalid_owner)
        for check_outcome in _WORKSPACE_CHECK_OUTCOMES
        for invalid_owner in _INVALID_OWNERS
    }
    | {
        ("invalid", replay_status, "invalid", invalid_owner)
        for replay_status in _WORKSPACE_REPLAY_STATUSES - {"applied"}
        for invalid_owner in _INVALID_OWNERS
    }
)

_RESULT_TERMINAL_STATUSES = _WORKSPACE_TERMINAL_STATUSES
_RESULT_SCOREABLE_STATES = frozenset({"scoreable", "agent_invalid", "benchmark_invalid"})
_RESULT_OUTCOMES = _WORKSPACE_CHECK_OUTCOMES
_RESULT_STATES = frozenset(
    {
        ("passed", "scoreable", "pass", None),
        ("failed", "scoreable", "fail", None),
        ("invalid", "agent_invalid", "invalid", "agent"),
        ("error", "agent_invalid", "invalid", "agent"),
        ("timeout", "agent_invalid", "invalid", "agent"),
        ("invalid", "benchmark_invalid", "invalid", "benchmark"),
    }
)


def canonical_data(value: Any) -> JSONValue:
    if is_dataclass(value):
        return {field.name: canonical_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [canonical_data(item) for item in value]
    if isinstance(value, Mapping):
        keys = tuple(value)
        if any(not isinstance(key, str) for key in keys):
            raise TypeError("canonical JSON mapping keys must be strings")
        return {key: canonical_data(value[key]) for key in sorted(keys)}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_data(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_digest(value: Any, *, exclude_self_digest: bool = False) -> str:
    data = canonical_data(value)
    if exclude_self_digest and is_dataclass(value):
        field_name = SELF_DIGEST_FIELDS.get(type(value))
        if field_name is not None and isinstance(data, dict):
            data = {key: item for key, item in data.items() if key != field_name}
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_with_digest(record: Any, digest_field: str | None = None) -> Any:
    if digest_field is None:
        digest_field = SELF_DIGEST_FIELDS.get(type(record))
    if digest_field is None:
        raise ValueError(f"{type(record).__name__} has no self digest field")
    digest = canonical_digest(record, exclude_self_digest=True)
    return replace(record, **{digest_field: digest})


def _self_digest_errors(record: Any, digest_field: str, record_label: str) -> list[str]:
    try:
        expected_digest = canonical_digest(record, exclude_self_digest=True)
    except (OverflowError, TypeError, ValueError):
        return [f"{record_label} is not strict canonical JSON"]
    if getattr(record, digest_field) != expected_digest:
        return [f"{digest_field} does not match canonical {record_label}"]
    return []


def task_check_ref_key(ref: TaskCheckRef) -> str:
    return canonical_digest(ref)


def validate_task(task: TaskRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(task)
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_ordered_timestamps(task, ["source_resolved_at", "task_material_available_at", "certified_at"]))
    hidden_refs = [ref for ref in task.solver_material_refs if _looks_hidden(ref)]
    if hidden_refs:
        errors.append("solver_material_refs must not include hidden check or oracle material")
    if not task.check_ids:
        errors.append("check_ids must not be empty")
    return _validation(errors)


def validate_check(check: CheckRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(check)
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_ordered_timestamps(check, ["check_material_available_at", "certified_at"]))
    if not check.check_type:
        errors.append("check_type is required")
    if not isinstance(check.resource_limits, Mapping) or not check.resource_limits:
        errors.append("resource_limits must be a non-empty mapping")
    elif any(value is None for value in check.resource_limits.values()):
        errors.append("resource_limits values must be bounded")
    if _looks_solver_visible(check.hidden_check_bundle_digest):
        errors.append("hidden_check_bundle_digest must not expose hidden material")
    return _validation(errors)


def validate_workspace_run(run: WorkspaceRunRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(run, nullable={"invalid_owner", "failure_label"})
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_ordered_timestamps(run, ["started_at", "finished_at"]))
    if run.terminal_status not in _WORKSPACE_TERMINAL_STATUSES:
        errors.append("terminal_status is not normalized")
    if run.replay_status not in _WORKSPACE_REPLAY_STATUSES:
        errors.append("replay_status is not normalized")
    if run.check_outcome not in _WORKSPACE_CHECK_OUTCOMES:
        errors.append("check_outcome is not normalized")
    if run.invalid_owner is not None and run.invalid_owner not in _INVALID_OWNERS:
        errors.append("invalid_owner is not normalized")
    if (run.terminal_status, run.replay_status, run.check_outcome, run.invalid_owner) not in _WORKSPACE_RUN_STATES:
        errors.append("workspace run state is inconsistent")
    if not isinstance(run.usage, Mapping):
        errors.append("usage must be a mapping")
    else:
        usage_errors, _ = _usage_measurement_errors(run.usage)
        errors.extend(usage_errors)
    return _validation(errors)


def validate_result_cache_identity(identity: ResultCacheIdentity) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        identity,
        nullable={"hardware_profile_digest", "identity_digest"},
    )
    if invalid_mapping:
        return _validation(errors)
    if identity.identity_digest:
        errors.extend(_self_digest_errors(identity, "identity_digest", "structured identity"))
    else:
        errors.append("identity_digest is required")
    return _validation(errors)


def validate_result(result: ResultRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(result, nullable={"invalid_owner", "failure_label"})
    if invalid_mapping:
        return _validation(errors)
    identity_result = validate_result_cache_identity(result.cache_identity)
    errors.extend(f"cache_identity: {error}" for error in identity_result.errors)
    errors.extend(_ordered_timestamps(result, ["started_at", "finished_at", "result_available_at"]))
    errors.extend(_self_digest_errors(result, "result_digest", "result record"))
    if result.cache_identity.task_id != result.task_id or result.cache_identity.check_id != result.check_id:
        errors.append("cache identity task/check does not match result")
    if not result.pricing_version:
        errors.append("pricing_version is required")
    if result.terminal_status not in _RESULT_TERMINAL_STATUSES:
        errors.append("terminal_status is not normalized")
    if result.scoreable_state not in _RESULT_SCOREABLE_STATES:
        errors.append("scoreable_state is not normalized")
    if result.outcome not in _RESULT_OUTCOMES:
        errors.append("outcome is not normalized")
    if result.invalid_owner is not None and result.invalid_owner not in _INVALID_OWNERS:
        errors.append("invalid_owner is not normalized")
    errors.extend(_result_state_errors(result))
    if not isinstance(result.cost, Mapping):
        errors.append("cost must be a mapping")
    else:
        errors.extend(
            _measurement_errors(
                "cost",
                result.cost,
                required_keys=("total_cost",),
                nullable_keys=("total_cost",),
            )
        )
    if not isinstance(result.latency, Mapping):
        errors.append("latency must be a mapping")
    else:
        errors.extend(_measurement_errors("latency", result.latency, required_keys=("workspace_seconds",)))
    if not isinstance(result.usage, Mapping):
        errors.append("usage must be a mapping")
    else:
        usage_errors, _ = _usage_measurement_errors(result.usage)
        errors.extend(usage_errors)
    return _validation(errors)


def validate_feature_snapshot(snapshot: FeatureSnapshotRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        snapshot,
        nullable={"feature_records", "result_view_digest"},
    )
    if invalid_mapping:
        return _validation(errors)
    if not snapshot.feature_record_ids:
        errors.append("feature_record_ids must not be empty")
    if snapshot.leakage_lint_status not in {"passed", "failed", "not_run"}:
        errors.append("leakage_lint_status is not normalized")
    if snapshot.feature_records:
        if snapshot.feature_record_ids != tuple(record.feature_id for record in snapshot.feature_records):
            errors.append("feature_record_ids must align with feature_records")
        for index, record in enumerate(snapshot.feature_records):
            record_errors = _required_errors(
                record,
                nullable={
                    "task_id",
                    "check_id",
                    "agent_id",
                    "result_id",
                    "result_cache_identity_digest",
                    "aggregation_window",
                    "aggregation_method",
                },
            )
            record_errors.extend(_ordered_timestamps(record, ["observed_at"]))
            errors.extend(f"feature_records[{index}]: {error}" for error in record_errors)
        try:
            expected_feature_records_digest = canonical_digest(snapshot.feature_records)
        except (OverflowError, TypeError, ValueError):
            errors.append("feature_records are not strict canonical JSON")
        else:
            if snapshot.feature_records_digest != expected_feature_records_digest:
                errors.append("feature_records_digest does not match feature_records")
    return _validation(errors)


def validate_selector_input(selector_input: SelectorInput) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(selector_input)
    if invalid_mapping:
        return _validation(errors)
    for field_name in ("pre_origin_result_ids", "pre_origin_result_digests"):
        if getattr(selector_input, field_name) == ():
            required_error = f"{field_name} is required"
            if required_error in errors:
                errors.remove(required_error)
    if not selector_input.eligible_task_check_refs:
        errors.append("eligible_task_check_refs must not be empty")
    if (
        selector_input.pre_origin_result_ids is not None
        and selector_input.pre_origin_result_digests is not None
        and len(selector_input.pre_origin_result_ids) != len(selector_input.pre_origin_result_digests)
    ):
        errors.append("pre_origin_result_ids and pre_origin_result_digests must align")
    if selector_input.selection_budget_limit is None or selector_input.selection_budget_limit < 1:
        errors.append("selection_budget_limit must be positive")
    if not selector_input.feature_records_digest:
        errors.append("feature_records_digest is required")
    if selector_input.feature_snapshot_lint_status != "passed":
        errors.append("feature_snapshot_lint_status must be passed")
    if not selector_input.origin_as_of_cutoff:
        errors.append("origin_as_of_cutoff is required")
    if not selector_input.origin_history_refs_digest:
        errors.append("origin_history_refs_digest is required")
    if selector_input.origin_history_refs_digest and selector_input.origin_history_refs_digest != canonical_digest(selector_input.eligible_task_check_refs):
        errors.append("origin_history_refs_digest does not match eligible refs")
    if selector_input.selector_input_id != make_selector_input_id(selector_input):
        errors.append("selector_input_id does not match selector input identity")
    errors.extend(_self_digest_errors(selector_input, "selector_input_digest", "selector input"))
    return _validation(errors)


def make_selector_input_id(selector_input: SelectorInput) -> str:
    identity = {
        "origin_id": selector_input.origin_id,
        "task_pool_id": selector_input.task_pool_id,
        "task_pool_digest": selector_input.task_pool_digest,
        "feature_snapshot_id": selector_input.feature_snapshot_id,
        "agent_ids": selector_input.agent_ids,
        "eligible_task_check_refs": selector_input.eligible_task_check_refs,
        "pre_origin_result_ids": selector_input.pre_origin_result_ids,
        "pre_origin_result_digests": selector_input.pre_origin_result_digests,
        "budget_digest": selector_input.budget_digest,
        "selection_budget_limit": selector_input.selection_budget_limit,
        "leakage_policy_digest": selector_input.leakage_policy_digest,
        "feature_records_digest": selector_input.feature_records_digest,
        "feature_snapshot_lint_status": selector_input.feature_snapshot_lint_status,
        "origin_as_of_cutoff": selector_input.origin_as_of_cutoff,
        "origin_history_refs_digest": selector_input.origin_history_refs_digest,
    }
    return f"selector_input_{canonical_digest(identity)}"


def validate_result_matrix(matrix: ResultMatrix) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(matrix, nullable={"abstention_reason"})
    if invalid_mapping:
        return _validation(errors)
    if matrix.matrix_role not in {"selected", "future_holdout"}:
        errors.append("matrix_role is not normalized")
    if len(matrix.agent_ids) != len(set(matrix.agent_ids)):
        errors.append("agent_ids must not contain duplicates")
    if _task_check_refs_have_duplicates(matrix.task_check_refs):
        errors.append("task_check_refs must not contain duplicates")
    _validate_cells(
        errors,
        matrix.cells,
        matrix.agent_ids,
        matrix.task_check_refs,
        require_full_denominator=True,
    )
    errors.extend(_self_digest_errors(matrix, "matrix_digest", "matrix"))
    return _validation(errors)


def validate_evaluation_cell_set(cells: EvaluationCellSet) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(cells, nullable={"abstention_reason"})
    if invalid_mapping:
        return _validation(errors)
    if _task_check_refs_have_duplicates(cells.selected_task_check_refs):
        errors.append("selected_task_check_refs must not contain duplicates")
    if _task_check_refs_have_duplicates(cells.future_task_check_refs):
        errors.append("future_task_check_refs must not contain duplicates")
    allowed_refs = cells.selected_task_check_refs + cells.future_task_check_refs
    _validate_cells(
        errors,
        cells.cells,
        tuple({cell.agent_id for cell in cells.cells}),
        allowed_refs,
        require_full_denominator=False,
    )
    present_refs = {(cell.task_id, cell.check_id) for cell in cells.cells}
    missing_refs = [
        (ref.task_id, ref.check_id)
        for ref in allowed_refs
        if (ref.task_id, ref.check_id) not in present_refs
    ]
    if missing_refs:
        errors.append("evaluation cell set must include at least one cell for each selected and future task/check ref")
    errors.extend(_self_digest_errors(cells, "cell_set_digest", "evaluation cell set"))
    return _validation(errors)


def validate_selector(selector: SelectorRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(selector)
    if invalid_mapping:
        return _validation(errors)
    if not selector.training_source_digests:
        errors.append("training_source_digests must not be empty")
    if not selector.allowed_feature_classes:
        errors.append("allowed_feature_classes must not be empty")
    if not isinstance(selector.parameters, Mapping):
        errors.append("parameters must be a mapping")
    else:
        expected_config_digest = canonical_digest(
            {
                "selector_family": selector.selector_family,
                "parameters": selector.parameters,
            }
        )
        if selector.config_digest != expected_config_digest:
            errors.append("config_digest does not match selector family and parameters")
    return _validation(errors)


def validate_benchmark_selection(selection: BenchmarkSelectionRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        selection,
        nullable={"exposed_at", "exposure_scope_digest"},
    )
    if invalid_mapping:
        return _validation(errors)
    if _task_check_refs_have_duplicates(selection.selected_task_check_refs):
        errors.append("selected_task_check_refs must not contain duplicates")
    selected_keys = {task_check_ref_key(ref) for ref in selection.selected_task_check_refs}
    weight_keys = set(selection.selected_weights)
    if selected_keys != weight_keys:
        errors.append("selected_weights must exactly cover selected_task_check_refs")
    if any(not _is_finite_positive_number(weight) for weight in selection.selected_weights.values()):
        errors.append("selected_weights must be finite positive numbers")
    if selection.exposure_state not in {"unexposed", "frozen", "exposed"}:
        errors.append("exposure_state is not normalized")
    if selection.exposure_state == "exposed" and not selection.exposed_at:
        errors.append("exposed selections must set exposed_at")
    if selection.exposure_state != "exposed" and selection.exposed_at is not None:
        errors.append("non-exposed selections must not set exposed_at")
    errors.extend(_ordered_timestamps(selection, ["created_at"] + (["exposed_at"] if selection.exposed_at else [])))
    errors.extend(_self_digest_errors(selection, "selection_digest", "benchmark selection"))
    return _validation(errors)


def validate_metric(metric: MetricRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        metric,
        nullable={"agent_id", "agent_pair", "aggregation_level", "budget_digest", "stratum_ref", "abstention_reason"},
    )
    if invalid_mapping:
        return _validation(errors)
    if metric.metric_scope == "agent":
        if not metric.agent_id or metric.agent_pair or metric.aggregation_level:
            errors.append("agent metrics must set only agent_id among dimension fields")
    elif metric.metric_scope == "pair":
        if not metric.agent_pair or metric.agent_id or metric.aggregation_level:
            errors.append("pairwise metrics must set only agent_pair among dimension fields")
    elif metric.metric_scope == "aggregate":
        if not metric.aggregation_level or metric.agent_id or metric.agent_pair:
            errors.append("aggregate metrics must set aggregation_level and no agent dimension")
    else:
        errors.append("metric_scope is not normalized")
    if not _is_finite_number(metric.metric_value):
        errors.append("metric_value must be a finite number")
    complete_states = {"complete", "complete_with_exclusions"}
    incomplete_states = {"incomplete", "abstained", "invalid"}
    if metric.completeness_state not in complete_states | incomplete_states:
        errors.append("completeness_state is not normalized")
    elif metric.completeness_state in complete_states and metric.abstention_reason is not None:
        errors.append("complete metrics must not set abstention_reason")
    elif metric.completeness_state in incomplete_states and not metric.abstention_reason:
        errors.append("incomplete metrics must set abstention_reason")
    errors.extend(_ordered_timestamps(metric, ["computed_at"]))
    errors.extend(_self_digest_errors(metric, "metric_digest", "metric"))
    return _validation(errors)


def make_task_id(repository_id: str, base_commit: str, source_digest: str) -> str:
    return f"task_{canonical_digest({'repository_id': repository_id, 'base_commit': base_commit, 'source_digest': source_digest})}"


def make_check_id(task_id: str, check_digest: str) -> str:
    return f"check_{canonical_digest({'task_id': task_id, 'check_digest': check_digest})}"


def make_check_digest(check: CheckRecord) -> str:
    """Digest every Check field that can change execution or verification."""
    return canonical_digest(
        {
            "check_type": check.check_type,
            "check_manifest_digest": check.check_manifest_digest,
            "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
            "verifier_image_digest": check.verifier_image_digest,
            "verifier_deps_digest": check.verifier_deps_digest,
            "resource_limits": check.resource_limits,
            "oracle_source": check.oracle_source,
        }
    )


def make_result_cache_identity(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> ResultCacheIdentity:
    if check.task_id != task.task_id:
        raise ValueError("check.task_id must match task.task_id")
    if check.check_id not in task.check_ids:
        raise ValueError("check.check_id must be listed in task.check_ids")
    identity = ResultCacheIdentity(
        task_id=task.task_id,
        check_id=check.check_id,
        repository_id=task.repository_id,
        base_commit=task.base_commit,
        submodule_state_digest=workspace_config.submodule_state_digest,
        solver_material_digest=task.solver_material_digest,
        check_digest=make_check_digest(check),
        agent_manifest_digest=agent.agent_manifest_digest,
        model_snapshot_id=agent.model_snapshot_id,
        harness_digest=agent.harness_digest,
        repository_instruction_digest=agent.repository_instruction_digest,
        prompt_digest=agent.prompt_digest,
        tools_digest=agent.tools_digest,
        retrieval_digest=agent.retrieval_digest,
        skills_digest=agent.skills_digest,
        network_policy_digest=agent.network_policy_digest,
        budget_digest=runtime_config.budget_digest,
        retry_policy_digest=runtime_config.retry_policy_digest,
        stochastic_settings_digest=runtime_config.stochastic_settings_digest,
        adapter_digest=agent.adapter_digest,
        workspace_config_digest=canonical_digest(workspace_config),
        runtime_config_digest=canonical_digest(runtime_config),
        hardware_profile_digest=runtime_config.hardware_profile_digest,
        identity_digest="",
    )
    return record_with_digest(identity)


def make_result_cache_key(identity: ResultCacheIdentity) -> str:
    validation = validate_result_cache_identity(identity)
    if not validation.ok:
        raise ValueError("result cache identity is incomplete or invalid")
    return identity.identity_digest


def make_selector_id(selector_digest: str) -> str:
    return f"selector_{canonical_digest({'selector_digest': selector_digest})}"


def load_jsonl_records(path: Path, record_type: type) -> list[Any]:
    records: list[Any] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(_from_data(record_type, json.loads(stripped, parse_constant=_reject_json_constant)))
    return records


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def write_jsonl_records(path: Path, records: Sequence[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            for record in records:
                tmp.write(canonical_json(record))
                tmp.write("\n")
        os.replace(tmp_path, path)
    except BaseException:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise


def _initial_validation_errors(
    record: Any,
    *,
    nullable: set[str] | None = None,
) -> tuple[list[str], bool]:
    errors = _required_errors(record, nullable=nullable)
    try:
        canonical_data(record)
    except TypeError as exc:
        errors.append(str(exc))
        return (errors, True)
    return (errors, False)


def _required_errors(record: Any, *, nullable: set[str] | None = None) -> list[str]:
    nullable = nullable or set()
    errors: list[str] = []
    for field in fields(record):
        value = getattr(record, field.name)
        if field.name in nullable:
            continue
        if value is None or value == "" or value == ():
            errors.append(f"{field.name} is required")
    return errors


def _ordered_timestamps(record: Any, names: Sequence[str]) -> list[str]:
    values = [getattr(record, name) for name in names]
    if any(not isinstance(value, str) for value in values):
        return [f"timestamps must be valid ISO datetimes: {', '.join(names)}"]
    if any(not value for value in values):
        return []
    try:
        instants = [_parse_timestamp_utc(value) for value in values]
    except ValueError:
        return [f"timestamps must be valid ISO datetimes: {', '.join(names)}"]
    if any(left > right for left, right in zip(instants, instants[1:])):
        return [f"timestamps must be ordered: {', '.join(names)}"]
    return []


def _parse_timestamp_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _result_state_errors(result: ResultRecord) -> list[str]:
    state = (result.terminal_status, result.scoreable_state, result.outcome, result.invalid_owner)
    return [] if state in _RESULT_STATES else ["result state is inconsistent"]


def _measurement_errors(
    name: str,
    values: Mapping[str, Any],
    *,
    required_keys: Sequence[str] = (),
    nullable_keys: Sequence[str] = (),
) -> list[str]:
    missing_keys = [key for key in required_keys if key not in values]
    if missing_keys:
        return [f"{name} must include {', '.join(missing_keys)}"]
    nullable = set(nullable_keys)
    for key, value in values.items():
        if key in nullable and value is None:
            continue
        if _is_finite_nonnegative_number(value):
            continue
        return [f"{name} values must be finite and nonnegative numbers"]
    return []


def _usage_measurement_errors(values: Mapping[str, Any]) -> tuple[list[str], int]:
    numeric_count = 0
    for value in values.values():
        if _is_finite_nonnegative_number(value):
            numeric_count += 1
            continue
        return (["usage values must be finite and nonnegative numbers"], numeric_count)
    return ([], numeric_count)


def _is_finite_nonnegative_number(value: Any) -> bool:
    return _is_finite_number(value) and value >= 0


def _is_finite_positive_number(value: Any) -> bool:
    return _is_finite_number(value) and value > 0


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def _validation(errors: Sequence[str]) -> ValidationResult:
    if errors:
        return ValidationResult.fail(errors)
    return ValidationResult.pass_()


def _looks_hidden(value: str) -> bool:
    lowered = value.lower()
    return "hidden" in lowered or "oracle" in lowered


def _looks_solver_visible(value: str) -> bool:
    return value.startswith("path:") or value.startswith("file:")


def _validate_cells(
    errors: list[str],
    cells: Sequence[ResultCellRef],
    agent_ids: Sequence[str],
    task_check_refs: Sequence[TaskCheckRef],
    *,
    require_full_denominator: bool,
) -> None:
    agent_set = set(agent_ids)
    ref_set = {(ref.task_id, ref.check_id) for ref in task_check_refs}
    seen_cells: set[tuple[str, str, str]] = set()
    for cell in cells:
        cell_key = (cell.agent_id, cell.task_id, cell.check_id)
        if cell_key in seen_cells:
            errors.append("duplicate Agent/Task/Check cell")
        seen_cells.add(cell_key)
        if cell.agent_id not in agent_set:
            errors.append("cell agent_id is not in matrix agent_ids")
        if (cell.task_id, cell.check_id) not in ref_set:
            errors.append("cell task/check ref is not in matrix task_check_refs")
        if not cell.required_identity_digest:
            errors.append("cell required_identity_digest is required")
        if cell.cell_state == "result":
            if not cell.result_id or not cell.result_digest:
                errors.append("result cells must bind result_id and result_digest")
            if cell.exclusion_reason:
                errors.append("result cells must not set exclusion_reason")
        elif cell.cell_state == "excluded":
            if not cell.exclusion_reason:
                errors.append("excluded cells must set exclusion_reason")
        elif cell.cell_state == "missing":
            if cell.result_id or cell.result_digest:
                errors.append("missing cells must not bind a result")
        else:
            errors.append("cell_state is not normalized")
    if require_full_denominator:
        expected_cells = {
            (agent_id, ref.task_id, ref.check_id)
            for agent_id in agent_ids
            for ref in task_check_refs
        }
        if seen_cells != expected_cells:
            errors.append("matrix cells must exactly cover every Agent/Task/Check denominator cell")


def _task_check_refs_have_duplicates(refs: Sequence[TaskCheckRef]) -> bool:
    keys = tuple((ref.task_id, ref.check_id) for ref in refs)
    return len(keys) != len(set(keys))


def _from_data(record_type: type, data: Any) -> Any:
    if not is_dataclass(record_type):
        return data
    type_hints = get_type_hints(record_type)
    kwargs: dict[str, Any] = {}
    for field in fields(record_type):
        kwargs[field.name] = _coerce_value(type_hints[field.name], data[field.name])
    return record_type(**kwargs)


def _coerce_value(expected_type: Any, data: Any) -> Any:
    origin = get_origin(expected_type)
    args = get_args(expected_type)
    if origin in {Union, UnionType}:
        non_none = [arg for arg in args if arg is not type(None)]
        if data is None:
            return None
        return _coerce_value(non_none[0], data)
    if origin is tuple:
        item_type = args[0] if args else Any
        return tuple(_coerce_value(item_type, item) for item in data)
    if origin is list:
        item_type = args[0] if args else Any
        return [_coerce_value(item_type, item) for item in data]
    if origin in {dict, Mapping, MappingABC}:
        return data
    if isinstance(expected_type, type) and is_dataclass(expected_type):
        return _from_data(expected_type, data)
    return data
