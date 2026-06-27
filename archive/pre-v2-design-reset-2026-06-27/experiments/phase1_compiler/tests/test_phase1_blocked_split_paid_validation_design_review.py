from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_blocked_split_paid_validation_design_review as review  # noqa: E402


def load_payloads() -> dict[str, object]:
    config = review.load_config()
    return {
        "config": config,
        "claim_policy": review.read_json(review.output_path(config, "claim_policy")),
        "overlap": review.read_json(review.output_path(config, "overlap_matrix")),
        "missing_cells": review.read_json(review.output_path(config, "missing_cells")),
        "protocol_options": review.read_json(review.output_path(config, "protocol_options")),
        "cost_projection": review.read_json(review.output_path(config, "cost_projection")),
        "reuse_policy": review.read_json(review.output_path(config, "reuse_policy")),
        "ready_package": review.read_json(review.output_path(config, "ready_package")),
    }


def test_claim_policy_permits_post_hoc_design_only_as_exploratory() -> None:
    payloads = load_payloads()
    policy = payloads["claim_policy"]
    validation = review.validate_claim_policy(payloads["config"])

    assert policy["phase_status"] == "exploratory"
    assert policy["post_hoc_design_allowed_for_exploration"] is True
    assert policy["formal_preregistration_claim_allowed"] is False
    assert policy["predictive_validity_established"] is False
    assert validation["valid"] is True
    assert validation["checks"]["post_hoc_allowed_only_for_exploration"] is True


def test_missing_cell_counts_are_adapter_specific_and_deterministic() -> None:
    payloads = load_payloads()
    overlap = payloads["overlap"]
    rebuilt, _ = review.build_overlap_payloads(payloads["config"])
    same = overlap["splits"]["same_budget_20_per_repo"]
    expanded = overlap["splits"]["expanded_30_per_repo"]
    rebuilt_same = rebuilt["splits"]["same_budget_20_per_repo"]

    assert same["selected_tasks"] == 60
    assert same["known_tasks"] == 36
    assert same["missing_tasks"] == 24
    assert same["missing_cells_by_adapter"] == {"codex_workspace": 24, "kilo_workspace": 24}
    assert same["missing_cell_manifest"] == rebuilt_same["missing_cell_manifest"]
    assert expanded["selected_tasks"] == 90
    assert expanded["missing_cells_by_adapter"] == {"codex_workspace": 34, "kilo_workspace": 34}


def test_no_missing_outcomes_are_imputed() -> None:
    payloads = load_payloads()
    overlap = payloads["overlap"]
    missing = payloads["missing_cells"]

    assert overlap["missing_outcomes_imputed"] is False
    assert missing["missing_outcomes_imputed"] is False
    for summary in missing["split_missing_cells"].values():
        assert summary["missing_cells"] == len(summary["missing_cell_manifest"])


def test_known_cells_have_committed_score_table_provenance() -> None:
    payloads = load_payloads()
    same = payloads["overlap"]["splits"]["same_budget_20_per_repo"]

    assert same["cells_safe_to_reuse"]
    for cell in same["cells_safe_to_reuse"]:
        score_table = REPO_ROOT / cell["score_table"]
        assert score_table.exists()
        assert cell["result_prefix"]
        assert cell["scoreable_cell"] is True
        assert cell["terminal_status"] in {"verified_pass", "verified_fail"}


def test_protocol_options_do_not_claim_predictive_validity() -> None:
    payloads = load_payloads()
    options = payloads["protocol_options"]["options"]

    assert {option["option_id"] for option in options} == {"A", "B", "C", "D", "E"}
    assert payloads["protocol_options"]["selected_recommended_option_id"] == "B"
    assert all(option["predictive_validity_claim_allowed"] is False for option in options)
    assert all("exploratory" in option["claim_boundary"] or option["option_id"] in {"A", "E"} for option in options)


def test_click_minor_risk_caveat_is_required_for_non_stop_options() -> None:
    options = load_payloads()["protocol_options"]["options"]

    non_stop = [option for option in options if option["option_id"] != "E"]
    assert non_stop
    assert all(option["click_minor_risk_status"] == "visible_title_only_minor_risk" for option in non_stop)
    assert next(option for option in options if option["option_id"] == "E")["click_minor_risk_status"] == (
        "treated_as_blocker_for_this_option"
    )


def test_cost_projections_are_adapter_stratified_and_token_estimated() -> None:
    payloads = load_payloads()
    cost = payloads["cost_projection"]
    option_b = next(option for option in cost["options"] if option["option_id"] == "B")

    assert cost["provider_billed_exact_cost_available"] is False
    assert option_b["new_paid_cell_count"] == 48
    assert set(option_b["by_adapter"]) == {"codex_workspace", "kilo_workspace"}
    assert option_b["by_adapter"]["codex_workspace"]["new_paid_cell_count"] == 24
    assert option_b["by_adapter"]["kilo_workspace"]["new_paid_cell_count"] == 24
    assert option_b["total_token_estimated_new_cost_usd"] == 20.506944
    assert all(
        adapter_cost["cost_basis"] == "token_estimated_from_committed_prior_cost_summary"
        for adapter_cost in option_b["by_adapter"].values()
    )


def test_ready_package_separates_reusable_and_missing_cells_without_raw_artifacts() -> None:
    payloads = load_payloads()
    reuse = payloads["reuse_policy"]
    ready = payloads["ready_package"]

    assert reuse["existing_outcomes_reusable_for_exploratory_accounting"] is True
    assert reuse["existing_outcomes_reusable_for_formal_preregistration"] is False
    assert ready["selected_protocol_option"] == "B"
    assert len(ready["known_reusable_cells"]) == 72
    assert len(ready["missing_paid_cells_to_run"]) == 48
    assert ready["endpoint_requirement"]["required_env_vars"] == ["LLM_BASE_URL", "LLM_API_KEY"]
    assert ready["endpoint_requirement"]["fallback_to_other_llm_auth_allowed"] is False
    assert ready["followup_runbook_written_by_worker"] is False
