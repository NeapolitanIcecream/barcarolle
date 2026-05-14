#!/usr/bin/env python3
"""Summarize Rich W* reserve feasibility after primary admission pilots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_pilot import DEFAULT_REPO, repo_relative, sha256_text
from rich_source_oracle_pilot import source_only_oracle_candidates
from rich_source_oracle_queue import public_source_oracle_item, triage_source_only_candidate


TOOL = "rich_wstar_reserve_feasibility"
SCHEMA_VERSION = "core-narrative.rich-wstar-reserve-feasibility.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_wstar_reserve_feasibility_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_wstar_reserve_feasibility.md"
RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"


ACCEPTED_WSTAR_ARTIFACTS = [
    "rich_direct_smoke_batch_20260514.json",
    "rich_source_oracle_pilot_20260514.json",
    "rich_source_oracle_pilot_emoji_20260514.json",
    "rich_source_oracle_pilot_linkids_20260514.json",
    "rich_source_oracle_pilot_drop38_20260514.json",
    "rich_source_oracle_pilot_svg_hash_20260514.json",
    "rich_source_oracle_pilot_currentframe_20260514.json",
    "rich_source_oracle_pilot_lazy_expandable_20260514.json",
    "rich_source_oracle_pilot_emoji_main_20260514.json",
    "rich_source_oracle_pilot_fix_docstring_20260514.json",
    "rich_source_oracle_pilot_spelling_20260514.json",
    "rich_source_oracle_pilot_remove_comments_20260514.json",
    "rich_replacement_oracle_pilot_20260514.json",
    "rich_replacement_oracle_pilot_zerospan_20260514.json",
    "rich_replacement_oracle_pilot_vs16_20260514.json",
    "rich_direct_without_nodes_oracle_pilot_20260514.json",
]

ACCEPTED_SOURCE_SUBJECT_DIGESTS = {
    "a41a08a1e787f9709cf7559b48f9957fa158675738ae848e1128c75642ba59dc",
    "09843c7601b117e3c82a9aea6f6fb91798f2133f7b4e87ade2b805aeff9ffac7",
    "798eb95fb90106178382ac013eb6cfabb51a398a5123020597e5b4844a3d0fb6",
    "1775d1e32da71cc75acd6fde38419ea6af94e8acbf4b600e7194a27717d7468b",
    "b432b2a758046b65dd9aeeedf17eaa5464ada014f23d1b4ef014207916d3fcff",
    "d5cf7be88ccba8cbfe8efc655a6f1f26adf8bc91071cacebdf8816c5d8ca35e2",
    "cff4bae4ebfa8c0fc65d78c19cecc57fa68f5d5590c94569982acd5a22201b6c",
    "d942f64886578d8747312e368ed92d9f6b2a8d45556f0f924e2444fe911d15af",
    "37f44829cea3ccdf11951a980fa7df6228e8bf4f79f63def9c5120b959c9bd9c",
    "1ff13fab66be01ebfabe5bac71b6943e72a263b9f1482da0e0606951ee81c353",
    "ad1a2bafd2e4a6b804dcd785da0e623e67bf9b86f6c37c8dc91b741b854f6871",
}

REMAINING_BLOCKERS = {
    "ws": ("whitespace_only_source_cleanup", "No semantic, API, docstring, import, or rendering discriminator was found."),
    "no need to rename locals": (
        "local_alias_refactor_behavior_equivalent",
        "The change renames local aliases only; observable rendering behavior is unchanged.",
    ),
    "more defensive condition": (
        "condition_equivalent_under_loop_invariant",
        "The changed branch is equivalent under split_graphemes loop bounds; no no-op/reference discriminator was found.",
    ),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    return parser.parse_args(list(argv) if argv is not None else None)


def accepted_primary_count(results_root: Path) -> int:
    direct_batch = json.loads((results_root / "rich_direct_smoke_batch_20260514.json").read_text(encoding="utf-8"))
    direct_count = int(direct_batch["accepted_count"])
    single_artifacts = [name for name in ACCEPTED_WSTAR_ARTIFACTS if name != "rich_direct_smoke_batch_20260514.json"]
    accepted_single_count = 0
    for name in single_artifacts:
        payload = json.loads((results_root / name).read_text(encoding="utf-8"))
        if payload.get("admission_decision") != "accepted":
            raise ToolError("expected accepted W* artifact", artifact=name, decision=payload.get("admission_decision"))
        accepted_single_count += 1
    return direct_count + accepted_single_count


def remaining_source_items(repo_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in source_only_oracle_candidates(repo_path):
        raw_subject = str(candidate.get("subject", ""))
        subject = raw_subject.strip()
        normalized_subject = subject.lower()
        subject_digest = sha256_text(raw_subject)
        if subject_digest in ACCEPTED_SOURCE_SUBJECT_DIGESTS:
            continue
        blocker_code, blocker_reason = REMAINING_BLOCKERS.get(
            normalized_subject,
            ("unclassified_unadmitted_candidate", "No accepted no-op/reference verifier is recorded."),
        )
        public_item = public_source_oracle_item(candidate, index=len(rows) + 1)
        triage = triage_source_only_candidate(candidate)
        rows.append(
            {
                "subject_digest": subject_digest,
                "source_anchor_digest": public_item["source_anchor_digest"],
                "base_anchor_digest": public_item["base_anchor_digest"],
                "changed_file_set_digest": public_item["changed_file_set_digest"],
                "family": candidate["family"],
                "surface": candidate["surface"],
                "triage_code": triage["triage_code"],
                "oracle_priority": triage["oracle_priority"],
                "reserve_blocker_code": blocker_code,
                "reserve_blocker_reason": blocker_reason,
            }
        )
    return rows


def build_payload(repo_path: Path, results_root: Path) -> dict[str, Any]:
    accepted_count = accepted_primary_count(results_root)
    remaining = remaining_source_items(repo_path)
    target_primary = 20
    target_reserve = 5
    target_total = target_primary + target_reserve
    max_total = accepted_count + len(remaining)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "repo_slug": "rich",
        "split": "W_star",
        "model_calls_made": 0,
        "primary_runs_authorized": False,
        "accepted_w_star_primary_count": accepted_count,
        "target_primary_count": target_primary,
        "target_reserve_count": target_reserve,
        "target_primary_plus_reserve_count": target_total,
        "remaining_unadmitted_w_star_design_candidates": len(remaining),
        "maximum_possible_w_star_admissions_under_current_scan": max_total,
        "reserve_gap_even_if_all_remaining_admitted": max(0, target_total - max_total),
        "candidate_pool_target": 40,
        "candidate_pool_gap": 17,
        "remaining_candidates": remaining,
        "decision": "w_star_primary_count_reached_but_reserve_and_pool_targets_unmet",
        "claim_boundary": [
            "This artifact does not freeze a full C/R/W* denominator.",
            "Raw subjects, raw commits, reference patches, and hidden verifier files are not included.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich W* Reserve Feasibility",
            "",
            f"Status: `{payload.get('status')}`",
            f"Generated at: `{payload.get('generated_at')}`",
            "",
            "## Result",
            "",
            f"- Accepted W* primary candidates: `{payload.get('accepted_w_star_primary_count')}`",
            f"- Target primary + reserve count: `{payload.get('target_primary_plus_reserve_count')}`",
            f"- Remaining unadmitted W* design candidates: `{payload.get('remaining_unadmitted_w_star_design_candidates')}`",
            f"- Maximum possible W* admissions under current scan: `{payload.get('maximum_possible_w_star_admissions_under_current_scan')}`",
            f"- Reserve gap even if all remaining are admitted: `{payload.get('reserve_gap_even_if_all_remaining_admitted')}`",
            f"- Candidate-pool gap: `{payload.get('candidate_pool_gap')}`",
            "",
            "Primary model attempts remain unauthorized because the W* reserve target, C/R task sets, role artifacts, and Rich ACUT variants are not complete.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(Path(args.repo).resolve(), RESULTS_ROOT)
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
