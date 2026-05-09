#!/usr/bin/env python3
"""Run an ACUT command in a prepared workspace and capture its patch."""

from __future__ import annotations

import argparse
import hashlib
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
    FULL_URL_RE,
    assert_safe_command_arguments,
    ensure_no_required_env_values,
    gate_exit_code,
    gate_payload,
    llm_safe_subprocess_env,
    parse_usd,
    redact_command_arguments,
    redact_sensitive_text,
    run_to_redacted_artifacts,
    unsafe_text_findings,
)


TOOL = "run_task"
HARNESS_UNTRACKED_PREFIXES = (
    ".core_narrative/",
    ".pytest_cache/",
    ".venv/",
)
HARNESS_UNTRACKED_PARTS = {"__pycache__"}
PATCH_DIFF_CONTEXT_LINES = 0
MAX_UNSAFE_PATCH_URL_OCCURRENCE_RECORDS = 20


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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def diff_command(*extra: str) -> list[str]:
    return [
        "git",
        "diff",
        "--binary",
        "--no-ext-diff",
        f"--unified={PATCH_DIFF_CONTEXT_LINES}",
        *extra,
    ]


def collect_patch(workspace: Path, env: dict[str, str]) -> str:
    try:
        completed = subprocess.run(
            diff_command("HEAD"),
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError("git executable was not found") from exc
    if completed.returncode != 0:
        raise ToolError(
            "failed to inspect patch",
            stderr=redact_sensitive_text(completed.stderr.strip(), env),
        )
    patch_parts = [completed.stdout] if completed.stdout else []

    try:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError("git executable was not found") from exc
    if untracked.returncode != 0:
        raise ToolError(
            "failed to inspect untracked files",
            stderr=redact_sensitive_text(os.fsdecode(untracked.stderr).strip(), env),
        )

    for raw_path in filter(None, untracked.stdout.split(b"\0")):
        relative_path = os.fsdecode(raw_path)
        if is_harness_untracked_path(relative_path):
            continue
        try:
            new_file_diff = subprocess.run(
                diff_command("--no-index", "--", "/dev/null", relative_path),
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ToolError("git executable was not found") from exc
        if new_file_diff.returncode not in (0, 1):
            raise ToolError(
                "failed to inspect untracked file patch",
                path=relative_path,
                stderr=redact_sensitive_text(new_file_diff.stderr.strip(), env),
            )
        if new_file_diff.stdout:
            patch_parts.append(new_file_diff.stdout)

    return "".join(part if part.endswith("\n") else f"{part}\n" for part in patch_parts)


def patch_line_role(line: str) -> str:
    if line.startswith(("diff --git ", "index ", "new file mode ", "deleted file mode ")):
        return "metadata"
    if line.startswith(("similarity index ", "rename from ", "rename to ", "@@ ")):
        return "metadata"
    if line.startswith(("--- ", "+++ ")):
        return "metadata"
    if line.startswith("+"):
        return "generated_added"
    if line.startswith("-"):
        return "source_removed"
    if line.startswith(" "):
        return "source_context"
    return "ambiguous"


def unsafe_patch_artifact_attribution(patch_text: str, findings: dict[str, object]) -> dict[str, object]:
    reason_counts = findings.get("reason_counts") if isinstance(findings.get("reason_counts"), dict) else {}
    full_url_role_counts: dict[str, int] = {}
    url_occurrences: list[dict[str, object]] = []
    truncated = False

    for line_number, line in enumerate(patch_text.splitlines(), start=1):
        matches = list(FULL_URL_RE.finditer(line))
        if not matches:
            continue
        role = patch_line_role(line)
        full_url_role_counts[role] = full_url_role_counts.get(role, 0) + len(matches)
        for match in matches:
            if len(url_occurrences) >= MAX_UNSAFE_PATCH_URL_OCCURRENCE_RECORDS:
                truncated = True
                continue
            url_text = match.group(0)
            url_occurrences.append(
                {
                    "line_number": line_number,
                    "diff_line_role": role,
                    "url_sha256": sha256_text(url_text),
                    "url_char_count": len(url_text),
                    "content_recorded": False,
                }
            )

    full_url_count = int(reason_counts.get("full_url", 0)) if isinstance(reason_counts.get("full_url"), int) else 0
    source_derived_count = full_url_role_counts.get("source_removed", 0) + full_url_role_counts.get("source_context", 0)
    generated_count = full_url_role_counts.get("generated_added", 0)
    ambiguous_count = max(
        0,
        full_url_count
        - source_derived_count
        - generated_count,
    )
    non_url_reason_counts = {
        str(reason): int(count)
        for reason, count in reason_counts.items()
        if reason != "full_url" and isinstance(count, int) and count > 0
    }

    if non_url_reason_counts:
        classification = "non_url_unsafe_patch_content"
    elif full_url_count == 0:
        classification = "no_full_url_patch_content"
    elif generated_count > 0:
        classification = "model_generated_full_url"
    elif ambiguous_count > 0:
        classification = "ambiguous_full_url"
    elif source_derived_count > 0:
        classification = "source_derived_full_url"
    else:
        classification = "ambiguous_full_url"

    return {
        "classification": classification,
        "reason_counts": dict(reason_counts),
        "full_url_count": full_url_count,
        "full_url_role_counts": dict(sorted(full_url_role_counts.items())),
        "source_derived_full_url_count": source_derived_count,
        "model_generated_full_url_count": generated_count,
        "ambiguous_full_url_count": ambiguous_count,
        "non_url_reason_counts": dict(sorted(non_url_reason_counts.items())),
        "all_full_urls_source_derived": bool(full_url_count > 0 and source_derived_count == full_url_count),
        "all_unsafe_reasons_source_derived": bool(
            full_url_count > 0 and source_derived_count == full_url_count and not non_url_reason_counts
        ),
        "url_occurrences": url_occurrences,
        "url_occurrences_truncated": truncated,
        "content_recorded": False,
    }


def write_redacted_patch_preview(patch_text: str, patch_path: Path, env: dict[str, str]) -> dict[str, object]:
    redacted = redact_sensitive_text(patch_text, env)
    findings = unsafe_text_findings(redacted, env)
    if findings["unsafe"]:
        return {
            "written": False,
            "unsafe_content_detected_after_redaction": True,
            "unsafe_content_after_redaction": findings,
        }
    preview_path = patch_path.with_name(f"{patch_path.name}.redacted.txt")
    preview_path.write_text(redacted, encoding="utf-8")
    return {
        "path": str(preview_path),
        "written": True,
        "unsafe_content_detected_after_redaction": False,
        "unsafe_content_after_redaction": findings,
        "size_bytes": len(redacted.encode("utf-8")),
        "applies_to_workspace": False,
        "policy": "redacted_diagnostic_preview_only",
    }


def is_harness_untracked_path(relative_path: str) -> bool:
    normalized = relative_path.replace(os.sep, "/")
    if any(normalized.startswith(prefix) for prefix in HARNESS_UNTRACKED_PREFIXES):
        return True
    return bool(HARNESS_UNTRACKED_PARTS.intersection(Path(normalized).parts))


def write_safe_patch(workspace: Path, patch_path: Path, env: dict[str, str]) -> dict[str, object]:
    patch_text = collect_patch(workspace, env)
    findings = unsafe_text_findings(patch_text, env)
    attribution = unsafe_patch_artifact_attribution(patch_text, findings)
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    if findings["unsafe"]:
        if patch_path.exists():
            patch_path.unlink()
        redacted_preview = write_redacted_patch_preview(patch_text, patch_path, env)
        return {
            "path": str(patch_path),
            "written": False,
            "unsafe_content_detected": True,
            "unsafe_content": findings,
            "unsafe_content_attribution": attribution,
            "redacted_preview": redacted_preview,
            "policy": "reject_before_write",
            "size_bytes": 0,
            "diff_context_lines": PATCH_DIFF_CONTEXT_LINES,
        }
    patch_path.write_text(patch_text, encoding="utf-8")
    return {
        "path": str(patch_path),
        "written": True,
        "unsafe_content_detected": False,
        "unsafe_content": findings,
        "unsafe_content_attribution": attribution,
        "policy": "reject_before_write",
        "size_bytes": len(patch_text.encode("utf-8")),
        "diff_context_lines": PATCH_DIFF_CONTEXT_LINES,
    }


def restore_tracked_workspace_changes(workspace: Path, env: dict[str, str]) -> dict[str, object]:
    result = git("reset", "--hard", "--quiet", "HEAD", cwd=workspace)
    if result.returncode != 0:
        raise ToolError(
            "failed to restore tracked workspace changes after unsafe patch rejection",
            stderr=redact_sensitive_text(result.stderr.strip(), env),
        )
    status = git("status", "--porcelain", "--untracked-files=no", cwd=workspace)
    if status.returncode != 0:
        raise ToolError(
            "failed to inspect tracked workspace state after unsafe patch rejection",
            stderr=redact_sensitive_text(status.stderr.strip(), env),
        )
    return {
        "attempted": True,
        "tracked_changes_remaining": bool(status.stdout.strip()),
    }


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
        patch_artifact = write_safe_patch(workspace, patch_path, acut_env)
        tracked_restore = {"attempted": False, "tracked_changes_remaining": None}
        unsafe_patch_rejected = bool(patch_artifact["unsafe_content_detected"])
        if unsafe_patch_rejected:
            tracked_restore = restore_tracked_workspace_changes(workspace, acut_env)
        finished_at = iso_now()

        if unsafe_patch_rejected:
            status = "unsafe_patch_rejected"
        elif run["timed_out"]:
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
                "patch_artifact_checked": True,
                "unsafe_patch_content_rejected": True,
                "patch_rejection_restores_tracked_changes": True,
            },
            "agent": {
                "exit_code": run["exit_code"],
                "duration_seconds": run["duration_seconds"],
                "stdout_artifact": str(stdout_path),
                "stderr_artifact": str(stderr_path),
            },
            "patch_path": str(patch_path),
            "patch_artifact": patch_artifact,
            "tracked_workspace_restore": tracked_restore,
        }
        emit_json(payload, args.output)
        if unsafe_patch_rejected:
            return 2
        return 0 if not run["timed_out"] else 124
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
