#!/usr/bin/env python3
"""Record the explicit Rich W* reserve-gate decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_pilot import repo_relative


TOOL = "rich_wstar_reserve_gate_decision"
SCHEMA_VERSION = "core-narrative.rich-wstar-reserve-gate-decision.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FEASIBILITY = REPO_ROOT / "experiments/core_narrative/results/rich_wstar_reserve_feasibility_20260514.json"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_wstar_reserve_gate_decision_20260515.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-15_rich_wstar_reserve_gate_decision.md"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feasibility", default=str(DEFAULT_FEASIBILITY), help="Rich W* reserve feasibility JSON.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public JSON decision output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    return parser.parse_args(list(argv) if argv is not None else None)


def load_feasibility(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ToolError("feasibility artifact does not exist", path=str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "core-narrative.rich-wstar-reserve-feasibility.v1":
        raise ToolError("unexpected feasibility schema", schema_version=payload.get("schema_version"))
    return payload


def build_payload(feasibility: Mapping[str, Any], feasibility_path: Path) -> dict[str, Any]:
    accepted_primary = int(feasibility.get("accepted_w_star_primary_count", 0))
    target_primary = int(feasibility.get("target_primary_count", 20))
    target_reserve = int(feasibility.get("target_reserve_count", 5))
    target_total = int(feasibility.get("target_primary_plus_reserve_count", target_primary + target_reserve))
    remaining = int(feasibility.get("remaining_unadmitted_w_star_design_candidates", 0))
    max_possible = int(feasibility.get("maximum_possible_w_star_admissions_under_current_scan", accepted_primary + remaining))
    reserve_gap = max(0, target_total - max_possible)
    candidate_pool_gap = int(feasibility.get("candidate_pool_gap", 0))

    primary_floor_reached = accepted_primary >= target_primary
    reserve_gate_reached = max_possible >= target_total and reserve_gap == 0
    candidate_pool_gate_reached = candidate_pool_gap == 0
    full_gate_reached = primary_floor_reached and reserve_gate_reached and candidate_pool_gate_reached
    decision = (
        "w_star_full_gate_passed_requires_separate_run_manifest"
        if full_gate_reached
        else "w_star_primary_reached_but_reserve_and_pool_gates_failed"
        if primary_floor_reached
        else "w_star_primary_gate_failed"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "repo_slug": "rich",
        "split": "W_star",
        "feasibility_artifact": repo_relative(feasibility_path),
        "model_calls_made": 0,
        "accepted_w_star_primary_count": accepted_primary,
        "target_primary_count": target_primary,
        "target_reserve_count": target_reserve,
        "target_primary_plus_reserve_count": target_total,
        "remaining_unadmitted_w_star_design_candidates": remaining,
        "maximum_possible_w_star_admissions_under_current_scan": max_possible,
        "reserve_gap_even_if_all_remaining_admitted": reserve_gap,
        "candidate_pool_gap": candidate_pool_gap,
        "primary_floor_reached": primary_floor_reached,
        "reserve_gate_reached": reserve_gate_reached,
        "candidate_pool_gate_reached": candidate_pool_gate_reached,
        "full_gate_reached": full_gate_reached,
        "decision": decision,
        "primary_runs_authorized": False,
        "authorization": {
            "run_r_primary": False,
            "run_w_star_primary": False,
            "run_g": False,
            "reason": "This decision does not authorize primary model attempts; W* reserve/candidate-pool gates remain failed under the frozen 0514 protocol."
            if not full_gate_reached
            else "All W* gates passed, but primary authorization must still be issued by a separate run manifest.",
        },
        "policy_basis": [
            "W* must not borrow earlier work.",
            "Do not lower success gates post hoc.",
            "Do not use W* results to modify R.",
            "Do not use ACUT outputs to choose W*.",
        ],
        "next_allowed_actions": [
            "Create a preregistered protocol revision if the experiment owner accepts a primary-only W* run without reserve.",
            "Or find additional W* candidates within the frozen W* window without using ACUT outputs or W* results.",
            "Or stop before primary runs and report the 0514 line as blocked by W* reserve/candidate-pool supply.",
        ],
        "claim_boundary": [
            "This artifact records a gate decision only.",
            "No ACUT primary attempt or model call was made.",
            "Raw subjects, raw commits, reference patches, and hidden verifier files are not included.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich W* Reserve-Gate Decision",
            "",
            f"Status: `{payload.get('status')}`",
            f"Decision: `{payload.get('decision')}`",
            "",
            "## Evidence",
            "",
            f"- Accepted W* primary candidates: `{payload.get('accepted_w_star_primary_count')}`",
            f"- Target primary count: `{payload.get('target_primary_count')}`",
            f"- Target primary + reserve count: `{payload.get('target_primary_plus_reserve_count')}`",
            f"- Remaining unadmitted W* design candidates: `{payload.get('remaining_unadmitted_w_star_design_candidates')}`",
            f"- Maximum possible W* admissions under current scan: `{payload.get('maximum_possible_w_star_admissions_under_current_scan')}`",
            f"- Reserve gap even if all remaining are admitted: `{payload.get('reserve_gap_even_if_all_remaining_admitted')}`",
            f"- Candidate-pool gap: `{payload.get('candidate_pool_gap')}`",
            "",
            "## Authorization",
            "",
            f"Primary runs authorized: `{str(payload.get('primary_runs_authorized')).lower()}`",
            "",
            "This decision does not authorize R, W*, or G primary attempts. Under the frozen 0514 protocol, W* reached the 20-task primary floor but still fails the 5-reserve and 40-candidate-pool targets.",
            "",
            "Next allowed actions are a preregistered protocol revision, additional W* candidates inside the frozen W* window, or stopping before primary runs and reporting the line as blocked by W* supply.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    feasibility_path = Path(args.feasibility).resolve()
    payload = build_payload(load_feasibility(feasibility_path), feasibility_path)
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
