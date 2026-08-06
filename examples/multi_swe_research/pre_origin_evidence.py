#!/usr/bin/env python3
"""Build and verify compact evidence for the pre-Origin signal sprint."""

from __future__ import annotations

import argparse
import hashlib
import json
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_swe_research.response_composition import (  # noqa: E402
    RESULT_SCHEMA as COMPOSITION_RESULT_SCHEMA,
    load_response_composition_plan,
)
from examples.multi_swe_research.response_signal import (  # noqa: E402
    DIAGNOSTIC_RESULT_SCHEMA,
    RESULT_SCHEMA as RESPONSE_RESULT_SCHEMA,
    load_response_signal_amendment,
    load_response_signal_diagnostic_plan,
    load_response_signal_plan,
)


HERE = Path(__file__).resolve().parent
DEFAULT_SUMMARY = HERE / "evidence" / "pre-origin-signal-summary.json"
SUMMARY_SCHEMA = "barcarolle_multi_swe_pre_origin_signal_summary_v1"


def build_pre_origin_evidence_summary(
    *,
    response_results_path: Path,
    response_reproduction_path: Path,
    history_diagnostic_path: Path,
    history_reproduction_path: Path,
    composition_results_path: Path,
    composition_reproduction_path: Path,
) -> Mapping[str, Any]:
    response_plan = load_response_signal_plan()
    amendment = load_response_signal_amendment(plan=response_plan)
    diagnostic_plan = load_response_signal_diagnostic_plan(
        plan=response_plan,
        amendment=amendment,
    )
    composition_plan = load_response_composition_plan()
    response = _load_self_digested(
        response_results_path,
        schema=RESPONSE_RESULT_SCHEMA,
        digest_key="response_signal_results_digest",
    )
    response_reproduction = _load_self_digested(
        response_reproduction_path,
        schema=RESPONSE_RESULT_SCHEMA,
        digest_key="response_signal_results_digest",
    )
    history = _load_self_digested(
        history_diagnostic_path,
        schema=DIAGNOSTIC_RESULT_SCHEMA,
        digest_key="diagnostic_results_digest",
    )
    history_reproduction = _load_self_digested(
        history_reproduction_path,
        schema=DIAGNOSTIC_RESULT_SCHEMA,
        digest_key="diagnostic_results_digest",
    )
    composition = _load_self_digested(
        composition_results_path,
        schema=COMPOSITION_RESULT_SCHEMA,
        digest_key="response_composition_results_digest",
    )
    composition_reproduction = _load_self_digested(
        composition_reproduction_path,
        schema=COMPOSITION_RESULT_SCHEMA,
        digest_key="response_composition_results_digest",
    )
    _require_equal_reproduction(
        response_results_path,
        response_reproduction_path,
        response,
        response_reproduction,
        "RCP result",
    )
    _require_equal_reproduction(
        history_diagnostic_path,
        history_reproduction_path,
        history,
        history_reproduction,
        "RCP history diagnostic",
    )
    _require_equal_reproduction(
        composition_results_path,
        composition_reproduction_path,
        composition,
        composition_reproduction,
        "PRCS result",
    )
    _validate_result_bindings(
        response,
        history,
        composition,
        response_plan=response_plan,
        amendment=amendment,
        diagnostic_plan=diagnostic_plan,
        composition_plan=composition_plan,
    )

    response_stage_a = _mapping(
        _mapping(response, "stage_a"),
        "summary",
    )
    history_summary = _mapping(history, "summary")
    history_null = _mapping(history, "permutation_null")
    composition_stage_a = _mapping(
        _mapping(composition, "stage_a"),
        "summary",
    )
    composition_stage_a_null = _mapping(
        _mapping(composition, "stage_a"),
        "null",
    )
    composition_stage_b = _mapping(composition, "stage_b")
    horizons = _mapping(composition_stage_b, "horizons")
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    h5_summary = _mapping(h5, "summary")
    h10_summary = _mapping(h10, "summary")
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": "multi-swe-pre-origin-signal-sprint-2026-07-28",
        "source": {
            "selector_plan_digest": response.get("selector_plan_digest"),
            "response_signal_plan_digest": response_plan.get(
                "response_signal_plan_digest"
            ),
            "response_signal_amendment_digest": amendment.get("amendment_digest"),
            "response_signal_diagnostic_plan_digest": diagnostic_plan.get(
                "diagnostic_plan_digest"
            ),
            "response_composition_plan_digest": composition_plan.get(
                "response_composition_plan_digest"
            ),
        },
        "artifacts": {
            "response_signal": _artifact_binding(
                response_results_path,
                response,
                "response_signal_results_digest",
            ),
            "response_signal_reproduction": _artifact_binding(
                response_reproduction_path,
                response_reproduction,
                "response_signal_results_digest",
            ),
            "response_history_diagnostic": _artifact_binding(
                history_diagnostic_path,
                history,
                "diagnostic_results_digest",
            ),
            "response_history_reproduction": _artifact_binding(
                history_reproduction_path,
                history_reproduction,
                "diagnostic_results_digest",
            ),
            "response_composition": _artifact_binding(
                composition_results_path,
                composition,
                "response_composition_results_digest",
            ),
            "response_composition_reproduction": _artifact_binding(
                composition_reproduction_path,
                composition_reproduction,
                "response_composition_results_digest",
            ),
        },
        "alg_013_rcp": {
            "future_block_stage_a": {
                "macro_repository_auc": response_stage_a.get("macro_repository_auc"),
                "repository_bootstrap_interval_95": response_stage_a.get(
                    "repository_bootstrap_interval_95"
                ),
                "favorable_repository_count": response_stage_a.get(
                    "favorable_repository_count"
                ),
                "valid_origin_count": response_stage_a.get("valid_origin_count"),
                "origin_count": response_stage_a.get("origin_count"),
            },
            "history_precision_diagnostic": {
                "macro_repository_auc": history_summary.get("macro_repository_auc"),
                "repository_bootstrap_interval_95": history_summary.get(
                    "repository_bootstrap_interval_95"
                ),
                "favorable_repository_count": history_summary.get(
                    "favorable_repository_count"
                ),
                "permutation_corrected_rate": history_null.get(
                    "corrected_as_good_or_better_rate"
                ),
                "negative_control_construction": history_null.get("construction"),
                "preserves_complete_task_response_vectors": history_null.get(
                    "preserves_complete_task_response_vectors"
                ),
            },
            "candidate_decision": response.get("decision"),
            "diagnostic_decision": history.get("decision"),
            "stage_b_status": _mapping(response, "stage_b").get("status"),
            "stage_c_status": _mapping(response, "stage_c").get("status"),
        },
        "alg_014_prcs": {
            "cross_agent_response_signal": {
                "macro_repository_auc": composition_stage_a.get("macro_repository_auc"),
                "repository_bootstrap_interval_95": composition_stage_a.get(
                    "repository_bootstrap_interval_95"
                ),
                "favorable_repository_count": composition_stage_a.get(
                    "favorable_repository_count"
                ),
                "permutation_corrected_rate": composition_stage_a_null.get(
                    "corrected_as_good_or_better_rate"
                ),
                "requirements_met": _mapping(
                    composition,
                    "stage_a",
                ).get("all_requirements_met"),
            },
            "h5_future_increment": _composition_horizon_summary(h5),
            "h10_future_increment": _composition_horizon_summary(h10),
            "h5_controls": {
                "recent_loss": h5_summary.get("recent_macro_repository_loss"),
                "local_without_prior_loss": h5_summary.get(
                    "local_without_prior_macro_repository_loss"
                ),
                "global_only_loss": h5_summary.get("global_only_macro_repository_loss"),
                "recent_expert_selection_rate": h5_summary.get(
                    "recent_expert_selection_rate"
                ),
            },
            "h10_controls": {
                "local_without_prior_loss": h10_summary.get(
                    "local_without_prior_macro_repository_loss"
                ),
                "recent_expert_selection_rate": h10_summary.get(
                    "recent_expert_selection_rate"
                ),
            },
            "stage_b_gate": composition_stage_b.get("gate"),
            "candidate_decision": composition.get("decision"),
            "stage_c_status": _mapping(composition, "stage_c").get("status"),
        },
        "decision": {
            "static_raw_embedding_response_transfer_supported": False,
            "static_cross_agent_response_structure_supported": True,
            "pre_origin_target_future_increment_supported": False,
            "selector_nominated": False,
            "current_opened_source_candidate_search": "closed",
            "theory_design_may_resume_with": (
                "a new observable mechanism proposed independently of the "
                "opened outcomes, without replay on the opened panels"
            ),
            "empirical_nomination_replay_requires": [
                "a source with native Task time and historical Result availability plus denser repository-local Origins",
                "an independent complete Agent panel or source family",
                "a strict prospective target-repository campaign",
            ],
        },
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "sealed_holdout_reads": 0,
        },
        "claim_boundary": (
            "Opened, task-time-projected Multi-SWE development evidence. "
            "It supports a bottleneck diagnosis, not Selector validity."
        ),
    }
    summary["pre_origin_signal_summary_digest"] = canonical_digest(summary)
    return summary


def load_pre_origin_evidence_summary(
    path: Path = DEFAULT_SUMMARY,
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop("pre_origin_signal_summary_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("pre-Origin signal summary digest does not match")
    payload["pre_origin_signal_summary_digest"] = digest
    if payload.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("pre-Origin signal summary schema is unsupported")
    response_plan = load_response_signal_plan()
    amendment = load_response_signal_amendment(plan=response_plan)
    diagnostic_plan = load_response_signal_diagnostic_plan(
        plan=response_plan,
        amendment=amendment,
    )
    composition_plan = load_response_composition_plan()
    source = _mapping(payload, "source")
    if (
        source.get("response_signal_plan_digest")
        != response_plan.get("response_signal_plan_digest")
        or source.get("response_signal_amendment_digest")
        != amendment.get("amendment_digest")
        or source.get("response_signal_diagnostic_plan_digest")
        != diagnostic_plan.get("diagnostic_plan_digest")
        or source.get("response_composition_plan_digest")
        != composition_plan.get("response_composition_plan_digest")
    ):
        raise ValueError("pre-Origin signal summary plan binding changed")
    decision = _mapping(payload, "decision")
    if (
        decision.get("static_raw_embedding_response_transfer_supported") is not False
        or decision.get("static_cross_agent_response_structure_supported") is not True
        or decision.get("pre_origin_target_future_increment_supported") is not False
        or decision.get("selector_nominated") is not False
        or decision.get("current_opened_source_candidate_search") != "closed"
        or decision.get("theory_design_may_resume_with")
        != (
            "a new observable mechanism proposed independently of the "
            "opened outcomes, without replay on the opened panels"
        )
        or decision.get("empirical_nomination_replay_requires")
        != [
            "a source with native Task time and historical Result availability plus denser repository-local Origins",
            "an independent complete Agent panel or source family",
            "a strict prospective target-repository campaign",
        ]
    ):
        raise ValueError("pre-Origin signal summary decision changed")
    resources = _mapping(payload, "resource_use")
    if any(resources.get(key) != 0 for key in resources):
        raise ValueError("pre-Origin signal summary resource use changed")
    return payload


def _validate_result_bindings(
    response: Mapping[str, object],
    history: Mapping[str, object],
    composition: Mapping[str, object],
    *,
    response_plan: Mapping[str, object],
    amendment: Mapping[str, object],
    diagnostic_plan: Mapping[str, object],
    composition_plan: Mapping[str, object],
) -> None:
    if (
        response.get("response_signal_plan_digest")
        != response_plan.get("response_signal_plan_digest")
        or response.get("amendment_digest") != amendment.get("amendment_digest")
        or response.get("decision") != "response_representation_signal_rejected"
        or _mapping(response, "stage_b").get("status")
        != "not_reached_by_frozen_decision_order"
        or _mapping(response, "stage_c").get("status")
        != "not_reached_by_frozen_decision_order"
    ):
        raise ValueError("RCP rejected result binding changed")
    if (
        history.get("diagnostic_plan_digest")
        != diagnostic_plan.get("diagnostic_plan_digest")
        or history.get("rejected_results_digest")
        != response.get("response_signal_results_digest")
        or history.get("alg_013_decision") != "response_representation_signal_rejected"
        or history.get("decision") != "response_contrast_representation_closed"
    ):
        raise ValueError("RCP diagnostic result binding changed")
    history_null = _mapping(history, "permutation_null")
    if (
        history_null.get("construction")
        != "deterministic within-repository circular row shift"
        or history_null.get("preserves_complete_task_response_vectors") is not True
    ):
        raise ValueError("RCP diagnostic negative control changed")
    if (
        composition.get("response_composition_plan_digest")
        != composition_plan.get("response_composition_plan_digest")
        or composition.get("decision") != "target_future_increment_rejected"
        or _mapping(composition, "stage_a").get("all_requirements_met") is not True
        or _mapping(composition, "stage_c").get("status")
        != "not_reached_by_frozen_decision_order"
    ):
        raise ValueError("PRCS rejected result binding changed")


def _composition_horizon_summary(
    horizon: Mapping[str, object],
) -> Mapping[str, Any]:
    summary = _mapping(horizon, "summary")
    candidate = _mapping(summary, "candidate")
    deep = _mapping(_mapping(horizon, "deep"), "candidate")
    return {
        "macro_repository_loss": candidate.get("macro_repository_loss"),
        "macro_repository_baseline_loss": candidate.get(
            "macro_repository_baseline_loss"
        ),
        "macro_repository_difference": candidate.get("macro_repository_difference"),
        "relative_loss_reduction": candidate.get("relative_loss_reduction"),
        "favorable_repository_count": candidate.get("favorable_repository_count"),
        "deep_macro_repository_difference": deep.get("macro_repository_difference"),
        "deep_favorable_repository_count": deep.get("favorable_repository_count"),
        "calendar_span": horizon.get("calendar_span"),
    }


def _load_self_digested(
    path: Path,
    *,
    schema: str,
    digest_key: str,
) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop(digest_key, None)
    if canonical_digest(payload) != digest:
        raise ValueError(f"result digest does not match: {path}")
    payload[digest_key] = digest
    if payload.get("schema_version") != schema:
        raise ValueError(f"result schema is unsupported: {path}")
    return payload


def _require_equal_reproduction(
    first_path: Path,
    second_path: Path,
    first: Mapping[str, object],
    second: Mapping[str, object],
    label: str,
) -> None:
    if first != second or first_path.read_bytes() != second_path.read_bytes():
        raise ValueError(f"{label} reproduction changed")


def _artifact_binding(
    path: Path,
    payload: Mapping[str, object],
    digest_key: str,
) -> Mapping[str, object]:
    return {
        "logical_digest": payload.get(digest_key),
        "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "byte_count": path.stat().st_size,
    }


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _mapping(
    value: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, Mapping):
        raise ValueError(f"{key} must be an object")
    return nested


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a number")
    return float(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    verify = subparsers.add_parser("verify")
    for subparser in (build, verify):
        subparser.add_argument("--response-results", type=Path, required=True)
        subparser.add_argument(
            "--response-reproduction",
            type=Path,
            required=True,
        )
        subparser.add_argument(
            "--history-diagnostic",
            type=Path,
            required=True,
        )
        subparser.add_argument(
            "--history-reproduction",
            type=Path,
            required=True,
        )
        subparser.add_argument(
            "--composition-results",
            type=Path,
            required=True,
        )
        subparser.add_argument(
            "--composition-reproduction",
            type=Path,
            required=True,
        )
    build.add_argument("--output", type=Path, required=True)
    verify.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args(argv)
    summary = build_pre_origin_evidence_summary(
        response_results_path=args.response_results,
        response_reproduction_path=args.response_reproduction,
        history_diagnostic_path=args.history_diagnostic,
        history_reproduction_path=args.history_reproduction,
        composition_results_path=args.composition_results,
        composition_reproduction_path=args.composition_reproduction,
    )
    if args.command == "build":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    else:
        committed = load_pre_origin_evidence_summary(args.summary)
        if summary != committed:
            raise ValueError("committed pre-Origin summary is not reproducible")
    print(canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
