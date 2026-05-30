from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_retrospective_predictive_signal as signal  # noqa: E402


def test_universe_is_outcome_blind_and_uses_repaired_click_overlay() -> None:
    config = signal.load_config()
    payload = signal.build_universe()

    assert payload["terminal_outcomes_loaded"] is False
    assert payload["outcome_fields_used_for_selection"] == []
    assert payload["analysis_universe_task_count"] == 95
    assert payload["counts_by_repo"]["click"]["eligible"] == 30
    assert payload["click_repair_overlay"]["overlay_rows_applied"] == 30
    assert all("terminal_status" not in row for row in payload["rows"])
    assert signal.output_path(config, "universe").exists()


def test_window_plan_keeps_pseudo_future_primary_when_rolling_is_sparse() -> None:
    payload = signal.build_window_plan()

    assert payload["analysis_mode"] == "mixed"
    assert payload["primary_mode"] == "retrospective_pseudo_future"
    assert payload["true_rolling_origin_support"] == "too_sparse_for_primary_claim"
    primary = next(row for row in payload["windows"] if row["primary_window"])
    assert primary["window_id"] == "blocked_split_heldout"
    assert primary["support_by_repo"]["attrs"]["B_eval_candidate_count"] == 10


def test_selection_freeze_registers_required_designs_without_outcome_fields() -> None:
    registry = signal.build_design_registry()
    freeze = signal.build_selection_freeze()

    assert {row["design_id"] for row in registry["designs"]} == set(signal.REQUIRED_DESIGNS)
    assert freeze["selection_freeze_status"] == "frozen_before_score_join"
    assert freeze["outcome_fields_used_for_selection"] == []
    selected = [row for row in freeze["selections"] if row["selection_status"].startswith("selected")]
    assert selected
    assert all(row["outcome_fields_used_for_selection"] == [] for row in selected)
    weighted = next(row for row in selected if row["design_id"] == "block_plus_shrinkage_weighted")
    assert weighted["diagnostics"]["max_weight"] <= weighted["diagnostics"]["max_weight_allowed"]


def test_score_join_preserves_invalid_output_as_non_scoreable() -> None:
    join = signal.build_score_join_manifest()

    assert join["join_happened_after_selection_freeze"] is True
    assert join["new_paid_acut_cells_run"] is False
    assert join["invalid_output_sensitivity"]["task_id"] == signal.INVALID_TASK_ID
    assert join["invalid_output_sensitivity"]["non_scoreable_selected_rows"] >= 1
    assert "invalid_output" in join["non_scoreable_by_reason"]


def test_metrics_and_comparison_remain_adapter_stratified_and_retrospective() -> None:
    metrics = signal.build_adapter_metrics()
    comparison, uncertainty = signal.build_baseline_comparison()

    assert metrics["primary_reporting"] == "adapter_stratified"
    assert set(metrics["by_adapter_design"]) == set(signal.ADAPTERS)
    assert comparison["best_simple_baseline"]["design_id"] in signal.SIMPLE_BASELINES
    assert comparison["best_barcarolle_candidate"]["design_id"] in signal.BARCAROLLE_CANDIDATES
    assert uncertainty["support_labels"]["claim_strength"] == "traction_evidence_only"


def test_decision_does_not_claim_predictive_validity_or_paid_calls() -> None:
    claim, decision = signal.build_claim_boundary_and_decision()

    assert claim["predictive_validity_established"] is False
    assert claim["no_paid_acut_cells_run"] is True
    assert claim["no_paid_llm_calls_run"] is True
    assert decision["future_paid_acut_remains_blocked_by_default"] is True
    assert decision["predictive_validity_established"] is False
