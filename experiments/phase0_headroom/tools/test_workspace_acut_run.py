from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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


def write_multi_adapter_config(tmp_path: Path, command: str) -> Path:
    path = tmp_path / "acut_workspace_adapters.yaml"
    path.write_text(
        "\n".join(
            [
                "schema_version: barcarolle.acut_workspace_adapters_config.v1",
                "preferred_model: fake-model",
                "comparison_design: same_model_cross_harness",
                "adapters:",
                "  - adapter_id: fake_codex",
                "    harness_name: codex",
                "    acut_id: fake_codex_acut",
                "    model_or_agent_name: fake-model",
                f'    command_template: "{command}"',
                "    timeout_seconds: 30",
                "    requires_env:",
                "      - LLM_BASE_URL",
                "      - LLM_API_KEY",
                "    endpoint_proof:",
                "      status: codex_eligible",
                "    usage_observation:",
                "      mode: harness_report_optional",
                "      report_path: null",
                "  - adapter_id: fake_kilo",
                "    harness_name: kilo",
                "    acut_id: fake_kilo_acut",
                "    model_or_agent_name: fake-model",
                f'    command_template: "{command}"',
                "    timeout_seconds: 30",
                "    requires_env:",
                "      - LLM_BASE_URL",
                "      - LLM_API_KEY",
                "    endpoint_proof:",
                "      status: kilo_eligible",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_multi_adapter_config_requires_adapter_id(tmp_path: Path) -> None:
    config_path = write_multi_adapter_config(tmp_path, f"{sys.executable} fake.py --workspace {{workspace}}")

    with pytest.raises(ValueError, match="adapter_id is required"):
        workspace_acut.resolve_adapter_config(config_path)


def test_multi_adapter_config_selects_adapter_metadata(tmp_path: Path) -> None:
    config_path = write_multi_adapter_config(tmp_path, f"{sys.executable} fake.py --workspace {{workspace}}")

    config = workspace_acut.resolve_adapter_config(config_path, adapter_id="fake_kilo")

    assert config.adapter_id == "fake_kilo"
    assert config.harness_name == "kilo"
    assert config.acut_id == "fake_kilo_acut"
    assert config.command_template_source == "config"
    assert config.endpoint_proof_status == "kilo_eligible"


def test_two_fake_adapters_isolate_raw_artifacts_with_result_prefix(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    fake_acut = write_fake_acut(
        tmp_path,
        "from pathlib import Path\n"
        "import argparse\n"
        "p=argparse.ArgumentParser(); p.add_argument('--workspace'); p.add_argument('--statement-file'); args=p.parse_args()\n"
        "(Path(args.workspace) / 'calc.py').write_text('def value():\\n    return 2\\n', encoding='utf-8')\n",
    )
    config_path = write_multi_adapter_config(
        tmp_path,
        f"{sys.executable} {fake_acut} --workspace {{workspace}} --statement-file {{statement_file}}",
    )
    package = package_for(repo, base_commit, tmp_path)
    codex_config = workspace_acut.resolve_adapter_config(config_path, adapter_id="fake_codex")
    kilo_config = workspace_acut.resolve_adapter_config(config_path, adapter_id="fake_kilo")

    codex_result = workspace_acut.run_workspace_cell(tmp_path, package, codex_config, "same-run", result_prefix="codex_kilo_workspace")
    kilo_result = workspace_acut.run_workspace_cell(tmp_path, package, kilo_config, "same-run", result_prefix="codex_kilo_workspace")

    assert codex_result.submission["status"] == "submitted"
    assert kilo_result.submission["status"] == "submitted"
    assert codex_result.submission["run_id"] == kilo_result.submission["run_id"] == "same-run"
    assert codex_result.submission["adapter_id"] == "fake_codex"
    assert kilo_result.submission["adapter_id"] == "fake_kilo"
    assert codex_result.submission["harness_name"] == "codex"
    assert kilo_result.submission["harness_name"] == "kilo"
    assert codex_result.solver_workspace != kilo_result.solver_workspace
    assert "codex_kilo_workspace/fake_codex/same-run" in codex_result.submission["raw_artifacts"]["patch"]
    assert "codex_kilo_workspace/fake_kilo/same-run" in kilo_result.submission["raw_artifacts"]["patch"]


def test_result_prefix_isolates_result_files(tmp_path: Path) -> None:
    exp = workspace_acut.phase0_root(tmp_path)

    workspace_acut.write_empty_result_files(tmp_path, "blocked_a", "reason_a", result_prefix="prefix_a")
    workspace_acut.write_empty_result_files(tmp_path, "blocked_b", "reason_b", result_prefix="prefix_b")

    assert workspace_acut.read_json(exp / "results" / "prefix_a_matrix.json")["blocker"] == "reason_a"
    assert workspace_acut.read_json(exp / "results" / "prefix_b_matrix.json")["blocker"] == "reason_b"
    assert (exp / "results" / "prefix_a_submissions.jsonl").exists()
    assert (exp / "results" / "prefix_b_submissions.jsonl").exists()


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
