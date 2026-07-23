"""Shared record contracts for Barcarolle module boundaries."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import UnionType
from typing import Any, Mapping, Sequence, Union, get_args, get_origin, get_type_hints
import hashlib
import json
import math
import os


JSONValue = Any
_SOLVER_MATERIAL_FORMAT = "task_text_and_file_refs_v1"
_WORKSPACE_CHECKOUT_MODE = "base_commit_history_v1"
_ROLLING_ORIGIN_PROTOCOL_VERSION = "rolling_origin_arrival_cohort_v2"
_LOWERCASE_HEX_DIGITS = frozenset("0123456789abcdef")


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
class SourceEventRecord:
    source_event_id: str
    repository_id: str
    source_family: str
    source_ref: str
    source_resolved_at: str
    task_material_available_at: str | None
    check_material_available_at: str | None
    label_mature_at: str | None
    candidate_id: str | None
    task_id: str | None
    check_id: str | None
    disposition: str
    rejection_stage: str | None
    rejection_reasons: tuple[str, ...]
    dependency_cluster_id: str
    sampling_stratum: str
    source_event_digest: str


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    repository_id: str
    base_commit: str
    source_family: str
    source_ref: str
    source_resolved_at: str
    task_material_available_at: str
    task_text: str
    solver_material_digest: str
    solver_material_refs: tuple[str, ...]
    check_ids: tuple[str, ...]
    dependency_cluster_id: str
    sampling_stratum: str


@dataclass(frozen=True)
class CheckRecord:
    check_id: str
    task_id: str
    check_type: str
    check_manifest_digest: str
    hidden_check_bundle_digest: str
    resource_limits: Mapping[str, JSONValue]
    oracle_source: str
    check_material_available_at: str


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    agent_manifest_digest: str
    requested_model_id: str
    model_snapshot_id: str | None
    model_resolution_scope_id: str | None
    model_resolution_scope_started_at: str | None
    model_resolution_scope_ended_at: str | None
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
    requested_model_id: str
    model_snapshot_id: str | None
    model_resolution_scope_id: str | None
    model_resolution_scope_started_at: str | None
    model_resolution_scope_ended_at: str | None
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
    latency: Mapping[str, JSONValue]
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
    feature_config_digest: str | None = None
    feature_snapshot_digest: str | None = None


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
    selector_digest: str


@dataclass(frozen=True)
class SelectorInput:
    selector_input_id: str
    origin_id: str
    task_pool_id: str
    feature_snapshot_id: str
    agent_ids: tuple[str, ...]
    agent_record_digests: tuple[str, ...]
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
    eligibility_mode: str | None = None


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
    certification_evidence_ref: str
    source_event_records_ref: str
    source_event_records_digest: str
    rejected_candidate_ids: tuple[str, ...]
    rejection_summary_digest: str
    certification_evidence_digest: str
    generator_config_digest: str
    certification_config_digest: str
    created_at: str
    source_window_start: str | None = None
    source_window_end: str | None = None


@dataclass(frozen=True)
class RollingOriginRecord:
    origin_id: str
    task_pool_id: str
    task_pool_digest: str
    origin_time: str
    policy_digest: str
    history_task_check_refs: tuple[TaskCheckRef, ...]
    history_censored_task_check_refs: tuple[TaskCheckRef, ...]
    future_holdout_task_check_refs: tuple[TaskCheckRef, ...]
    future_censored_task_check_refs: tuple[TaskCheckRef, ...]
    as_of_cutoff: str
    eligibility_mode: str
    holdout_overlap_policy: str
    as_of_cutoff_rule: str
    history_window_start: str | None
    future_window_start: str
    future_window_end: str
    future_cohort_time_basis: str
    maturity_lag_seconds: int
    label_maturity_cutoff: str
    future_holdout_known: bool
    allowed_dependency_cluster_ids: tuple[str, ...]
    origin_digest: str


@dataclass(frozen=True)
class BenchmarkSelectionRecord:
    selection_id: str
    task_pool_id: str
    task_pool_digest: str
    origin_id: str
    selector_id: str
    selector_digest: str
    selected_task_check_refs: tuple[TaskCheckRef, ...]
    selected_weights: Mapping[str, float]
    budget_digest: str
    selection_input_digest: str
    feature_snapshot_id: str
    eligibility_mode: str
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
    future_censored_task_check_refs: tuple[TaskCheckRef, ...]
    future_task_pool_id: str
    future_task_pool_digest: str
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
    SourceEventRecord: "source_event_digest",
    ResultCacheIdentity: "identity_digest",
    ResultRecord: "result_digest",
    FeatureSnapshotRecord: "feature_snapshot_digest",
    SelectorRecord: "selector_digest",
    SelectorInput: "selector_input_digest",
    TaskPoolRecord: "task_pool_digest",
    RollingOriginRecord: "origin_digest",
    BenchmarkSelectionRecord: "selection_digest",
    ResultMatrix: "matrix_digest",
    EvaluationCellSet: "cell_set_digest",
    MetricRecord: "metric_digest",
}

_WORKSPACE_TERMINAL_STATUSES = frozenset(
    {"passed", "failed", "invalid", "error", "timeout"}
)
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
_RESULT_SCOREABLE_STATES = frozenset(
    {"scoreable", "agent_invalid", "benchmark_invalid"}
)
_RESULT_OUTCOMES = _WORKSPACE_CHECK_OUTCOMES
_MATRIX_SCOREABLE_STATES = frozenset(
    {"complete", "complete_with_exclusions", "incomplete", "abstained"}
)
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
        return {
            field.name: canonical_data(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple | list):
        return [canonical_data(item) for item in value]
    if isinstance(value, Mapping):
        keys = tuple(value)
        if any(not isinstance(key, str) for key in keys):
            raise TypeError("canonical JSON mapping keys must be strings")
        return {key: canonical_data(value[key]) for key in sorted(keys)}
    if type(value) is float and value == 0.0:
        return 0.0
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


def make_check_command_digest(check_command: Sequence[str]) -> str:
    """Return the canonical identity of the exact Check argv."""
    return canonical_digest({"check_command": tuple(check_command)})


def parse_utc_timestamp(value: str) -> datetime:
    """Parse a timezone-aware ISO timestamp and normalize it to UTC."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed.astimezone(UTC)


def format_utc_timestamp(value: datetime) -> str:
    """Format a timezone-aware datetime as canonical UTC evidence time."""
    if value.utcoffset() is None:
        raise ValueError("timestamp datetime must be timezone-aware")
    return (
        value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def utc_now_timestamp() -> str:
    return format_utc_timestamp(datetime.now(UTC))


def record_with_digest(record: Any, digest_field: str | None = None) -> Any:
    if digest_field is None:
        digest_field = SELF_DIGEST_FIELDS.get(type(record))
    if digest_field is None:
        raise ValueError(f"{type(record).__name__} has no self digest field")
    data = canonical_data(record)
    if not isinstance(data, dict) or digest_field not in data:
        raise ValueError(f"{type(record).__name__} has no field named {digest_field}")
    digest = canonical_digest(
        {key: value for key, value in data.items() if key != digest_field}
    )
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
    errors, invalid_mapping = _initial_validation_errors(
        task,
        nullable={
            "dependency_cluster_id",
            "sampling_stratum",
            "solver_material_refs",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    if not is_full_git_object_id(task.base_commit):
        errors.append("base_commit must be a full lowercase Git object ID")
    errors.extend(
        _ordered_timestamps(task, ["source_resolved_at", "task_material_available_at"])
    )
    if not task.task_text.strip():
        errors.append("task_text must not be empty")
    else:
        if task.task_text != task.task_text.rstrip():
            errors.append("task_text must not have trailing whitespace")
        expected_solver_material_digest = make_solver_material_digest(
            task.task_text, task.solver_material_refs
        )
        if task.solver_material_digest != expected_solver_material_digest:
            errors.append(
                "solver_material_digest does not match task_text and solver_material_refs"
            )
    if not task.check_ids:
        errors.append("check_ids must not be empty")
    return _validation(errors)


def make_source_event_id(
    repository_id: str,
    source_family: str,
    source_ref: str,
) -> str:
    return (
        f"source_event_{canonical_digest((repository_id, source_family, source_ref))}"
    )


def validate_source_event(event: SourceEventRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        event,
        nullable={
            "task_material_available_at",
            "check_material_available_at",
            "label_mature_at",
            "candidate_id",
            "task_id",
            "check_id",
            "rejection_stage",
            "rejection_reasons",
            "dependency_cluster_id",
            "sampling_stratum",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    expected_label_mature_at, material_errors = _source_event_material_errors(event)
    errors.extend(material_errors)
    errors.extend(
        _source_event_disposition_errors(event, expected_label_mature_at is not None)
    )
    expected_id = make_source_event_id(
        event.repository_id,
        event.source_family,
        event.source_ref,
    )
    if event.source_event_id != expected_id:
        errors.append("source_event_id does not match source identity")
    errors.extend(
        _self_digest_errors(event, "source_event_digest", "source event record")
    )
    return _validation(errors)


def _source_event_material_errors(
    event: SourceEventRecord,
) -> tuple[str | None, tuple[str, ...]]:
    errors: list[str] = []
    task_timestamp_names = ("source_resolved_at",)
    if event.task_material_available_at is not None:
        task_timestamp_names += ("task_material_available_at",)
    errors.extend(_ordered_timestamps(event, task_timestamp_names))
    if event.check_material_available_at is not None:
        errors.extend(_ordered_timestamps(event, ("check_material_available_at",)))
    material_times = tuple(
        value
        for value in (
            event.task_material_available_at,
            event.check_material_available_at,
        )
        if value is not None
    )
    expected_label_mature_at = None
    if len(material_times) == 2:
        try:
            expected_label_mature_at = format_utc_timestamp(
                max(parse_utc_timestamp(value) for value in material_times)
            )
        except (AttributeError, TypeError, ValueError):
            pass
    if event.label_mature_at != expected_label_mature_at:
        errors.append(
            "label_mature_at must be the later Task/Check material time, or null"
        )
    return expected_label_mature_at, tuple(errors)


def _source_event_disposition_errors(
    event: SourceEventRecord,
    material_is_mature: bool,
) -> tuple[str, ...]:
    return (
        *_source_event_binding_errors(event),
        *_source_event_rejection_reason_errors(event),
        *_source_event_maturity_errors(event, material_is_mature),
    )


def _source_event_binding_errors(event: SourceEventRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if event.disposition == "accepted":
        if not all((event.candidate_id, event.task_id, event.check_id)):
            errors.append("accepted source events must bind candidate, Task, and Check")
        if event.rejection_stage is not None or event.rejection_reasons:
            errors.append("accepted source events must not carry rejection data")
    elif event.disposition == "certification_rejected":
        if (
            not event.candidate_id
            or event.task_id is not None
            or event.check_id is not None
        ):
            errors.append(
                "certification-rejected source events must bind only a candidate"
            )
        if event.rejection_stage != "certification" or not event.rejection_reasons:
            errors.append(
                "certification-rejected source events need certification reasons"
            )
    elif event.disposition == "excluded":
        if any((event.candidate_id, event.task_id, event.check_id)):
            errors.append(
                "excluded source events must not bind candidate, Task, or Check"
            )
        if event.rejection_stage != "candidate_filter" or not event.rejection_reasons:
            errors.append("excluded source events need candidate-filter reasons")
    else:
        errors.append("source event disposition is not normalized")
    return tuple(errors)


def _source_event_rejection_reason_errors(
    event: SourceEventRecord,
) -> tuple[str, ...]:
    if not isinstance(event.rejection_reasons, tuple):
        return ("source event rejection reasons must be a tuple of non-empty strings",)
    if any(
        not isinstance(reason, str) or not reason for reason in event.rejection_reasons
    ):
        return ("source event rejection reasons must be non-empty strings",)
    return ()


def _source_event_maturity_errors(
    event: SourceEventRecord,
    material_is_mature: bool,
) -> tuple[str, ...]:
    if event.disposition != "excluded" and not material_is_mature:
        return ("candidate source events must have mature Task/Check material",)
    return ()


def is_full_git_object_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(character in _LOWERCASE_HEX_DIGITS for character in value)
    )


def validate_check(check: CheckRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        check, nullable={"resource_limits"}
    )
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_ordered_timestamps(check, ["check_material_available_at"]))
    if not check.check_type:
        errors.append("check_type is required")
    if not isinstance(check.resource_limits, Mapping):
        errors.append("resource_limits must be a mapping")
    elif any(value is None for value in check.resource_limits.values()):
        errors.append("resource_limits values must be bounded")
    if _looks_solver_visible(check.hidden_check_bundle_digest):
        errors.append("hidden_check_bundle_digest must not expose hidden material")
    return _validation(errors)


def validate_agent(agent: AgentRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        agent,
        nullable={
            "model_snapshot_id",
            "model_resolution_scope_id",
            "model_resolution_scope_started_at",
            "model_resolution_scope_ended_at",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    errors.extend(
        _model_identity_errors(
            requested_model_id=agent.requested_model_id,
            model_snapshot_id=agent.model_snapshot_id,
            scope_id=agent.model_resolution_scope_id,
            scope_started_at=agent.model_resolution_scope_started_at,
            scope_ended_at=agent.model_resolution_scope_ended_at,
        )
    )
    return _validation(errors)


def validate_workspace_config(config: WorkspaceConfig) -> ValidationResult:
    errors, _ = _initial_validation_errors(config)
    return _validation(errors)


def validate_runtime_config(config: RuntimeConfig) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        config,
        nullable={"hardware_profile_digest"},
    )
    if invalid_mapping:
        return _validation(errors)
    if config.timeout_seconds <= 0:
        errors.append("timeout_seconds must be a positive integer")
    if config.hardware_profile_digest == "":
        errors.append("hardware_profile_digest must be a nonempty string or null")
    return _validation(errors)


def validate_workspace_run(run: WorkspaceRunRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        run, nullable={"invalid_owner", "failure_label"}
    )
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
    if (
        run.terminal_status,
        run.replay_status,
        run.check_outcome,
        run.invalid_owner,
    ) not in _WORKSPACE_RUN_STATES:
        errors.append("workspace run state is inconsistent")
    if not isinstance(run.usage, Mapping):
        errors.append("usage must be a mapping")
    else:
        usage_errors, _ = _usage_measurement_errors(run.usage)
        errors.extend(usage_errors)
    if not isinstance(run.latency, Mapping):
        errors.append("latency must be a mapping")
    else:
        errors.extend(
            _measurement_errors(
                "latency",
                run.latency,
                required_keys=(
                    "workspace_seconds",
                    "agent_seconds",
                    "verification_seconds",
                    "solver_checkout_seconds",
                    "verifier_checkout_seconds",
                    "diff_replay_seconds",
                    "cleanup_seconds",
                ),
            )
        )
    return _validation(errors)


def validate_result_cache_identity(identity: ResultCacheIdentity) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        identity,
        nullable={
            "model_snapshot_id",
            "model_resolution_scope_id",
            "model_resolution_scope_started_at",
            "model_resolution_scope_ended_at",
            "hardware_profile_digest",
            "identity_digest",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    errors.extend(
        _model_identity_errors(
            requested_model_id=identity.requested_model_id,
            model_snapshot_id=identity.model_snapshot_id,
            scope_id=identity.model_resolution_scope_id,
            scope_started_at=identity.model_resolution_scope_started_at,
            scope_ended_at=identity.model_resolution_scope_ended_at,
        )
    )
    if identity.identity_digest:
        errors.extend(
            _self_digest_errors(identity, "identity_digest", "structured identity")
        )
    else:
        errors.append("identity_digest is required")
    return _validation(errors)


def validate_result(result: ResultRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        result, nullable={"invalid_owner", "failure_label"}
    )
    if invalid_mapping:
        return _validation(errors)
    identity_result = validate_result_cache_identity(result.cache_identity)
    errors.extend(f"cache_identity: {error}" for error in identity_result.errors)
    errors.extend(
        _ordered_timestamps(
            result, ["started_at", "finished_at", "result_available_at"]
        )
    )
    errors.extend(_self_digest_errors(result, "result_digest", "result record"))
    if (
        result.cache_identity.task_id != result.task_id
        or result.cache_identity.check_id != result.check_id
    ):
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
        errors.extend(
            _measurement_errors(
                "latency", result.latency, required_keys=("workspace_seconds",)
            )
        )
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
    if snapshot.leakage_lint_status == "passed" and not snapshot.feature_records:
        errors.append("passed feature snapshots must include feature_records")
    if snapshot.feature_records:
        if snapshot.feature_record_ids != tuple(
            record.feature_id for record in snapshot.feature_records
        ):
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
            errors.extend(
                f"feature_records[{index}]: {error}" for error in record_errors
            )
        try:
            expected_feature_records_digest = canonical_digest(snapshot.feature_records)
        except (OverflowError, TypeError, ValueError):
            errors.append("feature_records are not strict canonical JSON")
        else:
            if snapshot.feature_records_digest != expected_feature_records_digest:
                errors.append("feature_records_digest does not match feature_records")
    if snapshot.feature_snapshot_id != make_feature_snapshot_id(snapshot):
        errors.append("feature_snapshot_id does not match feature snapshot identity")
    errors.extend(
        _self_digest_errors(
            snapshot,
            "feature_snapshot_digest",
            "feature snapshot",
        )
    )
    return _validation(errors)


def make_feature_snapshot_id(snapshot: FeatureSnapshotRecord) -> str:
    return f"feature_snapshot_{canonical_digest((snapshot.origin_id, snapshot.feature_config_digest, snapshot.feature_records_digest, snapshot.result_view_digest))}"


def validate_selector_input(selector_input: SelectorInput) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(selector_input)
    if invalid_mapping:
        return _validation(errors)
    for field_name in ("pre_origin_result_ids", "pre_origin_result_digests"):
        if getattr(selector_input, field_name) == ():
            required_error = f"{field_name} is required"
            if required_error in errors:
                errors.remove(required_error)
    errors.extend(_selector_input_membership_errors(selector_input))
    errors.extend(_selector_input_budget_errors(selector_input))
    errors.extend(_selector_input_origin_errors(selector_input))
    if selector_input.selector_input_id != make_selector_input_id(selector_input):
        errors.append("selector_input_id does not match selector input identity")
    errors.extend(
        _self_digest_errors(selector_input, "selector_input_digest", "selector input")
    )
    return _validation(errors)


def _selector_input_membership_errors(
    selector_input: SelectorInput,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not selector_input.eligible_task_check_refs:
        errors.append("eligible_task_check_refs must not be empty")
    if (
        selector_input.pre_origin_result_ids is not None
        and selector_input.pre_origin_result_digests is not None
        and len(selector_input.pre_origin_result_ids)
        != len(selector_input.pre_origin_result_digests)
    ):
        errors.append("pre_origin_result_ids and pre_origin_result_digests must align")
    if len(set(selector_input.agent_ids)) != len(selector_input.agent_ids):
        errors.append("agent_ids must be unique")
    if len(selector_input.agent_ids) != len(selector_input.agent_record_digests):
        errors.append("agent_ids and agent_record_digests must align")
    ref_keys = tuple(
        task_check_ref_key(ref) for ref in selector_input.eligible_task_check_refs
    )
    if len(set(ref_keys)) != len(ref_keys):
        errors.append("eligible_task_check_refs must be unique")
    return tuple(errors)


def _selector_input_budget_errors(selector_input: SelectorInput) -> tuple[str, ...]:
    if (
        type(selector_input.selection_budget_limit) is not int
        or selector_input.selection_budget_limit < 1
    ):
        return ("selection_budget_limit must be positive",)
    if selector_input.budget_digest != canonical_digest(
        {"max_task_checks": selector_input.selection_budget_limit}
    ):
        return ("budget_digest does not match selection_budget_limit",)
    return ()


def _selector_input_origin_errors(selector_input: SelectorInput) -> tuple[str, ...]:
    errors: list[str] = []
    if not selector_input.feature_records_digest:
        errors.append("feature_records_digest is required")
    if selector_input.feature_snapshot_lint_status != "passed":
        errors.append("feature_snapshot_lint_status must be passed")
    if not selector_input.origin_as_of_cutoff:
        errors.append("origin_as_of_cutoff is required")
    errors.extend(_ordered_timestamps(selector_input, ("origin_as_of_cutoff",)))
    if not selector_input.origin_history_refs_digest:
        errors.append("origin_history_refs_digest is required")
    if selector_input.eligibility_mode not in {
        "strict_prospective",
        "counterfactual_replay",
    }:
        errors.append("eligibility_mode is not normalized")
    if (
        selector_input.origin_history_refs_digest
        and selector_input.origin_history_refs_digest
        != canonical_digest(selector_input.eligible_task_check_refs)
    ):
        errors.append("origin_history_refs_digest does not match eligible refs")
    return tuple(errors)


def make_selector_input_id(selector_input: SelectorInput) -> str:
    identity = {
        "origin_id": selector_input.origin_id,
        "task_pool_id": selector_input.task_pool_id,
        "task_pool_digest": selector_input.task_pool_digest,
        "feature_snapshot_id": selector_input.feature_snapshot_id,
        "agent_ids": selector_input.agent_ids,
        "agent_record_digests": selector_input.agent_record_digests,
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
        "eligibility_mode": selector_input.eligibility_mode,
    }
    return f"selector_input_{canonical_digest(identity)}"


def validate_task_pool(task_pool: TaskPoolRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        task_pool,
        nullable={
            "task_ids",
            "check_ids",
            "rejected_candidate_ids",
            "source_window_start",
            "source_window_end",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    if (
        canonical_digest(task_pool, exclude_self_digest=True)
        != task_pool.task_pool_digest
    ):
        errors.append("task_pool_digest does not match TaskPoolRecord")
    return _validation(errors)


def make_rolling_origin_policy_digest(
    *,
    as_of_cutoff_rule: str,
    eligibility_mode: str,
    holdout_overlap_policy: str,
    future_holdout_known: bool,
    allowed_dependency_cluster_ids: Sequence[str],
    maturity_lag_seconds: int,
) -> str:
    return canonical_digest(
        {
            "protocol_version": _ROLLING_ORIGIN_PROTOCOL_VERSION,
            "as_of_cutoff_rule": as_of_cutoff_rule,
            "eligibility_mode": eligibility_mode,
            "holdout_overlap_policy": holdout_overlap_policy,
            "future_holdout_known": future_holdout_known,
            "allowed_dependency_cluster_ids": tuple(allowed_dependency_cluster_ids),
            "future_cohort_time_basis": "task_material_available_at",
            "maturity_lag_seconds": maturity_lag_seconds,
        }
    )


def make_rolling_origin_id(origin: RollingOriginRecord) -> str:
    identity = canonical_data(origin)
    if not isinstance(identity, dict):
        raise TypeError("rolling origin must serialize as an object")
    identity.pop("origin_id", None)
    identity.pop("origin_digest", None)
    return f"origin_{canonical_digest(identity)}"


def validate_rolling_origin(origin: RollingOriginRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        origin,
        nullable={
            "history_window_start",
            "allowed_dependency_cluster_ids",
            "history_task_check_refs",
            "history_censored_task_check_refs",
            "future_holdout_task_check_refs",
            "future_censored_task_check_refs",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_rolling_origin_mode_errors(origin))
    errors.extend(_rolling_origin_cohort_errors(origin))
    errors.extend(_rolling_origin_cluster_errors(origin))
    errors.extend(_rolling_origin_time_errors(origin))
    errors.extend(_rolling_origin_maturity_errors(origin))
    if origin.history_window_start is not None:
        errors.extend(
            _ordered_timestamps(origin, ["history_window_start", "as_of_cutoff"])
        )
    errors.extend(_rolling_origin_cutoff_rule_errors(origin))
    errors.extend(_rolling_origin_policy_errors(origin))
    if origin.origin_id != make_rolling_origin_id(origin):
        errors.append("origin_id does not match rolling origin identity")
    errors.extend(_self_digest_errors(origin, "origin_digest", "rolling origin"))
    return _validation(errors)


def _rolling_origin_mode_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if origin.eligibility_mode not in {"strict_prospective", "counterfactual_replay"}:
        errors.append("eligibility_mode is not normalized")
    if origin.holdout_overlap_policy not in {
        "allow_cluster_overlap",
        "disjoint_clusters",
    }:
        errors.append("holdout_overlap_policy is not normalized")
    if type(origin.future_holdout_known) is not bool:
        errors.append("future_holdout_known must be a boolean")
    else:
        if origin.eligibility_mode == "strict_prospective" and (
            origin.future_holdout_known
        ):
            errors.append("strict_prospective must not know future holdout refs")
        if not origin.future_holdout_known and (
            origin.future_holdout_task_check_refs
            or origin.future_censored_task_check_refs
        ):
            errors.append(
                "future holdout and censored refs require future_holdout_known"
            )
    return tuple(errors)


def _rolling_origin_cohort_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    cohorts = (
        ("history_task_check_refs", origin.history_task_check_refs),
        ("history_censored_task_check_refs", origin.history_censored_task_check_refs),
        ("future_holdout_task_check_refs", origin.future_holdout_task_check_refs),
        ("future_censored_task_check_refs", origin.future_censored_task_check_refs),
    )
    errors = [
        f"{name} must not contain duplicates"
        for name, refs in cohorts
        if _task_check_refs_have_duplicates(refs)
    ]
    cohort_keys = tuple(
        {(ref.task_id, ref.check_id) for ref in refs} for _, refs in cohorts
    )
    all_keys: set[tuple[str, str]] = set().union(*cohort_keys)
    if sum(len(keys) for keys in cohort_keys) != len(all_keys):
        errors.append("mature and censored Task/Check cohorts must not overlap")
    return tuple(errors)


def _rolling_origin_cluster_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if type(origin.allowed_dependency_cluster_ids) is not tuple or any(
        type(cluster_id) is not str or not cluster_id
        for cluster_id in origin.allowed_dependency_cluster_ids
    ):
        return ("allowed_dependency_cluster_ids must be a tuple of nonempty strings",)
    if len(origin.allowed_dependency_cluster_ids) != len(
        set(origin.allowed_dependency_cluster_ids)
    ):
        errors.append("allowed_dependency_cluster_ids must not contain duplicates")
    if (
        tuple(sorted(origin.allowed_dependency_cluster_ids))
        != origin.allowed_dependency_cluster_ids
    ):
        errors.append("allowed_dependency_cluster_ids must be sorted")
    return tuple(errors)


def _rolling_origin_time_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    errors = _ordered_timestamps(origin, ["as_of_cutoff", "origin_time"])
    errors.extend(
        _ordered_timestamps(
            origin,
            ["as_of_cutoff", "future_window_start", "future_window_end"],
        )
    )
    errors.extend(
        _ordered_timestamps(origin, ["future_window_end", "label_maturity_cutoff"])
    )
    if origin.future_cohort_time_basis != "task_material_available_at":
        errors.append("future_cohort_time_basis is not supported")
    return tuple(errors)


def _rolling_origin_maturity_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    if (
        isinstance(origin.maturity_lag_seconds, bool)
        or not isinstance(origin.maturity_lag_seconds, int)
        or origin.maturity_lag_seconds < 0
    ):
        return ("maturity_lag_seconds must be a nonnegative integer",)
    try:
        expected_label_cutoff = format_utc_timestamp(
            parse_utc_timestamp(origin.future_window_end)
            + timedelta(seconds=origin.maturity_lag_seconds)
        )
    except (TypeError, ValueError):
        return ()
    if origin.label_maturity_cutoff != expected_label_cutoff:
        return ("label_maturity_cutoff does not match future window and maturity lag",)
    return ()


def _rolling_origin_cutoff_rule_errors(
    origin: RollingOriginRecord,
) -> tuple[str, ...]:
    if origin.as_of_cutoff_rule == "origin_time":
        expected_cutoff = origin.origin_time
    else:
        try:
            expected_cutoff = format_utc_timestamp(
                parse_utc_timestamp(origin.as_of_cutoff_rule)
            )
        except (TypeError, ValueError):
            return ("as_of_cutoff_rule must be origin_time or a valid ISO datetime",)
    try:
        cutoff_matches = parse_utc_timestamp(
            origin.as_of_cutoff
        ) == parse_utc_timestamp(expected_cutoff)
    except (TypeError, ValueError):
        return ()
    if not cutoff_matches:
        return ("as_of_cutoff does not match as_of_cutoff_rule",)
    return ()


def _rolling_origin_policy_errors(origin: RollingOriginRecord) -> tuple[str, ...]:
    expected_policy_digest = make_rolling_origin_policy_digest(
        as_of_cutoff_rule=origin.as_of_cutoff_rule,
        eligibility_mode=origin.eligibility_mode,
        holdout_overlap_policy=origin.holdout_overlap_policy,
        future_holdout_known=origin.future_holdout_known,
        allowed_dependency_cluster_ids=origin.allowed_dependency_cluster_ids,
        maturity_lag_seconds=origin.maturity_lag_seconds,
    )
    if origin.policy_digest != expected_policy_digest:
        return ("policy_digest does not match rolling-origin behavior",)
    return ()


def validate_result_matrix(matrix: ResultMatrix) -> ValidationResult:
    nullable = {"abstention_reason"}
    if matrix.matrix_role == "future_holdout":
        nullable.update({"task_check_refs", "cells"})
    errors, invalid_mapping = _initial_validation_errors(
        matrix,
        nullable=nullable,
    )
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
    errors.extend(_matrix_scoreable_state_errors(matrix))
    errors.extend(_self_digest_errors(matrix, "matrix_digest", "matrix"))
    return _validation(errors)


def matrix_denominator_error(matrix: ResultMatrix) -> str | None:
    """Return the first condition that makes a Result Matrix unsafe to score."""
    if matrix.abstention_reason:
        return matrix.abstention_reason
    if any(cell.cell_state == "missing" for cell in matrix.cells):
        return "missing_required_results"
    for ref in matrix.task_check_refs:
        states = {
            cell.cell_state
            for cell in matrix.cells
            if (cell.task_id, cell.check_id) == (ref.task_id, ref.check_id)
        }
        if "excluded" in states and states != {"excluded"}:
            return "agent_specific_invalid_exclusion"
    agents_with_results = {
        cell.agent_id for cell in matrix.cells if cell.cell_state == "result"
    }
    if any(agent_id not in agents_with_results for agent_id in matrix.agent_ids):
        return f"{matrix.matrix_role}_empty_agent_denominator"
    return None


def validate_evaluation_cell_set(cells: EvaluationCellSet) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        cells,
        nullable={
            "abstention_reason",
            "future_task_check_refs",
            "future_censored_task_check_refs",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    if _task_check_refs_have_duplicates(cells.selected_task_check_refs):
        errors.append("selected_task_check_refs must not contain duplicates")
    if _task_check_refs_have_duplicates(cells.future_task_check_refs):
        errors.append("future_task_check_refs must not contain duplicates")
    if _task_check_refs_have_duplicates(cells.future_censored_task_check_refs):
        errors.append("future_censored_task_check_refs must not contain duplicates")
    if set(cells.future_task_check_refs) & set(cells.future_censored_task_check_refs):
        errors.append("mature and censored future Task/Check refs must not overlap")
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
        errors.append(
            "evaluation cell set must include at least one cell for each selected and future task/check ref"
        )
    errors.extend(_self_digest_errors(cells, "cell_set_digest", "evaluation cell set"))
    return _validation(errors)


def validate_selector(selector: SelectorRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        selector, nullable={"training_source_digests"}
    )
    if invalid_mapping:
        return _validation(errors)
    if (
        selector.selector_family == "rule_mixture"
        and not selector.training_source_digests
    ):
        errors.append("fitted selectors must include training_source_digests")
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
    errors.extend(_self_digest_errors(selector, "selector_digest", "selector"))
    return _validation(errors)


def validate_benchmark_selection(
    selection: BenchmarkSelectionRecord,
) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        selection,
    )
    if invalid_mapping:
        return _validation(errors)
    if _task_check_refs_have_duplicates(selection.selected_task_check_refs):
        errors.append("selected_task_check_refs must not contain duplicates")
    selected_keys = {
        task_check_ref_key(ref) for ref in selection.selected_task_check_refs
    }
    weight_keys = set(selection.selected_weights)
    if selected_keys != weight_keys:
        errors.append("selected_weights must exactly cover selected_task_check_refs")
    if any(
        not _is_finite_positive_float(weight)
        for weight in selection.selected_weights.values()
    ):
        errors.append("selected_weights must be finite positive floats")
    if selection.eligibility_mode not in {
        "strict_prospective",
        "counterfactual_replay",
    }:
        errors.append("eligibility_mode is not normalized")
    errors.extend(_ordered_timestamps(selection, ["created_at"]))
    errors.extend(
        _self_digest_errors(selection, "selection_digest", "benchmark selection")
    )
    return _validation(errors)


def validate_metric(metric: MetricRecord) -> ValidationResult:
    errors, invalid_mapping = _initial_validation_errors(
        metric,
        nullable={
            "agent_id",
            "agent_pair",
            "aggregation_level",
            "budget_digest",
            "stratum_ref",
            "abstention_reason",
        },
    )
    if invalid_mapping:
        return _validation(errors)
    errors.extend(_metric_dimension_errors(metric))
    errors.extend(_metric_optional_reference_errors(metric))
    if not _is_finite_float(metric.metric_value):
        errors.append("metric_value must be a finite float")
    errors.extend(_metric_completeness_errors(metric))
    errors.extend(_ordered_timestamps(metric, ["computed_at"]))
    errors.extend(_self_digest_errors(metric, "metric_digest", "metric"))
    return _validation(errors)


def _metric_dimension_errors(metric: MetricRecord) -> tuple[str, ...]:
    if metric.metric_scope == "agent":
        if (
            not isinstance(metric.agent_id, str)
            or not metric.agent_id
            or metric.agent_pair is not None
            or metric.aggregation_level is not None
        ):
            return ("agent metrics must set only agent_id among dimension fields",)
        return ()
    if metric.metric_scope == "pair":
        pair = metric.agent_pair
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or any(not isinstance(agent_id, str) or not agent_id for agent_id in pair)
            or metric.agent_id is not None
            or metric.aggregation_level is not None
        ):
            return ("pairwise metrics must set only agent_pair among dimension fields",)
        return ()
    if metric.metric_scope == "aggregate":
        if (
            not isinstance(metric.aggregation_level, str)
            or not metric.aggregation_level
            or metric.agent_id is not None
            or metric.agent_pair is not None
        ):
            return (
                "aggregate metrics must set aggregation_level and no agent dimension",
            )
        return ()
    return ("metric_scope is not normalized",)


def _metric_optional_reference_errors(metric: MetricRecord) -> tuple[str, ...]:
    references = (metric.budget_digest, metric.stratum_ref)
    if any(
        value is not None and (not isinstance(value, str) or not value)
        for value in references
    ):
        return ("metric optional references must be nonempty strings when present",)
    return ()


def _metric_completeness_errors(metric: MetricRecord) -> tuple[str, ...]:
    complete_states = {"complete", "complete_with_exclusions"}
    incomplete_states = {"incomplete", "abstained", "invalid"}
    if metric.completeness_state not in complete_states | incomplete_states:
        return ("completeness_state is not normalized",)
    if (
        metric.completeness_state in complete_states
        and metric.abstention_reason is not None
    ):
        return ("complete metrics must not set abstention_reason",)
    if metric.completeness_state in incomplete_states and (
        not isinstance(metric.abstention_reason, str) or not metric.abstention_reason
    ):
        return ("incomplete metrics must set abstention_reason",)
    return ()


def make_task_id(repository_id: str, base_commit: str, source_digest: str) -> str:
    return f"task_{canonical_digest({'repository_id': repository_id, 'base_commit': base_commit, 'source_digest': source_digest})}"


def make_solver_material_digest(
    task_text: str, solver_material_refs: Sequence[str]
) -> str:
    return canonical_digest(
        {
            "format": _SOLVER_MATERIAL_FORMAT,
            "task_text": task_text,
            "solver_material_refs": tuple(solver_material_refs),
        }
    )


def make_check_id(task_id: str, check_digest: str) -> str:
    return (
        f"check_{canonical_digest({'task_id': task_id, 'check_digest': check_digest})}"
    )


def make_check_digest(check: CheckRecord) -> str:
    """Digest every Check field that can change execution or verification."""
    return canonical_digest(
        {
            "check_type": check.check_type,
            "check_manifest_digest": check.check_manifest_digest,
            "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
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
        requested_model_id=agent.requested_model_id,
        model_snapshot_id=agent.model_snapshot_id,
        model_resolution_scope_id=agent.model_resolution_scope_id,
        model_resolution_scope_started_at=agent.model_resolution_scope_started_at,
        model_resolution_scope_ended_at=agent.model_resolution_scope_ended_at,
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
        workspace_config_digest=canonical_digest(
            {
                "checkout_mode": _WORKSPACE_CHECKOUT_MODE,
                "workspace_config": workspace_config,
            }
        ),
        runtime_config_digest=canonical_digest(runtime_config),
        hardware_profile_digest=runtime_config.hardware_profile_digest,
        identity_digest="",
    )
    return record_with_digest(identity)


def agent_record_from_cache_identity(
    agent_id: str,
    identity: ResultCacheIdentity,
) -> AgentRecord:
    """Project the Agent fields frozen inside a Result cache identity."""
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=identity.agent_manifest_digest,
        requested_model_id=identity.requested_model_id,
        model_snapshot_id=identity.model_snapshot_id,
        model_resolution_scope_id=identity.model_resolution_scope_id,
        model_resolution_scope_started_at=identity.model_resolution_scope_started_at,
        model_resolution_scope_ended_at=identity.model_resolution_scope_ended_at,
        harness_digest=identity.harness_digest,
        repository_instruction_digest=identity.repository_instruction_digest,
        prompt_digest=identity.prompt_digest,
        tools_digest=identity.tools_digest,
        retrieval_digest=identity.retrieval_digest,
        skills_digest=identity.skills_digest,
        network_policy_digest=identity.network_policy_digest,
        adapter_digest=identity.adapter_digest,
    )


def cache_identity_agent_mismatches(
    identity: ResultCacheIdentity,
    agent: AgentRecord,
) -> tuple[str, ...]:
    projected = agent_record_from_cache_identity(agent.agent_id, identity)
    return tuple(
        field.name
        for field in fields(AgentRecord)
        if getattr(projected, field.name) != getattr(agent, field.name)
    )


def cache_identity_task_check_mismatches(
    identity: ResultCacheIdentity,
    task: TaskRecord,
    check: CheckRecord,
) -> tuple[str, ...]:
    expected_fields = {
        "task_id": task.task_id,
        "check_id": check.check_id,
        "repository_id": task.repository_id,
        "base_commit": task.base_commit,
        "solver_material_digest": task.solver_material_digest,
        "check_digest": make_check_digest(check),
    }
    return tuple(
        field_name
        for field_name, expected in expected_fields.items()
        if getattr(identity, field_name) != expected
    )


def result_cell_record_mismatches(
    cell: ResultCellRef,
    result: ResultRecord,
) -> tuple[str, ...]:
    """Return frozen Result fields that disagree with a bound cell."""
    expected_fields = {
        "result_id": result.result_id,
        "result_digest": result.result_digest,
        "agent_id": result.agent_id,
        "task_id": result.task_id,
        "check_id": result.check_id,
        "required_identity_digest": result.cache_identity.identity_digest,
        "outcome": result.outcome,
    }
    return tuple(
        field_name
        for field_name, expected in expected_fields.items()
        if getattr(cell, field_name) != expected
    )


def make_result_cache_key(identity: ResultCacheIdentity) -> str:
    validation = validate_result_cache_identity(identity)
    if not validation.ok:
        raise ValueError("result cache identity is incomplete or invalid")
    return identity.identity_digest


def make_selector_id(selector: SelectorRecord) -> str:
    identity = (
        selector.selector_family,
        selector.selector_version,
        selector.training_source_digests,
        selector.allowed_feature_classes,
        selector.config_digest,
    )
    return f"selector_{canonical_digest(identity)}"


def load_jsonl_records(path: Path, record_type: type) -> list[Any]:
    records: list[Any] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = line[:-1] if line.endswith("\n") else line
            try:
                if not payload:
                    raise ValueError("blank JSONL records are not allowed")
                if payload != payload.strip():
                    raise ValueError(f"{record_type.__name__} is not canonical JSON")
                data = json.loads(
                    payload,
                    parse_constant=_reject_json_constant,
                )
                record = _from_data(record_type, data)
                if canonical_json(record) != payload:
                    raise ValueError(f"{record_type.__name__} is not canonical JSON")
                records.append(record)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}: line {line_number}: {exc}") from exc
    return records


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def write_jsonl_records(path: Path, records: Sequence[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as tmp:
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
        _from_data(type(record), canonical_data(record))
    except (OverflowError, TypeError, ValueError) as exc:
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
        instants = [parse_utc_timestamp(value) for value in values]
    except ValueError:
        return [f"timestamps must be valid ISO datetimes: {', '.join(names)}"]
    if any(left > right for left, right in zip(instants, instants[1:])):
        return [f"timestamps must be ordered: {', '.join(names)}"]
    return []


def _model_identity_errors(
    *,
    requested_model_id: object,
    model_snapshot_id: object,
    scope_id: object,
    scope_started_at: object,
    scope_ended_at: object,
) -> list[str]:
    if not isinstance(requested_model_id, str) or not requested_model_id:
        return ["requested_model_id is required"]
    scope_values = (scope_id, scope_started_at, scope_ended_at)
    if isinstance(model_snapshot_id, str) and model_snapshot_id:
        if any(value is not None for value in scope_values):
            return ["resolved model snapshots must not set a model resolution scope"]
        return []
    if model_snapshot_id is not None:
        return ["model_snapshot_id must be a nonempty string or null"]
    if any(not isinstance(value, str) or not value for value in scope_values):
        return ["unresolved model aliases require a complete model resolution scope"]
    assert isinstance(scope_started_at, str)
    assert isinstance(scope_ended_at, str)
    try:
        started_at = parse_utc_timestamp(scope_started_at)
        ended_at = parse_utc_timestamp(scope_ended_at)
    except ValueError:
        return ["model resolution scope timestamps must be valid ISO datetimes"]
    if started_at >= ended_at:
        return ["model resolution scope must have positive duration"]
    return []


def _result_state_errors(result: ResultRecord) -> list[str]:
    state = (
        result.terminal_status,
        result.scoreable_state,
        result.outcome,
        result.invalid_owner,
    )
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


def _is_finite_positive_float(value: Any) -> bool:
    return _is_finite_float(value) and value > 0


def _is_finite_float(value: Any) -> bool:
    return type(value) is float and math.isfinite(value)


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
        errors.extend(_cell_state_errors(cell))
    if require_full_denominator:
        _validate_full_cell_denominator(
            errors,
            seen_cells,
            agent_ids,
            task_check_refs,
        )


def _cell_state_errors(cell: ResultCellRef) -> tuple[str, ...]:
    if cell.cell_state == "result":
        return _result_cell_state_errors(cell)
    if cell.cell_state == "excluded":
        return _excluded_cell_state_errors(cell)
    if cell.cell_state == "missing":
        return _missing_cell_state_errors(cell)
    return ("cell_state is not normalized",)


def _result_cell_state_errors(cell: ResultCellRef) -> tuple[str, ...]:
    errors: list[str] = []
    if (
        not isinstance(cell.result_id, str)
        or not cell.result_id
        or not isinstance(cell.result_digest, str)
        or not cell.result_digest
    ):
        errors.append("result cells must bind result_id and result_digest")
    if cell.exclusion_reason is not None:
        errors.append("result cells must not set exclusion_reason")
    if cell.outcome not in _RESULT_OUTCOMES:
        errors.append("result cells must set a normalized outcome")
    return tuple(errors)


def _excluded_cell_state_errors(cell: ResultCellRef) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(cell.exclusion_reason, str) or not cell.exclusion_reason:
        errors.append("excluded cells must set exclusion_reason")
    has_binding_field = cell.result_id is not None or cell.result_digest is not None
    has_result_binding = (
        isinstance(cell.result_id, str)
        and bool(cell.result_id)
        and isinstance(cell.result_digest, str)
        and bool(cell.result_digest)
    )
    if has_binding_field and not has_result_binding:
        errors.append(
            "excluded cells must bind both result_id and result_digest or neither"
        )
    elif has_result_binding and cell.outcome not in _RESULT_OUTCOMES:
        errors.append("excluded cells with a result must set a normalized outcome")
    elif not has_binding_field and cell.outcome is not None:
        errors.append("excluded cells without a result must not set outcome")
    return tuple(errors)


def _missing_cell_state_errors(cell: ResultCellRef) -> tuple[str, ...]:
    errors: list[str] = []
    if cell.result_id is not None or cell.result_digest is not None:
        errors.append("missing cells must not bind a result")
    if cell.exclusion_reason is not None or cell.outcome is not None:
        errors.append("missing cells must not set exclusion_reason or outcome")
    return tuple(errors)


def _validate_full_cell_denominator(
    errors: list[str],
    seen_cells: set[tuple[str, str, str]],
    agent_ids: Sequence[str],
    task_check_refs: Sequence[TaskCheckRef],
) -> None:
    expected_cells = {
        (agent_id, ref.task_id, ref.check_id)
        for agent_id in agent_ids
        for ref in task_check_refs
    }
    if seen_cells != expected_cells:
        errors.append(
            "matrix cells must exactly cover every Agent/Task/Check denominator cell"
        )


def _matrix_scoreable_state_errors(matrix: ResultMatrix) -> tuple[str, ...]:
    if matrix.scoreable_state not in _MATRIX_SCOREABLE_STATES:
        return ("scoreable_state is not normalized",)
    if matrix.abstention_reason is not None:
        if matrix.scoreable_state != "abstained":
            return ("matrix with an abstention reason must be abstained",)
        return ()
    if matrix.scoreable_state == "abstained":
        return ("abstained matrices require an abstention reason",)
    expected_state = "complete"
    if any(cell.cell_state == "missing" for cell in matrix.cells):
        expected_state = "incomplete"
    elif any(cell.cell_state == "excluded" for cell in matrix.cells):
        expected_state = "complete_with_exclusions"
    if matrix.scoreable_state != expected_state:
        return ("scoreable_state does not match matrix cells",)
    return ()


def _task_check_refs_have_duplicates(refs: Sequence[TaskCheckRef]) -> bool:
    keys = tuple((ref.task_id, ref.check_id) for ref in refs)
    return len(keys) != len(set(keys))


def _from_data(record_type: type, data: Any) -> Any:
    if not is_dataclass(record_type):
        return _coerce_value(
            record_type,
            data,
            getattr(record_type, "__name__", "record"),
        )
    if not isinstance(data, MappingABC):
        raise TypeError(f"{record_type.__name__} must be a JSON object")
    expected_fields = {field.name for field in fields(record_type)}
    observed_fields = set(data)
    missing = sorted(expected_fields - observed_fields)
    unknown = sorted(observed_fields - expected_fields)
    if missing:
        raise TypeError(
            f"{record_type.__name__} schema is missing keys: {', '.join(missing)}"
        )
    if unknown:
        raise TypeError(
            f"{record_type.__name__} schema has unknown keys: {', '.join(unknown)}"
        )
    type_hints = get_type_hints(record_type)
    kwargs: dict[str, Any] = {}
    for field in fields(record_type):
        kwargs[field.name] = _coerce_value(
            type_hints[field.name],
            data[field.name],
            f"{record_type.__name__}.{field.name}",
        )
    return record_type(**kwargs)


def _coerce_value(expected_type: Any, data: Any, path: str) -> Any:
    if expected_type is Any:
        return data
    origin = get_origin(expected_type)
    args = get_args(expected_type)
    if origin in {Union, UnionType}:
        return _coerce_union(args, data, path)
    if origin is tuple:
        return _coerce_tuple(args, data, path)
    if origin is list:
        return _coerce_list(args, data, path)
    if origin in {dict, Mapping, MappingABC}:
        return _coerce_mapping(args, data, path)
    if isinstance(expected_type, type) and is_dataclass(expected_type):
        return _from_data(expected_type, data)
    return _coerce_scalar(expected_type, data, path)


def _coerce_union(args: tuple[Any, ...], data: Any, path: str) -> Any:
    if data is None:
        if type(None) in args:
            return None
        raise TypeError(f"{path} must not be null")
    errors: list[TypeError] = []
    for option in (arg for arg in args if arg is not type(None)):
        try:
            return _coerce_value(option, data, path)
        except TypeError as exc:
            errors.append(exc)
    if errors:
        raise errors[0]
    raise TypeError(f"{path} does not match its schema type")


def _coerce_tuple(args: tuple[Any, ...], data: Any, path: str) -> tuple[Any, ...]:
    if not isinstance(data, list):
        raise TypeError(f"{path} must be an array")
    if len(args) == 2 and args[1] is Ellipsis:
        return tuple(
            _coerce_value(args[0], item, f"{path}[{index}]")
            for index, item in enumerate(data)
        )
    if args and len(data) != len(args):
        raise TypeError(f"{path} must contain exactly {len(args)} items")
    return tuple(
        _coerce_value(
            args[index] if args else Any,
            item,
            f"{path}[{index}]",
        )
        for index, item in enumerate(data)
    )


def _coerce_list(args: tuple[Any, ...], data: Any, path: str) -> list[Any]:
    if not isinstance(data, list):
        raise TypeError(f"{path} must be an array")
    item_type = args[0] if args else Any
    return [
        _coerce_value(item_type, item, f"{path}[{index}]")
        for index, item in enumerate(data)
    ]


def _coerce_mapping(
    args: tuple[Any, ...],
    data: Any,
    path: str,
) -> dict[Any, Any]:
    if not isinstance(data, dict):
        raise TypeError(f"{path} must be an object")
    key_type = args[0] if args else str
    value_type = args[1] if len(args) > 1 else Any
    values: dict[Any, Any] = {}
    for key, value in data.items():
        normalized_key = _coerce_value(key_type, key, f"{path} key")
        values[normalized_key] = _coerce_value(
            value_type,
            value,
            f"{path}.{key}",
        )
    return values


def _coerce_scalar(expected_type: Any, data: Any, path: str) -> Any:
    if expected_type is str:
        if not isinstance(data, str):
            raise TypeError(f"{path} must be a string")
        return data
    if expected_type is bool:
        if not isinstance(data, bool):
            raise TypeError(f"{path} must be a boolean")
        return data
    if expected_type is int:
        if isinstance(data, bool) or not isinstance(data, int):
            raise TypeError(f"{path} must be an integer")
        return data
    if expected_type is float:
        if isinstance(data, bool) or not isinstance(data, int | float):
            raise TypeError(f"{path} must be a number")
        try:
            return float(data)
        except OverflowError:
            raise TypeError(f"{path} must be representable as a float") from None
    if isinstance(expected_type, type) and not isinstance(data, expected_type):
        raise TypeError(f"{path} has the wrong type")
    return data
