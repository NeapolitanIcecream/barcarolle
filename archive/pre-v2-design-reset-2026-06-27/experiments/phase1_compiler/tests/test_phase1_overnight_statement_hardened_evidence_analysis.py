from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_overnight_statement_hardened_evidence_analysis as analysis  # noqa: E402


CONFIG = REPO_ROOT / "experiments" / "phase1_compiler" / "configs" / "phase1_overnight_statement_hardened_evidence_analysis.yaml"
DECISION = REPO_ROOT / "experiments" / "phase1_compiler" / "results" / "phase1_overnight_statement_hardened_next_action_decision.json"


def load_config() -> dict:
    return analysis.load_config(CONFIG)


def test_integrity_audit_matches_paid_metrics_and_has_no_raw_artifacts() -> None:
    payload = analysis.build_integrity_audit(load_config())

    assert payload["status"] == "pass"
    assert payload["total_cells"] == 32
    assert payload["scoreable_cell_count"] == 32
    assert payload["terminal_status_counts"] == {"verified_fail": 11, "verified_pass": 21}
    assert payload["usage_observed_count"] == 32
    assert payload["raw_artifact_paths_committed"] == []


def test_task_outcome_matrix_identifies_failures_and_disagreement() -> None:
    payload = analysis.build_task_outcome_matrix(load_config())

    assert payload["task_count"] == 16
    assert payload["cell_count"] == 32
    assert payload["summary"]["both_failed_task_ids"] == [
        "attrs__hist__003",
        "attrs__hist__012",
        "attrs__hist__013",
        "boltons__hist__022",
        "boltons__hist__027",
    ]
    assert payload["summary"]["adapter_disagreement_task_ids"] == ["boltons__hist__011"]


def test_threshold_analysis_keeps_predictive_validity_false() -> None:
    payload = analysis.build_threshold_analysis(load_config())

    assert payload["predictive_validity_established"] is False
    assert payload["current_evidence_meets_primary_threshold"] is False
    assert payload["gap_intervals"]["attrs"]["observed_gap"] == 0.25
    assert payload["gap_intervals"]["boltons"]["observed_gap"] == 0.375
    assert len(payload["candidate_thresholds"]) >= 3


def test_power_analysis_marks_current_design_underpowered_for_primary_gap() -> None:
    payload = analysis.build_power_analysis(load_config())
    current = next(row for row in payload["designs"] if row["name"] == "current_design")

    assert current["cells_per_split"] == 16
    assert current["meets_0_15_precision_target"] is False
    assert payload["cells_per_split_needed_for_0_15_half_width"] > current["cells_per_split"]


def test_final_decision_preserves_claim_boundary_after_generation() -> None:
    assert DECISION.exists()
    payload = json.loads(DECISION.read_text(encoding="utf-8"))

    assert payload["primary_decision"] == "design_new_predictive_threshold_before_more_paid_validation"
    assert payload["predictive_validity_established"] is False
    assert payload["followup_runbook_written_by_worker"] is False
    assert payload["new_paid_calls_made"] is False
    assert "old_paid_result_repaired" in payload["disallowed_claims_not_made"]
