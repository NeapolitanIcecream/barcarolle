#!/usr/bin/env python3
"""Patch-generation command for ACUT adapter execution.

This command is intentionally small and subprocess-friendly: the outer
``acut_patch_adapter.py`` remains responsible for budget gating, redaction of
captured stdout/stderr, patch artifact collection, and ledger writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, git, load_manifest, require_keys
from _llm_budget import (
    REQUIRED_LLM_ENV_VARS,
    assert_safe_command_arguments,
    ensure_no_required_env_values,
    redact_sensitive_text,
    unsafe_text_findings,
)


TOOL = "barcarolle_patch_command"
COMMAND_CONTRACT_ID = "barcarolle-patch-command-v1"
DEFAULT_OUTPUT_CONTRACT = "patch-or-files-v1"
STRUCTURED_FILES_OUTPUT_CONTRACT = "structured-files-json-v1"
DEFAULT_TASK_PACKAGE = ".core_narrative/task.json"
DEFAULT_MAX_STATEMENT_CHARS = 6_000
DEFAULT_MAX_MANIFEST_CHARS = 5_000
DEFAULT_MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_HTTP_TIMEOUT_SECONDS = 120


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a task prompt, optionally call the configured LLM endpoint, "
            "and apply the returned patch in the prepared workspace. LLM "
            "credential values and endpoint URLs are read only from "
            "BARCAROLLE_LLM_API_KEY and BARCAROLLE_LLM_BASE_URL."
        )
    )
    parser.add_argument("--workspace", default=".", help="Prepared task workspace. Defaults to current directory.")
    parser.add_argument(
        "--task-package",
        default=DEFAULT_TASK_PACKAGE,
        help="Prepared workspace task package path, relative to --workspace by default.",
    )
    parser.add_argument(
        "--statement-path",
        help="Optional task statement path override, relative to --workspace by default.",
    )
    parser.add_argument("--acut", required=True, help="ACUT manifest JSON/YAML path.")
    parser.add_argument("--dry-run", action="store_true", help="Prepare the prompt without requiring env or calling a model.")
    parser.add_argument("--mock-response", help="Read a no-model mock response from this local file and apply it.")
    parser.add_argument("--mock-response-text", help="Use this no-model mock response text and apply it.")
    parser.add_argument("--no-apply", action="store_true", help="Validate a mock patch without modifying the workspace.")
    parser.add_argument("--summary-output", help="Optional redacted machine-readable summary JSON path.")
    parser.add_argument(
        "--output-contract",
        choices=(DEFAULT_OUTPUT_CONTRACT, STRUCTURED_FILES_OUTPUT_CONTRACT),
        default=DEFAULT_OUTPUT_CONTRACT,
        help=(
            "Direct model output contract. The default accepts unified diffs or "
            "structured files; structured-files-json-v1 requests strict JSON "
            "and rejects unified-diff fallbacks before workspace mutation."
        ),
    )
    parser.add_argument(
        "--http-timeout-seconds",
        type=int,
        default=DEFAULT_HTTP_TIMEOUT_SECONDS,
        help="Live LLM request timeout.",
    )
    parser.add_argument(
        "--max-statement-chars",
        type=int,
        default=DEFAULT_MAX_STATEMENT_CHARS,
        help="Maximum statement characters included in the prompt.",
    )
    parser.add_argument(
        "--max-manifest-chars",
        type=int,
        default=DEFAULT_MAX_MANIFEST_CHARS,
        help="Maximum sanitized ACUT manifest characters included in the prompt.",
    )
    parser.add_argument(
        "--max-response-bytes",
        type=int,
        default=DEFAULT_MAX_RESPONSE_BYTES,
        help="Maximum live response body bytes to read.",
    )
    return parser.parse_args(list(argv))


def mode_from_args(args: argparse.Namespace) -> str:
    selected = [
        bool(args.dry_run),
        args.mock_response is not None,
        args.mock_response_text is not None,
    ]
    if sum(selected) > 1:
        raise ToolError("choose only one of --dry-run, --mock-response, or --mock-response-text")
    if args.dry_run:
        return "dry_run"
    if args.mock_response is not None or args.mock_response_text is not None:
        return "mock_response"
    if args.no_apply:
        raise ToolError("--no-apply is only supported with no-model mock response modes")
    return "live"


def resolve_workspace(path: str) -> Path:
    workspace = Path(path).resolve()
    result = git("rev-parse", "--is-inside-work-tree", cwd=workspace)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ToolError("workspace is not a git work tree", workspace=str(workspace))
    return workspace


def resolve_workspace_file(workspace: Path, path: str, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ToolError(f"{label} must stay inside the workspace", path=path) from exc
    return resolved


def ensure_positive_int(value: int, name: str) -> None:
    if value < 1:
        raise ToolError(f"{name} must be at least 1")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n[truncated]\n", True


def sanitize_text(text: str) -> str:
    return redact_sensitive_text(text, os.environ)


def sanitize_jsonish(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in {"public_url"}:
                safe[key_text] = "<redacted:url>"
            else:
                safe[key_text] = sanitize_jsonish(item)
        return safe
    if isinstance(value, list):
        return [sanitize_jsonish(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def load_task_package(workspace: Path, args: argparse.Namespace) -> tuple[Path, dict[str, Any], Path | None, str, bool]:
    task_path = resolve_workspace_file(workspace, args.task_package, "--task-package")
    task = load_manifest(task_path)
    require_keys(task, ["task_id", "split"], "task package")

    statement_path: Path | None = None
    if args.statement_path:
        statement_path = resolve_workspace_file(workspace, args.statement_path, "--statement-path")
    elif isinstance(task.get("task_statement_path"), str) and task["task_statement_path"]:
        statement_path = resolve_workspace_file(workspace, str(task["task_statement_path"]), "task_statement_path")

    statement = ""
    statement_truncated = False
    if statement_path is not None and statement_path.exists():
        statement, statement_truncated = truncate_text(
            sanitize_text(statement_path.read_text(encoding="utf-8")),
            args.max_statement_chars,
        )
    return task_path, task, statement_path, statement, statement_truncated


def concise_acut_summary(acut: Mapping[str, Any]) -> dict[str, Any]:
    runtime_budget = acut.get("runtime_budget")
    retrieval = acut.get("retrieval_context_strategy")
    network = acut.get("network_policy")
    tool_permissions = acut.get("tool_permissions")
    return sanitize_jsonish(
        {
            "acut_id": acut.get("acut_id"),
            "provider": acut.get("provider"),
            "model": acut.get("model"),
            "model_parameters": acut.get("model_parameters", {}),
            "prompt_policy_digest": acut.get("prompt_policy_digest"),
            "retrieval_context_strategy": retrieval if isinstance(retrieval, dict) else {},
            "runtime_budget": runtime_budget if isinstance(runtime_budget, dict) else {},
            "network_policy": network if isinstance(network, dict) else {},
            "tool_permissions": tool_permissions if isinstance(tool_permissions, dict) else {},
        }
    )


def concise_task_summary(task: Mapping[str, Any]) -> dict[str, Any]:
    source = task.get("source") if isinstance(task.get("source"), dict) else {}
    return sanitize_jsonish(
        {
            "task_id": task.get("task_id"),
            "repo_slug": task.get("repo_slug"),
            "split": task.get("split"),
            "task_family": task.get("task_family"),
            "source": {
                "kind": source.get("kind"),
                "anchor_id": source.get("anchor_id"),
                "base_commit": source.get("base_commit"),
            },
            "allowed_context": task.get("allowed_context", {}),
            "workspace_history": task.get("workspace_history", {}),
        }
    )


def build_prompt(
    *,
    task: Mapping[str, Any],
    statement: str,
    acut: Mapping[str, Any],
    max_manifest_chars: int,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> tuple[str, bool]:
    acut_json = json.dumps(concise_acut_summary(acut), indent=2, sort_keys=True)
    acut_json, manifest_truncated = truncate_text(acut_json, max_manifest_chars)
    task_json = json.dumps(concise_task_summary(task), indent=2, sort_keys=True)
    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        return_contract = [
            "Return only a JSON object. Do not include markdown fences, prose, or a unified diff.",
            "The JSON object must have this shape:",
            '{"files":[{"path":"relative/path","action":"write","content":"full file content"}]}',
            "Allowed actions are write, create, replace, and delete. For delete, omit content.",
            "Each path must be relative and must not target .git or .core_narrative.",
        ]
    else:
        return_contract = [
            "Return either:",
            "1. A unified diff applicable with git apply.",
            "2. JSON with a string field named unified_diff, patch, or diff.",
            "3. JSON with files: [{path, action, content}], where action is write, create, replace, or delete.",
        ]
    prompt = "\n".join(
        [
            "You are generating a minimal repository patch for one prepared ACUT task.",
            "",
            "Use only the visible task package, public statement, and ACUT policy below.",
            "Do not use future history, reference patches, private benchmark artifacts, or ACUT outputs.",
            "Do not expose credentials, endpoint values, bearer tokens, or full URLs in the patch.",
            "",
            *return_contract,
            "",
            "Task package summary:",
            task_json,
            "",
            "Public task statement:",
            statement or "[no task statement was packaged]",
            "",
            "ACUT manifest summary:",
            acut_json,
        ]
    )
    return sanitize_text(prompt), manifest_truncated


def llm_env_summary(env: Mapping[str, str]) -> dict[str, Any]:
    return {
        "allowed_variable_names": list(REQUIRED_LLM_ENV_VARS),
        "required_present": {name: bool(env.get(name)) for name in REQUIRED_LLM_ENV_VARS},
        "values_recorded": False,
        "endpoint_value_recorded": False,
        "command_arguments_checked": True,
        "unsafe_command_arguments_rejected": True,
    }


def require_live_env(env: Mapping[str, str]) -> tuple[str, str]:
    missing = [name for name in REQUIRED_LLM_ENV_VARS if not env.get(name)]
    if missing:
        raise ToolError("missing required LLM environment", missing_env=missing, network_attempted=False)
    return env["BARCAROLLE_LLM_API_KEY"], env["BARCAROLLE_LLM_BASE_URL"]


def resolve_live_endpoint(raw_endpoint: str) -> tuple[str, str]:
    endpoint = raw_endpoint.strip()
    if not endpoint:
        raise ToolError("configured LLM endpoint is empty", network_attempted=False)
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ToolError("configured LLM endpoint is not an HTTP endpoint", network_attempted=False)

    path = parsed.path.rstrip("/")
    if path.endswith("/responses"):
        return endpoint, "responses"
    if path.endswith("/chat/completions"):
        return endpoint, "chat_completions"
    return endpoint.rstrip("/") + "/chat/completions", "chat_completions"


def live_request_payload(
    acut: Mapping[str, Any],
    prompt: str,
    endpoint_kind: str,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> dict[str, Any]:
    model = acut.get("model")
    if not isinstance(model, str) or not model:
        raise ToolError("ACUT manifest is missing model")
    params = acut.get("model_parameters") if isinstance(acut.get("model_parameters"), dict) else {}
    system = (
        "You are a patch-generation engine. Return only the requested patch "
        "format. Do not include credentials, endpoint values, bearer tokens, or full URLs."
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
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        **params,
    }
    if output_contract == STRUCTURED_FILES_OUTPUT_CONTRACT:
        payload["response_format"] = {"type": "json_object"}
    return payload


def extract_text_from_provider_response(body: bytes) -> str:
    raw_text = body.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text

    if isinstance(data, dict):
        direct = data.get("output_text")
        if isinstance(direct, str):
            return direct

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first.get("text")
                if isinstance(text, str):
                    return text

        output = data.get("output")
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content_items = item.get("content")
                if not isinstance(content_items, list):
                    continue
                for content_item in content_items:
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            if chunks:
                return "\n".join(chunks)
    return raw_text


def call_live_model(
    *,
    acut: Mapping[str, Any],
    prompt: str,
    env: Mapping[str, str],
    timeout_seconds: int,
    max_response_bytes: int,
    output_contract: str = DEFAULT_OUTPUT_CONTRACT,
) -> str:
    api_key, raw_endpoint = require_live_env(env)
    endpoint, endpoint_kind = resolve_live_endpoint(raw_endpoint)
    payload = live_request_payload(acut, prompt, endpoint_kind, output_contract)
    request_body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(max_response_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise ToolError(
            "LLM request failed",
            http_status=exc.code,
            network_attempted=True,
        ) from exc
    except urllib.error.URLError as exc:
        raise ToolError(
            "LLM request failed",
            error_type=type(exc.reason).__name__,
            network_attempted=True,
        ) from exc
    except TimeoutError as exc:
        raise ToolError("LLM request timed out", network_attempted=True) from exc
    except OSError as exc:
        raise ToolError(
            "LLM request failed",
            error_type=type(exc).__name__,
            network_attempted=True,
        ) from exc

    if len(body) > max_response_bytes:
        raise ToolError("LLM response exceeded maximum size", network_attempted=True)
    return extract_text_from_provider_response(body)


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def extract_fenced_diff(text: str) -> str | None:
    lines = text.splitlines()
    in_fence = False
    fence_lang = ""
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") and not in_fence:
            in_fence = True
            fence_lang = stripped[3:].strip().lower()
            buffer = []
            continue
        if stripped == "```" and in_fence:
            candidate = "\n".join(buffer).strip()
            if fence_lang in {"diff", "patch"} or "diff --git " in candidate or "\n--- " in candidate:
                return candidate
            in_fence = False
            fence_lang = ""
            buffer = []
            continue
        if in_fence:
            buffer.append(line)
    return None


def extract_inline_diff(text: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("diff --git "):
            return "\n".join(lines[index:]).strip() + "\n"
    for index, line in enumerate(lines):
        if line.startswith("--- ") and any(candidate.startswith("+++ ") for candidate in lines[index + 1 : index + 4]):
            return "\n".join(lines[index:]).strip() + "\n"
    return None


def parse_patch_response(text: str) -> dict[str, Any]:
    candidates = [text.strip(), strip_code_fence(text)]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            for key in ("unified_diff", "patch", "diff"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return {"kind": "unified_diff", "text": value.strip() + "\n"}
            files = data.get("files")
            if isinstance(files, list):
                return {"kind": "structured_files", "files": files}

    fenced = extract_fenced_diff(text)
    if fenced:
        return {"kind": "unified_diff", "text": fenced.strip() + "\n"}
    inline = extract_inline_diff(text)
    if inline:
        return {"kind": "unified_diff", "text": inline}
    raise ToolError("model response did not contain a supported patch")


def enforce_output_contract(parsed: Mapping[str, Any], output_contract: str) -> None:
    if output_contract != STRUCTURED_FILES_OUTPUT_CONTRACT:
        return
    if parsed.get("kind") != "structured_files":
        raise ToolError(
            "structured-files output contract requires JSON files",
            failure_class="output_contract_violation",
        )


def classify_failure(error: str, details: Mapping[str, Any]) -> str:
    if isinstance(details.get("failure_class"), str):
        return str(details["failure_class"])
    if error == "generated unified diff failed git apply validation":
        return "invalid_unified_diff"
    if error == "model response did not contain a supported patch":
        return "unsupported_patch_response"
    if error == "structured-files output contract requires JSON files":
        return "output_contract_violation"
    if "unsafe content" in error:
        return "unsafe_generated_content"
    if error == "LLM request timed out" or details.get("error_type") == "timeout":
        return "llm_request_timed_out"
    if error.startswith("LLM request"):
        return "llm_request_failed"
    return "direct_patch_command_error"


def reject_unsafe_generated_text(text: str, label: str) -> None:
    findings = unsafe_text_findings(text, os.environ)
    if findings["unsafe"]:
        raise ToolError(
            f"{label} contains unsafe content",
            unsafe_content=findings,
            network_attempted=False,
        )


def validate_patch_path(path: str) -> str:
    reject_unsafe_generated_text(path, "generated patch path")
    relative = Path(path)
    if relative.is_absolute():
        raise ToolError("patch path must be relative", path=path)
    if ".." in relative.parts:
        raise ToolError("patch path must not contain parent traversal", path=path)
    if any(part in {".git", ".core_narrative"} for part in relative.parts):
        raise ToolError("patch path targets reserved workspace metadata", path=path)
    if not str(relative):
        raise ToolError("patch path is empty")
    return str(relative)


def diff_paths(patch_text: str) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            for item in parts[2:4]:
                if item.startswith("a/") or item.startswith("b/"):
                    paths.append(item[2:])
            continue
        if line.startswith(("--- ", "+++ ")):
            marker = line[4:].split("\t", 1)[0].strip()
            if marker == "/dev/null":
                continue
            if marker.startswith(("a/", "b/")):
                paths.append(marker[2:])
    return sorted(set(paths))


def changed_paths(workspace: Path) -> list[str]:
    result = git("status", "--porcelain", "--untracked-files=all", cwd=workspace)
    if result.returncode != 0:
        raise ToolError("failed to inspect workspace status", stderr=sanitize_text(result.stderr.strip()))
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw == ".core_narrative" or raw.startswith(".core_narrative/"):
            continue
        paths.append(raw.strip())
    return sorted(paths)


def run_git_apply(workspace: Path, patch_text: str, *, apply_patch: bool) -> dict[str, Any]:
    reject_unsafe_generated_text(patch_text, "generated patch")
    patch_paths = diff_paths(patch_text)
    for path in patch_paths:
        validate_patch_path(path)

    check = subprocess.run(
        ["git", "apply", "--check", "--whitespace=nowarn", "-"],
        cwd=str(workspace),
        input=patch_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        raise ToolError(
            "generated unified diff failed git apply validation",
            git_apply_stderr=sanitize_text(check.stderr.strip()),
        )

    if apply_patch:
        applied = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            cwd=str(workspace),
            input=patch_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if applied.returncode != 0:
            raise ToolError(
                "generated unified diff failed to apply",
                git_apply_stderr=sanitize_text(applied.stderr.strip()),
            )

    return {
        "kind": "unified_diff",
        "validated": True,
        "applied": apply_patch,
        "declared_paths": patch_paths,
        "changed_paths": changed_paths(workspace),
    }


def workspace_target(workspace: Path, path: str) -> Path:
    safe_relative = validate_patch_path(path)
    target = (workspace / safe_relative).resolve()
    try:
        target.relative_to(workspace)
    except ValueError as exc:
        raise ToolError("structured patch path escaped workspace", path=path) from exc
    return target


def apply_structured_files(workspace: Path, files: Sequence[Any], *, apply_patch: bool) -> dict[str, Any]:
    planned_paths: list[str] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ToolError("structured patch file entry must be an object", index=index)
        path = item.get("path")
        if not isinstance(path, str) or not path:
            raise ToolError("structured patch file entry requires path", index=index)
        planned_paths.append(validate_patch_path(path))
        action = item.get("action", "write")
        if action not in {"write", "create", "replace", "delete"}:
            raise ToolError("unsupported structured patch action", index=index, action=action)
        if action != "delete":
            content = item.get("content")
            if not isinstance(content, str):
                raise ToolError("structured patch write action requires string content", index=index)
            reject_unsafe_generated_text(content, "structured patch content")

    if apply_patch:
        for item in files:
            path = str(item["path"])
            action = item.get("action", "write")
            target = workspace_target(workspace, path)
            if action == "delete":
                if target.exists():
                    target.unlink()
                continue
            content = str(item["content"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    return {
        "kind": "structured_files",
        "validated": True,
        "applied": apply_patch,
        "declared_paths": sorted(set(planned_paths)),
        "changed_paths": changed_paths(workspace),
    }


def apply_patch_response(workspace: Path, parsed: Mapping[str, Any], *, apply_patch: bool) -> dict[str, Any]:
    kind = parsed.get("kind")
    if kind == "unified_diff":
        text = parsed.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ToolError("unified diff response is empty")
        return run_git_apply(workspace, text, apply_patch=apply_patch)
    if kind == "structured_files":
        files = parsed.get("files")
        if not isinstance(files, list) or not files:
            raise ToolError("structured patch response has no files")
        return apply_structured_files(workspace, files, apply_patch=apply_patch)
    raise ToolError("unsupported parsed patch kind", kind=kind)


def read_mock_response(args: argparse.Namespace) -> str:
    if args.mock_response_text is not None:
        return str(args.mock_response_text)
    if args.mock_response is None:
        raise ToolError("mock response path is required")
    path = Path(args.mock_response)
    return path.read_text(encoding="utf-8")


def safe_json_text(payload: Mapping[str, Any]) -> str:
    return sanitize_text(json.dumps(payload, indent=2, sort_keys=True))


def emit_payload(payload: Mapping[str, Any], output_path: str | None = None, *, stderr: bool = False) -> None:
    text = safe_json_text(payload)
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text, file=sys.stderr if stderr else sys.stdout)


def base_payload(
    *,
    status: str,
    mode: str,
    workspace: Path | None,
    task: Mapping[str, Any] | None,
    acut: Mapping[str, Any] | None,
    prompt: str | None,
    statement_path: Path | None,
    statement_truncated: bool,
    manifest_truncated: bool,
    output_contract: str,
) -> dict[str, Any]:
    prompt_info = {
        "prepared": prompt is not None,
        "sha256": None if prompt is None else sha256_text(prompt),
        "char_count": None if prompt is None else len(prompt),
        "content_recorded": False,
        "full_urls_redacted": True,
        "statement_truncated": statement_truncated,
        "manifest_truncated": manifest_truncated,
    }
    return {
        "tool": TOOL,
        "command_contract_id": COMMAND_CONTRACT_ID,
        "status": status,
        "mode": mode,
        "output_contract": output_contract,
        "model_call_made": mode == "live" and status.endswith("_applied"),
        "workspace": None if workspace is None else str(workspace),
        "task_id": None if task is None else task.get("task_id"),
        "split": None if task is None else task.get("split"),
        "acut_id": None if acut is None else acut.get("acut_id"),
        "provider": None if acut is None else acut.get("provider"),
        "model": None if acut is None else acut.get("model"),
        "statement_path": None if statement_path is None else str(statement_path),
        "prompt": prompt_info,
        "llm_env_policy": llm_env_summary(os.environ),
    }


def run(argv: Sequence[str]) -> int:
    assert_safe_command_arguments(argv, os.environ)
    ensure_no_required_env_values(argv, os.environ)
    args = parse_args(argv)
    mode = mode_from_args(args)
    ensure_positive_int(args.http_timeout_seconds, "--http-timeout-seconds")
    ensure_positive_int(args.max_statement_chars, "--max-statement-chars")
    ensure_positive_int(args.max_manifest_chars, "--max-manifest-chars")
    ensure_positive_int(args.max_response_bytes, "--max-response-bytes")

    workspace = resolve_workspace(args.workspace)
    _, task, statement_path, statement, statement_truncated = load_task_package(workspace, args)
    acut = load_manifest(args.acut)
    require_keys(acut, ["acut_id", "model"], "ACUT manifest")
    prompt, manifest_truncated = build_prompt(
        task=task,
        statement=statement,
        acut=acut,
        max_manifest_chars=args.max_manifest_chars,
        output_contract=args.output_contract,
    )

    if mode == "dry_run":
        payload = base_payload(
            status="dry_run_completed",
            mode=mode,
            workspace=workspace,
            task=task,
            acut=acut,
            prompt=prompt,
            statement_path=statement_path,
            statement_truncated=statement_truncated,
            manifest_truncated=manifest_truncated,
            output_contract=args.output_contract,
        )
        payload["patch"] = {"received": False, "validated": False, "applied": False}
        emit_payload(payload, args.summary_output)
        return 0

    if mode == "mock_response":
        model_text = read_mock_response(args)
        model_call_made = False
        model_response_received = False
    else:
        model_text = call_live_model(
            acut=acut,
            prompt=prompt,
            env=os.environ,
            timeout_seconds=args.http_timeout_seconds,
            max_response_bytes=args.max_response_bytes,
            output_contract=args.output_contract,
        )
        model_call_made = True
        model_response_received = True

    try:
        reject_unsafe_generated_text(model_text, "model response")
        parsed = parse_patch_response(model_text)
        enforce_output_contract(parsed, args.output_contract)
        patch_result = apply_patch_response(workspace, parsed, apply_patch=not args.no_apply)
    except ToolError as exc:
        if model_response_received:
            exc.details.setdefault("model_call_made", True)
            exc.details.setdefault("model_response_received", True)
        raise

    status = "mock_response_validated" if args.no_apply else f"{mode}_applied"
    payload = base_payload(
        status=status,
        mode=mode,
        workspace=workspace,
        task=task,
        acut=acut,
        prompt=prompt,
        statement_path=statement_path,
        statement_truncated=statement_truncated,
        manifest_truncated=manifest_truncated,
        output_contract=args.output_contract,
    )
    payload["model_call_made"] = model_call_made
    payload["output_contract"] = args.output_contract
    payload["patch"] = {
        "received": True,
        "response_sha256": sha256_text(model_text),
        "response_content_recorded": False,
        **patch_result,
    }
    emit_payload(payload, args.summary_output)
    return 0


def main() -> int:
    try:
        return run(sys.argv[1:])
    except Exception as exc:
        exit_code = exc.exit_code if isinstance(exc, ToolError) else 1
        details = exc.details if isinstance(exc, ToolError) else {"exception_type": type(exc).__name__}
        failure_class = classify_failure(str(exc), details if isinstance(details, dict) else {})
        model_call_made = bool(details.get("model_call_made", details.get("network_attempted", False)))
        payload = {
            "tool": TOOL,
            "status": "error",
            "error": sanitize_text(str(exc)),
            "details": sanitize_jsonish(details),
            "failure_class": failure_class,
            "model_call_made": model_call_made,
            "llm_env_policy": llm_env_summary(os.environ),
        }
        if "--output-contract" in sys.argv:
            index = sys.argv.index("--output-contract")
            if index + 1 < len(sys.argv):
                payload["output_contract"] = sys.argv[index + 1]
        output_path = None
        if "--summary-output" in sys.argv:
            index = sys.argv.index("--summary-output")
            if index + 1 < len(sys.argv):
                output_path = sys.argv[index + 1]
        emit_payload(payload, output_path, stderr=True)
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
