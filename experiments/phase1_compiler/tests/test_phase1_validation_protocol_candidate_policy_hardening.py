from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_validation_protocol_candidate_policy_hardening as hardening  # noqa: E402


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    lines: list[str] = []

    def emit(key: str, value: object, indent: int) -> None:
        prefix = " " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            for child_key, child_value in value.items():
                emit(str(child_key), child_value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")

    for key, value in payload.items():
        emit(key, value, 0)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def temp_config_path(tmp_path: Path) -> Path:
    config = hardening.load_config()
    config.pop("_path", None)
    config["outputs"] = {
        key: str(tmp_path / "results" / Path(path).name)
        for key, path in config["outputs"].items()
    }
    config["reports"] = {
        key: str(tmp_path / "reports" / Path(path).name)
        for key, path in config["reports"].items()
    }
    config["docs"] = {
        key: str(tmp_path / "docs" / Path(path).name)
        for key, path in config["docs"].items()
    }
    path = tmp_path / "phase1_validation_protocol_candidate_policy_hardening.yaml"
    _write_yaml(path, config)
    return path


def test_config_forbids_paid_calls_external_review_and_browsing() -> None:
    config = hardening.load_config()

    assert config["paid_calls_allowed"] is False
    assert config["external_review_allowed"] is False
    assert config["public_citation_browsing_allowed"] is False


def test_preflight_confirms_m3_stop_label_and_boundaries(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    preflight = hardening.build_preflight(config_path)

    assert preflight["m3_stop_label"] == "proposal_evidence_package_complete"
    assert preflight["m3_stop_label_confirmed"] is True
    assert preflight["permission_lock"]["paid_acut_cells"] is False
    assert preflight["permission_lock"]["external_reviewer_calls"] is False
    assert preflight["permission_lock"]["public_citation_browsing"] is False
    assert preflight["missing_required_inputs"] == []


def test_candidate_policy_fails_current_fallback_caps_without_changing_tasks(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    policy = hardening.build_candidate_policy(config_path)

    assert policy["current_m3_fallback"]["overall_share"] == 0.3333
    assert policy["current_m3_fallback"]["share_by_repo"]["boltons"] == 1.0
    assert policy["fallback_governance"]["current_m3_candidate_passes_fallback_rule"] is False
    assert policy["fallback_governance"]["boltons_treatment"] == "claim_changing_because_fallback_share_is_6_of_6"
    assert policy["selected_task_ids_changed"] is False


def test_adapter_estimand_keeps_named_adapters_primary(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    estimand = hardening.build_adapter_estimand(config_path)

    assert estimand["primary_estimand"] == "per_named_acut_configuration"
    assert "cannot rescue" in estimand["pooled_metric_rule"]
    current = {row["adapter_id"]: row for row in estimand["current_m3_adapter_interpretation"]}
    assert current["codex_workspace"]["passes_primary_margin"] is False
    assert current["kilo_workspace"]["passes_primary_margin"] is True
    assert estimand["current_m3_cross_adapter_status"] == "fails_because_codex_does_not_pass_and_pooled_summary_is_secondary"


def test_build_all_outputs_decision_summary_and_clean_markdown(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    hardening.build_all(config_path)
    config = hardening.load_config(config_path)

    required_outputs = {
        "preflight",
        "claim_modes",
        "candidate_policy",
        "baseline_registry",
        "adapter_estimand",
        "success_gate",
        "support_thresholds",
        "release_schema",
        "power_budget_note",
        "decision",
    }
    for key in required_outputs:
        assert hardening.output_path(config, key).exists()
    for key in config["reports"]:
        assert hardening.report_path(config, key).exists()
    assert hardening.doc_path(config, "summary").exists()

    decision = hardening.read_json(hardening.output_path(config, "decision"))
    assert decision["stop_label"] == "validation_protocol_hardened_candidate_not_paid_ready"
    assert decision["current_m3_candidate_passes_hardened_no_paid_readiness_gate"] is False
    assert decision["paid_validation_authorization"] is False
    assert decision["predictive_validity_state"] == "not_established"
    assert decision["user_decisions_needed_before_M5"] is False
    assert decision["user_decisions_needed_before_M6_or_budget_bearing_discussion"] is True
    hardening.assert_generated_markdown_clean(config)


def test_success_gate_replaces_loose_margin_or_majority_logic(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    gate = hardening.build_success_gate(config_path)

    assert gate["gate_type"] == "joint_all_required"
    assert gate["current_m3_gate_result"]["passes_future_gate"] is False
    assert "aggregate MAE edge below future margin" in gate["current_m3_gate_result"]["main_failures"]
    assert gate["invalid_non_scoreable_rules"]["policy_violations_allowed_for_primary_claims"] == 0
    assert gate["catastrophic_miss_rules"]["gap_threshold"] == 0.15
