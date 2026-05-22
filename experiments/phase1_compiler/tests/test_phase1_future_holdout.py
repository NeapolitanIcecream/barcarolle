from __future__ import annotations

from datetime import timedelta

import phase1_future_holdout as holdout


def task(task_id: str, repo_id: str = "boltons", task_time: str | None = "2026-01-01T00:00:00+00:00") -> dict:
    return {
        "task_id": task_id,
        "repo_id": repo_id,
        "task_time": task_time,
        "status": "certified",
        "module_or_package": ["core"],
        "task_type_proxy": "behavior_or_feature_or_bugfix",
    }


def test_repo_time_sorting_uses_aware_task_timestamps() -> None:
    rows = [
        task("boltons__hist__002", task_time="2026-01-03T00:00:00+00:00"),
        task("boltons__hist__001", task_time="2026-01-01T23:00:00-01:00"),
    ]

    sorted_rows = holdout.sort_clean_tasks(rows)

    assert [row["task_id"] for row in sorted_rows] == ["boltons__hist__001", "boltons__hist__002"]
    assert holdout.parse_task_time(sorted_rows[0]["task_time"]).tzinfo is not None


def test_cutoff_selection_applies_embargo_between_compile_and_holdout() -> None:
    rows = [
        task("boltons__hist__001", task_time="2026-01-01T00:00:00+00:00"),
        task("boltons__hist__002", task_time="2026-01-02T00:00:00+00:00"),
        task("boltons__hist__003", task_time="2026-01-20T00:00:00+00:00"),
        task("boltons__hist__004", task_time="2026-01-21T00:00:00+00:00"),
    ]

    plan = holdout.select_cutoff_for_repo(
        "boltons",
        rows,
        embargo_gap_days=14,
        preferred_b=2,
        preferred_h=2,
        minimum_b=2,
        minimum_h=2,
        model_snapshot_date=None,
        model_snapshot_status="unknown",
    )

    assert plan["clean_validation_ready"] is True
    assert plan["validation_size"] == "preferred"
    assert plan["b_eval_task_ids"] == ["boltons__hist__001", "boltons__hist__002"]
    assert plan["h_future_task_ids"] == ["boltons__hist__003", "boltons__hist__004"]
    assert holdout.parse_task_time(plan["T_holdout_start"]) == holdout.parse_task_time(plan["T_compile_end"]) + timedelta(days=14)


def test_seen_outcomes_are_excluded_from_clean_validation() -> None:
    row = task("boltons__hist__007")

    classified = holdout.classify_task(
        row,
        benchmark_grade_task_ids={"boltons__hist__007"},
        outcome_seen_task_ids={"boltons__hist__007"},
        diagnostic_only_repos=set(),
        excluded_target_repos=set(),
    )

    assert classified.clean_eligible is False
    assert "previous_acut_outcome_seen" in classified.exclusion_reasons


def test_humanize_is_excluded_from_validation_grade_use() -> None:
    row = task("humanize__hist__001", repo_id="humanize")

    classified = holdout.classify_task(
        row,
        benchmark_grade_task_ids={"humanize__hist__001"},
        outcome_seen_task_ids=set(),
        diagnostic_only_repos={"humanize"},
        excluded_target_repos=set(),
    )

    assert classified.clean_eligible is False
    assert classified.exclusion_reasons == ["diagnostic_only_source_provenance"]


def test_cutoff_selection_falls_back_from_preferred_to_minimum_counts() -> None:
    rows = [
        task("boltons__hist__001", task_time="2026-01-01T00:00:00+00:00"),
        task("boltons__hist__002", task_time="2026-01-02T00:00:00+00:00"),
        task("boltons__hist__003", task_time="2026-01-20T00:00:00+00:00"),
        task("boltons__hist__004", task_time="2026-01-21T00:00:00+00:00"),
    ]

    plan = holdout.select_cutoff_for_repo(
        "boltons",
        rows,
        embargo_gap_days=14,
        preferred_b=3,
        preferred_h=3,
        minimum_b=2,
        minimum_h=2,
        model_snapshot_date=None,
        model_snapshot_status="unknown",
    )

    assert plan["clean_validation_ready"] is True
    assert plan["validation_size"] == "minimum"


def test_cutoff_selection_blocks_when_clean_supply_is_insufficient() -> None:
    rows = [
        task("boltons__hist__001", task_time="2026-01-01T00:00:00+00:00"),
        task("boltons__hist__002", task_time="2026-01-02T00:00:00+00:00"),
    ]

    plan = holdout.select_cutoff_for_repo(
        "boltons",
        rows,
        embargo_gap_days=14,
        preferred_b=2,
        preferred_h=2,
        minimum_b=2,
        minimum_h=2,
        model_snapshot_date=None,
        model_snapshot_status="unknown",
    )

    assert plan["clean_validation_ready"] is False
    assert "insufficient_clean_outcome_unseen_supply" in plan["blockers"]


def test_unknown_model_snapshot_preserves_repo_time_holdout_without_contamination_claim() -> None:
    plan = holdout.cutoff_plan_payload(
        repo_plans={
            "boltons": {
                "repo_id": "boltons",
                "clean_validation_ready": True,
                "b_eval_task_ids": ["boltons__hist__001", "boltons__hist__002"],
                "h_future_task_ids": ["boltons__hist__003", "boltons__hist__004"],
            }
        },
        embargo_gap_days=14,
        model_snapshot_status="unknown",
    )

    assert plan["repo_time_holdout_not_contamination_proof"] is True
    assert plan["predictive_validity_established"] is False


def test_clean_supply_overlay_rows_are_eligible_without_mutating_hardening_status() -> None:
    row = {
        **task("boltons__clean_ext__001"),
        "clean_supply_evidence_level": "clean_supply_overlay_sidecar",
        "clean_overlay_promotion_decision": "promote_to_clean_benchmark_candidate",
        "original_hardening_status": "diagnostic_only",
    }

    classified = holdout.classify_task(
        row,
        benchmark_grade_task_ids=set(),
        outcome_seen_task_ids=set(),
        diagnostic_only_repos=set(),
        excluded_target_repos=set(),
    )

    assert classified.clean_eligible is True
    assert classified.exclusion_reasons == []


def test_clean_supply_overlay_payload_is_converted_to_sidecar_candidate_tasks() -> None:
    payload = {
        "evidence_level": "clean_supply_overlay_sidecar",
        "promoted_tasks": [
            {
                "task_id": "boltons__clean_ext__001",
                "repo_id": "boltons",
                "task_time": "2022-12-07T18:22:36-08:00",
                "promotion_decision": "promote_to_clean_benchmark_candidate",
                "original_hardening_status": "diagnostic_only",
            }
        ],
    }

    rows = holdout.overlay_candidate_tasks(payload, source_path="overlay.json")

    assert rows == [
        {
            "task_id": "boltons__clean_ext__001",
            "repo_id": "boltons",
            "task_time": "2022-12-07T18:22:36-08:00",
            "status": "certified",
            "module_or_package": [],
            "task_type_proxy": "behavior_or_feature_or_bugfix",
            "clean_supply_evidence_level": "clean_supply_overlay_sidecar",
            "clean_overlay_promotion_decision": "promote_to_clean_benchmark_candidate",
            "clean_supply_overlay_source": "overlay.json",
            "original_hardening_status": "diagnostic_only",
            "target_commit_unseen": True,
        }
    ]


def test_boltons_only_paid_scoreable_run_closes_as_pilot_not_predictive() -> None:
    config = {
        "acceptance": {
            "policy_violations_max": 0,
            "non_scoreable_cells_max_per_split": 2,
            "predictive_validity_claim_min_repos": 2,
            "predictive_validity_claim_min_holdout_scoreable_cells": 12,
        }
    }
    supply = {"selected_repos": ["boltons"]}
    b_summary = {"scoreable_cell_count": 8, "non_scoreable_count": 0}
    h_summary = {"scoreable_cell_count": 8, "non_scoreable_count": 0}

    outcome = holdout.paid_validation_decision_outcome(
        config,
        supply,
        b_summary=b_summary,
        h_summary=h_summary,
        policy_violation_count=0,
    )

    assert outcome["primary_decision_label"] == "boltons_clean_future_holdout_pilot_complete_insufficient_sample"
    assert outcome["predictive_validity_established"] is False
    assert "predictive_validity_min_target_repos_not_met" in outcome["blockers"]
    assert "predictive_validity_min_holdout_scoreable_cells_not_met" in outcome["blockers"]
    assert outcome["recommended_next_runbook"] == "mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation"


def test_two_repo_preregistration_combines_existing_paid_and_planned_clean_supply() -> None:
    config = {
        "_path": "experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml",
        "acceptance": {
            "min_target_repos": 2,
            "min_holdout_scoreable_cells": 12,
            "policy_violations_max": 0,
            "non_scoreable_cells_max_per_split": 2,
        },
        "second_repo_planned_paid_prefixes": {
            "b_eval": "phase1_two_repo_future_holdout_attrs_b_eval",
            "h_future": "phase1_two_repo_future_holdout_attrs_h_future",
        },
        "adapters": {"ids": ["codex_workspace", "kilo_workspace"]},
    }
    clean_supply = {
        "clean_supply_ready": True,
        "selected_repos": ["boltons", "attrs"],
        "existing_paid_evidence": {"boltons": {"h_future_scoreable_cells": 8}},
        "second_repo_clean_supply": {
            "selected_b_eval_task_ids": ["attrs__hist__001", "attrs__hist__002"],
            "selected_h_future_task_ids": ["attrs__hist__003", "attrs__hist__004"],
        },
        "second_repo_planned_paid_prefixes": config["second_repo_planned_paid_prefixes"],
        "planned_second_repo_b_eval_cells": 4,
        "planned_second_repo_h_future_cells": 4,
        "total_h_future_scoreable_capacity_if_second_repo_scoreable": 12,
        "adapters": config["adapters"]["ids"],
        "blockers": [],
    }

    prereg = holdout.two_repo_preregistration_payload(config, clean_supply)

    assert prereg["status"] == "frozen"
    assert prereg["selected_repos"] == ["boltons", "attrs"]
    assert prereg["planned_second_repo_cells"]["h_future"] == 4
    assert prereg["total_h_future_scoreable_capacity_if_second_repo_scoreable"] == 12
    assert prereg["paid_second_repo_acut_calls_made"] is False
    assert prereg["predictive_validity_established"] is False


def test_two_repo_preregistration_blocks_when_capacity_is_below_threshold() -> None:
    config = {
        "_path": "experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml",
        "acceptance": {"min_target_repos": 2, "min_holdout_scoreable_cells": 12},
    }
    clean_supply = {
        "clean_supply_ready": False,
        "selected_repos": ["boltons", "attrs"],
        "existing_paid_evidence": {"boltons": {"h_future_scoreable_cells": 8}},
        "second_repo_clean_supply": {"selected_b_eval_task_ids": [], "selected_h_future_task_ids": []},
        "second_repo_planned_paid_prefixes": {},
        "planned_second_repo_b_eval_cells": 0,
        "planned_second_repo_h_future_cells": 0,
        "total_h_future_scoreable_capacity_if_second_repo_scoreable": 8,
        "adapters": ["codex_workspace", "kilo_workspace"],
        "blockers": ["min_holdout_scoreable_cells_not_met_if_second_repo_scoreable"],
    }

    prereg = holdout.two_repo_preregistration_payload(config, clean_supply)

    assert prereg["status"] == "blocked_clean_supply"
    assert prereg["recommended_next_runbook"] == "expand_clean_supply_sources_or_add_manual_canaries"
    assert prereg["predictive_validity_established"] is False
