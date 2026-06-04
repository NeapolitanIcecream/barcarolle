from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path

import phase1_three_repo_paid_readiness_packaging as packaging


def isolated_config(tmp_path: Path, monkeypatch) -> dict[str, object]:
    config = copy.deepcopy(packaging.load_config())
    config["outputs"] = {key: str(tmp_path / "results" / Path(path).name) for key, path in config["outputs"].items()}
    config["reports"] = {key: str(tmp_path / "reports" / Path(path).name) for key, path in config["reports"].items()}
    monkeypatch.setattr(packaging, "RELEASE_SELECTION_CONFIG", tmp_path / "phase1_three_repo_release_selection.yaml")
    monkeypatch.setattr(packaging, "THRESHOLD_CONFIG", tmp_path / "phase1_three_repo_paid_validation_thresholds.yaml")
    return config


def test_task_table_freezes_only_release_eligible_three_repo_supply() -> None:
    config = packaging.load_config()

    rows = packaging.task_table_rows(config)
    counts = Counter(row["repo_id"] for row in rows)
    encoded = json.dumps(rows, sort_keys=True)

    assert counts == {"attrs": 31, "boltons": 35, "click": 30}
    assert len(rows) == 96
    assert {"attrs__v2__218", "attrs__v2__231", "attrs__v2__237"} <= {row["candidate_id"] for row in rows}
    assert all(row["technical_certification_profile"]["technical_certified"] is True for row in rows)
    assert all(row["raw_diff_committed"] is False for row in rows)
    assert all(row["raw_command_log_committed"] is False for row in rows)
    assert "diff --git" not in encoded
    assert "raw_logs_storage" not in encoded


def test_source_quality_audit_accepts_all_selected_tasks_and_calls_out_click_margin(tmp_path: Path, monkeypatch) -> None:
    config = isolated_config(tmp_path, monkeypatch)

    audit = packaging.build_source_quality_audit(config)

    assert audit["audit_status_counts"] == {"accepted_for_paid_package": 96}
    assert audit["tasks_requiring_exclusion_or_repair"] == []
    assert audit["material_leakage_task_count"] == 0
    assert audit["ambiguity_task_count"] == 0
    assert audit["click_audit"]["release_eligible_count"] == 30
    assert audit["click_audit"]["thin_margin"] is True
    assert audit["paid_llm_review_used"] is False


def test_split_plan_is_deterministic_repo_stratified_and_not_weighted_primary(tmp_path: Path, monkeypatch) -> None:
    config = isolated_config(tmp_path, monkeypatch)
    packaging.build_source_quality_audit(config)

    first = packaging.build_split_plan(config)
    second = packaging.build_split_plan(config)

    assert first["assignments"] == second["assignments"]
    assert first["primary_design"] == "repo_stratified"
    assert first["old_weighted_design_primary"] is False
    assert first["H_future_outcomes_used_for_selection_or_weighting"] is False
    assert first["split_counts_by_repo"] == {
        "attrs": {"B_eval": 16, "H_future": 15},
        "boltons": {"B_eval": 18, "H_future": 17},
        "click": {"B_eval": 15, "H_future": 15},
    }
    assert first["imbalance_diagnostics"]["max_within_repo_split_count_delta"] == 1


def test_baseline_and_threshold_plans_keep_weighted_design_diagnostic_only(tmp_path: Path, monkeypatch) -> None:
    config = isolated_config(tmp_path, monkeypatch)

    baseline = packaging.build_baseline_plan(config)
    thresholds = packaging.build_threshold_preregistration(config)

    weighted = [row for row in baseline["baselines"] if row["design_id"] == "old_weighted_design"]
    assert baseline["primary_design"]["design_id"] == "repo_stratified"
    assert weighted and weighted[0]["role"] == "diagnostic_only"
    assert baseline["post_hoc_promotion_rule"] == "none"
    assert thresholds["thresholds"]["policy_violations_max"] == 0
    assert thresholds["thresholds"]["minimum_scoreability_rate"] == 0.95
    assert thresholds["thresholds"]["primary_gap_threshold"] == 0.15
    assert thresholds["precision_label_rules"]["predictive_validity_claim_before_paid_validation"] is False


def test_entry_gate_is_ready_when_non_paid_artifacts_are_complete_without_running_paid_cells(tmp_path: Path, monkeypatch) -> None:
    config = isolated_config(tmp_path, monkeypatch)
    packaging.build_supply_snapshot(config)
    packaging.build_source_quality_audit(config)
    packaging.build_split_plan(config)
    packaging.build_baseline_plan(config)
    packaging.build_threshold_preregistration(config)
    packaging.build_power_cost_plan(config)

    entry = packaging.build_entry_gate(config, run_tests=False)

    assert entry["status"] == "ready_for_paid_validation_runbook"
    assert entry["paid_ready"] is True
    assert entry["gates"]["no_paid_cells_run"] is True
    assert entry["gates"]["three_repos_at_30_release_eligible"] is True
    assert entry["gates"]["source_quality_audit_passed"] is True
    assert entry["failed_gates"] == []
