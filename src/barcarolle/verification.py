"""Verification checks and normalized outcomes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2, copytree
from time import monotonic
from typing import Any, Mapping, Sequence
import hashlib
import subprocess

from barcarolle.records import CheckRecord, RuntimeConfig, canonical_digest


@dataclass(frozen=True)
class WorkspaceRef:
    path: Path
    check_command: tuple[str, ...]
    check_id: str
    check_manifest_digest: str
    hidden_check_bundle_digest: str
    hidden_material_source: Path | None = None
    hidden_material_destination: Path | None = None
    prepared: bool = False


@dataclass(frozen=True)
class CheckOutcome:
    outcome: str
    failure_label: str | None
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    evidence_excerpt: str


@dataclass(frozen=True)
class CheckNormalizationConfig:
    pass_exit_codes: tuple[int, ...] = (0,)
    invalid_exit_codes: tuple[int, ...] = ()
    timeout_failure_label: str = "timeout"
    fail_failure_label: str = "check_failed"
    invalid_failure_label: str = "check_invalid"
    max_evidence_chars: int = 1200
    forbidden_evidence_markers: tuple[str, ...] = ("hidden", "oracle", "expected output")
    allow_verifier_text: bool = False


@dataclass(frozen=True)
class EvidenceSummary:
    outcome: str
    failure_label: str | None
    timed_out: bool
    duration_seconds: float
    evidence_excerpt: str


def prepare_verifier(check: CheckRecord, verifier_workspace: WorkspaceRef) -> WorkspaceRef:
    if not _workspace_matches_check(check, verifier_workspace):
        raise ValueError("verifier workspace identity does not match check")
    if verifier_workspace.hidden_material_source is None:
        raise ValueError("hidden_material_source is required to prepare verifier workspace")
    if _path_digest(verifier_workspace.hidden_material_source) != check.hidden_check_bundle_digest:
        raise ValueError("hidden material digest does not match check")
    if _check_command_digest(verifier_workspace.check_command) != check.check_manifest_digest:
        raise ValueError("check command digest does not match check manifest")
    if verifier_workspace.hidden_material_destination is None:
        raise ValueError("hidden_material_destination is required when hidden material is provided")
    destination = _resolve_under_workspace(verifier_workspace.path, verifier_workspace.hidden_material_destination)
    source = verifier_workspace.hidden_material_source
    if source.is_dir():
        copytree(source, destination, dirs_exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, destination)
    return WorkspaceRef(**{**verifier_workspace.__dict__, "prepared": True})


def verify_diff(
    check: CheckRecord,
    verifier_workspace: WorkspaceRef,
    runtime_config: RuntimeConfig,
) -> CheckOutcome:
    if not verifier_workspace.prepared:
        raise ValueError("verifier workspace must be prepared before verification")
    if not _workspace_matches_check(check, verifier_workspace):
        return CheckOutcome(
            outcome="invalid",
            failure_label="check_workspace_mismatch",
            exit_code=None,
            timed_out=False,
            duration_seconds=0.0,
            evidence_excerpt="",
        )
    if _check_command_digest(verifier_workspace.check_command) != check.check_manifest_digest:
        return CheckOutcome(
            outcome="invalid",
            failure_label="check_command_mismatch",
            exit_code=None,
            timed_out=False,
            duration_seconds=0.0,
            evidence_excerpt="[verifier output omitted]",
        )
    if not verifier_workspace.check_command:
        return CheckOutcome(
            outcome="invalid",
            failure_label="missing_check_command",
            exit_code=None,
            timed_out=False,
            duration_seconds=0.0,
            evidence_excerpt="",
        )
    timeout = _verification_timeout(check, runtime_config)
    start = monotonic()
    try:
        completed = subprocess.run(
            verifier_workspace.check_command,
            cwd=verifier_workspace.path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        duration = monotonic() - start
        return normalize_outcome(
            {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timed_out": False,
                "duration_seconds": duration,
            },
            CheckNormalizationConfig(),
        )
    except subprocess.TimeoutExpired as exc:
        duration = monotonic() - start
        return normalize_outcome(
            {
                "exit_code": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "timed_out": True,
                "duration_seconds": duration,
            },
            CheckNormalizationConfig(),
        )
    except OSError:
        duration = monotonic() - start
        return CheckOutcome(
            outcome="invalid",
            failure_label="check_launch_error",
            exit_code=None,
            timed_out=False,
            duration_seconds=duration,
            evidence_excerpt="[verifier output omitted]",
        )


def normalize_outcome(raw_output: object, normalization_config: CheckNormalizationConfig) -> CheckOutcome:
    raw = _raw_mapping(raw_output)
    timed_out = bool(raw.get("timed_out", False))
    exit_code = raw.get("exit_code")
    duration = float(raw.get("duration_seconds", 0.0))
    evidence_excerpt = _sanitize_evidence(
        f"{raw.get('stdout', '')}\n{raw.get('stderr', '')}",
        normalization_config,
    )
    if timed_out:
        return CheckOutcome("invalid", normalization_config.timeout_failure_label, None, True, duration, evidence_excerpt)
    if not isinstance(exit_code, int):
        return CheckOutcome("invalid", normalization_config.invalid_failure_label, None, False, duration, evidence_excerpt)
    if exit_code in normalization_config.pass_exit_codes:
        return CheckOutcome("pass", None, exit_code, False, duration, evidence_excerpt)
    if exit_code in normalization_config.invalid_exit_codes:
        return CheckOutcome("invalid", normalization_config.invalid_failure_label, exit_code, False, duration, evidence_excerpt)
    return CheckOutcome("fail", normalization_config.fail_failure_label, exit_code, False, duration, evidence_excerpt)


def repeat_verification(
    check: CheckRecord,
    verifier_workspace_factory: Callable[[], WorkspaceRef],
    repeat_count: int,
    runtime_config: RuntimeConfig,
    workspace_cleanup: Callable[[WorkspaceRef], None],
) -> Sequence[CheckOutcome]:
    if repeat_count < 1:
        raise ValueError("repeat_count must be at least 1")
    outcomes: list[CheckOutcome] = []
    for _ in range(repeat_count):
        workspace = verifier_workspace_factory()
        try:
            prepared_workspace = prepare_verifier(check, workspace)
            outcomes.append(verify_diff(check, prepared_workspace, runtime_config))
        finally:
            workspace_cleanup(workspace)
    return tuple(outcomes)


def summarize_evidence(outcome: CheckOutcome) -> EvidenceSummary:
    return EvidenceSummary(
        outcome=outcome.outcome,
        failure_label=outcome.failure_label,
        timed_out=outcome.timed_out,
        duration_seconds=outcome.duration_seconds,
        evidence_excerpt=_summary_safe_excerpt(outcome.evidence_excerpt),
    )


def _verification_timeout(check: CheckRecord, runtime_config: RuntimeConfig) -> int:
    check_timeout = check.resource_limits.get("timeout_seconds")
    if isinstance(check_timeout, int) and check_timeout > 0:
        return min(check_timeout, runtime_config.timeout_seconds)
    return runtime_config.timeout_seconds


def _raw_mapping(raw_output: object) -> Mapping[str, Any]:
    if isinstance(raw_output, Mapping):
        return raw_output
    if isinstance(raw_output, subprocess.CompletedProcess):
        return {
            "exit_code": raw_output.returncode,
            "stdout": raw_output.stdout or "",
            "stderr": raw_output.stderr or "",
            "timed_out": False,
            "duration_seconds": 0.0,
        }
    raise ValueError("raw_output must be a mapping or CompletedProcess")


def _sanitize_evidence(text: str, config: CheckNormalizationConfig) -> str:
    if not config.allow_verifier_text:
        return "[verifier output omitted]"
    sanitized = text[: config.max_evidence_chars]
    lowered = sanitized.lower()
    if any(marker.lower() in lowered for marker in config.forbidden_evidence_markers):
        return "[redacted unsafe verifier evidence]"
    return sanitized


def _workspace_matches_check(check: CheckRecord, verifier_workspace: WorkspaceRef) -> bool:
    return (
        verifier_workspace.check_id == check.check_id
        and verifier_workspace.check_manifest_digest == check.check_manifest_digest
        and verifier_workspace.hidden_check_bundle_digest == check.hidden_check_bundle_digest
    )


def _summary_safe_excerpt(evidence_excerpt: str) -> str:
    safe_values = {
        "",
        "[verifier output omitted]",
        "[redacted unsafe verifier evidence]",
    }
    if evidence_excerpt in safe_values:
        return evidence_excerpt
    return "[verifier output omitted]"


def _check_command_digest(check_command: Sequence[str]) -> str:
    return canonical_digest({"check_command": tuple(check_command)})


def _path_digest(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_dir():
        entries = []
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            entries.append((str(child.relative_to(path)), hashlib.sha256(child.read_bytes()).hexdigest()))
        return canonical_digest(tuple(entries))
    raise ValueError("hidden_material_source must be an existing file or directory")


def _resolve_under_workspace(workspace: Path, destination: Path) -> Path:
    workspace_resolved = workspace.resolve()
    destination_resolved = (workspace / destination).resolve() if not destination.is_absolute() else destination.resolve()
    if workspace_resolved != destination_resolved and workspace_resolved not in destination_resolved.parents:
        raise ValueError("hidden material destination must stay inside verifier workspace")
    return destination_resolved
