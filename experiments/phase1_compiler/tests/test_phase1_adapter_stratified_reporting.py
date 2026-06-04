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


def test_adapter_summary_reproduces_paid_diagnostic_pass_rates() -> None:
    payloads = reporting.build_summary_payloads(reporting.load_config())
    by_adapter = payloads["three_repo_summary"]["by_adapter"]

    assert by_adapter["codex_workspace"]["cell_count"] == 60
    assert by_adapter["codex_workspace"]["scoreable_count"] == 60
    assert by_adapter["codex_workspace"]["pass_count"] == 22
    assert by_adapter["codex_workspace"]["pass_rate"] == 0.3667
    assert by_adapter["kilo_workspace"]["cell_count"] == 60
    assert by_adapter["kilo_workspace"]["scoreable_count"] == 60
    assert by_adapter["kilo_workspace"]["pass_count"] == 32
    assert by_adapter["kilo_workspace"]["pass_rate"] == 0.5333


def test_adapter_summary_includes_repo_split_gap_breakouts() -> None:
    by_adapter = reporting.build_summary_payloads(reporting.load_config())["three_repo_summary"]["by_adapter"]

    assert by_adapter["codex_workspace"]["pass_rate_by_repo"]["attrs"]["pass_rate"] == 0.5
    assert by_adapter["codex_workspace"]["pass_rate_by_repo_and_split"]["click"]["B_eval"]["pass_rate"] == 0.1
    assert by_adapter["codex_workspace"]["b_eval_h_future_gap"]["by_repo"]["click"]["absolute_gap"] == 0.6
    assert by_adapter["kilo_workspace"]["pass_rate_by_repo_and_split"]["click"]["H_future"]["pass_rate"] == 0.8
    assert by_adapter["kilo_workspace"]["b_eval_h_future_gap"]["pooled"]["absolute_gap"] == 0.0


def test_pairwise_summary_reproduces_adapter_disagreements() -> None:
    pairwise = reporting.build_summary_payloads(reporting.load_config())["pairwise_summary"]

    assert pairwise["paired_task_count"] == 60
    assert pairwise["both_fail"] == 22
    assert pairwise["both_pass"] == 16
    assert pairwise["codex_workspace_only_pass"] == 6
    assert pairwise["kilo_workspace_only_pass"] == 16
    assert pairwise["disagreement_count"] == 22
    assert pairwise["disagreement_rate"] == 0.3667
    assert pairwise["exact_count_summary"]["p_value"] == 0.052479


def test_cost_latency_summary_reproduces_observed_token_estimates() -> None:
    cost = reporting.build_summary_payloads(reporting.load_config())["cost_latency_summary"]
    codex = cost["by_adapter"]["codex_workspace"]
    kilo = cost["by_adapter"]["kilo_workspace"]

    assert codex["observed_token_estimated_cost_usd"] == 32.22309
    assert codex["cost_per_cell_usd"] == 0.53705
    assert codex["usage_observed_rate"] == 1.0
    assert codex["median_latency_seconds"] == 115.059
    assert kilo["observed_token_estimated_cost_usd"] == 19.044243
    assert kilo["cost_per_cell_usd"] == 0.3174
    assert kilo["usage_observed_rate"] == 1.0
    assert kilo["median_latency_seconds"] == 52.5495
    assert cost["actual_provider_billed_cost_usd"] is None
    assert cost["provider_billed_exact_cost_available"] is False


def test_future_gates_prevent_pooled_only_cross_harness_headlines() -> None:
    gates = reporting.build_future_gates_payload(reporting.load_config())

    assert gates["status"] == "ready"
    assert gates["cross_harness_reporting_rule"]["adapter_table_required"] is True
    assert gates["cross_harness_reporting_rule"]["paired_disagreement_required_when_shared_tasks"] is True
    assert gates["pooled_summary_rule"]["never_allowed"] == "only_headline_for_cross_harness_paid_results"
    assert gates["pooled_summary_rule"]["primary_allowed"] == "only_if_preregistered_before_outcomes"
    assert gates["single_acut_reporting_rule"]["scoreable_adapter_must_be_preregistered"] is True
    assert gates["no_future_runbook_drafted"] is True
