"""Workspace orchestration for solver and verifier runs."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from tempfile import mkdtemp
from threading import Lock
from time import monotonic
from typing import Any, Mapping, Sequence
import hashlib
import json
import math
import os
import shutil
import subprocess
import warnings

from barcarolle._subprocess import run_bounded_process
from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    RuntimeConfig,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    is_full_git_object_id,
    make_check_command_digest,
    parse_utc_timestamp,
    utc_now_timestamp,
    validate_agent,
    validate_check,
    validate_runtime_config,
    validate_task,
    validate_workspace_config,
)
from barcarolle.verification import (
    VERIFICATION_ADAPTER_DIGEST,
    CheckOutcome,
    VerifierWorkspace,
    hidden_material_digest,
    prepare_verifier,
    verify_diff,
)


@dataclass(frozen=True)
class WorkspaceRef:
    path: Path
    role: str
    task_id: str
    base_commit: str
    workspace_digest: str
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

    def __post_init__(self) -> None:
        for field_name in ("preserve_stdout_stderr", "preserve_final_diff"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        for mode in (
            self.preserve_solver_workspace_summary,
            self.preserve_verifier_workspace_summary,
        ):
            if type(mode) is not str or mode not in {"never", "on_failure", "always"}:
                raise ValueError(
                    "workspace summary preservation must be never, on_failure, or always"
                )


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


@dataclass
class _WorkspacePhaseTimings:
    values: dict[str, float] = field(
        default_factory=lambda: {
            "solver_checkout_seconds": 0.0,
            "verifier_checkout_seconds": 0.0,
            "diff_replay_seconds": 0.0,
            "cleanup_seconds": 0.0,
        }
    )

    def record(self, phase: str, duration_seconds: float) -> None:
        self.values[phase] = self.values.get(phase, 0.0) + duration_seconds


@dataclass(frozen=True)
class _CheckMaterialBinding:
    check_command: tuple[str, ...]
    check_command_digest: str
    hidden_material_source: Path
    hidden_material_destination: Path


@dataclass(frozen=True)
class _AgentHarnessBinding:
    command: tuple[str, ...]
    execution_mode: str
    endpoint_harness_paths: tuple[Path, ...]


@dataclass(frozen=True)
class WorkspaceRunContext:
    """Immutable repository, Agent, and Check bindings for one run."""

    _repository_sources: tuple[tuple[str, Path], ...] = field(default=(), repr=False)
    _agent_harnesses: tuple[tuple[tuple[str, str, str], _AgentHarnessBinding], ...] = (
        field(default=(), repr=False)
    )
    _check_materials: tuple[tuple[tuple[str, str, str], _CheckMaterialBinding], ...] = (
        field(default=(), repr=False)
    )


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
_OPENAI_ENV_POLICY_VERSION = "openai_env_v1"
_OPENAI_BASE_URL_MARKER = "__BARCAROLLE_OPENAI_BASE_URL__"
_OPENAI_API_KEY_MARKER = "__BARCAROLLE_OPENAI_API_KEY_PRESENT__"
_BENCHMARK_CHECK_FAILURE_LABELS = frozenset(
    {
        "baseline_check_passed_without_diff",
        "check_command_mismatch",
        "check_process_containment_failed",
        "check_workspace_mismatch",
        "hidden_material_mismatch",
        "invalid_hidden_material_destination",
        "missing_check_command",
        "missing_verification_material",
        "not_verifier_workspace",
        "verifier_preparation_failed",
    }
)


def bind_repository_source(
    context: WorkspaceRunContext,
    workspace_config: WorkspaceConfig,
    repository_path: Path,
) -> WorkspaceRunContext:
    validation = validate_workspace_config(workspace_config)
    if not validation.ok:
        raise ValueError(f"workspace_config is invalid: {', '.join(validation.errors)}")
    source = repository_path.resolve()
    if not (source / ".git").exists():
        raise ValueError("repository_path must be a git repository checkout")
    key = workspace_config.repository_checkout_config_digest
    bindings = dict(context._repository_sources)
    existing = bindings.get(key)
    if existing is not None and existing != source:
        raise ValueError("repository source binding conflicts with run context")
    bindings[key] = source
    return replace(context, _repository_sources=tuple(sorted(bindings.items())))


def resolve_repository_commit(repository_path: Path, revision: str) -> str:
    source = repository_path.resolve()
    if not (source / ".git").exists():
        raise ValueError("repository_path must be a git repository checkout")
    if not revision or revision.startswith("-"):
        raise ValueError("repository revision must be a non-option value")
    object_format = _repository_object_format(source)
    commit = _run_git(
        source,
        ("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"),
    ).stdout.strip()
    expected_length = 40 if object_format == "sha1" else 64
    if not is_full_git_object_id(commit) or len(commit) != expected_length:
        raise RuntimeError("Git did not resolve revision to a full commit object ID")
    return commit


def bind_agent_harness(
    context: WorkspaceRunContext,
    agent: AgentRecord,
    command: Sequence[str],
    *,
    execution_mode: str | None = None,
    endpoint_harness_paths: Sequence[Path] = (),
) -> WorkspaceRunContext:
    agent_validation = validate_agent(agent)
    if not agent_validation.ok:
        raise ValueError(f"agent is invalid: {', '.join(agent_validation.errors)}")
    normalized = tuple(command)
    if not normalized:
        raise ValueError("agent harness command is required")
    if _agent_command_digest(normalized) != agent.harness_digest:
        raise ValueError("agent harness command digest does not match Agent harness")
    mode = execution_mode or "offline"
    if mode not in {"offline", "openai_paid"}:
        raise ValueError("execution_mode must be offline or openai_paid")
    paths = tuple(path.resolve() for path in endpoint_harness_paths)
    if mode == "offline":
        if agent.network_policy_digest != "offline":
            raise ValueError(
                "offline Agent network_policy_digest must be the literal 'offline'"
            )
        if paths:
            raise ValueError("offline Agent harness must not declare endpoint paths")
    elif not paths:
        raise ValueError("openai_paid Agent harness requires endpoint harness paths")
    else:
        command_paths = {argument for argument in normalized if argument}
        if not any(str(path) in command_paths for path in paths):
            raise ValueError(
                "openai_paid command must directly reference a declared harness path"
            )
        harness_content_digest(paths)
    key = _agent_key(agent)
    value = _AgentHarnessBinding(
        command=normalized,
        execution_mode=mode,
        endpoint_harness_paths=paths,
    )
    bindings = dict(context._agent_harnesses)
    existing = bindings.get(key)
    if existing is not None and existing != value:
        raise ValueError("Agent harness binding conflicts with run context")
    bindings[key] = value
    return replace(context, _agent_harnesses=tuple(sorted(bindings.items())))


def harness_content_digest(paths: Sequence[Path]) -> str:
    normalized = tuple(path.resolve() for path in paths)
    if not normalized:
        raise ValueError("harness content paths must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("harness content paths must not contain duplicates")
    digests: list[str] = []
    for path in normalized:
        if not path.is_file():
            raise ValueError("harness content path must be an existing file")
        digests.append(hashlib.sha256(path.read_bytes()).hexdigest())
    return canonical_digest({"file_sha256": tuple(sorted(digests))})


def openai_endpoint_digest(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if (
        not normalized
        or "\n" in normalized
        or "\r" in normalized
        or not normalized.startswith(("https://", "http://"))
    ):
        raise ValueError("OPENAI_BASE_URL must be a valid HTTP(S) base URL")
    return canonical_digest({"openai_base_url": normalized})


def make_openai_env_network_policy_digest(
    *,
    endpoint_digest: str,
    harness_digest: str,
    harness_content_digest: str,
) -> str:
    if not endpoint_digest or not harness_digest or not harness_content_digest:
        raise ValueError("OpenAI endpoint proof digests must not be empty")
    return canonical_digest(
        {
            "policy_version": _OPENAI_ENV_POLICY_VERSION,
            "endpoint_digest": endpoint_digest,
            "harness_digest": harness_digest,
            "harness_content_digest": harness_content_digest,
        }
    )


def resolve_openai_endpoint_digest(*, require_api_key: bool = False) -> str:
    base_url, api_key_present = _resolve_openai_environment(
        source_shell=require_api_key,
    )
    if not base_url:
        raise ValueError("OPENAI_BASE_URL is required for OpenAI benchmark calls")
    if require_api_key and not api_key_present:
        raise ValueError("OPENAI_API_KEY is required for OpenAI benchmark calls")
    return openai_endpoint_digest(base_url)


def bind_check_material(
    context: WorkspaceRunContext,
    check: CheckRecord,
    check_command: Sequence[str],
    hidden_material_source: Path,
    hidden_material_destination: Path = Path(".barcarolle/check_bundle"),
    *,
    check_manifest: Mapping[str, Any] | None = None,
) -> WorkspaceRunContext:
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
    if not hidden_material_source.exists() and not hidden_material_source.is_symlink():
        raise ValueError("hidden_material_source must exist")
    source_digest = hidden_material_digest(hidden_material_source)
    source = hidden_material_source.resolve()
    if source_digest != check.hidden_check_bundle_digest:
        raise ValueError("hidden material digest does not match check")
    key = _check_key(check)
    value = _CheckMaterialBinding(
        check_command=normalized_command,
        check_command_digest=make_check_command_digest(normalized_command),
        hidden_material_source=source,
        hidden_material_destination=hidden_material_destination,
    )
    bindings = dict(context._check_materials)
    existing = bindings.get(key)
    if existing is not None and existing != value:
        raise ValueError("Check material binding conflicts with run context")
    bindings[key] = value
    return replace(context, _check_materials=tuple(sorted(bindings.items())))


def preflight_run_bindings(
    context: WorkspaceRunContext,
    plans: Sequence[tuple[TaskRecord, CheckRecord, AgentRecord]],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> None:
    _validate_run_configs(workspace_config, runtime_config)
    source = dict(context._repository_sources).get(
        workspace_config.repository_checkout_config_digest
    )
    if source is None or not (source / ".git").exists():
        raise ValueError("repository source is not bound for workspace config")
    unique_checks: dict[tuple[str, str, str], CheckRecord] = {}
    unique_agents: dict[str, AgentRecord] = {}
    for task, check, agent in plans:
        _validate_preflight_plan(task, check, agent)
        unique_checks.setdefault(_check_key(check), check)
        unique_agents.setdefault(canonical_digest(agent), agent)
    for check in unique_checks.values():
        _validated_check_binding(check, context)
    _preflight_agent_bindings(context, tuple(unique_agents.values()))


def _validate_run_configs(
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


def _validate_preflight_plan(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> None:
    task_validation = validate_task(task)
    if not task_validation.ok:
        raise ValueError(f"task is invalid: {', '.join(task_validation.errors)}")
    check_validation = validate_check(check)
    if not check_validation.ok:
        raise ValueError(f"check is invalid: {', '.join(check_validation.errors)}")
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        raise ValueError("Task and Check do not match")
    agent_validation = validate_agent(agent)
    if not agent_validation.ok:
        raise ValueError(f"agent is invalid: {', '.join(agent_validation.errors)}")
    _validate_check_timeout(check)


def _preflight_agent_bindings(
    context: WorkspaceRunContext,
    agents: Sequence[AgentRecord],
) -> None:
    paid_endpoint_digest: str | None = None
    bindings = dict(context._agent_harnesses)
    for agent in agents:
        binding = bindings.get(_agent_key(agent))
        if binding is None:
            raise ValueError(f"Agent harness is not bound: {agent.agent_id}")
        if binding.execution_mode == "openai_paid" and paid_endpoint_digest is None:
            paid_endpoint_digest = resolve_openai_endpoint_digest(require_api_key=True)
        _validated_agent_binding(
            agent,
            context,
            endpoint_digest=paid_endpoint_digest,
        )


def check_execution_binding_digest(
    check: CheckRecord, context: WorkspaceRunContext
) -> str:
    binding = _validated_check_binding(check, context)
    return canonical_digest(
        {
            "binding_version": "builtin_check_binding_v1",
            "check_command_digest": binding.check_command_digest,
            "hidden_material_destination": binding.hidden_material_destination.as_posix(),
            "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
            "verification_adapter_digest": VERIFICATION_ADAPTER_DIGEST,
        }
    )


def create_solver_workspace(
    task: TaskRecord,
    workspace_config: WorkspaceConfig,
    context: WorkspaceRunContext,
    *,
    _phase_timings: _WorkspacePhaseTimings | None = None,
) -> WorkspaceRef:
    validation = validate_task(task)
    if not validation.ok:
        raise ValueError(f"task is invalid: {', '.join(validation.errors)}")
    checkout_started = monotonic()
    try:
        path = _checkout_repository(
            task, workspace_config, context, prefix="barcarolle-solver-"
        )
    finally:
        if _phase_timings is not None:
            _phase_timings.record(
                "solver_checkout_seconds", monotonic() - checkout_started
            )
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
    if workspace.task_id != task.task_id or workspace.role not in {
        "solver",
        "verifier",
    }:
        raise ValueError("workspace does not match Task")
    _validate_solver_material_refs(workspace.path, task)


def invoke_agent(
    solver_workspace: WorkspaceRef,
    task: TaskRecord,
    agent: AgentRecord,
    runtime_config: RuntimeConfig,
    context: WorkspaceRunContext,
) -> AgentRunOutcome:
    if solver_workspace.role != "solver" or solver_workspace.task_id != task.task_id:
        return AgentRunOutcome("invalid", 0.0, {}, "", "solver_workspace_task_mismatch")
    binding = _validated_agent_binding(agent, context)
    command = binding.command
    usage_path = solver_workspace.path / _USAGE_FILE
    usage_path.unlink(missing_ok=True)
    start = monotonic()
    try:
        completed = run_bounded_process(
            command,
            cwd=solver_workspace.path,
            timeout_seconds=runtime_config.timeout_seconds,
        )
    except OSError:
        return AgentRunOutcome(
            "invalid", monotonic() - start, {}, "", "agent_launch_error"
        )
    if completed.containment_error is not None:
        return AgentRunOutcome(
            terminal_status="invalid",
            duration_seconds=monotonic() - start,
            usage={},
            safe_output_digest=completed.output_digest,
            failure_label="agent_process_containment_failed",
            stdout=completed.stdout.text,
            stderr=completed.stderr.text,
        )
    if completed.timed_out:
        return AgentRunOutcome(
            terminal_status="timeout",
            duration_seconds=monotonic() - start,
            usage={},
            safe_output_digest=completed.output_digest,
            failure_label="agent_timeout",
            stdout=completed.stdout.text,
            stderr=completed.stderr.text,
        )
    try:
        usage = _load_agent_usage(usage_path)
    except (OSError, ValueError):
        usage = {}
    terminal_status = "completed" if completed.returncode == 0 else "error"
    return AgentRunOutcome(
        terminal_status=terminal_status,
        duration_seconds=monotonic() - start,
        usage=usage,
        safe_output_digest=completed.output_digest,
        failure_label=None if completed.returncode == 0 else "agent_failed",
        stdout=completed.stdout.text,
        stderr=completed.stderr.text,
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
            raise ValueError(
                f"Agent usage value for {key} must be finite and nonnegative"
            ) from exc
        if not math.isfinite(numeric_item) or numeric_item < 0.0:
            raise ValueError(
                f"Agent usage value for {key} must be finite and nonnegative"
            )
    return value


def capture_diff(solver_workspace: WorkspaceRef) -> CapturedDiff:
    if solver_workspace.role != "solver":
        raise ValueError("diff capture requires a solver workspace")
    if not _is_git_checkout(solver_workspace.path):
        raise ValueError("solver workspace must be a git checkout")
    _run_git(
        solver_workspace.path,
        ("add", "--intent-to-add", "--force", "--", *_CAPTURE_PATHSPEC),
    )
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
    return CapturedDiff(
        diff_text=diff_text,
        diff_digest=hashlib.sha256(diff_text.encode("utf-8")).hexdigest(),
    )


def create_verifier_workspace(
    task: TaskRecord,
    workspace_config: WorkspaceConfig,
    context: WorkspaceRunContext,
    *,
    _phase_timings: _WorkspacePhaseTimings | None = None,
) -> WorkspaceRef:
    validation = validate_task(task)
    if not validation.ok:
        raise ValueError(f"task is invalid: {', '.join(validation.errors)}")
    checkout_started = monotonic()
    try:
        path = _checkout_repository(
            task, workspace_config, context, prefix="barcarolle-verifier-"
        )
    finally:
        if _phase_timings is not None:
            _phase_timings.record(
                "verifier_checkout_seconds", monotonic() - checkout_started
            )
    try:
        _exclude_benchmark_material(path)
        return WorkspaceRef(
            path=path,
            role="verifier",
            task_id=task.task_id,
            base_commit=task.base_commit,
            workspace_digest=_workspace_digest(
                path, task, workspace_config, "verifier"
            ),
        )
    except BaseException:
        _discard_owned_workspace_path(path)
        raise


def cleanup_workspace(workspace: WorkspaceRef) -> None:
    """Remove a workspace returned by a low-level create function."""
    _cleanup_workspaces(workspace)


def apply_diff(
    verifier_workspace: WorkspaceRef, diff: CapturedDiff
) -> DiffReplayOutcome:
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
    context: WorkspaceRunContext,
) -> CheckOutcome:
    if verifier_workspace.role != "verifier":
        return CheckOutcome("invalid", "not_verifier_workspace", None, False, 0.0, "")
    if verifier_workspace.task_id != check.task_id:
        return CheckOutcome("invalid", "check_workspace_mismatch", None, False, 0.0, "")
    binding = _material_binding(check, verifier_workspace, context)
    if binding is None:
        return CheckOutcome(
            "invalid", "missing_verification_material", None, False, 0.0, ""
        )
    if not _is_reserved_hidden_material_destination(
        binding.hidden_material_destination
    ):
        return CheckOutcome(
            "invalid", "invalid_hidden_material_destination", None, False, 0.0, ""
        )
    verifier_ref = VerifierWorkspace(
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
        return CheckOutcome(
            "invalid", _preparation_failure_label(str(exc)), None, False, 0.0, ""
        )
    return verify_diff(check, prepared, runtime_config)


def run_agent_on_task(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    context: WorkspaceRunContext,
) -> WorkspaceRunRecord:
    return run_agent_on_task_with_artifacts(
        task, check, agent, workspace_config, runtime_config, context
    ).run


def run_agent_on_task_with_artifacts(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    context: WorkspaceRunContext,
    artifact_config: WorkspaceArtifactConfig | None = None,
) -> WorkspaceRunResult:
    workspace_started = monotonic()
    phase_timings = _WorkspacePhaseTimings()
    started_at = _now()
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        run = _invalid_run_record(
            task=task,
            check=check,
            agent=agent,
            started_at=started_at,
            workspace_started=workspace_started,
            phase_timings=phase_timings,
            failure_label="task_check_mismatch",
            invalid_owner="benchmark",
        )
        return _workspace_run_result(run, artifact_config, None, None, None, None)
    preflight_run_bindings(
        context,
        ((task, check, agent),),
        workspace_config,
        runtime_config,
    )
    solver_workspace: WorkspaceRef | None = None
    verifier_workspace: WorkspaceRef | None = None
    try:
        try:
            solver_workspace = create_solver_workspace(
                task,
                workspace_config,
                context,
                _phase_timings=phase_timings,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            run = _invalid_run_record(
                task=task,
                check=check,
                agent=agent,
                started_at=started_at,
                workspace_started=workspace_started,
                phase_timings=phase_timings,
                failure_label=_workspace_failure_label(str(exc)),
                invalid_owner="benchmark",
            )
            return _workspace_run_result(run, artifact_config, None, None, None, None)
        agent_outcome = invoke_agent(
            solver_workspace, task, agent, runtime_config, context
        )
        if agent_outcome.failure_label == "agent_process_containment_failed":
            run = _invalid_run_record(
                task=task,
                check=check,
                agent=agent,
                started_at=started_at,
                workspace_started=workspace_started,
                phase_timings=phase_timings,
                failure_label="agent_process_containment_failed",
                invalid_owner="benchmark",
                solver_workspace_digest=solver_workspace.workspace_digest,
                usage=agent_outcome.usage,
                agent_seconds=agent_outcome.duration_seconds,
            )
            return _workspace_run_result(
                run, artifact_config, None, agent_outcome, solver_workspace, None
            )
        try:
            diff = capture_diff(solver_workspace)
        except (OSError, RuntimeError, ValueError):
            run = _invalid_run_record(
                task=task,
                check=check,
                agent=agent,
                started_at=started_at,
                workspace_started=workspace_started,
                phase_timings=phase_timings,
                failure_label="agent_workspace_corrupted",
                invalid_owner="agent",
                solver_workspace_digest=solver_workspace.workspace_digest,
                usage=agent_outcome.usage,
                agent_seconds=agent_outcome.duration_seconds,
            )
            return _workspace_run_result(
                run, artifact_config, None, agent_outcome, solver_workspace, None
            )
        try:
            verifier_workspace = create_verifier_workspace(
                task,
                workspace_config,
                context,
                _phase_timings=phase_timings,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            replay = DiffReplayOutcome(
                "invalid", _workspace_failure_label(str(exc)), ""
            )
            check_outcome = CheckOutcome(
                "invalid", replay.failure_label, None, False, 0.0, ""
            )
            run = _workspace_run_record(
                task=task,
                check=check,
                agent=agent,
                solver_workspace_digest=solver_workspace.workspace_digest,
                verifier_workspace_digest=_synthetic_workspace_digest(
                    task, "verifier", replay.failure_label or "verifier_workspace_error"
                ),
                agent_outcome=agent_outcome,
                diff=diff,
                replay=replay,
                check_outcome=check_outcome,
                started_at=started_at,
                finished_at=_now(),
                workspace_started=workspace_started,
                phase_timings=phase_timings,
            )
            return _workspace_run_result(
                run, artifact_config, diff, agent_outcome, solver_workspace, None
            )
        replay_started = monotonic()
        try:
            replay = apply_diff(verifier_workspace, diff)
        finally:
            phase_timings.record("diff_replay_seconds", monotonic() - replay_started)
        if replay.replay_status == "applied":
            check_outcome = verify_agent_diff(
                verifier_workspace, check, runtime_config, context
            )
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
            check_outcome = CheckOutcome(
                "invalid", replay.failure_label, None, False, 0.0, ""
            )
        check_execution_failure_agent_owned = check_outcome.failure_label in {
            "check_invalid",
            "check_launch_error",
        } and _agent_changed_check_command_path(
            check, verifier_workspace, diff, context
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
            workspace_started=workspace_started,
            phase_timings=phase_timings,
            check_execution_failure_agent_owned=check_execution_failure_agent_owned,
        )
        return _workspace_run_result(
            run,
            artifact_config,
            diff,
            agent_outcome,
            solver_workspace,
            verifier_workspace,
        )
    finally:
        cleanup_started = monotonic()
        cleanup_error: RuntimeError | None = None
        try:
            _cleanup_workspaces(verifier_workspace, solver_workspace)
        except RuntimeError as exc:
            cleanup_error = exc
        finally:
            phase_timings.record("cleanup_seconds", monotonic() - cleanup_started)
        if cleanup_error is not None:
            warnings.warn(str(cleanup_error), RuntimeWarning, stacklevel=2)


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
    try:
        artifacts = _preserve_run_artifacts(
            artifact_config,
            run,
            diff,
            agent_outcome,
            solver_workspace,
            verifier_workspace,
        )
    except OSError as exc:
        warnings.warn(
            f"workspace artifact preservation failed ({type(exc).__name__})",
            RuntimeWarning,
            stacklevel=2,
        )
        return WorkspaceRunResult(run=run)
    return WorkspaceRunResult(run=run, artifacts=artifacts)


def _preserve_run_artifacts(
    config: WorkspaceArtifactConfig,
    run: WorkspaceRunRecord,
    diff: CapturedDiff | None,
    agent_outcome: AgentRunOutcome | None,
    solver_workspace: WorkspaceRef | None,
    verifier_workspace: WorkspaceRef | None,
) -> WorkspaceArtifactManifest:
    artifact_refs: list[WorkspaceArtifactRef] = []
    run_ref = run.workspace_run_id
    if config.preserve_final_diff and diff is not None:
        artifact_refs.append(
            _write_text_artifact(
                config.output_root, run_ref, "final.diff", "final_diff", diff.diff_text
            )
        )
    if config.preserve_stdout_stderr and agent_outcome is not None:
        artifact_refs.append(
            _write_text_artifact(
                config.output_root,
                run_ref,
                "stdout.txt",
                "agent_stdout",
                agent_outcome.stdout,
            )
        )
        artifact_refs.append(
            _write_text_artifact(
                config.output_root,
                run_ref,
                "stderr.txt",
                "agent_stderr",
                agent_outcome.stderr,
            )
        )
    if solver_workspace is not None and _should_preserve_workspace_summary(
        config.preserve_solver_workspace_summary, run
    ):
        artifact_refs.append(
            _write_text_artifact(
                config.output_root,
                run_ref,
                "solver-workspace-summary.json",
                "solver_workspace_summary",
                _workspace_summary_json(solver_workspace, private=False),
            )
        )
    if verifier_workspace is not None and _should_preserve_workspace_summary(
        config.preserve_verifier_workspace_summary, run
    ):
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
    manifest_path.write_text(
        json.dumps(manifest_payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return WorkspaceArtifactManifest(
        manifest_ref=manifest_ref, artifact_refs=tuple(artifact_refs)
    )


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


def _checkout_repository(
    task: TaskRecord,
    workspace_config: WorkspaceConfig,
    context: WorkspaceRunContext,
    *,
    prefix: str,
) -> Path:
    source = dict(context._repository_sources).get(
        workspace_config.repository_checkout_config_digest
    )
    if source is None:
        raise ValueError("repository source is not bound for workspace config")
    path = Path(mkdtemp(prefix=prefix))
    _register_owned_workspace_path(path)
    try:
        object_format = _repository_object_format(source)
        _run_git(path, ("init", "--quiet", f"--object-format={object_format}"))
        _run_git(
            path,
            ("fetch", "--quiet", "--no-tags", str(source), task.base_commit),
        )
        _run_git(path, ("checkout", "--quiet", "--detach", "FETCH_HEAD"))
        if _head_commit(path) != task.base_commit:
            raise RuntimeError("checked-out HEAD does not match Task base_commit")
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
    (material_dir / "solver-visible-task.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )
    (material_dir / "TASK.md").write_text(
        _solver_visible_task_markdown(task), encoding="utf-8"
    )


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
        raise ValueError(
            f"solver material reference could not be resolved: {ref}"
        ) from exc
    if not material_resolved.is_relative_to(workspace_root):
        raise ValueError(
            f"solver material reference resolves outside the workspace: {ref}"
        )
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


def _workspace_digest(
    path: Path, task: TaskRecord, workspace_config: WorkspaceConfig, role: str
) -> str:
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
    workspace_started: float,
    phase_timings: _WorkspacePhaseTimings,
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
        latency=_workspace_latency(
            workspace_started,
            phase_timings=phase_timings,
            agent_seconds=agent_outcome.duration_seconds,
            verification_seconds=check_outcome.duration_seconds,
        ),
        started_at=started_at,
        finished_at=finished_at,
    )


def _invalid_run_record(
    *,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    started_at: str,
    workspace_started: float,
    phase_timings: _WorkspacePhaseTimings,
    failure_label: str,
    invalid_owner: str,
    solver_workspace_digest: str | None = None,
    usage: Mapping[str, Any] | None = None,
    agent_seconds: float = 0.0,
    verification_seconds: float = 0.0,
) -> WorkspaceRunRecord:
    finished_at = _now()
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace_run_{canonical_digest((task.task_id, check.check_id, agent.agent_id, failure_label, started_at))}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest=solver_workspace_digest
        or _synthetic_workspace_digest(task, "solver", failure_label),
        verifier_workspace_digest=_synthetic_workspace_digest(
            task, "verifier", failure_label
        ),
        terminal_status="invalid",
        diff_digest=_EMPTY_DIFF_DIGEST,
        replay_status="skipped",
        check_outcome="invalid",
        invalid_owner=invalid_owner,
        failure_label=failure_label,
        usage=usage or {},
        latency=_workspace_latency(
            workspace_started,
            phase_timings=phase_timings,
            agent_seconds=agent_seconds,
            verification_seconds=verification_seconds,
        ),
        started_at=started_at,
        finished_at=finished_at,
    )


def _workspace_latency(
    workspace_started: float,
    *,
    phase_timings: _WorkspacePhaseTimings,
    agent_seconds: float,
    verification_seconds: float,
) -> Mapping[str, float]:
    phase_timings.values.update(
        {
            "workspace_seconds": monotonic() - workspace_started,
            "agent_seconds": agent_seconds,
            "verification_seconds": verification_seconds,
        }
    )
    return phase_timings.values


def _material_binding(
    check: CheckRecord,
    verifier_workspace: WorkspaceRef,
    context: WorkspaceRunContext,
) -> _CheckMaterialBinding | None:
    if (
        verifier_workspace.check_command
        and verifier_workspace.hidden_material_source is not None
    ):
        command_digest = make_check_command_digest(verifier_workspace.check_command)
        if command_digest != check.check_manifest_digest:
            return None
        return _CheckMaterialBinding(
            check_command=verifier_workspace.check_command,
            check_command_digest=command_digest,
            hidden_material_source=verifier_workspace.hidden_material_source,
            hidden_material_destination=verifier_workspace.hidden_material_destination
            or Path(".barcarolle/check_bundle"),
        )
    return dict(context._check_materials).get(_check_key(check))


def _validated_check_binding(
    check: CheckRecord, context: WorkspaceRunContext
) -> _CheckMaterialBinding:
    binding = dict(context._check_materials).get(_check_key(check))
    if binding is None:
        raise ValueError(f"Check material is not bound: {check.check_id}")
    if make_check_command_digest(binding.check_command) != binding.check_command_digest:
        raise ValueError(f"Check command binding changed: {check.check_id}")
    if not _is_reserved_hidden_material_destination(
        binding.hidden_material_destination
    ):
        raise ValueError(f"Check hidden destination is invalid: {check.check_id}")
    if (
        not binding.hidden_material_source.exists()
        or hidden_material_digest(binding.hidden_material_source)
        != check.hidden_check_bundle_digest
    ):
        raise ValueError(f"Check hidden material changed: {check.check_id}")
    return binding


def _validated_agent_binding(
    agent: AgentRecord,
    context: WorkspaceRunContext,
    *,
    endpoint_digest: str | None = None,
) -> _AgentHarnessBinding:
    agent_validation = validate_agent(agent)
    if not agent_validation.ok:
        raise ValueError(f"agent is invalid: {', '.join(agent_validation.errors)}")
    binding = dict(context._agent_harnesses).get(_agent_key(agent))
    if binding is None:
        raise ValueError(f"Agent harness is not bound: {agent.agent_id}")
    if _agent_command_digest(binding.command) != agent.harness_digest:
        raise ValueError(f"Agent harness command changed: {agent.agent_id}")
    if binding.execution_mode == "offline":
        if agent.network_policy_digest != "offline":
            raise ValueError(f"offline Agent network policy changed: {agent.agent_id}")
        return binding
    _validate_model_resolution_scope_for_paid_execution(agent)
    current_endpoint_digest = endpoint_digest or resolve_openai_endpoint_digest(
        require_api_key=True
    )
    current_harness_content_digest = harness_content_digest(
        binding.endpoint_harness_paths
    )
    expected_policy_digest = make_openai_env_network_policy_digest(
        endpoint_digest=current_endpoint_digest,
        harness_digest=agent.harness_digest,
        harness_content_digest=current_harness_content_digest,
    )
    if agent.network_policy_digest != expected_policy_digest:
        raise ValueError(
            f"OpenAI endpoint or harness proof does not match Agent: {agent.agent_id}"
        )
    return binding


def _validate_model_resolution_scope_for_paid_execution(agent: AgentRecord) -> None:
    if agent.model_snapshot_id is not None:
        return
    assert agent.model_resolution_scope_started_at is not None
    assert agent.model_resolution_scope_ended_at is not None
    now = parse_utc_timestamp(utc_now_timestamp())
    started_at = parse_utc_timestamp(agent.model_resolution_scope_started_at)
    ended_at = parse_utc_timestamp(agent.model_resolution_scope_ended_at)
    if not started_at <= now < ended_at:
        raise ValueError(
            f"model resolution scope is not active for Agent: {agent.agent_id}"
        )


def _validate_check_timeout(check: CheckRecord) -> None:
    if "timeout_seconds" not in check.resource_limits:
        return
    timeout = check.resource_limits["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise ValueError(
            f"Check timeout_seconds must be a positive integer: {check.check_id}"
        )


def _resolve_openai_environment(*, source_shell: bool) -> tuple[str, bool]:
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    api_key_present = bool(os.environ.get("OPENAI_API_KEY"))
    if base_url and (api_key_present or not source_shell):
        return base_url, api_key_present
    completed = subprocess.run(
        (
            "zsh",
            "-lc",
            (
                'source "$HOME/.zshrc" >/dev/null 2>&1; '
                f'printf "{_OPENAI_BASE_URL_MARKER}%s\\n" "${{OPENAI_BASE_URL-}}"; '
                f'if [[ -n "${{OPENAI_API_KEY-}}" ]]; then printf "{_OPENAI_API_KEY_MARKER}1\\n"; '
                f'else printf "{_OPENAI_API_KEY_MARKER}0\\n"; fi'
            ),
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    sourced_base_url = ""
    sourced_api_key_present = False
    for line in completed.stdout.splitlines():
        if line.startswith(_OPENAI_BASE_URL_MARKER):
            sourced_base_url = line.removeprefix(_OPENAI_BASE_URL_MARKER)
        elif line.startswith(_OPENAI_API_KEY_MARKER):
            sourced_api_key_present = line.removeprefix(_OPENAI_API_KEY_MARKER) == "1"
    return sourced_base_url, sourced_api_key_present


def _agent_changed_check_command_path(
    check: CheckRecord,
    verifier_workspace: WorkspaceRef,
    diff: CapturedDiff,
    context: WorkspaceRunContext,
) -> bool:
    binding = _material_binding(check, verifier_workspace, context)
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
        elif position == 0 and not any(
            separator in command_arg for separator in ("/", "\\")
        ):
            continue
        if command_path.as_posix() in changed_paths:
            return True
    return False


def _agent_key(agent: AgentRecord) -> tuple[str, str, str]:
    return (agent.agent_id, agent.agent_manifest_digest, agent.harness_digest)


def _check_key(check: CheckRecord) -> tuple[str, str, str]:
    return (
        check.check_id,
        check.check_manifest_digest,
        check.hidden_check_bundle_digest,
    )


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
    if agent_outcome.failure_label == "agent_process_containment_failed":
        return "benchmark"
    if replay.replay_status == "failed":
        return "agent"
    if replay.replay_status == "invalid":
        return "benchmark"
    if check_outcome.outcome == "invalid":
        if check_outcome.failure_label in {"check_invalid", "check_launch_error"}:
            return "agent" if check_execution_failure_agent_owned else "benchmark"
        return (
            "benchmark"
            if check_outcome.failure_label in _BENCHMARK_CHECK_FAILURE_LABELS
            else "agent"
        )
    if agent_outcome.terminal_status == "invalid":
        return "agent"
    return "benchmark"


def _failure_label(
    agent_outcome: AgentRunOutcome,
    replay: DiffReplayOutcome,
    check_outcome: CheckOutcome,
) -> str | None:
    if agent_outcome.failure_label == "agent_process_containment_failed":
        return agent_outcome.failure_label
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
        and len(destination.parts) >= 2
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
            raise ValueError(
                "captured diff path inspection returned malformed rename output"
            )
        paths.extend((entries[index + 1], entries[index + 2]))
        index += 3
    return tuple(paths)


def _synthetic_workspace_digest(task: TaskRecord, role: str, reason: str) -> str:
    return canonical_digest(
        {
            "role": role,
            "task_id": task.task_id,
            "base_commit": task.base_commit,
            "not_created": reason,
        }
    )


def _exclude_benchmark_material(path: Path) -> None:
    exclude_path = Path(
        _run_git(path, ("rev-parse", "--git-path", "info/exclude")).stdout.strip()
    )
    if not exclude_path.is_absolute():
        exclude_path = path / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    if ".barcarolle/" not in existing:
        exclude_path.write_text(
            f"{existing.rstrip()}\n.barcarolle/\n", encoding="utf-8"
        )


def _head_commit(path: Path) -> str:
    return _run_git(path, ("rev-parse", "HEAD")).stdout.strip()


def _repository_object_format(path: Path) -> str:
    object_format = _run_git(path, ("rev-parse", "--show-object-format")).stdout.strip()
    if object_format not in {"sha1", "sha256"}:
        raise RuntimeError(
            f"unsupported Git object format: {object_format or 'unknown'}"
        )
    return object_format


def _is_git_checkout(path: Path) -> bool:
    return (path / ".git").exists()


def _run_git(path: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return _run(("git", *args), cwd=path)


def _run(
    command: Sequence[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            (completed.stderr or completed.stdout or "command failed").strip()
        )
    return completed


def _safe_output_digest(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    return hashlib.sha256(
        (_normalize_output(stdout) + "\n" + _normalize_output(stderr)).encode("utf-8")
    ).hexdigest()


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _agent_command_digest(agent_command: Sequence[str]) -> str:
    return canonical_digest({"agent_command": tuple(agent_command)})


def _now() -> str:
    return utc_now_timestamp()
