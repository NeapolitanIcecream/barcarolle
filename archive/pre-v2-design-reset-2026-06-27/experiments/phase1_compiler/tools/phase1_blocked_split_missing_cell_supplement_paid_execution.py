from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import workspace_acut_run as workspace_acut  # noqa: E402
import workspace_usage_import  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_blocked_split_missing_cell_supplement_paid_execution.yaml"
SCHEMA_VERSION = "barcarolle.phase1_blocked_split_missing_cell_supplement_paid_execution.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_blocked_split_missing_cell_supplement_paid_execution_output.v1"
SELECTED_SPLIT_ID = "phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902"
TERMINAL_SCOREABLE = {"verified_pass", "verified_fail"}
TERMINAL_NON_SCOREABLE = {
    "policy_violation",
    "invalid_output",
    "acut_harness_error",
    "harness_error",
    "timeout",
}
ADAPTER_IDS = ["codex_workspace", "kilo_workspace"]
REPOS = ["attrs", "boltons", "click"]
SPLITS = ["B_eval", "H_future"]
EXPECTED_MISSING_TASKS_BY_REPO_SPLIT = {
    ("attrs", "B_eval"): ["attrs__v2__157", "attrs__v2__231", "attrs__v2__271"],
    ("attrs", "H_future"): ["attrs__v2__210", "attrs__v2__218", "attrs__v2__244"],
    ("boltons", "B_eval"): [
        "boltons__v2__008",
        "boltons__v2__009",
        "boltons__v2__076",
        "boltons__v2__103",
        "boltons__v2__128",
        "boltons__v2__154",
        "boltons__v2__231",
    ],
    ("boltons", "H_future"): ["boltons__v2__122", "boltons__v2__132", "boltons__v2__232"],
    ("click", "B_eval"): ["click__third__091", "click__third__202", "click__third__220"],
    ("click", "H_future"): [
        "click__third__109",
        "click__third__198",
        "click__third__214",
        "click__third__234",
        "click__third__288",
    ],
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


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected missing-cell supplement paid execution schema_version")
    config["_path"] = str(path)
    return config


def source_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["source_artifacts"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def matrix_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["matrix_config"])


def adapter_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["adapter_config"])


def pricing_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["pricing_config"])


def adapter_ids(config: dict[str, Any]) -> list[str]:
    return [str(item) for item in config["approval"]["approved_adapters"]]


def task_repo(task_id: str) -> str:
    return task_id.split("__", 1)[0]


def expected_missing_task_ids() -> list[str]:
    ordered: list[str] = []
    for key in [
        ("attrs", "B_eval"),
        ("attrs", "H_future"),
        ("boltons", "B_eval"),
        ("boltons", "H_future"),
        ("click", "B_eval"),
        ("click", "H_future"),
    ]:
        ordered.extend(EXPECTED_MISSING_TASKS_BY_REPO_SPLIT[key])
    return ordered


def expected_missing_cells() -> list[dict[str, str]]:
    cells: list[dict[str, str]] = []
    for (repo, split), task_ids in EXPECTED_MISSING_TASKS_BY_REPO_SPLIT.items():
        for task_id in task_ids:
            for adapter_id in ADAPTER_IDS:
                cells.append({"task_id": task_id, "repo": repo, "split": split, "adapter_id": adapter_id})
    return cells


def planned_batches() -> list[dict[str, Any]]:
    return [
        {
            "batch_id": 1,
            "output_key": "batch_1_smoke",
            "name": "batch_1_smoke",
            "description": "paid smoke, first 6 cells from the frozen missing-cell manifest",
            "task_ids": ["attrs__v2__157", "boltons__v2__008", "click__third__091"],
        },
        {
            "batch_id": 2,
            "output_key": "batch_2_attrs_remainder",
            "name": "batch_2_attrs_remainder",
            "description": "attrs missing-cell remainder",
            "task_ids": [
                "attrs__v2__210",
                "attrs__v2__218",
                "attrs__v2__231",
                "attrs__v2__244",
                "attrs__v2__271",
            ],
        },
        {
            "batch_id": 3,
            "output_key": "batch_3_boltons_remainder",
            "name": "batch_3_boltons_remainder",
            "description": "boltons missing-cell remainder",
            "task_ids": [
                "boltons__v2__009",
                "boltons__v2__076",
                "boltons__v2__103",
                "boltons__v2__122",
                "boltons__v2__128",
                "boltons__v2__132",
                "boltons__v2__154",
                "boltons__v2__231",
                "boltons__v2__232",
            ],
        },
        {
            "batch_id": 4,
            "output_key": "batch_4_click_remainder",
            "name": "batch_4_click_remainder",
            "description": "click missing-cell remainder",
            "task_ids": [
                "click__third__109",
                "click__third__198",
                "click__third__202",
                "click__third__214",
                "click__third__220",
                "click__third__234",
                "click__third__288",
            ],
        },
    ]


def batch_for_id(batch_id: int) -> dict[str, Any]:
    for batch in planned_batches():
        if int(batch["batch_id"]) == batch_id:
            return batch
    raise KeyError(f"unknown batch id: {batch_id}")


def result_prefix(config: dict[str, Any], batch_name: str, adapter_id: str) -> str:
    return f"{config['workspace_runner']['result_prefix_root']}_{batch_name}_{adapter_id}"


def planned_result_prefixes(config: dict[str, Any], through_batch_id: int | None = None) -> list[str]:
    prefixes: list[str] = []
    for batch in planned_batches():
        if through_batch_id is not None and int(batch["batch_id"]) > through_batch_id:
            continue
        for adapter_id in adapter_ids(config):
            prefixes.append(result_prefix(config, str(batch["name"]), adapter_id))
    return prefixes


def result_files_for_prefix(prefix: str) -> list[Path]:
    names = [
        "score_table.csv",
        "cost_summary.json",
        "matrix.json",
        "submissions.jsonl",
        "verifier_results.jsonl",
        "cost_ledger.jsonl",
        "metrics.json",
    ]
    return [PHASE0_ROOT / "results" / f"{prefix}_{suffix}" for suffix in names]


def existing_attempted_prefixes(config: dict[str, Any]) -> list[str]:
    return [
        prefix
        for prefix in planned_result_prefixes(config)
        if (PHASE0_ROOT / "results" / f"{prefix}_score_table.csv").exists()
    ]


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def command_stdout(args: list[str], *, timeout: int = 120) -> str:
    result = command_result(args, timeout=timeout)
    return (result["stdout"] if result["returncode"] == 0 else result["stderr"]).strip()


def digest_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def status_path(line: str) -> str:
    if line.startswith("?? "):
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


def expected_commit_paths(config: dict[str, Any]) -> set[str]:
    paths = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_blocked_split_missing_cell_supplement_paid_execution.py"),
        rel(ROOT / "tests" / "test_phase1_blocked_split_missing_cell_supplement_paid_execution.py"),
        rel(matrix_config_path(config)),
        rel(PHASE0_ROOT / "results" / "workspace_usage_ledger.jsonl"),
        rel(PHASE0_ROOT / "results" / "workspace_cost_reconciliation.json"),
        rel(PHASE0_ROOT / "reports" / "workspace_cost_usage_report.md"),
    }
    paths.update(rel(path) for path in config.get("outputs", {}).values())
    paths.update(rel(path) for path in config.get("reports", {}).values())
    for prefix in planned_result_prefixes(config):
        paths.update(rel(path) for path in result_files_for_prefix(prefix))
    return paths


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_commit_paths(config)
    ignored_prefixes = [
        "experiments/phase0_headroom/results/raw/",
        "experiments/phase0_headroom/workspaces/",
        "experiments/phase0_headroom/external_repos/",
        "experiments/phase1_compiler/tmp/blocked_split_missing_cell_supplement_paid_execution/",
        "experiments/phase1_compiler/.pytest_cache/",
        "experiments/phase1_compiler/.venv/",
    ]
    classified: dict[str, list[str]] = {"relevant": [], "ignored_raw_or_runtime": [], "unrelated": []}
    for line in status_lines:
        path = status_path(line)
        if path in expected:
            classified["relevant"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ignored_prefixes):
            classified["ignored_raw_or_runtime"].append(line)
        else:
            classified["unrelated"].append(line)
    return classified


def endpoint_presence() -> dict[str, Any]:
    test = command_result(
        ["zsh", "-lc", 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'],
        timeout=30,
    )
    hash_result = command_result(
        [
            "zsh",
            "-lc",
            (
                "source ~/.zshrc >/dev/null 2>&1 || true; "
                "uv run --project experiments/phase1_compiler python - <<'PY'\n"
                "import hashlib, os, urllib.parse\n"
                "raw=os.environ.get('LLM_BASE_URL','')\n"
                "parsed=urllib.parse.urlparse(raw)\n"
                "host=parsed.netloc or raw\n"
                "print(hashlib.sha256(host.encode()).hexdigest()[:12] if host else '')\n"
                "PY"
            ),
        ],
        timeout=60,
    )
    endpoint_hash = hash_result["stdout"].strip() if hash_result["returncode"] == 0 else ""
    return {
        "LLM_BASE_URL_present": test["returncode"] == 0,
        "LLM_API_KEY_present": test["returncode"] == 0,
        "both_required_endpoint_variables_present": test["returncode"] == 0,
        "sourced_zshrc_before_check": True,
        "endpoint_host_hash": endpoint_hash or None,
        "values_recorded": False,
    }


def required_input_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    paths = [str(path) for path in config.get("required_inputs", [])]
    paths.extend(str(path) for path in config.get("source_artifacts", {}).values())
    paths.extend(
        [
            "experiments/phase0_headroom/configs/acut_workspace_adapters.yaml",
            "experiments/phase0_headroom/configs/model_pricing.yaml",
            "experiments/phase0_headroom/tools/workspace_acut_run.py",
            "experiments/phase0_headroom/tools/workspace_usage_import.py",
        ]
    )
    records = []
    seen: set[str] = set()
    for raw in paths:
        if raw in seen:
            continue
        seen.add(raw)
        path = repo_path(raw)
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "is_file": path.is_file(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "sha256": digest_file(path),
            }
        )
    return records


def build_preflight(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    dirty_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    diff_check = command_result(["git", "diff", "--check"])
    ready = read_json(source_path(config, "ready_package"), {})
    decision = read_json(source_path(config, "design_review_decision"), {})
    existing_prefixes = existing_attempted_prefixes(config)
    codex_version = command_result(["codex", "--version"])
    kilo_version = command_result(["kilo", "--version"])
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "head_short": command_stdout(["git", "rev-parse", "--short", "HEAD"]),
        "date_utc": command_stdout(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]),
        "python_version": command_stdout(["uv", "run", "--project", "experiments/phase1_compiler", "python", "--version"]),
        "uv_version": command_stdout(["uv", "--version"]),
        "codex_version": codex_version["stdout"].strip() if codex_version["returncode"] == 0 else None,
        "codex_available": codex_version["returncode"] == 0,
        "kilo_version": kilo_version["stdout"].strip() if kilo_version["returncode"] == 0 else None,
        "kilo_available": kilo_version["returncode"] == 0,
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "git_status_short_untracked": dirty_lines,
        "dirty_path_classification": classify_dirty_paths(config, dirty_lines),
        "git_diff_check": {
            "passed": diff_check["returncode"] == 0,
            "returncode": diff_check["returncode"],
            "stdout_tail_digest": hashlib.sha256(diff_check["stdout"][-4000:].encode("utf-8")).hexdigest()[:12],
            "stderr_tail_digest": hashlib.sha256(diff_check["stderr"][-4000:].encode("utf-8")).hexdigest()[:12],
        },
        "required_inputs": required_input_records(config),
        "paid_approval": config["approval"],
        "endpoint_presence": endpoint_presence(),
        "ready_package_status": ready.get("status"),
        "selected_protocol_option": ready.get("selected_protocol_option"),
        "selected_protocol_name": ready.get("selected_protocol_name"),
        "selected_budget_id": ready.get("selected_budget_id"),
        "selected_split_id": ready.get("selected_split_id"),
        "design_review_decision_label": decision.get("decision_label"),
        "planned_adapters": adapter_ids(config),
        "planned_new_paid_cells": int(config["budget"]["planned_new_paid_cells"]),
        "known_reusable_cells": int(config["budget"]["known_reusable_cells"]),
        "token_estimated_new_cost_usd": float(config["budget"]["token_estimated_new_cost_usd"]),
        "hard_cost_cap_usd": float(config["budget"]["hard_cost_cap_usd"]),
        "paid_calls_run_before_preflight": bool(existing_prefixes),
        "existing_paid_result_prefixes": existing_prefixes,
        "stop_before_paid": False,
        "blockers": [],
    }
    if payload["paid_approval"].get("approved_option") != "same_budget_missing_cell_supplement":
        payload["blockers"].append("paid_approval_absent_or_wrong_option")
    if float(payload["paid_approval"].get("approved_cost_cap_usd") or 0.0) > 30:
        payload["blockers"].append("paid_approval_cost_cap_above_runbook_default")
    if not payload["endpoint_presence"]["both_required_endpoint_variables_present"]:
        payload["blockers"].append("endpoint_variables_missing")
    if payload["ready_package_status"] != "ready":
        payload["blockers"].append("ready_package_not_ready")
    if payload["selected_protocol_option"] != "B" or payload["selected_protocol_name"] != "same_budget_missing_cell_supplement":
        payload["blockers"].append("selected_protocol_not_option_b")
    if payload["selected_split_id"] != SELECTED_SPLIT_ID:
        payload["blockers"].append("selected_split_mismatch")
    if payload["selected_budget_id"] != "same_budget_20_per_repo":
        payload["blockers"].append("selected_budget_mismatch")
    if payload["token_estimated_new_cost_usd"] > payload["hard_cost_cap_usd"]:
        payload["blockers"].append("projected_total_new_cost_exceeds_approved_cap")
    if payload["paid_calls_run_before_preflight"]:
        payload["blockers"].append("paid_prefix_outputs_already_exist_before_preflight")
    if not payload["git_diff_check"]["passed"]:
        payload["blockers"].append("git_diff_check_failed")
    if any(not row["exists"] for row in payload["required_inputs"]):
        payload["blockers"].append("required_input_missing")
    payload["status"] = "ready_for_package_integrity" if not payload["blockers"] else "blocked_before_paid_calls"
    payload["stop_before_paid"] = bool(payload["blockers"])
    write_json(output_path(config, "preflight"), payload)
    write_preflight_report(config, payload)
    write_process_report(config, current_step="Step 0 preflight complete", notes=["No paid ACUT cells were run in preflight."])
    return payload


def write_preflight_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Preflight",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: the runbook inputs, paid approval boundary, endpoint variables, and current worktree state were recorded before any supplement cells ran.",
        "Why it matters: the 48-cell paid supplement can start only from the frozen ready package and the required endpoint.",
        f"Next paid batch should continue or stop: `{'continue' if payload['status'] == 'ready_for_package_integrity' else 'stop'}`.",
        "",
        f"- Approved option: `{payload['paid_approval'].get('approved_option')}`.",
        f"- Approved hard cap: `USD {payload['paid_approval'].get('approved_cost_cap_usd')}`.",
        f"- Planned new paid cells: `{payload['planned_new_paid_cells']}`.",
        f"- Known reusable cells: `{payload['known_reusable_cells']}`.",
        f"- Endpoint variables present: `{payload['endpoint_presence']['both_required_endpoint_variables_present']}`.",
        f"- Ready package status: `{payload['ready_package_status']}`.",
        f"- Selected protocol: `{payload['selected_protocol_option']} / {payload['selected_protocol_name']}`.",
        f"- Selected split: `{payload['selected_split_id']}`.",
        f"- `git diff --check`: `{payload['git_diff_check']['passed']}`.",
        f"- Paid calls before preflight: `{payload['paid_calls_run_before_preflight']}`.",
        "",
        "## Dirty Paths",
        "",
    ]
    for bucket, rows in payload["dirty_path_classification"].items():
        lines.append(f"- `{bucket}`: `{len(rows)}`.")
    lines.extend(["", "## Blockers", ""])
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "preflight"), "\n".join(lines))


def write_process_report(config: dict[str, Any], current_step: str, notes: list[str] | None = None) -> None:
    labels = [
        ("preflight", "Step 0 preflight"),
        ("ready_package_integrity", "Step 1 ready-package integrity"),
        ("reuse_manifest", "Step 2 reuse manifest"),
        ("entry_gate", "Step 2 entry gate"),
        ("batch_plan", "Step 2 batch plan"),
        ("batch_1_smoke", "Step 3 smoke batch"),
        ("batch_2_attrs_remainder", "Step 4 attrs batch"),
        ("batch_3_boltons_remainder", "Step 5 boltons batch"),
        ("batch_4_click_remainder", "Step 6 click batch"),
        ("cost_reconciliation", "Step 7 cost reconciliation"),
        ("combined_score_tables_manifest", "Step 7 combined score-table manifest"),
        ("adapter_stratified_metrics", "Step 8 adapter-stratified metrics"),
        ("decision", "Step 9 decision"),
    ]
    completed = [label for key, label in labels if output_path(config, key).exists()]
    lines = [
        "# Blocked Split Missing-Cell Supplement Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
        *(f"- {item}" for item in completed),
        "" if completed else "- None yet.",
        "",
        "Notes:",
        *(f"- {note}" for note in (notes or [])),
        "" if notes else "- No extra notes.",
        "",
        "Follow-up runbook drafted by this worker: `false`.",
    ]
    write_text(report_path(config, "process"), "\n".join(lines))


def ready_split_by_task(ready: dict[str, Any]) -> dict[str, str]:
    split_by_task: dict[str, str] = {}
    for split, task_ids in ready.get("split_labels", {}).items():
        for task_id in task_ids:
            split_by_task[str(task_id)] = str(split)
    return split_by_task


def write_selected_split_plan(config: dict[str, Any], ready: dict[str, Any]) -> Path:
    split_by_task = ready_split_by_task(ready)
    assignments = [
        {
            "candidate_id": task_id,
            "repo_id": task_repo(task_id),
            "split": split_by_task[task_id],
            "selected_split_id": ready["selected_split_id"],
        }
        for task_id in ready["selected_task_ids"]
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "selected_split_plan",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "source_ready_package": rel(source_path(config, "ready_package")),
        "selected_split_id": ready["selected_split_id"],
        "assignments": assignments,
    }
    write_json(output_path(config, "selected_split_plan"), payload)
    return output_path(config, "selected_split_plan")


def write_workspace_matrix_config(config: dict[str, Any], ready: dict[str, Any]) -> Path:
    selected_split_plan = write_selected_split_plan(config, ready)
    lines = [
        "schema_version: barcarolle.workspace_acut_matrix_config.v1",
        "status: configured_for_blocked_split_missing_cell_supplement_paid_execution",
        "phase1_three_repo_paid_validation: true",
        "phase1_blocked_split_missing_cell_supplement: true",
        f"adapter_config: {rel(adapter_config_path(config))}",
        f"task_table: {rel(source_path(config, 'task_table'))}",
        f"split_plan: {rel(selected_split_plan)}",
        f"fresh_certification_attempts: {rel(source_path(config, 'fresh_certification_attempts'))}",
        f"third_repo_certification_attempts: {rel(source_path(config, 'third_repo_certification_attempts'))}",
        f"task_supply_raw_anchor_inventory: {rel(source_path(config, 'task_supply_raw_anchor_inventory'))}",
        f"third_repo_raw_anchor_inventory: {rel(source_path(config, 'third_repo_raw_anchor_inventory'))}",
        f"attrs_source_repair_statement_packets: {rel(source_path(config, 'attrs_source_repair_statement_packets'))}",
        "task_ids:",
        *[f"  - {task_id}" for task_id in ready["selected_task_ids"]],
        "",
    ]
    write_text(matrix_config_path(config), "\n".join(lines))
    return matrix_config_path(config)


def validate_manifest_cells(ready: dict[str, Any]) -> dict[str, Any]:
    expected = sorted(expected_missing_cells(), key=lambda row: (row["repo"], row["split"], row["task_id"], row["adapter_id"]))
    actual = sorted(
        [
            {
                "task_id": str(row["task_id"]),
                "repo": str(row["repo"]),
                "split": str(row["split"]),
                "adapter_id": str(row["adapter_id"]),
            }
            for row in ready.get("missing_paid_cells_to_run", [])
        ],
        key=lambda row: (row["repo"], row["split"], row["task_id"], row["adapter_id"]),
    )
    expected_set = {tuple(row[key] for key in ["task_id", "repo", "split", "adapter_id"]) for row in expected}
    actual_set = {tuple(row[key] for key in ["task_id", "repo", "split", "adapter_id"]) for row in actual}
    return {
        "matches": expected == actual,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "unexpected_cells": [dict(zip(["task_id", "repo", "split", "adapter_id"], row)) for row in sorted(actual_set - expected_set)],
        "missing_cells": [dict(zip(["task_id", "repo", "split", "adapter_id"], row)) for row in sorted(expected_set - actual_set)],
    }


def commit_exists(repo: Path, commit: str) -> bool:
    result = command_result(["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"], timeout=30)
    return result["returncode"] == 0


def validate_ready_package_integrity(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    preflight = read_json(output_path(config, "preflight"), {})
    ready = read_json(source_path(config, "ready_package"), {})
    cost_projection = read_json(source_path(config, "cost_projection"), {})
    design_decision = read_json(source_path(config, "design_review_decision"), {})
    manifest_validation = validate_manifest_cells(ready)
    matrix_path = write_workspace_matrix_config(config, ready)
    packages = workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=matrix_path)
    package_by_id = {package.task_id: package for package in packages}
    ready_split = ready_split_by_task(ready)
    adapters = workspace_acut.load_adapter_configs(adapter_config_path(config))
    cli_checks = {
        "codex": command_result(["codex", "--version"]),
        "kilo": command_result(["kilo", "--version"]),
    }
    package_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for task_id in expected_missing_task_ids():
        package = package_by_id.get(task_id)
        rendered = workspace_acut.render_statement(package) if package else ""
        target_commit = "" if package is None else str(package.target_commit or "")
        row = {
            "task_id": task_id,
            "repo_id": task_repo(task_id),
            "loaded": package is not None,
            "split": None if package is None else package.split,
            "split_matches_selected": package is not None and package.split == ready_split.get(task_id),
            "source_repo_exists": package is not None and package.source_repo.exists(),
            "base_commit": None if package is None else package.base_commit,
            "base_commit_resolvable": bool(package and package.source_repo.exists() and commit_exists(package.source_repo, package.base_commit)),
            "solver_visible_statement_exists": bool(package and package.solver_facing_statement.strip()),
            "rendered_statement_sha256": None if not rendered else hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
            "target_commit_exposed_in_statement": bool(target_commit and target_commit in rendered),
            "raw_diff_marker_in_statement": "diff --git" in rendered or "\n@@" in rendered,
            "hidden_oracle_material_solver_visible": bool((target_commit and target_commit in rendered) or "diff --git" in rendered or "\n@@" in rendered),
            "allowed_code_paths": [] if package is None else package.allowed_code_paths,
            "test_paths": [] if package is None else package.test_paths,
            "tests_non_editable": bool(
                package
                and package.test_paths
                and not set(package.allowed_code_paths).intersection(set(package.test_paths))
                and all(workspace_acut.is_test_path(path) for path in package.test_paths)
            ),
            "verifier_command_configured": bool(package and package.verifier_command),
            "click_title_only_minor_risk_visible": task_repo(task_id) != "click"
            or (package is not None and package.metadata.get("source_context_status") == "pr_title_only_context"),
            "paid_acut_calls_made": False,
        }
        package_rows.append(row)
    option_b = next((option for option in cost_projection.get("options", []) if option.get("option_id") == "B"), {})
    if preflight.get("status") != "ready_for_package_integrity":
        blockers.append("preflight_not_ready")
    if ready.get("status") != "ready":
        blockers.append("ready_package_not_ready")
    if ready.get("selected_protocol_option") != "B" or ready.get("selected_protocol_name") != "same_budget_missing_cell_supplement":
        blockers.append("selected_protocol_not_option_b")
    if ready.get("selected_split_id") != SELECTED_SPLIT_ID:
        blockers.append("selected_split_mismatch")
    if ready.get("selected_budget_id") != "same_budget_20_per_repo":
        blockers.append("selected_budget_mismatch")
    if len(ready.get("selected_task_ids", [])) != 60:
        blockers.append("selected_task_count_mismatch")
    if len(ready.get("known_reusable_cells", [])) != 72:
        blockers.append("known_reusable_cell_count_mismatch")
    if len(ready.get("missing_paid_cells_to_run", [])) != 48:
        blockers.append("missing_paid_cell_count_mismatch")
    if ready.get("adapters") != ADAPTER_IDS:
        blockers.append("adapter_list_mismatch")
    if ready.get("endpoint_requirement", {}).get("required_env_vars") != ["LLM_BASE_URL", "LLM_API_KEY"]:
        blockers.append("endpoint_requirement_mismatch")
    if ready.get("endpoint_requirement", {}).get("fallback_to_other_llm_auth_allowed") is not False:
        blockers.append("llm_auth_fallback_not_disabled")
    if ready.get("click_minor_risk_caveat", {}).get("status") != "visible_title_only_minor_risk":
        blockers.append("click_minor_risk_caveat_missing")
    if design_decision.get("completed_paid_decision_changed") is not False:
        blockers.append("completed_paid_decision_changed")
    if option_b.get("new_paid_cell_count") != 48:
        blockers.append("cost_projection_option_b_cell_count_mismatch")
    if not manifest_validation["matches"]:
        blockers.append("missing_manifest_mismatch")
    if any(not row["loaded"] for row in package_rows):
        blockers.append("missing_task_package_not_loadable")
    if any(not row["split_matches_selected"] for row in package_rows):
        blockers.append("package_split_mismatch")
    if any(not row["source_repo_exists"] or not row["base_commit_resolvable"] for row in package_rows):
        blockers.append("solver_workspace_base_commit_unavailable")
    if any(not row["solver_visible_statement_exists"] for row in package_rows):
        blockers.append("solver_visible_statement_missing")
    if any(row["hidden_oracle_material_solver_visible"] for row in package_rows):
        blockers.append("solver_visible_statement_exposes_hidden_oracle_material")
    if any(not row["tests_non_editable"] for row in package_rows):
        blockers.append("editable_noneditable_path_policy_unenforceable")
    if any(not row["verifier_command_configured"] for row in package_rows):
        blockers.append("verifier_command_missing")
    if sorted(adapters) != ADAPTER_IDS:
        blockers.append("configured_adapters_do_not_match_approval")
    if any(set(adapters[adapter].requires_env) != {"LLM_BASE_URL", "LLM_API_KEY"} for adapter in adapters):
        blockers.append("adapter_endpoint_env_requirement_mismatch")
    if any(cli_checks[name]["returncode"] != 0 for name in ["codex", "kilo"]):
        blockers.append("adapter_cli_unavailable")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "ready_package_integrity",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "ready" if not blockers else "blocked_before_paid_calls",
        "blockers": blockers,
        "ready_package": rel(source_path(config, "ready_package")),
        "matrix_config": rel(matrix_path),
        "selected_split_plan": rel(output_path(config, "selected_split_plan")),
        "selected_split_id": ready.get("selected_split_id"),
        "selected_budget_id": ready.get("selected_budget_id"),
        "selected_task_count": len(ready.get("selected_task_ids", [])),
        "known_reusable_cells": len(ready.get("known_reusable_cells", [])),
        "missing_paid_cells": len(ready.get("missing_paid_cells_to_run", [])),
        "planned_adapters": ready.get("adapters"),
        "endpoint_requirement": ready.get("endpoint_requirement"),
        "click_minor_risk_caveat": ready.get("click_minor_risk_caveat"),
        "claim_boundary": ready.get("claim_boundary"),
        "manifest_validation": manifest_validation,
        "adapter_endpoint_requirements": {adapter: adapters[adapter].requires_env for adapter in sorted(adapters)},
        "adapter_cli_available": {name: cli_checks[name]["returncode"] == 0 for name in ["codex", "kilo"]},
        "no_paid_dry_inspection_passed": not blockers,
        "paid_acut_calls_made": False,
        "package_rows": package_rows,
    }
    write_json(output_path(config, "ready_package_integrity"), payload)
    write_ready_package_integrity_report(config, payload)
    write_process_report(config, current_step="Step 1 ready-package integrity complete", notes=["No paid ACUT cells were run in ready-package integrity."])
    return payload


def write_ready_package_integrity_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Ready Package Integrity",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: the ready package, selected split labels, task package loader, and adapter configs were inspected without invoking ACUTs.",
        "Why it matters: the paid runner can use the frozen 48-cell manifest only if every task and adapter resolves cleanly.",
        f"Next paid batch should continue or stop: `{'continue' if payload['status'] == 'ready' else 'stop'}`.",
        "",
        f"- Selected tasks: `{payload['selected_task_count']}`.",
        f"- Known reusable cells: `{payload['known_reusable_cells']}`.",
        f"- Missing paid cells: `{payload['missing_paid_cells']}`.",
        f"- Missing manifest matches runbook: `{payload['manifest_validation']['matches']}`.",
        f"- No-paid dry inspection passed: `{payload['no_paid_dry_inspection_passed']}`.",
        f"- Adapter CLI available: `{payload['adapter_cli_available']}`.",
        f"- Click caveat: `{payload['click_minor_risk_caveat'].get('status')}`.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "ready_package_integrity"), "\n".join(lines))


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def score_table_index(paths: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    rows_by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    duplicates: list[tuple[str, str]] = []
    for raw_path in sorted(set(paths)):
        path = repo_path(raw_path)
        if not path.exists():
            continue
        prefix = path.name.removesuffix("_score_table.csv")
        for row in read_csv_rows(path):
            key = (str(row["task_id"]), str(row["adapter_id"]))
            if key in rows_by_cell:
                duplicates.append(key)
            rows_by_cell[key] = {
                **row,
                "scoreable_cell": bool_from_csv(row.get("scoreable_cell")),
                "repo": task_repo(str(row["task_id"])),
                "result_prefix": prefix,
                "score_table": rel(path),
            }
    if duplicates:
        raise ValueError(f"duplicate score-table cells: {duplicates[:5]}")
    return rows_by_cell


def paid_score_table_paths(config: dict[str, Any]) -> list[str]:
    manifest = read_json(source_path(config, "paid_validation_score_tables_manifest"), {})
    paths = [str(entry["score_table"]) for entry in manifest.get("entries", [])]
    return sorted(set(paths))


def build_reuse_manifest(config: dict[str, Any], ready: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    score_index = score_table_index(paid_score_table_paths(config))
    selected_split = ready_split_by_task(ready)
    reusable_rows = []
    blockers: list[str] = []
    for cell in ready.get("known_reusable_cells", []):
        key = (str(cell["task_id"]), str(cell["adapter_id"]))
        row = score_index.get(key)
        if row is None:
            blockers.append(f"missing_reusable_score_table_row:{key[0]}:{key[1]}")
            continue
        if str(row.get("terminal_status")) != str(cell.get("terminal_status")):
            blockers.append(f"reusable_terminal_status_mismatch:{key[0]}:{key[1]}")
        if bool(row.get("scoreable_cell")) != bool(cell.get("scoreable_cell")):
            blockers.append(f"reusable_scoreability_mismatch:{key[0]}:{key[1]}")
        reusable_rows.append(
            {
                "task_id": key[0],
                "repo": str(cell["repo"]),
                "adapter_id": key[1],
                "selected_split": selected_split.get(key[0], cell.get("split")),
                "prior_paid_split": str(row.get("split") or cell.get("prior_paid_split") or ""),
                "old_score_table_source_path": row["score_table"],
                "old_result_prefix": row["result_prefix"],
                "old_terminal_status": row.get("terminal_status"),
                "old_scoreability_label": "scoreable" if row.get("scoreable_cell") is True else "non_scoreable",
                "old_scoreable_cell": row.get("scoreable_cell"),
                "old_submission_status": row.get("submission_status"),
                "terminal_outcome_changed": False,
                "assigned_to_selected_blocked_split": True,
                "cell_source": "reused_prior_paid_score_table",
            }
        )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "reuse_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "verified" if not blockers and len(reusable_rows) == 72 else "blocked_before_paid_calls",
        "blockers": blockers,
        "source_ready_package": rel(source_path(config, "ready_package")),
        "source_score_tables": paid_score_table_paths(config),
        "reused_cell_count": len(reusable_rows),
        "expected_reused_cell_count": 72,
        "scoreable_reused_cell_count": sum(1 for row in reusable_rows if row["old_scoreable_cell"] is True),
        "terminal_status_counts": dict(sorted(Counter(row["old_terminal_status"] for row in reusable_rows).items())),
        "reused_cells": sorted(reusable_rows, key=lambda row: (row["repo"], row["selected_split"], row["task_id"], row["adapter_id"])),
    }
    return payload, blockers


def build_batch_plan_payload(config: dict[str, Any], ready: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    ready_missing = {
        (str(row["task_id"]), str(row["adapter_id"]))
        for row in ready.get("missing_paid_cells_to_run", [])
    }
    split_by_task = ready_split_by_task(ready)
    matrix_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for batch in planned_batches():
        for task_id in batch["task_ids"]:
            for adapter_id in adapter_ids(config):
                if (task_id, adapter_id) not in ready_missing:
                    blockers.append(f"planned_paid_cell_outside_missing_manifest:{task_id}:{adapter_id}")
                matrix_rows.append(
                    {
                        "batch_id": batch["batch_id"],
                        "batch_name": batch["name"],
                        "task_id": task_id,
                        "repo": task_repo(task_id),
                        "split": split_by_task.get(task_id),
                        "adapter_id": adapter_id,
                        "result_prefix": result_prefix(config, str(batch["name"]), adapter_id),
                    }
                )
    if len(matrix_rows) != 48:
        blockers.append("planned_paid_cells_not_exactly_48")
    if {row["task_id"] for row in matrix_rows} != set(expected_missing_task_ids()):
        blockers.append("planned_task_set_mismatch")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "batch_plan",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "frozen" if not blockers else "blocked_before_paid_calls",
        "blockers": blockers,
        "planned_unique_tasks": len({row["task_id"] for row in matrix_rows}),
        "planned_cells": len(matrix_rows),
        "planned_adapters": adapter_ids(config),
        "batches": [
            {
                **batch,
                "task_count": len(batch["task_ids"]),
                "cell_count": len(batch["task_ids"]) * len(adapter_ids(config)),
                "result_prefixes": [result_prefix(config, str(batch["name"]), adapter_id) for adapter_id in adapter_ids(config)],
            }
            for batch in planned_batches()
        ],
        "matrix_rows": matrix_rows,
        "new_paid_outcomes_from_this_run_known_when_generated": False,
        "reused_prior_outcomes_known_when_generated": True,
    }
    return payload, blockers


def raw_runtime_staged(config: dict[str, Any]) -> list[str]:
    dirty_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    staged_or_modified = [line for line in dirty_lines if line[:2].strip()]
    return [
        line
        for line in staged_or_modified
        if classify_dirty_paths(config, [line])["ignored_raw_or_runtime"]
    ]


def write_entry_gate(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    ready = read_json(source_path(config, "ready_package"), {})
    preflight = read_json(output_path(config, "preflight"), {})
    integrity = read_json(output_path(config, "ready_package_integrity"), {})
    old_decision_diff = command_result(["git", "diff", "--name-only", "--", rel(source_path(config, "paid_validation_decision"))])
    reuse_manifest, reuse_blockers = build_reuse_manifest(config, ready)
    batch_plan, plan_blockers = build_batch_plan_payload(config, ready)
    blockers: list[str] = []
    if preflight.get("status") != "ready_for_package_integrity":
        blockers.append("preflight_not_ready")
    if integrity.get("status") != "ready":
        blockers.append("ready_package_integrity_not_ready")
    if reuse_manifest["status"] != "verified":
        blockers.append("reusable_cell_provenance_unverifiable")
    if batch_plan["status"] != "frozen":
        blockers.append("batch_plan_not_frozen")
    if not endpoint_presence()["both_required_endpoint_variables_present"]:
        blockers.append("endpoint_proof_missing")
    if old_decision_diff["stdout"].strip():
        blockers.append("old_completed_paid_decision_modified")
    if float(config["budget"]["token_estimated_new_cost_usd"]) > float(config["budget"]["hard_cost_cap_usd"]):
        blockers.append("projected_total_new_cost_exceeds_approved_cap")
    if raw_runtime_staged(config):
        blockers.append("raw_runtime_paths_staged")
    blockers.extend(reuse_blockers)
    blockers.extend(plan_blockers)
    entry_gate = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "entry_gate",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "ready_for_paid_batches" if not blockers else "blocked_before_paid_calls",
        "blockers": blockers,
        "approval_present": preflight.get("paid_approval", {}).get("approved_option") == "same_budget_missing_cell_supplement",
        "endpoint_variables_present": endpoint_presence()["both_required_endpoint_variables_present"],
        "ready_package_integrity_passes": integrity.get("status") == "ready",
        "reused_cells": reuse_manifest["reused_cell_count"],
        "planned_new_paid_cells": batch_plan["planned_cells"],
        "combined_planned_cells": int(reuse_manifest["reused_cell_count"]) + int(batch_plan["planned_cells"]),
        "cost_cap_recorded_usd": float(config["budget"]["hard_cost_cap_usd"]),
        "token_estimated_new_cost_usd": float(config["budget"]["token_estimated_new_cost_usd"]),
        "old_completed_paid_decision_modified": bool(old_decision_diff["stdout"].strip()),
        "no_raw_logs_workspaces_staged": not raw_runtime_staged(config),
        "paid_acut_calls_made": False,
    }
    write_json(output_path(config, "reuse_manifest"), reuse_manifest)
    write_json(output_path(config, "batch_plan"), batch_plan)
    write_json(output_path(config, "entry_gate"), entry_gate)
    write_reuse_manifest_report(config, reuse_manifest)
    write_batch_plan_report(config, batch_plan)
    write_process_report(config, current_step="Step 2 reuse import, entry gate, and batch plan complete", notes=["No paid ACUT cells were run in entry gate."])
    return reuse_manifest, entry_gate, batch_plan


def write_reuse_manifest_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Reuse Manifest",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: prior score-table cells named by the ready package were reindexed under the selected blocked split labels.",
        "Why it matters: these 72 cells can be reused for exploratory accounting without changing historical terminal outcomes.",
        f"Next paid batch should continue or stop: `{'continue' if payload['status'] == 'verified' else 'stop'}`.",
        "",
        f"- Reused cells: `{payload['reused_cell_count']}`.",
        f"- Scoreable reused cells: `{payload['scoreable_reused_cell_count']}`.",
        f"- Terminal statuses: `{payload['terminal_status_counts']}`.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "reuse_manifest"), "\n".join(lines))


def write_batch_plan_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Batch Plan",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: the 48-cell paid batch order was frozen before any new supplement outcome existed.",
        "Why it matters: paid results cannot be used to add, drop, or reorder later batches.",
        f"Next paid batch should continue or stop: `{'continue' if payload['status'] == 'frozen' else 'stop'}`.",
        "",
        f"- Planned unique tasks: `{payload['planned_unique_tasks']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Adapters: `{', '.join(payload['planned_adapters'])}`.",
        "",
        "## Batches",
        "",
    ]
    for batch in payload["batches"]:
        lines.append(f"- Batch `{batch['batch_id']}` `{batch['name']}`: `{batch['task_count']}` tasks, `{batch['cell_count']}` cells.")
    lines.extend(["", "## Blockers", ""])
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "batch_plan"), "\n".join(lines))


def read_score_table(prefix: str) -> list[dict[str, Any]]:
    path = PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"
    if not path.exists():
        return []
    rows = read_csv_rows(path)
    for row in rows:
        row["scoreable_cell"] = bool_from_csv(row.get("scoreable_cell"))
        row["repo"] = task_repo(str(row.get("task_id", "")))
        row["repo_id"] = row["repo"]
        row["result_prefix"] = prefix
        row["cell_source"] = "new_missing_cell_paid_run"
    return rows


def score_rows_for_prefixes(prefixes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prefix in prefixes:
        rows.extend(read_score_table(prefix))
    return rows


def cost_summary_for_prefix(prefix: str) -> dict[str, Any]:
    return read_json(PHASE0_ROOT / "results" / f"{prefix}_cost_summary.json", {})


def cost_value(summary: dict[str, Any], key: str = "observed_or_conservative_estimated_cost_usd") -> float:
    if summary.get(key) is not None:
        return float(summary.get(key) or 0.0)
    for fallback in ["observed_or_conservative_estimated_cost_usd", "conservative_estimated_cost_usd", "estimated_cost_usd"]:
        if summary.get(fallback) is not None:
            return float(summary.get(fallback) or 0.0)
    return 0.0


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_counts = dict(sorted(Counter(str(row.get("terminal_status") or "") for row in rows).items()))
    scoreable = [row for row in rows if row.get("scoreable_cell") is True]
    pass_count = sum(1 for row in scoreable if row.get("terminal_status") == "verified_pass")
    policy_count = sum(1 for row in rows if row.get("terminal_status") == "policy_violation")
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "non_scoreable_cell_count": len(rows) - len(scoreable),
        "scoreability_rate": None if not rows else round(len(scoreable) / len(rows), 4),
        "verified_pass_count": pass_count,
        "verified_fail_count": sum(1 for row in scoreable if row.get("terminal_status") == "verified_fail"),
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "policy_violation_count": policy_count,
        "terminal_status_counts": terminal_counts,
    }


def reusable_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    payload = read_json(output_path(config, "reuse_manifest"), {})
    rows = []
    for row in payload.get("reused_cells", []):
        rows.append(
            {
                "adapter_id": row["adapter_id"],
                "task_id": row["task_id"],
                "repo": row["repo"],
                "repo_id": row["repo"],
                "split": row["selected_split"],
                "terminal_status": row["old_terminal_status"],
                "scoreable_cell": bool(row["old_scoreable_cell"]),
                "submission_status": row["old_submission_status"],
                "result_prefix": row["old_result_prefix"],
                "score_table": row["old_score_table_source_path"],
                "cell_source": "reused_prior_paid_score_table",
            }
        )
    return rows


def combined_rows(config: dict[str, Any], through_batch_id: int | None = None) -> list[dict[str, Any]]:
    return [*reusable_rows(config), *score_rows_for_prefixes(existing_attempted_prefixes_through(config, through_batch_id))]


def existing_attempted_prefixes_through(config: dict[str, Any], through_batch_id: int | None = None) -> list[str]:
    prefixes = planned_result_prefixes(config, through_batch_id)
    return [prefix for prefix in prefixes if (PHASE0_ROOT / "results" / f"{prefix}_score_table.csv").exists()]


def option_b_cost_projection(config: dict[str, Any]) -> dict[str, Any]:
    cost_projection = read_json(source_path(config, "cost_projection"), {})
    return next((option for option in cost_projection.get("options", []) if option.get("option_id") == "B"), {})


def projected_remaining_cost_usd(config: dict[str, Any], through_batch_id: int) -> float:
    option_b = option_b_cost_projection(config)
    per_cell = {
        adapter: float(option_b.get("by_adapter", {}).get(adapter, {}).get("estimated_cost_per_cell_usd") or 0.0)
        for adapter in adapter_ids(config)
    }
    completed_by_adapter = Counter()
    for prefix in existing_attempted_prefixes_through(config, through_batch_id):
        adapter = prefix.rsplit("_", 2)[-2] + "_" + prefix.rsplit("_", 2)[-1] if prefix.endswith("_workspace") else ""
        for known_adapter in adapter_ids(config):
            if prefix.endswith(f"_{known_adapter}"):
                adapter = known_adapter
                break
        completed_by_adapter[adapter] += len(read_score_table(prefix))
    planned_by_adapter = {adapter: 24 for adapter in adapter_ids(config)}
    return round(sum(max(planned_by_adapter[adapter] - completed_by_adapter[adapter], 0) * per_cell[adapter] for adapter in adapter_ids(config)), 8)


def import_usage_for_prefixes(config: dict[str, Any], prefixes: list[str]) -> dict[str, Any]:
    if not prefixes:
        return {}
    ledger_path = PHASE0_ROOT / "results" / "workspace_usage_ledger.jsonl"
    reconciliation_path = PHASE0_ROOT / "results" / "workspace_cost_reconciliation.json"
    previous_ledger = workspace_usage_import.read_jsonl(ledger_path)
    previous_reconciliation = read_json(reconciliation_path, {})
    current = workspace_usage_import.run_import(
        REPO_ROOT,
        prefixes,
        pricing_config_path(config),
        endpoint_host_hash=None,
        allow_missing_price_estimate=False,
    )
    prefix_set = set(prefixes)
    current_ledger = workspace_usage_import.read_jsonl(ledger_path)
    merged_ledger = [row for row in previous_ledger if row.get("result_prefix") not in prefix_set]
    merged_ledger.extend(row for row in current_ledger if row.get("result_prefix") in prefix_set)
    workspace_usage_import.write_jsonl(ledger_path, merged_ledger)

    previous_summaries = [
        summary
        for summary in previous_reconciliation.get("summaries", [])
        if summary.get("result_prefix") not in prefix_set
    ]
    summaries = [*previous_summaries, *current.get("summaries", [])]
    merged = {
        **current,
        "result_prefixes": [str(summary.get("result_prefix")) for summary in summaries],
        "summaries": summaries,
        "totals": {
            "call_count": sum(int(summary.get("call_count") or 0) for summary in summaries),
            "usage_observed_count": sum(int(summary.get("usage_observed_count") or 0) for summary in summaries),
            "conservative_estimated_cost_usd": round(sum(float(summary.get("conservative_estimated_cost_usd") or 0.0) for summary in summaries), 8),
            "observed_token_estimated_cost_usd": round(sum(float(summary.get("observed_token_estimated_cost_usd") or 0.0) for summary in summaries), 8),
            "observed_or_conservative_estimated_cost_usd": round(
                sum(float(summary.get("observed_or_conservative_estimated_cost_usd") or 0.0) for summary in summaries),
                8,
            ),
        },
    }
    total_calls = int(merged["totals"]["call_count"])
    observed = int(merged["totals"]["usage_observed_count"])
    merged["totals"]["usage_observed_rate"] = None if total_calls == 0 else round(observed / total_calls, 4)
    write_json(reconciliation_path, merged)
    workspace_usage_import.write_report(PHASE0_ROOT, summaries)
    return current


def cumulative_summary(config: dict[str, Any], through_batch_id: int | None = None) -> dict[str, Any]:
    rows = combined_rows(config, through_batch_id)
    new_prefixes = existing_attempted_prefixes_through(config, through_batch_id)
    new_rows = score_rows_for_prefixes(new_prefixes)
    summary = summarize_rows(rows)
    new_summary = summarize_rows(new_rows)
    completed_new_cells = new_summary["cell_count"]
    remaining_new_cells = max(int(config["budget"]["planned_new_paid_cells"]) - completed_new_cells, 0)
    max_recoverable_scoreable = summary["scoreable_cell_count"] + remaining_new_cells
    max_recoverable_scoreability = round(max_recoverable_scoreable / int(config["budget"]["planned_combined_cells"]), 4)
    observed_cost = round(sum(cost_value(cost_summary_for_prefix(prefix)) for prefix in new_prefixes), 8)
    projected_remaining = projected_remaining_cost_usd(config, through_batch_id or 0)
    summary.update(
        {
            "combined_planned_cells": int(config["budget"]["planned_combined_cells"]),
            "reused_cells": len(reusable_rows(config)),
            "new_completed_cells": completed_new_cells,
            "new_planned_cells": int(config["budget"]["planned_new_paid_cells"]),
            "new_remaining_cells": remaining_new_cells,
            "new_scoreable_cells": new_summary["scoreable_cell_count"],
            "new_non_scoreable_cells": new_summary["non_scoreable_cell_count"],
            "attempted_result_prefixes": new_prefixes,
            "new_observed_or_conservative_cost_usd": observed_cost,
            "projected_remaining_new_cost_usd": projected_remaining,
            "projected_total_new_cost_usd": round(observed_cost + projected_remaining, 8),
            "hard_cost_cap_usd": float(config["budget"]["hard_cost_cap_usd"]),
            "max_recoverable_scoreability_rate": max_recoverable_scoreability,
        }
    )
    return summary


def stop_conditions(config: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    stops: list[str] = []
    if summary["max_recoverable_scoreability_rate"] < float(config["thresholds"]["minimum_scoreability_rate"]):
        stops.append("scoreability_below_gate_or_cannot_recover_to_gate")
    if int(summary.get("policy_violation_count") or 0) > int(config["thresholds"]["policy_violations_max"]):
        stops.append("policy_violation_count_above_0")
    if float(summary["projected_total_new_cost_usd"]) > float(config["budget"]["hard_cost_cap_usd"]):
        stops.append("projected_total_new_cost_exceeds_approved_cap")
    if not endpoint_presence()["both_required_endpoint_variables_present"]:
        stops.append("endpoint_proof_missing")
    if raw_runtime_staged(config):
        stops.append("raw_or_secret_artifact_would_be_committed")
    return stops


def write_batch_status(config: dict[str, Any], last_payload: dict[str, Any] | None = None) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Batch Status",
        "",
        "Click caveat: `visible_title_only_minor_risk`.",
        "",
    ]
    for batch in planned_batches():
        path = output_path(config, str(batch["output_key"]))
        if not path.exists():
            lines.append(f"- Batch `{batch['batch_id']}` `{batch['name']}`: not run.")
            continue
        payload = read_json(path, {})
        lines.append(
            f"- Batch `{batch['batch_id']}` `{batch['name']}`: `{payload.get('status')}`, batch cells `{payload.get('batch_summary', {}).get('cell_count')}`, cumulative new cells `{payload.get('cumulative_summary', {}).get('new_completed_cells')}`, combined scoreability `{payload.get('cumulative_summary', {}).get('scoreability_rate')}`, projected new cost `${payload.get('cumulative_summary', {}).get('projected_total_new_cost_usd')}`."
        )
    if last_payload:
        lines.extend(["", "Latest continue decision:", f"- `{last_payload.get('continue_decision')}`."])
    write_text(report_path(config, "batch_status"), "\n".join(lines))


def run_batch(batch_id: int, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    entry_gate = read_json(output_path(config, "entry_gate"), {})
    if entry_gate.get("status") != "ready_for_paid_batches":
        raise RuntimeError("entry gate is not ready for paid batches")
    if not os.environ.get("LLM_BASE_URL") or not os.environ.get("LLM_API_KEY"):
        raise RuntimeError("LLM_BASE_URL and LLM_API_KEY must be present in the run-batch process environment")
    batch = batch_for_id(batch_id)
    if batch_id > 1:
        previous = read_json(output_path(config, batch_for_id(batch_id - 1)["output_key"]), {})
        if previous.get("stop_conditions"):
            raise RuntimeError(f"previous batch stop conditions are set: {previous['stop_conditions']}")
    prefixes = []
    for adapter_id in adapter_ids(config):
        prefix = result_prefix(config, str(batch["name"]), adapter_id)
        prefixes.append(prefix)
        workspace_acut.run_matrix(
            REPO_ROOT,
            "matrix",
            adapter_config_path=adapter_config_path(config),
            adapter_id=adapter_id,
            matrix_config_path=matrix_config_path(config),
            result_prefix=prefix,
            task_ids=list(batch["task_ids"]),
        )
    import_usage_for_prefixes(config, existing_attempted_prefixes_through(config, batch_id))
    batch_rows = score_rows_for_prefixes(prefixes)
    batch_summary = summarize_rows(batch_rows)
    cumulative = cumulative_summary(config, batch_id)
    stops = stop_conditions(config, cumulative)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": batch["name"],
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "batch_complete_continue" if not stops and batch_id < 4 else "batch_complete_stop" if stops else "all_batches_complete",
        "batch_id": batch_id,
        "batch_name": batch["name"],
        "task_ids": list(batch["task_ids"]),
        "result_prefixes": prefixes,
        "batch_summary": batch_summary,
        "cumulative_summary": cumulative,
        "endpoint_compliance": endpoint_presence(),
        "raw_oracle_exposure_detected": False,
        "click_minor_risk_caveat": "visible_title_only_minor_risk",
        "stop_conditions": stops,
        "continue_decision": "continue_to_next_batch" if not stops and batch_id < 4 else "stop_before_next_batch" if stops else "all_batches_complete",
    }
    write_json(output_path(config, str(batch["output_key"])), payload)
    write_batch_status(config, payload)
    write_process_report(config, current_step=f"Batch {batch_id} complete", notes=[f"Continue decision: {payload['continue_decision']}."])
    return payload


def non_scoreable_by_status(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("terminal_status") or "") for row in rows if row.get("scoreable_cell") is not True)
    return {status: count for status, count in sorted(counts.items())}


def build_combined_score_tables_manifest(config: dict[str, Any], prefixes: list[str]) -> dict[str, Any]:
    reuse = read_json(output_path(config, "reuse_manifest"), {})
    new_entries = []
    for prefix in prefixes:
        rows = read_score_table(prefix)
        summary = summarize_rows(rows)
        new_entries.append(
            {
                "cell_source": "new_missing_cell_paid_run",
                "result_prefix": prefix,
                "score_table": rel(PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"),
                "matrix": rel(PHASE0_ROOT / "results" / f"{prefix}_matrix.json"),
                "submissions": rel(PHASE0_ROOT / "results" / f"{prefix}_submissions.jsonl"),
                "verifier_results": rel(PHASE0_ROOT / "results" / f"{prefix}_verifier_results.jsonl"),
                "cost_ledger": rel(PHASE0_ROOT / "results" / f"{prefix}_cost_ledger.jsonl"),
                "planned_cells": len(rows),
                "completed_cells": len(rows),
                "scoreable_cells": summary["scoreable_cell_count"],
                "non_scoreable_cells": summary["non_scoreable_cell_count"],
                "non_scoreable_by_status": non_scoreable_by_status(rows),
            }
        )
    rows = combined_rows(config)
    summary = summarize_rows(rows)
    coverage: dict[str, dict[str, int]] = defaultdict(lambda: {"planned": 0, "completed": 0, "scoreable": 0})
    for row in rows:
        key = f"{row.get('adapter_id')}|{row.get('repo')}|{row.get('split')}"
        coverage[key]["completed"] += 1
        if row.get("scoreable_cell") is True:
            coverage[key]["scoreable"] += 1
    ready = read_json(source_path(config, "ready_package"), {})
    for task_id in ready.get("selected_task_ids", []):
        repo = task_repo(str(task_id))
        split = ready_split_by_task(ready).get(str(task_id))
        for adapter_id in adapter_ids(config):
            coverage[f"{adapter_id}|{repo}|{split}"]["planned"] += 1
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "combined_score_tables_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if summary["cell_count"] == int(config["budget"]["planned_combined_cells"]) else "partial",
        "planned_selected_cells": int(config["budget"]["planned_combined_cells"]),
        "completed_cells": summary["cell_count"],
        "scoreable_cells": summary["scoreable_cell_count"],
        "non_scoreable_cells": summary["non_scoreable_cell_count"],
        "non_scoreable_by_status": non_scoreable_by_status(rows),
        "reused_result_sources": reuse.get("source_score_tables", []),
        "reused_cell_count": len(reusable_rows(config)),
        "new_result_prefixes": prefixes,
        "new_entries": new_entries,
        "coverage_by_adapter_repo_split": {key: dict(value) for key, value in sorted(coverage.items())},
        "provider_billed_exact_cost_available": False,
    }


def reconcile_cost(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    prefixes = existing_attempted_prefixes(config)
    reconciliation = import_usage_for_prefixes(config, prefixes) if prefixes else {}
    summaries = [cost_summary_for_prefix(prefix) for prefix in prefixes]
    option_b = option_b_cost_projection(config)
    historical_reused = float(option_b.get("total_token_estimated_historical_reused_cost_usd") or 0.0)
    new_observed = round(sum(cost_value(summary, "observed_token_estimated_cost_usd") for summary in summaries), 8)
    new_observed_or_conservative = round(sum(cost_value(summary) for summary in summaries), 8)
    conservative = round(sum(cost_value(summary, "conservative_estimated_cost_usd") for summary in summaries), 8)
    call_count = sum(int(summary.get("call_count") or 0) for summary in summaries)
    usage_count = sum(int(summary.get("usage_observed_count") or 0) for summary in summaries)
    manifest = build_combined_score_tables_manifest(config, prefixes)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "cost_reconciliation",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if prefixes and manifest["completed_cells"] == int(config["budget"]["planned_combined_cells"]) else "partial_or_not_run",
        "new_result_prefixes": prefixes,
        "workspace_cost_reconciliation": rel(PHASE0_ROOT / "results" / "workspace_cost_reconciliation.json") if reconciliation else None,
        "planned_token_estimated_new_cost_usd": float(config["budget"]["token_estimated_new_cost_usd"]),
        "observed_token_estimated_new_cost_usd": new_observed,
        "observed_or_conservative_new_cost_usd": new_observed_or_conservative,
        "conservative_estimated_new_cost_usd": conservative,
        "historical_reused_token_estimated_cost_usd": historical_reused,
        "total_token_estimated_historical_plus_new_cost_usd": round(historical_reused + new_observed_or_conservative, 8),
        "usage_observed_rate": None if call_count == 0 else round(usage_count / call_count, 4),
        "actual_provider_billed_cost_usd": None,
        "provider_billed_exact_cost_available": False,
        "cost_latency_accounting_complete": bool(prefixes and call_count == sum(len(read_score_table(prefix)) for prefix in prefixes)),
    }
    write_json(output_path(config, "cost_reconciliation"), payload)
    write_json(output_path(config, "combined_score_tables_manifest"), manifest)
    write_cost_report(config, payload)
    write_process_report(config, current_step="Step 7 cost reconciliation and score tables complete")
    return payload, manifest


def write_cost_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Cost Reconciliation",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "What happened: usage and cost summaries for the new supplement prefixes were reconciled with the reused historical cell estimate.",
        "Why it matters: the mixed 72+48 table must keep old reusable spend separate from new paid spend.",
        f"Next paid batch should continue or stop: `{'complete' if payload['status'] == 'complete' else 'stop'}`.",
        "",
        f"- New result prefixes: `{len(payload['new_result_prefixes'])}`.",
        f"- Planned new token-estimated cost: `USD {payload['planned_token_estimated_new_cost_usd']}`.",
        f"- Observed token-estimated new cost: `USD {payload['observed_token_estimated_new_cost_usd']}`.",
        f"- Observed-or-conservative new cost: `USD {payload['observed_or_conservative_new_cost_usd']}`.",
        f"- Historical reused token-estimated cost: `USD {payload['historical_reused_token_estimated_cost_usd']}`.",
        f"- Provider-billed exact cost available: `{payload['provider_billed_exact_cost_available']}`.",
        f"- Usage observed rate: `{payload['usage_observed_rate']}`.",
        f"- Cost/latency accounting complete: `{payload['cost_latency_accounting_complete']}`.",
    ]
    write_text(report_path(config, "cost_reconciliation"), "\n".join(lines))


def split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for split in SPLITS:
        split_rows = [row for row in rows if row.get("split") == split]
        metrics[split] = summarize_rows(split_rows)
    b_rate = metrics["B_eval"]["pass_rate"]
    h_rate = metrics["H_future"]["pass_rate"]
    metrics["absolute_gap"] = None if b_rate is None or h_rate is None else round(abs(b_rate - h_rate), 4)
    return metrics


def repo_split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for repo in REPOS:
        metrics[repo] = split_metrics([row for row in rows if row.get("repo") == repo])
    return metrics


def adapter_cost_latency(config: dict[str, Any], adapter_id: str) -> dict[str, Any]:
    option_b = option_b_cost_projection(config)
    baseline = option_b.get("by_adapter", {}).get(adapter_id, {})
    prefixes = [prefix for prefix in existing_attempted_prefixes(config) if prefix.endswith(f"_{adapter_id}")]
    summaries = [cost_summary_for_prefix(prefix) for prefix in prefixes]
    latencies = [float(summary["median_latency_seconds"]) for summary in summaries if summary.get("median_latency_seconds") is not None]
    return {
        "new_result_prefixes": prefixes,
        "planned_new_token_estimated_cost_usd": float(baseline.get("token_estimated_new_cost_usd") or 0.0),
        "observed_token_estimated_new_cost_usd": round(sum(cost_value(summary, "observed_token_estimated_cost_usd") for summary in summaries), 8),
        "observed_or_conservative_new_cost_usd": round(sum(cost_value(summary) for summary in summaries), 8),
        "historical_reused_token_estimated_cost_usd": float(baseline.get("token_estimated_historical_reused_cost_usd") or 0.0),
        "total_historical_plus_new_token_estimated_cost_usd": round(
            float(baseline.get("token_estimated_historical_reused_cost_usd") or 0.0)
            + sum(cost_value(summary) for summary in summaries),
            8,
        ),
        "new_usage_observed_rate": None
        if not summaries
        else round(
            sum(int(summary.get("usage_observed_count") or 0) for summary in summaries)
            / max(sum(int(summary.get("call_count") or 0) for summary in summaries), 1),
            4,
        ),
        "new_median_latency_seconds": None if not latencies else round(float(statistics.median(latencies)), 3),
        "historical_baseline_median_latency_seconds": baseline.get("median_latency_seconds"),
        "provider_billed_exact_cost_available": False,
    }


def paired_disagreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_task_adapter: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row.get("scoreable_cell") is True:
            by_task_adapter[(str(row["task_id"]), str(row["adapter_id"]))] = row
    selected_tasks = sorted({row["task_id"] for row in rows})
    counts = Counter()
    paired = 0
    for task_id in selected_tasks:
        codex = by_task_adapter.get((task_id, "codex_workspace"))
        kilo = by_task_adapter.get((task_id, "kilo_workspace"))
        if not (codex and kilo):
            continue
        paired += 1
        codex_pass = codex.get("terminal_status") == "verified_pass"
        kilo_pass = kilo.get("terminal_status") == "verified_pass"
        if codex_pass and kilo_pass:
            counts["both_pass"] += 1
        elif not codex_pass and not kilo_pass:
            counts["both_fail"] += 1
        elif codex_pass:
            counts["codex_only_pass"] += 1
        else:
            counts["kilo_only_pass"] += 1
    disagreement = counts["codex_only_pass"] + counts["kilo_only_pass"]
    return {
        "paired_task_count": paired,
        "both_pass": counts["both_pass"],
        "both_fail": counts["both_fail"],
        "codex_only_pass": counts["codex_only_pass"],
        "kilo_only_pass": counts["kilo_only_pass"],
        "disagreement_count": disagreement,
        "disagreement_rate": None if paired == 0 else round(disagreement / paired, 4),
    }


def pooled_unweighted(rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_repo = repo_split_metrics(rows)
    b_rates = [per_repo[repo]["B_eval"]["pass_rate"] for repo in REPOS if per_repo[repo]["B_eval"]["pass_rate"] is not None]
    h_rates = [per_repo[repo]["H_future"]["pass_rate"] for repo in REPOS if per_repo[repo]["H_future"]["pass_rate"] is not None]
    pooled_b = None if len(b_rates) != 3 else round(float(statistics.mean(b_rates)), 4)
    pooled_h = None if len(h_rates) != 3 else round(float(statistics.mean(h_rates)), 4)
    gap = None if pooled_b is None or pooled_h is None else round(abs(pooled_b - pooled_h), 4)
    return {
        "B_eval_pass_rate": pooled_b,
        "H_future_pass_rate": pooled_h,
        "primary_absolute_gap": gap,
    }


def compute_metrics(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = combined_rows(config)
    summary = summarize_rows(rows)
    cost = read_json(output_path(config, "cost_reconciliation"), {})
    by_adapter = {}
    for adapter_id in adapter_ids(config):
        adapter_rows = [row for row in rows if row.get("adapter_id") == adapter_id]
        adapter_summary = summarize_rows(adapter_rows)
        adapter_splits = split_metrics(adapter_rows)
        by_adapter[adapter_id] = {
            "adapter_id": adapter_id,
            "selected_cells": 60,
            "reused_cells": sum(1 for row in adapter_rows if row.get("cell_source") == "reused_prior_paid_score_table"),
            "new_cells": sum(1 for row in adapter_rows if row.get("cell_source") == "new_missing_cell_paid_run"),
            "completed_cells": adapter_summary["cell_count"],
            "scoreable_cells": adapter_summary["scoreable_cell_count"],
            "scoreability_rate": adapter_summary["scoreability_rate"],
            "pass_rate": adapter_summary["pass_rate"],
            "B_eval_pass_rate": adapter_splits["B_eval"]["pass_rate"],
            "H_future_pass_rate": adapter_splits["H_future"]["pass_rate"],
            "B_eval_H_future_absolute_gap": adapter_splits["absolute_gap"],
            "per_repo": repo_split_metrics(adapter_rows),
            "policy_violation_count": adapter_summary["policy_violation_count"],
            "raw_oracle_exposure_detected": False,
            "endpoint_compliance_status": "pass" if endpoint_presence()["both_required_endpoint_variables_present"] else "fail",
            "cost_latency": adapter_cost_latency(config, adapter_id),
        }
    pooled = pooled_unweighted(rows)
    threshold = float(config["thresholds"]["exploratory_gap_threshold"])
    old_metrics = read_json(source_path(config, "paid_validation_metrics"), {})
    previous_pooled_gap = (old_metrics.get("pooled_unweighted") or {}).get("primary_absolute_gap")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_stratified_metrics",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if summary["cell_count"] == int(config["budget"]["planned_combined_cells"]) else "partial_or_not_run",
        "adapter_stratified_results_first": True,
        "by_adapter": by_adapter,
        "paired_adapter_disagreement": paired_disagreement(rows),
        "pooled_summary_secondary": pooled,
        "exploratory_threshold_diagnostic": {
            "threshold": threshold,
            "pooled_absolute_gap": pooled["primary_absolute_gap"],
            "passes_exploratory_gap_threshold": None if pooled["primary_absolute_gap"] is None else pooled["primary_absolute_gap"] <= threshold,
            "formal_preregistered_threshold_claim": False,
        },
        "previous_split_diagnostic_comparison": {
            "previous_three_repo_primary_pooled_gap": previous_pooled_gap,
            "supplement_pooled_gap": pooled["primary_absolute_gap"],
            "looks_healthier_than_previous_pooled_gap": None
            if previous_pooled_gap is None or pooled["primary_absolute_gap"] is None
            else pooled["primary_absolute_gap"] < previous_pooled_gap,
            "comparison_claim_boundary": "exploratory_diagnostic_only",
        },
        "combined_summary": {
            **summary,
            "planned_cells": int(config["budget"]["planned_combined_cells"]),
            "reused_cells": len(reusable_rows(config)),
            "new_cells": sum(1 for row in rows if row.get("cell_source") == "new_missing_cell_paid_run"),
            "policy_violation_count": summary["policy_violation_count"],
            "endpoint_compliance_status": "pass" if endpoint_presence()["both_required_endpoint_variables_present"] else "fail",
            "cost_latency_accounting_status": "complete" if cost.get("cost_latency_accounting_complete") else "incomplete",
            "observed_or_conservative_new_cost_usd": cost.get("observed_or_conservative_new_cost_usd"),
        },
        "click_minor_risk_caveat": "visible_title_only_minor_risk",
        "predictive_validity_established": False,
        "formal_preregistration_claim_allowed": False,
    }
    write_json(output_path(config, "adapter_stratified_metrics"), payload)
    write_metrics_report(config, payload)
    write_process_report(config, current_step="Step 8 adapter-stratified metrics complete")
    return payload


def write_metrics_report(config: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Missing-Cell Supplement Adapter-Stratified Metrics",
        "",
        f"Status: `{metrics['status']}`.",
        "",
        "What happened: combined 72 reused plus new supplement cells were summarized by adapter before pooled summaries.",
        "Why it matters: Codex and Kilo behavior is not interchangeable, so adapter-level results are the primary view.",
        "Next paid batch should continue or stop: `complete`.",
        "",
        "## Adapter Results",
        "",
    ]
    for adapter_id, row in metrics["by_adapter"].items():
        lines.append(
            f"- `{adapter_id}`: cells `{row['completed_cells']}`, scoreable `{row['scoreable_cells']}`, pass rate `{row['pass_rate']}`, B_eval `{row['B_eval_pass_rate']}`, H_future `{row['H_future_pass_rate']}`, gap `{row['B_eval_H_future_absolute_gap']}`."
        )
    lines.extend(
        [
            "",
            "## Paired Disagreement",
            "",
            f"- Paired task count: `{metrics['paired_adapter_disagreement']['paired_task_count']}`.",
            f"- Disagreement rate: `{metrics['paired_adapter_disagreement']['disagreement_rate']}`.",
            "",
            "## Pooled Secondary Summary",
            "",
            f"- B_eval pass rate: `{metrics['pooled_summary_secondary']['B_eval_pass_rate']}`.",
            f"- H_future pass rate: `{metrics['pooled_summary_secondary']['H_future_pass_rate']}`.",
            f"- Absolute gap: `{metrics['pooled_summary_secondary']['primary_absolute_gap']}`.",
            f"- Exploratory <= 0.15 diagnostic: `{metrics['exploratory_threshold_diagnostic']['passes_exploratory_gap_threshold']}`.",
            "",
            "Claim boundary: exploratory evidence only. This is not formal preregistered predictive validity.",
            "Click caveat: `visible_title_only_minor_risk`.",
        ]
    )
    write_text(report_path(config, "adapter_stratified_metrics"), "\n".join(lines))


def verification_commands() -> list[list[str]]:
    return [
        [
            "uv",
            "run",
            "--project",
            "experiments/phase1_compiler",
            "pytest",
            "experiments/phase1_compiler/tests/test_phase1_blocked_split_missing_cell_supplement_paid_execution.py",
            "-q",
        ],
        ["uv", "run", "--project", "experiments/phase1_compiler", "pytest", "experiments/phase1_compiler/tests", "-q"],
        ["git", "diff", "--check"],
        ["git", "status", "--short", "--untracked-files=all"],
    ]


def run_verification_commands() -> list[dict[str, Any]]:
    results = []
    for command in verification_commands():
        timeout = 180 if command[:4] == ["uv", "run", "--project", "experiments/phase1_compiler"] else 60
        result = command_result(command, timeout=timeout)
        output = (result["stdout"] or result["stderr"]).strip()
        results.append(
            {
                "command": " ".join(command),
                "returncode": result["returncode"],
                "result": output.splitlines()[-1] if output else "passed",
                "stdout_tail": result["stdout"][-1000:],
                "stderr_tail": result["stderr"][-1000:],
            }
        )
    return results


def recent_run_commits() -> list[str]:
    raw = command_stdout(["git", "log", "--oneline", "-n", "20"])
    return [
        line
        for line in raw.splitlines()
        if "blocked split missing-cell supplement" in line.lower()
        or "blocked split supplement" in line.lower()
    ]


def write_decision(config_path: Path = DEFAULT_CONFIG, include_verification: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    metrics = read_json(output_path(config, "adapter_stratified_metrics"), {})
    cost = read_json(output_path(config, "cost_reconciliation"), {})
    manifest = read_json(output_path(config, "combined_score_tables_manifest"), {})
    combined = metrics.get("combined_summary") or {}
    completed_new = int(combined.get("new_cells") or 0)
    completed_all = completed_new == int(config["budget"]["planned_new_paid_cells"]) and combined.get("cell_count") == int(config["budget"]["planned_combined_cells"])
    non_scoreable = int(combined.get("non_scoreable_cell_count") or 0)
    if completed_new == 0:
        label = "blocked_split_missing_cell_supplement_blocked_before_paid_calls"
    elif not completed_all:
        label = "blocked_split_missing_cell_supplement_blocked_after_partial_run"
    elif non_scoreable:
        label = "blocked_split_missing_cell_supplement_completed_with_non_scoreable_cells"
    else:
        label = "blocked_split_missing_cell_supplement_completed_exploratory"
    tests_run = run_verification_commands() if include_verification else []
    gates_clean = {
        "endpoint": combined.get("endpoint_compliance_status"),
        "policy_violation_count": combined.get("policy_violation_count"),
        "raw_oracle_exposure": False,
        "cost_accounting": combined.get("cost_latency_accounting_status"),
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": label,
        "paid_cells_ran": completed_new > 0,
        "completed_new_paid_cells": completed_new,
        "reused_cells": int(combined.get("reused_cells") or 0),
        "combined_selected_cells_completed": int(combined.get("cell_count") or 0),
        "scoreable_cells": int(combined.get("scoreable_cell_count") or 0),
        "scoreability_rate": combined.get("scoreability_rate"),
        "policy_violation_count": int(combined.get("policy_violation_count") or 0),
        "raw_oracle_exposure_detected": False,
        "endpoint_compliance_status": combined.get("endpoint_compliance_status"),
        "new_token_estimated_cost_usd": cost.get("observed_or_conservative_new_cost_usd"),
        "planned_new_token_estimated_cost_usd": cost.get("planned_token_estimated_new_cost_usd"),
        "exact_provider_bill_available": False,
        "provider_billed_exact_cost_available": False,
        "click_minor_risk_caveat": "visible_title_only_minor_risk",
        "claim_boundary": {
            "blocked_split_missing_cell_supplement_executed": completed_new > 0,
            "selected_same_budget_blocked_split_completed": completed_all,
            "exploratory_evidence_only": True,
            "formal_preregistration_completed": False,
            "predictive_validity_established": False,
            "clean_pre_outcome_validation": False,
        },
        "rq_answers": {
            "RQ1_did_all_48_missing_cells_run": completed_new == 48,
            "RQ2_were_72_reusable_cells_traceable": int(combined.get("reused_cells") or 0) == 72,
            "RQ3_combined_selected_cell_scoreability_rate": combined.get("scoreability_rate"),
            "RQ4_gates_clean": gates_clean,
            "RQ5_new_token_estimated_cost": cost.get("observed_or_conservative_new_cost_usd"),
            "RQ6_adapter_stratified_B_eval_H_future_results": {
                adapter: {
                    "B_eval_pass_rate": row.get("B_eval_pass_rate"),
                    "H_future_pass_rate": row.get("H_future_pass_rate"),
                    "absolute_gap": row.get("B_eval_H_future_absolute_gap"),
                }
                for adapter, row in (metrics.get("by_adapter") or {}).items()
            },
            "RQ7_codex_kilo_disagreement": metrics.get("paired_adapter_disagreement"),
            "RQ8_exploratory_diagnostic_vs_previous_split": metrics.get("previous_split_diagnostic_comparison"),
            "RQ9_allowed_and_disallowed_claims": {
                "allowed": [
                    "blocked_split_missing_cell_supplement_executed",
                    "selected_same_budget_blocked_split_completed" if completed_all else "partial_missing_cell_supplement_recorded",
                    "adapter_stratified_exploratory_metrics_recorded",
                ],
                "not_allowed": [
                    "formal_preregistration_completed",
                    "predictive_validity_established",
                    "clean_pre_outcome_validation",
                    "production_benchmark_ranking",
                ],
            },
        },
        "completed_steps": [key for key in config["outputs"] if output_path(config, key).exists()],
        "commits_made_during_run": [*recent_run_commits(), "Close blocked split missing-cell supplement run (this commit)"],
        "tests_run": tests_run,
        "known_blockers": [] if completed_all else ["missing-cell supplement did not complete all planned new cells"],
        "raw_artifacts_committed": False,
        "followup_runbook_written_by_worker": False,
        "selected_blocked_split_changed": False,
        "completed_paid_decision_changed": False,
        "combined_score_tables_manifest": rel(output_path(config, "combined_score_tables_manifest")) if manifest else None,
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload, metrics, cost)
    write_process_report(config, current_step="Step 9 decision complete")
    return payload


def write_decision_report(config: dict[str, Any], payload: dict[str, Any], metrics: dict[str, Any], cost: dict[str, Any]) -> None:
    combined = metrics.get("combined_summary") or {}
    lines = [
        "# Blocked Split Missing-Cell Supplement Decision",
        "",
        f"Decision label: `{payload['decision_label']}`.",
        "",
        "What happened: the selected same-budget blocked split was evaluated as a mixed exploratory table using reused prior cells plus newly run missing cells.",
        "Why it matters: this fills the selected 120-cell table without rerunning cells whose committed prior outcomes already matched the selected task/adapter pairs.",
        "Next paid batch should continue or stop: `complete`.",
        "",
        f"- Planned new cells: `{config['budget']['planned_new_paid_cells']}`.",
        f"- Completed new cells: `{payload['completed_new_paid_cells']}`.",
        f"- Reused cells: `{payload['reused_cells']}`.",
        f"- Combined selected cells: `{payload['combined_selected_cells_completed']} / {config['budget']['planned_combined_cells']}`.",
        f"- Scoreable cells: `{payload['scoreable_cells']}`.",
        f"- Scoreability rate: `{payload['scoreability_rate']}`.",
        f"- Policy violations: `{payload['policy_violation_count']}`.",
        "- Raw oracle exposure: `false`.",
        f"- Endpoint compliance: `{payload['endpoint_compliance_status']}`.",
        f"- New token-estimated cost: `USD {payload['new_token_estimated_cost_usd']}`.",
        "- Exact provider bill: `unavailable`.",
        "",
        "Adapter-stratified results:",
    ]
    for adapter, row in (metrics.get("by_adapter") or {}).items():
        lines.append(
            f"- `{adapter}`: B_eval `{row.get('B_eval_pass_rate')}`, H_future `{row.get('H_future_pass_rate')}`, gap `{row.get('B_eval_H_future_absolute_gap')}`."
        )
    lines.extend(
        [
            "",
            f"Codex/Kilo disagreement rate: `{(metrics.get('paired_adapter_disagreement') or {}).get('disagreement_rate')}`.",
            f"Pooled secondary gap: `{(metrics.get('pooled_summary_secondary') or {}).get('primary_absolute_gap')}`.",
            f"Exploratory <= 0.15 diagnostic: `{(metrics.get('exploratory_threshold_diagnostic') or {}).get('passes_exploratory_gap_threshold')}`.",
            "",
            "Interpretation: this is exploratory evidence. The selected split was designed after earlier paid results existed, so this cannot be described as formal preregistered predictive validity or clean pre-outcome validation.",
            "Click caveat: `visible_title_only_minor_risk`.",
            "No raw logs, raw prompts, raw completions, solver workspaces, verifier workspaces, raw diffs, raw test patches, or secrets are committed by this report.",
        ]
    )
    if combined.get("cost_latency_accounting_status") != "complete":
        lines.append("Cost/accounting caveat: accounting is incomplete and must be treated as a blocker.")
    if cost.get("provider_billed_exact_cost_available") is False:
        lines.append("Provider-billed exact cost is not claimed because no bill artifact is available.")
    write_text(report_path(config, "decision"), "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the blocked split missing-cell supplement paid runbook.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("preflight")
    subcommands.add_parser("ready-package-integrity")
    subcommands.add_parser("entry-gate")
    subcommands.add_parser("batch-plan")
    run_batch_parser = subcommands.add_parser("run-batch")
    run_batch_parser.add_argument("--batch-id", type=int, required=True)
    subcommands.add_parser("cost-reconciliation")
    subcommands.add_parser("metrics")
    decision_parser = subcommands.add_parser("decision")
    decision_parser.add_argument("--include-verification", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config)
    if args.command == "preflight":
        build_preflight(config_path)
    elif args.command == "ready-package-integrity":
        validate_ready_package_integrity(config_path)
    elif args.command == "entry-gate":
        write_entry_gate(config_path)
    elif args.command == "batch-plan":
        config = load_config(config_path)
        ready = read_json(source_path(config, "ready_package"), {})
        payload, _ = build_batch_plan_payload(config, ready)
        write_json(output_path(config, "batch_plan"), payload)
        write_batch_plan_report(config, payload)
    elif args.command == "run-batch":
        run_batch(args.batch_id, config_path)
    elif args.command == "cost-reconciliation":
        reconcile_cost(config_path)
    elif args.command == "metrics":
        compute_metrics(config_path)
    elif args.command == "decision":
        write_decision(config_path, include_verification=args.include_verification)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
