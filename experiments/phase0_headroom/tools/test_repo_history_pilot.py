from __future__ import annotations

import json
from pathlib import Path

import repo_history_pilot as pilot
import statement_quality


def test_stable_task_id_generation() -> None:
    assert pilot.stable_task_id("humanize", 1) == "humanize__hist__001"
    assert pilot.stable_task_id("humanize", 16) == "humanize__hist__016"
    assert pilot.stable_task_id("boltons", 1) == "boltons__hist__001"


def test_code_test_path_classification_for_src_and_flat_layouts() -> None:
    code, tests = pilot.classify_paths(
        [
            "src/humanize/time.py",
            "src/humanize/py.typed",
            "tests/test_time.py",
            "docs/index.md",
            "humanize/filesize.py",
            "test_filesize.py",
            "setup.py",
        ]
    )

    assert code == ["humanize/filesize.py", "src/humanize/time.py"]
    assert tests == ["test_filesize.py", "tests/test_time.py"]


def test_first_failing_gate_selection() -> None:
    gates = {gate: "pass" for gate in pilot.GATE_ORDER}
    gates["reference_pass"] = "fail"
    gates["solution_leakage_review"] = "fail"

    assert pilot.first_failing_gate(gates) == "reference_pass"
    assert pilot.task_status(gates) == "near_certified"


def test_release_split_generation() -> None:
    rows = [
        {"task_id": "humanize__hist__004", "task_time": "2023-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__001", "task_time": "2020-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__003", "task_time": "2022-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__002", "task_time": "2021-01-01T00:00:00+00:00"},
    ]

    assert pilot.split_release_tasks(rows) == {
        "B_real": ["humanize__hist__001", "humanize__hist__002"],
        "W_real": ["humanize__hist__003", "humanize__hist__004"],
    }


def test_release_payload_marks_pilot_and_benchmark_grade(tmp_path: Path) -> None:
    config = pilot.PilotConfig(
        repo_id="humanize",
        repo_url="https://example.invalid/humanize.git",
        local_repo=tmp_path,
        command_template="python -m pytest -q {test_files}",
        certification_attempts=6,
        pilot_certified_min=4,
        benchmark_grade_min=6,
        result_prefix="humanize_pre_phase1_workspace",
    )
    rows = [
        {"task_id": f"humanize__hist__{i:03d}", "task_time": f"202{i}-01-01T00:00:00+00:00"}
        for i in range(1, 7)
    ]

    payload = pilot.release_payload(config, rows)

    assert payload["pilot_grade"] is True
    assert payload["benchmark_grade"] is True
    assert payload["splits"]["B_real"] == ["humanize__hist__001", "humanize__hist__002", "humanize__hist__003"]
    assert payload["splits"]["W_real"] == ["humanize__hist__004", "humanize__hist__005", "humanize__hist__006"]


def test_committed_json_rows_do_not_copy_raw_source_text(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    rows = [
        {
            "task_id": "humanize__hist__001",
            "changed_files": ["src/humanize/time.py", "tests/test_time.py"],
            "summary_hash": "abc123",
        }
    ]
    pilot.write_jsonl(path, rows)

    serialized = path.read_text(encoding="utf-8")
    assert "def naturaltime" not in serialized
    assert "diff --git" not in serialized
    assert json.loads(serialized)["task_id"] == "humanize__hist__001"


def test_commit_context_ref_uses_message_without_patch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    pilot.run_command(["git", "init"], repo)
    pilot.run_command(["git", "config", "user.email", "test@example.invalid"], repo)
    pilot.run_command(["git", "config", "user.name", "Test User"], repo)
    (repo / "module.py").write_text("value = 1\n", encoding="utf-8")
    pilot.run_command(["git", "add", "module.py"], repo)
    pilot.run_command(["git", "commit", "-m", "Describe behavior", "-m", "Fixes #123"], repo)
    commit = pilot.git_lines(repo, ["rev-parse", "HEAD"])[0]
    config = pilot.PilotConfig(
        repo_id="humanize",
        repo_url="https://example.invalid/humanize.git",
        local_repo=repo,
        command_template="python -m pytest -q {test_files}",
        certification_attempts=1,
        pilot_certified_min=1,
        benchmark_grade_min=1,
        result_prefix="humanize_pre_phase1_workspace",
    )

    ref = pilot.commit_context_ref(config, {"task_id": "humanize__hist__001", "target_commit": commit, "subject": "Describe behavior"})

    assert ref["classification"] == "diagnostic_only_context"
    assert ref["source_kind"] == "commit_message_fallback"
    assert ref["summary"] == "Describe behavior"
    assert ref["body_summary"] == "Fixes #123"


def test_commit_message_fallback_alone_does_not_produce_allowed_context_refs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    pilot.run_command(["git", "init"], repo)
    pilot.run_command(["git", "config", "user.email", "test@example.invalid"], repo)
    pilot.run_command(["git", "config", "user.name", "Test User"], repo)
    (repo / "module.py").write_text("value = 1\n", encoding="utf-8")
    pilot.run_command(["git", "add", "module.py"], repo)
    pilot.run_command(["git", "commit", "-m", "Fix a behavior"], repo)
    commit = pilot.git_lines(repo, ["rev-parse", "HEAD"])[0]
    config = pilot.PilotConfig(
        repo_id="humanize",
        repo_url="https://example.invalid/humanize.git",
        local_repo=repo,
        command_template="python -m pytest -q {test_files}",
        certification_attempts=1,
        pilot_certified_min=1,
        benchmark_grade_min=1,
        result_prefix="humanize_pre_phase1_workspace",
    )

    ref = pilot.commit_context_ref(config, {"task_id": "humanize__hist__001", "target_commit": commit, "subject": "Fix a behavior"})

    assert pilot.allowed_context_refs([ref]) == []


def test_solver_statement_uses_candidate_repo_id() -> None:
    statement = pilot.solver_statement(
        {"repo_id": "itsdangerous", "module_or_package": ["signer"]},
        [{"summary": "support FIPS builds without SHA-1"}],
    )

    assert "itsdangerous behavior" in statement
    assert "humanize behavior" not in statement


def test_solver_statement_uses_boltons_for_replacement_repo() -> None:
    statement = pilot.solver_statement(
        {"repo_id": "boltons", "module_or_package": ["iterutils"]},
        [{"summary": "handle empty iterables without raising"}],
    )

    assert "boltons behavior" in statement
    assert "itsdangerous behavior" not in statement
    assert "humanize behavior" not in statement


def test_candidate_filter_rejects_maintenance_dependency_subjects() -> None:
    decision = pilot.candidate_filter_decision(
        subject="update dev dependencies",
        changed_files=["src/itsdangerous/timed.py", "tests/test_itsdangerous/test_serializer.py"],
        code_files=["src/itsdangerous/timed.py"],
        added=4,
        deleted=2,
        modules=["timed"],
    )

    assert decision["candidate_filter_status"] == "rejected"
    assert "reject_subject_term:update dev dependencies" in decision["reject_reasons"]


def test_candidate_filter_rejects_large_changes_over_250_lines() -> None:
    decision = pilot.candidate_filter_decision(
        subject="fix timestamp behavior",
        changed_files=["src/itsdangerous/timed.py", "tests/test_itsdangerous/test_timed.py"],
        code_files=["src/itsdangerous/timed.py"],
        added=200,
        deleted=51,
        modules=["timed"],
    )

    assert decision["candidate_filter_status"] == "rejected"
    assert "changed_lines_over:250" in decision["reject_reasons"]


def test_candidate_filter_rejects_project_file_heavy_changes() -> None:
    decision = pilot.candidate_filter_decision(
        subject="fix serializer behavior",
        changed_files=[
            ".github/workflows/tests.yaml",
            "pyproject.toml",
            "requirements/tests.txt",
            "src/itsdangerous/serializer.py",
            "tests/test_itsdangerous/test_serializer.py",
        ],
        code_files=["src/itsdangerous/serializer.py"],
        added=12,
        deleted=8,
        modules=["serializer"],
    )

    assert decision["candidate_filter_status"] == "rejected"
    assert "project_file_heavy" in decision["reject_reasons"]


def test_github_pr_refs_store_sanitized_body_summary_without_raw_response(monkeypatch) -> None:
    body = "x" * 1000

    def fake_run_command(command, cwd, timeout=120, env=None):
        return pilot.CommandResult(
            0,
            json.dumps([{"number": 42, "title": "Fix behavior", "body": body}]),
            "",
            0.01,
        )

    monkeypatch.setattr(pilot, "run_command", fake_run_command)
    config = pilot.PilotConfig(
        repo_id="boltons",
        repo_url="https://github.com/mahmoud/boltons.git",
        local_repo=Path("/tmp/boltons"),
        command_template="python -m pytest -q {test_files}",
        certification_attempts=1,
        pilot_certified_min=1,
        benchmark_grade_min=1,
        result_prefix="boltons_replacement",
    )

    refs = pilot.github_pr_refs(config, "abc123")

    assert refs == [
        {
            "body_summary": "x" * statement_quality.PUBLIC_BODY_SUMMARY_LIMIT,
            "classification": "problem_context",
            "ref": "pr:42",
            "summary": "Fix behavior",
            "task_id": "",
        }
    ]
    assert "raw_response" not in refs[0]


def test_uv_commands_include_editable_workspace() -> None:
    command = pilot.command_test_files("uv run --project experiments/phase0_headroom python -m pytest -q {test_files}", ["/tmp/ws/tests/test_time.py"])

    wrapped = pilot.with_editable_workspace(command, Path("/tmp/ws"))

    assert wrapped[:4] == ["uv", "run", "--with-editable", "/tmp/ws"]
    assert wrapped[-1] == "/tmp/ws/tests/test_time.py"


def test_apply_patch_text_does_not_target_parent_repo(tmp_path: Path) -> None:
    outer = tmp_path / "outer"
    workspace = outer / "ignored" / "workspace"
    workspace.mkdir(parents=True)
    pilot.run_command(["git", "init"], outer)
    (workspace / "module.py").write_text("value = 1\n", encoding="utf-8")
    patch = """diff --git a/module.py b/module.py
--- a/module.py
+++ b/module.py
@@ -1 +1 @@
-value = 1
+value = 2
"""

    assert pilot.apply_patch_text(workspace, patch)
    assert (workspace / "module.py").read_text(encoding="utf-8") == "value = 2\n"
