#!/usr/bin/env python3
"""Run one Rich W* replacement-oracle admission smoke pilot for a rejected direct candidate."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_batch import DEFAULT_OUTPUT as DEFAULT_DIRECT_BATCH, direct_w_star_candidates
from rich_direct_smoke_pilot import (
    DEFAULT_REPO,
    admission_decision,
    patch_for_candidate,
    problem_statement,
    repo_relative,
    run_noop_smoke,
    run_reference_smoke,
    sha256_text,
    source_anchor_digest,
)
from rich_source_oracle_pilot import hidden_verifier_digest, materialize_task_pack
from rich_source_oracle_queue import load_direct_batch
from rich_task_admission_readiness import changed_file_set_digest


TOOL = "rich_replacement_oracle_pilot"
SCHEMA_VERSION = "core-narrative.rich-replacement-oracle-pilot.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_replacement_oracle_pilot_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_replacement_oracle_pilot.md"


SPLIT_GRAPHEMES_TIMEOUT_TEST = '''\
from __future__ import annotations

import signal

from rich.cells import split_graphemes


def _timeout(_signum: int, _frame: object) -> None:
    raise AssertionError("split_graphemes did not return for a leading zero-width character")


def test_split_graphemes_returns_for_leading_zero_width_character() -> None:
    """Leading zero-width characters should not hang split_graphemes."""
    previous_handler = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(1)
    try:
        spans, width = split_graphemes("\\u0301")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert spans == []
    assert width == 0
'''

SPLIT_GRAPHEMES_ZERO_WIDTH_SPAN_TEST = '''\
from __future__ import annotations

from rich.cells import split_graphemes


def test_split_graphemes_covers_leading_zero_width_character() -> None:
    """Leading zero-width characters should produce a zero-width span."""
    spans, width = split_graphemes("\\u0301")

    assert spans == [(0, 1, 0)]
    assert width == 0
'''


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--direct-batch", default=str(DEFAULT_DIRECT_BATCH), help="Public direct-smoke batch JSON.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    parser.add_argument("--batch-candidate-index", type=int, default=8, help="One-based direct-smoke batch candidate index.")
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default="python3")
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def direct_batch_result(direct_batch: Mapping[str, Any], batch_candidate_index: int) -> Mapping[str, Any]:
    results = direct_batch.get("results")
    if not isinstance(results, list):
        raise ToolError("direct-smoke batch result has no candidate results")
    for result in results:
        if isinstance(result, Mapping) and result.get("batch_candidate_index") == batch_candidate_index:
            if result.get("admission_decision") == "accepted":
                raise ToolError("direct candidate was already accepted", batch_candidate_index=batch_candidate_index)
            return result
    raise ToolError("direct-smoke batch candidate was not found", batch_candidate_index=batch_candidate_index)


def select_candidate(repo_path: Path, direct_batch: Mapping[str, Any], batch_candidate_index: int) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if batch_candidate_index <= 0:
        raise ToolError("batch candidate index must be one-based", batch_candidate_index=batch_candidate_index)
    candidates = direct_w_star_candidates(repo_path)
    if batch_candidate_index > len(candidates):
        raise ToolError(
            "batch candidate index is out of range",
            batch_candidate_index=batch_candidate_index,
            candidate_count=len(candidates),
        )
    result = direct_batch_result(direct_batch, batch_candidate_index)
    return candidates[batch_candidate_index - 1], result


def hidden_verifier_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    subject = str(candidate.get("subject", "")).strip().lower()
    source_files = set(str(path) for path in candidate.get("source_files", []))
    if subject == "fix for infinite loop in split_graphemes" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_split_graphemes_timeout.py",
                    "content": SPLIT_GRAPHEMES_TIMEOUT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_split_graphemes_timeout.py",
            "test_node_count": 1,
            "oracle_template": "split_graphemes_leading_zero_width_timeout",
        }
    if subject == "test cases" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_split_graphemes_zero_width_span.py",
                    "content": SPLIT_GRAPHEMES_ZERO_WIDTH_SPAN_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_split_graphemes_zero_width_span.py",
            "test_node_count": 1,
            "oracle_template": "split_graphemes_leading_zero_width_span",
        }
    raise ToolError(
        "no replacement-oracle template is available for selected candidate",
        subject_digest=sha256_text(str(candidate.get("subject", ""))),
        source_file_set_digest=changed_file_set_digest([str(path) for path in candidate.get("source_files", [])]),
    )


def public_result(
    *,
    candidate: Mapping[str, Any],
    direct_result: Mapping[str, Any],
    verifier: Mapping[str, Any],
    reference_patch_digest: str,
    reference_patch_bytes: int,
    noop: Mapping[str, Any],
    reference: Mapping[str, Any],
    private_root: str,
) -> dict[str, Any]:
    decision = admission_decision(str(noop.get("status")), str(reference.get("status")))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": "W_star",
        "pilot_scope": "one_rejected_direct_candidate_replacement_oracle",
        "batch_candidate_index": direct_result.get("batch_candidate_index"),
        "prior_no_op_status": direct_result.get("no_op_result", {}).get("status")
        if isinstance(direct_result.get("no_op_result"), Mapping)
        else None,
        "prior_reference_status": direct_result.get("reference_result", {}).get("status")
        if isinstance(direct_result.get("reference_result"), Mapping)
        else None,
        "oracle_template": verifier.get("oracle_template"),
        "source_anchor_digest": source_anchor_digest(str(candidate["commit"])),
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": sha256_text(str(candidate["subject"])),
        "family": candidate["family"],
        "surface": candidate["surface"],
        "source_file_count": candidate["source_file_count"],
        "test_file_count": candidate["test_file_count"],
        "test_node_count": verifier.get("test_node_count"),
        "changed_file_set_digest": candidate.get("changed_file_set_digest")
        or changed_file_set_digest(list(candidate.get("source_files", [])) + list(candidate.get("test_files", []))),
        "statement_digest": sha256_text(problem_statement(str(candidate["subject"]))),
        "hidden_verifier_digest": hidden_verifier_digest(verifier),
        "reference_patch_digest": reference_patch_digest,
        "reference_patch_bytes": reference_patch_bytes,
        "no_op_result": {
            "status": noop.get("status"),
            "verifier_exit_code": noop.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "reference_result": {
            "status": reference.get("status"),
            "verifier_exit_code": reference.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "admission_decision": decision,
        "primary_runs_authorized": False,
        "private_artifact_root": private_root,
        "claim_boundary": [
            "This is a one-candidate replacement-oracle smoke pilot, not a frozen Rich denominator.",
            "Raw source commits, raw subjects, reference patches, and hidden verifier files are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich Replacement-Oracle Pilot",
            "",
            f"Status: `{payload.get('status')}`",
            f"Generated at: `{payload.get('generated_at')}`",
            "",
            "## Result",
            "",
            f"- Admission decision: `{payload.get('admission_decision')}`",
            f"- Prior no-op status: `{payload.get('prior_no_op_status')}`",
            f"- Replacement no-op status: `{payload.get('no_op_result', {}).get('status') if isinstance(payload.get('no_op_result'), Mapping) else None}`",
            f"- Replacement reference status: `{payload.get('reference_result', {}).get('status') if isinstance(payload.get('reference_result'), Mapping) else None}`",
            f"- Oracle template: `{payload.get('oracle_template')}`",
            f"- Family: `{payload.get('family')}`",
            "",
            "Primary R/W* model attempts remain unauthorized. This pilot checks one rejected direct Rich W* candidate only.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_path = Path(args.repo).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        import shutil

        shutil.rmtree(private_root, ignore_errors=True)
    private_root.mkdir(parents=True, exist_ok=True)
    direct_batch = load_direct_batch(Path(args.direct_batch).resolve())
    candidate, direct_result = select_candidate(repo_path, direct_batch, args.batch_candidate_index)
    verifier = hidden_verifier_for_candidate(candidate)
    task_pack = materialize_task_pack(
        candidate,
        verifier,
        private_root / "candidate_task_pack",
        task_id=f"rich__wstar_replacement_oracle__{args.batch_candidate_index:03d}",
    )
    task_path = Path(task_pack["task_path"])
    reference_patch = patch_for_candidate(repo_path, candidate)
    reference_digest = sha256_text(reference_patch)
    noop = run_noop_smoke(
        task_path,
        repo_path,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    reference = run_reference_smoke(
        task_path,
        repo_path,
        candidate,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    payload = public_result(
        candidate=candidate,
        direct_result=direct_result,
        verifier=verifier,
        reference_patch_digest=reference_digest,
        reference_patch_bytes=len(reference_patch.encode("utf-8")),
        noop=noop,
        reference=reference,
        private_root=repo_relative(private_root),
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
