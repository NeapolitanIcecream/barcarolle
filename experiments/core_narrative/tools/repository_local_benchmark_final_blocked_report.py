#!/usr/bin/env python3
"""Generate the terminal blocked report for the 0514 repository-local line."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "repository_local_benchmark_final_blocked_report"
SCHEMA_VERSION = "core-narrative.repository-local-benchmark-final-blocked-report.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_COMPLETION_AUDIT = (
    REPO_ROOT / "experiments/core_narrative/results/repository_local_benchmark_completion_audit_20260514.json"
)
DEFAULT_WSTAR_DECISION = REPO_ROOT / "experiments/core_narrative/results/rich_wstar_reserve_gate_decision_20260515.json"
DEFAULT_ACUT_READINESS = REPO_ROOT / "experiments/core_narrative/results/rich_acut_intervention_readiness_20260515.json"
DEFAULT_OUTPUT = (
    REPO_ROOT / "experiments/core_narrative/results/repository_local_benchmark_final_blocked_report_20260515.json"
)
DEFAULT_REPORT = (
    REPO_ROOT / "experiments/core_narrative/reports/2026-05-15_repository_local_benchmark_final_blocked_report.md"
)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completion-audit", default=str(DEFAULT_COMPLETION_AUDIT))
    parser.add_argument("--wstar-decision", default=str(DEFAULT_WSTAR_DECISION))
    parser.add_argument("--acut-readiness", default=str(DEFAULT_ACUT_READINESS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv) if argv is not None else None)


def load_json(path: Path, *, schema_version: str) -> dict[str, Any]:
    if not path.exists():
        raise ToolError("input artifact does not exist", path=str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != schema_version:
        raise ToolError(
            "unexpected input artifact schema",
            path=str(path),
            expected_schema_version=schema_version,
            actual_schema_version=payload.get("schema_version"),
        )
    return payload


def require_blocking_wstar_decision(wstar_decision: Mapping[str, Any]) -> None:
    if wstar_decision.get("primary_runs_authorized"):
        raise ToolError(
            "cannot generate blocked final report from an authorized primary-run decision",
            decision=wstar_decision.get("decision"),
        )
    if wstar_decision.get("decision") != "w_star_primary_reached_but_reserve_and_pool_gates_failed":
        raise ToolError(
            "cannot generate blocked final report from a non-terminal W* decision",
            decision=wstar_decision.get("decision"),
        )
    if wstar_decision.get("reserve_gate_reached") or wstar_decision.get("candidate_pool_gate_reached"):
        raise ToolError(
            "cannot generate blocked final report when W* reserve or candidate-pool gates are marked reached",
            reserve_gate_reached=wstar_decision.get("reserve_gate_reached"),
            candidate_pool_gate_reached=wstar_decision.get("candidate_pool_gate_reached"),
        )


def artifact_inputs(
    completion_audit_path: Path,
    wstar_decision_path: Path,
    acut_readiness_path: Path,
) -> dict[str, str]:
    return {
        "completion_audit": repo_relative(completion_audit_path),
        "rich_wstar_reserve_gate_decision": repo_relative(wstar_decision_path),
        "rich_acut_intervention_readiness": repo_relative(acut_readiness_path),
    }


def phase_statuses(wstar_decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "phase": "repository_admission",
            "status": "completed",
            "evidence": ["experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md"],
        },
        {
            "phase": "task_admission",
            "status": "completed_until_terminal_wstar_supply_gate",
            "summary": (
                "Rich C reached 20 accepted calibration candidates; Rich R reached 25 accepted primary-plus-reserve "
                "candidates; Rich W* reached 20 accepted primary candidates but cannot reach the 25 primary-plus-reserve "
                "target or 40-candidate pool under the frozen scan."
            ),
            "wstar_gate": {
                "accepted_primary": wstar_decision.get("accepted_w_star_primary_count"),
                "target_primary": wstar_decision.get("target_primary_count"),
                "target_primary_plus_reserve": wstar_decision.get("target_primary_plus_reserve_count"),
                "maximum_possible_admissions_under_current_scan": wstar_decision.get(
                    "maximum_possible_w_star_admissions_under_current_scan"
                ),
                "reserve_gap_even_if_all_remaining_admitted": wstar_decision.get(
                    "reserve_gap_even_if_all_remaining_admitted"
                ),
                "candidate_pool_gap": wstar_decision.get("candidate_pool_gap"),
            },
        },
        {
            "phase": "acut_manifest_readiness",
            "status": "completed_for_rich_execution_plan",
            "evidence": ["experiments/core_narrative/reports/2026-05-15_rich_acut_intervention_readiness.md"],
        },
        {
            "phase": "primary_execution",
            "status": "not_applicable_blocked_before_primary_runs",
            "r_primary_attempts": 0,
            "w_star_primary_attempts": 0,
            "g_attempts": 0,
        },
        {
            "phase": "analysis",
            "status": "not_applicable_no_primary_results",
            "r_score_available": False,
            "w_star_score_available": False,
            "selection_regret_available": False,
        },
    ]


def deliverable_statuses() -> list[dict[str, Any]]:
    return [
        {
            "deliverable": "repository_admission_report",
            "status": "completed",
            "artifact": "experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md",
        },
        {
            "deliverable": "task_generation_validity_report",
            "status": "completed_with_terminal_wstar_gate_block",
            "artifact": "experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_completion_audit.md",
        },
        {
            "deliverable": "role_isolation_artifacts",
            "status": "not_executed_blocked_before_primary_runs",
            "reason": "The W* reserve/candidate-pool gate failed before role-run task admission artifacts were needed.",
        },
        {
            "deliverable": "acut_intervention_manifest",
            "status": "completed_for_rich_execution_plan",
            "artifact": "experiments/core_narrative/reports/2026-05-15_rich_acut_intervention_readiness.md",
        },
        {
            "deliverable": "r_wstar_primary_result_report",
            "status": "not_applicable_blocked_before_primary_runs",
            "reason": "No R, W*, or G primary attempts were authorized or run.",
        },
        {
            "deliverable": "decision_validity_report",
            "status": "not_applicable_no_primary_results",
            "reason": "R -> W* selection validity cannot be estimated without primary results.",
        },
        {
            "deliverable": "threats_to_validity_report",
            "status": "completed_for_terminal_gate_result",
            "artifact": "experiments/core_narrative/reports/2026-05-15_repository_local_benchmark_final_blocked_report.md",
        },
    ]


def build_payload(
    completion_audit: Mapping[str, Any],
    wstar_decision: Mapping[str, Any],
    acut_readiness: Mapping[str, Any],
    *,
    completion_audit_path: Path,
    wstar_decision_path: Path,
    acut_readiness_path: Path,
) -> dict[str, Any]:
    require_blocking_wstar_decision(wstar_decision)
    if acut_readiness.get("primary_runs_authorized"):
        raise ToolError("ACUT readiness unexpectedly authorizes primary runs")

    prior_next_allowed_actions = list(wstar_decision.get("next_allowed_actions") or [])
    if len(prior_next_allowed_actions) != 3:
        raise ToolError("W* decision must preserve the three protocol-clean next actions")
    next_valid_paths = [
        prior_next_allowed_actions[0],
        prior_next_allowed_actions[1],
        "Publish or keep the blocked 0514 line as the terminal result; do not run primary attempts under the current frozen protocol.",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "report_id": "repository-local-benchmark-final-blocked-report-20260515",
        "status": "completed_blocked_before_primary_runs",
        "generated_at": iso_now(),
        "objective_file": completion_audit.get("objective_file"),
        "selected_terminal_path": "stop_before_primary_runs_and_report_blocked_by_wstar_supply",
        "artifact_inputs": artifact_inputs(completion_audit_path, wstar_decision_path, acut_readiness_path),
        "terminal_gate": {
            "repo_slug": wstar_decision.get("repo_slug"),
            "split": wstar_decision.get("split"),
            "decision": wstar_decision.get("decision"),
            "accepted_w_star_primary_count": wstar_decision.get("accepted_w_star_primary_count"),
            "target_primary_count": wstar_decision.get("target_primary_count"),
            "target_reserve_count": wstar_decision.get("target_reserve_count"),
            "target_primary_plus_reserve_count": wstar_decision.get("target_primary_plus_reserve_count"),
            "remaining_unadmitted_w_star_design_candidates": wstar_decision.get(
                "remaining_unadmitted_w_star_design_candidates"
            ),
            "maximum_possible_w_star_admissions_under_current_scan": wstar_decision.get(
                "maximum_possible_w_star_admissions_under_current_scan"
            ),
            "reserve_gap_even_if_all_remaining_admitted": wstar_decision.get(
                "reserve_gap_even_if_all_remaining_admitted"
            ),
            "candidate_pool_gap": wstar_decision.get("candidate_pool_gap"),
            "primary_floor_reached": wstar_decision.get("primary_floor_reached"),
            "reserve_gate_reached": wstar_decision.get("reserve_gate_reached"),
            "candidate_pool_gate_reached": wstar_decision.get("candidate_pool_gate_reached"),
            "full_gate_reached": wstar_decision.get("full_gate_reached"),
        },
        "primary_runs_authorized": False,
        "model_calls_made_after_terminal_gate": 0,
        "primary_execution": {
            "run_r_primary": False,
            "run_w_star_primary": False,
            "run_g": False,
            "r_primary_attempts": 0,
            "w_star_primary_attempts": 0,
            "g_attempts": 0,
            "reason": (
                "The frozen 0514 protocol requires W* reserve and candidate-pool gates before primary execution; "
                "the explicit W* decision fails those gates."
            ),
        },
        "phase_status": phase_statuses(wstar_decision),
        "deliverable_status": deliverable_statuses(),
        "prohibitions_preserved": {
            "used_wstar_results_to_modify_r": False,
            "used_acut_outputs_to_choose_wstar": False,
            "mixed_old_m5_m6_denominator": False,
            "lowered_success_gate_post_hoc": False,
            "overclaimed_wstar_freshness": False,
        },
        "completion_conclusion": {
            "active_goal_should_be_marked_complete": True,
            "reason": (
                "The selected stop-and-report branch has been executed. No further primary-run or analysis work is "
                "permitted inside the frozen 0514 protocol without a new preregistered revision or new eligible W* supply."
            ),
        },
        "prior_next_allowed_actions": prior_next_allowed_actions,
        "next_valid_paths": next_valid_paths,
        "claim_boundary": [
            "This is a terminal blocked-experiment report, not a primary result report.",
            "No R, W*, or G primary model attempts were authorized or run after the W* gate decision.",
            "R_score, W*_score, paired deltas, selection regret, rank correlation, and family effects are not claimed.",
            "Raw subjects, raw commits, reference patches, hidden verifiers, and ACUT outputs are not included.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    gate = payload["terminal_gate"]
    deliverable_rows = [
        f"| `{item['deliverable']}` | `{item['status']}` |"
        for item in payload["deliverable_status"]  # type: ignore[index]
    ]
    next_paths = [f"- {item}" for item in payload["next_valid_paths"]]  # type: ignore[index]

    return "\n".join(
        [
            "# Repository-Local Benchmark Final Blocked Report",
            "",
            f"Status: `{payload.get('status')}`",
            f"Objective file: `{payload.get('objective_file')}`",
            "",
            "## Terminal Decision",
            "",
            "The frozen 0514 repository-local line stops before primary runs. Rich W* reached the 20-task primary floor, "
            "but the explicit reserve-gate decision fails both the 5-reserve target and the 40-candidate pool target.",
            "",
            f"- Decision: `{gate.get('decision')}`",
            f"- Accepted W* primary candidates: `{gate.get('accepted_w_star_primary_count')}`",
            f"- Target primary + reserve count: `{gate.get('target_primary_plus_reserve_count')}`",
            f"- Maximum possible W* admissions under current scan: `{gate.get('maximum_possible_w_star_admissions_under_current_scan')}`",
            f"- Reserve gap even if all remaining candidates are admitted: `{gate.get('reserve_gap_even_if_all_remaining_admitted')}`",
            f"- Candidate-pool gap: `{gate.get('candidate_pool_gap')}`",
            "",
            "Primary runs authorized: `false`",
            "Model calls after terminal gate: `0`",
            "",
            "## Requirement Closure",
            "",
            "| Deliverable | Status |",
            "|---|---|",
            *deliverable_rows,
            "",
            "The primary result report and decision-validity analysis are not missing execution steps inside this protocol; "
            "they are not applicable because the frozen gate prevented R, W*, and G primary attempts.",
            "",
            "## Preserved Boundaries",
            "",
            "- W* results were not used to modify R.",
            "- ACUT outputs were not used to choose W*.",
            "- The old M5/M6 denominator was not mixed into this line.",
            "- Success gates were not lowered post hoc.",
            "- W* freshness is reported only as a blocked gate condition, not as a completed benchmark claim.",
            "",
            "## Next Valid Paths",
            "",
            *next_paths,
            "",
            "These paths require a new owner decision. They are not authorized continuations of primary execution under the "
            "current frozen 0514 protocol.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    completion_audit_path = Path(args.completion_audit).resolve()
    wstar_decision_path = Path(args.wstar_decision).resolve()
    acut_readiness_path = Path(args.acut_readiness).resolve()
    payload = build_payload(
        load_json(
            completion_audit_path,
            schema_version="core-narrative.repository-local-benchmark-completion-audit.v1",
        ),
        load_json(
            wstar_decision_path,
            schema_version="core-narrative.rich-wstar-reserve-gate-decision.v1",
        ),
        load_json(
            acut_readiness_path,
            schema_version="core-narrative.rich-acut-intervention-readiness.v1",
        ),
        completion_audit_path=completion_audit_path,
        wstar_decision_path=wstar_decision_path,
        acut_readiness_path=acut_readiness_path,
    )
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
