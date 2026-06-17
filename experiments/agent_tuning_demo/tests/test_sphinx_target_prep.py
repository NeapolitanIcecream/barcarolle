from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import sphinx_target_prep as prep  # noqa: E402


def certified_tasks(count: int) -> list[dict[str, object]]:
    return [
        {
            "task_id": f"sphinx__hist__{index + 1:04d}",
            "target_commit": "b" * 40,
            "base_commit": "a" * 40,
            "task_time": "2024-01-01T00:00:00+00:00",
            "time_bucket": "2024_plus",
            "module_family": "config",
            "changed_implementation_files": "sphinx/config.py",
            "changed_test_files": "tests/test_config.py",
            "pytest_entry_files": "tests/test_config.py",
            "winning_verifier_profile": "py312_2024_editable",
            "verifier_duration_seconds": 1.0,
            "source_certification_provenance": "unit_test",
            "evidence_digest": "sha256:" + "0" * 64,
        }
        for index in range(count)
    ]


def test_uv_pytest_command_stays_outside_barcarolle_project() -> None:
    profile = {
        "python_version": "3.14",
        "exclude_newer_date": "2026-06-17",
        "dependency_constraints": [".", "pytest>=9,<10"],
    }

    command = prep.uv_pytest_command(profile, ["tests/test_util/test_util.py"])

    assert command[:4] == ["uv", "run", "--no-project", "--isolated"]
    assert "--project" not in command
    assert command[-2:] == ["tests/test_util/test_util.py", "-q"]


def test_command_shape_redacts_targeted_test_paths() -> None:
    command = [
        "uv",
        "run",
        "--no-project",
        "--with",
        ".",
        "--",
        "python",
        "-m",
        "pytest",
        "tests/test_a.py",
        "tests/test_b.py",
        "-q",
    ]

    shaped = prep.command_shape(command)

    assert shaped.count("<targeted_test_paths>") == 1
    assert "tests/test_a.py" not in shaped
    assert "tests/test_b.py" not in shaped


def test_classify_speed_uses_target_prep_thresholds() -> None:
    assert prep.classify_speed([]) == "not_measured"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 59.9}]) == "ideal_under_60s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 179.9}]) == "acceptable_under_180s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 599.9}]) == "risky_180s_to_600s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 600}]) == "unusable_over_600s"
    assert prep.classify_speed([{"status": "failed", "duration_seconds": 1.0}]) == "risky_or_unusable_partial_failure"


def test_setup_report_escapes_backticks_in_subject() -> None:
    payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "smoke_results": [],
        "smoke_pass_count": 0,
        "smoke_count": 0,
        "targeted_verifier_time_class": "not_measured",
        "repo_id": "sphinx",
        "local_checkout": "experiments/phase0_headroom/external_repos/sphinx",
        "head_commit": "a" * 40,
        "head_time": "2026-06-17T00:00:00+00:00",
        "head_subject": "Document `graphviz` requirement",
    }

    report = prep.setup_smoke_report(payload)

    assert "Document 'graphviz' requirement" in report


def test_historical_profiles_use_date_bucket_and_exclude_newer() -> None:
    profile = {
        "dependency_setup_policy": {
            "current_smoke_profile": {
                "profile_id": "current",
                "python_version": "3.14",
                "exclude_newer_date": "2026-06-17",
                "dependency_constraints": ["."],
            },
            "historical_verifier_profiles": [
                {
                    "profile_id": "old",
                    "active_from": "2018-01-01",
                    "python_version": "3.9",
                    "dependency_constraints": ["."],
                },
                {
                    "profile_id": "new",
                    "active_from": "2024-01-01",
                    "python_version": "3.12",
                    "dependency_constraints": ["."],
                },
            ],
        }
    }

    selected = prep.historical_profiles(profile, "2022-06-01T00:00:00+00:00")

    assert [row["profile_id"] for row in selected] == ["old"]
    assert all(row["exclude_newer_date"] == "2022-11-28" for row in selected)


def test_sphinx_candidate_path_classification_stays_inside_package_root() -> None:
    assert prep.is_impl_path("sphinx/config.py") is True
    assert prep.is_impl_path("tests/test_config/test_config.py") is False
    assert prep.is_test_path("tests/test_config/test_config.py") is True
    assert prep.is_pytest_entry_path("tests/test_config/test_config.py") is True
    assert prep.is_test_path("tests/roots/test-basic/conf.py") is True
    assert prep.is_pytest_entry_path("tests/roots/test-basic/conf.py") is False
    assert prep.is_impl_path("doc/conf.py") is False


def test_replay_base_row_keeps_required_inventory_fields() -> None:
    row = {
        "task_id": "sphinx__hist__0001",
        "target_commit": "b" * 40,
        "base_commit": "a" * 40,
        "task_time": "2024-01-01T00:00:00+00:00",
        "module_family": "config",
        "implementation_files": ["sphinx/config.py"],
        "test_files": ["tests/test_config/test_config.py"],
        "pytest_files": ["tests/test_config/test_config.py"],
        "public_source_context_reference": "pr_or_issue:1",
        "preliminary_risk_label": "normal",
    }

    base = prep.replay_base_row(row)

    assert base["changed_implementation_files"] == ["sphinx/config.py"]
    assert base["changed_test_files"] == ["tests/test_config/test_config.py"]
    assert base["pytest_entry_files"] == ["tests/test_config/test_config.py"]


def test_time_bucket_policy_matches_runbook_ranges() -> None:
    assert prep.time_bucket(2021) == "pre_2022"
    assert prep.time_bucket(2022) == "2022_2023"
    assert prep.time_bucket(2023) == "2022_2023"
    assert prep.time_bucket(2024) == "2024_plus"


def test_certification_csv_row_exposes_gate_booleans() -> None:
    row = {
        "task_id": "sphinx__hist__0001",
        "target_commit": "b" * 40,
        "base_commit": "a" * 40,
        "task_time": "2024-01-01T00:00:00+00:00",
        "module_family": "config",
        "terminal_status": "passed",
        "failure_label": "",
        "winning_profile_id": "py312_2024_editable",
        "verifier_duration_seconds": 1.2345,
        "changed_implementation_files": ["sphinx/config.py"],
        "changed_test_files": ["tests/test_config.py"],
        "pytest_entry_files": ["tests/test_config.py"],
    }

    flat = prep.certification_csv_row(row)

    assert flat["base_workspace_prepared"] is True
    assert flat["changed_tests_reconstructed"] is True
    assert flat["hidden_verifier_injection_works"] is True
    assert flat["base_reference_behavior_meaningful"] is True
    assert flat["verifier_duration_seconds"] == 1.234


def test_build_rolling_origin_policy_uses_projected_certified_count() -> None:
    inventory = {"candidate_count": 180}
    wave = {
        "sample_size": 24,
        "pass_count": 16,
        "conversion_rate": 0.6667,
        "verifier_duration_summary": {"median_seconds": 8.0},
        "dominant_failure_labels": {},
    }

    payload = prep.build_rolling_origin_policy(inventory, wave)

    assert payload["evidence_inputs"]["projected_certified_count_from_wave"] == 120
    assert payload["primary_policy"]["window_count"] == 3
    assert payload["paid_cell_estimates"]["baseline_discovery_cells_per_window"] == 160
    assert payload["paid_cell_estimates"]["selected_only_baseline_cells_per_window"] == 80
    assert payload["paid_cell_estimates"]["future_only_baseline_cells_per_window"] == 80
    assert payload["paid_cell_estimates"]["tuning_before_after_cells_per_window"] == 40


def test_rolling_origin_protocol_v2_selects_from_history_pool() -> None:
    payload = prep.build_rolling_origin_protocol_v2()

    assert "history_pool_before_origin" in payload["field_definitions"]
    assert "selected_benchmark_from_history" in payload["field_definitions"]
    assert payload["selector_leakage_rules"]["future_holdout_task_ids_allowed_before_selection"] is False
    assert "future_holdout_after_origin task IDs" in payload["selector_leakage_rules"]["selector_inputs_forbidden"]


def test_window_manifest_lists_history_pool_and_future_holdout_ids() -> None:
    payload = prep.build_window_manifest_from_tasks(certified_tasks(100))
    first_window = payload["windows"][0]

    assert payload["window_threshold_state"] == "preferred_policy_supported"
    assert first_window["origin_id"] == "origin_40"
    assert first_window["history_pool_before_origin"]["task_ids"] == [f"sphinx__hist__{index + 1:04d}" for index in range(40)]
    assert first_window["future_holdout_after_origin"]["task_ids"] == [f"sphinx__hist__{index + 1:04d}" for index in range(40, 60)]
    assert first_window["selected_benchmark_from_history"]["selected_task_ids"] == []
    assert first_window["selected_benchmark_from_history"]["allowed_task_ids"] == first_window["history_pool_before_origin"]["task_ids"]


def test_window_manifest_minimum_policy_at_80_tasks() -> None:
    payload = prep.build_window_manifest_from_tasks(certified_tasks(80))

    assert payload["window_threshold_state"] == "minimum_policy_supported"
    assert [window["origin_id"] for window in payload["windows"]] == ["origin_40", "origin_60"]


def test_paid_cell_accounting_uses_selected_plus_future_for_baseline() -> None:
    window_manifest = prep.build_window_manifest_from_tasks(certified_tasks(100))
    payload = prep.build_paid_cell_accounting(window_manifest)

    assert payload["per_window"][0]["selected_benchmark_cells"] == 80
    assert payload["per_window"][0]["future_holdout_cells"] == 80
    assert payload["per_window"][0]["naive_baseline_discovery_cells"] == 160
    assert payload["total_naive_baseline_discovery_cells"] == 480
    assert payload["deduplicated_unique_task_agent_cells"]["known_future_holdout_unique_task_count"] == 60
    assert payload["deduplicated_unique_task_agent_cells"]["selected_plus_future_unique_cells_range_depends_on_next_selector"] == [320, 400]
