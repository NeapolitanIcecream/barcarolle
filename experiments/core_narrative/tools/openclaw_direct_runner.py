#!/usr/bin/env python3
"""OpenClaw-native direct ACUT runner for scoreable patch artifacts.

This runner intentionally avoids the old Codex work/review-loop plumbing.  It
keeps the core experiment objects (task manifests, ACUT manifests, verifier,
normalized result shape, and cost ledger) but uses a small direct HTTP adapter
whose model output contract is easy to validate:

    {"edits": [{"path": "relative/file.py", "old": "...", "new": "..."}]}

The search/replace bundle keeps model output small while still producing a
normal git patch for the existing verifier/scorer path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, git, iso_now, load_manifest, require_keys, write_json
from _llm_budget import (
    DEFAULT_LEDGER_PATH,
    append_ledger_record,
    gate_payload,
    ledger_cumulative_decimal,
    llm_safe_subprocess_env,
    money_json,
    parse_non_negative_int,
    parse_usd,
    read_ledger_summary,
    redact_sensitive_text,
    unsafe_text_findings,
)
from barcarolle_patch_command import (
    DEFAULT_MAX_RESPONSE_BYTES,
    STRUCTURED_FILES_OUTPUT_CONTRACT,
    apply_patch_response,
    diff_paths,
    enforce_output_contract,
    parse_patch_response,
    reject_unsafe_generated_text,
    resolve_live_endpoint,
    strip_code_fence,
    validate_patch_path,
)
from run_task import write_safe_patch


TOOL = "openclaw_direct_runner"
RUNNER_ID = "openclaw-direct-search-replace-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HTTP_TIMEOUT_SECONDS = 300
DEFAULT_MAX_FILE_CHARS = 80_000
DEFAULT_MAX_CONTEXT_CHARS = 120_000
DEFAULT_MAX_FOCUSED_EXCERPT_CHARS = 8_000
DEFAULT_OUTPUT_CONTRACT = "anchored-search-replace-json-v3"
SUPPORTED_OUTPUT_CONTRACTS = (DEFAULT_OUTPUT_CONTRACT, STRUCTURED_FILES_OUTPUT_CONTRACT)


def output_contract_schema(output_contract: str = DEFAULT_OUTPUT_CONTRACT) -> dict[str, Any]:
    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        return {
            "id": STRUCTURED_FILES_OUTPUT_CONTRACT,
            "primary_top_level_key": "files",
            "requires_single_top_level_key": True,
            "requires_json_object": True,
            "requires_full_file_content": True,
            "rejects_incomplete_content_markers": True,
            "allowed_actions": ["write", "create", "replace", "delete"],
            "path_policy": {
                "paths_must_be_relative": True,
                "paths_must_not_target_reserved_metadata": [".git", ".core_narrative"],
                "paths_must_be_from_declared_context": True,
            },
            "diagnostic_failure_classes": {
                "output_contract_violation": "response did not satisfy the selected structured-files contract",
                "structured_files_invalid": "files entries were malformed or could not be applied as file-level edits",
                "unsafe_generated_text": "response, path, content, or generated patch contained unsafe generated text",
            },
        }
    return {
        "id": DEFAULT_OUTPUT_CONTRACT,
        "primary_top_level_key": "edits",
        "requires_single_top_level_key": True,
        "requires_exact_old_text": True,
        "requires_exact_path_from_context": True,
        "requires_immediate_anchors_for_repeated_old_text": True,
        "anchor_policy": {
            "omit_anchors_when_old_is_unique": True,
            "anchors_are_for_repeated_old_text_only": True,
            "anchors_must_be_immediate_adjacent_source": True,
            "invalid_anchors_reject_the_edit_even_when_old_is_unique": True,
        },
        "diagnostic_failure_classes": {
            "search_replace_anchor_mismatch": "old text was present, but supplied anchors did not isolate exactly one occurrence",
            "search_replace_old_occurrence_mismatch": "old text did not occur exactly once after earlier edits",
        },
        "legacy_parser_fallback_keys": ["unified_diff", "files"],
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Prepared git workspace.")
    parser.add_argument("--task", required=True, help="Full task manifest JSON/YAML path.")
    parser.add_argument("--acut", required=True, help="ACUT manifest JSON/YAML path.")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--patch-path", help="Defaults to ARTIFACT_DIR/submission.patch.")
    parser.add_argument("--output", required=True, help="Structured runner summary JSON path.")
    parser.add_argument("--llm-ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--projected-cost-usd", required=True)
    parser.add_argument("--estimated-cost-usd", help="Local ledger estimate. Defaults to projected cost.")
    parser.add_argument("--actual-cost-usd", help="Actual provider-billed USD cost, if an invoice/API reports it.")
    parser.add_argument(
        "--coordinator-decision-ref",
        help="Structured approval reference for budget-gated non-primary attempts or non-core runs.",
    )
    parser.add_argument("--input-tokens", default=None, help="Override input token count when provider usage is absent.")
    parser.add_argument("--output-tokens", default=None, help="Override output token count when provider usage is absent.")
    parser.add_argument("--context-path", action="append", default=[], help="Workspace-relative source file to include.")
    parser.add_argument("--dry-run", action="store_true", help="Write prompt/config artifacts without a model call.")
    parser.add_argument("--mock-response", help="No-model local response file for regression tests.")
    parser.add_argument("--mock-response-text", help="No-model response text for regression tests.")
    parser.add_argument("--http-timeout-seconds", type=int, default=DEFAULT_HTTP_TIMEOUT_SECONDS)
    parser.add_argument("--max-response-bytes", type=int, default=DEFAULT_MAX_RESPONSE_BYTES)
    parser.add_argument("--max-file-chars", type=int, default=DEFAULT_MAX_FILE_CHARS)
    parser.add_argument("--max-context-chars", type=int, default=DEFAULT_MAX_CONTEXT_CHARS)
    parser.add_argument(
        "--output-contract",
        choices=SUPPORTED_OUTPUT_CONTRACTS,
        default=DEFAULT_OUTPUT_CONTRACT,
        help="Model submission contract to request and validate.",
    )
    parser.add_argument(
        "--include-specialist-context",
        choices=("auto", "always", "never"),
        default="auto",
        help="Include the task-agnostic Click specialist context pack when ACUT policy allows it.",
    )
    return parser.parse_args(list(argv))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mode_from_args(args: argparse.Namespace) -> str:
    selected = [args.dry_run, args.mock_response is not None, args.mock_response_text is not None]
    if sum(bool(item) for item in selected) > 1:
        raise ToolError("choose only one of --dry-run, --mock-response, or --mock-response-text")
    if args.dry_run:
        return "dry_run"
    if args.mock_response is not None or args.mock_response_text is not None:
        return "mock_response"
    return "live"


def ensure_git_workspace(workspace: Path) -> None:
    result = git("rev-parse", "--is-inside-work-tree", cwd=workspace)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ToolError("workspace is not a git work tree", workspace=str(workspace))


def resolve_workspace_path(workspace: Path, path: str, label: str) -> Path:
    workspace = workspace.resolve()
    safe_relative = validate_patch_path(path)
    target = (workspace / safe_relative).resolve()
    try:
        target.relative_to(workspace)
    except ValueError as exc:
        raise ToolError(f"{label} escaped workspace", path=path) from exc
    return target


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n[truncated]\n", True


def safe_task_statement(task_path: Path, task: Mapping[str, Any]) -> tuple[str, str | None, bool]:
    raw = task.get("task_statement_path")
    if not isinstance(raw, str) or not raw:
        return "", None, False
    if raw.startswith("inline:"):
        statement = str(task.get("problem_statement", ""))
        return statement, raw, False
    path = (task_path.parent / raw).resolve()
    if not path.exists():
        return "", str(path), False
    statement = path.read_text(encoding="utf-8")
    return statement, str(path), False


def context_focus_terms(task: Mapping[str, Any], task_statement: str, rel_path: str) -> list[str]:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    combined = "\n".join(
        str(item)
        for item in [
            task.get("task_id"),
            task.get("task_family"),
            task_statement,
            metadata.get("visible_context_guidance"),
            metadata.get("risk_notes"),
            *(metadata.get("expected_touched_area") if isinstance(metadata.get("expected_touched_area"), list) else []),
        ]
        if item
    ).lower()
    if "prompt_required" not in combined:
        return []
    if rel_path.endswith("click/core.py"):
        return [
            "class Option(Parameter):",
            "    def consume_value(self, ctx, opts):",
        ]
    if rel_path.endswith("click/parser.py"):
        return [
            "class Option:",
            "class OptionParser:",
        ]
    return []


def focused_source_excerpts(
    text: str,
    *,
    visible_prefix_chars: int,
    focus_terms: Sequence[str],
    max_excerpt_chars: int = DEFAULT_MAX_FOCUSED_EXCERPT_CHARS,
) -> list[dict[str, Any]]:
    excerpts: list[dict[str, Any]] = []
    used_ranges: list[tuple[int, int]] = []
    for term in focus_terms:
        index = text.find(term)
        if index == -1 or index < visible_prefix_chars:
            continue
        start = max(0, index - 600)
        end = min(len(text), index + max_excerpt_chars)
        if any(start < used_end and end > used_start for used_start, used_end in used_ranges):
            continue
        used_ranges.append((start, end))
        excerpts.append(
            {
                "trigger": term,
                "start_char": start,
                "end_char": end,
                "char_count": end - start,
                "content": text[start:end],
            }
        )
    return excerpts


def effective_max_file_chars(
    *,
    requested_max_file_chars: int,
    max_context_chars: int,
    context_path_count: int,
    task: Mapping[str, Any],
    task_statement: str,
) -> int:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    expected = " ".join(str(item) for item in metadata.get("expected_touched_area", []) if item)
    prompt_required_task = "prompt_required" in f"{task_statement} {expected}".lower()
    if not prompt_required_task or context_path_count < 4:
        return requested_max_file_chars
    compact_budget = max(20_000, (max_context_chars - 20_000) // context_path_count)
    return min(requested_max_file_chars, compact_budget)


def context_file_payload(
    workspace: Path,
    rel_path: str,
    max_file_chars: int,
    *,
    focus_terms: Sequence[str] = (),
    allow_missing: bool = False,
) -> dict[str, Any]:
    path = resolve_workspace_path(workspace, rel_path, "--context-path")
    if not path.exists() or not path.is_file():
        if allow_missing and not path.exists():
            return {
                "path": validate_patch_path(rel_path),
                "exists": False,
                "sha256": None,
                "char_count": 0,
                "truncated": False,
                "displayed_char_count": 0,
                "focus_terms": list(focus_terms),
                "focused_excerpts": [],
                "content": "",
            }
        raise ToolError("context path is not a file", path=rel_path)
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    text = redact_sensitive_text(raw_text, os.environ)
    findings = unsafe_text_findings(text, os.environ)
    if findings["unsafe"]:
        raise ToolError(f"context file {rel_path} could not be redacted safely", unsafe_content=findings)
    shown, truncated = truncate_text(text, max_file_chars)
    visible_prefix_chars = min(len(text), max_file_chars)
    excerpts = focused_source_excerpts(
        text,
        visible_prefix_chars=visible_prefix_chars,
        focus_terms=focus_terms,
    ) if truncated else []
    return {
        "path": validate_patch_path(rel_path),
        "exists": True,
        "sha256": sha256_text(raw_text),
        "char_count": len(raw_text),
        "truncated": truncated,
        "displayed_char_count": len(shown),
        "focus_terms": list(focus_terms),
        "focused_excerpts": excerpts,
        "content": shown,
    }


def specialist_context_path(acut: Mapping[str, Any]) -> str | None:
    metadata = acut.get("metadata") if isinstance(acut.get("metadata"), dict) else {}
    specialist = metadata.get("specialist_context") if isinstance(metadata.get("specialist_context"), dict) else {}
    allowed = bool(specialist.get("click_task_agnostic_context_allowed"))
    pack = specialist.get("context_pack") if isinstance(specialist.get("context_pack"), dict) else {}
    path = pack.get("context_prompt_path")
    if allowed and isinstance(path, str) and path:
        return path
    return None


def expects_click_specialist_context(acut: Mapping[str, Any]) -> bool:
    acut_id = str(acut.get("acut_id") or "")
    strategy = acut.get("retrieval_context_strategy") if isinstance(acut.get("retrieval_context_strategy"), dict) else {}
    strategy_id = str(strategy.get("strategy_id") or "")
    metadata = acut.get("metadata") if isinstance(acut.get("metadata"), dict) else {}
    specialist = metadata.get("specialist_context") if isinstance(metadata.get("specialist_context"), dict) else {}
    return (
        bool(specialist.get("click_task_agnostic_context_allowed"))
        or "click-specialist" in acut_id
        or strategy_id == "click-specialist-task-agnostic-v2"
    )


def assert_specialist_context_policy(
    *,
    acut: Mapping[str, Any],
    include_mode: str,
    specialist_path: str | None,
) -> dict[str, Any]:
    expected = expects_click_specialist_context(acut)
    if expected and include_mode == "never":
        raise ToolError(
            "Click-specialist ACUT must include the task-agnostic Click context pack",
            acut_id=acut.get("acut_id"),
            failure_class="specialist_context_not_included",
        )
    if not expected and include_mode == "always":
        raise ToolError(
            "generic ACUT must not include the Click specialist context pack",
            acut_id=acut.get("acut_id"),
            failure_class="specialist_context_forbidden",
        )
    if expected and specialist_path is None:
        raise ToolError(
            "Click-specialist ACUT is missing metadata.specialist_context.context_pack",
            acut_id=acut.get("acut_id"),
            failure_class="specialist_context_missing",
        )
    return {
        "expected": "included" if expected else "excluded",
        "include_mode": include_mode,
        "passed": True,
    }


def resolve_specialist_context_file(path: str, acut_path: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    repo_relative = REPO_ROOT / candidate
    if repo_relative.exists():
        return repo_relative
    return (acut_path.parent / candidate).resolve()


def build_prompt(
    *,
    task: Mapping[str, Any],
    task_statement: str,
    acut: Mapping[str, Any],
    context_files: Sequence[Mapping[str, Any]],
    specialist_context: str | None,
    max_context_chars: int,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> str:
    acut_policy = {
        "acut_id": acut.get("acut_id"),
        "model": acut.get("model"),
        "retrieval_context_strategy": acut.get("retrieval_context_strategy", {}),
        "runtime_budget": acut.get("runtime_budget", {}),
    }
    task_summary = {
        "task_id": task.get("task_id"),
        "repo_slug": task.get("repo_slug"),
        "split": task.get("split"),
        "task_family": task.get("task_family"),
        "allowed_context": task.get("allowed_context", {}),
        "disallowed_context": task.get("disallowed_context", []),
        "expected_touched_area": (task.get("metadata") or {}).get("expected_touched_area")
        if isinstance(task.get("metadata"), dict)
        else None,
    }

    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        contract_lines = [
            "Return only one raw JSON object with this exact contract:",
            '{"files":[{"path":"relative/file.py","action":"write","content":"full file content"}]}',
            "The first non-whitespace character must be { and the last non-whitespace character must be }.",
            "Allowed actions are write, create, replace, and delete. For delete, omit content.",
            "For write, create, and replace, content must be the complete final file content from byte 1 through EOF, not a snippet or diff.",
            "Do not use placeholders like <unchanged>, [truncated], or comments saying the rest is unchanged.",
            "Do not return edits, old/new search strings, unified_diff, patch, diff, raw diff text, markdown fences, prose, or any top-level key other than files.",
            "Any JSON object with edits, unified_diff, patch, diff, or extra top-level keys is invalid.",
            "Do not include http:// or https:// URLs, endpoint values, credentials, bearer tokens, or generated API endpoints in paths or content.",
            "",
            "Pre-submit validation checklist:",
            "- The top-level JSON object has exactly one key: files.",
            "- Each file path exactly matches one of the Valid edit paths below.",
            "- Each non-delete entry includes complete final file content, including unchanged lines before and after the edit.",
            "- No markdown fences, prose, notes, placeholders, diffs, old/new edit bundles, URLs, or endpoint strings are present.",
            "- Keep changes minimal. Prefer source code fixes over test-only changes.",
        ]
    else:
        contract_lines = [
            "Return only one JSON object with this exact contract:",
            '{"edits":[{"path":"relative/file.py","old":"exact existing text","new":"replacement text",'
            '"before":"optional exact text immediately before old","after":"optional exact text immediately after old"}]}',
            "Do not return unified_diff, raw diff text, markdown fences, prose, or any top-level key other than edits.",
            "",
            "Pre-submit validation checklist:",
            "- The top-level JSON object has exactly one key: edits.",
            "- Each edit path exactly matches one of the Valid edit paths below.",
            "- Each old string is copied exactly from the currently shown source.",
            "- Apply edits in order mentally. For each edit, old must identify exactly one occurrence after earlier edits.",
            "- If old occurs exactly once, omit before and after anchors.",
            "- If old occurs more than once, include before and/or after anchors copied exactly from the same file.",
            "- Anchors must be immediate context: before must end exactly where old begins; after must begin exactly where old ends.",
            "Rules:",
            "- Repeated old strings without exact anchors are invalid and will not be applied.",
            "- Non-matching anchors are invalid even when old occurs once.",
            "- Never invent old text from memory or from APIs not shown in the source excerpts.",
            "- Keep edits minimal. Prefer source code fixes over test-only changes.",
        ]

    sections: list[str] = [
        "You are generating a minimal repository patch for one Barcarolle ACUT task.",
        "Use only the public task statement, ACUT policy, and source files included below.",
        "Do not use hidden verifier files, reference patches, future history, credentials, endpoints, or URLs.",
        "",
        *contract_lines,
        "",
        "Task summary:",
        json.dumps(task_summary, indent=2, sort_keys=True),
        "",
        "Public task statement:",
        task_statement or "[missing public statement]",
        "",
        "ACUT policy summary:",
        json.dumps(acut_policy, indent=2, sort_keys=True),
        "",
        "Valid edit paths:",
        json.dumps([item["path"] for item in context_files], indent=2),
    ]
    valid_paths = {str(item["path"]) for item in context_files}
    if any(path.startswith("click/") for path in valid_paths) and not any(path.startswith("src/click/") for path in valid_paths):
        sections.extend(
            [
                "",
                "Historical Click layout guard:",
                "- This prepared workspace predates Click's src/ layout.",
                "- Do not generate src/click/... paths; they are invalid for this task.",
                "- Use only the exact Valid edit paths listed above.",
            ]
        )
    if specialist_context:
        sections.extend(["", "Task-agnostic Click specialist context:", specialist_context])
    for item in context_files:
        if item.get("exists") is False:
            sections.extend(
                [
                    "",
                    f"Declared create-only path: {item['path']}",
                    "This file is not present in the prepared workspace. Use action create only if the task needs this new file.",
                ]
            )
            continue
        sections.extend(
            [
                "",
                f"Source file: {item['path']}",
                f"sha256: {item['sha256']} truncated: {item['truncated']} displayed_chars: {item.get('displayed_char_count')}",
                "```",
                str(item["content"]),
                "```",
            ]
        )
        excerpts = item.get("focused_excerpts") if isinstance(item.get("focused_excerpts"), list) else []
        if excerpts:
            sections.extend(
                [
                    f"Focused exact source excerpts for {item['path']}:",
                    "These excerpts are from the same current file and may be used for exact old strings.",
                ]
            )
            for excerpt in excerpts:
                sections.extend(
                    [
                        f"excerpt trigger: {excerpt.get('trigger')} chars: {excerpt.get('start_char')}..{excerpt.get('end_char')}",
                        "```",
                        str(excerpt.get("content", "")),
                        "```",
                    ]
                )
    prompt = redact_sensitive_text("\n".join(sections), os.environ)
    prompt, _ = truncate_text(prompt, max_context_chars)
    return prompt


def provider_text_and_usage(body: bytes) -> tuple[str, dict[str, Any] | None]:
    raw_text = body.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text, None
    usage = data.get("usage") if isinstance(data, dict) and isinstance(data.get("usage"), dict) else None
    text = extract_text(data)
    return (text if text is not None else raw_text), usage


def extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks = [chunk for item in value if (chunk := extract_text(item))]
        return "\n".join(chunks) if chunks else None
    if not isinstance(value, dict):
        return None

    for key in ("output_text", "text"):
        item = value.get(key)
        if isinstance(item, str):
            return item
    if value.get("type") in {"text", "output_text"} and isinstance(value.get("content"), str):
        return str(value["content"])
    if "content" in value:
        text = extract_text(value["content"])
        if text:
            return text
    choices = value.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            text = extract_text(message)
            if text:
                return text
            text = extract_text(first.get("text"))
            if text:
                return text
    output = value.get("output")
    text = extract_text(output)
    if text:
        return text
    return None


def live_payload(
    acut: Mapping[str, Any],
    prompt: str,
    endpoint_kind: str,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> dict[str, Any]:
    model = acut.get("model")
    if not isinstance(model, str) or not model:
        raise ToolError("ACUT manifest is missing model")
    params = acut.get("model_parameters") if isinstance(acut.get("model_parameters"), dict) else {}
    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        system = (
            "You are a patch-generation engine. Return only raw JSON matching "
            "the requested structured file-level contract. Do not include prose, "
            "markdown fences, URLs, endpoint values, credentials, or placeholders."
        )
    else:
        system = (
            "You are a patch-generation engine. Return only valid JSON matching "
            "the requested anchored search/replace edit contract."
        )
    if endpoint_kind == "responses":
        return {
            "model": model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            **params,
        }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        **params,
    }


def call_live_model(
    *,
    acut: Mapping[str, Any],
    prompt: str,
    timeout_seconds: int,
    max_response_bytes: int,
    raw_response_path: Path,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> tuple[str, dict[str, Any] | None, dict[str, Any]]:
    api_key = os.environ.get("BARCAROLLE_LLM_API_KEY")
    raw_endpoint = os.environ.get("BARCAROLLE_LLM_BASE_URL")
    if not api_key or not raw_endpoint:
        raise ToolError("missing required LLM environment", network_attempted=False)
    endpoint, endpoint_kind = resolve_live_endpoint(raw_endpoint)
    payload = live_payload(acut, prompt, endpoint_kind, output_contract)
    request_body = json.dumps(payload).encode("utf-8")
    profile = {
        "endpoint_kind": endpoint_kind,
        "output_contract": output_contract,
        "output_contract_schema": output_contract_schema(output_contract),
        "response_format_requested": payload.get("response_format") == {"type": "json_object"},
        "request_body_bytes": len(request_body),
        "prompt_sha256": sha256_text(prompt),
        "prompt_char_count": len(prompt),
        "timeout_seconds": timeout_seconds,
        "max_response_bytes": max_response_bytes,
        "model": acut.get("model"),
    }
    request = urllib.request.Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(max_response_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise ToolError("LLM request failed", http_status=exc.code, network_attempted=True, request_profile=profile) from exc
    except Exception as exc:
        raise ToolError("LLM request failed", error_type=type(exc).__name__, network_attempted=True, request_profile=profile) from exc

    if len(body) > max_response_bytes:
        raise ToolError("LLM response exceeded maximum size", network_attempted=True, request_profile=profile)
    raw_response_path.write_text(redact_sensitive_text(body, os.environ), encoding="utf-8")
    text, usage = provider_text_and_usage(body)
    return text, usage, profile


def read_mock_response(args: argparse.Namespace) -> str:
    if args.mock_response_text is not None:
        return args.mock_response_text
    if args.mock_response is None:
        raise ToolError("mock response path is required")
    return Path(args.mock_response).read_text(encoding="utf-8")


def parse_edit_bundle(text: str) -> list[dict[str, str]] | None:
    try:
        data = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    edits = data.get("edits")
    if not isinstance(edits, list):
        return None
    extra_keys = sorted(key for key in data if key != "edits")
    if extra_keys:
        raise ToolError(
            "edit bundle must not include unsupported top-level keys",
            unsupported_top_level_keys=extra_keys,
            failure_class="output_contract_violation",
        )
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(edits):
        if not isinstance(item, dict):
            raise ToolError("edit entry must be an object", index=index)
        path = item.get("path")
        old = item.get("old")
        new = item.get("new")
        if not isinstance(path, str) or not isinstance(old, str) or not isinstance(new, str):
            raise ToolError("edit entry requires string path, old, and new", index=index)
        if not old:
            raise ToolError("edit old string must not be empty", index=index)
        normalized_edit = {"path": validate_patch_path(path), "old": old, "new": new}
        for anchor_key in ("before", "after"):
            if anchor_key not in item:
                continue
            anchor = item.get(anchor_key)
            if not isinstance(anchor, str):
                raise ToolError(
                    "edit anchor must be a string",
                    index=index,
                    anchor=anchor_key,
                    failure_class="search_replace_anchor_invalid",
                )
            if not anchor:
                raise ToolError(
                    "edit anchor string must not be empty",
                    index=index,
                    anchor=anchor_key,
                    failure_class="search_replace_anchor_invalid",
                )
            normalized_edit[anchor_key] = anchor
        normalized.append(normalized_edit)
    if not normalized:
        raise ToolError("edit bundle contains no edits")
    return normalized


def ensure_paths_allowed(paths: Sequence[str], allowed_paths: Sequence[str]) -> list[str]:
    allowed = sorted({validate_patch_path(path) for path in allowed_paths})
    requested = sorted({validate_patch_path(path) for path in paths})
    outside = [path for path in requested if path not in allowed]
    if outside:
        raise ToolError(
            "generated patch path is outside declared context paths",
            paths=outside,
            allowed_context_paths=allowed,
            failure_class="generated_path_outside_context",
        )
    return requested


def ensure_paths_within_context(workspace: Path, paths: Sequence[str], allowed_paths: Sequence[str]) -> list[str]:
    requested = ensure_paths_allowed(paths, allowed_paths)
    allowed = sorted({validate_patch_path(path) for path in allowed_paths})
    for path in requested:
        target = resolve_workspace_path(workspace, path, "generated patch path")
        if not target.exists() or not target.is_file():
            raise ToolError(
                "edit path is not in the prepared workspace",
                path=path,
                failure_class="generated_path_not_in_workspace",
            )
    return requested


def ensure_parsed_patch_paths_within_context(
    workspace: Path,
    parsed: Mapping[str, Any],
    allowed_paths: Sequence[str],
) -> list[str]:
    if parsed.get("kind") != "structured_files":
        return ensure_paths_within_context(workspace, parsed_patch_paths(parsed), allowed_paths)
    files = parsed.get("files")
    if not isinstance(files, list):
        return ensure_paths_within_context(workspace, [], allowed_paths)
    paths: list[str] = []
    for item in files:
        if isinstance(item, Mapping) and isinstance(item.get("path"), str):
            paths.append(str(item["path"]))
    requested = ensure_paths_allowed(paths, allowed_paths)
    for item in files:
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str):
            continue
        path = validate_patch_path(str(item["path"]))
        if item.get("action", "write") == "create":
            continue
        target = resolve_workspace_path(workspace, path, "generated patch path")
        if not target.exists() or not target.is_file():
            raise ToolError(
                "edit path is not in the prepared workspace",
                path=path,
                failure_class="generated_path_not_in_workspace",
            )
    return requested


def parsed_patch_paths(parsed: Mapping[str, Any]) -> list[str]:
    kind = parsed.get("kind")
    if kind == "unified_diff":
        text = parsed.get("text")
        if not isinstance(text, str):
            return []
        return diff_paths(text)
    if kind == "structured_files":
        files = parsed.get("files")
        if not isinstance(files, list):
            return []
        paths: list[str] = []
        for item in files:
            if isinstance(item, Mapping) and isinstance(item.get("path"), str):
                paths.append(str(item["path"]))
        return sorted(set(paths))
    return []


def occurrence_offsets(text: str, old: str) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        index = text.find(old, start)
        if index == -1:
            return offsets
        offsets.append(index)
        start = index + len(old)


def anchored_offsets(text: str, old: str, *, before: str | None, after: str | None) -> tuple[list[int], list[int]]:
    offsets = occurrence_offsets(text, old)
    if before is None and after is None:
        return offsets, offsets
    matches: list[int] = []
    for offset in offsets:
        end = offset + len(old)
        if before is not None and not text[:offset].endswith(before):
            continue
        if after is not None and not text[end:].startswith(after):
            continue
        matches.append(offset)
    return offsets, matches


def edit_resolution_details(
    *,
    path: str,
    edit_index: int,
    old: str,
    offsets: Sequence[int],
    matches: Sequence[int],
    before_text: str | None,
    after_text: str | None,
) -> dict[str, Any]:
    anchored = before_text is not None or after_text is not None
    occurrences = len(offsets)
    anchor_matches = len(matches)
    if anchored:
        if occurrences == 1 and anchor_matches == 0:
            code = "unique_old_anchor_mismatch"
            recommendation = (
                "old occurs exactly once; omit before/after anchors unless they are exact immediate adjacent source"
            )
        else:
            code = "anchors_do_not_isolate_one_occurrence"
            recommendation = "copy before/after anchors from the immediate source adjacent to old"
    elif occurrences == 0:
        code = "old_text_not_found"
        recommendation = "copy old exactly from the displayed current source after applying earlier edits mentally"
    else:
        code = "old_text_repeated_without_anchors"
        recommendation = "include an exact immediate before or after anchor copied from the same file"
    return {
        "path": path,
        "edit_index": edit_index,
        "occurrences": occurrences,
        "anchor_matches": anchor_matches,
        "anchors": {
            "before": before_text is not None,
            "after": after_text is not None,
            "before_chars": 0 if before_text is None else len(before_text),
            "after_chars": 0 if after_text is None else len(after_text),
        },
        "old_text_char_count": len(old),
        "old_text_sha256": sha256_text(old),
        "diagnostic": {
            "code": code,
            "recommendation": recommendation,
            "anchor_policy": {
                "omit_anchors_when_old_is_unique": True,
                "anchors_required_when_old_is_repeated": True,
                "anchors_must_be_immediate_adjacent_source": True,
            },
        },
    }


def resolve_edit_offset(text: str, edit: Mapping[str, str], *, edit_index: int) -> tuple[int, int, bool]:
    path = str(edit["path"])
    old = str(edit["old"])
    before = edit.get("before")
    after = edit.get("after")
    before_text = str(before) if before is not None else None
    after_text = str(after) if after is not None else None
    offsets, matches = anchored_offsets(text, old, before=before_text, after=after_text)
    anchored = before_text is not None or after_text is not None
    if len(matches) == 1:
        start = matches[0]
        return start, start + len(old), anchored
    details = edit_resolution_details(
        path=path,
        edit_index=edit_index,
        old=old,
        offsets=offsets,
        matches=matches,
        before_text=before_text,
        after_text=after_text,
    )
    if anchored:
        raise ToolError(
            "edit anchors must identify exactly one old-string occurrence",
            **details,
            failure_class="search_replace_anchor_mismatch",
        )
    raise ToolError(
        "edit old string must occur exactly once",
        **details,
        failure_class="search_replace_old_occurrence_mismatch",
    )


def apply_edit_bundle(
    workspace: Path,
    edits: Sequence[Mapping[str, str]],
    *,
    allowed_paths: Sequence[str],
) -> dict[str, Any]:
    ensure_paths_within_context(workspace, [str(edit["path"]) for edit in edits], allowed_paths)
    changed: list[str] = []
    planned_texts: dict[str, str] = {}
    anchored_count = 0
    for index, edit in enumerate(edits):
        path = str(edit["path"])
        old = str(edit["old"])
        new = str(edit["new"])
        reject_unsafe_generated_text(path, "edit path")
        reject_unsafe_generated_text(old, "edit old text")
        reject_unsafe_generated_text(new, "edit new text")
        before = edit.get("before")
        after = edit.get("after")
        if before is not None:
            reject_unsafe_generated_text(str(before), "edit before anchor")
        if after is not None:
            reject_unsafe_generated_text(str(after), "edit after anchor")
        target = resolve_workspace_path(workspace, path, "edit path")
        if not target.exists() or not target.is_file():
            raise ToolError(
                "edit path is not in the prepared workspace",
                path=path,
                failure_class="generated_path_not_in_workspace",
            )
        text = planned_texts.get(path)
        if text is None:
            text = target.read_text(encoding="utf-8")
        start, end, anchored = resolve_edit_offset(text, edit, edit_index=index)
        if anchored:
            anchored_count += 1
        planned_texts[path] = f"{text[:start]}{new}{text[end:]}"
        changed.append(path)
    for path, text in planned_texts.items():
        resolve_workspace_path(workspace, path, "edit path").write_text(text, encoding="utf-8")
    return {
        "kind": "search_replace_edits",
        "validated": True,
        "applied": True,
        "changed_paths": sorted(set(changed)),
        "edit_count": len(edits),
        "anchored_edit_count": anchored_count,
        "output_contract": DEFAULT_OUTPUT_CONTRACT,
    }


def structured_files_failure_class(error: str) -> str:
    if error == "model response did not contain a supported patch":
        return "unsupported_patch_response"
    if error == "structured-files output contract requires JSON files":
        return "output_contract_violation"
    if "unsafe content" in error:
        return "unsafe_generated_text"
    return "structured_files_invalid"


def reject_unsafe_model_response(text: str) -> None:
    try:
        reject_unsafe_generated_text(text, "model response")
    except ToolError as exc:
        details = dict(exc.details)
        details.setdefault("failure_class", "unsafe_generated_text")
        raise ToolError(str(exc), **details) from exc


def reject_known_wrong_contract_json(text: str) -> None:
    seen: set[str] = set()
    for candidate in (text.strip(), strip_code_fence(text)):
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if "files" in data:
            extra_keys = sorted(key for key in data if key != "files")
            if extra_keys:
                raise ToolError(
                    "structured-files output contract requires a single files key",
                    unsupported_top_level_keys=extra_keys,
                    failure_class="output_contract_violation",
                )
            return
        if "edits" in data or any(key in data for key in ("unified_diff", "patch", "diff")):
            raise ToolError(
                "structured-files output contract requires JSON files",
                failure_class="output_contract_violation",
            )


def apply_structured_files_model_response(
    workspace: Path,
    text: str,
    *,
    allowed_paths: Sequence[str],
) -> dict[str, Any]:
    reject_unsafe_model_response(text)
    try:
        reject_known_wrong_contract_json(text)
        parsed = parse_patch_response(text)
        enforce_output_contract(parsed, STRUCTURED_FILES_OUTPUT_CONTRACT)
        ensure_parsed_patch_paths_within_context(workspace, parsed, allowed_paths)
        result = apply_patch_response(workspace, parsed, apply_patch=True)
        ensure_paths_allowed(result.get("changed_paths", []), allowed_paths)
    except ToolError as exc:
        details = dict(exc.details)
        failure_class = details.pop("failure_class", None)
        if not isinstance(failure_class, str) or not failure_class:
            failure_class = structured_files_failure_class(str(exc))
        raise ToolError(str(exc), **details, failure_class=failure_class) from exc
    result["allowed_context_paths"] = sorted({validate_patch_path(path) for path in allowed_paths})
    result["output_contract"] = STRUCTURED_FILES_OUTPUT_CONTRACT
    return result


def apply_model_response(
    workspace: Path,
    text: str,
    *,
    allowed_paths: Sequence[str],
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> dict[str, Any]:
    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        return apply_structured_files_model_response(workspace, text, allowed_paths=allowed_paths)
    reject_unsafe_model_response(text)
    edits = parse_edit_bundle(text)
    if edits is not None:
        result = apply_edit_bundle(workspace, edits, allowed_paths=allowed_paths)
        result["allowed_context_paths"] = sorted({validate_patch_path(path) for path in allowed_paths})
        return result
    try:
        parsed = parse_patch_response(text)
    except ToolError as exc:
        if str(exc) == "model response did not contain a supported patch":
            raise ToolError(str(exc), **exc.details, failure_class="unsupported_patch_response") from exc
        raise
    ensure_parsed_patch_paths_within_context(workspace, parsed, allowed_paths)
    try:
        result = apply_patch_response(workspace, parsed, apply_patch=True)
    except ToolError as exc:
        if str(exc) in {
            "generated unified diff failed git apply validation",
            "generated unified diff failed to apply",
        }:
            raise ToolError(
                str(exc),
                **exc.details,
                failure_class="invalid_unified_diff",
            ) from exc
        raise
    ensure_paths_within_context(workspace, result.get("changed_paths", []), allowed_paths)
    result["allowed_context_paths"] = sorted({validate_patch_path(path) for path in allowed_paths})
    return result


def usage_token_counts(usage: Mapping[str, Any] | None, args: argparse.Namespace) -> tuple[int, int]:
    input_tokens = None
    output_tokens = None
    if isinstance(usage, Mapping):
        for key in ("input_tokens", "prompt_tokens"):
            if isinstance(usage.get(key), int):
                input_tokens = int(usage[key])
                break
        for key in ("output_tokens", "completion_tokens"):
            if isinstance(usage.get(key), int):
                output_tokens = int(usage[key])
                break
    if input_tokens is None:
        input_tokens = parse_non_negative_int(args.input_tokens or "0", "--input-tokens")
    if output_tokens is None:
        output_tokens = parse_non_negative_int(args.output_tokens or "0", "--output-tokens")
    return input_tokens, output_tokens


def observed_provider_cost(usage: Mapping[str, Any] | None) -> float | None:
    if not isinstance(usage, Mapping):
        return None
    value = usage.get("cost")
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return None


def ledger_estimated_cost_for_provider_usage(
    *,
    mode: str,
    fallback_estimated_cost: Decimal,
    usage: Mapping[str, Any] | None,
) -> tuple[Decimal, str]:
    """Return the budget-ledger cost basis for a completed runner call."""

    if mode != "live":
        return Decimal("0"), "no_model"
    observed = observed_provider_cost(usage)
    if observed is not None:
        return parse_usd(observed, "observed_provider_cost_usd"), "provider_response_usage_cost_not_invoice"
    return fallback_estimated_cost, "local_projected_estimate_not_invoice"


def append_cost_record(
    *,
    ledger_path: Path,
    run_id: str,
    acut_id: str,
    task_id: str,
    split: str,
    attempt: int,
    event: str,
    started_at: str,
    finished_at: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: Decimal,
    actual_cost: Decimal | None,
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    before = read_ledger_summary(ledger_path)
    previous_cumulative = ledger_cumulative_decimal(before)
    cumulative = previous_cumulative + estimated_cost
    record = {
        "record_type": "acut_patch_generation_attempt",
        "run_id": run_id,
        "acut_id": acut_id,
        "task_id": task_id,
        "split": split,
        "attempt": attempt,
        "event": event,
        "started_at": started_at,
        "finished_at": finished_at,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": money_json(estimated_cost),
        "actual_cost_usd": None if actual_cost is None else money_json(actual_cost),
        "cumulative_estimated_cost_usd": money_json(cumulative),
        "metadata": dict(metadata),
    }
    append_ledger_record(ledger_path, record)
    after = read_ledger_summary(ledger_path)
    return {
        "status": "appended",
        "record_count_before": before["record_count"],
        "record_count_after": after["record_count"],
        "estimated_cost_usd": money_json(estimated_cost),
        "actual_cost_recorded": actual_cost is not None,
        "new_cumulative_estimated_cost_usd": money_json(cumulative),
    }


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


def append_failure_record_if_model_responded(args: argparse.Namespace, *, started_at: str, finished_at: str, exc: Exception) -> dict[str, Any] | None:
    """Best-effort ledgering for failures after a live provider attempt.

    The normal success path appends the ledger after patch collection.  If a
    model response is received but validation/application fails first, the run
    still consumed provider resources and needs an explicit cost/usage record.
    If the provider request was attempted but no response body was captured
    (for example an HTTP timeout), ledger the local projected estimate so the
    experiment budget remains conservative.
    """

    raw_response_path = Path(args.artifact_dir) / "provider_response.redacted.json"
    details = exc.details if isinstance(exc, ToolError) else {}
    network_attempted = isinstance(details, Mapping) and details.get("network_attempted") is True
    response_received = raw_response_path.exists()
    if (not response_received and not network_attempted) or ledger_has_run_id(Path(args.llm_ledger), args.run_id):
        return None
    try:
        task = load_manifest(args.task)
        acut = load_manifest(args.acut)
        text = ""
        usage = None
        if response_received:
            text, usage = provider_text_and_usage(raw_response_path.read_bytes())
        input_tokens, output_tokens = usage_token_counts(usage, args)
        projected_cost = parse_usd(args.projected_cost_usd, "--projected-cost-usd")
        estimated_cost = parse_usd(args.estimated_cost_usd, "--estimated-cost-usd") if args.estimated_cost_usd else projected_cost
        ledger_estimated_cost, cost_basis = ledger_estimated_cost_for_provider_usage(
            mode="live",
            fallback_estimated_cost=estimated_cost,
            usage=usage,
        )
        failure_class = (
            details.get("failure_class")
            if isinstance(details, Mapping) and isinstance(details.get("failure_class"), str)
            else details.get("error_type")
            if isinstance(details, Mapping) and isinstance(details.get("error_type"), str)
            else type(exc).__name__
        )
        response_sha = sha256_text(text) if response_received else None
        request_profile = details.get("request_profile") if isinstance(details, Mapping) else None
        return append_cost_record(
            ledger_path=Path(args.llm_ledger),
            run_id=args.run_id,
            acut_id=str(acut.get("acut_id")),
            task_id=str(task.get("task_id")),
            split=str(task.get("split")),
            attempt=args.attempt,
            event="runner_error_after_model_response" if response_received else "runner_error_after_model_attempt",
            started_at=started_at,
            finished_at=finished_at,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=ledger_estimated_cost,
            actual_cost=None,
            metadata={
                "runner_id": RUNNER_ID,
                "mode": "live",
                "submission_contract": getattr(args, "output_contract", DEFAULT_OUTPUT_CONTRACT),
                "model_call_made": True,
                "model_response_received": response_received,
                "network_attempted": network_attempted or response_received,
                "failure_class": failure_class,
                "error_type": details.get("error_type") if isinstance(details, Mapping) else None,
                "cost_basis": cost_basis,
                "actual_cost_status": "unknown_not_invoice_verified",
                "provider_usage_reported": usage is not None,
                "provider_usage": usage or {},
                "observed_provider_cost_usd": observed_provider_cost(usage),
                "observed_provider_cost_status": "provider_response_usage_cost_not_invoice"
                if observed_provider_cost(usage) is not None
                else "not_reported",
                "projected_cost_usd": money_json(projected_cost),
                "fallback_estimated_cost_usd": money_json(estimated_cost),
                "response_text_sha256": response_sha,
                "request_profile": request_profile if isinstance(request_profile, Mapping) else {},
            },
        )
    except Exception as ledger_exc:  # keep the original failure primary
        return {"status": "failed", "error": str(ledger_exc), "details": getattr(ledger_exc, "details", {})}


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    started_at = iso_now()
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        workspace = Path(args.workspace).resolve()
        task_path = Path(args.task)
        acut_path = Path(args.acut)
        artifact_dir = Path(args.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        raw_response_path = artifact_dir / "provider_response.redacted.json"
        prompt_path = artifact_dir / "prompt.txt"
        prompt_snapshot_path = artifact_dir / "prompt_snapshot.json"
        patch_path = Path(args.patch_path) if args.patch_path else artifact_dir / "submission.patch"
        ensure_git_workspace(workspace)

        task = load_manifest(task_path)
        acut = load_manifest(acut_path)
        require_keys(task, ["task_id", "split"], "task manifest")
        require_keys(acut, ["acut_id", "model"], "ACUT manifest")
        mode = mode_from_args(args)
        task_statement, statement_path, statement_truncated = safe_task_statement(task_path, task)

        max_file_chars = effective_max_file_chars(
            requested_max_file_chars=args.max_file_chars,
            max_context_chars=args.max_context_chars,
            context_path_count=len(args.context_path),
            task=task,
            task_statement=task_statement,
        )
        context_files = [
            context_file_payload(
                workspace,
                path,
                max_file_chars,
                focus_terms=context_focus_terms(task, task_statement, path),
                allow_missing=args.output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT,
            )
            for path in args.context_path
        ]
        if mode in {"live", "mock_response"} and not context_files:
            raise ToolError(
                "no context files available for model patch generation",
                failure_class="empty_context_paths",
                network_attempted=False,
                context_paths=list(args.context_path),
            )
        specialist_text = None
        specialist_path = specialist_context_path(acut)
        specialist_assertion = assert_specialist_context_policy(
            acut=acut,
            include_mode=args.include_specialist_context,
            specialist_path=specialist_path,
        )
        include_specialist = args.include_specialist_context == "always" or (
            args.include_specialist_context == "auto" and specialist_path is not None
        )
        if include_specialist and specialist_path is not None:
            specialist_file = resolve_specialist_context_file(specialist_path, acut_path)
            if not specialist_file.exists() or not specialist_file.is_file():
                raise ToolError(
                    "specialist context file does not exist",
                    path=specialist_path,
                    resolved_path=str(specialist_file),
                    failure_class="specialist_context_missing",
                )
            specialist_text, _ = truncate_text(specialist_file.read_text(encoding="utf-8"), args.max_file_chars)

        prompt = build_prompt(
            task=task,
            task_statement=task_statement,
            acut=acut,
            context_files=context_files,
            specialist_context=specialist_text,
            max_context_chars=args.max_context_chars,
            output_contract=args.output_contract,
        )
        prompt_path.write_text(prompt, encoding="utf-8")
        write_json(
            prompt_snapshot_path,
            {
                "tool": TOOL,
                "runner_id": RUNNER_ID,
                "run_id": args.run_id,
                "prompt_sha256": sha256_text(prompt),
                "prompt_char_count": len(prompt),
                "prompt_content_recorded": True,
                "task_statement_path": statement_path,
                "statement_truncated": statement_truncated,
                "context_files": [
                    {
                        key: item[key]
                        for key in (
                            "path",
                            "exists",
                            "sha256",
                            "char_count",
                            "truncated",
                            "displayed_char_count",
                            "focus_terms",
                        )
                    }
                    | {
                        "focused_excerpts": [
                            {
                                key: excerpt[key]
                                for key in ("trigger", "start_char", "end_char", "char_count")
                            }
                            for excerpt in item.get("focused_excerpts", [])
                        ]
                    }
                    for item in context_files
                ],
                "context_packaging": {
                    "requested_max_file_chars": args.max_file_chars,
                    "effective_max_file_chars": max_file_chars,
                    "max_context_chars": args.max_context_chars,
                    "prompt_truncated": prompt.endswith("[truncated]\n"),
                },
                "specialist_context_included": specialist_text is not None,
                "specialist_context_path": specialist_path if specialist_text is not None else None,
                "specialist_context_assertion": specialist_assertion,
                "output_contract": args.output_contract,
                "output_contract_schema": output_contract_schema(args.output_contract),
                "full_urls_redacted": True,
            },
        )

        projected_cost = parse_usd(args.projected_cost_usd, "--projected-cost-usd")
        estimated_cost = parse_usd(args.estimated_cost_usd, "--estimated-cost-usd") if args.estimated_cost_usd else projected_cost
        actual_cost = parse_usd(args.actual_cost_usd, "--actual-cost-usd") if args.actual_cost_usd else None
        budget_gate = gate_payload(
            ledger_path=Path(args.llm_ledger),
            projected_cost_usd=projected_cost,
            acut_id=str(acut["acut_id"]),
            split=str(task["split"]),
            attempt=args.attempt,
            coordinator_decision_ref=args.coordinator_decision_ref,
            env=os.environ,
        )
        if mode == "live" and budget_gate["status"] != "passed":
            raise ToolError("LLM budget gate blocked live run", gate=budget_gate)

        model_call_made = False
        provider_usage = None
        request_profile: dict[str, Any] | None = None
        duration_start = time.monotonic()
        if mode == "dry_run":
            model_text = ""
            patch_result = {"received": False, "applied": False}
            patch_artifact = {"path": str(patch_path), "written": False, "size_bytes": 0}
            status = "dry_run_completed"
            event = "dry_run_no_model"
        else:
            if mode == "mock_response":
                model_text = read_mock_response(args)
                raw_response_path.write_text(redact_sensitive_text(model_text, os.environ), encoding="utf-8")
            else:
                model_text, provider_usage, request_profile = call_live_model(
                    acut=acut,
                    prompt=prompt,
                    timeout_seconds=args.http_timeout_seconds,
                    max_response_bytes=args.max_response_bytes,
                    raw_response_path=raw_response_path,
                    output_contract=args.output_contract,
                )
                model_call_made = True
            patch_result = apply_model_response(
                workspace,
                model_text,
                allowed_paths=[str(item["path"]) for item in context_files],
                output_contract=args.output_contract,
            )
            safe_env, _ = llm_safe_subprocess_env(os.environ)
            patch_artifact = write_safe_patch(workspace, patch_path, safe_env)
            if patch_artifact.get("unsafe_content_detected") is True:
                raise ToolError(
                    "generated patch contains unsafe content",
                    failure_class="unsafe_generated_text",
                    unsafe_content=patch_artifact.get("unsafe_content", {}),
                )
            status = "patch_generated"
            event = "patch_generated"

        finished_at = iso_now()
        duration_seconds = round(time.monotonic() - duration_start, 3)
        input_tokens, output_tokens = usage_token_counts(provider_usage, args)
        ledger_estimated_cost, cost_basis = ledger_estimated_cost_for_provider_usage(
            mode=mode,
            fallback_estimated_cost=estimated_cost,
            usage=provider_usage,
        )
        ledger_append = append_cost_record(
            ledger_path=Path(args.llm_ledger),
            run_id=args.run_id,
            acut_id=str(acut["acut_id"]),
            task_id=str(task["task_id"]),
            split=str(task["split"]),
            attempt=args.attempt,
            event=event,
            started_at=started_at,
            finished_at=finished_at,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=ledger_estimated_cost,
            actual_cost=actual_cost,
            metadata={
                "runner_id": RUNNER_ID,
                "mode": mode,
                "submission_contract": args.output_contract,
                "model_call_made": model_call_made,
                "cost_basis": cost_basis,
                "actual_cost_status": "unknown_not_provider_reported" if actual_cost is None else "provider_or_invoice_reported",
                "provider_usage_reported": provider_usage is not None,
                "provider_usage": provider_usage or {},
                "observed_provider_cost_usd": observed_provider_cost(provider_usage),
                "observed_provider_cost_status": "provider_response_usage_cost_not_invoice"
                if observed_provider_cost(provider_usage) is not None
                else "not_reported",
                "projected_cost_usd": money_json(projected_cost),
                "fallback_estimated_cost_usd": money_json(estimated_cost),
                "request_profile": request_profile or {},
                "patch_size_bytes": patch_artifact.get("size_bytes", 0),
            },
        )
        payload = {
            "tool": TOOL,
            "runner_id": RUNNER_ID,
            "status": status,
            "run_id": args.run_id,
            "acut_id": acut["acut_id"],
            "task_id": task["task_id"],
            "split": task["split"],
            "attempt": args.attempt,
            "mode": mode,
            "submission_contract": args.output_contract,
            "output_contract": args.output_contract,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
            "workspace": str(workspace),
            "artifact_dir": str(artifact_dir),
            "prompt_artifact": str(prompt_path),
            "prompt_snapshot": str(prompt_snapshot_path),
            "raw_response_artifact": str(raw_response_path),
            "patch_path": str(patch_path),
            "model_call_made": model_call_made,
            "budget_gate": budget_gate,
            "cost_ledger_append": ledger_append,
            "cost_accounting": {
                "estimated_cost_usd": money_json(ledger_estimated_cost),
                "actual_cost_usd": None if actual_cost is None else money_json(actual_cost),
                "actual_cost_status": "unknown_not_provider_reported" if actual_cost is None else "provider_or_invoice_reported",
                "observed_provider_cost_usd": observed_provider_cost(provider_usage),
                "observed_provider_cost_status": "provider_response_usage_cost_not_invoice"
                if observed_provider_cost(provider_usage) is not None
                else "not_reported",
                "provider_usage_reported": provider_usage is not None,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "patch": patch_result,
            "patch_artifact": patch_artifact,
            "llm_env_policy": {
                "allowed_variable_names": ["BARCAROLLE_LLM_API_KEY", "BARCAROLLE_LLM_BASE_URL"],
                "values_recorded": False,
                "endpoint_value_recorded": False,
                "raw_response_redacted": True,
            },
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        finished_at = iso_now()
        details = exc.details if isinstance(exc, ToolError) else {"exception_type": type(exc).__name__}
        network_attempted = isinstance(details, Mapping) and details.get("network_attempted") is True
        failure_ledger_append = None
        try:
            if mode_from_args(args) == "live":
                failure_ledger_append = append_failure_record_if_model_responded(args, started_at=started_at, finished_at=finished_at, exc=exc)
        except Exception:
            failure_ledger_append = None
        payload = {
            "tool": TOOL,
            "runner_id": RUNNER_ID,
            "status": "error",
            "error": redact_sensitive_text(str(exc), os.environ),
            "details": details,
            "cost_ledger_append": failure_ledger_append,
            "started_at": started_at,
            "finished_at": finished_at,
        }
        if "args" in locals():
            payload["submission_contract"] = getattr(args, "output_contract", DEFAULT_OUTPUT_CONTRACT)
            payload["output_contract"] = getattr(args, "output_contract", DEFAULT_OUTPUT_CONTRACT)
        if "budget_gate" in locals():
            payload["budget_gate"] = budget_gate
        if isinstance(failure_ledger_append, Mapping) and failure_ledger_append.get("status") == "appended":
            payload["cost_accounting"] = {
                "estimated_cost_usd": failure_ledger_append.get("estimated_cost_usd"),
                "actual_cost_usd": None,
                "actual_cost_recorded": failure_ledger_append.get("actual_cost_recorded"),
                "cost_record_basis": "failure_ledger_append",
            }
        if "model_call_made" in locals():
            payload["model_call_made"] = bool(model_call_made or network_attempted)
        elif isinstance(failure_ledger_append, Mapping):
            payload["model_call_made"] = failure_ledger_append.get("status") == "appended"
        if "prompt_snapshot_path" in locals() and prompt_snapshot_path.exists():
            payload["prompt_snapshot"] = str(prompt_snapshot_path)
        if "raw_response_path" in locals() and raw_response_path.exists():
            payload["raw_response_artifact"] = str(raw_response_path)
        try:
            write_json(Path(args.output), payload)
        except Exception:
            pass
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return exc.exit_code if isinstance(exc, ToolError) else 1


if __name__ == "__main__":
    sys.exit(main())
