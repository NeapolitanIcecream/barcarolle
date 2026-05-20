#!/usr/bin/env python3
"""No-spend M2 unsafe patch-artifact repair evidence.

This report distinguishes source-derived full URLs in generated patch artifacts
from true model-generated unsafe replacements for anchored-search-replace-json-v3.
It does not call a model or run task verifiers.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from _llm_budget import FULL_URL_RE, llm_safe_subprocess_env, redact_sensitive_text, unsafe_text_findings
from run_task import collect_patch, unsafe_patch_artifact_attribution, write_safe_patch

import codex_nfl_experiment_runner as batch
import openclaw_direct_runner as direct


TOOL = "m2_unsafe_artifact_repair"
CONTRACT = "anchored-search-replace-json-v3"
DEFAULT_RUN_PREFIX = "m2_unsafe_artifact_repair_20260510"
DEFAULT_PRIOR_LIVE_SMOKE = "experiments/core_narrative/results/m2_anchored_occurrence_repair_live_smoke_20260510.json"

SOURCE_OVERBREADTH = "artifact_policy_source_derived_overbreadth"
TRUE_POSITIVE = "safety_policy_true_positive"
PLACEHOLDER_REJECTED = "redaction_placeholder_persistence_rejected"
AMBIGUOUS = "provider_or_artifact_ambiguous"
PATCH_READY = "patch_ready"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-live-smoke", default=DEFAULT_PRIOR_LIVE_SMOKE)
    parser.add_argument("--live-smoke-batch", help="Optional post-repair bounded live-smoke batch JSON.")
    parser.add_argument("--live-smoke-blocker", help="Optional post-repair live-smoke blocker JSON.")
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument("--raw-root", default=str(batch.RAW_ROOT))
    parser.add_argument("--workspace-root", default=str(batch.WORKSPACES_ROOT))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(list(argv))


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("JSON root must be an object", path=str(path))
    return data


def count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def remove_generated_path(path: Path, run_prefix: str, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise ToolError("generated path already exists; pass --force to replace", path=str(path))
    if not path.name.startswith(run_prefix):
        raise ToolError("refusing to remove path outside run prefix", path=str(path), run_prefix=run_prefix)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def run_capture(command: Sequence[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def init_workspace(root: Path, run_prefix: str, fixture: Mapping[str, Any], force: bool) -> Path:
    workspace = root / f"{run_prefix}__fixture__{fixture['fixture_id']}"
    remove_generated_path(workspace, run_prefix, force)
    workspace.mkdir(parents=True, exist_ok=True)
    for relative, text in (fixture.get("files") or {}).items():
        path = workspace / str(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding="utf-8")
    run_capture(["git", "init", "-q"], cwd=workspace)
    run_capture(["git", "add", "."], cwd=workspace)
    commit = run_capture(
        ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test", "commit", "-qm", "init"],
        cwd=workspace,
    )
    if commit.returncode != 0:
        raise ToolError("fixture workspace commit failed", fixture_id=fixture.get("fixture_id"), stderr=commit.stderr)
    return workspace


def fixture_definitions() -> list[dict[str, Any]]:
    source_url = "https://github.com/pallets/click/issues/3121"
    redacted_old = (
        "    # Lazily resolve default=True to flag_value.\n"
        "    # <redacted:url>\n"
        "    if value is True and self.is_flag:\n"
        "        value = self.flag_value\n"
    )
    return [
        {
            "fixture_id": "redacted_source_old_safe_replacement_source_url_artifact",
            "intent": "redacted source old text may match raw source once, but source-derived raw URL patch lines are attributed",
            "files": {
                "src/click/core.py": (
                    "def get_default():\n"
                    "    # Lazily resolve default=True to flag_value.\n"
                    f"    # {source_url}\n"
                    "    if value is True and self.is_flag:\n"
                    "        value = self.flag_value\n"
                    "    return value\n"
                )
            },
            "context_paths": ["src/click/core.py"],
            "model_text": json.dumps(
                {
                    "edits": [
                        {
                            "path": "src/click/core.py",
                            "old": redacted_old,
                            "new": "    if value is True and self.is_flag:\n        value = self.flag_value\n",
                        }
                    ]
                }
            ),
            "expected_classification": SOURCE_OVERBREADTH,
        },
        {
            "fixture_id": "model_generated_raw_url_replacement_true_positive",
            "intent": "model-generated raw URL replacement remains a true unsafe generated-text hit",
            "files": {"src/click/core.py": "VALUE = 1\n"},
            "context_paths": ["src/click/core.py"],
            "model_text": json.dumps(
                {
                    "edits": [
                        {
                            "path": "src/click/core.py",
                            "old": "VALUE = 1\n",
                            "new": 'VALUE = "https://generated.example.invalid/path"\n',
                        }
                    ]
                }
            ),
            "expected_classification": TRUE_POSITIVE,
        },
        {
            "fixture_id": "redaction_placeholder_persistence_rejection",
            "intent": "redaction placeholders must not persist into replacement text",
            "files": {"src/click/core.py": "VALUE = 1\n"},
            "context_paths": ["src/click/core.py"],
            "model_text": json.dumps(
                {
                    "edits": [
                        {
                            "path": "src/click/core.py",
                            "old": "VALUE = 1\n",
                            "new": 'VALUE = "<redacted:url>"\n',
                        }
                    ]
                }
            ),
            "expected_classification": PLACEHOLDER_REJECTED,
        },
        {
            "fixture_id": "missing_raw_artifact_ambiguity",
            "intent": "missing provider artifact remains ambiguous rather than treated as generated unsafe text",
            "files": {"src/click/core.py": "VALUE = 1\n"},
            "context_paths": ["src/click/core.py"],
            "model_text": None,
            "omit_raw_response_artifact": True,
            "expected_classification": AMBIGUOUS,
        },
    ]


def write_fixture_artifacts(
    artifact_dir: Path,
    run_prefix: str,
    fixture: Mapping[str, Any],
    *,
    force: bool,
) -> dict[str, Any]:
    remove_generated_path(artifact_dir, run_prefix, force)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    prompt_snapshot = artifact_dir / "prompt_snapshot.json"
    write_json(
        prompt_snapshot,
        {
            "tool": TOOL,
            "output_contract": CONTRACT,
            "context_files": [{"path": path} for path in fixture.get("context_paths", [])],
            "fixture_id": fixture.get("fixture_id"),
            "content_recorded": False,
            "full_urls_redacted": True,
        },
    )
    if fixture.get("omit_raw_response_artifact") is True:
        return {"prompt_snapshot": str(prompt_snapshot), "raw_response_artifact": None}
    model_text = str(fixture.get("model_text") or "")
    raw_response = artifact_dir / "provider_response.redacted.json"
    write_json(
        raw_response,
        {
            "choices": [{"message": {"content": redact_sensitive_text(model_text)}}],
            "usage": {"cost": 0},
        },
    )
    return {"prompt_snapshot": str(prompt_snapshot), "raw_response_artifact": str(raw_response)}


def provider_artifact_features(path_value: str | None) -> dict[str, Any]:
    if not path_value:
        return {
            "path": None,
            "exists": False,
            "json_valid": None,
            "raw_url_like_count": 0,
            "redacted_url_marker_count": 0,
            "content_sha256": None,
            "content_recorded": False,
        }
    path = Path(path_value)
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "json_valid": None,
            "raw_url_like_count": 0,
            "redacted_url_marker_count": 0,
            "content_sha256": None,
            "content_recorded": False,
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    content = ""
    json_valid = False
    try:
        data = json.loads(text)
        json_valid = isinstance(data, dict)
        choices = data.get("choices") if isinstance(data, dict) else None
        if isinstance(choices, list) and choices and isinstance(choices[0], Mapping):
            message = choices[0].get("message")
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                content = str(message["content"])
    except json.JSONDecodeError:
        json_valid = False
    return {
        "path": str(path),
        "exists": True,
        "json_valid": json_valid,
        "raw_url_like_count": len(FULL_URL_RE.findall(text)),
        "redacted_url_marker_count": text.count("<redacted:url>"),
        "content_sha256": sha256_text(content) if content else None,
        "content_char_count": len(content) if content else None,
        "content_recorded": False,
    }


def classify_unsafe_patch_artifact(patch_artifact: Mapping[str, Any]) -> str:
    attribution = patch_artifact.get("unsafe_content_attribution")
    if isinstance(attribution, Mapping):
        if attribution.get("all_unsafe_reasons_source_derived") is True:
            return SOURCE_OVERBREADTH
        if int(attribution.get("model_generated_full_url_count") or 0) > 0:
            return TRUE_POSITIVE
    return AMBIGUOUS


def replay_fixture(
    fixture: Mapping[str, Any],
    *,
    args: argparse.Namespace,
    workspace_root: Path,
    raw_root: Path,
) -> dict[str, Any]:
    artifact_dir = raw_root / f"{args.run_prefix}__fixture__{fixture['fixture_id']}"
    workspace = init_workspace(workspace_root, args.run_prefix, fixture, bool(args.force))
    artifacts = write_fixture_artifacts(artifact_dir, args.run_prefix, fixture, force=bool(args.force))
    raw_response = artifacts.get("raw_response_artifact") if isinstance(artifacts.get("raw_response_artifact"), str) else None
    base = {
        "fixture_id": fixture.get("fixture_id"),
        "intent": fixture.get("intent"),
        "contract": CONTRACT,
        "workspace": str(workspace),
        "artifact_dir": str(artifact_dir),
        "context_paths": list(fixture.get("context_paths", [])),
        "prompt_snapshot": artifacts.get("prompt_snapshot"),
        "raw_response_artifact": raw_response,
        "provider_artifact": provider_artifact_features(raw_response),
        "model_call_made": False,
        "model_spend_usd": 0.0,
        "expected_classification": fixture.get("expected_classification"),
    }
    model_text = fixture.get("model_text")
    if not isinstance(model_text, str):
        return {
            **base,
            "status": "missing_replay_input",
            "classification": AMBIGUOUS,
            "failure_owner": "infrastructure",
            "failure_class": "missing_raw_response_artifact",
            "patch_ready": False,
            "patch": None,
            "patch_artifact": None,
            "details": {"content_recorded": False},
        }

    try:
        patch_result = direct.apply_model_response(
            workspace,
            model_text,
            allowed_paths=list(fixture.get("context_paths", [])),
            output_contract=CONTRACT,
        )
        safe_env, _ = llm_safe_subprocess_env({})
        patch_path = artifact_dir / "submission.patch"
        patch_artifact = write_safe_patch(workspace, patch_path, safe_env)
        if patch_artifact.get("unsafe_content_detected") is True:
            classification = classify_unsafe_patch_artifact(patch_artifact)
            return {
                **base,
                "status": "invalid_submission",
                "classification": classification,
                "failure_owner": "model_output" if classification == TRUE_POSITIVE else "artifact_policy",
                "failure_class": "unsafe_generated_text",
                "patch_ready": False,
                "patch": patch_result,
                "patch_artifact": patch_artifact,
                "details": {
                    "failure_class": "unsafe_generated_text",
                    "unsafe_content": patch_artifact.get("unsafe_content"),
                    "unsafe_content_attribution": patch_artifact.get("unsafe_content_attribution"),
                    "patch_result_before_patch_artifact": patch_result,
                    "content_recorded": False,
                },
            }
        return {
            **base,
            "status": "patch_ready",
            "classification": PATCH_READY,
            "failure_owner": "candidate_patch",
            "failure_class": None,
            "patch_ready": True,
            "patch": patch_result,
            "patch_artifact": patch_artifact,
            "details": {"content_recorded": False},
        }
    except ToolError as exc:
        failure_class = exc.details.get("failure_class")
        if failure_class == "unsafe_generated_text":
            classification = TRUE_POSITIVE
        elif failure_class == "search_replace_redacted_source_mismatch":
            classification = PLACEHOLDER_REJECTED
        else:
            classification = AMBIGUOUS
        return {
            **base,
            "status": "invalid_submission",
            "classification": classification,
            "failure_owner": "model_output",
            "failure_class": failure_class if isinstance(failure_class, str) else "anchored_contract_error",
            "patch_ready": False,
            "patch": None,
            "patch_artifact": None,
            "error": str(exc),
            "details": {**exc.details, "content_recorded": bool(exc.details.get("content_recorded"))},
        }


def target_live_result(batch_payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    results = batch_payload.get("results")
    if not isinstance(results, list):
        return None
    for item in results:
        if not isinstance(item, Mapping):
            continue
        if item.get("acut_id") == "cheap-generic-swe" and item.get("task_id") == "click__rwork__006":
            return item
    return None


def inspect_prior_live_smoke(path_value: str | None) -> dict[str, Any]:
    if not path_value:
        return {"status": "not_provided"}
    path = Path(path_value)
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    payload = read_json(path)
    item = target_live_result(payload)
    if item is None:
        return {"status": "target_cell_missing", "path": str(path)}
    runner = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
    details = runner.get("details") if isinstance(runner.get("details"), Mapping) else {}
    patch_result = (
        details.get("patch_result_before_patch_artifact")
        if isinstance(details.get("patch_result_before_patch_artifact"), Mapping)
        else {}
    )
    edit_diagnostics = (
        patch_result.get("edit_diagnostics")
        if isinstance(patch_result.get("edit_diagnostics"), list)
        else []
    )
    redacted_source_matches = [
        diagnostic
        for diagnostic in edit_diagnostics
        if isinstance(diagnostic, Mapping)
        and isinstance(diagnostic.get("diagnostic"), Mapping)
        and diagnostic["diagnostic"].get("code") == "redacted_source_text_matched_raw_source"
    ]
    provider_path = item.get("raw_response_artifact") or runner.get("raw_response_artifact")
    prompt_path = item.get("prompt_snapshot") or runner.get("prompt_snapshot")
    prompt_features: dict[str, Any] = {"path": prompt_path, "exists": False}
    if isinstance(prompt_path, str) and Path(prompt_path).exists():
        prompt = read_json(prompt_path)
        prompt_features = {
            "path": prompt_path,
            "exists": True,
            "prompt_sha256": prompt.get("prompt_sha256"),
            "prompt_char_count": prompt.get("prompt_char_count"),
            "full_urls_redacted": prompt.get("full_urls_redacted"),
            "output_contract": prompt.get("output_contract"),
            "context_file_count": len(prompt.get("context_files", [])) if isinstance(prompt.get("context_files"), list) else None,
            "content_recorded": False,
        }
    workspace_value = item.get("runner_workspace") or item.get("workspace") or runner.get("workspace")
    attribution: dict[str, Any] | None = None
    if isinstance(workspace_value, str) and Path(workspace_value).exists():
        safe_env, _ = llm_safe_subprocess_env({})
        patch_text = collect_patch(Path(workspace_value), safe_env)
        findings = unsafe_text_findings(patch_text, safe_env)
        attribution = unsafe_patch_artifact_attribution(patch_text, findings)
    unsafe_content = details.get("unsafe_content") if isinstance(details.get("unsafe_content"), Mapping) else {}
    return {
        "status": "inspected",
        "path": str(path),
        "acut_id": item.get("acut_id"),
        "task_id": item.get("task_id"),
        "run_status": item.get("status"),
        "runner_status": runner.get("status"),
        "failure_class": details.get("failure_class"),
        "failure_owner": item.get("failure_owner"),
        "model_call_made": runner.get("model_call_made"),
        "unsafe_patch_artifact_reason_counts": unsafe_content.get("reason_counts"),
        "unsafe_patch_artifact_attribution": attribution,
        "redacted_source_match_count": len(redacted_source_matches),
        "redacted_source_replacement_marker_count": sum(
            1
            for diagnostic in redacted_source_matches
            if isinstance(diagnostic.get("diagnostic"), Mapping)
            and diagnostic["diagnostic"].get("replacement_contains_redacted_url_marker") is True
        ),
        "provider_artifact": provider_artifact_features(str(provider_path) if isinstance(provider_path, str) else None),
        "prompt_snapshot": prompt_features,
        "content_recorded": False,
    }


def live_smoke_status(args: argparse.Namespace) -> dict[str, Any]:
    if args.live_smoke_batch and args.live_smoke_blocker:
        raise ToolError("choose only one of --live-smoke-batch or --live-smoke-blocker")
    if args.live_smoke_blocker:
        blocker = read_json(args.live_smoke_blocker)
        return {
            "status": "blocked",
            "path": args.live_smoke_blocker,
            "model_call_made": bool(blocker.get("model_call_made")),
            "blockers": blocker.get("blockers") if isinstance(blocker.get("blockers"), list) else [],
            "details": blocker,
        }
    if args.live_smoke_batch:
        payload = read_json(args.live_smoke_batch)
        results = [item for item in payload.get("results", []) if isinstance(item, Mapping)]
        failure_rows: list[dict[str, Any]] = []
        unsafe_diagnostics: list[dict[str, Any]] = []
        for item in results:
            runner = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
            details = runner.get("details") if isinstance(runner.get("details"), Mapping) else {}
            normalized = item.get("normalized") if isinstance(item.get("normalized"), Mapping) else {}
            metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), Mapping) else {}
            failure_class = details.get("failure_class") or metadata.get("failure_class")
            failure_owner = item.get("failure_owner") or metadata.get("failure_owner")
            failure_rows.append({"failure_class": failure_class, "failure_owner": failure_owner})
            patch_artifact = details.get("patch_artifact") if isinstance(details.get("patch_artifact"), Mapping) else {}
            unsafe_content = details.get("unsafe_content") if isinstance(details.get("unsafe_content"), Mapping) else {}
            attribution = (
                details.get("unsafe_content_attribution")
                if isinstance(details.get("unsafe_content_attribution"), Mapping)
                else patch_artifact.get("unsafe_content_attribution")
                if isinstance(patch_artifact.get("unsafe_content_attribution"), Mapping)
                else None
            )
            patch_result = (
                details.get("patch_result_before_patch_artifact")
                if isinstance(details.get("patch_result_before_patch_artifact"), Mapping)
                else {}
            )
            edit_diagnostics = (
                patch_result.get("edit_diagnostics")
                if isinstance(patch_result.get("edit_diagnostics"), list)
                else []
            )
            unsafe_diagnostics.append(
                {
                    "acut_id": item.get("acut_id"),
                    "task_id": item.get("task_id"),
                    "status": item.get("status"),
                    "failure_class": failure_class,
                    "failure_owner": failure_owner,
                    "model_call_made": runner.get("model_call_made"),
                    "unsafe_reason_counts": unsafe_content.get("reason_counts"),
                    "unsafe_content_attribution": attribution,
                    "patch_artifact_written": patch_artifact.get("written"),
                    "redacted_preview_written": (
                        patch_artifact.get("redacted_preview", {}).get("written")
                        if isinstance(patch_artifact.get("redacted_preview"), Mapping)
                        else None
                    ),
                    "redacted_source_match_count": sum(
                        1
                        for diagnostic in edit_diagnostics
                        if isinstance(diagnostic, Mapping)
                        and isinstance(diagnostic.get("diagnostic"), Mapping)
                        and diagnostic["diagnostic"].get("code") == "redacted_source_text_matched_raw_source"
                    ),
                    "content_recorded": False,
                }
            )
        return {
            "status": "completed",
            "path": args.live_smoke_batch,
            "model_call_made": any(
                isinstance(item.get("runner_result"), Mapping)
                and item["runner_result"].get("model_call_made") is True
                for item in results
            ),
            "total": len(results),
            "status_counts": count_by(results, "status"),
            "failure_class_counts": count_by(failure_rows, "failure_class"),
            "failure_owner_counts": count_by(failure_rows, "failure_owner"),
            "unsafe_patch_artifact_diagnostics": unsafe_diagnostics,
            "submission_contract": payload.get("submission_contract"),
        }
    return {
        "status": "not_run",
        "model_call_made": False,
        "blockers": ["post_repair_live_smoke_not_attempted"],
    }


def aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "fixed_denominator": len(rows),
        "status_counts": count_by(rows, "status"),
        "classification_counts": count_by(rows, "classification"),
        "failure_class_counts": count_by(rows, "failure_class"),
        "failure_owner_counts": count_by(rows, "failure_owner"),
        "patch_ready_count": sum(1 for row in rows if row.get("patch_ready") is True),
        "model_call_count": sum(1 for row in rows if row.get("model_call_made") is True),
    }


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
        raise ToolError("repair report output would contain raw unsafe text", reason_counts=final_guard["reason_counts"])


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    workspace_root = Path(args.workspace_root)
    raw_root = Path(args.raw_root)
    rows = [
        replay_fixture(fixture, args=args, workspace_root=workspace_root, raw_root=raw_root)
        for fixture in fixture_definitions()
    ]
    prior_live = inspect_prior_live_smoke(args.prior_live_smoke)
    live_smoke = live_smoke_status(args)
    payload: dict[str, Any] = {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "prior_live_smoke": args.prior_live_smoke,
            "live_smoke_batch": args.live_smoke_batch,
            "live_smoke_blocker": args.live_smoke_blocker,
            "run_prefix": args.run_prefix,
            "raw_root": args.raw_root,
            "workspace_root": args.workspace_root,
            "force": bool(args.force),
            "output": args.output,
            "report": args.report,
        },
        "scope": {
            "contract": CONTRACT,
            "fixture_fixed_denominator": len(rows),
            "repair_focus": "unsafe_patch_artifact_source_attribution",
            "denominators_are_separate": True,
        },
        "method": {
            "fixture_model_calls": "none",
            "fixture_model_spend_usd": 0.0,
            "verifier_execution": "not_run",
            "runner_contract_schema": direct.output_contract_schema(CONTRACT),
            "diagnostics_policy": "reason counts plus source/generated role counts and hashes only; raw unsafe text not recorded",
            "claim_boundary": "scoreability/artifact-policy attribution only",
        },
        "prior_live_smoke_inspection": prior_live,
        "fixture_summary": aggregate(rows),
        "matrix": rows,
        "post_repair_live_smoke": live_smoke,
        "cost_model_call_flags": {
            "fixtures": {"model_call_made": False, "model_spend_usd": 0.0, "live_api_calls": False},
            "post_repair_live_smoke": {
                "model_call_made": bool(live_smoke.get("model_call_made")),
                "status": live_smoke.get("status"),
            },
        },
        "claim_status": "unsafe_patch_artifact_repair_not_m2_pass",
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
    attach_output_leakage_guard(payload)
    return payload


def write_report(payload: Mapping[str, Any], path: str) -> None:
    scope = payload.get("scope") if isinstance(payload.get("scope"), Mapping) else {}
    summary = payload.get("fixture_summary") if isinstance(payload.get("fixture_summary"), Mapping) else {}
    prior = payload.get("prior_live_smoke_inspection") if isinstance(payload.get("prior_live_smoke_inspection"), Mapping) else {}
    live = payload.get("post_repair_live_smoke") if isinstance(payload.get("post_repair_live_smoke"), Mapping) else {}
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
        "# M2 Unsafe Patch-Artifact Repair",
        "",
        f"Date: {report_date}",
        "",
        "## Scope",
        "",
        f"- Contract: `{scope.get('contract')}`.",
        f"- Repair focus: `{scope.get('repair_focus')}`.",
        "- Fixture replay made no model calls and ran no verifier.",
        "",
        "## Prior Live Artifact Inspection",
        "",
        f"- Status: `{prior.get('status')}`.",
        f"- Failure class: `{prior.get('failure_class')}`.",
        f"- Unsafe reason counts: `{prior.get('unsafe_patch_artifact_reason_counts')}`.",
        f"- Patch artifact attribution: `{prior.get('unsafe_patch_artifact_attribution')}`.",
        f"- Redacted source match count: `{prior.get('redacted_source_match_count')}`.",
        "",
        "## Fixture Matrix",
        "",
        "| Fixture | Classification | Status | Owner | Class | Patch-ready | Intent |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload.get("matrix", []):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| `{row.get('fixture_id')}` | `{row.get('classification')}` | `{row.get('status')}` | "
            f"`{row.get('failure_owner')}` | `{row.get('failure_class')}` | `{row.get('patch_ready')}` | "
            f"{row.get('intent')} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Classification counts: `{summary.get('classification_counts')}`.",
            f"- Failure classes: `{summary.get('failure_class_counts')}`.",
            f"- Patch-ready count: `{summary.get('patch_ready_count')}`.",
            "",
            "## Post-Repair Live Smoke",
            "",
            f"- Status: `{live.get('status')}`.",
            f"- Model call made: `{live.get('model_call_made')}`.",
            f"- Failure classes: `{live.get('failure_class_counts')}`.",
            f"- Blockers: `{live.get('blockers')}`.",
            f"- Unsafe diagnostics: `{live.get('unsafe_patch_artifact_diagnostics')}`.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_unsafe_artifact_repair.py \\",
            f"  --prior-live-smoke {payload.get('inputs', {}).get('prior_live_smoke')} \\",
            f"  --run-prefix {payload.get('inputs', {}).get('run_prefix')} \\",
            f"  --raw-root {payload.get('inputs', {}).get('raw_root')} \\",
            f"  --workspace-root {payload.get('inputs', {}).get('workspace_root')} \\",
            *(
                [f"  --live-smoke-batch {payload.get('inputs', {}).get('live_smoke_batch')} \\"]
                if payload.get("inputs", {}).get("live_smoke_batch")
                else []
            ),
            *(
                [f"  --live-smoke-blocker {payload.get('inputs', {}).get('live_smoke_blocker')} \\"]
                if payload.get("inputs", {}).get("live_smoke_blocker")
                else []
            ),
            "  --force \\",
            f"  --output {payload.get('inputs', {}).get('output')} \\",
            f"  --report {payload.get('inputs', {}).get('report')}",
            "```",
            "",
            "## Claim Boundaries",
            "",
            "This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports anchored-contract unsafe artifact attribution and post-repair live-smoke availability.",
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
