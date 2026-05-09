#!/usr/bin/env python3
"""Replay historical M2 patch-or-files outputs with the repaired parser.

This tool consumes existing raw/normalized M2 artifacts only. It does not make
model/API calls; it replays recorded provider responses through the current
local patch-or-files parser/applicator and records whether the old output is
now patch-ready or remains a model-output failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now
from _llm_budget import llm_safe_subprocess_env
from run_task import write_safe_patch

import codex_nfl_experiment_runner as batch
import openclaw_direct_runner as direct


TOOL = "m2_repaired_parser_replay"
DEFAULT_PATH_ID = "patch_or_files_v1_live"
PATCH_OR_FILES_CONTRACT = "patch-or-files-v1"
DEFAULT_RUN_PREFIX = "m2_repaired_parser_replay_20260509"
MODEL_OUTPUT_FAILURE_CLASSES = set(batch.MODEL_OUTPUT_FAILURE_CLASSES)
MODEL_OUTPUT_FAILURE_CLASSES.update({"apply_patch_context_mismatch", "apply_patch_invalid"})


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-summary", required=True)
    parser.add_argument("--path-id", default=DEFAULT_PATH_ID)
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument(
        "--workspace-mode",
        choices=("prepare", "existing"),
        default="prepare",
        help="Use clean re-created task workspaces by default; tests may use existing temp workspaces.",
    )
    parser.add_argument("--raw-root", default=str(batch.RAW_ROOT), help="Replay artifact root for generated patches.")
    parser.add_argument("--force", action="store_true", help="Remove replay artifact directories with the same run prefix.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(list(argv))


def read_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("JSON root must be an object", path=str(path))
    return data


def maybe_read_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return {}
    try:
        return read_json(candidate)
    except (json.JSONDecodeError, ToolError):
        return {}


def count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def response_text(path: str | None) -> str:
    if not path:
        return ""
    artifact = Path(path)
    if not artifact.exists() or not artifact.is_file():
        return ""
    raw = artifact.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(data, dict):
        return raw
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, Mapping):
            message = first.get("message")
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                return str(message["content"])
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text
    return raw


def response_usage_cost(path: str | None) -> float | None:
    if not path:
        return None
    data = maybe_read_json(path)
    usage = data.get("usage") if isinstance(data.get("usage"), Mapping) else {}
    cost = usage.get("cost") if isinstance(usage, Mapping) else None
    return float(cost) if isinstance(cost, (int, float)) else None


def artifact_dir_for_record(record: Mapping[str, Any]) -> Path | None:
    for key in ("raw_response_artifact", "prompt_snapshot"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return Path(value).parent
    run_id = record.get("run_id")
    if isinstance(run_id, str) and run_id:
        return batch.RAW_ROOT / run_id
    return None


def batch_result_for_record(record: Mapping[str, Any]) -> dict[str, Any]:
    artifact_dir = artifact_dir_for_record(record)
    if artifact_dir is None:
        return {}
    return maybe_read_json(artifact_dir / "batch_run_result.json")


def prompt_context_paths(record: Mapping[str, Any]) -> list[str]:
    prompt = maybe_read_json(record.get("prompt_snapshot") if isinstance(record.get("prompt_snapshot"), str) else None)
    context_files = prompt.get("context_files") if isinstance(prompt.get("context_files"), list) else []
    paths = [
        str(item["path"])
        for item in context_files
        if isinstance(item, Mapping) and isinstance(item.get("path"), str) and item.get("path")
    ]
    return sorted(dict.fromkeys(paths))


def context_paths_for_record(record: Mapping[str, Any], batch_result: Mapping[str, Any]) -> list[str]:
    paths = batch_result.get("context_paths") if isinstance(batch_result.get("context_paths"), list) else []
    clean = [str(item) for item in paths if isinstance(item, str) and item]
    if clean:
        return sorted(dict.fromkeys(clean))
    return prompt_context_paths(record)


def historical_workspace_for_record(batch_result: Mapping[str, Any]) -> Path | None:
    for key in ("runner_workspace", "workspace"):
        value = batch_result.get(key)
        if isinstance(value, str) and value:
            return Path(value)
    return None


def fixed_cells(summary: Mapping[str, Any], path_id: str) -> list[dict[str, Any]]:
    tasks = summary.get("tasks") if isinstance(summary.get("tasks"), list) else []
    acuts = summary.get("acuts") if isinstance(summary.get("acuts"), list) else []
    records_by_path = summary.get("records") if isinstance(summary.get("records"), Mapping) else {}
    records = records_by_path.get(path_id) if isinstance(records_by_path.get(path_id), list) else []
    by_cell = {
        (str(record.get("acut_id")), str(record.get("task_id"))): record
        for record in records
        if isinstance(record, Mapping)
    }
    cells: list[dict[str, Any]] = []
    for acut_id in [str(item) for item in acuts]:
        for task_id in [str(item) for item in tasks]:
            record = by_cell.get((acut_id, task_id))
            cells.append(
                {
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "record": record if isinstance(record, Mapping) else None,
                }
            )
    return cells


def old_record_payload(record: Mapping[str, Any] | None, *, acut_id: str, task_id: str) -> dict[str, Any]:
    if record is None:
        return {
            "acut_id": acut_id,
            "task_id": task_id,
            "run_id": None,
            "status": "missing",
            "failure_owner": "missing",
            "failure_class": None,
            "patch_ready": False,
            "clean_replay_attempted": False,
            "clean_replay_success": False,
            "model_call_made": None,
            "normalized_result": None,
            "raw_response_artifact": None,
            "prompt_snapshot": None,
            "historical_provider_usage_cost_usd": None,
        }
    raw_response_artifact = record.get("raw_response_artifact")
    return {
        "acut_id": acut_id,
        "task_id": task_id,
        "run_id": record.get("run_id"),
        "status": record.get("status"),
        "failure_owner": record.get("failure_owner"),
        "failure_class": record.get("failure_class"),
        "patch_ready": bool(record.get("patch_ready")),
        "clean_replay_attempted": bool(record.get("clean_replay_attempted")),
        "clean_replay_success": bool(record.get("clean_replay_success")),
        "model_call_made": record.get("model_call_made"),
        "normalized_result": record.get("normalized_result"),
        "raw_response_artifact": raw_response_artifact,
        "prompt_snapshot": record.get("prompt_snapshot"),
        "historical_provider_usage_cost_usd": response_usage_cost(raw_response_artifact if isinstance(raw_response_artifact, str) else None),
    }


def artifact_presence(record: Mapping[str, Any] | None, batch_result: Mapping[str, Any]) -> dict[str, bool]:
    if record is None:
        return {
            "normalized_result_exists": False,
            "raw_response_artifact_exists": False,
            "prompt_snapshot_exists": False,
            "batch_run_result_exists": False,
        }
    artifact_dir = artifact_dir_for_record(record)
    normalized = record.get("normalized_result")
    raw_response = record.get("raw_response_artifact")
    prompt = record.get("prompt_snapshot")
    return {
        "normalized_result_exists": isinstance(normalized, str) and Path(normalized).exists(),
        "raw_response_artifact_exists": isinstance(raw_response, str) and Path(raw_response).exists(),
        "prompt_snapshot_exists": isinstance(prompt, str) and Path(prompt).exists(),
        "batch_run_result_exists": bool(batch_result) or bool(artifact_dir and (artifact_dir / "batch_run_result.json").exists()),
    }


def response_shape(text: str, raw_path: str | None) -> dict[str, Any]:
    return {
        "raw_response_artifact_present": bool(raw_path),
        "response_char_count": len(text),
        "response_sha256": sha256_text(text) if text else None,
        "contains_apply_patch_transcript": "*** Begin Patch" in text,
        "contains_unified_diff_marker": "diff --git " in text or "\n--- " in text,
        "contains_redacted_url_marker": "<redacted:url>" in text,
        "content_recorded": False,
    }


def remove_existing_artifact_dir(artifact_dir: Path, run_prefix: str, force: bool) -> None:
    if not artifact_dir.exists():
        return
    if not any(artifact_dir.iterdir()):
        return
    if not force:
        raise ToolError("replay artifact directory already exists", artifact_dir=str(artifact_dir))
    if not artifact_dir.name.startswith(run_prefix):
        raise ToolError("refusing to remove artifact directory outside replay run prefix", artifact_dir=str(artifact_dir))
    shutil.rmtree(artifact_dir)


def prepare_replay_workspace(
    *,
    task_id: str,
    replay_run_id: str,
    artifact_dir: Path,
    force: bool,
    run_prefix: str,
    summary_name: str,
) -> tuple[Path, dict[str, Any]]:
    remove_existing_artifact_dir(artifact_dir, run_prefix, force)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return batch.prepare_workspace(task_id, replay_run_id, artifact_dir, summary_name=summary_name)


def write_replay_patch(workspace: Path, patch_path: Path) -> dict[str, Any]:
    safe_env, _ = llm_safe_subprocess_env(os.environ)
    patch_artifact = write_safe_patch(workspace, patch_path, safe_env)
    if patch_artifact.get("unsafe_content_detected") is True:
        raise ToolError(
            "generated patch contains unsafe content",
            failure_class="unsafe_generated_text",
            unsafe_content=patch_artifact.get("unsafe_content", {}),
        )
    return dict(patch_artifact)


def apply_generated_patch_to_clean_workspace(
    *,
    workspace: Path,
    patch_path: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    check_command = ["git", "apply", "--check", str(patch_path)]
    started_at = iso_now()
    check = batch.run_capture(check_command, cwd=workspace, timeout=120)
    finished_at = iso_now()
    check_summary = batch.write_command_artifacts(
        completed=check,
        artifact_dir=artifact_dir,
        name="clean_replay_git_apply_check",
        command=check_command,
        started_at=started_at,
        finished_at=finished_at,
    )
    if check.returncode != 0:
        return {
            "attempted": True,
            "success": False,
            "status": "git_apply_check_failed",
            "check": check_summary,
            "apply": None,
        }

    apply_command = ["git", "apply", str(patch_path)]
    started_at = iso_now()
    applied = batch.run_capture(apply_command, cwd=workspace, timeout=120)
    finished_at = iso_now()
    apply_summary = batch.write_command_artifacts(
        completed=applied,
        artifact_dir=artifact_dir,
        name="clean_replay_git_apply",
        command=apply_command,
        started_at=started_at,
        finished_at=finished_at,
    )
    return {
        "attempted": True,
        "success": applied.returncode == 0,
        "status": "applied_to_clean_workspace" if applied.returncode == 0 else "git_apply_failed",
        "check": check_summary,
        "apply": apply_summary,
    }


def classify_failure(exc: ToolError) -> tuple[str, str]:
    failure_class = exc.details.get("failure_class")
    if not isinstance(failure_class, str) or not failure_class:
        if str(exc) in {
            "generated unified diff failed git apply validation",
            "generated unified diff failed to apply",
        }:
            failure_class = "invalid_unified_diff"
        elif str(exc) == "model response did not contain a supported patch":
            failure_class = "unsupported_patch_response"
        else:
            failure_class = "replay_error"
    failure_owner = "model_output" if failure_class in MODEL_OUTPUT_FAILURE_CLASSES else "infrastructure"
    return failure_owner, failure_class


def replay_record(
    *,
    record: Mapping[str, Any],
    task_id: str,
    acut_id: str,
    args: argparse.Namespace,
    batch_result: Mapping[str, Any],
    context_paths: Sequence[str],
) -> dict[str, Any]:
    raw_path = record.get("raw_response_artifact") if isinstance(record.get("raw_response_artifact"), str) else None
    text = response_text(raw_path)
    if not raw_path:
        return missing_replay_payload("missing_raw_response_artifact")
    if not Path(raw_path).exists():
        return missing_replay_payload("raw_response_artifact_missing_on_disk")
    if not text.strip():
        return missing_replay_payload("empty_raw_response_artifact")
    if not context_paths:
        return missing_replay_payload("missing_context_paths")

    replay_run_id = f"{args.run_prefix}__{record.get('run_id') or acut_id + '__' + task_id}"
    artifact_dir = Path(args.raw_root) / replay_run_id
    workspace_summary: dict[str, Any] | None = None
    clean_workspace_summary: dict[str, Any] | None = None
    clean_replay: dict[str, Any] = {"attempted": False, "success": False, "status": "not_attempted"}

    if args.workspace_mode == "existing":
        workspace = historical_workspace_for_record(batch_result)
        if workspace is None:
            return missing_replay_payload("missing_existing_workspace_path")
        if not workspace.exists():
            return missing_replay_payload("existing_workspace_missing_on_disk")
        workspace = workspace.resolve()
        artifact_dir.mkdir(parents=True, exist_ok=True)
    else:
        workspace, workspace_summary = prepare_replay_workspace(
            task_id=task_id,
            replay_run_id=replay_run_id,
            artifact_dir=artifact_dir,
            force=bool(args.force),
            run_prefix=str(args.run_prefix),
            summary_name="prepare_replay_workspace",
        )

    try:
        parsed = direct.parse_patch_response(text)
        patch_result = direct.apply_model_response(
            workspace,
            text,
            allowed_paths=context_paths,
            output_contract=PATCH_OR_FILES_CONTRACT,
        )
        patch_path = artifact_dir / "submission.patch"
        try:
            patch_artifact = write_replay_patch(workspace, patch_path)
        except ToolError as exc:
            exc.details.setdefault("patch_result_before_patch_artifact", patch_result)
            raise
        patch_ready = bool(patch_artifact.get("written") and patch_artifact.get("size_bytes", 0) > 0)
        if patch_ready and args.workspace_mode == "prepare":
            clean_run_id = f"{replay_run_id}__clean_replay"
            clean_workspace, clean_workspace_summary = batch.prepare_workspace(
                task_id,
                clean_run_id,
                artifact_dir,
                summary_name="prepare_clean_replay_workspace",
            )
            clean_replay = apply_generated_patch_to_clean_workspace(
                workspace=clean_workspace,
                patch_path=patch_path,
                artifact_dir=artifact_dir,
            )
        elif patch_ready:
            clean_replay = {
                "attempted": False,
                "success": None,
                "status": "not_attempted_existing_workspace_mode",
            }
        else:
            clean_replay = {
                "attempted": False,
                "success": False,
                "status": "no_patch_artifact_written",
            }
        return {
            "attempted": True,
            "status": "patch_ready" if patch_ready else "clean_replay_no_patch",
            "failure_owner": "candidate_patch" if patch_ready else "model_output",
            "failure_class": None if patch_ready else "empty_generated_patch",
            "patch_ready": patch_ready,
            "clean_replay_attempted": bool(clean_replay.get("attempted")),
            "clean_replay_success": bool(clean_replay.get("success")) if clean_replay.get("success") is not None else None,
            "clean_replay_status": clean_replay.get("status"),
            "parser_kind": parsed.get("kind"),
            "patch_result": patch_result,
            "patch_artifact": patch_artifact,
            "workspace": str(workspace),
            "workspace_prepare": workspace_summary,
            "clean_replay_workspace_prepare": clean_workspace_summary,
            "clean_replay": clean_replay,
            "artifact_dir": str(artifact_dir),
            "model_call_made": False,
            "model_spend_usd": 0.0,
            "error": None,
            "details": {},
        }
    except ToolError as exc:
        failure_owner, failure_class = classify_failure(exc)
        row = {
            "attempted": True,
            "status": "invalid_submission",
            "failure_owner": failure_owner,
            "failure_class": failure_class,
            "patch_ready": False,
            "clean_replay_attempted": False,
            "clean_replay_success": False,
            "clean_replay_status": "not_attempted_after_replay_failure",
            "parser_kind": None,
            "patch_result": None,
            "patch_artifact": None,
            "workspace": str(workspace),
            "workspace_prepare": workspace_summary,
            "clean_replay_workspace_prepare": None,
            "clean_replay": clean_replay,
            "artifact_dir": str(artifact_dir),
            "model_call_made": False,
            "model_spend_usd": 0.0,
            "error": str(exc),
            "details": exc.details,
        }
        try:
            parsed = direct.parse_patch_response(text)
            row["parser_kind"] = parsed.get("kind")
        except ToolError:
            pass
        return row


def missing_replay_payload(failure_class: str) -> dict[str, Any]:
    owner = "missing" if failure_class == "missing_record" else "infrastructure"
    return {
        "attempted": False,
        "status": "missing_replay_input",
        "failure_owner": owner,
        "failure_class": failure_class,
        "patch_ready": False,
        "clean_replay_attempted": False,
        "clean_replay_success": False,
        "clean_replay_status": "not_attempted_missing_input",
        "parser_kind": None,
        "patch_result": None,
        "patch_artifact": None,
        "workspace": None,
        "workspace_prepare": None,
        "clean_replay_workspace_prepare": None,
        "clean_replay": {"attempted": False, "success": False, "status": "not_attempted_missing_input"},
        "artifact_dir": None,
        "model_call_made": False,
        "model_spend_usd": 0.0,
        "error": failure_class,
        "details": {},
    }


def classification_delta(old: Mapping[str, Any], repaired: Mapping[str, Any]) -> str:
    old_class = old.get("failure_class") or "none"
    repaired_class = repaired.get("failure_class") or "none"
    if old_class == repaired_class:
        return "unchanged"
    return f"{old_class} -> {repaired_class}"


def replay_cell(cell: Mapping[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    acut_id = str(cell["acut_id"])
    task_id = str(cell["task_id"])
    record = cell.get("record") if isinstance(cell.get("record"), Mapping) else None
    old = old_record_payload(record, acut_id=acut_id, task_id=task_id)
    batch_result = batch_result_for_record(record) if record is not None else {}
    artifacts = artifact_presence(record, batch_result)
    context_paths = context_paths_for_record(record, batch_result) if record is not None else []
    raw_path = old.get("raw_response_artifact") if isinstance(old.get("raw_response_artifact"), str) else None
    text = response_text(raw_path)
    if record is None:
        repaired = missing_replay_payload("missing_record")
    else:
        repaired = replay_record(
            record=record,
            task_id=task_id,
            acut_id=acut_id,
            args=args,
            batch_result=batch_result,
            context_paths=context_paths,
        )
    row = {
        "acut_id": acut_id,
        "task_id": task_id,
        "run_id": old.get("run_id"),
        "old": old,
        "artifacts": {
            **artifacts,
            "context_paths": context_paths,
            "context_path_count": len(context_paths),
            "workspace_mode": args.workspace_mode,
        },
        "response_shape": response_shape(text, raw_path),
        "repaired": repaired,
        "classification_delta": classification_delta(old, repaired),
    }
    return row


def missing_artifact_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def missing_count(key: str) -> int:
        return sum(
            1
            for row in rows
            if isinstance(row.get("artifacts"), Mapping) and row["artifacts"].get(key) is not True
        )

    missing_rows = [
        {
            "acut_id": row.get("acut_id"),
            "task_id": row.get("task_id"),
            "run_id": row.get("run_id"),
            "failure_class": (row.get("repaired") or {}).get("failure_class") if isinstance(row.get("repaired"), Mapping) else None,
        }
        for row in rows
        if isinstance(row.get("repaired"), Mapping) and row["repaired"].get("status") == "missing_replay_input"
    ]
    return {
        "normalized_result_missing_count": missing_count("normalized_result_exists"),
        "raw_response_artifact_missing_count": missing_count("raw_response_artifact_exists"),
        "prompt_snapshot_missing_count": missing_count("prompt_snapshot_exists"),
        "batch_run_result_missing_count": missing_count("batch_run_result_exists"),
        "missing_context_paths_count": sum(
            1
            for row in rows
            if isinstance(row.get("artifacts"), Mapping) and int(row["artifacts"].get("context_path_count") or 0) == 0
        ),
        "missing_replay_input_count": len(missing_rows),
        "missing_replay_input_rows": missing_rows,
    }


def aggregate_repaired(rows: Sequence[Mapping[str, Any]], denominator: int) -> dict[str, Any]:
    repaired_rows = [row.get("repaired") for row in rows if isinstance(row.get("repaired"), Mapping)]
    repaired = [row for row in repaired_rows if isinstance(row, Mapping)]
    patch_ready_count = sum(1 for row in repaired if row.get("patch_ready") is True)
    clean_attempted = sum(1 for row in repaired if row.get("clean_replay_attempted") is True)
    clean_success = sum(1 for row in repaired if row.get("clean_replay_success") is True)
    return {
        "fixed_denominator": denominator,
        "matrix_row_count": len(rows),
        "status_counts": count_by(repaired, "status"),
        "failure_owner_counts": count_by(repaired, "failure_owner"),
        "failure_class_counts": count_by(repaired, "failure_class"),
        "patch_ready_count": patch_ready_count,
        "patch_ready_coverage": rate(patch_ready_count, denominator),
        "clean_replay_attempted_count": clean_attempted,
        "clean_replay_success_count": clean_success,
        "clean_replay_success_rate": rate(clean_success, denominator),
        "classification_delta_counts": count_by(rows, "classification_delta"),
    }


def aggregate_old(rows: Sequence[Mapping[str, Any]], denominator: int, path_summary: Mapping[str, Any]) -> dict[str, Any]:
    old_rows = [row.get("old") for row in rows if isinstance(row.get("old"), Mapping)]
    old = [row for row in old_rows if isinstance(row, Mapping)]
    patch_ready_count = sum(1 for row in old if row.get("patch_ready") is True)
    return {
        "fixed_denominator": denominator,
        "status_counts": path_summary.get("status_counts") or count_by(old, "status"),
        "failure_owner_counts": path_summary.get("failure_owner_counts") or count_by(old, "failure_owner"),
        "failure_class_counts": path_summary.get("failure_class_counts") or count_by(old, "failure_class"),
        "patch_ready_count": path_summary.get("patch_ready_count", patch_ready_count),
        "patch_ready_coverage": path_summary.get("patch_ready_coverage", rate(patch_ready_count, denominator)),
        "invalid_submission_rate": path_summary.get("invalid_submission_rate"),
        "clean_replay_attempted_count": path_summary.get("clean_replay_attempted_count"),
        "clean_replay_success_count": path_summary.get("clean_replay_success_count"),
        "gate_status": (path_summary.get("gate") or {}).get("status") if isinstance(path_summary.get("gate"), Mapping) else None,
    }


def cost_model_call_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    old_rows = [row.get("old") for row in rows if isinstance(row.get("old"), Mapping)]
    historical_costs = [
        row.get("historical_provider_usage_cost_usd")
        for row in old_rows
        if isinstance(row, Mapping) and isinstance(row.get("historical_provider_usage_cost_usd"), (int, float))
    ]
    repaired_rows = [row.get("repaired") for row in rows if isinstance(row.get("repaired"), Mapping)]
    return {
        "historical": {
            "model_call_made_counts": count_by([row for row in old_rows if isinstance(row, Mapping)], "model_call_made"),
            "provider_usage_cost_usd_observed_sum": round(sum(float(item) for item in historical_costs), 6),
            "provider_usage_cost_observed_count": len(historical_costs),
            "provider_usage_cost_status": "historical_provider_response_usage_not_new_spend",
        },
        "replay": {
            "model_call_made": False,
            "model_call_made_counts": count_by([row for row in repaired_rows if isinstance(row, Mapping)], "model_call_made"),
            "model_spend_usd": 0.0,
            "live_api_calls": False,
            "no_model_spend_default": True,
        },
    }


def patch_result_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    repaired = row.get("repaired") if isinstance(row.get("repaired"), Mapping) else {}
    patch_result = repaired.get("patch_result") if isinstance(repaired.get("patch_result"), Mapping) else None
    if patch_result is not None:
        return patch_result
    details = repaired.get("details") if isinstance(repaired.get("details"), Mapping) else {}
    before_artifact = (
        details.get("patch_result_before_patch_artifact")
        if isinstance(details.get("patch_result_before_patch_artifact"), Mapping)
        else {}
    )
    return before_artifact


def context_anchor_repair_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    redacted_url_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        patch_result = patch_result_diagnostics(row)
        hunk_diagnostics = (
            patch_result.get("hunk_diagnostics")
            if isinstance(patch_result.get("hunk_diagnostics"), list)
            else []
        )
        redacted_matches = [
            item
            for item in hunk_diagnostics
            if isinstance(item, Mapping)
            and isinstance(item.get("diagnostic"), Mapping)
            and item["diagnostic"].get("code") == "redacted_url_context_matched_raw_source"
        ]
        if redacted_matches:
            redacted_url_rows.append(
                {
                    "acut_id": row.get("acut_id"),
                    "task_id": row.get("task_id"),
                    "run_id": row.get("run_id"),
                    "matched_hunk_count": len(redacted_matches),
                    "artifact_status": (row.get("repaired") or {}).get("failure_class")
                    if isinstance(row.get("repaired"), Mapping)
                    else None,
                }
            )
        repaired = row.get("repaired") if isinstance(row.get("repaired"), Mapping) else {}
        details = repaired.get("details") if isinstance(repaired.get("details"), Mapping) else {}
        if repaired.get("failure_class") == "apply_patch_context_mismatch" and isinstance(details.get("line_anchors"), list):
            mismatch_rows.append(
                {
                    "acut_id": row.get("acut_id"),
                    "task_id": row.get("task_id"),
                    "run_id": row.get("run_id"),
                    "path": details.get("path"),
                    "hunk_index": details.get("hunk_index"),
                    "old_text_sha256": details.get("old_text_sha256"),
                    "line_anchor_occurrences": [
                        {
                            "position": anchor.get("position"),
                            "occurrences": anchor.get("occurrences"),
                            "line_sha256": anchor.get("line_sha256"),
                        }
                        for anchor in details.get("line_anchors", [])
                        if isinstance(anchor, Mapping)
                    ],
                    "redacted_url_fallback_match_count": (
                        details.get("redacted_url_context", {}).get("fallback_match_count")
                        if isinstance(details.get("redacted_url_context"), Mapping)
                        else None
                    ),
                }
            )
    return {
        "redacted_url_source_context_match_count": len(redacted_url_rows),
        "redacted_url_source_context_rows": redacted_url_rows,
        "apply_patch_context_mismatch_diagnostic_count": len(mismatch_rows),
        "apply_patch_context_mismatch_rows": mismatch_rows,
        "content_recorded": False,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    summary = read_json(args.m2_summary)
    paths = summary.get("paths") if isinstance(summary.get("paths"), Mapping) else {}
    path_summary = paths.get(args.path_id) if isinstance(paths.get(args.path_id), Mapping) else {}
    cells = fixed_cells(summary, args.path_id)
    denominator = int(summary.get("fixed_denominator") or len(cells))
    rows = [replay_cell(cell, args) for cell in cells]
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "m2_summary": args.m2_summary,
            "path_id": args.path_id,
            "workspace_mode": args.workspace_mode,
            "run_prefix": args.run_prefix,
            "raw_root": args.raw_root,
            "force": bool(args.force),
            "output": args.output,
            "report": args.report,
        },
        "scope": {
            "source_path_id": args.path_id,
            "contract": PATCH_OR_FILES_CONTRACT,
            "tasks": summary.get("tasks"),
            "acuts": summary.get("acuts"),
            "fixed_denominator": denominator,
            "matrix_row_count": len(rows),
            "fixed_denominator_matches_matrix": denominator == len(rows),
            "prior_claim_status": summary.get("claim_status"),
        },
        "method": {
            "model_calls": "none",
            "model_spend_usd": 0.0,
            "uses_existing_provider_responses": True,
            "workspace_policy": "clean re-created task workspaces" if args.workspace_mode == "prepare" else "existing workspaces",
            "verifier_execution": "not_run",
            "claim_boundary": "parser/applicator scoreability replay only",
        },
        "old_summary": aggregate_old(rows, denominator, path_summary),
        "repaired_summary": aggregate_repaired(rows, denominator),
        "missing_artifact_summary": missing_artifact_summary(rows),
        "context_anchor_repair_summary": context_anchor_repair_summary(rows),
        "cost_model_call_flags": cost_model_call_flags(rows),
        "matrix": rows,
        "claim_status": "historical_replay_not_m2_pass",
        "claim_boundaries": {
            "m2_passed": False,
            "ranking_reversal": False,
            "task_solving_improvement": False,
            "capability_uplift": False,
            "g_score_predictivity": False,
            "g0_g5": False,
            "license": False,
            "admission": False,
            "authorization": False,
            "new_model_calls": False,
            "verifier_or_task_success_measured": False,
        },
        "prohibited_claims": {
            "m2_passed": False,
            "ranking_reversal": False,
            "task_solving_improvement": False,
            "capability_uplift": False,
            "g_score_predictivity": False,
            "g0_g5": False,
            "license": False,
            "admission": False,
            "authorization": False,
        },
    }


def pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def write_report(payload: Mapping[str, Any], path: str) -> None:
    scope = payload.get("scope") if isinstance(payload.get("scope"), Mapping) else {}
    old = payload.get("old_summary") if isinstance(payload.get("old_summary"), Mapping) else {}
    repaired = payload.get("repaired_summary") if isinstance(payload.get("repaired_summary"), Mapping) else {}
    missing = payload.get("missing_artifact_summary") if isinstance(payload.get("missing_artifact_summary"), Mapping) else {}
    anchors = (
        payload.get("context_anchor_repair_summary")
        if isinstance(payload.get("context_anchor_repair_summary"), Mapping)
        else {}
    )
    cost = payload.get("cost_model_call_flags") if isinstance(payload.get("cost_model_call_flags"), Mapping) else {}
    replay_cost = cost.get("replay") if isinstance(cost.get("replay"), Mapping) else {}
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), Mapping) else {}
    lines = [
        "# M2 Repaired Parser Historical Replay Report",
        "",
        "Date: 2026-05-09",
        "",
        "## Scope",
        "",
        f"- Source path: `{scope.get('source_path_id')}`.",
        f"- Fixed denominator: `{scope.get('fixed_denominator')}` rows; matrix rows: `{scope.get('matrix_row_count')}`.",
        f"- Replay model calls: `{replay_cost.get('model_call_made')}`; replay model spend USD: `{replay_cost.get('model_spend_usd')}`.",
        "- Verifier execution was not run; this measures local parser/applicator scoreability only.",
        "",
        "## Old vs Repaired",
        "",
        "| Metric | Old | Repaired |",
        "| --- | --- | --- |",
        f"| Patch-ready count | `{old.get('patch_ready_count')}` | `{repaired.get('patch_ready_count')}` |",
        f"| Patch-ready coverage | {pct(old.get('patch_ready_coverage'))} | {pct(repaired.get('patch_ready_coverage'))} |",
        f"| Status counts | `{old.get('status_counts')}` | `{repaired.get('status_counts')}` |",
        f"| Failure owners | `{old.get('failure_owner_counts')}` | `{repaired.get('failure_owner_counts')}` |",
        f"| Failure classes | `{old.get('failure_class_counts')}` | `{repaired.get('failure_class_counts')}` |",
        "",
        "## Replay Matrix",
        "",
        "| ACUT | Task | Old class | Repaired status | Repaired owner | Repaired class | Patch-ready | Clean replay |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload.get("matrix", []):
        if not isinstance(row, Mapping):
            continue
        old_row = row.get("old") if isinstance(row.get("old"), Mapping) else {}
        repaired_row = row.get("repaired") if isinstance(row.get("repaired"), Mapping) else {}
        lines.append(
            f"| `{row.get('acut_id')}` | `{row.get('task_id')}` | `{old_row.get('failure_class')}` | "
            f"`{repaired_row.get('status')}` | `{repaired_row.get('failure_owner')}` | "
            f"`{repaired_row.get('failure_class')}` | `{repaired_row.get('patch_ready')}` | "
            f"`{repaired_row.get('clean_replay_status')}` |"
        )
    lines.extend(
        [
            "",
            "## Context Anchor Diagnostics",
            "",
            f"- Redacted URL source-context matches: `{anchors.get('redacted_url_source_context_match_count')}`.",
            f"- Apply-patch context mismatch rows with line-anchor diagnostics: `{anchors.get('apply_patch_context_mismatch_diagnostic_count')}`.",
            "- Diagnostics record file paths, hunk indexes, hashes, line-anchor occurrence counts, and redacted-URL match counts; source content is not recorded in the JSON summary.",
            "",
            "## Missing Artifacts",
            "",
            f"- Raw response artifacts missing: `{missing.get('raw_response_artifact_missing_count')}`.",
            f"- Normalized results missing: `{missing.get('normalized_result_missing_count')}`.",
            f"- Prompt snapshots missing: `{missing.get('prompt_snapshot_missing_count')}`.",
            f"- Batch run results missing: `{missing.get('batch_run_result_missing_count')}`.",
            f"- Missing replay inputs: `{missing.get('missing_replay_input_count')}`.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_repaired_parser_replay.py \\",
            f"  --m2-summary {inputs.get('m2_summary')} \\",
            f"  --path-id {scope.get('source_path_id')} \\",
            f"  --run-prefix {inputs.get('run_prefix')} \\",
            "  --force \\",
            f"  --output {inputs.get('output')} \\",
            f"  --report {inputs.get('report')}",
            "```",
            "",
            "## Claim Boundaries",
            "",
            "This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports whether stored historical outputs are locally patch-ready under the repaired parser/applicator.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_payload(args)
        emit_json(payload, args.output)
        write_report(payload, args.report)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
