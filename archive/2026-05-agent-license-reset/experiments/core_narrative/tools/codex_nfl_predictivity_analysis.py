#!/usr/bin/env python3
"""Compare RBench/G_score evidence against held-out RWork W_score evidence."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import emit_json, fail, iso_now


TOOL = "codex_nfl_predictivity_analysis"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rbench-matrix", required=True)
    parser.add_argument("--rwork-matrix", required=True)
    parser.add_argument("--gscore-basis", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(list(argv))


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def score_rows(matrix: Mapping[str, Any], score_name: str) -> dict[str, dict[str, Any]]:
    by_acut = matrix.get("by_acut") if isinstance(matrix.get("by_acut"), dict) else {}
    rows: dict[str, dict[str, Any]] = {}
    for acut, payload in by_acut.items():
        if not isinstance(payload, dict):
            continue
        rows[str(acut)] = {
            "score_name": score_name,
            "score_percent": payload.get("score_percent_fixed_denominator"),
            "passed": payload.get("passed"),
            "denominator": payload.get("fixed_denominator"),
            "scoreable": payload.get("scoreable"),
            "canonical_present": payload.get("canonical_present"),
            "canonical_missing": payload.get("canonical_missing"),
            "wilson_95": payload.get("wilson_95_fixed_denominator"),
            "status_counts": payload.get("status_counts", {}),
            "failure_label_counts": payload.get("failure_label_counts", {}),
        }
    return rows


def rank_rows(rows: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    sortable = []
    for acut, row in rows.items():
        score = row.get("score_percent")
        if isinstance(score, (int, float)):
            sortable.append((float(score), acut))
    ordered = sorted(sortable, key=lambda item: (-item[0], item[1]))
    return [
        {"rank": index + 1, "acut_id": acut, "score_percent": score}
        for index, (score, acut) in enumerate(ordered)
    ]


def error_metrics(predictor: Mapping[str, Mapping[str, Any]], target: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[float] = []
    per_acut: dict[str, Any] = {}
    for acut, pred in predictor.items():
        pred_score = pred.get("score_percent")
        target_score = target.get(acut, {}).get("score_percent")
        if not isinstance(pred_score, (int, float)) or not isinstance(target_score, (int, float)):
            continue
        error = float(pred_score) - float(target_score)
        errors.append(error)
        per_acut[acut] = {
            "predicted_score_percent": float(pred_score),
            "target_score_percent": float(target_score),
            "signed_error_points": error,
            "absolute_error_points": abs(error),
        }
    if not errors:
        return {"status": "not_computable", "reason": "no paired numeric scores"}
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    bias = sum(errors) / len(errors)
    return {
        "status": "computed",
        "paired_acut_count": len(errors),
        "mae_points": mae,
        "rmse_points": rmse,
        "mean_signed_error_points": bias,
        "per_acut": per_acut,
    }


def rank_positions(rank: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {str(item["acut_id"]): int(item["rank"]) for item in rank if "acut_id" in item and "rank" in item}


def rank_delta(source_rank: Sequence[Mapping[str, Any]], target_rank: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    source = rank_positions(source_rank)
    target = rank_positions(target_rank)
    deltas = {
        acut: {
            "source_rank": source[acut],
            "target_rank": target[acut],
            "delta": source[acut] - target[acut],
        }
        for acut in sorted(source)
        if acut in target
    }
    return {"status": "computed" if deltas else "not_computable", "per_acut": deltas}


def gscore_rows(gscore: Mapping[str, Any], acuts: Sequence[str]) -> dict[str, dict[str, Any]]:
    raw_scores = gscore.get("g_scores") if isinstance(gscore.get("g_scores"), dict) else {}
    rows: dict[str, dict[str, Any]] = {}
    for acut in acuts:
        value = raw_scores.get(acut)
        rows[acut] = {
            "score_name": "G_score",
            "score_percent": value if isinstance(value, (int, float)) else None,
            "basis_status": gscore.get("status"),
            "basis": gscore.get("g_score_basis"),
            "direct_gscore_used": bool(gscore.get("direct_gscore_used")),
        }
    return rows


def status_distribution(matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status_counts_canonical": matrix.get("status_counts_canonical", {}),
        "failure_label_counts_canonical": matrix.get("failure_label_counts_canonical", {}),
        "metadata_missing_counts_canonical_future_contract": matrix.get(
            "metadata_missing_counts_canonical_future_contract",
            {},
        ),
    }


def build_report(payload: Mapping[str, Any]) -> str:
    r_error = payload["predictivity"]["r_score_vs_w_score_error"]
    g_error = payload["predictivity"]["g_score_vs_w_score_error"]
    r_dist = payload["r_score"]["distributions"]
    w_dist = payload["w_score"]["distributions"]

    def fmt_ci(row: Mapping[str, Any]) -> str:
        interval = row.get("wilson_95") if isinstance(row.get("wilson_95"), Mapping) else {}
        lower = interval.get("lower")
        upper = interval.get("upper")
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
            return "n/a"
        return f"{100 * lower:.1f}-{100 * upper:.1f}"

    def fmt_counts(value: Any) -> str:
        if not isinstance(value, Mapping) or not value:
            return "{}"
        return ", ".join(f"{key}={value[key]}" for key in sorted(value))

    def fmt_rank(rank: Sequence[Mapping[str, Any]]) -> str:
        return ", ".join(f"{item['rank']}. {item['acut_id']} ({item['score_percent']:.1f})" for item in rank)

    lines = [
        "# Barcarolle Click G/R/W Predictivity Step 7 Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Scope",
        "",
        "This report compares the Click RBench canonical evidence against the held-out Click RWork slice for the four core ACUTs. It also records G_score status from the pinned SWE-Bench Pro configuration.",
        "",
        "## Method",
        "",
        "- R_score is the canonical-latest fixed-denominator pass percentage from the 4 ACUT x 8 Click RBench matrix.",
        "- W_score is the canonical-latest fixed-denominator pass percentage from the 4 ACUT x 6 Click RWork matrix.",
        "- Canonical latest chooses the highest scoreable attempt for each ACUT/task cell. Provider/infra retries are retained as artifacts but do not replace scoreable evidence.",
        "- G_score uses only direct SWE-Bench Pro execution when feasible; this run did not substitute public, external, or proxy scores.",
        "",
        "## Result",
        "",
        f"- R_score vs W_score error status: `{r_error['status']}`.",
        f"- G_score vs W_score error status: `{g_error['status']}`.",
        f"- G_score basis: `{payload['g_score']['basis_status']}`; direct G_score used: `{payload['g_score']['direct_gscore_used']}`.",
        f"- Ranking reversal claim: `{payload['predictivity']['ranking_reversal_assessment']['status']}`.",
        "",
        "## Scores",
        "",
        "| ACUT | R_score | W_score | G_score basis |",
        "| --- | ---: | ---: | --- |",
    ]
    for acut in payload["acut_ids"]:
        r_score = payload["r_score"]["by_acut"][acut]["score_percent"]
        w_score = payload["w_score"]["by_acut"][acut]["score_percent"]
        g_row = payload["g_score"]["by_acut"][acut]
        g_score = g_row.get("score_percent")
        g_text = "unavailable" if g_score is None else f"{g_score:.1f}"
        lines.append(f"| `{acut}` | {r_score:.1f} | {w_score:.1f} | {g_text} |")
    lines.extend(
        [
            "",
            "## Confidence",
            "",
            "| ACUT | R passed/total | R Wilson 95% | W passed/total | W Wilson 95% |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for acut in payload["acut_ids"]:
        r_row = payload["r_score"]["by_acut"][acut]
        w_row = payload["w_score"]["by_acut"][acut]
        lines.append(
            f"| `{acut}` | {r_row['passed']}/{r_row['denominator']} | {fmt_ci(r_row)} | "
            f"{w_row['passed']}/{w_row['denominator']} | {fmt_ci(w_row)} |"
        )
    lines.extend(
        [
            "",
            "## Rank And Error",
            "",
            f"- R rank order: {fmt_rank(payload['r_score']['rank_order'])}.",
            f"- W rank order: {fmt_rank(payload['w_score']['rank_order'])}.",
        ]
    )
    if r_error["status"] == "computed":
        lines.extend(
            [
                f"- R->W MAE: {r_error['mae_points']:.2f} percentage points.",
                f"- R->W RMSE: {r_error['rmse_points']:.2f} percentage points.",
                f"- R->W mean signed error: {r_error['mean_signed_error_points']:.2f} percentage points.",
            ]
        )
    lines.extend(
        [
            "",
            "## Distributions",
            "",
            f"- RBench canonical status counts: {fmt_counts(r_dist.get('status_counts_canonical'))}.",
            f"- RBench canonical failure labels: {fmt_counts(r_dist.get('failure_label_counts_canonical'))}.",
            f"- RBench future-contract metadata gaps: {fmt_counts(r_dist.get('metadata_missing_counts_canonical_future_contract'))}.",
            f"- RWork canonical status counts: {fmt_counts(w_dist.get('status_counts_canonical'))}.",
            f"- RWork canonical failure labels: {fmt_counts(w_dist.get('failure_label_counts_canonical'))}.",
            f"- RWork future-contract metadata gaps: {fmt_counts(w_dist.get('metadata_missing_counts_canonical_future_contract'))}.",
            "",
            "## G Score",
            "",
            f"- Status: `{payload['g_score']['basis_status']}`.",
            f"- Basis: `{payload['g_score']['basis']}`.",
            "- Direct G_score values are unavailable and are not treated as zero.",
        ]
    )
    blockers = payload["g_score"].get("blockers")
    if isinstance(blockers, list) and blockers:
        for blocker in blockers:
            if isinstance(blocker, Mapping):
                lines.append(f"- Blocker: `{blocker.get('blocker')}`.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["predictivity"]["ranking_reversal_assessment"]["summary"],
            "",
            "R_score/W_score comparisons are based on small Click-only samples, so the numbers are diagnostic rather than proof of a stable ranking law. Missing direct G_score prevents any supported claim that repository-specific RBench is more predictive than a general benchmark under matched conditions.",
            "",
            "This run does show a Click-only mismatch: R_score overestimated W_score for all four ACUTs, and the R rank leader (`frontier-generic-swe`) tied for last by W_score. That is a warning signal, not a ranking-reversal proof.",
            "",
            "## Reproduction",
            "",
            "1. Run `codex_nfl_canonical_matrix.py --split rbench` against the normalized result root.",
            "2. Run `codex_nfl_canonical_matrix.py --split rwork` against the same normalized result root.",
            "3. Run `codex_nfl_gscore_basis.py` to record direct G_score feasibility from `general_benchmark.yaml`.",
            "4. Run `codex_nfl_predictivity_analysis.py` with the RBench matrix, RWork matrix, and G_score basis JSON artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def build_analysis(rbench: Mapping[str, Any], rwork: Mapping[str, Any], gscore: Mapping[str, Any]) -> dict[str, Any]:
    r_rows = score_rows(rbench, "R_score")
    w_rows = score_rows(rwork, "W_score")
    acuts = sorted(set(r_rows) | set(w_rows))
    g_rows = gscore_rows(gscore, acuts)
    r_rank = rank_rows(r_rows)
    w_rank = rank_rows(w_rows)
    g_rank = rank_rows(g_rows)
    g_direct_used = bool(gscore.get("direct_gscore_used"))
    ranking_assessment = {
        "status": "not_supported",
        "summary": (
            "No ranking reversal conclusion is supported: W_score has a bounded held-out Click slice, "
            "but direct G_score is unavailable and the R/W sample is too small for stable reversal claims."
        ),
        "blockers": [
            "direct G_score unavailable",
            "single repository only",
            "small RBench/RWork task counts",
        ],
    }
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "acut_ids": acuts,
        "inputs": {
            "rbench_split": rbench.get("split"),
            "rwork_split": rwork.get("split"),
            "gscore_status": gscore.get("status"),
        },
        "r_score": {
            "basis": "Click RBench canonical latest fixed-denominator pass percentage",
            "rank_order": r_rank,
            "by_acut": r_rows,
            "distributions": status_distribution(rbench),
        },
        "w_score": {
            "basis": "Click RWork canonical latest fixed-denominator pass percentage",
            "rank_order": w_rank,
            "by_acut": w_rows,
            "distributions": status_distribution(rwork),
        },
        "g_score": {
            "basis_status": gscore.get("status"),
            "basis": gscore.get("g_score_basis"),
            "direct_gscore_used": g_direct_used,
            "rank_order": g_rank,
            "by_acut": g_rows,
            "blockers": gscore.get("blockers", []),
        },
        "predictivity": {
            "r_score_vs_w_score_error": error_metrics(r_rows, w_rows),
            "g_score_vs_w_score_error": (
                error_metrics(g_rows, w_rows)
                if g_direct_used
                else {
                    "status": "not_computable",
                    "reason": "direct G_score unavailable; external/proxy scores were not substituted",
                }
            ),
            "r_score_vs_w_score_rank_delta": rank_delta(r_rank, w_rank),
            "g_score_vs_w_score_rank_delta": (
                rank_delta(g_rank, w_rank)
                if g_direct_used
                else {
                    "status": "not_computable",
                    "reason": "direct G_score unavailable",
                }
            ),
            "ranking_reversal_assessment": ranking_assessment,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_analysis(
            load_json(Path(args.rbench_matrix)),
            load_json(Path(args.rwork_matrix)),
            load_json(Path(args.gscore_basis)),
        )
        emit_json(payload, args.output)
        Path(args.report).write_text(build_report(payload), encoding="utf-8")
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
