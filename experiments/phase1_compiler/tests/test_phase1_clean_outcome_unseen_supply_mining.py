from __future__ import annotations

import phase1_clean_outcome_unseen_supply_mining as mining


def candidate_row(task_id: str = "boltons__hist__018", target_commit: str = "target-1") -> dict:
    return {
        "task_id": task_id,
        "repo_id": "boltons",
        "target_commit": target_commit,
        "task_time": "2022-12-07T18:22:36-08:00",
        "candidate_filter_status": "accepted",
        "changed_files": ["boltons/timeutils.py", "tests/test_timeutils.py"],
        "code_files": ["boltons/timeutils.py"],
        "test_files": ["tests/test_timeutils.py"],
        "module_or_package": ["timeutils"],
        "hardened_reject_reasons": ["source_diagnostic_only"],
        "gates": {
            "checkout": "pass",
            "oracle_extractable": "pass",
            "no_op_fail": "pass",
            "reference_pass": "pass",
            "known_bad_fail": "pass",
            "flakiness_check": "pass",
            "scope_clarity_review": "pass",
            "cost_boundedness": "pass",
            "taxonomy_labelability": "pass",
        },
    }


def issue_context() -> dict:
    return {
        "ref": "issue:319",
        "classification": "problem_context",
        "summary": "date_range handles December year steps incorrectly",
        "body_summary": "Minimal reproduction for December start and yearly step.",
    }


def test_outcome_seen_task_ids_are_never_promoted() -> None:
    review = mining.review_candidate(
        candidate_row(),
        extension_task_id="boltons__clean_ext__001",
        context=issue_context(),
        outcome_seen_task_ids={"boltons__hist__018"},
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "previous_acut_outcome_seen" in review["promotion_blockers"]


def test_outcome_seen_target_commits_are_never_promoted_under_renamed_task_id() -> None:
    review = mining.review_candidate(
        candidate_row(target_commit="seen-target"),
        extension_task_id="boltons__clean_ext__001",
        context=issue_context(),
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits={"seen-target"},
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "previous_acut_target_commit_seen" in review["promotion_blockers"]


def test_solution_exposure_rows_are_rejected() -> None:
    row = candidate_row()
    row["hardened_reject_reasons"] = ["solution_exposure_risk"]

    review = mining.review_candidate(
        row,
        extension_task_id="boltons__clean_ext__001",
        context=issue_context(),
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "solution_exposure_risk" in review["promotion_blockers"]


def test_project_heavy_ambiguous_rows_are_not_promoted() -> None:
    row = candidate_row()
    row["changed_files"] = [".github/workflows/tests.yaml", ".travis.yml", "appveyor.yml", "boltons/jsonutils.py"]
    row["subject"] = "Tox GH Action"

    review = mining.review_candidate(
        row,
        extension_task_id="boltons__clean_ext__001",
        context=issue_context(),
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "keep_manual_review_required"
    assert "scope_context_project_heavy_or_ambiguous" in review["promotion_blockers"]


def test_commit_message_only_context_is_diagnostic_only() -> None:
    review = mining.review_candidate(
        candidate_row(),
        extension_task_id="boltons__clean_ext__001",
        context={"ref": "commit:abc", "classification": "diagnostic_only_context", "summary": "fix bug"},
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "commit_message_only_source" in review["promotion_blockers"]


def test_extension_ids_do_not_collide_with_existing_history_or_extension_ids() -> None:
    task_id = mining.extension_task_id(
        "boltons",
        existing_task_ids={"boltons__hist__018", "boltons__clean_ext__001"},
    )

    assert task_id == "boltons__clean_ext__002"


def test_overlay_preserves_prior_supply_and_requires_cutoff_feasibility() -> None:
    prior_tasks = [
        {"task_id": "boltons__hist__011", "repo_id": "boltons", "split": "B_real"},
        {"task_id": "boltons__hist__022", "repo_id": "boltons", "split": "W_real"},
        {"task_id": "boltons__hist__023", "repo_id": "boltons", "split": "W_real"},
    ]
    promoted = [
        {
            "task_id": "boltons__clean_ext__001",
            "repo_id": "boltons",
            "split": "B_real",
            "promotion_decision": "promote_to_clean_benchmark_candidate",
        }
    ]

    blocked = mining.overlay_payload(
        prior_promoted_tasks=prior_tasks,
        promoted_reviews=promoted,
        minimum_clean_split={"B_real": 2, "W_real": 2},
        cutoff_feasibility={"boltons": {"clean_validation_ready": False}},
    )
    ready = mining.overlay_payload(
        prior_promoted_tasks=prior_tasks,
        promoted_reviews=promoted,
        minimum_clean_split={"B_real": 2, "W_real": 2},
        cutoff_feasibility={"boltons": {"clean_validation_ready": True}},
    )

    assert blocked["promoted_by_split"]["B_real"] == ["boltons__hist__011", "boltons__clean_ext__001"]
    assert blocked["clean_supply_ready"] is False
    assert ready["clean_supply_ready"] is True
    assert ready["predictive_validity_established"] is False
