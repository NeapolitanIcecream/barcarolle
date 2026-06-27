from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import task_generator_evolution as taskgen  # noqa: E402


def certified_rows(count: int, repo_id: str = "mypy") -> list[dict[str, object]]:
    return [
        {
            "task_id": f"{repo_id}__taskgen__{index + 1:04d}",
            "repo_id": repo_id,
            "reservoir_source_type": "mypy_typecheck_data_with_impl",
            "base_commit": "a" * 40,
            "target_commit": "b" * 40,
            "task_time": f"2024-01-{(index % 28) + 1:02d}T00:00:00+00:00",
            "module_family": "type_checker",
            "changed_implementation_files": "mypy/checker.py",
            "changed_test_files": "test-data/unit/check-basic.test",
            "support_oracle_files": "test-data/unit/check-basic.test",
            "verifier_entry_points": "mypy/test/testcheck.py::TypeCheckSuite::check-basic.test",
            "solver_visible_statement_provenance": "pr_or_issue:1",
            "hidden_oracle_provenance": "target_commit_changed_tests_and_support_files",
            "verifier_profile": "py312_data_or_pytest",
            "verifier_command_digest": "sha256:" + "0" * 64,
            "checkout_status": "passed",
            "install_setup_status": "passed_via_reference_command",
            "test_collection_status": "passed",
            "reference_changed_test_result": "passed",
            "base_with_injected_tests_result": "target_test_failure",
            "pass_to_pass_guard_result": "not_run_no_stable_adjacent_guard",
            "subgate_results_json": "[]",
            "certification_duration_seconds": 1.0,
            "leakage_label": "no_hidden_oracle_in_statement",
            "ambiguity_label": "commit_or_issue_context_only",
            "source_confidence_label": "medium",
            "sanitized_evidence_digest": "sha256:" + "1" * 64,
        }
        for index in range(count)
    ]


def test_mypy_data_file_maps_to_typecheck_suite_nodeid() -> None:
    entry_points = taskgen.mypy_entry_points([], ["test-data/unit/check-dataclasses.test"])

    assert entry_points == ["mypy/test/testcheck.py::TypeCheckSuite::check-dataclasses.test"]


def test_mypy_path_classification_separates_impl_data_and_python_tests() -> None:
    assert taskgen.is_mypy_impl_path("mypy/checker.py") is True
    assert taskgen.is_mypy_impl_path("mypy/test/testcheck.py") is False
    assert taskgen.is_mypy_typecheck_data("test-data/unit/check-basic.test") is True
    assert taskgen.is_mypy_typecheck_data("test-data/unit/fine-grained.test") is False
    assert taskgen.is_mypy_support_oracle("mypyc/test-data/run-classes.test") is True


def test_build_windows_uses_history_pool_and_hides_future_from_selection() -> None:
    payload = taskgen.build_windows(
        "mypy",
        {
            "tasks": certified_rows(100),
        },
    )
    first = payload["windows"][0]

    assert payload["window_count"] == 3
    assert first["origin_id"] == "origin_40"
    assert len(first["history_pool_before_origin"]["task_ids"]) == 40
    assert len(first["future_holdout_after_origin"]["task_ids"]) == 20
    assert first["selected_benchmark_from_history"]["selected_task_ids"] == []
    assert first["selected_benchmark_from_history"]["allowed_task_ids"] == first["history_pool_before_origin"]["task_ids"]


def test_paid_cell_accounting_keeps_160_cell_default_per_window() -> None:
    windows = taskgen.build_windows("mypy", {"tasks": certified_rows(80)})

    payload = taskgen.build_paid_cell_accounting([windows])

    assert payload["per_repo"]["mypy"]["window_count"] == 2
    assert payload["per_repo"]["mypy"]["baseline_cells_per_window"] == 160
    assert payload["per_repo"]["mypy"]["total_naive_baseline_discovery_cells"] == 320


def test_manifest_row_records_target_pass_and_base_fail_subgates() -> None:
    replay = {
        "task_id": "mypy__taskgen__0001",
        "repo_id": "mypy",
        "reservoir_source_type": "mypy_typecheck_data_with_impl",
        "base_commit": "a" * 40,
        "target_commit": "b" * 40,
        "task_time": "2024-01-01T00:00:00+00:00",
        "module_family": "type_checker",
        "changed_implementation_files": ["mypy/checker.py"],
        "changed_test_files": ["test-data/unit/check-basic.test"],
        "support_oracle_files": ["test-data/unit/check-basic.test"],
        "verifier_entry_points": ["mypy/test/testcheck.py::TypeCheckSuite::check-basic.test"],
        "solver_visible_statement_provenance": "pr_or_issue:1",
        "source_confidence_label": "medium",
        "winning_profile_id": "py312_data_or_pytest",
        "verifier_duration_seconds": 2.0,
        "commands": [
            {"role": "reference_target", "profile_id": "py312_data_or_pytest", "subgate_label": "passed"},
            {
                "role": "base_with_injected_tests",
                "profile_id": "py312_data_or_pytest",
                "subgate_label": "target_test_failure",
            },
        ],
    }

    row = taskgen.manifest_row_from_replay(replay)

    assert row["reference_changed_test_result"] == "passed"
    assert row["base_with_injected_tests_result"] == "target_test_failure"
    assert row["hidden_oracle_provenance"] == "target_commit_changed_tests_and_support_files"
