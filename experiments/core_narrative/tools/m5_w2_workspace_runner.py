#!/usr/bin/env python3
"""Run and summarize the M5-W2 repository-specific advantage stress test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json
from codex_nfl_workspace_runner import (
    build_acut_command,
    command_summary,
    estimate_cost_usd,
    read_acut_summary,
    workspace_python,
)
from rgw_status_semantics import WORKSPACE_MODE_STATUSES, classify_status


TOOL = "m5_w2_workspace_runner"
RUNNER_ID = "m5-w2-primary-v1"
SCHEMA_VERSION = "core-narrative.m5-w2-result.v1"
SUMMARY_SCHEMA_VERSION = "core-narrative.m5-w2-summary.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/m5_w2_matrix.yaml"
DEFAULT_BUNDLE_ROOT = REPO_ROOT / "experiments/core_narrative/results/m5_w2_primary"
DEFAULT_WORKSPACES_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/m5_w2_primary"
TASK_PACK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
WORKSPACE_MODE_RUNNER = REPO_ROOT / "experiments/core_narrative/tools/workspace_mode_runner.py"
EXPECTED_ACUTS = (
    "cheap-generic-swe",
    "cheap-click-specialist",
    "cheap-click-deep-specialist-v2",
    "frontier-generic-swe",
)
DEEP_SPECIALIST = "cheap-click-deep-specialist-v2"
CHEAP_GENERIC = "cheap-generic-swe"
FRONTIER_GENERIC = "frontier-generic-swe"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--bundle-root", default=str(DEFAULT_BUNDLE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACES_ROOT))
    parser.add_argument("--run-prefix", default="m5_w2_20260513")
    parser.add_argument("--phase", choices=("primary", "summary"), default="summary")
    parser.add_argument("--mode", choices=("live", "dry-run"), default="live")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--acut-timeout-seconds", type=int, default=3600)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--install-workspaces", action="store_true", default=True)
    parser.add_argument("--no-install-workspaces", dest="install_workspaces", action="store_false")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", help="Optional command output JSON.")
    return parser.parse_args(list(argv) if argv is not None else None)


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


def repo_relative_artifact_path(path: Path) -> str:
    resolved = path.resolve()
    repo_root = REPO_ROOT.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return os.path.relpath(resolved, repo_root)


def task_manifest_path(task_id: str) -> Path:
    if "__rwork__" not in task_id:
        raise ToolError("M5-W2 task id must be a Click RWork task", task_id=task_id)
    path = TASK_PACK_ROOT / "click" / "rwork" / task_id / "task.yaml"
    if not path.exists():
        raise ToolError("materialized M5-W2 task manifest is missing", task_id=task_id, path=str(path))
    return path


def acut_manifest_path(acut_id: str) -> Path:
    path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
    if not path.exists():
        raise ToolError("ACUT manifest does not exist", acut_id=acut_id, path=str(path))
    return path


def task_ids_from_manifest(path: Path) -> list[str]:
    manifest = load_manifest(path)
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ToolError("RWork-v2 manifest has no tasks list", manifest=str(path))
    task_ids: list[str] = []
    for item in tasks:
        if not isinstance(item, Mapping) or not isinstance(item.get("task_id"), str):
            continue
        task_id = str(item["task_id"])
        if "__rwork__" not in task_id:
            raise ToolError("RWork-v2 manifest contains non-RWork task", task_id=task_id)
        task_ids.append(task_id)
    return task_ids


def load_w2_design(config_path: Path) -> dict[str, Any]:
    config = load_manifest(config_path)
    acuts = list(config.get("acuts") or [])
    if acuts != list(EXPECTED_ACUTS):
        raise ToolError("M5-W2 ACUT order does not match the preregistered matrix", expected=list(EXPECTED_ACUTS), observed=acuts)
    if int(config.get("primary_attempts_per_acut_task") or 0) != 1:
        raise ToolError("M5-W2 primary attempts must be one", observed=config.get("primary_attempts_per_acut_task"))
    if config.get("best_of_n") is not False:
        raise ToolError("M5-W2 config must disable best-of-N", observed=config.get("best_of_n"))
    if config.get("fixed_denominator") is not True:
        raise ToolError("M5-W2 config must use fixed denominators", observed=config.get("fixed_denominator"))

    rwork = config.get("rwork_v2") if isinstance(config.get("rwork_v2"), Mapping) else {}
    manifest_value = rwork.get("manifest")
    if not isinstance(manifest_value, str):
        raise ToolError("M5-W2 config is missing rwork_v2.manifest")
    task_ids = task_ids_from_manifest(REPO_ROOT / manifest_value)
    task_count = int(rwork.get("task_count") or 0)
    if task_count != len(task_ids) or task_count != 10:
        raise ToolError("M5-W2 RWork-v2 denominator must be 10", configured=task_count, observed=len(task_ids))

    expected_attempts = config.get("primary_matrix", {}).get("expected_attempts", {})
    observed_attempts = len(task_ids) * len(acuts)
    if expected_attempts.get("rwork_v2") != observed_attempts or expected_attempts.get("total") != observed_attempts:
        raise ToolError(
            "M5-W2 expected attempts mismatch",
            expected=expected_attempts,
            observed={"rwork_v2": observed_attempts, "total": observed_attempts},
        )
    seed = str(config.get("primary_matrix", {}).get("shuffle_seed") or "m5-w2")
    return {"config": config, "acuts": acuts, "tasks": task_ids, "shuffle_seed": seed}


def cell_sort_key(seed: str, axis: str, task_id: str, acut_id: str) -> tuple[str, str, str, str]:
    digest = hashlib.sha256(f"{seed}\n{axis}\n{task_id}\n{acut_id}".encode("utf-8")).hexdigest()
    return digest, axis, task_id, acut_id


def iter_primary_cells(design: Mapping[str, Any]) -> Iterable[tuple[str, str, str]]:
    cells = [
        ("w2", str(task_id), str(acut_id))
        for task_id in design["tasks"]
        for acut_id in design["acuts"]
    ]
    seed = str(design["shuffle_seed"])
    yield from sorted(cells, key=lambda cell: cell_sort_key(seed, *cell))


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


def workspace_mode_command(
    *,
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


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def source_derived_private_replay(payload: Mapping[str, Any]) -> bool:
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
    policy = candidate.get("unsafe_content_policy") if isinstance(candidate.get("unsafe_content_policy"), Mapping) else {}
    return (
        metadata.get("replay_patch_private") is True
        or candidate.get("private_replay_allowed") is True
        or policy.get("decision") == "allow_private_replay_source_derived_url_only"
    )


def true_unsafe(payload: Mapping[str, Any]) -> bool:
    if str(payload.get("status")) != "unsafe_or_scope_violation":
        return False
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    policy = candidate.get("unsafe_content_policy") if isinstance(candidate.get("unsafe_content_policy"), Mapping) else {}
    return policy.get("decision") != "allow_private_replay_source_derived_url_only"


def normalized_from_workspace_payload(
    *,
    payload: Mapping[str, Any],
    config_path: Path,
    command: Mapping[str, Any],
    artifact_dir: Path,
    normalized_path: Path,
) -> dict[str, Any]:
    status = str(payload.get("status"))
    classification = classify_status(status, payload)
    acut_id = str(payload.get("acut_id"))
    acut_summary = read_acut_summary(artifact_dir)
    model_call_made = acut_summary.get("model_call_made") is True if isinstance(acut_summary, Mapping) else False
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    verification = payload.get("verification") if isinstance(payload.get("verification"), Mapping) else {}
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
    normalized = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "run_id": payload.get("run_id"),
        "axis": "w2",
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
        "candidate_patch": {
            "path": candidate.get("path") or str(artifact_dir / "candidate.patch"),
            "sha256": candidate.get("sha256"),
            "size_bytes": candidate.get("size_bytes"),
            "raw_candidate_patch_size_bytes": candidate.get("raw_candidate_patch_size_bytes"),
            "has_scoreable_diff": candidate.get("has_scoreable_diff"),
            "redacted_preview": candidate.get("redacted_preview"),
            "private_replay_allowed": candidate.get("private_replay_allowed"),
            "replay_patch_private": metadata.get("replay_patch_private"),
            "unsafe_content_policy": candidate.get("unsafe_content_policy"),
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
            "workspace_runner_command": str(artifact_dir / "workspace_runner_command.json"),
            "candidate_patch": str(artifact_dir / "candidate.patch"),
            "acut_summary": str(artifact_dir / "codex_cli_patch_command.json")
            if (artifact_dir / "codex_cli_patch_command.json").exists()
            else None,
            "normalized_result": str(normalized_path),
        },
        "command_lines": {
            "workspace_runner": command.get("command"),
            "config": str(config_path),
        },
        "cost_metadata": {
            "model_call_made": model_call_made,
            "estimated_cost_usd": estimate_cost_usd(acut_id, model_call_made),
            "actual_cost_usd": None,
            "cost_source": "estimated_by_acut_tier; codex_cli_patch_command does not expose token usage",
        },
        "secondary_flags": {
            "source_derived_private_replay": source_derived_private_replay(payload),
            "true_unsafe": true_unsafe(payload),
            "policy_hold": status == "unsafe_or_scope_violation",
        },
        "error": payload.get("error"),
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


def fallback_payload(
    *,
    run_id: str,
    task_id: str,
    acut_id: str,
    attempt: int,
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    timed_out = bool(summary.get("timed_out") or summary.get("exit_code") == 124)
    return {
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": "rwork",
        "attempt": attempt,
        "status": "timeout" if timed_out else "verifier_infra_error",
        "metadata": {"timeout_owner": "verifier" if timed_out else None},
        "candidate_patch": {},
        "verification": {"attempted": False},
        "started_at": summary.get("started_at"),
        "finished_at": summary.get("finished_at"),
        "duration_seconds": summary.get("duration_seconds"),
        "error": summary.get("command_error") or "workspace_mode_runner did not emit output",
    }


def run_w2_cell(
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
        payload = fallback_payload(run_id=run_id, task_id=task_id, acut_id=acut_id, attempt=args.attempt, summary=summary)
    return normalized_from_workspace_payload(
        payload=payload,
        config_path=config_path,
        command=summary,
        artifact_dir=artifact_dir,
        normalized_path=normalized_path,
    )


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


def is_dry_run_record(record: Mapping[str, Any]) -> bool:
    run_id = record.get("run_id")
    if isinstance(run_id, str) and "__dry-run__" in run_id:
        return True
    command_lines = record.get("command_lines") if isinstance(record.get("command_lines"), Mapping) else {}
    workspace_runner = command_lines.get("workspace_runner") if isinstance(command_lines, Mapping) else None
    return isinstance(workspace_runner, list) and "--dry-run" in {str(part) for part in workspace_runner}


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
    tasks: Sequence[str],
    acuts: Sequence[str],
) -> tuple[set[tuple[str, str]], dict[tuple[str, str], Mapping[str, Any]]]:
    expected_cells = {(str(acut), str(task_id)) for acut in acuts for task_id in tasks}
    by_cell: dict[tuple[str, str], tuple[tuple[str, int, str, int], Mapping[str, Any]]] = {}
    for sequence, record in enumerate(records):
        if record.get("axis") != "w2" or is_dry_run_record(record):
            continue
        key = (str(record.get("acut_id")), str(record.get("task_id")))
        if key not in expected_cells:
            continue
        recency_key = evidence_recency_key(record, sequence)
        current = by_cell.get(key)
        if current is None or recency_key > current[0]:
            by_cell[key] = (recency_key, record)
    return expected_cells, {key: record for key, (_, record) in by_cell.items()}


def flags(record: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return record.get("secondary_flags") if isinstance(record, Mapping) and isinstance(record.get("secondary_flags"), Mapping) else {}


def summarize_by_acut(
    by_cell: Mapping[tuple[str, str], Mapping[str, Any]],
    tasks: Sequence[str],
    acuts: Sequence[str],
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for acut in acuts:
        records = [by_cell[(str(acut), str(task_id))] for task_id in tasks if (str(acut), str(task_id)) in by_cell]
        scored = [record for record in records if isinstance(record.get("score_value"), int)]
        passed = sum(1 for record in scored if record.get("score_value") == 1)
        infra = [record for record in records if record.get("requires_rerun_or_exclusion") is True]
        triage = [record for record in records if record.get("triage_paused") is True]
        denominator = len(tasks)
        rows[str(acut)] = {
            "acut_id": str(acut),
            "present_cells": len(records),
            "missing_cells": denominator - len(records),
            "fixed_denominator": denominator,
            "effective_denominator_after_recorded_global_infra_exclusions": denominator - len(infra),
            "verified_pass": passed,
            "W2_verified_score": passed,
            "score_percent_fixed": 100.0 * passed / denominator if denominator else None,
            "primary_score_ready": len(records) == denominator and not infra and not triage,
            "status_counts": count_by(records, "status"),
            "no_diff_count": sum(1 for record in records if record.get("status") == "no_diff"),
            "true_unsafe_count": sum(1 for record in records if flags(record).get("true_unsafe") is True),
            "policy_hold_count": sum(1 for record in records if flags(record).get("policy_hold") is True),
            "source_derived_private_replay_count": sum(1 for record in records if flags(record).get("source_derived_private_replay") is True),
        }
    return rows


def paired_comparison(
    *,
    by_cell: Mapping[tuple[str, str], Mapping[str, Any]],
    tasks: Sequence[str],
    subject_acut: str,
    baseline_acut: str,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    wins = losses = ties = unscored = 0
    for task_id in tasks:
        subject = by_cell.get((subject_acut, str(task_id)))
        baseline = by_cell.get((baseline_acut, str(task_id)))
        subject_score = subject.get("score_value") if isinstance(subject, Mapping) else None
        baseline_score = baseline.get("score_value") if isinstance(baseline, Mapping) else None
        if not isinstance(subject_score, int) or not isinstance(baseline_score, int):
            outcome = "unscored"
            unscored += 1
        elif subject_score > baseline_score:
            outcome = "win"
            wins += 1
        elif subject_score < baseline_score:
            outcome = "loss"
            losses += 1
        else:
            outcome = "tie"
            ties += 1
        cells.append(
            {
                "task_id": str(task_id),
                "subject_score": subject_score,
                "baseline_score": baseline_score,
                "outcome": outcome,
            }
        )
    return {
        "subject_acut": subject_acut,
        "baseline_acut": baseline_acut,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "unscored": unscored,
        "cells": cells,
    }


def gate_analysis(rows: Mapping[str, Mapping[str, Any]], primary_ready: bool) -> dict[str, Any]:
    deep = rows.get(DEEP_SPECIALIST, {})
    cheap = rows.get(CHEAP_GENERIC, {})
    frontier = rows.get(FRONTIER_GENERIC, {})
    deep_score = deep.get("W2_verified_score")
    cheap_score = cheap.get("W2_verified_score")
    frontier_score = frontier.get("W2_verified_score")
    if not primary_ready or not all(isinstance(value, int) for value in (deep_score, cheap_score, frontier_score)):
        return {
            "status": "not_computable",
            "reason": "W2 primary matrix is missing, infrastructure-blocked, or triage-paused.",
            "context_effect": {"passed": None, "expression": f"{DEEP_SPECIALIST} >= {CHEAP_GENERIC} + 2 tasks"},
            "nfl_candidate": {"passed": None, "expression": f"{DEEP_SPECIALIST} > {FRONTIER_GENERIC}"},
            "next_action": "complete_or_repair_W2_primary_matrix",
        }
    context_passed = int(deep_score) >= int(cheap_score) + 2
    nfl_passed = int(deep_score) > int(frontier_score)
    if context_passed and nfl_passed:
        status = "passed"
        next_action = "design_R2_before_any_ACUT_G"
    else:
        status = "failed"
        next_action = "stop_and_write_negative_result"
    return {
        "status": status,
        "context_effect": {
            "passed": context_passed,
            "deep_score": deep_score,
            "cheap_generic_score": cheap_score,
            "margin_tasks": int(deep_score) - int(cheap_score),
            "expression": f"{DEEP_SPECIALIST} >= {CHEAP_GENERIC} + 2 tasks",
        },
        "nfl_candidate": {
            "passed": nfl_passed,
            "deep_score": deep_score,
            "frontier_generic_score": frontier_score,
            "margin_tasks": int(deep_score) - int(frontier_score),
            "expression": f"{DEEP_SPECIALIST} > {FRONTIER_GENERIC}",
        },
        "next_action": next_action,
    }


def write_cost_ledger(bundle_root: Path, records: Sequence[Mapping[str, Any]]) -> Path:
    path = bundle_root / "cost_ledger.jsonl"
    lines = []
    for record in records:
        cost = record.get("cost_metadata") if isinstance(record.get("cost_metadata"), Mapping) else {}
        normalized_cost = {
            str(key): repo_relative_artifact_path(Path(value)) if isinstance(value, str) and Path(value).is_absolute() else value
            for key, value in cost.items()
        }
        lines.append(
            json.dumps(
                {
                    "run_id": record.get("run_id"),
                    "axis": record.get("axis"),
                    "task_id": record.get("task_id"),
                    "acut_id": record.get("acut_id"),
                    "attempt": record.get("attempt"),
                    **normalized_cost,
                },
                sort_keys=True,
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def write_manifest(bundle_root: Path, records: Sequence[Mapping[str, Any]], design: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    raw_files = (
        sorted(repo_relative_artifact_path(path) for path in (bundle_root / "raw").rglob("*") if path.is_file())
        if (bundle_root / "raw").exists()
        else []
    )
    normalized = sorted(repo_relative_artifact_path(path) for path in normalized_files(bundle_root))
    manifest = {
        "schema_version": "core-narrative.m5-w2-artifact-manifest.v1",
        "generated_at": iso_now(),
        "experiment_id": RUNNER_ID,
        "config": repo_relative_artifact_path(config_path),
        "fixed_denominator": {"w2": len(design["tasks"]) * len(design["acuts"])},
        "raw_artifact_count": len(raw_files),
        "normalized_result_count": len(normalized),
        "raw_artifacts": raw_files,
        "normalized_results": normalized,
        "result_run_ids": sorted(str(record.get("run_id")) for record in records),
    }
    write_json(bundle_root / "raw_artifacts_manifest.json", manifest)
    return manifest


def build_summary(design: Mapping[str, Any], bundle_root: Path, config_path: Path) -> dict[str, Any]:
    records = load_normalized_results(bundle_root)
    expected_cells, by_cell = canonical_records_by_cell(records, design["tasks"], design["acuts"])
    cells: list[dict[str, Any]] = []
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
    infra = [cell for cell in present if cell["score_action"] == "rerun_or_global_exclusion_required"]
    triage = [cell for cell in present if cell["score_action"] == "triage_paused_before_primary_scoring"]
    primary_ready = len(present) == len(expected_cells) and not infra and not triage
    by_acut = summarize_by_acut(by_cell, design["tasks"], design["acuts"])
    paired = {
        "deep_vs_cheap_generic": paired_comparison(
            by_cell=by_cell,
            tasks=design["tasks"],
            subject_acut=DEEP_SPECIALIST,
            baseline_acut=CHEAP_GENERIC,
        ),
        "deep_vs_frontier_generic": paired_comparison(
            by_cell=by_cell,
            tasks=design["tasks"],
            subject_acut=DEEP_SPECIALIST,
            baseline_acut=FRONTIER_GENERIC,
        ),
    }
    gates = gate_analysis(by_acut, primary_ready)
    status = "w2_primary_complete_gate_passed" if primary_ready and gates["status"] == "passed" else (
        "w2_primary_complete_gate_failed" if primary_ready else "w2_primary_incomplete_or_infra_blocked"
    )
    cost_path = write_cost_ledger(bundle_root, records)
    manifest = write_manifest(bundle_root, records, design, config_path)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "tool": TOOL,
        "runner_id": RUNNER_ID,
        "generated_at": iso_now(),
        "status": status,
        "config": repo_relative_artifact_path(config_path),
        "fixed_denominator": len(expected_cells),
        "present_cells": len(present),
        "missing_cells": len(expected_cells) - len(present),
        "primary_score_ready": primary_ready,
        "status_counts": count_by(cells, "status"),
        "score_action_counts": count_by(cells, "score_action"),
        "w2_by_acut": by_acut,
        "paired_metrics": paired,
        "gates": gates,
        "infra_reruns_exclusions": {"count": len(infra), "cells": infra},
        "triage_paused": {"count": len(triage), "cells": triage},
        "cells": cells,
        "artifacts": {
            "manifest": repo_relative_artifact_path(bundle_root / "raw_artifacts_manifest.json"),
            "normalized_result_matrix": repo_relative_artifact_path(bundle_root / "normalized_result_matrix.json"),
            "cost_ledger": repo_relative_artifact_path(cost_path),
            "summary": repo_relative_artifact_path(bundle_root / "summary.json"),
            "report": repo_relative_artifact_path(bundle_root / "reports/w2_primary_summary.md"),
        },
        "manifest_digest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    write_json(bundle_root / "normalized_result_matrix.json", {"records": records, "cells": cells})
    (bundle_root / "reports").mkdir(parents=True, exist_ok=True)
    (bundle_root / "reports/w2_primary_summary.md").write_text(report_markdown(summary), encoding="utf-8")
    write_json(bundle_root / "summary.json", summary)
    return summary


def report_markdown(summary: Mapping[str, Any]) -> str:
    rows = summary.get("w2_by_acut") if isinstance(summary.get("w2_by_acut"), Mapping) else {}
    table_lines = [
        "| ACUT | W2 score | Ready | Status counts |",
        "|---|---:|---:|---|",
    ]
    for acut in EXPECTED_ACUTS:
        row = rows.get(acut) if isinstance(rows.get(acut), Mapping) else {}
        table_lines.append(
            f"| `{acut}` | `{row.get('W2_verified_score')}` / `{row.get('fixed_denominator')}` | `{row.get('primary_score_ready')}` | `{json.dumps(row.get('status_counts') or {}, sort_keys=True)}` |"
        )
    gates = summary.get("gates") if isinstance(summary.get("gates"), Mapping) else {}
    return "\n".join(
        [
            "# M5-W2 Primary Summary",
            "",
            f"Status: `{summary.get('status')}`",
            f"Generated at: `{summary.get('generated_at')}`",
            f"Primary score ready: `{summary.get('primary_score_ready')}`",
            "",
            "## Scores",
            "",
            *table_lines,
            "",
            "## Gates",
            "",
            f"- Gate status: `{gates.get('status')}`",
            f"- Next action: `{gates.get('next_action')}`",
            f"- Context effect: `{json.dumps(gates.get('context_effect') or {}, sort_keys=True)}`",
            f"- NFL candidate: `{json.dumps(gates.get('nfl_candidate') or {}, sort_keys=True)}`",
            "",
            "## Claim Boundary",
            "",
            "This report is W2 primary evidence only. It does not claim R2 or ACUT G results.",
            "",
        ]
    )


def reproduction_command(args: argparse.Namespace) -> str:
    parts = [
        "PYTHONPATH=experiments/core_narrative/tools",
        "python3",
        "experiments/core_narrative/tools/m5_w2_workspace_runner.py",
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


def execute(args: argparse.Namespace) -> dict[str, Any]:
    args = normalize_paths(args)
    if args.attempt != 1:
        raise ToolError("M5-W2 freezes primary_attempts_per_acut_task at 1", attempt=args.attempt)
    config_path = Path(args.config)
    design = load_w2_design(config_path)
    bundle_root = Path(args.bundle_root)
    for path in bundle_paths(bundle_root).values():
        path.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    if args.phase == "primary":
        for axis, task_id, acut_id in iter_primary_cells(design):
            results.append(run_w2_cell(axis=axis, task_id=task_id, acut_id=acut_id, args=args, config_path=config_path))
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
        "summary": str(bundle_root / "summary.json"),
        "summary_status": summary["status"],
        "reproduction_command": reproduction_command(args),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = execute(args)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
