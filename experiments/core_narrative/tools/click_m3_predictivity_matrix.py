#!/usr/bin/env python3
"""Gate Click M3 predictivity work on existing M2 scoreability evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now


TOOL = "click_m3_predictivity_matrix"
SCHEMA_VERSION = "core-narrative.click-m3-predictivity-matrix.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-09_click_m3_predictivity_matrix_gate_report.md"
DEFAULT_OUTPUT = DEFAULT_RESULTS_ROOT / "click_m3_predictivity_matrix_gate_20260509.json"

DEFAULT_INPUTS = {
    "m2_scoreability_summary": "m2_scoreability_summary_20260509.json",
    "scorecard_v0": "scorecard_v0_existing_matrices_20260509.json",
    "rbench_canonical_matrix": "codex_nfl_rbench_canonical_matrix_20260508.json",
    "rwork_canonical_matrix": "codex_nfl_rwork_canonical_matrix_20260508.json",
    "step7_predictivity_analysis": "codex_nfl_predictivity_analysis_20260508.json",
}

LIVE_GATE_PASS_CLAIM = "scoreability_gate_passed"
NO_MODEL_PATH_REASON = "no-model paths are instrumentation baselines, not live scoreability gates"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--m2-summary")
    parser.add_argument("--scorecard")
    parser.add_argument("--rbench-matrix")
    parser.add_argument("--rwork-matrix")
    parser.add_argument("--step7-predictivity")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv))


def default_input_paths(results_root: str | Path = DEFAULT_RESULTS_ROOT) -> dict[str, Path]:
    root = Path(results_root)
    return {key: root / filename for key, filename in DEFAULT_INPUTS.items()}


def input_paths_from_args(args: argparse.Namespace) -> dict[str, Path]:
    paths = default_input_paths(args.results_root)
    overrides = {
        "m2_scoreability_summary": args.m2_summary,
        "scorecard_v0": args.scorecard,
        "rbench_canonical_matrix": args.rbench_matrix,
        "rwork_canonical_matrix": args.rwork_matrix,
        "step7_predictivity_analysis": args.step7_predictivity,
    }
    for key, value in overrides.items():
        if value:
            paths[key] = Path(value)
    return paths


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_input(key: str, path: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    info: dict[str, Any] = {
        "path": str(path),
        "present": False,
        "status": "missing_input",
        "required_for_gate": key in {"m2_scoreability_summary", "scorecard_v0"},
    }
    if not path.exists():
        return info, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        info["status"] = "invalid_json"
        info["error"] = str(exc)
        return info, None
    except OSError as exc:
        info["status"] = "read_error"
        info["error"] = str(exc)
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


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def as_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return 0


def path_gate_status(path_summary: Mapping[str, Any]) -> str:
    gate = as_mapping(path_summary.get("gate"))
    status = gate.get("status", path_summary.get("gate_status"))
    return str(status) if isinstance(status, str) and status else "unknown"


def model_call_counts(path_summary: Mapping[str, Any]) -> dict[str, int]:
    counts = as_mapping(path_summary.get("model_call_made_counts"))
    return {
        "true": as_count(counts.get("true")),
        "false": as_count(counts.get("false")),
        "unknown": as_count(counts.get("unknown")),
    }


def is_live_path(path_summary: Mapping[str, Any]) -> bool:
    return model_call_counts(path_summary)["true"] > 0


def is_no_model_path(path_summary: Mapping[str, Any]) -> bool:
    counts = model_call_counts(path_summary)
    return counts["true"] == 0 and counts["false"] > 0


def compact_path_summary(path_id: str, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path_id": path_id,
        "contract": summary.get("contract"),
        "kind": summary.get("kind"),
        "total": summary.get("total"),
        "status_counts": as_mapping(summary.get("status_counts")),
        "patch_ready_coverage": summary.get("patch_ready_coverage"),
        "invalid_submission_rate": summary.get("invalid_submission_rate"),
        "clean_replay_disagreement_count": summary.get("clean_replay_disagreement_count"),
        "missing_cell_count": summary.get("missing_cell_count"),
        "blocked_cell_count": summary.get("blocked_cell_count"),
        "model_call_made_counts": model_call_counts(summary),
        "gate_status": path_gate_status(summary),
        "gate_checks": as_mapping(as_mapping(summary.get("gate")).get("checks") or summary.get("gate_checks")),
        "gate_thresholds": as_mapping(as_mapping(summary.get("gate")).get("thresholds") or summary.get("gate_thresholds")),
        "live_model_path": is_live_path(summary),
        "no_model_baseline": is_no_model_path(summary),
    }


def m2_paths(m2_payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    paths: dict[str, dict[str, Any]] = {}
    evidence_inputs = as_mapping(m2_payload.get("evidence_inputs"))
    for path_id, raw_summary in as_mapping(m2_payload.get("paths")).items():
        if not isinstance(path_id, str) or not isinstance(raw_summary, Mapping):
            continue
        summary = dict(raw_summary)
        input_info = as_mapping(evidence_inputs.get(path_id))
        if "contract" not in summary and input_info.get("contract") is not None:
            summary["contract"] = input_info.get("contract")
        if "kind" not in summary and input_info.get("kind") is not None:
            summary["kind"] = input_info.get("kind")
        paths[path_id] = compact_path_summary(path_id, summary)
    return paths


def live_gate(m2_payload: Mapping[str, Any] | None, input_info: Mapping[str, Any]) -> dict[str, Any]:
    if not input_info.get("present") or not isinstance(m2_payload, Mapping):
        return {
            "status": "blocked",
            "claim_status": None,
            "live_gate_passed": False,
            "blockers": [{"blocker": "m2_scoreability_summary_missing"}],
            "paths": {},
            "live_paths": [],
            "no_model_paths": [],
        }

    paths = m2_paths(m2_payload)
    live_paths = [path for path in paths.values() if path["live_model_path"]]
    no_model_paths = [path for path in paths.values() if path["no_model_baseline"]]
    passed_live_paths = [path for path in live_paths if path["gate_status"] == "passed"]
    failed_live_paths = [path for path in live_paths if path["gate_status"] != "passed"]
    claim_status = m2_payload.get("claim_status")
    blockers: list[dict[str, Any]] = []

    if claim_status != LIVE_GATE_PASS_CLAIM:
        blockers.append(
            {
                "blocker": "m2_claim_status_not_passed",
                "observed_claim_status": claim_status,
                "required_claim_status": LIVE_GATE_PASS_CLAIM,
            }
        )
    if not live_paths:
        blockers.append({"blocker": "m2_live_model_path_missing"})
    for path in failed_live_paths:
        blockers.append(
            {
                "blocker": "m2_live_path_gate_not_passed",
                "path_id": path["path_id"],
                "gate_status": path["gate_status"],
                "patch_ready_coverage": path["patch_ready_coverage"],
                "invalid_submission_rate": path["invalid_submission_rate"],
                "clean_replay_disagreement_count": path["clean_replay_disagreement_count"],
            }
        )
    for path in no_model_paths:
        if path["gate_status"] == "passed":
            blockers.append(
                {
                    "blocker": "no_model_path_not_sufficient_for_m3",
                    "path_id": path["path_id"],
                    "reason": NO_MODEL_PATH_REASON,
                }
            )

    gate_passed = (
        claim_status == LIVE_GATE_PASS_CLAIM
        and bool(live_paths)
        and bool(passed_live_paths)
        and not failed_live_paths
    )
    return {
        "status": "passed" if gate_passed else "blocked",
        "claim_status": claim_status,
        "live_gate_passed": gate_passed,
        "required_policy": (
            "M3 live predictivity work requires the M2 summary claim_status to pass and every "
            "live model path in the M2 summary to have gate_status passed. No-model baselines "
            "do not satisfy the live gate."
        ),
        "paths": paths,
        "live_paths": [path["path_id"] for path in live_paths],
        "live_gate_passed_paths": [path["path_id"] for path in passed_live_paths],
        "live_gate_failed_paths": [path["path_id"] for path in failed_live_paths],
        "no_model_paths": [path["path_id"] for path in no_model_paths],
        "blockers": blockers,
    }


def matrix_denominator_from_matrix(matrix: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(matrix, Mapping):
        return {"present": False}
    shape = as_mapping(matrix.get("matrix_shape"))
    by_acut = as_mapping(matrix.get("by_acut"))
    return {
        "present": True,
        "split": matrix.get("split"),
        "expected_cells": shape.get("expected_cells"),
        "acut_count": shape.get("acuts"),
        "task_count": shape.get("tasks"),
        "canonical_missing": len(as_mapping(matrix.get("missing")).get("canonical_cells", []))
        if isinstance(as_mapping(matrix.get("missing")).get("canonical_cells"), list)
        else None,
        "status_counts_canonical": as_mapping(matrix.get("status_counts_canonical")),
        "failure_label_counts_canonical": as_mapping(matrix.get("failure_label_counts_canonical")),
        "metadata_missing_counts_canonical_future_contract": as_mapping(
            matrix.get("metadata_missing_counts_canonical_future_contract")
        ),
        "by_acut": {
            str(acut): {
                "passed": summary.get("passed"),
                "fixed_denominator": summary.get("fixed_denominator"),
                "score_percent_fixed_denominator": summary.get("score_percent_fixed_denominator"),
                "canonical_present": summary.get("canonical_present"),
                "canonical_missing": summary.get("canonical_missing"),
                "scoreable": summary.get("scoreable"),
                "status_counts": as_mapping(summary.get("status_counts")),
            }
            for acut, summary in by_acut.items()
            if isinstance(summary, Mapping)
        },
    }


def scorecard_denominators(scorecard: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(scorecard, Mapping):
        return {"present": False}
    fixed = as_mapping(scorecard.get("fixed_denominators"))
    return {
        "present": True,
        "canonical_matrices": as_mapping(fixed.get("canonical_matrices")),
        "m2_scoreability": as_mapping(fixed.get("m2_scoreability")),
        "g_score_basis": as_mapping(fixed.get("g_score_basis")),
    }


def gscore_availability(scorecard: Mapping[str, Any] | None, predictivity: Mapping[str, Any] | None) -> dict[str, Any]:
    scorecard_g = as_mapping(scorecard.get("g_score")) if isinstance(scorecard, Mapping) else {}
    predictivity_g = as_mapping(predictivity.get("g_score")) if isinstance(predictivity, Mapping) else {}
    direct_available = (
        scorecard_g.get("available") is True
        and scorecard_g.get("direct_acut_scoring_attempted") is True
        and scorecard_g.get("public_leaderboard_proxy_used") is not True
    )
    return {
        "status": "available_direct_acut_scoring_present" if direct_available else "unavailable_direct_acut_scoring_required",
        "direct_acut_scoring_available": direct_available,
        "scorecard_availability_status": scorecard_g.get("availability_status"),
        "scorecard_blocked": scorecard_g.get("blocked"),
        "public_leaderboard_proxy_used": scorecard_g.get("public_leaderboard_proxy_used") is True,
        "prior_step7_direct_gscore_used": predictivity_g.get("direct_gscore_used") is True,
        "blocker_counts": as_mapping(scorecard_g.get("blocker_counts")),
    }


def prior_predictivity_snapshot(predictivity: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(predictivity, Mapping):
        return {"present": False}
    predictivity_section = as_mapping(predictivity.get("predictivity"))
    return {
        "present": True,
        "status": predictivity.get("status"),
        "r_score_vs_w_score_error_status": as_mapping(
            predictivity_section.get("r_score_vs_w_score_error")
        ).get("status"),
        "g_score_vs_w_score_error_status": as_mapping(
            predictivity_section.get("g_score_vs_w_score_error")
        ).get("status"),
        "ranking_reversal_assessment_status": as_mapping(
            predictivity_section.get("ranking_reversal_assessment")
        ).get("status"),
        "promoted_to_m3": False,
        "reason_not_promoted": "M2 live scoreability gate is evaluated separately before M3 work.",
    }


def claim_boundaries() -> dict[str, Any]:
    return {
        "model_or_api_budget_spent": False,
        "live_m3_experiments_run": False,
        "evidence_consumer_only": True,
        "does_not_claim": [
            "direct general-benchmark ACUT performance without direct scoring",
            "capability uplift",
            "task-solving improvement",
            "ranking reversal",
            "license, admission, or authorization outcome",
        ],
        "prohibited_claims": {
            "capability_uplift": False,
            "task_solving_improvement": False,
            "ranking_reversal": False,
            "g_score_predictivity": False,
            "license_or_admission_or_authorization_output": False,
        },
    }


def build_payload(input_paths: Mapping[str, Path]) -> dict[str, Any]:
    evidence_inputs: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any] | None] = {}
    for key, path in input_paths.items():
        info, payload = load_input(key, path)
        evidence_inputs[key] = info
        payloads[key] = payload

    gate = live_gate(payloads.get("m2_scoreability_summary"), evidence_inputs["m2_scoreability_summary"])
    scorecard = payloads.get("scorecard_v0")
    rbench = payloads.get("rbench_canonical_matrix")
    rwork = payloads.get("rwork_canonical_matrix")
    predictivity = payloads.get("step7_predictivity_analysis")
    boundaries = claim_boundaries()
    blocked = gate["status"] != "passed"

    return {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso_now(),
        "status": "blocked" if blocked else "gate_passed_existing_evidence_bounded",
        "model_or_api_budget_spent": False,
        "input_policy": {
            "mode": "existing_artifacts_only",
            "no_live_model_calls": True,
            "default_inputs": DEFAULT_INPUTS,
        },
        "evidence_inputs": evidence_inputs,
        "m2_live_scoreability_gate": gate,
        "m3_execution": {
            "live_model_or_api_experiments_run": False,
            "live_model_or_api_experiments_allowed": gate["status"] == "passed",
            "decision": "do_not_run_m3_live_experiments" if blocked else "eligible_for_bounded_m3_follow_up",
            "reason": (
                "M2 live scoreability gate is blocked; this artifact records the blocker only."
                if blocked
                else "M2 live scoreability gate passed; this artifact remains a no-model existing-evidence summary."
            ),
        },
        "blockers": gate["blockers"] if blocked else [],
        "fixed_denominators": {
            "scorecard_v0": scorecard_denominators(scorecard),
            "rbench_canonical_matrix": matrix_denominator_from_matrix(rbench),
            "rwork_canonical_matrix": matrix_denominator_from_matrix(rwork),
        },
        "existing_evidence_snapshot": {
            "prior_step7_predictivity": prior_predictivity_snapshot(predictivity),
            "g_score_predictivity": gscore_availability(scorecard, predictivity),
        },
        "claim_boundaries": boundaries,
    }


def fmt_rate(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{100 * float(value):.1f}%"
    return "n/a"


def fmt_counts(value: Any) -> str:
    counts = as_mapping(value)
    if not counts:
        return "none"
    return ", ".join(f"`{key}`: {counts[key]}" for key in sorted(counts))


def report_markdown(payload: Mapping[str, Any]) -> str:
    gate = as_mapping(payload.get("m2_live_scoreability_gate"))
    paths = as_mapping(gate.get("paths"))
    denominators = as_mapping(payload.get("fixed_denominators"))
    scorecard_denoms = as_mapping(as_mapping(denominators.get("scorecard_v0")).get("canonical_matrices"))
    by_split = as_mapping(scorecard_denoms.get("by_split"))
    g_score = as_mapping(as_mapping(payload.get("existing_evidence_snapshot")).get("g_score_predictivity"))

    path_rows: list[str] = []
    for path_id in sorted(paths):
        path = as_mapping(paths[path_id])
        path_rows.append(
            "| "
            + " | ".join(
                [
                    f"`{path_id}`",
                    "live" if path.get("live_model_path") else "no-model" if path.get("no_model_baseline") else "unknown",
                    str(path.get("total")),
                    fmt_counts(path.get("status_counts")),
                    fmt_rate(path.get("patch_ready_coverage")),
                    fmt_rate(path.get("invalid_submission_rate")),
                    f"`{path.get('gate_status')}`",
                ]
            )
            + " |"
        )
    if not path_rows:
        path_rows.append("| none | n/a | 0 | none | n/a | n/a | n/a |")

    denom_rows: list[str] = []
    for split in sorted(by_split):
        denom = as_mapping(by_split.get(split))
        denom_rows.append(
            "| "
            + " | ".join(
                [
                    f"`{split}`",
                    str(denom.get("expected_cells")),
                    str(denom.get("canonical_present")),
                    str(denom.get("canonical_missing")),
                    str(denom.get("scoreable_count")),
                ]
            )
            + " |"
        )
    if not denom_rows:
        denom_rows.append("| none | 0 | 0 | 0 | 0 |")

    blocker_lines = []
    for blocker in payload.get("blockers", []):
        if isinstance(blocker, Mapping):
            details = ", ".join(
                f"{key} `{value}`"
                for key, value in blocker.items()
                if key != "blocker" and isinstance(value, (str, int, float))
            )
            suffix = f" ({details})" if details else ""
            blocker_lines.append(f"- `{blocker.get('blocker')}`{suffix}")
    if not blocker_lines:
        blocker_lines.append("- none")

    return f"""# Click M3 Predictivity Matrix Gate Report

Date: 2026-05-09

## Scope

This is a no-model consumer of existing Click evidence. It inspects M2 scoreability and Scorecard v0 before any M3 predictivity work. No model or provider API call was made by this step.

Machine-readable output:

- `experiments/core_narrative/results/click_m3_predictivity_matrix_gate_20260509.json`

## Gate Decision

M2 live scoreability gate status: `{gate.get("status")}`.  
M2 claim status: `{gate.get("claim_status")}`.  
M3 live experiments run: `{as_mapping(payload.get("m3_execution")).get("live_model_or_api_experiments_run")}`.

Blockers:

{chr(10).join(blocker_lines)}

| M2 path | Kind | Cells | Status counts | Patch-ready | Invalid rate | Gate |
| --- | --- | ---: | --- | ---: | ---: | --- |
{chr(10).join(path_rows)}

The no-model path is an instrumentation baseline and does not satisfy the live scoreability gate for M3.

## Denominators Preserved

| Split | Fixed cells | Canonical present | Canonical missing | Scoreable |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(denom_rows)}

M2 fixed denominator: `{as_mapping(as_mapping(denominators.get("scorecard_v0")).get("m2_scoreability")).get("fixed_denominator")}`.

## G Score

G_score predictivity status: `{g_score.get("status")}`.  
Scorecard availability: `{g_score.get("scorecard_availability_status")}`.  
Public leaderboard proxy used: `{g_score.get("public_leaderboard_proxy_used")}`.

G_score predictivity remains unavailable unless direct ACUT scoring exists. No proxy or zero-fill score is used here.

## Claim Boundary

This artifact records a gate/blocker and denominator snapshot only. It does not assert capability uplift, task-solving improvement, ranking reversal, or any license/admission/authorization outcome.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/click_m3_predictivity_matrix.py \\
  --output experiments/core_narrative/results/click_m3_predictivity_matrix_gate_20260509.json \\
  --report experiments/core_narrative/reports/2026-05-09_click_m3_predictivity_matrix_gate_report.md
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_payload(input_paths_from_args(args))
        if args.report:
            write_report(args.report, payload)
        emit_json(payload, args.output)
        return 0
    except ToolError as exc:
        return fail(TOOL, exc)
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
