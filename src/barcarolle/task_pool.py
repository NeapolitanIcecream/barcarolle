"""Task Pool generation, certification, freezing, and summaries."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Mapping, Sequence, cast
import hashlib
import json
import math
import os
import shutil

from barcarolle.records import (
    CheckRecord,
    GenerationProvenanceManifest,
    ObservedFrameEventRecord,
    PreparedCandidateMaterialRecord,
    PreparedCandidatePackageManifest,
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
    hidden_material_digest,
    summarize_evidence,
)
from barcarolle.workspace import (
    CapturedDiff,
    RepositorySourceNotBoundError,
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
GENERATION_PROVENANCE_SCHEMA_VERSION = "barcarolle_generation_provenance_v1"
PREPARED_CANDIDATE_PACKAGE_SCHEMA_VERSION = "barcarolle_prepared_candidate_package_v1"
_GENERATOR_BEHAVIOR_FIELDS = {
    "generator_family",
    "adapter_version",
    "implementation_digest",
    "behavior_config",
}
_SOURCE_PROTOCOL_FIELDS = {
    "source_kind",
    "target_definition",
    "query_semantics",
    "sampling_policy",
    "deduplication_policy",
}
_OBSERVED_FRAME_FIELDS = {
    "frame_id",
    "source_protocol_digest",
    "source_revision",
    "window_start",
    "window_end",
    "event_inventory_ref",
    "event_inventory_digest",
    "observation_authority",
    "observation_receipt_digest",
    "known_blind_spots",
    "coverage_mode",
}
_GENERATION_RUN_FIELDS = {
    "run_id",
    "producer_id",
    "authority_kind",
    "authority_digest",
    "started_at",
    "finished_at",
    "input_snapshot_digest",
}
_GENERATION_OUTPUT_FIELDS = {
    "prepared_candidate_records_digest",
    "adapter_evidence_ref",
    "adapter_evidence_digest",
    "task_records_digest",
    "check_records_digest",
    "source_event_records_digest",
    "certification_evidence_digest",
}


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
class PreparedCandidatePackage:
    manifest: PreparedCandidatePackageManifest
    batch: CandidateBatch
    materials: tuple[PreparedCandidateMaterialRecord, ...]
    observed_frame_events: tuple[ObservedFrameEventRecord, ...]
    adapter_evidence: Mapping[str, Any] | None
    package_root: Path


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
    generation_provenance: GenerationProvenanceManifest | None = None
    observed_frame_events: tuple[ObservedFrameEventRecord, ...] = ()
    adapter_evidence: Mapping[str, Any] | None = None

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


def candidate_batch(
    candidates: Sequence[TaskCandidate],
    excluded_source_events: Sequence[SourceEventRecord] = (),
) -> CandidateBatch:
    return _candidate_batch(candidates, excluded_source_events)


def load_prepared_candidate_package(
    manifest_path: Path,
) -> PreparedCandidatePackage:
    """Load one strict, language-neutral Generator handoff without executing it."""
    manifest_file = manifest_path.resolve()
    if manifest_file.name != "prepared-candidate-package.jsonl":
        raise ValueError(
            "prepared candidate manifest must be named prepared-candidate-package.jsonl"
        )
    try:
        manifests = tuple(
            load_jsonl_records(manifest_file, PreparedCandidatePackageManifest)
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError(
            "prepared candidate manifest is unavailable or invalid"
        ) from exc
    if len(manifests) != 1:
        raise ValueError("prepared candidate manifest must contain exactly one record")
    manifest = manifests[0]
    root = manifest_file.parent
    candidates = _load_prepared_records(
        root,
        manifest.candidate_records_ref,
        "candidates.jsonl",
        TaskCandidate,
        "candidate records",
    )
    excluded = _load_prepared_records(
        root,
        manifest.excluded_source_event_records_ref,
        "excluded-source-events.jsonl",
        SourceEventRecord,
        "excluded source event records",
    )
    materials = _load_prepared_records(
        root,
        manifest.material_records_ref,
        "materials.jsonl",
        PreparedCandidateMaterialRecord,
        "candidate material records",
    )
    frame_events: tuple[ObservedFrameEventRecord, ...] = ()
    if manifest.observed_frame is not None:
        frame_ref = manifest.observed_frame.get("event_inventory_ref")
        if not isinstance(frame_ref, str) or not frame_ref:
            raise ValueError("prepared observed frame event_inventory_ref is invalid")
        frame_events = _load_prepared_records(
            root,
            frame_ref,
            "observed-frame-events.jsonl",
            ObservedFrameEventRecord,
            "observed frame events",
        )
    adapter_evidence = None
    if manifest.adapter_evidence_ref is not None:
        adapter_path = _prepared_package_ref_path(
            root,
            manifest.adapter_evidence_ref,
            "adapter-evidence.jsonl",
        )
        try:
            adapter_records = _load_mapping_records(adapter_path)
        except (OSError, TypeError, ValueError) as exc:
            raise ValueError("adapter evidence is unavailable or invalid") from exc
        if len(adapter_records) != 1:
            raise ValueError("adapter evidence must contain exactly one object")
        adapter_evidence = adapter_records[0]
    batch = _candidate_batch(candidates, excluded)
    package = PreparedCandidatePackage(
        manifest=manifest,
        batch=batch,
        materials=materials,
        observed_frame_events=frame_events,
        adapter_evidence=adapter_evidence,
        package_root=root,
    )
    errors = _prepared_candidate_package_errors(package)
    if errors:
        raise ValueError("prepared candidate package is invalid: " + "; ".join(errors))
    return package


def prepared_candidate_build_inputs(
    package: PreparedCandidatePackage,
) -> tuple[
    Mapping[str, CapturedDiff],
    Mapping[str, tuple[str, ...]],
    Mapping[str, Path],
    Mapping[str, Mapping[str, object]],
]:
    """Resolve already-validated package material for Task Pool certification."""
    errors = _prepared_candidate_package_errors(package)
    if errors:
        raise ValueError("prepared candidate package is invalid: " + "; ".join(errors))
    reference_patches: dict[str, CapturedDiff] = {}
    check_commands: dict[str, tuple[str, ...]] = {}
    hidden_material_paths: dict[str, Path] = {}
    check_manifests: dict[str, Mapping[str, object]] = {}
    for material in package.materials:
        patch_path = _prepared_material_ref_path(
            package.package_root,
            material.reference_patch_ref,
        )
        patch_text = patch_path.read_text(encoding="utf-8")
        reference_patches[material.candidate_id] = CapturedDiff(
            diff_text=patch_text,
            diff_digest=material.reference_patch_digest,
        )
        check_commands[material.candidate_id] = material.check_command
        hidden_material_paths[material.candidate_id] = _prepared_material_ref_path(
            package.package_root,
            material.hidden_material_ref,
        )
        manifest_path = _prepared_material_ref_path(
            package.package_root,
            material.check_manifest_ref,
        )
        check_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(check_manifest, MappingABC):
            raise ValueError("prepared check manifest must be an object")
        check_manifests[material.candidate_id] = dict(check_manifest)
    return (
        reference_patches,
        check_commands,
        hidden_material_paths,
        check_manifests,
    )


def bind_task_pool_generation_provenance(
    task_pool: TaskPoolRecord,
    bundle_dir: Path,
    package: PreparedCandidatePackage,
) -> tuple[
    TaskPoolRecord,
    GenerationProvenanceManifest | None,
    tuple[ObservedFrameEventRecord, ...],
    Mapping[str, Any] | None,
]:
    errors = _prepared_candidate_package_errors(package)
    if errors:
        raise ValueError("prepared candidate package is invalid: " + "; ".join(errors))
    prepared = package.manifest
    if prepared.generator_behavior is None:
        return task_pool, None, (), None
    if prepared.generator_behavior_digest is None or prepared.run is None:
        raise ValueError("prepared generation evidence is incomplete")
    frame = None
    frame_digest = None
    frame_events: tuple[ObservedFrameEventRecord, ...] = ()
    if prepared.observed_frame is not None:
        frame = {
            **prepared.observed_frame,
            "event_inventory_ref": (
                bundle_dir / "observed-frame-events.jsonl"
            ).as_posix(),
        }
        frame_digest = canonical_digest(frame)
        frame_events = package.observed_frame_events
    adapter_ref = (
        (bundle_dir / "adapter-evidence.jsonl").as_posix()
        if package.adapter_evidence is not None
        else None
    )
    adapter_digest = (
        canonical_digest(package.adapter_evidence)
        if package.adapter_evidence is not None
        else None
    )
    outputs = {
        "prepared_candidate_records_digest": prepared.candidate_records_digest,
        "adapter_evidence_ref": adapter_ref,
        "adapter_evidence_digest": adapter_digest,
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
    }
    provenance = record_with_digest(
        GenerationProvenanceManifest(
            schema_version=GENERATION_PROVENANCE_SCHEMA_VERSION,
            generator_behavior=prepared.generator_behavior,
            generator_behavior_digest=prepared.generator_behavior_digest,
            source_protocol=prepared.source_protocol,
            source_protocol_digest=prepared.source_protocol_digest,
            observed_frame=frame,
            observed_frame_digest=frame_digest,
            run=prepared.run,
            run_digest=cast(str, prepared.run_digest),
            outputs=outputs,
            outputs_digest=canonical_digest(outputs),
            manifest_digest="",
        )
    )
    bound_task_pool = bind_task_pool_generation_manifest(
        task_pool,
        (bundle_dir / "generation-provenance.jsonl").as_posix(),
        provenance,
    )
    return (
        bound_task_pool,
        provenance,
        frame_events,
        package.adapter_evidence,
    )


def bind_task_pool_generation_manifest(
    task_pool: TaskPoolRecord,
    provenance_ref: str,
    provenance: GenerationProvenanceManifest,
) -> TaskPoolRecord:
    if not isinstance(provenance_ref, str) or not provenance_ref:
        raise ValueError("generation provenance ref must be a nonempty string")
    bound = replace(
        task_pool,
        task_pool_id="",
        generation_provenance_ref=provenance_ref,
        generation_provenance_digest=provenance.manifest_digest,
        generator_config_digest=provenance.generator_behavior_digest,
        source_protocol_digest=provenance.source_protocol_digest,
        task_pool_digest="",
    )
    bound = replace(bound, task_pool_id=_automatic_task_pool_id(bound))
    return record_with_digest(bound)


def _load_prepared_records(
    root: Path,
    ref: str,
    expected_name: str,
    record_type: type,
    label: str,
) -> tuple[Any, ...]:
    path = _prepared_package_ref_path(root, ref, expected_name)
    try:
        return tuple(load_jsonl_records(path, record_type))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} are unavailable or invalid") from exc


def _prepared_package_ref_path(
    root: Path,
    ref: str,
    expected_name: str,
) -> Path:
    if not isinstance(ref, str) or not ref:
        raise ValueError(f"prepared package {expected_name} ref is invalid")
    path = Path(ref)
    if path.is_absolute() or path.name != expected_name:
        raise ValueError(
            f"prepared package ref must be relative and named {expected_name}"
        )
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("prepared package ref escapes package root")
    return resolved


def _prepared_material_ref_path(root: Path, ref: str) -> Path:
    if not isinstance(ref, str) or not ref:
        raise ValueError("prepared material ref is invalid")
    path = Path(ref)
    if path.is_absolute():
        raise ValueError("prepared material ref must be relative")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("prepared material ref escapes package root")
    return resolved


def _prepared_candidate_package_errors(
    package: PreparedCandidatePackage,
) -> tuple[str, ...]:
    manifest = package.manifest
    errors: list[str] = []
    if manifest.schema_version != PREPARED_CANDIDATE_PACKAGE_SCHEMA_VERSION:
        errors.append("prepared candidate schema_version is not supported")
    try:
        expected_manifest_digest = canonical_digest(manifest, exclude_self_digest=True)
    except (OverflowError, TypeError, ValueError):
        errors.append("prepared candidate manifest is not strict canonical JSON")
    else:
        if manifest.manifest_digest != expected_manifest_digest:
            errors.append("prepared candidate manifest digest does not match")
    candidates = package.batch.candidates
    excluded = package.batch.excluded_source_events
    if manifest.repository_id == "":
        errors.append("prepared candidate repository_id is required")
    if any(
        candidate.repository_id != manifest.repository_id for candidate in candidates
    ):
        errors.append("prepared candidates must use the manifest repository")
    if canonical_digest(candidates) != manifest.candidate_records_digest:
        errors.append("prepared candidate records digest does not match")
    if canonical_digest(excluded) != manifest.excluded_source_event_records_digest:
        errors.append("prepared excluded source event records digest does not match")
    if canonical_digest(package.materials) != manifest.material_records_digest:
        errors.append("prepared candidate material records digest does not match")
    errors.extend(_prepared_candidate_record_errors(candidates))
    errors.extend(
        _prepared_material_errors(
            package,
            candidates,
        )
    )
    errors.extend(_prepared_generation_evidence_errors(package))
    return tuple(errors)


def _prepared_candidate_record_errors(
    candidates: Sequence[TaskCandidate],
) -> tuple[str, ...]:
    errors: list[str] = []
    for candidate in candidates:
        if not (
            isinstance(candidate.base_commit, str)
            and len(candidate.base_commit) in {40, 64}
            and all(
                character in "0123456789abcdef" for character in candidate.base_commit
            )
        ):
            errors.append(
                f"prepared candidate {candidate.candidate_id} base_commit must be a full Git object ID"
            )
        for field_name in (
            "source_resolved_at",
            "task_material_available_at",
            "check_material_available_at",
        ):
            value = getattr(candidate, field_name)
            try:
                instant = parse_utc_timestamp(value)
            except (TypeError, ValueError):
                errors.append(
                    f"prepared candidate {candidate.candidate_id} {field_name} is invalid"
                )
                continue
            if value != format_utc_timestamp(instant):
                errors.append(
                    f"prepared candidate {candidate.candidate_id} {field_name} is not canonical UTC"
                )
        if any(not ref for ref in candidate.solver_material_refs):
            errors.append(
                f"prepared candidate {candidate.candidate_id} solver material refs must be nonempty"
            )
    return tuple(errors)


def _prepared_material_errors(
    package: PreparedCandidatePackage,
    candidates: Sequence[TaskCandidate],
) -> tuple[str, ...]:
    errors: list[str] = []
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    material_ids = tuple(material.candidate_id for material in package.materials)
    if material_ids != tuple(sorted(material_ids)):
        errors.append("prepared candidate materials must be ordered by candidate_id")
    if len(material_ids) != len(set(material_ids)):
        errors.append("prepared candidate materials contain duplicate candidate IDs")
    if set(material_ids) != set(candidate_by_id):
        errors.append("prepared candidate materials must exactly cover candidates")
    for material in package.materials:
        try:
            expected_digest = canonical_digest(material, exclude_self_digest=True)
        except (OverflowError, TypeError, ValueError):
            errors.append(
                f"prepared candidate material {material.candidate_id} is not canonical"
            )
            continue
        if material.material_digest != expected_digest:
            errors.append(
                f"prepared candidate material {material.candidate_id} digest does not match"
            )
        candidate = candidate_by_id.get(material.candidate_id)
        if candidate is None:
            continue
        if not material.check_command or any(
            not isinstance(item, str) or not item for item in material.check_command
        ):
            errors.append(
                f"prepared candidate material {material.candidate_id} check command is invalid"
            )
        try:
            patch_path = _prepared_material_ref_path(
                package.package_root,
                material.reference_patch_ref,
            )
            patch_text = patch_path.read_text(encoding="utf-8")
        except (OSError, TypeError, ValueError) as exc:
            errors.append(
                f"prepared candidate material {material.candidate_id} reference patch is unavailable: {exc}"
            )
        else:
            if hashlib.sha256(patch_text.encode("utf-8")).hexdigest() != (
                material.reference_patch_digest
            ):
                errors.append(
                    f"prepared candidate material {material.candidate_id} reference patch digest does not match"
                )
        try:
            manifest_path = _prepared_material_ref_path(
                package.package_root,
                material.check_manifest_ref,
            )
            check_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            errors.append(
                f"prepared candidate material {material.candidate_id} check manifest is unavailable: {exc}"
            )
        else:
            if not isinstance(check_manifest, MappingABC):
                errors.append(
                    f"prepared candidate material {material.candidate_id} check manifest must be an object"
                )
            elif canonical_digest(check_manifest) != material.check_manifest_digest:
                errors.append(
                    f"prepared candidate material {material.candidate_id} check manifest digest does not match"
                )
        if material.check_manifest_digest != candidate.check_manifest_digest:
            errors.append(
                f"prepared candidate material {material.candidate_id} check manifest does not match candidate"
            )
        try:
            hidden_path = _prepared_material_ref_path(
                package.package_root,
                material.hidden_material_ref,
            )
            observed_hidden_digest = hidden_material_digest(hidden_path)
        except (OSError, TypeError, ValueError) as exc:
            errors.append(
                f"prepared candidate material {material.candidate_id} hidden material is unavailable: {exc}"
            )
        else:
            if observed_hidden_digest != material.hidden_material_digest:
                errors.append(
                    f"prepared candidate material {material.candidate_id} hidden material digest does not match"
                )
        if material.hidden_material_digest != candidate.hidden_check_bundle_digest:
            errors.append(
                f"prepared candidate material {material.candidate_id} hidden material does not match candidate"
            )
    return tuple(errors)


def _prepared_generation_evidence_errors(
    package: PreparedCandidatePackage,
) -> tuple[str, ...]:
    manifest = package.manifest
    errors: list[str] = []
    if manifest.generator_behavior is None:
        if any(
            value is not None
            for value in (
                manifest.generator_behavior_digest,
                manifest.source_protocol,
                manifest.source_protocol_digest,
                manifest.observed_frame,
                manifest.observed_frame_digest,
                manifest.run,
                manifest.run_digest,
                manifest.adapter_evidence_ref,
                manifest.adapter_evidence_digest,
                package.adapter_evidence,
            )
        ):
            errors.append(
                "prepared generation evidence must be entirely absent without generator_behavior"
            )
        if package.observed_frame_events:
            errors.append("prepared observed frame events require generator_behavior")
        return tuple(errors)
    errors.extend(
        _generation_section_errors(
            "generator_behavior",
            manifest.generator_behavior,
            _GENERATOR_BEHAVIOR_FIELDS,
            manifest.generator_behavior_digest,
        )
    )
    errors.extend(_generator_behavior_errors(manifest.generator_behavior))
    if manifest.run is None:
        errors.append("prepared generation run is required")
    else:
        errors.extend(
            _generation_section_errors(
                "run",
                manifest.run,
                _GENERATION_RUN_FIELDS,
                manifest.run_digest,
            )
        )
        errors.extend(_generation_run_errors(manifest.run))
        if manifest.run.get("authority_kind") != "external_attested":
            errors.append(
                "prepared generation run must use external_attested authority"
            )
    errors.extend(
        _optional_generation_section_errors(
            "source_protocol",
            manifest.source_protocol,
            _SOURCE_PROTOCOL_FIELDS,
            manifest.source_protocol_digest,
        )
    )
    if manifest.source_protocol is not None:
        errors.extend(_source_protocol_errors(manifest.source_protocol))
    errors.extend(
        _optional_generation_section_errors(
            "observed_frame",
            manifest.observed_frame,
            _OBSERVED_FRAME_FIELDS,
            manifest.observed_frame_digest,
        )
    )
    if manifest.observed_frame is None:
        if package.observed_frame_events:
            errors.append("prepared observed frame events exist without observed_frame")
    else:
        if manifest.observed_frame.get("observation_authority") != "producer_attested":
            errors.append(
                "prepared observed frame must use producer_attested authority"
            )
        errors.extend(_prepared_observed_frame_errors(package))
    if package.adapter_evidence is None:
        if (
            manifest.adapter_evidence_ref is not None
            or manifest.adapter_evidence_digest is not None
        ):
            errors.append("prepared adapter evidence is absent but still referenced")
    else:
        if (
            not isinstance(manifest.adapter_evidence_ref, str)
            or not manifest.adapter_evidence_ref
        ):
            errors.append("prepared adapter_evidence_ref is required")
        if canonical_digest(package.adapter_evidence) != (
            manifest.adapter_evidence_digest
        ):
            errors.append("prepared adapter evidence digest does not match")
    return tuple(errors)


def _prepared_observed_frame_errors(
    package: PreparedCandidatePackage,
) -> tuple[str, ...]:
    frame = package.manifest.observed_frame
    if frame is None:
        return ()
    errors = list(
        _observed_frame_metadata_errors(
            frame,
            package.manifest.source_protocol_digest,
            "prepared observed_frame",
        )
    )
    if canonical_digest(package.observed_frame_events) != frame.get(
        "event_inventory_digest"
    ):
        errors.append("prepared observed frame inventory digest does not match")
    expected_ids = tuple(
        sorted(
            (
                *(
                    make_source_event_id(
                        candidate.repository_id,
                        candidate.source_family,
                        candidate.source_ref,
                    )
                    for candidate in package.batch.candidates
                ),
                *(
                    event.source_event_id
                    for event in package.batch.excluded_source_events
                ),
            )
        )
    )
    observed_ids = tuple(
        event.source_event_id for event in package.observed_frame_events
    )
    if observed_ids != tuple(sorted(observed_ids)) or len(observed_ids) != len(
        set(observed_ids)
    ):
        errors.append(
            "prepared observed frame events must have unique sorted identities"
        )
    if observed_ids != expected_ids:
        errors.append(
            "prepared observed frame must exactly cover candidates and excluded events"
        )
    run_finished_at = _generation_run_finished_at(package.manifest.run)
    for event in package.observed_frame_events:
        errors.extend(
            _observed_frame_event_errors_for_repository(
                package.manifest.repository_id,
                event,
                run_finished_at,
            )
        )
    return tuple(errors)


def _observed_frame_metadata_errors(
    frame: Mapping[str, object],
    source_protocol_digest: str | None,
    label: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    if source_protocol_digest is None:
        errors.append(f"{label} requires source_protocol evidence")
    if frame.get("source_protocol_digest") != source_protocol_digest:
        errors.append(f"{label} source_protocol_digest does not match manifest")
    if frame.get("coverage_mode") != "one_source_event_per_frame_unit_v1":
        errors.append(f"{label} coverage_mode is not supported")
    authority = frame.get("observation_authority")
    if authority not in {"source_authoritative", "producer_attested"}:
        errors.append(f"{label} observation_authority is not normalized")
    receipt = frame.get("observation_receipt_digest")
    if authority == "source_authoritative" and (
        not isinstance(receipt, str) or not receipt
    ):
        errors.append(f"source-authoritative {label} requires an observation receipt")
    elif receipt is not None and (not isinstance(receipt, str) or not receipt):
        errors.append(f"{label} observation_receipt_digest must be nonempty or null")
    for field_name in ("frame_id", "event_inventory_ref", "event_inventory_digest"):
        if not isinstance(frame.get(field_name), str) or not frame.get(field_name):
            errors.append(f"{label} {field_name} is required")
    source_revision = frame.get("source_revision")
    if source_revision is not None and (
        not isinstance(source_revision, str) or not source_revision
    ):
        errors.append(f"{label} source_revision must be nonempty or null")
    blind_spots = frame.get("known_blind_spots")
    if not isinstance(blind_spots, SequenceABC) or isinstance(blind_spots, str):
        errors.append(f"{label} known_blind_spots must be an array")
    elif any(not isinstance(item, str) or not item for item in blind_spots):
        errors.append(f"{label} known_blind_spots must contain nonempty strings")
    errors.extend(
        _ordered_generation_timestamps(
            frame,
            ("window_start", "window_end"),
            label,
        )
    )
    return tuple(errors)


def _observed_frame_event_errors_for_repository(
    repository_id: str,
    event: ObservedFrameEventRecord,
    run_finished_at: datetime | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if event.repository_id != repository_id:
        errors.append(
            f"observed frame event {event.source_event_id} repository does not match package"
        )
    expected_id = make_source_event_id(
        event.repository_id,
        event.source_family,
        event.source_ref,
    )
    if event.source_event_id != expected_id:
        errors.append(
            f"observed frame event {event.source_event_id} identity does not match source"
        )
    try:
        observed = parse_utc_timestamp(event.observed_at)
    except (TypeError, ValueError):
        errors.append(
            f"observed frame event {event.source_event_id} observed_at is invalid"
        )
    else:
        if event.observed_at != format_utc_timestamp(observed):
            errors.append(
                f"observed frame event {event.source_event_id} observed_at is not canonical UTC"
            )
        if run_finished_at is not None and observed > run_finished_at:
            errors.append(
                f"observed frame event {event.source_event_id} observed_at "
                "must not postdate generation run completion"
            )
    if event.frame_event_digest != canonical_digest(event, exclude_self_digest=True):
        errors.append(
            f"observed frame event {event.source_event_id} digest does not match"
        )
    return tuple(errors)


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
        generation_provenance_ref=_optional_str(metadata, "generation_provenance_ref"),
        generation_provenance_digest=_optional_str(
            metadata, "generation_provenance_digest"
        ),
        generator_config_digest=_optional_str(metadata, "generator_config_digest"),
        source_protocol_digest=_optional_str(metadata, "source_protocol_digest"),
        certification_config_digest=required_metadata["certification_config_digest"],
        created_at=required_metadata["created_at"],
        source_window_start=source_window_start,
        source_window_end=source_window_end,
    )
    if not record.task_pool_id:
        record = replace(record, task_pool_id=_automatic_task_pool_id(record))
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


def _automatic_task_pool_id(task_pool: TaskPoolRecord) -> str:
    unidentified = replace(
        task_pool,
        task_pool_id="",
        task_pool_digest="",
    )
    return f"task_pool_{canonical_digest(unidentified)}"


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
    generation_provenance: GenerationProvenanceManifest | None = None,
    observed_frame_events: Sequence[ObservedFrameEventRecord] = (),
    adapter_evidence: Mapping[str, Any] | None = None,
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
    errors.extend(
        _generation_provenance_errors(
            task_pool,
            generation_provenance,
            tuple(observed_frame_events),
            adapter_evidence,
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
    generation_provenance: GenerationProvenanceManifest | None = None,
    observed_frame_events: Sequence[ObservedFrameEventRecord] = (),
    adapter_evidence: Mapping[str, Any] | None = None,
) -> TaskPoolBundle:
    validation = validate_task_pool_artifacts(
        task_pool,
        tasks,
        checks,
        certification_evidence,
        source_events,
        generation_provenance,
        observed_frame_events,
        adapter_evidence,
    )
    if not validation.ok:
        raise ValueError("task pool bundle is invalid: " + "; ".join(validation.errors))
    return TaskPoolBundle(
        task_pool=task_pool,
        source_events=tuple(source_events),
        tasks=tuple(tasks),
        checks=tuple(checks),
        certification_evidence=tuple(
            cast(Mapping[str, Any], canonical_data(record))
            for record in certification_evidence
        ),
        generation_provenance=generation_provenance,
        observed_frame_events=tuple(observed_frame_events),
        adapter_evidence=(
            None
            if adapter_evidence is None
            else cast(Mapping[str, Any], canonical_data(adapter_evidence))
        ),
    )


def _generation_provenance_errors(
    task_pool: TaskPoolRecord,
    manifest: GenerationProvenanceManifest | None,
    frame_events: tuple[ObservedFrameEventRecord, ...],
    adapter_evidence: Mapping[str, Any] | None,
    source_events: tuple[SourceEventRecord, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    has_ref = task_pool.generation_provenance_ref is not None
    has_digest = task_pool.generation_provenance_digest is not None
    has_binding = has_ref and has_digest
    if has_ref != has_digest:
        errors.append(
            "generation provenance ref and digest must be both present or both absent"
        )
    if manifest is None:
        if has_binding:
            errors.append("generation provenance is missing from Task Pool bundle")
        if frame_events:
            errors.append("observed frame events require generation provenance")
        if adapter_evidence is not None:
            errors.append("adapter evidence requires generation provenance")
        return tuple(errors)
    if not has_binding:
        errors.append("generation provenance is not bound by TaskPoolRecord")
    elif task_pool.generation_provenance_ref is not None:
        errors.extend(
            _bundle_member_ref_errors(
                task_pool,
                task_pool.generation_provenance_ref,
                "generation-provenance.jsonl",
            )
        )
    if manifest.schema_version != GENERATION_PROVENANCE_SCHEMA_VERSION:
        errors.append("generation provenance schema_version is not supported")
    try:
        expected_manifest_digest = canonical_digest(manifest, exclude_self_digest=True)
    except (OverflowError, TypeError, ValueError):
        errors.append("generation provenance is not strict canonical JSON")
    else:
        if manifest.manifest_digest != expected_manifest_digest:
            errors.append(
                "generation provenance manifest_digest does not match canonical content"
            )
        if task_pool.generation_provenance_digest != manifest.manifest_digest:
            errors.append("generation provenance digest does not match TaskPoolRecord")
    errors.extend(
        _generation_section_errors(
            "generator_behavior",
            manifest.generator_behavior,
            _GENERATOR_BEHAVIOR_FIELDS,
            manifest.generator_behavior_digest,
        )
    )
    errors.extend(_generator_behavior_errors(manifest.generator_behavior))
    if task_pool.generator_config_digest != manifest.generator_behavior_digest:
        errors.append("generator behavior digest does not match TaskPoolRecord")
    errors.extend(
        _optional_generation_section_errors(
            "source_protocol",
            manifest.source_protocol,
            _SOURCE_PROTOCOL_FIELDS,
            manifest.source_protocol_digest,
        )
    )
    if task_pool.source_protocol_digest != manifest.source_protocol_digest:
        errors.append("source protocol digest does not match TaskPoolRecord")
    if manifest.source_protocol is not None:
        errors.extend(_source_protocol_errors(manifest.source_protocol))
    errors.extend(
        _optional_generation_section_errors(
            "observed_frame",
            manifest.observed_frame,
            _OBSERVED_FRAME_FIELDS,
            manifest.observed_frame_digest,
        )
    )
    errors.extend(
        _generation_section_errors(
            "run",
            manifest.run,
            _GENERATION_RUN_FIELDS,
            manifest.run_digest,
        )
    )
    errors.extend(_generation_run_errors(manifest.run))
    errors.extend(_generation_run_creation_errors(task_pool, manifest.run))
    errors.extend(
        _generation_section_errors(
            "outputs",
            manifest.outputs,
            _GENERATION_OUTPUT_FIELDS,
            manifest.outputs_digest,
        )
    )
    errors.extend(
        _generation_output_errors(
            task_pool,
            manifest.outputs,
            adapter_evidence,
        )
    )
    errors.extend(
        _observed_frame_errors(
            task_pool,
            manifest,
            frame_events,
            source_events,
        )
    )
    return tuple(errors)


def _generation_section_errors(
    label: str,
    section: object,
    expected_fields: set[str],
    section_digest: object,
) -> tuple[str, ...]:
    if not isinstance(section, MappingABC):
        return (f"generation provenance {label} must be an object",)
    errors = list(_exact_mapping_fields_errors(label, section, expected_fields))
    try:
        expected_digest = canonical_digest(section)
    except (OverflowError, TypeError, ValueError):
        errors.append(f"generation provenance {label} is not strict canonical JSON")
    else:
        if section_digest != expected_digest:
            errors.append(
                f"generation provenance {label} digest does not match content"
            )
    return tuple(errors)


def _optional_generation_section_errors(
    label: str,
    section: object,
    expected_fields: set[str],
    section_digest: object,
) -> tuple[str, ...]:
    if section is None:
        return (
            ()
            if section_digest is None
            else (f"generation provenance {label} digest must be null",)
        )
    if section_digest is None:
        return (
            f"generation provenance {label} digest is required when section exists",
            *_generation_section_errors(
                label,
                section,
                expected_fields,
                section_digest,
            ),
        )
    return _generation_section_errors(
        label,
        section,
        expected_fields,
        section_digest,
    )


def _exact_mapping_fields_errors(
    label: str,
    value: Mapping[str, Any],
    expected_fields: set[str],
) -> tuple[str, ...]:
    observed = set(value)
    missing = tuple(sorted(expected_fields - observed))
    unknown = tuple(sorted(observed - expected_fields))
    errors: list[str] = []
    if missing:
        errors.append(f"generation provenance {label} is missing: {', '.join(missing)}")
    if unknown:
        errors.append(
            f"generation provenance {label} has unknown keys: {', '.join(unknown)}"
        )
    return tuple(errors)


def _generator_behavior_errors(behavior: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in ("generator_family", "adapter_version", "implementation_digest"):
        if not isinstance(behavior.get(field_name), str) or not behavior.get(
            field_name
        ):
            errors.append(
                f"generation provenance generator_behavior {field_name} is required"
            )
    if not isinstance(behavior.get("behavior_config"), MappingABC):
        errors.append(
            "generation provenance generator_behavior behavior_config must be an object"
        )
    return tuple(errors)


def _source_protocol_errors(protocol: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in ("source_kind", "target_definition"):
        if not isinstance(protocol.get(field_name), str) or not protocol.get(
            field_name
        ):
            errors.append(
                f"generation provenance source_protocol {field_name} is required"
            )
    for field_name in (
        "query_semantics",
        "sampling_policy",
        "deduplication_policy",
    ):
        if not isinstance(protocol.get(field_name), MappingABC):
            errors.append(
                f"generation provenance source_protocol {field_name} must be an object"
            )
    return tuple(errors)


def _generation_run_errors(run: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in (
        "run_id",
        "producer_id",
        "authority_digest",
        "input_snapshot_digest",
    ):
        if not isinstance(run.get(field_name), str) or not run.get(field_name):
            errors.append(f"generation provenance run {field_name} is required")
    if run.get("authority_kind") not in {
        "barcarolle_managed",
        "external_attested",
    }:
        errors.append("generation provenance run authority_kind is not normalized")
    errors.extend(
        _ordered_generation_timestamps(
            run,
            ("started_at", "finished_at"),
            "generation provenance run",
        )
    )
    return tuple(errors)


def _generation_run_creation_errors(
    task_pool: TaskPoolRecord,
    run: Mapping[str, Any],
) -> tuple[str, ...]:
    finished_at_value = run.get("finished_at")
    if not isinstance(finished_at_value, str):
        return ()
    try:
        finished_at = parse_utc_timestamp(finished_at_value)
        created_at = parse_utc_timestamp(task_pool.created_at)
    except (TypeError, ValueError):
        return ()
    if finished_at > created_at:
        return (
            "generation provenance run finished_at must not postdate "
            "Task Pool creation",
        )
    return ()


def _generation_output_errors(
    task_pool: TaskPoolRecord,
    outputs: Mapping[str, Any],
    adapter_evidence: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in (
        "prepared_candidate_records_digest",
        "task_records_digest",
        "check_records_digest",
        "source_event_records_digest",
        "certification_evidence_digest",
    ):
        if not isinstance(outputs.get(field_name), str) or not outputs.get(field_name):
            errors.append(f"generation provenance outputs {field_name} is required")
    expected = {
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
    }
    for field_name, digest in expected.items():
        if outputs.get(field_name) != digest:
            errors.append(
                f"generation provenance outputs {field_name} does not match Task Pool"
            )
    adapter_ref = outputs.get("adapter_evidence_ref")
    adapter_digest = outputs.get("adapter_evidence_digest")
    if adapter_evidence is None:
        if adapter_ref is not None or adapter_digest is not None:
            errors.append(
                "generation provenance adapter evidence is absent but still referenced"
            )
    else:
        if not isinstance(adapter_ref, str) or not adapter_ref:
            errors.append("generation provenance adapter_evidence_ref is required")
        else:
            errors.extend(
                _bundle_member_ref_errors(
                    task_pool,
                    adapter_ref,
                    "adapter-evidence.jsonl",
                )
            )
        if adapter_digest != canonical_digest(adapter_evidence):
            errors.append(
                "generation provenance adapter evidence digest does not match content"
            )
    return tuple(errors)


def _observed_frame_errors(
    task_pool: TaskPoolRecord,
    manifest: GenerationProvenanceManifest,
    frame_events: tuple[ObservedFrameEventRecord, ...],
    source_events: tuple[SourceEventRecord, ...],
) -> tuple[str, ...]:
    frame = manifest.observed_frame
    if frame is None:
        return (
            ()
            if not frame_events
            else ("observed frame events exist without an observed_frame section",)
        )
    errors = list(
        _observed_frame_metadata_errors(
            frame,
            manifest.source_protocol_digest,
            "observed_frame",
        )
    )
    if (
        frame.get("window_start") != task_pool.source_window_start
        or frame.get("window_end") != task_pool.source_window_end
    ):
        errors.append("observed frame window does not match Task Pool source window")
    event_inventory_ref = frame.get("event_inventory_ref")
    if isinstance(event_inventory_ref, str) and event_inventory_ref:
        errors.extend(
            _bundle_member_ref_errors(
                task_pool,
                event_inventory_ref,
                "observed-frame-events.jsonl",
            )
        )
    if canonical_digest(frame_events) != frame.get("event_inventory_digest"):
        errors.append("observed frame event inventory digest does not match content")
    event_ids = tuple(event.source_event_id for event in frame_events)
    if event_ids != tuple(sorted(event_ids)) or len(event_ids) != len(set(event_ids)):
        errors.append("observed frame events must have unique sorted identities")
    source_event_ids = tuple(event.source_event_id for event in source_events)
    if event_ids != source_event_ids:
        errors.append(
            "observed frame inventory must exactly cover SourceEvent outcomes"
        )
    run_finished_at = _generation_run_finished_at(manifest.run)
    for event in frame_events:
        errors.extend(
            _observed_frame_event_errors(task_pool, event, run_finished_at)
        )
    return tuple(errors)


def _observed_frame_event_errors(
    task_pool: TaskPoolRecord,
    event: ObservedFrameEventRecord,
    run_finished_at: datetime | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    expected_id = make_source_event_id(
        event.repository_id,
        event.source_family,
        event.source_ref,
    )
    if event.source_event_id != expected_id:
        errors.append(
            f"observed frame event {event.source_event_id} identity does not match source"
        )
    if event.repository_id != task_pool.repository_id:
        errors.append(
            f"observed frame event {event.source_event_id} repository does not match Task Pool"
        )
    try:
        observed_at = parse_utc_timestamp(event.observed_at)
    except (TypeError, ValueError):
        errors.append(
            f"observed frame event {event.source_event_id} observed_at is invalid"
        )
    else:
        if event.observed_at != format_utc_timestamp(observed_at):
            errors.append(
                f"observed frame event {event.source_event_id} observed_at is not canonical UTC"
            )
        if run_finished_at is not None and observed_at > run_finished_at:
            errors.append(
                f"observed frame event {event.source_event_id} observed_at "
                "must not postdate generation run completion"
            )
        try:
            created_at = parse_utc_timestamp(task_pool.created_at)
        except (TypeError, ValueError):
            pass
        else:
            if observed_at > created_at:
                errors.append(
                    f"observed frame event {event.source_event_id} observed_at "
                    "must not postdate Task Pool creation"
                )
    try:
        expected_digest = canonical_digest(event, exclude_self_digest=True)
    except (OverflowError, TypeError, ValueError):
        errors.append(
            f"observed frame event {event.source_event_id} is not strict canonical JSON"
        )
    else:
        if event.frame_event_digest != expected_digest:
            errors.append(
                f"observed frame event {event.source_event_id} digest does not match"
            )
    return tuple(errors)


def _generation_run_finished_at(
    run: Mapping[str, Any] | None,
) -> datetime | None:
    if run is None:
        return None
    value = run.get("finished_at")
    if not isinstance(value, str):
        return None
    try:
        return parse_utc_timestamp(value)
    except ValueError:
        return None


def _ordered_generation_timestamps(
    value: Mapping[str, Any],
    field_names: tuple[str, str],
    label: str,
) -> tuple[str, ...]:
    parsed: list[datetime] = []
    errors: list[str] = []
    for field_name in field_names:
        timestamp = value.get(field_name)
        if not isinstance(timestamp, str) or not timestamp:
            errors.append(f"{label} {field_name} is required")
            continue
        try:
            instant = parse_utc_timestamp(timestamp)
        except (TypeError, ValueError):
            errors.append(f"{label} {field_name} is invalid")
            continue
        if timestamp != format_utc_timestamp(instant):
            errors.append(f"{label} {field_name} is not canonical UTC")
        parsed.append(instant)
    if len(parsed) == 2 and parsed[0] > parsed[1]:
        errors.append(f"{label} timestamps are out of order")
    return tuple(errors)


def _bundle_member_ref_errors(
    task_pool: TaskPoolRecord,
    ref: str,
    expected_name: str,
) -> tuple[str, ...]:
    normalized = ref[5:] if ref.startswith("path:") else ref
    candidate = Path(normalized)
    task_ref = task_pool.task_records_ref
    normalized_task_ref = task_ref[5:] if task_ref.startswith("path:") else task_ref
    task_path = Path(normalized_task_ref)
    task_parent = task_path.parent
    if (
        candidate.name != expected_name
        or candidate.is_absolute() != task_path.is_absolute()
        or candidate.parent != task_parent
    ):
        return (
            f"generation provenance {expected_name} ref must share the Task Pool bundle directory",
        )
    return ()


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
    generation_provenance = None
    observed_frame_events: tuple[ObservedFrameEventRecord, ...] = ()
    adapter_evidence = None
    if task_pool.generation_provenance_ref is not None:
        try:
            manifests = tuple(
                load_jsonl_records(
                    _artifact_ref_path(
                        task_pool.generation_provenance_ref,
                        artifact_root,
                    ),
                    GenerationProvenanceManifest,
                )
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            raise ValueError("generation provenance is unavailable or invalid") from exc
        if len(manifests) != 1:
            raise ValueError("generation provenance must contain exactly one manifest")
        generation_provenance = manifests[0]
        if generation_provenance.observed_frame is not None:
            frame_ref = generation_provenance.observed_frame.get("event_inventory_ref")
            if not isinstance(frame_ref, str) or not frame_ref:
                raise ValueError(
                    "observed frame event inventory ref is unavailable or invalid"
                )
            try:
                observed_frame_events = tuple(
                    load_jsonl_records(
                        _artifact_ref_path(frame_ref, artifact_root),
                        ObservedFrameEventRecord,
                    )
                )
            except (KeyError, OSError, TypeError, ValueError) as exc:
                raise ValueError(
                    "observed frame event inventory is unavailable or invalid"
                ) from exc
        adapter_ref = generation_provenance.outputs.get("adapter_evidence_ref")
        if adapter_ref is not None:
            if not isinstance(adapter_ref, str) or not adapter_ref:
                raise ValueError("adapter evidence ref is unavailable or invalid")
            try:
                adapter_records = _load_mapping_records(
                    _artifact_ref_path(adapter_ref, artifact_root)
                )
            except (OSError, TypeError, ValueError) as exc:
                raise ValueError("adapter evidence is unavailable or invalid") from exc
            if len(adapter_records) != 1:
                raise ValueError("adapter evidence must contain exactly one object")
            adapter_evidence = adapter_records[0]
    return validated_task_pool_bundle(
        task_pool,
        tasks,
        checks,
        evidence,
        source_events,
        generation_provenance,
        observed_frame_events,
        adapter_evidence,
    )


def open_task_pool_bundle(manifest_path: Path) -> TaskPoolBundle:
    """Open one published Task Pool bundle without modifying or republishing it."""
    manifest = manifest_path.resolve()
    if manifest.name != "task-pool.jsonl":
        raise ValueError("Task Pool manifest must be named task-pool.jsonl")
    try:
        records = tuple(load_jsonl_records(manifest, TaskPoolRecord))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("Task Pool manifest is unavailable or invalid") from exc
    if len(records) != 1:
        raise ValueError("Task Pool manifest must contain exactly one TaskPoolRecord")
    task_pool = records[0]
    relative_dir = _task_pool_bundle_relative_dir(task_pool)
    artifact_root = manifest.parent
    for _ in relative_dir.parts:
        artifact_root = artifact_root.parent
    if (artifact_root / relative_dir).resolve() != manifest.parent:
        raise ValueError("Task Pool manifest path does not match its member refs")
    return load_validated_task_pool_bundle(task_pool, artifact_root)


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
        bundle.generation_provenance,
        bundle.observed_frame_events,
        bundle.adapter_evidence,
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
        provenance_path = staging / "generation-provenance.jsonl"
        frame_events_path = staging / "observed-frame-events.jsonl"
        adapter_evidence_path = staging / "adapter-evidence.jsonl"
        write_jsonl_records(manifest_path, (bundle.task_pool,))
        write_jsonl_records(tasks_path, bundle.tasks)
        write_jsonl_records(checks_path, bundle.checks)
        write_jsonl_records(
            evidence_path,
            bundle.certification_evidence,
        )
        write_jsonl_records(source_events_path, bundle.source_events)
        optional_paths: list[Path] = []
        if bundle.generation_provenance is not None:
            write_jsonl_records(provenance_path, (bundle.generation_provenance,))
            optional_paths.append(provenance_path)
        has_observed_frame = (
            bundle.generation_provenance is not None
            and bundle.generation_provenance.observed_frame is not None
        )
        if has_observed_frame:
            write_jsonl_records(frame_events_path, bundle.observed_frame_events)
            optional_paths.append(frame_events_path)
        if bundle.adapter_evidence is not None:
            write_jsonl_records(adapter_evidence_path, (bundle.adapter_evidence,))
            optional_paths.append(adapter_evidence_path)
        for path in (
            manifest_path,
            tasks_path,
            checks_path,
            evidence_path,
            source_events_path,
            *optional_paths,
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
        staged_provenance = (
            tuple(
                load_jsonl_records(
                    provenance_path,
                    GenerationProvenanceManifest,
                )
            )[0]
            if bundle.generation_provenance is not None
            else None
        )
        staged_frame_events = (
            tuple(
                load_jsonl_records(
                    frame_events_path,
                    ObservedFrameEventRecord,
                )
            )
            if has_observed_frame
            else ()
        )
        staged_adapter_evidence = (
            _load_mapping_records(adapter_evidence_path)[0]
            if bundle.adapter_evidence is not None
            else None
        )
        validated_task_pool_bundle(
            bundle.task_pool,
            staged_tasks,
            staged_checks,
            staged_evidence,
            staged_source_events,
            staged_provenance,
            staged_frame_events,
            staged_adapter_evidence,
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
        "generation_provenance_ref": task_pool.generation_provenance_ref,
        "generation_provenance_digest": task_pool.generation_provenance_digest,
        "generator_config_digest": task_pool.generator_config_digest,
        "source_protocol_digest": task_pool.source_protocol_digest,
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
    if task_pool.generation_provenance_ref is not None:
        refs["generation-provenance.jsonl"] = task_pool.generation_provenance_ref
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
        or existing.generation_provenance != expected.generation_provenance
        or existing.observed_frame_events != expected.observed_frame_events
        or existing.adapter_evidence != expected.adapter_evidence
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
    return _load_mapping_records(path)


def _load_mapping_records(
    path: Path,
) -> tuple[Mapping[str, Any], ...]:
    values = load_jsonl_records(path, dict)
    if any(not isinstance(value, MappingABC) for value in values):
        raise ValueError("JSONL evidence must contain objects")
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
    required = (
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
    )
    allowed = set(required) | {
        "candidate_id",
        "solver_material_refs",
        "dependency_cluster_id",
        "sampling_stratum",
        "resource_limits",
    }
    unknown = tuple(sorted(set(data) - allowed))
    if unknown:
        raise ValueError("candidate has unknown fields: " + ", ".join(unknown))
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
    except RepositorySourceNotBoundError as exc:
        return CheckOutcome("invalid", exc.failure_label, None, False, 0.0, "")
    except (OSError, RuntimeError, ValueError):
        return CheckOutcome("invalid", "verifier_workspace_error", None, False, 0.0, "")

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
