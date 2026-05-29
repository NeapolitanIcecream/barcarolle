from __future__ import annotations

import copy
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_blocked_split_redesign as split_design  # noqa: E402


def load_committed_payloads() -> dict[str, object]:
    config = split_design.load_config()
    return {
        "config": config,
        "universe": split_design.load_candidate_universe(config),
        "candidates": split_design.read_json(split_design.output_path(config, "candidate_splits")),
        "selected": split_design.read_json(split_design.output_path(config, "selected_split")),
        "audit": split_design.read_json(split_design.output_path(config, "selection_audit")),
        "retrospective": split_design.read_json(split_design.output_path(config, "retrospective_outcome_diagnostics")),
        "cost": split_design.read_json(split_design.output_path(config, "cost_power_projection")),
    }


def test_candidate_universe_uses_only_release_eligible_visible_rows() -> None:
    payloads = load_committed_payloads()
    universe = payloads["universe"]
    rows = universe["rows"]

    assert universe["candidate_count_by_repo"] == {"attrs": 30, "boltons": 35, "click": 30}
    assert all(row["release_eligible_for_split_design"] is True for row in rows)
    assert universe["blocked_source_quality_selected_count"] == 0
    assert universe["diagnostic_only_selected_count"] == 0
    assert universe["outcome_fields_loaded"] is False
    assert universe["raw_text_fields_committed"] is False


def test_candidate_splits_have_exact_repo_split_counts_and_no_duplicates() -> None:
    payloads = load_committed_payloads()
    candidates = payloads["candidates"]["candidates"]

    assert payloads["candidates"]["candidate_seed_count_per_budget"] >= 100
    assert payloads["candidates"]["outcome_fields_loaded"] is False
    assert all(candidate["hard_constraint_failures"] == [] for candidate in candidates)
    for candidate in candidates:
        assert len(candidate["selected_task_ids"]) == len(set(candidate["selected_task_ids"]))
        expected_each_split = 10 if candidate["budget_id"] == "same_budget_20_per_repo" else 15
        assert candidate["split_counts_by_repo"] == {
            "attrs": {"B_eval": expected_each_split, "H_future": expected_each_split},
            "boltons": {"B_eval": expected_each_split, "H_future": expected_each_split},
            "click": {"B_eval": expected_each_split, "H_future": expected_each_split},
        }
        assert candidate["outcome_fields_used_for_selection"] is False


def test_feature_imbalance_objective_ignores_pass_fail_columns() -> None:
    payloads = load_committed_payloads()
    universe_rows = payloads["universe"]["rows"]
    selected = payloads["selected"]["selected_candidates"][0]
    original_rows = split_design.rows_by_task_id(universe_rows)

    mutated_rows = [copy.deepcopy(row) for row in universe_rows]
    for index, row in enumerate(mutated_rows):
        row["pass_flag"] = index % 2 == 0
        row["terminal_status"] = "verified_pass" if index % 2 == 0 else "verified_fail"
        row["adapter_id"] = "codex_workspace"
    mutated_by_id = split_design.rows_by_task_id(mutated_rows)

    assert split_design.compute_imbalance(selected, original_rows, split_design.soft_penalty_weights(payloads["config"])) == split_design.compute_imbalance(selected, mutated_by_id, split_design.soft_penalty_weights(payloads["config"]))


def test_click_minor_risk_caveat_is_required_when_click_is_included() -> None:
    payloads = load_committed_payloads()
    selected = payloads["selected"]
    click_tasks = [task_id for candidate in selected["selected_candidates"] for task_id in candidate["selected_task_ids"] if task_id.startswith("click__")]

    assert click_tasks
    assert selected["click_minor_risk_caveat"]["all_click_source_quality_minor_risk"] is True
    assert selected["click_minor_risk_caveat"]["all_click_source_context_title_only"] is True


def test_selection_audit_rejects_outcome_inputs_before_freeze() -> None:
    payloads = load_committed_payloads()
    audit = payloads["audit"]

    assert audit["selection_audit_passed"] is True
    assert audit["outcome_input_paths_loaded_before_freeze"] == []
    assert split_design.selection_audit_passes_for_loaded_paths(audit["loaded_input_paths_before_freeze"]) is True
    assert split_design.selection_audit_passes_for_loaded_paths(["experiments/phase0_headroom/results/example_score_table.csv"]) is False
    assert split_design.selection_audit_passes_for_loaded_paths(["experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json"]) is False


def test_retrospective_diagnostics_do_not_mutate_selected_split() -> None:
    payloads = load_committed_payloads()
    selected = payloads["selected"]
    retrospective = payloads["retrospective"]

    assert retrospective["retrospective_outcomes_did_not_choose_split"] is True
    assert retrospective["selected_split_changed_after_outcomes"] is False
    assert retrospective["predictive_validity_established"] is False
    assert set(retrospective["design_diagnostics"]) == {candidate["design_id"] for candidate in selected["selected_candidates"]}


def test_cost_projection_labels_token_estimated_vs_provider_billed_status() -> None:
    payloads = load_committed_payloads()
    cost = payloads["cost"]

    assert cost["paid_calls_made"] == 0
    assert cost["cost_basis"] == "token_estimated_unless_provider_billed_available"
    assert cost["workspace_usage_ledger_summary"]["matching_prior_paid_validation_records"] == 120
    for projection in cost["budget_projections"].values():
        for adapter_projection in projection["by_adapter"].values():
            assert adapter_projection["cost_basis"] == "token_estimated"
            assert adapter_projection["provider_billed_cost_status"] == "unavailable"
