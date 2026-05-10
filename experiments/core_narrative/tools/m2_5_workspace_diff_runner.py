#!/usr/bin/env python3
"""Run the M2.5 workspace-diff-v1 scoreability recovery smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, git, iso_now, load_manifest, write_json
from _llm_budget import DEFAULT_LEDGER_PATH, gate_payload, llm_safe_subprocess_env, money_json, redact_sensitive_text
from run_task import is_harness_untracked_path, write_safe_patch


TOOL = "m2_5_workspace_diff_runner"
SCHEMA_VERSION = "core-narrative.m2-5-workspace-diff-v1"
SUBMISSION_CONTRACT = "workspace-diff-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_PACK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces"
RAW_ROOT = REPO_ROOT / "experiments/core_narrative/results/raw"
NORMALIZED_ROOT = REPO_ROOT / "experiments/core_narrative/results/normalized"
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
ACUT_ADAPTER = REPO_ROOT / "experiments/core_narrative/tools/acut_patch_adapter.py"
CODEX_CLI_PATCH_COMMAND = REPO_ROOT / "experiments/core_narrative/tools/codex_cli_patch_command.py"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/m2_5_workspace_diff_summary_20260510.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_scoreability_recovery.md"
DEFAULT_TASKS = ("click__rwork__003", "click__rwork__004", "click__rwork__006")
DEFAULT_ACUTS = ("cheap-generic-swe", "cheap-click-specialist")
PATCH_READY_STATUSES = {"passed", "failed", "timeout"}
SCOREABLE_STATUSES = {"passed", "failed", "timeout", "invalid_submission"}
PATCH_READY_THRESHOLD = 0.70
INVALID_RATE_THRESHOLD = 0.25


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-prefix", default="m2_5_workspace_diff_20260510")
    parser.add_argument("--mode", choices=("synthetic", "noop", "live"), default="synthetic")
    parser.add_argument("--tasks", nargs="+", default=list(DEFAULT_TASKS))
    parser.add_argument("--acuts", nargs="+", default=list(DEFAULT_ACUTS))
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--llm-ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--runner-timeout-seconds", type=int, default=900)
    parser.add_argument("--codex-timeout-seconds", type=int, default=900)
    parser.add_argument("--skip-noop-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--coordinator-decision-ref",
        help="Forwarded to live budget gates when policy requires an explicit coordinator decision.",
    )
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


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str | None:
    if not root.exists():
        return None
    if root.is_file():
        return sha256_file(root)
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update((sha256_file(path) or "").encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def task_split_from_id(task_id: str) -> str:
    if "__rwork__" in task_id:
        return "rwork"
    if "__rbench__" in task_id:
        return "rbench"
    raise ToolError("task id does not encode a supported Click split", task_id=task_id)


def task_manifest_path(task_id: str) -> Path:
    split = task_split_from_id(task_id)
    path = TASK_PACK_ROOT / "click" / split / task_id / "task.yaml"
    if not path.exists():
        raise ToolError("task manifest does not exist", task_id=task_id, path=str(path))
    return path


def acut_manifest_path(acut_id: str) -> Path:
    path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
    if not path.exists():
        raise ToolError("ACUT manifest does not exist", acut_id=acut_id, path=str(path))
    return path


def context_paths_for_task(task: Mapping[str, Any], workspace: Path) -> list[str]:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
    compare = metadata.get("source_compare") if isinstance(metadata.get("source_compare"), Mapping) else {}
    paths = compare.get("changed_files") if isinstance(compare.get("changed_files"), list) else []
    valid = [str(path) for path in paths if isinstance(path, str) and (workspace / path).is_file()]
    if valid:
        return valid
    compare = task.get("source_compare") if isinstance(task.get("source_compare"), Mapping) else {}
    paths = compare.get("changed_files") if isinstance(compare.get("changed_files"), list) else []
    return [str(path) for path in paths if isinstance(path, str) and (workspace / path).is_file()]


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


def prepare_workspace(task_id: str, workspace_name: str, artifact_dir: Path, *, summary_name: str) -> tuple[Path, dict[str, Any]]:
    workspace = WORKSPACES_ROOT / workspace_name
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
        str(artifact_dir / f"{summary_name}.json"),
    ]
    completed = run_capture(command, timeout=120)
    if completed.returncode != 0:
        raise ToolError("workspace preparation failed", stderr=redact_sensitive_text(completed.stderr, os.environ))
    return workspace, json.loads((artifact_dir / f"{summary_name}.json").read_text(encoding="utf-8"))


def install_workspace(workspace: Path, artifact_dir: Path, timeout_seconds: int, *, name_prefix: str) -> dict[str, Any]:
    uv = shutil.which("uv")
    if uv:
        command = [uv, "venv", "--python", "3.12", ".venv"]
        started_at = iso_now()
        completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
        finished_at = iso_now()
        create_summary = write_command_artifacts(
            completed=completed,
            artifact_dir=artifact_dir,
            name=f"{name_prefix}venv_create",
            command=command,
            started_at=started_at,
            finished_at=finished_at,
        )
        if completed.returncode == 0:
            command = [uv, "pip", "install", "--python", ".venv/bin/python", "-q", "-e", ".", "pytest"]
            started_at = iso_now()
            completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
            finished_at = iso_now()
            install_summary = write_command_artifacts(
                completed=completed,
                artifact_dir=artifact_dir,
                name=f"{name_prefix}venv_install",
                command=command,
                started_at=started_at,
                finished_at=finished_at,
            )
            install_summary["venv_create"] = create_summary
            install_summary["venv_backend"] = "uv"
            if completed.returncode != 0:
                raise ToolError("workspace dependency install failed", summary=install_summary)
            return install_summary

    if (workspace / ".venv").exists():
        shutil.rmtree(workspace / ".venv")
    command = [sys.executable, "-m", "venv", ".venv"]
    started_at = iso_now()
    completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    create_summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_create",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace venv creation failed", summary=create_summary)
    command = [".venv/bin/python", "-m", "pip", "install", "-q", "--upgrade", "pip"]
    started_at = iso_now()
    completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    upgrade_summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_pip_upgrade",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace pip upgrade failed", summary=upgrade_summary)
    command = [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"]
    started_at = iso_now()
    completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    install_summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_install",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    install_summary["venv_create"] = create_summary
    install_summary["pip_upgrade"] = upgrade_summary
    install_summary["venv_backend"] = "python_venv"
    if completed.returncode != 0:
        raise ToolError("workspace dependency install failed", summary=install_summary)
    return install_summary


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
        f"{run_id}__noop",
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(output),
        "--skip-apply",
    ]
    started_at = iso_now()
    completed = run_capture(command, timeout=120)
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


def inspect_untracked_scope(workspace: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return {"checked": False, "failure_class": "git_ls_files_failed", "reserved_count": 0, "source_count": 0}
    reserved: list[str] = []
    source: list[str] = []
    for raw in filter(None, completed.stdout.split(b"\0")):
        path = os.fsdecode(raw)
        if is_harness_untracked_path(path) or path == ".git" or path.startswith(".git/"):
            reserved.append(path)
        else:
            source.append(path)
    return {
        "checked": True,
        "reserved_count": len(reserved),
        "source_count": len(source),
        "reserved_paths_sample": reserved[:10],
        "source_paths_sample": source[:10],
    }


def collect_workspace_candidate_patch(workspace: Path, patch_path: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    safe_env = dict(env or {})
    untracked_scope = inspect_untracked_scope(workspace)
    patch_artifact = write_safe_patch(workspace, patch_path, safe_env)
    size_bytes = int(patch_artifact.get("size_bytes") or 0)
    unsafe = patch_artifact.get("unsafe_content_detected") is True
    patch_ready = bool(patch_artifact.get("written") is True and size_bytes > 0 and not unsafe)
    if patch_ready:
        status = "candidate_patch_ready"
        failure_owner = "none"
        failure_class = None
    elif unsafe:
        status = "candidate_patch_rejected"
        failure_owner = "artifact_policy"
        failure_class = "unsafe_patch_content"
    elif untracked_scope.get("reserved_count", 0) and not untracked_scope.get("source_count", 0):
        status = "no_verifier_ready_source_patch"
        failure_owner = "candidate_patch"
        failure_class = "reserved_generated_artifact_only"
    else:
        status = "no_verifier_ready_source_patch"
        failure_owner = "candidate_patch"
        failure_class = "no_workspace_patch"
    return {
        "status": status,
        "patch_ready": patch_ready,
        "failure_owner": failure_owner,
        "failure_class": failure_class,
        "patch_artifact": patch_artifact,
        "untracked_scope": untracked_scope,
        "candidate_patch_sha256": sha256_file(patch_path),
        "candidate_patch_size_bytes": size_bytes,
    }


def apply_synthetic_workspace_edit(workspace: Path, context_paths: Sequence[str]) -> dict[str, Any]:
    for rel_path in context_paths:
        target = workspace / rel_path
        if not target.is_file():
            continue
        original = target.read_text(encoding="utf-8")
        suffix = "\n# barcarolle workspace-diff-v1 no-model baseline\n"
        target.write_text(original.rstrip("\n") + suffix, encoding="utf-8")
        return {"modified": True, "path": rel_path, "edit": "append_comment"}
    raise ToolError("synthetic mode needs at least one editable context file", failure_class="empty_context_paths")


def write_normalized_result(
    *,
    normalized_path: Path,
    run_id: str,
    acut_id: str,
    task_id: str,
    split: str,
    attempt: int,
    status: str,
    patch_path: Path,
    started_at: str,
    finished_at: str,
    error: str | None,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
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
            "stdout_artifact": None,
            "stderr_artifact": None,
            "duration_seconds": 0,
        },
        "review": {
            "mergeability_grade": None,
            "wrong_module": False,
            "rule_violation": False,
            "notes": "",
        },
        "error": error,
        "metadata": dict(metadata),
    }
    write_json(normalized_path, payload)
    return payload


def patch_artifact_from_collection(collection: Mapping[str, Any]) -> Mapping[str, Any]:
    artifact = collection.get("patch_artifact")
    return artifact if isinstance(artifact, Mapping) else {}


def patch_size_from_collection(collection: Mapping[str, Any], patch_path: Path) -> int:
    for value in (
        collection.get("candidate_patch_size_bytes"),
        patch_artifact_from_collection(collection).get("size_bytes"),
    ):
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return patch_path.stat().st_size if patch_path.exists() else 0


def patch_sha_from_collection(collection: Mapping[str, Any], patch_path: Path) -> str | None:
    value = collection.get("candidate_patch_sha256")
    return str(value) if value else sha256_file(patch_path)


def patch_persisted_from_collection(collection: Mapping[str, Any], patch_path: Path) -> bool:
    artifact = patch_artifact_from_collection(collection)
    return bool(artifact.get("written") is True and patch_size_from_collection(collection, patch_path) > 0)


def clean_replay_status_for_normalized_status(status: str, *, attempted: bool) -> str:
    if not attempted:
        return "not_attempted"
    if status in PATCH_READY_STATUSES:
        return "success"
    return status


def clean_replay_failure_class(status: str, *, attempted: bool) -> str | None:
    if not attempted or status in PATCH_READY_STATUSES:
        return None
    if status == "invalid_submission":
        return "clean_replay_invalid_submission"
    if status == "infra_failed":
        return "clean_replay_infra_failed"
    return f"clean_replay_{status}"


def adapter_patch_artifact_from_live_result(live_adapter_result: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(live_adapter_result, Mapping):
        return None
    adapter = live_adapter_result.get("adapter_result")
    if not isinstance(adapter, Mapping):
        return None
    artifact = adapter.get("patch_artifact")
    return artifact if isinstance(artifact, Mapping) else None


def workspace_diff_unsafe_metadata(
    collection_artifact: Mapping[str, Any],
    adapter_artifact: Mapping[str, Any] | None,
) -> dict[str, Any]:
    collection_unsafe = collection_artifact.get("unsafe_content_detected") is True
    adapter_unsafe = bool(adapter_artifact and adapter_artifact.get("unsafe_content_detected") is True)
    source = None
    attribution = None
    if adapter_unsafe and adapter_artifact is not None:
        source = "live_adapter_workspace_diff_collection"
        attribution = adapter_artifact.get("unsafe_content_attribution")
    elif collection_unsafe:
        source = "workspace_diff_collection"
        attribution = collection_artifact.get("unsafe_content_attribution")
    return {
        "unsafe_content_detected": collection_unsafe or adapter_unsafe,
        "collection_unsafe_content_detected": collection_unsafe,
        "adapter_unsafe_content_detected": adapter_unsafe if adapter_artifact is not None else None,
        "unsafe_content_source": source,
        "unsafe_content_attribution": attribution,
    }


def default_failure_owner(status: str, *, replay_attempted: bool) -> str:
    if status == "passed":
        return "none"
    if status == "infra_failed":
        return "infrastructure"
    if replay_attempted and status in {"failed", "timeout"}:
        return "verifier"
    return "candidate_patch"


def default_failure_class(status: str, *, replay_attempted: bool) -> str | None:
    if replay_attempted and status in {"failed", "timeout"}:
        return f"verifier_{status}"
    return None


def enrich_normalized_metadata(
    *,
    normalized: dict[str, Any],
    normalized_path: Path,
    task_id: str,
    acut_id: str,
    runner_workspace: Path | None,
    verify_workspace: Path | None,
    patch_path: Path,
    candidate_collection: Mapping[str, Any],
    mode: str,
    model_call_made: bool,
    clean_replay_invoked: bool | None = None,
    adapter_patch_artifact: Mapping[str, Any] | None = None,
    failure_owner: str | None = None,
    failure_class: str | None = None,
) -> dict[str, Any]:
    task_path = task_manifest_path(task_id)
    acut_path = acut_manifest_path(acut_id)
    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
    status = str(normalized.get("status"))
    collection_artifact = patch_artifact_from_collection(candidate_collection)
    patch_ready = candidate_collection.get("patch_ready") is True
    patch_size_bytes = patch_size_from_collection(candidate_collection, patch_path)
    patch_sha256 = patch_sha_from_collection(candidate_collection, patch_path)
    patch_persisted = patch_persisted_from_collection(candidate_collection, patch_path)
    replay_attempted = bool(clean_replay_invoked) if clean_replay_invoked is not None else verify_workspace is not None
    replay_status = clean_replay_status_for_normalized_status(status, attempted=replay_attempted)
    replay_failure_class = clean_replay_failure_class(status, attempted=replay_attempted)
    unsafe_metadata = workspace_diff_unsafe_metadata(collection_artifact, adapter_patch_artifact)
    owner = failure_owner or str(metadata.get("failure_owner") or default_failure_owner(status, replay_attempted=replay_attempted))
    klass = failure_class or metadata.get("failure_class") or default_failure_class(
        status,
        replay_attempted=replay_attempted,
    )
    metadata.update(
        {
            "batch_tool": TOOL,
            "schema_version": SCHEMA_VERSION,
            "submission_contract": SUBMISSION_CONTRACT,
            "output_contract": SUBMISSION_CONTRACT,
            "mode": mode,
            "model_call_made": model_call_made,
            "failure_owner": owner,
            "failure_class": klass,
            "task_manifest_path": str(task_path),
            "task_manifest_sha256": sha256_file(task_path),
            "acut_manifest_path": str(acut_path),
            "acut_manifest_sha256": sha256_file(acut_path),
            "verifier_digest_sha256": sha256_tree(task_path.parent / "verifier"),
            "candidate_patch_sha256": patch_sha256,
            "candidate_patch_size_bytes": patch_size_bytes,
            "workspace_diff": {
                "contract": SUBMISSION_CONTRACT,
                "collection_command": ["git", "diff", "--binary", "--no-ext-diff", "--unified=0", "HEAD"],
                "candidate_patch_sha256": patch_sha256,
                "candidate_patch_size_bytes": patch_size_bytes,
                "patch_artifact_written": collection_artifact.get("written") is True,
                "patch_ready": patch_ready,
                "untracked_scope": candidate_collection.get("untracked_scope"),
                **unsafe_metadata,
            },
            "patch_readiness": {
                "verifier_ready_patch_available": patch_ready,
                "patch_size_bytes": patch_size_bytes,
                "clean_replay_attempted": replay_attempted,
                "patch_artifact_persisted": patch_persisted,
                "verifier_attempt_channel": "verifier_ready_patch_artifact" if replay_attempted else "not_attempted",
            },
            "clean_patch_replay": {
                "attempted": replay_attempted,
                "status": replay_status,
                "failure_class": replay_failure_class,
                "error": normalized.get("error") if replay_failure_class else None,
                "runner_workspace": str(runner_workspace) if runner_workspace is not None else None,
                "verify_workspace": str(verify_workspace) if verify_workspace is not None else None,
                "separate_workspace": (
                    runner_workspace is not None
                    and verify_workspace is not None
                    and str(runner_workspace) != str(verify_workspace)
                ),
            },
            "verifier_attempt": {
                "attempted": replay_attempted,
                "channel": "verifier_ready_patch_artifact" if replay_attempted else "not_attempted",
                "verifier_ready_patch_artifact": patch_ready,
                "patch_artifact_persisted": patch_persisted,
            },
        }
    )
    normalized["metadata"] = metadata
    write_json(normalized_path, normalized)
    return normalized


def verify_patch(
    *,
    verify_workspace: Path,
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
        str(verify_workspace),
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


def live_preflight_gate(args: argparse.Namespace) -> dict[str, Any]:
    per_task_projected = Decimal(str(sum(3 if acut.startswith("frontier-") else 1 for acut in args.acuts)))
    projected = per_task_projected * Decimal(len(args.tasks))
    return gate_payload(
        ledger_path=Path(args.llm_ledger),
        projected_cost_usd=projected,
        coordinator_decision_ref=args.coordinator_decision_ref,
        acut_id=None,
        split="rwork",
        attempt=args.attempt,
        env=os.environ,
    )


def build_live_adapter_command(
    *,
    args: argparse.Namespace,
    workspace: Path,
    task_id: str,
    acut_id: str,
    run_id: str,
    artifact_dir: Path,
    normalized_path: Path,
) -> list[str]:
    inner_dir = artifact_dir / "inner"
    command = [
        sys.executable,
        str(ACUT_ADAPTER),
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
        str(artifact_dir / "adapter_result.json"),
        "--normalized-output",
        str(normalized_path),
        "--llm-ledger",
        str(args.llm_ledger),
        "--projected-cost-usd",
        "1",
        "--timeout-seconds",
        str(args.runner_timeout_seconds),
    ]
    if args.coordinator_decision_ref:
        command.extend(["--coordinator-decision-ref", args.coordinator_decision_ref])
    command.extend(
        [
            "--",
            sys.executable,
            str(CODEX_CLI_PATCH_COMMAND),
            "--workspace",
            str(workspace),
            "--acut",
            str(acut_manifest_path(acut_id)),
            "--artifact-dir",
            str(inner_dir),
            "--summary-output",
            str(artifact_dir / "codex_cli_patch_command.json"),
            "--codex-timeout-seconds",
            str(args.codex_timeout_seconds),
        ]
    )
    return command


def run_live_adapter(
    *,
    args: argparse.Namespace,
    workspace: Path,
    task_id: str,
    acut_id: str,
    run_id: str,
    artifact_dir: Path,
    normalized_path: Path,
) -> dict[str, Any]:
    command = build_live_adapter_command(
        args=args,
        workspace=workspace,
        task_id=task_id,
        acut_id=acut_id,
        run_id=run_id,
        artifact_dir=artifact_dir,
        normalized_path=normalized_path,
    )
    started_at = iso_now()
    completed = run_capture(command, timeout=args.runner_timeout_seconds + 90)
    finished_at = iso_now()
    command_summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name="workspace_diff_adapter_command",
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    adapter_result = {}
    result_path = artifact_dir / "adapter_result.json"
    if result_path.exists():
        adapter_result = json.loads(result_path.read_text(encoding="utf-8"))
    return {"command": command_summary, "adapter_result": adapter_result, "exit_code": completed.returncode}


def assert_run_id_available(run_id: str, artifact_dir: Path, normalized_path: Path, *, force: bool) -> None:
    if force:
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
        if normalized_path.exists():
            normalized_path.unlink()
        return
    blockers = []
    if artifact_dir.exists() and any(artifact_dir.iterdir()):
        blockers.append("raw_artifact_dir_exists")
    if normalized_path.exists():
        blockers.append("normalized_result_exists")
    if blockers:
        raise ToolError("run id already has artifacts; pass --force to replace", run_id=run_id, blockers=blockers)


def blocked_result_records(args: argparse.Namespace, gate: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = []
    for task_id in args.tasks:
        for acut_id in args.acuts:
            run_id = f"{args.run_prefix}__{acut_id}__{task_id}__attempt{args.attempt}"
            records.append(
                {
                    "run_id": run_id,
                    "task_id": task_id,
                    "acut_id": acut_id,
                    "submission_contract": SUBMISSION_CONTRACT,
                    "status": "blocked",
                    "scoreable": False,
                    "patch_ready": False,
                    "attemptable": False,
                    "failure_owner": "infrastructure",
                    "failure_class": ",".join(str(item) for item in gate.get("blockers", [])) or str(gate.get("status")),
                    "clean_replay_status": "not_attempted",
                    "model_call_made": False,
                    "normalized": {
                        "status": "blocked",
                        "metadata": {
                            "submission_contract": SUBMISSION_CONTRACT,
                            "output_contract": SUBMISSION_CONTRACT,
                            "failure_owner": "infrastructure",
                            "failure_class": ",".join(str(item) for item in gate.get("blockers", [])) or str(gate.get("status")),
                            "model_call_made": False,
                            "patch_readiness": {
                                "verifier_ready_patch_available": False,
                                "clean_replay_attempted": False,
                                "verifier_attempt_channel": "not_attempted",
                            },
                            "clean_patch_replay": {"attempted": False},
                            "verifier_attempt": {"attempted": False, "channel": "not_attempted"},
                        },
                    },
                    "blocker": gate,
                }
            )
    return records


def run_one(args: argparse.Namespace, task_id: str, acut_id: str) -> dict[str, Any]:
    task = load_manifest(task_manifest_path(task_id))
    split = str(task.get("split") or task_split_from_id(task_id))
    run_id = f"{args.run_prefix}__{acut_id}__{task_id}__attempt{args.attempt}"
    artifact_dir = RAW_ROOT / run_id
    normalized_path = NORMALIZED_ROOT / f"{run_id}.json"
    assert_run_id_available(run_id, artifact_dir, normalized_path, force=args.force)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    workspace, prepare_summary = prepare_workspace(task_id, run_id, artifact_dir, summary_name="prepare_workspace")
    context_paths = context_paths_for_task(task, workspace)
    noop_summary = None
    if not args.skip_noop_check:
        noop_workspace, noop_prepare = prepare_workspace(task_id, f"{run_id}__noop", artifact_dir, summary_name="prepare_noop_workspace")
        noop_install = install_workspace(noop_workspace, artifact_dir, args.install_timeout_seconds, name_prefix="noop_")
        noop_summary = {
            "prepare": noop_prepare,
            "install": noop_install,
            "verify": no_op_verify(
                workspace=noop_workspace,
                task_id=task_id,
                acut_id=acut_id,
                attempt=args.attempt,
                run_id=run_id,
                artifact_dir=artifact_dir,
            ),
        }
    patch_path = artifact_dir / "submission.patch"
    model_call_made = args.mode == "live"
    live_adapter_result = None
    synthetic_edit = None
    if args.mode == "synthetic":
        synthetic_edit = apply_synthetic_workspace_edit(workspace, context_paths)
    elif args.mode == "noop":
        pass
    else:
        live_adapter_result = run_live_adapter(
            args=args,
            workspace=workspace,
            task_id=task_id,
            acut_id=acut_id,
            run_id=run_id,
            artifact_dir=artifact_dir,
            normalized_path=normalized_path,
        )

    safe_env, _ = llm_safe_subprocess_env(os.environ)
    candidate_collection = collect_workspace_candidate_patch(workspace, patch_path, safe_env)
    adapter_patch_artifact = adapter_patch_artifact_from_live_result(live_adapter_result)
    patch_ready = bool(candidate_collection["patch_ready"])
    verify_code = None
    verify_workspace = None
    verify_prepare = None
    verify_install = None
    if patch_ready:
        verify_workspace, verify_prepare = prepare_workspace(task_id, f"{run_id}__verify", artifact_dir, summary_name="prepare_verify_workspace")
        verify_install = install_workspace(verify_workspace, artifact_dir, args.install_timeout_seconds, name_prefix="verify_")
        verify_code, normalized = verify_patch(
            verify_workspace=verify_workspace,
            task_id=task_id,
            acut_id=acut_id,
            attempt=args.attempt,
            run_id=run_id,
            artifact_dir=artifact_dir,
            normalized_path=normalized_path,
        )
        normalized = enrich_normalized_metadata(
            normalized=normalized,
            normalized_path=normalized_path,
            task_id=task_id,
            acut_id=acut_id,
            runner_workspace=workspace,
            verify_workspace=verify_workspace,
            patch_path=patch_path,
            candidate_collection=candidate_collection,
            mode=args.mode,
            model_call_made=model_call_made,
            clean_replay_invoked=verify_code is not None,
            adapter_patch_artifact=adapter_patch_artifact,
        )
    else:
        status = "invalid_submission"
        failure_owner = str(candidate_collection["failure_owner"])
        failure_class = str(candidate_collection["failure_class"])
        if args.mode == "live" and live_adapter_result:
            adapter = live_adapter_result.get("adapter_result")
            if isinstance(adapter, Mapping):
                inner = adapter.get("inner_patch_command") if isinstance(adapter.get("inner_patch_command"), Mapping) else {}
                if isinstance(inner.get("failure_class"), str) and inner["failure_class"]:
                    failure_class = str(inner["failure_class"])
                    failure_owner = "model_output"
                if adapter.get("status") in {"gate_blocked", "gate_requires_coordinator_approval"}:
                    status = "infra_failed"
                    failure_owner = "infrastructure"
                    failure_class = str(adapter.get("status"))
        normalized = write_normalized_result(
            normalized_path=normalized_path,
            run_id=run_id,
            acut_id=acut_id,
            task_id=task_id,
            split=split,
            attempt=args.attempt,
            status=status,
            patch_path=patch_path,
            started_at=iso_now(),
            finished_at=iso_now(),
            error="workspace diff did not produce a verifier-ready source patch",
            metadata={},
        )
        normalized = enrich_normalized_metadata(
            normalized=normalized,
            normalized_path=normalized_path,
            task_id=task_id,
            acut_id=acut_id,
            runner_workspace=workspace,
            verify_workspace=None,
            patch_path=patch_path,
            candidate_collection=candidate_collection,
            mode=args.mode,
            model_call_made=model_call_made,
            clean_replay_invoked=verify_code is not None,
            adapter_patch_artifact=adapter_patch_artifact,
            failure_owner=failure_owner,
            failure_class=failure_class,
        )

    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
    status = str(normalized.get("status"))
    attemptable = bool(metadata.get("verifier_attempt", {}).get("attempted")) if isinstance(metadata.get("verifier_attempt"), Mapping) else False
    clean_replay = metadata.get("clean_patch_replay") if isinstance(metadata.get("clean_patch_replay"), Mapping) else {}
    clean_replay_status = str(clean_replay.get("status") or "not_attempted")
    result = {
        "run_id": run_id,
        "task_id": task_id,
        "acut_id": acut_id,
        "submission_contract": SUBMISSION_CONTRACT,
        "status": status,
        "scoreable": status in SCOREABLE_STATUSES,
        "patch_ready": patch_ready,
        "attemptable": attemptable,
        "failure_owner": metadata.get("failure_owner"),
        "failure_class": metadata.get("failure_class"),
        "clean_replay_status": clean_replay_status,
        "model_call_made": model_call_made,
        "artifact_dir": str(artifact_dir),
        "workspace": str(workspace),
        "runner_workspace": str(workspace),
        "verify_workspace": str(verify_workspace) if verify_workspace is not None else None,
        "normalized_result": str(normalized_path),
        "patch_path": str(patch_path),
        "candidate_patch_sha256": metadata.get("candidate_patch_sha256"),
        "candidate_patch_size_bytes": metadata.get("candidate_patch_size_bytes"),
        "task_manifest_sha256": metadata.get("task_manifest_sha256"),
        "acut_manifest_sha256": metadata.get("acut_manifest_sha256"),
        "verifier_digest_sha256": metadata.get("verifier_digest_sha256"),
        "duration_seconds": round(time.monotonic() - started, 3),
        "prepare": prepare_summary,
        "context_paths": context_paths,
        "synthetic_edit": synthetic_edit,
        "noop": noop_summary,
        "candidate_collection": candidate_collection,
        "live_adapter": live_adapter_result,
        "verify_prepare": verify_prepare,
        "verify_install": verify_install,
        "verify_code": verify_code,
        "normalized": normalized,
    }
    write_json(artifact_dir / "batch_run_result.json", result)
    return result


def count_by(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def gate_for_summary(summary: Mapping[str, Any], *, blocked: bool) -> dict[str, Any]:
    attemptability = summary.get("attemptability_score")
    invalid = summary.get("invalid_submission_rate")
    disagreements = int(summary.get("clean_replay_disagreement_count") or 0)
    attemptable_pass = isinstance(attemptability, (int, float)) and float(attemptability) >= PATCH_READY_THRESHOLD
    invalid_pass = isinstance(invalid, (int, float)) and float(invalid) <= INVALID_RATE_THRESHOLD
    replay_pass = disagreements == 0
    if blocked:
        status = "blocked"
    elif attemptable_pass and invalid_pass and replay_pass:
        status = "passed"
    else:
        status = "failed"
    return {
        "status": status,
        "thresholds": {
            "patch_ready_or_verifier_attemptable_min": PATCH_READY_THRESHOLD,
            "invalid_submission_rate_max": INVALID_RATE_THRESHOLD,
            "clean_replay_disagreement_count_max": 0,
        },
        "checks": {
            "patch_ready_or_verifier_attemptable": attemptable_pass,
            "invalid_submission_rate": invalid_pass,
            "clean_replay_disagreement_count": replay_pass,
            "complete_fixed_denominator": int(summary.get("total") or 0) == int(summary.get("fixed_denominator") or 0),
        },
    }


def summarize_results(results: Sequence[Mapping[str, Any]], *, fixed_denominator: int, blocked: bool) -> dict[str, Any]:
    total = len(results)
    invalid = sum(1 for result in results if result.get("status") == "invalid_submission")
    attemptable = sum(1 for result in results if result.get("attemptable") is True or result.get("patch_ready") is True)
    patch_ready = sum(1 for result in results if result.get("patch_ready") is True)
    clean_replay_success = sum(1 for result in results if result.get("clean_replay_status") == "success")
    disagreements = [
        {"acut_id": result.get("acut_id"), "task_id": result.get("task_id"), "status": result.get("status")}
        for result in results
        if result.get("patch_ready") is True and result.get("clean_replay_status") != "success"
    ]
    summary = {
        "fixed_denominator": fixed_denominator,
        "total": total,
        "status_counts": count_by(results, "status"),
        "failure_owner_counts": count_by(results, "failure_owner"),
        "failure_class_counts": count_by(results, "failure_class"),
        "invalid_submission_count": invalid,
        "invalid_submission_rate": rate(invalid, total),
        "patch_ready_count": patch_ready,
        "patch_ready_coverage": rate(patch_ready, total),
        "attemptable_count": attemptable,
        "attemptability_score": rate(attemptable, total),
        "clean_replay_success_count": clean_replay_success,
        "clean_replay_success_rate": rate(clean_replay_success, total),
        "clean_replay_disagreement_count": len(disagreements),
        "clean_replay_disagreement_cells": disagreements,
        "digest_fields_present": {
            "candidate_patch_sha256": all(bool(result.get("candidate_patch_sha256")) for result in results if result.get("patch_ready")),
            "task_manifest_sha256": all(bool(result.get("task_manifest_sha256")) for result in results),
            "acut_manifest_sha256": all(bool(result.get("acut_manifest_sha256")) for result in results),
            "verifier_digest_sha256": all(bool(result.get("verifier_digest_sha256")) for result in results),
        },
    }
    summary["gate"] = gate_for_summary(summary, blocked=blocked)
    return summary


def report_markdown(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    gate = summary.get("gate") if isinstance(summary.get("gate"), Mapping) else {}
    blocker = payload.get("live_blocker") if isinstance(payload.get("live_blocker"), Mapping) else None
    blocker_text = ""
    if blocker is not None:
        blocker_text = f"\nLive blocker: `{blocker.get('status')}` with blockers `{blocker.get('blockers')}`.\n"
    rerun_note = payload.get("rerun_note")
    rerun_note_text = f"\n{rerun_note}\n" if rerun_note else ""
    return f"""# M2.5 Workspace-Diff-v1 Scoreability Recovery

Date: 2026-05-10

## Scope

This artifact evaluates `workspace-diff-v1`: the ACUT edits an isolated prepared task workspace, the runner extracts `git diff --binary`, and the clean-room verifier consumes that diff through the existing replay path.

Mode: `{payload.get("mode")}`. Fixed denominator: `{payload.get("fixed_denominator")}` cells (`2 ACUT x 3 RWork` for the live path unless blocked).{blocker_text}

## Results

- Status counts: `{summary.get("status_counts")}`
- Failure owners: `{summary.get("failure_owner_counts")}`
- Failure classes: `{summary.get("failure_class_counts")}`
- Attemptability score: `{summary.get("attemptability_score")}`
- Invalid submission rate: `{summary.get("invalid_submission_rate")}`
- Clean replay disagreements: `{summary.get("clean_replay_disagreement_count")}`
- Gate status: `{gate.get("status")}`

## Claim Boundary

This is measurement recovery evidence only. It does not claim task-solving improvement, capability uplift, ranking reversal, G_score predictivity, license, admission, or authorization.

## Reproduction
{rerun_note_text}
Exact delivered command:

```bash
{payload.get("reproduction_command")}
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def reproduction_command(args: argparse.Namespace) -> str:
    command = [
        "PYTHONPATH=experiments/core_narrative/tools",
        "python3",
        "experiments/core_narrative/tools/m2_5_workspace_diff_runner.py",
        "--mode",
        str(args.mode),
        "--run-prefix",
        str(args.run_prefix),
        "--output",
        str(args.output),
        "--report",
        str(args.report),
    ]
    if args.skip_noop_check:
        command.append("--skip-noop-check")
    if args.force:
        command.append("--force")
    if args.attempt != 1:
        command.extend(["--attempt", str(args.attempt)])
    if args.llm_ledger != str(DEFAULT_LEDGER_PATH):
        command.extend(["--llm-ledger", str(args.llm_ledger)])
    if args.install_timeout_seconds != 240:
        command.extend(["--install-timeout-seconds", str(args.install_timeout_seconds)])
    if args.runner_timeout_seconds != 900:
        command.extend(["--runner-timeout-seconds", str(args.runner_timeout_seconds)])
    if args.codex_timeout_seconds != 900:
        command.extend(["--codex-timeout-seconds", str(args.codex_timeout_seconds)])
    if args.coordinator_decision_ref:
        command.extend(["--coordinator-decision-ref", str(args.coordinator_decision_ref)])
    return " \\\n  ".join(shlex.quote(part) for part in command)


def build_payload(args: argparse.Namespace, results: Sequence[Mapping[str, Any]], *, live_gate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    fixed_denominator = len(args.tasks) * len(args.acuts)
    blocked = live_gate is not None and live_gate.get("status") != "passed"
    summary = summarize_results(results, fixed_denominator=fixed_denominator, blocked=blocked)
    digest_material = {
        "schema_version": SCHEMA_VERSION,
        "submission_contract": SUBMISSION_CONTRACT,
        "mode": args.mode,
        "tasks": list(args.tasks),
        "acuts": list(args.acuts),
        "results": [
            {
                key: result.get(key)
                for key in (
                    "run_id",
                    "acut_id",
                    "task_id",
                    "status",
                    "patch_ready",
                    "attemptable",
                    "failure_owner",
                    "failure_class",
                    "candidate_patch_sha256",
                    "task_manifest_sha256",
                    "acut_manifest_sha256",
                    "verifier_digest_sha256",
                )
            }
            for result in results
        ],
    }
    return {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked" if blocked else "completed",
        "generated_at": iso_now(),
        "mode": args.mode,
        "submission_contract": SUBMISSION_CONTRACT,
        "run_prefix": args.run_prefix,
        "tasks": list(args.tasks),
        "acuts": list(args.acuts),
        "attempt": args.attempt,
        "fixed_denominator": fixed_denominator,
        "success_criteria": {
            "patch_ready_or_verifier_attemptable_min": PATCH_READY_THRESHOLD,
            "invalid_submission_rate_max": INVALID_RATE_THRESHOLD,
            "clean_replay_disagreement_count_max": 0,
        },
        "summary": summary,
        "results": list(results),
        "live_blocker": live_gate if blocked else None,
        "score_input_set_digest": digest_payload(digest_material),
        "claim_status": "blocked" if blocked else summary["gate"]["status"],
        "reproduction_command": reproduction_command(args),
        "rerun_note": (
            "Live reruns are budget/env-gated and may spend live model budget; "
            "the command below is the exact delivered command, but rerunning it still requires the configured gates to pass."
            if args.mode == "live"
            else None
        ),
        "prohibited_claims": {
            "capability_uplift": False,
            "task_solving_improvement": False,
            "ranking_reversal": False,
            "g_score_predictivity": False,
            "license_or_admission_output": False,
        },
        "output_path_hint": str(args.output),
        "report_path_hint": str(args.report),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        if tuple(args.tasks) != DEFAULT_TASKS or tuple(args.acuts) != DEFAULT_ACUTS:
            raise ToolError(
                "M2.5 denominator is fixed at 2 ACUT x 3 RWork for this milestone",
                expected_tasks=list(DEFAULT_TASKS),
                expected_acuts=list(DEFAULT_ACUTS),
                observed_tasks=list(args.tasks),
                observed_acuts=list(args.acuts),
            )
        live_gate = live_preflight_gate(args) if args.mode == "live" else None
        if live_gate is not None and live_gate.get("status") != "passed":
            results = blocked_result_records(args, live_gate)
        else:
            results = [run_one(args, task_id, acut_id) for task_id in args.tasks for acut_id in args.acuts]
        payload = build_payload(args, results, live_gate=live_gate)
        if args.report:
            write_report(args.report, payload)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
