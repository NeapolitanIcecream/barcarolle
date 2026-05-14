#!/usr/bin/env python3
"""Build the Rich W* Golden-Oracle construction queue."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_task_admission_readiness import (
    DEFAULT_REPO,
    changed_file_set_digest,
    discover_candidates,
    public_candidate_row,
    repo_relative,
    sha256_text,
    source_anchor_digest,
)


TOOL = "rich_source_oracle_queue"
SCHEMA_VERSION = "core-narrative.rich-source-oracle-queue.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIRECT_BATCH = REPO_ROOT / "experiments/core_narrative/results/rich_direct_smoke_batch_20260514.json"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_source_oracle_queue_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_source_oracle_queue_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_source_oracle_queue.md"

PRIMARY_TARGET = 20
RESERVE_TARGET = 5
CANDIDATE_POOL_TARGET = 40

LOW_SIGNAL_RE = re.compile(
    r"(?i)\b(comments?|ws|docstring|spelling|dead|refactor|rename locals)\b|^import$|^drop 3\.8$"
)
PERFORMANCE_RE = re.compile(r"(?i)\b(perf|performance|lazy load|import time|faster|generator)\b")
BEHAVIOR_RE = re.compile(r"(?i)\b(support|defensive|none-able|expandable|preserve|handle|allow|fix)\b")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--direct-batch", default=str(DEFAULT_DIRECT_BATCH), help="Public direct-smoke batch JSON.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    return parser.parse_args(list(argv) if argv is not None else None)


def load_direct_batch(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ToolError("direct-smoke batch result is required before queue construction", path=str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolError("failed to parse direct-smoke batch result", path=str(path), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("direct-smoke batch result must be an object", path=str(path))
    return payload


def accepted_direct_count(direct_batch: Mapping[str, Any]) -> int:
    value = direct_batch.get("accepted_count", 0)
    return int(value) if isinstance(value, int) else 0


def rejected_direct_results(direct_batch: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    results = direct_batch.get("results")
    if not isinstance(results, list):
        return []
    return [
        result
        for result in results
        if isinstance(result, Mapping) and result.get("admission_decision") != "accepted"
    ]


def triage_source_only_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    subject = str(candidate.get("subject", ""))
    if LOW_SIGNAL_RE.search(subject):
        return {
            "oracle_priority": "low",
            "triage_code": "deprioritized_low_behavior_signal",
            "next_action": "manual_diff_review_before_verifier_authoring",
        }
    if PERFORMANCE_RE.search(subject):
        return {
            "oracle_priority": "medium",
            "triage_code": "performance_or_import_behavior_probe",
            "next_action": "construct_targeted_hidden_verifier_if_observable_without_timing_flakiness",
        }
    if BEHAVIOR_RE.search(subject):
        return {
            "oracle_priority": "high",
            "triage_code": "behavior_edge_case_probe",
            "next_action": "construct_targeted_hidden_verifier",
        }
    return {
        "oracle_priority": "medium",
        "triage_code": "manual_probe_required",
        "next_action": "manual_diff_review_before_verifier_authoring",
    }


def triage_direct_without_nodes(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "oracle_priority": "medium",
        "triage_code": "existing_tests_without_extractable_nodes",
        "next_action": "recover_or_replace_hidden_pytest_node",
    }


def triage_rejected_direct_result(result: Mapping[str, Any]) -> dict[str, Any]:
    noop = result.get("no_op_result") if isinstance(result.get("no_op_result"), Mapping) else {}
    noop_status = str(noop.get("status", "unknown"))
    if noop_status == "blocked_timeout":
        return {
            "oracle_priority": "medium",
            "triage_code": "timeout_verifier_prune_or_rewrite",
            "next_action": "prune_hanging_verifier_or_author_smaller_replacement",
        }
    if noop_status == "passed_unexpected":
        return {
            "oracle_priority": "high",
            "triage_code": "non_discriminating_existing_test",
            "next_action": "author_replacement_hidden_verifier",
        }
    return {
        "oracle_priority": "medium",
        "triage_code": "rejected_direct_candidate_review",
        "next_action": "inspect_private_smoke_artifacts_before_verifier_rewrite",
    }


def public_source_oracle_item(candidate: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    triage = triage_source_only_candidate(candidate)
    row = public_candidate_row(candidate)
    return {
        "queue_index": index,
        "work_item_kind": "source_only_golden_oracle",
        "source_anchor_digest": row["source_anchor_digest"],
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": row["subject_digest"],
        "changed_file_set_digest": row["changed_file_set_digest"],
        "family": row["family"],
        "surface": row["surface"],
        "source_file_count": row["source_file_count"],
        "test_file_count": row["test_file_count"],
        "test_node_count": row["test_node_count"],
        **triage,
    }


def public_direct_without_nodes_item(candidate: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    row = public_candidate_row(candidate)
    return {
        "queue_index": index,
        "work_item_kind": "direct_tests_without_extractable_nodes",
        "source_anchor_digest": row["source_anchor_digest"],
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": row["subject_digest"],
        "changed_file_set_digest": row["changed_file_set_digest"],
        "family": row["family"],
        "surface": row["surface"],
        "source_file_count": row["source_file_count"],
        "test_file_count": row["test_file_count"],
        "test_node_count": row["test_node_count"],
        **triage_direct_without_nodes(candidate),
    }


def public_rejected_direct_item(result: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    triage = triage_rejected_direct_result(result)
    return {
        "queue_index": index,
        "work_item_kind": "direct_smoke_replacement_oracle",
        "source_anchor_digest": result.get("source_anchor_digest"),
        "base_anchor_digest": result.get("base_anchor_digest"),
        "subject_digest": result.get("subject_digest"),
        "changed_file_set_digest": result.get("changed_file_set_digest"),
        "family": result.get("family"),
        "surface": result.get("surface"),
        "source_file_count": result.get("source_file_count"),
        "test_file_count": result.get("test_file_count"),
        "test_node_count": result.get("test_node_count"),
        "prior_no_op_status": result.get("no_op_result", {}).get("status") if isinstance(result.get("no_op_result"), Mapping) else None,
        "prior_reference_status": result.get("reference_result", {}).get("status")
        if isinstance(result.get("reference_result"), Mapping)
        else None,
        **triage,
    }


def item_sort_key(item: Mapping[str, Any]) -> tuple[int, str, int]:
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    kind_rank = {
        "source_only_golden_oracle": 0,
        "direct_smoke_replacement_oracle": 1,
        "direct_tests_without_extractable_nodes": 2,
    }
    return (
        priority_rank.get(str(item.get("oracle_priority")), 9),
        str(item.get("triage_code", "")),
        kind_rank.get(str(item.get("work_item_kind")), 9),
    )


def build_queue_items(candidates: Sequence[Mapping[str, Any]], direct_batch: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_items: list[dict[str, Any]] = []
    queue_index = 1
    for candidate in candidates:
        if candidate.get("window") != "W_star":
            continue
        if candidate.get("oracle_requirement") == "golden_oracle_required":
            raw_items.append(public_source_oracle_item(candidate, index=queue_index))
            queue_index += 1
        elif candidate.get("oracle_requirement") == "direct_tests_without_extractable_nodes":
            raw_items.append(public_direct_without_nodes_item(candidate, index=queue_index))
            queue_index += 1
    for result in rejected_direct_results(direct_batch):
        raw_items.append(public_rejected_direct_item(result, index=queue_index))
        queue_index += 1
    sorted_items = sorted(raw_items, key=item_sort_key)
    for index, item in enumerate(sorted_items, start=1):
        item["queue_index"] = index
    return sorted_items


def summarize_queue(*, items: Sequence[Mapping[str, Any]], accepted_direct: int, design_candidate_count: int) -> dict[str, Any]:
    kinds = Counter(str(item.get("work_item_kind")) for item in items)
    priorities = Counter(str(item.get("oracle_priority")) for item in items)
    triage_codes = Counter(str(item.get("triage_code")) for item in items)
    maximum_admitted_if_all_oracles_pass = accepted_direct + len(items)
    needed_for_primary = max(0, PRIMARY_TARGET - accepted_direct)
    needed_for_primary_plus_reserve = max(0, PRIMARY_TARGET + RESERVE_TARGET - accepted_direct)
    return {
        "accepted_direct_count": accepted_direct,
        "oracle_work_item_count": len(items),
        "work_item_kind_counts": dict(sorted(kinds.items())),
        "oracle_priority_counts": dict(sorted(priorities.items())),
        "triage_code_counts": dict(sorted(triage_codes.items())),
        "additional_acceptances_needed_for_20_primary": needed_for_primary,
        "additional_acceptances_needed_for_20_primary_plus_5_reserve": needed_for_primary_plus_reserve,
        "maximum_admitted_design_count_if_all_oracles_pass": maximum_admitted_if_all_oracles_pass,
        "can_reach_20_primary_if_all_oracles_pass": maximum_admitted_if_all_oracles_pass >= PRIMARY_TARGET,
        "can_reach_20_primary_plus_5_reserve_under_current_design_supply": design_candidate_count >= PRIMARY_TARGET + RESERVE_TARGET,
        "candidate_pool_gap_to_40": max(0, CANDIDATE_POOL_TARGET - design_candidate_count),
        "oracle_yield_required_for_20_primary": needed_for_primary,
        "oracle_yield_required_for_20_primary_plus_5_reserve": needed_for_primary_plus_reserve,
    }


def private_queue_payload(candidates: Sequence[Mapping[str, Any]], direct_batch: Mapping[str, Any]) -> dict[str, Any]:
    source_candidates = [
        {
            "commit": candidate.get("commit"),
            "base_commit": candidate.get("base_commit"),
            "subject": candidate.get("subject"),
            "window": candidate.get("window"),
            "family": candidate.get("family"),
            "surface": candidate.get("surface"),
            "source_files": candidate.get("source_files"),
            "test_files": candidate.get("test_files"),
            "test_nodes": candidate.get("test_nodes"),
            "oracle_requirement": candidate.get("oracle_requirement"),
            "triage": triage_source_only_candidate(candidate)
            if candidate.get("oracle_requirement") == "golden_oracle_required"
            else triage_direct_without_nodes(candidate)
            if candidate.get("oracle_requirement") == "direct_tests_without_extractable_nodes"
            else None,
        }
        for candidate in candidates
        if candidate.get("window") == "W_star"
        and candidate.get("oracle_requirement") in {"golden_oracle_required", "direct_tests_without_extractable_nodes"}
    ]
    return {
        "generated_at": iso_now(),
        "repo_slug": "rich",
        "split": "W_star",
        "private_raw_candidate_count": len(source_candidates),
        "source_candidates": source_candidates,
        "rejected_direct_results": rejected_direct_results(direct_batch),
    }


def build_payload(*, repo_path: Path, direct_batch_path: Path, private_root: Path) -> dict[str, Any]:
    direct_batch = load_direct_batch(direct_batch_path)
    candidates = discover_candidates(repo_path)
    w_star_candidates = [candidate for candidate in candidates if candidate.get("window") == "W_star"]
    items = build_queue_items(w_star_candidates, direct_batch)
    summary = summarize_queue(
        items=items,
        accepted_direct=accepted_direct_count(direct_batch),
        design_candidate_count=len(w_star_candidates),
    )
    private_root.mkdir(parents=True, exist_ok=True)
    private_payload_path = private_root / "rich_source_oracle_queue_private.json"
    write_json(private_payload_path, private_queue_payload(w_star_candidates, direct_batch))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": "W_star",
        "private_artifact_root": repo_relative(private_root),
        "private_queue_artifact": repo_relative(private_payload_path),
        "primary_runs_authorized": False,
        "direct_batch_artifact": repo_relative(direct_batch_path),
        "denominator_boundary": {
            "primary_target": PRIMARY_TARGET,
            "reserve_target": RESERVE_TARGET,
            "candidate_pool_target": CANDIDATE_POOL_TARGET,
            "design_candidate_count": len(w_star_candidates),
            **summary,
        },
        "queue_items": items,
        "claim_boundary": [
            "This is a Golden-Oracle construction queue, not task admission.",
            "Queue priority is heuristic triage only; no hidden verifier has been accepted from this artifact.",
            "Raw commits, raw subjects, source file lists, and private smoke details are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
            "The 20-primary plus 5-reserve target remains unreachable under the current W* design count unless the gate is explicitly revised.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    boundary = payload.get("denominator_boundary") if isinstance(payload.get("denominator_boundary"), Mapping) else {}
    lines = [
        "# Rich W* Golden-Oracle Queue",
        "",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Denominator Boundary",
        "",
        f"- Accepted direct W* tasks: `{boundary.get('accepted_direct_count')}`",
        f"- Oracle work items: `{boundary.get('oracle_work_item_count')}`",
        f"- Additional acceptances needed for 20 primary: `{boundary.get('additional_acceptances_needed_for_20_primary')}`",
        f"- Maximum admitted design count if all queued oracles pass: `{boundary.get('maximum_admitted_design_count_if_all_oracles_pass')}`",
        f"- Can reach 20 primary if all queued oracles pass: `{boundary.get('can_reach_20_primary_if_all_oracles_pass')}`",
        f"- Can reach 20 primary + 5 reserve under current design supply: `{boundary.get('can_reach_20_primary_plus_5_reserve_under_current_design_supply')}`",
        f"- 40-candidate pool gap: `{boundary.get('candidate_pool_gap_to_40')}`",
        "",
        "## Queue Composition",
        "",
        f"- Work item kinds: `{json.dumps(boundary.get('work_item_kind_counts', {}), sort_keys=True)}`",
        f"- Priorities: `{json.dumps(boundary.get('oracle_priority_counts', {}), sort_keys=True)}`",
        f"- Triage codes: `{json.dumps(boundary.get('triage_code_counts', {}), sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "This queue does not admit tasks or authorize primary runs. It only identifies the next hidden-verifier construction work needed after the direct-smoke batch.",
        "",
    ]
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    report = Path(args.report)
    payload = build_payload(
        repo_path=Path(args.repo).resolve(),
        direct_batch_path=Path(args.direct_batch).resolve(),
        private_root=Path(args.private_root).resolve(),
    )
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
