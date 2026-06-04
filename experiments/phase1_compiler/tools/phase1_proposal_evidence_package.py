from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from phase1_future_holdout import simple_yaml_load

import phase1_retrospective_predictive_signal as signal


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_proposal_evidence_package.yaml"
SCHEMA_VERSION = "barcarolle.phase1_proposal_evidence_package.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_proposal_evidence_package_output.v1"

REPORT_INDEX_ROWS = [
    {
        "report": "experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md",
        "evidence_type": "diagnostic_negative",
        "claim_function": "Shows naive weighting can fail materially.",
        "key_numeric_result_or_status": "Weighted gaps: attrs 0.3148, boltons 0.7481; simple same-budget baselines 0.25 and 0.125.",
        "limitation": "Two-repo paid pilot; negative evidence for one design, not a validation result.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md",
        "evidence_type": "diagnostic_negative",
        "claim_function": "Diagnoses why the old weighted objective is underidentified.",
        "key_numeric_result_or_status": "Old weighted target-profile design not promoted; repo-stratified/simple baselines remain conservative.",
        "limitation": "Local no-paid analysis only.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md",
        "evidence_type": "technical_tractability",
        "claim_function": "Shows workspace ACUT protocol, endpoint accounting, and policy checks can run end to end.",
        "key_numeric_result_or_status": "120 planned cells, 120 completed, scoreability 1.0, endpoint compliance pass, cost $51.267333.",
        "limitation": "Exploratory pilot evidence; predictive validity not established.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md",
        "evidence_type": "source_quality",
        "claim_function": "Repairs the click source-context caveat for source-quality narrative use.",
        "key_numeric_result_or_status": "30/30 click tasks repaired with public context; 0 paid LLM calls; 0 paid ACUT cells.",
        "limitation": "Does not rewrite paid outcomes or prove predictive validity.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md",
        "evidence_type": "adapter_reporting",
        "claim_function": "Justifies adapter-stratified reporting as primary.",
        "key_numeric_result_or_status": "Supplement fair enough to interpret as ACUT-configuration evidence; model-only claim disallowed.",
        "limitation": "Post-hoc diagnostic supplement, not primary predictive-validity evidence.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md",
        "evidence_type": "retrospective_traction",
        "claim_function": "Compares candidate against simple baselines before M3 strengthening.",
        "key_numeric_result_or_status": "Coverage candidate MAE 0.209 vs temporal baseline MAE 0.2149.",
        "limitation": "Pseudo-future and underpowered; needs many-seed random and baseline envelope.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md",
        "evidence_type": "adapter_fragility",
        "claim_function": "Shows the candidate signal is not uniform across ACUT adapters.",
        "key_numeric_result_or_status": "Candidate worse than temporal baseline on Codex and better on Kilo in the proposal report summary.",
        "limitation": "Retrospective slices are sparse.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md",
        "evidence_type": "uncertainty",
        "claim_function": "Keeps retrospective signal in traction-only scope.",
        "key_numeric_result_or_status": "Claim strength: traction_evidence_only; sample size too sparse for formal predictive validity.",
        "limitation": "No formal interval estimated.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md",
        "evidence_type": "candidate_policy",
        "claim_function": "Freezes the outcome-blind candidate policy and exposes fallback behavior.",
        "key_numeric_result_or_status": "18 selected tasks; 6 per repo; boltons uses insufficient-feature-support fallback.",
        "limitation": "M4 still owns fallback threshold and candidate-policy hardening.",
        "main_text": "yes",
    },
    {
        "report": "experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md",
        "evidence_type": "source_supply",
        "claim_function": "Keeps task supply work in Layer 1 infrastructure rather than core claim.",
        "key_numeric_result_or_status": "Paid-ready false; internal repo-history v2 should continue; external systems are future references/adapters only.",
        "limitation": "Does not make broad generator expansion part of M3.",
        "main_text": "no",
    },
]


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


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(repo_path(path))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected proposal evidence package config schema_version")
    config["_path"] = str(repo_path(path))
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def doc_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["docs"][key])


def read_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_file(path: str | Path) -> str | None:
    resolved = repo_path(path)
    if not resolved.exists():
        return None
    return "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def command_stdout(args: list[str], *, timeout: int = 120) -> str:
    result = command_result(args, timeout=timeout)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_tracked(path: str | Path) -> bool:
    result = command_result(["git", "ls-files", "--error-unmatch", rel(path)])
    return result["returncode"] == 0


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if pct <= 0:
        return ordered[0]
    if pct >= 100:
        return ordered[-1]
    position = (len(ordered) - 1) * pct / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def distribution_summary(values: list[float]) -> dict[str, Any]:
    valid = [float(value) for value in values if value is not None]
    if not valid:
        return {"count": 0, "min": None, "p05": None, "p25": None, "median": None, "mean": None, "p75": None, "p95": None, "max": None}
    return {
        "count": len(valid),
        "min": round_float(min(valid)),
        "p05": round_float(percentile(valid, 5)),
        "p25": round_float(percentile(valid, 25)),
        "median": round_float(percentile(valid, 50)),
        "mean": round_float(statistics.mean(valid)),
        "p75": round_float(percentile(valid, 75)),
        "p95": round_float(percentile(valid, 95)),
        "max": round_float(max(valid)),
    }


def candidate_percentile(values: list[float], candidate_value: float | None) -> dict[str, Any]:
    valid = [float(value) for value in values if value is not None]
    if candidate_value is None or not valid:
        return {"lower_is_better_percentile": None, "beats_random_share": None, "tie_share": None}
    lower_or_equal = sum(1 for value in valid if value <= candidate_value)
    greater_or_equal = sum(1 for value in valid if value >= candidate_value)
    ties = sum(1 for value in valid if value == candidate_value)
    return {
        "lower_is_better_percentile": round_float(100 * lower_or_equal / len(valid)),
        "beats_random_share": round_float(100 * greater_or_equal / len(valid)),
        "tie_share": round_float(100 * ties / len(valid)),
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_None._"]
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def required_input_availability(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    availability: dict[str, dict[str, Any]] = {}
    for key, raw_path in sorted(config["inputs"].items()):
        resolved = repo_path(raw_path)
        availability[key] = {
            "path": rel(resolved),
            "exists": resolved.exists(),
            "tracked": git_tracked(resolved) if resolved.exists() else False,
            "size_bytes": resolved.stat().st_size if resolved.exists() else None,
            "digest": digest_file(resolved),
        }
    return availability


def write_process_report(config: dict[str, Any], current_step: str, completed: list[str], notes: list[str] | None = None) -> None:
    lines = [
        "# Phase 1 Proposal Evidence Package Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
    ]
    lines.extend([f"- `{item}`" for item in completed] or ["- None yet."])
    lines.extend(
        [
            "",
            "Boundary:",
            "",
            "- New paid ACUT solver cells run: `false`.",
            "- New paid LLM calls run: `false`.",
            "- External reviewer calls run: `false`.",
            "- Public citation browsing run: `false`.",
            "- Score tables, selected task IDs, split labels, source eligibility artifacts, task statements, and completed decisions changed: `false`.",
            "- Predictive validity established: `false`.",
            "- Paid validation authorized: `false`.",
            "- Later M4/M5/M6 runbook drafted: `false`.",
        ]
    )
    if notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in notes)
    write_text(report_path(config, "process"), "\n".join(lines))


def build_preflight(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    status = command_result(["git", "status", "--short", "--untracked-files=all"])
    diff_check = command_result(["git", "diff", "--check"])
    availability = required_input_availability(config)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "date_utc": now_utc()[:10],
        "worktree_status_short_untracked_all": [line for line in status["stdout"].splitlines() if line.strip()],
        "git_diff_check": {"returncode": diff_check["returncode"], "stdout": diff_check["stdout"], "stderr": diff_check["stderr"]},
        "required_input_availability": availability,
        "missing_required_inputs": [item["path"] for item in availability.values() if not item["exists"]],
        "m2_route_confirmed": True,
        "artifact_plan": {
            "add_tooling": True,
            "reason": "M3 requires many-seed random, envelope, ablation, fallback, source-status, summary, and evidence-index outputs not emitted by the retrospective tool.",
        },
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "preflight"), payload)
    write_process_report(
        config,
        "Step 0 - Preflight And Artifact Plan",
        [rel(output_path(config, "preflight"))],
        ["All required inputs are inventoried; no paid calls or external review calls are made by this tool."],
    )
    return payload


def boundary_flags(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "new_paid_acut_cells_run": False,
        "new_paid_llm_calls_run": False,
        "external_reviewer_calls_run": False,
        "public_citation_browsing_run": False,
        "paid_calls_allowed_by_config": bool(config.get("paid_calls_allowed")),
        "external_review_allowed_by_config": bool(config.get("external_review_allowed")),
        "public_citation_browsing_allowed_by_config": bool(config.get("public_citation_browsing_allowed")),
        "score_tables_changed": False,
        "task_ids_or_split_labels_changed": False,
        "predictive_validity_established": False,
        "paid_validation_authorized": False,
    }


def retrospective_config(config: dict[str, Any]) -> dict[str, Any]:
    return signal.load_config(input_path(config, "retrospective_config"))


def metric_rows_for_design(config: dict[str, Any], design_id: str) -> list[dict[str, Any]]:
    metrics = read_json(input_path(config, "retrospective_adapter_metrics"))
    return [row for row in metrics["metric_rows"] if row["design_id"] == design_id]


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("absolute_gap") is not None]
    if not valid:
        return {
            "slice_count": 0,
            "MAE": None,
            "RMSE": None,
            "mean_signed_error": None,
            "catastrophic_miss_rate": None,
            "non_scoreable_count": sum(int(row.get("missing_or_non_scoreable_count") or 0) for row in rows),
        }
    return {
        "slice_count": len(valid),
        "MAE": round_float(statistics.mean(float(row["absolute_gap"]) for row in valid)),
        "RMSE": round_float(math.sqrt(statistics.mean(float(row["squared_error"]) for row in valid))),
        "mean_signed_error": round_float(statistics.mean(float(row["signed_error"]) for row in valid)),
        "catastrophic_miss_rate": round_float(sum(1 for row in valid if row["catastrophic_miss"]) / len(valid)),
        "non_scoreable_count": sum(int(row.get("missing_or_non_scoreable_count") or 0) for row in rows),
    }


def group_specs(metric_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    adapters = sorted({str(row["adapter_id"]) for row in metric_rows})
    repos = sorted({str(row["repo"]) for row in metric_rows})
    windows = sorted({str(row["window_id"]) for row in metric_rows})
    specs = [{"group_type": "overall", "group_id": "overall", "primary": "secondary_equal_mix"}]
    specs.extend({"group_type": "adapter", "group_id": adapter, "primary": "primary"} for adapter in adapters)
    specs.extend({"group_type": "repo", "group_id": repo, "primary": "diagnostic"} for repo in repos)
    specs.extend({"group_type": "window", "group_id": window, "primary": "diagnostic"} for window in windows)
    return specs


def filter_group(rows: list[dict[str, Any]], group: dict[str, str]) -> list[dict[str, Any]]:
    group_type = group["group_type"]
    group_id = group["group_id"]
    if group_type == "overall":
        return rows
    if group_type == "adapter":
        return [row for row in rows if row["adapter_id"] == group_id]
    if group_type == "repo":
        return [row for row in rows if row["repo"] == group_id]
    if group_type == "window":
        return [row for row in rows if row["window_id"] == group_id]
    raise ValueError(f"unknown group type {group_type}")


def score_row_or_missing(score_by_adapter_task: dict[tuple[str, str], dict[str, Any]], adapter: str, task_id: str) -> dict[str, Any]:
    source = score_by_adapter_task.get((adapter, task_id))
    if source:
        return source
    return {
        "adapter_id": adapter,
        "task_id": task_id,
        "scoreable_cell": False,
        "pass_flag": False,
        "fail_flag": False,
        "terminal_status": "missing_committed_score_row",
    }


def random_seed_metric_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    retro = retrospective_config(config)
    universe = signal.load_universe(retro)
    window_plan = signal.load_window_plan(retro)
    row_by_id = signal.rows_by_task_id(universe)
    score_rows = signal.read_score_rows(retro)
    score_by_adapter_task = {(row["adapter_id"], row["task_id"]): row for row in score_rows}
    threshold = float(config["settings"]["catastrophic_gap_threshold"])
    seed_start = int(config["settings"]["random_seed_start"])
    seed_count = int(config["settings"]["random_seed_count"])
    rows: list[dict[str, Any]] = []
    for seed in range(seed_start, seed_start + seed_count):
        for window in window_plan["windows"]:
            pools = signal.window_pools(window, row_by_id)
            budget_key = "rolling_b_eval_budget_per_repo" if window["window_id"] == "repo_specific_earliest_time_bucket_cutoff" else "primary_b_eval_budget_per_repo"
            for repo in signal.REPOS:
                b_pool = pools[repo]["B_eval"]
                h_pool = pools[repo]["H_future"]
                budget = min(int(retro["settings"][budget_key]), len(b_pool))
                selected = signal.select_seeded_random(b_pool, budget, seed, str(window["window_id"]), repo)
                weights = signal.uniform_weights([row["task_id"] for row in selected])
                for adapter in signal.ADAPTERS:
                    b_rows = [score_row_or_missing(score_by_adapter_task, adapter, row["task_id"]) for row in selected]
                    h_rows = [score_row_or_missing(score_by_adapter_task, adapter, row["task_id"]) for row in h_pool]
                    b_rate, b_n, b_pass, b_non = signal.weighted_rate(b_rows, weights)
                    h_rate, h_n, h_pass, h_non = signal.weighted_rate(h_rows, None)
                    if b_rate is None or h_rate is None:
                        signed = None
                        gap = None
                        squared = None
                    else:
                        signed = b_rate - h_rate
                        gap = abs(signed)
                        squared = signed * signed
                    rows.append(
                        {
                            "seed": seed,
                            "window_id": window["window_id"],
                            "mode": window["mode"],
                            "repo": repo,
                            "adapter_id": adapter,
                            "design_id": config["settings"]["random_baseline_id"],
                            "B_eval_pass_rate": round_float(b_rate),
                            "H_future_pass_rate": round_float(h_rate),
                            "signed_error": round_float(signed),
                            "absolute_gap": round_float(gap),
                            "squared_error": round_float(squared),
                            "catastrophic_miss": bool(gap is not None and gap > threshold),
                            "B_eval_scoreable_count": b_n,
                            "H_future_scoreable_count": h_n,
                            "B_eval_pass_count": b_pass,
                            "H_future_pass_count": h_pass,
                            "missing_or_non_scoreable_count": b_non + h_non,
                        }
                    )
    return rows


def seed_summaries_for_group(rows: list[dict[str, Any]], group: dict[str, str]) -> list[dict[str, Any]]:
    by_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in filter_group(rows, group):
        by_seed[int(row["seed"])].append(row)
    summaries: list[dict[str, Any]] = []
    for seed in sorted(by_seed):
        summary = summarize_rows(by_seed[seed])
        summaries.append({"seed": seed, **summary})
    return summaries


def build_random_baseline_distribution(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    candidate_id = str(config["settings"]["candidate_design_id"])
    random_rows = random_seed_metric_rows(config)
    candidate_rows = metric_rows_for_design(config, candidate_id)
    groups = group_specs(candidate_rows)
    group_distributions = []
    for group in groups:
        seed_summaries = seed_summaries_for_group(random_rows, group)
        candidate_summary = summarize_rows(filter_group(candidate_rows, group))
        mae_values = [row["MAE"] for row in seed_summaries if row["MAE"] is not None]
        miss_values = [row["catastrophic_miss_rate"] for row in seed_summaries if row["catastrophic_miss_rate"] is not None]
        group_distributions.append(
            {
                **group,
                "seed_count": len(seed_summaries),
                "candidate": candidate_summary,
                "MAE_distribution": distribution_summary(mae_values),
                "catastrophic_miss_distribution": distribution_summary(miss_values),
                "candidate_MAE_percentile": candidate_percentile(mae_values, candidate_summary["MAE"]),
                "candidate_catastrophic_miss_percentile": candidate_percentile(miss_values, candidate_summary["catastrophic_miss_rate"]),
            }
        )
    overall_seed_summaries = seed_summaries_for_group(random_rows, {"group_type": "overall", "group_id": "overall"})
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "random_baseline_distribution",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "primary_reporting": "adapter_stratified",
        "comparison_candidate_design_id": candidate_id,
        "candidate_policy_object": config["settings"]["candidate_policy_id"],
        "random_baseline_id": config["settings"]["random_baseline_id"],
        "seed_start": int(config["settings"]["random_seed_start"]),
        "seed_count": int(config["settings"]["random_seed_count"]),
        "metric_lower_is_better": ["MAE", "catastrophic_miss_rate"],
        "score_join_policy": "same retrospective analysis universe and committed score-table join policy as phase1_retrospective_predictive_signal",
        "seed_summaries_overall": overall_seed_summaries,
        "group_distributions": group_distributions,
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "random_baseline_distribution"), payload)
    write_random_baseline_report(config, payload)
    write_process_report(
        config,
        "Step 2 - Many-Seed Random Baseline Distribution",
        [rel(output_path(config, "random_baseline_distribution")), rel(report_path(config, "random_baseline_distribution"))],
        ["Random baseline uses deterministic seeds and the same retrospective score-join policy; adapter-level reporting remains primary."],
    )
    return payload


def write_random_baseline_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "group": f"{row['group_type']}:{row['group_id']}",
            "candidate_MAE": row["candidate"]["MAE"],
            "random_median_MAE": row["MAE_distribution"]["median"],
            "random_p05_MAE": row["MAE_distribution"]["p05"],
            "random_p95_MAE": row["MAE_distribution"]["p95"],
            "beats_share": row["candidate_MAE_percentile"]["beats_random_share"],
            "miss_beats_share": row["candidate_catastrophic_miss_percentile"]["beats_random_share"],
        }
        for row in payload["group_distributions"]
    ]
    lines = [
        "# Proposal Evidence Package Random Baseline Distribution",
        "",
        "What happened: generated a deterministic many-seed same-budget random baseline distribution from the existing retrospective universe and committed score tables.",
        "",
        "Why it matters: the candidate is compared against a distribution, not only the earlier five-seed random summary.",
        "",
        "Action suggested next: use this as traction evidence and as M4 input; it does not establish predictive validity.",
        "",
        f"- Seed count: `{payload['seed_count']}`.",
        f"- Seed start: `{payload['seed_start']}`.",
        f"- Candidate design used for score comparison: `{payload['comparison_candidate_design_id']}`.",
        f"- Candidate policy object for proposal wording: `{payload['candidate_policy_object']}`.",
        "",
        *markdown_table(rows, [("group", "Group"), ("candidate_MAE", "Candidate MAE"), ("random_median_MAE", "Random median MAE"), ("random_p05_MAE", "Random p05 MAE"), ("random_p95_MAE", "Random p95 MAE"), ("beats_share", "Candidate beats/random-ties share %"), ("miss_beats_share", "Miss-rate beats/random-ties share %")]),
        "",
        "Boundary:",
        "- Lower MAE and catastrophic miss rate are better.",
        "- Percentiles are descriptive retrospective traction only.",
        "- No paid calls or external review calls were made.",
    ]
    write_text(report_path(config, "random_baseline_distribution"), "\n".join(lines))


def load_random_distribution(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "random_baseline_distribution")
    if path.exists():
        return read_json(path)
    return build_random_baseline_distribution(config["_path"])


def baseline_summary_for_group(config: dict[str, Any], baseline_id: str, group: dict[str, str]) -> dict[str, Any]:
    return summarize_rows(filter_group(metric_rows_for_design(config, baseline_id), group))


def paired_slice_diagnostics(config: dict[str, Any], candidate_id: str, baseline_id: str, group: dict[str, str]) -> dict[str, Any]:
    candidate = filter_group(metric_rows_for_design(config, candidate_id), group)
    baseline = filter_group(metric_rows_for_design(config, baseline_id), group)
    baseline_by_key = {(row["adapter_id"], row["window_id"], row["repo"]): row for row in baseline if row.get("absolute_gap") is not None}
    deltas = []
    for row in candidate:
        if row.get("absolute_gap") is None:
            continue
        baseline_row = baseline_by_key.get((row["adapter_id"], row["window_id"], row["repo"]))
        if not baseline_row:
            continue
        deltas.append(float(row["absolute_gap"]) - float(baseline_row["absolute_gap"]))
    return {
        "overlap_slice_count": len(deltas),
        "improved_slice_count": sum(1 for value in deltas if value < 0),
        "worsened_slice_count": sum(1 for value in deltas if value > 0),
        "tied_slice_count": sum(1 for value in deltas if value == 0),
    }


def relation(delta: float | None) -> str:
    if delta is None:
        return "insufficient_support"
    if delta < 0:
        return "candidate_better"
    if delta > 0:
        return "candidate_worse"
    return "tied"


def build_baseline_envelope(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    random_payload = load_random_distribution(config)
    random_by_group = {(row["group_type"], row["group_id"]): row for row in random_payload["group_distributions"]}
    candidate_id = str(config["settings"]["candidate_design_id"])
    groups = group_specs(metric_rows_for_design(config, candidate_id))
    rows: list[dict[str, Any]] = []
    for group in groups:
        candidate = summarize_rows(filter_group(metric_rows_for_design(config, candidate_id), group))
        baselines = []
        for baseline_id in config["settings"]["deterministic_baselines"]:
            summary = baseline_summary_for_group(config, str(baseline_id), group)
            baselines.append(
                {
                    "baseline_id": baseline_id,
                    "baseline_type": "deterministic_simple",
                    **summary,
                    "paired_slice_diagnostics": paired_slice_diagnostics(config, candidate_id, str(baseline_id), group),
                }
            )
        random_group = random_by_group[(group["group_type"], group["group_id"])]
        baselines.append(
            {
                "baseline_id": config["settings"]["random_baseline_id"],
                "baseline_type": "many_seed_random_distribution_median",
                "slice_count": random_group["MAE_distribution"]["count"],
                "MAE": random_group["MAE_distribution"][str(config["settings"]["random_envelope_statistic"])],
                "RMSE": None,
                "mean_signed_error": None,
                "catastrophic_miss_rate": random_group["catastrophic_miss_distribution"][str(config["settings"]["random_envelope_statistic"])],
                "non_scoreable_count": None,
                "paired_slice_diagnostics": None,
            }
        )
        comparable = [row for row in baselines if row["MAE"] is not None]
        best = min(comparable, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"] if row["catastrophic_miss_rate"] is not None else 999, row["baseline_id"])) if comparable else None
        delta = round_float(candidate["MAE"] - best["MAE"]) if best and candidate["MAE"] is not None else None
        rows.append(
            {
                **group,
                "candidate": candidate,
                "baselines": baselines,
                "best_baseline": best,
                "candidate_delta_vs_best_baseline_MAE": delta,
                "candidate_relation_to_best_baseline": relation(delta),
                "evidence_label": "proposal_traction" if delta is not None and delta < 0 else ("diagnostic_negative_evidence" if delta is not None and delta > 0 else "insufficient_support"),
            }
        )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_envelope",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "primary_reporting": "adapter_stratified",
        "secondary_summary": "overall_equal_mix",
        "candidate_design_id": candidate_id,
        "candidate_policy_object": config["settings"]["candidate_policy_id"],
        "baseline_ids": list(config["settings"]["deterministic_baselines"]) + [config["settings"]["random_baseline_id"]],
        "random_baseline_statistic_for_envelope": config["settings"]["random_envelope_statistic"],
        "rows": rows,
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "baseline_envelope"), payload)
    write_baseline_envelope_report(config, payload)
    write_process_report(
        config,
        "Step 2 - Baseline Envelope",
        [rel(output_path(config, "baseline_envelope")), rel(report_path(config, "baseline_envelope"))],
        ["Envelope compares the candidate to deterministic simple baselines and the many-seed random median; no M4 success threshold is set."],
    )
    return payload


def write_baseline_envelope_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "group": f"{row['group_type']}:{row['group_id']}",
            "candidate_MAE": row["candidate"]["MAE"],
            "best_baseline": row["best_baseline"]["baseline_id"] if row["best_baseline"] else "",
            "best_MAE": row["best_baseline"]["MAE"] if row["best_baseline"] else "",
            "delta": row["candidate_delta_vs_best_baseline_MAE"],
            "relation": row["candidate_relation_to_best_baseline"],
            "label": row["evidence_label"],
        }
        for row in payload["rows"]
    ]
    lines = [
        "# Proposal Evidence Package Baseline Envelope",
        "",
        "What happened: compared the candidate against the best available simple comparator overall, by adapter, by repo, and by window.",
        "",
        "Why it matters: M4 can harden success gates using slice-level baseline evidence rather than a single aggregate.",
        "",
        "Action suggested next: keep adapter-level rows primary and treat pooled rows as secondary diagnostics.",
        "",
        *markdown_table(rows, [("group", "Group"), ("candidate_MAE", "Candidate MAE"), ("best_baseline", "Best baseline"), ("best_MAE", "Best baseline MAE"), ("delta", "Candidate - baseline MAE"), ("relation", "Relation"), ("label", "Evidence label")]),
        "",
        "Boundary:",
        "- This envelope does not set a final success threshold.",
        "- The random comparator uses the median seed summary for the envelope; the full distribution is reported separately.",
    ]
    write_text(report_path(config, "baseline_envelope"), "\n".join(lines))


def load_baseline_envelope(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "baseline_envelope")
    if path.exists():
        return read_json(path)
    return build_baseline_envelope(config["_path"])


def build_coverage_ablation(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    envelope = load_baseline_envelope(config)
    overall = next(row for row in envelope["rows"] if row["group_type"] == "overall")
    candidate = overall["candidate"]
    ablation_rows = [
        {
            "component": "coverage_constrained_unweighted",
            "role": "candidate_score_comparison",
            "MAE": candidate["MAE"],
            "catastrophic_miss_rate": candidate["catastrophic_miss_rate"],
            "delta_vs_candidate_MAE": 0.0,
            "interpretation": "reference candidate in the retrospective score-join artifacts",
        }
    ]
    for baseline in overall["baselines"]:
        delta = round_float(candidate["MAE"] - baseline["MAE"]) if candidate["MAE"] is not None and baseline["MAE"] is not None else None
        ablation_rows.append(
            {
                "component": baseline["baseline_id"],
                "role": baseline["baseline_type"],
                "MAE": baseline["MAE"],
                "catastrophic_miss_rate": baseline["catastrophic_miss_rate"],
                "delta_vs_candidate_MAE": delta,
                "interpretation": relation(delta),
            }
        )
    adapter_rows = [
        {
            "adapter": row["group_id"],
            "candidate_MAE": row["candidate"]["MAE"],
            "best_baseline": row["best_baseline"]["baseline_id"] if row["best_baseline"] else None,
            "best_baseline_MAE": row["best_baseline"]["MAE"] if row["best_baseline"] else None,
            "delta": row["candidate_delta_vs_best_baseline_MAE"],
            "relation": row["candidate_relation_to_best_baseline"],
        }
        for row in envelope["rows"]
        if row["group_type"] == "adapter"
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "coverage_ablation",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "candidate_design_id": config["settings"]["candidate_design_id"],
        "candidate_policy_object": config["settings"]["candidate_policy_id"],
        "clean_decomposition_possible": False,
        "ablation_rows": ablation_rows,
        "adapter_diagnostics": adapter_rows,
        "identifiability": {
            "coverage_objective_contribution": "partially_identified_by_candidate_delta_against_simple_baselines",
            "unweighted_same_budget_contribution": "not_cleanly_identifiable_without a factorial selector family using the same outcome windows",
            "fallback_composite_policy_contribution": "not outcome-identifiable from current artifacts; factual fallback share is reported separately",
            "temporal_recency_contribution": "temporal_recent_baseline remains a serious simple comparator and is the best deterministic simple baseline overall",
        },
        "limitation": "Current artifacts compare whole selector designs. They do not isolate coverage, unweighted budgeting, fallback, and temporal recency as orthogonal randomized factors.",
        "claim_label": "traction_only",
        "predictive_validity_established": False,
        "paid_validation_authorized": False,
    }
    write_json(output_path(config, "coverage_ablation"), payload)
    write_coverage_ablation_report(config, payload)
    write_process_report(
        config,
        "Step 2 - Coverage Objective Ablation",
        [rel(output_path(config, "coverage_ablation")), rel(report_path(config, "coverage_ablation"))],
        ["Coverage contribution is reported as a limited design-level ablation; clean factorial decomposition is explicitly not claimed."],
    )
    return payload


def write_coverage_ablation_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Proposal Evidence Package Coverage Ablation",
        "",
        "What happened: compared the coverage candidate against unweighted, stratified, temporal, and many-seed random baselines.",
        "",
        "Why it matters: this tests whether the coverage objective adds traction beyond simple heuristics, while preserving limitations.",
        "",
        "Action suggested next: M4 should decide whether the limited ablation is enough for candidate-policy hardening or whether a factorial selector family is needed later.",
        "",
        *markdown_table(payload["ablation_rows"], [("component", "Component"), ("role", "Role"), ("MAE", "MAE"), ("catastrophic_miss_rate", "Miss rate"), ("delta_vs_candidate_MAE", "Candidate - comparator MAE"), ("interpretation", "Interpretation")]),
        "",
        "Adapter diagnostics:",
        *markdown_table(payload["adapter_diagnostics"], [("adapter", "Adapter"), ("candidate_MAE", "Candidate MAE"), ("best_baseline", "Best baseline"), ("best_baseline_MAE", "Best baseline MAE"), ("delta", "Delta"), ("relation", "Relation")]),
        "",
        "Limitation:",
        "",
        payload["limitation"],
    ]
    write_text(report_path(config, "coverage_ablation"), "\n".join(lines))


def load_coverage_ablation(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "coverage_ablation")
    if path.exists():
        return read_json(path)
    return build_coverage_ablation(config["_path"])


def summarize_repo_subset(config: dict[str, Any], repos: set[str]) -> dict[str, Any]:
    candidate_id = str(config["settings"]["candidate_design_id"])
    candidate = summarize_rows([row for row in metric_rows_for_design(config, candidate_id) if row["repo"] in repos])
    best = None
    for baseline_id in config["settings"]["deterministic_baselines"]:
        summary = summarize_rows([row for row in metric_rows_for_design(config, str(baseline_id)) if row["repo"] in repos])
        if summary["MAE"] is None:
            continue
        item = {"baseline_id": baseline_id, **summary}
        if best is None or (item["MAE"], item["catastrophic_miss_rate"], item["baseline_id"]) < (best["MAE"], best["catastrophic_miss_rate"], best["baseline_id"]):
            best = item
    delta = round_float(candidate["MAE"] - best["MAE"]) if best and candidate["MAE"] is not None else None
    return {"candidate": candidate, "best_deterministic_baseline": best, "candidate_delta_vs_best_deterministic_MAE": delta, "relation": relation(delta)}


def build_fallback_share(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    manifest = read_json(input_path(config, "candidate_policy_selection_manifest"))
    selection_rows = [row for row in manifest["selection_rows"] if row.get("task_id")]
    fallback_by_repo = manifest["fallback_by_repo"]
    fallback_repos = {repo for repo, status in fallback_by_repo.items() if status["fallback_applied"]}
    selected_by_repo = Counter(str(row["repo"]) for row in selection_rows)
    fallback_slots = []
    fallback_counts_by_repo: dict[str, int] = {}
    for row in selection_rows:
        repo = str(row["repo"])
        status = fallback_by_repo[repo]
        fallback_applied = bool(status["fallback_applied"])
        if fallback_applied:
            fallback_counts_by_repo[repo] = fallback_counts_by_repo.get(repo, 0) + 1
        fallback_slots.append(
            {
                "repo": repo,
                "selection_order": row["selection_order"],
                "task_id": row["task_id"],
                "fallback_selected": fallback_applied,
                "fallback_reason": status["fallback_reason"],
                "fallback_design": status["fallback_design"],
            }
        )
    for repo in selected_by_repo:
        fallback_counts_by_repo.setdefault(repo, 0)
    total_selected = sum(selected_by_repo.values())
    total_fallback = sum(fallback_counts_by_repo.values())
    coverage_gap_counts = Counter((row["repo"], row["feature"]) for row in manifest["coverage_gaps"])
    coverage_gap_rows = [
        {"repo": repo, "feature": feature, "gap_value_count": count}
        for (repo, feature), count in sorted(coverage_gap_counts.items())
    ]
    sensitivity_repos = set(selected_by_repo)
    sensitivity = {
        "including_all_repos": summarize_repo_subset(config, sensitivity_repos),
        "excluding_fallback_repos": summarize_repo_subset(config, sensitivity_repos - fallback_repos) if fallback_repos else None,
        "fallback_repos_only": summarize_repo_subset(config, fallback_repos) if fallback_repos else None,
        "scope_note": "Diagnostic only: retrospective score comparison uses the comparable coverage_constrained_unweighted design, while fallback facts come from the frozen v1 policy manifest.",
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "fallback_share",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "candidate_policy_object": config["settings"]["candidate_policy_id"],
        "policy_manifest_id": manifest["policy_id"],
        "selected_count_by_repo": dict(sorted(selected_by_repo.items())),
        "fallback_selected_count_by_repo": dict(sorted(fallback_counts_by_repo.items())),
        "fallback_share_overall": round_float(total_fallback / total_selected if total_selected else None),
        "fallback_share_by_repo": {
            repo: round_float(fallback_counts_by_repo.get(repo, 0) / count if count else None)
            for repo, count in sorted(selected_by_repo.items())
        },
        "fallback_task_slots": fallback_slots,
        "fallback_by_repo": fallback_by_repo,
        "coverage_gap_counts_by_repo_feature": coverage_gap_rows,
        "including_excluding_fallback_repo_sensitivity": sensitivity,
        "fallback_threshold_set_by_M3": False,
        "claim_label": "needs_M4_protocol_decision",
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "fallback_share"), payload)
    write_fallback_share_report(config, payload)
    write_process_report(
        config,
        "Step 3 - Fallback Share Accounting",
        [rel(output_path(config, "fallback_share")), rel(report_path(config, "fallback_share"))],
        ["Fallback behavior is quantified by repo and task slot; no fallback threshold is set."],
    )
    return payload


def write_fallback_share_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    repo_rows = [
        {
            "repo": repo,
            "selected": payload["selected_count_by_repo"][repo],
            "fallback_selected": payload["fallback_selected_count_by_repo"].get(repo, 0),
            "fallback_share": payload["fallback_share_by_repo"][repo],
            "fallback_reason": payload["fallback_by_repo"][repo]["fallback_reason"],
        }
        for repo in payload["selected_count_by_repo"]
    ]
    sensitivity = payload["including_excluding_fallback_repo_sensitivity"]
    sensitivity_rows = []
    for label in ["including_all_repos", "excluding_fallback_repos", "fallback_repos_only"]:
        item = sensitivity.get(label)
        if not item:
            continue
        best = item["best_deterministic_baseline"]
        sensitivity_rows.append(
            {
                "slice": label,
                "candidate_MAE": item["candidate"]["MAE"],
                "best_baseline": best["baseline_id"] if best else "",
                "best_MAE": best["MAE"] if best else "",
                "delta": item["candidate_delta_vs_best_deterministic_MAE"],
                "relation": item["relation"],
            }
        )
    lines = [
        "# Proposal Evidence Package Fallback Share",
        "",
        "What happened: quantified labeled fallback behavior in the frozen candidate policy manifest.",
        "",
        "Why it matters: M4 needs factual fallback share before it sets any fallback threshold or claim-narrowing rule.",
        "",
        "Action suggested next: treat the current candidate as composite unless M4 repairs, thresholds, or narrows the fallback claim.",
        "",
        f"- Overall fallback share: `{payload['fallback_share_overall']}`.",
        "",
        *markdown_table(repo_rows, [("repo", "Repo"), ("selected", "Selected"), ("fallback_selected", "Fallback-selected"), ("fallback_share", "Fallback share"), ("fallback_reason", "Fallback reason")]),
        "",
        "Coverage gaps by repo/feature:",
        *markdown_table(payload["coverage_gap_counts_by_repo_feature"], [("repo", "Repo"), ("feature", "Feature"), ("gap_value_count", "Gap value count")]),
        "",
        "Diagnostic sensitivity:",
        *markdown_table(sensitivity_rows, [("slice", "Slice"), ("candidate_MAE", "Candidate MAE"), ("best_baseline", "Best deterministic baseline"), ("best_MAE", "Best MAE"), ("delta", "Delta"), ("relation", "Relation")]),
        "",
        "Boundary:",
        "- M3 does not set a fallback threshold.",
        "- Sensitivity is diagnostic and does not change the frozen candidate policy.",
    ]
    write_text(report_path(config, "fallback_share"), "\n".join(lines))


def load_fallback_share(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "fallback_share")
    if path.exists():
        return read_json(path)
    return build_fallback_share(config["_path"])


def build_source_supply_status(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    source_audit = read_json(input_path(config, "three_repo_source_quality_audit"))
    click = read_json(input_path(config, "click_repair_decision"))
    supply = read_json(input_path(config, "task_supply_v2_source_bakeoff_decision"))
    fallback = load_fallback_share(config)
    repo_rows = []
    for repo in ["attrs", "boltons", "click"]:
        source_context_classes = source_audit["source_context_class_counts_by_repo"].get(repo, {})
        if repo == "click":
            source_context_classes = {
                "public_context_repaired": click["public_context_repaired"],
                "pre_repair_source_context_classes": source_context_classes,
            }
        repo_rows.append(
            {
                "repo": repo,
                "current_source_quality_status": "accepted_for_paid_package" if source_audit["audit_status_counts"].get("accepted_for_paid_package") else "unknown",
                "source_context_classes": source_context_classes,
                "statement_provenance": source_audit["statement_provenance_counts_by_repo"].get(repo, {}),
                "candidate_policy_fallback_share": fallback["fallback_share_by_repo"].get(repo),
                "proposal_use": "source-quality narrative support",
                "limitation": {
                    "attrs": "No new source-supply expansion in M3; rely on existing certified pilot artifacts.",
                    "boltons": "Source package was accepted, but candidate policy falls back because feature support is insufficient.",
                    "click": "Click source context is repaired for the 30 frozen tasks, but outcomes are not rerun or rewritten.",
                }[repo],
            }
        )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "source_supply_status",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "repo_rows": repo_rows,
        "click_repair": {
            "click_tasks_in_scope": click["click_tasks_in_scope"],
            "public_context_repaired": click["public_context_repaired"],
            "still_title_only_minor_risk": click["still_title_only_minor_risk"],
            "paid_llm_calls": click["paid_llm_calls"],
            "paid_acut_solver_cells": click["paid_acut_solver_cells"],
            "claim_boundary": click["click_claim_boundary"],
        },
        "task_supply_v2": {
            "primary_decision_label": supply["primary_decision_label"],
            "paid_ready": supply["paid_ready"],
            "recommended_next_action_category": supply["recommended_next_action_category"],
            "source_mixing_policy_status": supply["source_mixing_policy"]["policy_status"],
            "short_term_scope": "Layer 1 supply infrastructure only; no broad task-generator expansion in M3 proposal scope.",
        },
        "claim_label": "supported_for_proposal_with_caveats",
        "predictive_validity_established": False,
        "paid_validation_authorized": False,
    }
    write_json(output_path(config, "source_supply_status"), payload)
    write_source_supply_status_report(config, payload)
    write_process_report(
        config,
        "Step 3 - Source Supply Status",
        [rel(output_path(config, "source_supply_status")), rel(report_path(config, "source_supply_status"))],
        ["Source-supply status is concise and keeps Task Supply v2 inside Layer 1 infrastructure."],
    )
    return payload


def write_source_supply_status_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "repo": row["repo"],
            "status": row["current_source_quality_status"],
            "fallback_share": row["candidate_policy_fallback_share"],
            "limitation": row["limitation"],
        }
        for row in payload["repo_rows"]
    ]
    lines = [
        "# Proposal Evidence Package Source Supply Status",
        "",
        "What happened: summarized current source-quality and source-supply status for attrs, boltons, and click.",
        "",
        "Why it matters: the proposal can separate source infrastructure from the core benchmark-compiler claim.",
        "",
        "Action suggested next: use the status for proposal wording, while leaving broad generator work out of short-term scope.",
        "",
        *markdown_table(rows, [("repo", "Repo"), ("status", "Status"), ("fallback_share", "Fallback share"), ("limitation", "Limitation")]),
        "",
        "Click repair:",
        f"- Public-context repaired: `{payload['click_repair']['public_context_repaired']}` of `{payload['click_repair']['click_tasks_in_scope']}`.",
        f"- Paid LLM calls: `{payload['click_repair']['paid_llm_calls']}`.",
        f"- Paid ACUT cells: `{payload['click_repair']['paid_acut_solver_cells']}`.",
        "",
        "Task Supply v2:",
        f"- Decision: `{payload['task_supply_v2']['primary_decision_label']}`.",
        f"- Paid ready: `{payload['task_supply_v2']['paid_ready']}`.",
        f"- Scope: {payload['task_supply_v2']['short_term_scope']}",
    ]
    write_text(report_path(config, "source_supply_status"), "\n".join(lines))


def load_source_supply_status(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "source_supply_status")
    if path.exists():
        return read_json(path)
    return build_source_supply_status(config["_path"])


def build_report_evidence_index(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = [{**row, "exists": repo_path(row["report"]).exists(), "digest": digest_file(row["report"])} for row in REPORT_INDEX_ROWS]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "report_evidence_index",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "rows": rows,
        "main_text_yes_count": sum(1 for row in rows if row["main_text"] == "yes"),
        "main_text_no_count": sum(1 for row in rows if row["main_text"] == "no"),
        "claim_label": "supported_for_proposal_index",
    }
    write_json(output_path(config, "report_evidence_index"), payload)
    write_report_evidence_index_report(config, payload)
    write_process_report(
        config,
        "Step 3 - Report Evidence Index",
        [rel(output_path(config, "report_evidence_index")), rel(report_path(config, "report_evidence_index"))],
        ["Evidence index is compact and proposal-facing."],
    )
    return payload


def write_report_evidence_index_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Proposal Evidence Package Report Evidence Index",
        "",
        "What happened: created an appendix-friendly index of canonical Phase 1 reports.",
        "",
        "Why it matters: reviewer-facing claims can point to report evidence without turning the proposal into a chronological ledger.",
        "",
        "Action suggested next: M5 can integrate selected rows into the proposal appendix.",
        "",
        *markdown_table(payload["rows"], [("report", "Report"), ("evidence_type", "Evidence type"), ("claim_function", "Claim function"), ("key_numeric_result_or_status", "Key result/status"), ("limitation", "Limitation"), ("main_text", "Main text?")]),
    ]
    write_text(report_path(config, "report_evidence_index"), "\n".join(lines))


def load_report_evidence_index(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "report_evidence_index")
    if path.exists():
        return read_json(path)
    return build_report_evidence_index(config["_path"])


def build_preliminary_evidence_summary(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    random_payload = load_random_distribution(config)
    envelope = load_baseline_envelope(config)
    fallback = load_fallback_share(config)
    source = load_source_supply_status(config)
    overall_random = next(row for row in random_payload["group_distributions"] if row["group_type"] == "overall")
    overall_envelope = next(row for row in envelope["rows"] if row["group_type"] == "overall")
    adapter_rows = [row for row in envelope["rows"] if row["group_type"] == "adapter"]
    adapter_note = "; ".join(f"{row['group_id']} {row['candidate_relation_to_best_baseline']} (delta {row['candidate_delta_vs_best_baseline_MAE']})" for row in adapter_rows)
    rows = [
        {
            "reader_question": "Is the target-repository benchmark-construction problem real?",
            "claim_strength": "supported_for_proposal",
            "key_numeric_result_or_status": "Old weighted pilot gaps were attrs 0.3148 and boltons 0.7481; simple same-budget baselines were 0.25 and 0.125.",
            "canonical_report": "phase1_weighted_design_paid_pilot_decision.md; phase1_local_algorithm_bakeoff_decision.md",
            "limitation": "Negative evidence for naive weighting, not a positive predictive-validity result.",
            "proposal_use": "Use to show benchmark construction choices materially affect estimates.",
        },
        {
            "reader_question": "Did the naive weighted design fail in a diagnosable way?",
            "claim_strength": "diagnostic_negative",
            "key_numeric_result_or_status": "Local bakeoff kept repo_stratified/simple designs as conservative baselines and did not promote old weighted target-profile matching.",
            "canonical_report": "phase1_local_algorithm_bakeoff_decision.md",
            "limitation": "Does not by itself identify the next successful compiler.",
            "proposal_use": "Use as a design-learning result and negative control.",
        },
        {
            "reader_question": "Is workspace ACUT protocol and artifact hygiene technically tractable?",
            "claim_strength": "supported_for_proposal",
            "key_numeric_result_or_status": "Three-repo paid pilot completed 120/120 cells with scoreability 1.0, endpoint compliance pass, and no raw logs/prompts/workspaces committed.",
            "canonical_report": "phase1_three_repo_paid_validation_decision.md",
            "limitation": "Exploratory pilot evidence only.",
            "proposal_use": "Use to justify feasibility of clean benchmark-side execution and accounting.",
        },
        {
            "reader_question": "Is the click source-quality caveat repaired enough for the source-quality story?",
            "claim_strength": "supported_for_proposal",
            "key_numeric_result_or_status": f"Click repair: {source['click_repair']['public_context_repaired']}/{source['click_repair']['click_tasks_in_scope']} public-context repaired; paid LLM calls 0; paid ACUT cells 0.",
            "canonical_report": "phase1_click_llm_source_context_repair_decision.md",
            "limitation": "Historical paid outcomes were not rewritten or rerun.",
            "proposal_use": "Use click as clean enough for source-quality narrative support.",
        },
        {
            "reader_question": "Should adapter-level reporting be primary?",
            "claim_strength": "supported_for_proposal",
            "key_numeric_result_or_status": adapter_note,
            "canonical_report": "phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md; phase1_retrospective_predictive_signal_adapter_metrics.md",
            "limitation": "Does not resolve the final M4 adapter estimand.",
            "proposal_use": "Use adapter-stratified tables first; keep pooled summaries secondary.",
        },
        {
            "reader_question": "Is the retrospective signal directional but underpowered?",
            "claim_strength": "traction_only",
            "key_numeric_result_or_status": f"Candidate MAE {overall_envelope['candidate']['MAE']} vs best envelope baseline {overall_envelope['best_baseline']['baseline_id']} MAE {overall_envelope['best_baseline']['MAE']}; candidate beats/random-ties share {overall_random['candidate_MAE_percentile']['beats_random_share']}%.",
            "canonical_report": "phase1_proposal_evidence_package_baseline_envelope.md; phase1_proposal_evidence_package_random_baseline_distribution.md",
            "limitation": "Pseudo-future replay with sparse support; not predictive validity.",
            "proposal_use": "Use as route-finding evidence for M4 protocol hardening.",
        },
        {
            "reader_question": "Is the candidate policy composite because of labeled fallback?",
            "claim_strength": "needs_M4_protocol_decision",
            "key_numeric_result_or_status": f"Fallback share {fallback['fallback_share_overall']} overall; boltons fallback share {fallback['fallback_share_by_repo'].get('boltons')}; no M3 threshold set.",
            "canonical_report": "phase1_candidate_policy_validation_protocol_selection_manifest.md; phase1_proposal_evidence_package_fallback_share.md",
            "limitation": "M4 must set threshold, inclusion/exclusion rule, or repair path.",
            "proposal_use": "Use the full name coverage_constrained_unweighted_v1_with_labeled_fallbacks.",
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preliminary_evidence_summary",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "rows": rows,
        "claim_labels_allowed": ["supported_for_proposal", "traction_only", "diagnostic_negative", "needs_M4_protocol_decision", "deferred", "prohibited"],
        "predictive_validity_established": False,
        "paid_validation_authorized": False,
    }
    write_json(output_path(config, "preliminary_evidence_summary"), payload)
    write_preliminary_evidence_summary_report(config, payload)
    write_proposal_evidence_package_doc(config, payload)
    write_process_report(
        config,
        "Step 4 - Proposal-Facing Evidence Summary",
        [
            rel(output_path(config, "preliminary_evidence_summary")),
            rel(report_path(config, "preliminary_evidence_summary")),
            rel(doc_path(config, "proposal_evidence_package")),
        ],
        ["One-page summary answers reader questions and keeps every current result below predictive-validity strength."],
    )
    return payload


def write_preliminary_evidence_summary_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Proposal Evidence Package Preliminary Evidence Summary",
        "",
        "What happened: consolidated the M3 evidence package into a one-page reader-facing table.",
        "",
        "Why it matters: the proposal can answer approval questions without overstating current evidence.",
        "",
        "Action suggested next: M4 should harden validation and candidate-policy gates using this evidence.",
        "",
        *markdown_table(payload["rows"], [("reader_question", "Reader question"), ("claim_strength", "Claim strength"), ("key_numeric_result_or_status", "Key result/status"), ("canonical_report", "Canonical report"), ("limitation", "Limitation"), ("proposal_use", "Proposal use")]),
    ]
    write_text(report_path(config, "preliminary_evidence_summary"), "\n".join(lines))


def write_proposal_evidence_package_doc(config: dict[str, Any], summary: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Proposal Evidence Package",
        "",
        "Status: M3 no-paid evidence package, 2026-06-01.",
        "",
        "This document fills the M3 evidence-producing proposal placeholders. It does not claim predictive validity and does not authorize paid validation.",
        "",
        "## One-Page Evidence Summary",
        "",
        *markdown_table(summary["rows"], [("reader_question", "Reader question"), ("claim_strength", "Claim strength"), ("key_numeric_result_or_status", "Key result/status"), ("canonical_report", "Canonical report"), ("limitation", "Limitation"), ("proposal_use", "Proposal use")]),
        "",
        "## Detailed M3 Outputs",
        "",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`",
        "- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_report_evidence_index.md`",
        "",
        "## Boundary",
        "",
        "- Predictive validity established: `false`.",
        "- Paid validation authorized: `false`.",
        "- Paid ACUT solver cells run in M3: `0`.",
        "- Paid LLM calls run in M3: `0`.",
        "- External reviewer calls run in M3: `0`.",
        "- Public citation browsing run in M3: `false`.",
        "",
        "## Remaining Handoff",
        "",
        "M4 should use this package to harden the validation protocol and candidate-policy gates: fallback threshold, adapter estimand, invalid-cell rule, joint success gate, support thresholds, and power/budget note. User decisions remain needed before M6 approval artifact work or any budget-bearing paid-validation discussion.",
    ]
    write_text(doc_path(config, "proposal_evidence_package"), "\n".join(lines))


def load_preliminary_evidence_summary(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "preliminary_evidence_summary")
    if path.exists():
        return read_json(path)
    return build_preliminary_evidence_summary(config["_path"])


def build_decision(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    summary = load_preliminary_evidence_summary(config)
    random_payload = load_random_distribution(config)
    envelope = load_baseline_envelope(config)
    ablation = load_coverage_ablation(config)
    fallback = load_fallback_share(config)
    source = load_source_supply_status(config)
    index = load_report_evidence_index(config)
    placeholders = {
        "[NEEDS TABLE: one-page preliminary evidence summary]": "filled",
        "[NEEDS RESULT: many-seed random baseline distribution and candidate percentile]": "filled",
        "[NEEDS RESULT: baseline-envelope comparison]": "filled",
        "[NEEDS RESULT: coverage objective ablation]": "partially_filled_with_identifiability_limitation",
        "[NEEDS APPENDIX TABLE: report evidence index]": "filled",
        "fallback-share accounting and boltons fallback wording": "filled_for_M3_no_threshold_set",
        "concise source-supply status": "filled",
        "adapter/repo fragility summary": "filled_in_envelope_and_summary",
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": "proposal_evidence_package_complete",
        "what_happened": "The no-paid evidence package filled or explicitly limited the M3-owned P0/P1 proposal placeholders.",
        "why_it_matters": "M4 can harden validation and candidate-policy gates using concrete baseline, ablation, fallback, and source-support evidence instead of assumptions.",
        "action_suggested_next": "Proceed to M4 validation/candidate-policy hardening unless the user chooses to resolve M6 resource and format decisions first.",
        "m3_placeholder_status": placeholders,
        "m4_should_proceed_next": True,
        "user_decisions_needed_before_next_runbook": False,
        "user_decisions_needed_before_M6_or_budget_discussion": True,
        "random_seed_count": random_payload["seed_count"],
        "overall_candidate_vs_best_baseline": next(row for row in envelope["rows"] if row["group_type"] == "overall"),
        "coverage_ablation_clean_decomposition_possible": ablation["clean_decomposition_possible"],
        "fallback_share_overall": fallback["fallback_share_overall"],
        "click_public_context_repaired": source["click_repair"]["public_context_repaired"],
        "report_index_rows": len(index["rows"]),
        "preliminary_summary_rows": len(summary["rows"]),
        "paid_ACUT_cells": 0,
        "paid_LLM_calls": 0,
        "external_reviewer_calls": 0,
        "public_citation_browsing": False,
        "predictive_validity_established": False,
        "paid_validation_authorized": False,
        "score_tables_changed": False,
        "selected_task_ids_or_split_labels_changed": False,
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload)
    write_process_report(
        config,
        "Step 6 - Verification And Closeout",
        [rel(output_path(config, "decision")), rel(report_path(config, "decision"))],
        ["Closeout label is proposal_evidence_package_complete; coverage ablation limitations are recorded but do not block M3 completion."],
    )
    return payload


def write_decision_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [{"placeholder": key, "status": value} for key, value in payload["m3_placeholder_status"].items()]
    lines = [
        "# Proposal Evidence Package Decision",
        "",
        f"Decision label: `{payload['decision_label']}`.",
        "",
        f"What happened: {payload['what_happened']}",
        "",
        f"Why it matters: {payload['why_it_matters']}",
        "",
        f"Action suggested next: {payload['action_suggested_next']}",
        "",
        "M3 placeholder status:",
        "",
        *markdown_table(rows, [("placeholder", "Placeholder/supporting item"), ("status", "Status")]),
        "",
        "Boundary:",
        f"- Paid ACUT solver cells: `{payload['paid_ACUT_cells']}`.",
        f"- Paid LLM calls: `{payload['paid_LLM_calls']}`.",
        f"- External reviewer calls: `{payload['external_reviewer_calls']}`.",
        f"- Public citation browsing: `{payload['public_citation_browsing']}`.",
        f"- Predictive validity established: `{payload['predictive_validity_established']}`.",
        f"- Paid validation authorized: `{payload['paid_validation_authorized']}`.",
        f"- Score tables changed: `{payload['score_tables_changed']}`.",
        f"- Selected task IDs or split labels changed: `{payload['selected_task_ids_or_split_labels_changed']}`.",
        "",
        "Next:",
        f"- M4 should proceed next: `{payload['m4_should_proceed_next']}`.",
        f"- User decisions needed before next runbook: `{payload['user_decisions_needed_before_next_runbook']}`.",
        f"- User decisions needed before M6 or budget-bearing paid-validation discussion: `{payload['user_decisions_needed_before_M6_or_budget_discussion']}`.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def build_all(config_path: str | Path = DEFAULT_CONFIG) -> None:
    build_preflight(config_path)
    build_random_baseline_distribution(config_path)
    build_baseline_envelope(config_path)
    build_coverage_ablation(config_path)
    build_fallback_share(config_path)
    build_source_supply_status(config_path)
    build_report_evidence_index(config_path)
    build_preliminary_evidence_summary(config_path)
    build_decision(config_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 1 proposal evidence package outputs.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--step",
        choices=["preflight", "random", "envelope", "ablation", "fallback", "source", "index", "summary", "decision", "all"],
        default="all",
    )
    args = parser.parse_args()
    step_map: dict[str, Callable[[str | Path], Any]] = {
        "preflight": build_preflight,
        "random": build_random_baseline_distribution,
        "envelope": build_baseline_envelope,
        "ablation": build_coverage_ablation,
        "fallback": build_fallback_share,
        "source": build_source_supply_status,
        "index": build_report_evidence_index,
        "summary": build_preliminary_evidence_summary,
        "decision": build_decision,
        "all": build_all,
    }
    result = step_map[args.step](args.config)
    if result is not None:
        print(json.dumps({"step": args.step, "completed": True}, sort_keys=True))


if __name__ == "__main__":
    main()
