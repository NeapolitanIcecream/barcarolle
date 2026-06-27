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


DEFAULT_CONFIG = ROOT / "configs" / "phase1_three_repo_paid_validation.yaml"
SCHEMA_VERSION = "barcarolle.phase1_three_repo_paid_validation.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_three_repo_paid_validation_output.v1"
PRIMARY_PILOT_TASK_IDS = [
    "attrs__v2__207",
    "attrs__v2__264",
    "attrs__v2__187",
    "attrs__v2__044",
    "attrs__v2__253",
    "attrs__v2__237",
    "attrs__v2__250",
    "attrs__v2__227",
    "attrs__v2__048",
    "attrs__v2__223",
    "attrs__v2__261",
    "attrs__v2__206",
    "attrs__v2__196",
    "attrs__v2__052",
    "attrs__v2__056",
    "attrs__v2__220",
    "attrs__v2__215",
    "attrs__v2__158",
    "attrs__v2__202",
    "attrs__v2__235",
    "boltons__v2__135",
    "boltons__v2__148",
    "boltons__v2__229",
    "boltons__v2__142",
    "boltons__v2__068",
    "boltons__v2__133",
    "boltons__v2__147",
    "boltons__v2__093",
    "boltons__v2__007",
    "boltons__v2__155",
    "boltons__v2__141",
    "boltons__v2__163",
    "boltons__v2__170",
    "boltons__v2__144",
    "boltons__v2__091",
    "boltons__v2__086",
    "boltons__v2__006",
    "boltons__v2__087",
    "boltons__v2__164",
    "boltons__v2__140",
    "click__third__275",
    "click__third__045",
    "click__third__203",
    "click__third__217",
    "click__third__271",
    "click__third__204",
    "click__third__278",
    "click__third__201",
    "click__third__274",
    "click__third__200",
    "click__third__208",
    "click__third__213",
    "click__third__216",
    "click__third__250",
    "click__third__206",
    "click__third__199",
    "click__third__166",
    "click__third__050",
    "click__third__205",
    "click__third__238",
]
TERMINAL_SCOREABLE = {"verified_pass", "verified_fail"}
TERMINAL_NON_SCOREABLE = {"policy_violation", "invalid_output", "acut_harness_error", "harness_error", "timeout"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(path)
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
        raise ValueError("unexpected phase1 three-repo paid validation config schema_version")
    config["_path"] = str(path)
    return config


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def source_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["source_artifacts"][key])


def matrix_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["matrix_config"])


def adapter_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["adapter_config"])


def pricing_config_path(config: dict[str, Any]) -> Path:
    return repo_path(config["workspace_runner"]["pricing_config"])


def adapter_ids(config: dict[str, Any]) -> list[str]:
    return [str(item) for item in config["approval"]["approved_adapters"]]


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


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def digest_payload(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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
        rel(PHASE0_ROOT / "tools" / "workspace_acut_run.py"),
        rel(ROOT / "tools" / "phase1_three_repo_paid_validation.py"),
        rel(ROOT / "tests" / "test_phase1_three_repo_paid_validation.py"),
        rel(matrix_config_path(config)),
    }
    paths.update(rel(path) for path in config.get("outputs", {}).values())
    paths.update(rel(path) for path in config.get("reports", {}).values())
    return paths


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_commit_paths(config)
    ignored_prefixes = [
        "experiments/phase0_headroom/results/raw/",
        "experiments/phase0_headroom/workspaces/",
        "experiments/phase0_headroom/external_repos/",
        "experiments/phase1_compiler/tmp/three_repo_paid_validation/",
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


def ids_by_repo() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"attrs": [], "boltons": [], "click": []}
    for task_id in PRIMARY_PILOT_TASK_IDS:
        grouped[task_id.split("__", 1)[0]].append(task_id)
    return grouped


def planned_batches() -> list[dict[str, Any]]:
    grouped = ids_by_repo()
    return [
        {
            "batch_id": 1,
            "output_key": "batch_1_smoke",
            "name": "batch_1_smoke",
            "description": "paid smoke, one task per repo",
            "task_ids": [grouped["attrs"][0], grouped["boltons"][0], grouped["click"][0]],
        },
        {
            "batch_id": 2,
            "output_key": "batch_2_small_pilot_complete",
            "name": "batch_2_small_pilot_complete",
            "description": "complete the 18-task small pilot",
            "task_ids": [*grouped["attrs"][1:6], *grouped["boltons"][1:6], *grouped["click"][1:6]],
        },
        {
            "batch_id": 3,
            "output_key": "batch_3_attrs_remainder",
            "name": "batch_3_attrs_remainder",
            "description": "attrs primary_pilot remainder",
            "task_ids": grouped["attrs"][6:],
        },
        {
            "batch_id": 4,
            "output_key": "batch_4_boltons_remainder",
            "name": "batch_4_boltons_remainder",
            "description": "boltons primary_pilot remainder",
            "task_ids": grouped["boltons"][6:],
        },
        {
            "batch_id": 5,
            "output_key": "batch_5_click_remainder",
            "name": "batch_5_click_remainder",
            "description": "click primary_pilot remainder",
            "task_ids": grouped["click"][6:],
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


def existing_attempted_prefixes(config: dict[str, Any]) -> list[str]:
    prefixes = []
    for prefix in planned_result_prefixes(config):
        if (PHASE0_ROOT / "results" / f"{prefix}_score_table.csv").exists():
            prefixes.append(prefix)
    return prefixes


def write_workspace_matrix_config(config: dict[str, Any]) -> Path:
    lines = [
        "schema_version: barcarolle.workspace_acut_matrix_config.v1",
        "status: configured_for_phase1_three_repo_paid_validation",
        "phase1_three_repo_paid_validation: true",
        f"adapter_config: {rel(adapter_config_path(config))}",
        f"task_table: {rel(source_path(config, 'task_table'))}",
        f"split_plan: {rel(source_path(config, 'split_plan'))}",
        f"fresh_certification_attempts: {rel(source_path(config, 'fresh_certification_attempts'))}",
        f"third_repo_certification_attempts: {rel(source_path(config, 'third_repo_certification_attempts'))}",
        f"task_supply_raw_anchor_inventory: {rel(source_path(config, 'task_supply_raw_anchor_inventory'))}",
        f"third_repo_raw_anchor_inventory: {rel(source_path(config, 'third_repo_raw_anchor_inventory'))}",
        f"attrs_source_repair_statement_packets: {rel(source_path(config, 'attrs_source_repair_statement_packets'))}",
        "task_ids:",
        *[f"  - {task_id}" for task_id in PRIMARY_PILOT_TASK_IDS],
        "",
    ]
    write_text(matrix_config_path(config), "\n".join(lines))
    return matrix_config_path(config)


def rows_from_task_table(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(source_path(config, "task_table"), {})
    return {str(row["candidate_id"]): row for row in payload.get("rows", []) if row.get("candidate_id")}


def split_by_id(config: dict[str, Any]) -> dict[str, str]:
    payload = read_json(source_path(config, "split_plan"), {})
    return {str(row["candidate_id"]): str(row["split"]) for row in payload.get("assignments", []) if row.get("candidate_id")}


def read_score_table(prefix: str) -> list[dict[str, Any]]:
    path = PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["scoreable_cell"] = str(row.get("scoreable_cell", "")).lower() == "true"
        row["repo_id"] = str(row.get("task_id", "")).split("__", 1)[0]
    return rows


def read_phase0_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def score_rows_for_prefixes(prefixes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prefix in prefixes:
        for row in read_score_table(prefix):
            rows.append({**row, "result_prefix": prefix})
    return rows


def cost_summary_for_prefix(prefix: str) -> dict[str, Any]:
    return read_phase0_json(PHASE0_ROOT / "results" / f"{prefix}_cost_summary.json")


def cost_value(summary: dict[str, Any]) -> float:
    for key in ["observed_or_conservative_estimated_cost_usd", "conservative_estimated_cost_usd", "estimated_cost_usd"]:
        if summary.get(key) is not None:
            return float(summary.get(key) or 0.0)
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


def cumulative_summary(config: dict[str, Any], through_batch_id: int | None = None) -> dict[str, Any]:
    prefixes = planned_result_prefixes(config, through_batch_id)
    attempted_prefixes = [prefix for prefix in prefixes if (PHASE0_ROOT / "results" / f"{prefix}_score_table.csv").exists()]
    rows = score_rows_for_prefixes(attempted_prefixes)
    total_cost = round(sum(cost_value(cost_summary_for_prefix(prefix)) for prefix in attempted_prefixes), 8)
    summary = summarize_rows(rows)
    summary.update(
        {
            "attempted_result_prefixes": attempted_prefixes,
            "observed_or_conservative_cost_usd": total_cost,
            "projected_full_run_conservative_cost_usd": float(config["budget"]["conservative_cost_estimate_usd"]),
            "hard_cost_cap_usd": float(config["budget"]["hard_cost_cap_usd"]),
            "projected_total_cost_with_full_conservative_plan_usd": max(total_cost, float(config["budget"]["conservative_cost_estimate_usd"])),
        }
    )
    return summary


def stop_conditions(config: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    stops: list[str] = []
    if summary["cell_count"] and (summary["scoreability_rate"] or 0.0) < float(config["thresholds"]["minimum_scoreability_rate"]):
        stops.append("scoreability_rate_below_0.95_after_batch")
    if int(summary.get("policy_violation_count") or 0) > int(config["thresholds"]["policy_violations_max"]):
        stops.append("policy_violation_count_above_0")
    if float(summary["projected_total_cost_with_full_conservative_plan_usd"]) > float(config["budget"]["hard_cost_cap_usd"]):
        stops.append("projected_total_cost_exceeds_approved_cap")
    if not endpoint_presence()["both_required_endpoint_variables_present"]:
        stops.append("endpoint_proof_missing")
    return stops


def write_process_report(config: dict[str, Any], current_step: str, notes: list[str] | None = None) -> None:
    completed = []
    for key, label in [
        ("preflight", "Step 0 preflight"),
        ("tooling_check", "Step 1 tooling check"),
        ("entry_gate", "Step 2 entry gate"),
        ("batch_plan", "Step 2 batch plan"),
        ("batch_1_smoke", "Step 3 smoke batch"),
        ("batch_2_small_pilot_complete", "Step 4 small pilot batch"),
        ("batch_3_attrs_remainder", "Step 5 attrs batch"),
        ("batch_4_boltons_remainder", "Step 5 boltons batch"),
        ("batch_5_click_remainder", "Step 5 click batch"),
        ("cost_reconciliation", "Step 6 cost reconciliation"),
        ("metrics", "Step 7 metrics"),
        ("decision", "Step 8 decision"),
    ]:
        if output_path(config, key).exists():
            completed.append(label)
    lines = [
        "# Three-Repo Paid Validation Process",
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


def build_preflight(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    dirty_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    diff_check = command_result(["git", "diff", "--check"])
    packaging_gate = read_json(source_path(config, "packaging_entry_gate"), {})
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
        "codex_version": command_stdout(["codex", "--version"]),
        "kilo_version": command_stdout(["kilo", "--version"]),
        "git_status_short_branch": command_stdout(["git", "status", "--short", "--branch"]),
        "git_status_short_untracked": dirty_lines,
        "dirty_path_classification": classify_dirty_paths(config, dirty_lines),
        "git_diff_check": {
            "passed": diff_check["returncode"] == 0,
            "returncode": diff_check["returncode"],
            "stdout_tail_digest": hashlib.sha256(diff_check["stdout"][-4000:].encode("utf-8")).hexdigest()[:12],
            "stderr_tail_digest": hashlib.sha256(diff_check["stderr"][-4000:].encode("utf-8")).hexdigest()[:12],
        },
        "paid_approval": config["approval"],
        "endpoint_presence": endpoint_presence(),
        "packaging_entry_gate_status": packaging_gate.get("status"),
        "packaging_paid_ready": packaging_gate.get("paid_ready"),
        "planned_adapters": adapter_ids(config),
        "planned_cells": int(config["budget"]["planned_cells"]),
        "paid_calls_run_before_preflight": False,
        "existing_paid_result_prefixes": existing_attempted_prefixes(config),
        "stop_before_paid": False,
        "blockers": [],
    }
    if payload["paid_approval"].get("approved_option") != "primary_pilot":
        payload["blockers"].append("paid_approval_absent_or_wrong_option")
    if not payload["endpoint_presence"]["both_required_endpoint_variables_present"]:
        payload["blockers"].append("endpoint_variables_missing")
    if payload["packaging_entry_gate_status"] != "ready_for_paid_validation_runbook":
        payload["blockers"].append("packaging_entry_gate_not_ready")
    if not payload["git_diff_check"]["passed"]:
        payload["blockers"].append("git_diff_check_failed")
    if payload["existing_paid_result_prefixes"]:
        payload["blockers"].append("paid_prefix_outputs_already_exist")
    payload["status"] = "ready_for_tooling_check" if not payload["blockers"] else "blocked_before_paid_calls"
    payload["stop_before_paid"] = bool(payload["blockers"])
    write_json(output_path(config, "preflight"), payload)
    write_preflight_report(config, payload)
    write_process_report(config, current_step="Step 0 preflight complete", notes=["No paid ACUT cells were run in preflight."])
    return payload


def write_preflight_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Preflight",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Approved option: `{payload['paid_approval'].get('approved_option')}`.",
        f"- Approved hard cap: `USD {payload['paid_approval'].get('approved_cost_cap_usd')}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Planned adapters: `{', '.join(payload['planned_adapters'])}`.",
        f"- Endpoint variables present: `{payload['endpoint_presence']['both_required_endpoint_variables_present']}`.",
        f"- Packaging entry gate: `{payload['packaging_entry_gate_status']}`.",
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


def validate_tooling(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    write_workspace_matrix_config(config)
    packages = workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=matrix_config_path(config))
    package_by_id = {package.task_id: package for package in packages}
    split_map = split_by_id(config)
    task_rows = rows_from_task_table(config)
    adapters = workspace_acut.load_adapter_configs(adapter_config_path(config))
    package_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for task_id in PRIMARY_PILOT_TASK_IDS:
        package = package_by_id.get(task_id)
        table_row = task_rows.get(task_id, {})
        target_commit = str(table_row.get("target_commit") or "")
        rendered = workspace_acut.render_statement(package) if package else ""
        row = {
            "task_id": task_id,
            "loaded": package is not None,
            "repo_id": None if package is None else package.repo_id,
            "split": None if package is None else package.split,
            "split_matches_frozen": package is not None and package.split == split_map.get(task_id),
            "source_repo_exists": package is not None and package.source_repo.exists(),
            "base_commit": None if package is None else package.base_commit,
            "target_commit_recorded": bool(target_commit),
            "solver_visible_statement_exists": bool(package and package.solver_facing_statement.strip()),
            "rendered_statement_sha256": None if not rendered else hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
            "target_commit_exposed_in_statement": bool(target_commit and target_commit in rendered),
            "raw_diff_marker_in_statement": "diff --git" in rendered or "\n@@" in rendered,
            "allowed_code_paths": [] if package is None else package.allowed_code_paths,
            "test_paths": [] if package is None else package.test_paths,
            "tests_non_editable": bool(
                package
                and package.test_paths
                and not set(package.allowed_code_paths).intersection(set(package.test_paths))
                and all(workspace_acut.is_test_path(path) for path in package.test_paths)
            ),
            "verifier_command_configured": bool(package and package.verifier_command),
            "paid_acut_calls_made": False,
        }
        package_rows.append(row)
    missing = [row["task_id"] for row in package_rows if not row["loaded"]]
    if missing:
        blockers.append("primary_pilot_task_ids_missing_from_loader")
    if any(not row["split_matches_frozen"] for row in package_rows):
        blockers.append("package_split_mismatch")
    if any(not row["solver_visible_statement_exists"] for row in package_rows):
        blockers.append("solver_visible_statement_missing")
    if any(row["target_commit_exposed_in_statement"] or row["raw_diff_marker_in_statement"] for row in package_rows):
        blockers.append("solver_visible_statement_exposes_hidden_oracle_material")
    if any(not row["tests_non_editable"] for row in package_rows):
        blockers.append("test_paths_not_enforced_as_non_editable")
    if any(not row["verifier_command_configured"] for row in package_rows):
        blockers.append("verifier_command_missing")
    if sorted(adapters) != sorted(adapter_ids(config)):
        blockers.append("configured_adapters_do_not_match_approval")
    if any(set(adapters[adapter].requires_env) != {"LLM_BASE_URL", "LLM_API_KEY"} for adapter in adapters):
        blockers.append("adapter_endpoint_env_requirement_mismatch")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "tooling_check",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "ready" if not blockers else "blocked_before_paid_calls",
        "blockers": blockers,
        "matrix_config": rel(matrix_config_path(config)),
        "selected_task_count": len(packages),
        "expected_task_count": len(PRIMARY_PILOT_TASK_IDS),
        "selected_task_ids": [package.task_id for package in packages],
        "expected_task_ids": PRIMARY_PILOT_TASK_IDS,
        "adapter_ids": sorted(adapters),
        "adapter_endpoint_requirements": {adapter: adapters[adapter].requires_env for adapter in sorted(adapters)},
        "no_paid_dry_inspection_passed": not blockers,
        "paid_acut_calls_made": False,
        "package_rows": package_rows,
    }
    write_json(output_path(config, "tooling_check"), payload)
    write_tooling_report(config, payload)
    write_process_report(config, current_step="Step 1 tooling check complete", notes=["No paid ACUT cells were run in tooling check."])
    return payload


def write_tooling_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Tooling Check",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Matrix config: `{payload['matrix_config']}`.",
        f"- Loaded tasks: `{payload['selected_task_count']}` of `{payload['expected_task_count']}`.",
        f"- Adapters: `{', '.join(payload['adapter_ids'])}`.",
        f"- No-paid dry inspection passed: `{payload['no_paid_dry_inspection_passed']}`.",
        f"- Paid ACUT calls made: `{payload['paid_acut_calls_made']}`.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "tooling_check"), "\n".join(lines))


def build_batch_plan(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    split_map = split_by_id(config)
    task_rows = rows_from_task_table(config)
    matrix_rows: list[dict[str, Any]] = []
    for batch in planned_batches():
        for task_id in batch["task_ids"]:
            row = task_rows[task_id]
            for adapter_id in adapter_ids(config):
                matrix_rows.append(
                    {
                        "batch_id": batch["batch_id"],
                        "batch_name": batch["name"],
                        "task_id": task_id,
                        "repo_id": row["repo_id"],
                        "split": split_map[task_id],
                        "adapter_id": adapter_id,
                        "result_prefix": result_prefix(config, str(batch["name"]), adapter_id),
                    }
                )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "batch_plan",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "frozen",
        "primary_design": config["primary_design"],
        "planned_unique_tasks": len(PRIMARY_PILOT_TASK_IDS),
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
        "paid_outcomes_known_when_generated": False,
    }
    write_json(output_path(config, "batch_plan"), payload)
    write_batch_plan_report(config, payload)
    return payload


def write_batch_plan_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Batch Plan",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Planned unique tasks: `{payload['planned_unique_tasks']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Adapters: `{', '.join(payload['planned_adapters'])}`.",
        f"- Paid outcomes known when generated: `{payload['paid_outcomes_known_when_generated']}`.",
        "",
        "## Batches",
        "",
    ]
    for batch in payload["batches"]:
        lines.append(f"- Batch `{batch['batch_id']}` `{batch['name']}`: `{batch['task_count']}` tasks, `{batch['cell_count']}` cells.")
    write_text(report_path(config, "batch_plan"), "\n".join(lines))


def write_entry_gate(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    preflight = read_json(output_path(config, "preflight"), {})
    tooling = read_json(output_path(config, "tooling_check"), {})
    source_audit = read_json(source_path(config, "source_quality_audit"), {})
    thresholds = read_json(source_path(config, "threshold_preregistration"), {})
    batch_plan = build_batch_plan(config_path)
    dirty_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    raw_staged = [line for line in dirty_lines if line[:2].strip() and classify_dirty_paths(config, [line])["ignored_raw_or_runtime"]]
    blockers: list[str] = []
    if preflight.get("status") != "ready_for_tooling_check":
        blockers.append("preflight_not_ready")
    if tooling.get("status") != "ready":
        blockers.append("tooling_check_not_ready")
    if not endpoint_presence()["both_required_endpoint_variables_present"]:
        blockers.append("endpoint_variables_missing")
    if source_audit.get("tasks_requiring_exclusion_or_repair"):
        blockers.append("source_quality_audit_has_exclusions")
    frozen_thresholds = thresholds.get("thresholds", {})
    if float(frozen_thresholds.get("primary_gap_threshold") or -1) != float(config["thresholds"]["primary_gap_threshold"]):
        blockers.append("primary_gap_threshold_mismatch")
    if int(batch_plan["planned_cells"]) != int(config["budget"]["planned_cells"]):
        blockers.append("planned_cell_count_mismatch")
    if raw_staged:
        blockers.append("raw_runtime_paths_staged")
    if float(config["budget"]["conservative_cost_estimate_usd"]) > float(config["budget"]["hard_cost_cap_usd"]):
        blockers.append("projected_total_cost_exceeds_approved_cap")
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "entry_gate",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "ready_for_paid_batches" if not blockers else "blocked_before_paid_calls",
        "blockers": blockers,
        "approval_present": preflight.get("paid_approval", {}).get("approved_option") == "primary_pilot",
        "endpoint_variables_present": endpoint_presence()["both_required_endpoint_variables_present"],
        "package_integrity_passes": tooling.get("status") == "ready",
        "source_quality_audit_passes": not source_audit.get("tasks_requiring_exclusion_or_repair"),
        "thresholds_frozen": not any(blocker.endswith("threshold_mismatch") for blocker in blockers),
        "cost_cap_recorded_usd": float(config["budget"]["hard_cost_cap_usd"]),
        "planned_cells": int(batch_plan["planned_cells"]),
        "no_raw_logs_workspaces_staged": not raw_staged,
        "paid_acut_calls_made": False,
    }
    write_json(output_path(config, "entry_gate"), payload)
    write_entry_gate_report(config, payload)
    write_process_report(config, current_step="Step 2 entry gate and batch plan complete", notes=["No paid ACUT cells were run in entry gate."])
    return payload


def write_entry_gate_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Entry Gate",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Approval present: `{payload['approval_present']}`.",
        f"- Endpoint variables present: `{payload['endpoint_variables_present']}`.",
        f"- Package integrity passes: `{payload['package_integrity_passes']}`.",
        f"- Source quality audit passes: `{payload['source_quality_audit_passes']}`.",
        f"- Planned cells: `{payload['planned_cells']}`.",
        f"- Cost cap: `USD {payload['cost_cap_recorded_usd']}`.",
        f"- Paid ACUT calls made: `{payload['paid_acut_calls_made']}`.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- `{blocker}`" for blocker in payload["blockers"]] or ["- None."])
    write_text(report_path(config, "entry_gate"), "\n".join(lines))


def import_usage_for_prefixes(config: dict[str, Any], prefixes: list[str]) -> dict[str, Any]:
    if not prefixes:
        return {}
    exp = PHASE0_ROOT
    ledger_path = exp / "results" / "workspace_usage_ledger.jsonl"
    reconciliation_path = exp / "results" / "workspace_cost_reconciliation.json"
    previous_ledger = workspace_usage_import.read_jsonl(ledger_path)
    previous_reconciliation = read_phase0_json(reconciliation_path)
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
    workspace_usage_import.write_report(exp, summaries)
    return current


def write_batch_status(config: dict[str, Any], last_payload: dict[str, Any] | None = None) -> None:
    lines = [
        "# Three-Repo Paid Validation Batch Status",
        "",
    ]
    for batch in planned_batches():
        path = output_path(config, str(batch["output_key"]))
        if not path.exists():
            lines.append(f"- Batch `{batch['batch_id']}` `{batch['name']}`: not run.")
            continue
        payload = read_json(path, {})
        lines.append(
            f"- Batch `{batch['batch_id']}` `{batch['name']}`: `{payload.get('status')}`, cells `{payload.get('batch_summary', {}).get('cell_count')}`, cumulative scoreability `{payload.get('cumulative_summary', {}).get('scoreability_rate')}`, cost `${payload.get('cumulative_summary', {}).get('observed_or_conservative_cost_usd')}`."
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
    previous_stops = []
    if batch_id > 1:
        previous = read_json(output_path(config, batch_for_id(batch_id - 1)["output_key"]), {})
        previous_stops = previous.get("stop_conditions", [])
    if previous_stops:
        raise RuntimeError(f"previous batch stop conditions are set: {previous_stops}")
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
    import_usage_for_prefixes(config, planned_result_prefixes(config, batch_id))
    batch_rows = score_rows_for_prefixes(prefixes)
    batch_summary = summarize_rows(batch_rows)
    cumulative = cumulative_summary(config, batch_id)
    stops = stop_conditions(config, cumulative)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": batch["name"],
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "batch_complete_continue" if not stops else "batch_complete_stop",
        "batch_id": batch_id,
        "batch_name": batch["name"],
        "task_ids": list(batch["task_ids"]),
        "result_prefixes": prefixes,
        "batch_summary": batch_summary,
        "cumulative_summary": cumulative,
        "stop_conditions": stops,
        "continue_decision": "continue_to_next_batch" if not stops and batch_id < 5 else "stop_before_next_batch" if stops else "all_batches_complete",
    }
    write_json(output_path(config, str(batch["output_key"])), payload)
    write_batch_status(config, payload)
    write_process_report(config, current_step=f"Batch {batch_id} complete", notes=[f"Continue decision: {payload['continue_decision']}."])
    return payload


def build_score_tables_manifest(config: dict[str, Any], prefixes: list[str]) -> dict[str, Any]:
    entries = []
    for prefix in prefixes:
        rows = read_score_table(prefix)
        summary = summarize_rows(rows)
        entries.append(
            {
                "result_prefix": prefix,
                "score_table": rel(PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"),
                "matrix": rel(PHASE0_ROOT / "results" / f"{prefix}_matrix.json"),
                "planned_cells": len(rows),
                "completed_cells": len(rows),
                "scoreable_cells": summary["scoreable_cell_count"],
                "non_scoreable_cells": summary["non_scoreable_cell_count"],
                "non_scoreable_by_status": {
                    status: count for status, count in summary["terminal_status_counts"].items() if status in TERMINAL_NON_SCOREABLE
                },
            }
        )
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "score_tables_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "result_prefixes": prefixes,
        "entries": entries,
        "total_completed_cells": sum(entry["completed_cells"] for entry in entries),
        "total_scoreable_cells": sum(entry["scoreable_cells"] for entry in entries),
    }


def reconcile_cost(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    prefixes = existing_attempted_prefixes(config)
    reconciliation = import_usage_for_prefixes(config, prefixes) if prefixes else {}
    totals = reconciliation.get("totals", {}) if reconciliation else {}
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "cost_reconciliation",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if prefixes else "not_run",
        "result_prefixes": prefixes,
        "workspace_cost_reconciliation": rel(PHASE0_ROOT / "results" / "workspace_cost_reconciliation.json") if reconciliation else None,
        "observed_token_estimated_cost_usd": totals.get("observed_token_estimated_cost_usd"),
        "conservative_estimated_cost_usd": totals.get("conservative_estimated_cost_usd"),
        "observed_or_conservative_cost_usd": totals.get("observed_or_conservative_estimated_cost_usd"),
        "usage_observed_rate": totals.get("usage_observed_rate"),
        "actual_provider_billed_cost_usd": None,
        "cost_latency_accounting_complete": bool(prefixes and totals.get("call_count") == sum(len(read_score_table(prefix)) for prefix in prefixes)),
    }
    manifest = build_score_tables_manifest(config, prefixes)
    write_json(output_path(config, "cost_reconciliation"), payload)
    write_json(output_path(config, "score_tables_manifest"), manifest)
    write_cost_report(config, payload)
    write_process_report(config, current_step="Step 6 cost reconciliation complete")
    return payload, manifest


def write_cost_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Cost Reconciliation",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Result prefixes: `{len(payload['result_prefixes'])}`.",
        f"- Observed-token estimated cost: `${payload['observed_token_estimated_cost_usd']}`.",
        f"- Conservative estimated cost: `${payload['conservative_estimated_cost_usd']}`.",
        f"- Observed-or-conservative cost: `${payload['observed_or_conservative_cost_usd']}`.",
        f"- Usage observed rate: `{payload['usage_observed_rate']}`.",
        f"- Cost/latency accounting complete: `{payload['cost_latency_accounting_complete']}`.",
    ]
    write_text(report_path(config, "cost_reconciliation"), "\n".join(lines))


def repo_split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for repo_id in ["attrs", "boltons", "click"]:
        repo_rows = [row for row in rows if row.get("repo_id") == repo_id]
        metrics[repo_id] = {}
        for split in ["B_eval", "H_future"]:
            split_rows = [row for row in repo_rows if row.get("split") == split]
            metrics[repo_id][split] = summarize_rows(split_rows)
        b_rate = metrics[repo_id]["B_eval"]["pass_rate"]
        h_rate = metrics[repo_id]["H_future"]["pass_rate"]
        metrics[repo_id]["absolute_gap"] = None if b_rate is None or h_rate is None else round(abs(b_rate - h_rate), 4)
    return metrics


def compute_metrics(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    prefixes = existing_attempted_prefixes(config)
    rows = score_rows_for_prefixes(prefixes)
    summary = summarize_rows(rows)
    per_repo = repo_split_metrics(rows)
    b_rates = [per_repo[repo]["B_eval"]["pass_rate"] for repo in ["attrs", "boltons", "click"] if per_repo[repo]["B_eval"]["pass_rate"] is not None]
    h_rates = [per_repo[repo]["H_future"]["pass_rate"] for repo in ["attrs", "boltons", "click"] if per_repo[repo]["H_future"]["pass_rate"] is not None]
    pooled_b = None if len(b_rates) != 3 else round(statistics.mean(b_rates), 4)
    pooled_h = None if len(h_rates) != 3 else round(statistics.mean(h_rates), 4)
    primary_gap = None if pooled_b is None or pooled_h is None else round(abs(pooled_b - pooled_h), 4)
    policy_count = int(summary["policy_violation_count"])
    completed = summary["cell_count"] == int(config["budget"]["planned_cells"])
    scoreability_gate = bool(summary["scoreability_rate"] is not None and summary["scoreability_rate"] >= float(config["thresholds"]["minimum_scoreability_rate"]))
    threshold_met = bool(primary_gap is not None and primary_gap <= float(config["thresholds"]["primary_gap_threshold"]))
    cost = read_json(output_path(config, "cost_reconciliation"), {})
    metrics = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "metrics",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if completed else "partial_or_not_run",
        "primary_design": config["primary_design"],
        "planned_cells": int(config["budget"]["planned_cells"]),
        "completed_cells": summary["cell_count"],
        "scoreable_cells": summary["scoreable_cell_count"],
        "scoreability_rate": summary["scoreability_rate"],
        "terminal_status_counts": summary["terminal_status_counts"],
        "policy_violation_count": policy_count,
        "endpoint_compliance_status": "pass" if endpoint_presence()["both_required_endpoint_variables_present"] else "fail",
        "cost_latency_accounting_status": "complete" if cost.get("cost_latency_accounting_complete") else "incomplete",
        "observed_or_conservative_cost_usd": cost.get("observed_or_conservative_cost_usd"),
        "per_repo": per_repo,
        "pooled_unweighted": {
            "B_eval_pass_rate": pooled_b,
            "H_future_pass_rate": pooled_h,
            "primary_absolute_gap": primary_gap,
        },
        "primary_gap_threshold": float(config["thresholds"]["primary_gap_threshold"]),
        "pilot_threshold_met": completed and scoreability_gate and policy_count == 0 and threshold_met,
        "pilot_threshold_not_met": completed and (not scoreability_gate or policy_count > 0 or threshold_met is False),
        "pilot_result_insufficient_precision": completed,
        "predictive_validity_established": False,
    }
    baseline_plan = read_json(source_path(config, "baseline_plan"), {})
    baseline_comparison = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_comparison",
        "run_id": config["run_id"],
        "generated_at": metrics["generated_at"],
        "status": "recorded",
        "primary_design": config["primary_design"],
        "frozen_baselines": baseline_plan.get("baselines", []),
        "old_weighted_design": {
            "role": "diagnostic_only",
            "promoted_to_primary_after_outcomes": False,
            "score_tables_merged_into_primary": False,
        },
        "baseline_result_note": "This runbook records frozen baseline roles and evaluates the preregistered primary design only.",
    }
    write_json(output_path(config, "metrics"), metrics)
    write_json(output_path(config, "baseline_comparison"), baseline_comparison)
    write_metrics_report(config, metrics)
    write_baseline_report(config, baseline_comparison)
    write_process_report(config, current_step="Step 7 metrics complete")
    return metrics, baseline_comparison


def write_metrics_report(config: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Metrics",
        "",
        f"Status: `{metrics['status']}`.",
        "",
        f"- Completed cells: `{metrics['completed_cells']}` of `{metrics['planned_cells']}`.",
        f"- Scoreable cells: `{metrics['scoreable_cells']}`.",
        f"- Scoreability rate: `{metrics['scoreability_rate']}`.",
        f"- Policy violations: `{metrics['policy_violation_count']}`.",
        f"- Primary pooled absolute gap: `{metrics['pooled_unweighted']['primary_absolute_gap']}`.",
        f"- Threshold <= 0.15: `{metrics['pilot_threshold_met']}`.",
        f"- Predictive validity established: `{metrics['predictive_validity_established']}`.",
        "",
        "## Per Repo",
        "",
    ]
    for repo_id, row in metrics["per_repo"].items():
        lines.append(
            f"- `{repo_id}`: B_eval `{row['B_eval']['pass_rate']}`, H_future `{row['H_future']['pass_rate']}`, abs gap `{row['absolute_gap']}`."
        )
    write_text(report_path(config, "metrics"), "\n".join(lines))


def write_baseline_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Baseline Comparison",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Primary design: `{payload['primary_design']}`.",
        "- Old weighted design role: `diagnostic_only`.",
        "- Old weighted design promoted after outcomes: `false`.",
        "",
        "## Frozen Baselines",
        "",
    ]
    for row in payload["frozen_baselines"]:
        lines.append(f"- `{row.get('design_id')}`: `{row.get('role')}`.")
    write_text(report_path(config, "baseline_comparison"), "\n".join(lines))


def write_decision(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    metrics = read_json(output_path(config, "metrics"), {})
    cost = read_json(output_path(config, "cost_reconciliation"), {})
    completed = metrics.get("completed_cells") == metrics.get("planned_cells") and metrics.get("planned_cells") is not None
    paid_ran = bool(metrics.get("completed_cells"))
    if not paid_ran:
        label = "three_repo_paid_validation_blocked_before_paid_calls"
    elif not completed:
        label = "three_repo_paid_validation_blocked_after_partial_run"
    elif metrics.get("pilot_threshold_met"):
        label = "three_repo_paid_pilot_threshold_met"
    elif metrics.get("pilot_threshold_not_met"):
        label = "three_repo_paid_pilot_threshold_not_met"
    else:
        label = "three_repo_paid_pilot_insufficient_precision"
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": label,
        "predictive_validity_established": False,
        "old_weighted_design_diagnostic_only": True,
        "followup_runbook_written_by_worker": False,
        "raw_oracle_exposure_detected": False,
        "rq_answers": {
            "RQ1_all_planned_primary_pilot_cells_complete": completed,
            "RQ2_scoreability_rate": metrics.get("scoreability_rate"),
            "RQ3_gates_clean": {
                "endpoint": metrics.get("endpoint_compliance_status"),
                "policy_violation_count": metrics.get("policy_violation_count"),
                "raw_oracle_exposure": False,
                "cost_accounting": metrics.get("cost_latency_accounting_status"),
            },
            "RQ4_primary_gaps": {
                "per_repo": {repo: row.get("absolute_gap") for repo, row in (metrics.get("per_repo") or {}).items()},
                "pooled": (metrics.get("pooled_unweighted") or {}).get("primary_absolute_gap"),
            },
            "RQ5_preregistered_pilot_threshold_passed": metrics.get("pilot_threshold_met"),
            "RQ6_baselines_and_diagnostics": "Frozen baselines recorded; old weighted design remains diagnostic only.",
            "RQ7_cost": cost.get("observed_or_conservative_cost_usd"),
            "RQ8_validity_status": "pilot evidence only" if completed else "blocked",
        },
        "completed_steps": [
            key
            for key in config["outputs"]
            if output_path(config, key).exists()
        ],
        "tests_run": [],
        "known_blockers": [] if completed else ["paid validation did not complete all planned cells"],
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload, metrics, cost)
    write_process_report(config, current_step="Step 8 decision complete")
    return payload


def write_decision_report(config: dict[str, Any], payload: dict[str, Any], metrics: dict[str, Any], cost: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Validation Decision",
        "",
        f"Decision label: `{payload['decision_label']}`.",
        "",
        "What happened: the frozen attrs/boltons/click primary_pilot paid validation was evaluated up to the recorded terminal state.",
        "Why it matters: this records pilot evidence and gates without changing the preregistered primary design after outcomes.",
        f"Next paid batch should continue or stop: `{'stop' if payload['decision_label'].endswith('partial_run') or 'blocked' in payload['decision_label'] else 'complete'}`.",
        "",
        f"- Planned cells: `{metrics.get('planned_cells')}`.",
        f"- Completed cells: `{metrics.get('completed_cells')}`.",
        f"- Scoreable cells: `{metrics.get('scoreable_cells')}`.",
        f"- Scoreability rate: `{metrics.get('scoreability_rate')}`.",
        f"- Policy violations: `{metrics.get('policy_violation_count')}`.",
        "- Raw oracle exposure: `false`.",
        f"- Endpoint compliance: `{metrics.get('endpoint_compliance_status')}`.",
        f"- Cost: `${cost.get('observed_or_conservative_cost_usd')}` observed/conservative.",
        "- Primary design: `repo_stratified`.",
        f"- Primary gap: `{(metrics.get('pooled_unweighted') or {}).get('primary_absolute_gap')}`.",
        f"- Threshold <= 0.15: `{metrics.get('pilot_threshold_met')}`.",
        "",
        "Predictive validity: not established. This run can only support pilot evidence or a blocker.",
        "Old weighted design: diagnostic only; not promoted to primary.",
        "No raw logs, raw prompts, raw completions, solver workspaces, verifier workspaces, or secrets are committed by this report.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the Phase 1 three-repo paid validation runbook.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("preflight")
    subcommands.add_parser("tooling-check")
    subcommands.add_parser("entry-gate")
    subcommands.add_parser("batch-plan")
    run_batch_parser = subcommands.add_parser("run-batch")
    run_batch_parser.add_argument("--batch-id", type=int, required=True)
    subcommands.add_parser("cost-reconciliation")
    subcommands.add_parser("metrics")
    subcommands.add_parser("decision")
    args = parser.parse_args()
    config_path = Path(args.config)
    if args.command == "preflight":
        build_preflight(config_path)
    elif args.command == "tooling-check":
        validate_tooling(config_path)
    elif args.command == "entry-gate":
        write_entry_gate(config_path)
    elif args.command == "batch-plan":
        build_batch_plan(config_path)
    elif args.command == "run-batch":
        run_batch(args.batch_id, config_path)
    elif args.command == "cost-reconciliation":
        reconcile_cost(config_path)
    elif args.command == "metrics":
        compute_metrics(config_path)
    elif args.command == "decision":
        write_decision(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
