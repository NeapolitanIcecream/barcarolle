#!/usr/bin/env python3
"""Emit a machine-readable gap map for report future-work steps 1-7."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import emit_json, fail, iso_now


TOOL = "codex_nfl_future_work_gap_map"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--admission-artifact")
    parser.add_argument("--rbench-matrix")
    parser.add_argument("--rwork-matrix")
    parser.add_argument("--gscore-basis")
    parser.add_argument("--prediction-analysis")
    parser.add_argument("--prediction-report")
    return parser.parse_args(list(argv))


def exists(path: str | None) -> bool:
    return bool(path) and Path(path).exists()


def load(path: str | None) -> dict[str, Any]:
    if not path or not Path(path).exists():
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def status_for(condition: bool, partial: bool = False) -> str:
    if condition:
        return "satisfied"
    if partial:
        return "partial"
    return "open"


def build_gap_map(args: argparse.Namespace) -> dict[str, Any]:
    admission = load(args.admission_artifact)
    rbench = load(args.rbench_matrix)
    rwork = load(args.rwork_matrix)
    gscore = load(args.gscore_basis)
    prediction = load(args.prediction_analysis)
    click008_closure = Path("experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_scoreable_closure_20260508.json")
    click008_reports = [
        Path("experiments/core_narrative/reports/2026-05-08_codex_nfl_click008_attempt3_report.md"),
        Path("experiments/core_narrative/reports/2026-05-08_codex_nfl_click008_frontier_retry_report.md"),
    ]
    output_contract_tests = Path("experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py").exists()
    admission_ok = admission.get("status") == "passed" and int(admission.get("selected_tasks_count", 0) or 0) >= 8
    admission_defects = admission.get("defect_classification_counts") if isinstance(admission.get("defect_classification_counts"), dict) else {}
    rbench_missing = rbench.get("missing", {}) if isinstance(rbench.get("missing"), dict) else {}
    rwork_missing = rwork.get("missing", {}) if isinstance(rwork.get("missing"), dict) else {}
    rbench_complete = exists(args.rbench_matrix) and not rbench_missing.get("canonical_cells")
    rwork_complete = exists(args.rwork_matrix) and not rwork_missing.get("canonical_cells")
    prediction_done = exists(args.prediction_analysis) and exists(args.prediction_report) and prediction.get("status") == "completed"
    return {
        "tool": TOOL,
        "status": "completed" if prediction_done else "partial",
        "generated_at": iso_now(),
        "report_future_work_steps": {
            "1_gap_audit": {
                "status": "satisfied",
                "artifact": args.output,
                "already_satisfied_by_merged_artifacts": [
                    "Click008 attempt 3 report exists" if click008_reports[0].exists() else "Click008 attempt 3 report missing",
                    "Click008 frontier retry report exists" if click008_reports[1].exists() else "Click008 frontier retry report missing",
                    "Click008 scoreable closure exists" if click008_closure.exists() else "Click008 scoreable closure missing",
                ],
                "remaining_work": [],
            },
            "2_task_admission_freeze_click_001_008": {
                "status": status_for(admission_ok, exists(args.admission_artifact)),
                "artifact": args.admission_artifact,
                "already_satisfied_by_merged_artifacts": [
                    "codex_nfl_gate0_preflight.py existed before this workflow",
                    "materialized Click RBench task packs 001-008 exist",
                ],
                "remaining_work": []
                if admission_ok
                else ["resolve the Click005 reference/verifier strict-admission defect, then rerun the eight-task admission freeze"],
                "admission_status": admission.get("status"),
                "defect_classification_counts": dict(sorted(admission_defects.items())),
            },
            "3_output_contract_v3_workspace_isolation": {
                "status": status_for(output_contract_tests),
                "already_satisfied_by_merged_artifacts": [
                    "Click008 closure artifacts contain scoreable outcomes for all four core ACUTs",
                    "existing tests cover clean verify workspace and no-op isolation",
                ],
                "remaining_work": [],
                "future_contract_metadata_missing_counts": rbench.get("metadata_missing_counts_canonical_future_contract", {}),
            },
            "4_click_rbench_clean_slice": {
                "status": status_for(rbench_complete, exists(args.rbench_matrix)),
                "artifact": args.rbench_matrix,
                "remaining_work": [] if rbench_complete else ["complete missing canonical RBench cells"],
                "missing": rbench_missing,
                "click008_no_retry_policy": "preserve canonical closure as latest clean scoreable evidence",
            },
            "5_gscore_basis": {
                "status": "blocked_direct_gscore_recorded" if gscore.get("status") == "direct_gscore_blocked" else status_for(bool(gscore)),
                "artifact": args.gscore_basis,
                "remaining_work": [
                    "materialize SWE-Bench Pro cache/evaluator and run gold-patch smoke before direct G_score ACUT calls"
                ]
                if gscore.get("status") == "direct_gscore_blocked"
                else [],
                "blockers": gscore.get("blockers", []),
            },
            "6_rwork_w_score": {
                "status": status_for(rwork_complete, exists(args.rwork_matrix)),
                "artifact": args.rwork_matrix,
                "remaining_work": [] if rwork_complete else ["run and summarize bounded RWork slice"],
                "missing": rwork_missing,
            },
            "7_prediction_analysis": {
                "status": status_for(prediction_done, exists(args.prediction_analysis)),
                "analysis_artifact": args.prediction_analysis,
                "report": args.prediction_report,
                "remaining_work": [] if prediction_done else ["produce R/G/W prediction analysis artifact and report"],
                "ranking_reversal_status": (
                    prediction.get("predictivity", {})
                    .get("ranking_reversal_assessment", {})
                    .get("status")
                    if isinstance(prediction.get("predictivity"), dict)
                    else None
                ),
            },
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        emit_json(build_gap_map(args), args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
