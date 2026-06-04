from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_adapter_stratified_reporting.yaml"
SCHEMA_VERSION = "barcarolle.phase1_adapter_stratified_reporting.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_adapter_stratified_reporting_output.v1"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(str(path))
    return raw if raw.is_absolute() else REPO_ROOT / raw


def rel(path: str | Path) -> str:
    resolved = repo_path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected adapter stratified reporting config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in repo_path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_csv(path: str | Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def round_or_none(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [row for row in rows if row.get("scoreable_flag") is True]
    pass_count = sum(1 for row in scoreable if row.get("pass_flag") is True)
    fail_count = sum(1 for row in scoreable if row.get("pass_flag") is False)
    return {
        "cell_count": len(rows),
        "scoreable_count": len(scoreable),
        "non_scoreable_count": len(rows) - len(scoreable),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "policy_violation_count": sum(1 for row in rows if row.get("terminal_status") == "policy_violation"),
        "terminal_status_counts": dict(sorted(Counter(str(row.get("terminal_status") or "") for row in rows).items())),
    }


def group_rows(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "")].append(row)
    return dict(grouped)


def rate_gap(b_eval_rows: list[dict[str, Any]], h_future_rows: list[dict[str, Any]]) -> dict[str, Any]:
    b_eval = summarize_rows(b_eval_rows)["pass_rate"]
    h_future = summarize_rows(h_future_rows)["pass_rate"]
    signed = None if b_eval is None or h_future is None else round(h_future - b_eval, 4)
    absolute = None if signed is None else round(abs(signed), 4)
    return {
        "B_eval_pass_rate": b_eval,
        "H_future_pass_rate": h_future,
        "H_future_minus_B_eval": signed,
        "absolute_gap": absolute,
    }


def load_result_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    payload = read_json(input_path(config, "diagnostics_result_cube"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("diagnostics result cube rows must be a list")
    return rows


def result_prefixes(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row["result_prefix"]) for row in rows if row.get("result_prefix")}


def adapter_ids(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row["adapter_id"]) for row in rows if row.get("adapter_id")})


def cost_summary_paths(config: dict[str, Any], prefixes: set[str]) -> list[Path]:
    pattern = str(input_path(config, "cost_summaries_glob"))
    paths = [Path(path) for path in sorted(glob.glob(pattern)) if Path(path).is_file()]
    if not paths:
        paths = sorted(repo_path("experiments/phase0_headroom/results").glob("phase1_three_repo_paid_validation_*_cost_summary.json"))
    selected = []
    for path in paths:
        payload = read_json(path)
        if payload.get("result_prefix") in prefixes:
            selected.append(path)
    return selected


def aggregate_cost_latency(config: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    prefixes = result_prefixes(rows)
    costs_by_adapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in cost_summary_paths(config, prefixes):
        payload = read_json(path)
        per_harness = payload.get("per_harness_observed_token_cost_usd") or {}
        adapter_id = next(iter(per_harness), None)
        if adapter_id is None:
            suffix = str(payload.get("result_prefix") or "")
            adapter_id = "kilo_workspace" if suffix.endswith("kilo_workspace") else "codex_workspace"
        payload["_path"] = rel(path)
        costs_by_adapter[str(adapter_id)].append(payload)

    usage_rows = [
        row
        for row in read_jsonl(input_path(config, "workspace_usage_ledger"))
        if str(row.get("result_prefix") or "") in prefixes
    ]
    latencies_by_adapter: dict[str, list[float]] = defaultdict(list)
    for row in usage_rows:
        latency = row.get("latency_seconds")
        if latency is not None:
            latencies_by_adapter[str(row.get("adapter_id"))].append(float(latency))

    adapter_summaries: dict[str, dict[str, Any]] = {}
    for adapter_id in adapter_ids(rows):
        cost_rows = costs_by_adapter.get(adapter_id, [])
        call_count = sum(int(row.get("call_count") or 0) for row in cost_rows)
        usage_observed_count = sum(int(row.get("usage_observed_count") or 0) for row in cost_rows)
        observed = sum(float(row.get("observed_token_estimated_cost_usd") or 0.0) for row in cost_rows)
        conservative = sum(float(row.get("conservative_estimated_cost_usd") or 0.0) for row in cost_rows)
        observed_or_conservative = sum(float(row.get("observed_or_conservative_estimated_cost_usd") or 0.0) for row in cost_rows)
        actual_values = [row.get("actual_provider_billed_cost_usd") for row in cost_rows]
        actual_provider_billed = next((value for value in actual_values if value is not None), None)
        adapter_cell_count = sum(1 for row in rows if row.get("adapter_id") == adapter_id)
        latencies = latencies_by_adapter.get(adapter_id, [])
        adapter_summaries[adapter_id] = {
            "adapter_id": adapter_id,
            "cost_basis": "observed_token_estimate",
            "cost_summary_count": len(cost_rows),
            "call_count": call_count,
            "usage_observed_count": usage_observed_count,
            "usage_observed_rate": None if call_count == 0 else round(usage_observed_count / call_count, 4),
            "missing_usage_cell_count": sum(int(row.get("missing_usage_cell_count") or 0) for row in cost_rows),
            "observed_token_estimated_cost_usd": round(observed, 6),
            "conservative_token_estimated_cost_usd": round(conservative, 6),
            "observed_or_conservative_estimated_cost_usd": round(observed_or_conservative, 6),
            "actual_provider_billed_cost_usd": actual_provider_billed,
            "provider_billed_cost_status": "available" if actual_provider_billed is not None else "unavailable",
            "cost_per_cell_usd": None if adapter_cell_count == 0 else round(observed / adapter_cell_count, 5),
            "median_latency_seconds": None if not latencies else round(statistics.median(latencies), 4),
            "latency_source": "workspace_usage_ledger",
            "latency_observation_count": len(latencies),
            "cost_summary_paths": [row["_path"] for row in cost_rows],
        }

    observed_total = sum(item["observed_token_estimated_cost_usd"] for item in adapter_summaries.values())
    conservative_total = sum(item["conservative_token_estimated_cost_usd"] for item in adapter_summaries.values())
    return {
        "artifact": "cost_latency_summary",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "cost_basis": "token_estimated_from_observed_usage",
        "provider_billed_exact_cost_available": any(
            item["actual_provider_billed_cost_usd"] is not None for item in adapter_summaries.values()
        ),
        "actual_provider_billed_cost_usd": None,
        "observed_token_estimated_cost_usd": round(observed_total, 6),
        "conservative_token_estimated_cost_usd": round(conservative_total, 6),
        "by_adapter": adapter_summaries,
        "notes": [
            "Observed token estimated cost is not a provider bill.",
            "Provider-billed exact cost is unavailable because actual_provider_billed_cost_usd is null.",
            "Raw usage artifact references were read from the committed ledger but are not copied into this summary.",
        ],
    }


def adapter_score_summary(config: dict[str, Any], rows: list[dict[str, Any]], cost_latency: dict[str, Any]) -> dict[str, Any]:
    summaries: dict[str, dict[str, Any]] = {}
    for adapter_id in adapter_ids(rows):
        adapter_rows = [row for row in rows if row.get("adapter_id") == adapter_id]
        by_repo = {
            repo_id: summarize_rows(repo_rows)
            for repo_id, repo_rows in sorted(group_rows(adapter_rows, "repo_id").items())
        }
        by_split = {
            split: summarize_rows(split_rows)
            for split, split_rows in sorted(group_rows(adapter_rows, "split").items())
        }
        by_repo_and_split: dict[str, dict[str, Any]] = {}
        b_eval_gap_by_repo: dict[str, dict[str, Any]] = {}
        for repo_id, repo_rows in sorted(group_rows(adapter_rows, "repo_id").items()):
            split_rows = group_rows(repo_rows, "split")
            by_repo_and_split[repo_id] = {
                split: summarize_rows(split_rows[split]) for split in sorted(split_rows)
            }
            b_eval_gap_by_repo[repo_id] = rate_gap(split_rows.get("B_eval", []), split_rows.get("H_future", []))
        split_rows = group_rows(adapter_rows, "split")
        base = summarize_rows(adapter_rows)
        cost_fields = cost_latency["by_adapter"].get(adapter_id, {})
        summaries[adapter_id] = {
            "adapter_id": adapter_id,
            **base,
            "pass_rate_by_repo": by_repo,
            "pass_rate_by_split": by_split,
            "pass_rate_by_repo_and_split": by_repo_and_split,
            "b_eval_h_future_gap": {
                "pooled": rate_gap(split_rows.get("B_eval", []), split_rows.get("H_future", [])),
                "by_repo": b_eval_gap_by_repo,
            },
            "observed_token_estimated_cost_usd": cost_fields.get("observed_token_estimated_cost_usd"),
            "conservative_token_estimated_cost_usd": cost_fields.get("conservative_token_estimated_cost_usd"),
            "actual_provider_billed_cost_usd": cost_fields.get("actual_provider_billed_cost_usd"),
            "provider_billed_cost_status": cost_fields.get("provider_billed_cost_status"),
            "cost_per_cell_usd": cost_fields.get("cost_per_cell_usd"),
            "usage_observed_rate": cost_fields.get("usage_observed_rate"),
            "median_latency_seconds": cost_fields.get("median_latency_seconds"),
        }
    return {
        "artifact": "three_repo_summary",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "adapter_level_results_first": True,
        "pooled_summary_status": "retrospective_diagnostic_only",
        "by_adapter": summaries,
    }

def csv_rows_for_adapter_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for adapter_id, adapter in summary["by_adapter"].items():
        rows.append(
            {
                "scope": "adapter_overall",
                "adapter_id": adapter_id,
                "repo_id": "",
                "split": "",
                "cell_count": adapter["cell_count"],
                "scoreable_count": adapter["scoreable_count"],
                "pass_count": adapter["pass_count"],
                "pass_rate": adapter["pass_rate"],
                "policy_violation_count": adapter["policy_violation_count"],
                "B_eval_pass_rate": adapter["b_eval_h_future_gap"]["pooled"]["B_eval_pass_rate"],
                "H_future_pass_rate": adapter["b_eval_h_future_gap"]["pooled"]["H_future_pass_rate"],
                "absolute_gap": adapter["b_eval_h_future_gap"]["pooled"]["absolute_gap"],
                "observed_token_estimated_cost_usd": adapter["observed_token_estimated_cost_usd"],
                "cost_per_cell_usd": adapter["cost_per_cell_usd"],
                "median_latency_seconds": adapter["median_latency_seconds"],
            }
        )
        for repo_id, repo_summary in adapter["pass_rate_by_repo"].items():
            gap = adapter["b_eval_h_future_gap"]["by_repo"][repo_id]
            rows.append(
                {
                    "scope": "adapter_repo",
                    "adapter_id": adapter_id,
                    "repo_id": repo_id,
                    "split": "",
                    "cell_count": repo_summary["cell_count"],
                    "scoreable_count": repo_summary["scoreable_count"],
                    "pass_count": repo_summary["pass_count"],
                    "pass_rate": repo_summary["pass_rate"],
                    "policy_violation_count": repo_summary["policy_violation_count"],
                    "B_eval_pass_rate": gap["B_eval_pass_rate"],
                    "H_future_pass_rate": gap["H_future_pass_rate"],
                    "absolute_gap": gap["absolute_gap"],
                }
            )
        for split, split_summary in adapter["pass_rate_by_split"].items():
            rows.append(
                {
                    "scope": "adapter_split",
                    "adapter_id": adapter_id,
                    "repo_id": "",
                    "split": split,
                    "cell_count": split_summary["cell_count"],
                    "scoreable_count": split_summary["scoreable_count"],
                    "pass_count": split_summary["pass_count"],
                    "pass_rate": split_summary["pass_rate"],
                    "policy_violation_count": split_summary["policy_violation_count"],
                }
            )
        for repo_id, split_map in adapter["pass_rate_by_repo_and_split"].items():
            for split, split_summary in split_map.items():
                rows.append(
                    {
                        "scope": "adapter_repo_split",
                        "adapter_id": adapter_id,
                        "repo_id": repo_id,
                        "split": split,
                        "cell_count": split_summary["cell_count"],
                        "scoreable_count": split_summary["scoreable_count"],
                        "pass_count": split_summary["pass_count"],
                        "pass_rate": split_summary["pass_rate"],
                        "policy_violation_count": split_summary["policy_violation_count"],
                    }
                )
    return rows


def exact_two_sided_sign_test(adapter_b_only: int, adapter_a_only: int) -> dict[str, Any]:
    n = adapter_a_only + adapter_b_only
    if n == 0:
        return {"n": 0, "adapter_b_only_pass": adapter_b_only, "adapter_a_only_pass": adapter_a_only, "p_value": None}
    tail = min(adapter_a_only, adapter_b_only)
    probability = 2 * sum(math.comb(n, k) * (0.5**n) for k in range(tail + 1))
    return {
        "n": n,
        "adapter_b_only_pass": adapter_b_only,
        "adapter_a_only_pass": adapter_a_only,
        "p_value": round(min(1.0, probability), 6),
    }


def paired_task_summary(config: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    adapters = adapter_ids(rows)
    if len(adapters) != 2:
        raise ValueError(f"expected exactly two adapters for paired summary, found {adapters}")
    adapter_a, adapter_b = adapters
    by_task: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_task[str(row["task_id"])][str(row["adapter_id"])] = row

    outcome_counts: Counter[str] = Counter()
    by_repo: dict[str, Counter[str]] = defaultdict(Counter)
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    complete_pairs = 0
    for task_id, task_rows in by_task.items():
        if adapter_a not in task_rows or adapter_b not in task_rows:
            continue
        complete_pairs += 1
        a_pass = task_rows[adapter_a].get("pass_flag") is True
        b_pass = task_rows[adapter_b].get("pass_flag") is True
        if a_pass and b_pass:
            outcome = "both_pass"
        elif not a_pass and not b_pass:
            outcome = "both_fail"
        elif a_pass:
            outcome = f"{adapter_a}_only_pass"
        else:
            outcome = f"{adapter_b}_only_pass"
        outcome_counts[outcome] += 1
        repo_id = str(task_rows[adapter_a].get("repo_id") or task_rows[adapter_b].get("repo_id") or "")
        split = str(task_rows[adapter_a].get("split") or task_rows[adapter_b].get("split") or "")
        by_repo[repo_id][outcome] += 1
        by_split[split][outcome] += 1

    adapter_a_only = outcome_counts[f"{adapter_a}_only_pass"]
    adapter_b_only = outcome_counts[f"{adapter_b}_only_pass"]
    disagreement_count = adapter_a_only + adapter_b_only
    return {
        "artifact": "pairwise_summary",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "adapter_a_id": adapter_a,
        "adapter_b_id": adapter_b,
        "paired_task_count": complete_pairs,
        "both_pass": outcome_counts["both_pass"],
        "both_fail": outcome_counts["both_fail"],
        "adapter_a_only_pass": adapter_a_only,
        "adapter_b_only_pass": adapter_b_only,
        f"{adapter_a}_only_pass": adapter_a_only,
        f"{adapter_b}_only_pass": adapter_b_only,
        "disagreement_count": disagreement_count,
        "disagreement_rate": None if complete_pairs == 0 else round(disagreement_count / complete_pairs, 4),
        "exact_count_summary": {
            "adapter_b_minus_adapter_a_only_pass": adapter_b_only - adapter_a_only,
            **exact_two_sided_sign_test(adapter_b_only, adapter_a_only),
        },
        "outcome_counts": dict(outcome_counts),
        "by_repo": {repo_id: dict(counter) for repo_id, counter in sorted(by_repo.items())},
        "by_split": {split: dict(counter) for split, counter in sorted(by_split.items())},
    }


def build_summary_payloads(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = load_result_rows(config)
    cost_latency = aggregate_cost_latency(config, rows)
    three_repo = adapter_score_summary(config, rows, cost_latency)
    pairwise = paired_task_summary(config, rows)
    return {
        "three_repo_summary": three_repo,
        "pairwise_summary": pairwise,
        "cost_latency_summary": cost_latency,
    }


def write_summary_artifacts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payloads = build_summary_payloads(config)
    write_json(output_path(config, "three_repo_summary"), payloads["three_repo_summary"])
    write_json(output_path(config, "pairwise_summary"), payloads["pairwise_summary"])
    write_json(output_path(config, "cost_latency_summary"), payloads["cost_latency_summary"])
    csv_rows = csv_rows_for_adapter_summary(payloads["three_repo_summary"])
    write_csv(
        output_path(config, "three_repo_summary_csv"),
        csv_rows,
        [
            "scope",
            "adapter_id",
            "repo_id",
            "split",
            "cell_count",
            "scoreable_count",
            "pass_count",
            "pass_rate",
            "policy_violation_count",
            "B_eval_pass_rate",
            "H_future_pass_rate",
            "absolute_gap",
            "observed_token_estimated_cost_usd",
            "cost_per_cell_usd",
            "median_latency_seconds",
        ],
    )
    return payloads


def build_future_gates_payload(config: dict[str, Any]) -> dict[str, Any]:
    validation = validate_policy(config)
    return {
        "artifact": "future_gates",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_loaded": validation["valid"],
        "status": "ready" if validation["valid"] else "blocked",
        "gates": [
            {
                "gate_id": "adapter_reporting_policy_loaded",
                "required_for": "all paid validation runbooks",
                "acceptance": "The runbook names the adapter reporting policy artifact before paid outcomes are interpreted.",
            },
            {
                "gate_id": "adapter_level_result_table_required",
                "required_for": "all cross-harness paid reports",
                "acceptance": "Each adapter has cell count, scoreable count, pass rate, repo/split breakouts, policy violations, cost basis, cost per cell, usage observed rate, and median latency.",
            },
            {
                "gate_id": "paired_disagreement_table_required_for_shared_tasks",
                "required_for": "cross-harness runs where adapters share tasks",
                "acceptance": "The report shows both pass, both fail, adapter A only pass, adapter B only pass, and disagreement rate.",
            },
            {
                "gate_id": "cost_estimate_or_bill_status_required",
                "required_for": "all paid reports",
                "acceptance": "The report states whether cost is token-estimated or provider-billed, and says provider-billed exact cost is unavailable when actual_provider_billed_cost_usd is null.",
            },
            {
                "gate_id": "pooled_headline_primary_only_if_preregistered",
                "required_for": "cross-harness paid reports with pooled summaries",
                "acceptance": "A pooled adapter headline is primary only if the runbook preregistered that aggregate before outcomes.",
            },
            {
                "gate_id": "pooled_headline_secondary_or_diagnostic_otherwise",
                "required_for": "cross-harness paid reports with non-preregistered pooled summaries",
                "acceptance": "A pooled adapter result is clearly marked secondary or retrospective diagnostic.",
            },
            {
                "gate_id": "single_acut_runs_must_name_scoreable_adapter_before_outcomes",
                "required_for": "single-ACUT paid validation",
                "acceptance": "The runbook chooses one scoreable ACUT/adapter before outcomes and reports that adapter identity in the result table.",
            },
        ],
        "single_acut_reporting_rule": {
            "adapter_table_required": True,
            "paired_disagreement_required": False,
            "scoreable_adapter_must_be_preregistered": True,
            "pooled_adapter_headline_allowed": False,
        },
        "cross_harness_reporting_rule": {
            "adapter_table_required": True,
            "paired_disagreement_required_when_shared_tasks": True,
            "adapter_as_blocking_or_reporting_factor": True,
            "pooled_only_headline_allowed": False,
        },
        "pooled_summary_rule": {
            "primary_allowed": "only_if_preregistered_before_outcomes",
            "otherwise": "secondary_or_retrospective_diagnostic",
            "never_allowed": "only_headline_for_cross_harness_paid_results",
        },
        "existing_runbooks_or_templates_to_reference": [
            "docs/experiments/phase-1-three-repo-paid-validation-runbook.md",
            "docs/experiments/phase-1-future-holdout-validation-runbook.md",
            "docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md",
            "docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md",
            "docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md",
            "docs/experiments/phase-1-boltons-paid-acut-smoke-runbook.md",
        ],
        "direct_runbook_updates_made": [],
        "why_no_direct_template_update": "No single central future paid-validation template exists in this repository. This run records gates and reference targets without drafting a next runbook.",
        "no_future_runbook_drafted": True,
    }


def render_future_gates_report(payload: dict[str, Any]) -> str:
    gates = "\n".join(
        f"- `{gate['gate_id']}`: {gate['acceptance']}" for gate in payload["gates"]
    )
    references = "\n".join(f"- `{path}`" for path in payload["existing_runbooks_or_templates_to_reference"])
    return f"""# Adapter Reporting Future Gates

Status: `{payload['status']}`.

What happened: future paid validation now has explicit adapter-reporting gates.
Why it matters: the next paid run should not repeat a pooled-only cross-harness headline.
Action suggested next: reference these gates before authorizing or executing any future cross-harness paid validation.

## Gates

{gates}

## Single-ACUT Rule

What happened: a single-ACUT paid run must name the scoreable adapter before outcomes.
Why it matters: a single adapter can be interpreted as one ACUT result, but the adapter identity is still part of the evidence.
Action suggested next: record the selected ACUT/adapter in the entry gate and result table.

## Cross-Harness Rule

What happened: a cross-harness paid run must show adapter-level results first and paired disagreement when adapters share tasks.
Why it matters: adapter effects can be large enough to change the apparent result.
Action suggested next: report each adapter as a separate ACUT result unless a pooled aggregate was preregistered.

## Pooled Summary Rule

- Primary pooled headline allowed: `{payload['pooled_summary_rule']['primary_allowed']}`.
- Otherwise: `{payload['pooled_summary_rule']['otherwise']}`.
- Never allowed: `{payload['pooled_summary_rule']['never_allowed']}`.

## Reference Targets

{references}

No direct runbook/template update was made in this step because there is no single central future paid-validation template. This run does not draft or create the next runbook.
"""


def write_future_gates_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_future_gates_payload(config)
    write_json(output_path(config, "future_gates"), payload)
    write_text(report_path(config, "future_gates"), render_future_gates_report(payload))
    return payload


def validate_policy(config: dict[str, Any]) -> dict[str, Any]:
    policy = config["policy"]
    adapter_metrics = set(config["required_adapter_metrics"])
    pairwise_metrics = set(config["required_pairwise_metrics"])
    cost_latency_fields = set(config["required_cost_latency_fields"])
    future_gates = set(config["future_paid_gates"])

    checks = {
        "adapter_level_results_before_pooled": policy.get("adapter_level_results_before_pooled") is True,
        "pooled_only_cross_harness_headline_disallowed": policy.get("pooled_only_cross_harness_headline_allowed") is False,
        "pooled_result_has_allowed_secondary_or_preregistered_forms": (
            policy.get("pooled_result_allowed_when_preregistered_primary") is True
            and policy.get("pooled_result_allowed_when_marked_diagnostic") is True
        ),
        "pilot_claim_boundary_preserved": policy.get("completed_paid_pilot_claim_boundary") == "pilot_evidence_only",
        "completed_paid_decision_not_mutable": policy.get("completed_paid_pilot_decision_mutable") is False,
        "predictive_validity_not_claimed": policy.get("predictive_validity_claim_allowed") is False,
        "token_estimate_not_provider_bill": policy.get("token_estimated_cost_is_provider_billed_cost") is False,
        "exact_bill_requires_provider_billed_cost": policy.get("actual_provider_billed_cost_required_for_exact_bill_claim") is True,
        "provider_bill_null_language_required": policy.get("if_actual_provider_billed_cost_null")
        == "report_provider_billed_cost_unavailable",
        "adapter_metrics_complete": {
            "adapter_id",
            "cell_count",
            "scoreable_count",
            "pass_rate",
            "pass_rate_by_repo",
            "pass_rate_by_split",
            "pass_rate_by_repo_and_split",
            "b_eval_h_future_gap",
            "policy_violation_count",
            "observed_token_estimated_cost_usd",
            "cost_per_cell_usd",
            "usage_observed_rate",
            "median_latency_seconds",
        }.issubset(adapter_metrics),
        "pairwise_metrics_complete": {
            "both_pass",
            "both_fail",
            "adapter_a_only_pass",
            "adapter_b_only_pass",
            "disagreement_rate",
        }.issubset(pairwise_metrics),
        "cost_latency_fields_complete": {
            "cost_basis",
            "observed_token_estimated_cost_usd",
            "actual_provider_billed_cost_usd",
            "provider_billed_cost_status",
            "median_latency_seconds",
        }.issubset(cost_latency_fields),
        "future_gates_complete": {
            "adapter_reporting_policy_loaded",
            "adapter_level_result_table_required",
            "paired_disagreement_table_required_for_shared_tasks",
            "cost_estimate_or_bill_status_required",
            "pooled_headline_primary_only_if_preregistered",
            "pooled_headline_secondary_or_diagnostic_otherwise",
        }.issubset(future_gates),
    }
    return {
        "valid": all(value is True for value in checks.values()),
        "checks": checks,
    }


def build_policy_payload(config: dict[str, Any]) -> dict[str, Any]:
    validation = validate_policy(config)
    return {
        "artifact": "policy",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "source_run_id": config["source_run_id"],
        "diagnostics_run_id": config["diagnostics_run_id"],
        "generated_at": now_utc(),
        "policy_valid": validation["valid"],
        "policy_checks": validation["checks"],
        "required_adapter_metrics": config["required_adapter_metrics"],
        "required_pairwise_metrics": config["required_pairwise_metrics"],
        "required_cost_latency_fields": config["required_cost_latency_fields"],
        "future_paid_gates": config["future_paid_gates"],
        "claim_boundaries": {
            "adapter_level_first": config["policy"]["adapter_level_results_before_pooled"],
            "pooled_only_cross_harness_headline_allowed": config["policy"]["pooled_only_cross_harness_headline_allowed"],
            "pooled_result_primary_allowed_only_if_preregistered": config["policy"][
                "pooled_result_allowed_when_preregistered_primary"
            ],
            "pooled_result_secondary_allowed_if_marked_diagnostic": config["policy"][
                "pooled_result_allowed_when_marked_diagnostic"
            ],
            "completed_paid_pilot": config["policy"]["completed_paid_pilot_claim_boundary"],
            "completed_paid_pilot_decision_mutable": config["policy"]["completed_paid_pilot_decision_mutable"],
            "predictive_validity_claim_allowed": config["policy"]["predictive_validity_claim_allowed"],
        },
        "cost_language": {
            "observed_token_estimated_cost_is_provider_billed_cost": config["policy"][
                "token_estimated_cost_is_provider_billed_cost"
            ],
            "exact_bill_claim_requires_actual_provider_billed_cost": config["policy"][
                "actual_provider_billed_cost_required_for_exact_bill_claim"
            ],
            "when_actual_provider_billed_cost_is_null": config["policy"]["if_actual_provider_billed_cost_null"],
        },
        "actions_suggested_next": [
            "Generate adapter-level score, cost, and latency tables before any pooled result.",
            "Mark any pooled adapter summary as preregistered primary or retrospective diagnostic.",
            "Keep the completed paid pilot claim boundary as pilot evidence only.",
        ],
    }


def render_policy_report(payload: dict[str, Any]) -> str:
    return f"""# Adapter-Stratified Reporting Policy

Status: `{'complete' if payload['policy_valid'] else 'blocked'}`.

What happened: the reporting rule now requires adapter-level evidence before any pooled cross-harness summary.
Why it matters: Codex and Kilo results can differ even under the same model, so a single pooled headline can hide a harness effect.
Action suggested next: generate adapter-stratified score, paired-disagreement, cost, and latency summaries from committed artifacts.

## Required Rule

- Adapter-level results must be shown before pooled adapter summaries.
- A pooled cross-harness result must not be the only headline.
- A pooled result can be primary only when it was preregistered before outcomes.
- Otherwise, pooled results are secondary or retrospective diagnostic evidence.
- The completed three-repo paid pilot remains pilot evidence only.
- This run does not change the completed paid pilot decision.

## Required Adapter Metrics

{chr(10).join(f'- `{metric}`' for metric in payload['required_adapter_metrics'])}

## Required Paired-Task Metrics

{chr(10).join(f'- `{metric}`' for metric in payload['required_pairwise_metrics'])}

## Cost Language

- Token-estimated cost is an estimate from observed token usage.
- Provider-billed exact cost can be claimed only when `actual_provider_billed_cost_usd` is available.
- If `actual_provider_billed_cost_usd` is null, the report must say provider-billed exact cost is unavailable.

## Validation

- Policy valid: `{payload['policy_valid']}`.
- Failed checks: `{[key for key, value in payload['policy_checks'].items() if value is not True]}`.
"""


def write_policy_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_policy_payload(config)
    write_json(output_path(config, "policy"), payload)
    write_text(report_path(config, "policy"), render_policy_report(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 1 adapter-stratified reporting artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("command", choices=["policy", "summaries", "future-gates", "all"])
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.command in {"policy", "all"}:
        payload = write_policy_artifacts(config)
        if not payload["policy_valid"]:
            return 1
    if args.command in {"summaries", "all"}:
        write_summary_artifacts(config)
    if args.command in {"future-gates", "all"}:
        write_future_gates_artifacts(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
