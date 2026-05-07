#!/usr/bin/env python3
"""Run a compact Codex-owned Barcarolle core-narrative experiment slice."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json
from _llm_budget import DEFAULT_LEDGER_PATH, redact_sensitive_text


TOOL = "codex_nfl_experiment_runner"
RUNNER_ID = "codex-nfl-batch-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_SPLIT = REPO_ROOT / "experiments/core_narrative/configs/tasks/rbench_click.yaml"
TASK_PACK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces"
RAW_ROOT = REPO_ROOT / "experiments/core_narrative/results/raw"
NORMALIZED_ROOT = REPO_ROOT / "experiments/core_narrative/results/normalized"
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
DIRECT_RUNNER = REPO_ROOT / "experiments/core_narrative/tools/codex_nfl_direct_runner.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_RUN_PREFIX = "codex_nfl_20260508"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--acuts", nargs="+", required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--mode", choices=("live", "mock", "dry-run"), default="live")
    parser.add_argument("--mock-response")
    parser.add_argument("--mock-response-text")
    parser.add_argument("--llm-ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--output", required=True)
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--runner-timeout-seconds", type=int, default=360)
    parser.add_argument("--skip-noop-check", action="store_true")
    return parser.parse_args(list(argv))


def run_capture(command: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def write_command_artifacts(
    *,
    completed: subprocess.CompletedProcess[str],
    artifact_dir: Path,
    name: str,
    command: Sequence[str],
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    stdout_path = artifact_dir / f"{name}.stdout.txt"
    stderr_path = artifact_dir / f"{name}.stderr.txt"
    stdout_path.write_text(redact_sensitive_text(completed.stdout, os.environ), encoding="utf-8")
    stderr_path.write_text(redact_sensitive_text(completed.stderr, os.environ), encoding="utf-8")
    summary = {
        "name": name,
        "command": [redact_sensitive_text(part, os.environ) for part in command],
        "exit_code": completed.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }
    write_json(artifact_dir / f"{name}.json", summary)
    return summary


def task_by_id(split_manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = split_manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ToolError("task split manifest has no tasks list")
    result: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if isinstance(task, dict) and isinstance(task.get("task_id"), str):
            result[str(task["task_id"])] = task
    return result


def task_manifest_path(task_id: str) -> Path:
    path = TASK_PACK_ROOT / "click" / "rbench" / task_id / "task.yaml"
    if not path.exists():
        raise ToolError(
            "materialized task pack does not exist; run materialize_task_pack.py first",
            task_id=task_id,
            path=str(path),
        )
    return path


def acut_manifest_path(acut_id: str) -> Path:
    path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
    if not path.exists():
        raise ToolError("ACUT manifest does not exist", acut_id=acut_id, path=str(path))
    return path


def projected_cost_for_acut(acut_id: str) -> str:
    return "3" if acut_id.startswith("frontier-") else "1"


def context_paths_for_task(task: Mapping[str, Any], workspace: Path) -> list[str]:
    compare = task.get("source_compare") if isinstance(task.get("source_compare"), dict) else {}
    paths = compare.get("changed_files") if isinstance(compare.get("changed_files"), list) else []
    valid: list[str] = []
    for item in paths:
        if not isinstance(item, str):
            continue
        candidate = workspace / item
        if candidate.exists() and candidate.is_file():
            valid.append(item)
    if valid:
        return valid
    expected = task.get("expected_touched_area") if isinstance(task.get("expected_touched_area"), list) else []
    for item in expected:
        if not isinstance(item, str):
            continue
        for word in item.replace(",", " ").split():
            if "/" not in word:
                continue
            clean = word.strip("`'\".;:()")
            if (workspace / clean).exists():
                valid.append(clean)
    return sorted(set(valid))


def prepare_workspace(task_id: str, run_id: str, artifact_dir: Path) -> tuple[Path, dict[str, Any]]:
    workspace = WORKSPACES_ROOT / run_id
    command = [
        sys.executable,
        str(PREPARE),
        "--task",
        str(task_manifest_path(task_id)),
        "--source-repo",
        str(SOURCE_REPO),
        "--workspace",
        str(workspace),
        "--force",
        "--output",
        str(artifact_dir / "prepare_workspace.json"),
    ]
    completed = run_capture(command, timeout=120)
    if completed.returncode != 0:
        raise ToolError("workspace preparation failed", stderr=redact_sensitive_text(completed.stderr, os.environ))
    return workspace, json.loads((artifact_dir / "prepare_workspace.json").read_text(encoding="utf-8"))


def install_workspace(workspace: Path, artifact_dir: Path, timeout_seconds: int) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "venv",
        ".venv",
    ]
    started_at = iso_now()
    completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="venv_create",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace venv creation failed", summary=summary)

    install = [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"]
    started_at = iso_now()
    completed = run_capture(install, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="venv_install",
        command=install,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace dependency install failed", summary=summary)
    return summary


def no_op_verify(
    *,
    workspace: Path,
    task_id: str,
    acut_id: str,
    attempt: int,
    run_id: str,
    artifact_dir: Path,
) -> dict[str, Any]:
    output = artifact_dir / "noop_verify.json"
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_manifest_path(task_id)),
        "--patch",
        str(artifact_dir / "missing_noop.patch"),
        "--acut-id",
        acut_id,
        "--attempt",
        str(attempt),
        "--run-id",
        run_id + "__noop",
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(output),
        "--skip-apply",
    ]
    started_at = iso_now()
    completed = run_capture(command, timeout=90)
    finished_at = iso_now()
    summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="noop_verify_command",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    result = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"status": "infra_failed"}
    return {"command": summary, "result": result}


def run_direct_runner(
    *,
    args: argparse.Namespace,
    task: Mapping[str, Any],
    task_id: str,
    acut_id: str,
    workspace: Path,
    run_id: str,
    artifact_dir: Path,
    context_paths: Sequence[str],
) -> tuple[int, dict[str, Any]]:
    output = artifact_dir / "runner_result.json"
    command = [
        sys.executable,
        str(DIRECT_RUNNER),
        "--workspace",
        str(workspace),
        "--task",
        str(task_manifest_path(task_id)),
        "--acut",
        str(acut_manifest_path(acut_id)),
        "--attempt",
        str(args.attempt),
        "--run-id",
        run_id,
        "--artifact-dir",
        str(artifact_dir),
        "--patch-path",
        str(artifact_dir / "submission.patch"),
        "--output",
        str(output),
        "--llm-ledger",
        str(args.llm_ledger),
        "--projected-cost-usd",
        projected_cost_for_acut(acut_id),
        "--estimated-cost-usd",
        projected_cost_for_acut(acut_id),
        "--http-timeout-seconds",
        str(args.runner_timeout_seconds),
    ]
    for path in context_paths:
        command.extend(["--context-path", path])
    if args.mode == "dry-run":
        command.append("--dry-run")
    elif args.mode == "mock":
        if args.mock_response:
            command.extend(["--mock-response", args.mock_response])
        else:
            command.extend(["--mock-response-text", args.mock_response_text or '{"edits": []}'])

    started_at = iso_now()
    completed = run_capture(command, timeout=args.runner_timeout_seconds + 30)
    finished_at = iso_now()
    write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="direct_runner_command",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    result = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {
        "status": "error",
        "error": redact_sensitive_text(completed.stderr, os.environ),
    }
    result["selected_context_paths"] = list(context_paths)
    result["task_visible_context_guidance"] = task.get("visible_context_guidance")
    return completed.returncode, result


def write_infra_failed_result(
    *,
    run_id: str,
    task_id: str,
    split: str,
    acut_id: str,
    attempt: int,
    normalized_path: Path,
    patch_path: Path,
    runner_result: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "core-narrative.run-result.v1",
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "started_at": runner_result.get("started_at"),
        "finished_at": runner_result.get("finished_at"),
        "status": "infra_failed",
        "patch_path": str(patch_path),
        "verification": {
            "exit_code": None,
            "stdout_artifact": None,
            "stderr_artifact": None,
            "duration_seconds": None,
        },
        "review": {
            "mergeability_grade": None,
            "wrong_module": False,
            "rule_violation": False,
            "notes": "",
        },
        "error": runner_result.get("error") or "direct runner did not produce a verifier-ready patch",
        "metadata": {
            "tool": TOOL,
            "runner_id": RUNNER_ID,
            "direct_runner_id": runner_result.get("runner_id"),
            "direct_runner_status": runner_result.get("status"),
            "model_call_made": runner_result.get("model_call_made"),
            "failure_class": (runner_result.get("details") or {}).get("failure_class")
            if isinstance(runner_result.get("details"), dict)
            else None,
            "verifier_ready_patch_available": False,
            "raw_response_artifact": runner_result.get("raw_response_artifact"),
            "prompt_snapshot": runner_result.get("prompt_snapshot"),
        },
    }
    write_json(normalized_path, payload)
    return payload


def verify_patch(
    *,
    workspace: Path,
    task_id: str,
    acut_id: str,
    attempt: int,
    run_id: str,
    artifact_dir: Path,
    normalized_path: Path,
) -> tuple[int, dict[str, Any]]:
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_manifest_path(task_id)),
        "--patch",
        str(artifact_dir / "submission.patch"),
        "--acut-id",
        acut_id,
        "--attempt",
        str(attempt),
        "--run-id",
        run_id,
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(normalized_path),
        "--skip-apply",
    ]
    started_at = iso_now()
    completed = run_capture(command, timeout=120)
    finished_at = iso_now()
    write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="verify_command",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    result = json.loads(normalized_path.read_text(encoding="utf-8")) if normalized_path.exists() else {
        "status": "infra_failed",
        "error": redact_sensitive_text(completed.stderr, os.environ),
    }
    return completed.returncode, result


def run_one(args: argparse.Namespace, task: Mapping[str, Any], acut_id: str) -> dict[str, Any]:
    task_id = str(task["task_id"])
    run_id = f"{args.run_prefix}__{acut_id}__{task_id}__attempt{args.attempt}"
    artifact_dir = RAW_ROOT / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    normalized_path = NORMALIZED_ROOT / f"{run_id}.json"

    started = time.monotonic()
    workspace, prepare_summary = prepare_workspace(task_id, run_id, artifact_dir)
    install_summary = install_workspace(workspace, artifact_dir, args.install_timeout_seconds)
    context_paths = context_paths_for_task(task, workspace)
    noop_summary = None
    if not args.skip_noop_check:
        noop_summary = no_op_verify(
            workspace=workspace,
            task_id=task_id,
            acut_id=acut_id,
            attempt=args.attempt,
            run_id=run_id,
            artifact_dir=artifact_dir,
        )
    runner_code, runner_result = run_direct_runner(
        args=args,
        task=task,
        task_id=task_id,
        acut_id=acut_id,
        workspace=workspace,
        run_id=run_id,
        artifact_dir=artifact_dir,
        context_paths=context_paths,
    )
    patch_path = artifact_dir / "submission.patch"
    patch_ready = runner_code == 0 and patch_path.exists() and patch_path.stat().st_size > 0
    if patch_ready:
        verify_code, normalized = verify_patch(
            workspace=workspace,
            task_id=task_id,
            acut_id=acut_id,
            attempt=args.attempt,
            run_id=run_id,
            artifact_dir=artifact_dir,
            normalized_path=normalized_path,
        )
    else:
        verify_code = None
        normalized = write_infra_failed_result(
            run_id=run_id,
            task_id=task_id,
            split=str(task["split"]),
            acut_id=acut_id,
            attempt=args.attempt,
            normalized_path=normalized_path,
            patch_path=patch_path,
            runner_result=runner_result,
        )

    result = {
        "run_id": run_id,
        "task_id": task_id,
        "acut_id": acut_id,
        "status": normalized.get("status"),
        "scoreable": normalized.get("status") in {"passed", "failed", "timeout"},
        "patch_ready": patch_ready,
        "runner_status": runner_result.get("status"),
        "runner_code": runner_code,
        "verify_code": verify_code,
        "artifact_dir": str(artifact_dir),
        "workspace": str(workspace),
        "normalized_result": str(normalized_path),
        "patch_path": str(patch_path),
        "prompt_snapshot": runner_result.get("prompt_snapshot"),
        "raw_response_artifact": runner_result.get("raw_response_artifact"),
        "context_paths": context_paths,
        "duration_seconds": round(time.monotonic() - started, 3),
        "prepare": prepare_summary,
        "install": install_summary,
        "noop": noop_summary,
        "runner_result": runner_result,
        "normalized": normalized,
    }
    write_json(artifact_dir / "batch_run_result.json", result)
    return result


def aggregate(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    by_acut: dict[str, dict[str, int]] = {}
    by_task: dict[str, dict[str, int]] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
        acut = str(result.get("acut_id"))
        task = str(result.get("task_id"))
        by_acut.setdefault(acut, {})[status] = by_acut.setdefault(acut, {}).get(status, 0) + 1
        by_task.setdefault(task, {})[status] = by_task.setdefault(task, {}).get(status, 0) + 1
    return {
        "total": len(results),
        "scoreable": sum(1 for result in results if result.get("scoreable")),
        "passed": counts.get("passed", 0),
        "failed": counts.get("failed", 0),
        "infra_failed": counts.get("infra_failed", 0),
        "timeout": counts.get("timeout", 0),
        "status_counts": counts,
        "by_acut": by_acut,
        "by_task": by_task,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        split_manifest = load_manifest(TASK_SPLIT)
        tasks = task_by_id(split_manifest)
        selected_tasks = []
        for task_id in args.tasks:
            if task_id not in tasks:
                raise ToolError("requested task is not in RBench Click manifest", task_id=task_id)
            selected_tasks.append(tasks[task_id])
        results: list[dict[str, Any]] = []
        for task in selected_tasks:
            for acut_id in args.acuts:
                results.append(run_one(args, task, acut_id))
        payload = {
            "tool": TOOL,
            "runner_id": RUNNER_ID,
            "status": "completed",
            "mode": args.mode,
            "run_prefix": args.run_prefix,
            "tasks": args.tasks,
            "acuts": args.acuts,
            "attempt": args.attempt,
            "started_at": results[0]["runner_result"].get("started_at") if results else None,
            "finished_at": iso_now(),
            "aggregate": aggregate(results),
            "results": results,
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
