#!/usr/bin/env python3
"""Run and summarize repository-local-rich-w20-v1 primary attempts."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json
from _llm_budget import redact_sensitive_text
from rgw_status_semantics import WORKSPACE_MODE_STATUSES, classify_status


TOOL = "repository_local_rich_w20_primary_runner"
RUNNER_ID = "repository-local-rich-w20-v1"
SCHEMA_VERSION = "core-narrative.repository-local-rich-w20-result.v1"
SUMMARY_SCHEMA_VERSION = "core-narrative.repository-local-rich-w20-summary.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_READINESS = REPO_ROOT / "experiments/core_narrative/results/repository_local_rich_w20_protocol_readiness_20260515.json"
DEFAULT_START_DECISION = REPO_ROOT / "experiments/core_narrative/results/repository_local_rich_w20_start_decision_20260515.json"
DEFAULT_PREFLIGHT = REPO_ROOT / "experiments/core_narrative/results/repository_local_rich_w20_live_preflight_20260515.json"
DEFAULT_ROUTE_PROBE = REPO_ROOT / "experiments/core_narrative/results/repository_local_rich_w20_route_probe_20260515.json"
DEFAULT_PUBLIC_ROOT = REPO_ROOT / "experiments/core_narrative/results/repository_local_rich_w20_v1"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/repository_local_rich_w20_v1"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/repository_local_rich_w20_v1"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/rich"
WORKSPACE_MODE_RUNNER = REPO_ROOT / "experiments/core_narrative/tools/workspace_mode_runner.py"
CODEX_CLI_PATCH_COMMAND = REPO_ROOT / "experiments/core_narrative/tools/codex_cli_patch_command.py"
ACUT_TIMEOUT_SECONDS = 3600
VERIFIER_TIMEOUT_SECONDS = 120


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", default=str(DEFAULT_READINESS))
    parser.add_argument("--start-decision", default=str(DEFAULT_START_DECISION))
    parser.add_argument("--preflight", default=str(DEFAULT_PREFLIGHT))
    parser.add_argument("--route-probe", default=str(DEFAULT_ROUTE_PROBE))
    parser.add_argument("--public-root", default=str(DEFAULT_PUBLIC_ROOT))
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--phase", choices=("primary", "summary"), default="summary")
    parser.add_argument("--mode", choices=("live", "dry-run"), default="live")
    parser.add_argument("--run-prefix", default="repository_local_rich_w20_v1_20260515")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--acut-timeout-seconds", type=int, default=ACUT_TIMEOUT_SECONDS)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=VERIFIER_TIMEOUT_SECONDS)
    parser.add_argument("--install-workspaces", action="store_true", default=True)
    parser.add_argument("--no-install-workspaces", dest="install_workspaces", action="store_false")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, help="Optional first-N cell limit for smoke runs.")
    parser.add_argument("--output")
    return parser.parse_args(list(argv) if argv is not None else None)


def resolve_repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return os.path.relpath(path.resolve(), REPO_ROOT.resolve())


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_start_gates(
    readiness: Mapping[str, Any],
    start_decision: Mapping[str, Any],
    preflight: Mapping[str, Any],
    route_probe: Mapping[str, Any],
    mode: str,
) -> None:
    if readiness.get("protocol_id") != RUNNER_ID:
        raise ToolError("readiness artifact is for the wrong protocol", observed=readiness.get("protocol_id"))
    if mode == "live" and start_decision.get("decision") != "authorize_primary_attempts_after_live_preflight":
        raise ToolError("start decision does not authorize primary attempts", decision=start_decision.get("decision"))
    if mode == "live" and preflight.get("status") != "passed":
        raise ToolError("live preflight must pass before primary attempts", preflight_status=preflight.get("status"))
    if mode == "live" and route_probe.get("status") != "passed":
        raise ToolError("live route probe must pass before primary attempts", route_probe_status=route_probe.get("status"))
    checks = readiness.get("pre_primary_checks") if isinstance(readiness.get("pre_primary_checks"), Mapping) else {}
    if checks.get("all_primary_checks_pass") is not True:
        raise ToolError("readiness pre-primary checks are not all passing", checks=checks)
    workers = readiness.get("runner_concurrency_requirement") if isinstance(readiness.get("runner_concurrency_requirement"), Mapping) else {}
    if int(workers.get("implemented_default_max_workers") or 0) < 4:
        raise ToolError("readiness does not prove 4-way runner support", runner_concurrency_requirement=workers)


def acut_rows(readiness: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = readiness.get("acuts")
    if not isinstance(rows, list) or not rows:
        raise ToolError("readiness artifact has no ACUT rows")
    result = [row for row in rows if isinstance(row, Mapping)]
    if len(result) != 4:
        raise ToolError("Rich-W20 primary expects four ACUT rows", observed=len(result))
    return result


def task_rows(readiness: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    denominators = readiness.get("denominators") if isinstance(readiness.get("denominators"), Mapping) else {}
    w = denominators.get("W_star") if isinstance(denominators.get("W_star"), Mapping) else {}
    r = denominators.get("R") if isinstance(denominators.get("R"), Mapping) else {}
    w_tasks = w.get("primary_tasks") if isinstance(w.get("primary_tasks"), list) else []
    r_tasks = r.get("primary_tasks") if isinstance(r.get("primary_tasks"), list) else []
    tasks = [task for task in [*w_tasks, *r_tasks] if isinstance(task, Mapping)]
    if len(tasks) != 40:
        raise ToolError("Rich-W20 primary expects 40 primary tasks", observed=len(tasks))
    return tasks


def iter_cells(readiness: Mapping[str, Any]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    return [(task, acut) for task in task_rows(readiness) for acut in acut_rows(readiness)]


def run_id_for(prefix: str, mode: str, task: Mapping[str, Any], acut: Mapping[str, Any], attempt: int) -> str:
    split = str(task["split"])
    protocol_task_id = str(task["protocol_task_id"])
    acut_slot = str(acut["slot"])
    acut_id = str(acut["acut_id"])
    return f"{prefix}__{slug(mode)}__{slug(split)}__{slug(protocol_task_id)}__{slug(acut_slot)}__{slug(acut_id)}__attempt{attempt}"


def normalized_path(public_root: Path, run_id: str) -> Path:
    return public_root / "normalized" / f"{run_id}.json"


def artifact_dir(private_root: Path, run_id: str) -> Path:
    return private_root / "raw" / run_id


def command_summary(
    *,
    command: Sequence[str],
    cwd: Path,
    timeout_seconds: int | None,
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    started_at = iso_now()
    started = time.monotonic()
    timed_out = False
    exit_code: int | None = None
    command_error: str | None = None
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout_path.write_text(redact_sensitive_text(completed.stdout, os.environ), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(completed.stderr, os.environ), encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout_path.write_text(redact_sensitive_text(exc.stdout or "", os.environ), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(exc.stderr or "", os.environ), encoding="utf-8")
    except FileNotFoundError as exc:
        command_error = str(exc)
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(command_error, os.environ), encoding="utf-8")
    return {
        "command": [redact_sensitive_text(str(part), os.environ) for part in command],
        "cwd": str(cwd),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "command_error": command_error,
        "started_at": started_at,
        "finished_at": iso_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_artifact": repo_relative(stdout_path),
        "stderr_artifact": repo_relative(stderr_path),
    }


def workspace_mode_command(
    *,
    task: Mapping[str, Any],
    acut: Mapping[str, Any],
    args: argparse.Namespace,
    run_id: str,
    artifact_dir_path: Path,
) -> list[str]:
    acut_manifest = resolve_repo_path(str(acut["manifest"]))
    task_pack_path = resolve_repo_path(str(task["task_pack_path"]))
    command = [
        sys.executable,
        str(WORKSPACE_MODE_RUNNER),
        "--task",
        str(task_pack_path),
        "--source-repo",
        str(SOURCE_REPO),
        "--acut",
        str(acut_manifest),
        "--attempt",
        str(args.attempt),
        "--run-id",
        run_id,
        "--workspace-root",
        str(Path(args.workspace_root)),
        "--artifact-dir",
        str(artifact_dir_path),
        "--output",
        str(artifact_dir_path / "workspace_mode_output.json"),
        "--acut-timeout-seconds",
        str(args.acut_timeout_seconds),
        "--verifier-timeout-seconds",
        str(args.verifier_timeout_seconds),
    ]
    if args.install_workspaces:
        command.append("--install-workspaces")
    command.append("--")
    command.extend(
        [
            sys.executable,
            str(CODEX_CLI_PATCH_COMMAND),
            "--workspace",
            ".",
            "--acut",
            str(acut_manifest),
            "--artifact-dir",
            str(artifact_dir_path / "codex_cli_patch_command"),
            "--summary-output",
            str(artifact_dir_path / "codex_cli_patch_command.json"),
            "--codex-timeout-seconds",
            str(args.acut_timeout_seconds),
        ]
    )
    if args.mode == "dry-run":
        command.append("--dry-run")
    return command


def read_acut_summary(artifact_dir_path: Path) -> dict[str, Any] | None:
    return load_json(artifact_dir_path / "codex_cli_patch_command.json")


def llm_backend_unavailable(acut_summary: Mapping[str, Any] | None) -> bool:
    if not isinstance(acut_summary, Mapping):
        return False
    if acut_summary.get("model_call_made") is not True:
        return False
    status = acut_summary.get("status")
    if status in {"codex_exec_failed", "timeout"}:
        return True
    failure_capture = acut_summary.get("failure_capture")
    if isinstance(failure_capture, Mapping) and failure_capture.get("failure_class") in {"nonzero_exit", "timeout"}:
        return True
    return False


def public_llm_backend_summary(acut_summary: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(acut_summary, Mapping):
        return {
            "checked": False,
            "status": None,
            "model_call_made": False,
        }
    codex_exec = acut_summary.get("codex_exec")
    failure_capture = acut_summary.get("failure_capture")
    return {
        "checked": True,
        "status": acut_summary.get("status"),
        "model_call_made": acut_summary.get("model_call_made") is True,
        "model": acut_summary.get("model"),
        "codex_exec_exit_code": codex_exec.get("exit_code") if isinstance(codex_exec, Mapping) else None,
        "codex_exec_timed_out": codex_exec.get("timed_out") if isinstance(codex_exec, Mapping) else None,
        "failure_class": failure_capture.get("failure_class") if isinstance(failure_capture, Mapping) else None,
        "failure_text_recorded": False,
    }


def normalize_workspace_payload(
    *,
    payload: Mapping[str, Any],
    task: Mapping[str, Any],
    acut: Mapping[str, Any],
    run_id: str,
    command: Mapping[str, Any],
    artifact_dir_path: Path,
    normalized_result_path: Path,
) -> dict[str, Any]:
    acut_summary = read_acut_summary(artifact_dir_path)
    workspace_mode_status = str(payload.get("status"))
    status = "llm_backend_unavailable" if llm_backend_unavailable(acut_summary) else workspace_mode_status
    classification = classify_status(status, payload)
    model_call_made = acut_summary.get("model_call_made") is True if isinstance(acut_summary, Mapping) else False
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    verification = payload.get("verification") if isinstance(payload.get("verification"), Mapping) else {}
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "run_id": run_id,
        "mode": command.get("mode"),
        "split": task.get("split"),
        "protocol_task_id": task.get("protocol_task_id"),
        "task_id": payload.get("task_id"),
        "task_pack_path": task.get("task_pack_path"),
        "source_artifact": task.get("source_artifact"),
        "acut_slot": acut.get("slot"),
        "acut_role": acut.get("role"),
        "acut_id": acut.get("acut_id"),
        "acut_manifest": acut.get("manifest"),
        "model": acut.get("model"),
        "attempt": payload.get("attempt"),
        "status": status,
        "workspace_mode_status": workspace_mode_status,
        "recognized_workspace_mode_status": workspace_mode_status in WORKSPACE_MODE_STATUSES,
        "primary_pass": classification["primary_pass"],
        "score_action": classification["score_action"],
        "score_value": classification["score_value"],
        "requires_rerun_or_exclusion": classification["requires_rerun_or_exclusion"],
        "triage_paused": classification["triage_paused"],
        "timeout_owner": classification["timeout_owner"],
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "candidate_patch": {
            "sha256": candidate.get("sha256"),
            "size_bytes": candidate.get("size_bytes"),
            "has_scoreable_diff": candidate.get("has_scoreable_diff"),
            "unsafe_content_detected": candidate.get("unsafe_content_detected"),
        },
        "verification": {
            "attempted": verification.get("attempted"),
            "base_tree_matches_run": verification.get("base_tree_matches_run"),
            "verifier_exit_code": verification.get("verifier_exit_code"),
        },
        "artifact_paths": {
            "private_artifact_dir": repo_relative(artifact_dir_path),
            "workspace_mode_output": repo_relative(artifact_dir_path / "workspace_mode_output.json"),
            "workspace_mode_result": repo_relative(artifact_dir_path / "workspace_mode_result.json"),
            "workspace_runner_command": repo_relative(artifact_dir_path / "workspace_runner_command.json"),
            "normalized_result": repo_relative(normalized_result_path),
        },
        "command": {
            "workspace_runner": command.get("command"),
            "exit_code": command.get("exit_code"),
            "timed_out": command.get("timed_out"),
            "command_error": command.get("command_error"),
        },
        "cost_metadata": {
            "model_call_made": model_call_made,
            "estimated_cost_usd": 1.0 if model_call_made else 0.0,
            "actual_cost_usd": None,
            "cost_source": "estimated_cheap_route_default; codex_cli_patch_command records exact usage when available in private summary",
            "acut_summary_artifact": repo_relative(artifact_dir_path / "codex_cli_patch_command.json")
            if (artifact_dir_path / "codex_cli_patch_command.json").exists()
            else None,
        },
        "error": payload.get("error"),
        "metadata": {
            "workspace_mode_schema_version": payload.get("schema_version"),
            "workspace_mode_tool": payload.get("tool"),
            "status_semantics": classification,
            "llm_backend": public_llm_backend_summary(acut_summary),
            "model_call_made": model_call_made,
            "commit_values_recorded": False,
            "subject_text_values_recorded": False,
        },
    }
    write_json(normalized_result_path, normalized)
    return normalized


def run_cell(
    *,
    task: Mapping[str, Any],
    acut: Mapping[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    public_root = Path(args.public_root)
    private_root = Path(args.private_root)
    run_id = run_id_for(args.run_prefix, args.mode, task, acut, args.attempt)
    artifact_dir_path = artifact_dir(private_root, run_id)
    normalized_result_path = normalized_path(public_root, run_id)
    if normalized_result_path.exists() and not args.force:
        existing = load_json(normalized_result_path)
        if existing is not None:
            return existing
    if artifact_dir_path.exists() and any(artifact_dir_path.iterdir()) and not args.force:
        raise ToolError("private artifacts exist but public normalized result is missing", run_id=run_id, artifact_dir=repo_relative(artifact_dir_path))
    if args.force and artifact_dir_path.exists():
        import shutil

        shutil.rmtree(artifact_dir_path)
    if args.force and normalized_result_path.exists():
        normalized_result_path.unlink()

    artifact_dir_path.mkdir(parents=True, exist_ok=True)
    normalized_result_path.parent.mkdir(parents=True, exist_ok=True)
    command = workspace_mode_command(task=task, acut=acut, args=args, run_id=run_id, artifact_dir_path=artifact_dir_path)
    summary = command_summary(
        command=command,
        cwd=REPO_ROOT,
        timeout_seconds=args.acut_timeout_seconds + args.verifier_timeout_seconds + 900,
        stdout_path=artifact_dir_path / "workspace_runner_command.stdout.txt",
        stderr_path=artifact_dir_path / "workspace_runner_command.stderr.txt",
    )
    summary["mode"] = args.mode
    write_json(artifact_dir_path / "workspace_runner_command.json", summary)
    payload = load_json(artifact_dir_path / "workspace_mode_output.json") or load_json(artifact_dir_path / "workspace_mode_result.json")
    if payload is None:
        timed_out = bool(summary["timed_out"] or summary["exit_code"] == 124)
        payload = {
            "run_id": run_id,
            "acut_id": acut.get("acut_id"),
            "task_id": task.get("protocol_task_id"),
            "split": task.get("split"),
            "attempt": args.attempt,
            "status": "timeout" if timed_out else "verifier_infra_error",
            "metadata": {"timeout_owner": "verifier" if timed_out else None},
            "candidate_patch": {},
            "verification": {"attempted": False},
            "started_at": summary["started_at"],
            "finished_at": summary["finished_at"],
            "duration_seconds": summary["duration_seconds"],
            "error": summary["command_error"] or "workspace_mode_runner did not emit output",
        }
    return normalize_workspace_payload(
        payload=payload,
        task=task,
        acut=acut,
        run_id=run_id,
        command=summary,
        artifact_dir_path=artifact_dir_path,
        normalized_result_path=normalized_result_path,
    )


def run_cells(cells: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]], args: argparse.Namespace) -> list[dict[str, Any]]:
    ordered_cells = list(cells)
    if args.limit is not None:
        ordered_cells = ordered_cells[: args.limit]
    if args.max_workers == 1 or len(ordered_cells) <= 1:
        return [run_cell(task=task, acut=acut, args=args) for task, acut in ordered_cells]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = [pool.submit(run_cell, task=task, acut=acut, args=args) for task, acut in ordered_cells]
        return [future.result() for future in futures]


def normalized_files(public_root: Path) -> list[Path]:
    root = public_root / "normalized"
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def load_normalized_results(public_root: Path) -> list[dict[str, Any]]:
    records = []
    for path in normalized_files(public_root):
        payload = load_json(path)
        if isinstance(payload, dict) and payload.get("runner_id") == RUNNER_ID:
            records.append(payload)
    return records


def summarize_axis(records: Sequence[Mapping[str, Any]], split: str, tasks: Sequence[Mapping[str, Any]], acuts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = {(str(task["protocol_task_id"]), str(acut["acut_id"])) for task in tasks if task.get("split") == split for acut in acuts}
    by_cell = {(str(record.get("protocol_task_id")), str(record.get("acut_id"))): record for record in records if record.get("split") == split}
    cells = []
    for task_id, acut_id in sorted(expected):
        record = by_cell.get((task_id, acut_id))
        cells.append(
            {
                "protocol_task_id": task_id,
                "acut_id": acut_id,
                "present": record is not None,
                "status": record.get("status") if record else "missing",
                "score_action": record.get("score_action") if record else "missing_primary_attempt",
                "score_value": record.get("score_value") if record else None,
                "normalized_result": record.get("artifact_paths", {}).get("normalized_result") if record else None,
            }
        )
    present = [cell for cell in cells if cell["present"]]
    scored = [cell for cell in present if isinstance(cell["score_value"], int)]
    passed = sum(1 for cell in scored if cell["score_value"] == 1)
    infra = [cell for cell in present if cell["score_action"] == "rerun_or_global_exclusion_required"]
    triage = [cell for cell in present if cell["score_action"] == "triage_paused_before_primary_scoring"]
    return {
        "split": split,
        "expected_cells": len(expected),
        "present_cells": len(present),
        "missing_cells": len(expected) - len(present),
        "passed": passed,
        "score_percent_fixed_denominator": 100.0 * passed / len(expected) if expected else None,
        "primary_score_ready": len(present) == len(expected) and not infra and not triage,
        "infra_cells": infra,
        "triage_paused_cells": triage,
        "cells": cells,
    }


def by_acut_table(records: Sequence[Mapping[str, Any]], tasks: Sequence[Mapping[str, Any]], acuts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for acut in acuts:
        acut_id = str(acut["acut_id"])
        row: dict[str, Any] = {"acut_id": acut_id, "slot": acut.get("slot"), "role": acut.get("role")}
        for split, prefix in (("R", "r"), ("W_star", "w_star")):
            expected_tasks = [task for task in tasks if task.get("split") == split]
            axis_records = [
                record
                for record in records
                if record.get("split") == split and record.get("acut_id") == acut_id
            ]
            scored = [record for record in axis_records if isinstance(record.get("score_value"), int)]
            passed = sum(1 for record in scored if record.get("score_value") == 1)
            infra = [record for record in axis_records if record.get("requires_rerun_or_exclusion") is True]
            triage = [record for record in axis_records if record.get("triage_paused") is True]
            denominator = len(expected_tasks)
            row[f"{prefix}_passed"] = passed
            row[f"{prefix}_fixed_denominator"] = denominator
            row[f"{prefix}_score_percent_fixed"] = 100.0 * passed / denominator if denominator else None
            row[f"{prefix}_primary_score_ready"] = len(axis_records) == denominator and not infra and not triage
        table[acut_id] = row
    return table


def build_summary(readiness: Mapping[str, Any], public_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    tasks = task_rows(readiness)
    acuts = acut_rows(readiness)
    records = load_normalized_results(public_root)
    axes = {
        "R": summarize_axis(records, "R", tasks, acuts),
        "W_star": summarize_axis(records, "W_star", tasks, acuts),
    }
    table = by_acut_table(records, tasks, acuts)
    status = "primary_complete" if all(axis["primary_score_ready"] for axis in axes.values()) else "primary_incomplete_or_infra_blocked"
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "generated_at": iso_now(),
        "status": status,
        "mode": args.mode,
        "expected_primary_attempts": len(tasks) * len(acuts),
        "normalized_result_count": len(records),
        "concurrency": {
            "max_workers": args.max_workers,
            "executor": "ThreadPoolExecutor",
            "result_order": "readiness_task_order_then_acut_order",
        },
        "axes": axes,
        "rw_table": table,
        "artifacts": {
            "summary": repo_relative(public_root / "summary.json"),
            "rw_table": repo_relative(public_root / "rw_table.json"),
            "normalized_dir": repo_relative(public_root / "normalized"),
        },
    }
    write_json(public_root / "summary.json", summary)
    write_json(public_root / "rw_table.json", table)
    return summary


def reproduction_command(args: argparse.Namespace) -> str:
    parts = [
        "PYTHONPATH=experiments/core_narrative/tools",
        "python3",
        "experiments/core_narrative/tools/repository_local_rich_w20_primary_runner.py",
        "--phase",
        str(args.phase),
        "--mode",
        str(args.mode),
        "--max-workers",
        str(args.max_workers),
    ]
    return " ".join(shlex.quote(part) for part in parts)


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    args.readiness = str(resolve_repo_path(args.readiness))
    args.start_decision = str(resolve_repo_path(args.start_decision))
    args.preflight = str(resolve_repo_path(args.preflight))
    args.route_probe = str(resolve_repo_path(args.route_probe))
    args.public_root = str(resolve_repo_path(args.public_root))
    args.private_root = str(resolve_repo_path(args.private_root))
    args.workspace_root = str(resolve_repo_path(args.workspace_root))
    if args.output:
        args.output = str(resolve_repo_path(args.output))
    return args


def execute(args: argparse.Namespace) -> dict[str, Any]:
    args = normalize_args(args)
    readiness = load_manifest(args.readiness)
    start_decision = load_manifest(args.start_decision)
    preflight = load_manifest(args.preflight)
    route_probe = load_manifest(args.route_probe)
    if args.phase == "primary":
        validate_start_gates(readiness, start_decision, preflight, route_probe, args.mode)
    public_root = Path(args.public_root)
    public_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    if args.phase == "primary":
        results = run_cells(iter_cells(readiness), args)
    summary = build_summary(readiness, public_root, args)
    payload = {
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": "completed",
        "phase": args.phase,
        "mode": args.mode,
        "generated_at": iso_now(),
        "results_written": len(results),
        "summary_status": summary["status"],
        "summary": repo_relative(public_root / "summary.json"),
        "reproduction_command": reproduction_command(args),
    }
    write_json(public_root / "runner_execution_diagnostics.json", payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.attempt != 1:
            raise ToolError("repository-local-rich-w20-v1 freezes primary attempts at 1", attempt=args.attempt)
        if args.max_workers < 1:
            raise ToolError("--max-workers must be at least 1", max_workers=args.max_workers)
        payload = execute(args)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
