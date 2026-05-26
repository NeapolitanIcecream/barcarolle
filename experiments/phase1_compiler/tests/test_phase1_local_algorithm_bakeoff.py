from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_local_algorithm_bakeoff as bakeoff  # noqa: E402


def test_reproduction_matches_committed_weighted_and_unweighted_metrics() -> None:
    payload = bakeoff.build_reproduction()

    assert payload["weighted_pilot_metrics_reproduced"] is True
    assert payload["recomputed_summary"]["candidate_metrics"]["barcarolle_weighted_time_family_matched"]["max_abs_gap"] == 0.7481
    assert payload["recomputed_summary"]["candidate_metrics"]["repo_unweighted_same_budget"]["max_abs_gap"] == 0.25
    assert payload["task_level_summary"]["task_count"] == 22


def test_underidentification_enumerates_all_current_feasible_splits() -> None:
    payload = bakeoff.build_underidentification()

    assert payload["metadata_objective_underidentification_measured"] is True
    assert payload["repo_summaries"]["attrs"]["split_count"] == 3150
    assert payload["repo_summaries"]["boltons"]["split_count"] == 34650
    assert payload["oracle_diagnostic_policy"].startswith("Observed outcome gap")


def test_feature_schema_uses_coarse_non_outcome_features() -> None:
    payload = bakeoff.build_features()

    assert payload["H_future_outcomes_used_for_features"] is False
    assert {row["name"] for row in payload["feature_dimensions"]} == set(bakeoff.FEATURE_DIMS)
    assert all("task_family_label" not in row["name"] for row in payload["feature_dimensions"])
    assert any(row["work_cluster"] == "rare_or_unknown" for row in payload["rows"])


def test_candidate_designs_record_no_outcome_selection_inputs() -> None:
    payload = bakeoff.build_candidate_designs()

    designs = {row["design_id"]: row for row in payload["candidate_designs"]}
    assert bakeoff.BLOCK_ID in designs
    assert bakeoff.SHRINKAGE_ID in designs
    assert designs["optional_block_plus_prior_difficulty"]["status"] == "skipped"
    for design in payload["candidate_designs"]:
        assert design["outcome_fields_used_for_selection"] == []
        assert design["hidden_oracle_material_used"] is False


def test_shrinkage_weights_are_normalized_and_capped_or_fallback() -> None:
    payload = bakeoff.build_shrinkage_weights()
    candidate = next(row for row in payload["weighted_candidates"] if row["candidate_id"] == bakeoff.SHRINKAGE_ID)

    for repo_split, weights in candidate["weights_by_repo_split"].items():
        diagnostics = candidate["diagnostics_by_repo_split"][repo_split]
        assert round(sum(weights.values()), 8) == 1.0
        assert max(weights.values()) <= diagnostics["max_weight_allowed"]
        assert diagnostics["ESS_ratio"] >= 0.7


def test_validation_and_paid_readiness_are_local_only_and_conservative() -> None:
    validation = bakeoff.build_validation()
    readiness = bakeoff.build_paid_readiness()

    assert validation["validation_mode"] == "pseudo_future_validation"
    assert validation["new_paid_acut_calls_made"] is False
    assert readiness["status"] == "not_ready_keep_stratified_mainline"
    assert readiness["new_paid_llm_calls_made"] is False
    assert readiness["no_paid_runbook_written_by_worker"] is True
