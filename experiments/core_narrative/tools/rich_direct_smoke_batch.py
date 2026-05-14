#!/usr/bin/env python3
"""Run direct-oracle admission smoke for Rich candidates with existing tests."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_pilot import (
    DEFAULT_REPO,
    hidden_verifier_digest,
    materialize_task_pack,
    patch_for_candidate,
    public_result,
    repo_relative,
    run_noop_smoke,
    run_reference_smoke,
    sha256_text,
)
from rich_task_admission_readiness import discover_candidates


TOOL = "rich_direct_smoke_batch"
SCHEMA_VERSION = "core-narrative.rich-direct-smoke-batch.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_direct_smoke_batch_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_direct_smoke_batch_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_direct_smoke_batch.md"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    parser.add_argument("--split", choices=["C", "R", "W_star"], default="W_star", help="Time split to smoke.")
    parser.add_argument("--candidate-limit", type=int, help="Limit number of direct candidates to smoke.")
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default=sys.executable)
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def direct_candidates(repo_path: Path, split: str = "W_star") -> list[Mapping[str, Any]]:
    return [
        candidate
        for candidate in discover_candidates(repo_path)
        if candidate.get("window") == split and candidate.get("direct_smoke_ready")
    ]


def direct_w_star_candidates(repo_path: Path) -> list[Mapping[str, Any]]:
    return direct_candidates(repo_path, "W_star")


def summarize_results(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    decisions = Counter(str(result.get("admission_decision")) for result in results)
    noop_statuses = Counter(
        str(result.get("no_op_result", {}).get("status")) for result in results if isinstance(result.get("no_op_result"), Mapping)
    )
    reference_statuses = Counter(
        str(result.get("reference_result", {}).get("status")) for result in results if isinstance(result.get("reference_result"), Mapping)
    )
    blocked = sum(
        1
        for result in results
        if (
            isinstance(result.get("no_op_result"), Mapping)
            and str(result["no_op_result"].get("status", "")).startswith("blocked")
        )
        or (
            isinstance(result.get("reference_result"), Mapping)
            and str(result["reference_result"].get("status", "")).startswith("blocked")
        )
    )
    return {
        "smoked_candidate_count": len(results),
        "accepted_count": decisions.get("accepted", 0),
        "rejected_count": decisions.get("rejected", 0),
        "blocked_count": blocked,
        "admission_decision_counts": dict(sorted(decisions.items())),
        "noop_status_counts": dict(sorted(noop_statuses.items())),
        "reference_status_counts": dict(sorted(reference_statuses.items())),
    }


def public_summary(*, results: Sequence[Mapping[str, Any]], private_root: str, split: str = "W_star") -> dict[str, Any]:
    summary = summarize_results(results)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": split,
        "batch_scope": "all_current_direct_oracle_candidates",
        "private_artifact_root": private_root,
        "primary_runs_authorized": False,
        **summary,
        "results": list(results),
        "claim_boundary": [
            "This direct-smoke batch is not a frozen Rich denominator.",
            "Only candidates with source changes, test changes, and extractable pytest nodes are smoked.",
            "Source-only candidates still require Golden-Oracle verifier construction.",
            "Raw commits, reference patches, and hidden verifier files are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def smoke_candidate(
    *,
    repo_path: Path,
    candidate: Mapping[str, Any],
    index: int,
    private_root: Path,
    install_timeout: int,
    verifier_timeout: int,
    venv_python: str,
    split: str = "W_star",
) -> Mapping[str, Any]:
    candidate_root = private_root / f"candidate_{index:03d}"
    split_slug = split.lower().replace("_", "")
    task_pack = materialize_task_pack(
        candidate,
        candidate_root / "candidate_task_pack",
        repo_path,
        task_id=f"rich__{split_slug}_direct_batch__{index:03d}",
        split=split,
    )
    task_path = Path(task_pack["task_path"])
    hidden_digest = hidden_verifier_digest(repo_path, candidate)
    reference_patch = patch_for_candidate(repo_path, candidate)
    noop = run_noop_smoke(
        task_path,
        repo_path,
        candidate_root,
        install_timeout,
        verifier_timeout,
        venv_python,
    )
    reference = run_reference_smoke(
        task_path,
        repo_path,
        candidate,
        candidate_root,
        install_timeout,
        verifier_timeout,
        venv_python,
    )
    result = public_result(
        candidate=candidate,
        hidden_verifier_digest=hidden_digest,
        reference_patch_digest=sha256_text(reference_patch),
        reference_patch_bytes=len(reference_patch.encode("utf-8")),
        noop=noop,
        reference=reference,
        private_root=repo_relative(candidate_root),
        split=split,
    )
    result["batch_candidate_index"] = index
    result["pilot_scope"] = "direct_oracle_batch_candidate"
    return result


def render_report(payload: Mapping[str, Any]) -> str:
    split = payload.get("split", "W_star")
    lines = [
        "# Rich Direct-Smoke Batch",
        "",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Result",
        "",
        f"- Split: `{split}`",
        f"- Smoked candidates: `{payload.get('smoked_candidate_count')}`",
        f"- Accepted: `{payload.get('accepted_count')}`",
        f"- Rejected: `{payload.get('rejected_count')}`",
        f"- Blocked: `{payload.get('blocked_count')}`",
        f"- No-op statuses: `{json.dumps(payload.get('noop_status_counts', {}), sort_keys=True)}`",
        f"- Reference statuses: `{json.dumps(payload.get('reference_status_counts', {}), sort_keys=True)}`",
        "",
        "## Boundary",
        "",
        "This is direct-smoke admission progress only. It is not a frozen Rich denominator and does not authorize primary ACUT runs.",
        "",
    ]
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_path = Path(args.repo).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        shutil.rmtree(private_root, ignore_errors=True)
    private_root.mkdir(parents=True, exist_ok=True)
    candidates = direct_candidates(repo_path, args.split)
    if args.candidate_limit is not None:
        if args.candidate_limit < 0:
            raise ToolError("--candidate-limit must be non-negative")
        candidates = candidates[: args.candidate_limit]
    if not candidates:
        raise ToolError("no Rich direct-smoke candidates found", split=args.split)
    results = [
        smoke_candidate(
            repo_path=repo_path,
            candidate=candidate,
            index=index,
            private_root=private_root,
            install_timeout=args.install_timeout_seconds,
            verifier_timeout=args.verifier_timeout_seconds,
            venv_python=args.venv_python,
            split=args.split,
        )
        for index, candidate in enumerate(candidates, start=1)
    ]
    payload = public_summary(results=results, private_root=repo_relative(private_root), split=args.split)
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
