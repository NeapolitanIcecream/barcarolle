from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_selection_demo" / "tools"
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [TOOLS, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import agent_selection_demo as demo  # noqa: E402
import workspace_acut_run as workspace  # noqa: E402


PHASE1_RESULTS = ROOT / "experiments" / "phase1_compiler" / "results"
TASK_TABLE = PHASE1_RESULTS / "phase1_three_repo_paid_readiness_packaging_task_table.json"
FRESH_ATTEMPTS = PHASE1_RESULTS / "phase1_task_supply_v2_fresh_certification_attempts.json"
RAW_ANCHORS = PHASE1_RESULTS / "phase1_task_supply_v2_raw_anchor_inventory.json"
CAPACITY_AUDIT = ROOT / "experiments" / "agent_tuning_demo" / "results" / "boltons_capacity_generator_audit.json"
CAPACITY_DRY_RUN = ROOT / "experiments" / "agent_tuning_demo" / "results" / "boltons_capacity_certification_dry_run.json"

MANIFEST = demo.result_path("boltons_small_expansion_task_manifest.json")
INVENTORY_REPORT = demo.report_path("boltons_small_expansion_inventory_zh.md")
TASK_GATE_REPORT = demo.report_path("boltons_small_expansion_task_gate_zh.md")
PAID_MATRIX_REPORT = demo.report_path("boltons_small_expansion_paid_matrix_zh.md")
FINAL_ANALYSIS_REPORT = demo.report_path("boltons_small_expansion_final_analysis_zh.md")
ROLLING_REPORT = demo.report_path("boltons_strict_rolling_origin_zh.md")
DEMO_REPORT = demo.report_path("boltons_small_expansion_demo_report_zh.md")

FRESH_SUBMISSIONS = demo.result_path("boltons_small_expansion_submissions.jsonl")
FRESH_VERIFIERS = demo.result_path("boltons_small_expansion_verifier_results.jsonl")
FRESH_COST = demo.result_path("boltons_small_expansion_fresh_cost_ledger.jsonl")
SCORE_TABLE = demo.result_path("boltons_small_expansion_score_table.csv")
COST_LEDGER = demo.result_path("boltons_small_expansion_cost_ledger.jsonl")
FINAL_MATRIX = demo.result_path("boltons_small_expansion_final_matrix.csv")
SUMMARY_JSON = demo.result_path("boltons_small_expansion_summary.json")
ROLLING_SLICES = demo.result_path("boltons_strict_rolling_origin_slices.csv")
ROLLING_SUMMARY = demo.result_path("boltons_strict_rolling_origin_summary.json")

DEFAULT_SELECTION_COUNT = 30
DEFAULT_LATER_COUNT = 20
DEFAULT_ROLLING_WINDOW_SIZE = 10
DEFAULT_RANDOM_SEEDS = 500
NEW_PAID_CELL_HARD_CAP = 140
RUN_PREFIX = "agent_selection_demo_2026_06_15_boltons_small_expansion"

SCORE_FIELDNAMES = [
    "final_split",
    "agent_id",
    "reviewer_name",
    "harness",
    "model",
    "task_id",
    "terminal_status",
    "scoreable_cell",
    "verified_pass",
    "failure_category",
    "latency_seconds",
    "estimated_cost_usd",
    "usage_observed",
    "cost_observation_kind",
    "usage_source",
    "billed_cost_usd",
    "patch_sha256",
    "run_id",
    "paid_cell_source",
    "score_source_kind",
    "source_artifact_path",
    "replacement_rule",
]

FINAL_MATRIX_FIELDNAMES = [
    *SCORE_FIELDNAMES,
    "task_time",
    "task_order",
    "source_package",
    "code_files",
    "test_files",
]

ROLLING_FIELDNAMES = [
    "origin_id",
    "origin_index",
    "origin_time",
    "selection_start_time",
    "selection_end_time",
    "future_start_time",
    "future_end_time",
    "agent_id",
    "reviewer_name",
    "selection_task_count",
    "future_task_count",
    "selection_scoreable_count",
    "future_scoreable_count",
    "selection_pass_rate",
    "future_pass_rate",
    "absolute_error",
    "selection_pass_count",
    "future_pass_count",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_time(raw: Any) -> datetime:
    text = str(raw or "").strip()
    if not text:
        return datetime.min.replace(tzinfo=timezone.utc)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        value = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def csv_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def fnum(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def r6(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def package_source(package: workspace.TaskPackage) -> str:
    sources = package.metadata.get("metadata_sources") if isinstance(package.metadata, dict) else {}
    if isinstance(sources, dict) and sources.get("task_source"):
        return str(sources["task_source"])
    return str(package.metadata.get("evidence_level") or "unknown")


def verifier_timeout(config: dict[str, Any]) -> int:
    return demo.run_policy_int(config, "verifier_timeout_seconds", demo.DEFAULT_VERIFIER_TIMEOUT_SECONDS)


def load_boltons_v2_packages(config: dict[str, Any]) -> list[workspace.TaskPackage]:
    exp = workspace.phase0_root(ROOT)
    task_rows = workspace.three_repo_rows_by_id(TASK_TABLE)
    attempt_rows = workspace.three_repo_rows_by_id(FRESH_ATTEMPTS)
    raw_rows = workspace.three_repo_rows_by_id(RAW_ANCHORS)
    packages: list[workspace.TaskPackage] = []
    for task_id, row in sorted(task_rows.items(), key=lambda item: (str(item[1].get("task_time") or ""), item[0])):
        if str(row.get("repo_id")) != "boltons":
            continue
        attempt = attempt_rows.get(task_id)
        if not attempt:
            continue
        raw = raw_rows.get(task_id, {})
        implementation_files = [str(path) for path in row.get("implementation_files", [])]
        test_files = [str(path) for path in row.get("test_files", [])]
        statement = workspace.three_repo_statement(row, raw, {})
        command = workspace.three_repo_command_from_attempt(attempt)
        metadata = {
            "allowed_context_refs": workspace.three_repo_public_context_refs(raw, {}, str(row.get("target_commit") or "")),
            "base_commit": row.get("base_commit"),
            "changed_files": [*implementation_files, *test_files],
            "evidence_level": "phase1_three_repo_paid_validation_incremental_boltons_v2",
            "metadata_sources": {
                "task_table": demo.display_path(TASK_TABLE),
                "certification_attempts": demo.display_path(FRESH_ATTEMPTS),
                "raw_anchor_inventory": demo.display_path(RAW_ANCHORS),
            },
            "source_context_status": row.get("source_context_quality"),
            "source_reservoir": row.get("source_reservoir"),
            "statement_digest": f"sha256:{workspace.sha256_text(statement)}",
            "statement_source": "phase1_three_repo_paid_validation_committed_metadata",
            "task_time": row.get("task_time"),
            "test_files": test_files,
            "technical_certification_profile": row.get("technical_certification_profile") or {},
            "verifier_command_metadata": {
                "winning_profile_id": attempt.get("winning_profile_id"),
                "command_source": "certification_attempt_command_shape",
            },
        }
        packages.append(
            workspace.TaskPackage(
                task_id=task_id,
                repo_id="boltons",
                split="unassigned",
                source_repo=exp / "external_repos" / "boltons",
                base_commit=str(row["base_commit"]),
                target_commit=str(row.get("target_commit") or attempt.get("target_commit_optional") or ""),
                solver_facing_statement=statement,
                verifier_command=command,
                allowed_code_paths=implementation_files,
                test_paths=test_files,
                timeout_seconds=verifier_timeout(config),
                scope_boundaries="Modify only the listed implementation paths; do not edit tests, generated metadata, or benchmark artifacts.",
                metadata=metadata,
            )
        )
    return packages


def load_expanded_pool(config: dict[str, Any]) -> tuple[list[workspace.TaskPackage], dict[str, Any]]:
    current, audit_rows = demo.load_task_pool(config)
    v2 = load_boltons_v2_packages(config)
    by_target_commit = {package.target_commit: package for package in current if package.target_commit}
    incremental_v2: list[workspace.TaskPackage] = []
    for package in v2:
        if package.target_commit and package.target_commit in by_target_commit:
            continue
        incremental_v2.append(package)
        by_target_commit[package.target_commit] = package
    packages = [*current, *incremental_v2]
    packages.sort(key=lambda package: (parse_time(package.metadata.get("task_time")), package.task_id))
    stats = {
        "current_certified_count": len(current),
        "phase1_v2_release_eligible_count": len(v2),
        "incremental_v2_by_target_commit_count": len(incremental_v2),
        "combined_unique_target_commit_count": len(packages),
        "task_pool_audit_rows": len(audit_rows),
    }
    return packages, stats


def task_role(index: int, selection_count: int, later_count: int) -> str:
    if index < selection_count:
        return "selection"
    if index < selection_count + later_count:
        return "later_check"
    if index == selection_count + later_count:
        return "smoke_or_unused"
    return "unused"


def package_manifest_row(package: workspace.TaskPackage, index: int, selection_count: int, later_count: int) -> dict[str, Any]:
    return {
        "task_id": package.task_id,
        "task_order": index,
        "task_time": package.metadata.get("task_time"),
        "final_role": task_role(index, selection_count, later_count),
        "source_package": package_source(package),
        "base_commit": package.base_commit,
        "target_commit": package.target_commit,
        "code_files": list(package.allowed_code_paths),
        "test_files": list(package.test_paths),
        "source_context_status": package.metadata.get("source_context_status"),
        "allowed_context_refs": package.metadata.get("allowed_context_refs") or [],
        "statement_sha256": workspace.sha256_text(package.solver_facing_statement),
        "verifier_command_sha256": workspace.sha256_text(" ".join(package.verifier_command)),
    }


def build_manifest(config: dict[str, Any], selection_count: int = DEFAULT_SELECTION_COUNT, later_count: int = DEFAULT_LATER_COUNT) -> dict[str, Any]:
    packages, stats = load_expanded_pool(config)
    needed = selection_count + later_count
    if len(packages) < needed:
        raise RuntimeError(f"expanded boltons pool has {len(packages)} tasks, below required {needed}")
    rows = [package_manifest_row(package, index, selection_count, later_count) for index, package in enumerate(packages)]
    selection = [row["task_id"] for row in rows if row["final_role"] == "selection"]
    later = [row["task_id"] for row in rows if row["final_role"] == "later_check"]
    selection_times = [row["task_time"] for row in rows if row["final_role"] == "selection"]
    later_times = [row["task_time"] for row in rows if row["final_role"] == "later_check"]
    if parse_time(max(selection_times)) >= parse_time(min(later_times)):
        raise RuntimeError("selection/later_check task_time ordering is not strict")
    return {
        "schema_version": "barcarolle.agent_selection_demo.boltons_small_expansion_manifest.v1",
        "generated_at": iso_now(),
        "target_repo": config["target_repo"]["repo_name"],
        "selection_count": len(selection),
        "later_check_count": len(later),
        "displayed_task_count": len(selection) + len(later),
        "new_paid_cell_hard_cap": NEW_PAID_CELL_HARD_CAP,
        "agent_ids": [str(candidate["agent_id"]) for candidate in config["agent_candidates"]],
        "selection_tasks": selection,
        "later_check_tasks": later,
        "unused_or_smoke_tasks": [row["task_id"] for row in rows if row["final_role"] in {"smoke_or_unused", "unused"}],
        "time_ranges": {
            "selection_start": min(selection_times),
            "selection_end": max(selection_times),
            "later_check_start": min(later_times),
            "later_check_end": max(later_times),
        },
        "pool_stats": stats,
        "source_artifacts": {
            "demo_config": demo.display_path(ROOT / demo.DEFAULT_CONFIG),
            "phase1_task_table": demo.display_path(TASK_TABLE),
            "phase1_fresh_certification_attempts": demo.display_path(FRESH_ATTEMPTS),
            "phase1_raw_anchor_inventory": demo.display_path(RAW_ANCHORS),
            "capacity_audit": demo.display_path(CAPACITY_AUDIT),
            "capacity_dry_run": demo.display_path(CAPACITY_DRY_RUN),
        },
        "task_rows": rows,
        "paid_agent_calls_made": False,
        "split_rule": "strict task_time order over current 35 boltons certified tasks plus phase1 v2 incremental target commits; first 30 Selection, next 20 later-check",
    }


def write_inventory_report(config: dict[str, Any], manifest: dict[str, Any]) -> None:
    displayed_selection = {row["task_id"] for row in read_csv(demo.result_path("selection_score_table.csv"))}
    displayed_holdout = {row["task_id"] for row in read_csv(demo.result_path("holdout_score_table.csv"))}
    top2 = {row["task_id"] for row in read_csv(demo.result_path("doubled_timeout_top2_repeat_score_table.csv"))}
    smoke = {row["task_id"] for row in read_csv(demo.result_path("smoke_score_table.csv"))}
    rows = manifest["task_rows"]
    classifications: Counter[str] = Counter()
    for row in rows:
        task_id = row["task_id"]
        if task_id in displayed_selection:
            classifications["already_displayed_selection"] += 1
        elif task_id in displayed_holdout:
            classifications["already_displayed_holdout"] += 1
        elif task_id in smoke:
            classifications["unused_smoke_but_release_ready"] += 1
        elif row["source_package"] == "phase1_three_repo_paid_validation_incremental_boltons_v2":
            classifications["newly_promotable_after_no_paid_certification"] += 1
        else:
            classifications["previously_certified_but_unused"] += 1
    capacity = demo.read_json(CAPACITY_AUDIT) if CAPACITY_AUDIT.exists() else {}
    rejected_counts = {
        key: value
        for key, value in sorted((capacity.get("classification_counts") or {}).items())
        if key not in {"new_release_eligible_from_no_paid_dry_run", "already_used_in_phase2b_scoreable_pool", "previously_certified_but_unused_or_smoke"}
    }
    model_gate = demo.model_gate(config)
    secret_gate = demo.secret_isolation_gate()
    table_rows = [
        {
            "Class": key,
            "Count": value,
        }
        for key, value in sorted(classifications.items())
    ]
    task_preview = [
        {
            "Role": row["final_role"],
            "Task": row["task_id"],
            "Time": row["task_time"],
            "Source": row["source_package"],
        }
        for row in rows[: min(len(rows), 55)]
    ]
    lines = [
        "# Boltons small expansion inventory",
        "",
        f"生成时间：`{manifest['generated_at']}`。",
        "",
        "## Preflight",
        "",
        f"- Endpoint/model gate: `{model_gate['status']}`；present models: `{', '.join(model_gate.get('present_models') or [])}`；endpoint host hash: `{model_gate.get('endpoint_host_hash')}`。",
        f"- Secret isolation gate: `{secret_gate['status']}`；agent child sees real endpoint env: `{secret_gate['real_endpoint_env_visible_to_agent_child']}`。",
        f"- Target repo: `{config['target_repo']['repo_name']}`。",
        "",
        "## Inventory classes",
        "",
        *demo.markdown_table(table_rows, [("Class", "Class"), ("Count", "Count")]),
        "",
        "Doubled-timeout repeated top-2 tasks are the existing original Holdout tasks only; count: "
        f"`{len(top2)}`。",
        "",
        "## Rejected or deferred capacity rows",
        "",
        *[f"- `{key}`: `{value}`" for key, value in rejected_counts.items()],
        "",
        "## Frozen candidate order preview",
        "",
        *demo.markdown_table(task_preview, [("Role", "Role"), ("Task", "Task"), ("Time", "Time"), ("Source", "Source")]),
        "",
        "本报告只读取 committed sanitized metadata、score tables 和 capacity summaries；没有读取 raw prompts、raw completions、transcripts、solver workspaces 或 verifier workspaces。",
    ]
    demo.write_text(INVENTORY_REPORT, "\n".join(lines) + "\n")


def write_task_gate_report(manifest: dict[str, Any]) -> None:
    stats = manifest["pool_stats"]
    role_counts = Counter(row["final_role"] for row in manifest["task_rows"])
    source_counts = Counter(row["source_package"] for row in manifest["task_rows"] if row["final_role"] in {"selection", "later_check"})
    role_rows = [{"Role": key, "Count": value} for key, value in sorted(role_counts.items())]
    source_rows = [{"Source": key, "Displayed tasks": value} for key, value in sorted(source_counts.items())]
    lines = [
        "# Boltons small expansion task gate",
        "",
        f"生成时间：`{manifest['generated_at']}`。",
        "",
        "## Gate result",
        "",
        f"- Combined release-ready pool: `{stats['combined_unique_target_commit_count']}` tasks。",
        f"- Current demo certified tasks: `{stats['current_certified_count']}`。",
        f"- Phase 1 v2 release-eligible boltons tasks: `{stats['phase1_v2_release_eligible_count']}`。",
        f"- Incremental v2 target commits: `{stats['incremental_v2_by_target_commit_count']}`。",
        f"- Frozen Selection: `{manifest['selection_count']}` tasks。",
        f"- Frozen later-check: `{manifest['later_check_count']}` tasks。",
        f"- Time order: Selection `{manifest['time_ranges']['selection_start']}` to `{manifest['time_ranges']['selection_end']}`; later-check `{manifest['time_ranges']['later_check_start']}` to `{manifest['time_ranges']['later_check_end']}`。",
        "",
        "## Source mix",
        "",
        *demo.markdown_table(source_rows, [("Source", "Source"), ("Displayed tasks", "Displayed tasks")]),
        "",
        "## Role counts",
        "",
        *demo.markdown_table(role_rows, [("Role", "Role"), ("Count", "Count")]),
        "",
        "## Freeze artifact",
        "",
        f"- Manifest: `{demo.display_path(MANIFEST)}`。",
        f"- Manifest task rows: `{len(manifest['task_rows'])}`。",
        "- Paid Agent calls made by this gate: `false`。",
        "",
        "Selection 和 later-check 只按真实 `task_time` 排序切分；后续 rolling-origin 诊断必须继续使用真实时间，不得把普通 heldout label 当作时间 origin。",
    ]
    demo.write_text(TASK_GATE_REPORT, "\n".join(lines) + "\n")


def command_freeze(args: argparse.Namespace) -> int:
    config = demo.load_config(demo.repo_path(args.config))
    manifest = build_manifest(config, args.selection_count, args.later_count)
    demo.write_json(MANIFEST, manifest)
    write_inventory_report(config, manifest)
    write_task_gate_report(manifest)
    return 0


def load_manifest() -> dict[str, Any]:
    return demo.read_json(MANIFEST)


def load_package_map(config: dict[str, Any]) -> dict[str, workspace.TaskPackage]:
    packages, _stats = load_expanded_pool(config)
    return {package.task_id: package for package in packages}


def manifest_role_by_task(manifest: dict[str, Any]) -> dict[str, str]:
    return {str(row["task_id"]): str(row["final_role"]) for row in manifest["task_rows"]}


def manifest_row_by_task(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in manifest["task_rows"]}


def normalize_score_row(
    row: dict[str, Any],
    *,
    final_split: str,
    run_id: str,
    paid_cell_source: str,
    score_source_kind: str,
    source_artifact_path: str,
    replacement_rule: str = "",
) -> dict[str, Any]:
    return {
        "final_split": final_split,
        "agent_id": row.get("agent_id", ""),
        "reviewer_name": row.get("reviewer_name", ""),
        "harness": row.get("harness", ""),
        "model": row.get("model", ""),
        "task_id": row.get("task_id", ""),
        "terminal_status": row.get("terminal_status", ""),
        "scoreable_cell": csv_bool(row.get("scoreable_cell")),
        "verified_pass": csv_bool(row.get("verified_pass")),
        "failure_category": row.get("failure_category", ""),
        "latency_seconds": row.get("latency_seconds", ""),
        "estimated_cost_usd": row.get("estimated_cost_usd", ""),
        "usage_observed": csv_bool(row.get("usage_observed")),
        "cost_observation_kind": row.get("cost_observation_kind", ""),
        "usage_source": row.get("usage_source", ""),
        "billed_cost_usd": row.get("billed_cost_usd", ""),
        "patch_sha256": row.get("patch_sha256", ""),
        "run_id": run_id,
        "paid_cell_source": paid_cell_source,
        "score_source_kind": score_source_kind,
        "source_artifact_path": source_artifact_path,
        "replacement_rule": replacement_rule,
    }


def score_row_from_fresh(stage: str, submission: dict[str, Any], verifier: dict[str, Any], cost: dict[str, Any]) -> dict[str, Any]:
    terminal = verifier.get("status") or submission.get("status")
    return {
        "final_split": stage,
        "agent_id": submission.get("adapter_id", ""),
        "reviewer_name": cost.get("reviewer_name", ""),
        "harness": submission.get("harness_name", ""),
        "model": submission.get("model_or_agent_name", ""),
        "task_id": submission.get("task_id", ""),
        "terminal_status": terminal,
        "scoreable_cell": terminal in demo.SCOREABLE_STATUSES,
        "verified_pass": terminal == "verified_pass",
        "failure_category": demo.failure_category(verifier, submission),
        "latency_seconds": submission.get("latency_seconds", ""),
        "estimated_cost_usd": cost.get("estimated_cost_usd", ""),
        "usage_observed": cost.get("usage_observed", False),
        "cost_observation_kind": cost.get("cost_observation_kind", cost.get("cost_method", "")),
        "usage_source": cost.get("usage_source", ""),
        "billed_cost_usd": cost.get("billed_cost_usd", ""),
        "patch_sha256": submission.get("patch_sha256", ""),
        "run_id": submission.get("run_id", ""),
        "paid_cell_source": "fresh_paid_small_expansion",
        "score_source_kind": "fresh_paid_cell",
        "source_artifact_path": demo.display_path(SCORE_TABLE),
        "replacement_rule": "",
    }


def existing_active_rows(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    role_by_task = manifest_role_by_task(manifest)
    displayed = set(manifest["selection_tasks"]) | set(manifest["later_check_tasks"])
    active: dict[tuple[str, str], dict[str, Any]] = {}
    for artifact_name, source_kind in [
        ("selection_score_table.csv", "reused_original_selection_score"),
        ("holdout_score_table.csv", "reused_original_holdout_score"),
    ]:
        source_path = demo.result_path(artifact_name)
        for row in read_csv(source_path):
            task_id = str(row.get("task_id") or "")
            agent_id = str(row.get("agent_id") or "")
            if task_id not in displayed or not agent_id:
                continue
            active[(task_id, agent_id)] = normalize_score_row(
                row,
                final_split=role_by_task[task_id],
                run_id=str(row.get("run_id") or f"reused__{source_kind}__{agent_id}__{task_id}"),
                paid_cell_source="reused_committed_paid_cell",
                score_source_kind=source_kind,
                source_artifact_path=demo.display_path(source_path),
            )
    repeat_path = demo.result_path("doubled_timeout_top2_repeat_score_table.csv")
    for row in read_csv(repeat_path):
        task_id = str(row.get("task_id") or "")
        agent_id = str(row.get("agent_id") or "")
        if task_id not in displayed or agent_id not in set(demo.TOP2_REPEAT_AGENT_IDS):
            continue
        active[(task_id, agent_id)] = normalize_score_row(
            row,
            final_split=role_by_task[task_id],
            run_id=str(row.get("run_id") or f"reused__doubled_timeout__{agent_id}__{task_id}"),
            paid_cell_source="reused_committed_paid_cell",
            score_source_kind="reused_doubled_timeout_top2_repeat",
            source_artifact_path=demo.display_path(repeat_path),
            replacement_rule="active_1800s_timeout_top2_repeat_supersedes_original_holdout_for_codex_gpt_5_4_and_kilo_gpt_5_4",
        )
    return active


def fresh_rows_by_key() -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    submissions = demo.read_jsonl(FRESH_SUBMISSIONS)
    verifiers = demo.read_jsonl(FRESH_VERIFIERS)
    costs = [demo.normalize_cost_row(row) for row in demo.read_jsonl(FRESH_COST)]
    verifier_by_run = {row["run_id"]: row for row in verifiers if row.get("run_id")}
    cost_by_run = {row["run_id"]: row for row in costs if row.get("run_id")}
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for submission in submissions:
        run_id = submission.get("run_id")
        if not run_id:
            continue
        verifier = verifier_by_run.get(run_id, {})
        cost = cost_by_run.get(run_id, {})
        stage = str(submission.get("split") or "")
        scored = score_row_from_fresh(stage, submission, verifier, cost)
        rows[(str(scored["task_id"]), str(scored["agent_id"]))] = scored
    return rows, submissions, verifiers, costs


def combined_score_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    active = existing_active_rows(manifest)
    fresh, _submissions, _verifiers, _costs = fresh_rows_by_key()
    active.update(fresh)
    ordered_tasks = [*manifest["selection_tasks"], *manifest["later_check_tasks"]]
    rows: list[dict[str, Any]] = []
    for task_id in ordered_tasks:
        for agent_id in manifest["agent_ids"]:
            row = active.get((task_id, agent_id))
            if row:
                rows.append(row)
    return rows


def combined_cost_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in score_rows:
        rows.append(
            {
                "schema_version": "barcarolle.agent_selection_demo.boltons_small_expansion.cost.v1",
                "run_id": row.get("run_id"),
                "final_split": row.get("final_split"),
                "agent_id": row.get("agent_id"),
                "reviewer_name": row.get("reviewer_name"),
                "harness": row.get("harness"),
                "model": row.get("model"),
                "task_id": row.get("task_id"),
                "status": row.get("terminal_status"),
                "usage_observed": row.get("usage_observed"),
                "estimated_cost_usd": fnum(row.get("estimated_cost_usd")),
                "cost_observation_kind": row.get("cost_observation_kind"),
                "usage_source": row.get("usage_source"),
                "billed_cost_usd": row.get("billed_cost_usd") or None,
                "latency_seconds": fnum(row.get("latency_seconds")),
                "paid_cell_source": row.get("paid_cell_source"),
                "score_source_kind": row.get("score_source_kind"),
                "source_artifact_path": row.get("source_artifact_path"),
            }
        )
    return rows


def persist_combined_outputs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = combined_score_rows(manifest)
    demo.write_csv(SCORE_TABLE, rows, SCORE_FIELDNAMES)
    demo.write_jsonl(COST_LEDGER, combined_cost_rows(rows))
    return rows


def missing_cells(manifest: dict[str, Any]) -> list[tuple[str, str, str]]:
    active_keys = {(row["task_id"], row["agent_id"]) for row in combined_score_rows(manifest)}
    missing: list[tuple[str, str, str]] = []
    for final_split, task_ids in [("selection", manifest["selection_tasks"]), ("later_check", manifest["later_check_tasks"])]:
        for task_id in task_ids:
            for agent_id in manifest["agent_ids"]:
                if (task_id, agent_id) not in active_keys:
                    missing.append((final_split, task_id, agent_id))
    return missing


def run_missing_cells(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    missing_env = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing_env:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing_env)}")
    packages = load_package_map(config)
    candidates = demo.candidate_by_id(config)
    fresh_by_key, submissions, verifiers, costs = fresh_rows_by_key()
    already_fresh_count = len(fresh_by_key)
    missing = missing_cells(manifest)
    if already_fresh_count + len(missing) > NEW_PAID_CELL_HARD_CAP:
        raise RuntimeError(
            f"paid-cell hard cap would be exceeded: existing fresh {already_fresh_count}, missing {len(missing)}, cap {NEW_PAID_CELL_HARD_CAP}"
        )
    for final_split, task_id, agent_id in missing:
        package = replace(packages[task_id], split=final_split, timeout_seconds=verifier_timeout(config))
        candidate = candidates[agent_id]
        adapter = demo.adapter_config_for(config, candidate)
        run_id = f"boltons_small_expansion__{final_split}__{agent_id}__{task_id}"
        start = time.monotonic()
        result = workspace.run_workspace_cell(ROOT, package, adapter, run_id, result_prefix=RUN_PREFIX)
        usage = demo.usage_from_submission(result.submission)
        usage_observed, estimated_cost, token_counts = demo.estimate_cost(usage, candidate["model"], config)
        cost_row = {
            "schema_version": "barcarolle.agent_selection_demo.cost.v1",
            "run_id": run_id,
            "timestamp": iso_now(),
            "stage": final_split,
            "agent_id": agent_id,
            "reviewer_name": candidate["reviewer_name"],
            "harness": candidate["harness"],
            "model": candidate["model"],
            "task_id": task_id,
            "status": result.verifier["status"],
            "usage_observed": usage_observed,
            "estimated_cost_usd": estimated_cost,
            "cost_method": "observed_token_estimate" if usage_observed else "conservative_per_cell_estimate",
            **demo.cost_observation_metadata(usage_observed),
            "latency_seconds": result.submission.get("latency_seconds", round(time.monotonic() - start, 3)),
            **token_counts,
        }
        submissions = workspace.merge_rows_by_run_id(submissions, [result.submission])
        verifiers = workspace.merge_rows_by_run_id(verifiers, [result.verifier])
        costs = workspace.merge_rows_by_run_id(costs, [cost_row])
        demo.write_jsonl(FRESH_SUBMISSIONS, submissions)
        demo.write_jsonl(FRESH_VERIFIERS, verifiers)
        demo.write_jsonl(FRESH_COST, [demo.normalize_cost_row(row) for row in costs])
        persist_combined_outputs(manifest)
        print(
            json.dumps(
                {
                    "completed": run_id,
                    "status": result.verifier["status"],
                    "fresh_paid_cells": len(costs),
                    "remaining": len(missing_cells(manifest)),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    rows = persist_combined_outputs(manifest)
    return summarize_paid_matrix(manifest, rows)


def summarize_split_agent(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_agent: dict[str, dict[str, Any]] = {}
    for agent_id in sorted({str(row["agent_id"]) for row in rows}):
        agent_rows = [row for row in rows if row["agent_id"] == agent_id]
        scoreable = [row for row in agent_rows if row["scoreable_cell"] is True]
        pass_count = sum(1 for row in scoreable if row["verified_pass"] is True)
        latencies = [value for value in (fnum(row.get("latency_seconds")) for row in agent_rows) if value is not None]
        costs = [value or 0.0 for value in (fnum(row.get("estimated_cost_usd")) for row in agent_rows)]
        by_agent[agent_id] = {
            "reviewer_name": agent_rows[0].get("reviewer_name", agent_id) if agent_rows else agent_id,
            "scheduled_cells": len(agent_rows),
            "scoreable_cells": len(scoreable),
            "verified_pass_count": pass_count,
            "verified_pass_rate": r6(None if not scoreable else pass_count / len(scoreable)),
            "scoreable_cell_rate": r6(None if not agent_rows else len(scoreable) / len(agent_rows)),
            "estimated_cost_usd": round(sum(costs), 8),
            "median_latency_seconds": None if not latencies else round(statistics.median(latencies), 3),
            "failure_counts": dict(sorted(Counter(str(row.get("failure_category") or "") for row in agent_rows).items())),
        }
    return by_agent


def ranked_agents(agent_summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [{"agent_id": agent_id, **summary} for agent_id, summary in agent_summary.items()]
    rows.sort(
        key=lambda row: (
            -(row.get("verified_pass_rate") or 0.0),
            -int(row.get("verified_pass_count") or 0),
            str(row.get("agent_id") or ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def summarize_paid_matrix(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_split = {
        split: summarize_split_agent([row for row in rows if row["final_split"] == split])
        for split in ["selection", "later_check"]
    }
    source_counts = Counter(str(row.get("score_source_kind") or "") for row in rows)
    paid_source_counts = Counter(str(row.get("paid_cell_source") or "") for row in rows)
    summary = {
        "schema_version": "barcarolle.agent_selection_demo.boltons_small_expansion.paid_matrix_summary.v1",
        "generated_at": iso_now(),
        "manifest": demo.display_path(MANIFEST),
        "scheduled_cells": len(manifest["selection_tasks"]) * len(manifest["agent_ids"]) + len(manifest["later_check_tasks"]) * len(manifest["agent_ids"]),
        "completed_cells": len(rows),
        "scoreable_cells": sum(1 for row in rows if row["scoreable_cell"] is True),
        "verified_pass_cells": sum(1 for row in rows if row["verified_pass"] is True),
        "new_paid_cells": paid_source_counts.get("fresh_paid_small_expansion", 0),
        "reused_committed_cells": paid_source_counts.get("reused_committed_paid_cell", 0),
        "score_source_counts": dict(sorted(source_counts.items())),
        "paid_cell_source_counts": dict(sorted(paid_source_counts.items())),
        "by_split": by_split,
        "rankings": {split: ranked_agents(agent_summary) for split, agent_summary in by_split.items()},
        "estimated_cost_usd": round(sum(fnum(row.get("estimated_cost_usd")) or 0.0 for row in rows), 8),
        "fresh_estimated_cost_usd": round(
            sum(fnum(row.get("estimated_cost_usd")) or 0.0 for row in rows if row.get("paid_cell_source") == "fresh_paid_small_expansion"),
            8,
        ),
    }
    return summary


def write_paid_matrix_report(summary: dict[str, Any]) -> None:
    source_rows = [{"Source": key, "Cells": value} for key, value in summary["score_source_counts"].items()]
    paid_rows = [{"Source": key, "Cells": value} for key, value in summary["paid_cell_source_counts"].items()]
    selection_rows = [
        {"Agent": row["reviewer_name"], "Pass": row["verified_pass_rate"], "Scoreable": row["scoreable_cells"], "Rank": row["rank"]}
        for row in summary["rankings"]["selection"]
    ]
    later_rows = [
        {"Agent": row["reviewer_name"], "Pass": row["verified_pass_rate"], "Scoreable": row["scoreable_cells"], "Rank": row["rank"]}
        for row in summary["rankings"]["later_check"]
    ]
    lines = [
        "# Boltons small expansion paid matrix",
        "",
        f"生成时间：`{summary['generated_at']}`。",
        "",
        f"- Scheduled cells: `{summary['scheduled_cells']}`。",
        f"- Completed cells: `{summary['completed_cells']}`。",
        f"- Scoreable cells: `{summary['scoreable_cells']}`。",
        f"- New paid cells in this expansion: `{summary['new_paid_cells']}` / cap `{NEW_PAID_CELL_HARD_CAP}`。",
        f"- Reused committed cells: `{summary['reused_committed_cells']}`。",
        f"- Estimated displayed-matrix cost: `${summary['estimated_cost_usd']}`；fresh expansion estimated cost `${summary['fresh_estimated_cost_usd']}`。",
        "",
        "## Paid/reuse source counts",
        "",
        *demo.markdown_table(paid_rows, [("Source", "Source"), ("Cells", "Cells")]),
        "",
        "## Score source counts",
        "",
        *demo.markdown_table(source_rows, [("Source", "Source"), ("Cells", "Cells")]),
        "",
        "## Selection ranking",
        "",
        *demo.markdown_table(selection_rows, [("Rank", "Rank"), ("Agent", "Agent"), ("Pass rate", "Pass"), ("Scoreable", "Scoreable")]),
        "",
        "## Later-check ranking",
        "",
        *demo.markdown_table(later_rows, [("Rank", "Rank"), ("Agent", "Agent"), ("Pass rate", "Pass"), ("Scoreable", "Scoreable")]),
        "",
        "Replacement rule: doubled-timeout top-2 rows supersede original Holdout rows only for `codex_gpt_5_4` and `kilo_gpt_5_4` on original Holdout tasks. No separate top-2 chart is used.",
    ]
    demo.write_text(PAID_MATRIX_REPORT, "\n".join(lines) + "\n")


def command_run_paid(args: argparse.Namespace) -> int:
    config = demo.load_config(demo.repo_path(args.config))
    manifest = load_manifest()
    model_gate = demo.model_gate(config)
    if model_gate["status"] != "ready":
        raise RuntimeError(f"model gate is not ready: {model_gate}")
    secret_gate = demo.secret_isolation_gate()
    if secret_gate["status"] != "ready":
        raise RuntimeError(f"secret isolation gate is not ready: {secret_gate}")
    summary = run_missing_cells(config, manifest)
    demo.write_json(demo.result_path("boltons_small_expansion_paid_matrix_summary.json"), summary)
    write_paid_matrix_report(summary)
    return 0 if summary["completed_cells"] == summary["scheduled_cells"] else 2


def write_final_matrix(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_rows = manifest_row_by_task(manifest)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        task = task_rows.get(str(row["task_id"]), {})
        enriched.append(
            {
                **row,
                "task_time": task.get("task_time", ""),
                "task_order": task.get("task_order", ""),
                "source_package": task.get("source_package", ""),
                "code_files": ",".join(task.get("code_files") or []),
                "test_files": ",".join(task.get("test_files") or []),
            }
        )
    demo.write_csv(FINAL_MATRIX, enriched, FINAL_MATRIX_FIELDNAMES)
    return enriched


def pass_rate_for(rows: list[dict[str, Any]], agent_id: str, task_ids: list[str]) -> dict[str, Any]:
    wanted = set(task_ids)
    cells = [row for row in rows if row["agent_id"] == agent_id and row["task_id"] in wanted]
    scoreable = [row for row in cells if row["scoreable_cell"] is True]
    passes = sum(1 for row in scoreable if row["verified_pass"] is True)
    return {
        "pass_rate": None if not scoreable else passes / len(scoreable),
        "pass_count": passes,
        "scoreable_count": len(scoreable),
        "scheduled_count": len(cells),
    }


def selection_vs_later_summary(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    agent_ids = list(manifest["agent_ids"])
    split_rates: dict[str, dict[str, Any]] = {}
    for split, task_ids in [("selection", manifest["selection_tasks"]), ("later_check", manifest["later_check_tasks"])]:
        split_rates[split] = {agent_id: pass_rate_for(rows, agent_id, task_ids) for agent_id in agent_ids}
    matrix = []
    for agent_id in agent_ids:
        selection_rate = split_rates["selection"][agent_id]["pass_rate"]
        later_rate = split_rates["later_check"][agent_id]["pass_rate"]
        name = next((row.get("reviewer_name") for row in rows if row["agent_id"] == agent_id and row.get("reviewer_name")), agent_id)
        matrix.append(
            {
                "agent_id": agent_id,
                "reviewer_name": name,
                "selection_pass_rate": r6(selection_rate),
                "selection_pass_count": split_rates["selection"][agent_id]["pass_count"],
                "selection_scoreable_count": split_rates["selection"][agent_id]["scoreable_count"],
                "later_check_pass_rate": r6(later_rate),
                "later_check_pass_count": split_rates["later_check"][agent_id]["pass_count"],
                "later_check_scoreable_count": split_rates["later_check"][agent_id]["scoreable_count"],
                "later_minus_selection": r6(None if selection_rate is None or later_rate is None else later_rate - selection_rate),
            }
        )
    selection_rank = sorted(matrix, key=lambda row: (-(row["selection_pass_rate"] or 0.0), -row["selection_pass_count"], row["agent_id"]))
    later_rank = sorted(matrix, key=lambda row: (-(row["later_check_pass_rate"] or 0.0), -row["later_check_pass_count"], row["agent_id"]))
    recommendation = selection_rank[0]["agent_id"] if selection_rank else None
    later_top = later_rank[0]["agent_id"] if later_rank else None
    later_best = later_rank[0]["later_check_pass_rate"] or 0.0 if later_rank else 0.0
    recommendation_row = next((row for row in matrix if row["agent_id"] == recommendation), {})
    regret = None if not recommendation_row else later_best - float(recommendation_row.get("later_check_pass_rate") or 0.0)
    return {
        "matrix": matrix,
        "selection_rank": selection_rank,
        "later_check_rank": later_rank,
        "selection_recommendation_agent_id": recommendation,
        "later_check_top_agent_id": later_top,
        "selection_later_top_agree": recommendation == later_top and recommendation is not None,
        "selection_recommendation_regret_on_later": r6(regret),
    }


def write_final_analysis_report(payload: dict[str, Any]) -> None:
    matrix_rows = [
        {
            "Agent": row["reviewer_name"],
            "Selection": row["selection_pass_rate"],
            "Selection cells": f"{row['selection_pass_count']}/{row['selection_scoreable_count']}",
            "Later": row["later_check_pass_rate"],
            "Later cells": f"{row['later_check_pass_count']}/{row['later_check_scoreable_count']}",
            "Delta": row["later_minus_selection"],
        }
        for row in payload["selection_vs_later"]["matrix"]
    ]
    summary = payload["paid_matrix_summary"]
    verdict = "一致" if payload["selection_vs_later"]["selection_later_top_agree"] else "不一致"
    lines = [
        "# Boltons small expansion final analysis",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        f"- Selection tasks: `{payload['task_counts']['selection']}`；later-check tasks: `{payload['task_counts']['later_check']}`。",
        f"- Final displayed cells: `{summary['completed_cells']}`；new paid cells: `{summary['new_paid_cells']}`；reused committed cells: `{summary['reused_committed_cells']}`。",
        f"- Selection recommendation: `{payload['selection_vs_later']['selection_recommendation_agent_id']}`。",
        f"- Later-check top Agent: `{payload['selection_vs_later']['later_check_top_agent_id']}`。",
        f"- Selection/later top agreement: `{verdict}`。",
        f"- Recommendation regret on later-check: `{payload['selection_vs_later']['selection_recommendation_regret_on_later']}`。",
        "",
        "## Final Selection vs later-check matrix",
        "",
        *demo.markdown_table(
            matrix_rows,
            [
                ("Agent", "Agent"),
                ("Selection", "Selection"),
                ("Selection cells", "Selection cells"),
                ("Later", "Later"),
                ("Later cells", "Later cells"),
                ("Later-Selection", "Delta"),
            ],
        ),
        "",
        "## Replacement rule",
        "",
        "原始 Holdout 中 top-2 Agent 的 doubled-timeout rows 在 active matrix 中替换旧 rows；非 top-2 Agent 和从旧 Selection 迁入 later-check 的任务继续使用已提交的 scoreable rows。Phase 1 v2 旧 low-cost rows 因 Agent ID / active policy 不完全一致，未作为四-Agent demo rows 复用。",
        "",
        "## Interpretation",
        "",
        "这是 presentation-oriented boltons demo expansion。它支持在更大的时间有序 Selection/later-check matrix 上做一次可审计 Agent 选型，并检查该推荐在后续任务上的表现；不支持跨仓库、全局 Agent 排名或 predictive-validity proof。",
    ]
    demo.write_text(FINAL_ANALYSIS_REPORT, "\n".join(lines) + "\n")


def command_analyze(args: argparse.Namespace) -> int:
    del args
    manifest = load_manifest()
    rows = persist_combined_outputs(manifest)
    enriched = write_final_matrix(manifest, rows)
    summary = summarize_paid_matrix(manifest, rows)
    selection_later = selection_vs_later_summary(manifest, rows)
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.boltons_small_expansion.summary.v1",
        "generated_at": iso_now(),
        "manifest": demo.display_path(MANIFEST),
        "score_table": demo.display_path(SCORE_TABLE),
        "final_matrix": demo.display_path(FINAL_MATRIX),
        "task_counts": {
            "selection": len(manifest["selection_tasks"]),
            "later_check": len(manifest["later_check_tasks"]),
            "displayed": len(manifest["selection_tasks"]) + len(manifest["later_check_tasks"]),
        },
        "cell_counts": {
            "displayed": len(enriched),
            "new_paid": summary["new_paid_cells"],
            "reused_committed": summary["reused_committed_cells"],
            "scoreable": summary["scoreable_cells"],
        },
        "paid_matrix_summary": summary,
        "selection_vs_later": selection_later,
        "replacement_rule": "doubled-timeout top-2 rows supersede original Holdout rows for codex_gpt_5_4 and kilo_gpt_5_4 only",
        "claim_boundary": {
            "presentation_demo_supported": True,
            "predictive_validity_proven": False,
            "global_agent_ranking_supported": False,
            "cross_repo_generalization_supported": False,
            "raw_estimated_cost_is_actual_billing": False,
        },
    }
    demo.write_json(SUMMARY_JSON, payload)
    write_final_analysis_report(payload)
    return 0


def rate_map(rows: list[dict[str, Any]], task_ids: list[str], agent_ids: list[str]) -> dict[str, dict[str, Any]]:
    return {agent_id: pass_rate_for(rows, agent_id, task_ids) for agent_id in agent_ids}


def forced_top(rates: dict[str, dict[str, Any]]) -> str | None:
    usable = [(agent_id, row["pass_rate"], row["pass_count"]) for agent_id, row in rates.items() if row["pass_rate"] is not None]
    if not usable:
        return None
    usable.sort(key=lambda item: (-float(item[1]), -int(item[2]), item[0]))
    return usable[0][0]


def rolling_metrics(
    rows: list[dict[str, Any]],
    agent_ids: list[str],
    selection_ids: list[str],
    future_ids: list[str],
) -> dict[str, Any]:
    selection_rates = rate_map(rows, selection_ids, agent_ids)
    future_rates = rate_map(rows, future_ids, agent_ids)
    errors = []
    for agent_id in agent_ids:
        sel = selection_rates[agent_id]["pass_rate"]
        fut = future_rates[agent_id]["pass_rate"]
        if sel is not None and fut is not None:
            errors.append(abs(float(sel) - float(fut)))
    selection_top = forced_top(selection_rates)
    future_top = forced_top(future_rates)
    future_best = max((float(row["pass_rate"]) for row in future_rates.values() if row["pass_rate"] is not None), default=0.0)
    regret = None if selection_top is None else future_best - float(future_rates[selection_top]["pass_rate"] or 0.0)
    ranked_selection = sorted(
        [(agent_id, row["pass_rate"]) for agent_id, row in selection_rates.items() if row["pass_rate"] is not None],
        key=lambda item: (-float(item[1]), item[0]),
    )
    gap_agrees = None
    gap = None
    future_gap = None
    if len(ranked_selection) >= 2:
        first, second = ranked_selection[0][0], ranked_selection[1][0]
        gap = float(selection_rates[first]["pass_rate"]) - float(selection_rates[second]["pass_rate"])
        future_gap = float(future_rates[first]["pass_rate"] or 0.0) - float(future_rates[second]["pass_rate"] or 0.0)
        gap_agrees = (gap >= 0 and future_gap >= 0) or (gap <= 0 and future_gap <= 0)
    return {
        "selection_rates": selection_rates,
        "future_rates": future_rates,
        "MAE": r6(None if not errors else sum(errors) / len(errors)),
        "selection_top_agent_id": selection_top,
        "future_top_agent_id": future_top,
        "top_rank_agreement": selection_top == future_top and selection_top is not None,
        "recommendation_regret": r6(regret),
        "selection_top_gap": r6(gap),
        "future_same_pair_gap": r6(future_gap),
        "pass_rate_gap_direction_agreement": gap_agrees,
    }


def random_comparison_for_origin(
    rows: list[dict[str, Any]],
    agent_ids: list[str],
    prior_ids: list[str],
    future_ids: list[str],
    window_size: int,
    seeds: int,
) -> dict[str, Any]:
    if len(prior_ids) < window_size:
        return {"sample_count": 0}
    mae_values: list[float] = []
    regret_values: list[float] = []
    top_agreement_values: list[bool] = []
    for seed in range(seeds):
        rng = random.Random(seed)
        sample = sorted(rng.sample(prior_ids, window_size))
        metrics = rolling_metrics(rows, agent_ids, sample, future_ids)
        if metrics["MAE"] is not None:
            mae_values.append(float(metrics["MAE"]))
        if metrics["recommendation_regret"] is not None:
            regret_values.append(float(metrics["recommendation_regret"]))
        top_agreement_values.append(bool(metrics["top_rank_agreement"]))
    return {
        "sample_count": seeds,
        "MAE_mean": r6(statistics.mean(mae_values) if mae_values else None),
        "MAE_p05": r6(percentile(mae_values, 5) if mae_values else None),
        "MAE_p95": r6(percentile(mae_values, 95) if mae_values else None),
        "recommendation_regret_mean": r6(statistics.mean(regret_values) if regret_values else None),
        "top_rank_agreement_rate": r6(sum(top_agreement_values) / len(top_agreement_values) if top_agreement_values else None),
    }


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil((p / 100.0) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def strict_rolling_origin(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    window_size: int = DEFAULT_ROLLING_WINDOW_SIZE,
    write_outputs: bool = True,
) -> dict[str, Any]:
    task_rows = [
        row
        for row in sorted(manifest["task_rows"], key=lambda item: (parse_time(item["task_time"]), str(item["task_id"])))
        if row["final_role"] in {"selection", "later_check"}
    ]
    task_ids = [row["task_id"] for row in task_rows]
    row_by_task = {row["task_id"]: row for row in task_rows}
    agent_ids = list(manifest["agent_ids"])
    origin_indices = [index for index in [10, 20, 30, 40] if index >= window_size and len(task_ids) - index >= 8]
    slice_rows: list[dict[str, Any]] = []
    origin_summaries: list[dict[str, Any]] = []
    for origin_index in origin_indices:
        prior_ids = task_ids[:origin_index]
        selection_ids = task_ids[origin_index - window_size : origin_index]
        future_ids = task_ids[origin_index:]
        metrics = rolling_metrics(rows, agent_ids, selection_ids, future_ids)
        random_summary = random_comparison_for_origin(rows, agent_ids, prior_ids, future_ids, window_size, DEFAULT_RANDOM_SEEDS)
        origin_id = f"origin_{origin_index:02d}_{row_by_task[selection_ids[-1]]['task_time'][:10]}"
        for agent_id in agent_ids:
            selection_rate = metrics["selection_rates"][agent_id]
            future_rate = metrics["future_rates"][agent_id]
            slice_rows.append(
                {
                    "origin_id": origin_id,
                    "origin_index": origin_index,
                    "origin_time": row_by_task[selection_ids[-1]]["task_time"],
                    "selection_start_time": row_by_task[selection_ids[0]]["task_time"],
                    "selection_end_time": row_by_task[selection_ids[-1]]["task_time"],
                    "future_start_time": row_by_task[future_ids[0]]["task_time"],
                    "future_end_time": row_by_task[future_ids[-1]]["task_time"],
                    "agent_id": agent_id,
                    "reviewer_name": next((row.get("reviewer_name") for row in rows if row["agent_id"] == agent_id), agent_id),
                    "selection_task_count": len(selection_ids),
                    "future_task_count": len(future_ids),
                    "selection_scoreable_count": selection_rate["scoreable_count"],
                    "future_scoreable_count": future_rate["scoreable_count"],
                    "selection_pass_rate": r6(selection_rate["pass_rate"]),
                    "future_pass_rate": r6(future_rate["pass_rate"]),
                    "absolute_error": r6(
                        None
                        if selection_rate["pass_rate"] is None or future_rate["pass_rate"] is None
                        else abs(float(selection_rate["pass_rate"]) - float(future_rate["pass_rate"]))
                    ),
                    "selection_pass_count": selection_rate["pass_count"],
                    "future_pass_count": future_rate["pass_count"],
                }
            )
        origin_summaries.append(
            {
                "origin_id": origin_id,
                "origin_index": origin_index,
                "origin_time": row_by_task[selection_ids[-1]]["task_time"],
                "selection_task_ids": selection_ids,
                "future_task_ids_sha256": workspace.sha256_text("\n".join(future_ids)),
                "future_task_count": len(future_ids),
                **{key: value for key, value in metrics.items() if key not in {"selection_rates", "future_rates"}},
                "random_same_budget": random_summary,
            }
        )
    mae_values = [float(row["MAE"]) for row in origin_summaries if row.get("MAE") is not None]
    regret_values = [float(row["recommendation_regret"]) for row in origin_summaries if row.get("recommendation_regret") is not None]
    gap_values = [row["pass_rate_gap_direction_agreement"] for row in origin_summaries if row.get("pass_rate_gap_direction_agreement") is not None]
    summary = {
        "schema_version": "barcarolle.agent_selection_demo.boltons_strict_rolling_origin.v1",
        "generated_at": iso_now(),
        "source_matrix": demo.display_path(FINAL_MATRIX),
        "uses_actual_task_time": True,
        "does_not_use_heldout_split_labels_as_origins": True,
        "selection_window_size": window_size,
        "origin_count": len(origin_summaries),
        "origins": origin_summaries,
        "overall": {
            "MAE_mean": r6(statistics.mean(mae_values) if mae_values else None),
            "top_rank_agreement_rate": r6(
                sum(1 for row in origin_summaries if row["top_rank_agreement"]) / len(origin_summaries) if origin_summaries else None
            ),
            "mean_recommendation_regret": r6(statistics.mean(regret_values) if regret_values else None),
            "max_recommendation_regret": r6(max(regret_values) if regret_values else None),
            "pass_rate_gap_direction_agreement_rate": r6(
                sum(1 for value in gap_values if value is True) / len(gap_values) if gap_values else None
            ),
        },
        "random_comparison": {
            "sample_count_per_origin": DEFAULT_RANDOM_SEEDS,
            "directional_only": True,
            "mean_random_MAE": r6(
                statistics.mean(
                    float(origin["random_same_budget"]["MAE_mean"])
                    for origin in origin_summaries
                    if origin.get("random_same_budget", {}).get("MAE_mean") is not None
                )
                if any(origin.get("random_same_budget", {}).get("MAE_mean") is not None for origin in origin_summaries)
                else None
            ),
        },
        "claim_boundary": {
            "historical_pseudo_future_only": True,
            "predictive_validity_proven": False,
        },
    }
    if write_outputs:
        demo.write_csv(ROLLING_SLICES, slice_rows, ROLLING_FIELDNAMES)
        demo.write_json(ROLLING_SUMMARY, summary)
    return summary


def write_rolling_report(summary: dict[str, Any]) -> None:
    origin_rows = [
        {
            "Origin": row["origin_id"],
            "Time": row["origin_time"],
            "Future": row["future_task_count"],
            "MAE": row["MAE"],
            "Top agree": row["top_rank_agreement"],
            "Regret": row["recommendation_regret"],
            "Gap agree": row["pass_rate_gap_direction_agreement"],
            "Random MAE": row.get("random_same_budget", {}).get("MAE_mean"),
        }
        for row in summary["origins"]
    ]
    overall = summary["overall"]
    lines = [
        "# Boltons strict chronological rolling-origin diagnostics",
        "",
        f"生成时间：`{summary['generated_at']}`。",
        "",
        "本诊断只用 expanded boltons final matrix，并按真实 `task_time` 形成 origin；没有把普通 Selection/Holdout label 混入 rolling-origin claim。",
        "",
        f"- Origins: `{summary['origin_count']}`。",
        f"- Selection window size per origin: `{summary['selection_window_size']}` tasks。",
        f"- Overall MAE mean: `{overall['MAE_mean']}`。",
        f"- Top-rank agreement rate: `{overall['top_rank_agreement_rate']}`。",
        f"- Mean recommendation regret: `{overall['mean_recommendation_regret']}`；max regret `{overall['max_recommendation_regret']}`。",
        f"- Gap-direction agreement rate: `{overall['pass_rate_gap_direction_agreement_rate']}`。",
        f"- Same-budget random mean MAE: `{summary['random_comparison']['mean_random_MAE']}`。",
        "",
        "## Origins",
        "",
        *demo.markdown_table(
            origin_rows,
            [
                ("Origin", "Origin"),
                ("Time", "Time"),
                ("Future tasks", "Future"),
                ("MAE", "MAE"),
                ("Top agree", "Top agree"),
                ("Regret", "Regret"),
                ("Gap agree", "Gap agree"),
                ("Random MAE", "Random MAE"),
            ],
        ),
        "",
        "这些结果是 historical pseudo-future diagnostics，只能作为 directional evidence；不能单独证明 predictive validity 或 selector optimality。",
    ]
    demo.write_text(ROLLING_REPORT, "\n".join(lines) + "\n")


def command_rolling(args: argparse.Namespace) -> int:
    del args
    manifest = load_manifest()
    rows = read_csv(FINAL_MATRIX) if FINAL_MATRIX.exists() else persist_combined_outputs(manifest)
    normalized = []
    for row in rows:
        normalized.append({**row, "scoreable_cell": csv_bool(row.get("scoreable_cell")), "verified_pass": csv_bool(row.get("verified_pass"))})
    summary = strict_rolling_origin(manifest, normalized)
    write_rolling_report(summary)
    return 0


def write_demo_report(final_summary: dict[str, Any], rolling: dict[str, Any]) -> None:
    matrix_rows = [
        {
            "Agent": row["reviewer_name"],
            "Selection": row["selection_pass_rate"],
            "Later": row["later_check_pass_rate"],
            "Delta": row["later_minus_selection"],
        }
        for row in final_summary["selection_vs_later"]["matrix"]
    ]
    lines = [
        "# Boltons small expansion demo report",
        "",
        f"生成时间：`{iso_now()}`。",
        "",
        "## What changed",
        "",
        "本次把 boltons demo 从旧的 `20` Selection tasks / `10` Holdout tasks 展示，扩展为严格按 `task_time` 排序的 `30` Selection tasks / `20` later-check tasks。新增任务来自 Phase 1 v2 no-paid certification 已证明 release-eligible 的 boltons target commits；没有切换到 attrs、click 或其他 fallback repository。",
        "",
        "## Final counts",
        "",
        f"- Displayed tasks: `{final_summary['task_counts']['displayed']}` (`{final_summary['task_counts']['selection']}` Selection + `{final_summary['task_counts']['later_check']}` later-check)。",
        f"- Displayed cells: `{final_summary['cell_counts']['displayed']}`。",
        f"- New paid cells: `{final_summary['cell_counts']['new_paid']}` / hard cap `{NEW_PAID_CELL_HARD_CAP}`。",
        f"- Reused committed cells: `{final_summary['cell_counts']['reused_committed']}`。",
        f"- Scoreable cells: `{final_summary['cell_counts']['scoreable']}`。",
        "",
        "## Selection vs later-check matrix",
        "",
        *demo.markdown_table(matrix_rows, [("Agent", "Agent"), ("Selection", "Selection"), ("Later", "Later"), ("Later-Selection", "Delta")]),
        "",
        "## Strict chronological diagnostics",
        "",
        f"- Origins: `{rolling['origin_count']}`。",
        f"- MAE mean: `{rolling['overall']['MAE_mean']}`。",
        f"- Top-rank agreement: `{rolling['overall']['top_rank_agreement_rate']}`。",
        f"- Mean/max regret: `{rolling['overall']['mean_recommendation_regret']}` / `{rolling['overall']['max_recommendation_regret']}`。",
        f"- Same-budget random mean MAE: `{rolling['random_comparison']['mean_random_MAE']}`。",
        "",
        "## Cost and usage caveats",
        "",
        "Cost values are estimated from adapter token usage when available and conservative per-cell estimates when usage is missing. They are not actual billing unless `billed_cost_usd` is populated.",
        "",
        "## Supported PPT claim",
        "",
        "On boltons, the expanded target-repo benchmark can compare complete Agents on a larger time-ordered Selection/later-check matrix, make an auditable recommendation, and evaluate how that recommendation behaves on later tasks. Strict chronological historical checks provide directional evidence that this is a measurable predictive-evaluation problem.",
        "",
        "## Unsupported claims",
        "",
        "- Predictive validity is proven.",
        "- The selected Agent is globally best.",
        "- Boltons results generalize to all repositories.",
        "- The selector is statistically superior or optimal.",
        "- Raw cost estimates are actual billing when usage coverage is incomplete.",
    ]
    demo.write_text(DEMO_REPORT, "\n".join(lines) + "\n")


def command_report(args: argparse.Namespace) -> int:
    del args
    final_summary = demo.read_json(SUMMARY_JSON)
    rolling = demo.read_json(ROLLING_SUMMARY)
    write_demo_report(final_summary, rolling)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the boltons small expansion package.")
    parser.add_argument("--config", default=str(demo.DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    freeze = subcommands.add_parser("freeze")
    freeze.add_argument("--selection-count", type=int, default=DEFAULT_SELECTION_COUNT)
    freeze.add_argument("--later-count", type=int, default=DEFAULT_LATER_COUNT)
    subcommands.add_parser("run-paid")
    subcommands.add_parser("analyze")
    subcommands.add_parser("rolling")
    subcommands.add_parser("report")
    args = parser.parse_args()
    if args.command == "freeze":
        return command_freeze(args)
    if args.command == "run-paid":
        return command_run_paid(args)
    if args.command == "analyze":
        return command_analyze(args)
    if args.command == "rolling":
        return command_rolling(args)
    if args.command == "report":
        return command_report(args)
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
