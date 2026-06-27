from __future__ import annotations

import phase1_clean_supply_breal_extension as breal


def review_row(task_id: str = "boltons__hist__014") -> dict:
    return {
        "task_id": task_id,
        "split": "B_real",
        "outcome_seen": False,
        "source_context_status": "non_leaky_problem_context",
        "oracle_alignment_status": "aligned",
        "solution_exposure_risk": "none_detected",
        "project_or_docs_only_risk": False,
        "project_or_config_heavy_risk": False,
        "scope_clarity_status": "clear_behavior_scope",
    }


def test_outcome_seen_tasks_cannot_be_promoted() -> None:
    row = review_row()
    row["outcome_seen"] = True

    decision = breal.promotion_decision(row)

    assert decision["promotion_decision"] == "reject_for_clean_holdout"
    assert "previous_acut_outcome_seen" in decision["promotion_blockers"]


def test_boltons_014_promotes_only_when_project_heavy_ambiguity_is_resolved() -> None:
    row = review_row()
    row["project_or_config_heavy_risk"] = True
    row["scope_clarity_status"] = "ambiguous_project_heavy_context"

    decision = breal.promotion_decision(row)

    assert decision["promotion_decision"] == "keep_manual_review_required"
    assert "scope_context_project_heavy_or_ambiguous" in decision["promotion_blockers"]

    row["project_or_config_heavy_risk"] = False
    row["scope_clarity_status"] = "clear_behavior_scope"
    decision = breal.promotion_decision(row)

    assert decision["promotion_decision"] == "promote_to_clean_benchmark_candidate"


def test_solution_exposure_risk_rows_are_not_promoted() -> None:
    row = review_row()
    row["solution_exposure_risk"] = "solution_exposure_risk"

    decision = breal.promotion_decision(row)

    assert decision["promotion_decision"] == "reject_for_clean_holdout"
    assert "solution_exposure_risk" in decision["promotion_blockers"]


def test_overlay_combines_prior_and_new_promoted_supply() -> None:
    overlay = breal.overlay_payload(
        prior_promoted={"B_real": ["boltons__hist__011"], "W_real": ["boltons__hist__022", "boltons__hist__023"]},
        new_promoted=[{"task_id": "boltons__hist__014", "split": "B_real"}],
        minimum={"B_real": 2, "W_real": 2},
    )

    assert overlay["promoted_by_split"]["B_real"] == ["boltons__hist__011", "boltons__hist__014"]
    assert overlay["promoted_by_split"]["W_real"] == ["boltons__hist__022", "boltons__hist__023"]
    assert overlay["clean_supply_ready"] is True


def test_clean_supply_readiness_requires_two_b_and_two_w() -> None:
    overlay = breal.overlay_payload(
        prior_promoted={"B_real": ["boltons__hist__011"], "W_real": ["boltons__hist__022", "boltons__hist__023"]},
        new_promoted=[],
        minimum={"B_real": 2, "W_real": 2},
    )

    assert overlay["clean_supply_ready"] is False


def test_predictive_validity_remains_false() -> None:
    overlay = breal.overlay_payload(
        prior_promoted={"B_real": ["boltons__hist__011"], "W_real": ["boltons__hist__022", "boltons__hist__023"]},
        new_promoted=[{"task_id": "boltons__hist__014", "split": "B_real"}],
        minimum={"B_real": 2, "W_real": 2},
    )

    assert overlay["predictive_validity_established"] is False
