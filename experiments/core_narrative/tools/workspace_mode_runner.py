#!/usr/bin/env python3
"""Run an ACUT in a repo workspace and verify the resulting workspace diff."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
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
from _llm_budget import llm_safe_subprocess_env, redact_sensitive_text, run_to_redacted_artifacts, unsafe_text_findings
from run_task import is_harness_untracked_path, unsafe_patch_artifact_attribution, write_redacted_patch_preview


TOOL = "workspace_mode_runner"
SCHEMA_VERSION = "core-narrative.workspace-mode-execution.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces"
DEFAULT_RAW_ROOT = REPO_ROOT / "experiments/core_narrative/results/raw"
WORKSPACE_DIFF_CONTEXT_LINES = 3


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create an isolated ACUT run workspace, collect the final workspace "
            "state as a candidate patch, replay it in a fresh verification "
            "workspace, and emit a structured result."
        )
    )
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--source-repo", required=True, help="Local target repository checkout.")
    parser.add_argument("--acut", help="ACUT manifest JSON/YAML path.")
    parser.add_argument("--acut-id", help="ACUT id override when --acut is not supplied.")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--run-id")
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACES_ROOT))
    parser.add_argument("--artifact-dir")
    parser.add_argument("--output")
    parser.add_argument("--acut-timeout-seconds", type=int)
    parser.add_argument("--verifier-timeout-seconds", type=int)
    parser.add_argument(
        "--install-workspaces",
        action="store_true",
        help="Create .venv and install the package in run and verification workspaces before use.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="ACUT command to run after --.")
    return parser.parse_args(list(argv) if argv is not None else None)


def resolve_acut_id(args: argparse.Namespace) -> str:
    if args.acut:
        acut = load_manifest(args.acut)
        require_keys(acut, ["acut_id"], "ACUT manifest")
        return str(acut["acut_id"])
    if args.acut_id:
        return str(args.acut_id)
    raise ToolError("either --acut or --acut-id is required")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture_artifacts(
    command: Sequence[str],
    *,
    artifact_dir: Path,
    name: str,
    cwd: Path | None = None,
    timeout_seconds: int | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    stdout_path = artifact_dir / f"{name}.stdout.txt"
    stderr_path = artifact_dir / f"{name}.stderr.txt"
    summary_path = artifact_dir / f"{name}.json"
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
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env) if env is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout_path.write_text(redact_sensitive_text(completed.stdout, env or os.environ), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(completed.stderr, env or os.environ), encoding="utf-8")
    except FileNotFoundError as exc:
        command_error = f"command executable was not found: {command[0]}"
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(command_error, env or os.environ), encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout_path.write_text(redact_sensitive_text(exc.stdout or "", env or os.environ), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(exc.stderr or "", env or os.environ), encoding="utf-8")
    finished_at = iso_now()
    summary = {
        "name": name,
        "command": [redact_sensitive_text(str(part), env or os.environ) for part in command],
        "cwd": str(cwd) if cwd is not None else None,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "command_error": command_error,
        "duration_seconds": round(time.monotonic() - started, 3),
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
        "summary_artifact": str(summary_path),
    }
    write_json(summary_path, summary)
    return summary


def git_required(workspace: Path, *args: str, message: str) -> str:
    result = git(*args, cwd=workspace)
    if result.returncode != 0:
        raise ToolError(message, command=["git", *args], stderr=result.stderr.strip(), workspace=str(workspace))
    return result.stdout.strip()


def workspace_refs(workspace: Path) -> dict[str, str]:
    return {
        "base_ref": git_required(workspace, "rev-parse", "HEAD", message="failed to record BASE_REF"),
        "base_tree": git_required(workspace, "rev-parse", "HEAD^{tree}", message="failed to record BASE_TREE"),
    }


def prepare_workspace_for_task(
    *,
    task_path: Path,
    source_repo: Path,
    workspace: Path,
    artifact_dir: Path,
    summary_name: str,
) -> tuple[Path, dict[str, Any], dict[str, str]]:
    prepare_payload_path = artifact_dir / f"{summary_name}_payload.json"
    prepare_command_path = artifact_dir / f"{summary_name}.json"
    command = [
        sys.executable,
        str(PREPARE),
        "--task",
        str(task_path),
        "--source-repo",
        str(source_repo),
        "--workspace",
        str(workspace),
        "--force",
        "--output",
        str(prepare_payload_path),
    ]
    summary = run_capture_artifacts(command, artifact_dir=artifact_dir, name=summary_name, timeout_seconds=120)
    if summary["exit_code"] != 0 or summary["timed_out"]:
        raise ToolError("workspace preparation failed", summary=summary)
    prepare_payload = json.loads(prepare_payload_path.read_text(encoding="utf-8"))
    prepare_payload["workspace_mode_artifacts"] = {
        "payload": str(prepare_payload_path),
        "command": str(prepare_command_path),
        "stdout": summary["stdout_artifact"],
        "stderr": summary["stderr_artifact"],
    }
    prepare_payload["workspace_mode_command"] = summary
    base = workspace_refs(workspace)
    write_json(
        artifact_dir / f"{summary_name}_base_refs.json",
        {
            "workspace": str(workspace),
            "BASE_REF": base["base_ref"],
            "BASE_TREE": base["base_tree"],
            "recorded_immediately_after_workspace_creation": True,
        },
    )
    return workspace, prepare_payload, base


def install_workspace_dependencies(
    *,
    workspace: Path,
    artifact_dir: Path,
    name_prefix: str,
    timeout_seconds: int | None,
) -> dict[str, Any]:
    if not any((workspace / name).exists() for name in ("pyproject.toml", "setup.py", "setup.cfg")):
        return {"status": "skipped", "reason": "no_python_project_metadata"}

    venv = workspace / ".venv"
    if venv.exists():
        shutil.rmtree(venv)
    create = run_capture_artifacts(
        [sys.executable, "-m", "venv", ".venv"],
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_create",
        cwd=workspace,
        timeout_seconds=timeout_seconds,
    )
    if create["exit_code"] != 0 or create["timed_out"]:
        raise ToolError("workspace venv creation failed", summary=create)

    pip = ".venv/bin/python"
    upgrade = run_capture_artifacts(
        [pip, "-m", "pip", "install", "-q", "--upgrade", "pip"],
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_pip_upgrade",
        cwd=workspace,
        timeout_seconds=timeout_seconds,
    )
    if upgrade["exit_code"] != 0 or upgrade["timed_out"]:
        raise ToolError("workspace pip upgrade failed", summary=upgrade)

    install = run_capture_artifacts(
        [pip, "-m", "pip", "install", "-q", "-e", ".", "pytest"],
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_install",
        cwd=workspace,
        timeout_seconds=timeout_seconds,
    )
    if install["exit_code"] != 0 or install["timed_out"]:
        raise ToolError("workspace dependency install failed", summary=install)
    return {
        "status": "installed",
        "venv_backend": "python_venv",
        "venv_create": create,
        "pip_upgrade": upgrade,
        "venv_install": install,
    }


def sorted_untracked_files(workspace: Path, env: Mapping[str, str]) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ToolError(
            "failed to inspect untracked files",
            stderr=redact_sensitive_text(os.fsdecode(result.stderr).strip(), env),
        )
    return sorted(os.fsdecode(raw) for raw in filter(None, result.stdout.split(b"\0")))


def is_harness_generated_untracked_path(relative_path: str) -> bool:
    normalized = relative_path.replace(os.sep, "/")
    if is_harness_untracked_path(normalized):
        return True
    return any(part.endswith(".egg-info") for part in Path(normalized).parts)


def write_status_artifact(workspace: Path, path: Path, env: Mapping[str, str]) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v2", "--untracked-files=all"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ToolError("failed to inspect workspace status", stderr=redact_sensitive_text(result.stderr, env))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.stdout, encoding="utf-8")
    return {
        "path": str(path),
        "size_bytes": len(result.stdout.encode("utf-8")),
        "line_count": len(result.stdout.splitlines()),
    }


def workspace_diff_command(base_ref: str) -> list[str]:
    return [
        "git",
        "diff",
        "--binary",
        "--no-ext-diff",
        "--full-index",
        f"--unified={WORKSPACE_DIFF_CONTEXT_LINES}",
        base_ref,
        "--",
    ]


def collect_candidate_patch_from_workspace(
    *,
    workspace: Path,
    patch_path: Path,
    base_ref: str,
    base_tree: str,
    env: Mapping[str, str],
    status_path: Path,
) -> dict[str, Any]:
    status_artifact = write_status_artifact(workspace, status_path, env)
    current_head = git_required(workspace, "rev-parse", "HEAD", message="failed to inspect current HEAD")
    head_drifted = current_head != base_ref
    untracked_records: list[dict[str, Any]] = []
    included_paths: list[str] = []
    index_restore_error: str | None = None

    for relative_path in sorted_untracked_files(workspace, env):
        record: dict[str, Any] = {"path": relative_path}
        if is_harness_generated_untracked_path(relative_path):
            record.update({"disposition": "ignored_harness", "reason": "harness_generated_path"})
            untracked_records.append(record)
            continue
        target = workspace / relative_path
        if target.is_symlink():
            record.update({"disposition": "rejected_untracked_file", "reason": "symlink_not_included"})
            untracked_records.append(record)
            continue
        if not target.is_file():
            record.update({"disposition": "rejected_untracked_file", "reason": "not_a_regular_file"})
            untracked_records.append(record)
            continue
        add = git("add", "-N", "--", relative_path, cwd=workspace)
        if add.returncode != 0:
            record.update(
                {
                    "disposition": "rejected_untracked_file",
                    "reason": "git_add_intent_failed",
                    "stderr": redact_sensitive_text(add.stderr.strip(), env),
                }
            )
            untracked_records.append(record)
            continue
        included_paths.append(relative_path)
        record.update({"disposition": "included", "reason": "regular_file_intent_to_add"})
        untracked_records.append(record)

    try:
        completed = subprocess.run(
            workspace_diff_command(base_ref),
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    finally:
        if included_paths:
            reset = git("reset", "-q", "--", *included_paths, cwd=workspace)
            if reset.returncode != 0:
                index_restore_error = redact_sensitive_text(reset.stderr.strip(), env)

    if completed.returncode != 0:
        raise ToolError("failed to extract candidate patch", stderr=redact_sensitive_text(completed.stderr, env))

    patch_text = completed.stdout
    findings = unsafe_text_findings(patch_text, env)
    attribution = unsafe_patch_artifact_attribution(patch_text, dict(findings))
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    if findings["unsafe"]:
        if patch_path.exists():
            patch_path.unlink()
        redacted_preview = write_redacted_patch_preview(patch_text, patch_path, dict(env))
        written = False
        size_bytes = 0
    else:
        patch_path.write_text(patch_text, encoding="utf-8")
        redacted_preview = None
        written = True
        size_bytes = len(patch_text.encode("utf-8"))

    rejected = [item for item in untracked_records if item["disposition"] == "rejected_untracked_file"]
    ignored = [item for item in untracked_records if item["disposition"] == "ignored_harness"]
    return {
        "path": str(patch_path),
        "written": written,
        "size_bytes": size_bytes,
        "raw_candidate_patch_size_bytes": len(patch_text.encode("utf-8")),
        "sha256": sha256_file(patch_path),
        "unsafe_content_detected": bool(findings["unsafe"]),
        "unsafe_content": findings,
        "unsafe_content_attribution": attribution,
        "redacted_preview": redacted_preview,
        "diff_command": workspace_diff_command(base_ref),
        "diff_base_ref": base_ref,
        "base_ref": base_ref,
        "base_tree": base_tree,
        "current_head": current_head,
        "head_drifted": head_drifted,
        "status_artifact": status_artifact,
        "untracked_files": untracked_records,
        "rejected_untracked_files": rejected,
        "ignored_harness_untracked_files": ignored,
        "included_untracked_files": [item for item in untracked_records if item["disposition"] == "included"],
        "index_restore_error": index_restore_error,
        "diff_context_lines": WORKSPACE_DIFF_CONTEXT_LINES,
        "has_scoreable_diff": bool(written and size_bytes > 0 and not findings["unsafe"]),
    }


def verification_status_from_normalized(
    *,
    normalized: Mapping[str, Any],
    command_summary: Mapping[str, Any],
) -> tuple[str, str | None]:
    if command_summary.get("timed_out") is True:
        return "timeout", "verifier"
    if command_summary.get("exit_code") not in (0, None) and not normalized:
        return "verifier_infra_error", None
    status = normalized.get("status")
    verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
    if status == "passed":
        return "verified_pass", None
    if status == "failed":
        return "verified_fail", None
    if status == "timeout":
        return "timeout", "verifier"
    if status == "invalid_submission" and verification.get("exit_code") is None:
        return "patch_apply_error", None
    return "verifier_infra_error", None


def verify_candidate_patch(
    *,
    task_path: Path,
    source_repo: Path,
    workspace_root: Path,
    workspace_name: str,
    artifact_dir: Path,
    patch_path: Path,
    acut_id: str,
    attempt: int,
    run_id: str,
    recorded_base_tree: str,
    verifier_timeout_seconds: int | None,
    install_workspace_before_verify: bool,
) -> dict[str, Any]:
    verify_workspace, prepare_summary, verify_base = prepare_workspace_for_task(
        task_path=task_path,
        source_repo=source_repo,
        workspace=workspace_root / workspace_name,
        artifact_dir=artifact_dir,
        summary_name="prepare_verify_workspace",
    )
    base_tree_matches_run = verify_base["base_tree"] == recorded_base_tree
    if not base_tree_matches_run:
        return {
            "attempted": False,
            "status": "base_tree_mismatch",
            "reason": "verification_workspace_base_tree_mismatch",
            "timeout_owner": None,
            "workspace": str(verify_workspace),
            "prepare": prepare_summary,
            "install": None,
            "base_tree": verify_base["base_tree"],
            "recorded_run_base_tree": recorded_base_tree,
            "base_tree_matches_run": False,
            "command": None,
            "normalized_result": None,
            "normalized": None,
            "verifier_exit_code": None,
            "verifier_stdout_artifact": None,
            "verifier_stderr_artifact": None,
            "patch_apply_error": None,
            "error": "verification workspace base tree did not match recorded run BASE_TREE",
        }

    install_summary = None
    if install_workspace_before_verify:
        install_summary = install_workspace_dependencies(
            workspace=verify_workspace,
            artifact_dir=artifact_dir,
            name_prefix="verify_",
            timeout_seconds=verifier_timeout_seconds,
        )

    normalized_path = artifact_dir / "normalized_result.json"
    if normalized_path.exists():
        normalized_path.unlink()
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(verify_workspace),
        "--task",
        str(task_path),
        "--patch",
        str(patch_path),
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
    ]
    if verifier_timeout_seconds is not None:
        command.extend(["--timeout-seconds", str(verifier_timeout_seconds)])
    outer_timeout = None if verifier_timeout_seconds is None else verifier_timeout_seconds + 30
    command_summary = run_capture_artifacts(
        command,
        artifact_dir=artifact_dir,
        name="verify_command",
        timeout_seconds=outer_timeout,
    )
    if normalized_path.exists():
        normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
    else:
        normalized = {
            "status": "infra_failed",
            "error": command_summary.get("command_error") or "verifier did not emit a normalized result",
            "verification": {"exit_code": None, "stdout_artifact": None, "stderr_artifact": None, "duration_seconds": None},
            "metadata": {"tool": TOOL},
        }
    status, timeout_owner = verification_status_from_normalized(
        normalized=normalized,
        command_summary=command_summary,
    )
    verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
    return {
        "attempted": True,
        "status": status,
        "timeout_owner": timeout_owner,
        "workspace": str(verify_workspace),
        "prepare": prepare_summary,
        "install": install_summary,
        "base_tree": verify_base["base_tree"],
        "recorded_run_base_tree": recorded_base_tree,
        "base_tree_matches_run": base_tree_matches_run,
        "command": command_summary,
        "normalized_result": str(normalized_path),
        "normalized": normalized,
        "verifier_exit_code": verification.get("exit_code"),
        "verifier_stdout_artifact": verification.get("stdout_artifact"),
        "verifier_stderr_artifact": verification.get("stderr_artifact"),
        "patch_apply_error": normalized.get("error") if status == "patch_apply_error" else None,
    }


def acut_command_status(run: Mapping[str, Any]) -> str:
    if run.get("timed_out") is True:
        return "timeout"
    if run.get("command_error"):
        return "error"
    if run.get("exit_code") == 0:
        return "zero"
    if run.get("exit_code") is None:
        return "unknown"
    return "nonzero"


def run_acut_command(
    *,
    command: Sequence[str],
    workspace: Path,
    artifact_dir: Path,
    timeout_seconds: int | None,
    env: Mapping[str, str],
) -> dict[str, Any]:
    stdout_path = artifact_dir / "acut.stdout.txt"
    stderr_path = artifact_dir / "acut.stderr.txt"
    started = time.monotonic()
    try:
        run = run_to_redacted_artifacts(
            command,
            cwd=workspace,
            timeout_seconds=timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            env=env,
        )
        command_error = None
    except ToolError as exc:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(str(exc), env), encoding="utf-8")
        run = {
            "exit_code": None,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        command_error = str(exc)
    summary = {
        "name": "acut_command",
        "command": [redact_sensitive_text(str(part), env) for part in command],
        "cwd": str(workspace),
        "exit_code": run["exit_code"],
        "timed_out": run["timed_out"],
        "command_error": command_error,
        "duration_seconds": run["duration_seconds"],
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }
    write_json(artifact_dir / "acut_command.json", summary)
    return summary


def no_verification_result(reason: str) -> dict[str, Any]:
    return {
        "attempted": False,
        "status": "not_attempted",
        "reason": reason,
        "timeout_owner": None,
        "workspace": None,
        "verifier_exit_code": None,
        "normalized": None,
    }


def execute_workspace_mode(
    *,
    task_path: Path,
    source_repo: Path,
    acut_id: str,
    attempt: int,
    run_id: str,
    artifact_dir: Path,
    workspace_root: Path,
    command: Sequence[str],
    acut_timeout_seconds: int | None,
    verifier_timeout_seconds: int | None,
    install_workspaces: bool,
) -> dict[str, Any]:
    if attempt < 1:
        raise ToolError("--attempt must be at least 1")
    command = command_from_args(list(command))
    task = load_manifest(task_path)
    require_keys(task, ["task_id", "repo_slug", "split", "source", "verifier"], "task manifest")
    task_id = str(task["task_id"])
    split = str(task["split"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    workspace_root.mkdir(parents=True, exist_ok=True)
    started_at = iso_now()
    started = time.monotonic()

    run_workspace, prepare_summary, base = prepare_workspace_for_task(
        task_path=task_path,
        source_repo=source_repo,
        workspace=workspace_root / f"{run_id}__run",
        artifact_dir=artifact_dir,
        summary_name="prepare_run_workspace",
    )
    run_install = None
    if install_workspaces:
        run_install = install_workspace_dependencies(
            workspace=run_workspace,
            artifact_dir=artifact_dir,
            name_prefix="run_",
            timeout_seconds=acut_timeout_seconds,
        )

    acut_env, scrubbed_env_var_count = llm_safe_subprocess_env(os.environ)
    acut_env["CORE_NARRATIVE_TASK_PACKAGE"] = str((run_workspace / ".core_narrative" / "task.json").resolve())
    acut_summary = run_acut_command(
        command=command,
        workspace=run_workspace,
        artifact_dir=artifact_dir,
        timeout_seconds=acut_timeout_seconds,
        env=acut_env,
    )

    patch_path = artifact_dir / "candidate.patch"
    try:
        candidate = collect_candidate_patch_from_workspace(
            workspace=run_workspace,
            patch_path=patch_path,
            base_ref=base["base_ref"],
            base_tree=base["base_tree"],
            env=acut_env,
            status_path=artifact_dir / "run_workspace.status",
        )
        extraction_error = None
    except Exception as exc:
        candidate = {
            "path": str(patch_path),
            "written": False,
            "size_bytes": 0,
            "sha256": None,
            "base_ref": base["base_ref"],
            "base_tree": base["base_tree"],
            "current_head": None,
            "head_drifted": None,
            "has_scoreable_diff": False,
            "untracked_files": [],
        }
        extraction_error = str(exc)

    if extraction_error is not None:
        status = "candidate_patch_extraction_error"
        timeout_owner = None
        verification = no_verification_result("candidate_patch_extraction_failed")
        error = extraction_error
    elif acut_summary["timed_out"]:
        status = "timeout"
        timeout_owner = "acut"
        verification = no_verification_result("acut_timeout")
        error = "ACUT command timed out"
    elif candidate.get("unsafe_content_detected") is True:
        status = "unsafe_or_scope_violation"
        timeout_owner = None
        verification = no_verification_result("unsafe_candidate_patch")
        error = "candidate patch contained unsafe content"
    elif not candidate.get("has_scoreable_diff"):
        if acut_summary.get("command_error"):
            status = "acut_command_error"
            error = str(acut_summary["command_error"])
        else:
            status = "no_diff"
            error = None
        timeout_owner = None
        verification = no_verification_result("no_scoreable_source_diff")
    else:
        verification = verify_candidate_patch(
            task_path=task_path,
            source_repo=source_repo,
            workspace_root=workspace_root,
            workspace_name=f"{run_id}__verify",
            artifact_dir=artifact_dir,
            patch_path=patch_path,
            acut_id=acut_id,
            attempt=attempt,
            run_id=run_id,
            recorded_base_tree=base["base_tree"],
            verifier_timeout_seconds=verifier_timeout_seconds,
            install_workspace_before_verify=install_workspaces,
        )
        status = str(verification["status"])
        timeout_owner = verification.get("timeout_owner")
        error = verification.get("patch_apply_error") or verification.get("error")

    finished_at = iso_now()
    metadata = {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "acut_exit_code": acut_summary["exit_code"],
        "acut_command_status": acut_command_status(acut_summary),
        "acut_timed_out": acut_summary["timed_out"],
        "acut_command_error": acut_summary.get("command_error"),
        "timeout_owner": timeout_owner,
        "base_ref": base["base_ref"],
        "base_tree": base["base_tree"],
        "current_head": candidate.get("current_head"),
        "head_drifted": candidate.get("head_drifted"),
        "candidate_patch_sha256": candidate.get("sha256"),
        "candidate_patch_size_bytes": candidate.get("size_bytes"),
        "candidate_patch_from_base_ref": True,
        "candidate_patch_extraction_error": extraction_error,
        "scrubbed_secret_like_env_var_count": scrubbed_env_var_count,
        "run_workspace_local_tests_are_auxiliary": True,
        "verifier_result_source": "fresh_verification_workspace" if verification.get("attempted") else "not_attempted",
    }
    payload = {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(time.monotonic() - started, 3),
        "run_workspace": str(run_workspace),
        "prepare": prepare_summary,
        "install": run_install,
        "acut": acut_summary,
        "candidate_patch": candidate,
        "verification": verification,
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "prepare_run_payload": prepare_summary["workspace_mode_artifacts"]["payload"],
            "prepare_run_command": prepare_summary["workspace_mode_artifacts"]["command"],
            "acut_stdout": str(artifact_dir / "acut.stdout.txt"),
            "acut_stderr": str(artifact_dir / "acut.stderr.txt"),
            "acut_command": str(artifact_dir / "acut_command.json"),
            "run_status": str(artifact_dir / "run_workspace.status"),
            "candidate_patch": str(patch_path),
            "normalized_result": verification.get("normalized_result"),
        },
        "metadata": metadata,
        "error": error,
    }
    write_json(artifact_dir / "workspace_mode_result.json", payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        task_path = Path(args.task)
        task = load_manifest(task_path)
        require_keys(task, ["task_id"], "task manifest")
        acut_id = resolve_acut_id(args)
        timestamp = iso_now().replace(":", "").replace("-", "")
        run_id = args.run_id or f"{slug(acut_id)}__{slug(str(task['task_id']))}__attempt{args.attempt}__{timestamp}"
        artifact_dir = Path(args.artifact_dir) if args.artifact_dir else DEFAULT_RAW_ROOT / run_id
        payload = execute_workspace_mode(
            task_path=task_path,
            source_repo=Path(args.source_repo),
            acut_id=acut_id,
            attempt=args.attempt,
            run_id=run_id,
            artifact_dir=artifact_dir,
            workspace_root=Path(args.workspace_root),
            command=args.command,
            acut_timeout_seconds=args.acut_timeout_seconds,
            verifier_timeout_seconds=args.verifier_timeout_seconds,
            install_workspaces=args.install_workspaces,
        )
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
