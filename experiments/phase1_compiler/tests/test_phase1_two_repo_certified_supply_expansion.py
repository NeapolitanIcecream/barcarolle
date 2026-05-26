from __future__ import annotations

import phase1_two_repo_certified_supply_expansion as expansion


def test_stable_supply_expansion_task_ids_are_versioned_by_repo() -> None:
    assert expansion.stable_candidate_id("attrs", 7) == "attrs__supply_expansion_20260526__007"
    assert expansion.stable_candidate_id("boltons", 42) == "boltons__supply_expansion_20260526__042"


def test_review_certification_never_promotes_outcome_seen_target_commit() -> None:
    row = {
        "repo_id": "attrs",
        "task_id": "attrs__supply_expansion_20260526__001",
        "target_commit": "seen-target",
        "status": "certified",
        "gates": {gate: "pass" for gate in expansion.REQUIRED_CERTIFICATION_GATES if gate != "statement_quality_review"},
    }
    context = {
        "source_context_status": "non_leaky_problem_context",
        "source_ref": "issue:123",
        "statement_quality": {"statement_quality_gate": "pass"},
        "source_leakage_risks": [],
    }

    reviewed = expansion.review_certification_row(
        row,
        context,
        {"paid_outcome_seen_target_commits": ["seen-target"]},
    )

    assert reviewed["promotion_decision"] == "not_promoted"
    assert "previous_acut_target_commit_seen" in reviewed["promotion_blockers"]


def test_review_certification_requires_statement_quality_pass() -> None:
    row = {
        "repo_id": "boltons",
        "task_id": "boltons__supply_expansion_20260526__001",
        "target_commit": "target",
        "status": "certified",
        "gates": {gate: "pass" for gate in expansion.REQUIRED_CERTIFICATION_GATES if gate != "statement_quality_review"},
    }
    context = {
        "source_context_status": "non_leaky_problem_context",
        "source_ref": "issue:456",
        "statement_quality": {"statement_quality_gate": "material_risk"},
        "source_leakage_risks": [],
    }

    reviewed = expansion.review_certification_row(
        row,
        context,
        {"paid_outcome_seen_target_commits": []},
    )

    assert reviewed["promotion_decision"] == "not_promoted"
    assert reviewed["reviewed_required_gates"]["statement_quality_review"] == "fail"
    assert "statement_quality_risk" in reviewed["promotion_blockers"]


def test_review_certification_promotes_only_when_all_required_gates_pass() -> None:
    row = {
        "repo_id": "attrs",
        "task_id": "attrs__supply_expansion_20260526__002",
        "target_commit": "target",
        "status": "certified",
        "gates": {gate: "pass" for gate in expansion.REQUIRED_CERTIFICATION_GATES if gate != "statement_quality_review"},
    }
    context = {
        "source_context_status": "non_leaky_problem_context",
        "source_ref": "issue:789",
        "statement_quality": {"statement_quality_gate": "pass"},
        "source_leakage_risks": [],
    }

    reviewed = expansion.review_certification_row(
        row,
        context,
        {"paid_outcome_seen_target_commits": []},
    )

    assert reviewed["promotion_decision"] == "locally_certified_statement_ready"
    assert reviewed["promotion_blockers"] == []


def test_candidate_filter_requires_changed_tests_for_selection() -> None:
    decision = expansion.candidate_filter_status(
        "Fix behavior",
        ["src/attr/_make.py"],
        added=5,
        deleted=2,
    )

    assert decision["selected"] is False
    assert "no_changed_test_file" in decision["reject_reasons"]
