from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tuning_artifacts import ARTIFACT_SCHEMA_VERSION, materialize_artifact, validate_artifact, with_computed_hash


ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [ROOT, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from experiments.demo_common import costs as demo_costs  # noqa: E402
from experiments.demo_common import workspace_inputs  # noqa: E402
import selection_snapshot  # noqa: E402
import task_generator_evolution as taskgen  # noqa: E402
import workspace_acut_run as workspace  # noqa: E402


DEMO_REL = Path("experiments/agent_tuning_demo")
RESULTS = ROOT / DEMO_REL / "results"
REPORTS = ROOT / DEMO_REL / "reports"
CANDIDATE_DIR = RESULTS / "agent_tuning_demo_candidate_artifacts"
CHOSEN_DIR = RESULTS / "agent_tuning_demo_chosen_artifact"
PHASE0_EXP = ROOT / "experiments" / "phase0_headroom"

SCHEMA = "barcarolle.agent_tuning_demo.autonomous_completion.v1"
PRIMARY_REPO = "mypy"
PRIMARY_ORIGIN = "origin_40"
TARGET_AGENT_ID = "kilo_gpt_5_4_mini"
TARGET_AGENT_NAME = "Kilo + GPT low-cost"
TARGET_HARNESS = "kilo"
TARGET_MODEL = "gpt-5.4-mini"
TARGET_SURFACE = "repo_AGENTS_md"
TARGET_ARTIFACT_TYPE = "agents_md_appendix"
TARGET_ARTIFACT_PATH = "AGENTS.md"
RESULT_PREFIX = "agent_tuning_demo_2026_06_17"
SELECTED_SIZE = 20
TRAIN_FEEDBACK_COUNT = 12
DEV_EVAL_COUNT = 8
FUTURE_HOLDOUT_COUNT = 20
MAX_CONCURRENCY_DEFAULT = 2
MAX_CONCURRENCY_HARD_CAP = 4
SCOREABLE_STATUSES = {"verified_pass", "verified_fail"}

PREREG_JSON = RESULTS / "agent_tuning_demo_preregistration.json"
PREREG_REPORT = REPORTS / "agent_tuning_demo_preregistration_zh.md"
BATCH_PLAN = RESULTS / "agent_tuning_demo_batch_plan.jsonl"
COST_LEDGER = RESULTS / "agent_tuning_demo_cost_ledger.jsonl"
COST_SUMMARY_JSON = RESULTS / "agent_tuning_demo_cost_summary.json"
COST_SUMMARY_REPORT = REPORTS / "agent_tuning_demo_cost_summary_zh.md"
SELECTED_BASELINE_CSV = RESULTS / "agent_tuning_demo_selected_baseline.csv"
BASELINE_MATRIX_CSV = RESULTS / "agent_tuning_demo_baseline_matrix.csv"
BASELINE_SUMMARY_JSON = RESULTS / "agent_tuning_demo_baseline_summary.json"
BASELINE_REPORT = REPORTS / "agent_tuning_demo_baseline_summary_zh.md"
FEEDBACK_JSONL = RESULTS / "agent_tuning_demo_feedback_export.jsonl"
FEEDBACK_REPORT = REPORTS / "agent_tuning_demo_feedback_export_zh.md"
CANDIDATES_JSON = RESULTS / "agent_tuning_demo_candidate_artifacts.json"
CANDIDATES_REPORT = REPORTS / "agent_tuning_demo_candidate_artifacts_zh.md"
DEV_EVAL_CSV = RESULTS / "agent_tuning_demo_dev_eval.csv"
DEV_EVAL_SUMMARY_JSON = RESULTS / "agent_tuning_demo_dev_eval_summary.json"
DEV_EVAL_REPORT = REPORTS / "agent_tuning_demo_dev_eval_zh.md"
CHOSEN_JSON = RESULTS / "agent_tuning_demo_chosen_artifact.json"
FUTURE_CSV = RESULTS / "agent_tuning_demo_future_holdout.csv"
FUTURE_SUMMARY_JSON = RESULTS / "agent_tuning_demo_future_holdout_summary.json"
FUTURE_REPORT = REPORTS / "agent_tuning_demo_future_holdout_zh.md"
FINAL_JSON = RESULTS / "agent_tuning_demo_final_closeout.json"
FINAL_REPORT = REPORTS / "agent_tuning_demo_final_report_zh.md"
FINAL_CLOSEOUT_REPORT = REPORTS / "agent_tuning_demo_final_closeout_zh.md"

SCORE_FIELDS = [
    "stage",
    "condition",
    "candidate_id",
    "repository",
    "origin_id",
    "agent_id",
    "reviewer_name",
    "harness",
    "model",
    "surface",
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
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "endpoint_proof_status",
    "artifact_hash",
    "patch_sha256",
    "run_id",
    "result_artifact_path",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def bjt_now() -> str:
    return datetime.now(timezone.utc).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows).rstrip())


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    rows = read_jsonl(path)
    rows.append(row)
    write_jsonl(path, rows)


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def split_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [part for part in str(value or "").split(";") if part]


def bool_from_cell(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def endpoint_status() -> dict[str, Any]:
    base = os.environ.get("LLM_BASE_URL", "")
    key = os.environ.get("LLM_API_KEY", "")
    parsed = urllib.parse.urlparse(base)
    host = parsed.netloc or base
    return {
        "llm_base_url_present": bool(base),
        "llm_api_key_present": bool(key),
        "endpoint_host_hash": hashlib.sha256(host.encode()).hexdigest()[:12] if host else "",
        "api_key_fingerprint": hashlib.sha256(key.encode()).hexdigest()[:8] if key else "",
        "endpoint_proof_status": "llm_endpoint_proxy_secret_isolated" if base and key else "missing_endpoint_env",
    }


def require_endpoint_env() -> None:
    missing = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing)}")


def load_manifest(repo_id: str) -> dict[str, Any]:
    return read_json(RESULTS / f"{repo_id}_task_generator_certified_manifest.json")


def load_windows(repo_id: str) -> dict[str, Any]:
    return read_json(RESULTS / f"{repo_id}_task_generator_rolling_origin_windows.json")


def task_rows_by_id(repo_id: str) -> dict[str, dict[str, Any]]:
    return {row["task_id"]: row for row in load_manifest(repo_id)["tasks"]}


def selected_window(repo_id: str = PRIMARY_REPO, origin_id: str = PRIMARY_ORIGIN) -> dict[str, Any]:
    for window in load_windows(repo_id)["windows"]:
        if window["origin_id"] == origin_id:
            return window
    raise KeyError(f"window not found: {repo_id} {origin_id}")


def select_history_benchmark(
    window: dict[str, Any],
    rows_by_id: dict[str, dict[str, Any]],
    *,
    selection_size: int = SELECTED_SIZE,
) -> list[str]:
    allowed_ids = list(window["selected_benchmark_from_history"]["allowed_task_ids"])
    future_ids = set(window["future_holdout_after_origin"]["task_ids"])
    if future_ids & set(allowed_ids):
        raise ValueError("history pool overlaps future holdout")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task_id in allowed_ids:
        row = rows_by_id[task_id]
        groups[str(row.get("module_family") or "unknown")].append(row)
    for group in groups.values():
        group.sort(key=lambda row: (float(row.get("certification_duration_seconds") or 9999), str(row.get("task_time") or ""), row["task_id"]))

    selected: list[str] = []
    family_names = sorted(groups)
    while len(selected) < selection_size and any(groups.values()):
        for family in family_names:
            if not groups[family]:
                continue
            selected.append(groups[family].pop(0)["task_id"])
            if len(selected) == selection_size:
                break
    if len(selected) != selection_size:
        raise ValueError(f"could only select {len(selected)} history tasks")
    return selected


def protocol_payload() -> dict[str, Any]:
    repo_id = PRIMARY_REPO
    origin_id = PRIMARY_ORIGIN
    rows_by_id = task_rows_by_id(repo_id)
    window = selected_window(repo_id, origin_id)
    selected_ids = select_history_benchmark(window, rows_by_id)
    train_ids = selected_ids[:TRAIN_FEEDBACK_COUNT]
    dev_ids = selected_ids[TRAIN_FEEDBACK_COUNT : TRAIN_FEEDBACK_COUNT + DEV_EVAL_COUNT]
    future_ids = list(window["future_holdout_after_origin"]["task_ids"])[:FUTURE_HOLDOUT_COUNT]
    endpoint = endpoint_status()
    future_hash = sha256_text("\n".join(future_ids))
    return {
        "schema_version": f"{SCHEMA}.preregistration.v1",
        "generated_at": iso_now(),
        "status": "frozen_before_new_paid_result_inspection",
        "target_repositories": {
            "primary": {
                "repo_id": repo_id,
                "repo_url": "https://github.com/python/mypy.git",
                "local_repo": "experiments/phase0_headroom/external_repos/mypy",
                "role": "paid before_after primary",
                "selection_reason": "single verifier profile, lower certified verifier median than Sphinx, and explicit TypeCheckSuite/test-data oracle shape",
            },
            "secondary": {
                "repo_id": "sphinx",
                "role": "no-paid task-supply sanity unless the primary result is inconclusive and time remains",
                "selection_reason": "prepared certified manifest exists, but verifier profile mix is broader and expected paid wall-clock risk is higher",
            },
        },
        "rolling_origin_window": {
            "repo_id": repo_id,
            "origin_id": origin_id,
            "shape": "history_pool_before_origin -> selected_benchmark_from_history -> future_holdout_after_origin",
            "history_pool_count": window["history_pool_before_origin"]["task_count"],
            "selected_benchmark_from_history_task_ids": selected_ids,
            "selected_benchmark_selection_rule": "metadata-only round-robin by module_family from the pre-origin history pool, ordered by certification duration, task_time, task_id",
            "train_feedback_task_ids": train_ids,
            "dev_eval_task_ids": dev_ids,
            "future_holdout_count": len(future_ids),
            "future_holdout_task_ids_withheld_until_artifact_freeze": True,
            "future_holdout_task_ids_sha256": future_hash,
            "future_holdout_source": "mypy_task_generator_rolling_origin_windows.json:origin_40.future_holdout_after_origin.task_ids",
        },
        "baseline_agent": {
            "agent_id": TARGET_AGENT_ID,
            "agent_name": TARGET_AGENT_NAME,
            "harness": TARGET_HARNESS,
            "model": TARGET_MODEL,
            "surface": "none",
        },
        "tuned_agent_surface": {
            "agent_id": TARGET_AGENT_ID,
            "agent_name": TARGET_AGENT_NAME,
            "harness": TARGET_HARNESS,
            "model": TARGET_MODEL,
            "surface": TARGET_SURFACE,
            "artifact_type": TARGET_ARTIFACT_TYPE,
            "artifact_workspace_path": TARGET_ARTIFACT_PATH,
            "injection_path": "materialize repo-local AGENTS.md appendix before Kilo run, then discard solver workspace after capture",
        },
        "tuner_inputs": {
            "allowed": [
                "selected train-feedback task IDs",
                "selected train-feedback baseline statuses and failure labels",
                "selected train-feedback module_family and editable implementation paths",
                "historical task generator metadata before the origin",
            ],
            "withheld": [
                "future holdout task IDs until artifact hash freeze",
                "future holdout outcomes until after candidate choice",
                "raw prompts, raw completions, raw transcripts, solver workspaces, verifier workspaces, and hidden oracle contents",
            ],
        },
        "score_join_rules": {
            "scoreable_statuses": sorted(SCOREABLE_STATUSES),
            "verified_pass": "verifier status verified_pass",
            "verified_fail": "verifier status verified_fail",
            "invalid_unscoreable": "empty diff, policy violation, adapter timeout/error, patch apply failure, verifier infrastructure error, or timeout",
            "test_edits": "policy violation and failed cell",
            "out_of_scope_edits": "policy violation and failed cell",
        },
        "timeouts": {
            "agent_timeout_seconds": 1800,
            "adapter_cleanup_grace_seconds": 60,
            "outer_timeout_seconds": 1860,
            "verifier_timeout_seconds": 360,
        },
        "paid_scheduler": {
            "entry_point": "uv run --project experiments/phase1_compiler python experiments/agent_tuning_demo/tools/agent_tuning_demo_run.py run-stage",
            "max_concurrency_default": MAX_CONCURRENCY_DEFAULT,
            "max_concurrency_hard_cap": MAX_CONCURRENCY_HARD_CAP,
            "resume_policy": "idempotent skip by stage, condition, task_id in committed sanitized CSVs; raw retry is not launched once a sanitized row exists",
            "duplicate_cell_prevention": "stable run_id per stage/condition/agent/task/artifact hash",
            "cost_ledger_strategy": "main process collects worker results and rewrites a deterministic sanitized ledger with cumulative cost",
            "workspace_isolation": "separate solver/verifier workspaces under ignored phase0 workspace namespace per run_id",
            "endpoint_proof_per_worker": "LLM_BASE_URL/LLM_API_KEY checked in parent and Kilo adapter; adapter routes through llm_endpoint_proxy with isolated dummy child key",
            "sequential_fallback_rule": "allowed only for a small remaining batch, checkpoint mode, or if bounded concurrency becomes the blocker",
            "paid_smoke": "first selected-baseline cell is run as a one-cell paid scheduler smoke and then skipped by the larger selected-baseline batch",
        },
        "retry_policy": {
            "outer_retries": 0,
            "repeat_policy": "no automatic paid repeats; rerun only if a repairable harness bug is fixed and the prior cell is explicitly marked superseded in a report",
        },
        "cost_accounting": {
            "ledger": display_path(COST_LEDGER),
            "summary": display_path(COST_SUMMARY_JSON),
            "conservative_missing_usage_estimate_usd": conservative_cell_estimate(),
            "pricing_source": "selection_input_snapshot pricing_per_1m_tokens_usd for observed token estimates",
        },
        "success_criteria": {
            "preferred": "tuned future holdout paired net wins > 0 with no higher invalid/unscoreable count",
            "acceptable_neutral_or_negative": "two train-only candidate artifacts attempted; dev/future before-after completed; final report states no improvement or regression and preserves claim boundary",
            "dev_gate": "choose a positive dev candidate if one exists; otherwise choose the least-regressing non-infrastructure candidate after both serious local artifacts are evaluated",
        },
        "stop_conditions": [
            "agent_tuning_demo_complete",
            "deadline_checkpoint_2026_06_18_0800_bjt",
            "missing LLM_BASE_URL or LLM_API_KEY after sourcing ~/.zshrc",
            "cost ledger cannot be updated after paid calls",
            "future holdout IDs or outcomes enter feedback/artifact proposal before artifact hash freeze",
        ],
        "endpoint_preflight": endpoint,
        "paid_cells_planned": {
            "selected_baseline": SELECTED_SIZE,
            "dev_tuned_candidates": DEV_EVAL_COUNT * 2,
            "future_baseline": FUTURE_HOLDOUT_COUNT,
            "future_tuned": FUTURE_HOLDOUT_COUNT,
            "total_solver_agent_cells": SELECTED_SIZE + DEV_EVAL_COUNT * 2 + FUTURE_HOLDOUT_COUNT * 2,
        },
    }


def conservative_cell_estimate() -> float:
    config = selection_snapshot.selection_config()
    return float(config["run_policy"]["conservative_cell_estimate_usd"])


def write_preregistration() -> None:
    payload = protocol_payload()
    write_json(PREREG_JSON, payload)
    write_cost_summary()
    rows = [
        ("Primary repo", payload["target_repositories"]["primary"]["repo_id"]),
        ("Origin", payload["rolling_origin_window"]["origin_id"]),
        ("Selected benchmark", len(payload["rolling_origin_window"]["selected_benchmark_from_history_task_ids"])),
        ("Train feedback", len(payload["rolling_origin_window"]["train_feedback_task_ids"])),
        ("Dev eval", len(payload["rolling_origin_window"]["dev_eval_task_ids"])),
        ("Future holdout", payload["rolling_origin_window"]["future_holdout_count"]),
        ("Planned paid cells", payload["paid_cells_planned"]["total_solver_agent_cells"]),
        ("Max concurrency", payload["paid_scheduler"]["max_concurrency_default"]),
    ]
    lines = [
        "# Agent Tuning Demo preregistration",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        "## 冻结协议",
        "",
        "| Item | Value |",
        "| --- | --- |",
        *[f"| {key} | `{value}` |" for key, value in rows],
        "",
        "本轮使用 corrected rolling-origin 形状：`history_pool_before_origin -> selected_benchmark_from_history -> future_holdout_after_origin`。",
        "selected benchmark 只从 origin 前历史池选择；future holdout ID 在 artifact hash freeze 前只以 hash 形式记录，不进入反馈或候选 artifact。",
        "",
        "## Agent 与 artifact",
        "",
        f"- Baseline: `{TARGET_AGENT_NAME}` / `{TARGET_MODEL}` / `{TARGET_HARNESS}`。",
        f"- Tuned surface: repo-local `{TARGET_ARTIFACT_PATH}` appendix, injected as `{TARGET_SURFACE}`。",
        "- Tuner/proposer: train-only local rule proposer first; no LLM proposer unless later iterations need it and ledger records the call.",
        "",
        "## Scheduler",
        "",
        f"- Entry point: `{payload['paid_scheduler']['entry_point']}`。",
        f"- Default concurrency: `{MAX_CONCURRENCY_DEFAULT}`, hard cap `{MAX_CONCURRENCY_HARD_CAP}`。",
        "- One selected-baseline paid cell is the scheduler smoke; the later selected-baseline batch skips it by stable row key.",
        "- Raw prompts/completions/transcripts/workspaces are not committed; raw adapter artifacts stay under ignored phase0 paths.",
        "",
        "## Endpoint proof",
        "",
        f"- `LLM_BASE_URL` present: `{payload['endpoint_preflight']['llm_base_url_present']}`。",
        f"- `LLM_API_KEY` present: `{payload['endpoint_preflight']['llm_api_key_present']}`。",
        f"- Endpoint host hash: `{payload['endpoint_preflight']['endpoint_host_hash']}`。",
        f"- Key fingerprint: `{payload['endpoint_preflight']['api_key_fingerprint']}`。",
        "",
    ]
    write_text(PREREG_REPORT, "\n".join(lines))


def target_candidate_config() -> dict[str, Any]:
    return {
        "agent_id": TARGET_AGENT_ID,
        "reviewer_name": TARGET_AGENT_NAME,
        "harness": TARGET_HARNESS,
        "model": TARGET_MODEL,
        "adapter_script": "experiments/phase0_headroom/tools/kilo_workspace_adapter.py",
        "timeout_seconds": 1800,
        "completion_mode": "strict-final",
    }


def workspace_config() -> dict[str, Any]:
    base = selection_snapshot.selection_config()
    return {
        "run_policy": {
            **base["run_policy"],
            "adapter_cleanup_grace_seconds": 60,
            "conservative_cell_estimate_usd": conservative_cell_estimate(),
            "verifier_timeout_seconds": 360,
        },
        "pricing_per_1m_tokens_usd": base["pricing_per_1m_tokens_usd"],
    }


def adapter_config() -> workspace.AdapterConfig:
    return workspace_inputs.adapter_config_for(workspace_config(), target_candidate_config(), command_template_source="agent_tuning_demo_autonomous_completion")


def source_repo_for(repo_id: str) -> Path:
    return PHASE0_EXP / "external_repos" / repo_id


def verifier_command_for(row: dict[str, Any]) -> list[str]:
    repo_id = row["repo_id"]
    entry_points = split_field(row.get("verifier_entry_points"))
    if repo_id == "mypy":
        return taskgen.mypy_command({**row, "verifier_entry_points": entry_points}, "3.12", "pytest>=8,<10")
    raise ValueError(f"unsupported repo for paid runner: {repo_id}")


def task_statement(row: dict[str, Any]) -> str:
    impl_paths = split_field(row.get("changed_implementation_files"))
    entry_points = split_field(row.get("verifier_entry_points"))
    provenance = row.get("solver_visible_statement_provenance") or "public repository history"
    source_confidence = row.get("source_confidence_label") or "unknown"
    module_family = row.get("module_family") or "unknown"
    visible_command = " ".join(verifier_command_for(row))
    return "\n".join(
        [
            "Repair the target repository behavior described by the approved public context.",
            f"Public context provenance label: {provenance}.",
            f"Task family: {module_family}. Source confidence: {source_confidence}.",
            f"Focus implementation path(s): {', '.join(impl_paths)}.",
            f"Verifier entry point names: {', '.join(entry_points)}.",
            "Preserve existing public behavior and keep the patch as narrow as possible.",
            f"Visible local check command shape: `{visible_command}`.",
            "Do not edit tests, test-data files, hidden verifier files, generated metadata, caches, lockfiles, or files outside the listed editable implementation paths.",
        ]
    )


def package_for(row: dict[str, Any], stage: str) -> workspace.TaskPackage:
    test_paths = [*split_field(row.get("changed_test_files")), *split_field(row.get("support_oracle_files"))]
    return workspace.TaskPackage(
        task_id=row["task_id"],
        repo_id=row["repo_id"],
        split=stage,
        source_repo=source_repo_for(row["repo_id"]),
        base_commit=row["base_commit"],
        target_commit=row["target_commit"],
        solver_facing_statement=task_statement(row),
        verifier_command=workspace.with_editable_current_worktree(workspace.absolute_uv_project(verifier_command_for(row), PHASE0_EXP)),
        hidden_files={},
        allowed_code_paths=split_field(row.get("changed_implementation_files")),
        test_paths=sorted(set(test_paths)),
        timeout_seconds=360,
        scope_boundaries="implementation files only; tests, test-data, support fixtures, and verifier files are prohibited",
        metadata={
            "task_time": row.get("task_time"),
            "statement_source": row.get("solver_visible_statement_provenance"),
            "source_context_status": row.get("source_confidence_label"),
            "verifier_command_metadata": {
                "verifier_profile": row.get("verifier_profile"),
                "verifier_entry_points": split_field(row.get("verifier_entry_points")),
            },
        },
    )


def run_workspace_cell_with_artifact(
    package: workspace.TaskPackage,
    config: workspace.AdapterConfig,
    run_id: str,
    stage: str,
    condition: str,
    artifact: dict[str, Any] | None,
) -> workspace.CellResult:
    namespace = workspace.artifact_namespace(f"{RESULT_PREFIX}_{stage}_{condition}", config.adapter_id)
    raw_dir = PHASE0_EXP / workspace.RAW_REL / namespace / run_id
    workspace_root = PHASE0_EXP / workspace.WORKSPACE_REL / namespace / run_id
    solver_workspace = workspace_root / "solver"
    verifier_workspace = workspace_root / "verifier"
    if solver_workspace.exists():
        shutil.rmtree(solver_workspace)
    if verifier_workspace.exists():
        shutil.rmtree(verifier_workspace)
    workspace.archive_tree(package.source_repo, package.base_commit, solver_workspace)
    injection_record = None
    if artifact is not None:
        injection_record = materialize_artifact(solver_workspace, artifact, run_id=run_id, surface=TARGET_SURFACE)
    workspace.initialize_workspace_git(solver_workspace)
    statement_file = workspace.write_statement_file(solver_workspace, package)
    raw_dir.mkdir(parents=True, exist_ok=True)
    command = workspace.render_command(
        config.command_template,
        workspace=solver_workspace,
        statement_file=statement_file,
        task_id=package.task_id,
        run_id=run_id,
        raw_dir=raw_dir,
        timeout_seconds=config.timeout_seconds,
    )
    start = time.monotonic()
    acut = workspace.run_command(command, solver_workspace, timeout=config.timeout_seconds, env=os.environ.copy())
    latency = round(time.monotonic() - start, 3)
    stdout_path = raw_dir / "acut_stdout.txt"
    stderr_path = raw_dir / "acut_stderr.txt"
    stdout_path.write_text(acut.stdout, encoding="utf-8")
    stderr_path.write_text(acut.stderr, encoding="utf-8")
    patch_text = workspace.capture_diff(solver_workspace)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_sha = workspace.sha256_file(patch_path)
    base_submission = {
        "schema_version": "barcarolle.workspace_acut_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": config.adapter_id,
        "acut_id": config.acut_id,
        "harness_name": config.harness_name,
        "model_or_agent_name": config.model_or_agent_name,
        "command_template_source": config.command_template_source,
        "endpoint_proof_status": config.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "patch_source": "git_diff_after_workspace_run",
        "patch_sha256": patch_sha,
        "latency_seconds": latency,
        "adapter_timed_out": acut.timed_out,
        "raw_artifacts": {
            "stdout": str(stdout_path.relative_to(PHASE0_EXP)),
            "stderr": str(stderr_path.relative_to(PHASE0_EXP)),
            "patch": str(patch_path.relative_to(PHASE0_EXP)),
        },
        "task_package_metadata": workspace.package_submission_metadata(package),
        "agent_tuning_demo_condition": condition,
        "agent_tuning_demo_artifact_hash": None if artifact is None else artifact["hash"],
        "agent_tuning_demo_injection_record": injection_record,
    }
    verifier = {
        "schema_version": "barcarolle.workspace_acut_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": config.adapter_id,
        "acut_id": config.acut_id,
        "harness_name": config.harness_name,
        "model_or_agent_name": config.model_or_agent_name,
        "command_template_source": config.command_template_source,
        "endpoint_proof_status": config.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "fresh_workspace": False,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
        "agent_tuning_demo_condition": condition,
        "agent_tuning_demo_artifact_hash": None if artifact is None else artifact["hash"],
    }
    if acut.returncode != 0:
        submission = {**base_submission, "status": "acut_harness_error", "acut_exit_code": acut.returncode}
        verifier.update({"status": "acut_harness_error", "harness_error": "acut_command_failed", "acut_exit_code": acut.returncode, "adapter_timed_out": acut.timed_out})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    if not patch_text.strip():
        submission = {**base_submission, "status": "invalid_output", "acut_exit_code": acut.returncode}
        verifier.update({"status": "invalid_output", "harness_error": "empty_workspace_diff"})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    changed = workspace.changed_paths(solver_workspace)
    submission = {**base_submission, "status": "submitted", "acut_exit_code": acut.returncode, "changed_paths": changed}
    violation, violating_paths = workspace.policy_violation(changed, package)
    if violation:
        verifier.update({"status": "policy_violation", "harness_error": violation, "changed_paths": violating_paths})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    workspace.archive_tree(package.source_repo, package.base_commit, verifier_workspace)
    workspace.initialize_workspace_git(verifier_workspace)
    applied, apply_error = workspace.apply_patch(verifier_workspace, patch_path)
    if not applied:
        verifier.update({"status": "harness_error", "harness_error": "captured_patch_did_not_apply", "patch_apply_error_tail": apply_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    injected, inject_error = workspace.inject_hidden_oracle(ROOT, package, verifier_workspace, raw_dir)
    if not injected:
        verifier.update({"status": "harness_error", "harness_error": inject_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    verify_stdout = raw_dir / "verifier_stdout.txt"
    verify_stderr = raw_dir / "verifier_stderr.txt"
    verify = workspace.run_command(package.verifier_command, verifier_workspace, timeout=package.timeout_seconds, env=workspace.verifier_env_for(package, verifier_workspace))
    verify_stdout.write_text(verify.stdout, encoding="utf-8")
    verify_stderr.write_text(verify.stderr, encoding="utf-8")
    verifier.update(
        {
            "status": "timeout" if verify.timed_out else "verified_pass" if verify.returncode == 0 else "verified_fail",
            "verifier_exit_code": verify.returncode,
            "duration_seconds": round(verify.duration_seconds, 3),
            "fresh_workspace": True,
            "raw_artifacts": {
                "stdout": str(verify_stdout.relative_to(PHASE0_EXP)),
                "stderr": str(verify_stderr.relative_to(PHASE0_EXP)),
            },
        }
    )
    return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)


def score_row_for_result(
    result: workspace.CellResult,
    *,
    stage: str,
    condition: str,
    candidate_id: str,
    artifact_hash: str | None,
) -> dict[str, Any]:
    config = workspace_config()
    usage = demo_costs.usage_from_submission(result.submission)
    usage_observed, estimated_cost, token_counts = demo_costs.estimate_cost(usage, TARGET_MODEL, config)
    cost_meta = demo_costs.cost_observation_metadata(usage_observed)
    terminal = result.verifier.get("status") or result.submission.get("status")
    return {
        "stage": stage,
        "condition": condition,
        "candidate_id": candidate_id,
        "repository": result.submission["repo_id"],
        "origin_id": PRIMARY_ORIGIN,
        "agent_id": TARGET_AGENT_ID,
        "reviewer_name": TARGET_AGENT_NAME,
        "harness": TARGET_HARNESS,
        "model": TARGET_MODEL,
        "surface": TARGET_SURFACE if artifact_hash else "baseline_no_artifact",
        "task_id": result.submission["task_id"],
        "terminal_status": terminal,
        "scoreable_cell": terminal in SCOREABLE_STATUSES,
        "verified_pass": terminal == "verified_pass",
        "failure_category": demo_costs.failure_category(result.verifier, result.submission),
        "latency_seconds": result.submission.get("latency_seconds", ""),
        "estimated_cost_usd": estimated_cost,
        "usage_observed": usage_observed,
        "cost_observation_kind": cost_meta["cost_observation_kind"],
        "usage_source": cost_meta["usage_source"],
        "input_tokens": token_counts["input_tokens"],
        "cached_input_tokens": token_counts["cached_input_tokens"],
        "output_tokens": token_counts["output_tokens"],
        "endpoint_proof_status": result.submission["endpoint_proof_status"],
        "artifact_hash": artifact_hash or "",
        "patch_sha256": result.submission.get("patch_sha256", ""),
        "run_id": result.submission["run_id"],
        "result_artifact_path": display_path(PHASE0_EXP / result.submission["raw_artifacts"]["patch"]),
    }


def ledger_row_from_score(row: dict[str, Any], *, category: str = "solver Agent") -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA}.cost_ledger.v1",
        "call_id": row["run_id"],
        "timestamp": iso_now(),
        "call_category": category,
        "repository": row.get("repository", PRIMARY_REPO),
        "window_or_origin": row.get("origin_id", PRIMARY_ORIGIN),
        "task_id": row.get("task_id", ""),
        "artifact_id": row.get("candidate_id", ""),
        "agent_model_harness_surface": {
            "agent_id": row.get("agent_id", TARGET_AGENT_ID),
            "model": row.get("model", TARGET_MODEL),
            "harness": row.get("harness", TARGET_HARNESS),
            "surface": row.get("surface", TARGET_SURFACE),
        },
        "endpoint_proof_status": row.get("endpoint_proof_status", ""),
        "input_tokens": row.get("input_tokens", ""),
        "cached_input_tokens": row.get("cached_input_tokens", ""),
        "output_tokens": row.get("output_tokens", ""),
        "token_usage_source": row.get("usage_source", ""),
        "observed_or_estimated_usd_cost": float(row.get("estimated_cost_usd") or 0.0),
        "cost_observation_kind": row.get("cost_observation_kind", ""),
        "latency_seconds": row.get("latency_seconds", ""),
        "terminal_status": row.get("terminal_status", ""),
        "artifact_or_result_path": row.get("result_artifact_path", ""),
        "cumulative_estimated_cost_after_row": 0.0,
    }


def merge_rows_by_key(existing: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {(row["stage"], row["condition"], row["task_id"]): row for row in existing}
    for row in new_rows:
        merged[(row["stage"], row["condition"], row["task_id"])] = row
    return sorted(merged.values(), key=lambda row: (row["stage"], row["condition"], row["task_id"]))


def rebuild_cost_ledger() -> None:
    rows: list[dict[str, Any]] = []
    for path in [SELECTED_BASELINE_CSV, DEV_EVAL_CSV, FUTURE_CSV]:
        for row in read_csv_rows(path):
            if row.get("run_id"):
                if path == DEV_EVAL_CSV and row.get("condition") == "baseline":
                    continue
                rows.append(ledger_row_from_score(row))
    if CANDIDATES_JSON.exists():
        payload = read_json(CANDIDATES_JSON)
        for artifact in payload.get("candidate_artifacts", []):
            rows.append(
                {
                    "schema_version": f"{SCHEMA}.cost_ledger.v1",
                    "call_id": f"local_proposer__{artifact['artifact_id']}",
                    "timestamp": payload["generated_at"],
                    "call_category": "tuner/proposer",
                    "repository": PRIMARY_REPO,
                    "window_or_origin": PRIMARY_ORIGIN,
                    "task_id": "",
                    "artifact_id": artifact["artifact_id"],
                    "agent_model_harness_surface": {
                        "agent_id": "local_rule_proposer",
                        "model": "none",
                        "harness": "local",
                        "surface": TARGET_SURFACE,
                    },
                    "endpoint_proof_status": "no_paid_call_local_rule",
                    "input_tokens": "",
                    "cached_input_tokens": "",
                    "output_tokens": "",
                    "token_usage_source": "no_model_call",
                    "observed_or_estimated_usd_cost": 0.0,
                    "cost_observation_kind": "no-cost local",
                    "latency_seconds": 0,
                    "terminal_status": "artifact_frozen",
                    "artifact_or_result_path": display_path(CANDIDATES_JSON),
                    "cumulative_estimated_cost_after_row": 0.0,
                }
            )
    rows.sort(key=lambda row: row["call_id"])
    cumulative = 0.0
    for row in rows:
        cumulative += float(row.get("observed_or_estimated_usd_cost") or 0.0)
        row["cumulative_estimated_cost_after_row"] = round(cumulative, 8)
    write_jsonl(COST_LEDGER, rows)
    write_cost_summary()


def write_cost_summary() -> None:
    ledger = read_jsonl(COST_LEDGER)
    by_kind: dict[str, float] = defaultdict(float)
    call_counts: dict[str, int] = defaultdict(int)
    for row in ledger:
        kind = str(row.get("cost_observation_kind") or "unknown")
        by_kind[kind] += float(row.get("observed_or_estimated_usd_cost") or 0.0)
        call_counts[str(row.get("call_category") or "unknown")] += 1
    payload = {
        "schema_version": f"{SCHEMA}.cost_summary.v1",
        "generated_at": iso_now(),
        "ledger": display_path(COST_LEDGER),
        "total_estimated_or_observed_cost_usd": round(sum(by_kind.values()), 8),
        "cost_by_observation_kind_usd": {key: round(value, 8) for key, value in sorted(by_kind.items())},
        "call_counts_by_category": dict(sorted(call_counts.items())),
        "actual_billed_cost_usd": None,
        "actual_billed_cost_status": "not_available_from_endpoint_or_provider_export",
        "paid_solver_agent_cells": sum(1 for row in ledger if row.get("call_category") == "solver Agent"),
        "paid_tuner_or_proposer_calls": sum(1 for row in ledger if row.get("call_category") in {"tuner/proposer", "reflection"} and row.get("cost_observation_kind") != "no-cost local"),
    }
    write_json(COST_SUMMARY_JSON, payload)
    lines = [
        "# Agent Tuning Demo cost summary",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        f"- Ledger: `{payload['ledger']}`。",
        f"- Total estimated/observed cost: `${payload['total_estimated_or_observed_cost_usd']:.8f}`。",
        f"- Paid solver Agent cells: `{payload['paid_solver_agent_cells']}`。",
        f"- Paid tuner/proposer calls: `{payload['paid_tuner_or_proposer_calls']}`。",
        f"- Actual billed cost: `{payload['actual_billed_cost_usd']}` ({payload['actual_billed_cost_status']})。",
        "",
        "## By observation kind",
        "",
        "| Kind | USD |",
        "| --- | --- |",
        *[f"| {kind} | `{value:.8f}` |" for kind, value in payload["cost_by_observation_kind_usd"].items()],
        "",
    ]
    write_text(COST_SUMMARY_REPORT, "\n".join(lines))


def append_batch_plan(stage: str, condition_count: int, planned_cells: int, max_concurrency: int) -> None:
    append_jsonl(
        BATCH_PLAN,
        {
            "schema_version": f"{SCHEMA}.batch_plan.v1",
            "batch_id": f"{stage}_{condition_count}_{int(time.time())}",
            "timestamp": iso_now(),
            "stage": stage,
            "planned_max_cells": planned_cells,
            "max_concurrency": max_concurrency,
            "per_cell_timeout_seconds": 1800,
            "cleanup_grace_seconds": 60,
            "estimated_max_cost_usd": round(planned_cells * conservative_cell_estimate(), 8),
            "duplicate_paid_call_protection": "skip existing stage/condition/task_id rows before launch",
        },
    )


def protocol_or_raise() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise RuntimeError("run write-preregistration before paid stages")
    payload = read_json(PREREG_JSON)
    if payload.get("schema_version") != f"{SCHEMA}.preregistration.v1":
        raise RuntimeError("unsupported preregistration schema")
    return payload


def stage_task_ids(stage: str) -> list[str]:
    protocol = protocol_or_raise()
    window = protocol["rolling_origin_window"]
    if stage == "selected_baseline":
        return list(window["selected_benchmark_from_history_task_ids"])
    if stage == "dev_eval":
        return list(window["dev_eval_task_ids"])
    if stage in {"future_baseline", "future_tuned"}:
        if not CHOSEN_JSON.exists():
            raise RuntimeError("future task IDs are revealed only after chosen artifact freeze")
        return list(read_json(CHOSEN_JSON)["future_holdout_task_ids_revealed_after_freeze"])
    raise ValueError(f"unknown stage: {stage}")


def load_artifacts() -> list[dict[str, Any]]:
    payload = read_json(CANDIDATES_JSON)
    artifacts = payload.get("candidate_artifacts") or []
    for artifact in artifacts:
        validate_artifact(artifact)
    return artifacts


def run_stage(stage: str, *, max_concurrency: int = MAX_CONCURRENCY_DEFAULT, task_limit: int | None = None) -> None:
    if max_concurrency < 1 or max_concurrency > MAX_CONCURRENCY_HARD_CAP:
        raise ValueError(f"max_concurrency must be between 1 and {MAX_CONCURRENCY_HARD_CAP}")
    require_endpoint_env()
    protocol = protocol_or_raise()
    repo_id = protocol["target_repositories"]["primary"]["repo_id"]
    rows_by_id = task_rows_by_id(repo_id)
    adapter = adapter_config()
    task_ids = stage_task_ids(stage)
    if task_limit is not None:
        task_ids = task_ids[:task_limit]

    if stage == "selected_baseline":
        output_csv = SELECTED_BASELINE_CSV
        conditions = [("baseline", "", None)]
    elif stage == "dev_eval":
        if not CANDIDATES_JSON.exists():
            raise RuntimeError("candidate artifacts must be frozen before dev eval")
        output_csv = DEV_EVAL_CSV
        conditions = [(f"tuned_candidate_{index}", artifact["artifact_id"], artifact) for index, artifact in enumerate(load_artifacts(), start=1)]
    elif stage == "future_baseline":
        output_csv = FUTURE_CSV
        conditions = [("baseline", "", None)]
    elif stage == "future_tuned":
        chosen = read_json(CHOSEN_JSON)
        artifact = read_json(CHOSEN_DIR / "artifact.json")
        validate_artifact(artifact)
        output_csv = FUTURE_CSV
        conditions = [("tuned", artifact["artifact_id"], artifact)]
        if artifact["hash"] != chosen["artifact_hash"]:
            raise RuntimeError("chosen artifact hash does not match materialized artifact")
    else:
        raise ValueError(f"unknown stage: {stage}")

    existing = read_csv_rows(output_csv)
    seen = {(row["condition"], row["task_id"]) for row in existing}
    jobs: list[tuple[str, str, dict[str, Any] | None, workspace.TaskPackage, str]] = []
    for condition, candidate_id, artifact in conditions:
        artifact_hash = "" if artifact is None else artifact["hash"].replace("sha256:", "")[:12]
        for task_id in task_ids:
            if (condition, task_id) in seen:
                continue
            package = replace(package_for(rows_by_id[task_id], stage), split=stage)
            run_id = f"{stage}__{condition}__{TARGET_AGENT_ID}__{task_id}"
            if artifact_hash:
                run_id = f"{run_id}__{artifact_hash}"
            jobs.append((condition, candidate_id, artifact, package, run_id))

    append_batch_plan(stage, len(conditions), len(jobs), max_concurrency)
    if not jobs:
        rebuild_cost_ledger()
        return

    new_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        futures = {
            pool.submit(run_workspace_cell_with_artifact, package, adapter, run_id, stage, condition, artifact): (
                condition,
                candidate_id,
                artifact,
            )
            for condition, candidate_id, artifact, package, run_id in jobs
        }
        for future in as_completed(futures):
            condition, candidate_id, artifact = futures[future]
            result = future.result()
            row = score_row_for_result(
                result,
                stage=stage,
                condition=condition,
                candidate_id=candidate_id,
                artifact_hash=None if artifact is None else artifact["hash"],
            )
            new_rows.append(row)
            merged = merge_rows_by_key(read_csv_rows(output_csv), [row])
            write_csv(output_csv, merged, SCORE_FIELDS)
            rebuild_cost_ledger()

    merged = merge_rows_by_key(read_csv_rows(output_csv), new_rows)
    write_csv(output_csv, merged, SCORE_FIELDS)
    rebuild_cost_ledger()


def condition_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [row for row in rows if bool_from_cell(row.get("scoreable_cell"))]
    invalid = [row for row in rows if not bool_from_cell(row.get("scoreable_cell"))]
    costs = [float(row.get("estimated_cost_usd") or 0.0) for row in rows]
    return {
        "cells": len(rows),
        "scoreable_cells": len(scoreable),
        "invalid_or_unscoreable_cells": len(invalid),
        "verified_pass_count": sum(1 for row in scoreable if bool_from_cell(row.get("verified_pass"))),
        "pass_rate": None
        if not scoreable
        else round(sum(1 for row in scoreable if bool_from_cell(row.get("verified_pass"))) / len(scoreable), 4),
        "estimated_cost_usd": round(sum(costs), 8),
        "failure_categories": dict(sorted(Counter(str(row.get("failure_category") or "") for row in rows).items())),
    }


def paired_summary(rows: list[dict[str, Any]], tuned_condition: str) -> dict[str, Any]:
    baseline = {row["task_id"]: row for row in rows if row["condition"] == "baseline"}
    tuned = {row["task_id"]: row for row in rows if row["condition"] == tuned_condition}
    common_ids = sorted(set(baseline) & set(tuned))
    improved = [task_id for task_id in common_ids if bool_from_cell(tuned[task_id]["verified_pass"]) and not bool_from_cell(baseline[task_id]["verified_pass"])]
    regressed = [task_id for task_id in common_ids if bool_from_cell(baseline[task_id]["verified_pass"]) and not bool_from_cell(tuned[task_id]["verified_pass"])]
    base_metrics = condition_metrics(list(baseline.values()))
    tuned_metrics = condition_metrics(list(tuned.values()))
    return {
        "candidate_condition": tuned_condition,
        "paired_task_count": len(common_ids),
        "improved_task_ids": improved,
        "regressed_task_ids": regressed,
        "paired_net_wins": len(improved) - len(regressed),
        "conditions": {"baseline": base_metrics, "tuned": tuned_metrics},
        "candidate_acceptable_for_future": bool(
            common_ids
            and tuned_metrics["invalid_or_unscoreable_cells"] <= base_metrics["invalid_or_unscoreable_cells"]
            and len(regressed) <= len(improved)
        ),
        "matrix": [
            {
                "task_id": task_id,
                "baseline_status": baseline[task_id]["terminal_status"],
                "baseline_pass": bool_from_cell(baseline[task_id]["verified_pass"]),
                "tuned_status": tuned[task_id]["terminal_status"],
                "tuned_pass": bool_from_cell(tuned[task_id]["verified_pass"]),
            }
            for task_id in common_ids
        ],
    }


def write_feedback() -> None:
    protocol = protocol_or_raise()
    train_ids = set(protocol["rolling_origin_window"]["train_feedback_task_ids"])
    rows_by_id = task_rows_by_id(PRIMARY_REPO)
    baseline = {row["task_id"]: row for row in read_csv_rows(SELECTED_BASELINE_CSV) if row["condition"] == "baseline"}
    feedback_rows: list[dict[str, Any]] = []
    for task_id in protocol["rolling_origin_window"]["train_feedback_task_ids"]:
        if task_id not in baseline:
            continue
        score = baseline[task_id]
        task = rows_by_id[task_id]
        feedback_rows.append(
            {
                "schema_version": f"{SCHEMA}.feedback_row.v1",
                "repository": PRIMARY_REPO,
                "origin_id": PRIMARY_ORIGIN,
                "task_id": task_id,
                "split": "train_feedback",
                "future_holdout_derived": False,
                "terminal_status": score["terminal_status"],
                "verified_pass": bool_from_cell(score["verified_pass"]),
                "failure_category": score["failure_category"],
                "module_family": task.get("module_family"),
                "editable_implementation_paths": split_field(task.get("changed_implementation_files")),
                "source_confidence_label": task.get("source_confidence_label"),
                "evidence_digest": task.get("sanitized_evidence_digest"),
            }
        )
    forbidden_ids = set(protocol["rolling_origin_window"]["dev_eval_task_ids"])
    if train_ids & forbidden_ids:
        raise RuntimeError("train feedback overlaps dev ids")
    write_jsonl(FEEDBACK_JSONL, feedback_rows)
    label_counts = Counter(row["failure_category"] for row in feedback_rows)
    family_counts = Counter(row["module_family"] for row in feedback_rows)
    lines = [
        "# Agent Tuning Demo feedback export",
        "",
        f"生成时间：`{iso_now()}`。",
        "",
        f"- Feedback rows: `{len(feedback_rows)}`。",
        "- Source: selected benchmark train-feedback baseline rows only.",
        "- Future holdout IDs/outcomes included: `false`。",
        "",
        "## Failure labels",
        "",
        "| Label | Count |",
        "| --- | --- |",
        *[f"| {label} | `{count}` |" for label, count in sorted(label_counts.items())],
        "",
        "## Module families",
        "",
        "| Family | Count |",
        "| --- | --- |",
        *[f"| {family} | `{count}` |" for family, count in sorted(family_counts.items())],
        "",
    ]
    write_text(FEEDBACK_REPORT, "\n".join(lines))


def artifact_payload(artifact_id: str, content: str, evidence_task_ids: list[str], labels: list[str], intended: str) -> dict[str, Any]:
    artifact = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_type": TARGET_ARTIFACT_TYPE,
        "target_agent": "kilo_workspace",
        "changed_files": [TARGET_ARTIFACT_PATH],
        "files": [
            {
                "workspace_relative_path": TARGET_ARTIFACT_PATH,
                "write_mode": "append",
                "content": content.rstrip() + "\n",
            }
        ],
        "intended_effect": intended,
        "rollback_plan": "Remove the appended Barcarolle Agent Tuning Demo section from AGENTS.md.",
        "optimizer_source": "local train-only rule proposer from selected benchmark baseline feedback",
        "visible_to_optimizer": True,
        "holdout_derived": False,
        "evidence_task_ids": evidence_task_ids,
        "targeted_failure_labels": labels,
        "generated_at": iso_now(),
    }
    return with_computed_hash(artifact)


def propose_artifacts() -> None:
    feedback = read_jsonl(FEEDBACK_JSONL)
    if not feedback:
        raise RuntimeError("feedback export is empty")
    failing = [row for row in feedback if not row.get("verified_pass")]
    evidence = [row["task_id"] for row in failing] or [row["task_id"] for row in feedback[:3]]
    labels = sorted({row["failure_category"] for row in failing}) or ["verified_pass_headroom"]
    families = sorted({str(row.get("module_family") or "unknown") for row in feedback})
    content_a = f"""

## Barcarolle Agent Tuning Demo Appendix

When solving mypy tasks for this benchmark, treat the task as a narrow data-driven regression repair.
Start from the listed editable implementation paths and inspect adjacent implementation code before editing.
If the statement names TypeCheckSuite or `test-data` entry points, infer the expected behavior from nearby existing cases,
but do not edit tests or test-data files. Prefer a minimal semantic fix over broad rewrites, and run the targeted verifier
command shape from the task statement before finishing when feasible.
""".strip()
    content_b = f"""

## Barcarolle Agent Tuning Demo Appendix

For mypy benchmark tasks in module families {", ".join(families)}, first identify whether the failure is semantic-analysis,
incremental-cache, or type-checker behavior. Keep the patch inside the declared implementation paths, preserve public APIs,
and avoid touching generated files, tests, or test-data fixtures. If the first hypothesis is uncertain, inspect the smallest
neighboring implementation and test-data examples before editing, then run the targeted check command.
""".strip()
    artifacts = [
        artifact_payload(
            "agent-tuning-demo-mypy-data-driven-loop",
            content_a,
            evidence,
            labels,
            "Improve Kilo's behavior on mypy data-driven regression tasks by making it inspect nearby implementation and targeted TypeCheckSuite context before editing.",
        ),
        artifact_payload(
            "agent-tuning-demo-mypy-family-triage-loop",
            content_b,
            evidence,
            labels,
            "Improve Kilo's behavior by adding a family-specific mypy diagnosis loop before choosing a narrow implementation edit.",
        ),
    ]
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        validate_artifact(artifact)
        write_json(CANDIDATE_DIR / f"{artifact['artifact_id']}.json", artifact)
        write_text(CANDIDATE_DIR / f"{artifact['artifact_id']}.md", artifact["files"][0]["content"])
    payload = {
        "schema_version": f"{SCHEMA}.candidate_artifacts.v1",
        "generated_at": iso_now(),
        "repository": PRIMARY_REPO,
        "origin_id": PRIMARY_ORIGIN,
        "proposer": "local_train_only_rule_proposer",
        "paid_llm_calls": 0,
        "future_or_dev_task_ids_in_proposer_input": False,
        "raw_prompt_completion_committed": False,
        "candidate_artifacts": artifacts,
    }
    write_json(CANDIDATES_JSON, payload)
    rows = [
        {
            "Artifact": artifact["artifact_id"],
            "Hash": artifact["hash"][:24],
            "Evidence": len(artifact["evidence_task_ids"]),
            "Labels": ",".join(artifact["targeted_failure_labels"]),
        }
        for artifact in artifacts
    ]
    lines = [
        "# Agent Tuning Demo candidate artifacts",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        "- Proposer: local train-only rule proposer.",
        "- Paid LLM proposer calls: `0`.",
        "- Future/dev task IDs in proposer input: `false`.",
        "",
        "| Artifact | Hash | Evidence tasks | Labels |",
        "| --- | --- | --- | --- |",
        *[f"| {row['Artifact']} | `{row['Hash']}` | `{row['Evidence']}` | {row['Labels']} |" for row in rows],
        "",
    ]
    write_text(CANDIDATES_REPORT, "\n".join(lines))
    rebuild_cost_ledger()


def copy_dev_baseline() -> None:
    protocol = protocol_or_raise()
    dev_ids = set(protocol["rolling_origin_window"]["dev_eval_task_ids"])
    existing = read_csv_rows(DEV_EVAL_CSV)
    seen = {(row["condition"], row["task_id"]) for row in existing}
    baseline_rows = []
    for row in read_csv_rows(SELECTED_BASELINE_CSV):
        if row["condition"] == "baseline" and row["task_id"] in dev_ids and ("baseline", row["task_id"]) not in seen:
            copied = dict(row)
            copied["stage"] = "dev_eval"
            copied["result_artifact_path"] = row["result_artifact_path"]
            baseline_rows.append(copied)
    merged = merge_rows_by_key(existing, baseline_rows)
    write_csv(DEV_EVAL_CSV, merged, SCORE_FIELDS)
    rebuild_cost_ledger()


def summarize_baseline() -> None:
    selected_rows = read_csv_rows(SELECTED_BASELINE_CSV)
    future_rows = [row for row in read_csv_rows(FUTURE_CSV) if row["condition"] == "baseline"]
    all_rows = [*selected_rows, *future_rows]
    write_csv(BASELINE_MATRIX_CSV, all_rows, SCORE_FIELDS)
    payload = {
        "schema_version": f"{SCHEMA}.baseline_summary.v1",
        "generated_at": iso_now(),
        "selected_baseline": condition_metrics(selected_rows),
        "future_baseline": condition_metrics(future_rows),
        "total_paid_baseline_cells": len(selected_rows) + len(future_rows),
        "matrix": display_path(BASELINE_MATRIX_CSV),
    }
    write_json(BASELINE_SUMMARY_JSON, payload)
    lines = [
        "# Agent Tuning Demo baseline summary",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        f"- Selected/history baseline: `{payload['selected_baseline']['verified_pass_count']}/{payload['selected_baseline']['scoreable_cells']}` scoreable pass.",
        f"- Future baseline: `{payload['future_baseline']['verified_pass_count']}/{payload['future_baseline']['scoreable_cells']}` scoreable pass.",
        f"- Paid baseline cells: `{payload['total_paid_baseline_cells']}`。",
        "",
    ]
    write_text(BASELINE_REPORT, "\n".join(lines))


def summarize_dev() -> dict[str, Any]:
    rows = read_csv_rows(DEV_EVAL_CSV)
    artifacts = load_artifacts()
    candidate_summaries = []
    for index, artifact in enumerate(artifacts, start=1):
        summary = paired_summary(rows, f"tuned_candidate_{index}")
        summary["artifact_id"] = artifact["artifact_id"]
        summary["artifact_hash"] = artifact["hash"]
        candidate_summaries.append(summary)
    positive = [item for item in candidate_summaries if item["paired_net_wins"] > 0 and item["candidate_acceptable_for_future"]]
    acceptable = [item for item in candidate_summaries if item["candidate_acceptable_for_future"]]
    if positive:
        chosen = sorted(positive, key=lambda item: (-item["paired_net_wins"], item["conditions"]["tuned"]["invalid_or_unscoreable_cells"]))[0]
        decision = "choose_positive_dev_candidate"
    elif acceptable:
        chosen = sorted(acceptable, key=lambda item: (-item["paired_net_wins"], item["conditions"]["tuned"]["invalid_or_unscoreable_cells"]))[0]
        decision = "choose_non_regressing_candidate_after_two_attempts"
    else:
        chosen = sorted(candidate_summaries, key=lambda item: (-item["paired_net_wins"], item["conditions"]["tuned"]["invalid_or_unscoreable_cells"]))[0] if candidate_summaries else None
        decision = "choose_least_bad_candidate_for_required_holdout_story" if chosen else "no_candidate"
    payload = {
        "schema_version": f"{SCHEMA}.dev_eval_summary.v1",
        "generated_at": iso_now(),
        "repository": PRIMARY_REPO,
        "origin_id": PRIMARY_ORIGIN,
        "candidate_summaries": candidate_summaries,
        "future_gate_decision": decision,
        "chosen_artifact_hash": None if chosen is None else chosen["artifact_hash"],
        "chosen_artifact_id": None if chosen is None else chosen["artifact_id"],
        "paid_cells": sum(1 for row in rows if row["condition"] != "baseline"),
        "baseline_rows_reused_from_selected_baseline": sum(1 for row in rows if row["condition"] == "baseline"),
    }
    write_json(DEV_EVAL_SUMMARY_JSON, payload)
    lines = [
        "# Agent Tuning Demo dev eval",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        f"- Future gate decision: `{payload['future_gate_decision']}`。",
        f"- Chosen artifact: `{payload['chosen_artifact_id']}`。",
        f"- Paid tuned dev cells: `{payload['paid_cells']}`。",
        "",
        "| Candidate | Net wins | Improved | Regressed | Tuned pass | Tuned scoreable |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in candidate_summaries:
        tuned = item["conditions"]["tuned"]
        lines.append(
            f"| {item['artifact_id']} | `{item['paired_net_wins']}` | `{len(item['improved_task_ids'])}` | `{len(item['regressed_task_ids'])}` | `{tuned['verified_pass_count']}` | `{tuned['scoreable_cells']}` |"
        )
    lines.append("")
    write_text(DEV_EVAL_REPORT, "\n".join(lines))
    return payload


def choose_artifact() -> None:
    summary = summarize_dev()
    chosen_hash = summary.get("chosen_artifact_hash")
    if not chosen_hash:
        raise RuntimeError("no candidate available to choose")
    artifacts = {artifact["hash"]: artifact for artifact in load_artifacts()}
    artifact = artifacts[chosen_hash]
    CHOSEN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(CHOSEN_DIR / "artifact.json", artifact)
    write_text(CHOSEN_DIR / "AGENTS_appendix.md", artifact["files"][0]["content"])
    protocol = protocol_or_raise()
    window = selected_window(PRIMARY_REPO, PRIMARY_ORIGIN)
    future_ids = list(window["future_holdout_after_origin"]["task_ids"])[:FUTURE_HOLDOUT_COUNT]
    if sha256_text("\n".join(future_ids)) != protocol["rolling_origin_window"]["future_holdout_task_ids_sha256"]:
        raise RuntimeError("future holdout hash mismatch at reveal")
    payload = {
        "schema_version": f"{SCHEMA}.chosen_artifact.v1",
        "generated_at": iso_now(),
        "artifact_id": artifact["artifact_id"],
        "artifact_hash": artifact["hash"],
        "artifact_path": display_path(CHOSEN_DIR / "artifact.json"),
        "selection_basis": summary["future_gate_decision"],
        "future_holdout_task_ids_revealed_after_freeze": future_ids,
        "future_holdout_reveal_after_artifact_freeze": True,
        "future_holdout_hash": protocol["rolling_origin_window"]["future_holdout_task_ids_sha256"],
    }
    write_json(CHOSEN_JSON, payload)


def summarize_future() -> dict[str, Any]:
    rows = read_csv_rows(FUTURE_CSV)
    summary = paired_summary(rows, "tuned")
    payload = {
        "schema_version": f"{SCHEMA}.future_holdout_summary.v1",
        "generated_at": iso_now(),
        "repository": PRIMARY_REPO,
        "origin_id": PRIMARY_ORIGIN,
        "chosen_artifact": read_json(CHOSEN_JSON) if CHOSEN_JSON.exists() else {},
        "paired_summary": summary,
        "paid_cells": len(rows),
        "future_holdout_task_ids_were_tuner_inputs": False,
    }
    write_json(FUTURE_SUMMARY_JSON, payload)
    tuned = summary["conditions"]["tuned"]
    base = summary["conditions"]["baseline"]
    lines = [
        "# Agent Tuning Demo future holdout",
        "",
        f"生成时间：`{payload['generated_at']}`。",
        "",
        f"- Paired future tasks: `{summary['paired_task_count']}`。",
        f"- Baseline pass: `{base['verified_pass_count']}/{base['scoreable_cells']}`。",
        f"- Tuned pass: `{tuned['verified_pass_count']}/{tuned['scoreable_cells']}`。",
        f"- Paired net wins: `{summary['paired_net_wins']}`。",
        f"- Improved: `{len(summary['improved_task_ids'])}`；regressed: `{len(summary['regressed_task_ids'])}`。",
        "- Future holdout IDs/outcomes were tuner inputs: `false`。",
        "",
    ]
    write_text(FUTURE_REPORT, "\n".join(lines))
    summarize_baseline()
    return payload


def write_final() -> None:
    summarize_baseline()
    dev = summarize_dev()
    future = summarize_future()
    cost = read_json(COST_SUMMARY_JSON)
    future_pair = future["paired_summary"]
    if future_pair["paired_net_wins"] > 0:
        terminal = "agent_tuning_demo_complete_improved"
    elif future_pair["paired_net_wins"] == 0:
        terminal = "agent_tuning_demo_complete_neutral"
    else:
        terminal = "agent_tuning_demo_complete_regressed"
    payload = {
        "schema_version": f"{SCHEMA}.final_closeout.v1",
        "generated_at": iso_now(),
        "terminal_state": "agent_tuning_demo_complete",
        "result_label": terminal,
        "target_repository": PRIMARY_REPO,
        "origin_id": PRIMARY_ORIGIN,
        "artifact_id": read_json(CHOSEN_JSON)["artifact_id"],
        "artifact_hash": read_json(CHOSEN_JSON)["artifact_hash"],
        "dev_eval_summary": display_path(DEV_EVAL_SUMMARY_JSON),
        "future_holdout_summary": display_path(FUTURE_SUMMARY_JSON),
        "future_paired_net_wins": future_pair["paired_net_wins"],
        "total_estimated_or_observed_cost_usd": cost["total_estimated_or_observed_cost_usd"],
        "claim_supported": [
            "Barcarolle supplied a repo-specific certified mypy task set.",
            "Barcarolle froze a corrected rolling-origin window without future leakage into tuning feedback.",
            "Barcarolle exported train-only feedback, produced deployable Kilo AGENTS.md artifacts, and hash-froze the chosen artifact before future holdout reveal.",
            "Barcarolle completed before/after future holdout validation with cost accounting.",
        ],
        "claim_not_supported": [
            "predictive validity",
            "statistical significance",
            "cross-repo generalization",
            "model fine-tuning",
            "general opaque-Agent tuning superiority",
        ],
        "canonical_reports": {
            "final_report": display_path(FINAL_REPORT),
            "final_closeout": display_path(FINAL_CLOSEOUT_REPORT),
            "cost_summary": display_path(COST_SUMMARY_REPORT),
            "future_holdout": display_path(FUTURE_REPORT),
        },
    }
    write_json(FINAL_JSON, payload)
    lines = [
        "# Agent Tuning Demo final report",
        "",
        "## 结论",
        "",
        f"本轮完成了 Agent Tuning Demo。Terminal state: `{payload['terminal_state']}`；result label: `{payload['result_label']}`。",
        "",
        "Barcarolle 在 `mypy` 上使用已认证任务供给，冻结了 corrected rolling-origin window：先从 origin 前历史池选择 benchmark，再在 artifact hash freeze 后才揭示未来 holdout 任务。调优 artifact 是一个可部署的 repo-local Kilo `AGENTS.md` appendix。",
        "",
        "## 协议",
        "",
        "- Primary repo: `mypy`。",
        f"- Origin: `{PRIMARY_ORIGIN}`。",
        f"- Selected benchmark: `{SELECTED_SIZE}` tasks；train feedback `{TRAIN_FEEDBACK_COUNT}`，dev eval `{DEV_EVAL_COUNT}`。",
        f"- Future holdout: `{FUTURE_HOLDOUT_COUNT}` tasks。",
        "- Future holdout IDs/outcomes were not tuner inputs.",
        "",
        "## Feedback 与 artifact",
        "",
        f"- Candidate artifacts: `{display_path(CANDIDATES_JSON)}`。",
        f"- Chosen artifact: `{payload['artifact_id']}` / `{payload['artifact_hash']}`。",
        "- Tuner path: train-only local rule proposer; no paid LLM proposer calls were needed.",
        "",
        "## Dev 与 future 结果",
        "",
        f"- Dev gate decision: `{dev['future_gate_decision']}`。",
        f"- Future paired tasks: `{future_pair['paired_task_count']}`。",
        f"- Future paired net wins: `{future_pair['paired_net_wins']}`。",
        f"- Improved tasks: `{len(future_pair['improved_task_ids'])}`；regressed tasks: `{len(future_pair['regressed_task_ids'])}`。",
        "",
        "## Cost",
        "",
        f"- Total estimated/observed cost: `${payload['total_estimated_or_observed_cost_usd']:.8f}`。",
        f"- Cost ledger: `{display_path(COST_LEDGER)}`。",
        "- Actual billed provider cost was not available from endpoint export, so observed-token and conservative estimates are reported separately in the cost summary.",
        "",
        "## 支持与不支持的 claim",
        "",
        "支持：Barcarolle 可以供应 repo-specific certified tasks，冻结无未来泄漏的 rolling-origin window，导出 train-only feedback，产出 deployable repo-local Agent artifact，并在未来 holdout 上完成 before/after 验证和成本记录。",
        "",
        "不支持：这不是 predictive validity 证明，不是统计显著结论，不证明跨 repo 泛化，不是模型 fine-tuning，也不证明任意 opaque Agent 都能被这个方法稳定改进。",
        "",
    ]
    write_text(FINAL_REPORT, "\n".join(lines))
    closeout = [
        "# Agent Tuning Demo final closeout",
        "",
        f"- Terminal state: `{payload['terminal_state']}`。",
        f"- Result label: `{payload['result_label']}`。",
        f"- Target repo: `{PRIMARY_REPO}`。",
        f"- Artifact: `{payload['artifact_id']}`。",
        f"- Future paired net wins: `{payload['future_paired_net_wins']}`。",
        f"- Total estimated/observed cost: `${payload['total_estimated_or_observed_cost_usd']:.8f}`。",
        f"- Final report: `{display_path(FINAL_REPORT)}`。",
        "",
    ]
    write_text(FINAL_CLOSEOUT_REPORT, "\n".join(closeout))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Agent Tuning Demo autonomous completion protocol.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("write-preregistration")
    run = sub.add_parser("run-stage")
    run.add_argument("--stage", required=True, choices=["selected_baseline", "dev_eval", "future_baseline", "future_tuned"])
    run.add_argument("--max-concurrency", type=int, default=MAX_CONCURRENCY_DEFAULT)
    run.add_argument("--task-limit", type=int, default=None)
    sub.add_parser("write-feedback")
    sub.add_parser("propose-artifacts")
    sub.add_parser("copy-dev-baseline")
    sub.add_parser("summarize-dev")
    sub.add_parser("choose-artifact")
    sub.add_parser("summarize-future")
    sub.add_parser("summarize-baseline")
    sub.add_parser("write-final")
    sub.add_parser("rebuild-cost-ledger")
    args = parser.parse_args(argv)

    if args.command == "write-preregistration":
        write_preregistration()
    elif args.command == "run-stage":
        run_stage(args.stage, max_concurrency=args.max_concurrency, task_limit=args.task_limit)
    elif args.command == "write-feedback":
        write_feedback()
    elif args.command == "propose-artifacts":
        propose_artifacts()
    elif args.command == "copy-dev-baseline":
        copy_dev_baseline()
    elif args.command == "summarize-dev":
        summarize_dev()
    elif args.command == "choose-artifact":
        choose_artifact()
    elif args.command == "summarize-future":
        summarize_future()
    elif args.command == "summarize-baseline":
        summarize_baseline()
    elif args.command == "write-final":
        write_final()
    elif args.command == "rebuild-cost-ledger":
        rebuild_cost_ledger()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
