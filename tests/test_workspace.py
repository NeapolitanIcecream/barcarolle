from dataclasses import replace
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import pytest

from barcarolle import workspace as workspace_module
from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    RuntimeConfig,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    make_solver_material_digest,
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
    cleanup_workspace,
    create_solver_workspace,
    create_verifier_workspace,
    invoke_agent,
    run_agent_on_task,
    run_agent_on_task_with_artifacts,
    verify_agent_diff,
)


@pytest.fixture
def managed_workspaces():
    workspaces = []
    yield workspaces
    for workspace in reversed(workspaces):
        cleanup_workspace(workspace)


def test_create_solver_workspace_clones_base_commit_and_writes_only_solver_visible_material(
    tmp_path: Path, managed_workspaces
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    past_commit = _git(repo, "rev-parse", f"{base_commit}^").stdout.strip()
    future_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert future_commit != base_commit
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)
    material_dir = workspace.path / ".barcarolle"
    material = (material_dir / "solver-visible-task.json").read_text(encoding="utf-8")
    material_payload = json.loads(material)
    task_markdown = (material_dir / "TASK.md").read_text(encoding="utf-8")

    assert workspace.role == "solver"
    assert _git(workspace.path, "rev-parse", "HEAD").stdout.strip() == base_commit
    assert _git(workspace.path, "remote").stdout.strip() == ""
    assert not (workspace.path / ".git" / "FETCH_HEAD").exists()
    assert _git(workspace.path, "rev-list", "--all").stdout.splitlines() == [base_commit, past_commit]
    assert subprocess.run(
        ("git", "cat-file", "-e", f"{future_commit}^{{commit}}"),
        cwd=workspace.path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    ).returncode != 0
    assert (workspace.path / "README.md").read_text(encoding="utf-8") == "base\n"
    assert "solver_material_refs" in material
    assert "TASK.md" in material
    assert set(material_payload) == {"solver_material_refs", "task_material_file"}
    assert "README.md" in task_markdown
    assert "Fix the issue." in task_markdown
    assert task.task_id not in task_markdown
    assert task.base_commit not in task_markdown
    assert "base\n" not in task_markdown
    assert "hidden" not in material.lower()
    assert "oracle" not in material.lower()
    assert "hidden" not in task_markdown.lower()
    assert "oracle" not in task_markdown.lower()


def test_cleanup_workspace_rejects_unowned_path(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    workspace = WorkspaceRef(tmp_path, "solver", "task", "commit", "workspace")

    with pytest.raises(RuntimeError, match="cleanup failed"):
        cleanup_workspace(workspace)

    assert marker.read_text(encoding="utf-8") == "keep"


def test_cleanup_workspace_rejects_replaced_owned_path(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config)
    moved_workspace = workspace.path.with_name(f"{workspace.path.name}-moved")
    workspace.path.rename(moved_workspace)
    workspace.path.mkdir()
    (workspace.path / "decoy.txt").write_text("keep", encoding="utf-8")

    try:
        with pytest.raises(RuntimeError, match="cleanup failed"):
            cleanup_workspace(workspace)
        assert (workspace.path / "decoy.txt").read_text(encoding="utf-8") == "keep"
        assert moved_workspace.exists()
    finally:
        (workspace.path / "decoy.txt").unlink(missing_ok=True)
        workspace.path.rmdir()
        moved_workspace.rename(workspace.path)
        cleanup_workspace(workspace)


def test_create_solver_workspace_rejects_solver_material_resolving_outside_checkout(
    tmp_path: Path, managed_workspaces
) -> None:
    repo, _ = _make_repo(tmp_path)
    outside_material = tmp_path / "outside-private.txt"
    outside_material.write_text("private check content\n", encoding="utf-8")
    symlink_ref = repo / "statement.md"
    symlink_ref.symlink_to(outside_material)
    _git(repo, "add", "statement.md")
    _git(repo, "commit", "-m", "add symlink solver material")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _with_solver_refs(_task(base_commit=base_commit), ("statement.md",))
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    with pytest.raises(ValueError, match="solver material reference resolves outside the workspace"):
        create_solver_workspace(task, workspace_config)


def test_create_solver_workspace_reads_path_prefixed_solver_material_ref(tmp_path: Path, managed_workspaces) -> None:
    repo, _ = _make_repo(tmp_path)
    (repo / "statement.md").write_text("Implement the parser fix.\n", encoding="utf-8")
    _git(repo, "add", "statement.md")
    _git(repo, "commit", "-m", "add solver statement")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _with_solver_refs(_task(base_commit=base_commit), ("path:statement.md",))
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)
    task_markdown = (workspace.path / ".barcarolle" / "TASK.md").read_text(encoding="utf-8")

    assert "path:statement.md" in task_markdown
    assert "Implement the parser fix." not in task_markdown


def test_create_solver_workspace_allows_task_text_without_attachment_refs(
    tmp_path: Path, managed_workspaces
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _with_solver_refs(_task(base_commit=base_commit), ())
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)

    task_markdown = (workspace.path / ".barcarolle" / "TASK.md").read_text(encoding="utf-8")
    assert "Fix the issue." in task_markdown


def test_invoke_agent_runs_bound_harness_command_and_digest_safe_output(tmp_path: Path) -> None:
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('done.txt').write_text('ok'); print('done')")
    agent = _agent(agent_command)
    bind_agent_harness(agent, agent_command)
    workspace = WorkspaceRef(path=tmp_path, role="solver", task_id="task", base_commit="commit", workspace_digest="workspace")

    outcome = invoke_agent(workspace, _task(), agent, _runtime())

    assert outcome.terminal_status == "completed"
    assert outcome.usage == {}
    assert outcome.safe_output_digest
    assert (tmp_path / "done.txt").read_text(encoding="utf-8") == "ok"


def test_invoke_agent_reads_harness_usage_file(tmp_path: Path) -> None:
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('.barcarolle').mkdir(); "
        "Path('.barcarolle/usage.json').write_text('{\"input_tokens\": 12, \"output_tokens\": 3}')",
    )
    agent = _agent(agent_command)
    bind_agent_harness(agent, agent_command)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="solver",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = invoke_agent(workspace, _task(), agent, _runtime())

    assert outcome.terminal_status == "completed"
    assert outcome.usage == {"input_tokens": 12, "output_tokens": 3}


@pytest.mark.parametrize(
    "usage_json",
    (
        "[]",
        '{"input_tokens": -1}',
        '{"input_tokens": "unknown"}',
        '{"input_tokens": true}',
    ),
)
def test_invoke_agent_ignores_invalid_harness_usage_file(tmp_path: Path, usage_json: str) -> None:
    agent_command = (
        sys.executable,
        "-c",
        "import os; from pathlib import Path; Path('.barcarolle').mkdir(); "
        "Path('.barcarolle/usage.json').write_text(os.environ['TEST_USAGE_JSON'])",
    )
    agent = _agent(agent_command)
    bind_agent_harness(agent, agent_command)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="solver",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )
    previous = os.environ.get("TEST_USAGE_JSON")
    os.environ["TEST_USAGE_JSON"] = usage_json
    try:
        outcome = invoke_agent(workspace, _task(), agent, _runtime())
    finally:
        if previous is None:
            os.environ.pop("TEST_USAGE_JSON", None)
        else:
            os.environ["TEST_USAGE_JSON"] = previous

    assert outcome.terminal_status == "completed"
    assert outcome.failure_label is None
    assert outcome.usage == {}


def test_bind_agent_harness_rejects_command_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="harness command digest"):
        bind_agent_harness(_agent(), (sys.executable, "-c", "print('different harness')"))


def test_bind_check_material_rejects_destination_outside_reserved_namespace(tmp_path: Path) -> None:
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")

    with pytest.raises(ValueError, match="must stay under .barcarolle"):
        bind_check_material(_check(command=command, hidden=hidden), command, hidden, Path("collision"))


def test_capture_diff_reads_git_worktree_and_includes_untracked_files(tmp_path: Path, managed_workspaces) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)
    (workspace.path / "new.txt").write_text("new file\n", encoding="utf-8")
    (workspace.path / ".barcarolle/internal.txt").write_text("benchmark side data\n", encoding="utf-8")

    diff = capture_diff(workspace)

    assert "diff --git a/new.txt b/new.txt" in diff.diff_text
    assert "+new file" in diff.diff_text
    assert ".barcarolle" not in diff.diff_text
    assert diff.diff_digest == hashlib.sha256(diff.diff_text.encode("utf-8")).hexdigest()


def test_capture_diff_excludes_python_runtime_caches(tmp_path: Path, managed_workspaces) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)
    (workspace.path / "changed.py").write_text("value = 1\n", encoding="utf-8")
    pytest_cache = workspace.path / ".pytest_cache" / "v" / "cache"
    pytest_cache.mkdir(parents=True)
    (pytest_cache / "nodeids").write_text("[]\n", encoding="utf-8")
    bytecode_cache = workspace.path / "package" / "__pycache__"
    bytecode_cache.mkdir(parents=True)
    (bytecode_cache / "module.cpython-314.pyc").write_bytes(b"generated")

    diff = capture_diff(workspace)

    assert "diff --git a/changed.py b/changed.py" in diff.diff_text
    assert ".pytest_cache" not in diff.diff_text
    assert "__pycache__" not in diff.diff_text


def test_capture_diff_fails_closed_if_reserved_material_escapes_pathspec(
    tmp_path: Path,
    managed_workspaces,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(workspace)
    monkeypatch.setattr(workspace_module, "_CAPTURE_PATHSPEC", (".",))

    with pytest.raises(ValueError, match="reserved workspace material"):
        capture_diff(workspace)


def test_apply_diff_replays_captured_diff_in_fresh_verifier_checkout(tmp_path: Path, managed_workspaces) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    bind_repository_source(workspace_config, repo)
    solver = create_solver_workspace(task, workspace_config)
    managed_workspaces.append(solver)
    (solver.path / "new.txt").write_text("agent edit\n", encoding="utf-8")
    diff = capture_diff(solver)
    verifier = create_verifier_workspace(task, workspace_config)
    managed_workspaces.append(verifier)

    replay = apply_diff(verifier, diff)

    assert replay.replay_status == "applied"
    assert (verifier.path / "new.txt").read_text(encoding="utf-8") == "agent edit\n"


def test_apply_diff_normalizes_git_launch_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".git").mkdir()
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")

    def fail_to_launch(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git missing")

    monkeypatch.setattr(workspace_module.subprocess, "run", fail_to_launch)

    outcome = apply_diff(workspace, CapturedDiff("diff --git a/a b/a\n", "digest"))

    assert outcome.replay_status == "invalid"
    assert outcome.failure_label == "diff_replay_launch_error"


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


def test_bind_check_material_accepts_semantic_manifest(tmp_path: Path) -> None:
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")
    manifest = {"implementation_sha256": "check-code", "timeout_seconds": 5}
    check = replace(
        _check(command=command, hidden=hidden),
        check_manifest_digest=canonical_digest(manifest),
    )

    bind_check_material(check, command, hidden, check_manifest=manifest)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="verifier",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = verify_agent_diff(workspace, check, _runtime())

    assert outcome.outcome == "pass"


def test_bind_check_material_rejects_semantic_manifest_mismatch(
    tmp_path: Path,
) -> None:
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")
    check = replace(
        _check(command=command, hidden=hidden),
        check_manifest_digest=canonical_digest({"implementation": "expected"}),
    )

    with pytest.raises(ValueError, match="check manifest digest"):
        bind_check_material(
            check,
            command,
            hidden,
            check_manifest={"implementation": "different"},
        )


def test_verify_agent_diff_normalizes_hidden_material_copy_collision(tmp_path: Path) -> None:
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    oracle = hidden / "oracle.txt"
    oracle.write_text("private oracle", encoding="utf-8")
    hidden_digest = canonical_digest((("oracle.txt", hashlib.sha256(oracle.read_bytes()).hexdigest()),))
    command = (sys.executable, "-c", "print('ok')")
    check = replace(_check(command=command), hidden_check_bundle_digest=hidden_digest)
    bind_check_material(check, command, hidden)
    verifier = tmp_path / "verifier"
    (verifier / ".barcarolle").mkdir(parents=True)
    (verifier / ".barcarolle/check_bundle").write_text("collision", encoding="utf-8")
    workspace = WorkspaceRef(verifier, "verifier", "task", "commit", "workspace")

    outcome = verify_agent_diff(workspace, check, _runtime())

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "verifier_preparation_failed"


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


def test_run_agent_on_task_captures_changes_committed_by_agent_from_task_base(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; import subprocess; "
        "Path('new.txt').write_text('committed agent edit\\n', encoding='utf-8'); "
        "subprocess.run(('git', 'add', 'new.txt'), check=True); "
        "subprocess.run(('git', '-c', 'user.email=agent@example.invalid', '-c', 'user.name=Agent', "
        "'commit', '-m', 'agent commit'), check=True)",
    )
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "assert Path('new.txt').read_text(encoding='utf-8') == 'committed agent edit\\n'",
    )
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"


def test_run_agent_on_task_excludes_reserved_material_after_agent_clears_git_exclude(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "Path('.git/info/exclude').write_text('', encoding='utf-8'); "
        "Path('.barcarolle/agent-only.txt').write_text('must not cross boundary\\n', encoding='utf-8'); "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8')",
    )
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "assert Path('new.txt').read_text(encoding='utf-8') == 'agent edit\\n'; "
        "assert not Path('.barcarolle/agent-only.txt').exists()",
    )
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(output_root=tmp_path / "artifacts")

    result = run_agent_on_task_with_artifacts(task, check, agent, workspace_config, _runtime(), artifact_config)

    assert result.run.terminal_status == "passed"
    assert result.artifacts is not None
    diff_ref = next(ref for ref in result.artifacts.artifact_refs if ref.kind == "final_diff")
    diff_text = (artifact_config.output_root / diff_ref.ref).read_text(encoding="utf-8")
    assert "diff --git a/new.txt b/new.txt" in diff_text
    assert ".barcarolle" not in diff_text


def test_run_agent_on_task_disables_agent_configured_textconv_during_capture(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; import subprocess; "
        "Path('.gitattributes').write_text('README.md diff=evil\\n', encoding='utf-8'); "
        "subprocess.run(('git', 'config', 'diff.evil.textconv', 'sed s/base/fake/'), check=True); "
        "Path('README.md').write_text('solution\\n', encoding='utf-8')",
    )
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; assert Path('README.md').read_text(encoding='utf-8') == 'solution\\n'",
    )
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"


def test_run_agent_on_task_removes_solver_and_verifier_workspaces_after_success(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    solver_path_record = tmp_path / "solver-path.txt"
    verifier_path_record = tmp_path / "verifier-path.txt"
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        f"Path({str(solver_path_record)!r}).write_text(str(Path.cwd()), encoding='utf-8'); "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8')",
    )
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        f"Path({str(verifier_path_record)!r}).write_text(str(Path.cwd()), encoding='utf-8')",
    )
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "passed"
    assert not Path(solver_path_record.read_text(encoding="utf-8")).exists()
    assert not Path(verifier_path_record.read_text(encoding="utf-8")).exists()


def test_run_agent_on_task_returns_completed_record_when_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    original_remove = workspace_module._remove_owned_workspace_path
    failed_paths: list[Path] = []

    def fail_once(path: Path) -> None:
        if not failed_paths:
            failed_paths.append(path)
            raise OSError("transient cleanup failure")
        original_remove(path)

    record = None
    try:
        with monkeypatch.context() as patch:
            patch.setattr(workspace_module, "_remove_owned_workspace_path", fail_once)
            with pytest.warns(RuntimeWarning, match="workspace cleanup failed"):
                record = run_agent_on_task(task, check, agent, workspace_config, _runtime())
    finally:
        for path in failed_paths:
            original_remove(path)

    assert record is not None
    assert record.terminal_status == "passed"
    assert record.check_outcome == "pass"


def test_run_agent_on_task_rejects_noop_when_the_base_checkout_passes_the_check(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "print('no edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "baseline_check_passed_without_diff"


def test_baseline_pass_takes_priority_over_nonzero_agent_exit(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "raise SystemExit(1)")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "baseline_check_passed_without_diff"


def test_benchmark_verifier_failure_takes_priority_over_nonzero_agent_exit(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit'); raise SystemExit(1)",
    )
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "missing_verification_material"


def test_verifier_preparation_collision_remains_benchmark_owned(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    reserved_material = repo / ".barcarolle" / "check_bundle"
    reserved_material.parent.mkdir()
    reserved_material.write_text("repository collision", encoding="utf-8")
    _git(repo, "add", ".barcarolle/check_bundle")
    _git(repo, "commit", "-m", "add verifier material collision")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    oracle = hidden / "oracle.txt"
    oracle.write_text("private oracle", encoding="utf-8")
    hidden_digest = canonical_digest((("oracle.txt", hashlib.sha256(oracle.read_bytes()).hexdigest()),))
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = replace(_check(command=check_command), hidden_check_bundle_digest=hidden_digest)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "verifier_preparation_failed"


def test_post_diff_check_timeout_is_agent_invalid_to_prevent_denominator_removal(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    check_command = (sys.executable, "-c", "import time; time.sleep(2)")
    agent = _agent(agent_command)
    check = replace(_check(command=check_command, hidden=hidden), resource_limits={"timeout_seconds": 1})
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "timeout"


def test_post_diff_check_launch_error_caused_by_agent_is_agent_invalid(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    check_script = repo / "check.sh"
    check_script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    check_script.chmod(0o755)
    _git(repo, "add", "check.sh")
    _git(repo, "commit", "-m", "add check script")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('check.sh').unlink()")
    check_command = ("./check.sh",)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_launch_error"


def test_interpreter_launched_check_invalid_caused_by_agent_is_agent_invalid(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    check_script = repo / "check.py"
    check_script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    _git(repo, "add", "check.py")
    _git(repo, "commit", "-m", "add check script")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('check.py').unlink()",
    )
    check_command = (sys.executable, "check.py")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_invalid"


def test_post_diff_check_invalid_caused_by_agent_is_agent_invalid(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    check_script = repo / "check.sh"
    check_script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    check_script.chmod(0o755)
    _git(repo, "add", "check.sh")
    _git(repo, "commit", "-m", "add check script")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('check.sh').write_text('#!/bin/sh\\nexit 2\\n')",
    )
    check_command = ("./check.sh",)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_invalid"


def test_external_check_launch_error_is_benchmark_invalid(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    external_check = tmp_path / "external-check"
    external_check.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    external_check.chmod(0o755)
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    check_command = (str(external_check),)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    external_check.unlink()

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "check_launch_error"


def test_external_check_invalid_is_benchmark_invalid(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    external_check = tmp_path / "external-check"
    external_check.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    external_check.chmod(0o755)
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    check_command = (str(external_check),)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "check_invalid"


def test_run_agent_on_task_counts_noop_as_failure_when_the_check_fails(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "print('no edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(1)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)

    record = run_agent_on_task(task, check, agent, workspace_config, _runtime())

    assert record.terminal_status == "failed"
    assert record.check_outcome == "fail"
    assert record.invalid_owner is None


def test_run_agent_on_task_with_artifacts_rejects_invalid_config_before_agent_invocation(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_started = tmp_path / "agent-started.txt"
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        f"Path({str(agent_started)!r}).write_text('started', encoding='utf-8'); "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8')",
    )
    agent = _agent(agent_command)
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(output_root=tmp_path / "artifacts", path_mode="absolute")

    with pytest.raises(ValueError, match="path_mode"):
        run_agent_on_task_with_artifacts(task, check, agent, workspace_config, _runtime(), artifact_config)

    assert not agent_started.exists()


def test_run_agent_on_task_with_artifacts_returns_completed_run_when_artifact_persistence_fails(
    tmp_path: Path,
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('agent edit')")
    agent = _agent(agent_command)
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    check = _check(command=check_command, hidden=hidden)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    bind_check_material(check, check_command, hidden)
    artifact_output = tmp_path / "artifacts"
    artifact_output.write_text("not a directory", encoding="utf-8")
    artifact_config = WorkspaceArtifactConfig(output_root=artifact_output)

    with pytest.warns(RuntimeWarning, match="artifact preservation failed"):
        result = run_agent_on_task_with_artifacts(task, check, agent, workspace_config, _runtime(), artifact_config)

    assert result.run.terminal_status == "passed"
    assert result.run.check_outcome == "pass"
    assert result.artifacts is None


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


def test_run_agent_on_task_attributes_agent_deletion_of_git_metadata_to_agent(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    solver_path_record = tmp_path / "failed-solver-path.txt"
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; import shutil; "
        f"Path({str(solver_path_record)!r}).write_text(str(Path.cwd()), encoding='utf-8'); "
        "shutil.rmtree('.git'); Path('new.txt').write_text('agent edit\\n')",
    )
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "agent_workspace_corrupted"
    assert record.replay_status == "skipped"
    assert not Path(solver_path_record.read_text(encoding="utf-8")).exists()


def test_run_agent_on_task_attributes_agent_corruption_of_git_config_to_agent(tmp_path: Path) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "Path('.git/config').write_text('[broken\\n', encoding='utf-8'); "
        "Path('new.txt').write_text('agent edit\\n', encoding='utf-8')",
    )
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "agent_workspace_corrupted"
    assert record.replay_status == "skipped"


def test_run_agent_on_task_attributes_unappliable_captured_diff_to_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (sys.executable, "-c", "print('agent finished')")
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    diff_text = (
        "diff --git a/README.md b/README.md\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-not-the-base\n"
        "+solution\n"
    )
    monkeypatch.setattr(
        workspace_module,
        "capture_diff",
        lambda workspace: CapturedDiff(diff_text, hashlib.sha256(diff_text.encode("utf-8")).hexdigest()),
    )

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "failed"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "diff_replay_failed"


def test_run_agent_on_task_keeps_invalid_replay_infrastructure_benchmark_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (sys.executable, "-c", "from pathlib import Path; Path('new.txt').write_text('edit')")
    agent = _agent(agent_command)
    bind_repository_source(workspace_config, repo)
    bind_agent_harness(agent, agent_command)
    monkeypatch.setattr(
        workspace_module,
        "apply_diff",
        lambda workspace, diff: workspace_module.DiffReplayOutcome("invalid", "diff_replay_launch_error", ""),
    )

    record = run_agent_on_task(task, _check(), agent, workspace_config, _runtime())

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "diff_replay_launch_error"


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
    (repo / "README.md").write_text("past\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "past")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "commit", "-am", "base")
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
    task_text = "Fix the issue."
    solver_material_refs = ("README.md",)
    return TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit=base_commit,
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-02T00:00:00Z",
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(task_text, solver_material_refs),
        solver_material_refs=solver_material_refs,
        check_ids=("check",),
        cluster_id="cluster",
    )


def _with_solver_refs(task: TaskRecord, refs: tuple[str, ...]) -> TaskRecord:
    return replace(
        task,
        solver_material_refs=refs,
        solver_material_digest=make_solver_material_digest(task.task_text, refs),
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
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at="2026-01-02T00:00:00Z",
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
