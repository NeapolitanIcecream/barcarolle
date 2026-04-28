#!/usr/bin/env python3
"""Run an ACUT command in a prepared workspace and capture its patch."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from _common import (
    ToolError,
    command_from_args,
    emit_json,
    fail,
    git,
    iso_now,
    load_manifest,
    require_keys,
    slug,
)
from _llm_budget import (
    DEFAULT_LEDGER_PATH,
    assert_safe_command_arguments,
    ensure_no_required_env_values,
    gate_exit_code,
    gate_payload,
    llm_safe_subprocess_env,
    parse_usd,
    redact_command_arguments,
    run_to_redacted_artifacts,
)


TOOL = "run_task"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute an agent or harness command in a prepared workspace, save "
            "stdout/stderr artifacts, and write a git patch for verification."
        )
    )
    parser.add_argument("--workspace", required=True, help="Prepared git workspace.")
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--acut", help="ACUT manifest JSON/YAML path.")
    parser.add_argument("--acut-id", help="ACUT id override when --acut is not supplied.")
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number, starting at 1.")
    parser.add_argument("--run-id", help="Stable run id. Defaults to acut/task/attempt/timestamp.")
    parser.add_argument("--artifact-dir", help="Directory for stdout, stderr, and patch artifacts.")
    parser.add_argument("--patch-path", help="Patch output path. Defaults under --artifact-dir.")
    parser.add_argument("--output", help="Optional path for the structured JSON summary.")
    parser.add_argument("--timeout-seconds", type=int, help="Timeout for the ACUT command.")
    parser.add_argument(
        "--llm-ledger",
        default=str(DEFAULT_LEDGER_PATH),
        help="Cost ledger JSONL path that must exist and be writable before ACUT execution.",
    )
    parser.add_argument(
        "--projected-cost-usd",
        help="Conservative projected cost for this ACUT patch-generation attempt.",
    )
    parser.add_argument(
        "--coordinator-decision-ref",
        help="Reference to an explicit coordinator approval for soft-stop, rerun, or non-core ACUT execution.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --.")
    return parser.parse_args()


def resolve_acut_id(args: argparse.Namespace) -> str:
    if args.acut:
        acut = load_manifest(args.acut)
        require_keys(acut, ["acut_id"], "ACUT manifest")
        return str(acut["acut_id"])
    if args.acut_id:
        return args.acut_id
    raise ToolError("either --acut or --acut-id is required")


def write_patch(workspace: Path, patch_path: Path) -> None:
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with patch_path.open("w", encoding="utf-8") as patch_file:
            completed = subprocess.run(
                ["git", "diff", "--binary", "--no-ext-diff"],
                cwd=str(workspace),
                stdout=patch_file,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
    except FileNotFoundError as exc:
        raise ToolError("git executable was not found") from exc
    if completed.returncode != 0:
        raise ToolError("failed to write patch", stderr=completed.stderr.strip())


def main() -> int:
    args = parse_args()
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")

        workspace = Path(args.workspace)
        result = git("rev-parse", "--is-inside-work-tree", cwd=workspace)
        if result.returncode != 0 or result.stdout.strip() != "true":
            raise ToolError("workspace is not a git work tree", workspace=str(workspace))

        task = load_manifest(args.task)
        require_keys(task, ["task_id", "split"], "task manifest")
        task_id = str(task["task_id"])
        acut_id = resolve_acut_id(args)
        timestamp = iso_now().replace(":", "").replace("-", "")
        run_id = args.run_id or f"{slug(acut_id)}__{slug(task_id)}__attempt{args.attempt}__{timestamp}"
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else Path("experiments/core_narrative/results/raw") / run_id
        stdout_path = artifact_dir / "agent.stdout.txt"
        stderr_path = artifact_dir / "agent.stderr.txt"
        patch_path = Path(args.patch_path) if args.patch_path else artifact_dir / "submission.patch"
        command = command_from_args(args.command)
        assert_safe_command_arguments(command, os.environ)
        ensure_no_required_env_values(command, os.environ)
        redacted_command = redact_command_arguments(command, os.environ)
        projected_cost_usd = parse_usd(args.projected_cost_usd, "--projected-cost-usd")
        budget_gate = gate_payload(
            ledger_path=Path(args.llm_ledger),
            projected_cost_usd=projected_cost_usd,
            coordinator_decision_ref=args.coordinator_decision_ref,
            acut_id=acut_id,
            split=str(task["split"]),
            attempt=args.attempt,
            env=os.environ,
        )
        if budget_gate["status"] != "passed":
            raise ToolError(
                "LLM budget gate blocked ACUT execution",
                exit_code=gate_exit_code(budget_gate),
                gate=budget_gate,
            )
        acut_env, scrubbed_env_var_count = llm_safe_subprocess_env(os.environ)

        started_at = iso_now()
        run = run_to_redacted_artifacts(
            command,
            cwd=workspace,
            timeout_seconds=args.timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            env=acut_env,
        )
        finished_at = iso_now()
        write_patch(workspace, patch_path)

        if run["timed_out"]:
            status = "timeout"
        elif run["exit_code"] == 0:
            status = "command_completed"
        else:
            status = "command_failed"

        payload = {
            "tool": TOOL,
            "status": status,
            "run_id": run_id,
            "acut_id": acut_id,
            "task_id": task_id,
            "split": task["split"],
            "attempt": args.attempt,
            "started_at": started_at,
            "finished_at": finished_at,
            "workspace": str(workspace),
            "command": redacted_command,
            "llm_budget_gate": budget_gate,
            "credential_env_policy": {
                "allowed_llm_env_vars": ["BARCAROLLE_LLM_API_KEY", "BARCAROLLE_LLM_BASE_URL"],
                "scrubbed_secret_like_env_var_count": scrubbed_env_var_count,
                "captured_artifacts_redacted": True,
                "command_arguments_checked": True,
                "unsafe_command_arguments_rejected": True,
                "command_representation_redacted": True,
            },
            "agent": {
                "exit_code": run["exit_code"],
                "duration_seconds": run["duration_seconds"],
                "stdout_artifact": str(stdout_path),
                "stderr_artifact": str(stderr_path),
            },
            "patch_path": str(patch_path),
        }
        emit_json(payload, args.output)
        return 0 if not run["timed_out"] else 124
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
