"""Workspace orchestration for solver and verifier runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from threading import Lock
from time import monotonic
from typing import Any, Mapping, Sequence
import hashlib
import json
import math
import shutil
import subprocess
import warnings

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    RuntimeConfig,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    validate_task,
)
from barcarolle.verification import CheckOutcome, WorkspaceRef as VerifierWorkspaceRef
from barcarolle.verification import prepare_verifier, verify_diff


@dataclass(frozen=True)
class WorkspaceRef:
    path: Path
    role: str
    task_id: str
    base_commit: str
    workspace_digest: str
    agent_command: tuple[str, ...] = ()
    check_command: tuple[str, ...] = ()
    hidden_material_source: Path | None = None
    hidden_material_destination: Path | None = None


@dataclass(frozen=True)
class WorkspaceArtifactConfig:
    output_root: Path
    preserve_stdout_stderr: bool = True
    preserve_final_diff: bool = True
    preserve_solver_workspace_summary: str = "never"
    preserve_verifier_workspace_summary: str = "never"
    path_mode: str = "relative"


@dataclass(frozen=True)
class WorkspaceArtifactRef:
    kind: str
    ref: str
    digest: str
    private: bool = False


@dataclass(frozen=True)
class WorkspaceArtifactManifest:
    manifest_ref: str
    artifact_refs: tuple[WorkspaceArtifactRef, ...]


@dataclass(frozen=True)
class WorkspaceRunResult:
    run: WorkspaceRunRecord
    artifacts: WorkspaceArtifactManifest | None = None


@dataclass(frozen=True)
class AgentRunOutcome:
    terminal_status: str
    duration_seconds: float
    usage: Mapping[str, Any]
    safe_output_digest: str
    failure_label: str | None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class CapturedDiff:
    diff_text: str
    diff_digest: str


@dataclass(frozen=True)
class DiffReplayOutcome:
    replay_status: str
    failure_label: str | None
    safe_output_digest: str


@dataclass(frozen=True)
class _CheckMaterialBinding:
    check_command: tuple[str, ...]
    check_command_digest: str
    hidden_material_source: Path
    hidden_material_destination: Path


_REPOSITORY_SOURCES: dict[str, Path] = {}
_AGENT_HARNESSES: dict[tuple[str, str, str], tuple[str, ...]] = {}
_CHECK_MATERIALS: dict[tuple[str, str, str], _CheckMaterialBinding] = {}
_OWNED_WORKSPACES: dict[Path, tuple[int, int]] = {}
_OWNED_WORKSPACE_LOCK = Lock()
_EMPTY_DIFF_DIGEST = hashlib.sha256(b"").hexdigest()
_CAPTURE_PATHSPEC = (
    ".",
    ":(top,exclude).barcarolle",
    ":(top,exclude).barcarolle/**",
    ":(top,glob,exclude)**/.pytest_cache/**",
    ":(top,glob,exclude)**/__pycache__/**",
)
_USAGE_FILE = Path(".barcarolle/usage.json")
_BENCHMARK_CHECK_FAILURE_LABELS = frozenset(
    {
        "baseline_check_passed_without_diff",
        "check_command_mismatch",
        "check_workspace_mismatch",
        "hidden_material_mismatch",
        "invalid_hidden_material_destination",
        "missing_check_command",
        "missing_verification_material",
        "not_verifier_workspace",
        "verifier_preparation_failed",
    }
)


def bind_repository_source(workspace_config: WorkspaceConfig, repository_path: Path) -> None:
    source = repository_path.resolve()
    if not (source / ".git").exists():
        raise ValueError("repository_path must be a git repository checkout")
    _REPOSITORY_SOURCES[workspace_config.repository_checkout_config_digest] = source


def bind_agent_harness(agent: AgentRecord, command: Sequence[str]) -> None:
    normalized = tuple(command)
    if not normalized:
        raise ValueError("agent harness command is required")
    if _agent_command_digest(normalized) != agent.harness_digest:
        raise ValueError("agent harness command digest does not match Agent harness")
    _AGENT_HARNESSES[_agent_key(agent)] = normalized


def bind_check_material(
    check: CheckRecord,
    check_command: Sequence[str],
    hidden_material_source: Path,
    hidden_material_destination: Path = Path(".barcarolle/check_bundle"),
    *,
    check_manifest: Mapping[str, Any] | None = None,
) -> None:
    if not _is_reserved_hidden_material_destination(hidden_material_destination):
        raise ValueError("hidden material destination must stay under .barcarolle")
    normalized_command = tuple(check_command)
    manifest = (
        check_manifest
        if check_manifest is not None
        else {"check_command": normalized_command}
    )
    if canonical_digest(manifest) != check.check_manifest_digest:
        raise ValueError("check manifest digest does not match check")
    source = hidden_material_source.resolve()
    if not source.exists():
        raise ValueError("hidden_material_source must exist")
    if _path_digest(source) != check.hidden_check_bundle_digest:
        raise ValueError("hidden material digest does not match check")
    _CHECK_MATERIALS[_check_key(check)] = _CheckMaterialBinding(
        check_command=normalized_command,
        check_command_digest=_check_command_digest(normalized_command),
        hidden_material_source=source,
        hidden_material_destination=hidden_material_destination,
    )


def create_solver_workspace(task: TaskRecord, workspace_config: WorkspaceConfig) -> WorkspaceRef:
    validation = validate_task(task)
    if not validation.ok:
        raise ValueError(f"task is invalid: {', '.join(validation.errors)}")
    path = _checkout_repository(task, workspace_config, prefix="barcarolle-solver-")
    try:
        _exclude_benchmark_material(path)
        _write_solver_visible_task_material(path, task)
        return WorkspaceRef(
            path=path,
            role="solver",
            task_id=task.task_id,
            base_commit=task.base_commit,
            workspace_digest=_workspace_digest(path, task, workspace_config, "solver"),
        )
    except BaseException:
        _discard_owned_workspace_path(path)
        raise


def validate_solver_material_refs(workspace: WorkspaceRef, task: TaskRecord) -> None:
    if workspace.task_id != task.task_id or workspace.role not in {"solver", "verifier"}:
        raise ValueError("workspace does not match Task")
    _validate_solver_material_refs(workspace.path, task)


def invoke_agent(
    solver_workspace: WorkspaceRef,
    task: TaskRecord,
    agent: AgentRecord,
    runtime_config: RuntimeConfig,
) -> AgentRunOutcome:
    if solver_workspace.role != "solver" or solver_workspace.task_id != task.task_id:
        return AgentRunOutcome("invalid", 0.0, {}, "", "solver_workspace_task_mismatch")
    command = solver_workspace.agent_command or _AGENT_HARNESSES.get(_agent_key(agent), ())
    if not command:
        return AgentRunOutcome("invalid", 0.0, {}, "", "missing_agent_command")
    usage_path = solver_workspace.path / _USAGE_FILE
    usage_path.unlink(missing_ok=True)
    start = monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=solver_workspace.path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=runtime_config.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _normalize_output(exc.stdout)
        stderr = _normalize_output(exc.stderr)
        return AgentRunOutcome(
            terminal_status="timeout",
            duration_seconds=monotonic() - start,
            usage={},
            safe_output_digest=_safe_output_digest(stdout, stderr),
            failure_label="agent_timeout",
            stdout=stdout,
            stderr=stderr,
        )
    except OSError:
        return AgentRunOutcome("invalid", monotonic() - start, {}, "", "agent_launch_error")
    try:
        usage = _load_agent_usage(usage_path)
    except (OSError, ValueError):
        usage = {}
    terminal_status = "completed" if completed.returncode == 0 else "error"
    return AgentRunOutcome(
        terminal_status=terminal_status,
        duration_seconds=monotonic() - start,
        usage=usage,
        safe_output_digest=_safe_output_digest(completed.stdout, completed.stderr),
        failure_label=None if completed.returncode == 0 else "agent_failed",
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _load_agent_usage(path: Path) -> Mapping[str, int | float]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Agent usage must be a string-keyed JSON object")
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError(f"Agent usage value for {key} must be numeric")
        try:
            numeric_item = float(item)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"Agent usage value for {key} must be finite and nonnegative") from exc
        if not math.isfinite(numeric_item) or numeric_item < 0.0:
            raise ValueError(f"Agent usage value for {key} must be finite and nonnegative")
    return value


def capture_diff(solver_workspace: WorkspaceRef) -> CapturedDiff:
    if solver_workspace.role != "solver":
        raise ValueError("diff capture requires a solver workspace")
    if not _is_git_checkout(solver_workspace.path):
        raise ValueError("solver workspace must be a git checkout")
    _run_git(solver_workspace.path, ("add", "--intent-to-add", "--force", "--", *_CAPTURE_PATHSPEC))
    diff_text = _run_git(
        solver_workspace.path,
        (
            "diff",
            "--binary",
            "--no-color",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            solver_workspace.base_commit,
            "--",
            *_CAPTURE_PATHSPEC,
        ),
    ).stdout
    _validate_captured_diff_paths(diff_text)
    return CapturedDiff(diff_text=diff_text, diff_digest=hashlib.sha256(diff_text.encode("utf-8")).hexdigest())


def create_verifier_workspace(task: TaskRecord, workspace_config: WorkspaceConfig) -> WorkspaceRef:
    path = _checkout_repository(task, workspace_config, prefix="barcarolle-verifier-")
    try:
        _exclude_benchmark_material(path)
        return WorkspaceRef(
            path=path,
            role="verifier",
            task_id=task.task_id,
            base_commit=task.base_commit,
            workspace_digest=_workspace_digest(path, task, workspace_config, "verifier"),
        )
    except BaseException:
        _discard_owned_workspace_path(path)
        raise


def cleanup_workspace(workspace: WorkspaceRef) -> None:
    """Remove a workspace returned by a low-level create function."""
    _cleanup_workspaces(workspace)


def apply_diff(verifier_workspace: WorkspaceRef, diff: CapturedDiff) -> DiffReplayOutcome:
    if verifier_workspace.role != "verifier":
        return DiffReplayOutcome("invalid", "not_verifier_workspace", "")
    if not _is_git_checkout(verifier_workspace.path):
        return DiffReplayOutcome("invalid", "missing_git_checkout", "")
    if not diff.diff_text:
        return DiffReplayOutcome("applied", None, "")
    try:
        completed = subprocess.run(
            ("git", "apply", "--whitespace=nowarn", "-"),
            cwd=verifier_workspace.path,
            input=diff.diff_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return DiffReplayOutcome("invalid", "diff_replay_launch_error", "")
    return DiffReplayOutcome(
        replay_status="applied" if completed.returncode == 0 else "failed",
        failure_label=None if completed.returncode == 0 else "diff_replay_failed",
        safe_output_digest=_safe_output_digest(completed.stdout, completed.stderr),
    )


def verify_agent_diff(
    verifier_workspace: WorkspaceRef,
    check: CheckRecord,
    runtime_config: RuntimeConfig,
) -> CheckOutcome:
    if verifier_workspace.role != "verifier":
        return CheckOutcome("invalid", "not_verifier_workspace", None, False, 0.0, "")
    if verifier_workspace.task_id != check.task_id:
        return CheckOutcome("invalid", "check_workspace_mismatch", None, False, 0.0, "")
    binding = _material_binding(check, verifier_workspace)
    if binding is None:
        return CheckOutcome("invalid", "missing_verification_material", None, False, 0.0, "")
    if not _is_reserved_hidden_material_destination(binding.hidden_material_destination):
        return CheckOutcome("invalid", "invalid_hidden_material_destination", None, False, 0.0, "")
    verifier_ref = VerifierWorkspaceRef(
        path=verifier_workspace.path,
        check_command=binding.check_command,
        check_command_digest=binding.check_command_digest,
        check_id=check.check_id,
        check_manifest_digest=check.check_manifest_digest,
        hidden_check_bundle_digest=check.hidden_check_bundle_digest,
        hidden_material_source=binding.hidden_material_source,
        hidden_material_destination=binding.hidden_material_destination,
    )
    try:
        prepared = prepare_verifier(check, verifier_ref)
    except (OSError, ValueError, shutil.Error) as exc:
        return CheckOutcome("invalid", _preparation_failure_label(str(exc)), None, False, 0.0, "")
    return verify_diff(check, prepared, runtime_config)


def run_agent_on_task(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> WorkspaceRunRecord:
    return run_agent_on_task_with_artifacts(task, check, agent, workspace_config, runtime_config).run


def run_agent_on_task_with_artifacts(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    artifact_config: WorkspaceArtifactConfig | None = None,
) -> WorkspaceRunResult:
    started_at = _now()
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        run = _invalid_run_record(
            task=task,
            check=check,
            agent=agent,
            started_at=started_at,
            failure_label="task_check_mismatch",
            invalid_owner="benchmark",
        )
        return _workspace_run_result(run, artifact_config, None, None, None, None)
    solver_workspace: WorkspaceRef | None = None
    verifier_workspace: WorkspaceRef | None = None
    try:
        try:
            solver_workspace = create_solver_workspace(task, workspace_config)
        except (OSError, RuntimeError, ValueError) as exc:
            run = _invalid_run_record(
                task=task,
                check=check,
                agent=agent,
                started_at=started_at,
                failure_label=_workspace_failure_label(str(exc)),
                invalid_owner="benchmark",
            )
            return _workspace_run_result(run, artifact_config, None, None, None, None)
        agent_outcome = invoke_agent(solver_workspace, task, agent, runtime_config)
        try:
            diff = capture_diff(solver_workspace)
        except (OSError, RuntimeError, ValueError):
            run = _invalid_run_record(
                task=task,
                check=check,
                agent=agent,
                started_at=started_at,
                failure_label="agent_workspace_corrupted",
                invalid_owner="agent",
                solver_workspace_digest=solver_workspace.workspace_digest,
                usage=agent_outcome.usage,
            )
            return _workspace_run_result(run, artifact_config, None, agent_outcome, solver_workspace, None)
        try:
            verifier_workspace = create_verifier_workspace(task, workspace_config)
        except (OSError, RuntimeError, ValueError) as exc:
            replay = DiffReplayOutcome("invalid", _workspace_failure_label(str(exc)), "")
            check_outcome = CheckOutcome("invalid", replay.failure_label, None, False, 0.0, "")
            run = _workspace_run_record(
                task=task,
                check=check,
                agent=agent,
                solver_workspace_digest=solver_workspace.workspace_digest,
                verifier_workspace_digest=_synthetic_workspace_digest(task, "verifier", replay.failure_label or "verifier_workspace_error"),
                agent_outcome=agent_outcome,
                diff=diff,
                replay=replay,
                check_outcome=check_outcome,
                started_at=started_at,
                finished_at=_now(),
            )
            return _workspace_run_result(run, artifact_config, diff, agent_outcome, solver_workspace, None)
        replay = apply_diff(verifier_workspace, diff)
        if replay.replay_status == "applied":
            check_outcome = verify_agent_diff(verifier_workspace, check, runtime_config)
            if not diff.diff_text and check_outcome.outcome == "pass":
                check_outcome = CheckOutcome(
                    outcome="invalid",
                    failure_label="baseline_check_passed_without_diff",
                    exit_code=check_outcome.exit_code,
                    timed_out=check_outcome.timed_out,
                    duration_seconds=check_outcome.duration_seconds,
                    evidence_excerpt=check_outcome.evidence_excerpt,
                )
        else:
            check_outcome = CheckOutcome("invalid", replay.failure_label, None, False, 0.0, "")
        check_execution_failure_agent_owned = (
            check_outcome.failure_label in {"check_invalid", "check_launch_error"}
            and _agent_changed_check_command_path(check, verifier_workspace, diff)
        )
        run = _workspace_run_record(
            task=task,
            check=check,
            agent=agent,
            solver_workspace_digest=solver_workspace.workspace_digest,
            verifier_workspace_digest=verifier_workspace.workspace_digest,
            agent_outcome=agent_outcome,
            diff=diff,
            replay=replay,
            check_outcome=check_outcome,
            started_at=started_at,
            finished_at=_now(),
            check_execution_failure_agent_owned=check_execution_failure_agent_owned,
        )
        return _workspace_run_result(run, artifact_config, diff, agent_outcome, solver_workspace, verifier_workspace)
    finally:
        try:
            _cleanup_workspaces(verifier_workspace, solver_workspace)
        except RuntimeError as exc:
            warnings.warn(str(exc), RuntimeWarning, stacklevel=2)


def _workspace_run_result(
    run: WorkspaceRunRecord,
    artifact_config: WorkspaceArtifactConfig | None,
    diff: CapturedDiff | None,
    agent_outcome: AgentRunOutcome | None,
    solver_workspace: WorkspaceRef | None,
    verifier_workspace: WorkspaceRef | None,
) -> WorkspaceRunResult:
    if artifact_config is None:
        return WorkspaceRunResult(run=run)
    return WorkspaceRunResult(
        run=run,
        artifacts=_preserve_run_artifacts(
            artifact_config,
            run,
            diff,
            agent_outcome,
            solver_workspace,
            verifier_workspace,
        ),
    )


def _preserve_run_artifacts(
    config: WorkspaceArtifactConfig,
    run: WorkspaceRunRecord,
    diff: CapturedDiff | None,
    agent_outcome: AgentRunOutcome | None,
    solver_workspace: WorkspaceRef | None,
    verifier_workspace: WorkspaceRef | None,
) -> WorkspaceArtifactManifest:
    _validate_artifact_config(config)
    artifact_refs: list[WorkspaceArtifactRef] = []
    run_ref = run.workspace_run_id
    if config.preserve_final_diff and diff is not None:
        artifact_refs.append(_write_text_artifact(config.output_root, run_ref, "final.diff", "final_diff", diff.diff_text))
    if config.preserve_stdout_stderr and agent_outcome is not None:
        artifact_refs.append(_write_text_artifact(config.output_root, run_ref, "stdout.txt", "agent_stdout", agent_outcome.stdout))
        artifact_refs.append(_write_text_artifact(config.output_root, run_ref, "stderr.txt", "agent_stderr", agent_outcome.stderr))
    if solver_workspace is not None and _should_preserve_workspace_summary(config.preserve_solver_workspace_summary, run):
        artifact_refs.append(
            _write_text_artifact(
                config.output_root,
                run_ref,
                "solver-workspace-summary.json",
                "solver_workspace_summary",
                _workspace_summary_json(solver_workspace, private=False),
            )
        )
    if verifier_workspace is not None and _should_preserve_workspace_summary(config.preserve_verifier_workspace_summary, run):
        artifact_refs.append(
            _write_text_artifact(
                config.output_root,
                run_ref,
                "verifier-workspace-summary.json",
                "verifier_workspace_summary",
                _workspace_summary_json(verifier_workspace, private=True),
                private=True,
            )
        )
    manifest_ref = f"{run_ref}/manifest.json"
    manifest_payload = {
        "workspace_run_id": run.workspace_run_id,
        "artifact_refs": tuple(_artifact_ref_data(ref) for ref in artifact_refs),
    }
    manifest_path = config.output_root / manifest_ref
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return WorkspaceArtifactManifest(manifest_ref=manifest_ref, artifact_refs=tuple(artifact_refs))


def _validate_artifact_config(config: WorkspaceArtifactConfig) -> None:
    if config.path_mode != "relative":
        raise ValueError("Workspace artifact path_mode must be relative")
    for mode in (config.preserve_solver_workspace_summary, config.preserve_verifier_workspace_summary):
        if mode not in {"never", "on_failure", "always"}:
            raise ValueError("workspace summary preservation must be never, on_failure, or always")


def _should_preserve_workspace_summary(mode: str, run: WorkspaceRunRecord) -> bool:
    if mode == "always":
        return True
    if mode == "on_failure":
        return run.terminal_status != "passed"
    return False


def _write_text_artifact(
    output_root: Path,
    run_ref: str,
    filename: str,
    kind: str,
    content: str,
    *,
    private: bool = False,
) -> WorkspaceArtifactRef:
    ref = f"{run_ref}/{filename}"
    path = output_root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return WorkspaceArtifactRef(
        kind=kind,
        ref=ref,
        digest=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        private=private,
    )


def _workspace_summary_json(workspace: WorkspaceRef, *, private: bool) -> str:
    payload = {
        "artifact_class": "verifier_private" if private else "solver",
        "base_commit": workspace.base_commit,
        "private": private,
        "task_id": workspace.task_id,
        "workspace_digest": workspace.workspace_digest,
        "workspace_role": workspace.role,
    }
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def _artifact_ref_data(ref: WorkspaceArtifactRef) -> Mapping[str, Any]:
    return {
        "kind": ref.kind,
        "ref": ref.ref,
        "digest": ref.digest,
        "private": ref.private,
    }


def _checkout_repository(task: TaskRecord, workspace_config: WorkspaceConfig, *, prefix: str) -> Path:
    source = _REPOSITORY_SOURCES.get(workspace_config.repository_checkout_config_digest)
    if source is None:
        raise ValueError("repository source is not bound for workspace config")
    path = Path(mkdtemp(prefix=prefix))
    _register_owned_workspace_path(path)
    try:
        _run_git(path, ("init", "--quiet"))
        _run_git(
            path,
            ("fetch", "--quiet", "--no-tags", str(source), task.base_commit),
        )
        _run_git(path, ("checkout", "--quiet", "--detach", "FETCH_HEAD"))
        (path / ".git" / "FETCH_HEAD").unlink(missing_ok=True)
        return path
    except BaseException:
        _discard_owned_workspace_path(path)
        raise


def _cleanup_workspaces(*workspaces: WorkspaceRef | None) -> None:
    failures: list[str] = []
    for workspace in workspaces:
        if workspace is None:
            continue
        try:
            _remove_owned_workspace_path(workspace.path)
        except (OSError, ValueError) as exc:
            failures.append(f"{workspace.role}:{type(exc).__name__}")
    if failures:
        raise RuntimeError(f"workspace cleanup failed ({', '.join(failures)})")


def _register_owned_workspace_path(path: Path) -> None:
    resolved = path.resolve(strict=True)
    stat = resolved.stat()
    with _OWNED_WORKSPACE_LOCK:
        _OWNED_WORKSPACES[resolved] = (stat.st_dev, stat.st_ino)


def _remove_owned_workspace_path(path: Path) -> None:
    resolved = path.resolve()
    with _OWNED_WORKSPACE_LOCK:
        expected_identity = _OWNED_WORKSPACES.get(resolved)
        if expected_identity is None:
            raise ValueError("workspace path is not owned by Barcarolle")
    try:
        stat = path.stat()
    except FileNotFoundError as exc:
        raise ValueError("owned workspace path is missing") from exc
    if (stat.st_dev, stat.st_ino) != expected_identity:
        raise ValueError("owned workspace path was replaced")
    with _OWNED_WORKSPACE_LOCK:
        _OWNED_WORKSPACES.pop(resolved, None)
    try:
        shutil.rmtree(path)
    except OSError:
        with _OWNED_WORKSPACE_LOCK:
            _OWNED_WORKSPACES[resolved] = expected_identity
        raise


def _discard_owned_workspace_path(path: Path) -> None:
    resolved = path.resolve()
    with _OWNED_WORKSPACE_LOCK:
        owned = resolved in _OWNED_WORKSPACES
    if not owned:
        return
    try:
        _remove_owned_workspace_path(path)
    except OSError:
        shutil.rmtree(path, ignore_errors=True)
        with _OWNED_WORKSPACE_LOCK:
            _OWNED_WORKSPACES.pop(resolved, None)


def _write_solver_visible_task_material(path: Path, task: TaskRecord) -> None:
    _validate_solver_material_refs(path, task)
    material_dir = path / ".barcarolle"
    material_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "solver_material_refs": task.solver_material_refs,
        "task_material_file": ".barcarolle/TASK.md",
    }
    (material_dir / "solver-visible-task.json").write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    (material_dir / "TASK.md").write_text(_solver_visible_task_markdown(task), encoding="utf-8")


def _solver_visible_task_markdown(task: TaskRecord) -> str:
    lines = [
        "# Task",
        "",
        task.task_text.rstrip(),
    ]
    if task.solver_material_refs:
        lines.extend(["", "## Files", ""])
        for ref in task.solver_material_refs:
            lines.append(f"- `{ref}`")
    return "\n".join(lines).rstrip() + "\n"


def _validate_solver_material_ref(path: Path, ref: str) -> None:
    ref_path = Path(_solver_material_path_ref(ref))
    if ref_path.is_absolute() or ".." in ref_path.parts:
        raise ValueError(f"solver material reference is outside the workspace: {ref}")
    workspace_root = path.resolve()
    material_path = workspace_root / ref_path
    try:
        material_resolved = material_path.resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"solver material reference could not be resolved: {ref}") from exc
    if not _is_within(material_resolved, workspace_root):
        raise ValueError(f"solver material reference resolves outside the workspace: {ref}")
    if not material_path.is_file():
        raise ValueError(f"solver material reference was not found: {ref}")


def _validate_solver_material_refs(path: Path, task: TaskRecord) -> None:
    for ref in task.solver_material_refs:
        _validate_solver_material_ref(path, ref)


def _solver_material_path_ref(ref: str) -> str:
    for prefix in ("path:", "file:"):
        if ref.startswith(prefix):
            return ref.removeprefix(prefix)
    return ref


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _workspace_digest(path: Path, task: TaskRecord, workspace_config: WorkspaceConfig, role: str) -> str:
    return canonical_digest(
        {
            "role": role,
            "path": str(path),
            "task_id": task.task_id,
            "base_commit": task.base_commit,
            "workspace_config_id": workspace_config.workspace_config_id,
            "repository_checkout_config_digest": workspace_config.repository_checkout_config_digest,
            "submodule_state_digest": workspace_config.submodule_state_digest,
            "base_image_digest": workspace_config.base_image_digest,
            "dependency_lock_digest": workspace_config.dependency_lock_digest,
            "head_commit": _head_commit(path),
        }
    )


def _workspace_run_record(
    *,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    solver_workspace_digest: str,
    verifier_workspace_digest: str,
    agent_outcome: AgentRunOutcome,
    diff: CapturedDiff,
    replay: DiffReplayOutcome,
    check_outcome: CheckOutcome,
    started_at: str,
    finished_at: str,
    check_execution_failure_agent_owned: bool = False,
) -> WorkspaceRunRecord:
    terminal_status = _terminal_status(agent_outcome, replay, check_outcome)
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace_run_{canonical_digest((task.task_id, check.check_id, agent.agent_id, diff.diff_digest, started_at))}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest=solver_workspace_digest,
        verifier_workspace_digest=verifier_workspace_digest,
        terminal_status=terminal_status,
        diff_digest=diff.diff_digest,
        replay_status=replay.replay_status,
        check_outcome=check_outcome.outcome,
        invalid_owner=_invalid_owner(
            terminal_status,
            agent_outcome,
            replay,
            check_outcome,
            check_execution_failure_agent_owned=check_execution_failure_agent_owned,
        ),
        failure_label=_failure_label(agent_outcome, replay, check_outcome),
        usage=agent_outcome.usage,
        started_at=started_at,
        finished_at=finished_at,
    )


def _invalid_run_record(
    *,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    started_at: str,
    failure_label: str,
    invalid_owner: str,
    solver_workspace_digest: str | None = None,
    usage: Mapping[str, Any] | None = None,
) -> WorkspaceRunRecord:
    finished_at = _now()
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace_run_{canonical_digest((task.task_id, check.check_id, agent.agent_id, failure_label, started_at))}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest=solver_workspace_digest or _synthetic_workspace_digest(task, "solver", failure_label),
        verifier_workspace_digest=_synthetic_workspace_digest(task, "verifier", failure_label),
        terminal_status="invalid",
        diff_digest=_EMPTY_DIFF_DIGEST,
        replay_status="skipped",
        check_outcome="invalid",
        invalid_owner=invalid_owner,
        failure_label=failure_label,
        usage=usage or {},
        started_at=started_at,
        finished_at=finished_at,
    )


def _material_binding(check: CheckRecord, verifier_workspace: WorkspaceRef) -> _CheckMaterialBinding | None:
    if verifier_workspace.check_command and verifier_workspace.hidden_material_source is not None:
        command_digest = _check_command_digest(verifier_workspace.check_command)
        if command_digest != check.check_manifest_digest:
            return None
        return _CheckMaterialBinding(
            check_command=verifier_workspace.check_command,
            check_command_digest=command_digest,
            hidden_material_source=verifier_workspace.hidden_material_source,
            hidden_material_destination=verifier_workspace.hidden_material_destination or Path(".barcarolle/check_bundle"),
        )
    return _CHECK_MATERIALS.get(_check_key(check))


def _agent_changed_check_command_path(
    check: CheckRecord,
    verifier_workspace: WorkspaceRef,
    diff: CapturedDiff,
) -> bool:
    binding = _material_binding(check, verifier_workspace)
    if binding is None or not binding.check_command:
        return False
    try:
        changed_paths = set(_captured_diff_paths(diff.diff_text))
    except (RuntimeError, ValueError):
        return False
    for position, command_arg in enumerate(binding.check_command):
        if not command_arg or command_arg.startswith("-"):
            continue
        command_path = Path(command_arg.replace("\\", "/"))
        if command_path.is_absolute():
            try:
                command_path = command_path.relative_to(verifier_workspace.path)
            except ValueError:
                continue
        elif ".." in command_path.parts:
            continue
        elif position == 0 and not any(separator in command_arg for separator in ("/", "\\")):
            continue
        if command_path.as_posix() in changed_paths:
            return True
    return False


def _agent_key(agent: AgentRecord) -> tuple[str, str, str]:
    return (agent.agent_id, agent.agent_manifest_digest, agent.harness_digest)


def _check_key(check: CheckRecord) -> tuple[str, str, str]:
    return (check.check_id, check.check_manifest_digest, check.hidden_check_bundle_digest)


def _terminal_status(
    agent_outcome: AgentRunOutcome,
    replay: DiffReplayOutcome,
    check_outcome: CheckOutcome,
) -> str:
    if replay.replay_status != "applied" or check_outcome.outcome == "invalid":
        return "invalid"
    if agent_outcome.terminal_status != "completed":
        return agent_outcome.terminal_status
    if check_outcome.outcome == "pass":
        return "passed"
    if check_outcome.outcome == "fail":
        return "failed"
    return "invalid"


def _invalid_owner(
    terminal_status: str,
    agent_outcome: AgentRunOutcome,
    replay: DiffReplayOutcome,
    check_outcome: CheckOutcome,
    *,
    check_execution_failure_agent_owned: bool = False,
) -> str | None:
    if terminal_status != "invalid":
        return None
    if replay.replay_status == "failed":
        return "agent"
    if replay.replay_status == "invalid":
        return "benchmark"
    if check_outcome.outcome == "invalid":
        if check_outcome.failure_label in {"check_invalid", "check_launch_error"}:
            return "agent" if check_execution_failure_agent_owned else "benchmark"
        return "benchmark" if check_outcome.failure_label in _BENCHMARK_CHECK_FAILURE_LABELS else "agent"
    if agent_outcome.terminal_status == "invalid":
        return "agent"
    return "benchmark"


def _failure_label(
    agent_outcome: AgentRunOutcome,
    replay: DiffReplayOutcome,
    check_outcome: CheckOutcome,
) -> str | None:
    if replay.replay_status != "applied":
        return replay.failure_label
    if check_outcome.outcome == "invalid":
        return check_outcome.failure_label
    if agent_outcome.terminal_status != "completed":
        return agent_outcome.failure_label
    return check_outcome.failure_label


def _workspace_failure_label(message: str) -> str:
    lowered = message.lower()
    if "repository source is not bound" in lowered:
        return "missing_repository_source"
    if "checkout" in lowered:
        return "repository_checkout_failed"
    return "workspace_preparation_failed"


def _preparation_failure_label(message: str) -> str:
    lowered = message.lower()
    if "identity does not match" in lowered:
        return "check_workspace_mismatch"
    if "hidden_material_source" in lowered:
        return "missing_verification_material"
    if "hidden material digest" in lowered:
        return "hidden_material_mismatch"
    if "check command digest" in lowered:
        return "check_command_mismatch"
    if "inside verifier workspace" in lowered:
        return "invalid_hidden_material_destination"
    return "verifier_preparation_failed"


def _is_reserved_hidden_material_destination(destination: Path) -> bool:
    return (
        not destination.is_absolute()
        and bool(destination.parts)
        and destination.parts[0] == ".barcarolle"
        and ".." not in destination.parts
    )


def _validate_captured_diff_paths(diff_text: str) -> None:
    if not diff_text:
        return
    paths = _captured_diff_paths(diff_text)
    if not paths:
        raise ValueError("captured diff has no parseable paths")
    if any(path == ".barcarolle" or path.startswith(".barcarolle/") for path in paths):
        raise ValueError("captured diff contains reserved workspace material")


def _captured_diff_paths(diff_text: str) -> tuple[str, ...]:
    try:
        completed = subprocess.run(
            ("git", "apply", "--numstat", "-z", "-"),
            input=diff_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError("captured diff path inspection failed") from exc
    if completed.returncode != 0:
        raise RuntimeError("captured diff path inspection failed")
    paths: list[str] = []
    entries = completed.stdout.split("\0")
    index = 0
    while index < len(entries) - 1:
        fields = entries[index].split("\t", 2)
        if len(fields) != 3:
            raise ValueError("captured diff path inspection returned malformed output")
        if fields[2]:
            paths.append(fields[2])
            index += 1
            continue
        if index + 2 >= len(entries) - 1:
            raise ValueError("captured diff path inspection returned malformed rename output")
        paths.extend((entries[index + 1], entries[index + 2]))
        index += 3
    return tuple(paths)


def _synthetic_workspace_digest(task: TaskRecord, role: str, reason: str) -> str:
    return canonical_digest({"role": role, "task_id": task.task_id, "base_commit": task.base_commit, "not_created": reason})


def _exclude_benchmark_material(path: Path) -> None:
    exclude_path = Path(_run_git(path, ("rev-parse", "--git-path", "info/exclude")).stdout.strip())
    if not exclude_path.is_absolute():
        exclude_path = path / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    if ".barcarolle/" not in existing:
        exclude_path.write_text(f"{existing.rstrip()}\n.barcarolle/\n", encoding="utf-8")


def _head_commit(path: Path) -> str:
    return _run_git(path, ("rev-parse", "HEAD")).stdout.strip()


def _is_git_checkout(path: Path) -> bool:
    return (path / ".git").exists()


def _run_git(path: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return _run(("git", *args), cwd=path)


def _run(command: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "command failed").strip())
    return completed


def _safe_output_digest(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    return hashlib.sha256((_normalize_output(stdout) + "\n" + _normalize_output(stderr)).encode("utf-8")).hexdigest()


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _check_command_digest(check_command: Sequence[str]) -> str:
    return canonical_digest({"check_command": tuple(check_command)})


def _agent_command_digest(agent_command: Sequence[str]) -> str:
    return canonical_digest({"agent_command": tuple(agent_command)})


def _path_digest(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if path.is_dir():
        entries = []
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            entries.append((str(child.relative_to(path)), hashlib.sha256(child.read_bytes()).hexdigest()))
        return canonical_digest(tuple(entries))
    raise ValueError("hidden_material_source must be an existing file or directory")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
