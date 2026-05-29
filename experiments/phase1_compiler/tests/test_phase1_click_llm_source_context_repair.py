from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_click_llm_source_context_repair as repair  # noqa: E402


HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b")


def build_payloads() -> dict[str, dict[str, object]]:
    config = repair.load_config()
    inventory = repair.build_click_inventory(config)
    public_context = repair.build_public_context_review(config, inventory)
    plan = repair.build_llm_packet_plan(config, public_context)
    smoke = repair.build_llm_smoke(config, plan)
    packets = repair.build_statement_packets(config, inventory, public_context)
    reviews = repair.build_review_records(config, packets)
    overlay = repair.build_quality_overlay(config, inventory, public_context, reviews)
    claim = repair.build_claim_boundary(config, overlay)
    return {
        "inventory": inventory,
        "public_context": public_context,
        "plan": plan,
        "smoke": smoke,
        "packets": packets,
        "reviews": reviews,
        "overlay": overlay,
        "claim": claim,
    }


def assert_sanitized(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, sort_keys=True)
    assert "diff --git" not in encoded
    assert "\n@@" not in encoded
    assert "hidden verifier" not in encoded.lower()
    assert "raw_completion_text" not in encoded
    assert "raw_prompt_text" not in encoded
    assert not HEX40_RE.search(encoded)


def test_inventory_freezes_thirty_click_title_only_tasks_without_outcomes() -> None:
    inventory = repair.build_click_inventory(repair.load_config())

    assert inventory["task_count"] == 30
    assert inventory["expected_task_count_met"] is True
    assert inventory["all_tasks_title_only_minor_risk"] is True
    assert inventory["title_only_minor_risk_count"] == 30
    assert inventory["outcome_fields_absent"] is True
    assert inventory["paid_outcomes_used_for_inventory"] is False
    assert inventory["adapter_outcomes_used_for_inventory"] is False
    assert inventory["split_outcome_labels_loaded"] is False
    assert inventory["task_ids"] == sorted(inventory["task_ids"])
    assert_sanitized(inventory)


def test_public_context_repairs_all_click_tasks_without_llm_calls() -> None:
    payloads = build_payloads()
    public_context = payloads["public_context"]

    assert public_context["candidate_count"] == 30
    assert public_context["accepted_public_context_count"] == 30
    assert public_context["insufficient_public_context_count"] == 0
    assert public_context["rejected_leaky_public_context_count"] == 0
    assert public_context["missing_public_context_evidence_count"] == 0
    assert public_context["paid_llm_calls_made"] == 0
    assert {row["verdict"] for row in public_context["rows"]} == {"accepted_public_context"}
    assert all(row["sufficient_for_solver_visible_statement"] is True for row in public_context["rows"])
    assert all(row["leakage_flags"] == [] for row in public_context["rows"])
    assert_sanitized(public_context)


def test_llm_plan_skips_generation_when_public_context_is_sufficient() -> None:
    payloads = build_payloads()
    plan = payloads["plan"]
    smoke = payloads["smoke"]

    assert plan["remaining_tasks_requiring_llm_assistance"] == 0
    assert plan["selected_task_count"] == 0
    assert plan["estimated_cost_usd"] == 0.0
    assert plan["model_calls_made"] == 0
    assert smoke["smoke_status"] == "skipped_public_context_sufficient"
    assert smoke["paid_llm_generation_calls_made"] == 0
    assert smoke["paid_llm_review_calls_made"] == 0
    assert smoke["token_estimated_cost_usd"] == 0.0
    assert_sanitized(plan)
    assert_sanitized(smoke)


def test_statement_packets_and_reviews_are_non_leaky_clean_candidates() -> None:
    payloads = build_payloads()
    packets = payloads["packets"]
    reviews = payloads["reviews"]

    assert packets["statement_packet_count"] == 30
    assert packets["llm_generation_status"] == "skipped_public_context_sufficient"
    assert packets["paid_llm_calls_made"] == 0
    assert packets["raw_prompts_or_completions_committed"] is False
    assert packets["raw_statement_text_committed"] is False
    assert reviews["review_count"] == 30
    assert reviews["recommendation_counts"] == {"clean_source_candidate": 30}
    assert reviews["paid_llm_review_calls_made"] == 0
    assert all(row["leakage_status"] == "pass" for row in reviews["rows"])
    assert all(row["ambiguity_status"] == "pass" for row in reviews["rows"])
    assert all(row["source_sufficiency_status"] == "pass" for row in reviews["rows"])
    assert all(row["contains_implementation_recipe"] is False for row in reviews["rows"])
    assert_sanitized(packets)
    assert_sanitized(reviews)


def test_overlay_moves_click_to_clean_claim_boundary_without_paid_result_changes() -> None:
    payloads = build_payloads()
    overlay = payloads["overlay"]
    claim = payloads["claim"]

    assert overlay["overlay_row_count"] == 30
    assert overlay["previous_title_only_minor_risk_count"] == 30
    assert overlay["upgraded_to_clean_or_cleaner_count"] == 30
    assert overlay["still_requiring_caveat_count"] == 0
    assert overlay["rejected_or_blocked_count"] == 0
    assert overlay["remaining_title_only_share"] == 0.0
    assert overlay["historical_paid_results_changed"] is False
    assert overlay["historical_task_ids_changed"] is False
    assert overlay["outcome_joined_after_freeze"] is False
    assert claim["claim_boundary_label"] == "click_clean_enough_for_three_repo_claim"
    assert claim["predictive_validity_established"] is False
    assert claim["paid_acut_cells_remain_blocked_by_default"] is True
    assert_sanitized(overlay)
    assert_sanitized(claim)
