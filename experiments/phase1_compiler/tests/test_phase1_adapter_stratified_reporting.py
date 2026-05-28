from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_adapter_stratified_reporting as reporting  # noqa: E402


def test_reporting_config_loads_with_no_paid_boundary() -> None:
    config = reporting.load_config()

    assert config["schema_version"] == "barcarolle.phase1_adapter_stratified_reporting.v1"
    assert config["diagnostic_only"] is True
    assert config["paid_calls_allowed"] is False
    assert config["policy"]["completed_paid_pilot_decision_mutable"] is False
    assert config["policy"]["predictive_validity_claim_allowed"] is False


def test_policy_requires_adapter_level_before_pooled_results() -> None:
    config = reporting.load_config()
    validation = reporting.validate_policy(config)

    assert validation["valid"] is True
    assert validation["checks"]["adapter_level_results_before_pooled"] is True
    assert validation["checks"]["pooled_only_cross_harness_headline_disallowed"] is True
    assert validation["checks"]["pilot_claim_boundary_preserved"] is True


def test_policy_requires_cost_estimate_bill_distinction() -> None:
    payload = reporting.build_policy_payload(reporting.load_config())

    assert payload["cost_language"]["observed_token_estimated_cost_is_provider_billed_cost"] is False
    assert payload["cost_language"]["exact_bill_claim_requires_actual_provider_billed_cost"] is True
    assert (
        payload["cost_language"]["when_actual_provider_billed_cost_is_null"]
        == "report_provider_billed_cost_unavailable"
    )


def test_policy_declares_required_adapter_and_pairwise_metrics() -> None:
    payload = reporting.build_policy_payload(reporting.load_config())

    assert "pass_rate_by_repo_and_split" in payload["required_adapter_metrics"]
    assert "b_eval_h_future_gap" in payload["required_adapter_metrics"]
    assert "observed_token_estimated_cost_usd" in payload["required_adapter_metrics"]
    assert "median_latency_seconds" in payload["required_adapter_metrics"]
    assert "both_pass" in payload["required_pairwise_metrics"]
    assert "both_fail" in payload["required_pairwise_metrics"]
    assert "disagreement_rate" in payload["required_pairwise_metrics"]
