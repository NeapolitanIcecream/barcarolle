"""Task Pool generation, certification, freezing, and summaries."""

from __future__ import annotations

from collections.abc import Sequence as SequenceABC
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
import json

from barcarolle.records import (
    CheckRecord,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    make_check_id,
    make_task_id,
    record_with_digest,
    validate_check,
    validate_task,
)


@dataclass(frozen=True)
class TimeRange:
    start: str
    end: str

    def contains(self, value: str) -> bool:
        instant = _parse_timestamp_utc(value)
        return _parse_timestamp_utc(self.start) <= instant <= _parse_timestamp_utc(self.end)


@dataclass(frozen=True)
class TaskSourceConfig:
    source_family: str
    source_events: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class ImportConfig:
    source_family: str = "user_import"


@dataclass(frozen=True)
class StatementConfig:
    material_keys: tuple[str, ...] = ("title", "body")
    separator: str = "\n\n"
    forbidden_markers: tuple[str, ...] = ("hidden", "oracle")


@dataclass(frozen=True)
class CheckConfig:
    check_type: str
    verifier_image_digest: str
    verifier_deps_digest: str
    resource_limits: Mapping[str, Any]
    oracle_source: str


@dataclass(frozen=True)
class CertificationConfig:
    hidden_ref_markers: tuple[str, ...] = ("hidden", "oracle")
    require_statement: bool = True
    required_evidence_keys: tuple[str, ...] = (
        "checkout_valid",
        "dependencies_restored",
        "check_executable",
        "oracle_stable",
        "solver_visible_boundary",
        "hidden_material_separated",
        "statement_clear",
    )


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
    solver_material_refs: tuple[str, ...]
    solver_material_digest: str
    cluster_id: str
    statement_material: Mapping[str, Any]
    check_manifest_digest: str
    hidden_check_bundle_digest: str
    verifier_image_digest: str
    verifier_deps_digest: str
    resource_limits: Mapping[str, Any]
    oracle_source: str
    check_type: str
    certification_evidence: Mapping[str, Any]


@dataclass(frozen=True)
class CertificationResult:
    candidate_id: str
    accepted: bool
    task: TaskRecord | None
    check: CheckRecord | None
    rejection_reasons: tuple[str, ...]
    evidence: Mapping[str, Any]
    evidence_digest: str


def generate_history_candidates(
    repository_url_or_path: str,
    time_range: TimeRange,
    task_source_config: TaskSourceConfig,
) -> Sequence[TaskCandidate]:
    candidates: list[TaskCandidate] = []
    for event in task_source_config.source_events:
        resolved_at = _required_str(event, "source_resolved_at")
        if not time_range.contains(resolved_at):
            continue
        event_with_defaults = {
            **event,
            "repository_id": event.get("repository_id", repository_url_or_path),
            "source_family": event.get("source_family", task_source_config.source_family),
        }
        candidates.append(_candidate_from_mapping(event_with_defaults))
    return tuple(candidates)


def import_task_pool(source_path: Path, import_config: ImportConfig) -> Sequence[TaskCandidate]:
    raw_records = _load_candidate_payloads(source_path)
    candidates = []
    for payload in raw_records:
        candidates.append(_candidate_from_mapping({"source_family": import_config.source_family, **payload}))
    return tuple(candidates)


def build_task_statement(candidate: TaskCandidate, statement_config: StatementConfig) -> str:
    parts = []
    for key in statement_config.material_keys:
        value = candidate.statement_material.get(key)
        if value is not None and str(value).strip():
            parts.append(str(value).strip())
    task_text = statement_config.separator.join(parts)
    lowered = task_text.lower()
    if any(marker.lower() in lowered for marker in statement_config.forbidden_markers):
        raise ValueError("solver-visible task statement contains hidden or oracle material")
    return task_text


def build_check_candidate(candidate: TaskCandidate, check_config: CheckConfig) -> CheckRecord:
    task_id = make_task_id(candidate.repository_id, candidate.base_commit, canonical_digest(_source_identity(candidate)))
    check_id = make_check_id(task_id, candidate.check_manifest_digest)
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type=check_config.check_type,
        check_manifest_digest=candidate.check_manifest_digest,
        hidden_check_bundle_digest=candidate.hidden_check_bundle_digest,
        verifier_image_digest=check_config.verifier_image_digest,
        verifier_deps_digest=check_config.verifier_deps_digest,
        resource_limits=check_config.resource_limits,
        oracle_source=check_config.oracle_source,
        check_material_available_at=candidate.check_material_available_at,
        certified_at=candidate.check_material_available_at,
    )


def certify_task_candidate(
    candidate: TaskCandidate,
    certification_config: CertificationConfig,
) -> CertificationResult:
    rejection_reasons: list[str] = []
    check = build_check_candidate(
        candidate,
        CheckConfig(
            check_type=candidate.check_type,
            verifier_image_digest=candidate.verifier_image_digest,
            verifier_deps_digest=candidate.verifier_deps_digest,
            resource_limits=candidate.resource_limits,
            oracle_source=candidate.oracle_source,
        ),
    )
    task = _task_from_candidate(candidate, check)

    try:
        statement = build_task_statement(
            candidate,
            StatementConfig(forbidden_markers=certification_config.hidden_ref_markers),
        )
    except ValueError as exc:
        statement = ""
        rejection_reasons.append(str(exc))
    if certification_config.require_statement and not statement:
        rejection_reasons.append("task statement is empty")
    lowered_refs = " ".join(candidate.solver_material_refs).lower()
    for marker in certification_config.hidden_ref_markers:
        if marker.lower() in lowered_refs:
            rejection_reasons.append("solver-visible material references hidden check material")
            break
    for evidence_key in certification_config.required_evidence_keys:
        if candidate.certification_evidence.get(evidence_key) is not True:
            rejection_reasons.append(f"certification evidence failed: {evidence_key}")

    task_validation = validate_task(task)
    check_validation = validate_check(check)
    rejection_reasons.extend(task_validation.errors)
    rejection_reasons.extend(check_validation.errors)

    accepted = not rejection_reasons
    evidence = {
        "candidate_id": candidate.candidate_id,
        "accepted": accepted,
        "rejection_reasons": tuple(rejection_reasons),
        "certification_evidence": dict(candidate.certification_evidence),
        "required_evidence_keys": certification_config.required_evidence_keys,
        "task_digest": canonical_digest(task),
        "check_digest": canonical_digest(check),
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


def freeze_task_pool(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    rejected: Sequence[CertificationResult],
    metadata: Mapping[str, object],
) -> TaskPoolRecord:
    _validate_accepted_task_check_linkage(accepted_tasks, accepted_checks)
    _require_metadata(
        metadata,
        (
            "repository_id",
            "accepted_certification_results",
            "task_records_ref",
            "check_records_ref",
            "source_event_inventory_digest",
            "generator_config_digest",
            "certification_config_digest",
            "created_at",
        ),
    )
    repository_id = str(metadata["repository_id"])
    _validate_accepted_records(accepted_tasks, accepted_checks, repository_id)
    task_records_digest = canonical_digest(tuple(accepted_tasks))
    check_records_digest = canonical_digest(tuple(accepted_checks))
    rejection_summary = _rejection_summary(rejected)
    accepted_evidence_digests = _accepted_certification_evidence_digests(
        accepted_tasks,
        accepted_checks,
        metadata["accepted_certification_results"],
    )
    certification_evidence = {
        "accepted_task_digests": tuple(canonical_digest(task) for task in accepted_tasks),
        "accepted_check_digests": tuple(canonical_digest(check) for check in accepted_checks),
        "accepted_certification_evidence_digests": accepted_evidence_digests,
        "rejected_evidence_digests": tuple(result.evidence_digest for result in rejected),
    }

    record = TaskPoolRecord(
        task_pool_id=str(metadata.get("task_pool_id", "")),
        task_pool_digest="",
        repository_id=repository_id,
        task_ids=tuple(task.task_id for task in accepted_tasks),
        check_ids=tuple(check.check_id for check in accepted_checks),
        task_records_ref=str(metadata["task_records_ref"]),
        task_records_digest=task_records_digest,
        check_records_ref=str(metadata["check_records_ref"]),
        check_records_digest=check_records_digest,
        rejected_candidate_ids=tuple(result.candidate_id for result in rejected if not result.accepted),
        rejection_summary_digest=canonical_digest(rejection_summary),
        certification_evidence_digest=canonical_digest(certification_evidence),
        source_event_inventory_digest=str(metadata["source_event_inventory_digest"]),
        generator_config_digest=str(metadata["generator_config_digest"]),
        certification_config_digest=str(metadata["certification_config_digest"]),
        created_at=str(metadata["created_at"]),
    )
    if not record.task_pool_id:
        record = TaskPoolRecord(**{**record.__dict__, "task_pool_id": f"task_pool_{canonical_digest(record)}"})
    return record_with_digest(record)


def summarize_task_pool(task_pool: TaskPoolRecord) -> Mapping[str, object]:
    return {
        "task_pool_id": task_pool.task_pool_id,
        "repository_id": task_pool.repository_id,
        "task_count": len(task_pool.task_ids),
        "check_count": len(task_pool.check_ids),
        "rejected_count": len(task_pool.rejected_candidate_ids),
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
        "source_event_inventory_digest": task_pool.source_event_inventory_digest,
        "created_at": task_pool.created_at,
    }


def _load_candidate_payloads(source_path: Path) -> list[Mapping[str, Any]]:
    text = source_path.read_text(encoding="utf-8")
    if source_path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("candidates"), list):
        return data["candidates"]
    raise ValueError("import source must be a JSON list, JSON object with candidates, or JSONL")


def _candidate_from_mapping(data: Mapping[str, Any]) -> TaskCandidate:
    required = [
        "repository_id",
        "base_commit",
        "source_family",
        "source_ref",
        "source_resolved_at",
        "task_material_available_at",
        "check_material_available_at",
        "solver_material_digest",
        "check_manifest_digest",
        "hidden_check_bundle_digest",
        "verifier_image_digest",
        "verifier_deps_digest",
        "oracle_source",
        "check_type",
    ]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"candidate is missing required fields: {', '.join(missing)}")
    source_identity = {
        "repository_id": data["repository_id"],
        "base_commit": data["base_commit"],
        "source_family": data["source_family"],
        "source_ref": data["source_ref"],
        "source_resolved_at": data["source_resolved_at"],
    }
    return TaskCandidate(
        candidate_id=str(data.get("candidate_id") or f"candidate_{canonical_digest(source_identity)}"),
        repository_id=str(data["repository_id"]),
        base_commit=str(data["base_commit"]),
        source_family=str(data["source_family"]),
        source_ref=str(data["source_ref"]),
        source_resolved_at=str(data["source_resolved_at"]),
        task_material_available_at=str(data["task_material_available_at"]),
        check_material_available_at=str(data["check_material_available_at"]),
        solver_material_refs=tuple(str(ref) for ref in data.get("solver_material_refs", ())),
        solver_material_digest=str(data["solver_material_digest"]),
        cluster_id=str(data.get("cluster_id", "")),
        statement_material=dict(data.get("statement_material", {})),
        check_manifest_digest=str(data["check_manifest_digest"]),
        hidden_check_bundle_digest=str(data["hidden_check_bundle_digest"]),
        verifier_image_digest=str(data["verifier_image_digest"]),
        verifier_deps_digest=str(data["verifier_deps_digest"]),
        resource_limits=dict(data.get("resource_limits", {})),
        oracle_source=str(data["oracle_source"]),
        check_type=str(data["check_type"]),
        certification_evidence=dict(data.get("certification_evidence", {})),
    )


def _source_identity(candidate: TaskCandidate) -> Mapping[str, str]:
    return {
        "source_family": candidate.source_family,
        "source_ref": candidate.source_ref,
        "source_resolved_at": candidate.source_resolved_at,
    }


def _task_from_candidate(candidate: TaskCandidate, check: CheckRecord) -> TaskRecord:
    return TaskRecord(
        task_id=check.task_id,
        repository_id=candidate.repository_id,
        base_commit=candidate.base_commit,
        source_family=candidate.source_family,
        source_ref=candidate.source_ref,
        source_resolved_at=candidate.source_resolved_at,
        task_material_available_at=candidate.task_material_available_at,
        certified_at=max(candidate.task_material_available_at, candidate.check_material_available_at),
        solver_material_digest=candidate.solver_material_digest,
        solver_material_refs=candidate.solver_material_refs,
        check_ids=(check.check_id,),
        cluster_id=candidate.cluster_id,
    )


def _validate_accepted_task_check_linkage(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
) -> None:
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
            raise ValueError(f"check {check.check_id} is not listed by task {task.task_id}")


def _validate_accepted_records(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    repository_id: str,
) -> None:
    for task in accepted_tasks:
        if task.repository_id != repository_id:
            raise ValueError(f"task {task.task_id} repository_id does not match task pool repository_id")
        validation = validate_task(task)
        if not validation.ok:
            raise ValueError(f"task {task.task_id} failed validation: {'; '.join(validation.errors)}")
    for check in accepted_checks:
        validation = validate_check(check)
        if not validation.ok:
            raise ValueError(f"check {check.check_id} failed validation: {'; '.join(validation.errors)}")


def _accepted_certification_evidence_digests(
    accepted_tasks: Sequence[TaskRecord],
    accepted_checks: Sequence[CheckRecord],
    accepted_results: object,
) -> tuple[str, ...]:
    if not isinstance(accepted_results, SequenceABC) or isinstance(accepted_results, str):
        raise ValueError("accepted_certification_results must be a sequence of CertificationResult")
    results = tuple(accepted_results)
    expected_pairs = tuple((check.task_id, check.check_id) for check in accepted_checks)
    if len(results) != len(expected_pairs):
        raise ValueError("accepted_certification_results must align with accepted Task/Check pairs")
    tasks_by_id = {task.task_id: task for task in accepted_tasks}
    results_by_pair: dict[tuple[str, str], CertificationResult] = {}
    for result in results:
        if not isinstance(result, CertificationResult):
            raise ValueError("accepted_certification_results must contain CertificationResult values")
        if not result.accepted or result.task is None or result.check is None:
            raise ValueError("accepted_certification_results must contain accepted results with Task/Check records")
        if result.evidence_digest != canonical_digest(result.evidence):
            raise ValueError("accepted certification evidence digest does not match structured evidence")
        pair = (result.task.task_id, result.check.check_id)
        if pair in results_by_pair:
            raise ValueError("accepted_certification_results contains duplicate Task/Check evidence")
        results_by_pair[pair] = result
    evidence_digests: list[str] = []
    for task_id, check_id in expected_pairs:
        result = results_by_pair.get((task_id, check_id))
        task = tasks_by_id.get(task_id)
        check = next((candidate for candidate in accepted_checks if candidate.check_id == check_id), None)
        if result is None or task is None or check is None:
            raise ValueError("accepted certification evidence is missing for an accepted Task/Check pair")
        if canonical_digest(result.task) != canonical_digest(task):
            raise ValueError("accepted certification evidence task digest does not match frozen task")
        if canonical_digest(result.check) != canonical_digest(check):
            raise ValueError("accepted certification evidence check digest does not match frozen check")
        if result.evidence.get("task_digest") != canonical_digest(task):
            raise ValueError("accepted certification evidence payload task digest does not match frozen task")
        if result.evidence.get("check_digest") != canonical_digest(check):
            raise ValueError("accepted certification evidence payload check digest does not match frozen check")
        evidence_digests.append(result.evidence_digest)
    return tuple(evidence_digests)


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
    return str(value)


def _parse_timestamp_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _require_metadata(metadata: Mapping[str, object], keys: Sequence[str]) -> None:
    missing = [key for key in keys if key not in metadata or metadata[key] is None or metadata[key] == ""]
    if missing:
        raise ValueError(f"metadata is missing required fields: {', '.join(missing)}")
