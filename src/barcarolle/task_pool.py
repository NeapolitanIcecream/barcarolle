"""Task Pool generation, certification, freezing, and summaries."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Mapping, Sequence
import hashlib
import json
import math
import os
import shutil

from barcarolle.records import (
    CheckRecord,
    RuntimeConfig,
    SourceEventRecord,
    TaskPoolRecord,
    TaskRecord,
    ValidationResult,
    WorkspaceConfig,
    canonical_data,
    canonical_digest,
    format_utc_timestamp,
    load_jsonl_records,
    make_check_id,
    make_source_event_id,
    make_solver_material_digest,
    make_task_id,
    parse_utc_timestamp,
    record_with_digest,
    validate_check,
    validate_runtime_config,
    validate_source_event,
    validate_task,
    validate_task_pool,
    validate_workspace_config,
    write_jsonl_records,
)
from barcarolle.verification import (
    VERIFICATION_ADAPTER_DIGEST,
    CheckOutcome,
    summarize_evidence,
)
from barcarolle.workspace import (
    CapturedDiff,
    WorkspaceRunContext,
    apply_diff,
    cleanup_workspace,
    check_execution_binding_digest,
    create_verifier_workspace,
    validate_solver_material_refs,
    verify_agent_diff,
)


_VALIDATION_SETUP_FAILURES = frozenset(
    {
        "check_command_mismatch",
        "check_invalid",
        "check_launch_error",
        "check_workspace_mismatch",
        "diff_replay_launch_error",
        "hidden_material_mismatch",
        "invalid_hidden_material_destination",
        "missing_check_command",
        "missing_git_checkout",
        "missing_repository_source",
        "missing_verification_material",
        "not_verifier_workspace",
        "verifier_preparation_failed",
        "verifier_workspace_error",
        "verification_error",
        "workspace_cleanup_failed",
    }
)
_CERTIFICATION_EVIDENCE_FIELDS = (
    "candidate_id",
    "accepted",
    "rejection_reasons",
    "repeat_count",
    "base_check",
    "reference_patch_check",
    "reference_patch_digest",
    "task_digest",
    "check_digest",
    "workspace_config_digest",
    "runtime_config_digest",
    "check_execution_binding_digest",
    "verification_adapter_digest",
)


@dataclass(frozen=True)
class TimeRange:
    start: str
    end: str

    def contains(self, value: str) -> bool:
        instant = parse_utc_timestamp(value)
        return (
            parse_utc_timestamp(self.start) <= instant <= parse_utc_timestamp(self.end)
        )


@dataclass(frozen=True)
class TaskSourceConfig:
    source_family: str
    source_events: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class ImportConfig:
    source_family: str = "user_import"


@dataclass(frozen=True)
class CertificationConfig:
    repeat_count: int = 1

    def __post_init__(self) -> None:
        if type(self.repeat_count) is not int or self.repeat_count < 1:
            raise ValueError("repeat_count must be a positive integer")


@dataclass(frozen=True)
class TaskCandidate:
    candidate_id: str
    repository_id: str
    base_commit: str
    source_family: str
    source_ref: str
    source_resolved_at: str
    task_material_available_at: str
    check_material_available_at: str
    task_text: str
    solver_material_refs: tuple[str, ...]
    dependency_cluster_id: str
    sampling_stratum: str
    check_manifest_digest: str
    hidden_check_bundle_digest: str
    resource_limits: Mapping[str, Any]
    oracle_source: str
    check_type: str


@dataclass(frozen=True)
class CandidateBatch:
    candidates: tuple[TaskCandidate, ...]
    excluded_source_events: tuple[SourceEventRecord, ...] = ()


@dataclass(frozen=True)
class CertificationResult:
    candidate_id: str
    accepted: bool
    task: TaskRecord | None
    check: CheckRecord | None
    rejection_reasons: tuple[str, ...]
    evidence: Mapping[str, Any]
    evidence_digest: str


@dataclass(frozen=True)
class TaskPoolBundle:
    task_pool: TaskPoolRecord
    source_events: tuple[SourceEventRecord, ...]
    tasks: tuple[TaskRecord, ...]
    checks: tuple[CheckRecord, ...]
    certification_evidence: tuple[Mapping[str, Any], ...]

    @property
    def checks_by_id(self) -> Mapping[str, CheckRecord]:
        return {check.check_id: check for check in self.checks}


@dataclass(frozen=True)
class _CertificationEvidenceValues:
    candidate_id: str | None
    accepted: bool | None
    rejection_reasons: tuple[str, ...]
    repeat_count: int
    task_digest: str | None
    check_digest: str | None
    base_outcomes: tuple[str, ...]
    reference_outcomes: tuple[str, ...]


def filter_history_candidates(
    repository_id: str,
    time_range: TimeRange,
    task_source_config: TaskSourceConfig,
) -> CandidateBatch:
    candidates: list[TaskCandidate] = []
    excluded: list[SourceEventRecord] = []
    for event in task_source_config.source_events:
        event_with_defaults = {
            **event,
            "repository_id": event.get("repository_id", repository_id),
            "source_family": event.get(
                "source_family", task_source_config.source_family
            ),
        }
        resolved_at = _required_str(event_with_defaults, "source_resolved_at")
        if not time_range.contains(resolved_at):
            excluded.append(
                _excluded_source_event(
                    event_with_defaults,
                    "outside_source_time_range",
                )
            )
            continue
        if not event_with_defaults.get("task_material_available_at"):
            excluded.append(
                _excluded_source_event(
                    event_with_defaults,
                    "task_material_unavailable",
                )
            )
            continue
        if not event_with_defaults.get("check_material_available_at"):
            excluded.append(
                _excluded_source_event(
                    event_with_defaults,
                    "check_material_unavailable",
                )
            )
            continue
        candidates.append(_candidate_from_mapping(event_with_defaults))
    return _candidate_batch(candidates, excluded)


def import_task_candidates(
    source_path: Path,
    import_config: ImportConfig,
) -> CandidateBatch:
    raw_records = _load_candidate_payloads(source_path)
    candidates = []
    for payload in raw_records:
        candidates.append(
            _candidate_from_mapping(
                {"source_family": import_config.source_family, **payload}
            )
        )
    return _candidate_batch(candidates, ())


def candidate_batch(candidates: Sequence[TaskCandidate]) -> CandidateBatch:
    return _candidate_batch(candidates, ())


def finalize_source_event_records(
    batch: CandidateBatch,
    certification_results: Sequence[CertificationResult],
) -> tuple[SourceEventRecord, ...]:
    results_by_candidate = _certification_results_by_candidate(
        batch,
        certification_results,
    )
    records = list(batch.excluded_source_events)
    records.extend(
        _source_event_from_certification(
            candidate,
            results_by_candidate[candidate.candidate_id],
        )
        for candidate in batch.candidates
    )
    return _validated_source_event_records(records)


def build_check_candidate(candidate: TaskCandidate) -> CheckRecord:
    task_id = make_task_id(
        candidate.repository_id,
        candidate.base_commit,
        canonical_digest(_source_identity(candidate)),
    )
    return CheckRecord(
        check_id=make_check_id(task_id, candidate.check_manifest_digest),
        task_id=task_id,
        check_type=candidate.check_type,
        check_manifest_digest=candidate.check_manifest_digest,
        hidden_check_bundle_digest=candidate.hidden_check_bundle_digest,
        resource_limits=candidate.resource_limits,
        oracle_source=candidate.oracle_source,
        check_material_available_at=candidate.check_material_available_at,
    )


def certify_task_candidate(
    candidate: TaskCandidate,
    certification_config: CertificationConfig,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    reference_patch: CapturedDiff,
    run_context: WorkspaceRunContext,
) -> CertificationResult:
    _validate_certification_configs(workspace_config, runtime_config)
    rejection_reasons: list[str] = []
    check = build_check_candidate(candidate)
    task = _task_from_candidate(candidate, check)

    if not candidate.task_text.strip():
        rejection_reasons.append("task_text must not be empty")

    task_validation = validate_task(task)
    check_validation = validate_check(check)
    rejection_reasons.extend(task_validation.errors)
    rejection_reasons.extend(check_validation.errors)

    reference_patch_digest = hashlib.sha256(
        reference_patch.diff_text.encode("utf-8")
    ).hexdigest()
    if reference_patch.diff_digest != reference_patch_digest:
        rejection_reasons.append("reference patch digest does not match its content")

    base_outcomes: tuple[CheckOutcome, ...] = ()
    reference_outcomes: tuple[CheckOutcome, ...] = ()
    if not rejection_reasons:
        bases: list[CheckOutcome] = []
        patched: list[CheckOutcome] = []
        for attempt in range(1, certification_config.repeat_count + 1):
            base_outcome = _run_task_check(
                task,
                check,
                workspace_config,
                runtime_config,
                None,
                run_context,
                validate_material_refs=True,
            )
            bases.append(base_outcome)
            if (
                base_outcome.outcome == "invalid"
                and base_outcome.failure_label in _VALIDATION_SETUP_FAILURES
            ):
                raise RuntimeError(
                    "task validation could not execute the base check: "
                    + (base_outcome.failure_label or "unknown failure")
                )
            if base_outcome.outcome != "fail":
                rejection_reasons.append(
                    _unexpected_check_outcome(
                        f"base check attempt {attempt}",
                        "fail",
                        base_outcome,
                    )
                )
                break
            outcome = _run_task_check(
                task,
                check,
                workspace_config,
                runtime_config,
                reference_patch,
                run_context,
            )
            patched.append(outcome)
            if (
                outcome.outcome == "invalid"
                and outcome.failure_label in _VALIDATION_SETUP_FAILURES
            ):
                raise RuntimeError(
                    "task validation could not execute the reference patch check: "
                    + (outcome.failure_label or "unknown failure")
                )
            if outcome.outcome != "pass":
                rejection_reasons.append(
                    _unexpected_check_outcome(
                        f"reference patch check attempt {attempt}",
                        "pass",
                        outcome,
                    )
                )
                break
        base_outcomes = tuple(bases)
        reference_outcomes = tuple(patched)

    accepted = not rejection_reasons
    evidence = {
        "candidate_id": candidate.candidate_id,
        "accepted": accepted,
        "rejection_reasons": tuple(rejection_reasons),
        "repeat_count": certification_config.repeat_count,
        "base_check": tuple(
            summarize_evidence(outcome).__dict__ for outcome in base_outcomes
        ),
        "reference_patch_check": tuple(
            summarize_evidence(outcome).__dict__ for outcome in reference_outcomes
        ),
        "reference_patch_digest": reference_patch_digest,
        "task_digest": canonical_digest(task),
        "check_digest": canonical_digest(check),
        "workspace_config_digest": canonical_digest(workspace_config),
        "runtime_config_digest": canonical_digest(runtime_config),
        "check_execution_binding_digest": check_execution_binding_digest(
            check, run_context
        ),
        "verification_adapter_digest": VERIFICATION_ADAPTER_DIGEST,
    }
    return CertificationResult(
        candidate_id=candidate.candidate_id,
        accepted=accepted,
        task=task if accepted else None,
        check=check if accepted else None,
        rejection_reasons=tuple(rejection_reasons),
        evidence=evidence,
        evidence_digest=canonical_digest(evidence),
    )


def _validate_certification_configs(
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> None:
    for config_name, validation in (
        ("workspace_config", validate_workspace_config(workspace_config)),
        ("runtime_config", validate_runtime_config(runtime_config)),
    ):
        if not validation.ok:
            raise ValueError(
                f"{config_name} is invalid: {', '.join(validation.errors)}"
            )


def freeze_task_pool(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    certification_results: Sequence[CertificationResult],
    source_events: Sequence[SourceEventRecord],
    metadata: Mapping[str, object],
) -> TaskPoolRecord:
    _validate_accepted_task_check_linkage(accepted_tasks, accepted_checks)
    required_metadata = _require_metadata(
        metadata,
        (
            "repository_id",
            "task_records_ref",
            "check_records_ref",
            "certification_evidence_ref",
            "source_event_records_ref",
            "generator_config_digest",
            "certification_config_digest",
            "created_at",
        ),
    )
    task_pool_id = metadata.get("task_pool_id", "")
    if not isinstance(task_pool_id, str):
        raise ValueError("task_pool_id must be a string")
    repository_id = required_metadata["repository_id"]
    source_window_start, source_window_end = _metadata_source_window(metadata)
    _validate_accepted_records(accepted_tasks, accepted_checks, repository_id)
    task_records_digest = canonical_digest(tuple(accepted_tasks))
    check_records_digest = canonical_digest(tuple(accepted_checks))
    ordered_results = _validated_certification_results(
        accepted_tasks,
        accepted_checks,
        certification_results,
    )
    rejection_summary = _rejection_summary(ordered_results)
    certification_evidence = certification_evidence_records(ordered_results)
    source_event_records = tuple(source_events)

    record = TaskPoolRecord(
        task_pool_id=task_pool_id,
        task_pool_digest="",
        repository_id=repository_id,
        task_ids=tuple(task.task_id for task in accepted_tasks),
        check_ids=tuple(check.check_id for check in accepted_checks),
        task_records_ref=required_metadata["task_records_ref"],
        task_records_digest=task_records_digest,
        check_records_ref=required_metadata["check_records_ref"],
        check_records_digest=check_records_digest,
        certification_evidence_ref=required_metadata["certification_evidence_ref"],
        source_event_records_ref=required_metadata["source_event_records_ref"],
        source_event_records_digest=canonical_digest(source_event_records),
        rejected_candidate_ids=tuple(
            result.candidate_id for result in ordered_results if not result.accepted
        ),
        rejection_summary_digest=canonical_digest(rejection_summary),
        certification_evidence_digest=canonical_digest(certification_evidence),
        generator_config_digest=required_metadata["generator_config_digest"],
        certification_config_digest=required_metadata["certification_config_digest"],
        created_at=required_metadata["created_at"],
        source_window_start=source_window_start,
        source_window_end=source_window_end,
    )
    if not record.task_pool_id:
        record = TaskPoolRecord(
            **{
                **record.__dict__,
                "task_pool_id": f"task_pool_{canonical_digest(record)}",
            }
        )
    record = record_with_digest(record)
    validation = validate_task_pool_artifacts(
        record,
        accepted_tasks,
        accepted_checks,
        certification_evidence,
        source_event_records,
    )
    if not validation.ok:
        raise ValueError(
            "task pool artifacts failed validation: " + "; ".join(validation.errors)
        )
    return record


def certification_evidence_records(
    results: Sequence[CertificationResult],
) -> tuple[Mapping[str, Any], ...]:
    ordered = tuple(
        sorted(
            (_require_certification_result(result) for result in results),
            key=lambda result: result.candidate_id,
        )
    )
    candidate_ids = tuple(result.candidate_id for result in ordered)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("certification results contain duplicate candidate_id values")
    for result in ordered:
        if result.evidence_digest != canonical_digest(result.evidence):
            raise ValueError(
                "certification evidence digest does not match structured evidence"
            )
    return tuple(result.evidence for result in ordered)


def validate_task_pool_artifacts(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    certification_evidence: Sequence[Mapping[str, Any]],
    source_events: Sequence[SourceEventRecord],
) -> ValidationResult:
    tasks_tuple = tuple(tasks)
    checks_tuple = tuple(checks)
    evidence_tuple = tuple(certification_evidence)
    source_events_tuple = tuple(source_events)
    member_validation = validate_task_pool_members(
        task_pool,
        tasks_tuple,
        checks_tuple,
    )
    if not member_validation.ok:
        return member_validation
    errors: list[str] = []
    if canonical_digest(evidence_tuple) != task_pool.certification_evidence_digest:
        errors.append("certification evidence digest does not match TaskPoolRecord")
    if canonical_digest(source_events_tuple) != task_pool.source_event_records_digest:
        errors.append("source event records digest does not match TaskPoolRecord")
    errors.extend(
        _certification_evidence_errors(
            task_pool,
            tasks_tuple,
            checks_tuple,
            evidence_tuple,
        )
    )
    errors.extend(
        _source_event_errors(
            task_pool,
            tasks_tuple,
            checks_tuple,
            evidence_tuple,
            source_events_tuple,
        )
    )
    return ValidationResult.fail(errors) if errors else ValidationResult.pass_()


def validate_task_pool_members(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
) -> ValidationResult:
    record_validation = validate_task_pool(task_pool)
    if not record_validation.ok:
        return record_validation
    tasks_tuple = tuple(tasks)
    checks_tuple = tuple(checks)
    try:
        _validate_accepted_records(
            tasks_tuple,
            checks_tuple,
            task_pool.repository_id,
        )
    except ValueError as exc:
        return ValidationResult.fail((str(exc),))
    errors: list[str] = []
    if canonical_digest(tasks_tuple) != task_pool.task_records_digest:
        errors.append("task records digest does not match TaskPoolRecord")
    if tuple(task.task_id for task in tasks_tuple) != task_pool.task_ids:
        errors.append("task records do not match TaskPoolRecord task_ids")
    if canonical_digest(checks_tuple) != task_pool.check_records_digest:
        errors.append("check records digest does not match TaskPoolRecord")
    if tuple(check.check_id for check in checks_tuple) != task_pool.check_ids:
        errors.append("check records do not match TaskPoolRecord check_ids")
    try:
        _validate_accepted_task_check_linkage(tasks_tuple, checks_tuple)
    except ValueError as exc:
        errors.append(str(exc))
    return ValidationResult.fail(errors) if errors else ValidationResult.pass_()


def validated_task_pool_bundle(
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    certification_evidence: Sequence[Mapping[str, Any]],
    source_events: Sequence[SourceEventRecord],
) -> TaskPoolBundle:
    validation = validate_task_pool_artifacts(
        task_pool,
        tasks,
        checks,
        certification_evidence,
        source_events,
    )
    if not validation.ok:
        raise ValueError("task pool bundle is invalid: " + "; ".join(validation.errors))
    return TaskPoolBundle(
        task_pool=task_pool,
        source_events=tuple(source_events),
        tasks=tuple(tasks),
        checks=tuple(checks),
        certification_evidence=tuple(
            canonical_data(record) for record in certification_evidence
        ),
    )


def load_validated_task_pool_bundle(
    task_pool: TaskPoolRecord,
    artifact_root: Path,
) -> TaskPoolBundle:
    try:
        tasks = tuple(
            load_jsonl_records(
                _artifact_ref_path(task_pool.task_records_ref, artifact_root),
                TaskRecord,
            )
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("task records are unavailable or invalid") from exc
    try:
        checks = tuple(
            load_jsonl_records(
                _artifact_ref_path(task_pool.check_records_ref, artifact_root),
                CheckRecord,
            )
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("check records are unavailable or invalid") from exc
    try:
        evidence = _load_certification_evidence_records(
            _artifact_ref_path(
                task_pool.certification_evidence_ref,
                artifact_root,
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError("certification evidence is unavailable or invalid") from exc
    try:
        source_events = tuple(
            load_jsonl_records(
                _artifact_ref_path(
                    task_pool.source_event_records_ref,
                    artifact_root,
                ),
                SourceEventRecord,
            )
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("source event records are unavailable or invalid") from exc
    return validated_task_pool_bundle(
        task_pool,
        tasks,
        checks,
        evidence,
        source_events,
    )


def publish_task_pool_bundle(
    bundle: TaskPoolBundle,
    artifact_root: Path,
) -> Path:
    validated_task_pool_bundle(
        bundle.task_pool,
        bundle.tasks,
        bundle.checks,
        bundle.certification_evidence,
        bundle.source_events,
    )
    relative_dir = _task_pool_bundle_relative_dir(bundle.task_pool)
    root = artifact_root.resolve()
    target = _artifact_ref_path(relative_dir.as_posix(), root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        _require_identical_published_bundle(bundle, root, target)
        return target
    staging = Path(mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        manifest_path = staging / "task-pool.jsonl"
        tasks_path = staging / "tasks.jsonl"
        checks_path = staging / "checks.jsonl"
        evidence_path = staging / "certification-evidence.jsonl"
        source_events_path = staging / "source-events.jsonl"
        write_jsonl_records(manifest_path, (bundle.task_pool,))
        write_jsonl_records(tasks_path, bundle.tasks)
        write_jsonl_records(checks_path, bundle.checks)
        write_jsonl_records(
            evidence_path,
            bundle.certification_evidence,
        )
        write_jsonl_records(source_events_path, bundle.source_events)
        for path in (
            manifest_path,
            tasks_path,
            checks_path,
            evidence_path,
            source_events_path,
        ):
            _fsync_file(path)
        _fsync_directory(staging)
        staged_tasks = tuple(load_jsonl_records(tasks_path, TaskRecord))
        staged_checks = tuple(load_jsonl_records(checks_path, CheckRecord))
        staged_evidence = _load_certification_evidence_records(evidence_path)
        staged_source_events = tuple(
            load_jsonl_records(
                source_events_path,
                SourceEventRecord,
            )
        )
        validated_task_pool_bundle(
            bundle.task_pool,
            staged_tasks,
            staged_checks,
            staged_evidence,
            staged_source_events,
        )
        try:
            staging.replace(target)
            _fsync_directory(target.parent)
        except OSError:
            if not target.exists():
                raise
            _require_identical_published_bundle(bundle, root, target)
        return target
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _certification_evidence_errors(
    task_pool: TaskPoolRecord,
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    evidence: tuple[Mapping[str, Any], ...],
) -> tuple[str, ...]:
    values, parsing_errors = _parsed_certification_evidence(evidence)
    return (
        *parsing_errors,
        *_certification_evidence_collection_errors(task_pool, evidence, values),
        *_accepted_certification_coverage_errors(tasks, checks, values),
        *_rejected_certification_coverage_errors(task_pool, values),
    )


def _parsed_certification_evidence(
    evidence: Sequence[object],
) -> tuple[tuple[_CertificationEvidenceValues, ...], tuple[str, ...]]:
    values: list[_CertificationEvidenceValues] = []
    errors: list[str] = []
    for index, record in enumerate(evidence):
        parsed, record_errors = _certification_evidence_values(record, index)
        errors.extend(record_errors)
        if parsed is None:
            continue
        values.append(parsed)
        if parsed.accepted is not None:
            errors.extend(_certification_evidence_semantic_errors(parsed))
    return tuple(values), tuple(errors)


def _certification_evidence_collection_errors(
    task_pool: TaskPoolRecord,
    evidence: Sequence[object],
    values: Sequence[_CertificationEvidenceValues],
) -> tuple[str, ...]:
    candidate_ids = [
        value.candidate_id for value in values if value.candidate_id is not None
    ]
    certification_config_digests = {
        canonical_digest(CertificationConfig(repeat_count=value.repeat_count))
        for value in values
        if value.accepted is not None and value.repeat_count
    }
    errors: list[str] = []
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("certification evidence contains duplicate candidate_id values")
    if candidate_ids != sorted(candidate_ids):
        errors.append("certification evidence records must be ordered by candidate_id")
    if evidence and certification_config_digests != {
        task_pool.certification_config_digest
    }:
        errors.append(
            "certification evidence repeat_count does not match certification_config_digest"
        )
    errors.extend(_certification_context_errors(evidence))
    return tuple(errors)


def _accepted_certification_coverage_errors(
    tasks: Sequence[TaskRecord],
    checks: Sequence[CheckRecord],
    values: Sequence[_CertificationEvidenceValues],
) -> tuple[str, ...]:
    accepted_pairs = [
        (value.task_digest, value.check_digest)
        for value in values
        if value.accepted is True
        and value.task_digest is not None
        and value.check_digest is not None
    ]
    tasks_by_id = {task.task_id: task for task in tasks}
    expected_accepted_pairs = {
        (canonical_digest(tasks_by_id[check.task_id]), canonical_digest(check))
        for check in checks
        if check.task_id in tasks_by_id
    }
    errors: list[str] = []
    if len(accepted_pairs) != len(set(accepted_pairs)):
        errors.append(
            "certification evidence contains duplicate accepted Task/Check records"
        )
    if set(accepted_pairs) != expected_accepted_pairs:
        errors.append(
            "certification evidence does not exactly cover accepted Task/Check records"
        )
    return tuple(errors)


def _rejected_certification_coverage_errors(
    task_pool: TaskPoolRecord,
    values: Sequence[_CertificationEvidenceValues],
) -> tuple[str, ...]:
    rejected = tuple(value for value in values if value.accepted is False)
    rejected_ids = [
        value.candidate_id for value in rejected if value.candidate_id is not None
    ]
    errors: list[str] = []
    if (
        len(rejected_ids) != len(set(rejected_ids))
        or tuple(rejected_ids) != task_pool.rejected_candidate_ids
        or len(task_pool.rejected_candidate_ids)
        != len(set(task_pool.rejected_candidate_ids))
    ):
        errors.append(
            "certification evidence does not exactly cover rejected candidates"
        )
    rejection_reason_counts: dict[str, int] = {}
    for value in rejected:
        for reason in value.rejection_reasons:
            rejection_reason_counts[reason] = rejection_reason_counts.get(reason, 0) + 1
    rejection_summary = {
        "rejected_count": len(rejected),
        "reasons": rejection_reason_counts,
    }
    if canonical_digest(rejection_summary) != task_pool.rejection_summary_digest:
        errors.append("rejection summary digest does not match certification evidence")
    return tuple(errors)


def _certification_context_errors(
    evidence: Sequence[object],
) -> tuple[str, ...]:
    errors: list[str] = []
    for field in ("workspace_config_digest", "runtime_config_digest"):
        values = {
            value
            for record in evidence
            if isinstance(record, MappingABC)
            and isinstance((value := record.get(field)), str)
            and value
        }
        if len(values) > 1:
            errors.append(f"certification evidence contains multiple {field} values")
    return tuple(errors)


def _certification_evidence_values(
    record: object,
    index: int,
) -> tuple[_CertificationEvidenceValues | None, tuple[str, ...]]:
    label = f"certification evidence record {index}"
    validated_record, record_errors = _validated_certification_evidence_record(
        record,
        label,
    )
    if validated_record is None:
        return None, record_errors
    record = validated_record
    errors = list(record_errors)

    candidate_id = _certification_evidence_string(
        record,
        "candidate_id",
        label,
        errors,
    )
    accepted_value = record["accepted"]
    if not isinstance(accepted_value, bool):
        errors.append(f"{label} accepted must be boolean")
        return (
            _CertificationEvidenceValues(
                candidate_id,
                None,
                (),
                0,
                None,
                None,
                (),
                (),
            ),
            tuple(errors),
        )

    rejection_reasons = _certification_rejection_reasons(record, label, errors)
    repeat_count = _certification_repeat_count(record, label, errors)
    _certification_evidence_string(
        record,
        "reference_patch_digest",
        label,
        errors,
    )
    task_digest = _certification_evidence_string(
        record,
        "task_digest",
        label,
        errors,
    )
    check_digest = _certification_evidence_string(
        record,
        "check_digest",
        label,
        errors,
    )
    _append_certification_context_digest_errors(record, label, errors)
    base_outcomes = _evidence_outcomes(
        record["base_check"],
        f"{label} base_check",
        errors,
    )
    reference_outcomes = _evidence_outcomes(
        record["reference_patch_check"],
        f"{label} reference_patch_check",
        errors,
    )
    return (
        _CertificationEvidenceValues(
            candidate_id=candidate_id,
            accepted=accepted_value,
            rejection_reasons=rejection_reasons,
            repeat_count=repeat_count,
            task_digest=task_digest,
            check_digest=check_digest,
            base_outcomes=base_outcomes,
            reference_outcomes=reference_outcomes,
        ),
        tuple(errors),
    )


def _validated_certification_evidence_record(
    record: object,
    label: str,
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    if not isinstance(record, MappingABC):
        return None, (f"{label} must be an object",)
    missing = tuple(
        field for field in _CERTIFICATION_EVIDENCE_FIELDS if field not in record
    )
    if missing:
        return None, (f"{label} is missing: {', '.join(missing)}",)
    unknown = tuple(sorted(set(record) - set(_CERTIFICATION_EVIDENCE_FIELDS)))
    if unknown:
        return record, (f"{label} has unknown keys: {', '.join(unknown)}",)
    return record, ()


def _certification_evidence_string(
    record: Mapping[str, Any],
    field: str,
    label: str,
    errors: list[str],
) -> str | None:
    value = record[field]
    if isinstance(value, str) and value:
        return value
    errors.append(f"{label} {field} must be a non-empty string")
    return None


def _certification_rejection_reasons(
    record: Mapping[str, Any],
    label: str,
    errors: list[str],
) -> tuple[str, ...]:
    value = record["rejection_reasons"]
    if (
        not isinstance(value, SequenceABC)
        or isinstance(value, str)
        or any(not isinstance(reason, str) or not reason for reason in value)
    ):
        errors.append(
            f"{label} rejection_reasons must be a sequence of non-empty strings"
        )
        return ()
    return tuple(value)


def _certification_repeat_count(
    record: Mapping[str, Any],
    label: str,
    errors: list[str],
) -> int:
    value = record["repeat_count"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        errors.append(f"{label} repeat_count must be a positive integer")
        return 0
    return value


def _append_certification_context_digest_errors(
    record: Mapping[str, Any],
    label: str,
    errors: list[str],
) -> None:
    for field in (
        "workspace_config_digest",
        "runtime_config_digest",
        "check_execution_binding_digest",
        "verification_adapter_digest",
    ):
        _certification_evidence_string(record, field, label, errors)
    if record["verification_adapter_digest"] != VERIFICATION_ADAPTER_DIGEST:
        errors.append(f"{label} verification_adapter_digest is not supported")


def _certification_evidence_semantic_errors(
    values: _CertificationEvidenceValues,
) -> tuple[str, ...]:
    if values.accepted:
        errors: list[str] = []
        if values.rejection_reasons:
            errors.append(
                "accepted certification evidence must not have rejection reasons"
            )
        if len(values.base_outcomes) != values.repeat_count:
            errors.append("accepted certification base checks must match repeat_count")
        elif any(outcome != "fail" for outcome in values.base_outcomes):
            errors.append("accepted certification base checks must fail")
        if len(values.reference_outcomes) != values.repeat_count:
            errors.append(
                "accepted certification reference patch checks must match repeat_count"
            )
        elif any(outcome != "pass" for outcome in values.reference_outcomes):
            errors.append("accepted certification reference patch checks must pass")
        return tuple(errors)
    if values.accepted is False and not values.rejection_reasons:
        return ("rejected certification evidence must include rejection reasons",)
    return ()


def _source_event_errors(
    task_pool: TaskPoolRecord,
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    evidence: tuple[Mapping[str, Any], ...],
    source_events: tuple[SourceEventRecord, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not source_events:
        errors.append("source event records must not be empty")
        return tuple(errors)
    errors.extend(_source_event_collection_errors(source_events))
    errors.extend(_source_window_errors(task_pool, source_events))
    observed_through, timestamp_errors = _source_event_observation_boundary(task_pool)
    errors.extend(timestamp_errors)
    evidence_by_candidate = {
        str(record.get("candidate_id")): record
        for record in evidence
        if isinstance(record, MappingABC)
        and isinstance(record.get("candidate_id"), str)
    }
    tasks_by_id = {task.task_id: task for task in tasks}
    checks_by_id = {check.check_id: check for check in checks}
    represented_candidates: set[str] = set()
    accepted_pairs: set[tuple[str, str]] = set()
    rejected_candidate_ids: set[str] = set()

    for index, event in enumerate(source_events):
        errors.extend(
            _source_event_record_errors(
                task_pool,
                event,
                index,
                observed_through,
            )
        )
        if event.candidate_id is None:
            continue
        represented_candidates.add(event.candidate_id)
        evidence_record = evidence_by_candidate.get(event.candidate_id)
        if evidence_record is None:
            errors.append(
                f"source event {event.source_event_id} references missing certification evidence"
            )
            continue
        evidence_accepted = evidence_record.get("accepted")
        evidence_reasons_value = evidence_record.get("rejection_reasons", ())
        evidence_reasons = (
            tuple(evidence_reasons_value)
            if isinstance(evidence_reasons_value, SequenceABC)
            and not isinstance(evidence_reasons_value, str)
            else ()
        )
        if event.disposition == "accepted":
            accepted_pair, accepted_errors = _accepted_source_event_errors(
                event,
                evidence_accepted,
                tasks_by_id,
                checks_by_id,
            )
            errors.extend(accepted_errors)
            if accepted_pair is not None:
                accepted_pairs.add(accepted_pair)
        elif event.disposition == "certification_rejected":
            rejected_candidate_ids.add(event.candidate_id)
            errors.extend(
                _rejected_source_event_errors(
                    event,
                    evidence_accepted,
                    evidence_reasons,
                )
            )

    errors.extend(
        _source_event_coverage_errors(
            task_pool,
            checks,
            evidence_by_candidate,
            represented_candidates,
            accepted_pairs,
            rejected_candidate_ids,
        )
    )
    return tuple(errors)


def _metadata_source_window(
    metadata: Mapping[str, object],
) -> tuple[str | None, str | None]:
    raw_start = metadata.get("source_window_start")
    raw_end = metadata.get("source_window_end")
    if raw_start is None and raw_end is None:
        return None, None
    if not isinstance(raw_start, str) or not isinstance(raw_end, str):
        raise ValueError("Task Pool source window requires string start and end")
    start = format_utc_timestamp(parse_utc_timestamp(raw_start))
    end = format_utc_timestamp(parse_utc_timestamp(raw_end))
    if parse_utc_timestamp(start) > parse_utc_timestamp(end):
        raise ValueError("Task Pool source window start must not be after end")
    return start, end


def _source_window_errors(
    task_pool: TaskPoolRecord,
    source_events: Sequence[SourceEventRecord],
) -> tuple[str, ...]:
    start_time, end_time, boundary_errors = _source_window_boundary(task_pool)
    if start_time is None or end_time is None:
        return boundary_errors
    return (
        *boundary_errors,
        *_source_event_window_errors(source_events, start_time, end_time),
    )


def _source_window_boundary(
    task_pool: TaskPoolRecord,
) -> tuple[datetime | None, datetime | None, tuple[str, ...]]:
    start = task_pool.source_window_start
    end = task_pool.source_window_end
    if start is None and end is None:
        return None, None, ()
    if not isinstance(start, str) or not isinstance(end, str):
        return None, None, ("Task Pool source window requires string start and end",)
    errors: list[str] = []
    try:
        start_time = parse_utc_timestamp(start)
        end_time = parse_utc_timestamp(end)
    except (TypeError, ValueError):
        return None, None, ("Task Pool source window timestamps are invalid",)
    if start != format_utc_timestamp(start_time) or end != format_utc_timestamp(
        end_time
    ):
        errors.append("Task Pool source window timestamps are not canonical UTC")
    if start_time > end_time:
        errors.append("Task Pool source window start is after end")
        return None, None, tuple(errors)
    try:
        created_at = parse_utc_timestamp(task_pool.created_at)
    except (TypeError, ValueError):
        created_at = None
    if created_at is not None and end_time > created_at:
        errors.append("Task Pool source window ends after created_at")
    return start_time, end_time, tuple(errors)


def _source_event_window_errors(
    source_events: Sequence[SourceEventRecord],
    start_time: datetime,
    end_time: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []
    for event in source_events:
        try:
            resolved_at = parse_utc_timestamp(event.source_resolved_at)
        except (TypeError, ValueError):
            continue
        outside = resolved_at < start_time or resolved_at > end_time
        marked_outside = "outside_source_time_range" in event.rejection_reasons
        if outside and event.disposition != "excluded":
            errors.append(f"{event.disposition} source event is outside source window")
        if outside and not marked_outside:
            errors.append(
                f"source event {event.source_event_id} outside source window lacks exclusion reason"
            )
        if not outside and marked_outside:
            errors.append(
                f"source event {event.source_event_id} inside source window has outside-range reason"
            )
    return tuple(errors)


def _source_event_collection_errors(
    source_events: Sequence[SourceEventRecord],
) -> tuple[str, ...]:
    event_ids = tuple(event.source_event_id for event in source_events)
    candidate_ids = tuple(
        event.candidate_id for event in source_events if event.candidate_id is not None
    )
    errors: list[str] = []
    if len(event_ids) != len(set(event_ids)):
        errors.append("source event records contain duplicate identities")
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("source event records contain duplicate candidate_id values")
    if event_ids != tuple(sorted(event_ids)):
        errors.append("source event records must be ordered by source_event_id")
    return tuple(errors)


def _source_event_observation_boundary(
    task_pool: TaskPoolRecord,
) -> tuple[Any | None, tuple[str, ...]]:
    try:
        return parse_utc_timestamp(task_pool.created_at), ()
    except ValueError:
        return None, ("Task Pool created_at is not a valid evidence timestamp",)


def _source_event_record_errors(
    task_pool: TaskPoolRecord,
    event: SourceEventRecord,
    index: int,
    observed_through: Any | None,
) -> tuple[str, ...]:
    validation = validate_source_event(event)
    errors = [f"source event record {index}: {error}" for error in validation.errors]
    if event.repository_id != task_pool.repository_id:
        errors.append(
            f"source event {event.source_event_id} repository_id does not match Task Pool"
        )
    if observed_through is None:
        return tuple(errors)
    for field_name in (
        "source_resolved_at",
        "task_material_available_at",
        "check_material_available_at",
        "label_mature_at",
    ):
        timestamp = getattr(event, field_name)
        if timestamp is None:
            continue
        try:
            after_observation = parse_utc_timestamp(timestamp) > observed_through
        except ValueError:
            continue
        if after_observation:
            errors.append(
                f"source event {event.source_event_id} {field_name} is after Task Pool created_at"
            )
    return tuple(errors)


def _accepted_source_event_errors(
    event: SourceEventRecord,
    evidence_accepted: object,
    tasks_by_id: Mapping[str, TaskRecord],
    checks_by_id: Mapping[str, CheckRecord],
) -> tuple[tuple[str, str] | None, tuple[str, ...]]:
    errors: list[str] = []
    if evidence_accepted is not True:
        errors.append("accepted source event has non-accepted certification evidence")
    if event.task_id is None or event.check_id is None:
        return None, tuple(errors)
    task = tasks_by_id.get(event.task_id)
    check = checks_by_id.get(event.check_id)
    if task is None or check is None or check.task_id != event.task_id:
        errors.append("accepted source event does not bind a frozen Task/Check pair")
        return None, tuple(errors)
    accepted_pair = (event.task_id, event.check_id)
    if (
        task.repository_id != event.repository_id
        or task.source_family != event.source_family
        or task.source_ref != event.source_ref
        or task.source_resolved_at != event.source_resolved_at
        or task.task_material_available_at != event.task_material_available_at
        or task.dependency_cluster_id != event.dependency_cluster_id
        or task.sampling_stratum != event.sampling_stratum
        or check.check_material_available_at != event.check_material_available_at
    ):
        errors.append("accepted source event does not match frozen Task/Check material")
    return accepted_pair, tuple(errors)


def _rejected_source_event_errors(
    event: SourceEventRecord,
    evidence_accepted: object,
    evidence_reasons: tuple[Any, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    if evidence_accepted is not False:
        errors.append("rejected source event has accepted certification evidence")
    if event.rejection_reasons != evidence_reasons:
        errors.append(
            "source event rejection reasons do not match certification evidence"
        )
    return tuple(errors)


def _source_event_coverage_errors(
    task_pool: TaskPoolRecord,
    checks: Sequence[CheckRecord],
    evidence_by_candidate: Mapping[str, Mapping[str, Any]],
    represented_candidates: set[str],
    accepted_pairs: set[tuple[str, str]],
    rejected_candidate_ids: set[str],
) -> tuple[str, ...]:
    errors: list[str] = []
    if represented_candidates != set(evidence_by_candidate):
        errors.append(
            "source event records must exactly cover certification candidates"
        )
    expected_pairs = {(check.task_id, check.check_id) for check in checks}
    if accepted_pairs != expected_pairs:
        errors.append(
            "source event records must exactly cover accepted Task/Check pairs"
        )
    if rejected_candidate_ids != set(task_pool.rejected_candidate_ids):
        errors.append("source event records must exactly cover rejected candidates")
    return tuple(errors)


def _evidence_outcomes(
    value: object,
    label: str,
    errors: list[str],
) -> tuple[str, ...]:
    if not isinstance(value, SequenceABC) or isinstance(value, str):
        errors.append(f"{label} must be a sequence")
        return ()
    outcomes: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, MappingABC):
            errors.append(f"{label} attempt {index} must be an object")
            continue
        expected_fields = {
            "outcome",
            "failure_label",
            "timed_out",
            "duration_seconds",
            "evidence_excerpt",
        }
        missing = tuple(sorted(expected_fields - set(item)))
        unknown = tuple(sorted(set(item) - expected_fields))
        if missing:
            errors.append(f"{label} attempt {index} is missing: {', '.join(missing)}")
            continue
        if unknown:
            errors.append(
                f"{label} attempt {index} has unknown keys: {', '.join(unknown)}"
            )
        outcome = item.get("outcome")
        if outcome not in {"pass", "fail", "invalid"}:
            errors.append(f"{label} attempt {index} outcome is not normalized")
            continue
        errors.extend(
            _evidence_outcome_state_errors(
                item,
                outcome,
                f"{label} attempt {index}",
            )
        )
        duration = item["duration_seconds"]
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int | float)
            or not math.isfinite(float(duration))
            or duration < 0
        ):
            errors.append(
                f"{label} attempt {index} duration_seconds must be finite and nonnegative"
            )
        if not isinstance(item["evidence_excerpt"], str):
            errors.append(f"{label} attempt {index} evidence_excerpt must be a string")
        outcomes.append(outcome)
    return tuple(outcomes)


def _evidence_outcome_state_errors(
    item: Mapping[str, Any],
    outcome: str,
    label: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    failure_label = item["failure_label"]
    if outcome == "pass" and failure_label is not None:
        errors.append(f"{label} passing attempts must not have a failure_label")
    elif outcome != "pass" and (
        not isinstance(failure_label, str) or not failure_label
    ):
        errors.append(
            f"{label} non-passing attempts must have a non-empty failure_label"
        )
    timed_out = item["timed_out"]
    if not isinstance(timed_out, bool):
        errors.append(f"{label} timed_out must be boolean")
    elif timed_out and outcome != "invalid":
        errors.append(f"{label} timed_out attempts must have invalid outcome")
    return tuple(errors)


def summarize_task_pool(task_pool: TaskPoolRecord) -> Mapping[str, object]:
    return {
        "task_pool_id": task_pool.task_pool_id,
        "repository_id": task_pool.repository_id,
        "task_count": len(task_pool.task_ids),
        "check_count": len(task_pool.check_ids),
        "rejected_count": len(task_pool.rejected_candidate_ids),
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "certification_evidence_ref": task_pool.certification_evidence_ref,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
        "source_event_records_ref": task_pool.source_event_records_ref,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "source_window_start": task_pool.source_window_start,
        "source_window_end": task_pool.source_window_end,
        "created_at": task_pool.created_at,
    }


def _artifact_ref_path(ref: str, artifact_root: Path) -> Path:
    if not ref:
        raise ValueError("Task Pool artifact ref must not be empty")
    normalized = ref[5:] if ref.startswith("path:") else ref
    path = Path(normalized)
    if path.is_absolute():
        return path
    root = artifact_root.resolve()
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Task Pool artifact ref escapes artifact_root")
    return resolved


def _task_pool_bundle_relative_dir(task_pool: TaskPoolRecord) -> Path:
    refs = {
        "tasks.jsonl": task_pool.task_records_ref,
        "checks.jsonl": task_pool.check_records_ref,
        "certification-evidence.jsonl": task_pool.certification_evidence_ref,
        "source-events.jsonl": task_pool.source_event_records_ref,
    }
    parents: set[Path] = set()
    for expected_name, ref in refs.items():
        normalized = ref[5:] if ref.startswith("path:") else ref
        path = Path(normalized)
        if path.is_absolute() or path.name != expected_name:
            raise ValueError(
                "published Task Pool refs must be relative bundle member paths"
            )
        parents.add(path.parent)
    if len(parents) != 1:
        raise ValueError("published Task Pool refs must share one bundle directory")
    relative_dir = next(iter(parents))
    if relative_dir == Path("."):
        raise ValueError("published Task Pool refs must use a bundle directory")
    return relative_dir


def _require_identical_published_bundle(
    expected: TaskPoolBundle,
    artifact_root: Path,
    target: Path,
) -> None:
    manifests = tuple(load_jsonl_records(target / "task-pool.jsonl", TaskPoolRecord))
    if len(manifests) != 1 or manifests[0] != expected.task_pool:
        raise ValueError(
            "immutable Task Pool bundle target contains different manifest"
        )
    existing = load_validated_task_pool_bundle(manifests[0], artifact_root)
    if (
        existing.tasks != expected.tasks
        or existing.checks != expected.checks
        or existing.certification_evidence != expected.certification_evidence
        or existing.source_events != expected.source_events
    ):
        raise ValueError("immutable Task Pool bundle target contains different members")


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _load_certification_evidence_records(
    path: Path,
) -> tuple[Mapping[str, Any], ...]:
    values = load_jsonl_records(path, dict)
    if any(not isinstance(value, MappingABC) for value in values):
        raise ValueError("certification evidence must contain objects")
    return tuple(values)


def _require_certification_result(value: object) -> CertificationResult:
    if not isinstance(value, CertificationResult):
        raise ValueError(
            "certification_results must contain CertificationResult values"
        )
    if not isinstance(value.accepted, bool):
        raise ValueError("certification result accepted must be a boolean")
    return value


def _certification_results_by_candidate(
    batch: CandidateBatch,
    certification_results: Sequence[CertificationResult],
) -> dict[str, CertificationResult]:
    results_by_candidate: dict[str, CertificationResult] = {}
    for value in certification_results:
        result = _require_certification_result(value)
        if result.candidate_id in results_by_candidate:
            raise ValueError(
                f"duplicate certification result for {result.candidate_id}"
            )
        results_by_candidate[result.candidate_id] = result
    expected_candidate_ids = {candidate.candidate_id for candidate in batch.candidates}
    if set(results_by_candidate) != expected_candidate_ids:
        raise ValueError(
            "certification results must exactly cover generated candidates"
        )
    return results_by_candidate


def _source_event_from_certification(
    candidate: TaskCandidate,
    result: CertificationResult,
) -> SourceEventRecord:
    if result.accepted and (result.task is None or result.check is None):
        raise ValueError("accepted certification result is missing Task or Check")
    if not result.accepted and (result.task is not None or result.check is not None):
        raise ValueError("rejected certification result must not expose Task or Check")
    return record_with_digest(
        SourceEventRecord(
            source_event_id=make_source_event_id(
                candidate.repository_id,
                candidate.source_family,
                candidate.source_ref,
            ),
            repository_id=candidate.repository_id,
            source_family=candidate.source_family,
            source_ref=candidate.source_ref,
            source_resolved_at=candidate.source_resolved_at,
            task_material_available_at=candidate.task_material_available_at,
            check_material_available_at=candidate.check_material_available_at,
            label_mature_at=_label_mature_at(
                candidate.task_material_available_at,
                candidate.check_material_available_at,
            ),
            candidate_id=candidate.candidate_id,
            task_id=result.task.task_id if result.task is not None else None,
            check_id=result.check.check_id if result.check is not None else None,
            disposition="accepted" if result.accepted else "certification_rejected",
            rejection_stage=None if result.accepted else "certification",
            rejection_reasons=result.rejection_reasons,
            dependency_cluster_id=candidate.dependency_cluster_id,
            sampling_stratum=candidate.sampling_stratum,
            source_event_digest="",
        )
    )


def _validated_source_event_records(
    records: Sequence[SourceEventRecord],
) -> tuple[SourceEventRecord, ...]:
    ordered = tuple(sorted(records, key=lambda record: record.source_event_id))
    source_event_ids = tuple(record.source_event_id for record in ordered)
    if len(source_event_ids) != len(set(source_event_ids)):
        raise ValueError("source events contain duplicate source identities")
    for record in ordered:
        validation = validate_source_event(record)
        if not validation.ok:
            raise ValueError(
                f"source event {record.source_event_id} is invalid: "
                + "; ".join(validation.errors)
            )
    return ordered


def _candidate_batch(
    candidates: Sequence[TaskCandidate],
    excluded_source_events: Sequence[SourceEventRecord],
) -> CandidateBatch:
    candidates_tuple = tuple(candidates)
    excluded_tuple = tuple(excluded_source_events)
    candidate_ids = tuple(candidate.candidate_id for candidate in candidates_tuple)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate batch contains duplicate candidate IDs")
    candidate_event_ids = tuple(
        make_source_event_id(
            candidate.repository_id,
            candidate.source_family,
            candidate.source_ref,
        )
        for candidate in candidates_tuple
    )
    excluded_event_ids = tuple(event.source_event_id for event in excluded_tuple)
    all_event_ids = (*candidate_event_ids, *excluded_event_ids)
    if len(all_event_ids) != len(set(all_event_ids)):
        raise ValueError("candidate batch contains duplicate source event identities")
    for event in excluded_tuple:
        validation = validate_source_event(event)
        if not validation.ok or event.disposition != "excluded":
            raise ValueError(
                "candidate batch contains an invalid excluded source event"
            )
    return CandidateBatch(candidates_tuple, excluded_tuple)


def _excluded_source_event(
    data: Mapping[str, Any],
    reason: str,
) -> SourceEventRecord:
    repository_id = _required_str(data, "repository_id")
    source_family = _required_str(data, "source_family")
    source_ref = _required_str(data, "source_ref")
    source_resolved_at = _required_str(data, "source_resolved_at")
    task_material_available_at = _optional_str(
        data,
        "task_material_available_at",
    )
    check_material_available_at = _optional_str(
        data,
        "check_material_available_at",
    )
    record = SourceEventRecord(
        source_event_id=make_source_event_id(
            repository_id,
            source_family,
            source_ref,
        ),
        repository_id=repository_id,
        source_family=source_family,
        source_ref=source_ref,
        source_resolved_at=source_resolved_at,
        task_material_available_at=task_material_available_at,
        check_material_available_at=check_material_available_at,
        label_mature_at=(
            _label_mature_at(
                task_material_available_at,
                check_material_available_at,
            )
            if task_material_available_at is not None
            and check_material_available_at is not None
            else None
        ),
        candidate_id=None,
        task_id=None,
        check_id=None,
        disposition="excluded",
        rejection_stage="candidate_filter",
        rejection_reasons=(reason,),
        dependency_cluster_id=_string_or_empty(data, "dependency_cluster_id"),
        sampling_stratum=_string_or_empty(data, "sampling_stratum"),
        source_event_digest="",
    )
    record = record_with_digest(record)
    validation = validate_source_event(record)
    if not validation.ok:
        raise ValueError(
            "excluded source event is invalid: " + "; ".join(validation.errors)
        )
    return record


def _label_mature_at(
    task_material_available_at: str,
    check_material_available_at: str,
) -> str:
    return format_utc_timestamp(
        max(
            parse_utc_timestamp(task_material_available_at),
            parse_utc_timestamp(check_material_available_at),
        )
    )


def _load_candidate_payloads(source_path: Path) -> list[Mapping[str, Any]]:
    text = source_path.read_text(encoding="utf-8")
    if source_path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("candidates"), list):
        return data["candidates"]
    raise ValueError(
        "import source must be a JSON list, JSON object with candidates, or JSONL"
    )


def _candidate_from_mapping(data: Mapping[str, Any]) -> TaskCandidate:
    required = [
        "repository_id",
        "base_commit",
        "source_family",
        "source_ref",
        "source_resolved_at",
        "task_material_available_at",
        "check_material_available_at",
        "task_text",
        "check_manifest_digest",
        "hidden_check_bundle_digest",
        "oracle_source",
        "check_type",
    ]
    missing = [key for key in required if data.get(key) is None or data.get(key) == ""]
    if missing:
        raise ValueError(f"candidate is missing required fields: {', '.join(missing)}")
    repository_id = _required_str(data, "repository_id")
    base_commit = _required_str(data, "base_commit")
    source_family = _required_str(data, "source_family")
    source_ref = _required_str(data, "source_ref")
    source_resolved_at = _required_str(data, "source_resolved_at")
    task_material_available_at = _required_str(data, "task_material_available_at")
    check_material_available_at = _required_str(data, "check_material_available_at")
    task_text = _required_str(data, "task_text")
    check_manifest_digest = _required_str(data, "check_manifest_digest")
    hidden_check_bundle_digest = _required_str(data, "hidden_check_bundle_digest")
    oracle_source = _required_str(data, "oracle_source")
    check_type = _required_str(data, "check_type")
    source_identity = {
        "repository_id": repository_id,
        "base_commit": base_commit,
        "source_family": source_family,
        "source_ref": source_ref,
        "source_resolved_at": source_resolved_at,
    }
    candidate_id = _optional_str(data, "candidate_id")
    return TaskCandidate(
        candidate_id=candidate_id or f"candidate_{canonical_digest(source_identity)}",
        repository_id=repository_id,
        base_commit=base_commit,
        source_family=source_family,
        source_ref=source_ref,
        source_resolved_at=source_resolved_at,
        task_material_available_at=task_material_available_at,
        check_material_available_at=check_material_available_at,
        task_text=task_text,
        solver_material_refs=_string_tuple(data, "solver_material_refs"),
        dependency_cluster_id=_string_or_empty(data, "dependency_cluster_id"),
        sampling_stratum=_string_or_empty(data, "sampling_stratum"),
        check_manifest_digest=check_manifest_digest,
        hidden_check_bundle_digest=hidden_check_bundle_digest,
        resource_limits=_mapping_copy(data, "resource_limits"),
        oracle_source=oracle_source,
        check_type=check_type,
    )


def _run_task_check(
    task: TaskRecord,
    check: CheckRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    reference_patch: CapturedDiff | None,
    run_context: WorkspaceRunContext,
    *,
    validate_material_refs: bool = False,
) -> CheckOutcome:
    try:
        workspace = create_verifier_workspace(task, workspace_config, run_context)
    except (OSError, RuntimeError, ValueError) as exc:
        failure_label = (
            "missing_repository_source"
            if "repository source is not bound" in str(exc).lower()
            else "verifier_workspace_error"
        )
        return CheckOutcome("invalid", failure_label, None, False, 0.0, "")

    try:
        if validate_material_refs:
            try:
                validate_solver_material_refs(workspace, task)
            except ValueError:
                outcome = CheckOutcome(
                    "invalid", "invalid_solver_material", None, False, 0.0, ""
                )
            else:
                outcome = verify_agent_diff(
                    workspace, check, runtime_config, run_context
                )
        elif reference_patch is not None:
            replay = apply_diff(workspace, reference_patch)
            if replay.replay_status != "applied":
                outcome = CheckOutcome(
                    "invalid",
                    replay.failure_label or "diff_replay_failed",
                    None,
                    False,
                    0.0,
                    "",
                )
            else:
                outcome = verify_agent_diff(
                    workspace, check, runtime_config, run_context
                )
        else:
            outcome = verify_agent_diff(workspace, check, runtime_config, run_context)
    except (OSError, RuntimeError, ValueError):
        outcome = CheckOutcome("invalid", "verification_error", None, False, 0.0, "")

    try:
        cleanup_workspace(workspace)
    except RuntimeError:
        return CheckOutcome("invalid", "workspace_cleanup_failed", None, False, 0.0, "")
    return outcome


def _unexpected_check_outcome(label: str, expected: str, outcome: CheckOutcome) -> str:
    detail = f" ({outcome.failure_label})" if outcome.failure_label else ""
    return f"{label} must {expected}; observed {outcome.outcome}{detail}"


def _source_identity(candidate: TaskCandidate) -> Mapping[str, str]:
    return {
        "source_family": candidate.source_family,
        "source_ref": candidate.source_ref,
        "source_resolved_at": candidate.source_resolved_at,
    }


def _task_from_candidate(candidate: TaskCandidate, check: CheckRecord) -> TaskRecord:
    task_text = candidate.task_text.rstrip()
    return TaskRecord(
        task_id=check.task_id,
        repository_id=candidate.repository_id,
        base_commit=candidate.base_commit,
        source_family=candidate.source_family,
        source_ref=candidate.source_ref,
        source_resolved_at=candidate.source_resolved_at,
        task_material_available_at=candidate.task_material_available_at,
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, candidate.solver_material_refs
        ),
        solver_material_refs=candidate.solver_material_refs,
        check_ids=(check.check_id,),
        dependency_cluster_id=candidate.dependency_cluster_id,
        sampling_stratum=candidate.sampling_stratum,
    )


def _validate_accepted_task_check_linkage(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
) -> None:
    if len({task.task_id for task in accepted_tasks}) != len(accepted_tasks):
        raise ValueError("accepted tasks contain duplicate task_id values")
    if len({check.check_id for check in accepted_checks}) != len(accepted_checks):
        raise ValueError("accepted checks contain duplicate check_id values")
    tasks_by_id = {task.task_id: task for task in accepted_tasks}
    check_ids = {check.check_id for check in accepted_checks}
    for task in accepted_tasks:
        missing = [check_id for check_id in task.check_ids if check_id not in check_ids]
        if missing:
            raise ValueError(f"task {task.task_id} references missing checks")
    for check in accepted_checks:
        task = tasks_by_id.get(check.task_id)
        if task is None:
            raise ValueError(f"check {check.check_id} references missing task")
        if check.check_id not in task.check_ids:
            raise ValueError(
                f"check {check.check_id} is not listed by task {task.task_id}"
            )


def _validate_accepted_records(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    repository_id: str,
) -> None:
    for task in accepted_tasks:
        validation = validate_task(task)
        if not validation.ok:
            raise ValueError(
                f"task {task.task_id} failed validation: {'; '.join(validation.errors)}"
            )
        if task.repository_id != repository_id:
            raise ValueError(
                f"task {task.task_id} repository_id does not match task pool repository_id"
            )
    for check in accepted_checks:
        validation = validate_check(check)
        if not validation.ok:
            raise ValueError(
                f"check {check.check_id} failed validation: {'; '.join(validation.errors)}"
            )


def _validated_certification_results(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    certification_results: Sequence[CertificationResult],
) -> tuple[CertificationResult, ...]:
    results = tuple(certification_results)
    results_by_pair = _indexed_certification_results(results)
    expected_pairs = tuple((check.task_id, check.check_id) for check in accepted_checks)
    _validate_certification_result_coverage(results_by_pair, expected_pairs)
    _validate_frozen_certification_bindings(
        results_by_pair,
        expected_pairs,
        {task.task_id: task for task in accepted_tasks},
        {check.check_id: check for check in accepted_checks},
    )
    return tuple(sorted(results, key=lambda result: result.candidate_id))


def _indexed_certification_results(
    results: Sequence[CertificationResult],
) -> dict[tuple[str, str], CertificationResult]:
    results_by_pair: dict[tuple[str, str], CertificationResult] = {}
    candidate_ids: set[str] = set()
    for value in results:
        result = _require_certification_result(value)
        if result.candidate_id in candidate_ids:
            raise ValueError("certification_results contain duplicate candidate IDs")
        candidate_ids.add(result.candidate_id)
        if result.evidence_digest != canonical_digest(result.evidence):
            raise ValueError(
                "certification evidence digest does not match structured evidence"
            )
        if not result.accepted:
            if result.task is not None or result.check is not None:
                raise ValueError(
                    "rejected certification results must not contain Task/Check records"
                )
            if not result.rejection_reasons:
                raise ValueError("rejected certification results must include reasons")
            continue
        if result.task is None or result.check is None:
            raise ValueError(
                "accepted certification result is missing Task/Check records"
            )
        pair = (result.task.task_id, result.check.check_id)
        if pair in results_by_pair:
            raise ValueError(
                "certification_results contain duplicate Task/Check evidence"
            )
        results_by_pair[pair] = result
    return results_by_pair


def _validate_certification_result_coverage(
    results_by_pair: Mapping[tuple[str, str], CertificationResult],
    expected_pairs: Sequence[tuple[str, str]],
) -> None:
    if set(results_by_pair) != set(expected_pairs):
        raise ValueError(
            "accepted certification results must exactly cover frozen Task/Check pairs"
        )


def _validate_frozen_certification_bindings(
    results_by_pair: Mapping[tuple[str, str], CertificationResult],
    expected_pairs: Sequence[tuple[str, str]],
    tasks_by_id: Mapping[str, TaskRecord],
    checks_by_id: Mapping[str, CheckRecord],
) -> None:
    for task_id, check_id in expected_pairs:
        result = results_by_pair.get((task_id, check_id))
        task = tasks_by_id.get(task_id)
        check = checks_by_id.get(check_id)
        if result is None or task is None or check is None:
            raise ValueError(
                "accepted certification evidence is missing for an accepted Task/Check pair"
            )
        if canonical_digest(result.task) != canonical_digest(task):
            raise ValueError(
                "accepted certification evidence task digest does not match frozen task"
            )
        if canonical_digest(result.check) != canonical_digest(check):
            raise ValueError(
                "accepted certification evidence check digest does not match frozen check"
            )
        if result.evidence.get("task_digest") != canonical_digest(task):
            raise ValueError(
                "accepted certification evidence payload task digest does not match frozen task"
            )
        if result.evidence.get("check_digest") != canonical_digest(check):
            raise ValueError(
                "accepted certification evidence payload check digest does not match frozen check"
            )


def _rejection_summary(results: Sequence[CertificationResult]) -> Mapping[str, Any]:
    reasons: dict[str, int] = {}
    for result in results:
        if result.accepted:
            continue
        for reason in result.rejection_reasons:
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "rejected_count": sum(1 for result in results if not result.accepted),
        "reasons": reasons,
    }


def _required_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or value == "":
        raise ValueError(f"{key} is required")
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _string_or_empty(data: Mapping[str, Any], key: str) -> str:
    return _optional_str(data, key) or ""


def _string_tuple(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, ())
    if isinstance(value, str) or not isinstance(value, SequenceABC):
        raise ValueError(f"{key} must be a sequence of strings")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a sequence of strings")
    return tuple(value)


def _mapping_copy(data: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, MappingABC):
        raise ValueError(f"{key} must be a mapping")
    if any(not isinstance(item_key, str) for item_key in value):
        raise ValueError(f"{key} keys must be strings")
    return dict(value)


def _require_metadata(
    metadata: Mapping[str, object], keys: Sequence[str]
) -> dict[str, str]:
    missing = [
        key
        for key in keys
        if key not in metadata or metadata[key] is None or metadata[key] == ""
    ]
    if missing:
        raise ValueError(f"metadata is missing required fields: {', '.join(missing)}")
    nonstrings = [key for key in keys if not isinstance(metadata[key], str)]
    if nonstrings:
        raise ValueError(f"metadata fields must be strings: {', '.join(nonstrings)}")
    return {key: value for key in keys if isinstance((value := metadata[key]), str)}
