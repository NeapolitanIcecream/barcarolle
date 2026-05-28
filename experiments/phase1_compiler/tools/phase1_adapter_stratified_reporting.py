from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_adapter_stratified_reporting.yaml"
SCHEMA_VERSION = "barcarolle.phase1_adapter_stratified_reporting.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_adapter_stratified_reporting_output.v1"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(str(path))
    return raw if raw.is_absolute() else REPO_ROOT / raw


def rel(path: str | Path) -> str:
    resolved = repo_path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected adapter stratified reporting config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def validate_policy(config: dict[str, Any]) -> dict[str, Any]:
    policy = config["policy"]
    adapter_metrics = set(config["required_adapter_metrics"])
    pairwise_metrics = set(config["required_pairwise_metrics"])
    cost_latency_fields = set(config["required_cost_latency_fields"])
    future_gates = set(config["future_paid_gates"])

    checks = {
        "adapter_level_results_before_pooled": policy.get("adapter_level_results_before_pooled") is True,
        "pooled_only_cross_harness_headline_disallowed": policy.get("pooled_only_cross_harness_headline_allowed") is False,
        "pooled_result_has_allowed_secondary_or_preregistered_forms": (
            policy.get("pooled_result_allowed_when_preregistered_primary") is True
            and policy.get("pooled_result_allowed_when_marked_diagnostic") is True
        ),
        "pilot_claim_boundary_preserved": policy.get("completed_paid_pilot_claim_boundary") == "pilot_evidence_only",
        "completed_paid_decision_not_mutable": policy.get("completed_paid_pilot_decision_mutable") is False,
        "predictive_validity_not_claimed": policy.get("predictive_validity_claim_allowed") is False,
        "token_estimate_not_provider_bill": policy.get("token_estimated_cost_is_provider_billed_cost") is False,
        "exact_bill_requires_provider_billed_cost": policy.get("actual_provider_billed_cost_required_for_exact_bill_claim") is True,
        "provider_bill_null_language_required": policy.get("if_actual_provider_billed_cost_null")
        == "report_provider_billed_cost_unavailable",
        "adapter_metrics_complete": {
            "adapter_id",
            "cell_count",
            "scoreable_count",
            "pass_rate",
            "pass_rate_by_repo",
            "pass_rate_by_split",
            "pass_rate_by_repo_and_split",
            "b_eval_h_future_gap",
            "policy_violation_count",
            "observed_token_estimated_cost_usd",
            "cost_per_cell_usd",
            "usage_observed_rate",
            "median_latency_seconds",
        }.issubset(adapter_metrics),
        "pairwise_metrics_complete": {
            "both_pass",
            "both_fail",
            "adapter_a_only_pass",
            "adapter_b_only_pass",
            "disagreement_rate",
        }.issubset(pairwise_metrics),
        "cost_latency_fields_complete": {
            "cost_basis",
            "observed_token_estimated_cost_usd",
            "actual_provider_billed_cost_usd",
            "provider_billed_cost_status",
            "median_latency_seconds",
        }.issubset(cost_latency_fields),
        "future_gates_complete": {
            "adapter_reporting_policy_loaded",
            "adapter_level_result_table_required",
            "paired_disagreement_table_required_for_shared_tasks",
            "cost_estimate_or_bill_status_required",
            "pooled_headline_primary_only_if_preregistered",
            "pooled_headline_secondary_or_diagnostic_otherwise",
        }.issubset(future_gates),
    }
    return {
        "valid": all(value is True for value in checks.values()),
        "checks": checks,
    }


def build_policy_payload(config: dict[str, Any]) -> dict[str, Any]:
    validation = validate_policy(config)
    return {
        "artifact": "policy",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "source_run_id": config["source_run_id"],
        "diagnostics_run_id": config["diagnostics_run_id"],
        "generated_at": now_utc(),
        "policy_valid": validation["valid"],
        "policy_checks": validation["checks"],
        "required_adapter_metrics": config["required_adapter_metrics"],
        "required_pairwise_metrics": config["required_pairwise_metrics"],
        "required_cost_latency_fields": config["required_cost_latency_fields"],
        "future_paid_gates": config["future_paid_gates"],
        "claim_boundaries": {
            "adapter_level_first": config["policy"]["adapter_level_results_before_pooled"],
            "pooled_only_cross_harness_headline_allowed": config["policy"]["pooled_only_cross_harness_headline_allowed"],
            "pooled_result_primary_allowed_only_if_preregistered": config["policy"][
                "pooled_result_allowed_when_preregistered_primary"
            ],
            "pooled_result_secondary_allowed_if_marked_diagnostic": config["policy"][
                "pooled_result_allowed_when_marked_diagnostic"
            ],
            "completed_paid_pilot": config["policy"]["completed_paid_pilot_claim_boundary"],
            "completed_paid_pilot_decision_mutable": config["policy"]["completed_paid_pilot_decision_mutable"],
            "predictive_validity_claim_allowed": config["policy"]["predictive_validity_claim_allowed"],
        },
        "cost_language": {
            "observed_token_estimated_cost_is_provider_billed_cost": config["policy"][
                "token_estimated_cost_is_provider_billed_cost"
            ],
            "exact_bill_claim_requires_actual_provider_billed_cost": config["policy"][
                "actual_provider_billed_cost_required_for_exact_bill_claim"
            ],
            "when_actual_provider_billed_cost_is_null": config["policy"]["if_actual_provider_billed_cost_null"],
        },
        "actions_suggested_next": [
            "Generate adapter-level score, cost, and latency tables before any pooled result.",
            "Mark any pooled adapter summary as preregistered primary or retrospective diagnostic.",
            "Keep the completed paid pilot claim boundary as pilot evidence only.",
        ],
    }


def render_policy_report(payload: dict[str, Any]) -> str:
    return f"""# Adapter-Stratified Reporting Policy

Status: `{'complete' if payload['policy_valid'] else 'blocked'}`.

What happened: the reporting rule now requires adapter-level evidence before any pooled cross-harness summary.
Why it matters: Codex and Kilo results can differ even under the same model, so a single pooled headline can hide a harness effect.
Action suggested next: generate adapter-stratified score, paired-disagreement, cost, and latency summaries from committed artifacts.

## Required Rule

- Adapter-level results must be shown before pooled adapter summaries.
- A pooled cross-harness result must not be the only headline.
- A pooled result can be primary only when it was preregistered before outcomes.
- Otherwise, pooled results are secondary or retrospective diagnostic evidence.
- The completed three-repo paid pilot remains pilot evidence only.
- This run does not change the completed paid pilot decision.

## Required Adapter Metrics

{chr(10).join(f'- `{metric}`' for metric in payload['required_adapter_metrics'])}

## Required Paired-Task Metrics

{chr(10).join(f'- `{metric}`' for metric in payload['required_pairwise_metrics'])}

## Cost Language

- Token-estimated cost is an estimate from observed token usage.
- Provider-billed exact cost can be claimed only when `actual_provider_billed_cost_usd` is available.
- If `actual_provider_billed_cost_usd` is null, the report must say provider-billed exact cost is unavailable.

## Validation

- Policy valid: `{payload['policy_valid']}`.
- Failed checks: `{[key for key, value in payload['policy_checks'].items() if value is not True]}`.
"""


def write_policy_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_policy_payload(config)
    write_json(output_path(config, "policy"), payload)
    write_text(report_path(config, "policy"), render_policy_report(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1 adapter-stratified reporting artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("command", choices=["policy"])
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.command == "policy":
        payload = write_policy_artifacts(config)
        if not payload["policy_valid"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
