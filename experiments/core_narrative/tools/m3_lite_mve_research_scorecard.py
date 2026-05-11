#!/usr/bin/env python3
"""Build the M3-lite research-grade minimum viable evidence scorecard."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "m3_lite_mve_research_scorecard"
SCHEMA_VERSION = "core-narrative.m3-lite-mve.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MATRIX = REPO_ROOT / "experiments/core_narrative/configs/m3_lite_mve_matrix.yaml"
DEFAULT_SCORECARD_V1 = REPO_ROOT / "experiments/core_narrative/results/scorecard_v1_before_predictivity_20260510.json"
DEFAULT_M2_5 = REPO_ROOT / "experiments/core_narrative/results/m2_5_workspace_diff_summary_20260510.json"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/m3_lite_mve_research_scorecard_20260511.json"
DEFAULT_M2_5_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/m3_lite_m2_5_recovery_20260511.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-11_m3_lite_minimum_viable_evidence.md"
OUTCOMES = (
    "verified_pass",
    "verified_fail",
    "invalid_submission",
    "infra_failed",
    "missing_coverage",
    "policy_invalid",
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--scorecard-v1", default=str(DEFAULT_SCORECARD_V1))
    parser.add_argument("--m2-5-summary", default=str(DEFAULT_M2_5))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--m2-5-output", default=str(DEFAULT_M2_5_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def load_json_input(path_value: str | Path | None, *, input_key: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    path = resolve_path(str(path_value)) if path_value is not None else None
    info: dict[str, Any] = {
        "input_key": input_key,
        "path": repo_relative(path),
        "present": False,
        "status": "missing_input",
    }
    if path is None or not path.exists():
        return info, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        info.update({"status": "invalid_json", "error": str(exc)})
        return info, None
    if not isinstance(payload, dict):
        info["status"] = "invalid_json_root"
        return info, None
    info.update(
        {
            "present": True,
            "status": "loaded",
            "sha256": sha256_file(path),
            "byte_count": path.stat().st_size,
            "tool": payload.get("tool"),
            "schema_version": payload.get("schema_version"),
            "payload_status": payload.get("status"),
            "generated_at": payload.get("generated_at"),
        }
    )
    return info, payload


def require_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    matrix_root = matrix.get("matrix") if isinstance(matrix.get("matrix"), Mapping) else {}
    acuts = [str(item) for item in matrix_root.get("acuts", []) if isinstance(item, str)]
    rbench = [str(item) for item in matrix_root.get("rbench_tasks", []) if isinstance(item, str)]
    rwork = [str(item) for item in matrix_root.get("rwork_tasks", []) if isinstance(item, str)]
    if len(acuts) < 3:
        raise ToolError("M3-lite protocol requires at least 3 ACUTs", acuts=acuts)
    if len(rbench) < 4 or len(rwork) < 4:
        raise ToolError("M3-lite protocol requires at least 4 RBench and 4 RWork tasks", rbench=rbench, rwork=rwork)
    return {
        "repository": matrix_root.get("repository"),
        "acuts": acuts,
        "rbench_tasks": rbench,
        "rwork_tasks": rwork,
        "fixed_denominators": {
            "r_score_cells": len(acuts) * len(rbench),
            "w_score_cells": len(acuts) * len(rwork),
        },
    }


def scorecard_entries(scorecard_v1: Mapping[str, Any] | None, *, source_input: str) -> dict[tuple[str, str], Mapping[str, Any]]:
    entries: dict[tuple[str, str], Mapping[str, Any]] = {}
    if not isinstance(scorecard_v1, Mapping):
        return entries
    for entry in scorecard_v1.get("score_input_entries", []):
        if not isinstance(entry, Mapping):
            continue
        if entry.get("source_input") != source_input:
            continue
        acut_id = entry.get("acut_id")
        task_id = entry.get("task_id")
        if isinstance(acut_id, str) and isinstance(task_id, str):
            entries[(acut_id, task_id)] = entry
    return entries


def outcome_from_entry(entry: Mapping[str, Any] | None) -> str:
    if entry is None:
        return "missing_coverage"
    outcome = entry.get("scorecard_v1_outcome")
    if isinstance(outcome, str) and outcome in OUTCOMES:
        return outcome
    status = str(entry.get("status") or "")
    if status == "passed":
        return "verified_pass"
    if status in {"failed", "timeout"}:
        return "verified_fail"
    if status == "invalid_submission":
        return "invalid_submission"
    if status == "infra_failed":
        return "infra_failed"
    if status == "policy_invalid":
        return "policy_invalid"
    return "missing_coverage"


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def empty_counts() -> dict[str, int]:
    return {outcome: 0 for outcome in OUTCOMES}


def aggregate_cells(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = empty_counts()
    by_acut: dict[str, dict[str, Any]] = {}
    for cell in cells:
        outcome = str(cell.get("research_outcome"))
        counts[outcome] = counts.get(outcome, 0) + 1
        acut_id = str(cell.get("acut_id"))
        stats = by_acut.setdefault(
            acut_id,
            {
                "fixed_denominator": 0,
                "verified_pass": 0,
                "verified_fail": 0,
                "invalid_submission": 0,
                "infra_failed": 0,
                "missing_coverage": 0,
                "policy_invalid": 0,
            },
        )
        stats["fixed_denominator"] += 1
        stats[outcome] = stats.get(outcome, 0) + 1
    for stats in by_acut.values():
        verified = int(stats.get("verified_pass", 0)) + int(stats.get("verified_fail", 0))
        stats["fixed_denominator_pass_rate"] = rate(int(stats.get("verified_pass", 0)), int(stats.get("fixed_denominator", 0)))
        stats["verified_correctness_rate"] = rate(int(stats.get("verified_pass", 0)), verified)
        stats["verified_outcome_count"] = verified
    verified_pass = counts["verified_pass"]
    verified_fail = counts["verified_fail"]
    verified_total = verified_pass + verified_fail
    total = len(cells)
    return {
        "fixed_denominator": total,
        "outcome_counts": counts,
        "verified_pass_count": verified_pass,
        "verified_outcome_count": verified_total,
        "fixed_denominator_pass_rate": rate(verified_pass, total),
        "verified_correctness_rate": rate(verified_pass, verified_total),
        "by_acut": dict(sorted(by_acut.items())),
    }


def build_split_cells(
    *,
    scorecard_v1: Mapping[str, Any] | None,
    acuts: Sequence[str],
    tasks: Sequence[str],
    source_input: str,
    split_score: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries = scorecard_entries(scorecard_v1, source_input=source_input)
    cells: list[dict[str, Any]] = []
    for acut_id in acuts:
        for task_id in tasks:
            entry = entries.get((acut_id, task_id))
            outcome = outcome_from_entry(entry)
            cells.append(
                {
                    "score": split_score,
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "source_input": source_input,
                    "present": entry is not None,
                    "research_outcome": outcome,
                    "verified_correctness_credit": outcome == "verified_pass",
                    "status": entry.get("status") if entry is not None else "missing",
                    "run_id": entry.get("run_id") if entry is not None else None,
                    "failure_owner": entry.get("failure_owner") if entry is not None else "missing",
                    "failure_class": entry.get("failure_class") if entry is not None else "missing_coverage",
                }
            )
    return cells, aggregate_cells(cells)


def collect_workspace_diff(workspace: Path | None) -> dict[str, Any]:
    if workspace is None or not workspace.exists():
        return {"present": False, "status": "missing_workspace", "path": repo_relative(workspace)}
    if not (workspace / ".git").exists():
        return {"present": False, "status": "not_git_workspace", "path": repo_relative(workspace)}
    completed = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff", "--unified=0", "HEAD"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "present": False,
            "status": "git_diff_failed",
            "path": repo_relative(workspace),
            "stderr_sha256": sha256_bytes(completed.stderr),
        }
    return {
        "present": bool(completed.stdout),
        "status": "diff_collected",
        "path": repo_relative(workspace),
        "size_bytes": len(completed.stdout),
        "sha256": sha256_bytes(completed.stdout) if completed.stdout else None,
    }


def read_normalized(path: Path | None) -> Mapping[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, Mapping) else {}


def patch_evidence(path: Path | None, fallback_sha: object, fallback_size: object) -> dict[str, Any]:
    exists = path is not None and path.is_file()
    fallback_size_int = fallback_size if isinstance(fallback_size, int) else None
    fallback_sha_str = fallback_sha if isinstance(fallback_sha, str) and fallback_sha else None
    size = path.stat().st_size if exists and path is not None else fallback_size_int
    sha = sha256_file(path) if exists and path is not None else fallback_sha_str
    return {
        "present": bool(size is not None and int(size) > 0 and sha),
        "path": repo_relative(path),
        "sha256": sha,
        "size_bytes": size,
    }


def recover_m2_5(m2_5_payload: Mapping[str, Any] | None) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if not isinstance(m2_5_payload, Mapping):
        return {
            "status": "missing_input",
            "records": records,
            "summary": {
                "total": 0,
                "research_scoreable_count": 0,
                "persisted_patch_count": 0,
                "final_workspace_diff_count": 0,
            },
        }
    for item in m2_5_payload.get("results", []):
        if not isinstance(item, Mapping):
            continue
        patch_path = resolve_path(item.get("patch_path"))
        workspace = resolve_path(item.get("workspace") or item.get("runner_workspace"))
        normalized_path = resolve_path(item.get("normalized_result"))
        normalized = read_normalized(normalized_path)
        metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
        clean_replay = metadata.get("clean_patch_replay") if isinstance(metadata.get("clean_patch_replay"), Mapping) else {}
        verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
        review = normalized.get("review") if isinstance(normalized.get("review"), Mapping) else {}
        patch = patch_evidence(
            patch_path,
            item.get("candidate_patch_sha256"),
            item.get("candidate_patch_size_bytes"),
        )
        workspace_diff = collect_workspace_diff(workspace)
        evidence_types: list[str] = []
        if patch["present"]:
            evidence_types.append("persisted_submission_patch")
        if workspace_diff.get("present") is True:
            evidence_types.append("final_workspace_git_diff")
        if verification.get("exit_code") is not None:
            evidence_types.append("verifier_or_test_result")
        if review.get("mergeability_grade") is not None:
            evidence_types.append("review_evidence")
        status = str(item.get("status") or normalized.get("status") or "missing")
        if status == "passed":
            research_outcome = "verified_pass"
        elif status in {"failed", "timeout"}:
            research_outcome = "verified_fail"
        elif patch["present"] and clean_replay.get("status") == "invalid_submission":
            research_outcome = "produced_patch_replay_invalid"
        elif patch["present"] or workspace_diff.get("present") is True:
            research_outcome = "produced_patch_unverified"
        else:
            research_outcome = "no_research_scoreable_patch"
        records.append(
            {
                "run_id": item.get("run_id"),
                "acut_id": item.get("acut_id"),
                "task_id": item.get("task_id"),
                "status": status,
                "research_scoreable": bool(evidence_types),
                "research_outcome": research_outcome,
                "evidence_types": evidence_types,
                "clean_room_replay_required": False,
                "clean_room_replay_status": clean_replay.get("status") or item.get("clean_replay_status"),
                "failure_owner": item.get("failure_owner"),
                "failure_class": item.get("failure_class"),
                "patch": patch,
                "final_workspace_diff": workspace_diff,
                "normalized_result": {
                    "present": bool(normalized),
                    "path": repo_relative(normalized_path),
                    "status": normalized.get("status") if normalized else None,
                },
                "verifier_or_test_evidence": {
                    "present": verification.get("exit_code") is not None,
                    "exit_code": verification.get("exit_code"),
                    "duration_seconds": verification.get("duration_seconds"),
                },
                "review_evidence": {
                    "present": review.get("mergeability_grade") is not None,
                    "mergeability_grade": review.get("mergeability_grade"),
                    "wrong_module": review.get("wrong_module"),
                    "rule_violation": review.get("rule_violation"),
                },
            }
        )
    summary_counts: dict[str, int] = {}
    for record in records:
        outcome = str(record["research_outcome"])
        summary_counts[outcome] = summary_counts.get(outcome, 0) + 1
    return {
        "status": "completed",
        "source_schema_version": m2_5_payload.get("schema_version"),
        "source_run_prefix": m2_5_payload.get("run_prefix"),
        "records": records,
        "summary": {
            "total": len(records),
            "research_scoreable_count": sum(1 for record in records if record["research_scoreable"]),
            "persisted_patch_count": sum(1 for record in records if record["patch"]["present"]),
            "final_workspace_diff_count": sum(1 for record in records if record["final_workspace_diff"].get("present") is True),
            "verifier_or_test_evidence_count": sum(1 for record in records if record["verifier_or_test_evidence"]["present"]),
            "review_evidence_count": sum(1 for record in records if record["review_evidence"]["present"]),
            "outcome_counts": dict(sorted(summary_counts.items())),
        },
    }


def score_table(acuts: Sequence[str], r_summary: Mapping[str, Any], w_summary: Mapping[str, Any], g_score: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    r_by_acut = r_summary.get("by_acut") if isinstance(r_summary.get("by_acut"), Mapping) else {}
    w_by_acut = w_summary.get("by_acut") if isinstance(w_summary.get("by_acut"), Mapping) else {}
    for acut_id in acuts:
        r_stats = r_by_acut.get(acut_id) if isinstance(r_by_acut.get(acut_id), Mapping) else {}
        w_stats = w_by_acut.get(acut_id) if isinstance(w_by_acut.get(acut_id), Mapping) else {}
        rows.append(
            {
                "acut_id": acut_id,
                "g_score": None,
                "g_score_status": g_score.get("availability_status") or "unavailable",
                "r_score_partial_fixed_denominator": r_stats.get("fixed_denominator_pass_rate"),
                "r_verified_correctness_rate": r_stats.get("verified_correctness_rate"),
                "r_verified_outcome_count": r_stats.get("verified_outcome_count"),
                "w_score_partial_fixed_denominator": w_stats.get("fixed_denominator_pass_rate"),
                "w_verified_correctness_rate": w_stats.get("verified_correctness_rate"),
                "w_verified_outcome_count": w_stats.get("verified_outcome_count"),
            }
        )
    return rows


def story_impact(payload: Mapping[str, Any]) -> dict[str, Any]:
    g_score = payload.get("g_score") if isinstance(payload.get("g_score"), Mapping) else {}
    w_score = payload.get("w_score_partial") if isinstance(payload.get("w_score_partial"), Mapping) else {}
    w_summary = w_score.get("summary") if isinstance(w_score.get("summary"), Mapping) else {}
    m2_5 = payload.get("m2_5_recovery") if isinstance(payload.get("m2_5_recovery"), Mapping) else {}
    m2_5_summary = m2_5.get("summary") if isinstance(m2_5.get("summary"), Mapping) else {}
    blockers = []
    if g_score.get("available") is not True:
        blockers.append("g_score_unavailable")
    if int(w_summary.get("verified_outcome_count") or 0) < 2:
        blockers.append("weak_w_verified_coverage")
    if int(m2_5_summary.get("research_scoreable_count") or 0) == 0:
        blockers.append("m2_5_no_recovered_work_product")
    return {
        "status": "partial_evidence_only",
        "advances": [
            "Defines a fixed MVE protocol with at least 3 ACUTs, 4 RBench tasks, and 4 RWork tasks.",
            "Separates research-scoreability from product admission and license claims.",
            "Recovers existing M2.5 work-product evidence without requiring clean-room replay.",
        ],
        "weakens_or_blocks": blockers,
        "nfl_claim_status": "not_established",
        "interpretation": (
            "M3-lite advances measurement readiness and partial R/W inspection, but it does not establish "
            "the NFL ranking-reversal story because G_score is unavailable and W evidence remains limited."
        ),
    }


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    matrix = load_manifest(args.matrix)
    protocol = require_matrix(matrix)
    scorecard_info, scorecard_v1 = load_json_input(args.scorecard_v1, input_key="scorecard_v1")
    m2_5_info, m2_5_payload = load_json_input(args.m2_5_summary, input_key="m2_5_workspace_diff")
    r_cells, r_summary = build_split_cells(
        scorecard_v1=scorecard_v1,
        acuts=protocol["acuts"],
        tasks=protocol["rbench_tasks"],
        source_input="rbench_canonical_matrix",
        split_score="R_score",
    )
    w_cells, w_summary = build_split_cells(
        scorecard_v1=scorecard_v1,
        acuts=protocol["acuts"],
        tasks=protocol["rwork_tasks"],
        source_input="rwork_canonical_matrix",
        split_score="W_score",
    )
    m2_5_recovery = recover_m2_5(m2_5_payload)
    g_score_source = scorecard_v1.get("g_score") if isinstance(scorecard_v1, Mapping) and isinstance(scorecard_v1.get("g_score"), Mapping) else {}
    g_score = {
        "available": g_score_source.get("available") is True,
        "availability_status": g_score_source.get("availability_status") or "unavailable_in_m3_lite",
        "value": None,
        "unavailable_is_not_zero": True,
        "direct_acut_scoring_attempted": bool(g_score_source.get("direct_acut_scoring_attempted") is True),
    }
    score_input_digest = digest_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "matrix": protocol,
            "scorecard_v1_sha256": scorecard_info.get("sha256"),
            "m2_5_sha256": m2_5_info.get("sha256"),
            "r_cells": r_cells,
            "w_cells": w_cells,
            "m2_5_recovery_records": m2_5_recovery["records"],
        }
    )
    payload: dict[str, Any] = {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "status": "completed",
        "generated_at": iso_now(),
        "scope": {
            "mode": "research_grade_minimum_viable_evidence",
            "product_gate": False,
            "clean_room_replay_required_for_research_scoreability": False,
            "license_or_admission_claims_allowed": False,
        },
        "protocol": {
            **protocol,
            "matrix_path": repo_relative(resolve_path(args.matrix)),
            "schema_version": matrix.get("schema_version"),
            "scope_reset": matrix.get("scope_reset"),
            "research_scoreability_protocol": matrix.get("research_scoreability_protocol"),
        },
        "evidence_inputs": {
            "scorecard_v1": scorecard_info,
            "m2_5_workspace_diff": m2_5_info,
        },
        "g_score": g_score,
        "r_score_partial": {
            "cells": r_cells,
            "summary": r_summary,
        },
        "w_score_partial": {
            "cells": w_cells,
            "summary": w_summary,
        },
        "m2_5_recovery": m2_5_recovery,
        "score_table": score_table(protocol["acuts"], r_summary, w_summary, g_score),
        "score_input_set_digest": score_input_digest,
        "claim_boundaries": {
            "does_not_claim_g_score_predictivity": True,
            "does_not_claim_ranking_reversal": True,
            "does_not_claim_task_solving_improvement": True,
            "does_not_claim_capability_uplift": True,
            "does_not_emit_license": True,
            "does_not_emit_admission": True,
            "does_not_emit_authorization": True,
        },
        "reproduction_command": reproduction_command(args),
        "output_paths": {
            "scorecard": repo_relative(resolve_path(args.output)),
            "m2_5_recovery": repo_relative(resolve_path(args.m2_5_output)),
            "report": repo_relative(resolve_path(args.report)),
        },
    }
    payload["story_impact"] = story_impact(payload)
    m2_5_artifact = {
        "tool": TOOL,
        "schema_version": "core-narrative.m3-lite-m2-5-recovery.v1",
        "status": m2_5_recovery["status"],
        "generated_at": payload["generated_at"],
        "source_input": m2_5_info,
        "scope": payload["scope"],
        "recovery": m2_5_recovery,
        "claim_boundaries": payload["claim_boundaries"],
    }
    return payload, m2_5_artifact


def reproduction_command(args: argparse.Namespace) -> str:
    return (
        "PYTHONPATH=experiments/core_narrative/tools python3 "
        "experiments/core_narrative/tools/m3_lite_mve_research_scorecard.py "
        f"--matrix {repo_relative(resolve_path(args.matrix))} "
        f"--scorecard-v1 {repo_relative(resolve_path(args.scorecard_v1))} "
        f"--m2-5-summary {repo_relative(resolve_path(args.m2_5_summary))} "
        f"--output {repo_relative(resolve_path(args.output))} "
        f"--m2-5-output {repo_relative(resolve_path(args.m2_5_output))} "
        f"--report {repo_relative(resolve_path(args.report))}"
    )


def fmt_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{100 * float(value):.1f}%"
    return "n/a"


def fmt_counts(counts: object) -> str:
    if not isinstance(counts, Mapping):
        return "none"
    return ", ".join(f"`{key}`: {value}" for key, value in counts.items() if value) or "none"


def report_markdown(payload: Mapping[str, Any]) -> str:
    protocol = payload.get("protocol") if isinstance(payload.get("protocol"), Mapping) else {}
    r_summary = payload.get("r_score_partial", {}).get("summary") if isinstance(payload.get("r_score_partial"), Mapping) else {}
    w_summary = payload.get("w_score_partial", {}).get("summary") if isinstance(payload.get("w_score_partial"), Mapping) else {}
    m2_5 = payload.get("m2_5_recovery", {}).get("summary") if isinstance(payload.get("m2_5_recovery"), Mapping) else {}
    g_score = payload.get("g_score") if isinstance(payload.get("g_score"), Mapping) else {}
    story = payload.get("story_impact") if isinstance(payload.get("story_impact"), Mapping) else {}
    rows = payload.get("score_table") if isinstance(payload.get("score_table"), list) else []
    table_lines = [
        "| ACUT | G | R fixed pass | W fixed pass | R verified n | W verified n |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        table_lines.append(
            "| {acut} | {g} | {r} | {w} | {rn} | {wn} |".format(
                acut=row.get("acut_id"),
                g="n/a",
                r=fmt_rate(row.get("r_score_partial_fixed_denominator")),
                w=fmt_rate(row.get("w_score_partial_fixed_denominator")),
                rn=row.get("r_verified_outcome_count"),
                wn=row.get("w_verified_outcome_count"),
            )
        )
    return f"""# M3-lite Minimum Viable Evidence

Date: 2026-05-11

## Scope Reset

M3-lite is research-grade minimum viable evidence, not a product gate. Clean-room replay is recorded when available but is not required for research-scoreability. This artifact does not issue or imply license, admission, authorization, capability-uplift, ranking-reversal, or G_score-predictivity claims.

Protocol: `{protocol.get("matrix_path")}`. Matrix: `{len(protocol.get("acuts", []))}` ACUTs, `{len(protocol.get("rbench_tasks", []))}` RBench tasks, `{len(protocol.get("rwork_tasks", []))}` RWork tasks.

Score input set digest: `{payload.get("score_input_set_digest")}`

## Partial G/R/W

G_score availability: `{g_score.get("availability_status")}`. Unavailable G_score is reported as `None`, not zero.

{chr(10).join(table_lines)}

R outcomes: {fmt_counts(r_summary.get("outcome_counts"))}. Fixed-denominator pass rate: `{r_summary.get("fixed_denominator_pass_rate")}`.

W outcomes: {fmt_counts(w_summary.get("outcome_counts"))}. Fixed-denominator pass rate: `{w_summary.get("fixed_denominator_pass_rate")}`.

## M2.5 Recovery

Recovered M2.5 records: `{m2_5.get("total")}`. Research-scoreable records: `{m2_5.get("research_scoreable_count")}`. Persisted patches: `{m2_5.get("persisted_patch_count")}`. Final workspace diffs: `{m2_5.get("final_workspace_diff_count")}`. Outcome counts: {fmt_counts(m2_5.get("outcome_counts"))}.

These M2.5 records are work-product evidence. They are not blended into verified W_score unless verifier or review evidence supports that stronger conclusion.

## Story Impact

Status: `{story.get("nfl_claim_status")}`.

{story.get("interpretation")}

## Limitations

- G_score is unavailable in this MVE, so no G/R/W ranking reversal can be claimed.
- The W slice is small and contains invalid-submission/output-contract failures that remain visible in the denominator.
- M2.5 recovery can show persisted patches or final workspace diffs, but replay-invalid records remain weaker than verified passes or blinded review.
- Existing artifacts include historical runner limitations; this report separates measurement recovery from task capability.

## Reproduction

```bash
{payload.get("reproduction_command")}
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = resolve_path(str(path))
    if out is None:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload, m2_5_artifact = build_payload(args)
        write_json(args.m2_5_output, m2_5_artifact)
        if args.report:
            write_report(args.report, payload)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
