from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_pre_paid_replication_compiler_readiness as readiness  # noqa: E402


def test_preflight_records_boundary_and_previous_evidence() -> None:
    payload = readiness.build_preflight()

    assert payload["boundary_checks"]["previous_paid_scoreable_cells_eq_32"] is True
    assert payload["boundary_checks"]["previous_policy_violations_eq_0"] is True
    assert payload["boundary_checks"]["previous_predictive_validity_established_false"] is True
    assert payload["boundary_checks"]["new_paid_acut_replication_allowed_in_this_runbook"] is False
    assert payload["previous_evidence"]["terminal_status_counts"] == {"verified_fail": 11, "verified_pass": 21}


def test_threshold_preregistration_freezes_primary_rule_before_selection() -> None:
    payload = readiness.build_threshold_preregistration()

    assert payload["frozen_before_release_selection"] is True
    assert payload["primary_rule"]["gap_threshold"] == 0.15
    assert payload["policy_rule"]["policy_violations"] == 0
    assert payload["target_profile_boundary"]["H_future_is_validation_data_not_target_profile"] is True
    assert "count previous H_future outcomes as validation for a post-hoc redesigned release" in payload["previous_paid_evidence_use_policy"]["not_allowed"]


def test_inventory_normalizes_all_local_certified_candidates_once() -> None:
    payload = readiness.build_candidate_inventory()
    rows = payload["rows"]

    assert payload["candidate_count"] == 60
    assert len({row["task_id"] for row in rows}) == len(rows)
    assert payload["summary"]["eligible_for_next_release_count"] >= 20
    assert payload["historical_outcome_policy"]["outcome_fields_drive_target_profile_estimation"] is False
    for row in rows:
        assert row["repo_id"]
        assert row["task_time"]
        assert row["source_kind"]
        assert row["statement_digest"].startswith("sha256:")
        assert row["editable_paths"]
        assert row["test_paths"]
        assert isinstance(row["historical_paid_outcome_summary"], dict)


def test_target_profiles_exclude_h_future_outcomes_as_inputs() -> None:
    payload = readiness.build_target_profiles()

    assert payload["included_repo_ids"] == ["attrs", "boltons"]
    assert payload["outcome_fields_used"] == []
    assert payload["H_future_is_target_profile"] is False
    for profile in payload["profiles"]:
        assert profile["candidate_support_count"] >= 16
        assert set(profile["profile_weight_tables"]) == set(readiness.PROFILE_DIMENSIONS)


def test_split_matching_recommends_weighted_design_without_paid_outcomes() -> None:
    payload = readiness.build_strata_matching()
    designs = {design["design_id"]: design for design in payload["designs"]}

    assert payload["recommended_design_id"] == "barcarolle_weighted_time_family_matched"
    assert designs["barcarolle_weighted_time_family_matched"]["outcome_fields_used_for_selection"] == []
    assert designs["barcarolle_weighted_time_family_matched"]["metrics"]["mean_l1_distance_to_target_profile"] <= designs["repo_unweighted_same_budget"]["metrics"]["mean_l1_distance_to_target_profile"]
    for design in designs.values():
        for task_ids in design["task_ids_by_repo_split"].values():
            assert len(task_ids) == readiness.TASKS_PER_REPO_SPLIT


def test_statement_gate_passes_without_paid_llm_calls() -> None:
    payload = readiness.build_statement_quality_gate()

    assert payload["status"] == "pass"
    assert payload["new_paid_llm_calls_made"] is False
    assert payload["blocking_task_ids"] == []
    assert payload["verdict_counts"]["pass"] + payload["verdict_counts"]["pass_with_minor_risk"] == payload["audited_task_count"]


def test_release_candidates_and_entry_gate_are_pilot_ready() -> None:
    release = readiness.build_release_candidates()
    power = readiness.build_power_and_cost_plan()
    entry = readiness.build_entry_gate()
    decision = readiness.build_decision()

    assert release["recommended_release_candidate_id"] == "barcarolle_weighted_time_family_matched"
    assert release["recommended_planned_cells"] == 32
    assert entry["entry_status"] == "ready_for_paid_replication"
    assert entry["replication_grade"] == "pilot_grade_ready_not_precision_target"
    assert entry["paid_acut_calls_already_run_for_this_release"] is False
    assert power["status"] == "pilot_ready_precision_underpowered"
    assert decision["final_decision"] == "ready_for_pilot_paid_replication"
    assert decision["new_paid_acut_calls_made"] is False
    assert decision["new_paid_llm_calls_made"] is False


def test_entry_gate_contains_no_local_absolute_paths_or_secret_values() -> None:
    payload = readiness.build_entry_gate()
    serialized = json.dumps(payload, sort_keys=True)

    assert "<external-user-home>/" not in serialized
    assert "sk-" not in serialized
    assert payload["required_env"] == {"LLM_API_KEY": "required", "LLM_BASE_URL": "required"}
