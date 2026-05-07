#!/usr/bin/env python3
"""Budget-gated ACUT patch-generation adapter with mandatory ledger records."""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    write_json,
)
from _llm_budget import (
    DEFAULT_LEDGER_PATH,
    append_ledger_record,
    assert_safe_command_arguments,
    ensure_no_required_env_values,
    gate_exit_code,
    gate_payload,
    ledger_cumulative_decimal,
    llm_safe_subprocess_env,
    money_json,
    parse_non_negative_int,
    parse_usd,
    read_ledger_summary,
    redact_command_arguments,
    run_to_redacted_artifacts,
)
from run_task import restore_tracked_workspace_changes, write_safe_patch


TOOL = "acut_patch_adapter"
ADAPTER_ID = "codex-cli-acut-adapter-v0"
NO_MODEL_COMMAND = ["<dry-run:no-model-patch-generation>"]
INNER_PATCH_COMMAND_TOOL = "codex_cli_patch_command"
DIRECT_PATCH_COMMAND_TOOL = "barcarolle_patch_command"
DEFAULT_NONZERO_FAILURE_CLASS = "nonzero_exit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one ACUT patch-generation attempt through the experiment LLM "
            "budget gate, then append a cost-ledger record. Credential values "
            "and full endpoint URLs are never accepted as CLI arguments."
        )
    )
    parser.add_argument("--workspace", help="Prepared git workspace. Required unless the gate blocks or --dry-run is used.")
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--acut", help="ACUT manifest JSON/YAML path.")
    parser.add_argument("--acut-id", help="ACUT id override when --acut is not supplied.")
    parser.add_argument("--attempt", type=int, default=1, help="Attempt number, starting at 1.")
    parser.add_argument("--run-id", help="Stable run id. Defaults to acut/task/attempt/timestamp.")
    parser.add_argument("--artifact-dir", help="Directory for adapter stdout/stderr and patch artifacts.")
    parser.add_argument("--patch-path", help="Patch output path. Defaults under --artifact-dir.")
    parser.add_argument("--output", help="Optional path for the structured adapter summary.")
    parser.add_argument("--normalized-output", help="Optional normalized smoke result JSON path.")
    parser.add_argument(
        "--llm-ledger",
        default=str(DEFAULT_LEDGER_PATH),
        help="Cost ledger JSONL path that must exist and be writable before command execution.",
    )
    parser.add_argument(
        "--projected-cost-usd",
        required=True,
        help="Conservative projected USD cost for this patch-generation attempt.",
    )
    parser.add_argument("--actual-cost-usd", help="Actual provider-billed USD cost, when available.")
    parser.add_argument("--input-tokens", default="0", help="Input tokens recorded for the attempt, when available.")
    parser.add_argument("--output-tokens", default="0", help="Output tokens recorded for the attempt, when available.")
    parser.add_argument(
        "--coordinator-decision-ref",
        help="Reference to an explicit coordinator approval for soft-stop, rerun, or non-core ACUT execution.",
    )
    parser.add_argument("--timeout-seconds", type=int, help="Timeout for the patch-generation command.")
    parser.add_argument("--dry-run", action="store_true", help="Exercise gate, ledger, and artifact paths without a model call.")
    parser.add_argument(
        "--command-no-model",
        action="store_true",
        help=(
            "Run the command path as a no-model smoke. Requires zero projected, "
            "input, and output cost fields and records model_call_made=false."
        ),
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Patch-generation command to run after --.")
    return parser.parse_args()


def resolve_acut_id(args: argparse.Namespace) -> str:
    if args.acut:
        acut = load_manifest(args.acut)
        require_keys(acut, ["acut_id"], "ACUT manifest")
        return str(acut["acut_id"])
    if args.acut_id:
        return args.acut_id
    raise ToolError("either --acut or --acut-id is required")


def resolve_command(args: argparse.Namespace) -> list[str]:
    if args.command:
        return command_from_args(args.command)
    if args.dry_run:
        return list(NO_MODEL_COMMAND)
    raise ToolError("command is required after -- unless --dry-run is used")


def require_workspace(path: str | None) -> Path:
    if not path:
        raise ToolError("--workspace is required when executing a patch-generation command")
    workspace = Path(path)
    result = git("rev-parse", "--is-inside-work-tree", cwd=workspace)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ToolError("workspace is not a git work tree", workspace=str(workspace))
    return workspace


def append_attempt_record(
    *,
    ledger_path: Path,
    run_id: str,
    acut_id: str,
    task_id: str,
    split: str,
    attempt: int,
    event: str,
    started_at: str,
    finished_at: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: Decimal,
    actual_cost: Decimal | None,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    before = read_ledger_summary(ledger_path)
    previous_cumulative = ledger_cumulative_decimal(before)
    cumulative = previous_cumulative + estimated_cost
    record: dict[str, Any] = {
        "record_type": "acut_patch_generation_attempt",
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "event": event,
        "started_at": started_at,
        "finished_at": finished_at,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": money_json(estimated_cost),
        "actual_cost_usd": None if actual_cost is None else money_json(actual_cost),
        "cumulative_estimated_cost_usd": money_json(cumulative),
        "metadata": dict(metadata),
    }
    append_ledger_record(ledger_path, record)
    after = read_ledger_summary(ledger_path)
    return {
        "status": "appended",
        "path": str(ledger_path),
        "event": event,
        "record_count_before": before["record_count"],
        "record_count_after": after["record_count"],
        "estimated_cost_usd": money_json(estimated_cost),
        "actual_cost_recorded": actual_cost is not None,
        "previous_cumulative_estimated_cost_usd": money_json(previous_cumulative),
        "new_cumulative_estimated_cost_usd": money_json(cumulative),
    }


def ledger_append_error(exc: BaseException) -> dict[str, Any]:
    details = getattr(exc, "details", {})
    return {
        "status": "failed",
        "error": str(exc),
        "details": details if isinstance(details, dict) else {},
    }


def write_static_artifacts(
    *,
    stdout_path: Path,
    stderr_path: Path,
    patch_path: Path,
    stdout_text: str,
    stderr_text: str = "",
    write_empty_patch: bool = False,
) -> None:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    if write_empty_patch:
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text("", encoding="utf-8")


def default_review() -> dict[str, object]:
    return {
        "mergeability_grade": None,
        "wrong_module": False,
        "rule_violation": False,
        "notes": "",
    }


def write_normalized_result(
    *,
    path: str | None,
    run_id: str,
    acut_id: str,
    task_id: str,
    split: str,
    attempt: int,
    started_at: str,
    finished_at: str,
    status: str,
    patch_path: Path,
    stdout_path: Path | None,
    stderr_path: Path | None,
    duration_seconds: float,
    error: str | None,
    metadata: Mapping[str, Any],
) -> None:
    if path is None:
        return
    payload = {
        "schema_version": "core-narrative.run-result.v1",
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "patch_path": str(patch_path),
        "verification": {
            "exit_code": None,
            "stdout_artifact": None if stdout_path is None else str(stdout_path),
            "stderr_artifact": None if stderr_path is None else str(stderr_path),
            "duration_seconds": duration_seconds,
        },
        "review": default_review(),
        "error": error,
        "metadata": dict(metadata),
    }
    write_json(path, payload)


def command_option_value(command: Sequence[str], option: str) -> str | None:
    for index, value in enumerate(command[:-1]):
        if value == option:
            return command[index + 1]
    return None


def sanitized_transport_failure(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict) or value.get("present") is not True:
        return None
    allowed_keys = {
        "present",
        "failure_class",
        "wire_api",
        "endpoint_path",
        "after_reconnects",
        "reconnect_limit",
        "retry_exhausted",
        "matched_stdout",
        "matched_stderr",
        "messages_recorded",
        "content_recorded",
        "redaction_applied_before_detection",
    }
    sanitized: dict[str, Any] = {}
    for key in allowed_keys:
        item = value.get(key)
        if isinstance(item, (bool, int)) or item is None:
            sanitized[key] = item
        elif isinstance(item, str) and "://" not in item:
            if key == "endpoint_path" and not item.startswith("/"):
                continue
            sanitized[key] = item
    return sanitized


def read_inner_patch_command_summary(command: Sequence[str]) -> dict[str, Any]:
    summary_arg = command_option_value(command, "--summary-output")
    metadata: dict[str, Any] = {
        "summary_output_arg_present": summary_arg is not None,
        "summary_read": False,
        "summary_path": summary_arg,
    }
    if summary_arg is None:
        return metadata

    try:
        data = json.loads(Path(summary_arg).read_text(encoding="utf-8"))
    except OSError as exc:
        metadata["summary_read_error_type"] = type(exc).__name__
        return metadata
    except json.JSONDecodeError:
        metadata["summary_read_error_type"] = "JSONDecodeError"
        return metadata

    if not isinstance(data, dict):
        metadata["summary_read_error_type"] = "unexpected_json_shape"
        return metadata

    tool = data.get("tool")
    metadata.update(
        {
            "summary_read": True,
            "tool": tool,
            "inner_status": data.get("status"),
        }
    )
    if tool == DIRECT_PATCH_COMMAND_TOOL:
        failure_class = data.get("failure_class")
        details = data.get("details") if isinstance(data.get("details"), dict) else {}
        metadata.update(
            {
                "failure_class": failure_class if isinstance(failure_class, str) else None,
                "model_call_made": bool(data.get("model_call_made")),
                "model_response_received": bool(details.get("model_response_received")),
                "output_contract": data.get("output_contract") if isinstance(data.get("output_contract"), str) else None,
            }
        )
        return metadata

    if tool != INNER_PATCH_COMMAND_TOOL:
        return metadata

    failure_capture = data.get("failure_capture")
    if not isinstance(failure_capture, dict):
        failure_capture = {}
    failure_class = failure_capture.get("failure_class")
    transport_failure = sanitized_transport_failure(data.get("transport_failure"))
    if transport_failure is None:
        transport_failure = sanitized_transport_failure(failure_capture.get("transport_failure"))

    metadata.update(
        {
            "failure_class": failure_class if isinstance(failure_class, str) else None,
            "cli_log_inspected": bool(failure_capture.get("cli_log_inspected")),
        }
    )
    if transport_failure is not None:
        metadata["transport_failure"] = transport_failure
    return metadata


def effective_nonzero_failure_class(inner_summary: Mapping[str, Any]) -> str:
    failure_class = inner_summary.get("failure_class")
    if isinstance(failure_class, str) and failure_class:
        return failure_class
    return DEFAULT_NONZERO_FAILURE_CLASS


def base_payload(
    *,
    status: str,
    run_id: str,
    acut_id: str,
    task_id: str,
    split: str,
    attempt: int,
    started_at: str,
    finished_at: str,
    artifact_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    patch_path: Path,
    command: Sequence[str],
    budget_gate: Mapping[str, Any],
    ledger_append: Mapping[str, Any],
    dry_run: bool,
    command_duration_seconds: float,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tool": TOOL,
        "adapter_id": ADAPTER_ID,
        "status": status,
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "started_at": started_at,
        "finished_at": finished_at,
        "artifact_dir": str(artifact_dir),
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
        "patch_path": str(patch_path),
        "command": redact_command_arguments(command, os.environ),
        "command_duration_seconds": command_duration_seconds,
        "dry_run": dry_run,
        "model_call_made": False if dry_run or budget_gate["status"] != "passed" else None,
        "llm_budget_gate": budget_gate,
        "cost_ledger_append": ledger_append,
        "llm_env_policy": {
            "allowed_variable_names": ["BARCAROLLE_LLM_API_KEY", "BARCAROLLE_LLM_BASE_URL"],
            "values_recorded": False,
            "command_arguments_checked": True,
            "unsafe_command_arguments_rejected": True,
            "command_representation_redacted": True,
            "captured_artifacts_redacted": True,
        },
    }
    if extra:
        payload.update(extra)
    return payload


def main() -> int:
    args = parse_args()
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        if args.timeout_seconds is not None and args.timeout_seconds < 1:
            raise ToolError("--timeout-seconds must be at least 1")

        task = load_manifest(args.task)
        require_keys(task, ["task_id", "split"], "task manifest")
        task_id = str(task["task_id"])
        split = str(task["split"])
        acut_id = resolve_acut_id(args)
        command = resolve_command(args)
        if command != NO_MODEL_COMMAND:
            assert_safe_command_arguments(command, os.environ)
            ensure_no_required_env_values(command, os.environ)

        projected_cost = parse_usd(args.projected_cost_usd, "--projected-cost-usd")
        actual_cost = parse_usd(args.actual_cost_usd, "--actual-cost-usd") if args.actual_cost_usd is not None else None
        input_tokens = parse_non_negative_int(args.input_tokens, "--input-tokens")
        output_tokens = parse_non_negative_int(args.output_tokens, "--output-tokens")
        if args.command_no_model and args.dry_run:
            raise ToolError("--command-no-model is only meaningful when a command is executed")
        if args.command_no_model:
            if projected_cost != Decimal("0"):
                raise ToolError("--command-no-model requires --projected-cost-usd 0")
            if actual_cost not in (None, Decimal("0")):
                raise ToolError("--command-no-model requires --actual-cost-usd 0 when provided")
            if input_tokens != 0 or output_tokens != 0:
                raise ToolError("--command-no-model requires zero input and output tokens")

        timestamp = iso_now().replace(":", "").replace("-", "")
        run_id = args.run_id or f"{slug(acut_id)}__{slug(task_id)}__attempt{args.attempt}__{timestamp}"
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else Path("experiments/core_narrative/results/raw") / run_id
        stdout_path = artifact_dir / "adapter.stdout.txt"
        stderr_path = artifact_dir / "adapter.stderr.txt"
        patch_path = Path(args.patch_path) if args.patch_path else artifact_dir / "submission.patch"

        started_at = iso_now()
        budget_gate = gate_payload(
            ledger_path=Path(args.llm_ledger),
            projected_cost_usd=projected_cost,
            coordinator_decision_ref=args.coordinator_decision_ref,
            acut_id=acut_id,
            split=split,
            attempt=args.attempt,
            env=os.environ,
        )

        if budget_gate["status"] != "passed":
            finished_at = iso_now()
            write_static_artifacts(
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                patch_path=patch_path,
                stdout_text=f"Patch-generation command not executed; budget gate status: {budget_gate['status']}.\n",
            )
            ledger_append: dict[str, Any]
            try:
                ledger_append = append_attempt_record(
                    ledger_path=Path(args.llm_ledger),
                    run_id=run_id,
                    acut_id=acut_id,
                    task_id=task_id,
                    split=split,
                    attempt=args.attempt,
                    event=f"gate_{budget_gate['status']}",
                    started_at=started_at,
                    finished_at=finished_at,
                    input_tokens=0,
                    output_tokens=0,
                    estimated_cost=Decimal("0"),
                    actual_cost=None,
                    metadata={
                        "adapter_id": ADAPTER_ID,
                        "mode": "dry_run" if args.dry_run else "command",
                        "gate_status": budget_gate["status"],
                        "gate_blockers": budget_gate["blockers"],
                        "approvals_required": budget_gate["approvals_required"],
                        "model_call_made": False,
                    },
                )
            except Exception as exc:  # The gate may be blocked because the ledger itself is unavailable.
                ledger_append = ledger_append_error(exc)

            payload = base_payload(
                status=f"gate_{budget_gate['status']}",
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                artifact_dir=artifact_dir,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                patch_path=patch_path,
                command=command,
                budget_gate=budget_gate,
                ledger_append=ledger_append,
                dry_run=args.dry_run,
                command_duration_seconds=0,
            )
            write_normalized_result(
                path=args.normalized_output,
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                status="infra_failed",
                patch_path=patch_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=0,
                error=f"budget gate status: {budget_gate['status']}",
                metadata={
                    "tool": TOOL,
                    "adapter_id": ADAPTER_ID,
                    "dry_run": args.dry_run,
                    "model_call_made": False,
                    "ledger_append_status": ledger_append["status"],
                },
            )
            emit_json(payload, args.output)
            return gate_exit_code(budget_gate)

        if args.dry_run:
            finished_at = iso_now()
            write_static_artifacts(
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                patch_path=patch_path,
                stdout_text="No-model dry run completed; patch-generation command was not executed.\n",
                write_empty_patch=True,
            )
            ledger_append = append_attempt_record(
                ledger_path=Path(args.llm_ledger),
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                event="dry_run_no_model",
                started_at=started_at,
                finished_at=finished_at,
                input_tokens=0,
                output_tokens=0,
                estimated_cost=Decimal("0"),
                actual_cost=None,
                metadata={
                    "adapter_id": ADAPTER_ID,
                    "mode": "dry_run",
                    "gate_status": budget_gate["status"],
                    "model_call_made": False,
                },
            )
            payload = base_payload(
                status="dry_run_completed",
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                artifact_dir=artifact_dir,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                patch_path=patch_path,
                command=command,
                budget_gate=budget_gate,
                ledger_append=ledger_append,
                dry_run=True,
                command_duration_seconds=0,
            )
            write_normalized_result(
                path=args.normalized_output,
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                status="infra_failed",
                patch_path=patch_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=0,
                error="no-model dry run; no ACUT patch was generated",
                metadata={
                    "tool": TOOL,
                    "adapter_id": ADAPTER_ID,
                    "dry_run": True,
                    "model_call_made": False,
                    "ledger_append_status": ledger_append["status"],
                },
            )
            emit_json(payload, args.output)
            return 0

        workspace = require_workspace(args.workspace)
        command_model_call_made = not args.command_no_model
        acut_env, scrubbed_env_var_count = llm_safe_subprocess_env(os.environ)
        run = run_to_redacted_artifacts(
            command,
            cwd=workspace,
            timeout_seconds=args.timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            env=acut_env,
        )
        inner_patch_command = read_inner_patch_command_summary(command)
        patch_artifact = write_safe_patch(workspace, patch_path, acut_env)
        tracked_restore = {"attempted": False, "tracked_changes_remaining": None}
        unsafe_patch_rejected = bool(patch_artifact["unsafe_content_detected"])
        patch_size_bytes = int(patch_artifact.get("size_bytes") or 0)
        no_patch_generated = (
            run["exit_code"] == 0
            and not run["timed_out"]
            and not unsafe_patch_rejected
            and patch_size_bytes == 0
        )
        if unsafe_patch_rejected:
            tracked_restore = restore_tracked_workspace_changes(workspace, acut_env)
        finished_at = iso_now()

        if unsafe_patch_rejected:
            status = "unsafe_patch_rejected"
            event = "command_completed_unsafe_patch_rejected"
        elif run["timed_out"]:
            status = "timeout"
            event = "command_timeout"
        elif no_patch_generated:
            status = "no_patch_generated"
            event = "no_patch_generated"
        elif run["exit_code"] == 0:
            status = "command_completed"
            event = "command_completed"
        else:
            status = "command_failed"
            event = "command_failed"
        verifier_ready_patch_available = (
            status == "command_completed"
            and not unsafe_patch_rejected
            and not run["timed_out"]
            and patch_size_bytes > 0
        )
        nonzero_exit_without_verifier_patch = (
            status == "command_failed"
            and run["exit_code"] not in (0, None)
            and not run["timed_out"]
            and not unsafe_patch_rejected
            and patch_size_bytes == 0
        )
        nonzero_failure_class = (
            effective_nonzero_failure_class(inner_patch_command)
            if nonzero_exit_without_verifier_patch
            else None
        )

        ledger_metadata = {
            "adapter_id": ADAPTER_ID,
            "mode": "command",
            "gate_status": budget_gate["status"],
            "command_exit_code": run["exit_code"],
            "command_timed_out": run["timed_out"],
            "model_call_made": command_model_call_made,
            "patch_size_bytes": patch_size_bytes,
            "no_patch_generated": no_patch_generated,
        }
        if nonzero_failure_class is not None:
            ledger_metadata["failure_class"] = nonzero_failure_class
        transport_failure = inner_patch_command.get("transport_failure")
        if isinstance(transport_failure, dict) and transport_failure.get("present") is True:
            ledger_metadata["transport_failure_class"] = transport_failure.get("failure_class")

        ledger_append = append_attempt_record(
            ledger_path=Path(args.llm_ledger),
            run_id=run_id,
            acut_id=acut_id,
            task_id=task_id,
            split=split,
            attempt=args.attempt,
            event=event,
            started_at=started_at,
            finished_at=finished_at,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=projected_cost,
            actual_cost=actual_cost,
            metadata=ledger_metadata,
        )
        payload = base_payload(
            status=status,
            run_id=run_id,
            acut_id=acut_id,
            task_id=task_id,
            split=split,
            attempt=args.attempt,
            started_at=started_at,
            finished_at=finished_at,
            artifact_dir=artifact_dir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            patch_path=patch_path,
            command=command,
            budget_gate=budget_gate,
            ledger_append=ledger_append,
            dry_run=False,
            command_duration_seconds=float(run["duration_seconds"]),
            extra={
                "model_call_made": command_model_call_made,
                "command_no_model": args.command_no_model,
                "scrubbed_env_var_count": scrubbed_env_var_count,
                "command_exit_code": run["exit_code"],
                "command_timed_out": run["timed_out"],
                "patch_artifact": patch_artifact,
                "no_patch_generated": no_patch_generated,
                "verifier_ready_patch_available": verifier_ready_patch_available,
                "nonzero_exit_without_verifier_patch": nonzero_exit_without_verifier_patch,
                "inner_patch_command": inner_patch_command,
                "tracked_workspace_restore": tracked_restore,
            },
        )
        if status == "no_patch_generated":
            write_normalized_result(
                path=args.normalized_output,
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                status="infra_failed",
                patch_path=patch_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=float(run["duration_seconds"]),
                error="patch-generation command completed without producing a patch",
                metadata={
                    "tool": TOOL,
                    "adapter_id": ADAPTER_ID,
                    "adapter_status": status,
                    "dry_run": False,
                    "command_no_model": args.command_no_model,
                    "model_call_made": command_model_call_made,
                    "command_exit_code": run["exit_code"],
                    "patch_size_bytes": patch_size_bytes,
                    "ledger_append_status": ledger_append["status"],
                },
            )
        elif nonzero_exit_without_verifier_patch:
            write_normalized_result(
                path=args.normalized_output,
                run_id=run_id,
                acut_id=acut_id,
                task_id=task_id,
                split=split,
                attempt=args.attempt,
                started_at=started_at,
                finished_at=finished_at,
                status="infra_failed",
                patch_path=patch_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                duration_seconds=float(run["duration_seconds"]),
                error="patch-generation command exited nonzero without producing a verifier-ready patch",
                metadata={
                    "tool": TOOL,
                    "adapter_id": ADAPTER_ID,
                    "adapter_status": status,
                    "failure_class": nonzero_failure_class or DEFAULT_NONZERO_FAILURE_CLASS,
                    "inner_patch_command": inner_patch_command,
                    "dry_run": False,
                    "command_no_model": args.command_no_model,
                    "model_call_made": command_model_call_made,
                    "command_exit_code": run["exit_code"],
                    "command_timed_out": run["timed_out"],
                    "patch_size_bytes": patch_size_bytes,
                    "no_patch_generated": no_patch_generated,
                    "verifier_ready_patch_available": verifier_ready_patch_available,
                    "ledger_append_status": ledger_append["status"],
                },
            )
        emit_json(payload, args.output)
        if unsafe_patch_rejected:
            return 2
        return 0 if not run["timed_out"] else 124
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
