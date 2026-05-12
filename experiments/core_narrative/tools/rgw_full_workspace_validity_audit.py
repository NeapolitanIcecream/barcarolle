#!/usr/bin/env python3
"""Build the RGW-full-workspace-v1 RBench/RWork validity audit overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json
from _llm_budget import redact_sensitive_text


TOOL = "rgw_full_workspace_validity_audit"
SCHEMA_VERSION = "core-narrative.rgw-full-workspace-validity-audit.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
PRIMARY_ROOT = REPO_ROOT / "experiments/core_narrative/results/rgw_full_workspace_v1"
MATRIX_PATH = PRIMARY_ROOT / "normalized_result_matrix.json"
AUDIT_ROOT = PRIMARY_ROOT / "validity_audit"
REPORT_PATH = PRIMARY_ROOT / "interim_report/validity_audit_report.md"
PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/rgw_full_workspace_v1_validity_audit"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
TASK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks/click"
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
REFERENCE_TASKS = ("click__rbench__001", "click__rbench__004", "click__rbench__008", "click__rwork__004")
FULL_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
INTERNAL_RESOLVED_ARTIFACT_DIR = "_resolved_artifact_dir"
DISALLOWED_PUBLIC_RE = {
    "full_url": FULL_URL_RE,
    "file_url": re.compile(r"file:", re.IGNORECASE),
    "absolute_users_path": re.compile(r"/Users/"),
    "private_key_marker": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key_id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", default=str(PRIMARY_ROOT))
    parser.add_argument("--audit-root", default=str(AUDIT_ROOT))
    parser.add_argument("--report", default=str(REPORT_PATH))
    parser.add_argument("--private-root", default=str(PRIVATE_ROOT))
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--force-private", action="store_true", default=True)
    parser.add_argument("--no-force-private", dest="force_private", action="store_false")
    parser.add_argument("--output", help="Optional command summary JSON.")
    return parser.parse_args(list(argv) if argv is not None else None)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_relative_artifact_path(path: Path) -> str:
    resolved = path.resolve()
    repo_root = REPO_ROOT.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return os.path.relpath(resolved, repo_root)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def split_from_task_id(task_id: str) -> str:
    if "__rbench__" in task_id:
        return "rbench"
    if "__rwork__" in task_id:
        return "rwork"
    raise ToolError("unsupported Click task id", task_id=task_id)


def task_manifest_path(task_id: str) -> Path:
    split = split_from_task_id(task_id)
    path = TASK_ROOT / split / task_id / "task.yaml"
    if not path.exists():
        raise ToolError("task manifest is missing", task_id=task_id, path=str(path))
    return path


def changed_files(task: Mapping[str, Any]) -> list[str]:
    compare = task.get("source_compare") if isinstance(task.get("source_compare"), Mapping) else None
    if compare is None:
        metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
        compare = metadata.get("source_compare") if isinstance(metadata.get("source_compare"), Mapping) else {}
    files = compare.get("changed_files") if isinstance(compare, Mapping) else []
    result = [str(item) for item in files if isinstance(item, str)]
    if not result:
        raise ToolError("task has no changed_files for reference smoke", task_id=task.get("task_id"))
    return result


def run_capture(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def write_private_command_artifacts(
    *,
    artifact_dir: Path,
    name: str,
    command: Sequence[str],
    cwd: Path | None,
    completed: subprocess.CompletedProcess[str],
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / f"{name}.stdout.txt"
    stderr_path = artifact_dir / f"{name}.stderr.txt"
    stdout_path.write_text(redact_sensitive_text(completed.stdout, os.environ), encoding="utf-8")
    stderr_path.write_text(redact_sensitive_text(completed.stderr, os.environ), encoding="utf-8")
    summary = {
        "name": name,
        "command": [redact_sensitive_text(str(part), os.environ) for part in command],
        "cwd": str(cwd) if cwd is not None else None,
        "exit_code": completed.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }
    write_json(artifact_dir / f"{name}.json", summary)
    return summary


def command_or_blocker(
    command: Sequence[str],
    *,
    artifact_dir: Path,
    name: str,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> tuple[subprocess.CompletedProcess[str] | None, dict[str, Any]]:
    started_at = iso_now()
    started = time.monotonic()
    try:
        completed = run_capture(command, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        completed = subprocess.CompletedProcess(list(command), 124, stdout=stdout, stderr=stderr)
        finished_at = iso_now()
        summary = write_private_command_artifacts(
            artifact_dir=artifact_dir,
            name=name,
            command=command,
            cwd=cwd,
            completed=completed,
            started_at=started_at,
            finished_at=finished_at,
        )
        summary["timed_out"] = True
        summary["duration_seconds"] = round(time.monotonic() - started, 3)
        write_json(artifact_dir / f"{name}.json", summary)
        return None, summary
    finished_at = iso_now()
    summary = write_private_command_artifacts(
        artifact_dir=artifact_dir,
        name=name,
        command=command,
        cwd=cwd,
        completed=completed,
        started_at=started_at,
        finished_at=finished_at,
    )
    summary["timed_out"] = False
    summary["duration_seconds"] = round(time.monotonic() - started, 3)
    write_json(artifact_dir / f"{name}.json", summary)
    return completed, summary


def prepare_workspace(task_id: str, workspace: Path, artifact_dir: Path) -> dict[str, Any]:
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
        str(artifact_dir / "prepare_workspace_payload.json"),
    ]
    completed, summary = command_or_blocker(command, artifact_dir=artifact_dir, name="prepare_workspace", timeout=120)
    if completed is None or completed.returncode != 0:
        raise ToolError("workspace preparation failed", task_id=task_id, summary=summary)
    payload = load_json(artifact_dir / "prepare_workspace_payload.json")
    return {"payload": payload, "command": summary}


def install_workspace(workspace: Path, artifact_dir: Path, timeout_seconds: int) -> dict[str, Any]:
    uv = shutil.which("uv")
    if uv:
        create = [uv, "venv", "--python", "3.12", ".venv"]
        completed, summary = command_or_blocker(
            create,
            cwd=workspace,
            artifact_dir=artifact_dir,
            name="venv_create",
            timeout=timeout_seconds,
        )
        if completed is not None and completed.returncode == 0:
            install = [uv, "pip", "install", "--python", ".venv/bin/python", "-q", "-e", ".", "pytest"]
            completed, install_summary = command_or_blocker(
                install,
                cwd=workspace,
                artifact_dir=artifact_dir,
                name="venv_install",
                timeout=timeout_seconds,
            )
            if completed is None or completed.returncode != 0:
                raise ToolError("workspace dependency install failed", summary=install_summary)
            return {"status": "installed", "venv_backend": "uv", "venv_create": summary, "venv_install": install_summary}

    if (workspace / ".venv").exists():
        shutil.rmtree(workspace / ".venv")
    create = [sys.executable, "-m", "venv", ".venv"]
    completed, create_summary = command_or_blocker(
        create,
        cwd=workspace,
        artifact_dir=artifact_dir,
        name="venv_create_fallback",
        timeout=timeout_seconds,
    )
    if completed is None or completed.returncode != 0:
        raise ToolError("workspace venv creation failed", summary=create_summary)
    upgrade = [".venv/bin/python", "-m", "pip", "install", "-q", "--upgrade", "pip"]
    completed, upgrade_summary = command_or_blocker(
        upgrade,
        cwd=workspace,
        artifact_dir=artifact_dir,
        name="venv_pip_upgrade",
        timeout=timeout_seconds,
    )
    if completed is None or completed.returncode != 0:
        raise ToolError("workspace pip upgrade failed", summary=upgrade_summary)
    install = [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"]
    completed, install_summary = command_or_blocker(
        install,
        cwd=workspace,
        artifact_dir=artifact_dir,
        name="venv_install_fallback",
        timeout=timeout_seconds,
    )
    if completed is None or completed.returncode != 0:
        raise ToolError("workspace dependency install failed", summary=install_summary)
    return {
        "status": "installed",
        "venv_backend": "python_venv",
        "venv_create": create_summary,
        "pip_upgrade": upgrade_summary,
        "venv_install": install_summary,
    }


def verify_patch(
    *,
    task_id: str,
    acut_id: str,
    run_id: str,
    workspace: Path,
    patch_path: Path,
    artifact_dir: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    output = artifact_dir / "normalized_result.json"
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_manifest_path(task_id)),
        "--patch",
        str(patch_path),
        "--acut-id",
        acut_id,
        "--attempt",
        "1",
        "--run-id",
        run_id,
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(output),
        "--timeout-seconds",
        str(timeout_seconds),
        "--redact-verifier-artifacts",
    ]
    completed, command_summary = command_or_blocker(
        command,
        artifact_dir=artifact_dir,
        name="verify_command",
        timeout=timeout_seconds + 60,
    )
    if output.exists():
        normalized = load_json(output)
    else:
        normalized = {
            "status": "infra_blocked",
            "error": redact_sensitive_text(completed.stderr if completed is not None else "", os.environ),
            "verification": {"exit_code": None, "duration_seconds": None},
        }
    return {"command": command_summary, "normalized": normalized}


def reference_patch_for_task(task_id: str) -> tuple[str, dict[str, Any]]:
    task = load_manifest(task_manifest_path(task_id))
    source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
    base_commit = source.get("base_commit")
    target_commit = source.get("target_commit")
    if not isinstance(base_commit, str) or not isinstance(target_commit, str):
        raise ToolError("task source commits are missing", task_id=task_id)
    files = changed_files(task)
    command = ["git", "diff", "--binary", base_commit, target_commit, "--", *files]
    completed = run_capture(command, cwd=SOURCE_REPO, timeout=60)
    if completed.returncode != 0:
        raise ToolError("failed to generate reference patch", task_id=task_id, stderr=completed.stderr.strip())
    if not completed.stdout.strip():
        raise ToolError("reference patch was empty", task_id=task_id)
    metadata = {
        "patch_bytes": len(completed.stdout.encode("utf-8")),
        "patch_sha256": sha256_text(completed.stdout),
        "changed_file_count": len(files),
    }
    return completed.stdout, metadata


def reference_smoke_oracle_status(status: Any) -> str:
    if status == "passed":
        return "reference_passed"
    if status in {"failed", "invalid_submission", "patch_apply_error"}:
        return "task_oracle_invalid"
    return "reference_smoke_blocked"


def run_reference_smoke(
    *,
    task_id: str,
    private_root: Path,
    install_timeout_seconds: int,
    verifier_timeout_seconds: int,
    force_private: bool,
) -> dict[str, Any]:
    run_id = f"validity_audit_20260512__reference__{slug(task_id)}"
    artifact_dir = private_root / "artifacts" / run_id
    workspace = private_root / "workspaces" / f"{run_id}__verify"
    if force_private:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        shutil.rmtree(workspace, ignore_errors=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        patch_text, patch_metadata = reference_patch_for_task(task_id)
        patch_path = artifact_dir / "reference.patch"
        patch_path.write_text(patch_text, encoding="utf-8")
        prepare_workspace(task_id, workspace, artifact_dir)
        install_workspace(workspace, artifact_dir, install_timeout_seconds)
        verified = verify_patch(
            task_id=task_id,
            acut_id="reference-gold-smoke",
            run_id=run_id,
            workspace=workspace,
            patch_path=patch_path,
            artifact_dir=artifact_dir,
            timeout_seconds=verifier_timeout_seconds,
        )
        normalized = verified["normalized"]
        status = normalized.get("status")
        oracle_status = reference_smoke_oracle_status(status)
        verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
        return {
            "task_id": task_id,
            "private_run_id": run_id,
            "smoke_kind": "source_target_reference_patch",
            "status": status,
            "oracle_status": oracle_status,
            "reference_patch": patch_metadata,
            "verifier_exit_code": verification.get("exit_code"),
            "verifier_duration_seconds": verification.get("duration_seconds"),
            "verifier_artifacts_redacted": True,
            "public_artifact_redacted": True,
        }
    except Exception as exc:
        return {
            "task_id": task_id,
            "private_run_id": run_id,
            "smoke_kind": "source_target_reference_patch",
            "status": "infra_blocked",
            "oracle_status": "reference_smoke_blocked",
            "blocker": redact_sensitive_text(str(exc), os.environ),
            "public_artifact_redacted": True,
        }


def attribution_category(attribution: Mapping[str, Any]) -> str:
    non_url = attribution.get("non_url_reason_counts")
    if isinstance(non_url, Mapping) and any(int(value) > 0 for value in non_url.values() if isinstance(value, int)):
        return "non_url_unsafe_patch_content"
    if int(attribution.get("model_generated_full_url_count") or 0) > 0:
        return "model_generated_full_url"
    if int(attribution.get("ambiguous_full_url_count") or 0) > 0:
        return "ambiguous_full_url"
    if attribution.get("all_full_urls_source_derived") is True and attribution.get("all_unsafe_reasons_source_derived") is True:
        return "all_full_urls_source_derived"
    if int(attribution.get("source_derived_full_url_count") or 0) > 0:
        return "source_derived_full_url"
    return "ambiguous_full_url"


def redacted_url_occurrences(attribution: Mapping[str, Any]) -> list[dict[str, Any]]:
    occurrences = attribution.get("url_occurrences")
    if not isinstance(occurrences, list):
        return []
    redacted: list[dict[str, Any]] = []
    for occurrence in occurrences:
        if not isinstance(occurrence, Mapping):
            continue
        redacted.append(
            {
                "diff_line_role": occurrence.get("diff_line_role"),
                "line_number": occurrence.get("line_number"),
                "url_char_count": occurrence.get("url_char_count"),
                "url_sha256": occurrence.get("url_sha256"),
                "content_recorded": False,
            }
        )
    return redacted


def resolve_primary_artifact_dir(record: Mapping[str, Any], primary_root: Path) -> Path:
    artifact_paths = record.get("artifact_paths") if isinstance(record.get("artifact_paths"), Mapping) else {}
    recorded = artifact_paths.get("artifact_dir")
    run_id = str(record.get("run_id") or "")
    candidates: list[Path] = []

    def add_candidate(path: Path) -> None:
        if path not in candidates:
            candidates.append(path)

    recorded_path = Path(str(recorded)) if isinstance(recorded, str) and recorded else None
    if run_id:
        add_candidate(primary_root / "raw" / run_id)
    if recorded_path is not None:
        add_candidate(primary_root / "raw" / recorded_path.name)
        if recorded_path.is_absolute():
            add_candidate(recorded_path)
        else:
            add_candidate(primary_root / recorded_path)
            add_candidate(recorded_path)

    if not candidates:
        raise ToolError("normalized USV record is missing artifact_dir", run_id=record.get("run_id"))

    for artifact_dir in candidates:
        if (artifact_dir / "workspace_mode_result.json").exists():
            return artifact_dir
    return candidates[0]


def usv_cache_key(item: Mapping[str, Any]) -> tuple[str, str, str, str] | None:
    split = item.get("split")
    task_id = item.get("task_id")
    acut_id = item.get("acut_id")
    run_id = item.get("run_id")
    if not all(isinstance(value, str) and value for value in (split, task_id, acut_id, run_id)):
        return None
    return str(split), str(task_id), str(acut_id), str(run_id)


def cached_usv_cells_by_key(cached_usv_path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    if not cached_usv_path.exists():
        return {}
    payload = load_json(cached_usv_path)
    cells = payload.get("cells") if isinstance(payload.get("cells"), list) else []
    cached: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        key = usv_cache_key(cell)
        if key is None:
            continue
        cached[key] = public_usv_cell(cell)
    return cached


def usv_primary_cell_key(record: Mapping[str, Any]) -> tuple[str, str, str] | None:
    split = record.get("split")
    task_id = record.get("task_id")
    acut_id = record.get("acut_id")
    if split is None or task_id is None or acut_id is None:
        return None
    return str(split), str(task_id), str(acut_id)


def is_dry_run_record(record: Mapping[str, Any]) -> bool:
    run_id = record.get("run_id")
    if isinstance(run_id, str) and "__dry-run__" in run_id:
        return True
    command_lines = record.get("command_lines") if isinstance(record.get("command_lines"), Mapping) else {}
    workspace_runner = command_lines.get("workspace_runner") if isinstance(command_lines, Mapping) else None
    return isinstance(workspace_runner, list) and "--dry-run" in {str(part) for part in workspace_runner}


def has_explicit_non_live_model_call(record: Mapping[str, Any]) -> bool:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), Mapping) else {}
    if metadata.get("model_call_made") is False:
        return True
    cost_metadata = record.get("cost_metadata") if isinstance(record.get("cost_metadata"), Mapping) else {}
    return cost_metadata.get("model_call_made") is False


def is_non_live_primary_record(record: Mapping[str, Any]) -> bool:
    return is_dry_run_record(record) or has_explicit_non_live_model_call(record)


def canonical_usv_input_records(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    unkeyed: list[Mapping[str, Any]] = []
    keyed: dict[tuple[str, str, str], tuple[tuple[str, int, str, int], Mapping[str, Any]]] = {}
    for sequence, record in enumerate(records):
        if is_non_live_primary_record(record):
            continue
        key = usv_primary_cell_key(record)
        if key is None:
            unkeyed.append(record)
            continue
        recency_key = evidence_recency_key(record, sequence)
        current = keyed.get(key)
        if current is None or recency_key > current[0]:
            keyed[key] = (recency_key, record)
    return unkeyed + [keyed[key][1] for key in sorted(keyed)]


def build_usv_audit(
    records: Sequence[Mapping[str, Any]],
    primary_root: Path,
    cached_usv_path: Path | None = None,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    cached_cells: dict[tuple[str, str, str, str], dict[str, Any]] | None = None
    fallback_path = cached_usv_path if cached_usv_path is not None else primary_root / "validity_audit/usv_attribution.json"

    def cached_cell_for(record: Mapping[str, Any]) -> dict[str, Any] | None:
        nonlocal cached_cells
        if cached_cells is None:
            cached_cells = cached_usv_cells_by_key(fallback_path)
        key = usv_cache_key(record)
        return cached_cells.get(key) if key is not None else None

    for record in canonical_usv_input_records(records):
        if record.get("status") != "unsafe_or_scope_violation":
            continue
        artifact_dir = resolve_primary_artifact_dir(record, primary_root)
        workspace_result_path = artifact_dir / "workspace_mode_result.json"
        if not workspace_result_path.exists():
            cached_cell = cached_cell_for(record)
            if cached_cell is not None:
                cells.append(cached_cell)
                continue
            raise ToolError(
                "USV raw artifact is missing and no committed redacted attribution fallback exists",
                run_id=record.get("run_id"),
                workspace_mode_result=str(workspace_result_path),
                cached_usv_path=str(fallback_path),
            )
        payload = load_json(workspace_result_path)
        candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
        attribution = (
            candidate.get("unsafe_content_attribution")
            if isinstance(candidate.get("unsafe_content_attribution"), Mapping)
            else {}
        )
        category = attribution_category(attribution)
        policy_hold = category == "all_full_urls_source_derived"
        run_id = str(record.get("run_id") or artifact_dir.name)
        raw_artifact_ref = artifact_dir.relative_to(primary_root).as_posix() if artifact_dir.is_relative_to(primary_root) else run_id
        cells.append(
            {
                "cell_id": f"{record.get('split')}::{record.get('task_id')}::{record.get('acut_id')}",
                "split": record.get("split"),
                "task_id": record.get("task_id"),
                "acut_id": record.get("acut_id"),
                "run_id": run_id,
                "primary_status": record.get("status"),
                "primary_result_kind": "true_primary_result",
                INTERNAL_RESOLVED_ARTIFACT_DIR: str(artifact_dir),
                "audit_attribution_category": category,
                "audit_disposition": "policy_hold_source_derived_url" if policy_hold else "true_unsafe_primary_result",
                "acut_failure_counted_in_overlay": not policy_hold,
                "raw_artifact_ref": raw_artifact_ref,
                "workspace_mode_status": payload.get("status"),
                "candidate_patch": {
                    "persisted": candidate.get("written"),
                    "stored_size_bytes": candidate.get("size_bytes"),
                    "raw_candidate_patch_size_bytes": candidate.get("raw_candidate_patch_size_bytes"),
                    "redacted_preview_written": (
                        candidate.get("redacted_preview", {}).get("written")
                        if isinstance(candidate.get("redacted_preview"), Mapping)
                        else None
                    ),
                },
                "unsafe_attribution_redacted": {
                    "reason_counts": attribution.get("reason_counts", {}),
                    "full_url_count": attribution.get("full_url_count", 0),
                    "source_derived_full_url_count": attribution.get("source_derived_full_url_count", 0),
                    "model_generated_full_url_count": attribution.get("model_generated_full_url_count", 0),
                    "ambiguous_full_url_count": attribution.get("ambiguous_full_url_count", 0),
                    "non_url_reason_counts": attribution.get("non_url_reason_counts", {}),
                    "full_url_role_counts": attribution.get("full_url_role_counts", {}),
                    "content_recorded": False,
                    "url_occurrences": redacted_url_occurrences(attribution),
                },
            }
        )
    return sorted(cells, key=lambda item: (str(item["task_id"]), str(item["acut_id"])))


def public_usv_cell(cell: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in cell.items() if not str(key).startswith("_")}


def resolve_cell_artifact_dir(cell: Mapping[str, Any], primary_root: Path) -> Path:
    candidates: list[Path] = []

    def add_candidate(path: Path) -> None:
        if path not in candidates:
            candidates.append(path)

    resolved_artifact_dir = cell.get(INTERNAL_RESOLVED_ARTIFACT_DIR)
    if isinstance(resolved_artifact_dir, str) and resolved_artifact_dir:
        add_candidate(Path(resolved_artifact_dir))

    raw_artifact_ref = cell.get("raw_artifact_ref")
    if isinstance(raw_artifact_ref, str) and raw_artifact_ref:
        raw_artifact_path = Path(raw_artifact_ref)
        if raw_artifact_path.is_absolute():
            add_candidate(raw_artifact_path)
        else:
            add_candidate(primary_root / raw_artifact_path)
            if len(raw_artifact_path.parts) == 1:
                add_candidate(primary_root / "raw" / raw_artifact_path)

    run_id = cell.get("run_id")
    if isinstance(run_id, str) and run_id:
        add_candidate(primary_root / "raw" / run_id)

    for candidate in candidates:
        if (candidate / "workspace_mode_result.json").exists():
            return candidate
    if candidates:
        return candidates[0]
    raise ToolError("policy-hold replay cell is missing artifact reference", cell_id=cell.get("cell_id"))


def policy_hold_replay_cache_key(item: Mapping[str, Any], *, run_id_key: str) -> tuple[str, str] | None:
    cell_id = item.get("cell_id")
    run_id = item.get(run_id_key)
    if not isinstance(cell_id, str) or not cell_id or not isinstance(run_id, str) or not run_id:
        return None
    return cell_id, run_id


def cached_policy_hold_replays_by_key(cached_replays_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not cached_replays_path.exists():
        return {}
    payload = load_json(cached_replays_path)
    replays = payload.get("replays") if isinstance(payload.get("replays"), list) else []
    cached: dict[tuple[str, str], dict[str, Any]] = {}
    for replay in replays:
        if not isinstance(replay, Mapping):
            continue
        key = policy_hold_replay_cache_key(replay, run_id_key="primary_run_id")
        if key is None:
            continue
        cached[key] = dict(replay)
    return cached


def has_workspace_mode_result(cell: Mapping[str, Any], primary_root: Path) -> bool:
    try:
        artifact_dir = resolve_cell_artifact_dir(cell, primary_root)
    except ToolError:
        return False
    return (artifact_dir / "workspace_mode_result.json").exists()


def extract_patch_from_preserved_workspace(cell: Mapping[str, Any], primary_root: Path, artifact_dir: Path) -> tuple[Path, dict[str, Any]]:
    workspace_result = load_json(resolve_cell_artifact_dir(cell, primary_root) / "workspace_mode_result.json")
    run_workspace = Path(str(workspace_result.get("run_workspace")))
    candidate = workspace_result.get("candidate_patch") if isinstance(workspace_result.get("candidate_patch"), Mapping) else {}
    base_ref = candidate.get("diff_base_ref") or candidate.get("base_ref")
    if not run_workspace.exists():
        raise ToolError("preserved run workspace is missing", run_id=cell.get("run_id"))
    if not isinstance(base_ref, str) or not base_ref:
        raise ToolError("preserved run workspace base ref is missing", run_id=cell.get("run_id"))
    command = ["git", "diff", "--binary", "--no-ext-diff", "--full-index", "--unified=3", base_ref, "--"]
    completed, summary = command_or_blocker(
        command,
        cwd=run_workspace,
        artifact_dir=artifact_dir,
        name="extract_preserved_workspace_patch",
        timeout=60,
    )
    if completed is None or completed.returncode != 0:
        raise ToolError("failed to extract preserved workspace patch", summary=summary)
    patch_text = completed.stdout
    if not patch_text.strip():
        raise ToolError("preserved workspace diff was empty", run_id=cell.get("run_id"))
    patch_path = artifact_dir / "preserved_workspace.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    return patch_path, {
        "patch_bytes": len(patch_text.encode("utf-8")),
        "patch_sha256": sha256_text(patch_text),
    }


def run_policy_hold_replay(
    *,
    cell: Mapping[str, Any],
    primary_root: Path,
    private_root: Path,
    install_timeout_seconds: int,
    verifier_timeout_seconds: int,
    force_private: bool,
) -> dict[str, Any]:
    run_id = f"validity_audit_20260512__replay__{slug(str(cell['acut_id']))}__{slug(str(cell['task_id']))}"
    artifact_dir = private_root / "artifacts" / run_id
    workspace = private_root / "workspaces" / f"{run_id}__verify"
    if force_private:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        shutil.rmtree(workspace, ignore_errors=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    try:
        patch_path, patch_metadata = extract_patch_from_preserved_workspace(cell, primary_root, artifact_dir)
        prepare_workspace(str(cell["task_id"]), workspace, artifact_dir)
        install_workspace(workspace, artifact_dir, install_timeout_seconds)
        verified = verify_patch(
            task_id=str(cell["task_id"]),
            acut_id=str(cell["acut_id"]),
            run_id=run_id,
            workspace=workspace,
            patch_path=patch_path,
            artifact_dir=artifact_dir,
            timeout_seconds=verifier_timeout_seconds,
        )
        normalized = verified["normalized"]
        status = normalized.get("status")
        if status == "passed":
            replay_outcome = "verified_pass"
        elif status == "failed":
            replay_outcome = "verified_fail"
        elif status == "timeout":
            replay_outcome = "timeout"
        else:
            replay_outcome = str(status or "infra_blocked")
        verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
        return {
            "cell_id": cell["cell_id"],
            "task_id": cell["task_id"],
            "acut_id": cell["acut_id"],
            "primary_run_id": cell["run_id"],
            "private_run_id": run_id,
            "replay_basis": "post_run_replay_from_preserved_workspace",
            "primary_result_promoted": False,
            "replay_outcome": replay_outcome,
            "verifier_exit_code": verification.get("exit_code"),
            "verifier_duration_seconds": verification.get("duration_seconds"),
            "verifier_artifacts_redacted": True,
            "patch": patch_metadata,
        }
    except Exception as exc:
        return {
            "cell_id": cell["cell_id"],
            "task_id": cell["task_id"],
            "acut_id": cell["acut_id"],
            "primary_run_id": cell["run_id"],
            "private_run_id": run_id,
            "replay_basis": "post_run_replay_from_preserved_workspace",
            "primary_result_promoted": False,
            "replay_outcome": "infra_blocked",
            "blocker": redact_sensitive_text(str(exc), os.environ),
        }


def build_policy_hold_replays(
    *,
    policy_holds: Sequence[Mapping[str, Any]],
    primary_root: Path,
    private_root: Path,
    cached_replays_path: Path,
    install_timeout_seconds: int,
    verifier_timeout_seconds: int,
    force_private: bool,
) -> list[dict[str, Any]]:
    replays: list[dict[str, Any]] = []
    cached_replays: dict[tuple[str, str], dict[str, Any]] | None = None

    def cached_replay_for(cell: Mapping[str, Any]) -> dict[str, Any] | None:
        nonlocal cached_replays
        if cached_replays is None:
            cached_replays = cached_policy_hold_replays_by_key(cached_replays_path)
        key = policy_hold_replay_cache_key(cell, run_id_key="run_id")
        return cached_replays.get(key) if key is not None else None

    for cell in policy_holds:
        if not has_workspace_mode_result(cell, primary_root):
            cached_replay = cached_replay_for(cell)
            if cached_replay is not None:
                replays.append(cached_replay)
                continue
        replays.append(
            run_policy_hold_replay(
                cell=cell,
                primary_root=primary_root,
                private_root=private_root,
                install_timeout_seconds=install_timeout_seconds,
                verifier_timeout_seconds=verifier_timeout_seconds,
                force_private=force_private,
            )
        )
    return replays


def primary_cell_key(item: Mapping[str, Any]) -> tuple[str, str] | None:
    task_id = item.get("task_id")
    acut_id = item.get("acut_id")
    if task_id is None or acut_id is None:
        return None
    return str(task_id), str(acut_id)


def evidence_recency_key(record: Mapping[str, Any], sequence: int) -> tuple[str, int, str, int]:
    evidence_at = record.get("finished_at") or record.get("started_at")
    attempt = record.get("attempt")
    return (
        evidence_at if isinstance(evidence_at, str) else "",
        attempt if isinstance(attempt, int) else -1,
        str(record.get("run_id") or ""),
        sequence,
    )


def canonical_rwork_records(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    unkeyed: list[Mapping[str, Any]] = []
    keyed: dict[tuple[str, str], tuple[tuple[str, int, str, int], Mapping[str, Any]]] = {}
    for sequence, record in enumerate(records):
        if record.get("split") != "rwork":
            continue
        if is_non_live_primary_record(record):
            continue
        key = primary_cell_key(record)
        if key is None:
            unkeyed.append(record)
            continue
        recency_key = evidence_recency_key(record, sequence)
        current = keyed.get(key)
        if current is None or recency_key > current[0]:
            keyed[key] = (recency_key, record)
    return unkeyed + [keyed[key][1] for key in sorted(keyed)]


def canonical_rwork_usv_cells(
    records: Sequence[Mapping[str, Any]],
    usv_cells: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    unkeyed: list[Mapping[str, Any]] = []
    by_cell: dict[tuple[str, str], Mapping[str, Any]] = {}
    by_run: dict[tuple[tuple[str, str], str], Mapping[str, Any]] = {}
    for cell in usv_cells:
        if cell.get("split") != "rwork":
            continue
        key = primary_cell_key(cell)
        if key is None:
            unkeyed.append(cell)
            continue
        by_cell[key] = cell
        run_id = cell.get("run_id")
        if run_id is not None:
            by_run[(key, str(run_id))] = cell

    selected: list[Mapping[str, Any]] = []
    for record in records:
        if record.get("status") != "unsafe_or_scope_violation":
            continue
        key = primary_cell_key(record)
        if key is None:
            continue
        run_id = record.get("run_id")
        cell = by_run.get((key, str(run_id))) if run_id is not None else None
        if cell is None:
            cell = by_cell.get(key)
        if cell is not None:
            selected.append(cell)
    selected.extend(unkeyed)
    return selected


def w_metrics(records: Sequence[Mapping[str, Any]], usv_cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rwork = canonical_rwork_records(records)
    rwork_usv_cells = canonical_rwork_usv_cells(rwork, usv_cells)
    verified_passes = sum(1 for record in rwork if record.get("status") == "verified_pass")
    policy_hold_count = sum(
        1 for cell in rwork_usv_cells if cell.get("audit_disposition") == "policy_hold_source_derived_url"
    )
    true_unsafe_count = sum(
        1 for cell in rwork_usv_cells if cell.get("audit_disposition") == "true_unsafe_primary_result"
    )
    fixed_denominator = len(rwork)
    measured_denominator = max(0, fixed_denominator - policy_hold_count)
    return {
        "metrics": {
            "fixed_denominator_verified_pass_rate": verified_passes / fixed_denominator if fixed_denominator else None,
            "measured_verified_pass_rate": verified_passes / measured_denominator if measured_denominator else None,
            "policy_hold_count": policy_hold_count,
            "true_unsafe_count": true_unsafe_count,
        },
        "denominators": {
            "fixed_denominator": fixed_denominator,
            "measured_denominator": measured_denominator,
            "verified_pass_count": verified_passes,
            "policy_holds_excluded_from_measured_denominator": policy_hold_count,
        },
    }


def format_optional_rate(value: float | None) -> str:
    return "null" if value is None else f"{value:.6f}"


def scan_public_artifacts(paths: Sequence[Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in DISALLOWED_PUBLIC_RE.items():
            if pattern.search(text):
                findings.append({"path": path.as_posix(), "finding": name})
    return {"passed": not findings, "findings": findings}


def write_report(
    *,
    report_path: Path,
    usv_cells: Sequence[Mapping[str, Any]],
    reference_smokes: Sequence[Mapping[str, Any]],
    replays: Sequence[Mapping[str, Any]],
    overlay: Mapping[str, Any],
) -> None:
    replay_by_cell = {str(item["cell_id"]): item for item in replays if isinstance(item.get("cell_id"), str)}
    metrics = overlay["metrics"]
    denominators = overlay["denominators"]
    lines = [
        "# RGW-full-workspace-v1 Validity Audit",
        "",
        "## Scope and non-claims",
        "",
        "This audit covers only current RBench/RWork primary validity for RGW-full-workspace-v1.",
        "It does not continue G, does not rerun the full RGW R/W matrix, and does not rerun all RBench/RWork cells.",
        "It makes no NFL reversal claim and does not introduce license, admission, authorization, product policy, redaction, or scorecard semantics.",
        "",
        "Raw replay patches, verifier logs, and full paths are kept in ignored local workspace artifacts. This report records only redacted summaries.",
        "",
        "## Denominators",
        "",
        f"Fixed W denominator: `{denominators['fixed_denominator']}` current RWork primary cells.",
        f"Measured W denominator: `{denominators['measured_denominator']}` after excluding source-derived URL-only policy holds from measured failures.",
        "Post-run replay outcomes are not promoted to true primary results.",
        "",
        "## USV Attribution",
        "",
        "| Cell | Attribution | Audit disposition | Replay | Primary distinction |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cell in usv_cells:
        replay = replay_by_cell.get(str(cell["cell_id"]))
        replay_text = replay.get("replay_outcome") if replay else "not_attempted"
        lines.append(
            "| `{cell}` | `{category}` | `{disposition}` | `{replay}` | `{kind}` |".format(
                cell=cell["cell_id"],
                category=cell["audit_attribution_category"],
                disposition=cell["audit_disposition"],
                replay=replay_text,
                kind=cell["primary_result_kind"],
            )
        )
    lines.extend(
        [
            "",
            "## Reference Smoke",
            "",
            "| Task | Status | Oracle conclusion |",
            "| --- | --- | --- |",
        ]
    )
    for smoke in reference_smokes:
        lines.append(
            f"| `{smoke['task_id']}` | `{smoke.get('status')}` | `{smoke.get('oracle_status')}` |"
        )
    lines.extend(
        [
            "",
            "If a reference patch cannot pass, the task is `task_oracle_invalid` and needs global exclusion or correction followed by rerunning all ACUTs for that task only. No such exclusion is applied unless recorded above.",
            "",
            "## W Metrics",
            "",
            "```yaml",
            f"fixed_denominator_verified_pass_rate: {format_optional_rate(metrics['fixed_denominator_verified_pass_rate'])}",
            f"measured_verified_pass_rate: {format_optional_rate(metrics['measured_verified_pass_rate'])}",
            f"policy_hold_count: {metrics['policy_hold_count']}",
            f"true_unsafe_count: {metrics['true_unsafe_count']}",
            "```",
            "",
            "## Audit Conclusion",
            "",
            "The current Click W pack provides signal after validity audit: measured primary pass signal remains, true unsafe outcomes are isolated, and source-derived URL-only artifact-policy holds are no longer treated as ordinary ACUT failures in the audit overlay.",
            "This is only an audit conclusion for the Click W pack and is not an NFL reversal claim.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    primary_root = Path(args.primary_root)
    audit_root = Path(args.audit_root)
    private_root = Path(args.private_root)
    report_path = Path(args.report)
    matrix_path = primary_root / "normalized_result_matrix.json"
    matrix = load_json(matrix_path)
    records = matrix.get("records") if isinstance(matrix.get("records"), list) else []
    started_at = iso_now()

    usv_cells = build_usv_audit(records, primary_root, audit_root / "usv_attribution.json")
    policy_holds = [cell for cell in usv_cells if cell["audit_disposition"] == "policy_hold_source_derived_url"]
    replays = build_policy_hold_replays(
        policy_holds=policy_holds,
        primary_root=primary_root,
        private_root=private_root,
        cached_replays_path=audit_root / "post_run_replays.json",
        install_timeout_seconds=args.install_timeout_seconds,
        verifier_timeout_seconds=args.verifier_timeout_seconds,
        force_private=args.force_private,
    )
    reference_smokes = [
        run_reference_smoke(
            task_id=task_id,
            private_root=private_root,
            install_timeout_seconds=args.install_timeout_seconds,
            verifier_timeout_seconds=args.verifier_timeout_seconds,
            force_private=args.force_private,
        )
        for task_id in REFERENCE_TASKS
    ]
    overlay = w_metrics(records, usv_cells)
    public_usv_cells = [public_usv_cell(cell) for cell in usv_cells]

    write_json(audit_root / "usv_attribution.json", {"schema_version": SCHEMA_VERSION, "cells": public_usv_cells})
    write_json(audit_root / "post_run_replays.json", {"schema_version": SCHEMA_VERSION, "replays": replays})
    write_json(audit_root / "reference_smokes.json", {"schema_version": SCHEMA_VERSION, "tasks": reference_smokes})
    write_json(audit_root / "w_metric_overlay.json", {"schema_version": SCHEMA_VERSION, **overlay})
    write_report(
        report_path=report_path,
        usv_cells=public_usv_cells,
        reference_smokes=reference_smokes,
        replays=replays,
        overlay=overlay,
    )
    public_scan = scan_public_artifacts(
        [
            audit_root / "usv_attribution.json",
            audit_root / "post_run_replays.json",
            audit_root / "reference_smokes.json",
            audit_root / "w_metric_overlay.json",
            report_path,
        ]
    )
    write_json(audit_root / "public_artifact_safety_scan.json", {"schema_version": SCHEMA_VERSION, **public_scan})
    if not public_scan["passed"]:
        raise ToolError("public audit artifact safety scan failed", findings=public_scan["findings"])

    summary = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "delivered",
        "started_at": started_at,
        "finished_at": iso_now(),
        "primary_root": repo_relative_artifact_path(primary_root),
        "audit_root": repo_relative_artifact_path(audit_root),
        "private_material_root": repo_relative_artifact_path(private_root),
        "usv_cell_count": len(usv_cells),
        "policy_hold_count": overlay["metrics"]["policy_hold_count"],
        "true_unsafe_count": overlay["metrics"]["true_unsafe_count"],
        "reference_smoke_status_counts": count_by(reference_smokes, "oracle_status"),
        "replay_outcome_counts": count_by(replays, "replay_outcome"),
        "w_metrics": overlay["metrics"],
        "public_artifact_safety_scan": public_scan,
    }
    write_json(audit_root / "audit_summary.json", summary)
    return summary


def count_by(items: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_audit(args)
        emit_json(summary, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
