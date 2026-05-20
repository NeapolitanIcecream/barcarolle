#!/usr/bin/env python3
"""Audit bounded M2 live scoreability repair work without capability claims."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now


TOOL = "m2_live_scoreability_repair"
APPLY_PATCH_MARKER = "*** Begin Patch"
PATCH_READY_THRESHOLD = 0.70
INVALID_RATE_THRESHOLD = 0.25


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-summary", required=True)
    parser.add_argument("--unsafe-triage", required=True)
    parser.add_argument("--live-smoke-batch", help="Optional bounded live smoke batch JSON after repair.")
    parser.add_argument("--live-smoke-blocker", help="Optional machine-readable live-smoke blocker JSON.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(list(argv))


def read_json(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("JSON root must be an object", path=path)
    return data


def count_by(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def provider_text(path: str | None) -> str:
    if not path:
        return ""
    artifact = Path(path)
    if not artifact.exists():
        return ""
    raw = artifact.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(data, dict):
        return raw
    choice_content = (((data.get("choices") or [{}])[0] or {}).get("message") or {}).get("content") if isinstance(data.get("choices"), list) else None
    if isinstance(choice_content, str):
        return choice_content
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text
    return raw


def response_shape(record: Mapping[str, Any]) -> dict[str, Any]:
    text = provider_text(record.get("raw_response_artifact") if isinstance(record.get("raw_response_artifact"), str) else None)
    return {
        "raw_response_artifact_present": bool(record.get("raw_response_artifact")),
        "contains_apply_patch_transcript": APPLY_PATCH_MARKER in text,
        "contains_unified_diff_marker": "diff --git " in text or "\n--- " in text,
        "contains_redacted_url_marker": "<redacted:url>" in text,
        "response_char_count": len(text) if text else 0,
        "content_recorded": False,
    }


def concrete_mode(path_id: str, status: str, failure_owner: str, failure_class: str, shape: Mapping[str, Any]) -> tuple[str, str, str]:
    if path_id == "structured_files_json_v1_live" and failure_class == "unsafe_generated_text":
        return (
            "structured_full_file_patch_artifact_full_url_overbreadth",
            "classified_not_repaired",
            "No safe verifier-ready patch artifact was produced; preserve no-raw-URL/no-secret artifact policy.",
        )
    if path_id == "patch_or_files_v1_live" and failure_class == "unsupported_patch_response":
        if shape.get("contains_apply_patch_transcript") is True:
            return (
                "codex_apply_patch_transcript_previously_unsupported",
                "locally_repaired_by_parser_applicator_tests",
                "Future equivalent transcripts are accepted under patch-or-files-v1 when hunks match exactly.",
            )
        return (
            "unsupported_patch_shape_without_apply_patch_marker",
            "not_repaired",
            "No safe parser repair identified for this recorded shape.",
        )
    if path_id == "patch_or_files_v1_live" and failure_class == "invalid_unified_diff":
        return (
            "malformed_unified_diff",
            "not_auto_repaired",
            "Malformed hunk headers or line counts remain invalid; no semantic auto-rewrite is claimed.",
        )
    if status == "infra_failed" or failure_owner == "infrastructure":
        return (
            "provider_or_runner_infrastructure_failure",
            "not_locally_repaired",
            "Requires provider/tooling retry evidence; not a parser/applicator repair.",
        )
    return ("other_recorded_failure_mode", "not_repaired", "No local repair status assigned.")


def failure_modes(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    modes: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    records_by_path = summary.get("records") if isinstance(summary.get("records"), Mapping) else {}
    for path_id, records in records_by_path.items():
        if not str(path_id).endswith("_live"):
            continue
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, Mapping):
                continue
            status = str(record.get("status") or "unknown")
            if status in {"passed", "failed", "timeout", "missing"}:
                continue
            failure_owner = str(record.get("failure_owner") or "none")
            failure_class = str(record.get("failure_class") or "none")
            shape = response_shape(record)
            mode, repair_status, residual = concrete_mode(str(path_id), status, failure_owner, failure_class, shape)
            key = (str(path_id), status, failure_owner, failure_class, mode)
            entry = modes.setdefault(
                key,
                {
                    "path_id": str(path_id),
                    "status": status,
                    "failure_owner": failure_owner,
                    "failure_class": failure_class,
                    "concrete_mode": mode,
                    "local_repair_status": repair_status,
                    "residual_blocker_or_limit": residual,
                    "cell_count": 0,
                    "cells": [],
                    "response_shape_counts": {
                        "contains_apply_patch_transcript": 0,
                        "contains_unified_diff_marker": 0,
                        "contains_redacted_url_marker": 0,
                        "raw_response_artifact_present": 0,
                    },
                },
            )
            entry["cell_count"] += 1
            entry["cells"].append({"acut_id": record.get("acut_id"), "task_id": record.get("task_id")})
            for field in entry["response_shape_counts"]:
                if shape.get(field) is True:
                    entry["response_shape_counts"][field] += 1
    return sorted(modes.values(), key=lambda item: (item["path_id"], item["failure_class"], item["concrete_mode"]))


def live_smoke_status(args: argparse.Namespace) -> dict[str, Any]:
    if args.live_smoke_batch and args.live_smoke_blocker:
        raise ToolError("choose only one of --live-smoke-batch or --live-smoke-blocker")
    if args.live_smoke_blocker:
        blocker = read_json(args.live_smoke_blocker)
        return {
            "status": "blocked",
            "path": args.live_smoke_blocker,
            "model_call_made": bool(blocker.get("model_call_made")),
            "blockers": blocker.get("blockers") if isinstance(blocker.get("blockers"), list) else [],
            "details": blocker,
        }
    if args.live_smoke_batch:
        batch = read_json(args.live_smoke_batch)
        results = batch.get("results") if isinstance(batch.get("results"), list) else []
        status_counts = count_by([item for item in results if isinstance(item, Mapping)], "status")
        return {
            "status": "completed",
            "path": args.live_smoke_batch,
            "model_call_made": any(
                ((item.get("runner_result") or {}).get("model_call_made") is True)
                for item in results
                if isinstance(item, Mapping) and isinstance(item.get("runner_result"), Mapping)
            ),
            "total": len(results),
            "status_counts": status_counts,
            "submission_contract": batch.get("submission_contract"),
        }
    return {
        "status": "not_run",
        "model_call_made": False,
        "blockers": ["live_smoke_not_attempted_in_this_artifact_generation"],
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    summary = read_json(args.m2_summary)
    unsafe = read_json(args.unsafe_triage)
    modes = failure_modes(summary)
    live_paths = {
        path_id: path_summary
        for path_id, path_summary in (summary.get("paths") or {}).items()
        if isinstance(path_summary, Mapping) and str(path_id).endswith("_live")
    }
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "m2_summary": args.m2_summary,
            "unsafe_triage": args.unsafe_triage,
            "live_smoke_batch": args.live_smoke_batch,
            "live_smoke_blocker": args.live_smoke_blocker,
            "output": args.output,
            "report": args.report,
        },
        "scope": {
            "tasks": summary.get("tasks"),
            "acuts": summary.get("acuts"),
            "fixed_denominator": summary.get("fixed_denominator"),
        },
        "prior_m2_claim_status": summary.get("claim_status"),
        "prior_live_gate_status": {
            path_id: {
                "gate_status": path_summary.get("gate", {}).get("status") if isinstance(path_summary.get("gate"), Mapping) else None,
                "patch_ready_coverage": path_summary.get("patch_ready_coverage"),
                "invalid_submission_rate": path_summary.get("invalid_submission_rate"),
                "status_counts": path_summary.get("status_counts"),
                "failure_owner_counts": path_summary.get("failure_owner_counts"),
                "failure_class_counts": path_summary.get("failure_class_counts"),
            }
            for path_id, path_summary in live_paths.items()
        },
        "unsafe_triage_summary": unsafe.get("summary", {}),
        "failure_modes": modes,
        "local_repairs": [
            {
                "repair_id": "patch_or_files_v1_apply_patch_transcript_parser",
                "status": "implemented_with_focused_tests",
                "claim": "local contract/applicator scoreability repair only",
                "does_not_claim": [
                    "capability uplift",
                    "task-solving improvement",
                    "ranking reversal",
                    "G_score predictivity",
                    "license/admission/authorization outcome",
                ],
            },
            {
                "repair_id": "apply_patch_context_mismatch_failure_owner",
                "status": "implemented_with_focused_tests",
                "claim": "failed apply_patch transcript replays remain model-output invalid submissions",
            },
            {
                "repair_id": "apply_patch_context_mismatch_line_anchor_diagnostics",
                "status": "implemented_with_focused_tests",
                "claim": "mismatch artifacts identify path, hunk index, old-text hash, line-anchor occurrence counts, and redacted-URL match counts without recording source content",
            },
            {
                "repair_id": "patch_or_files_v1_redacted_url_source_context_match",
                "status": "implemented_with_focused_tests",
                "claim": "old hunk context containing <redacted:url> can match raw workspace URLs only when the replacement does not persist redacted placeholders; safe patch-artifact policy still applies",
            },
            {
                "repair_id": "patch_or_files_v1_default_flag_focused_context_excerpts",
                "status": "implemented_with_focused_tests",
                "claim": "future Click default/flag prompts include focused Option internals beyond the truncated source-file prefix",
            },
        ],
        "live_smoke": live_smoke_status(args),
        "success_criteria_preserved": {
            "patch_ready_coverage_min": PATCH_READY_THRESHOLD,
            "invalid_submission_rate_max": INVALID_RATE_THRESHOLD,
            "clean_replay_disagreement_count_max": 0,
            "fixed_denominator_preserved": True,
        },
        "claim_status": "scoreability_repair_attempted_not_capability_claim",
        "prohibited_claims": {
            "capability_uplift": False,
            "task_solving_improvement": False,
            "ranking_reversal": False,
            "g_score_predictivity": False,
            "license": False,
            "admission": False,
            "authorization": False,
        },
    }


def pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def write_report(payload: Mapping[str, Any], path: str) -> None:
    lines = [
        "# M2 Live Scoreability Repair Report",
        "",
        "Date: 2026-05-09",
        "",
        "## Scope",
        "",
        "This is a bounded scoreability repair attempt. It does not claim capability uplift, task-solving improvement, ranking reversal, G_score predictivity, license, admission, or authorization outcomes.",
        "",
        "## Prior Live Gate",
        "",
        "| Path | Gate | Patch-ready | Invalid rate | Status counts | Failure owners | Failure classes |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for path_id, item in payload.get("prior_live_gate_status", {}).items():
        if not isinstance(item, Mapping):
            continue
        lines.append(
            f"| `{path_id}` | `{item.get('gate_status')}` | {pct(item.get('patch_ready_coverage'))} | "
            f"{pct(item.get('invalid_submission_rate'))} | `{item.get('status_counts')}` | "
            f"`{item.get('failure_owner_counts')}` | `{item.get('failure_class_counts')}` |"
        )
    lines.extend(
        [
            "",
            "## Local Repair",
            "",
            "- `patch-or-files-v1` now accepts Codex `*** Begin Patch` transcripts when hunks match the prepared workspace exactly.",
            "- Failed apply-patch transcript replays are classified as model-output `invalid_submission`, not infrastructure failures.",
            "- Apply-patch context mismatches now record path, hunk index, hashes, line-anchor occurrence counts, and redacted-URL match counts without source content.",
            "- Redacted URL placeholders in old hunk context can match raw source URLs only when replacement text does not persist placeholders; safe patch-artifact policy is still enforced.",
            "- Future Click default/flag prompts include focused `Option` internals beyond the truncated source-file prefix.",
            "- Malformed unified diffs, provider HTTP failures, and structured full-file artifact-safety blockers remain residual blockers.",
            "",
            "## Failure Modes",
            "",
            "| Path | Failure class | Concrete mode | Cells | Local status | Residual blocker or limit |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for mode in payload.get("failure_modes", []):
        if not isinstance(mode, Mapping):
            continue
        lines.append(
            f"| `{mode.get('path_id')}` | `{mode.get('failure_class')}` | `{mode.get('concrete_mode')}` | "
            f"{mode.get('cell_count')} | `{mode.get('local_repair_status')}` | {mode.get('residual_blocker_or_limit')} |"
        )
    smoke = payload.get("live_smoke") if isinstance(payload.get("live_smoke"), Mapping) else {}
    smoke_details = f"Status: `{smoke.get('status')}`. Model call made: `{smoke.get('model_call_made')}`."
    if smoke.get("status") == "completed":
        smoke_details += f" Total cells: `{smoke.get('total')}`. Status counts: `{smoke.get('status_counts')}`."
    elif smoke.get("status") == "blocked":
        smoke_details += f" Blockers: `{smoke.get('blockers')}`."
    reproduction_lines = [
        "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_live_scoreability_repair.py \\",
        "  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \\",
        "  --unsafe-triage experiments/core_narrative/results/unsafe_generated_text_triage_20260509.json \\",
    ]
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), Mapping) else {}
    if inputs.get("live_smoke_batch"):
        reproduction_lines.append(f"  --live-smoke-batch {inputs.get('live_smoke_batch')} \\")
    if inputs.get("live_smoke_blocker"):
        reproduction_lines.append(f"  --live-smoke-blocker {inputs.get('live_smoke_blocker')} \\")
    reproduction_lines.extend(
        [
            f"  --output {inputs.get('output')} \\",
            f"  --report {inputs.get('report')}",
        ]
    )
    lines.extend(
        [
            "",
            "## Live Smoke",
            "",
            smoke_details,
            "",
            "## Reproduction",
            "",
            "```bash",
            *reproduction_lines,
            "```",
            "",
            "## Limitations",
            "",
            "The audit consumes existing redacted artifacts and optional bounded live-smoke evidence. It does not reinterpret no-model evidence as live scoreability and does not turn prior failed cells into capability evidence.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_payload(args)
        emit_json(payload, args.output)
        write_report(payload, args.report)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
