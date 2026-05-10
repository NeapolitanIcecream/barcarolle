#!/usr/bin/env python3
"""Aggregate the M2 stable nonpersistent historical replay matrix.

This tool consumes existing no-new-model-call replay artifacts and historical
M2 batch outputs. It does not call a model. It separates verifier-ready
persisted patch artifacts, nonpersistent verifier attempts, model-output
invalid submissions, infrastructure failures, missing raw artifacts, and
cleanup blockers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now
from _llm_budget import unsafe_text_findings


TOOL = "m2_stable_nonpersistent_replay_matrix"

DEFAULT_M2_SUMMARY = "experiments/core_narrative/results/m2_scoreability_summary_20260509.json"
DEFAULT_PATCH_REPLAY = (
    "experiments/core_narrative/results/"
    "m2_stable_nonpersistent_replay_matrix_patch_or_files_replay_20260510.json"
)
DEFAULT_ANCHORED_BATCHES: tuple[tuple[str, str, str], ...] = (
    (
        "anchored_contract_live_smoke",
        "historical_live",
        "experiments/core_narrative/results/m2_anchored_contract_live_smoke_20260509.json",
    ),
    (
        "anchored_occurrence_repair_live_smoke",
        "historical_live",
        "experiments/core_narrative/results/m2_anchored_occurrence_repair_live_smoke_20260510.json",
    ),
    (
        "unsafe_artifact_repair_live_smoke",
        "historical_live",
        "experiments/core_narrative/results/m2_unsafe_artifact_repair_live_smoke_20260510.json",
    ),
    (
        "nonpersistent_channel_replay",
        "no_model_replay",
        "experiments/core_narrative/results/m2_nonpersistent_verifier_channel_replay_20260510.json",
    ),
    (
        "nonpersistent_channel_live_smoke",
        "historical_live",
        "experiments/core_narrative/results/m2_nonpersistent_verifier_channel_live_smoke_20260510.json",
    ),
)

PATCH_OR_FILES_CONTRACT = "patch-or-files-v1"
ANCHORED_CONTRACT = "anchored-search-replace-json-v3"
ATTEMPTABLE_CATEGORIES = {
    "verifier_ready_persisted_patch_artifact",
    "nonpersistent_verifier_attempt",
}
PROHIBITED_CLAIMS = {
    "m2_passed": False,
    "ranking_reversal": False,
    "task_solving_improvement": False,
    "capability_uplift": False,
    "g_score_predictivity": False,
    "g0_g5": False,
    "license": False,
    "admission": False,
    "authorization": False,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-summary", default=DEFAULT_M2_SUMMARY)
    parser.add_argument("--patch-replay", default=DEFAULT_PATCH_REPLAY)
    parser.add_argument(
        "--anchored-batch",
        action="append",
        nargs=3,
        metavar=("LABEL", "MODE", "PATH"),
        help=(
            "Anchored-search-replace batch evidence. MODE should be "
            "historical_live, no_model_replay, or blocker."
        ),
    )
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
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def response_text(path: str | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return ""
    raw = candidate.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(data, dict):
        return raw
    choices = data.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], Mapping):
        message = choices[0].get("message")
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


def bool_label(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def response_shape(path: str | None) -> dict[str, Any]:
    text = response_text(path)
    return {
        "raw_response_artifact_present": bool(path),
        "raw_response_artifact_exists": bool(path and Path(path).exists()),
        "response_char_count": len(text),
        "response_sha256": sha256_text(text) if text else None,
        "contains_apply_patch_transcript": "*** Begin Patch" in text,
        "contains_unified_diff_marker": "diff --git " in text or "\n--- " in text,
        "contains_redacted_url_marker": "<redacted:url>" in text,
        "contains_raw_url_like": "http://" in text or "https://" in text,
        "content_recorded": False,
    }


def artifact_presence(*paths: object) -> dict[str, bool]:
    labels = ["normalized_result", "raw_response_artifact", "prompt_snapshot"]
    result: dict[str, bool] = {}
    for label, value in zip(labels, paths):
        result[f"{label}_exists"] = isinstance(value, str) and Path(value).exists()
    return result


def category_from_old_record(old: Mapping[str, Any]) -> str:
    raw_path = old.get("raw_response_artifact") if isinstance(old.get("raw_response_artifact"), str) else None
    if raw_path is None or not Path(raw_path).exists():
        return "missing_raw_artifact"
    status = str(old.get("status") or "")
    owner = str(old.get("failure_owner") or "")
    if bool(old.get("patch_ready")):
        return "verifier_ready_persisted_patch_artifact"
    if status == "infra_failed" or owner == "infrastructure":
        return "infra_failure"
    if status == "invalid_submission" or owner == "model_output":
        return "model_output_invalid_submission"
    return "other_not_attemptable"


def category_from_repaired(repaired: Mapping[str, Any], old: Mapping[str, Any]) -> str:
    if repaired.get("failure_class") == "missing_raw_response_artifact":
        return "missing_raw_artifact"
    if repaired.get("failure_class") == "nonpersistent_transient_workspace_cleanup_failed":
        return "cleanup_blocker"
    if repaired.get("patch_ready") is True:
        return "verifier_ready_persisted_patch_artifact"
    status = str(repaired.get("status") or "")
    owner = str(repaired.get("failure_owner") or "")
    if status == "missing_replay_input":
        raw_path = old.get("raw_response_artifact") if isinstance(old.get("raw_response_artifact"), str) else None
        return "missing_raw_artifact" if not raw_path or not Path(raw_path).exists() else "infra_failure"
    if status == "infra_failed" or owner == "infrastructure":
        return "infra_failure"
    if status == "invalid_submission" or owner == "model_output":
        return "model_output_invalid_submission"
    return "other_not_attemptable"


def patch_replay_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("matrix", [])):
        if not isinstance(item, Mapping):
            continue
        old = item.get("old") if isinstance(item.get("old"), Mapping) else {}
        repaired = item.get("repaired") if isinstance(item.get("repaired"), Mapping) else {}
        raw_path = old.get("raw_response_artifact") if isinstance(old.get("raw_response_artifact"), str) else None
        historical_category = category_from_old_record(old)
        stable_category = category_from_repaired(repaired, old)
        historical_cost = old.get("historical_provider_usage_cost_usd")
        if historical_cost is None:
            historical_cost = response_usage_cost(raw_path)
        row = {
            "matrix_source": "patch_or_files_replay",
            "source_label": "patch_or_files_v1_live",
            "evidence_mode": "no_model_historical_replay",
            "contract": PATCH_OR_FILES_CONTRACT,
            "denominator_kind": "fixed_acut_task_cells",
            "index": index,
            "acut_id": item.get("acut_id"),
            "task_id": item.get("task_id"),
            "run_id": item.get("run_id"),
            "historical_status": old.get("status"),
            "historical_failure_owner": old.get("failure_owner"),
            "historical_failure_class": old.get("failure_class"),
            "historical_category": historical_category,
            "stable_status": repaired.get("status"),
            "stable_failure_owner": repaired.get("failure_owner"),
            "stable_failure_class": repaired.get("failure_class"),
            "stable_category": stable_category,
            "verifier_attemptable_after_replay": stable_category in ATTEMPTABLE_CATEGORIES,
            "became_verifier_attemptable": (
                historical_category not in ATTEMPTABLE_CATEGORIES
                and stable_category in ATTEMPTABLE_CATEGORIES
            ),
            "verifier_ready_persisted_patch_artifact": stable_category == "verifier_ready_persisted_patch_artifact",
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": (
                "verifier_ready_patch_artifact"
                if stable_category == "verifier_ready_persisted_patch_artifact"
                else "not_attempted"
            ),
            "cleanup_blocker": False,
            "historical_model_call_made": old.get("model_call_made"),
            "replay_model_call_made": repaired.get("model_call_made"),
            "new_model_call_made_for_this_package": False,
            "historical_provider_usage_cost_usd": historical_cost,
            "replay_model_spend_usd": repaired.get("model_spend_usd", 0.0),
            "raw_response_artifact": raw_path,
            "prompt_snapshot": old.get("prompt_snapshot"),
            "normalized_result": old.get("normalized_result"),
            "response_shape": response_shape(raw_path),
            "artifact_presence": artifact_presence(old.get("normalized_result"), raw_path, old.get("prompt_snapshot")),
            "classification_delta": item.get("classification_delta"),
            "content_recorded": False,
        }
        rows.append(row)
    return rows


def existing_patch_or_files_path_rows(summary: Mapping[str, Any], path_id: str) -> list[dict[str, Any]]:
    records_by_path = summary.get("records") if isinstance(summary.get("records"), Mapping) else {}
    records = records_by_path.get(path_id) if isinstance(records_by_path.get(path_id), list) else []
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            continue
        raw_path = record.get("raw_response_artifact") if isinstance(record.get("raw_response_artifact"), str) else None
        normalized_path = record.get("normalized_result") if isinstance(record.get("normalized_result"), str) else None
        normalized = maybe_read_json(normalized_path)
        verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
        category = category_from_old_record(record)
        row = {
            "matrix_source": "m2_scoreability_summary_existing_path",
            "source_label": path_id,
            "evidence_mode": "existing_no_model_control",
            "contract": PATCH_OR_FILES_CONTRACT,
            "denominator_kind": "fixed_acut_task_cells",
            "index": index,
            "acut_id": record.get("acut_id"),
            "task_id": record.get("task_id"),
            "run_id": record.get("run_id"),
            "historical_status": record.get("status"),
            "historical_failure_owner": record.get("failure_owner"),
            "historical_failure_class": record.get("failure_class"),
            "historical_category": category,
            "stable_status": record.get("status"),
            "stable_failure_owner": record.get("failure_owner"),
            "stable_failure_class": record.get("failure_class"),
            "stable_category": category,
            "verifier_attemptable_after_replay": category in ATTEMPTABLE_CATEGORIES,
            "became_verifier_attemptable": False,
            "verifier_ready_persisted_patch_artifact": category == "verifier_ready_persisted_patch_artifact",
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": (
                "verifier_ready_patch_artifact"
                if category == "verifier_ready_persisted_patch_artifact"
                else "not_attempted"
            ),
            "cleanup_blocker": False,
            "historical_model_call_made": record.get("model_call_made"),
            "replay_model_call_made": record.get("model_call_made"),
            "new_model_call_made_for_this_package": False,
            "historical_provider_usage_cost_usd": response_usage_cost(raw_path),
            "replay_model_spend_usd": 0.0 if record.get("model_call_made") is False else None,
            "raw_response_artifact": raw_path,
            "prompt_snapshot": record.get("prompt_snapshot"),
            "normalized_result": normalized_path,
            "response_shape": response_shape(raw_path),
            "artifact_presence": artifact_presence(normalized_path, raw_path, record.get("prompt_snapshot")),
            "classification_delta": None,
            "verifier_exit_code": verification.get("exit_code"),
            "content_recorded": False,
        }
        rows.append(row)
    return rows


def metadata_from_item(item: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    normalized = item.get("normalized") if isinstance(item.get("normalized"), Mapping) else {}
    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
    runner_result = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
    return dict(normalized), dict(metadata), dict(runner_result)


def anchored_failure_class(
    item: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner_result: Mapping[str, Any],
) -> str | None:
    details = runner_result.get("details") if isinstance(runner_result.get("details"), Mapping) else {}
    return first_string(
        metadata.get("failure_class"),
        item.get("failure_class"),
        runner_result.get("failure_class"),
        details.get("failure_class") if isinstance(details, Mapping) else None,
    )


def anchored_failure_owner(
    item: Mapping[str, Any],
    metadata: Mapping[str, Any],
    status: str,
) -> str:
    owner = first_string(metadata.get("failure_owner"), item.get("failure_owner"))
    if owner:
        return owner
    if status == "passed":
        return "none"
    if status in {"failed", "timeout"}:
        return "candidate_patch"
    if status == "invalid_submission":
        return "model_output"
    if status == "infra_failed":
        return "infrastructure"
    return "unknown"


def anchored_category(
    item: Mapping[str, Any],
    normalized: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner_result: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    readiness = metadata.get("patch_readiness") if isinstance(metadata.get("patch_readiness"), Mapping) else {}
    verifier_attempt = metadata.get("verifier_attempt") if isinstance(metadata.get("verifier_attempt"), Mapping) else {}
    nonpersistent = (
        metadata.get("nonpersistent_verifier_channel")
        if isinstance(metadata.get("nonpersistent_verifier_channel"), Mapping)
        else item.get("nonpersistent_verifier")
        if isinstance(item.get("nonpersistent_verifier"), Mapping)
        else {}
    )
    cleanup = (
        nonpersistent.get("transient_workspace_cleanup")
        if isinstance(nonpersistent.get("transient_workspace_cleanup"), Mapping)
        else {}
    )
    status = str(item.get("status") or normalized.get("status") or "unknown")
    failure_class = anchored_failure_class(item, metadata, runner_result)
    owner = anchored_failure_owner(item, metadata, status)
    verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
    verifier_exit_code = verification.get("exit_code")
    nonpersistent_attempted = bool(
        nonpersistent.get("attempted") is True
        or verifier_attempt.get("channel") == "nonpersistent_preapplied_workspace"
        or readiness.get("nonpersistent_verifier_attempted") is True
    )
    persisted_attempted = bool(
        verifier_attempt.get("channel") == "verifier_ready_patch_artifact"
        or (
            readiness.get("verifier_ready_patch_available") is True
            and verifier_attempt.get("attempted") is True
        )
    )
    if nonpersistent_attempted and cleanup and cleanup.get("removed") is not True:
        return "cleanup_blocker", {
            "nonpersistent_verifier_attempted": True,
            "verifier_attempt_channel": "nonpersistent_preapplied_workspace",
            "cleanup_blocker": True,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    if failure_class == "nonpersistent_transient_workspace_cleanup_failed":
        return "cleanup_blocker", {
            "nonpersistent_verifier_attempted": nonpersistent_attempted,
            "verifier_attempt_channel": "nonpersistent_preapplied_workspace",
            "cleanup_blocker": True,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    if nonpersistent_attempted:
        return "nonpersistent_verifier_attempt", {
            "nonpersistent_verifier_attempted": True,
            "verifier_attempt_channel": "nonpersistent_preapplied_workspace",
            "cleanup_blocker": False,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    if persisted_attempted and status in {"passed", "failed", "timeout"} and isinstance(verifier_exit_code, int):
        return "verifier_ready_persisted_patch_artifact", {
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": "verifier_ready_patch_artifact",
            "cleanup_blocker": False,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    raw_path = first_string(
        metadata.get("raw_response_artifact"),
        runner_result.get("raw_response_artifact"),
        item.get("raw_response_artifact"),
    )
    if raw_path is None or not Path(raw_path).exists():
        return "missing_raw_artifact", {
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": "not_attempted",
            "cleanup_blocker": False,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    if status == "infra_failed" or owner == "infrastructure":
        return "infra_failure", {
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": "not_attempted",
            "cleanup_blocker": False,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    if status == "invalid_submission" or owner == "model_output":
        return "model_output_invalid_submission", {
            "nonpersistent_verifier_attempted": False,
            "verifier_attempt_channel": (
                "verifier_ready_patch_artifact_clean_apply_blocked"
                if persisted_attempted
                else "not_attempted"
            ),
            "cleanup_blocker": False,
            "transient_workspace_cleanup": cleanup,
            "verifier_exit_code": verifier_exit_code,
        }
    return "other_not_attemptable", {
        "nonpersistent_verifier_attempted": False,
        "verifier_attempt_channel": "not_attempted",
        "cleanup_blocker": False,
        "transient_workspace_cleanup": cleanup,
        "verifier_exit_code": verifier_exit_code,
    }


def anchored_batch_rows(label: str, mode: str, path: str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("results", [])):
        if not isinstance(item, Mapping):
            continue
        normalized, metadata, runner_result = metadata_from_item(item)
        category, details = anchored_category(item, normalized, metadata, runner_result)
        raw_path = first_string(
            metadata.get("raw_response_artifact"),
            runner_result.get("raw_response_artifact"),
            item.get("raw_response_artifact"),
        )
        prompt = first_string(metadata.get("prompt_snapshot"), runner_result.get("prompt_snapshot"), item.get("prompt_snapshot"))
        normalized_result = first_string(item.get("normalized_result"))
        status = str(item.get("status") or normalized.get("status") or "unknown")
        failure_class = anchored_failure_class(item, metadata, runner_result)
        failure_owner = anchored_failure_owner(item, metadata, status)
        shape = response_shape(raw_path)
        row = {
            "matrix_source": "anchored_batch",
            "source_label": label,
            "source_path": path,
            "evidence_mode": mode,
            "contract": ANCHORED_CONTRACT,
            "denominator_kind": "fixed_input_records",
            "index": index,
            "acut_id": item.get("acut_id"),
            "task_id": item.get("task_id"),
            "run_id": item.get("run_id"),
            "historical_status": status,
            "historical_failure_owner": failure_owner,
            "historical_failure_class": failure_class,
            "historical_category": category,
            "stable_status": status,
            "stable_failure_owner": failure_owner,
            "stable_failure_class": failure_class,
            "stable_category": category,
            "verifier_attemptable_after_replay": category in ATTEMPTABLE_CATEGORIES,
            "became_verifier_attemptable": False,
            "verifier_ready_persisted_patch_artifact": category == "verifier_ready_persisted_patch_artifact",
            "nonpersistent_verifier_attempted": details["nonpersistent_verifier_attempted"],
            "verifier_attempt_channel": details["verifier_attempt_channel"],
            "cleanup_blocker": details["cleanup_blocker"],
            "transient_workspace_cleanup": details["transient_workspace_cleanup"],
            "verifier_exit_code": details["verifier_exit_code"],
            "historical_model_call_made": metadata.get("model_call_made", runner_result.get("model_call_made")),
            "replay_model_call_made": metadata.get("model_call_made", runner_result.get("model_call_made"))
            if mode == "no_model_replay"
            else None,
            "new_model_call_made_for_this_package": False,
            "historical_provider_usage_cost_usd": response_usage_cost(raw_path),
            "replay_model_spend_usd": 0.0 if mode == "no_model_replay" else None,
            "raw_response_artifact": raw_path,
            "prompt_snapshot": prompt,
            "normalized_result": normalized_result,
            "response_shape": shape,
            "artifact_presence": artifact_presence(normalized_result, raw_path, prompt),
            "classification_delta": None,
            "content_recorded": False,
        }
        rows.append(row)
    return rows


def mark_anchored_transitions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_response: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        shape = row.get("response_shape") if isinstance(row.get("response_shape"), Mapping) else {}
        digest = shape.get("response_sha256")
        if isinstance(digest, str):
            by_response.setdefault(digest, []).append(row)
    for group in by_response.values():
        has_prior_not_attemptable = any(
            row.get("evidence_mode") == "historical_live"
            and row.get("stable_category") not in ATTEMPTABLE_CATEGORIES
            for row in group
        )
        if not has_prior_not_attemptable:
            continue
        for row in group:
            if row.get("evidence_mode") == "no_model_replay" and row.get("stable_category") in ATTEMPTABLE_CATEGORIES:
                row["became_verifier_attemptable"] = True
    return rows


def missing_artifact_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_raw_rows = [
        row
        for row in rows
        if row.get("stable_category") == "missing_raw_artifact"
        or not (
            isinstance(row.get("artifact_presence"), Mapping)
            and row["artifact_presence"].get("raw_response_artifact_exists") is True
        )
    ]
    return {
        "missing_raw_artifact_count": len(missing_raw_rows),
        "missing_raw_artifact_rows": [
            {
                "source_label": row.get("source_label"),
                "acut_id": row.get("acut_id"),
                "task_id": row.get("task_id"),
                "run_id": row.get("run_id"),
                "failure_class": row.get("stable_failure_class"),
            }
            for row in missing_raw_rows
        ],
        "missing_prompt_snapshot_count": sum(
            1
            for row in rows
            if not (
                isinstance(row.get("artifact_presence"), Mapping)
                and row["artifact_presence"].get("prompt_snapshot_exists") is True
            )
        ),
        "missing_normalized_result_count": sum(
            1
            for row in rows
            if not (
                isinstance(row.get("artifact_presence"), Mapping)
                and row["artifact_presence"].get("normalized_result_exists") is True
            )
        ),
    }


def cost_model_call_accounting(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    historical_costs = [
        float(row.get("historical_provider_usage_cost_usd"))
        for row in rows
        if isinstance(row.get("historical_provider_usage_cost_usd"), (int, float))
    ]
    replay_spend = [
        float(row.get("replay_model_spend_usd"))
        for row in rows
        if isinstance(row.get("replay_model_spend_usd"), (int, float))
    ]
    return {
        "historical": {
            "model_call_made_counts": count_by(rows, "historical_model_call_made"),
            "provider_usage_cost_usd_observed_sum": round(sum(historical_costs), 6),
            "provider_usage_cost_observed_count": len(historical_costs),
            "provider_usage_cost_status": "historical_provider_response_usage_not_new_spend",
        },
        "replay": {
            "model_call_made_counts": count_by(rows, "replay_model_call_made"),
            "new_model_call_made_count": sum(1 for row in rows if row.get("new_model_call_made_for_this_package") is True),
            "model_spend_usd_observed_sum": round(sum(replay_spend), 6),
            "live_api_calls": False,
            "canonical_cost_ledger_mutated": False,
        },
    }


def aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_contract: dict[str, dict[str, Any]] = {}
    for contract in sorted({str(row.get("contract")) for row in rows}):
        contract_rows = [row for row in rows if row.get("contract") == contract]
        by_contract[contract] = {
            "fixed_denominator": len(contract_rows),
            "category_counts": count_by(contract_rows, "stable_category"),
            "historical_category_counts": count_by(contract_rows, "historical_category"),
            "verifier_attemptable_count": sum(
                1 for row in contract_rows if row.get("stable_category") in ATTEMPTABLE_CATEGORIES
            ),
            "verifier_ready_persisted_patch_artifact_count": sum(
                1
                for row in contract_rows
                if row.get("stable_category") == "verifier_ready_persisted_patch_artifact"
            ),
            "nonpersistent_verifier_attempt_count": sum(
                1 for row in contract_rows if row.get("stable_category") == "nonpersistent_verifier_attempt"
            ),
            "prior_failures_became_verifier_attemptable_count": sum(
                1 for row in contract_rows if row.get("became_verifier_attemptable") is True
            ),
            "attemptable_rate": rate(
                sum(1 for row in contract_rows if row.get("stable_category") in ATTEMPTABLE_CATEGORIES),
                len(contract_rows),
            ),
        }
    return {
        "fixed_denominator": len(rows),
        "category_counts": count_by(rows, "stable_category"),
        "historical_category_counts": count_by(rows, "historical_category"),
        "verifier_attemptable_count": sum(1 for row in rows if row.get("stable_category") in ATTEMPTABLE_CATEGORIES),
        "verifier_ready_persisted_patch_artifact_count": sum(
            1 for row in rows if row.get("stable_category") == "verifier_ready_persisted_patch_artifact"
        ),
        "nonpersistent_verifier_attempt_count": sum(
            1 for row in rows if row.get("stable_category") == "nonpersistent_verifier_attempt"
        ),
        "model_output_invalid_submission_count": sum(
            1 for row in rows if row.get("stable_category") == "model_output_invalid_submission"
        ),
        "infra_failure_count": sum(1 for row in rows if row.get("stable_category") == "infra_failure"),
        "missing_raw_artifact_count": sum(1 for row in rows if row.get("stable_category") == "missing_raw_artifact"),
        "cleanup_blocker_count": sum(1 for row in rows if row.get("stable_category") == "cleanup_blocker"),
        "prior_failures_became_verifier_attemptable_count": sum(
            1 for row in rows if row.get("became_verifier_attemptable") is True
        ),
        "attemptable_rate": rate(sum(1 for row in rows if row.get("stable_category") in ATTEMPTABLE_CATEGORIES), len(rows)),
        "by_contract": by_contract,
    }


def blocker_summary(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    tasks = [str(item) for item in summary.get("tasks", []) if isinstance(item, str)]
    acuts = [str(item) for item in summary.get("acuts", []) if isinstance(item, str)]
    expected_grid = {(acut, task) for acut in acuts for task in tasks}
    anchored_cells = {
        (str(row.get("acut_id")), str(row.get("task_id")))
        for row in rows
        if row.get("contract") == ANCHORED_CONTRACT and row.get("acut_id") and row.get("task_id")
    }
    missing_cells = sorted(expected_grid - anchored_cells)
    if expected_grid and missing_cells:
        blockers.append(
            {
                "blocker_id": "anchored_search_replace_fixed_grid_inputs_insufficient",
                "status": "blocked",
                "expected_fixed_denominator": len(expected_grid),
                "observed_unique_cell_count": len(anchored_cells),
                "missing_cell_count": len(missing_cells),
                "missing_cells": [
                    {"acut_id": acut_id, "task_id": task_id}
                    for acut_id, task_id in missing_cells
                ],
                "effect": (
                    "anchored-search-replace evidence is limited to recorded target-cell smoke/replay artifacts; "
                    "do not claim full M2 matrix passage or coverage"
                ),
            }
        )
    return blockers


def output_leakage_guard(payload: Mapping[str, Any]) -> dict[str, Any]:
    findings = unsafe_text_findings(json.dumps(payload, sort_keys=True))
    return {
        "contains_raw_unsafe_text": bool(findings["unsafe"]),
        "reason_counts": findings["reason_counts"],
    }


def attach_output_leakage_guard(payload: dict[str, Any]) -> None:
    payload["output_leakage_guard"] = output_leakage_guard(payload)
    final_guard = output_leakage_guard(payload)
    payload["output_leakage_guard"] = final_guard
    if final_guard["contains_raw_unsafe_text"]:
        raise ToolError("stable replay matrix output would contain raw unsafe text", reason_counts=final_guard["reason_counts"])


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    m2_summary = read_json(args.m2_summary)
    patch_replay = read_json(args.patch_replay)
    anchored_inputs = args.anchored_batch if args.anchored_batch is not None else list(DEFAULT_ANCHORED_BATCHES)
    rows = patch_replay_rows(patch_replay)
    rows.extend(existing_patch_or_files_path_rows(m2_summary, "patch_or_files_v1_no_model"))
    anchored_rows: list[dict[str, Any]] = []
    anchored_evidence_inputs: list[dict[str, Any]] = []
    for label, mode, path in anchored_inputs:
        if mode not in {"historical_live", "no_model_replay", "blocker"}:
            raise ToolError("unsupported anchored evidence mode", label=label, mode=mode)
        anchored_evidence_inputs.append({"label": label, "mode": mode, "path": path})
        if mode == "blocker":
            continue
        anchored_rows.extend(anchored_batch_rows(label, mode, path))
    rows.extend(mark_anchored_transitions(anchored_rows))
    blockers = blocker_summary(m2_summary, rows)
    payload: dict[str, Any] = {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "m2_summary": args.m2_summary,
            "patch_replay": args.patch_replay,
            "anchored_batches": anchored_evidence_inputs,
            "output": args.output,
            "report": args.report,
        },
        "scope": {
            "patch_or_files_contract": PATCH_OR_FILES_CONTRACT,
            "anchored_contract": ANCHORED_CONTRACT,
            "m2_tasks": m2_summary.get("tasks"),
            "m2_acuts": m2_summary.get("acuts"),
            "m2_fixed_denominator": m2_summary.get("fixed_denominator"),
            "patch_or_files_matrix_rows": sum(1 for row in rows if row.get("contract") == PATCH_OR_FILES_CONTRACT),
            "anchored_input_rows": sum(1 for row in rows if row.get("contract") == ANCHORED_CONTRACT),
            "fixed_denominators": {
                "patch_or_files_v1_live": patch_replay.get("scope", {}).get("fixed_denominator")
                if isinstance(patch_replay.get("scope"), Mapping)
                else None,
                "patch_or_files_v1_no_model": len(existing_patch_or_files_path_rows(m2_summary, "patch_or_files_v1_no_model")),
                "anchored_search_replace_existing_records": sum(
                    1 for row in rows if row.get("contract") == ANCHORED_CONTRACT
                ),
            },
        },
        "method": {
            "model_calls": "none_in_this_package",
            "uses_existing_provider_responses": True,
            "patch_or_files_replay_source": "m2_repaired_parser_replay output generated with current parser/applicator",
            "patch_or_files_no_model_source": "existing M2 no-model verifier-ready control records from m2_scoreability_summary",
            "anchored_evidence_source": "existing M2 anchored live-smoke and no-model nonpersistent replay batch outputs",
            "verifier_success_claim": "not_claimed",
            "claim_boundary": "verifier-attemptability and artifact channel accounting only",
            "content_policy": "hashes, counts, paths, and metadata only; raw provider text is not copied into the summary",
        },
        "summary": aggregate(rows),
        "missing_artifact_summary": missing_artifact_summary(rows),
        "cost_model_call_accounting": cost_model_call_accounting(rows),
        "blockers": blockers,
        "matrix": rows,
        "claim_status": "stable_nonpersistent_replay_matrix_not_m2_pass",
        "claim_boundaries": {
            **PROHIBITED_CLAIMS,
            "new_model_calls": False,
            "verifier_or_task_success_measured_by_this_package": False,
            "anchored_full_fixed_grid_available": not blockers,
        },
        "prohibited_claims": dict(PROHIBITED_CLAIMS),
    }
    attach_output_leakage_guard(payload)
    return payload


def pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def write_report(payload: Mapping[str, Any], path: str) -> None:
    scope = payload.get("scope") if isinstance(payload.get("scope"), Mapping) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    cost = payload.get("cost_model_call_accounting") if isinstance(payload.get("cost_model_call_accounting"), Mapping) else {}
    replay_cost = cost.get("replay") if isinstance(cost.get("replay"), Mapping) else {}
    missing = payload.get("missing_artifact_summary") if isinstance(payload.get("missing_artifact_summary"), Mapping) else {}
    generated_at = str(payload.get("generated_at") or "")
    date_from_path = re.search(r"\d{4}-\d{2}-\d{2}", str(path))
    report_date = (
        date_from_path.group(0)
        if date_from_path
        else generated_at[:10]
        if len(generated_at) >= 10
        else "2026-05-10"
    )
    lines = [
        "# M2 Stable Nonpersistent Replay Matrix",
        "",
        f"Date: {report_date}",
        "",
        "## Scope",
        "",
        f"- Patch-or-files fixed denominator: `{scope.get('fixed_denominators', {}).get('patch_or_files_v1_live')}`.",
        f"- Patch-or-files no-model control denominator: `{scope.get('fixed_denominators', {}).get('patch_or_files_v1_no_model')}`.",
        f"- Anchored input-record denominator: `{scope.get('fixed_denominators', {}).get('anchored_search_replace_existing_records')}`.",
        f"- New model calls in this package: `{replay_cost.get('new_model_call_made_count')}`.",
        "- This is verifier-attemptability and artifact-channel accounting only.",
        "",
        "## Aggregate",
        "",
        f"- Category counts: `{summary.get('category_counts')}`.",
        f"- Verifier-attemptable count: `{summary.get('verifier_attemptable_count')}` ({pct(summary.get('attemptable_rate'))}).",
        f"- Persisted patch-artifact attemptable count: `{summary.get('verifier_ready_persisted_patch_artifact_count')}`.",
        f"- Nonpersistent verifier attempts: `{summary.get('nonpersistent_verifier_attempt_count')}`.",
        f"- Prior failures becoming verifier-attemptable: `{summary.get('prior_failures_became_verifier_attemptable_count')}`.",
        f"- Missing raw artifacts: `{missing.get('missing_raw_artifact_count')}`.",
        "",
        "## By Contract",
        "",
        "| Contract | Rows | Attemptable | Persisted patch | Nonpersistent | Model invalid | Infra | Missing raw | Cleanup blockers | Became attemptable |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    by_contract = summary.get("by_contract") if isinstance(summary.get("by_contract"), Mapping) else {}
    for contract, item in by_contract.items():
        if not isinstance(item, Mapping):
            continue
        cats = item.get("category_counts") if isinstance(item.get("category_counts"), Mapping) else {}
        lines.append(
            f"| `{contract}` | {item.get('fixed_denominator')} | {item.get('verifier_attemptable_count')} | "
            f"{item.get('verifier_ready_persisted_patch_artifact_count')} | {item.get('nonpersistent_verifier_attempt_count')} | "
            f"{cats.get('model_output_invalid_submission', 0)} | {cats.get('infra_failure', 0)} | "
            f"{cats.get('missing_raw_artifact', 0)} | {cats.get('cleanup_blocker', 0)} | "
            f"{item.get('prior_failures_became_verifier_attemptable_count')} |"
        )
    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| Source | Mode | ACUT | Task | Category | Owner | Class | Channel | Became attemptable |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload.get("matrix", []):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| `{row.get('source_label')}` | `{row.get('evidence_mode')}` | `{row.get('acut_id')}` | "
            f"`{row.get('task_id')}` | `{row.get('stable_category')}` | `{row.get('stable_failure_owner')}` | "
            f"`{row.get('stable_failure_class')}` | `{row.get('verifier_attempt_channel')}` | "
            f"`{row.get('became_verifier_attemptable')}` |"
        )
    blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    lines.extend(["", "## Blockers", ""])
    if blockers:
        for blocker in blockers:
            if isinstance(blocker, Mapping):
                lines.append(
                    f"- `{blocker.get('blocker_id')}`: expected `{blocker.get('expected_fixed_denominator')}` "
                    f"anchored grid cells, observed `{blocker.get('observed_unique_cell_count')}`; "
                    f"missing `{blocker.get('missing_cell_count')}`."
                )
    else:
        lines.append("- None recorded.")
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "```bash",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_repaired_parser_replay.py \\",
            f"  --m2-summary {inputs.get('m2_summary')} \\",
            "  --path-id patch_or_files_v1_live \\",
            "  --run-prefix m2_stable_nonpersistent_replay_matrix_patch_or_files_20260510 \\",
            "  --force \\",
            f"  --output {inputs.get('patch_replay')} \\",
            "  --report experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_patch_or_files_replay.md",
            "",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_stable_nonpersistent_replay_matrix.py \\",
            f"  --m2-summary {inputs.get('m2_summary')} \\",
            f"  --patch-replay {inputs.get('patch_replay')} \\",
            f"  --output {inputs.get('output')} \\",
            f"  --report {inputs.get('report')}",
            "```",
            "",
            "## Claim Boundaries",
            "",
            "This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.",
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
