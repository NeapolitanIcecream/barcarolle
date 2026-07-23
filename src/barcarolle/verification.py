"""Verification checks and normalized outcomes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from shutil import copy2, copytree
from time import monotonic
from typing import Any, Mapping
import hashlib
import math
import os
import stat
import subprocess

from barcarolle._subprocess import run_bounded_process
from barcarolle.records import (
    CheckRecord,
    RuntimeConfig,
    canonical_digest,
    make_check_command_digest,
)


VERIFICATION_ADAPTER_DIGEST = canonical_digest(
    {"adapter": "builtin_verifier", "version": 1}
)


@dataclass(frozen=True)
class VerifierWorkspace:
    path: Path
    check_command: tuple[str, ...]
    check_command_digest: str
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
    invalid_exit_codes: tuple[int, ...] = (2,)
    timeout_failure_label: str = "timeout"
    fail_failure_label: str = "check_failed"
    invalid_failure_label: str = "check_invalid"
    max_evidence_chars: int = 1200
    forbidden_evidence_markers: tuple[str, ...] = (
        "hidden",
        "oracle",
        "expected output",
    )
    allow_verifier_text: bool = False

    def __post_init__(self) -> None:
        if any(
            type(codes) is not tuple or any(type(code) is not int for code in codes)
            for codes in (self.pass_exit_codes, self.invalid_exit_codes)
        ):
            raise ValueError("pass and invalid exit codes must be integers")
        if set(self.pass_exit_codes) & set(self.invalid_exit_codes):
            raise ValueError("pass and invalid exit codes must not overlap")
        labels = (
            self.timeout_failure_label,
            self.fail_failure_label,
            self.invalid_failure_label,
        )
        if any(type(label) is not str or not label for label in labels):
            raise ValueError("failure labels must be nonempty strings")
        if type(self.max_evidence_chars) is not int or self.max_evidence_chars <= 0:
            raise ValueError("max_evidence_chars must be a positive integer")
        if type(self.forbidden_evidence_markers) is not tuple or any(
            type(marker) is not str for marker in self.forbidden_evidence_markers
        ):
            raise ValueError("forbidden evidence markers must be strings")
        if type(self.allow_verifier_text) is not bool:
            raise ValueError("allow_verifier_text must be a bool")


@dataclass(frozen=True)
class EvidenceSummary:
    outcome: str
    failure_label: str | None
    timed_out: bool
    duration_seconds: float
    evidence_excerpt: str


def prepare_verifier(
    check: CheckRecord, verifier_workspace: VerifierWorkspace
) -> VerifierWorkspace:
    if not _workspace_matches_check(check, verifier_workspace):
        raise ValueError("verifier workspace identity does not match check")
    if verifier_workspace.hidden_material_source is None:
        raise ValueError(
            "hidden_material_source is required to prepare verifier workspace"
        )
    if (
        hidden_material_digest(verifier_workspace.hidden_material_source)
        != check.hidden_check_bundle_digest
    ):
        raise ValueError("hidden material digest does not match check")
    if (
        make_check_command_digest(verifier_workspace.check_command)
        != verifier_workspace.check_command_digest
    ):
        raise ValueError("check command digest does not match bound command")
    if verifier_workspace.hidden_material_destination is None:
        raise ValueError(
            "hidden_material_destination is required when hidden material is provided"
        )
    destination = _resolve_under_workspace(
        verifier_workspace.path, verifier_workspace.hidden_material_destination
    )
    source = verifier_workspace.hidden_material_source
    if _path_lexists(destination):
        raise ValueError(
            "hidden material destination must be absent before preparation"
        )
    relative_destination = verifier_workspace.hidden_material_destination
    if (
        not relative_destination.is_absolute()
        and relative_destination.parts
        and relative_destination.parts[0] == ".barcarolle"
        and _path_lexists(verifier_workspace.path / ".barcarolle")
    ):
        raise ValueError(
            "reserved .barcarolle namespace must be absent before preparation"
        )
    if source.is_dir():
        copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, destination)
    if hidden_material_digest(destination) != check.hidden_check_bundle_digest:
        raise ValueError("copied hidden material digest does not match check")
    return replace(verifier_workspace, prepared=True)


def verify_diff(
    check: CheckRecord,
    verifier_workspace: VerifierWorkspace,
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
    if (
        make_check_command_digest(verifier_workspace.check_command)
        != verifier_workspace.check_command_digest
    ):
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
        completed = run_bounded_process(
            verifier_workspace.check_command,
            cwd=verifier_workspace.path,
            timeout_seconds=timeout,
        )
        duration = monotonic() - start
        if completed.containment_error is not None:
            return CheckOutcome(
                outcome="invalid",
                failure_label="check_process_containment_failed",
                exit_code=completed.returncode,
                timed_out=completed.timed_out,
                duration_seconds=duration,
                evidence_excerpt="[verifier output omitted]",
            )
        return normalize_outcome(
            {
                "exit_code": completed.returncode,
                "stdout": completed.stdout.text,
                "stderr": completed.stderr.text,
                "timed_out": completed.timed_out,
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


def normalize_outcome(
    raw_output: object, normalization_config: CheckNormalizationConfig
) -> CheckOutcome:
    raw = _raw_mapping(raw_output)
    timed_out = raw.get("timed_out", False)
    exit_code = raw.get("exit_code")
    raw_duration = raw.get("duration_seconds", 0.0)
    evidence_excerpt = _sanitize_evidence(
        f"{raw.get('stdout', '')}\n{raw.get('stderr', '')}",
        normalization_config,
    )
    try:
        duration = float(raw_duration)
    except (OverflowError, TypeError, ValueError):
        duration = math.nan
    if (
        type(timed_out) is not bool
        or (exit_code is not None and type(exit_code) is not int)
        or isinstance(raw_duration, bool)
        or not isinstance(raw_duration, int | float)
        or not math.isfinite(duration)
        or duration < 0.0
    ):
        return CheckOutcome(
            "invalid",
            normalization_config.invalid_failure_label,
            None,
            False,
            0.0,
            evidence_excerpt,
        )
    if timed_out:
        return CheckOutcome(
            "invalid",
            normalization_config.timeout_failure_label,
            None,
            True,
            duration,
            evidence_excerpt,
        )
    if not isinstance(exit_code, int):
        return CheckOutcome(
            "invalid",
            normalization_config.invalid_failure_label,
            None,
            False,
            duration,
            evidence_excerpt,
        )
    if exit_code in normalization_config.pass_exit_codes:
        return CheckOutcome("pass", None, exit_code, False, duration, evidence_excerpt)
    if exit_code in normalization_config.invalid_exit_codes:
        return CheckOutcome(
            "invalid",
            normalization_config.invalid_failure_label,
            exit_code,
            False,
            duration,
            evidence_excerpt,
        )
    return CheckOutcome(
        "fail",
        normalization_config.fail_failure_label,
        exit_code,
        False,
        duration,
        evidence_excerpt,
    )


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


def _workspace_matches_check(
    check: CheckRecord, verifier_workspace: VerifierWorkspace
) -> bool:
    return (
        verifier_workspace.check_id == check.check_id
        and verifier_workspace.check_manifest_digest == check.check_manifest_digest
        and verifier_workspace.hidden_check_bundle_digest
        == check.hidden_check_bundle_digest
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


def hidden_material_digest(path: Path) -> str:
    """Digest one verifier-only tree without following symbolic links."""
    if path.is_symlink():
        raise ValueError("hidden material must not contain symbolic links")
    if path.is_file():
        entries = (_hidden_entry(path, Path(".")),)
    elif path.is_dir():
        entries_list = [_hidden_entry(path, Path("."))]
        for root, directory_names, file_names in os.walk(path, followlinks=False):
            directory_names.sort()
            file_names.sort()
            root_path = Path(root)
            for name in directory_names:
                child = root_path / name
                if child.is_symlink():
                    raise ValueError("hidden material must not contain symbolic links")
                entries_list.append(_hidden_entry(child, child.relative_to(path)))
            for name in file_names:
                child = root_path / name
                if child.is_symlink():
                    raise ValueError("hidden material must not contain symbolic links")
                entries_list.append(_hidden_entry(child, child.relative_to(path)))
        entries = tuple(sorted(entries_list, key=lambda entry: entry[0]))
    else:
        raise ValueError(
            "hidden_material_source must be an existing regular file or directory"
        )
    return canonical_digest(
        {
            "format": "hidden_material_tree_v1",
            "entries": entries,
        }
    )


def _hidden_entry(path: Path, relative_path: Path) -> tuple[str, str, int, str | None]:
    metadata = path.lstat()
    executable_bits = stat.S_IMODE(metadata.st_mode) & 0o111
    if stat.S_ISREG(metadata.st_mode):
        entry_type = "file"
        content_digest: str | None = _file_sha256(path)
    elif stat.S_ISDIR(metadata.st_mode):
        entry_type = "directory"
        content_digest = None
    else:
        raise ValueError("hidden material contains an unsupported entry type")
    return (
        relative_path.as_posix(),
        entry_type,
        executable_bits,
        content_digest,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _resolve_under_workspace(workspace: Path, destination: Path) -> Path:
    workspace_resolved = workspace.resolve()
    destination_resolved = (
        (workspace / destination).resolve()
        if not destination.is_absolute()
        else destination.resolve()
    )
    if not destination_resolved.is_relative_to(workspace_resolved):
        raise ValueError(
            "hidden material destination must stay inside verifier workspace"
        )
    return destination_resolved
