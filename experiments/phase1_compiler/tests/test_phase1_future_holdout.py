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
