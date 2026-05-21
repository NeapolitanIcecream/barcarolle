from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import workspace_acut_run as workspace_acut


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "calc.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_calc.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    return repo, git(repo, "rev-parse", "HEAD").strip()


def write_fake_acut(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "fake_acut.py"
    script.write_text(body, encoding="utf-8")
    return script


def package_for(repo: Path, base_commit: str, tmp_path: Path) -> workspace_acut.TaskPackage:
    return workspace_acut.TaskPackage(
        task_id="fake__001",
        repo_id="fake",
        split="B_real",
        source_repo=repo,
        base_commit=base_commit,
        solver_facing_statement="Make calc.value return 2.",
        verifier_command=[sys.executable, "hidden_verify.py"],
        hidden_files={"hidden_verify.py": "import calc\nassert calc.value() == 2\n"},
        allowed_code_paths=["calc.py"],
        test_paths=["tests/test_calc.py"],
        timeout_seconds=30,
    )


def test_workspace_adapter_captures_git_diff_and_verifies_in_fresh_workspace(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    fake_acut = write_fake_acut(
        tmp_path,
        "from pathlib import Path\n"
        "import argparse\n"
        "p=argparse.ArgumentParser(); p.add_argument('--workspace'); p.add_argument('--statement-file'); args=p.parse_args()\n"
        "workspace=Path(args.workspace)\n"
        "assert not (workspace / 'hidden_verify.py').exists()\n"
        "(workspace / 'calc.py').write_text('def value():\\n    return 2\\n', encoding='utf-8')\n",
    )
    config = workspace_acut.AdapterConfig(
        adapter_id="fake",
        acut_id="fake_acut",
        model_or_agent_name="fake-model",
        command_template=f"{sys.executable} {fake_acut} --workspace {{workspace}} --statement-file {{statement_file}}",
        timeout_seconds=30,
    )

    result = workspace_acut.run_workspace_cell(tmp_path, package_for(repo, base_commit, tmp_path), config, "run-pass")

    assert result.submission["status"] == "submitted"
    assert result.submission["patch_source"] == "git_diff_after_workspace_run"
    assert result.verifier["status"] == "verified_pass"
    assert result.verifier["fresh_workspace"] is True
    assert result.solver_workspace != result.verifier_workspace
    assert not (result.solver_workspace / "hidden_verify.py").exists()
    assert (result.verifier_workspace / "hidden_verify.py").exists()


def test_workspace_adapter_classifies_empty_diff(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    fake_acut = write_fake_acut(
        tmp_path,
        "import argparse\np=argparse.ArgumentParser(); p.add_argument('--workspace'); p.add_argument('--statement-file'); p.parse_args()\n",
    )
    config = workspace_acut.AdapterConfig(
        adapter_id="fake",
        acut_id="fake_acut",
        model_or_agent_name="fake-model",
        command_template=f"{sys.executable} {fake_acut} --workspace {{workspace}} --statement-file {{statement_file}}",
        timeout_seconds=30,
    )

    result = workspace_acut.run_workspace_cell(tmp_path, package_for(repo, base_commit, tmp_path), config, "run-empty")

    assert result.submission["status"] == "invalid_output"
    assert result.verifier["status"] == "invalid_output"
    assert result.verifier["harness_error"] == "empty_workspace_diff"


def test_workspace_adapter_blocks_prohibited_test_edits(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    fake_acut = write_fake_acut(
        tmp_path,
        "from pathlib import Path\n"
        "import argparse\n"
        "p=argparse.ArgumentParser(); p.add_argument('--workspace'); p.add_argument('--statement-file'); args=p.parse_args()\n"
        "(Path(args.workspace) / 'tests' / 'test_calc.py').write_text('def test_bad():\\n    assert True\\n', encoding='utf-8')\n",
    )
    config = workspace_acut.AdapterConfig(
        adapter_id="fake",
        acut_id="fake_acut",
        model_or_agent_name="fake-model",
        command_template=f"{sys.executable} {fake_acut} --workspace {{workspace}} --statement-file {{statement_file}}",
        timeout_seconds=30,
    )

    result = workspace_acut.run_workspace_cell(tmp_path, package_for(repo, base_commit, tmp_path), config, "run-test-edit")

    assert result.verifier["status"] == "policy_violation"
    assert result.verifier["harness_error"] == "submission_edited_tests"
    assert result.verifier["changed_paths"] == ["tests/test_calc.py"]


def test_workspace_adapter_classifies_nonzero_acut_exit(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    fake_acut = write_fake_acut(
        tmp_path,
        "import sys\nsys.exit(7)\n",
    )
    config = workspace_acut.AdapterConfig(
        adapter_id="fake",
        acut_id="fake_acut",
        model_or_agent_name="fake-model",
        command_template=f"{sys.executable} {fake_acut} --workspace {{workspace}} --statement-file {{statement_file}}",
        timeout_seconds=30,
    )

    result = workspace_acut.run_workspace_cell(tmp_path, package_for(repo, base_commit, tmp_path), config, "run-nonzero")

    assert result.submission["status"] == "acut_harness_error"
    assert result.verifier["status"] == "acut_harness_error"
    assert result.verifier["harness_error"] == "acut_command_failed"
