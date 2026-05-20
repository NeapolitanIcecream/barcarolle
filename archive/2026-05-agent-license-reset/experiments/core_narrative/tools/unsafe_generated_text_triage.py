#!/usr/bin/env python3
"""No-model triage for unsafe_generated_text experiment cells."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now
from _llm_budget import unsafe_text_findings


TOOL = "unsafe_generated_text_triage"
DEFAULT_ACUTS = ("cheap-generic-swe", "cheap-click-specialist")
DEFAULT_TASKS = ("click__rwork__004", "click__rwork__006")
STRUCTURED_CONTRACT = "structured-files-json-v1"

TRUE_POSITIVE = "safety_policy_true_positive"
FALSE_POSITIVE = "safety_policy_false_positive"
OVERBREADTH = "prompt_or_applicator_overbreadth"
AMBIGUOUS = "provider_or_artifact_ambiguous"
OTHER = "other"

SECRET_OR_CREDENTIAL_REASONS = {
    "bearer_token",
    "credential_literal_value",
    "provider_token",
    "resolved_llm_environment_value",
}

RAW_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
REDACTED_URL_MARKER = "<redacted:url>"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True, help="M1.1 batch JSON to triage.")
    parser.add_argument("--output", required=True, help="Sanitized machine-readable triage JSON.")
    parser.add_argument("--repo-root", default=str(default_repo_root()))
    parser.add_argument("--acuts", nargs="+", default=list(DEFAULT_ACUTS))
    parser.add_argument("--tasks", nargs="+", default=list(DEFAULT_TASKS))
    return parser.parse_args(list(argv))


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolError("JSON input does not exist", path=str(path)) from exc
    except json.JSONDecodeError as exc:
        raise ToolError("JSON input is not valid JSON", path=str(path), error=str(exc)) from exc
    if not isinstance(data, dict):
        raise ToolError("JSON input root must be an object", path=str(path))
    return data


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def normalize_reason_counts(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    counts: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str):
            continue
        if isinstance(count, int):
            normalized = count
        elif isinstance(count, float) and count.is_integer():
            normalized = int(count)
        else:
            continue
        if normalized > 0:
            counts[key] = normalized
    return dict(sorted(counts.items()))


def safe_path(value: object, *, repo_root: Path) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    try:
        resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    except OSError:
        return Path(value).name
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return f"<outside-repo>/{resolved.name}"


def safe_status_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if RAW_URL_RE.search(normalized):
        return "<redacted:path>"
    return normalized


def provider_redacted_artifact_features(path_value: object, *, repo_root: Path) -> dict[str, Any]:
    safe = safe_path(path_value, repo_root=repo_root)
    if not isinstance(path_value, str) or not path_value:
        return {
            "path": safe,
            "exists": False,
            "json_valid": None,
            "redacted_url_marker_count": 0,
            "raw_url_like_count": 0,
            "content_char_count": None,
            "enough_for_sanitized_review": False,
        }
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        return {
            "path": safe,
            "exists": False,
            "json_valid": None,
            "redacted_url_marker_count": 0,
            "raw_url_like_count": 0,
            "content_char_count": None,
            "enough_for_sanitized_review": False,
        }

    text = path.read_text(encoding="utf-8", errors="replace")
    raw_url_count = len(RAW_URL_RE.findall(text))
    marker_count = text.count(REDACTED_URL_MARKER)
    content_char_count: int | None = None
    json_valid = False
    try:
        data = json.loads(text)
        json_valid = isinstance(data, dict)
        content = (
            as_mapping(as_mapping((data.get("choices") or [None])[0]).get("message")).get("content")
            if isinstance(data.get("choices"), list) and data.get("choices")
            else None
        )
        if isinstance(content, str):
            content_char_count = len(content)
    except (json.JSONDecodeError, AttributeError, IndexError, TypeError):
        json_valid = False

    return {
        "path": safe,
        "exists": True,
        "json_valid": json_valid,
        "redacted_url_marker_count": marker_count,
        "raw_url_like_count": raw_url_count,
        "content_char_count": content_char_count,
        "enough_for_sanitized_review": json_valid and raw_url_count == 0,
    }


def workspace_status_features(workspace_value: object, *, repo_root: Path) -> dict[str, Any]:
    safe = safe_path(workspace_value, repo_root=repo_root)
    if not isinstance(workspace_value, str) or not workspace_value:
        return {
            "path": safe,
            "status_available": False,
            "workspace_mutation_happened": None,
            "tracked_changed_paths": [],
            "untracked_non_harness_paths": [],
            "harness_metadata_untracked_count": 0,
        }
    workspace = Path(workspace_value)
    if not workspace.is_absolute():
        workspace = repo_root / workspace
    if not workspace.exists():
        return {
            "path": safe,
            "status_available": False,
            "workspace_mutation_happened": None,
            "tracked_changed_paths": [],
            "untracked_non_harness_paths": [],
            "harness_metadata_untracked_count": 0,
        }

    result = subprocess.run(
        ["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "path": safe,
            "status_available": False,
            "workspace_mutation_happened": None,
            "tracked_changed_paths": [],
            "untracked_non_harness_paths": [],
            "harness_metadata_untracked_count": 0,
        }

    tracked: list[str] = []
    untracked: list[str] = []
    harness_untracked = 0
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        raw_path = raw_path.strip()
        if raw_path == ".core_narrative" or raw_path.startswith(".core_narrative/"):
            harness_untracked += 1
            continue
        if status == "??":
            untracked.append(safe_status_path(raw_path))
        else:
            tracked.append(safe_status_path(raw_path))

    return {
        "path": safe,
        "status_available": True,
        "workspace_mutation_happened": bool(tracked or untracked),
        "tracked_changed_paths": sorted(tracked),
        "untracked_non_harness_paths": sorted(untracked),
        "harness_metadata_untracked_count": harness_untracked,
    }


def contract_markers(
    item: Mapping[str, Any],
    normalized: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner: Mapping[str, Any],
) -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    sources = (
        ("batch", item),
        ("normalized", normalized),
        ("normalized.metadata", metadata),
        ("runner_result", runner),
    )
    for source_name, source in sources:
        for key in ("submission_contract", "output_contract"):
            value = source.get(key)
            if isinstance(value, str) and value:
                markers.append({"source": source_name, "field": key, "value": value})
    return markers


def load_runner_result(item: Mapping[str, Any], artifact_dir: object, *, repo_root: Path) -> Mapping[str, Any]:
    runner = item.get("runner_result")
    if isinstance(runner, Mapping):
        return runner
    if isinstance(artifact_dir, str) and artifact_dir:
        path = Path(artifact_dir)
        if not path.is_absolute():
            path = repo_root / path
        candidate = path / "runner_result.json"
        if candidate.exists():
            try:
                return read_json(candidate)
            except ToolError:
                return {}
    return {}


def load_normalized(item: Mapping[str, Any], *, repo_root: Path) -> Mapping[str, Any]:
    normalized = item.get("normalized")
    if isinstance(normalized, Mapping):
        return normalized
    path_value = item.get("normalized_result")
    if isinstance(path_value, str) and path_value:
        path = Path(path_value)
        if not path.is_absolute():
            path = repo_root / path
        if path.exists():
            try:
                return read_json(path)
            except ToolError:
                return {}
    return {}


def failure_class_from(
    normalized: Mapping[str, Any],
    metadata: Mapping[str, Any],
    runner: Mapping[str, Any],
) -> str | None:
    details = as_mapping(runner.get("details"))
    return first_string(
        metadata.get("failure_class"),
        runner.get("failure_class"),
        details.get("failure_class"),
        normalized.get("failure_class"),
    )


def reason_counts_from(runner: Mapping[str, Any]) -> dict[str, int]:
    details = as_mapping(runner.get("details"))
    unsafe = as_mapping(details.get("unsafe_content"))
    if unsafe:
        return normalize_reason_counts(unsafe.get("reason_counts"))
    patch_artifact = as_mapping(runner.get("patch_artifact"))
    patch_unsafe = as_mapping(patch_artifact.get("unsafe_content"))
    return normalize_reason_counts(patch_unsafe.get("reason_counts"))


def enough_redacted_evidence(
    *,
    failure_class: str | None,
    reason_counts: Mapping[str, int],
    provider: Mapping[str, Any],
    markers: Sequence[Mapping[str, str]],
) -> bool:
    return (
        failure_class == "unsafe_generated_text"
        and bool(reason_counts)
        and provider.get("exists") is True
        and provider.get("json_valid") is True
        and provider.get("raw_url_like_count") == 0
        and bool(markers)
    )


def classify_cell(features: Mapping[str, Any]) -> tuple[str, str]:
    if features.get("cell_present") is not True:
        return OTHER, "missing target cell in fixed denominator"

    failure_class = features.get("failure_class")
    if failure_class != "unsafe_generated_text":
        return OTHER, "target cell is not an unsafe_generated_text failure"

    provider = as_mapping(features.get("redacted_provider_artifact"))
    reason_counts = normalize_reason_counts(features.get("reason_counts"))
    if not reason_counts:
        return FALSE_POSITIVE, "unsafe_generated_text was recorded without positive unsafe reason counts"

    if provider.get("exists") is not True or provider.get("json_valid") is not True:
        return AMBIGUOUS, "provider redacted artifact is missing or not valid JSON"

    if provider.get("raw_url_like_count"):
        return AMBIGUOUS, "redacted provider artifact still contains raw URL-like text"

    if any(reason_counts.get(reason, 0) > 0 for reason in SECRET_OR_CREDENTIAL_REASONS):
        return TRUE_POSITIVE, "secret or credential-like generated text reason was detected"

    only_full_url = set(reason_counts) == {"full_url"}
    error = str(features.get("error") or "")
    workspace = as_mapping(features.get("workspace"))
    patch_written = features.get("patch_written") is True
    if only_full_url and "model response" in error and workspace.get("workspace_mutation_happened") is not True:
        return TRUE_POSITIVE, "model response itself triggered the configured full-url safety policy"

    if (
        only_full_url
        and "generated patch" in error
        and patch_written is False
        and workspace.get("workspace_mutation_happened") is True
    ):
        return (
            OVERBREADTH,
            "full-url rejection happened during patch artifact collection after workspace mutation, before patch write",
        )

    if only_full_url:
        return AMBIGUOUS, "full-url-only finding lacks enough redacted source attribution"

    return TRUE_POSITIVE, "non-URL unsafe generated text reason was detected"


def cell_features(
    *,
    item: Mapping[str, Any] | None,
    acut_id: str,
    task_id: str,
    repo_root: Path,
) -> dict[str, Any]:
    if item is None:
        return {
            "cell_present": False,
            "acut_id": acut_id,
            "task_id": task_id,
            "classification": OTHER,
            "classification_detail": "missing target cell in fixed denominator",
            "enough_redacted_evidence": False,
        }

    artifact_dir = item.get("artifact_dir")
    runner = load_runner_result(item, artifact_dir, repo_root=repo_root)
    normalized = load_normalized(item, repo_root=repo_root)
    metadata = as_mapping(normalized.get("metadata"))
    markers = contract_markers(item, normalized, metadata, runner)
    failure_class = failure_class_from(normalized, metadata, runner)
    reason_counts = reason_counts_from(runner)
    patch_artifact = as_mapping(runner.get("patch_artifact"))
    patch_path_value = first_string(item.get("patch_path"), runner.get("patch_path"), normalized.get("patch_path"))
    patch_file_exists = False
    if patch_path_value:
        patch_path = Path(patch_path_value)
        if not patch_path.is_absolute():
            patch_path = repo_root / patch_path
        patch_file_exists = patch_path.exists()
    patch_written = patch_artifact.get("written") is True or patch_file_exists
    raw_response_artifact = first_string(
        item.get("raw_response_artifact"),
        metadata.get("raw_response_artifact"),
        runner.get("raw_response_artifact"),
    )
    workspace_value = first_string(item.get("workspace"), runner.get("workspace"))
    provider = provider_redacted_artifact_features(raw_response_artifact, repo_root=repo_root)
    workspace = workspace_status_features(workspace_value, repo_root=repo_root)

    features: dict[str, Any] = {
        "cell_present": True,
        "acut_id": acut_id,
        "task_id": task_id,
        "run_id": item.get("run_id"),
        "status": item.get("status") or normalized.get("status") or runner.get("status"),
        "runner_status": runner.get("status"),
        "error": first_string(normalized.get("error"), runner.get("error")),
        "failure_owner": first_string(metadata.get("failure_owner")),
        "failure_class": failure_class,
        "reason_counts": reason_counts,
        "unsafe_flag": bool(as_mapping(as_mapping(runner.get("details")).get("unsafe_content")).get("unsafe"))
        if as_mapping(runner.get("details")).get("unsafe_content") is not None
        else None,
        "resolved_env_var_name_count": len(
            as_mapping(as_mapping(runner.get("details")).get("unsafe_content")).get("resolved_env_var_names", [])
            if isinstance(
                as_mapping(as_mapping(runner.get("details")).get("unsafe_content")).get("resolved_env_var_names"),
                list,
            )
            else []
        ),
        "model_call_made": metadata.get("model_call_made")
        if metadata.get("model_call_made") in (True, False)
        else runner.get("model_call_made"),
        "contract_markers": markers,
        "all_contract_markers_match_structured_v1": bool(markers)
        and all(marker["value"] == STRUCTURED_CONTRACT for marker in markers),
        "patch_path": safe_path(patch_path_value, repo_root=repo_root),
        "patch_path_declared": bool(patch_path_value),
        "patch_file_exists": patch_file_exists,
        "patch_written": patch_written,
        "patch_artifact_fields_present": bool(patch_artifact),
        "patch_artifact_policy": patch_artifact.get("policy"),
        "patch_artifact_unsafe_content_detected": patch_artifact.get("unsafe_content_detected"),
        "redacted_provider_artifact": provider,
        "workspace": workspace,
    }
    features["enough_redacted_evidence"] = enough_redacted_evidence(
        failure_class=failure_class,
        reason_counts=reason_counts,
        provider=provider,
        markers=markers,
    )
    classification, detail = classify_cell(features)
    features["classification"] = classification
    features["classification_detail"] = detail
    return features


def build_triage(
    *,
    batch: Mapping[str, Any],
    batch_path: Path | None,
    repo_root: Path,
    acuts: Sequence[str],
    tasks: Sequence[str],
) -> dict[str, Any]:
    results = batch.get("results")
    if not isinstance(results, list):
        raise ToolError("batch JSON must contain a results array")

    by_cell: dict[tuple[str, str], Mapping[str, Any]] = {}
    duplicates: list[dict[str, str]] = []
    wanted = {(acut_id, task_id) for acut_id in acuts for task_id in tasks}
    for item in results:
        if not isinstance(item, Mapping):
            continue
        key = (str(item.get("acut_id")), str(item.get("task_id")))
        if key not in wanted:
            continue
        if key in by_cell:
            duplicates.append({"acut_id": key[0], "task_id": key[1]})
            continue
        by_cell[key] = item

    cells = [
        cell_features(item=by_cell.get((acut_id, task_id)), acut_id=acut_id, task_id=task_id, repo_root=repo_root)
        for task_id in tasks
        for acut_id in acuts
    ]
    classification_counts: dict[str, int] = {}
    enough_count = 0
    for cell in cells:
        classification = str(cell["classification"])
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        if cell.get("enough_redacted_evidence") is True:
            enough_count += 1

    payload: dict[str, Any] = {
        "tool": TOOL,
        "schema_version": "unsafe-generated-text-triage.v1",
        "generated_at": iso_now(),
        "model_or_api_budget_spent": False,
        "inputs": {
            "batch": safe_path(str(batch_path), repo_root=repo_root) if batch_path is not None else None,
            "acuts": list(acuts),
            "tasks": list(tasks),
            "redacted_artifacts_only": True,
        },
        "fixed_denominator": {
            "total": len(acuts) * len(tasks),
            "present_cell_count": sum(1 for cell in cells if cell.get("cell_present") is True),
            "missing_cell_count": sum(1 for cell in cells if cell.get("cell_present") is not True),
            "duplicate_target_rows": duplicates,
        },
        "summary": {
            "classification_counts": dict(sorted(classification_counts.items())),
            "enough_redacted_evidence_count": enough_count,
            "reason_counts_total": total_reason_counts(cells),
            "patch_written_count": sum(1 for cell in cells if cell.get("patch_written") is True),
            "workspace_mutation_count": sum(
                1 for cell in cells if as_mapping(cell.get("workspace")).get("workspace_mutation_happened") is True
            ),
        },
        "cells": cells,
        "claim_boundaries": [
            "No task-solving improvement claim.",
            "No capability uplift claim.",
            "No G-score predictivity claim.",
            "No ranking reversal claim.",
        ],
    }
    attach_output_leakage_guard(payload)
    return payload


def total_reason_counts(cells: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for cell in cells:
        for reason, count in normalize_reason_counts(cell.get("reason_counts")).items():
            totals[reason] = totals.get(reason, 0) + count
    return dict(sorted(totals.items()))


def output_leakage_guard(payload: Mapping[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, sort_keys=True)
    findings = unsafe_text_findings(text)
    return {
        "contains_raw_unsafe_text": bool(findings["unsafe"]),
        "reason_counts": findings["reason_counts"],
    }


def attach_output_leakage_guard(payload: dict[str, Any]) -> None:
    payload["output_leakage_guard"] = output_leakage_guard(payload)
    final_guard = output_leakage_guard(payload)
    payload["output_leakage_guard"] = final_guard
    if final_guard["contains_raw_unsafe_text"]:
        raise ToolError("triage output would contain raw unsafe text", reason_counts=final_guard["reason_counts"])


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = Path(args.repo_root).resolve()
        batch_path = Path(args.batch)
        if not batch_path.is_absolute():
            batch_path = repo_root / batch_path
        batch = read_json(batch_path)
        payload = build_triage(
            batch=batch,
            batch_path=batch_path,
            repo_root=repo_root,
            acuts=args.acuts,
            tasks=args.tasks,
        )
        emit_json(payload, Path(args.output))
        return 0
    except ToolError as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
