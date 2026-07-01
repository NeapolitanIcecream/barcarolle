from dataclasses import replace
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pytest

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    RuntimeConfig,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    validate_workspace_run,
)
from barcarolle.workspace import (
    CapturedDiff,
    WorkspaceArtifactConfig,
    WorkspaceRef,
    apply_diff,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    capture_diff,
    create_solver_workspace,
    create_verifier_workspace,
    invoke_agent,
    run_agent_on_task,
    run_agent_on_task_with_artifacts,
    verify_agent_diff,
)


def test_create_solver_workspace_clones_base_commit_and_writes_only_solver_visible_material(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config)
    material_dir = workspace.path / ".barcarolle"
    material = (material_dir / "solver-visible-task.json").read_text(encoding="utf-8")
    task_markdown = (material_dir / "TASK.md").read_text(encoding="utf-8")

    assert workspace.role == "solver"
    assert _git(workspace.path, "rev-parse", "HEAD").stdout.strip() == base_commit
    assert (workspace.path / "README.md").read_text(encoding="utf-8") == "base\n"
    assert "solver_material_refs" in material
    assert "TASK.md" in material
    assert "README.md" in task_markdown
    assert "base" in task_markdown
    assert "hidden" not in material.lower()
    assert "oracle" not in material.lower()
    assert "hidden" not in task_markdown.lower()
    assert "oracle" not in task_markdown.lower()


def test_create_solver_workspace_does_not_dereference_solver_material_symlink(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    outside_material = tmp_path / "outside-private.txt"
    outside_material.write_text("private check content\n", encoding="utf-8")
    symlink_ref = repo / "statement.md"
    symlink_ref.symlink_to(outside_material)
    _git(repo, "add", "statement.md")
    _git(repo, "commit", "-m", "add symlink solver material")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = replace(_task(base_commit=base_commit), solver_material_refs=("statement.md",))
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config)
    task_markdown = (workspace.path / ".barcarolle" / "TASK.md").read_text(encoding="utf-8")

    assert "Reference uses a symlink and was not copied." in task_markdown
    assert "private check content" not in task_markdown


def test_invoke_agent_runs_bound_harness_command_and_digest_safe_output(tmp_path: Path) -> None:
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('done.txt').write_text('ok'); print('done')")
    agent = _agent(agent_command)
    bind_agent_harness(agent, agent_command)
    workspace = WorkspaceRef(path=tmp_path, role="solver", task_id="task", base_commit="commit", workspace_digest="workspace")

    outcome = invoke_agent(workspace, _task(), agent, _runtime())

    assert outcome.terminal_status == "completed"
    assert outcome.safe_output_digest
    assert (tmp_path / "done.txt").read_text(encoding="utf-8") == "ok"


def test_bind_agent_harness_rejects_command_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="harness command digest"):
        bind_agent_harness(_agent(), (sys.executable, "-c", "print('different harness')"))


def test_capture_diff_reads_git_worktree_and_includes_untracked_files(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config)
    (workspace.path / "new.txt").write_text("new file\n", encoding="utf-8")
    (workspace.path / ".barcarolle/internal.txt").write_text("benchmark side data\n", encoding="utf-8")

    diff = capture_diff(workspace)

    assert "diff --git a/new.txt b/new.txt" in diff.diff_text
    assert "+new file" in diff.diff_text
    assert ".barcarolle" not in diff.diff_text
    assert diff.diff_digest == hashlib.sha256(diff.diff_text.encode("utf-8")).hexdigest()


def test_apply_diff_replays_captured_diff_in_fresh_verifier_checkout(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    solver = create_solver_workspace(task, workspace_config)
    (solver.path / "new.txt").write_text("agent edit\n", encoding="utf-8")
    diff = capture_diff(solver)
    verifier = create_verifier_workspace(task, workspace_config)

    replay = apply_diff(verifier, diff)

    assert replay.replay_status == "applied"
    assert (verifier.path / "new.txt").read_text(encoding="utf-8") == "agent edit\n"


def test_verify_agent_diff_delegates_to_verification_with_bound_material(tmp_path: Path) -> None:
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "from pathlib import Path; assert Path('.barcarolle/check_bundle').exists()")
    check = _check(command=command, hidden=hidden)
    bind_check_material(check, command, hidden)
    workspace = WorkspaceRef(path=tmp_path, role="verifier", task_id="task", base_commit="commit", workspace_digest="workspace")

    outcome = verify_agent_diff(workspace, check, _runtime())

    assert outcome.outcome == "pass"
    assert (tmp_path / ".barcarolle/check_bundle").read_text(encoding="utf-8") == "private oracle"


def test_run_agent_on_task_executes_scoreable_workspace_path_and_returns_valid_record(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8'); "
        "assert 'hidden' not in Path('.barcarolle/solver-visible-task.json').read_text().lower()",
    )
    agent = _agent(agent_command)
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "assert Path('new.txt').read_text(encoding='utf-8') == 'agent edit\\n'; "
        "assert Path('.barcarolle/check_bundle').read_text(encoding='utf-8') == 'private oracle'",
    )
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"
    assert record.invalid_owner is None
    assert record.failure_label is None
    assert record.diff_digest != hashlib.sha256(b"").hexdigest()


def test_run_agent_on_task_with_artifacts_preserves_relative_run_outputs(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; import sys; "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8'); "
        "print('hello stdout'); print('hello stderr', file=sys.stderr)",
    )
    agent = _agent(agent_command)
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; assert Path('new.txt').read_text(encoding='utf-8') == 'agent edit\\n'",
    )
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(
        output_root=tmp_path / "artifacts",
        preserve_solver_workspace_summary="always",
        preserve_verifier_workspace_summary="always",
    )

    result = run_agent_on_task_with_artifacts(task, check, agent, workspace_config, _runtime(), artifact_config)

    assert result.run.terminal_status == "passed"
    assert result.artifacts is not None
    assert Path(result.artifacts.manifest_ref).is_absolute() is False
    refs = {artifact.kind: artifact for artifact in result.artifacts.artifact_refs}
    assert set(refs) == {
        "agent_stderr",
        "agent_stdout",
        "final_diff",
        "solver_workspace_summary",
        "verifier_workspace_summary",
    }
    for artifact in result.artifacts.artifact_refs:
        assert Path(artifact.ref).is_absolute() is False
        assert str(tmp_path) not in artifact.ref
        assert (artifact_config.output_root / artifact.ref).exists()
        assert artifact.digest
    assert "hello stdout" in (artifact_config.output_root / refs["agent_stdout"].ref).read_text(encoding="utf-8")
    assert "hello stderr" in (artifact_config.output_root / refs["agent_stderr"].ref).read_text(encoding="utf-8")
    assert "new.txt" in (artifact_config.output_root / refs["final_diff"].ref).read_text(encoding="utf-8")
    assert refs["verifier_workspace_summary"].private is True
    solver_summary = json.loads((artifact_config.output_root / refs["solver_workspace_summary"].ref).read_text(encoding="utf-8"))
    assert solver_summary["artifact_class"] == "solver"
    assert "private oracle" not in json.dumps(solver_summary)
    manifest = json.loads((artifact_config.output_root / result.artifacts.manifest_ref).read_text(encoding="utf-8"))
    assert manifest["workspace_run_id"] == result.run.workspace_run_id
    assert str(tmp_path) not in json.dumps(manifest)


def test_run_agent_on_task_replays_and_verifies_diff_after_nonzero_agent_exit(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('agent edit\\n', encoding='utf-8'); raise SystemExit(1)",
    )
    agent = _agent(agent_command)
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; assert Path('new.txt').read_text(encoding='utf-8') == 'agent edit\\n'",
    )
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "error"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"
    assert record.failure_label == "agent_failed"


def test_run_agent_on_task_normalizes_diff_capture_failure(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; import shutil; shutil.rmtree('.git'); Path('new.txt').write_text('agent edit\\n')",
    )
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "diff_capture_failed"
    assert record.replay_status == "skipped"


def test_run_agent_on_task_rejects_task_check_mismatch_before_agent_runs(tmp_path: Path) -> None:
    marker = tmp_path / "agent-ran.txt"
    agent_command = (sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')")
    agent = _agent(agent_command)
    bind_agent_harness(agent, agent_command)
    check = _check(task_id="other-task")

    record = run_agent_on_task(_task(), check, agent, _workspace_config(tmp_path), _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "task_check_mismatch"
    assert not marker.exists()


def test_apply_diff_reports_missing_git_checkout_for_nonempty_diff(tmp_path: Path) -> None:
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")

    replay = apply_diff(workspace, CapturedDiff("diff --git a/a b/a\n", "digest"))

    assert replay.replay_status == "invalid"
    assert replay.failure_label == "missing_git_checkout"


def test_verify_agent_diff_returns_invalid_when_material_is_missing(tmp_path: Path) -> None:
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")

    outcome = verify_agent_diff(workspace, _check(), _runtime())

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "missing_verification_material"


def _make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "barcarolle@example.invalid")
    _git(repo, "config", "user.name", "Barcarolle Tests")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "README.md").write_text("future\n", encoding="utf-8")
    _git(repo, "commit", "-am", "future")
    return repo, base_commit


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _task(base_commit: str = "commit") -> TaskRecord:
    return TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit=base_commit,
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-02T00:00:00Z",
        certified_at="2026-01-03T00:00:00Z",
        solver_material_digest="solver-material",
        solver_material_refs=("README.md",),
        check_ids=("check",),
        cluster_id="cluster",
    )


def _check(
    command: tuple[str, ...] = (sys.executable, "-c", "print('ok')"),
    hidden: Path | None = None,
    task_id: str = "task",
) -> CheckRecord:
    hidden_digest = hashlib.sha256(hidden.read_bytes()).hexdigest() if hidden is not None else hashlib.sha256(b"private oracle").hexdigest()
    return CheckRecord(
        check_id="check",
        task_id=task_id,
        check_type="pytest",
        check_manifest_digest=canonical_digest({"check_command": command}),
        hidden_check_bundle_digest=hidden_digest,
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at="2026-01-02T00:00:00Z",
        certified_at="2026-01-03T00:00:00Z",
    )


def _agent(command: tuple[str, ...] | None = None) -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        model_snapshot_id="model",
        harness_digest=canonical_digest({"agent_command": command}) if command is not None else "harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _workspace_config(repo: Path) -> WorkspaceConfig:
    return WorkspaceConfig(
        workspace_config_id=f"workspace-config-{hashlib.sha256(str(repo).encode('utf-8')).hexdigest()}",
        repository_checkout_config_digest=canonical_digest({"repository_path": str(repo)}),
        submodule_state_digest="submodules",
        base_image_digest="image",
        dependency_lock_digest="lock",
    )


def _runtime() -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id="runtime",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        timeout_seconds=5,
        hardware_profile_digest=None,
    )
