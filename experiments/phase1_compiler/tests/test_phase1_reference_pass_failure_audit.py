from __future__ import annotations

from pathlib import Path

import phase1_reference_pass_failure_audit as audit
import repo_history_pilot


def reference_failure_row(task_id: str = "attrs__supply_expansion_20260526__001") -> dict:
    return {
        "task_id": task_id,
        "repo_id": task_id.split("__", 1)[0],
        "task_time": "2017-01-02T00:00:00+00:00",
        "first_failing_gate": "reference_pass",
        "review_first_failing_gate": "reference_pass",
        "candidate_filter_status": "accepted",
        "source_context_status": "non_leaky_problem_context",
        "change_size_bucket": "s_21_80",
        "module_or_package": ["_make"],
        "test_files": ["tests/test_make.py"],
        "implementation_files": ["attr/_make.py"],
        "commands": [
            {
                "role": "noop_test_patch_on_base",
                "returncode": 1,
                "duration_seconds": 0.2,
                "stderr_tail_hash": "noopstderr",
                "stdout_tail_hash": audit.EMPTY_SHA,
            },
            {
                "role": "reference_run_1",
                "returncode": 1,
                "duration_seconds": 0.3,
                "stderr_tail_hash": "refstderr",
                "stdout_tail_hash": audit.EMPTY_SHA,
            },
            {
                "role": "reference_run_2",
                "returncode": 1,
                "duration_seconds": 0.3,
                "stderr_tail_hash": "refstderr",
                "stdout_tail_hash": audit.EMPTY_SHA,
            },
        ],
    }


def test_reference_pass_rows_accepts_review_gate_alias() -> None:
    rows = [
        reference_failure_row(),
        {"task_id": "x", "first_failing_gate": "none", "review_first_failing_gate": "reference_pass"},
        {"task_id": "y", "first_failing_gate": "solution_leakage_review"},
    ]

    selected = audit.reference_pass_rows(rows)

    assert [row["task_id"] for row in selected] == ["attrs__supply_expansion_20260526__001", "x"]


def test_inventory_groups_counts_and_selects_per_repo_sample() -> None:
    attrs = reference_failure_row("attrs__supply_expansion_20260526__001")
    boltons = reference_failure_row("boltons__supply_expansion_20260526__001")

    records = [audit.row_inventory_record(row) for row in [attrs, boltons]]
    sample = audit.prioritized_sample([attrs, boltons], per_repo=1)

    assert audit.counter_dict(records, "repo_id") == {"attrs": 1, "boltons": 1}
    assert {row["task_id"] for row in sample} == {
        "attrs__supply_expansion_20260526__001",
        "boltons__supply_expansion_20260526__001",
    }
    assert all(row["priority"] == "high" for row in sample)


def test_result_summary_redacts_raw_output_and_workspace_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "target"
    workspace.mkdir()
    result = repo_history_pilot.CommandResult(
        returncode=1,
        stdout=f"raw stdout from {workspace}\n",
        stderr=f"ModuleNotFoundError: No module named 'hypothesis' in {workspace}\n",
        duration_seconds=0.1,
    )
    env = {"PYTHONPATH": str(workspace)}

    summary = audit.result_summary(
        "A_current_barcarolle_command",
        result,
        ["python", "-m", "pytest", str(workspace / "tests/test_x.py")],
        audit.REPO_ROOT,
        workspace,
        env,
    )

    assert summary["error_class"] == "missing_optional_dependency"
    assert "<workspace>" in summary["command_argv_shape"][-1]
    assert "raw stdout" not in summary
    assert str(workspace) not in summary["sanitized_error_snippet"]


def test_absolute_project_command_rewrites_relative_project_path() -> None:
    command = ["uv", "run", "--project", "experiments/phase0_headroom", "python", "-m", "pytest"]

    rewritten = audit.absolute_project_command(command)

    assert rewritten[3] == str(audit.REPO_ROOT / "experiments/phase0_headroom")


def test_replay_variants_express_command_contract() -> None:
    cfg = repo_history_pilot.PilotConfig(
        repo_id="attrs",
        repo_url="https://example.invalid/attrs.git",
        local_repo=Path("/tmp/attrs"),
        command_template='uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q {test_files}',
        certification_attempts=0,
        pilot_certified_min=0,
        benchmark_grade_min=0,
        result_prefix="attrs_audit",
    )
    workspace = Path("/tmp/workspace")

    variants = audit.replay_variants(cfg, workspace, ["tests/test_make.py"])
    by_name = {variant.name: variant for variant in variants}

    assert by_name["A_current_barcarolle_command"].cwd == audit.REPO_ROOT
    assert by_name["A_current_barcarolle_command"].editable_install is True
    assert "--with-editable" in by_name["A_current_barcarolle_command"].command
    assert by_name["C_no_editable_pythonpath"].editable_install is False
    assert by_name["D_pytest_config_visible"].test_path_style == "relative"
