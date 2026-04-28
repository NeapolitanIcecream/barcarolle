#!/usr/bin/env python3
"""Apply a submitted patch and emit a normalized run-result JSON object."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _common import (
    ToolError,
    emit_json,
    fail,
    git,
    iso_now,
    load_manifest,
    require_keys,
    require_mapping,
    run_to_artifacts,
    slug,
    split_command,
)


TOOL = "apply_and_verify"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a candidate patch to a prepared workspace, run the task verifier, "
            "and write a normalized run result."
        )
    )
    parser.add_argument("--workspace", required=True, help="Prepared git workspace.")
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--patch", required=True, help="Patch file produced by run_task.py.")
    parser.add_argument("--acut-id", required=True, help="ACUT id for the normalized result.")
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number, starting at 1.")
    parser.add_argument("--run-id", help="Stable run id. Defaults to acut/task/attempt/timestamp.")
    parser.add_argument("--artifact-dir", help="Directory for verifier stdout/stderr artifacts.")
    parser.add_argument("--output", help="Optional path for the normalized JSON result.")
    parser.add_argument("--timeout-seconds", type=int, help="Override verifier timeout.")
    parser.add_argument("--verifier-command", help="Override verifier.command from the task manifest.")
    parser.add_argument("--verifier-root", help="Directory for resolving relative verifier commands.")
    parser.add_argument("--skip-apply", action="store_true", help="Run verifier without applying the patch.")
    return parser.parse_args()


def resolve_verifier_command(command: str, verifier_root: Path) -> list[str]:
    parts = split_command(command)
    executable = Path(parts[0])
    if not executable.is_absolute():
        candidate = verifier_root / executable
        if candidate.exists():
            parts[0] = str(candidate.resolve())
    return parts


def apply_patch(workspace: Path, patch_path: Path) -> str | None:
    if not patch_path.exists():
        return "patch file does not exist"
    if patch_path.stat().st_size == 0:
        return "patch file is empty"

    check = git("apply", "--check", str(patch_path), cwd=workspace)
    if check.returncode != 0:
        return check.stderr.strip() or "git apply --check failed"

    applied = git("apply", str(patch_path), cwd=workspace)
    if applied.returncode != 0:
        return applied.stderr.strip() or "git apply failed"
    return None


def default_review() -> dict[str, object]:
    return {
        "mergeability_grade": None,
        "wrong_module": False,
        "rule_violation": False,
        "notes": "",
    }


def main() -> int:
    args = parse_args()
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")

        workspace = Path(args.workspace)
        patch_path = Path(args.patch).resolve()
        task_path = Path(args.task)
        task = load_manifest(task_path)
        require_keys(task, ["task_id", "split", "verifier"], "task manifest")
        verifier = require_mapping(task.get("verifier"), "task.verifier")
        require_keys(verifier, ["command", "timeout_seconds"], "task.verifier")

        task_id = str(task["task_id"])
        timestamp = iso_now().replace(":", "").replace("-", "")
        run_id = args.run_id or f"{slug(args.acut_id)}__{slug(task_id)}__attempt{args.attempt}__{timestamp}"
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else Path("experiments/core_narrative/results/raw") / run_id
        stdout_path = artifact_dir / "verifier.stdout.txt"
        stderr_path = artifact_dir / "verifier.stderr.txt"
        verifier_root = Path(args.verifier_root) if args.verifier_root else task_path.parent
        verifier_command = args.verifier_command or str(verifier["command"])
        timeout = args.timeout_seconds if args.timeout_seconds is not None else int(verifier["timeout_seconds"])

        started_at = iso_now()
        apply_error = None if args.skip_apply else apply_patch(workspace, patch_path)
        if apply_error is not None:
            finished_at = iso_now()
            payload = {
                "schema_version": "core-narrative.run-result.v1",
                "run_id": run_id,
                "acut_id": args.acut_id,
                "task_id": task_id,
                "split": task["split"],
                "attempt": args.attempt,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": "invalid_submission",
                "patch_path": str(patch_path),
                "verification": {
                    "exit_code": None,
                    "stdout_artifact": None,
                    "stderr_artifact": None,
                    "duration_seconds": 0,
                },
                "review": default_review(),
                "error": apply_error,
                "metadata": {"tool": TOOL},
            }
            emit_json(payload, args.output)
            return 0

        command = resolve_verifier_command(verifier_command, verifier_root)
        run = run_to_artifacts(
            command,
            cwd=workspace,
            timeout_seconds=timeout,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            env={**os.environ.copy(), "CORE_NARRATIVE_TASK_DIR": str(task_path.parent.resolve())},
        )
        finished_at = iso_now()

        if run["timed_out"]:
            status = "timeout"
        elif run["exit_code"] == 0:
            status = "passed"
        else:
            status = "failed"

        payload = {
            "schema_version": "core-narrative.run-result.v1",
            "run_id": run_id,
            "acut_id": args.acut_id,
            "task_id": task_id,
            "split": task["split"],
            "attempt": args.attempt,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "patch_path": str(patch_path),
            "verification": {
                "exit_code": run["exit_code"],
                "stdout_artifact": str(stdout_path),
                "stderr_artifact": str(stderr_path),
                "duration_seconds": run["duration_seconds"],
            },
            "review": default_review(),
            "error": None,
            "metadata": {
                "tool": TOOL,
                "verifier_command": command,
                "timeout_seconds": timeout,
                "skip_apply": args.skip_apply,
            },
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
