#!/usr/bin/env python3
"""Run and summarize RGW-full-workspace-v1 through workspace_mode_runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json
from _llm_budget import redact_sensitive_text
from rgw_status_semantics import WORKSPACE_MODE_STATUSES, classify_status


TOOL = "codex_nfl_workspace_runner"
RUNNER_ID = "rgw-full-workspace-v1"
SCHEMA_VERSION = "core-narrative.rgw-full-workspace-result.v1"
SUMMARY_SCHEMA_VERSION = "core-narrative.rgw-full-workspace-summary.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/rgw_full_workspace_v1.yaml"
TASK_PACK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
WORKSPACE_MODE_RUNNER = REPO_ROOT / "experiments/core_narrative/tools/workspace_mode_runner.py"
CODEX_CLI_PATCH_COMMAND = REPO_ROOT / "experiments/core_narrative/tools/codex_cli_patch_command.py"
GSCORE_GOLD_PATCH_SMOKE = REPO_ROOT / "experiments/core_narrative/tools/codex_nfl_gscore_gold_patch_smoke.py"
DEFAULT_BUNDLE_ROOT = REPO_ROOT / "experiments/core_narrative/results/rgw_full_workspace_v1"
DEFAULT_WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/rgw_full_workspace_v1"
MIN_WORKSPACE_PYTHON = (3, 10)
WORKSPACE_PYTHON_CACHE: str | None = None
ACUTS = (
    "cheap-generic-swe",
    "cheap-click-specialist",
    "frontier-generic-swe",
    "frontier-click-specialist",
)
SENTINEL_CELLS = (
    ("rbench", "click__rbench__001", "cheap-generic-swe"),
    ("rbench", "click__rbench__002", "cheap-click-specialist"),
    ("rwork", "click__rwork__001", "frontier-generic-swe"),
    ("rwork", "click__rwork__002", "frontier-click-specialist"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--bundle-root", default=str(DEFAULT_BUNDLE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACES_ROOT))
    parser.add_argument("--run-prefix", default="rgw_full_workspace_v1_20260512")
    parser.add_argument("--phase", choices=("sentinels", "primary", "summary", "g6-smoke"), default="summary")
    parser.add_argument("--mode", choices=("live", "dry-run"), default="live")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--acut-timeout-seconds", type=int, default=3600)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--install-workspaces", action="store_true", default=True)
    parser.add_argument("--no-install-workspaces", dest="install_workspaces", action="store_false")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", help="Optional command output JSON.")
    parser.add_argument("--execute-gold-patch", action="store_true")
    return parser.parse_args(list(argv) if argv is not None else None)


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def split_from_task_id(task_id: str) -> str:
    if "__rbench__" in task_id:
        return "rbench"
    if "__rwork__" in task_id:
        return "rwork"
    raise ToolError("Click task id does not encode rbench/rwork split", task_id=task_id)


def task_manifest_path(task_id: str) -> Path:
    split = split_from_task_id(task_id)
    path = TASK_PACK_ROOT / "click" / split / task_id / "task.yaml"
    if not path.exists():
        raise ToolError("materialized Click task manifest is missing", task_id=task_id, path=str(path))
    return path


def acut_manifest_path(acut_id: str) -> Path:
    path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
    if not path.exists():
        raise ToolError("ACUT manifest does not exist", acut_id=acut_id, path=str(path))
    return path


def task_ids_from_split_manifest(path: Path, expected_split: str) -> list[str]:
    manifest = load_manifest(path)
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ToolError("task split manifest has no tasks list", manifest=str(path))
    task_ids: list[str] = []
    for task in tasks:
        if not isinstance(task, Mapping) or not isinstance(task.get("task_id"), str):
            continue
        task_id = str(task["task_id"])
        if split_from_task_id(task_id) != expected_split:
            raise ToolError("task split manifest contains wrong split", task_id=task_id, expected_split=expected_split)
        task_ids.append(task_id)
    return task_ids


def general_task_ids(config: Mapping[str, Any]) -> list[str]:
    general_path = REPO_ROOT / str(config["general"]["manifest"])
    general = load_manifest(general_path)
    subset = general.get("task_subset") if isinstance(general.get("task_subset"), Mapping) else {}
    locked = subset.get("locked_task_ids") if isinstance(subset.get("locked_task_ids"), list) else []
    ids = [str(item["instance_id"]) for item in locked if isinstance(item, Mapping) and isinstance(item.get("instance_id"), str)]
    if len(ids) != 6:
        raise ToolError("general benchmark locked denominator is not G6", observed_count=len(ids), manifest=str(general_path))
    return ids


def load_frozen_design(config_path: Path) -> dict[str, Any]:
    config = load_manifest(config_path)
    acuts = list(config.get("acuts") or [])
    if acuts != list(ACUTS):
        raise ToolError("RGW config ACUT order is not frozen", expected=list(ACUTS), observed=acuts)
    if int(config.get("primary_attempts_per_acut_task") or 0) != 1:
        raise ToolError("RGW primary attempts must be one", observed=config.get("primary_attempts_per_acut_task"))
    if config.get("best_of_n") is not False:
        raise ToolError("RGW config must disable best-of-N", observed=config.get("best_of_n"))

    rbench_path = REPO_ROOT / str(config["rbench"]["manifest"])
    rwork_path = REPO_ROOT / str(config["rwork"]["manifest"])
    rbench = task_ids_from_split_manifest(rbench_path, "rbench")
    rwork = task_ids_from_split_manifest(rwork_path, "rwork")
    g_tasks = general_task_ids(config)
    expected = config.get("primary_matrix", {}).get("expected_attempts", {})
    observed = {
        "rbench": len(rbench) * len(acuts),
        "rwork": len(rwork) * len(acuts),
        "general": len(g_tasks) * len(acuts),
    }
    observed["total"] = sum(observed.values())
    for key, value in observed.items():
        if expected.get(key) != value:
            raise ToolError("RGW fixed denominator mismatch", key=key, expected=expected.get(key), observed=value)
    return {"config": config, "rbench": rbench, "rwork": rwork, "general": g_tasks, "acuts": acuts}


def iter_primary_cells(design: Mapping[str, Any]) -> Iterable[tuple[str, str, str]]:
    for axis in ("rbench", "rwork", "general"):
        for task_id in design[axis]:
            for acut_id in design["acuts"]:
                yield axis, str(task_id), str(acut_id)


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
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }


def bundle_paths(bundle_root: Path, run_id: str | None = None) -> dict[str, Path]:
    paths = {
        "raw": bundle_root / "raw",
        "normalized": bundle_root / "normalized",
        "reports": bundle_root / "reports",
        "logs": bundle_root / "logs",
    }
    if run_id:
        paths["artifact_dir"] = paths["raw"] / run_id
        paths["normalized_result"] = paths["normalized"] / f"{run_id}.json"
    return paths


def run_id_for(prefix: str, axis: str, task_id: str, acut_id: str, attempt: int, mode: str) -> str:
    return f"{prefix}__{slug(mode)}__{axis}__{acut_id}__{slug(task_id)}__attempt{attempt}"


def python_version(executable: str) -> tuple[int, int] | None:
    try:
        completed = subprocess.run(
            [
                executable,
                "-c",
                "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        major, minor = completed.stdout.strip().split(".", 1)
        return int(major), int(minor)
    except (TypeError, ValueError):
        return None


def python_can_create_venv(executable: str) -> bool:
    try:
        with tempfile.TemporaryDirectory(prefix="rgw_workspace_python_probe_") as tmpdir:
            completed = subprocess.run(
                [executable, "-m", "venv", tmpdir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def workspace_python() -> str:
    global WORKSPACE_PYTHON_CACHE
    if WORKSPACE_PYTHON_CACHE:
        return WORKSPACE_PYTHON_CACHE

    candidates: list[str] = []
    env_override = os.environ.get("RGW_WORKSPACE_PYTHON")
    if env_override:
        candidates.append(env_override)
    candidates.append(sys.executable)
    candidates.extend(
        [
            "/opt/homebrew/opt/python@3.14/bin/python3.14",
            "/opt/homebrew/bin/python3.14",
            "/opt/homebrew/bin/python3.13",
            "/opt/homebrew/bin/python3.12",
            "/opt/homebrew/bin/python3.11",
            "/opt/homebrew/bin/python3.10",
        ]
    )
    for name in ("python3.14", "python3.13", "python3.12", "python3.11", "python3.10", "python3"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(resolved)

    seen: set[str] = set()
    inspected: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        version = python_version(candidate)
        venv_usable = version is not None and version >= MIN_WORKSPACE_PYTHON and python_can_create_venv(candidate)
        inspected.append(
            {
                "executable": candidate,
                "version": ".".join(map(str, version)) if version else None,
                "venv_usable": venv_usable,
            }
        )
        if venv_usable:
            WORKSPACE_PYTHON_CACHE = candidate
            return candidate
    raise ToolError(
        "workspace-mode Click runs require Python >=3.10",
        minimum=".".join(map(str, MIN_WORKSPACE_PYTHON)),
        inspected=inspected,
    )


def build_acut_command(*, acut_id: str, artifact_dir: Path, acut_timeout_seconds: int, mode: str) -> list[str]:
    inner_dir = artifact_dir / "codex_cli_patch_command"
    command = [
        workspace_python(),
        str(CODEX_CLI_PATCH_COMMAND),
        "--workspace",
        ".",
        "--acut",
        str(acut_manifest_path(acut_id)),
        "--artifact-dir",
        str(inner_dir),
        "--summary-output",
        str(artifact_dir / "codex_cli_patch_command.json"),
        "--codex-timeout-seconds",
        str(acut_timeout_seconds),
    ]
    if mode == "dry-run":
        command.append("--dry-run")
    return command


def workspace_mode_command(
    *,
    axis: str,
    task_id: str,
    acut_id: str,
    attempt: int,
    run_id: str,
    artifact_dir: Path,
    workspace_root: Path,
    acut_timeout_seconds: int,
    verifier_timeout_seconds: int,
    install_workspaces: bool,
    mode: str,
) -> list[str]:
    command = [
        workspace_python(),
        str(WORKSPACE_MODE_RUNNER),
        "--task",
        str(task_manifest_path(task_id)),
        "--source-repo",
        str(SOURCE_REPO),
        "--acut",
        str(acut_manifest_path(acut_id)),
        "--attempt",
        str(attempt),
        "--run-id",
        run_id,
        "--workspace-root",
        str(workspace_root),
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(artifact_dir / "workspace_mode_output.json"),
        "--acut-timeout-seconds",
        str(acut_timeout_seconds + 30),
        "--verifier-timeout-seconds",
        str(verifier_timeout_seconds),
    ]
    if install_workspaces:
        command.append("--install-workspaces")
    command.append("--")
    command.extend(build_acut_command(acut_id=acut_id, artifact_dir=artifact_dir, acut_timeout_seconds=acut_timeout_seconds, mode=mode))
    return command


def estimate_cost_usd(acut_id: str, model_call_made: bool) -> float | None:
    if not model_call_made:
        return 0.0
    return 3.0 if acut_id.startswith("frontier-") else 1.0


def read_acut_summary(artifact_dir: Path) -> dict[str, Any] | None:
    return load_json(artifact_dir / "codex_cli_patch_command.json")


def normalized_from_workspace_payload(
    *,
    payload: Mapping[str, Any],
    axis: str,
    config_path: Path,
    command: Mapping[str, Any],
    artifact_dir: Path,
    normalized_path: Path,
) -> dict[str, Any]:
    status = str(payload.get("status"))
    classification = classify_status(status, payload)
    acut_id = str(payload.get("acut_id"))
    acut_summary = read_acut_summary(artifact_dir)
    model_call_made = bool(acut_summary.get("model_call_made")) if isinstance(acut_summary, Mapping) else True
    cost_metadata = {
        "model_call_made": model_call_made,
        "estimated_cost_usd": estimate_cost_usd(acut_id, model_call_made),
        "actual_cost_usd": None,
        "cost_source": "estimated_by_acut_tier; codex_cli_patch_command does not expose token usage",
        "acut_summary_artifact": str(artifact_dir / "codex_cli_patch_command.json")
        if (artifact_dir / "codex_cli_patch_command.json").exists()
        else None,
    }
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    verification = payload.get("verification") if isinstance(payload.get("verification"), Mapping) else {}
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "run_id": payload.get("run_id"),
        "axis": axis,
        "split": payload.get("split"),
        "task_id": payload.get("task_id"),
        "acut_id": acut_id,
        "attempt": payload.get("attempt"),
        "status": status,
        "recognized_workspace_mode_status": status in WORKSPACE_MODE_STATUSES,
        "primary_pass": classification["primary_pass"],
        "score_action": classification["score_action"],
        "score_value": classification["score_value"],
        "requires_rerun_or_exclusion": classification["requires_rerun_or_exclusion"],
        "triage_paused": classification["triage_paused"],
        "timeout_owner": classification["timeout_owner"],
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "base_refs": {
            "base_ref": metadata.get("base_ref") or candidate.get("base_ref"),
            "base_tree": metadata.get("base_tree") or candidate.get("base_tree"),
            "current_head": metadata.get("current_head") or candidate.get("current_head"),
            "head_drifted": metadata.get("head_drifted") or candidate.get("head_drifted"),
        },
        "candidate_patch": {
            "path": candidate.get("path") or str(artifact_dir / "candidate.patch"),
            "sha256": candidate.get("sha256"),
            "size_bytes": candidate.get("size_bytes"),
            "has_scoreable_diff": candidate.get("has_scoreable_diff"),
            "extracted_from_base_ref": candidate.get("candidate_patch_from_base_ref", True),
        },
        "verification_workspace": {
            "attempted": verification.get("attempted"),
            "workspace": verification.get("workspace"),
            "base_tree": verification.get("base_tree"),
            "base_tree_matches_run": verification.get("base_tree_matches_run"),
            "normalized_result": verification.get("normalized_result"),
            "verifier_exit_code": verification.get("verifier_exit_code"),
            "verifier_stdout_artifact": verification.get("verifier_stdout_artifact"),
            "verifier_stderr_artifact": verification.get("verifier_stderr_artifact"),
        },
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "workspace_mode_output": str(artifact_dir / "workspace_mode_output.json"),
            "workspace_mode_result": str(artifact_dir / "workspace_mode_result.json"),
            "candidate_patch": str(artifact_dir / "candidate.patch"),
            "acut_stdout": str(artifact_dir / "acut.stdout.txt"),
            "acut_stderr": str(artifact_dir / "acut.stderr.txt"),
            "workspace_runner_command": str(artifact_dir / "workspace_runner_command.json"),
            "normalized_result": str(normalized_path),
        },
        "command_lines": {
            "workspace_runner": command.get("command"),
            "config": str(config_path),
        },
        "cost_metadata": cost_metadata,
        "error": payload.get("error"),
        "source_workspace_payload_status": status,
        "metadata": {
            "batch_tool": TOOL,
            "runner_id": RUNNER_ID,
            "workspace_mode_schema_version": payload.get("schema_version"),
            "workspace_mode_tool": payload.get("tool"),
            "acut_command_status": metadata.get("acut_command_status"),
            "acut_exit_code": metadata.get("acut_exit_code"),
            "acut_command_error": metadata.get("acut_command_error"),
            "model_call_made": model_call_made,
            "status_semantics": classification,
        },
    }
    write_json(normalized_path, normalized)
    return normalized


def normalized_infra_result(
    *,
    run_id: str,
    axis: str,
    task_id: str,
    acut_id: str,
    attempt: int,
    artifact_dir: Path,
    normalized_path: Path,
    config_path: Path,
    reason: str,
    details: Mapping[str, Any],
) -> dict[str, Any]:
    status = "verifier_infra_error"
    classification = classify_status(status, {})
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "run_id": run_id,
        "axis": axis,
        "split": axis,
        "task_id": task_id,
        "acut_id": acut_id,
        "attempt": attempt,
        "status": status,
        "recognized_workspace_mode_status": True,
        "primary_pass": False,
        "score_action": classification["score_action"],
        "score_value": None,
        "requires_rerun_or_exclusion": True,
        "triage_paused": False,
        "timeout_owner": None,
        "started_at": iso_now(),
        "finished_at": iso_now(),
        "duration_seconds": 0,
        "base_refs": {"base_ref": None, "base_tree": None, "current_head": None, "head_drifted": None},
        "candidate_patch": {
            "path": str(artifact_dir / "candidate.patch"),
            "sha256": None,
            "size_bytes": 0,
            "has_scoreable_diff": False,
            "extracted_from_base_ref": False,
        },
        "verification_workspace": {
            "attempted": False,
            "workspace": None,
            "base_tree": None,
            "base_tree_matches_run": None,
            "normalized_result": None,
            "verifier_exit_code": None,
            "verifier_stdout_artifact": None,
            "verifier_stderr_artifact": None,
        },
        "artifact_paths": {
            "artifact_dir": str(artifact_dir),
            "candidate_patch": str(artifact_dir / "candidate.patch"),
            "normalized_result": str(normalized_path),
        },
        "command_lines": {"workspace_runner": None, "config": str(config_path)},
        "cost_metadata": {
            "model_call_made": False,
            "estimated_cost_usd": 0.0,
            "actual_cost_usd": None,
            "cost_source": "not_run_due_to_global_infrastructure_blocker",
        },
        "error": reason,
        "source_workspace_payload_status": status,
        "metadata": {
            "batch_tool": TOOL,
            "runner_id": RUNNER_ID,
            "model_call_made": False,
            "status_semantics": classification,
            "global_infra_exclusion_candidate": True,
            "infra_blocker_details": dict(details),
        },
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    write_json(artifact_dir / "infra_exclusion_result.json", normalized)
    write_json(normalized_path, normalized)
    return normalized


def run_click_cell(
    *,
    axis: str,
    task_id: str,
    acut_id: str,
    args: argparse.Namespace,
    config_path: Path,
) -> dict[str, Any]:
    run_id = run_id_for(args.run_prefix, axis, task_id, acut_id, args.attempt, args.mode)
    paths = bundle_paths(Path(args.bundle_root), run_id)
    artifact_dir = paths["artifact_dir"]
    normalized_path = paths["normalized_result"]
    if artifact_dir.exists() and any(artifact_dir.iterdir()) and not args.force:
        existing = load_json(normalized_path)
        if existing is not None:
            return existing
        raise ToolError("run artifacts already exist but normalized result is missing", run_id=run_id, artifact_dir=str(artifact_dir))
    if args.force and artifact_dir.exists():
        import shutil

        shutil.rmtree(artifact_dir)
    if args.force and normalized_path.exists():
        normalized_path.unlink()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    command = workspace_mode_command(
        axis=axis,
        task_id=task_id,
        acut_id=acut_id,
        attempt=args.attempt,
        run_id=run_id,
        artifact_dir=artifact_dir,
        workspace_root=Path(args.workspace_root),
        acut_timeout_seconds=args.acut_timeout_seconds,
        verifier_timeout_seconds=args.verifier_timeout_seconds,
        install_workspaces=args.install_workspaces,
        mode=args.mode,
    )
    summary = command_summary(
        command=command,
        cwd=REPO_ROOT,
        timeout_seconds=args.acut_timeout_seconds + args.verifier_timeout_seconds + 300,
        stdout_path=artifact_dir / "workspace_runner_command.stdout.txt",
        stderr_path=artifact_dir / "workspace_runner_command.stderr.txt",
    )
    write_json(artifact_dir / "workspace_runner_command.json", summary)
    payload = load_json(artifact_dir / "workspace_mode_output.json") or load_json(artifact_dir / "workspace_mode_result.json")
    if payload is None:
        timed_out = bool(summary["timed_out"] or summary["exit_code"] == 124)
        payload = {
            "run_id": run_id,
            "acut_id": acut_id,
            "task_id": task_id,
            "split": axis,
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
    normalized = normalized_from_workspace_payload(
        payload=payload,
        axis=axis,
        config_path=config_path,
        command=summary,
        artifact_dir=artifact_dir,
        normalized_path=normalized_path,
    )
    return normalized


def run_g6_smoke(args: argparse.Namespace, config_path: Path) -> dict[str, Any]:
    bundle_root = Path(args.bundle_root)
    smoke_output = bundle_root / "g6_gold_patch_smoke.json"
    smoke_report = bundle_root / "reports/g6_gold_patch_smoke.md"
    artifact_dir = bundle_root / "raw/g6_gold_patch_smoke"
    command = [
        sys.executable,
        str(GSCORE_GOLD_PATCH_SMOKE),
        "--config",
        str(REPO_ROOT / "experiments/core_narrative/configs/general_benchmark.yaml"),
        "--output",
        str(smoke_output),
        "--report",
        str(smoke_report),
        "--artifact-dir",
        str(artifact_dir),
    ]
    if args.execute_gold_patch:
        command.append("--execute-gold-patch")
    summary = command_summary(
        command=command,
        cwd=REPO_ROOT,
        timeout_seconds=14_700 if args.execute_gold_patch else 300,
        stdout_path=bundle_root / "logs/g6_gold_patch_smoke.stdout.txt",
        stderr_path=bundle_root / "logs/g6_gold_patch_smoke.stderr.txt",
    )
    write_json(bundle_root / "logs/g6_gold_patch_smoke_command.json", summary)
    payload = load_json(smoke_output) or {
        "tool": "codex_nfl_gscore_gold_patch_smoke",
        "status": "gold_patch_smoke_infra_error",
        "error": "gold-patch smoke did not emit output",
    }
    payload["command"] = summary
    write_json(smoke_output, payload)
    return payload


def g_infra_details(bundle_root: Path) -> dict[str, Any]:
    smoke = load_json(bundle_root / "g6_gold_patch_smoke.json") or {}
    status = smoke.get("status")
    gold_path = smoke.get("gold_patch_path") if isinstance(smoke.get("gold_patch_path"), Mapping) else {}
    return {
        "g6_gold_patch_smoke_status": status,
        "gold_patch_basis_proven": gold_path.get("basis_proven") is True,
        "gold_patch_ran": gold_path.get("ran") is True,
        "blockers": smoke.get("all_blockers") or smoke.get("blockers") or [],
        "artifact": str(bundle_root / "g6_gold_patch_smoke.json"),
    }


def run_general_infra_records(
    *,
    design: Mapping[str, Any],
    args: argparse.Namespace,
    config_path: Path,
) -> list[dict[str, Any]]:
    details = g_infra_details(Path(args.bundle_root))
    results: list[dict[str, Any]] = []
    for task_id in design["general"]:
        for acut_id in design["acuts"]:
            run_id = run_id_for(args.run_prefix, "general", str(task_id), str(acut_id), args.attempt, args.mode)
            paths = bundle_paths(Path(args.bundle_root), run_id)
            if paths["normalized_result"].exists() and not args.force:
                existing = load_json(paths["normalized_result"])
                if existing is not None:
                    results.append(existing)
                    continue
            results.append(
                normalized_infra_result(
                    run_id=run_id,
                    axis="general",
                    task_id=str(task_id),
                    acut_id=str(acut_id),
                    attempt=args.attempt,
                    artifact_dir=paths["artifact_dir"],
                    normalized_path=paths["normalized_result"],
                    config_path=config_path,
                    reason="G-score workspace-mode ACUT verification is globally excluded until G6 gold-patch infrastructure is proven and SWE-Bench Pro task workspaces/verifier are materialized.",
                    details=details,
                )
            )
    return results


def normalized_files(bundle_root: Path) -> list[Path]:
    root = bundle_root / "normalized"
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def load_normalized_results(bundle_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in normalized_files(bundle_root):
        payload = load_json(path)
        if isinstance(payload, dict) and payload.get("runner_id") == RUNNER_ID:
            records.append(payload)
    return records


def count_by(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def evidence_recency_key(record: Mapping[str, Any], sequence: int) -> tuple[str, int, str, int]:
    evidence_at = record.get("finished_at") or record.get("started_at")
    attempt = record.get("attempt")
    return (
        evidence_at if isinstance(evidence_at, str) else "",
        attempt if isinstance(attempt, int) else -1,
        str(record.get("run_id") or ""),
        sequence,
    )


def canonical_records_by_cell(
    records: Sequence[Mapping[str, Any]],
    axis: str,
    task_ids: Sequence[str],
    acuts: Sequence[str],
) -> tuple[set[tuple[str, str]], dict[tuple[str, str], Mapping[str, Any]]]:
    expected_cells = {(str(acut), str(task_id)) for acut in acuts for task_id in task_ids}
    by_cell: dict[tuple[str, str], tuple[tuple[str, int, str, int], Mapping[str, Any]]] = {}
    for sequence, record in enumerate(records):
        if record.get("axis") != axis:
            continue
        key = (str(record.get("acut_id")), str(record.get("task_id")))
        if key in expected_cells:
            recency_key = evidence_recency_key(record, sequence)
            current = by_cell.get(key)
            if current is None or recency_key > current[0]:
                by_cell[key] = (recency_key, record)
    return expected_cells, {key: record for key, (_, record) in by_cell.items()}


def summarize_axis(records: Sequence[Mapping[str, Any]], axis: str, task_ids: Sequence[str], acuts: Sequence[str]) -> dict[str, Any]:
    expected_cells, by_cell = canonical_records_by_cell(records, axis, task_ids, acuts)
    cells = []
    for acut, task_id in sorted(expected_cells):
        record = by_cell.get((acut, task_id))
        cells.append(
            {
                "acut_id": acut,
                "task_id": task_id,
                "present": record is not None,
                "status": record.get("status") if record else "missing",
                "score_action": record.get("score_action") if record else "missing_primary_attempt",
                "score_value": record.get("score_value") if record else None,
                "normalized_result": record.get("artifact_paths", {}).get("normalized_result") if record else None,
            }
        )
    present = [cell for cell in cells if cell["present"]]
    scored = [cell for cell in present if isinstance(cell["score_value"], int)]
    passes = sum(1 for cell in scored if cell["score_value"] == 1)
    infra = [cell for cell in present if cell["score_action"] == "rerun_or_global_exclusion_required"]
    triage = [cell for cell in present if cell["score_action"] == "triage_paused_before_primary_scoring"]
    effective_denominator = len(expected_cells) - len(infra)
    return {
        "axis": axis,
        "expected_cells": len(expected_cells),
        "present_cells": len(present),
        "missing_cells": len(expected_cells) - len(present),
        "fixed_denominator": len(expected_cells),
        "effective_denominator_after_recorded_global_infra_exclusions": effective_denominator,
        "passed": passes,
        "score_percent_fixed_denominator": 100.0 * passes / len(expected_cells) if expected_cells else None,
        "score_percent_effective_denominator": 100.0 * passes / effective_denominator if effective_denominator else None,
        "primary_score_ready": len(present) == len(expected_cells) and not infra and not triage,
        "status_counts": count_by([cell for cell in cells], "status"),
        "score_action_counts": count_by([cell for cell in cells], "score_action"),
        "infra_cells": infra,
        "triage_paused_cells": triage,
        "cells": cells,
    }


def by_acut_table(records: Sequence[Mapping[str, Any]], design: Mapping[str, Any]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for acut in design["acuts"]:
        row: dict[str, Any] = {"acut_id": acut}
        for axis in ("rbench", "rwork", "general"):
            task_ids = design[axis]
            _, by_cell = canonical_records_by_cell(records, axis, task_ids, [acut])
            axis_records = [
                by_cell[(str(acut), str(task_id))]
                for task_id in task_ids
                if (str(acut), str(task_id)) in by_cell
            ]
            scored = [record for record in axis_records if isinstance(record.get("score_value"), int)]
            passed = sum(1 for record in scored if record.get("score_value") == 1)
            infra = [record for record in axis_records if record.get("requires_rerun_or_exclusion") is True]
            triage = [record for record in axis_records if record.get("triage_paused") is True]
            denominator = len(task_ids)
            effective = denominator - len(infra)
            prefix = "r" if axis == "rbench" else "w" if axis == "rwork" else "g"
            row[f"{prefix}_passed"] = passed
            row[f"{prefix}_fixed_denominator"] = denominator
            row[f"{prefix}_effective_denominator"] = effective
            row[f"{prefix}_score_percent_fixed"] = 100.0 * passed / denominator if denominator else None
            row[f"{prefix}_score_percent_effective"] = 100.0 * passed / effective if effective else None
            row[f"{prefix}_primary_score_ready"] = len(axis_records) == denominator and not infra and not triage
            row[f"{prefix}_status_counts"] = count_by(axis_records, "status")
        table[str(acut)] = row
    return table


def rank(values: Mapping[str, Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    pairs: list[tuple[float, str]] = []
    for acut, row in values.items():
        value = row.get(key)
        if isinstance(value, (int, float)):
            pairs.append((float(value), acut))
    return [
        {"rank": index + 1, "acut_id": acut, "score_percent": score}
        for index, (score, acut) in enumerate(sorted(pairs, key=lambda item: (-item[0], item[1])))
    ]


def reversal_analysis(table: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    ready = all(row.get("r_primary_score_ready") and row.get("w_primary_score_ready") for row in table.values())
    r_rank = rank(table, "r_score_percent_fixed")
    w_rank = rank(table, "w_score_percent_fixed")
    if not ready:
        return {
            "status": "not_computable",
            "statement": "No ranking reversal statement: at least one R/W primary score is missing, triage-paused, or infrastructure-blocked.",
            "r_rank_order": r_rank,
            "w_rank_order": w_rank,
        }
    r_positions = {item["acut_id"]: item["rank"] for item in r_rank}
    w_positions = {item["acut_id"]: item["rank"] for item in w_rank}
    reversals = [
        {"acut_id": acut, "r_rank": r_positions[acut], "w_rank": w_positions[acut]}
        for acut in sorted(r_positions)
        if acut in w_positions and r_positions[acut] != w_positions[acut]
    ]
    return {
        "status": "reversal_observed" if reversals else "no_reversal_observed",
        "statement": "Ranking reversal observed." if reversals else "No R/W rank reversal observed under RGW-full-workspace-v1 primary scores.",
        "r_rank_order": r_rank,
        "w_rank_order": w_rank,
        "rank_deltas": reversals,
    }


def write_cost_ledger(bundle_root: Path, records: Sequence[Mapping[str, Any]]) -> Path:
    path = bundle_root / "cost_ledger.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for record in records:
        cost = record.get("cost_metadata") if isinstance(record.get("cost_metadata"), Mapping) else {}
        lines.append(
            json.dumps(
                {
                    "run_id": record.get("run_id"),
                    "axis": record.get("axis"),
                    "task_id": record.get("task_id"),
                    "acut_id": record.get("acut_id"),
                    "attempt": record.get("attempt"),
                    **dict(cost),
                },
                sort_keys=True,
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def repo_relative_artifact_path(path: Path) -> str:
    resolved = path.resolve()
    repo_root = REPO_ROOT.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return os.path.relpath(resolved, repo_root)


def write_manifest(bundle_root: Path, records: Sequence[Mapping[str, Any]], design: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    raw_files = (
        sorted(repo_relative_artifact_path(path) for path in (bundle_root / "raw").rglob("*") if path.is_file())
        if (bundle_root / "raw").exists()
        else []
    )
    normalized = sorted(repo_relative_artifact_path(path) for path in normalized_files(bundle_root))
    manifest = {
        "schema_version": "core-narrative.rgw-artifact-manifest.v1",
        "generated_at": iso_now(),
        "experiment_id": RUNNER_ID,
        "config": repo_relative_artifact_path(config_path),
        "fixed_denominator": {
            "rbench": len(design["rbench"]) * len(design["acuts"]),
            "rwork": len(design["rwork"]) * len(design["acuts"]),
            "general": len(design["general"]) * len(design["acuts"]),
            "total": len(design["rbench"]) * len(design["acuts"]) + len(design["rwork"]) * len(design["acuts"]) + len(design["general"]) * len(design["acuts"]),
        },
        "raw_artifact_count": len(raw_files),
        "normalized_result_count": len(normalized),
        "raw_artifacts": raw_files,
        "normalized_results": normalized,
        "result_run_ids": sorted(str(record.get("run_id")) for record in records),
    }
    write_json(bundle_root / "raw_artifacts_manifest.json", manifest)
    return manifest


def threats_to_validity(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# RGW-full-workspace-v1 Threats To Validity",
            "",
            "- The primary RGW bundle is separated from historical M2/M3/M2.5 artifacts; historical results are not denominators or score inputs.",
            "- G-score cells remain non-comparable until the pinned SWE-Bench Pro gold-patch path and per-task workspace/verifier materialization are proven.",
            "- Cost metadata is estimated from ACUT tier when provider token usage is unavailable in Codex CLI summaries.",
            "- A `patch_apply_error` pauses primary scoring for that cell until triage, rather than being counted as model failure.",
            "- Infrastructure statuses require rerun or a recorded global exclusion before final primary scores should be treated as complete.",
        ]
    ) + "\n"


def build_summary(design: Mapping[str, Any], bundle_root: Path, config_path: Path) -> dict[str, Any]:
    records = load_normalized_results(bundle_root)
    axes = {
        "rbench": summarize_axis(records, "rbench", design["rbench"], design["acuts"]),
        "rwork": summarize_axis(records, "rwork", design["rwork"], design["acuts"]),
        "general": summarize_axis(records, "general", design["general"], design["acuts"]),
    }
    table = by_acut_table(records, design)
    infra = [
        {
            "run_id": record.get("run_id"),
            "axis": record.get("axis"),
            "task_id": record.get("task_id"),
            "acut_id": record.get("acut_id"),
            "status": record.get("status"),
            "score_action": record.get("score_action"),
            "normalized_result": record.get("artifact_paths", {}).get("normalized_result"),
        }
        for record in records
        if record.get("requires_rerun_or_exclusion") is True
    ]
    triage = [
        {
            "run_id": record.get("run_id"),
            "axis": record.get("axis"),
            "task_id": record.get("task_id"),
            "acut_id": record.get("acut_id"),
            "status": record.get("status"),
            "normalized_result": record.get("artifact_paths", {}).get("normalized_result"),
        }
        for record in records
        if record.get("triage_paused") is True
    ]
    cost_path = write_cost_ledger(bundle_root, records)
    manifest = write_manifest(bundle_root, records, design, config_path)
    reversal = reversal_analysis(table)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "generated_at": iso_now(),
        "status": "primary_complete" if all(axis["primary_score_ready"] for axis in axes.values()) else "primary_incomplete_or_infra_blocked",
        "config": str(config_path),
        "status_semantics": {
            "primary_pass_only": ["verified_pass"],
            "fixed_denominator_zero": ["verified_fail", "no_diff", "timeout/acut", "unsafe_or_scope_violation", "acut_command_error"],
            "infrastructure_rerun_or_global_exclusion_required": [
                "verifier_infra_error",
                "base_tree_mismatch",
                "candidate_patch_extraction_error",
                "timeout/verifier_or_unknown",
            ],
            "triage_paused_before_primary_scoring": ["patch_apply_error"],
        },
        "axes": axes,
        "grw_table": table,
        "reversal_analysis": reversal,
        "infra_reruns_exclusions": {
            "count": len(infra),
            "cells": infra,
        },
        "triage_paused": {
            "count": len(triage),
            "cells": triage,
        },
        "artifacts": {
            "manifest": str(bundle_root / "raw_artifacts_manifest.json"),
            "normalized_result_matrix": str(bundle_root / "normalized_result_matrix.json"),
            "cost_ledger": str(cost_path),
            "grw_table": str(bundle_root / "grw_table.json"),
            "reversal_analysis": str(bundle_root / "reversal_analysis.json"),
            "infra_reruns_exclusions": str(bundle_root / "infra_reruns_exclusions.json"),
            "threats_to_validity": str(bundle_root / "reports/threats_to_validity.md"),
            "summary": str(bundle_root / "summary.json"),
        },
        "manifest_digest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    write_json(bundle_root / "normalized_result_matrix.json", {"records": records, "axes": axes})
    write_json(bundle_root / "grw_table.json", table)
    write_json(bundle_root / "reversal_analysis.json", reversal)
    write_json(bundle_root / "infra_reruns_exclusions.json", summary["infra_reruns_exclusions"])
    (bundle_root / "reports").mkdir(parents=True, exist_ok=True)
    (bundle_root / "reports/threats_to_validity.md").write_text(threats_to_validity(summary), encoding="utf-8")
    write_json(bundle_root / "summary.json", summary)
    return summary


def reproduction_command(args: argparse.Namespace) -> str:
    parts = [
        "PYTHONPATH=experiments/core_narrative/tools",
        "python3",
        "experiments/core_narrative/tools/codex_nfl_workspace_runner.py",
        "--config",
        str(args.config),
        "--bundle-root",
        str(args.bundle_root),
        "--run-prefix",
        str(args.run_prefix),
        "--phase",
        str(args.phase),
        "--mode",
        str(args.mode),
        "--attempt",
        str(args.attempt),
    ]
    if args.force:
        parts.append("--force")
    return " ".join(shlex.quote(part) for part in parts)


def resolve_repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def normalize_paths(args: argparse.Namespace) -> argparse.Namespace:
    args.config = str(resolve_repo_path(args.config))
    args.bundle_root = str(resolve_repo_path(args.bundle_root))
    args.workspace_root = str(resolve_repo_path(args.workspace_root))
    if args.output:
        args.output = str(resolve_repo_path(args.output))
    return args


def execute(args: argparse.Namespace) -> dict[str, Any]:
    args = normalize_paths(args)
    config_path = Path(args.config)
    design = load_frozen_design(config_path)
    bundle_root = Path(args.bundle_root)
    for path in bundle_paths(bundle_root).values():
        path.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    g6_smoke = None
    if args.phase == "g6-smoke":
        g6_smoke = run_g6_smoke(args, config_path)
    elif args.phase == "sentinels":
        for axis, task_id, acut_id in SENTINEL_CELLS:
            results.append(run_click_cell(axis=axis, task_id=task_id, acut_id=acut_id, args=args, config_path=config_path))
    elif args.phase == "primary":
        for axis, task_id, acut_id in iter_primary_cells(design):
            if axis == "general":
                continue
            results.append(run_click_cell(axis=axis, task_id=task_id, acut_id=acut_id, args=args, config_path=config_path))
        results.extend(run_general_infra_records(design=design, args=args, config_path=config_path))
    summary = build_summary(design, bundle_root, config_path)
    return {
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": "completed",
        "phase": args.phase,
        "mode": args.mode,
        "generated_at": iso_now(),
        "config": str(config_path),
        "bundle_root": str(bundle_root),
        "results_written": len(results),
        "g6_smoke_status": g6_smoke.get("status") if isinstance(g6_smoke, Mapping) else None,
        "summary": str(bundle_root / "summary.json"),
        "summary_status": summary["status"],
        "reproduction_command": reproduction_command(args),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.attempt != 1:
            raise ToolError("RGW-full-workspace-v1 freezes primary_attempts_per_acut_task at 1", attempt=args.attempt)
        payload = execute(args)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
