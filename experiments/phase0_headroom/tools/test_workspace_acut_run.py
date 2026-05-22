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


def section(text: str, heading: str) -> str:
    start = text.index(f"## {heading}")
    rest = text[start + len(f"## {heading}") :]
    next_heading = rest.find("\n## ")
    return rest if next_heading == -1 else rest[:next_heading]


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


def write_clean_overlay_fixture(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    root = tmp_path
    repo, base_commit = make_repo(tmp_path)
    exp = root / "experiments" / "phase0_headroom"
    phase1 = root / "experiments" / "phase1_compiler"
    (exp / "certified_tasks").mkdir(parents=True)
    (exp / "releases").mkdir(parents=True)
    (exp / "target_profiles").mkdir(parents=True)
    (phase1 / "results").mkdir(parents=True)
    (exp / "configs").mkdir(parents=True)

    sidecar_row = {
        "task_id": "boltons__clean_ext__001",
        "repo_id": "boltons",
        "base_commit": base_commit,
        "target_commit": "target-clean-ext-001",
        "task_time": "2020-01-06T22:29:17-08:00",
        "changed_files": ["calc.py", "tests/test_calc.py"],
        "test_files": ["tests/test_calc.py"],
        "allowed_context_refs": ["issue:231"],
        "sanitized_context": {
            "classification": "problem_context",
            "ref": "issue:231",
            "summary": "calc.value returns the wrong public value",
            "body_summary": "A public issue reports that calc.value should return 2.",
        },
        "original_hardening_status": "diagnostic_only",
        "promotion_decision": "promote_to_clean_benchmark_candidate",
        "promotion_rationale": "source_context_repaired_with_sanitized_public_issue",
        "subject": "SECRET implementation: return 2",
        "harness_test_command": "python -m pytest -q {test_files}",
    }
    canonical_row = {
        "task_id": "boltons__hist__011",
        "repo_id": "boltons",
        "base_commit": base_commit,
        "target_commit": "target-hist-011",
        "task_time": "2020-06-22T01:19:35-04:00",
        "code_files": ["calc.py"],
        "changed_files": ["calc.py", "tests/test_calc.py"],
        "test_files": ["tests/test_calc.py"],
        "solver_facing_statement": "Repair the public calc behavior.",
        "harness_test_command": "python -m pytest -q {test_files}",
        "scope_boundaries": "Modify only calc.py; do not edit tests.",
    }
    workspace_acut.write_jsonl(exp / "certified_tasks" / "boltons_clean_outcome_unseen_supply_certified_tasks.jsonl", [sidecar_row])
    workspace_acut.write_jsonl(exp / "certified_tasks" / "boltons_certified_tasks.jsonl", [canonical_row])
    release_path = exp / "releases" / "boltons_phase0_pilot_release.json"
    workspace_acut.write_json(
        release_path,
        {
            "pilot_grade": True,
            "splits": {"B_real": ["boltons__hist__011"], "W_real": []},
            "tasks": [{"task_id": "boltons__hist__011", "split": "B_real"}],
        },
    )
    workspace_acut.write_json(exp / "target_profiles" / "boltons_target_profile.json", {"local_repo": str(repo), "test_command": "python -m pytest -q {test_files}"})
    workspace_acut.write_json(
        phase1 / "results" / "phase1_clean_outcome_unseen_supply_overlay.json",
        {
            "evidence_level": "clean_supply_overlay_sidecar",
            "promoted_tasks": [
                {
                    "task_id": "boltons__clean_ext__001",
                    "repo_id": "boltons",
                    "task_time": "2020-01-06T22:29:17-08:00",
                    "promotion_decision": "promote_to_clean_benchmark_candidate",
                    "promotion_rationale": "source_context_repaired_with_sanitized_public_issue",
                    "original_hardening_status": "diagnostic_only",
                    "sanitized_context": sidecar_row["sanitized_context"],
                },
                {
                    "task_id": "boltons__hist__011",
                    "repo_id": "boltons",
                    "task_time": "2020-06-22T01:19:35-04:00",
                    "clean_overlay_promotion_decision": "prior_promoted_clean_supply",
                    "original_hardening_status": "manual_review_required",
                },
            ],
        },
    )
    matrix_path = exp / "configs" / "phase1_preregistered_clean_future_holdout_workspace_matrix.yaml"
    matrix_path.write_text(
        "\n".join(
            [
                "schema_version: barcarolle.phase1_preregistered_clean_future_holdout_workspace_matrix.v1",
                "status: configured",
                "clean_supply_overlay: experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json",
                "clean_ext_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl",
                "canonical_boltons_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl",
                "canonical_boltons_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json",
                "result_prefixes:",
                "  b_eval: phase1_future_holdout_b_eval",
                "  h_future: phase1_future_holdout_h_future",
                "splits:",
                "  b_eval:",
                "    - boltons__clean_ext__001",
                "  h_future:",
                "    - boltons__hist__011",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root, matrix_path, release_path, base_commit


def write_second_repo_clean_overlay_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path
    repo, base_commit = make_repo(tmp_path)
    exp = root / "experiments" / "phase0_headroom"
    phase1 = root / "experiments" / "phase1_compiler"
    (exp / "certified_tasks").mkdir(parents=True)
    (exp / "configs").mkdir(parents=True)
    (phase1 / "configs").mkdir(parents=True)
    (phase1 / "results").mkdir(parents=True)

    row = {
        "task_id": "attrs__hist__001",
        "repo_id": "attrs",
        "base_commit": base_commit,
        "target_commit": base_commit,
        "task_time": "2020-01-13T02:46:11-05:00",
        "changed_files": ["calc.py", "tests/test_calc.py"],
        "test_files": ["tests/test_calc.py"],
        "allowed_context_refs": ["issue:611"],
        "sanitized_context": {
            "classification": "problem_context",
            "ref": "issue:611",
            "summary": "calc.value should preserve attrs behavior",
            "body_summary": "A public attrs issue describes the behavior without implementation details.",
        },
        "promotion_decision": "promote_to_clean_benchmark_candidate",
        "promotion_rationale": "local_certification_and_non_leaky_public_context",
        "source_context_status": "non_leaky_problem_context",
    }
    workspace_acut.write_jsonl(exp / "certified_tasks" / "attrs_clean_outcome_unseen_supply_certified_tasks.jsonl", [row])
    workspace_acut.write_json(
        phase1 / "results" / "phase1_second_repo_clean_supply_overlay.json",
        {
            "evidence_level": "clean_supply_overlay_sidecar",
            "selected_repo_id": "attrs",
            "selected_b_eval_task_ids": ["attrs__hist__001"],
            "selected_h_future_task_ids": [],
            "promoted_task_ids": ["attrs__hist__001"],
            "promoted_tasks": [row],
            "config": "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml",
        },
    )
    (phase1 / "configs" / "phase1_second_repo_clean_outcome_unseen_supply.yaml").write_text(
        "\n".join(
            [
                "schema_version: barcarolle.phase1_second_repo_clean_outcome_unseen_supply.v1",
                "candidate_repos:",
                "  attrs:",
                "    repo_url: https://github.com/python-attrs/attrs.git",
                f"    local_repo: {repo}",
                "    candidate_source_prefix: attrs_clean_outcome_unseen_supply",
                "    test_environment:",
                "      command_template: uv run --project experiments/phase0_headroom --with pytest>=7,<8 python -m pytest -q {test_files}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    matrix_path = phase1 / "configs" / "phase1_two_repo_future_holdout_validation.yaml"
    matrix_path.write_text(
        "\n".join(
            [
                "schema_version: barcarolle.phase1_two_repo_future_holdout_validation.v1",
                "status: configured",
                "second_repo_clean_supply_overlay: experiments/phase1_compiler/results/phase1_second_repo_clean_supply_overlay.json",
                "splits:",
                "  b_eval:",
                "    - attrs__hist__001",
                "  h_future:",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root, matrix_path, repo


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


def test_select_packages_prefers_explicit_task_ids_over_smoke_defaults(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    packages = [
        package_for(repo, base_commit, tmp_path),
        workspace_acut.TaskPackage(
            task_id="click__rbench__001",
            repo_id="click",
            split="G_mini",
            source_repo=repo,
            base_commit=base_commit,
            solver_facing_statement="Keep me out of an explicit probe.",
            verifier_command=["true"],
        ),
    ]

    selected = workspace_acut.select_packages(packages, mode="smoke", task_ids=["fake__001"])

    assert [package.task_id for package in selected] == ["fake__001"]


def test_clean_overlay_task_ids_can_be_selected_by_task_id(tmp_path: Path) -> None:
    root, matrix_path, _release_path, _base_commit = write_clean_overlay_fixture(tmp_path)

    packages = workspace_acut.load_phase0_packages(root, matrix_config_path=matrix_path)
    selected = workspace_acut.select_packages(packages, mode="matrix", task_ids=["boltons__clean_ext__001"])

    assert [package.task_id for package in selected] == ["boltons__clean_ext__001"]
    assert selected[0].repo_id == "boltons"
    assert selected[0].metadata["evidence_level"] == "clean_supply_overlay_sidecar"


def test_second_repo_clean_overlay_task_ids_can_be_selected_by_task_id(tmp_path: Path) -> None:
    root, matrix_path, repo = write_second_repo_clean_overlay_fixture(tmp_path)

    packages = workspace_acut.load_phase0_packages(root, matrix_config_path=matrix_path)
    selected = workspace_acut.select_packages(packages, mode="matrix", task_ids=["attrs__hist__001"])

    assert [package.task_id for package in selected] == ["attrs__hist__001"]
    assert selected[0].repo_id == "attrs"
    assert selected[0].source_repo == repo
    assert selected[0].split == "B_eval"
    assert selected[0].metadata["evidence_level"] == "clean_supply_overlay_sidecar"
    assert "pytest>=7,<8" in " ".join(selected[0].verifier_command)


def test_clean_overlay_loader_does_not_rewrite_canonical_release(tmp_path: Path) -> None:
    root, matrix_path, release_path, _base_commit = write_clean_overlay_fixture(tmp_path)
    before = release_path.read_text(encoding="utf-8")

    workspace_acut.load_phase0_packages(root, matrix_config_path=matrix_path)

    assert release_path.read_text(encoding="utf-8") == before


def test_clean_overlay_statement_uses_public_context_without_target_diff(tmp_path: Path) -> None:
    root, matrix_path, _release_path, _base_commit = write_clean_overlay_fixture(tmp_path)
    package = {
        package.task_id: package for package in workspace_acut.load_phase0_packages(root, matrix_config_path=matrix_path)
    }["boltons__clean_ext__001"]

    text = workspace_acut.render_statement(package)

    assert "calc.value returns the wrong public value" in text
    assert "issue:231" in text
    assert "calc.py" in section(text, "Editable Paths")
    assert "python -m pytest -q tests/test_calc.py" in text
    assert "target-clean-ext-001" not in text
    assert "SECRET implementation" not in text
    assert "diff --git" not in text


def test_clean_overlay_provenance_is_recorded_as_sidecar_metadata(tmp_path: Path) -> None:
    root, matrix_path, _release_path, _base_commit = write_clean_overlay_fixture(tmp_path)
    package = {
        package.task_id: package for package in workspace_acut.load_phase0_packages(root, matrix_config_path=matrix_path)
    }["boltons__clean_ext__001"]

    assert package.metadata["evidence_level"] == "clean_supply_overlay_sidecar"
    assert package.metadata["task_time"] == "2020-01-06T22:29:17-08:00"
    assert package.metadata["changed_files"] == ["calc.py", "tests/test_calc.py"]
    assert package.metadata["allowed_context_refs"] == ["issue:231"]
    assert package.metadata["original_hardening_status"] == "diagnostic_only"
    assert package.metadata["promotion_rationale"] == "source_context_repaired_with_sanitized_public_issue"
    assert package.metadata["sanitized_context"]["classification"] == "problem_context"


def test_future_holdout_prefixes_keep_separate_score_tables(tmp_path: Path) -> None:
    exp = workspace_acut.phase0_root(tmp_path)

    workspace_acut.write_empty_result_files(tmp_path, "ready", "", result_prefix="phase1_future_holdout_b_eval")
    workspace_acut.write_empty_result_files(tmp_path, "ready", "", result_prefix="phase1_future_holdout_h_future")

    assert (exp / "results" / "phase1_future_holdout_b_eval_score_table.csv").exists()
    assert (exp / "results" / "phase1_future_holdout_h_future_score_table.csv").exists()
    assert (exp / "results" / "phase1_future_holdout_b_eval_score_table.csv") != (
        exp / "results" / "phase1_future_holdout_h_future_score_table.csv"
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


def test_statement_policy_lists_only_allowed_code_paths_as_editable(tmp_path: Path) -> None:
    package = workspace_acut.TaskPackage(
        task_id="click__fake",
        repo_id="click",
        split="G_mini",
        source_repo=tmp_path,
        base_commit="base",
        solver_facing_statement="Update CliRunner behavior.",
        verifier_command=["true"],
        allowed_code_paths=["click/testing.py"],
        scope_boundaries="\n".join(
            [
                "click/testing.py implementation behavior",
                "tests/test_testing.py regression coverage",
            ]
        ),
    )

    text = workspace_acut.render_statement(package)

    assert "## Editable Paths" in text
    assert "- click/testing.py" in section(text, "Editable Paths")
    assert "tests/test_testing.py" not in section(text, "Editable Paths")
    assert "tests/test_testing.py regression coverage" not in section(text, "Scope Boundary")
    assert "tests/test_testing.py regression coverage" in section(text, "Non-Editable Paths")
    assert "Do not edit tests" in section(text, "Non-Editable Paths")


def test_click_generic_statements_do_not_present_tests_as_editable() -> None:
    packages = {package.task_id: package for package in workspace_acut.load_generic_packages(Path.cwd())}

    click_002 = workspace_acut.render_statement(packages["click__rbench__002"])
    click_003 = workspace_acut.render_statement(packages["click__rbench__003"])

    assert "- click/testing.py" in section(click_002, "Editable Paths")
    assert "tests/test_testing.py" not in section(click_002, "Editable Paths")
    assert "tests/test_testing.py regression coverage" in section(click_002, "Non-Editable Paths")

    editable_003 = section(click_003, "Editable Paths")
    assert "- click/core.py" in editable_003
    assert "- click/termui.py" in editable_003
    assert "tests/test_termui.py" not in editable_003
    assert "tests/test_termui.py regression coverage" in section(click_003, "Non-Editable Paths")


def test_load_repo_history_pilot_package_uses_editable_verifier(tmp_path: Path) -> None:
    repo, base_commit = make_repo(tmp_path)
    exp = workspace_acut.phase0_root(tmp_path)
    (exp / "certified_tasks").mkdir()
    (exp / "releases").mkdir()
    (exp / "target_profiles").mkdir()
    target_commit = base_commit
    certified = {
        "task_id": "humanize__hist__002",
        "base_commit": base_commit,
        "target_commit": target_commit,
        "solver_facing_statement": "Update naturaldelta behavior.",
        "harness_test_command": "uv run --project experiments/phase0_headroom --with \"setuptools<81\" --with freezegun --with \"pytest>=9\" python -m pytest -q {test_files}",
        "code_files": ["src/humanize/time.py"],
        "test_files": ["tests/test_time.py"],
        "scope_boundaries": "Modify only humanize time behavior.",
    }
    workspace_acut.write_jsonl(exp / "certified_tasks" / "humanize_certified_tasks.jsonl", [certified])
    workspace_acut.write_json(
        exp / "releases" / "humanize_phase0_pilot_release.json",
        {
            "pilot_grade": True,
            "splits": {"B_real": ["humanize__hist__002"], "W_real": []},
            "tasks": [{"task_id": "humanize__hist__002", "split": "B_real"}],
        },
    )
    workspace_acut.write_json(
        exp / "target_profiles" / "humanize_target_profile.json",
        {"local_repo": str(repo), "test_command": certified["harness_test_command"]},
    )

    packages = workspace_acut.load_repo_history_pilot_packages(tmp_path, "humanize")

    assert len(packages) == 1
    package = packages[0]
    assert package.repo_id == "humanize"
    assert package.source_repo == repo
    assert package.allowed_code_paths == ["src/humanize/time.py"]
    assert package.test_paths == ["tests/test_time.py"]
    assert package.verifier_command[:4] == ["uv", "run", "--with-editable", "."]
    assert str(exp) in package.verifier_command


def test_toolz_statement_keeps_useful_scope_boundary() -> None:
    packages = {package.task_id: package for package in workspace_acut.load_toolz_packages(Path.cwd())}

    text = workspace_acut.render_statement(packages["toolz__hist__010"])

    assert "- toolz/functoolz.py" in section(text, "Editable Paths")
    assert "Add the helper without changing existing pipe behavior." in section(text, "Scope Boundary")
    assert "Hidden verifier material" in text


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
