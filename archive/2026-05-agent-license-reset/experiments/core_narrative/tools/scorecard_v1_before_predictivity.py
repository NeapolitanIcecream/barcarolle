#!/usr/bin/env python3
"""Build Scorecard v1 before any predictivity or admission claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now
import scorecard_v0_from_existing_matrices as v0


TOOL = "scorecard_v1_before_predictivity"
SCHEMA_VERSION = "core-narrative.scorecard-v1-before-predictivity.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"
DEFAULT_OUTPUT = DEFAULT_RESULTS_ROOT / "scorecard_v1_before_predictivity_20260510.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-10_scorecard_v1_before_predictivity.md"
DEFAULT_M2_5 = DEFAULT_RESULTS_ROOT / "m2_5_workspace_diff_summary_20260510.json"
OUTCOME_CLASSES = (
    "verified_pass",
    "verified_fail",
    "invalid_submission",
    "infra_failed",
    "missing_coverage",
    "policy_invalid",
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--rbench-matrix")
    parser.add_argument("--rwork-matrix")
    parser.add_argument("--m2-summary")
    parser.add_argument("--m2-5-summary", default=str(DEFAULT_M2_5))
    parser.add_argument("--gscore-smoke")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def read_optional_json(path: str | Path | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if path is None:
        return {"path": None, "present": False, "status": "missing_input"}, None
    info, payload = v0.load_input("optional", path)
    return info, payload


def classify_outcome(status: object, *, policy_invalid: bool = False) -> str:
    if policy_invalid:
        return "policy_invalid"
    text = str(status or "missing")
    if text == "passed":
        return "verified_pass"
    if text in {"failed", "timeout"}:
        return "verified_fail"
    if text == "invalid_submission":
        return "invalid_submission"
    if text == "infra_failed":
        return "infra_failed"
    if text in {"blocked", "missing", "missing_replay_input"}:
        return "missing_coverage"
    if text == "policy_invalid":
        return "policy_invalid"
    return "infra_failed"


def empty_counts() -> dict[str, int]:
    return {key: 0 for key in OUTCOME_CLASSES}


def increment(counts: dict[str, int], key: str, amount: int = 1) -> None:
    counts[key] = counts.get(key, 0) + amount


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def canonical_entries_from_matrix(input_key: str, matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    _summary, entries = v0.canonical_matrix_entries(input_key, matrix)
    result: list[dict[str, Any]] = []
    for entry in entries:
        outcome = classify_outcome(entry.get("status"))
        attemptable = outcome in {"verified_pass", "verified_fail"}
        result.append(
            {
                **entry,
                "scorecard_v1_outcome": outcome,
                "verifier_attemptable": attemptable,
                "capability_interpretation_allowed": outcome in {"verified_pass", "verified_fail"},
            }
        )
    return result


def m2_records(payload: Mapping[str, Any] | None, source_input: str) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    records_by_path = payload.get("records") if isinstance(payload.get("records"), Mapping) else {}
    records: list[dict[str, Any]] = []
    for path_id, items in records_by_path.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, Mapping):
                continue
            outcome = classify_outcome(item.get("status"))
            attemptable = bool(item.get("patch_ready")) or outcome in {"verified_pass", "verified_fail"}
            records.append(
                {
                    "source_input": source_input,
                    "path_id": path_id,
                    "contract": item.get("contract"),
                    "acut_id": item.get("acut_id"),
                    "task_id": item.get("task_id"),
                    "run_id": item.get("run_id"),
                    "status": item.get("status"),
                    "scorecard_v1_outcome": outcome,
                    "verifier_attemptable": attemptable,
                    "failure_owner": item.get("failure_owner"),
                    "failure_class": item.get("failure_class"),
                    "capability_interpretation_allowed": outcome in {"verified_pass", "verified_fail"},
                }
            )
    return records


def m2_5_records(payload: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    records = []
    for item in payload.get("results", []):
        if not isinstance(item, Mapping):
            continue
        outcome = classify_outcome(item.get("status"))
        attemptable = bool(item.get("attemptable")) or bool(item.get("patch_ready")) or outcome in {"verified_pass", "verified_fail"}
        records.append(
            {
                "source_input": "m2_5_workspace_diff",
                "path_id": "workspace_diff_v1",
                "contract": item.get("submission_contract") or payload.get("submission_contract"),
                "acut_id": item.get("acut_id"),
                "task_id": item.get("task_id"),
                "run_id": item.get("run_id"),
                "status": item.get("status"),
                "scorecard_v1_outcome": outcome,
                "verifier_attemptable": attemptable,
                "failure_owner": item.get("failure_owner"),
                "failure_class": item.get("failure_class"),
                "candidate_patch_sha256": item.get("candidate_patch_sha256"),
                "capability_interpretation_allowed": outcome in {"verified_pass", "verified_fail"},
            }
        )
    return records


def aggregate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = empty_counts()
    by_source: dict[str, dict[str, int]] = {}
    attemptable = 0
    verified_pass = 0
    verified_total = 0
    for record in records:
        outcome = str(record.get("scorecard_v1_outcome"))
        increment(counts, outcome)
        source = str(record.get("source_input") or "unknown")
        by_source.setdefault(source, empty_counts())
        increment(by_source[source], outcome)
        if record.get("verifier_attemptable") is True:
            attemptable += 1
        if outcome in {"verified_pass", "verified_fail"}:
            verified_total += 1
        if outcome == "verified_pass":
            verified_pass += 1
    total = len(records)
    return {
        "total": total,
        "outcome_counts": {key: counts.get(key, 0) for key in OUTCOME_CLASSES},
        "outcome_counts_by_source": {
            source: {key: source_counts.get(key, 0) for key in OUTCOME_CLASSES}
            for source, source_counts in sorted(by_source.items())
        },
        "attemptable_count": attemptable,
        "attemptability_score": rate(attemptable, total),
        "verified_pass_count": verified_pass,
        "verified_outcome_count": verified_total,
        "verified_correctness_rate": rate(verified_pass, verified_total),
        "fixed_denominator_pass_rate": rate(verified_pass, total),
    }


def input_paths_from_args(args: argparse.Namespace) -> dict[str, Path | None]:
    defaults = v0.default_input_paths(args.results_root)
    return {
        "rbench_canonical_matrix": Path(args.rbench_matrix) if args.rbench_matrix else defaults["rbench_canonical_matrix"],
        "rwork_canonical_matrix": Path(args.rwork_matrix) if args.rwork_matrix else defaults["rwork_canonical_matrix"],
        "m2_scoreability_summary": Path(args.m2_summary) if args.m2_summary else defaults["m2_scoreability_summary"],
        "m2_5_workspace_diff": Path(args.m2_5_summary) if args.m2_5_summary else None,
        "gscore_gold_patch_smoke": Path(args.gscore_smoke) if args.gscore_smoke else defaults["gscore_gold_patch_smoke"],
    }


def build_scorecard(input_paths: Mapping[str, str | Path | None]) -> dict[str, Any]:
    evidence_inputs: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any] | None] = {}
    for key, path in input_paths.items():
        info, payload = read_optional_json(path)
        evidence_inputs[key] = info
        payloads[key] = payload

    records: list[dict[str, Any]] = []
    if isinstance(payloads.get("rbench_canonical_matrix"), Mapping):
        records.extend(canonical_entries_from_matrix("rbench_canonical_matrix", payloads["rbench_canonical_matrix"]))  # type: ignore[arg-type]
    if isinstance(payloads.get("rwork_canonical_matrix"), Mapping):
        records.extend(canonical_entries_from_matrix("rwork_canonical_matrix", payloads["rwork_canonical_matrix"]))  # type: ignore[arg-type]
    records.extend(m2_records(payloads.get("m2_scoreability_summary"), "m2_scoreability_summary"))
    records.extend(m2_5_records(payloads.get("m2_5_workspace_diff")))

    g_score = v0.summarize_gscore(payloads.get("gscore_gold_patch_smoke"), evidence_inputs["gscore_gold_patch_smoke"])
    g_score_v1 = {
        **g_score,
        "g_score_value": None,
        "g_score_unavailable_not_zero": g_score.get("available") is not True,
        "unavailable_is_not_failure_score": True,
    }
    fixed_denominator = {
        "score_input_entries": len(records),
        "canonical_matrix_entries": sum(1 for record in records if str(record.get("source_input")).endswith("canonical_matrix")),
        "m2_scoreability_entries": sum(1 for record in records if record.get("source_input") == "m2_scoreability_summary"),
        "m2_5_workspace_diff_entries": sum(1 for record in records if record.get("source_input") == "m2_5_workspace_diff"),
    }
    score_input_material = {
        "schema_version": SCHEMA_VERSION,
        "evidence_inputs": v0.evidence_digest_material(evidence_inputs),
        "fixed_denominator": fixed_denominator,
        "records": [
            {
                key: record.get(key)
                for key in (
                    "source_input",
                    "path_id",
                    "contract",
                    "acut_id",
                    "task_id",
                    "run_id",
                    "status",
                    "scorecard_v1_outcome",
                    "verifier_attemptable",
                    "failure_owner",
                    "failure_class",
                    "candidate_patch_sha256",
                )
            }
            for record in records
        ],
        "g_score": {
            "available": g_score_v1.get("available"),
            "availability_status": g_score_v1.get("availability_status"),
            "g_score_value": None,
        },
    }
    return {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "scorecard_version": "scorecard_v1_before_predictivity",
        "generated_at": iso_now(),
        "status": "completed",
        "model_or_api_budget_spent": False,
        "input_policy": {
            "mode": "existing_artifacts_only",
            "no_live_model_calls": True,
            "failed_scoreability_cells_are_not_capability_failures": True,
        },
        "trial_policy": {
            "primary_attempts_per_acut_task": 1,
            "canonical_matrix_policy": "consume canonical_latest from existing matrices; do not best-of-N in this scorecard",
            "rerun_policy": "reruns are evidence inputs only when already materialized and explicitly canonicalized",
        },
        "coverage_policy": {
            "fixed_denominator_preserved": True,
            "missing_coverage_preserved": True,
            "infra_failed_not_reinterpreted_as_capability": True,
            "invalid_submission_visible_as_admission_risk": True,
        },
        "evidence_inputs": evidence_inputs,
        "evidence_input_set_digest": digest_payload(v0.evidence_digest_material(evidence_inputs)),
        "score_input_set_digest": digest_payload(score_input_material),
        "fixed_denominator": fixed_denominator,
        "score_input_entries": records,
        "outcomes": aggregate(records),
        "g_score": g_score_v1,
        "claim_boundaries": {
            "pre_predictivity": True,
            "admission_safe": True,
            "does_not_claim_ranking_reversal": True,
            "does_not_claim_g_score_predictivity": True,
            "does_not_emit_license_or_authorization": True,
            "prohibited_claims": {
                "capability_uplift": False,
                "task_solving_improvement": False,
                "ranking_reversal": False,
                "g_score_predictivity": False,
                "license_or_admission_output": False,
            },
        },
    }


def fmt_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{100 * float(value):.1f}%"
    return "n/a"


def fmt_counts(value: object) -> str:
    if not isinstance(value, Mapping):
        return "none"
    return ", ".join(f"`{key}`: {value.get(key, 0)}" for key in OUTCOME_CLASSES if value.get(key, 0)) or "none"


def report_markdown(payload: Mapping[str, Any]) -> str:
    outcomes = payload.get("outcomes") if isinstance(payload.get("outcomes"), Mapping) else {}
    g_score = payload.get("g_score") if isinstance(payload.get("g_score"), Mapping) else {}
    return f"""# Scorecard v1 Before Predictivity

Date: 2026-05-10

## Scope

Scorecard v1 is a no-model, pre-predictivity, admission-safe diagnostic artifact. It separates verified outcomes from invalid submissions, infrastructure failures, missing coverage, and policy invalidity. It does not reinterpret failed scoreability cells as task capability failures.

Score input set digest: `{payload.get("score_input_set_digest")}`
Evidence input set digest: `{payload.get("evidence_input_set_digest")}`

## Outcomes

- Fixed denominator entries: `{payload.get("fixed_denominator", {}).get("score_input_entries")}`
- Outcome classes: {fmt_counts(outcomes.get("outcome_counts"))}
- Attemptability score: `{outcomes.get("attemptability_score")}`
- Verified correctness rate: `{outcomes.get("verified_correctness_rate")}`
- Fixed-denominator pass rate: `{outcomes.get("fixed_denominator_pass_rate")}`

## G_score

Availability: `{g_score.get("availability_status")}`. G_score value is `{g_score.get("g_score_value")}` because unavailable G_score is not treated as zero.

## Claim Boundary

This artifact does not claim ranking reversal, R_score > G_score predictivity, task-solving improvement, capability uplift, admission, license, or authorization.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/scorecard_v1_before_predictivity.py \\
  --output experiments/core_narrative/results/scorecard_v1_before_predictivity_20260510.json \\
  --report experiments/core_narrative/reports/2026-05-10_scorecard_v1_before_predictivity.md
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_scorecard(input_paths_from_args(args))
        if args.report:
            write_report(args.report, payload)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
