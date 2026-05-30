from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_retrospective_predictive_signal.yaml"
SCHEMA_VERSION = "barcarolle.phase1_retrospective_predictive_signal.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_retrospective_predictive_signal_output.v1"

REPOS = ("attrs", "boltons", "click")
ADAPTERS = ("codex_workspace", "kilo_workspace")
SPLITS = ("B_eval", "H_future")
TIME_BUCKET_ORDER = {
    "legacy_2018_or_earlier": 0,
    "middle_2019_2022": 1,
    "recent_2023_or_later": 2,
    "unknown": 99,
}
FEATURE_KEYS = (
    "coarse_task_family",
    "time_bucket",
    "editable_scope_bucket",
    "source_context_type_bucket",
)
BLOCK_FEATURE_KEYS = (
    "source_quality_bucket",
    "source_context_type_bucket",
    "coarse_task_family",
    "time_bucket",
    "editable_scope_bucket",
)
REQUIRED_DESIGNS = (
    "repo_unweighted_same_budget",
    "repo_stratified_by_target_profile",
    "temporal_recent_baseline",
    "seeded_random_same_budget",
    "coverage_constrained_unweighted",
    "block_randomized_stratified",
    "block_plus_shrinkage_weighted",
    "old_weighted_target_profile",
    "completed_blocked_split_supplement",
)
SIMPLE_BASELINES = (
    "repo_stratified_by_target_profile",
    "repo_unweighted_same_budget",
    "temporal_recent_baseline",
    "seeded_random_same_budget",
)
BARCAROLLE_CANDIDATES = (
    "coverage_constrained_unweighted",
    "block_randomized_stratified",
    "block_plus_shrinkage_weighted",
    "completed_blocked_split_supplement",
)
PROMOTABLE_BARCAROLLE_CANDIDATES = (
    "coverage_constrained_unweighted",
    "block_randomized_stratified",
    "block_plus_shrinkage_weighted",
)
DIAGNOSTIC_CANDIDATES = ("completed_blocked_split_supplement",)
TERMINAL_SCOREABLE = {"verified_pass", "verified_fail"}
INVALID_TASK_ID = "attrs__v2__157"
OUTCOME_COLUMNS = {
    "submission_status",
    "terminal_status",
    "verifier_exit_code",
    "scoreable_cell",
    "agent_failure",
    "harness_error",
}


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
        raise ValueError("unexpected retrospective predictive signal config schema_version")
    config["_path"] = str(repo_path(path))
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


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


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def digest_file(path: str | Path) -> str | None:
    resolved = repo_path(path)
    if not resolved.exists():
        return None
    return "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()


def stable_int(*parts: Any) -> int:
    text = "||".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


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


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def parse_time(value: str | None) -> str:
    if not value:
        return ""
    return str(value)


def time_sort_value(row: dict[str, Any]) -> tuple[int, str]:
    return (TIME_BUCKET_ORDER.get(str(row.get("time_bucket") or "unknown"), 99), parse_time(row.get("task_time")))


def recent_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    bucket_order = TIME_BUCKET_ORDER.get(str(row.get("time_bucket") or "unknown"), 99)
    return (-bucket_order, parse_time(row.get("task_time")), str(row.get("task_id")))


def task_sort_key(row: dict[str, Any]) -> tuple[str, int, str, str]:
    return (
        str(row.get("repo") or ""),
        TIME_BUCKET_ORDER.get(str(row.get("time_bucket") or "unknown"), 99),
        parse_time(row.get("task_time")),
        str(row.get("task_id") or ""),
    )


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


def status_path(line: str) -> str:
    if line.startswith("?? "):
        text = line[3:]
    elif len(line) > 3 and line[:2].strip() and line[2] == " ":
        text = line[3:]
    elif len(line) > 3 and line[0] == " " and line[1].strip() and line[2] == " ":
        text = line[3:]
    elif len(line) > 2 and line[1] == " ":
        text = line[2:]
    elif len(line) > 2 and line[0] in "MADRCU":
        text = line[2:]
    else:
        text = line
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    return text.strip()


def expected_paths(config: dict[str, Any]) -> set[str]:
    expected = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_retrospective_predictive_signal.py"),
        rel(ROOT / "tests" / "test_phase1_retrospective_predictive_signal.py"),
    }
    expected.update(rel(path) for path in config["outputs"].values())
    expected.update(rel(path) for path in config["reports"].values())
    return expected


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_paths(config)
    known_external = "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/"
    runbook_path = rel(input_path(config, "runbook"))
    classified: dict[str, list[str]] = {
        "this_run_expected_outputs": [],
        "current_runbook_input": [],
        "known_unrelated_external_review": [],
        "preexisting_process_or_instruction_edits": [],
        "unrelated_or_requires_review": [],
    }
    for line in status_lines:
        path = status_path(line)
        if path in expected:
            classified["this_run_expected_outputs"].append(line)
        elif path == runbook_path:
            classified["current_runbook_input"].append(line)
        elif path.startswith(known_external):
            classified["known_unrelated_external_review"].append(line)
        elif path in {"AGENTS.md", "PROCESS.md"}:
            classified["preexisting_process_or_instruction_edits"].append(line)
        else:
            classified["unrelated_or_requires_review"].append(line)
    return classified


def git_tracked(path: str | Path) -> bool:
    result = command_result(["git", "ls-files", "--error-unmatch", rel(path)])
    return result["returncode"] == 0


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


def score_table_paths(config: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    three_repo_manifest = read_json(input_path(config, "three_repo_paid_score_tables_manifest"))
    for entry in three_repo_manifest.get("entries", []):
        paths.append(str(entry["score_table"]))
    supplement_manifest = read_json(input_path(config, "supplement_combined_score_tables_manifest"))
    paths.extend(str(path) for path in supplement_manifest.get("reused_result_sources", []))
    for entry in supplement_manifest.get("new_entries", []):
        paths.append(str(entry["score_table"]))
    return sorted(set(paths))


def read_score_table_coverage(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    coverage: dict[str, dict[str, Any]] = defaultdict(lambda: {"adapters": set(), "splits": set(), "score_table_count": 0})
    for path in score_table_paths(config):
        with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                task_id = str(row["task_id"])
                coverage[task_id]["adapters"].add(str(row["adapter_id"]))
                coverage[task_id]["splits"].add(str(row.get("split") or ""))
                coverage[task_id]["score_table_count"] += 1
    return {
        task_id: {
            "adapters_with_committed_rows": sorted(value["adapters"]),
            "split_labels_seen_in_score_tables": sorted(value["splits"]),
            "committed_score_table_rows": value["score_table_count"],
        }
        for task_id, value in sorted(coverage.items())
    }


def write_process_report(config: dict[str, Any], current_step: str, completed: list[str], notes: list[str] | None = None) -> None:
    lines = [
        "# Retrospective Predictive-Signal Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
    ]
    lines.extend([f"- {item}" for item in completed] or ["- None yet."])
    lines.extend(
        [
            "",
            "Boundary:",
            "- This is a no-paid retrospective analysis.",
            "- New paid ACUT solver cells run: `false`.",
            "- New paid LLM calls run: `false`.",
            "- Score tables are joined only after `phase1_retrospective_predictive_signal_selection_freeze.json` exists.",
            "- Predictive validity is not established by this run.",
        ]
    )
    if notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in notes)
    write_text(report_path(config, "process"), "\n".join(lines))


def build_preflight(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    status = command_result(["git", "status", "--short", "--untracked-files=all"])
    status_lines = [line for line in status["stdout"].splitlines() if line.strip()]
    diff_check = command_result(["git", "diff", "--check"])
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "date_utc": now_utc()[:10],
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_untracked_all": status_lines,
        "dirty_tree_classification": classify_dirty_paths(config, status_lines),
        "git_diff_check": {
            "returncode": diff_check["returncode"],
            "stdout": diff_check["stdout"],
            "stderr": diff_check["stderr"],
        },
        "required_input_availability": required_input_availability(config),
        "paid_boundary": {
            "new_paid_acut_cells_run": False,
            "new_paid_llm_calls_run": False,
            "paid_calls_allowed_by_config": bool(config.get("paid_calls_allowed")),
            "llm_endpoint_required_for_paid_calls_but_not_used": "LLM_BASE_URL + LLM_API_KEY",
        },
        "score_outcome_join_policy": {
            "score_tables_available_for_later_join": score_table_paths(config),
            "terminal_outcomes_loaded_before_selection_freeze": False,
            "score_tables_joined_after_selection_freeze": None,
        },
        "claim_boundary": {
            "analysis_kind": "retrospective_pseudo_future_signal_analysis_with_sparse_rolling_diagnostic",
            "predictive_validity_established": False,
            "formal_preregistration_completed": False,
        },
    }
    write_json(output_path(config, "preflight"), payload)
    write_process_report(
        config,
        "Step 0 - Preflight And Scope Check",
        [rel(output_path(config, "preflight"))],
        [
            "The current runbook input is untracked in this worktree and is classified separately from generated outputs.",
            "Existing score tables are treated as read-only inputs and terminal outcomes are deferred until after selection freeze.",
        ],
    )
    return payload


def task_metadata_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = read_json(input_path(config, "task_table")).get("rows", [])
    return {str(row["candidate_id"]): row for row in rows}


def click_overlay_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = read_json(input_path(config, "click_repair_quality_overlay")).get("rows", [])
    return {str(row["task_id"]): row for row in rows}


def universe_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_payload = read_json(input_path(config, "blocked_candidate_universe"))
    if candidate_payload.get("outcome_fields_loaded") is not False:
        raise ValueError("blocked candidate universe must be outcome-blind")
    metadata = task_metadata_by_id(config)
    click_overlay = click_overlay_by_id(config)
    coverage = read_score_table_coverage(config)
    rows: list[dict[str, Any]] = []
    for source in candidate_payload.get("rows", []):
        task_id = str(source["task_id"])
        repo = str(source.get("repo") or repo_from_task_id(task_id))
        meta = metadata.get(task_id, {})
        overlay = click_overlay.get(task_id, {})
        source_quality_before = str(source.get("source_quality_bucket") or "unknown")
        source_context_before = str(source.get("source_context_type_bucket") or "unknown")
        leakage_before = str(source.get("leakage_risk_bucket") or "unknown")
        if overlay:
            source_quality_after = "clean"
            source_context_after = "public_context_repaired"
            leakage_after = "low"
            overlay_status = "click_repair_overlay_applied"
        else:
            source_quality_after = source_quality_before
            source_context_after = source_context_before
            leakage_after = leakage_before
            overlay_status = "not_applicable"
        exclusion_reasons: list[str] = []
        if not source.get("release_eligible_for_split_design", False):
            exclusion_reasons.append("not_release_eligible_for_split_design")
        if leakage_after not in {"low", "minor_risk"}:
            exclusion_reasons.append("unresolved_hidden_oracle_or_leakage_risk")
        row = {
            "task_id": task_id,
            "repo": repo,
            "eligible_for_analysis": not exclusion_reasons,
            "exclusion_reasons": exclusion_reasons,
            "time_bucket": str(source.get("time_bucket") or meta.get("task_time_bucket") or "unknown"),
            "task_time": meta.get("task_time", ""),
            "coarse_task_family": str(source.get("coarse_task_family") or meta.get("task_family") or "unknown"),
            "editable_scope_bucket": str(source.get("editable_scope_bucket") or "unknown"),
            "source_quality_bucket": source_quality_after,
            "source_quality_bucket_before_repair_overlay": source_quality_before,
            "source_context_type_bucket": source_context_after,
            "source_context_type_bucket_before_repair_overlay": source_context_before,
            "statement_specificity_bucket": str(source.get("statement_specificity_bucket") or "unknown"),
            "context_length_bucket": str(source.get("context_length_bucket") or "unknown"),
            "ambiguity_risk_bucket": "low" if overlay else str(source.get("ambiguity_risk_bucket") or "unknown"),
            "leakage_risk_bucket": leakage_after,
            "leakage_risk_bucket_before_repair_overlay": leakage_before,
            "certification_risk_bucket": str(source.get("certification_risk_bucket") or "unknown"),
            "rare_or_unknown_feature_flag": bool(source.get("rare_or_unknown_feature_flag")),
            "source_reservoir": meta.get("source_reservoir", ""),
            "source_context_class": meta.get("source_context_class", ""),
            "base_commit": meta.get("base_commit", ""),
            "target_commit": meta.get("target_commit", ""),
            "implementation_file_count": len(meta.get("implementation_files", []) or []),
            "test_file_count": len(meta.get("test_files", []) or []),
            "statement_digest": overlay.get("statement_digest") or meta.get("digests", {}).get("task_metadata_digest", ""),
            "repair_overlay_status": overlay_status,
            "paid_outcome_used_for_overlay": bool(overlay.get("paid_outcome_used_for_overlay", False)),
            "committed_outcome_coverage": coverage.get(
                task_id,
                {
                    "adapters_with_committed_rows": [],
                    "split_labels_seen_in_score_tables": [],
                    "committed_score_table_rows": 0,
                },
            ),
        }
        rows.append(row)
    return sorted(rows, key=task_sort_key)


def build_universe(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = universe_rows(config)
    eligible = [row for row in rows if row["eligible_for_analysis"]]
    by_repo = {
        repo: {
            "total": sum(1 for row in rows if row["repo"] == repo),
            "eligible": sum(1 for row in eligible if row["repo"] == repo),
            "with_any_committed_outcome_row": sum(
                1
                for row in eligible
                if row["repo"] == repo and row["committed_outcome_coverage"]["committed_score_table_rows"] > 0
            ),
            "with_both_adapter_rows": sum(
                1
                for row in eligible
                if row["repo"] == repo
                and set(row["committed_outcome_coverage"]["adapters_with_committed_rows"]) == set(ADAPTERS)
            ),
            "time_bucket_counts": dict(sorted(Counter(row["time_bucket"] for row in eligible if row["repo"] == repo).items())),
        }
        for repo in REPOS
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "analysis_universe",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "analysis_universe_task_count": len(eligible),
        "raw_candidate_count": len(rows),
        "repos": list(REPOS),
        "counts_by_repo": by_repo,
        "click_repair_overlay": {
            "overlay_rows_applied": sum(1 for row in rows if row["repair_overlay_status"] == "click_repair_overlay_applied"),
            "historical_paid_results_changed": False,
            "historical_task_ids_changed": False,
        },
        "outcome_fields_absent": True,
        "terminal_outcomes_loaded": False,
        "outcome_fields_used_for_selection": [],
        "coverage_limitation": "Committed score-table row presence is recorded as coverage only; terminal status and pass/fail are absent until the score join.",
        "rows": eligible,
    }
    write_json(output_path(config, "universe"), payload)
    write_universe_report(config, payload)
    write_process_report(
        config,
        "Step 1 - Analysis Universe",
        [rel(output_path(config, "preflight")), rel(output_path(config, "universe")), rel(report_path(config, "universe"))],
        ["Universe rows contain no terminal outcome or pass/fail fields."],
    )
    return payload


def write_universe_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "repo": repo,
            "eligible": summary["eligible"],
            "covered": summary["with_any_committed_outcome_row"],
            "both_adapters": summary["with_both_adapter_rows"],
            "time_buckets": ", ".join(f"{key}:{value}" for key, value in summary["time_bucket_counts"].items()),
        }
        for repo, summary in payload["counts_by_repo"].items()
    ]
    lines = [
        "# Retrospective Predictive-Signal Universe",
        "",
        "What happened: built an outcome-blind universe from the repaired attrs, boltons, and click candidate supply.",
        "",
        "Why it matters: the downstream replay uses task metadata and coverage only until selections are frozen.",
        "",
        "Action suggested next: use this universe for fixed windows and selections, then join score tables later.",
        "",
        *markdown_table(rows, [("repo", "Repo"), ("eligible", "Eligible"), ("covered", "Any score row"), ("both_adapters", "Both adapters"), ("time_buckets", "Time buckets")]),
        "",
        "Boundary:",
        "- Terminal outcomes loaded before selection freeze: `false`.",
        "- Pass/fail fields present in universe rows: `false`.",
        "- Click repair overlay used only public-context review metadata and did not change historical paid outcomes.",
    ]
    write_text(report_path(config, "universe"), "\n".join(lines))


def load_universe(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "universe")
    if path.exists():
        return read_json(path)
    return build_universe(config["_path"])


def selected_split_pools(config: dict[str, Any]) -> dict[str, dict[str, dict[str, list[str]]]]:
    plans = {
        "original_three_repo_split_heldout": read_json(input_path(config, "three_repo_split_plan")).get("assignments", []),
        "blocked_split_heldout": read_json(input_path(config, "supplement_selected_split_plan")).get("assignments", []),
    }
    pools: dict[str, dict[str, dict[str, list[str]]]] = {}
    for window_id, assignments in plans.items():
        pools[window_id] = {repo: {split: [] for split in SPLITS} for repo in REPOS}
        for row in assignments:
            repo = str(row["repo_id"])
            split = str(row["split"])
            if repo in pools[window_id] and split in pools[window_id][repo]:
                pools[window_id][repo][split].append(str(row["candidate_id"]))
        for repo in REPOS:
            for split in SPLITS:
                pools[window_id][repo][split].sort()
    return pools


def build_window_plan(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    universe = load_universe(config)
    rows = universe["rows"]
    rows_by_repo = {repo: [row for row in rows if row["repo"] == repo] for repo in REPOS}
    selected_pools = selected_split_pools(config)
    windows: list[dict[str, Any]] = []
    for window_id, mode_label in [
        ("blocked_split_heldout", "retrospective_pseudo_future"),
        ("original_three_repo_split_heldout", "retrospective_pseudo_future"),
    ]:
        support = {}
        for repo in REPOS:
            b_tasks = selected_pools[window_id][repo]["B_eval"]
            h_tasks = selected_pools[window_id][repo]["H_future"]
            support[repo] = {
                "B_eval_candidate_count": len(b_tasks),
                "H_future_candidate_count": len(h_tasks),
                "B_eval_task_ids": b_tasks,
                "H_future_task_ids": h_tasks,
            }
        windows.append(
            {
                "window_id": window_id,
                "mode": mode_label,
                "primary_window": window_id == "blocked_split_heldout",
                "support_status": "accepted",
                "cutoff_rule": "preexisting outcome-blind split labels; H_future is held-out, not formal future.",
                "support_by_repo": support,
            }
        )
    rolling_support = {}
    true_rolling_accept = True
    for repo, repo_rows in rows_by_repo.items():
        buckets = sorted({str(row["time_bucket"]) for row in repo_rows}, key=lambda value: TIME_BUCKET_ORDER.get(value, 99))
        if len(buckets) < 2:
            true_rolling_accept = False
        cutoff_bucket = buckets[0] if buckets else "none"
        b_rows = [row for row in repo_rows if TIME_BUCKET_ORDER.get(str(row["time_bucket"]), 99) <= TIME_BUCKET_ORDER.get(cutoff_bucket, 99)]
        h_rows = [row for row in repo_rows if TIME_BUCKET_ORDER.get(str(row["time_bucket"]), 99) > TIME_BUCKET_ORDER.get(cutoff_bucket, 99)]
        min_b = int(config["settings"]["minimum_true_rolling_b_eval_tasks"])
        min_h = int(config["settings"]["minimum_true_rolling_h_future_tasks"])
        repo_accept = len(b_rows) >= min_b and len(h_rows) >= min_h
        true_rolling_accept = true_rolling_accept and repo_accept
        rolling_support[repo] = {
            "cutoff_after_bucket": cutoff_bucket,
            "B_eval_candidate_count": len(b_rows),
            "H_future_candidate_count": len(h_rows),
            "B_eval_task_ids": [row["task_id"] for row in sorted(b_rows, key=task_sort_key)],
            "H_future_task_ids": [row["task_id"] for row in sorted(h_rows, key=task_sort_key)],
            "minimum_support_passed": repo_accept,
        }
    rolling_too_sparse = (
        not true_rolling_accept
        or min(summary["B_eval_candidate_count"] for summary in rolling_support.values()) <= int(config["settings"]["minimum_true_rolling_b_eval_tasks"])
    )
    windows.append(
        {
            "window_id": "repo_specific_earliest_time_bucket_cutoff",
            "mode": "true_rolling_origin_diagnostic",
            "primary_window": False,
            "support_status": "diagnostic_sparse" if rolling_too_sparse else "accepted_diagnostic",
            "cutoff_rule": "repo-specific cutoff after each repo's earliest non-empty time bucket.",
            "support_by_repo": rolling_support,
        }
    )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "window_plan",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "analysis_mode": "mixed",
        "primary_mode": "retrospective_pseudo_future",
        "true_rolling_origin_support": "too_sparse_for_primary_claim" if rolling_too_sparse else "available_as_diagnostic",
        "terminal_outcomes_loaded": False,
        "outcome_fields_used_for_window_selection": [],
        "windows": windows,
        "limitations": [
            "Only one repo-specific time cutoff is available with minimum support.",
            "The time-cutoff B_eval side is exactly at the four-task minimum for attrs and click.",
            "The primary analysis therefore uses preexisting outcome-blind held-out split labels and is labeled pseudo-future evidence.",
        ],
    }
    write_json(output_path(config, "window_plan"), payload)
    write_window_plan_report(config, payload)
    write_process_report(
        config,
        "Step 2 - Window And Cutoff Plan",
        [rel(output_path(config, "window_plan")), rel(report_path(config, "window_plan"))],
        ["Window and cutoff choices are frozen before score-table terminal outcomes are loaded."],
    )
    return payload


def write_window_plan_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for window in payload["windows"]:
        for repo, support in window["support_by_repo"].items():
            rows.append(
                {
                    "window": window["window_id"],
                    "mode": window["mode"],
                    "repo": repo,
                    "B_eval": support["B_eval_candidate_count"],
                    "H_future": support["H_future_candidate_count"],
                    "status": window["support_status"],
                }
            )
    lines = [
        "# Retrospective Predictive-Signal Window Plan",
        "",
        "What happened: froze two held-out pseudo-future windows and one sparse time-cutoff diagnostic.",
        "",
        "Why it matters: the primary analysis has enough held-out score coverage, while rolling-origin support is too thin for a formal claim.",
        "",
        "Action suggested next: report pseudo-future signal and keep true rolling-origin as a future preregistration need.",
        "",
        *markdown_table(rows, [("window", "Window"), ("mode", "Mode"), ("repo", "Repo"), ("B_eval", "B_eval pool"), ("H_future", "H_future pool"), ("status", "Status")]),
        "",
        "Boundary:",
        "- Terminal outcomes loaded before this plan: `false`.",
        "- Primary mode: `retrospective_pseudo_future`.",
        "- True rolling-origin support: `" + payload["true_rolling_origin_support"] + "`.",
    ]
    write_text(report_path(config, "window_plan"), "\n".join(lines))


def load_window_plan(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "window_plan")
    if path.exists():
        return read_json(path)
    return build_window_plan(config["_path"])


def rows_by_task_id(universe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in universe["rows"]}


def get_pool_rows(task_ids: list[str], row_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [row_by_id[task_id] for task_id in task_ids if task_id in row_by_id]


def select_unweighted(pool: list[dict[str, Any]], budget: int) -> list[dict[str, Any]]:
    return sorted(pool, key=lambda row: str(row["task_id"]))[:budget]


def feature_counts(rows: Iterable[dict[str, Any]], feature: str) -> Counter[str]:
    return Counter(str(row.get(feature) or "unknown") for row in rows)


def stratification_distance(selected: list[dict[str, Any]], target: list[dict[str, Any]], budget: int) -> float:
    if not target or not selected:
        return float("inf")
    distance = 0.0
    for feature in FEATURE_KEYS:
        selected_counts = feature_counts(selected, feature)
        target_counts = feature_counts(target, feature)
        values = set(selected_counts) | set(target_counts)
        for value in values:
            selected_share = selected_counts[value] / max(1, budget)
            target_share = target_counts[value] / len(target)
            distance += abs(selected_share - target_share)
    return distance


def select_stratified(pool: list[dict[str, Any]], target: list[dict[str, Any]], budget: int) -> list[dict[str, Any]]:
    remaining = sorted(pool, key=lambda row: str(row["task_id"]))
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < budget:
        best = min(
            remaining,
            key=lambda row: (
                stratification_distance(selected + [row], target, budget),
                str(row["task_id"]),
            ),
        )
        selected.append(best)
        remaining.remove(best)
    return selected


def select_temporal_recent(pool: list[dict[str, Any]], budget: int) -> list[dict[str, Any]]:
    return sorted(pool, key=recent_sort_key, reverse=True)[:budget]


def select_seeded_random(pool: list[dict[str, Any]], budget: int, seed: int, window_id: str, repo: str) -> list[dict[str, Any]]:
    rng = random.Random(stable_int("seeded_random_same_budget", seed, window_id, repo))
    rows = list(pool)
    rng.shuffle(rows)
    return sorted(rows[:budget], key=lambda row: str(row["task_id"]))


def has_both_adapter_coverage(row: dict[str, Any]) -> bool:
    return set(row["committed_outcome_coverage"]["adapters_with_committed_rows"]) == set(ADAPTERS)


def select_coverage_constrained(pool: list[dict[str, Any]], budget: int) -> list[dict[str, Any]]:
    return sorted(pool, key=lambda row: (not has_both_adapter_coverage(row), str(row["task_id"])))[:budget]


def block_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(feature) or "unknown") for feature in BLOCK_FEATURE_KEYS)


def select_block_randomized(pool: list[dict[str, Any]], budget: int, seed: int, window_id: str, repo: str) -> list[dict[str, Any]]:
    by_block: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in pool:
        by_block[block_key(row)].append(row)
    for rows in by_block.values():
        rows.sort(key=lambda row: stable_int("block", seed, window_id, repo, row["task_id"]))
    selected: list[dict[str, Any]] = []
    block_keys = sorted(by_block)
    while len(selected) < budget and any(by_block.values()):
        for key in block_keys:
            if by_block[key] and len(selected) < budget:
                selected.append(by_block[key].pop(0))
    return sorted(selected, key=lambda row: str(row["task_id"]))


def uniform_weights(task_ids: list[str]) -> dict[str, float]:
    if not task_ids:
        return {}
    weight = 1.0 / len(task_ids)
    return {task_id: weight for task_id in task_ids}


def weight_diagnostics(weights: dict[str, float], fallback_mode: str | None = None) -> dict[str, Any]:
    if not weights:
        return {"ESS": 0.0, "ESS_ratio": 0.0, "max_weight": 0.0, "fallback_mode": fallback_mode or "empty"}
    ess = 1.0 / sum(value * value for value in weights.values())
    return {
        "ESS": round_float(ess),
        "ESS_ratio": round_float(ess / len(weights)),
        "max_weight": round_float(max(weights.values())),
        "fallback_mode": fallback_mode,
    }


def shrinkage_weights(selected: list[dict[str, Any]], target: list[dict[str, Any]]) -> tuple[dict[str, float], dict[str, Any]]:
    task_ids = [str(row["task_id"]) for row in selected]
    if not selected or not target:
        weights = uniform_weights(task_ids)
        return weights, weight_diagnostics(weights, "empty_selection_or_target")
    raw: dict[str, float] = {}
    for row in selected:
        score = 1.0
        for feature in ("coarse_task_family", "time_bucket"):
            selected_counts = feature_counts(selected, feature)
            target_counts = feature_counts(target, feature)
            values = set(selected_counts) | set(target_counts)
            smoothing = 0.5 / max(1, len(values))
            value = str(row.get(feature) or "unknown")
            target_share = (target_counts[value] + smoothing) / (len(target) + smoothing * len(values))
            selected_share = (selected_counts[value] + smoothing) / (len(selected) + smoothing * len(values))
            score *= target_share / selected_share
        raw[str(row["task_id"])] = score
    total = sum(raw.values())
    weights = {task_id: value / total for task_id, value in raw.items()}
    cap = 0.35
    if max(weights.values()) > cap:
        capped = {task_id: min(value, cap) for task_id, value in weights.items()}
        total = sum(capped.values())
        weights = {task_id: value / total for task_id, value in capped.items()}
    diagnostics = weight_diagnostics(weights, None)
    diagnostics["weight_mode"] = "capped_shrinkage"
    diagnostics["max_weight_allowed"] = cap
    cap_overflow = max(weights.values()) > cap
    low_ess = diagnostics["ESS_ratio"] is not None and diagnostics["ESS_ratio"] < 0.5
    if cap_overflow or low_ess:
        weights = uniform_weights(task_ids)
        fallback = "uniform_fallback_cap_overflow" if cap_overflow else "uniform_fallback_low_ess"
        diagnostics = weight_diagnostics(weights, fallback)
        diagnostics["weight_mode"] = "uniform_fallback"
        diagnostics["max_weight_allowed"] = cap
    return weights, diagnostics


def build_design_registry(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    local_designs = read_json(input_path(config, "local_algorithm_candidate_designs")).get("candidate_designs", [])
    local_by_id = {str(row["design_id"]): row for row in local_designs}
    designs: list[dict[str, Any]] = []
    design_specs = {
        "repo_unweighted_same_budget": ("baseline", "Simple deterministic same-budget unweighted B_eval selector."),
        "repo_stratified_by_target_profile": ("baseline", "Greedy selector matching H_future metadata buckets from B_eval candidates."),
        "temporal_recent_baseline": ("baseline", "Most recent B_eval candidates by task time and time bucket."),
        "seeded_random_same_budget": ("baseline", "Multiple preregistered random seeds with same B_eval budget."),
        "coverage_constrained_unweighted": ("candidate", "Coverage-oriented unweighted selector preferring tasks with both adapter rows."),
        "block_randomized_stratified": ("candidate", "Barcarolle-style block-randomized stratified selector with deterministic seed."),
        "block_plus_shrinkage_weighted": ("candidate", "Blocked selector with capped shrinkage weights computed from metadata only."),
        "old_weighted_target_profile": ("negative_control", "Historical weighted target-profile design retained as a reference only."),
        "completed_blocked_split_supplement": ("diagnostic", "Completed same-budget blocked split supplement, labeled post-hoc exploratory."),
    }
    for design_id in REQUIRED_DESIGNS:
        role, description = design_specs[design_id]
        local = local_by_id.get(design_id, {})
        designs.append(
            {
                "design_id": design_id,
                "role": role,
                "description": description,
                "registered_before_score_join": True,
                "outcome_fields_used_for_selection": [],
                "hidden_oracle_material_used": False,
                "random_seed_policy": list(config["settings"]["random_seeds"]) if design_id == "seeded_random_same_budget" else "deterministic",
                "weight_mode": "capped_shrinkage" if design_id == "block_plus_shrinkage_weighted" else "uniform_or_not_applicable",
                "local_bakeoff_status": local.get("status", "not_in_local_bakeoff"),
                "claim_boundary": "diagnostic_only_post_hoc" if design_id == "completed_blocked_split_supplement" else ("reference_only_not_promotable" if design_id == "old_weighted_target_profile" else "eligible_for_exploratory_comparison"),
            }
        )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "design_registry",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "terminal_outcomes_loaded": False,
        "registered_design_count": len(designs),
        "designs": designs,
    }
    write_json(output_path(config, "design_registry"), payload)
    return payload


def load_design_registry(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "design_registry")
    if path.exists():
        return read_json(path)
    return build_design_registry(config["_path"])


def window_pools(window: dict[str, Any], row_by_id: dict[str, dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    pools: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for repo, support in window["support_by_repo"].items():
        pools[repo] = {
            "B_eval": get_pool_rows(support["B_eval_task_ids"], row_by_id),
            "H_future": get_pool_rows(support["H_future_task_ids"], row_by_id),
        }
    return pools


def select_for_design(
    config: dict[str, Any],
    design_id: str,
    window: dict[str, Any],
    repo: str,
    b_pool: list[dict[str, Any]],
    h_pool: list[dict[str, Any]],
    seed: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, float], dict[str, Any]]:
    if design_id == "old_weighted_target_profile":
        return [], [], {}, {"selection_status": "not_evaluable_no_current_three_repo_task_overlap"}
    if design_id == "completed_blocked_split_supplement":
        if window["window_id"] != "blocked_split_heldout":
            return [], [], {}, {"selection_status": "not_applicable_outside_blocked_split_window"}
        selected = sorted(b_pool, key=lambda row: str(row["task_id"]))
        task_ids = [row["task_id"] for row in selected]
        return selected, sorted(h_pool, key=lambda row: str(row["task_id"])), uniform_weights(task_ids), {"selection_status": "selected_completed_supplement_full_budget"}
    budget_key = "rolling_b_eval_budget_per_repo" if window["window_id"] == "repo_specific_earliest_time_bucket_cutoff" else "primary_b_eval_budget_per_repo"
    budget = min(int(config["settings"][budget_key]), len(b_pool))
    if design_id == "repo_unweighted_same_budget":
        selected = select_unweighted(b_pool, budget)
    elif design_id == "repo_stratified_by_target_profile":
        selected = select_stratified(b_pool, h_pool, budget)
    elif design_id == "temporal_recent_baseline":
        selected = select_temporal_recent(b_pool, budget)
    elif design_id == "seeded_random_same_budget":
        if seed is None:
            raise ValueError("seeded random design requires a seed")
        selected = select_seeded_random(b_pool, budget, seed, window["window_id"], repo)
    elif design_id == "coverage_constrained_unweighted":
        selected = select_coverage_constrained(b_pool, budget)
    elif design_id in {"block_randomized_stratified", "block_plus_shrinkage_weighted"}:
        selected = select_block_randomized(b_pool, budget, 2026053007, window["window_id"], repo)
    else:
        raise ValueError(f"unknown design {design_id}")
    task_ids = [str(row["task_id"]) for row in selected]
    weights = uniform_weights(task_ids)
    diagnostics = {"selection_status": "selected", "budget": budget}
    if design_id == "block_plus_shrinkage_weighted":
        weights, weight_diag = shrinkage_weights(selected, h_pool)
        diagnostics.update(weight_diag)
    else:
        diagnostics.update(weight_diagnostics(weights))
        diagnostics["weight_mode"] = "uniform"
    return selected, sorted(h_pool, key=lambda row: str(row["task_id"])), weights, diagnostics


def build_selection_freeze(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    universe = load_universe(config)
    window_plan = load_window_plan(config)
    design_registry = load_design_registry(config)
    row_by_id = rows_by_task_id(universe)
    selections: list[dict[str, Any]] = []
    for window in window_plan["windows"]:
        pools = window_pools(window, row_by_id)
        for design in design_registry["designs"]:
            design_id = design["design_id"]
            seeds = list(config["settings"]["random_seeds"]) if design_id == "seeded_random_same_budget" else [None]
            for seed in seeds:
                instance_id = f"{design_id}__seed_{seed}" if seed is not None else design_id
                for repo in REPOS:
                    b_rows, h_rows, weights, diagnostics = select_for_design(
                        config,
                        design_id,
                        window,
                        repo,
                        pools[repo]["B_eval"],
                        pools[repo]["H_future"],
                        seed,
                    )
                    if not b_rows and not h_rows:
                        selections.append(
                            {
                                "selection_id": f"{window['window_id']}|{repo}|{instance_id}",
                                "window_id": window["window_id"],
                                "mode": window["mode"],
                                "repo": repo,
                                "design_id": design_id,
                                "design_instance_id": instance_id,
                                "seed": seed,
                                "role": design["role"],
                                "claim_boundary": design["claim_boundary"],
                                "selection_status": diagnostics.get("selection_status", "not_selected"),
                                "B_eval_task_ids": [],
                                "H_future_task_ids": [],
                                "B_eval_weights": {},
                                "diagnostics": diagnostics,
                                "outcome_fields_used_for_selection": [],
                            }
                        )
                        continue
                    selections.append(
                        {
                            "selection_id": f"{window['window_id']}|{repo}|{instance_id}",
                            "window_id": window["window_id"],
                            "mode": window["mode"],
                            "repo": repo,
                            "design_id": design_id,
                            "design_instance_id": instance_id,
                            "seed": seed,
                            "role": design["role"],
                            "claim_boundary": design["claim_boundary"],
                            "selection_status": diagnostics.get("selection_status", "selected"),
                            "B_eval_task_ids": [str(row["task_id"]) for row in b_rows],
                            "H_future_task_ids": [str(row["task_id"]) for row in h_rows],
                            "B_eval_weights": weights,
                            "diagnostics": diagnostics,
                            "selection_features_used": list(FEATURE_KEYS if design_id == "repo_stratified_by_target_profile" else BLOCK_FEATURE_KEYS if design_id.startswith("block_") else ()),
                            "outcome_fields_used_for_selection": [],
                        }
                    )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "selection_freeze",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "selection_freeze_status": "frozen_before_score_join",
        "terminal_outcomes_loaded_before_freeze": False,
        "outcome_fields_used_for_selection": [],
        "score_tables_joined_before_freeze": False,
        "design_registry_digest": digest_payload(design_registry),
        "window_plan_digest": digest_payload(window_plan),
        "selection_count": len(selections),
        "selections": selections,
    }
    write_json(output_path(config, "selection_freeze"), payload)
    write_design_registry_report(config, design_registry, payload)
    write_process_report(
        config,
        "Step 3 - Design Registry And Selection Freeze",
        [rel(output_path(config, "design_registry")), rel(output_path(config, "selection_freeze")), rel(report_path(config, "design_registry"))],
        ["Designs, seeds, weights, windows, and selections are frozen before score-table outcomes are joined."],
    )
    return payload


def write_design_registry_report(config: dict[str, Any], registry: dict[str, Any], freeze: dict[str, Any]) -> None:
    rows = [
        {
            "design": row["design_id"],
            "role": row["role"],
            "claim": row["claim_boundary"],
            "seeds": ",".join(str(seed) for seed in row["random_seed_policy"]) if isinstance(row["random_seed_policy"], list) else row["random_seed_policy"],
        }
        for row in registry["designs"]
    ]
    selected_count = sum(1 for row in freeze["selections"] if row["selection_status"].startswith("selected"))
    lines = [
        "# Retrospective Predictive-Signal Design Registry",
        "",
        "What happened: registered required baselines, candidates, negative controls, and diagnostic designs before score outcomes were joined.",
        "",
        "Why it matters: no task selection, weight, seed, cutoff, or design inclusion can move after outcomes are loaded.",
        "",
        "Action suggested next: join committed score tables against the frozen selections.",
        "",
        *markdown_table(rows, [("design", "Design"), ("role", "Role"), ("claim", "Claim boundary"), ("seeds", "Seeds")]),
        "",
        "Freeze summary:",
        f"- Selection rows: `{freeze['selection_count']}`.",
        f"- Selected rows: `{selected_count}`.",
        "- Outcome fields used for selection: `[]`.",
        "- Completed blocked split supplement is diagnostic only.",
        "- Old weighted target-profile is reference-only and not promotable.",
    ]
    write_text(report_path(config, "design_registry"), "\n".join(lines))


def load_selection_freeze(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "selection_freeze")
    if path.exists():
        return read_json(path)
    return build_selection_freeze(config["_path"])


def read_score_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in score_table_paths(config):
        with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (str(row["adapter_id"]), str(row["task_id"]), str(row.get("attempt") or "1"))
                if key in seen:
                    continue
                seen.add(key)
                normalized = dict(row)
                normalized["repo"] = repo_from_task_id(str(row["task_id"]))
                normalized["scoreable_cell"] = bool_from_csv(row.get("scoreable_cell"))
                normalized["agent_failure"] = bool_from_csv(row.get("agent_failure"))
                normalized["harness_error"] = bool_from_csv(row.get("harness_error"))
                normalized["pass_flag"] = normalized["scoreable_cell"] and row.get("terminal_status") == "verified_pass"
                normalized["fail_flag"] = normalized["scoreable_cell"] and row.get("terminal_status") == "verified_fail"
                normalized["score_table"] = rel(path)
                normalized["cell_source"] = "committed_paid_score_table"
                rows.append(normalized)
    return rows


def build_score_join_manifest(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    freeze = load_selection_freeze(config)
    score_rows = read_score_rows(config)
    score_by_adapter_task = {(row["adapter_id"], row["task_id"]): row for row in score_rows}
    joined_rows: list[dict[str, Any]] = []
    for selection in freeze["selections"]:
        for split in SPLITS:
            for task_id in selection[f"{split}_task_ids"]:
                for adapter in ADAPTERS:
                    source = score_by_adapter_task.get((adapter, task_id))
                    if source:
                        joined_rows.append(
                            {
                                "selection_id": selection["selection_id"],
                                "window_id": selection["window_id"],
                                "repo": selection["repo"],
                                "design_id": selection["design_id"],
                                "design_instance_id": selection["design_instance_id"],
                                "adapter_id": adapter,
                                "split": split,
                                "task_id": task_id,
                                "terminal_status": source["terminal_status"],
                                "scoreable_cell": source["scoreable_cell"],
                                "pass_flag": source["pass_flag"],
                                "fail_flag": source["fail_flag"],
                                "non_scoreable_reason": None if source["scoreable_cell"] else source["terminal_status"],
                                "score_table": source["score_table"],
                                "cell_source": source["cell_source"],
                                "cost_latency_fields_available": False,
                            }
                        )
                    else:
                        joined_rows.append(
                            {
                                "selection_id": selection["selection_id"],
                                "window_id": selection["window_id"],
                                "repo": selection["repo"],
                                "design_id": selection["design_id"],
                                "design_instance_id": selection["design_instance_id"],
                                "adapter_id": adapter,
                                "split": split,
                                "task_id": task_id,
                                "terminal_status": "missing_committed_score_row",
                                "scoreable_cell": False,
                                "pass_flag": False,
                                "fail_flag": False,
                                "non_scoreable_reason": "missing_committed_score_row",
                                "score_table": None,
                                "cell_source": "missing_from_committed_score_tables",
                                "cost_latency_fields_available": False,
                            }
                        )
    non_scoreable_counts = Counter(str(row["non_scoreable_reason"]) for row in joined_rows if not row["scoreable_cell"])
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "score_join_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "join_happened_after_selection_freeze": True,
        "selection_freeze_digest": digest_payload(freeze),
        "score_table_sources": score_table_paths(config),
        "score_table_source_count": len(score_table_paths(config)),
        "historical_paid_outcomes_changed": False,
        "new_paid_acut_cells_run": False,
        "new_paid_llm_calls_run": False,
        "joined_row_count": len(joined_rows),
        "scoreable_joined_row_count": sum(1 for row in joined_rows if row["scoreable_cell"]),
        "non_scoreable_joined_row_count": sum(1 for row in joined_rows if not row["scoreable_cell"]),
        "non_scoreable_by_reason": dict(sorted(non_scoreable_counts.items())),
        "terminal_status_counts": dict(sorted(Counter(str(row["terminal_status"]) for row in joined_rows).items())),
        "invalid_output_sensitivity": {
            "task_id": INVALID_TASK_ID,
            "selected_join_rows": sum(1 for row in joined_rows if row["task_id"] == INVALID_TASK_ID),
            "non_scoreable_selected_rows": sum(1 for row in joined_rows if row["task_id"] == INVALID_TASK_ID and not row["scoreable_cell"]),
        },
        "joined_rows": joined_rows,
    }
    write_json(output_path(config, "score_join_manifest"), payload)
    write_process_report(
        config,
        "Step 4 - Score Join Manifest",
        [rel(output_path(config, "score_join_manifest"))],
        ["Committed score tables were joined only after the selection freeze artifact existed."],
    )
    return payload


def load_score_join(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "score_join_manifest")
    if path.exists():
        return read_json(path)
    return build_score_join_manifest(config["_path"])


def weighted_rate(rows: list[dict[str, Any]], weights: dict[str, float] | None = None) -> tuple[float | None, int, int, int]:
    scoreable = [row for row in rows if row["scoreable_cell"]]
    if not scoreable:
        return None, 0, 0, len(rows)
    if weights:
        available_weight = sum(weights.get(row["task_id"], 0.0) for row in scoreable)
        if available_weight <= 0:
            return None, len(scoreable), 0, len(rows) - len(scoreable)
        pass_weight = sum(weights.get(row["task_id"], 0.0) for row in scoreable if row["pass_flag"])
        return pass_weight / available_weight, len(scoreable), sum(1 for row in scoreable if row["pass_flag"]), len(rows) - len(scoreable)
    pass_count = sum(1 for row in scoreable if row["pass_flag"])
    return pass_count / len(scoreable), len(scoreable), pass_count, len(rows) - len(scoreable)


def metric_rows(config: dict[str, Any], freeze: dict[str, Any], join: dict[str, Any]) -> list[dict[str, Any]]:
    rows_by_selection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in join["joined_rows"]:
        rows_by_selection[row["selection_id"]].append(row)
    metrics: list[dict[str, Any]] = []
    threshold = float(config["settings"]["catastrophic_gap_threshold"])
    for selection in freeze["selections"]:
        if not selection["B_eval_task_ids"] or not selection["H_future_task_ids"]:
            continue
        joined = rows_by_selection[selection["selection_id"]]
        for adapter in ADAPTERS:
            b_rows = [row for row in joined if row["adapter_id"] == adapter and row["split"] == "B_eval"]
            h_rows = [row for row in joined if row["adapter_id"] == adapter and row["split"] == "H_future"]
            b_rate, b_n, b_pass, b_non = weighted_rate(b_rows, selection.get("B_eval_weights"))
            h_rate, h_n, h_pass, h_non = weighted_rate(h_rows, None)
            if b_rate is None or h_rate is None:
                signed = None
                gap = None
                squared = None
            else:
                signed = b_rate - h_rate
                gap = abs(signed)
                squared = signed * signed
            metrics.append(
                {
                    "window_id": selection["window_id"],
                    "mode": selection["mode"],
                    "repo": selection["repo"],
                    "adapter_id": adapter,
                    "design_id": selection["design_id"],
                    "design_instance_id": selection["design_instance_id"],
                    "role": selection["role"],
                    "claim_boundary": selection["claim_boundary"],
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
                    "B_eval_non_scoreable_count": b_non,
                    "H_future_non_scoreable_count": h_non,
                    "missing_or_non_scoreable_count": b_non + h_non,
                    "invalid_output_sensitivity_label": "contains_known_invalid_output" if any(row["task_id"] == INVALID_TASK_ID for row in b_rows + h_rows) else "not_in_slice",
                }
            )
    return metrics


def summarize_design(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row["absolute_gap"] is not None]
    if not valid:
        return {
            "slice_count": 0,
            "MAE": None,
            "RMSE": None,
            "mean_signed_error": None,
            "catastrophic_miss_rate": None,
            "B_eval_scoreable_count": 0,
            "H_future_scoreable_count": 0,
            "non_scoreable_count": sum(row["missing_or_non_scoreable_count"] for row in rows),
        }
    return {
        "slice_count": len(valid),
        "MAE": round_float(statistics.mean(row["absolute_gap"] for row in valid)),
        "RMSE": round_float(math.sqrt(statistics.mean(row["squared_error"] for row in valid))),
        "mean_signed_error": round_float(statistics.mean(row["signed_error"] for row in valid)),
        "catastrophic_miss_rate": round_float(sum(1 for row in valid if row["catastrophic_miss"]) / len(valid)),
        "B_eval_scoreable_count": sum(row["B_eval_scoreable_count"] for row in valid),
        "H_future_scoreable_count": sum(row["H_future_scoreable_count"] for row in valid),
        "non_scoreable_count": sum(row["missing_or_non_scoreable_count"] for row in rows),
    }


def build_adapter_metrics(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    freeze = load_selection_freeze(config)
    join = load_score_join(config)
    rows = metric_rows(config, freeze, join)
    by_adapter_design: dict[str, dict[str, Any]] = {adapter: {} for adapter in ADAPTERS}
    for adapter in ADAPTERS:
        for design_id in REQUIRED_DESIGNS:
            by_adapter_design[adapter][design_id] = summarize_design([row for row in rows if row["adapter_id"] == adapter and row["design_id"] == design_id])
    by_design = {design_id: summarize_design([row for row in rows if row["design_id"] == design_id]) for design_id in REQUIRED_DESIGNS}
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_metrics",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "primary_reporting": "adapter_stratified",
        "pooled_reporting": "secondary_all_adapter_equal_slice_mix",
        "catastrophic_gap_threshold": float(config["settings"]["catastrophic_gap_threshold"]),
        "metric_rows": rows,
        "by_adapter_design": by_adapter_design,
        "by_design_equal_mix_secondary": by_design,
    }
    write_json(output_path(config, "adapter_metrics"), payload)
    write_adapter_metrics_report(config, payload)
    write_process_report(
        config,
        "Step 5 - Adapter-Stratified Metrics",
        [rel(output_path(config, "adapter_metrics")), rel(report_path(config, "adapter_metrics"))],
        ["Adapter-level metrics are primary; pooled equal-mix summaries are secondary diagnostics."],
    )
    return payload


def write_adapter_metrics_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for adapter, by_design in payload["by_adapter_design"].items():
        for design_id, summary in by_design.items():
            if summary["slice_count"]:
                rows.append(
                    {
                        "adapter": adapter,
                        "design": design_id,
                        "slices": summary["slice_count"],
                        "MAE": summary["MAE"],
                        "RMSE": summary["RMSE"],
                        "miss": summary["catastrophic_miss_rate"],
                    }
                )
    lines = [
        "# Retrospective Predictive-Signal Adapter Metrics",
        "",
        "What happened: computed B_eval-to-H_future prediction error separately for Codex and Kilo workspace adapters.",
        "",
        "Why it matters: adapter differences are ACUT-configuration evidence, so the primary readout keeps them separate.",
        "",
        "Action suggested next: compare candidates against simple baselines with uncertainty labels.",
        "",
        *markdown_table(rows, [("adapter", "Adapter"), ("design", "Design"), ("slices", "Slices"), ("MAE", "MAE"), ("RMSE", "RMSE"), ("miss", "Catastrophic miss rate")]),
        "",
        "Boundary:",
        "- Adapter-level metrics are primary.",
        "- Equal-mix pooled metrics are secondary diagnostics only.",
        "- Known invalid-output sensitivity is labeled on affected slices, not coerced to pass or fail.",
    ]
    write_text(report_path(config, "adapter_metrics"), "\n".join(lines))


def load_adapter_metrics(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "adapter_metrics")
    if path.exists():
        return read_json(path)
    return build_adapter_metrics(config["_path"])


def overlapping_rows(metric_rows_all: list[dict[str, Any]], design_id: str, baseline_id: str, adapter: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    design_rows = [row for row in metric_rows_all if row["design_id"] == design_id and row["absolute_gap"] is not None and (adapter is None or row["adapter_id"] == adapter)]
    baseline_rows = [row for row in metric_rows_all if row["design_id"] == baseline_id and row["absolute_gap"] is not None and (adapter is None or row["adapter_id"] == adapter)]
    baseline_by_key = {
        (row["adapter_id"], row["window_id"], row["repo"]): row
        for row in baseline_rows
    }
    paired_design = []
    paired_baseline = []
    for row in design_rows:
        key = (row["adapter_id"], row["window_id"], row["repo"])
        if key in baseline_by_key:
            paired_design.append(row)
            paired_baseline.append(baseline_by_key[key])
    return paired_design, paired_baseline


def comparison_summary(design_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not design_rows or not baseline_rows:
        return {
            "overlap_slice_count": 0,
            "design_MAE": None,
            "baseline_MAE": None,
            "baseline_delta_MAE": None,
            "design_catastrophic_miss_rate": None,
            "baseline_catastrophic_miss_rate": None,
            "catastrophic_miss_delta": None,
            "improved_slice_count": 0,
            "worsened_slice_count": 0,
            "same_slice_count": 0,
        }
    deltas = [design["absolute_gap"] - baseline["absolute_gap"] for design, baseline in zip(design_rows, baseline_rows)]
    return {
        "overlap_slice_count": len(design_rows),
        "design_MAE": round_float(statistics.mean(row["absolute_gap"] for row in design_rows)),
        "baseline_MAE": round_float(statistics.mean(row["absolute_gap"] for row in baseline_rows)),
        "baseline_delta_MAE": round_float(statistics.mean(deltas)),
        "design_catastrophic_miss_rate": round_float(sum(1 for row in design_rows if row["catastrophic_miss"]) / len(design_rows)),
        "baseline_catastrophic_miss_rate": round_float(sum(1 for row in baseline_rows if row["catastrophic_miss"]) / len(baseline_rows)),
        "catastrophic_miss_delta": round_float(
            sum(1 for row in design_rows if row["catastrophic_miss"]) / len(design_rows)
            - sum(1 for row in baseline_rows if row["catastrophic_miss"]) / len(baseline_rows)
        ),
        "improved_slice_count": sum(1 for delta in deltas if delta < 0),
        "worsened_slice_count": sum(1 for delta in deltas if delta > 0),
        "same_slice_count": sum(1 for delta in deltas if delta == 0),
    }


def uncertainty_label(summary: dict[str, Any], design_rows: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    if summary["overlap_slice_count"] < 12:
        labels.append("too_sparse")
    delta = summary["baseline_delta_MAE"]
    if delta is None:
        labels.append("too_sparse")
    elif delta < 0:
        labels.append("directional_only")
        improved_repos = {row["repo"] for row in design_rows}
        improved_adapters = {row["adapter_id"] for row in design_rows}
        if len(improved_repos) >= 2 and len(improved_adapters) >= 2:
            labels.append("stable_across_repos")
        else:
            labels.append("single_repo_driven")
    elif delta > 0:
        labels.append("candidate_worse_than_baseline")
    else:
        labels.append("tie_with_baseline")
    return sorted(set(labels))


def build_baseline_comparison(config_path: str | Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    metrics = load_adapter_metrics(config)
    rows = metrics["metric_rows"]
    comparisons: list[dict[str, Any]] = []
    for design_id in [item for item in REQUIRED_DESIGNS if item != "old_weighted_target_profile"]:
        for baseline_id in SIMPLE_BASELINES:
            if design_id == baseline_id:
                continue
            paired_design, paired_baseline = overlapping_rows(rows, design_id, baseline_id)
            summary = comparison_summary(paired_design, paired_baseline)
            comparisons.append(
                {
                    "design_id": design_id,
                    "baseline_id": baseline_id,
                    **summary,
                    "uncertainty_labels": uncertainty_label(summary, paired_design),
                }
            )
    simple_baseline_scores = [
        {
            "design_id": baseline_id,
            "MAE": metrics["by_design_equal_mix_secondary"][baseline_id]["MAE"],
            "catastrophic_miss_rate": metrics["by_design_equal_mix_secondary"][baseline_id]["catastrophic_miss_rate"],
            "slice_count": metrics["by_design_equal_mix_secondary"][baseline_id]["slice_count"],
        }
        for baseline_id in SIMPLE_BASELINES
        if metrics["by_design_equal_mix_secondary"][baseline_id]["MAE"] is not None
    ]
    best_simple = min(simple_baseline_scores, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"]))
    candidate_scores = [
        {
            "design_id": design_id,
            "MAE": metrics["by_design_equal_mix_secondary"][design_id]["MAE"],
            "catastrophic_miss_rate": metrics["by_design_equal_mix_secondary"][design_id]["catastrophic_miss_rate"],
            "slice_count": metrics["by_design_equal_mix_secondary"][design_id]["slice_count"],
        }
        for design_id in BARCAROLLE_CANDIDATES
        if metrics["by_design_equal_mix_secondary"][design_id]["MAE"] is not None
    ]
    promotable_candidate_scores = [row for row in candidate_scores if row["design_id"] in PROMOTABLE_BARCAROLLE_CANDIDATES]
    diagnostic_candidate_scores = [row for row in candidate_scores if row["design_id"] in DIAGNOSTIC_CANDIDATES]
    best_candidate = min(promotable_candidate_scores, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"]))
    best_diagnostic = (
        min(diagnostic_candidate_scores, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"]))
        if diagnostic_candidate_scores
        else None
    )
    candidate_beats_best_simple = best_candidate["MAE"] < best_simple["MAE"] if best_candidate and best_simple else False
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_comparison",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "comparison_policy": "compare by overlapping adapter/repo/window slices; adapter-stratified metrics remain primary.",
        "simple_baseline_scores": simple_baseline_scores,
        "candidate_scores": candidate_scores,
        "promotable_candidate_scores": promotable_candidate_scores,
        "diagnostic_candidate_scores": diagnostic_candidate_scores,
        "best_simple_baseline": best_simple,
        "best_barcarolle_candidate": best_candidate,
        "best_diagnostic_candidate": best_diagnostic,
        "candidate_beats_best_simple_baseline": candidate_beats_best_simple,
        "comparisons": comparisons,
    }
    uncertainty = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "uncertainty",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "interval_policy": "No formal interval estimated; support is too sparse and retrospective.",
        "support_labels": {
            "overall": "directional_only" if candidate_beats_best_simple else "candidate_worse_than_baseline",
            "sample_size": "too_sparse_for_formal_predictive_validity",
            "claim_strength": "traction_evidence_only",
        },
        "design_uncertainty_labels": {
            row["design_id"] + "__vs__" + row["baseline_id"]: row["uncertainty_labels"]
            for row in comparisons
        },
        "driver_checks": driver_checks(metrics, best_candidate["design_id"] if best_candidate else None, best_simple["design_id"] if best_simple else None),
    }
    write_json(output_path(config, "baseline_comparison"), payload)
    write_json(output_path(config, "uncertainty"), uncertainty)
    write_baseline_comparison_report(config, payload)
    write_uncertainty_report(config, uncertainty)
    write_process_report(
        config,
        "Step 6 - Baseline Comparison And Uncertainty",
        [
            rel(output_path(config, "baseline_comparison")),
            rel(output_path(config, "uncertainty")),
            rel(report_path(config, "baseline_comparison")),
            rel(report_path(config, "uncertainty")),
        ],
        ["Baseline comparisons are retrospective and directional, not formal predictive-validity evidence."],
    )
    return payload, uncertainty


def driver_checks(metrics: dict[str, Any], candidate_id: str | None, baseline_id: str | None) -> dict[str, Any]:
    if not candidate_id or not baseline_id:
        return {}
    rows = metrics["metric_rows"]
    candidate, baseline = overlapping_rows(rows, candidate_id, baseline_id)
    by_repo: dict[str, list[float]] = defaultdict(list)
    by_adapter: dict[str, list[float]] = defaultdict(list)
    for design_row, baseline_row in zip(candidate, baseline):
        delta = design_row["absolute_gap"] - baseline_row["absolute_gap"]
        by_repo[design_row["repo"]].append(delta)
        by_adapter[design_row["adapter_id"]].append(delta)
    return {
        "best_candidate": candidate_id,
        "best_baseline": baseline_id,
        "delta_MAE_by_repo": {repo: round_float(statistics.mean(values)) for repo, values in sorted(by_repo.items())},
        "delta_MAE_by_adapter": {adapter: round_float(statistics.mean(values)) for adapter, values in sorted(by_adapter.items())},
    }


def write_baseline_comparison_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "design": row["design_id"],
            "MAE": row["MAE"],
            "miss": row["catastrophic_miss_rate"],
            "slices": row["slice_count"],
        }
        for row in payload["simple_baseline_scores"] + payload["candidate_scores"]
    ]
    lines = [
        "# Retrospective Predictive-Signal Baseline Comparison",
        "",
        "What happened: compared candidate MAE and catastrophic miss rate against simple baselines on overlapping slices.",
        "",
        "Why it matters: the question is whether Barcarolle-style selection predicts held-out outcomes better than simple alternatives.",
        "",
        "Action suggested next: treat any improvement as directional traction only unless a future run is preregistered.",
        "",
        f"Best simple baseline: `{payload['best_simple_baseline']['design_id']}` with MAE `{payload['best_simple_baseline']['MAE']}`.",
        f"Best Barcarolle candidate: `{payload['best_barcarolle_candidate']['design_id']}` with MAE `{payload['best_barcarolle_candidate']['MAE']}`.",
        f"Best diagnostic candidate: `{payload['best_diagnostic_candidate']['design_id']}` with MAE `{payload['best_diagnostic_candidate']['MAE']}`." if payload.get("best_diagnostic_candidate") else "Best diagnostic candidate: `none`.",
        f"Candidate beats best simple baseline: `{payload['candidate_beats_best_simple_baseline']}`.",
        "",
        *markdown_table(rows, [("design", "Design"), ("MAE", "MAE"), ("miss", "Catastrophic miss rate"), ("slices", "Slices")]),
    ]
    write_text(report_path(config, "baseline_comparison"), "\n".join(lines))


def write_uncertainty_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Retrospective Predictive-Signal Uncertainty",
        "",
        "What happened: assigned qualitative uncertainty labels instead of formal intervals.",
        "",
        "Why it matters: the analysis is retrospective and has sparse true rolling-origin support.",
        "",
        "Action suggested next: use the result to choose action categories, not to claim predictive validity.",
        "",
        "Labels:",
    ]
    for key, value in payload["support_labels"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "Driver checks:",
            "```json",
            json.dumps(payload["driver_checks"], indent=2, sort_keys=True),
            "```",
        ]
    )
    write_text(report_path(config, "uncertainty"), "\n".join(lines))


def load_baseline_comparison(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "baseline_comparison")
    if path.exists():
        return read_json(path)
    comparison, _ = build_baseline_comparison(config["_path"])
    return comparison


def build_claim_boundary_and_decision(config_path: str | Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    comparison = load_baseline_comparison(config)
    metrics = load_adapter_metrics(config)
    preflight = read_json(output_path(config, "preflight"))
    if comparison["candidate_beats_best_simple_baseline"]:
        decision_label = "retrospective_signal_positive_directional"
        supports_traction = True
    else:
        decision_label = "retrospective_signal_negative_against_baselines"
        supports_traction = False
    if comparison["best_barcarolle_candidate"]["slice_count"] < 12:
        decision_label = "retrospective_signal_mixed_underpowered"
    claim_boundary = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "claim_boundary",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "claim_boundary_label": decision_label,
        "allowed_claims": [
            "retrospective_predictive_signal_analysis_completed",
            "selection_freeze_outcome_blind",
            "adapter_stratified_metrics_computed",
            "baseline_comparison_completed",
            "analysis_underpowered",
            "true_rolling_origin_support_too_sparse",
            "pseudo_future_signal_only",
            "future_preregistered_validation_recommended",
            "no_paid_acut_cells_run",
            "no_paid_llm_calls_run",
        ],
        "disallowed_claims_preserved": [
            "predictive_validity_established",
            "formal_preregistration_completed",
            "new_paid_validation_completed",
            "post_hoc_design_promoted_as_primary",
            "outcome_informed_selection",
            "model_only_superiority",
            "followup_runbook_written_by_worker",
        ],
        "predictive_validity_established": False,
        "formal_preregistration_completed": False,
        "no_paid_acut_cells_run": True,
        "no_paid_llm_calls_run": True,
    }
    decision = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": decision_label,
        "analysis_mode": "mixed",
        "primary_mode": "retrospective_pseudo_future",
        "repos_included": list(REPOS),
        "adapters_included": list(ADAPTERS),
        "window_count": 3,
        "candidate_designs_evaluated": [design for design in REQUIRED_DESIGNS if design != "old_weighted_target_profile"],
        "best_simple_baseline": comparison["best_simple_baseline"],
        "best_barcarolle_candidate": comparison["best_barcarolle_candidate"],
        "candidate_beats_best_simple_baseline": comparison["candidate_beats_best_simple_baseline"],
        "supports_traction_narrative": supports_traction,
        "future_paid_acut_remains_blocked_by_default": True,
        "recommended_next_action_categories": [
            "use the result as retrospective traction or negative evidence only",
            "keep paid ACUT reruns blocked by default",
            "future validation should preregister true rolling-origin windows before outcomes are inspected",
            "keep adapter-stratified reporting as the primary reporting surface",
        ],
        "MAE_summary": metrics["by_design_equal_mix_secondary"],
        "catastrophic_miss_summary": {
            design_id: summary["catastrophic_miss_rate"]
            for design_id, summary in metrics["by_design_equal_mix_secondary"].items()
        },
        "support_level": "directional_retrospective_underpowered",
        "paid_ACUT_cells": 0,
        "paid_LLM_calls": 0,
        "predictive_validity_established": False,
        "process_md_updated": False,
        "preflight_head": preflight["head"],
    }
    write_json(output_path(config, "claim_boundary"), claim_boundary)
    write_json(output_path(config, "decision"), decision)
    write_decision_report(config, claim_boundary, decision)
    write_process_report(
        config,
        "Step 7 - Claim Boundary And Decision",
        [rel(output_path(config, "claim_boundary")), rel(output_path(config, "decision")), rel(report_path(config, "decision"))],
        ["Closeout is complete; no follow-up runbook was drafted or created."],
    )
    return claim_boundary, decision


def write_decision_report(config: dict[str, Any], claim_boundary: dict[str, Any], decision: dict[str, Any]) -> None:
    lines = [
        "# Retrospective Predictive-Signal Decision",
        "",
        f"Decision label: `{decision['decision_label']}`.",
        "",
        "What happened: ran a no-paid retrospective pseudo-future signal analysis over repaired attrs, boltons, and click supply, with a sparse time-cutoff diagnostic.",
        "",
        "Why it matters: the result tests whether Barcarolle-style selections have retrospective signal beyond simple baselines without adding new paid outcomes.",
        "",
        "Action suggested next: keep paid ACUT cells blocked by default and require a future preregistered rolling-origin validation before any predictive-validity claim.",
        "",
        f"- Analysis mode: `{decision['analysis_mode']}` with primary `{decision['primary_mode']}`.",
        f"- Repos included: `{', '.join(decision['repos_included'])}`.",
        f"- Adapters included: `{', '.join(decision['adapters_included'])}`.",
        f"- Windows: `{decision['window_count']}`.",
        f"- Designs evaluated: `{len(decision['candidate_designs_evaluated'])}`.",
        f"- Best simple baseline: `{decision['best_simple_baseline']['design_id']}` MAE `{decision['best_simple_baseline']['MAE']}`.",
        f"- Best Barcarolle candidate: `{decision['best_barcarolle_candidate']['design_id']}` MAE `{decision['best_barcarolle_candidate']['MAE']}`.",
        f"- Candidate beats baseline: `{decision['candidate_beats_best_simple_baseline']}`.",
        f"- Support level: `{decision['support_level']}`.",
        f"- Paid ACUT cells: `{decision['paid_ACUT_cells']}`.",
        f"- Paid LLM calls: `{decision['paid_LLM_calls']}`.",
        f"- Predictive validity established: `{decision['predictive_validity_established']}`.",
        f"- PROCESS.md updated: `{decision['process_md_updated']}`.",
        "",
        "## Boundary",
        "",
        f"- Claim boundary label: `{claim_boundary['claim_boundary_label']}`.",
        "- The completed blocked split supplement remains diagnostic and post-hoc exploratory.",
        "- Adapter differences are ACUT configuration evidence, not model-only superiority.",
        "- No follow-up runbook was drafted or created.",
        "",
        "## Verification",
        "",
        "- Focused tests: recorded in final command output for this run.",
        "- Relevant suite: `uv run pytest tests/test_phase1_retrospective_predictive_signal.py`.",
        "- git diff --check: recorded in final command output for this run.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def build_all(config_path: str | Path = DEFAULT_CONFIG) -> None:
    build_preflight(config_path)
    build_universe(config_path)
    build_window_plan(config_path)
    build_selection_freeze(config_path)
    build_score_join_manifest(config_path)
    build_adapter_metrics(config_path)
    build_baseline_comparison(config_path)
    build_claim_boundary_and_decision(config_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 1 retrospective predictive-signal analysis.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--step",
        choices=["preflight", "universe", "windows", "freeze", "join", "metrics", "comparison", "decision", "all"],
        default="all",
    )
    args = parser.parse_args()
    step_map = {
        "preflight": build_preflight,
        "universe": build_universe,
        "windows": build_window_plan,
        "freeze": build_selection_freeze,
        "join": build_score_join_manifest,
        "metrics": build_adapter_metrics,
        "comparison": build_baseline_comparison,
        "decision": build_claim_boundary_and_decision,
        "all": build_all,
    }
    result = step_map[args.step](args.config)
    if result is not None:
        print(json.dumps({"step": args.step, "completed": True}, sort_keys=True))


if __name__ == "__main__":
    main()
