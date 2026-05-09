#!/usr/bin/env python3
"""Run a compact Codex-owned Barcarolle core-narrative experiment slice."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
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
TASK_SPLIT_MANIFESTS = {
    "rbench": TASK_SPLIT,
    "rwork": REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click.yaml",
}
TASK_PACK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces"
RAW_ROOT = REPO_ROOT / "experiments/core_narrative/results/raw"
NORMALIZED_ROOT = REPO_ROOT / "experiments/core_narrative/results/normalized"
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
DIRECT_RUNNER = REPO_ROOT / "experiments/core_narrative/tools/codex_nfl_direct_runner.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_RUN_PREFIX = "codex_nfl_20260508"
SCOREABLE_STATUSES = {"passed", "failed", "timeout", "invalid_submission"}
DEFAULT_SUBMISSION_CONTRACT = "anchored-search-replace-json-v3"
STRUCTURED_FILES_SUBMISSION_CONTRACT = "structured-files-json-v1"
PATCH_OR_FILES_SUBMISSION_CONTRACT = "patch-or-files-v1"
SUBMISSION_CONTRACTS = (
    DEFAULT_SUBMISSION_CONTRACT,
    STRUCTURED_FILES_SUBMISSION_CONTRACT,
    PATCH_OR_FILES_SUBMISSION_CONTRACT,
)
MODEL_OUTPUT_FAILURE_CLASSES = {
    "generated_path_not_in_workspace",
    "generated_path_outside_context",
    "search_replace_anchor_invalid",
    "search_replace_anchor_mismatch",
    "search_replace_old_occurrence_mismatch",
    "output_contract_violation",
    "apply_patch_context_mismatch",
    "apply_patch_invalid",
    "invalid_unified_diff",
    "unsupported_patch_response",
    "structured_files_invalid",
    "unsafe_generated_text",
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument(
        "--task-split",
        choices=sorted(TASK_SPLIT_MANIFESTS),
        default="rbench",
        help="Click task split manifest and task-pack root to use.",
    )
    parser.add_argument(
        "--task-split-manifest",
        help="Optional explicit task split manifest path; defaults from --task-split.",
    )
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--acuts", nargs="+", required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--mode", choices=("live", "mock", "dry-run"), default="live")
    parser.add_argument("--mock-response")
    parser.add_argument("--mock-response-text")
    parser.add_argument(
        "--submission-contract",
        choices=SUBMISSION_CONTRACTS,
        default=DEFAULT_SUBMISSION_CONTRACT,
        help="Submission/output contract used by the direct runner.",
    )
    parser.add_argument("--llm-ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument(
        "--coordinator-decision-ref",
        help="Structured approval reference forwarded to live runner budget gates.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--runner-timeout-seconds", type=int, default=360)
    parser.add_argument("--max-context-chars", type=int, help="Forwarded to the direct runner.")
    parser.add_argument("--max-file-chars", type=int, help="Forwarded to the direct runner.")
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


def split_from_task_id(task_id: str) -> str:
    if "__rwork__" in task_id:
        return "rwork"
    if "__rbench__" in task_id:
        return "rbench"
    raise ToolError("task id does not encode a supported Click split", task_id=task_id)


def task_split_manifest_path(split: str) -> Path:
    key = split.lower()
    if key not in TASK_SPLIT_MANIFESTS:
        raise ToolError("unsupported Click task split", split=split, supported=sorted(TASK_SPLIT_MANIFESTS))
    return TASK_SPLIT_MANIFESTS[key]


def task_manifest_path(task_id: str, split: str | None = None) -> Path:
    split_key = (split or split_from_task_id(task_id)).lower()
    path = TASK_PACK_ROOT / "click" / split_key / task_id / "task.yaml"
    if not path.exists():
        raise ToolError(
            "materialized task pack does not exist; run materialize_task_pack.py first",
            task_id=task_id,
            split=split_key,
            path=str(path),
        )
    return path


def acut_manifest_path(acut_id: str) -> Path:
    path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
    if not path.exists():
        raise ToolError("ACUT manifest does not exist", acut_id=acut_id, path=str(path))
    return path


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
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((sha256_file(path) or "").encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def context_pack_digest(acut_id: str) -> str | None:
    acut = load_manifest(acut_manifest_path(acut_id))
    metadata = acut.get("metadata") if isinstance(acut.get("metadata"), dict) else {}
    specialist = metadata.get("specialist_context") if isinstance(metadata.get("specialist_context"), dict) else {}
    pack = specialist.get("context_pack") if isinstance(specialist.get("context_pack"), dict) else {}
    digest = pack.get("pack_hash")
    return str(digest) if isinstance(digest, str) and digest else None


def ledger_has_run_id(path: Path, run_id: str) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("run_id") == run_id:
            return True
    return False


def path_has_entries(path: Path) -> bool:
    return path.exists() and any(path.iterdir()) if path.is_dir() else path.exists()


def assert_run_id_available(*, run_id: str, artifact_dir: Path, normalized_path: Path, ledger_path: Path) -> None:
    blockers: list[str] = []
    if path_has_entries(artifact_dir):
        blockers.append("raw_artifact_dir_exists")
    if normalized_path.exists():
        blockers.append("normalized_result_exists")
    if ledger_has_run_id(ledger_path, run_id):
        blockers.append("ledger_run_id_exists")
    if blockers:
        raise ToolError("run id already has artifacts; refusing to overwrite by default", run_id=run_id, blockers=blockers)


def projected_cost_for_acut(acut_id: str) -> str:
    return "3" if acut_id.startswith("frontier-") else "1"


def default_mock_response_text(
    workspace: Path,
    context_paths: Sequence[str],
    *,
    submission_contract: str = DEFAULT_SUBMISSION_CONTRACT,
) -> str:
    for context_path in context_paths:
        path = Path(context_path)
        if path.is_absolute() or ".." in path.parts:
            continue
        target = workspace / path
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8")
        if submission_contract == STRUCTURED_FILES_SUBMISSION_CONTRACT:
            if text:
                return json.dumps({"files": [{"path": context_path, "action": "replace", "content": text}]})
            continue
        if submission_contract == PATCH_OR_FILES_SUBMISSION_CONTRACT:
            if text:
                addition = "# barcarolle no-model scoreability baseline\n"
                new_text = text if text.endswith("\n") else text + "\n"
                new_text = new_text + addition
                patch = "".join(
                    difflib.unified_diff(
                        text.splitlines(keepends=True),
                        new_text.splitlines(keepends=True),
                        fromfile=f"a/{context_path}",
                        tofile=f"b/{context_path}",
                    )
                )
                return json.dumps({"unified_diff": patch})
            continue
        for candidate in text.splitlines(keepends=True):
            if candidate.strip() and text.count(candidate) == 1:
                return json.dumps(
                    {"edits": [{"path": context_path, "old": candidate, "new": candidate}]}
                )
        if text:
            return json.dumps({"edits": [{"path": context_path, "old": text, "new": text}]})
    raise ToolError(
        "mock mode needs at least one non-empty context file when no mock response is provided",
        failure_class="empty_mock_context",
    )


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


def prepare_workspace(
    task_id: str,
    workspace_name: str,
    artifact_dir: Path,
    *,
    summary_name: str = "prepare_workspace",
) -> tuple[Path, dict[str, Any]]:
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


def install_workspace(
    workspace: Path,
    artifact_dir: Path,
    timeout_seconds: int,
    *,
    name_prefix: str = "",
) -> dict[str, Any]:
    uv = shutil.which("uv")
    uv_venv_create_attempt: dict[str, Any] | None = None
    if uv:
        command = [uv, "venv", "--python", "3.12", ".venv"]
        started_at = iso_now()
        completed = run_capture(command, cwd=workspace, timeout=timeout_seconds)
        finished_at = iso_now()
        uv_venv_create_attempt = write_command_artifacts(
            completed=completed,
            artifact_dir=artifact_dir,
            name=f"{name_prefix}venv_create",
            command=command,
            started_at=started_at,
            finished_at=finished_at,
        )
        if completed.returncode == 0:
            install = [uv, "pip", "install", "--python", ".venv/bin/python", "-q", "-e", ".", "pytest"]
            started_at = iso_now()
            completed = run_capture(install, cwd=workspace, timeout=timeout_seconds)
            finished_at = iso_now()
            install_summary = write_command_artifacts(
                completed=completed,
                artifact_dir=artifact_dir,
                name=f"{name_prefix}venv_install",
                command=install,
                started_at=started_at,
                finished_at=finished_at,
            )
            install_summary["venv_backend"] = "uv"
            if completed.returncode != 0:
                raise ToolError("workspace dependency install failed", summary=install_summary)
            return install_summary

    if uv_venv_create_attempt is not None:
        venv_create_name = f"{name_prefix}venv_create_fallback"
    else:
        venv_create_name = f"{name_prefix}venv_create"
    if (workspace / ".venv").exists():
        shutil.rmtree(workspace / ".venv")
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
        name=venv_create_name,
        command=command,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        if uv_venv_create_attempt is not None:
            raise ToolError(
                "workspace venv creation failed",
                summary=summary,
                uv_venv_create_attempt=uv_venv_create_attempt,
            )
        raise ToolError("workspace venv creation failed", summary=summary)

    upgrade_pip = [".venv/bin/python", "-m", "pip", "install", "-q", "--upgrade", "pip"]
    started_at = iso_now()
    completed = run_capture(upgrade_pip, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    upgrade_summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_pip_upgrade",
        command=upgrade_pip,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace pip upgrade failed", summary=upgrade_summary)

    install = [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"]
    started_at = iso_now()
    completed = run_capture(install, cwd=workspace, timeout=timeout_seconds)
    finished_at = iso_now()
    summary = write_command_artifacts(
        completed=completed,
        artifact_dir=artifact_dir,
        name=f"{name_prefix}venv_install",
        command=install,
        started_at=started_at,
        finished_at=finished_at,
    )
    if completed.returncode != 0:
        raise ToolError("workspace dependency install failed", summary=summary)
    summary["venv_backend"] = "python_venv"
    summary["pip_upgrade"] = upgrade_summary
    if uv_venv_create_attempt is not None:
        summary["uv_venv_create_attempt"] = uv_venv_create_attempt
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
    if getattr(args, "max_context_chars", None) is not None:
        command.extend(["--max-context-chars", str(args.max_context_chars)])
    if getattr(args, "max_file_chars", None) is not None:
        command.extend(["--max-file-chars", str(args.max_file_chars)])
    submission_contract = getattr(args, "submission_contract", DEFAULT_SUBMISSION_CONTRACT)
    command.extend(["--output-contract", str(submission_contract)])
    if args.mode == "dry-run":
        command.append("--dry-run")
    elif args.mode == "mock":
        if args.mock_response:
            command.extend(["--mock-response", args.mock_response])
        else:
            command.extend(
                [
                    "--mock-response-text",
                    args.mock_response_text
                    or default_mock_response_text(
                        workspace,
                        context_paths,
                        submission_contract=str(submission_contract),
                    ),
                ]
            )
    coordinator_decision_ref = getattr(args, "coordinator_decision_ref", None)
    if coordinator_decision_ref:
        command.extend(["--coordinator-decision-ref", coordinator_decision_ref])

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
    result.setdefault("submission_contract", submission_contract)
    result.setdefault("output_contract", submission_contract)
    result["selected_context_paths"] = list(context_paths)
    result["task_visible_context_guidance"] = task.get("visible_context_guidance")
    return completed.returncode, result


def submission_contract_from_runner_result(runner_result: Mapping[str, Any] | None) -> str:
    if isinstance(runner_result, Mapping):
        for key in ("submission_contract", "output_contract"):
            value = runner_result.get(key)
            if isinstance(value, str) and value:
                return value
    return DEFAULT_SUBMISSION_CONTRACT


def failure_owner_for_status(status: object, metadata: Mapping[str, Any], runner_result: Mapping[str, Any] | None) -> str:
    existing = metadata.get("failure_owner")
    if isinstance(existing, str) and existing:
        return existing
    status_text = str(status)
    if status_text == "passed":
        return "none"
    if status_text == "invalid_submission":
        return "model_output"
    if status_text in {"failed", "timeout"}:
        return "candidate_patch"
    if status_text == "infra_failed":
        return "infrastructure"
    if isinstance(runner_result, Mapping) and runner_result.get("status") == "error":
        return "infrastructure"
    return "unknown"


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
    details = runner_result.get("details") if isinstance(runner_result.get("details"), dict) else {}
    failure_class = details.get("failure_class")
    status = "invalid_submission" if failure_class in MODEL_OUTPUT_FAILURE_CLASSES else "infra_failed"
    payload = {
        "schema_version": "core-narrative.run-result.v1",
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "started_at": runner_result.get("started_at"),
        "finished_at": runner_result.get("finished_at"),
        "status": status,
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
            "submission_contract": submission_contract_from_runner_result(runner_result),
            "model_call_made": runner_result.get("model_call_made"),
            "failure_class": failure_class,
            "failure_owner": "model_output" if status == "invalid_submission" else "infrastructure",
            "verifier_ready_patch_available": False,
            "patch_readiness": {
                "verifier_ready_patch_available": False,
                "patch_size_bytes": 0,
                "clean_replay_attempted": False,
            },
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


def enrich_normalized_metadata(
    *,
    normalized: dict[str, Any],
    normalized_path: Path,
    task_id: str,
    acut_id: str,
    runner_result: Mapping[str, Any] | None,
    runner_workspace: Path | None,
    verify_workspace: Path | None,
    clean_patch_replay_attempted: bool,
) -> dict[str, Any]:
    task_path = task_manifest_path(task_id)
    acut_path = acut_manifest_path(acut_id)
    prompt_snapshot = runner_result.get("prompt_snapshot") if isinstance(runner_result, Mapping) else None
    prompt_snapshot_path = Path(str(prompt_snapshot)) if isinstance(prompt_snapshot, str) else None
    raw_response_artifact = runner_result.get("raw_response_artifact") if isinstance(runner_result, Mapping) else None
    cost_accounting = runner_result.get("cost_accounting") if isinstance(runner_result, Mapping) else None
    cost_ledger_append = runner_result.get("cost_ledger_append") if isinstance(runner_result, Mapping) else None
    budget_gate = runner_result.get("budget_gate") if isinstance(runner_result, Mapping) else None
    runner_model_call_made = runner_result.get("model_call_made") if isinstance(runner_result, Mapping) else None
    patch_artifact = runner_result.get("patch_artifact") if isinstance(runner_result, Mapping) else None
    patch_size_bytes = patch_artifact.get("size_bytes") if isinstance(patch_artifact, Mapping) else None
    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
    model_call_made = metadata.get("model_call_made")
    if model_call_made is None:
        model_call_made = runner_model_call_made
    submission_contract = submission_contract_from_runner_result(runner_result)
    enriched = {
        **metadata,
        "batch_tool": TOOL,
        "runner_id": RUNNER_ID,
        "direct_runner_id": runner_result.get("runner_id") if isinstance(runner_result, Mapping) else None,
        "submission_contract": submission_contract,
        "model_call_made": model_call_made,
        "failure_owner": failure_owner_for_status(normalized.get("status"), metadata, runner_result),
        "task_manifest_path": str(task_path),
        "task_manifest_sha256": sha256_file(task_path),
        "acut_manifest_path": str(acut_path),
        "acut_manifest_sha256": sha256_file(acut_path),
        "verifier_digest_sha256": sha256_tree(task_path.parent / "verifier"),
        "prompt_snapshot": str(prompt_snapshot_path) if prompt_snapshot_path is not None else None,
        "prompt_snapshot_sha256": sha256_file(prompt_snapshot_path) if prompt_snapshot_path is not None else None,
        "raw_response_artifact": str(raw_response_artifact) if isinstance(raw_response_artifact, str) else metadata.get("raw_response_artifact"),
        "direct_runner_cost_accounting": cost_accounting if isinstance(cost_accounting, Mapping) else metadata.get("direct_runner_cost_accounting"),
        "direct_runner_cost_ledger_append": cost_ledger_append if isinstance(cost_ledger_append, Mapping) else metadata.get("direct_runner_cost_ledger_append"),
        "direct_runner_budget_gate": budget_gate if isinstance(budget_gate, Mapping) else metadata.get("direct_runner_budget_gate"),
        "context_pack_digest": context_pack_digest(acut_id),
        "patch_readiness": {
            "verifier_ready_patch_available": clean_patch_replay_attempted,
            "patch_size_bytes": patch_size_bytes if isinstance(patch_size_bytes, int) else None,
            "clean_replay_attempted": clean_patch_replay_attempted,
        },
        "clean_patch_replay": {
            "attempted": clean_patch_replay_attempted,
            "skip_apply": metadata.get("skip_apply"),
            "runner_workspace": str(runner_workspace) if runner_workspace is not None else None,
            "verify_workspace": str(verify_workspace) if verify_workspace is not None else None,
            "separate_workspace": (
                runner_workspace is not None
                and verify_workspace is not None
                and str(runner_workspace) != str(verify_workspace)
            ),
        },
    }
    normalized["metadata"] = enriched
    write_json(normalized_path, normalized)
    return normalized


def run_one(args: argparse.Namespace, task: Mapping[str, Any], acut_id: str) -> dict[str, Any]:
    task_id = str(task["task_id"])
    run_id = f"{args.run_prefix}__{acut_id}__{task_id}__attempt{args.attempt}"
    artifact_dir = RAW_ROOT / run_id
    normalized_path = NORMALIZED_ROOT / f"{run_id}.json"
    assert_run_id_available(
        run_id=run_id,
        artifact_dir=artifact_dir,
        normalized_path=normalized_path,
        ledger_path=Path(getattr(args, "llm_ledger", DEFAULT_LEDGER_PATH)),
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    workspace, prepare_summary = prepare_workspace(task_id, run_id, artifact_dir)
    install_summary = install_workspace(workspace, artifact_dir, args.install_timeout_seconds)
    context_paths = context_paths_for_task(task, workspace)
    noop_summary = None
    noop_workspace = None
    noop_prepare_summary = None
    noop_install_summary = None
    if not args.skip_noop_check:
        noop_workspace, noop_prepare_summary = prepare_workspace(
            task_id,
            run_id + "__noop",
            artifact_dir,
            summary_name="prepare_noop_workspace",
        )
        noop_install_summary = install_workspace(
            noop_workspace,
            artifact_dir,
            args.install_timeout_seconds,
            name_prefix="noop_",
        )
        noop_summary = no_op_verify(
            workspace=noop_workspace,
            task_id=task_id,
            acut_id=acut_id,
            attempt=args.attempt,
            run_id=run_id,
            artifact_dir=artifact_dir,
        )
        noop_result = noop_summary.get("result") if isinstance(noop_summary, dict) else {}
        if isinstance(noop_result, dict) and noop_result.get("status") == "passed":
            patch_path = artifact_dir / "submission.patch"
            normalized = write_infra_failed_result(
                run_id=run_id,
                task_id=task_id,
                split=str(task["split"]),
                acut_id=acut_id,
                attempt=args.attempt,
                normalized_path=normalized_path,
                patch_path=patch_path,
                runner_result={
                    "status": "noop_verifier_passed",
                    "error": "no-op verifier passed before applying an ACUT patch",
                    "details": {"failure_class": "noop_verifier_passed"},
                    "model_call_made": False,
                    "started_at": noop_result.get("started_at"),
                    "finished_at": noop_result.get("finished_at"),
                },
            )
            normalized = enrich_normalized_metadata(
                normalized=normalized,
                normalized_path=normalized_path,
                task_id=task_id,
                acut_id=acut_id,
                runner_result=None,
                runner_workspace=workspace,
                verify_workspace=None,
                clean_patch_replay_attempted=False,
            )
            result = {
                "run_id": run_id,
                "task_id": task_id,
                "acut_id": acut_id,
                "submission_contract": getattr(args, "submission_contract", DEFAULT_SUBMISSION_CONTRACT),
                "status": "infra_failed",
                "scoreable": False,
                "patch_ready": False,
                "runner_status": "noop_verifier_passed",
                "runner_code": None,
                "verify_code": None,
                "artifact_dir": str(artifact_dir),
                "workspace": str(workspace),
                "runner_workspace": str(workspace),
                "verify_workspace": None,
                "noop_workspace": str(noop_workspace),
                "normalized_result": str(normalized_path),
                "patch_path": str(patch_path),
                "prompt_snapshot": None,
                "raw_response_artifact": None,
                "context_paths": context_paths,
                "duration_seconds": round(time.monotonic() - started, 3),
                "prepare": prepare_summary,
                "install": install_summary,
                "noop_prepare": noop_prepare_summary,
                "noop_install": noop_install_summary,
                "verify_prepare": None,
                "verify_install": None,
                "noop": noop_summary,
                "runner_result": None,
                "normalized": normalized,
            }
            write_json(artifact_dir / "batch_run_result.json", result)
            return result
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
    verify_workspace = None
    verify_prepare_summary = None
    verify_install_summary = None
    if patch_ready:
        verify_workspace, verify_prepare_summary = prepare_workspace(
            task_id,
            run_id + "__verify",
            artifact_dir,
            summary_name="prepare_verify_workspace",
        )
        verify_install_summary = install_workspace(
            verify_workspace,
            artifact_dir,
            args.install_timeout_seconds,
            name_prefix="verify_",
        )
        verify_code, normalized = verify_patch(
            workspace=verify_workspace,
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
            runner_result=runner_result,
            runner_workspace=workspace,
            verify_workspace=verify_workspace,
            clean_patch_replay_attempted=True,
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
        normalized = enrich_normalized_metadata(
            normalized=normalized,
            normalized_path=normalized_path,
            task_id=task_id,
            acut_id=acut_id,
            runner_result=runner_result,
            runner_workspace=workspace,
            verify_workspace=None,
            clean_patch_replay_attempted=False,
        )

    result = {
        "run_id": run_id,
        "task_id": task_id,
        "acut_id": acut_id,
        "submission_contract": submission_contract_from_runner_result(runner_result),
        "status": normalized.get("status"),
        "scoreable": normalized.get("status") in SCOREABLE_STATUSES,
        "patch_ready": patch_ready,
        "runner_status": runner_result.get("status"),
        "runner_code": runner_code,
        "verify_code": verify_code,
        "artifact_dir": str(artifact_dir),
        "workspace": str(workspace),
        "runner_workspace": str(workspace),
        "verify_workspace": str(verify_workspace) if verify_workspace is not None else None,
        "noop_workspace": str(noop_workspace) if noop_workspace is not None else None,
        "normalized_result": str(normalized_path),
        "patch_path": str(patch_path),
        "prompt_snapshot": runner_result.get("prompt_snapshot"),
        "raw_response_artifact": runner_result.get("raw_response_artifact"),
        "context_paths": context_paths,
        "duration_seconds": round(time.monotonic() - started, 3),
        "prepare": prepare_summary,
        "install": install_summary,
        "noop_prepare": noop_prepare_summary,
        "noop_install": noop_install_summary,
        "verify_prepare": verify_prepare_summary,
        "verify_install": verify_install_summary,
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
    by_contract: dict[str, dict[str, int]] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
        acut = str(result.get("acut_id"))
        task = str(result.get("task_id"))
        contract = str(result.get("submission_contract") or DEFAULT_SUBMISSION_CONTRACT)
        by_acut.setdefault(acut, {})[status] = by_acut.setdefault(acut, {}).get(status, 0) + 1
        by_task.setdefault(task, {})[status] = by_task.setdefault(task, {}).get(status, 0) + 1
        by_contract.setdefault(contract, {})[status] = by_contract.setdefault(contract, {}).get(status, 0) + 1
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
        "by_contract": by_contract,
    }


def started_at_for_batch(results: Sequence[Mapping[str, Any]]) -> str | None:
    for result in results:
        runner_result = result.get("runner_result")
        if isinstance(runner_result, Mapping) and isinstance(runner_result.get("started_at"), str):
            return str(runner_result["started_at"])
        noop = result.get("noop")
        noop_result = noop.get("result") if isinstance(noop, Mapping) else None
        if isinstance(noop_result, Mapping) and isinstance(noop_result.get("started_at"), str):
            return str(noop_result["started_at"])
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        task_split = str(args.task_split).lower()
        split_manifest_path = Path(args.task_split_manifest) if args.task_split_manifest else task_split_manifest_path(task_split)
        split_manifest = load_manifest(split_manifest_path)
        manifest_split = str(split_manifest.get("split", task_split)).lower()
        if manifest_split != task_split:
            raise ToolError(
                "task split manifest split does not match --task-split",
                task_split=task_split,
                manifest_split=manifest_split,
                manifest_path=str(split_manifest_path),
            )
        tasks = task_by_id(split_manifest)
        selected_tasks = []
        for task_id in args.tasks:
            if task_id not in tasks:
                raise ToolError(
                    "requested task is not in selected Click manifest",
                    task_id=task_id,
                    task_split=task_split,
                    manifest_path=str(split_manifest_path),
                )
            task = tasks[task_id]
            encoded_split = split_from_task_id(task_id)
            task_fields = (("task_id", encoded_split), ("split", task.get("split")), ("benchmark_split", task.get("benchmark_split")))
            for field, value in task_fields:
                if isinstance(value, str) and value.lower() != task_split:
                    raise ToolError(
                        "requested task split does not match --task-split",
                        task_id=task_id,
                        field=field,
                        task_split=task_split,
                        observed_split=value.lower(),
                        manifest_path=str(split_manifest_path),
                    )
            selected_tasks.append(task)
        results: list[dict[str, Any]] = []
        for task in selected_tasks:
            for acut_id in args.acuts:
                results.append(run_one(args, task, acut_id))
        payload = {
            "tool": TOOL,
            "runner_id": RUNNER_ID,
            "status": "completed",
            "mode": args.mode,
            "submission_contract": args.submission_contract,
            "run_prefix": args.run_prefix,
            "task_split": task_split,
            "task_split_manifest": str(split_manifest_path),
            "tasks": args.tasks,
            "acuts": args.acuts,
            "attempt": args.attempt,
            "started_at": started_at_for_batch(results),
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
