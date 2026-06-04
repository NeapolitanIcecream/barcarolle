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


def second_repo_certified_row(task_id: str = "attrs__hist__001", task_time: str = "2020-01-01T00:00:00+00:00") -> dict:
    return {
        "task_id": task_id,
        "repo_id": "attrs",
        "target_commit": f"target-{task_id}",
        "task_time": task_time,
        "status": "certified",
        "candidate_filter_status": "accepted",
        "changed_files": ["src/attr/_make.py", "tests/test_make.py"],
        "code_files": ["src/attr/_make.py"],
        "test_files": ["tests/test_make.py"],
        "module_or_package": ["_make"],
        "gates": {
            "checkout": "pass",
            "oracle_extractable": "pass",
            "no_op_fail": "pass",
            "reference_pass": "pass",
            "known_bad_fail": "pass",
            "flakiness_check": "pass",
            "ambiguity_review": "pass",
            "solution_leakage_review": "pass",
            "scope_clarity_review": "pass",
            "cost_boundedness": "pass",
            "taxonomy_labelability": "pass",
        },
    }


def attrs_problem_context(summary: str = "Fix cache hash incompatibility") -> dict:
    return {
        "ref": "pr:612",
        "classification": "problem_context",
        "summary": summary,
        "body_summary": "Small public report without implementation details.",
    }


def capped_summary(text: str) -> str:
    return (text + " " + ("x" * 240))[:240]


def test_second_repo_review_rejects_outcome_seen_target_commits() -> None:
    review = mining.review_second_repo_candidate(
        second_repo_certified_row(target_commit := "attrs__hist__001"),
        context=attrs_problem_context(),
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits={f"target-{target_commit}"},
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "previous_acut_target_commit_seen" in review["promotion_blockers"]


def test_second_repo_review_rejects_solution_leaky_context() -> None:
    review = mining.review_second_repo_candidate(
        second_repo_certified_row(),
        context=attrs_problem_context("Rework linecache handling"),
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "solution_exposure_risk" in review["promotion_blockers"]


def test_second_repo_review_rejects_solution_leaky_pr_body_even_with_fix_title() -> None:
    review = mining.review_second_repo_candidate(
        second_repo_certified_row(),
        context=attrs_problem_context("Fixed frozen cache hash incompatibility")
        | {"body_summary": "This uses a wrapper class and refactor to bypass __setattr__."},
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "solution_exposure_risk" in review["promotion_blockers"]


def test_second_repo_review_flags_severe_statement_truncation() -> None:
    review = mining.review_second_repo_candidate(
        second_repo_certified_row(),
        context={
            "ref": "issue:999",
            "classification": "problem_context",
            "summary": "Generated init annotations are incomplete",
            "body_summary": capped_summary("Expected result: ```python {'return': <class 'NoneType"),
        },
        outcome_seen_task_ids=set(),
        outcome_seen_target_commits=set(),
    )

    assert review["promotion_decision"] == "reject_for_clean_holdout"
    assert "statement_quality_risk" in review["promotion_blockers"]
    assert review["statement_quality"]["statement_probably_truncated"] is True


def test_issue_numbers_from_text_finds_plain_issue_mentions() -> None:
    assert mining.issue_numbers_from_text("Fix issue 589 (#590). Fixes #611") == [590, 611, 589]


def test_second_repo_overlay_uses_preferred_chronological_split() -> None:
    config = {
        "_path": "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml",
        "minimum_clean_split": {"B_eval": 2, "H_future": 2},
        "preferred_clean_split": {"B_eval": 4, "H_future": 4},
        "mining": {"embargo_gap_days": 14},
    }
    promoted = [
        {
            **second_repo_certified_row(f"attrs__hist__{index:03d}", f"2020-{index:02d}-01T00:00:00+00:00"),
            "promotion_decision": "promote_to_clean_benchmark_candidate",
        }
        for index in range(1, 9)
    ]

    overlay = mining.second_repo_overlay_payload(config, repo_id="attrs", promoted_reviews=promoted)

    assert overlay["clean_supply_ready"] is True
    assert overlay["selected_b_eval_task_ids"] == [
        "attrs__hist__001",
        "attrs__hist__002",
        "attrs__hist__003",
        "attrs__hist__004",
    ]
    assert overlay["selected_h_future_task_ids"] == [
        "attrs__hist__005",
        "attrs__hist__006",
        "attrs__hist__007",
        "attrs__hist__008",
    ]
    assert overlay["predictive_validity_established"] is False


def test_second_repo_inventory_preserves_mining_anchor_counts_during_certification() -> None:
    """Regression: certification rewrites must not reset mined anchor counts to zero."""
    config = {
        "_path": "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml",
        "candidate_repos": {
            "attrs": {
                "repo_url": "https://github.com/python-attrs/attrs.git",
                "local_repo": "experiments/phase0_headroom/external_repos/attrs",
            }
        },
        "mining": {"max_history_anchors": 1000},
    }
    prior_inventory = {
        "anchors_scanned": 388,
        "first_filter_counts": {
            "anchor_status_counts": {"accepted": 48, "rejected": 340},
            "candidate_filter_status_counts": {"candidate": 48, "rejected": 340},
            "reject_reason_counts": {"docs_only": 12},
        },
    }

    inventory = mining.second_repo_inventory_payload(
        config,
        repo_id="attrs",
        candidates=[second_repo_certified_row()],
        contexts=[attrs_problem_context()],
        reviews=[],
        certification_rows=[],
        prior_inventory=prior_inventory,
    )

    assert inventory["anchors_scanned"] == 388
    assert inventory["first_filter_counts"] == prior_inventory["first_filter_counts"]
