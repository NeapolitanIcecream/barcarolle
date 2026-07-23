from dataclasses import replace
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from typing import Any

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
    WorkspaceRunContext,
    apply_diff,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    capture_diff,
    check_execution_binding_digest,
    cleanup_workspace,
    create_solver_workspace,
    create_verifier_workspace,
    harness_content_digest,
    invoke_agent,
    make_openai_env_network_policy_digest,
    openai_endpoint_digest,
    preflight_run_bindings,
    resolve_repository_commit,
    run_agent_on_task,
    run_agent_on_task_with_artifacts,
    verify_agent_diff,
)
from barcarolle.verification import hidden_material_digest


@pytest.fixture
def managed_workspaces():
    workspaces = []
    yield workspaces
    for workspace in reversed(workspaces):
        cleanup_workspace(workspace)


def test_create_solver_workspace_clones_base_commit_and_writes_only_solver_visible_material(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    past_commit = _git(repo, "rev-parse", f"{base_commit}^").stdout.strip()
    future_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert future_commit != base_commit
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)
    material_dir = workspace.path / ".barcarolle"
    material = (material_dir / "solver-visible-task.json").read_text(encoding="utf-8")
    material_payload = json.loads(material)
    task_markdown = (material_dir / "TASK.md").read_text(encoding="utf-8")

    assert workspace.role == "solver"
    assert _git(workspace.path, "rev-parse", "HEAD").stdout.strip() == base_commit
    assert _git(workspace.path, "remote").stdout.strip() == ""
    assert not (workspace.path / ".git" / "FETCH_HEAD").exists()
    assert _git(workspace.path, "rev-list", "--all").stdout.splitlines() == [
        base_commit,
        past_commit,
    ]
    assert (
        subprocess.run(
            ("git", "cat-file", "-e", f"{future_commit}^{{commit}}"),
            cwd=workspace.path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode
        != 0
    )
    assert (workspace.path / "README.md").read_text(encoding="utf-8") == "base\n"
    assert "solver_material_refs" in material
    assert "TASK.md" in material
    assert set(material_payload) == {"solver_material_refs", "task_material_file"}
    assert "README.md" in task_markdown
    assert "Fix the issue." in task_markdown
    assert task.task_id not in task_markdown
    assert task.base_commit not in task_markdown
    assert task.dependency_cluster_id not in material
    assert task.dependency_cluster_id not in task_markdown
    assert "base\n" not in task_markdown
    assert "hidden" not in material.lower()
    assert "oracle" not in material.lower()
    assert "hidden" not in task_markdown.lower()
    assert "oracle" not in task_markdown.lower()


def test_repository_binding_returns_a_new_context_without_mutating_the_original(
    tmp_path: Path,
    managed_workspaces,
) -> None:
    original_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)

    bound_context = bind_repository_source(original_context, workspace_config, repo)

    assert bound_context is not original_context
    with pytest.raises(ValueError, match="repository source is not bound"):
        create_solver_workspace(task, workspace_config, original_context)
    workspace = create_solver_workspace(task, workspace_config, bound_context)
    managed_workspaces.append(workspace)


def test_repository_binding_rejects_invalid_workspace_config(tmp_path: Path) -> None:
    repo, _ = _make_repo(tmp_path)
    workspace_config = replace(_workspace_config(repo), workspace_config_id=7)

    with pytest.raises(
        ValueError,
        match="workspace_config is invalid: "
        "WorkspaceConfig.workspace_config_id must be a string",
    ):
        bind_repository_source(WorkspaceRunContext(), workspace_config, repo)


def test_resolve_repository_commit_freezes_symbolic_revision(
    tmp_path: Path,
    managed_workspaces,
) -> None:
    run_context = WorkspaceRunContext()
    repo, _ = _make_repo(tmp_path)
    frozen_commit = resolve_repository_commit(repo, "HEAD")
    (repo / "README.md").write_text("later\n", encoding="utf-8")
    _git(repo, "commit", "-am", "later")

    assert len(frozen_commit) == 40
    assert resolve_repository_commit(repo, "HEAD") != frozen_commit

    task = _task(base_commit=frozen_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)

    assert _git(workspace.path, "rev-parse", "HEAD").stdout.strip() == frozen_commit
    assert (workspace.path / "README.md").read_text(encoding="utf-8") == "future\n"


def test_create_solver_workspace_supports_sha256_repository(
    tmp_path: Path,
    managed_workspaces,
) -> None:
    run_context = WorkspaceRunContext()
    repo = tmp_path / "sha256-repository"
    repo.mkdir()
    init = subprocess.run(
        ("git", "init", "--quiet", "--object-format=sha256"),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if init.returncode != 0:
        pytest.skip("installed Git does not support SHA-256 repositories")
    _git(repo, "config", "user.email", "barcarolle@example.invalid")
    _git(repo, "config", "user.name", "Barcarolle Tests")
    (repo / "README.md").write_text("sha256\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")

    base_commit = resolve_repository_commit(repo, "HEAD")
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)

    assert len(base_commit) == 64
    assert (
        _git(workspace.path, "rev-parse", "--show-object-format").stdout.strip()
        == "sha256"
    )
    assert _git(workspace.path, "rev-parse", "HEAD").stdout.strip() == base_commit


def test_cleanup_workspace_rejects_unowned_path(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    workspace = WorkspaceRef(tmp_path, "solver", "task", "commit", "workspace")

    with pytest.raises(RuntimeError, match="cleanup failed"):
        cleanup_workspace(workspace)

    assert marker.read_text(encoding="utf-8") == "keep"


def test_cleanup_workspace_rejects_replaced_owned_path(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
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
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)

    with pytest.raises(
        ValueError, match="solver material reference resolves outside the workspace"
    ):
        create_solver_workspace(task, workspace_config, run_context)


def test_create_solver_workspace_reads_path_prefixed_solver_material_ref(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, _ = _make_repo(tmp_path)
    (repo / "statement.md").write_text("Implement the parser fix.\n", encoding="utf-8")
    _git(repo, "add", "statement.md")
    _git(repo, "commit", "-m", "add solver statement")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    task = _with_solver_refs(_task(base_commit=base_commit), ("path:statement.md",))
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)
    task_markdown = (workspace.path / ".barcarolle" / "TASK.md").read_text(
        encoding="utf-8"
    )

    assert "path:statement.md" in task_markdown
    assert "Implement the parser fix." not in task_markdown


def test_create_solver_workspace_allows_task_text_without_attachment_refs(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _with_solver_refs(_task(base_commit=base_commit), ())
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)

    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)

    task_markdown = (workspace.path / ".barcarolle" / "TASK.md").read_text(
        encoding="utf-8"
    )
    assert "Fix the issue." in task_markdown


def test_invoke_agent_runs_bound_harness_command_and_digest_safe_output(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('done.txt').write_text('ok'); print('done')",
    )
    agent = _agent(agent_command)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="solver",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = invoke_agent(workspace, _task(), agent, _runtime(), run_context)

    assert outcome.terminal_status == "completed"
    assert outcome.usage == {}
    assert outcome.safe_output_digest
    assert (tmp_path / "done.txt").read_text(encoding="utf-8") == "ok"


def test_invoke_agent_bounds_large_stdout_and_stderr(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    agent_command = (
        sys.executable,
        "-c",
        "import sys; "
        "sys.stdout.buffer.write(b'A' * (2 * 1024 * 1024) + b'stdout-tail'); "
        "sys.stderr.buffer.write(b'B' * (2 * 1024 * 1024) + b'stderr-tail')",
    )
    agent = _agent(agent_command)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="solver",
        task_id="task",
        base_commit="a" * 40,
        workspace_digest="workspace",
    )

    outcome = invoke_agent(workspace, _task(), agent, _runtime(), run_context)

    assert outcome.terminal_status == "completed"
    assert "barcarolle output truncated" in outcome.stdout
    assert "total_bytes=2097163" in outcome.stdout
    assert outcome.stdout.endswith("stdout-tail")
    assert outcome.stderr.endswith("stderr-tail")
    assert len(outcome.stdout.encode("utf-8")) < 1024 * 1025
    assert len(outcome.stderr.encode("utf-8")) < 1024 * 1025
    assert outcome.safe_output_digest


def test_invoke_agent_reads_harness_usage_file(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('.barcarolle').mkdir(); "
        "Path('.barcarolle/usage.json').write_text('{\"input_tokens\": 12, \"output_tokens\": 3}')",
    )
    agent = _agent(agent_command)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="solver",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = invoke_agent(workspace, _task(), agent, _runtime(), run_context)

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
def test_invoke_agent_ignores_invalid_harness_usage_file(
    tmp_path: Path, usage_json: str
) -> None:
    run_context = WorkspaceRunContext()
    agent_command = (
        sys.executable,
        "-c",
        "import os; from pathlib import Path; Path('.barcarolle').mkdir(); "
        "Path('.barcarolle/usage.json').write_text(os.environ['TEST_USAGE_JSON'])",
    )
    agent = _agent(agent_command)
    run_context = bind_agent_harness(run_context, agent, agent_command)
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
        outcome = invoke_agent(workspace, _task(), agent, _runtime(), run_context)
    finally:
        if previous is None:
            os.environ.pop("TEST_USAGE_JSON", None)
        else:
            os.environ["TEST_USAGE_JSON"] = previous

    assert outcome.terminal_status == "completed"
    assert outcome.failure_label is None
    assert outcome.usage == {}


def test_bind_agent_harness_rejects_command_digest_mismatch() -> None:
    run_context = WorkspaceRunContext()
    with pytest.raises(ValueError, match="harness command digest"):
        run_context = bind_agent_harness(
            run_context, _agent(), (sys.executable, "-c", "print('different harness')")
        )


def test_bind_agent_harness_rejects_implicit_nonoffline_mode() -> None:
    run_context = WorkspaceRunContext()
    command = (sys.executable, "-c", "print('agent')")
    agent = replace(_agent(command), network_policy_digest="opaque-network-policy")

    with pytest.raises(ValueError, match="offline Agent network_policy_digest"):
        run_context = bind_agent_harness(run_context, agent, command)


def test_preflight_validates_each_immutable_binding_once_per_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    check, run_context = _bind_default_check(tmp_path, run_context)
    command = (sys.executable, "-c", "print('agent')")
    agent = _agent(command)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, command)
    check_calls = 0
    agent_calls = 0
    validate_check_binding = workspace_module._validated_check_binding
    validate_agent_binding = workspace_module._validated_agent_binding

    def count_check_binding(*args, **kwargs):
        nonlocal check_calls
        check_calls += 1
        return validate_check_binding(*args, **kwargs)

    def count_agent_binding(*args, **kwargs):
        nonlocal agent_calls
        agent_calls += 1
        return validate_agent_binding(*args, **kwargs)

    monkeypatch.setattr(
        workspace_module, "_validated_check_binding", count_check_binding
    )
    monkeypatch.setattr(
        workspace_module, "_validated_agent_binding", count_agent_binding
    )

    preflight_run_bindings(
        run_context,
        ((task, check, agent), (task, check, agent), (task, check, agent)),
        workspace_config,
        _runtime(),
    )

    assert check_calls == 1
    assert agent_calls == 1


@pytest.mark.parametrize(
    ("config_name", "changes", "expected_error"),
    (
        (
            "workspace_config",
            {"workspace_config_id": 7},
            "workspace_config is invalid: "
            "WorkspaceConfig.workspace_config_id must be a string",
        ),
        (
            "runtime_config",
            {"runtime_config_id": 7},
            "runtime_config is invalid: "
            "RuntimeConfig.runtime_config_id must be a string",
        ),
    ),
)
def test_preflight_validates_configs_without_an_execution_plan(
    tmp_path: Path,
    config_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    repo, _ = _make_repo(tmp_path)
    workspace_config = _workspace_config(repo)
    runtime_config = _runtime()
    run_context = bind_repository_source(WorkspaceRunContext(), workspace_config, repo)
    if config_name == "workspace_config":
        workspace_config = replace(workspace_config, **changes)
    else:
        runtime_config = replace(runtime_config, **changes)

    with pytest.raises(ValueError, match=expected_error):
        preflight_run_bindings(
            run_context,
            (),
            workspace_config,
            runtime_config,
        )


def test_paid_preflight_binds_endpoint_and_harness_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    check, run_context = _bind_default_check(tmp_path, run_context)
    harness = tmp_path / "paid-harness.py"
    harness.write_text("print('paid harness')\n", encoding="utf-8")
    command = (sys.executable, str(harness))
    endpoint = "https://example.invalid/v1"
    harness_digest = canonical_digest({"agent_command": command})
    agent = replace(
        _agent(command),
        network_policy_digest=make_openai_env_network_policy_digest(
            endpoint_digest=openai_endpoint_digest(endpoint),
            harness_digest=harness_digest,
            harness_content_digest=harness_content_digest((harness,)),
        ),
    )
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(
        run_context,
        agent,
        command,
        execution_mode="openai_paid",
        endpoint_harness_paths=(harness,),
    )
    monkeypatch.setenv("OPENAI_BASE_URL", endpoint)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-never-reported")

    preflight_run_bindings(
        run_context,
        ((task, check, agent),),
        workspace_config,
        _runtime(),
    )

    harness.write_text("print('changed harness')\n", encoding="utf-8")
    with pytest.raises(ValueError, match="endpoint or harness proof") as exc_info:
        preflight_run_bindings(
            run_context,
            ((task, check, agent),),
            workspace_config,
            _runtime(),
        )
    assert endpoint not in str(exc_info.value)
    assert "test-secret-never-reported" not in str(exc_info.value)


def test_paid_preflight_rejects_missing_api_key_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    check, run_context = _bind_default_check(tmp_path, run_context)
    harness = tmp_path / "paid-harness.py"
    harness.write_text("print('paid harness')\n", encoding="utf-8")
    command = (sys.executable, str(harness))
    endpoint = "https://example.invalid/v1"
    agent = replace(
        _agent(command),
        network_policy_digest=make_openai_env_network_policy_digest(
            endpoint_digest=openai_endpoint_digest(endpoint),
            harness_digest=canonical_digest({"agent_command": command}),
            harness_content_digest=harness_content_digest((harness,)),
        ),
    )
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(
        run_context,
        agent,
        command,
        execution_mode="openai_paid",
        endpoint_harness_paths=(harness,),
    )
    monkeypatch.setattr(
        workspace_module,
        "_resolve_openai_environment",
        lambda *, source_shell: (endpoint, False),
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        preflight_run_bindings(
            run_context,
            ((task, check, agent),),
            workspace_config,
            _runtime(),
        )


def test_paid_preflight_rejects_unresolved_model_outside_campaign_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    check, run_context = _bind_default_check(tmp_path, run_context)
    harness = tmp_path / "paid-harness.py"
    harness.write_text("print('paid harness')\n", encoding="utf-8")
    command = (sys.executable, str(harness))
    endpoint = "https://example.invalid/v1"
    agent = replace(
        _agent(command),
        requested_model_id="moving-alias",
        model_snapshot_id=None,
        model_resolution_scope_id="expired-campaign",
        model_resolution_scope_started_at="2026-01-01T00:00:00Z",
        model_resolution_scope_ended_at="2026-02-01T00:00:00Z",
        network_policy_digest=make_openai_env_network_policy_digest(
            endpoint_digest=openai_endpoint_digest(endpoint),
            harness_digest=canonical_digest({"agent_command": command}),
            harness_content_digest=harness_content_digest((harness,)),
        ),
    )
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(
        run_context,
        agent,
        command,
        execution_mode="openai_paid",
        endpoint_harness_paths=(harness,),
    )
    monkeypatch.setenv("OPENAI_BASE_URL", endpoint)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-never-reported")
    monkeypatch.setattr(
        workspace_module,
        "utc_now_timestamp",
        lambda: "2026-02-01T00:00:00Z",
    )

    with pytest.raises(ValueError, match="model resolution scope is not active"):
        preflight_run_bindings(
            run_context,
            ((task, check, agent),),
            workspace_config,
            _runtime(),
        )


@pytest.mark.parametrize("timeout", (0, -1, True, "5"))
def test_preflight_rejects_invalid_check_timeout_before_agent(
    tmp_path: Path,
    timeout: object,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    command = (sys.executable, "-c", "print('agent')")
    agent = _agent(command)
    check, run_context = _bind_default_check(tmp_path, run_context)
    check = replace(check, resource_limits={"timeout_seconds": timeout})
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, command)

    with pytest.raises(ValueError, match="Check timeout_seconds"):
        preflight_run_bindings(
            run_context,
            ((task, check, agent),),
            workspace_config,
            _runtime(),
        )


def test_bind_check_material_rejects_destination_outside_reserved_namespace(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")

    with pytest.raises(ValueError, match="must stay under .barcarolle"):
        run_context = bind_check_material(
            run_context,
            _check(command=command, hidden=hidden),
            command,
            hidden,
            Path("collision"),
        )


def test_capture_diff_reads_git_worktree_and_includes_untracked_files(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)
    (workspace.path / "new.txt").write_text("new file\n", encoding="utf-8")
    (workspace.path / ".barcarolle/internal.txt").write_text(
        "benchmark side data\n", encoding="utf-8"
    )

    diff = capture_diff(workspace)

    assert "diff --git a/new.txt b/new.txt" in diff.diff_text
    assert "+new file" in diff.diff_text
    assert ".barcarolle" not in diff.diff_text
    assert (
        diff.diff_digest == hashlib.sha256(diff.diff_text.encode("utf-8")).hexdigest()
    )


def test_capture_diff_excludes_python_runtime_caches(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
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
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    workspace = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(workspace)
    monkeypatch.setattr(workspace_module, "_CAPTURE_PATHSPEC", (".",))

    with pytest.raises(ValueError, match="reserved workspace material"):
        capture_diff(workspace)


def test_apply_diff_replays_captured_diff_in_fresh_verifier_checkout(
    tmp_path: Path, managed_workspaces
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    solver = create_solver_workspace(task, workspace_config, run_context)
    managed_workspaces.append(solver)
    (solver.path / "new.txt").write_text("agent edit\n", encoding="utf-8")
    diff = capture_diff(solver)
    verifier = create_verifier_workspace(task, workspace_config, run_context)
    managed_workspaces.append(verifier)

    replay = apply_diff(verifier, diff)

    assert replay.replay_status == "applied"
    assert (verifier.path / "new.txt").read_text(encoding="utf-8") == "agent edit\n"


def test_apply_diff_normalizes_git_launch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")

    def fail_to_launch(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git missing")

    monkeypatch.setattr(workspace_module.subprocess, "run", fail_to_launch)

    outcome = apply_diff(workspace, CapturedDiff("diff --git a/a b/a\n", "digest"))

    assert outcome.replay_status == "invalid"
    assert outcome.failure_label == "diff_replay_launch_error"


def test_verify_agent_diff_delegates_to_verification_with_bound_material(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (
        sys.executable,
        "-c",
        "from pathlib import Path; assert Path('.barcarolle/check_bundle').exists()",
    )
    check = _check(command=command, hidden=hidden)
    run_context = bind_check_material(run_context, check, command, hidden)
    workspace = WorkspaceRef(
        path=tmp_path,
        role="verifier",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = verify_agent_diff(workspace, check, _runtime(), run_context)

    assert outcome.outcome == "pass"
    assert (tmp_path / ".barcarolle/check_bundle").read_text(
        encoding="utf-8"
    ) == "private oracle"


def test_bind_check_material_accepts_semantic_manifest(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")
    manifest = {"implementation_sha256": "check-code", "timeout_seconds": 5}
    check = replace(
        _check(command=command, hidden=hidden),
        check_manifest_digest=canonical_digest(manifest),
    )

    run_context = bind_check_material(
        run_context, check, command, hidden, check_manifest=manifest
    )
    workspace = WorkspaceRef(
        path=tmp_path,
        role="verifier",
        task_id="task",
        base_commit="commit",
        workspace_digest="workspace",
    )

    outcome = verify_agent_diff(workspace, check, _runtime(), run_context)

    assert outcome.outcome == "pass"


def test_check_execution_binding_digest_changes_across_immutable_contexts(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    manifest = {"implementation": "semantic-check-v1"}
    first_command = (sys.executable, "-c", "raise SystemExit(0)")
    second_command = (sys.executable, "-c", "raise SystemExit(1)")
    check = replace(
        _check(command=first_command, hidden=hidden),
        check_manifest_digest=canonical_digest(manifest),
    )

    run_context = bind_check_material(
        run_context, check, first_command, hidden, check_manifest=manifest
    )
    first_digest = check_execution_binding_digest(check, run_context)
    second_context = bind_check_material(
        WorkspaceRunContext(),
        check,
        second_command,
        hidden,
        check_manifest=manifest,
    )
    second_digest = check_execution_binding_digest(check, second_context)

    assert first_digest != second_digest
    with pytest.raises(ValueError, match="conflicts with run context"):
        bind_check_material(
            run_context,
            check,
            second_command,
            hidden,
            check_manifest=manifest,
        )


def test_check_binding_detects_hidden_executable_bit_drift(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "raise SystemExit(0)")
    check = _check(command=command, hidden=hidden)
    run_context = bind_check_material(run_context, check, command, hidden)
    hidden.chmod(hidden.stat().st_mode | 0o100)

    with pytest.raises(ValueError, match="hidden material changed"):
        check_execution_binding_digest(check, run_context)


def test_bind_check_material_rejects_symbolic_link_source(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    target = tmp_path / "target.txt"
    target.write_text("private oracle", encoding="utf-8")
    hidden = tmp_path / "hidden-link.txt"
    hidden.symlink_to(target)
    command = (sys.executable, "-c", "raise SystemExit(0)")
    check = _check(command=command, hidden=target)

    with pytest.raises(ValueError, match="symbolic links"):
        run_context = bind_check_material(run_context, check, command, hidden)


def test_bind_check_material_rejects_semantic_manifest_mismatch(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    command = (sys.executable, "-c", "print('ok')")
    check = replace(
        _check(command=command, hidden=hidden),
        check_manifest_digest=canonical_digest({"implementation": "expected"}),
    )

    with pytest.raises(ValueError, match="check manifest digest"):
        run_context = bind_check_material(
            run_context,
            check,
            command,
            hidden,
            check_manifest={"implementation": "different"},
        )


def test_verify_agent_diff_normalizes_hidden_material_copy_collision(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    oracle = hidden / "oracle.txt"
    oracle.write_text("private oracle", encoding="utf-8")
    hidden_digest = hidden_material_digest(hidden)
    command = (sys.executable, "-c", "print('ok')")
    check = replace(_check(command=command), hidden_check_bundle_digest=hidden_digest)
    run_context = bind_check_material(run_context, check, command, hidden)
    verifier = tmp_path / "verifier"
    (verifier / ".barcarolle").mkdir(parents=True)
    (verifier / ".barcarolle/check_bundle").write_text("collision", encoding="utf-8")
    workspace = WorkspaceRef(verifier, "verifier", "task", "commit", "workspace")

    outcome = verify_agent_diff(workspace, check, _runtime(), run_context)

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "verifier_preparation_failed"


def test_run_agent_on_task_executes_scoreable_workspace_path_and_returns_valid_record(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"
    assert record.invalid_owner is None
    assert record.failure_label is None
    assert record.diff_digest != hashlib.sha256(b"").hexdigest()
    assert record.latency["agent_seconds"] > 0.0
    assert record.latency["verification_seconds"] > 0.0
    assert record.latency["solver_checkout_seconds"] > 0.0
    assert record.latency["verifier_checkout_seconds"] > 0.0
    assert record.latency["diff_replay_seconds"] > 0.0
    assert record.latency["cleanup_seconds"] >= 0.0
    assert record.latency["workspace_seconds"] >= (
        record.latency["agent_seconds"]
        + record.latency["verification_seconds"]
        + record.latency["solver_checkout_seconds"]
        + record.latency["verifier_checkout_seconds"]
        + record.latency["diff_replay_seconds"]
    )


def test_run_agent_on_task_captures_changes_committed_by_agent_from_task_base(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"


def test_run_agent_on_task_excludes_reserved_material_after_agent_clears_git_exclude(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(output_root=tmp_path / "artifacts")

    result = run_agent_on_task_with_artifacts(
        task, check, agent, workspace_config, _runtime(), run_context, artifact_config
    )

    assert result.run.terminal_status == "passed"
    assert result.artifacts is not None
    diff_ref = next(
        ref for ref in result.artifacts.artifact_refs if ref.kind == "final_diff"
    )
    diff_text = (artifact_config.output_root / diff_ref.ref).read_text(encoding="utf-8")
    assert "diff --git a/new.txt b/new.txt" in diff_text
    assert ".barcarolle" not in diff_text


def test_run_agent_on_task_disables_agent_configured_textconv_during_capture(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "passed"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"


def test_run_agent_on_task_removes_solver_and_verifier_workspaces_after_success(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "passed"
    assert not Path(solver_path_record.read_text(encoding="utf-8")).exists()
    assert not Path(verifier_path_record.read_text(encoding="utf-8")).exists()


def test_run_agent_on_task_returns_completed_record_when_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
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
                record = run_agent_on_task(
                    task, check, agent, workspace_config, _runtime(), run_context
                )
    finally:
        for path in failed_paths:
            original_remove(path)

    assert record is not None
    assert record.terminal_status == "passed"
    assert record.check_outcome == "pass"
    assert record.latency["cleanup_seconds"] >= 0.0


def test_run_agent_on_task_rejects_noop_when_the_base_checkout_passes_the_check(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "print('no edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "baseline_check_passed_without_diff"


def test_baseline_pass_takes_priority_over_nonzero_agent_exit(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "raise SystemExit(1)")
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "baseline_check_passed_without_diff"


def test_benchmark_verifier_failure_takes_priority_over_nonzero_agent_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit'); raise SystemExit(1)",
    )
    agent = _agent(agent_command)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)
    monkeypatch.setattr(
        workspace_module,
        "verify_agent_diff",
        lambda *_args: workspace_module.CheckOutcome(
            "invalid",
            "missing_verification_material",
            None,
            False,
            0.0,
            "",
        ),
    )

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "invalid"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "missing_verification_material"


def test_verifier_preparation_collision_remains_benchmark_owned(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
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
    hidden_digest = hidden_material_digest(hidden)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    agent = _agent(agent_command)
    check = replace(
        _check(command=check_command), hidden_check_bundle_digest=hidden_digest
    )
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "verifier_preparation_failed"


def test_post_diff_check_timeout_is_agent_invalid_to_prevent_denominator_removal(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    check_command = (sys.executable, "-c", "import time; time.sleep(2)")
    agent = _agent(agent_command)
    check = replace(
        _check(command=check_command, hidden=hidden),
        resource_limits={"timeout_seconds": 1},
    )
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "timeout"


def test_post_diff_check_launch_error_caused_by_agent_is_agent_invalid(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
        "from pathlib import Path; Path('check.sh').unlink()",
    )
    check_command = ("./check.sh",)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_launch_error"


def test_interpreter_launched_check_invalid_caused_by_agent_is_agent_invalid(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_invalid"


def test_post_diff_check_invalid_caused_by_agent_is_agent_invalid(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "check_invalid"


def test_external_check_launch_error_is_benchmark_invalid(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    external_check = tmp_path / "external-check"
    external_check.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    external_check.chmod(0o755)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    check_command = (str(external_check),)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
    external_check.unlink()

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "check_launch_error"


def test_external_check_invalid_is_benchmark_invalid(tmp_path: Path) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    external_check = tmp_path / "external-check"
    external_check.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    external_check.chmod(0o755)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    check_command = (str(external_check),)
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "applied"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "check_invalid"


def test_run_agent_on_task_counts_noop_as_failure_when_the_check_fails(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (sys.executable, "-c", "print('no edit')")
    check_command = (sys.executable, "-c", "raise SystemExit(1)")
    agent = _agent(agent_command)
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert record.terminal_status == "failed"
    assert record.check_outcome == "fail"
    assert record.invalid_owner is None


def test_workspace_artifact_config_does_not_expose_path_mode(tmp_path: Path) -> None:
    config_type: Any = WorkspaceArtifactConfig

    with pytest.raises(TypeError, match="path_mode"):
        config_type(output_root=tmp_path / "artifacts", path_mode="relative")


@pytest.mark.parametrize(
    "field_name", ("preserve_stdout_stderr", "preserve_final_diff")
)
def test_workspace_artifact_config_requires_exact_booleans(
    tmp_path: Path,
    field_name: str,
) -> None:
    config_type: Any = WorkspaceArtifactConfig

    with pytest.raises(ValueError, match=rf"{field_name} must be a bool"):
        config_type(output_root=tmp_path / "artifacts", **{field_name: "false"})


def test_workspace_artifact_config_rejects_malformed_summary_mode(
    tmp_path: Path,
) -> None:
    config_type: Any = WorkspaceArtifactConfig

    with pytest.raises(ValueError, match="workspace summary preservation"):
        config_type(
            output_root=tmp_path / "artifacts",
            preserve_solver_workspace_summary=["always"],
        )


def test_run_agent_on_task_with_artifacts_returns_completed_run_when_artifact_persistence_fails(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('agent edit')",
    )
    agent = _agent(agent_command)
    check_command = (sys.executable, "-c", "raise SystemExit(0)")
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
    artifact_output = tmp_path / "artifacts"
    artifact_output.write_text("not a directory", encoding="utf-8")
    artifact_config = WorkspaceArtifactConfig(output_root=artifact_output)

    with pytest.warns(RuntimeWarning, match="artifact preservation failed"):
        result = run_agent_on_task_with_artifacts(
            task,
            check,
            agent,
            workspace_config,
            _runtime(),
            run_context,
            artifact_config,
        )

    assert result.run.terminal_status == "passed"
    assert result.run.check_outcome == "pass"
    assert result.artifacts is None


def test_run_agent_on_task_with_artifacts_preserves_relative_run_outputs(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(
        output_root=tmp_path / "artifacts",
        preserve_solver_workspace_summary="always",
        preserve_verifier_workspace_summary="always",
    )

    result = run_agent_on_task_with_artifacts(
        task, check, agent, workspace_config, _runtime(), run_context, artifact_config
    )

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
    assert "hello stdout" in (
        artifact_config.output_root / refs["agent_stdout"].ref
    ).read_text(encoding="utf-8")
    assert "hello stderr" in (
        artifact_config.output_root / refs["agent_stderr"].ref
    ).read_text(encoding="utf-8")
    assert "new.txt" in (
        artifact_config.output_root / refs["final_diff"].ref
    ).read_text(encoding="utf-8")
    assert refs["verifier_workspace_summary"].private is True
    solver_summary = json.loads(
        (artifact_config.output_root / refs["solver_workspace_summary"].ref).read_text(
            encoding="utf-8"
        )
    )
    assert solver_summary["artifact_class"] == "solver"
    assert "private oracle" not in json.dumps(solver_summary)
    manifest = json.loads(
        (artifact_config.output_root / result.artifacts.manifest_ref).read_text(
            encoding="utf-8"
        )
    )
    assert manifest["workspace_run_id"] == result.run.workspace_run_id
    assert str(tmp_path) not in json.dumps(manifest)


def test_run_agent_on_task_with_artifacts_preserves_bounded_large_output_contract(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
        "sys.stdout.buffer.write(b'A' * (2 * 1024 * 1024) + b'preserved-tail')",
    )
    agent = _agent(agent_command)
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; assert Path('new.txt').exists()",
    )
    check = _check(command=check_command, hidden=hidden)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)
    artifact_config = WorkspaceArtifactConfig(output_root=tmp_path / "artifacts")

    result = run_agent_on_task_with_artifacts(
        task,
        check,
        agent,
        workspace_config,
        _runtime(),
        run_context,
        artifact_config,
    )

    assert result.run.terminal_status == "passed"
    assert result.artifacts is not None
    stdout_ref = next(
        ref for ref in result.artifacts.artifact_refs if ref.kind == "agent_stdout"
    )
    assert Path(stdout_ref.ref).name == "stdout.txt"
    stdout_text = (artifact_config.output_root / stdout_ref.ref).read_text(
        encoding="utf-8"
    )
    assert "barcarolle output truncated" in stdout_text
    assert "total_bytes=2097166" in stdout_text
    assert stdout_text.endswith("preserved-tail")
    assert stdout_ref.digest == hashlib.sha256(stdout_text.encode("utf-8")).hexdigest()
    manifest = json.loads(
        (artifact_config.output_root / result.artifacts.manifest_ref).read_text(
            encoding="utf-8"
        )
    )
    manifest_stdout = next(
        ref for ref in manifest["artifact_refs"] if ref["kind"] == "agent_stdout"
    )
    assert manifest_stdout["ref"] == stdout_ref.ref
    assert manifest_stdout["digest"] == stdout_ref.digest


def test_run_agent_on_task_replays_and_verifies_diff_after_nonzero_agent_exit(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "error"
    assert record.replay_status == "applied"
    assert record.check_outcome == "pass"
    assert record.failure_label == "agent_failed"


def test_run_agent_on_task_attributes_agent_deletion_of_git_metadata_to_agent(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "agent_workspace_corrupted"
    assert record.replay_status == "skipped"
    assert not Path(solver_path_record.read_text(encoding="utf-8")).exists()


def test_run_agent_on_task_attributes_agent_corruption_of_git_config_to_agent(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
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
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "agent_workspace_corrupted"
    assert record.replay_status == "skipped"


def test_run_agent_on_task_attributes_unappliable_captured_diff_to_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (sys.executable, "-c", "print('agent finished')")
    agent = _agent(agent_command)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)
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
        lambda workspace: CapturedDiff(
            diff_text, hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
        ),
    )

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "failed"
    assert record.invalid_owner == "agent"
    assert record.failure_label == "diff_replay_failed"


def test_run_agent_on_task_keeps_invalid_replay_infrastructure_benchmark_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; Path('new.txt').write_text('edit')",
    )
    agent = _agent(agent_command)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)
    monkeypatch.setattr(
        workspace_module,
        "apply_diff",
        lambda workspace, diff: workspace_module.DiffReplayOutcome(
            "invalid", "diff_replay_launch_error", ""
        ),
    )

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "diff_replay_launch_error"


def test_run_agent_on_task_short_circuits_agent_containment_failure_as_benchmark_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_context = WorkspaceRunContext()
    repo, base_commit = _make_repo(tmp_path)
    task = _task(base_commit=base_commit)
    workspace_config = _workspace_config(repo)
    agent_command = (sys.executable, "-c", "print('unused')")
    agent = _agent(agent_command)
    run_context = bind_repository_source(run_context, workspace_config, repo)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check, run_context = _bind_default_check(tmp_path, run_context)
    monotonic_tick = 0

    def monotonic_counter() -> float:
        nonlocal monotonic_tick
        monotonic_tick += 1
        return float(monotonic_tick)

    monkeypatch.setattr(workspace_module, "monotonic", monotonic_counter)
    monkeypatch.setattr(
        workspace_module,
        "invoke_agent",
        lambda *_args: workspace_module.AgentRunOutcome(
            terminal_status="invalid",
            duration_seconds=0.1,
            usage={"tokens": 3},
            safe_output_digest="safe-output",
            failure_label="agent_process_containment_failed",
            stdout="bounded stdout",
            stderr="",
        ),
    )

    def unexpected_diff_capture(_workspace: WorkspaceRef) -> CapturedDiff:
        raise AssertionError(
            "containment failure must stop before diff capture and verification"
        )

    monkeypatch.setattr(workspace_module, "capture_diff", unexpected_diff_capture)

    record = run_agent_on_task(
        task, check, agent, workspace_config, _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.replay_status == "skipped"
    assert record.check_outcome == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "agent_process_containment_failed"
    assert record.usage == {"tokens": 3}
    assert record.latency["solver_checkout_seconds"] == 1.0
    assert record.latency["verifier_checkout_seconds"] == 0.0
    assert record.latency["diff_replay_seconds"] == 0.0
    assert record.latency["cleanup_seconds"] == 1.0


def test_run_agent_on_task_rejects_task_check_mismatch_before_agent_runs(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    marker = tmp_path / "agent-ran.txt"
    agent_command = (
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
    )
    agent = _agent(agent_command)
    run_context = bind_agent_harness(run_context, agent, agent_command)
    check = _check(task_id="other-task")

    record = run_agent_on_task(
        _task(), check, agent, _workspace_config(tmp_path), _runtime(), run_context
    )

    assert validate_workspace_run(record).ok
    assert record.terminal_status == "invalid"
    assert record.invalid_owner == "benchmark"
    assert record.failure_label == "task_check_mismatch"
    assert not marker.exists()


def test_apply_diff_reports_missing_git_checkout_for_nonempty_diff(
    tmp_path: Path,
) -> None:
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")

    replay = apply_diff(workspace, CapturedDiff("diff --git a/a b/a\n", "digest"))

    assert replay.replay_status == "invalid"
    assert replay.failure_label == "missing_git_checkout"


def test_verify_agent_diff_returns_invalid_when_material_is_missing(
    tmp_path: Path,
) -> None:
    run_context = WorkspaceRunContext()
    workspace = WorkspaceRef(tmp_path, "verifier", "task", "commit", "workspace")
    check = replace(_check(), check_id="unbound-check")

    outcome = verify_agent_diff(workspace, check, _runtime(), run_context)

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


def _task(base_commit: str = "a" * 40) -> TaskRecord:
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
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=("check",),
        dependency_cluster_id="dependency-cluster",
        sampling_stratum="stratum",
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
    hidden_digest = (
        hidden_material_digest(hidden) if hidden is not None else _hidden_digest()
    )
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


def _bind_default_check(
    tmp_path: Path, run_context: WorkspaceRunContext
) -> tuple[CheckRecord, WorkspaceRunContext]:
    hidden = tmp_path / "default-hidden-check.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    check = _check(hidden=hidden)
    run_context = bind_check_material(
        run_context,
        check,
        (sys.executable, "-c", "print('ok')"),
        hidden,
    )
    return check, run_context


def _hidden_digest() -> str:
    return canonical_digest(
        {
            "format": "hidden_material_tree_v1",
            "entries": (
                (
                    ".",
                    "file",
                    0,
                    hashlib.sha256(b"private oracle").hexdigest(),
                ),
            ),
        }
    )


def _agent(command: tuple[str, ...] | None = None) -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
        harness_digest=canonical_digest({"agent_command": command})
        if command is not None
        else "harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="offline",
        adapter_digest="adapter",
    )


def _workspace_config(repo: Path) -> WorkspaceConfig:
    return WorkspaceConfig(
        workspace_config_id=f"workspace-config-{hashlib.sha256(str(repo).encode('utf-8')).hexdigest()}",
        repository_checkout_config_digest=canonical_digest(
            {"repository_path": str(repo)}
        ),
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
