#!/usr/bin/env python3
"""Prepare, run, and score Phase 2 external E ACUT attempts for SymPy."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as admission
import external_calibrated_swebench_smoke as smoke
from _common import ToolError, emit_json, fail, git, iso_now, load_manifest, slug, write_json
from _llm_budget import llm_safe_subprocess_env, redact_sensitive_text
from workspace_mode_runner import (
    collect_candidate_patch_from_workspace,
    run_capture_artifacts,
    workspace_refs,
)


TOOL = "external_calibrated_e_runner"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.e-runner.v1"
SCORE_SCHEMA_VERSION = "external-calibrated-repo-benchmark.e-score-table.v1"
TASK_MANIFEST_SCHEMA_VERSION = "external-calibrated-repo-benchmark.e-private-task.v1"
PROTOCOL_ID = admission.PROTOCOL_ID
REPO_ROOT = admission.REPO_ROOT
CONFIG_ROOT = REPO_ROOT / "experiments/core_narrative/configs"
RESULTS_ROOT = admission.RESULTS_ROOT
REPORTS_ROOT = admission.REPORTS_ROOT
PREPARE_WORKSPACE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
CODEX_PATCH_COMMAND = REPO_ROOT / "experiments/core_narrative/tools/codex_cli_patch_command.py"

DEFAULT_PROTOCOL = CONFIG_ROOT / "external_calibrated_benchmark_20260515.yaml"
DEFAULT_E_CONFIG = CONFIG_ROOT / "external/swebench_sympy_e_v1.yaml"
DEFAULT_MATRIX = CONFIG_ROOT / "external/sympy_external_acut_execution_matrix_v1.yaml"
DEFAULT_SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/sympy"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/external_calibrated_e_primary_20260516"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/external_calibrated_e_primary_20260516"
DEFAULT_OUTPUT = RESULTS_ROOT / "external_e_primary/external_calibrated_e_phase2_run_20260516.json"
DEFAULT_REPORT = REPORTS_ROOT / "external_e_primary_run_report.md"
DEFAULT_SCORE_OUTPUT = RESULTS_ROOT / "external_e_primary/e_score_table_20260516.json"
DEFAULT_DATASET = "SWE-bench/SWE-bench_Verified"
DEFAULT_SPLIT = "test"
DEFAULT_SWEBENCH_PYTHON = REPO_ROOT / "experiments/core_narrative/cache/swebench_eval_py313_venv/bin/python"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prepare", "run", "score"), default="prepare")
    parser.add_argument("--mode", choices=("dry-run", "live"), default="dry-run")
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--e-config", default=str(DEFAULT_E_CONFIG))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--source-repo", default=str(DEFAULT_SOURCE_REPO))
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--swebench-python", default=str(DEFAULT_SWEBENCH_PYTHON))
    parser.add_argument("--score-output", default=str(DEFAULT_SCORE_OUTPUT))
    parser.add_argument("--acut-slot", action="append", help="Filter matrix cells by ACUT slot. May be repeated.")
    parser.add_argument("--acut-id", action="append", help="Filter matrix cells by ACUT id. May be repeated.")
    parser.add_argument("--instance-id", action="append", help="Filter matrix cells by SWE-bench instance id. May be repeated.")
    parser.add_argument("--run-id", action="append", help="Filter by frozen run id. May be repeated.")
    parser.add_argument("--limit", type=int, help="Limit selected cells after filters, preserving frozen matrix order.")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-provider-mode", choices=("default", "barcarolle"), default="default")
    parser.add_argument("--acut-timeout-seconds", type=int, default=3600)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900, help="SWE-bench per-instance timeout.")
    parser.add_argument("--command-timeout", type=int, default=7200, help="Overall SWE-bench subprocess timeout.")
    parser.add_argument("--cache-level", choices=("none", "base", "env", "instance"), default="base")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    return admission.repo_relative(path)


def sha256_text(value: str) -> str:
    return admission.sha256_text(value)


def path_from_repo(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def ensure_positive_limit(limit: int | None) -> None:
    if limit is not None and limit < 1:
        raise ToolError("--limit must be at least 1", limit=limit)


def frozen_e_tasks(e_config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    tasks = e_config.get("tasks") if isinstance(e_config.get("tasks"), list) else []
    result: dict[str, Mapping[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, Mapping) or task.get("smoke_status") != "gold_resolved":
            continue
        instance_id = task.get("instance_id")
        if isinstance(instance_id, str) and instance_id:
            result[instance_id] = task
    return result


def dataset_rows_by_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("instance_id")): row for row in rows if row.get("instance_id")}


def select_run_cells(
    matrix: Mapping[str, Any],
    *,
    acut_slots: Sequence[str] | None = None,
    acut_ids: Sequence[str] | None = None,
    instance_ids: Sequence[str] | None = None,
    run_ids: Sequence[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    ensure_positive_limit(limit)
    cells = matrix.get("phase2_e_cells") if isinstance(matrix.get("phase2_e_cells"), list) else []
    slot_filter = set(acut_slots or [])
    acut_filter = set(acut_ids or [])
    instance_filter = set(instance_ids or [])
    run_filter = set(run_ids or [])
    selected: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        if slot_filter and cell.get("acut_slot") not in slot_filter:
            continue
        if acut_filter and cell.get("acut_id") not in acut_filter:
            continue
        if instance_filter and cell.get("task_id") not in instance_filter:
            continue
        if run_filter and cell.get("run_id") not in run_filter:
            continue
        attempt = int(cell.get("attempt", 0) or 0)
        if attempt != 1:
            raise ToolError("frozen E matrix contains a non-primary attempt", run_id=cell.get("run_id"), attempt=attempt)
        selected.append(dict(cell))
        if limit is not None and len(selected) >= limit:
            break
    return selected


def profile_dir_from_matrix(matrix: Mapping[str, Any]) -> Path:
    raw = matrix.get("profile_dir")
    if not isinstance(raw, str) or not raw:
        raise ToolError("ACUT matrix is missing profile_dir")
    return path_from_repo(raw)


def profile_path_for_cell(matrix: Mapping[str, Any], cell: Mapping[str, Any]) -> Path:
    acut_id = str(cell.get("acut_id") or "")
    if not acut_id:
        raise ToolError("matrix cell is missing acut_id", run_id=cell.get("run_id"))
    return profile_dir_from_matrix(matrix) / f"{acut_id}.yaml"


def materialize_private_task_pack(
    row: Mapping[str, Any],
    frozen_task: Mapping[str, Any],
    *,
    private_root: Path,
    dataset_name: str,
    split: str,
    repo_slug: str = "sympy",
) -> dict[str, Any]:
    instance_id = str(row.get("instance_id") or frozen_task.get("instance_id") or "")
    if not instance_id:
        raise ToolError("dataset row is missing instance_id")
    base_commit = str(row.get("base_commit") or "")
    if not base_commit:
        raise ToolError("dataset row is missing base_commit", instance_id=instance_id)
    problem_statement = str(row.get("problem_statement") or "")
    if not problem_statement:
        raise ToolError("dataset row is missing problem_statement", instance_id=instance_id)

    task_pack_dir = private_root / "task_packs" / slug(instance_id)
    public_dir = task_pack_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    statement_path = public_dir / "statement.md"
    statement_path.write_text(problem_statement, encoding="utf-8")
    manifest_path = task_pack_dir / "task.json"
    task_manifest = {
        "schema_version": TASK_MANIFEST_SCHEMA_VERSION,
        "task_id": instance_id,
        "repo_slug": repo_slug,
        "split": "external_e",
        "task_family": frozen_task.get("family_if_available") or "unknown",
        "task_statement_path": "public/statement.md",
        "source": {
            "kind": "swebench_verified",
            "anchor_id": instance_id,
            "base_commit": base_commit,
        },
        "allowed_context": {
            "public_task_statement": True,
            "local_repository_files": True,
            "network_resources": False,
            "swebench_gold_patch": False,
            "swebench_test_patch": False,
        },
        "metadata": {
            "protocol_id": PROTOCOL_ID,
            "dataset": dataset_name,
            "split": split,
            "repo": row.get("repo"),
            "ordinal": frozen_task.get("ordinal"),
            "raw_gold_patch_included": False,
            "raw_test_patch_included": False,
        },
    }
    write_json(manifest_path, task_manifest)
    public_record = {
        "instance_id": instance_id,
        "task_ordinal": frozen_task.get("ordinal"),
        "task_family": frozen_task.get("family_if_available"),
        "private_task_pack": repo_relative(task_pack_dir),
        "private_task_manifest": repo_relative(manifest_path),
        "problem_statement_sha256": sha256_text(problem_statement),
        "problem_statement_size_bytes": len(problem_statement.encode("utf-8")),
        "base_commit_sha256": sha256_text(base_commit),
        "raw_problem_statement_emitted": False,
        "raw_base_commit_emitted": False,
        "raw_gold_patch_emitted": False,
        "raw_test_patch_emitted": False,
    }
    return {
        "task_pack_dir": task_pack_dir,
        "task_manifest_path": manifest_path,
        "statement_path": statement_path,
        "public_record": public_record,
    }


def run_git_required(workspace: Path, *args: str, message: str) -> None:
    result = git(*args, cwd=workspace)
    if result.returncode != 0:
        raise ToolError(message, command=["git", *args], stderr=result.stderr.strip(), workspace=str(workspace))


def install_prompt_policy_reference(acut: Mapping[str, Any], workspace: Path) -> dict[str, Any]:
    raw_reference = acut.get("prompt_policy_reference")
    if not isinstance(raw_reference, str) or not raw_reference:
        return {"installed": False, "reason": "missing_prompt_policy_reference"}
    source = path_from_repo(raw_reference)
    if not source.exists():
        raise ToolError("ACUT prompt policy reference does not exist", path=repo_relative(source))
    text = source.read_text(encoding="utf-8")
    agents_path = workspace / "AGENTS.md"
    agents_path.write_text(text, encoding="utf-8")
    run_git_required(workspace, "add", "AGENTS.md", message="failed to stage ACUT AGENTS.md")
    run_git_required(
        workspace,
        "commit",
        "--no-gpg-sign",
        "-m",
        "core narrative acut prompt policy",
        message="failed to commit ACUT AGENTS.md into run base",
    )
    return {
        "installed": True,
        "workspace_path": "AGENTS.md",
        "source_reference": repo_relative(source),
        "sha256": sha256_text(text),
        "size_bytes": len(text.encode("utf-8")),
        "content_recorded_publicly": False,
        "committed_into_run_base": True,
    }


def prepare_run_workspace(
    *,
    task_path: Path,
    source_repo: Path,
    workspace: Path,
    artifact_dir: Path,
    acut: Mapping[str, Any],
) -> dict[str, Any]:
    prepare_payload_path = artifact_dir / "prepare_workspace_payload.json"
    command = [
        sys.executable,
        str(PREPARE_WORKSPACE),
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
    summary = run_capture_artifacts(command, artifact_dir=artifact_dir, name="prepare_workspace", timeout_seconds=180)
    if summary.get("exit_code") != 0 or summary.get("timed_out"):
        raise ToolError("workspace preparation failed", summary=summary)
    prepare_payload = json.loads(prepare_payload_path.read_text(encoding="utf-8"))
    policy = install_prompt_policy_reference(acut, workspace)
    base = workspace_refs(workspace)
    return {
        "workspace": workspace,
        "prepare_payload": prepare_payload,
        "prepare_command": summary,
        "prompt_policy": policy,
        "base_ref": base["base_ref"],
        "base_tree": base["base_tree"],
    }


def build_codex_patch_command(
    *,
    workspace: Path,
    acut_path: Path,
    artifact_dir: Path,
    summary_output: Path,
    codex_bin: str,
    codex_provider_mode: str,
    timeout_seconds: int,
    dry_run: bool,
) -> list[str]:
    command = [
        sys.executable,
        str(CODEX_PATCH_COMMAND),
        "--workspace",
        str(workspace),
        "--acut",
        str(acut_path),
        "--codex-provider-mode",
        codex_provider_mode,
        "--artifact-dir",
        str(artifact_dir),
        "--summary-output",
        str(summary_output),
        "--codex-bin",
        codex_bin,
        "--codex-timeout-seconds",
        str(timeout_seconds),
    ]
    if dry_run:
        command.append("--dry-run")
    return command


def public_candidate_summary(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_patch_private_path": candidate.get("path"),
        "candidate_patch_sha256": candidate.get("sha256"),
        "candidate_patch_size_bytes": candidate.get("size_bytes"),
        "raw_candidate_patch_size_bytes": candidate.get("raw_candidate_patch_size_bytes"),
        "has_scoreable_diff": bool(candidate.get("has_scoreable_diff")),
        "unsafe_content_detected": bool(candidate.get("unsafe_content_detected")),
        "private_replay_allowed": bool(candidate.get("private_replay_allowed")),
        "head_drifted": candidate.get("head_drifted"),
        "raw_patch_recorded_publicly": False,
    }


def result_status_from_acut_and_candidate(acut_summary: Mapping[str, Any], candidate: Mapping[str, Any]) -> tuple[str, str | None]:
    if acut_summary.get("timed_out") is True:
        return "timeout", "acut"
    if candidate.get("unsafe_content_detected") is True and not candidate.get("private_replay_allowed"):
        return "unsafe_or_scope_violation", None
    if candidate.get("has_scoreable_diff"):
        return "patch_ready_for_swebench", None
    if acut_summary.get("command_error"):
        return "acut_command_error", None
    if acut_summary.get("exit_code") not in (0, None):
        return "acut_command_error", None
    return "no_diff", None


def run_one_cell(
    cell: Mapping[str, Any],
    *,
    row: Mapping[str, Any],
    frozen_task: Mapping[str, Any],
    matrix: Mapping[str, Any],
    source_repo: Path,
    private_root: Path,
    workspace_root: Path,
    dataset_name: str,
    split: str,
    mode: str,
    codex_bin: str,
    codex_provider_mode: str,
    acut_timeout_seconds: int,
) -> dict[str, Any]:
    run_id = str(cell["run_id"])
    acut_path = profile_path_for_cell(matrix, cell)
    acut = load_manifest(acut_path)
    task_pack = materialize_private_task_pack(
        row,
        frozen_task,
        private_root=private_root,
        dataset_name=dataset_name,
        split=split,
    )
    cell_dir = private_root / "cells" / slug(run_id)
    cell_dir.mkdir(parents=True, exist_ok=True)
    started_at = iso_now()
    if mode == "dry-run":
        result = {
            "schema_version": SCHEMA_VERSION,
            "tool": TOOL,
            "protocol_id": PROTOCOL_ID,
            "phase": "e",
            "mode": mode,
            "status": "dry_run_ready",
            "run_id": run_id,
            "instance_id": cell.get("task_id"),
            "acut_id": cell.get("acut_id"),
            "acut_slot": cell.get("acut_slot"),
            "attempt": cell.get("attempt"),
            "model_call_made": False,
            "started_at": started_at,
            "finished_at": iso_now(),
            "private_artifact_dir": repo_relative(cell_dir),
            "task_pack": task_pack["public_record"],
            "acut_manifest": repo_relative(acut_path),
            "raw_patch_recorded_publicly": False,
        }
        write_json(cell_dir / "cell_result_private.json", result)
        return result

    workspace = workspace_root / slug(run_id)
    prepare = prepare_run_workspace(
        task_path=task_pack["task_manifest_path"],
        source_repo=source_repo,
        workspace=workspace,
        artifact_dir=cell_dir,
        acut=acut,
    )
    codex_artifact_dir = cell_dir / "codex_cli_patch_command"
    codex_summary_path = cell_dir / "codex_cli_patch_command_summary.json"
    command = build_codex_patch_command(
        workspace=workspace,
        acut_path=acut_path,
        artifact_dir=codex_artifact_dir,
        summary_output=codex_summary_path,
        codex_bin=codex_bin,
        codex_provider_mode=codex_provider_mode,
        timeout_seconds=acut_timeout_seconds,
        dry_run=False,
    )
    safe_env, _scrubbed_count = llm_safe_subprocess_env(os.environ)
    acut_summary = run_capture_artifacts(
        command,
        artifact_dir=cell_dir,
        name="codex_patch_command",
        cwd=workspace,
        timeout_seconds=acut_timeout_seconds + 90,
        env=safe_env,
    )
    try:
        candidate = collect_candidate_patch_from_workspace(
            workspace=workspace,
            patch_path=cell_dir / "candidate.patch",
            base_ref=str(prepare["base_ref"]),
            base_tree=str(prepare["base_tree"]),
            env=safe_env,
            status_path=cell_dir / "run_workspace.status",
        )
        extraction_error = None
    except Exception as exc:
        candidate = {
            "path": str(cell_dir / "candidate.patch"),
            "sha256": None,
            "size_bytes": 0,
            "raw_candidate_patch_size_bytes": 0,
            "has_scoreable_diff": False,
            "unsafe_content_detected": False,
            "private_replay_allowed": False,
            "head_drifted": None,
        }
        extraction_error = str(exc)

    if extraction_error is not None:
        status = "candidate_patch_extraction_error"
        timeout_owner = None
    else:
        status, timeout_owner = result_status_from_acut_and_candidate(acut_summary, candidate)
    finished_at = iso_now()
    result = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "phase": "e",
        "mode": mode,
        "status": status,
        "run_id": run_id,
        "instance_id": cell.get("task_id"),
        "acut_id": cell.get("acut_id"),
        "acut_slot": cell.get("acut_slot"),
        "attempt": cell.get("attempt"),
        "model_call_made": True,
        "started_at": started_at,
        "finished_at": finished_at,
        "private_artifact_dir": repo_relative(cell_dir),
        "workspace": repo_relative(workspace),
        "task_pack": task_pack["public_record"],
        "acut_manifest": repo_relative(acut_path),
        "prepare": {
            "workspace": repo_relative(workspace),
            "base_ref_sha256": sha256_text(str(prepare["base_ref"])),
            "base_tree": prepare["base_tree"],
            "prompt_policy": prepare["prompt_policy"],
        },
        "acut_command": {
            "exit_code": acut_summary.get("exit_code"),
            "timed_out": acut_summary.get("timed_out"),
            "duration_seconds": acut_summary.get("duration_seconds"),
            "summary_artifact": acut_summary.get("summary_artifact"),
            "stdout_artifact": acut_summary.get("stdout_artifact"),
            "stderr_artifact": acut_summary.get("stderr_artifact"),
        },
        "candidate_patch": public_candidate_summary(candidate),
        "timeout_owner": timeout_owner,
        "extraction_error": extraction_error,
        "raw_patch_recorded_publicly": False,
        "ready_for_swebench_scoring": status in {"patch_ready_for_swebench", "no_diff", "timeout", "acut_command_error"},
    }
    write_json(cell_dir / "cell_result_private.json", result)
    return result


def unique_tasks_for_cells(cells: Sequence[Mapping[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for cell in cells:
        task_id = str(cell.get("task_id") or "")
        if task_id and task_id not in seen:
            seen.add(task_id)
            ordered.append(task_id)
    return ordered


def prepare_task_packs(
    cells: Sequence[Mapping[str, Any]],
    *,
    rows_by_id: Mapping[str, Mapping[str, Any]],
    frozen_tasks_by_id: Mapping[str, Mapping[str, Any]],
    private_root: Path,
    dataset_name: str,
    split: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for instance_id in unique_tasks_for_cells(cells):
        row = rows_by_id.get(instance_id)
        task = frozen_tasks_by_id.get(instance_id)
        if row is None or task is None:
            raise ToolError("selected E task is missing dataset or freeze metadata", instance_id=instance_id)
        materialized = materialize_private_task_pack(
            row,
            task,
            private_root=private_root,
            dataset_name=dataset_name,
            split=split,
        )
        records.append(materialized["public_record"])
    return records


def patch_text_for_prediction(cell_result: Mapping[str, Any]) -> tuple[str, str]:
    if cell_result.get("status") != "patch_ready_for_swebench":
        return "", "empty_patch_for_non_patch_ready_status"
    candidate = cell_result.get("candidate_patch") if isinstance(cell_result.get("candidate_patch"), Mapping) else {}
    path_value = candidate.get("candidate_patch_private_path")
    if not isinstance(path_value, str) or not path_value:
        return "", "empty_patch_missing_private_path"
    patch_path = Path(path_value)
    if not patch_path.is_absolute():
        patch_path = REPO_ROOT / patch_path
    if not patch_path.exists():
        return "", "empty_patch_missing_private_file"
    return patch_path.read_text(encoding="utf-8"), "candidate_patch"


def write_predictions_jsonl(predictions: Sequence[Mapping[str, Any]], predictions_path: Path) -> dict[str, Any]:
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with predictions_path.open("w", encoding="utf-8") as handle:
        for prediction in predictions:
            model_patch = str(prediction.get("model_patch", ""))
            record = {
                "instance_id": str(prediction["instance_id"]),
                "model_name_or_path": str(prediction["model_name_or_path"]),
                "model_patch": model_patch,
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            records.append(
                {
                    "instance_id": record["instance_id"],
                    "model_name_or_path": record["model_name_or_path"],
                    "model_patch_sha256": sha256_text(model_patch),
                    "model_patch_size_bytes": len(model_patch.encode("utf-8")),
                    "model_patch_recorded_publicly": False,
                }
            )
    content = predictions_path.read_text(encoding="utf-8")
    return {
        "predictions_path": repo_relative(predictions_path),
        "prediction_count": len(records),
        "predictions_sha256": sha256_text(content),
        "records": records,
        "raw_model_patches_recorded_publicly": False,
    }


def build_prediction_records(cell_results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for result in cell_results:
        patch_text, patch_source = patch_text_for_prediction(result)
        records.append(
            {
                "run_id": result.get("run_id"),
                "instance_id": result.get("instance_id"),
                "acut_id": result.get("acut_id"),
                "acut_slot": result.get("acut_slot"),
                "model_name_or_path": result.get("acut_id"),
                "model_patch": patch_text,
                "patch_source": patch_source,
                "generation_status": result.get("status"),
            }
        )
    return records


def build_harness_command(
    *,
    python_executable: str,
    dataset_name: str,
    split: str,
    predictions_path: Path,
    instance_ids: Sequence[str],
    run_id: str,
    max_workers: int,
    timeout: int,
    cache_level: str,
) -> list[str]:
    return [
        python_executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        dataset_name,
        "--split",
        split,
        "--predictions_path",
        str(predictions_path),
        "--instance_ids",
        *instance_ids,
        "--max_workers",
        str(max_workers),
        "--timeout",
        str(timeout),
        "--cache_level",
        cache_level,
        "--run_id",
        run_id,
        "--report_dir",
        "reports",
    ]


def command_digest(value: str) -> dict[str, Any]:
    return {
        "sha256": sha256_text(value),
        "line_count": len(value.splitlines()),
        "byte_count": len(value.encode("utf-8", errors="replace")),
    }


def run_harness_command(
    command: Sequence[str],
    *,
    raw_dir: Path,
    timeout_seconds: int,
) -> tuple[subprocess.CompletedProcess[str] | None, float, str | None]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(raw_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return completed, time.monotonic() - started, None
    except subprocess.TimeoutExpired as exc:
        return None, time.monotonic() - started, f"harness command timed out after {timeout_seconds} seconds"


def load_harness_report(raw_dir: Path, *, acut_id: str, run_id: str) -> dict[str, Any]:
    report_path = raw_dir / f"{acut_id.replace('/', '__')}.{run_id}.json"
    if not report_path.exists():
        return {}
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to parse SWE-bench report", path=repo_relative(report_path), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("SWE-bench report root was not an object", path=repo_relative(report_path))
    return payload


def score_summary_from_report(
    report: Mapping[str, Any],
    predictions: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    acut_id: str,
    acut_slot: str,
) -> dict[str, Any]:
    selected = [prediction for prediction in predictions if prediction.get("acut_id") == acut_id]
    resolved = set(smoke.report_id_list(report, "resolved_ids"))
    unresolved = set(smoke.report_id_list(report, "unresolved_ids"))
    empty = set(smoke.report_id_list(report, "empty_patch_ids"))
    errors = set(smoke.report_id_list(report, "error_ids"))
    completed = set(smoke.report_id_list(report, "completed_ids"))
    cells: list[dict[str, Any]] = []
    numerator = 0
    denominator = 0
    infra_errors = 0
    for prediction in selected:
        instance_id = str(prediction.get("instance_id"))
        if instance_id in errors:
            status = "external_verifier_infra_error"
            score = None
            infra_errors += 1
        elif instance_id in resolved:
            status = "resolved"
            score = 1
            numerator += 1
            denominator += 1
        elif instance_id in empty:
            status = "empty_patch"
            score = 0
            denominator += 1
        elif instance_id in unresolved or instance_id in completed:
            status = "unresolved"
            score = 0
            denominator += 1
        else:
            status = "not_completed"
            score = None
            infra_errors += 1
        cells.append(
            {
                "run_id": prediction.get("run_id"),
                "instance_id": instance_id,
                "acut_id": acut_id,
                "acut_slot": acut_slot,
                "status": status,
                "score": score,
            }
        )
    score_rate = None if denominator == 0 else numerator / denominator
    return {
        "schema_version": SCORE_SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "run_id": run_id,
        "acut_id": acut_id,
        "acut_slot": acut_slot,
        "attempted_instances": len(selected),
        "resolved_instances": numerator,
        "score_table": [
            {
                "acut_id": acut_id,
                "acut_slot": acut_slot,
                "score_numerator": numerator,
                "score_denominator": denominator,
                "score_rate": score_rate,
                "external_verifier_infra_errors": infra_errors,
            }
        ],
        "cells": cells,
        "raw_patch_recorded_publicly": False,
        "raw_harness_logs_recorded_publicly": False,
    }


def group_predictions_by_acut(predictions: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        grouped[str(prediction.get("acut_id"))].append(dict(prediction))
    return dict(grouped)


def load_cell_results(private_root: Path, cells: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for cell in cells:
        path = private_root / "cells" / slug(str(cell["run_id"])) / "cell_result_private.json"
        if not path.exists():
            raise ToolError("cell result is missing; run Phase 2 generation before scoring", run_id=cell["run_id"], path=repo_relative(path))
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ToolError("cell result root was not an object", path=repo_relative(path))
        results.append(payload)
    return results


def score_predictions(
    *,
    cell_results: Sequence[Mapping[str, Any]],
    private_root: Path,
    dataset_name: str,
    split: str,
    python_executable: str,
    mode: str,
    max_workers: int,
    timeout: int,
    command_timeout: int,
    cache_level: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    prediction_records = build_prediction_records(cell_results)
    grouped = group_predictions_by_acut(prediction_records)
    score_summaries: list[dict[str, Any]] = []
    prediction_summaries: list[dict[str, Any]] = []
    model_calls = 0
    for acut_id, predictions in grouped.items():
        acut_slot = str(predictions[0].get("acut_slot") or "")
        run_id = f"external_calibrated_sympy_e_score_{slug(acut_slot.lower() or acut_id)}_20260516"
        predictions_path = private_root / "predictions" / f"{slug(acut_id)}.jsonl"
        prediction_summary = write_predictions_jsonl(predictions, predictions_path)
        prediction_summaries.append(prediction_summary)
        if mode == "dry-run":
            score_summaries.append(
                {
                    "schema_version": SCORE_SCHEMA_VERSION,
                    "tool": TOOL,
                    "protocol_id": PROTOCOL_ID,
                    "run_id": run_id,
                    "acut_id": acut_id,
                    "acut_slot": acut_slot,
                    "status": "dry_run_ready",
                    "prediction_summary": prediction_summary,
                    "model_calls_made": 0,
                    "harness_command": build_harness_command(
                        python_executable=python_executable,
                        dataset_name=dataset_name,
                        split=split,
                        predictions_path=predictions_path,
                        instance_ids=[str(prediction["instance_id"]) for prediction in predictions],
                        run_id=run_id,
                        max_workers=max_workers,
                        timeout=timeout,
                        cache_level=cache_level,
                    ),
                }
            )
            continue
        raw_dir = private_root / "swebench_harness" / slug(acut_id)
        command = build_harness_command(
            python_executable=python_executable,
            dataset_name=dataset_name,
            split=split,
            predictions_path=predictions_path,
            instance_ids=[str(prediction["instance_id"]) for prediction in predictions],
            run_id=run_id,
            max_workers=max_workers,
            timeout=timeout,
            cache_level=cache_level,
        )
        completed, duration, timeout_error = run_harness_command(command, raw_dir=raw_dir, timeout_seconds=command_timeout)
        report = load_harness_report(raw_dir, acut_id=acut_id, run_id=run_id)
        score = score_summary_from_report(report, predictions, run_id=run_id, acut_id=acut_id, acut_slot=acut_slot)
        score.update(
            {
                "status": "scored" if report and completed is not None and completed.returncode == 0 else "score_infra_error",
                "harness": {
                    "exit_code": None if completed is None else completed.returncode,
                    "duration_seconds": round(duration, 3),
                    "timeout_error": timeout_error,
                    "stdout": command_digest(completed.stdout if completed is not None else ""),
                    "stderr": command_digest(completed.stderr if completed is not None else ""),
                    "raw_dir": repo_relative(raw_dir),
                    "raw_logs_recorded_publicly": False,
                },
                "prediction_summary": prediction_summary,
            }
        )
        score_summaries.append(score)
    return score_summaries, prediction_summaries, model_calls


def protocol_blockers(protocol: Mapping[str, Any], e_config: Mapping[str, Any], matrix: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if protocol.get("status") != "phase2_e_runs_authorized":
        blockers.append("protocol_not_authorized_for_phase2_e_runs")
    if e_config.get("freeze_allowed") is not True:
        blockers.append("e_slice_not_frozen")
    if matrix.get("status") != "acut_profiles_frozen":
        blockers.append("acut_matrix_not_frozen")
    return blockers


def build_payload(
    *,
    phase: str,
    mode: str,
    protocol: Mapping[str, Any],
    e_config: Mapping[str, Any],
    matrix: Mapping[str, Any],
    selected_cells: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
    private_root: Path,
    workspace_root: Path,
    model_calls_made: int,
    score_summaries: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    blockers = protocol_blockers(protocol, e_config, matrix)
    failed_results = [result for result in results if result.get("status") in {"candidate_patch_extraction_error"}]
    if failed_results:
        blockers.append("cell_generation_infra_error")
    if phase == "score" and score_summaries:
        score_errors = [score for score in score_summaries if score.get("status") == "score_infra_error"]
        if score_errors:
            blockers.append("swebench_score_infra_error")
    status = "blocked" if blockers else {
        "prepare": "prepared",
        "run": "run_completed" if mode == "live" else "dry_run_ready",
        "score": "scored" if mode == "live" else "score_dry_run_ready",
    }[phase]
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "phase": phase,
        "mode": mode,
        "status": status,
        "blockers": blockers,
        "model_calls_made": model_calls_made,
        "selected_cell_count": len(selected_cells),
        "selected_cells": [
            {
                "run_id": cell.get("run_id"),
                "acut_slot": cell.get("acut_slot"),
                "acut_id": cell.get("acut_id"),
                "instance_id": cell.get("task_id"),
                "task_ordinal": cell.get("task_ordinal"),
                "attempt": cell.get("attempt"),
            }
            for cell in selected_cells
        ],
        "result_count": len(results),
        "results": list(results),
        "score_summaries": list(score_summaries or []),
        "private_root": repo_relative(private_root),
        "workspace_root": repo_relative(workspace_root),
        "raw_material_policy": {
            "raw_problem_statements_recorded_publicly": False,
            "raw_base_commits_recorded_publicly": False,
            "raw_candidate_patches_recorded_publicly": False,
            "raw_predictions_recorded_publicly": False,
            "raw_swebench_logs_recorded_publicly": False,
            "private_roots_are_ignored_artifact_roots": True,
        },
        "next_required_steps": [
            "Run remaining Phase 2 E primary attempts on the frozen matrix." if phase != "score" else "Inspect E spread gate after all ACUT E scores are complete."
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# External E Primary Run",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Phase: `{payload.get('phase')}`",
        f"Mode: `{payload.get('mode')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        f"Selected cells: `{payload.get('selected_cell_count')}`",
        f"Model calls made: `{payload.get('model_calls_made')}`",
        f"Blockers: `{payload.get('blockers')}`",
        "",
        "## Results",
        "",
    ]
    for result in payload.get("results", []):
        if not isinstance(result, Mapping):
            continue
        if payload.get("phase") == "prepare" and result.get("run_id") is None:
            lines.append(
                f"- task pack `{result.get('instance_id')}` ordinal `{result.get('task_ordinal')}` "
                f"family `{result.get('task_family')}`: statement digest `{result.get('problem_statement_sha256')}`"
            )
        else:
            lines.append(
                f"- `{result.get('run_id')}` `{result.get('acut_slot')}` `{result.get('instance_id')}`: `{result.get('status')}`"
            )
    if payload.get("score_summaries"):
        lines.extend(["", "## Scores", ""])
        for score in payload.get("score_summaries", []):
            if not isinstance(score, Mapping):
                continue
            table = score.get("score_table")
            row = table[0] if isinstance(table, list) and table and isinstance(table[0], Mapping) else {}
            lines.append(
                f"- `{score.get('acut_slot')}` `{score.get('acut_id')}`: "
                f"`{row.get('score_numerator')}` / `{row.get('score_denominator')}`"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Public artifacts contain run status, counts, paths, and digests only. Raw E statements, base commits, candidate patches, predictions, and SWE-bench logs remain under ignored private roots.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    protocol = load_manifest(args.protocol)
    e_config = load_manifest(args.e_config)
    matrix = load_manifest(args.matrix)
    selected_cells = select_run_cells(
        matrix,
        acut_slots=args.acut_slot,
        acut_ids=args.acut_id,
        instance_ids=args.instance_id,
        run_ids=args.run_id,
        limit=args.limit,
    )
    if not selected_cells:
        raise ToolError("no Phase 2 E matrix cells matched the requested filters")
    private_root = path_from_repo(args.private_root)
    workspace_root = path_from_repo(args.workspace_root)
    source_repo = path_from_repo(args.source_repo)
    frozen_tasks_by_id = frozen_e_tasks(e_config)
    rows = smoke.load_dataset_rows(args.dataset_name, split=args.split) if args.phase in {"prepare", "run"} else []
    rows_by_id = dataset_rows_by_id(rows)

    if args.phase == "prepare":
        results = prepare_task_packs(
            selected_cells,
            rows_by_id=rows_by_id,
            frozen_tasks_by_id=frozen_tasks_by_id,
            private_root=private_root,
            dataset_name=args.dataset_name,
            split=args.split,
        )
        model_calls_made = 0
        score_summaries: list[dict[str, Any]] = []
    elif args.phase == "run":
        results = []
        for cell in selected_cells:
            instance_id = str(cell.get("task_id"))
            row = rows_by_id.get(instance_id)
            frozen_task = frozen_tasks_by_id.get(instance_id)
            if row is None or frozen_task is None:
                raise ToolError("selected E task is missing dataset or freeze metadata", instance_id=instance_id)
            result = run_one_cell(
                cell,
                row=row,
                frozen_task=frozen_task,
                matrix=matrix,
                source_repo=source_repo,
                private_root=private_root,
                workspace_root=workspace_root,
                dataset_name=args.dataset_name,
                split=args.split,
                mode=args.mode,
                codex_bin=args.codex_bin,
                codex_provider_mode=args.codex_provider_mode,
                acut_timeout_seconds=args.acut_timeout_seconds,
            )
            results.append(result)
        model_calls_made = sum(1 for result in results if result.get("model_call_made") is True)
        score_summaries = []
    else:
        cell_results = load_cell_results(private_root, selected_cells)
        score_summaries, _prediction_summaries, model_calls_made = score_predictions(
            cell_results=cell_results,
            private_root=private_root,
            dataset_name=args.dataset_name,
            split=args.split,
            python_executable=str(path_from_repo(args.swebench_python)),
            mode=args.mode,
            max_workers=args.max_workers,
            timeout=args.timeout,
            command_timeout=args.command_timeout,
            cache_level=args.cache_level,
        )
        results = cell_results

    payload = build_payload(
        phase=args.phase,
        mode=args.mode,
        protocol=protocol,
        e_config=e_config,
        matrix=matrix,
        selected_cells=selected_cells,
        results=results,
        private_root=private_root,
        workspace_root=workspace_root,
        model_calls_made=model_calls_made,
        score_summaries=score_summaries,
    )
    output = Path(args.score_output if args.phase == "score" else args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0 if payload.get("status") not in {"blocked"} else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
