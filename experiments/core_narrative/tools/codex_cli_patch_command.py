#!/usr/bin/env python3
"""Codex CLI patch-generation command for ACUT adapter execution.

The outer ``acut_patch_adapter.py`` remains responsible for the budget gate,
ledger record, captured-artifact redaction, patch collection, verifier
execution, and normalized handoff. This command only prepares and invokes the
inner ``codex exec`` patch-generation agent.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, git, iso_now, load_manifest
from _llm_budget import (
    REQUIRED_LLM_ENV_VARS,
    assert_safe_command_arguments,
    ensure_no_required_env_values,
    llm_safe_subprocess_env,
    redact_sensitive_text,
    unsafe_text_findings,
)
from barcarolle_patch_command import (
    DEFAULT_MAX_MANIFEST_CHARS,
    DEFAULT_MAX_STATEMENT_CHARS,
    DEFAULT_TASK_PACKAGE,
    concise_acut_summary,
    concise_task_summary,
    load_task_package,
    sanitize_jsonish,
    sanitize_text,
    sha256_text,
    truncate_text,
)
from click_specialist_context import load_click_specialist_context, prompt_injection_evidence


TOOL = "codex_cli_patch_command"
COMMAND_CONTRACT_ID = "codex-cli-patch-command-v1"
PROVIDER_ID = "barcarolle"
PROVIDER_DISPLAY_NAME = "Barcarolle"
PROVIDER_WIRE_API = "responses"
ACTIVE_MODEL_ROUTES = ("openai/gpt-5.4-mini", "openai/gpt-5.5")
CATALOG_BASE_SLUGS = {
    "openai/gpt-5.4-mini": "gpt-5.4-mini",
    "openai/gpt-5.5": "gpt-5.5",
}
MODEL_DISPLAY_NAMES = {
    "openai/gpt-5.4-mini": "OpenAI GPT-5.4 Mini via Barcarolle",
    "openai/gpt-5.5": "OpenAI GPT-5.5 via Barcarolle",
}
DEFAULT_CODEX_TIMEOUT_SECONDS = 3600
DEFAULT_FAILURE_CAPTURE_TAIL_CHARS = 2000
RESPONSES_STREAMING_DISCONNECT_CLASS = "responses_streaming_disconnect"
HOSTNAME_LABEL_RE = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
NETWORK_HOSTNAME_RE = re.compile(
    rf"(?<![A-Za-z0-9_.-])(?:{HOSTNAME_LABEL_RE}\.)+"
    rf"(?=[A-Za-z0-9-]*[A-Za-z]){HOSTNAME_LABEL_RE}\.?"
    rf"(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,}[0-9A-Fa-f]{1,4}\b")
LOCALHOST_RE = re.compile(r"\blocalhost\b", re.IGNORECASE)
RESPONSES_STREAM_DISCONNECT_RE = re.compile(r"\bstream disconnected before completion\b", re.IGNORECASE)
RESPONSES_ENDPOINT_PATH_RE = re.compile(r"/responses\b", re.IGNORECASE)
CODEX_RECONNECT_RE = re.compile(r"\bReconnecting\.\.\.\s+(\d+)\s*/\s*(\d+)\b", re.IGNORECASE)

NON_INTERACTIVE_BASE_INSTRUCTIONS = "\n".join(
    [
        "You are running as a non-interactive ACUT patch-generation agent.",
        "Complete the task using tools; do not stop at a progress-only final answer such as 'I will modify'.",
        "Inspect the repository, make the necessary file edits, and verify changed files before finishing.",
        "Keep the final answer brief and do not include credentials, endpoint values, authorization secrets, or full URLs.",
    ]
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a task prompt and run Codex CLI as the inner ACUT "
            "patch-generation agent. Credential values and endpoint URLs are "
            "read only from BARCAROLLE_LLM_API_KEY and BARCAROLLE_LLM_BASE_URL."
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
    parser.add_argument("--model", help="Provider-prefixed model route. Defaults to the ACUT manifest model.")
    parser.add_argument(
        "--artifact-dir",
        help=(
            "Directory for inner Codex CLI artifacts. Defaults to "
            ".core_narrative/codex_cli_patch_command under --workspace."
        ),
    )
    parser.add_argument("--summary-output", help="Optional redacted machine-readable summary JSON path.")
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable name or path.")
    parser.add_argument("--dry-run", "--no-model", action="store_true", help="Construct artifacts without a model call.")
    parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=DEFAULT_CODEX_TIMEOUT_SECONDS,
        help="Timeout for the inner codex exec process.",
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
    return parser.parse_args(list(argv))


def resolve_workspace(path: str) -> Path:
    workspace = Path(path).resolve()
    result = git("rev-parse", "--is-inside-work-tree", cwd=workspace)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ToolError("workspace is not a git work tree", workspace=str(workspace))
    return workspace


def ensure_positive_int(value: int, name: str) -> None:
    if value < 1:
        raise ToolError(f"{name} must be at least 1")


def resolve_artifact_dir(workspace: Path, raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).resolve()
    return (workspace / ".core_narrative" / "codex_cli_patch_command").resolve()


def resolve_model(acut: Mapping[str, Any], requested_model: str | None) -> str:
    model = requested_model if requested_model is not None else acut.get("model")
    if not isinstance(model, str) or not model:
        raise ToolError("ACUT manifest is missing model")
    if model not in ACTIVE_MODEL_ROUTES:
        raise ToolError(
            "model route is not supported by the temporary Codex CLI catalog",
            model=model,
            supported_models=list(ACTIVE_MODEL_ROUTES),
        )
    return model


def toml_string(value: str) -> str:
    return json.dumps(value)


def write_project_trust_config(codex_home: Path, workspace: Path) -> Path:
    codex_home.mkdir(parents=True, exist_ok=True)
    config_path = codex_home / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                f"[projects.{toml_string(str(workspace))}]",
                'trust_level = "trusted"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def run_codex_debug_models(codex_bin: str, codex_home: Path, env: Mapping[str, str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [codex_bin, "debug", "models", "--bundled"],
            cwd=str(codex_home),
            env={**dict(env), "CODEX_HOME": str(codex_home)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError("codex executable was not found", executable=codex_bin) from exc
    if completed.returncode != 0:
        raise ToolError(
            "failed to read bundled Codex model catalog",
            exit_code=completed.returncode,
            stderr=redact_sensitive_text(completed.stderr, env).strip(),
        )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError("bundled Codex model catalog was not valid JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise ToolError("bundled Codex model catalog has unexpected shape")
    return data


def write_model_catalog(codex_bin: str, codex_home: Path, catalog_path: Path, env: Mapping[str, str]) -> Path:
    bundled = run_codex_debug_models(codex_bin, codex_home, env)
    bundled_by_slug = {
        item.get("slug"): item
        for item in bundled["models"]
        if isinstance(item, dict) and isinstance(item.get("slug"), str)
    }
    models: list[dict[str, Any]] = []
    for route in ACTIVE_MODEL_ROUTES:
        base_slug = CATALOG_BASE_SLUGS[route]
        base = bundled_by_slug.get(base_slug)
        if not isinstance(base, dict):
            raise ToolError("bundled Codex model catalog is missing required base model", model=base_slug)
        entry = dict(base)
        entry["slug"] = route
        entry["display_name"] = MODEL_DISPLAY_NAMES[route]
        entry["base_instructions"] = NON_INTERACTIVE_BASE_INSTRUCTIONS
        entry["shell_type"] = entry.get("shell_type") or "shell_command"
        entry["apply_patch_tool_type"] = entry.get("apply_patch_tool_type") or "freeform"
        # Keep the temporary catalog compact and free of bundled prose that can
        # contain unrelated URL-like examples. The shell/edit metadata above is
        # the part we need to inherit for the ACUT command path.
        entry.pop("model_messages", None)
        entry.pop("availability_nux", None)
        entry.pop("upgrade", None)
        safe_entry = sanitize_jsonish(entry)
        if not isinstance(safe_entry, dict):
            raise ToolError("sanitized Codex model catalog entry has unexpected shape", model=route)
        models.append(safe_entry)

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps({"models": models}, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return catalog_path


def build_prompt(
    *,
    task: Mapping[str, Any],
    statement: str,
    acut: Mapping[str, Any],
    click_specialist_context: str,
    max_manifest_chars: int,
) -> tuple[str, bool]:
    acut_json = json.dumps(concise_acut_summary(acut), indent=2, sort_keys=True)
    acut_json, manifest_truncated = truncate_text(acut_json, max_manifest_chars)
    task_json = json.dumps(concise_task_summary(task), indent=2, sort_keys=True)
    sections = [
        "You are generating a minimal repository patch for one prepared ACUT task.",
        "",
        "Work only in the prepared git workspace. Use shell and edit tools as needed.",
        "Use only the visible task package, public statement, and ACUT policy below.",
        "Do not use future history, reference patches, private benchmark artifacts, ACUT outputs, or public model results.",
        "Do not expose credentials, endpoint values, authorization secrets, or full URLs in edits, stdout, stderr, or the final answer.",
        "Leave the repository changes in the workspace; the outer adapter will collect the git diff.",
        "Before finishing, inspect changed files and run focused verification when it is feasible within the ACUT policy.",
        "Keep the final answer brief.",
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
    if click_specialist_context:
        sections.extend(
            [
                "",
                "Task-agnostic Click specialist context:",
                click_specialist_context,
            ]
        )
    prompt = "\n".join(sections)
    return sanitize_text(prompt), manifest_truncated


def require_live_env(env: Mapping[str, str]) -> str:
    missing = [name for name in REQUIRED_LLM_ENV_VARS if not env.get(name)]
    if missing:
        raise ToolError("missing required LLM environment", missing_env=missing, network_attempted=False)
    return env["BARCAROLLE_LLM_BASE_URL"]


def provider_config(endpoint: str) -> str:
    return (
        f"model_providers.{PROVIDER_ID}="
        "{"
        f"name={toml_string(PROVIDER_DISPLAY_NAME)}, "
        f"base_url={toml_string(endpoint)}, "
        'env_key="BARCAROLLE_LLM_API_KEY", '
        f"wire_api={toml_string(PROVIDER_WIRE_API)}"
        "}"
    )


def display_provider_config() -> str:
    return (
        f"model_providers.{PROVIDER_ID}="
        "{"
        f"name={toml_string(PROVIDER_DISPLAY_NAME)}, "
        'base_url="<from BARCAROLLE_LLM_BASE_URL at runtime>", '
        'env_key="BARCAROLLE_LLM_API_KEY", '
        f"wire_api={toml_string(PROVIDER_WIRE_API)}"
        "}"
    )


def build_codex_command(
    *,
    codex_bin: str,
    workspace: Path,
    model: str,
    model_catalog_path: Path,
    final_output_path: Path,
    endpoint: str,
) -> list[str]:
    return [
        codex_bin,
        "-a",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--full-auto",
        "--cd",
        str(workspace),
        "--model",
        model,
        "-c",
        f'model_provider="{PROVIDER_ID}"',
        "-c",
        provider_config(endpoint),
        "-c",
        f"model_catalog_json={toml_string(str(model_catalog_path))}",
        "-o",
        str(final_output_path),
        "-",
    ]


def build_display_command(
    *,
    codex_bin: str,
    workspace: Path,
    model: str,
    model_catalog_path: Path,
    final_output_path: Path,
) -> list[str]:
    return [
        codex_bin,
        "-a",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--full-auto",
        "--cd",
        str(workspace),
        "--model",
        model,
        "-c",
        f'model_provider="{PROVIDER_ID}"',
        "-c",
        display_provider_config(),
        "-c",
        f"model_catalog_json={toml_string(str(model_catalog_path))}",
        "-o",
        str(final_output_path),
        "-",
    ]


def env_summary(env: Mapping[str, str]) -> dict[str, Any]:
    return {
        "allowed_variable_names": list(REQUIRED_LLM_ENV_VARS),
        "required_present": {name: bool(env.get(name)) for name in REQUIRED_LLM_ENV_VARS},
        "values_recorded": False,
        "endpoint_value_recorded": False,
        "command_arguments_checked": True,
        "unsafe_command_arguments_rejected": True,
    }


def redact_failure_capture_text(text: str | bytes | None, env: Mapping[str, str]) -> str:
    """Redact snippets and artifacts more strictly than normal command output."""
    redacted = redact_sensitive_text(text, env)
    redacted = IPV4_RE.sub("<redacted:ip-address>", redacted)
    redacted = IPV6_RE.sub("<redacted:ip-address>", redacted)
    redacted = NETWORK_HOSTNAME_RE.sub("<redacted:hostname>", redacted)
    redacted = LOCALHOST_RE.sub("<redacted:hostname>", redacted)
    return redacted


def tail_text(text: str, max_chars: int = DEFAULT_FAILURE_CAPTURE_TAIL_CHARS) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[-max_chars:], True


def iter_codex_exec_error_messages(text: str) -> list[str]:
    messages: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            messages.append(line)
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message")
        if isinstance(message, str):
            messages.append(message)
        error = event.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            messages.append(str(error["message"]))
    return messages


def detect_responses_streaming_disconnect(stdout: str, stderr: str) -> dict[str, Any]:
    stdout_messages = iter_codex_exec_error_messages(stdout)
    stderr_messages = iter_codex_exec_error_messages(stderr)
    combined = "\n".join([*stdout_messages, *stderr_messages])
    stream_disconnect = bool(RESPONSES_STREAM_DISCONNECT_RE.search(combined))
    responses_endpoint = bool(RESPONSES_ENDPOINT_PATH_RE.search(combined))
    reconnect_matches = [
        (int(match.group(1)), int(match.group(2)))
        for match in CODEX_RECONNECT_RE.finditer(combined)
    ]
    max_reconnect = max((attempt for attempt, _limit in reconnect_matches), default=None)
    reconnect_limit = max((limit for _attempt, limit in reconnect_matches), default=None)
    retry_exhausted = bool(
        max_reconnect is not None
        and reconnect_limit is not None
        and max_reconnect >= reconnect_limit
    )
    present = stream_disconnect and responses_endpoint
    return {
        "present": present,
        "failure_class": RESPONSES_STREAMING_DISCONNECT_CLASS if present else None,
        "wire_api": PROVIDER_WIRE_API if present else None,
        "endpoint_path": "/responses" if present else None,
        "after_reconnects": max_reconnect,
        "reconnect_limit": reconnect_limit,
        "retry_exhausted": retry_exhausted,
        "matched_stdout": bool(stdout_messages and RESPONSES_STREAM_DISCONNECT_RE.search("\n".join(stdout_messages))),
        "matched_stderr": bool(stderr_messages and RESPONSES_STREAM_DISCONNECT_RE.search("\n".join(stderr_messages))),
        "messages_recorded": False,
        "content_recorded": False,
        "redaction_applied_before_detection": True,
    }


def inspect_workspace_patch_state(workspace: Path, env: Mapping[str, str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "diff", "--binary", "--no-ext-diff", "HEAD"],
            cwd=str(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {
            "checked": False,
            "usable_patch": False,
            "failure_class": "git_executable_not_found",
            "content_recorded": False,
        }
    if completed.returncode != 0:
        stderr = redact_failure_capture_text(completed.stderr, env).strip()
        stderr_tail, stderr_truncated = tail_text(stderr)
        return {
            "checked": False,
            "usable_patch": False,
            "failure_class": "git_diff_failed",
            "exit_code": completed.returncode,
            "stderr_tail": stderr_tail,
            "stderr_tail_truncated": stderr_truncated,
            "content_recorded": False,
        }

    patch_text = completed.stdout
    findings = unsafe_text_findings(patch_text, env)
    size_bytes = len(patch_text.encode("utf-8"))
    unsafe_content_detected = bool(findings["unsafe"])
    return {
        "checked": True,
        "collection_command": ["git", "diff", "--binary", "--no-ext-diff", "HEAD"],
        "matches_outer_adapter_patch_scope": True,
        "untracked_files_ignored": True,
        "size_bytes": size_bytes,
        "has_patch": size_bytes > 0,
        "unsafe_content_detected": unsafe_content_detected,
        "unsafe_content": findings,
        "usable_patch": size_bytes > 0 and not unsafe_content_detected,
        "content_recorded": False,
    }


def classify_failure(run: Mapping[str, Any], workspace_patch: Mapping[str, Any]) -> str | None:
    if run.get("timed_out"):
        return "timeout"
    transport_failure = run.get("transport_failure")
    if isinstance(transport_failure, Mapping) and transport_failure.get("present"):
        failure_class = transport_failure.get("failure_class")
        if isinstance(failure_class, str) and failure_class:
            return failure_class
    exit_code = run.get("exit_code")
    if exit_code not in (0, None):
        return "nonzero_exit"
    if not workspace_patch.get("checked"):
        return str(workspace_patch.get("failure_class") or "patch_state_unavailable")
    if workspace_patch.get("unsafe_content_detected"):
        return "unsafe_patch_content"
    if not workspace_patch.get("usable_patch"):
        return "no_workspace_patch"
    return None


def build_failure_capture(
    *,
    run: Mapping[str, Any],
    failure_class: str | None,
    timeout_seconds: int,
    workspace_patch: Mapping[str, Any],
) -> dict[str, Any]:
    present = failure_class is not None
    transport_failure = run.get("transport_failure")
    return {
        "present": present,
        "failure_class": failure_class,
        "transport_failure": transport_failure if isinstance(transport_failure, Mapping) else {"present": False},
        "exit_code": run.get("exit_code"),
        "timed_out": bool(run.get("timed_out")),
        "duration_seconds": run.get("duration_seconds"),
        "timeout_seconds": timeout_seconds,
        "stdout_artifact": run.get("stdout_artifact"),
        "stderr_artifact": run.get("stderr_artifact"),
        "stdout_tail": run.get("stdout_tail") if present else "",
        "stderr_tail": run.get("stderr_tail") if present else "",
        "stdout_tail_truncated": bool(run.get("stdout_tail_truncated")) if present else False,
        "stderr_tail_truncated": bool(run.get("stderr_tail_truncated")) if present else False,
        "stdout_bytes": run.get("stdout_bytes"),
        "stderr_bytes": run.get("stderr_bytes"),
        "workspace_patch_checked": bool(workspace_patch.get("checked")),
        "workspace_patch_usable": bool(workspace_patch.get("usable_patch")),
        "workspace_patch_size_bytes": workspace_patch.get("size_bytes"),
        "redaction_policy": {
            "credential_values_redacted": True,
            "bearer_tokens_redacted": True,
            "resolved_required_env_values_redacted": True,
            "full_urls_redacted": True,
            "hostnames_redacted": True,
            "ip_addresses_redacted": True,
            "tail_max_chars": DEFAULT_FAILURE_CAPTURE_TAIL_CHARS,
        },
        "cli_log_required_for_review": False,
        "cli_log_inspected": False,
    }


def payload_base(
    *,
    status: str,
    mode: str,
    workspace: Path,
    artifact_dir: Path,
    codex_home: Path,
    config_path: Path,
    model_catalog_path: Path,
    final_output_path: Path,
    command: Sequence[str],
    task: Mapping[str, Any],
    acut: Mapping[str, Any],
    model: str,
    prompt: str,
    context_pack_evidence: Mapping[str, Any],
    statement_path: Path | None,
    statement_truncated: bool,
    manifest_truncated: bool,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tool": TOOL,
        "command_contract_id": COMMAND_CONTRACT_ID,
        "status": status,
        "mode": mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "model_call_made": mode == "live",
        "workspace": str(workspace),
        "artifact_dir": str(artifact_dir),
        "task_id": task.get("task_id"),
        "split": task.get("split"),
        "acut_id": acut.get("acut_id"),
        "provider": acut.get("provider"),
        "model": model,
        "statement_path": None if statement_path is None else str(statement_path),
        "prompt": {
            "prepared": True,
            "sha256": sha256_text(prompt),
            "char_count": len(prompt),
            "content_recorded": False,
            "full_urls_redacted": True,
            "statement_truncated": statement_truncated,
            "manifest_truncated": manifest_truncated,
        },
        "specialist_context_pack": context_pack_evidence,
        "codex_home": {
            "path": str(codex_home),
            "temporary_run_local": True,
            "config_path": str(config_path),
            "project_trust_configured": True,
            "trusted_workspace": str(workspace),
            "real_user_profile_written": False,
        },
        "model_catalog": {
            "path": str(model_catalog_path),
            "routes": list(ACTIVE_MODEL_ROUTES),
            "provider_prefixed_routes": True,
            "shell_tool_enabled": True,
            "edit_tool_enabled": True,
            "non_interactive_base_instructions": True,
            "content_safe_for_artifact": True,
        },
        "provider_override": {
            "provider_id": PROVIDER_ID,
            "wire_api": PROVIDER_WIRE_API,
            "endpoint_source_env": "BARCAROLLE_LLM_BASE_URL",
            "endpoint_value_recorded": False,
            "credential_env_key": "BARCAROLLE_LLM_API_KEY",
            "credential_value_recorded": False,
            "catalog_refresh_warnings_nonfatal": True,
        },
        "llm_env_policy": env_summary(os.environ),
        "codex_exec": {
            "command": list(command),
            "prompt_passed_via_stdin": True,
            "command_contains_prompt": False,
            "command_contains_endpoint_value": False,
            "command_contains_credential_value": False,
            "final_output_path": str(final_output_path),
        },
    }
    if extra:
        payload.update(extra)
    return sanitize_jsonish(payload)


def write_summary(path: str | None, payload: Mapping[str, Any]) -> None:
    text = sanitize_text(json.dumps(payload, indent=2, sort_keys=True))
    if path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


def run_codex_exec(
    *,
    command: Sequence[str],
    prompt: str,
    workspace: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(workspace),
            env=dict(env),
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        safe_stdout = redact_failure_capture_text(completed.stdout, env)
        safe_stderr = redact_failure_capture_text(completed.stderr, env)
        transport_failure = detect_responses_streaming_disconnect(safe_stdout, safe_stderr)
        stdout_path.write_text(safe_stdout, encoding="utf-8")
        stderr_path.write_text(safe_stderr, encoding="utf-8")
        if safe_stdout:
            print(safe_stdout, end="")
        if safe_stderr:
            print(safe_stderr, file=sys.stderr, end="")
        stdout_tail, stdout_truncated = tail_text(safe_stdout)
        stderr_tail, stderr_truncated = tail_text(safe_stderr)
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_artifact": str(stdout_path),
            "stderr_artifact": str(stderr_path),
            "stdout_bytes": len(safe_stdout.encode("utf-8")),
            "stderr_bytes": len(safe_stderr.encode("utf-8")),
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "stdout_tail_truncated": stdout_truncated,
            "stderr_tail_truncated": stderr_truncated,
            "transport_failure": transport_failure,
        }
    except subprocess.TimeoutExpired as exc:
        safe_stdout = redact_failure_capture_text(exc.stdout, env)
        safe_stderr = redact_failure_capture_text(exc.stderr, env)
        transport_failure = detect_responses_streaming_disconnect(safe_stdout, safe_stderr)
        stdout_path.write_text(safe_stdout, encoding="utf-8")
        stderr_path.write_text(safe_stderr, encoding="utf-8")
        if safe_stdout:
            print(safe_stdout, end="")
        if safe_stderr:
            print(safe_stderr, file=sys.stderr, end="")
        stdout_tail, stdout_truncated = tail_text(safe_stdout)
        stderr_tail, stderr_truncated = tail_text(safe_stderr)
        return {
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_artifact": str(stdout_path),
            "stderr_artifact": str(stderr_path),
            "stdout_bytes": len(safe_stdout.encode("utf-8")),
            "stderr_bytes": len(safe_stderr.encode("utf-8")),
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "stdout_tail_truncated": stdout_truncated,
            "stderr_tail_truncated": stderr_truncated,
            "transport_failure": transport_failure,
        }
    except FileNotFoundError as exc:
        raise ToolError("codex executable was not found", executable=command[0]) from exc


def run(argv: Sequence[str]) -> int:
    assert_safe_command_arguments(argv, os.environ)
    ensure_no_required_env_values(argv, os.environ)
    args = parse_args(argv)
    ensure_positive_int(args.codex_timeout_seconds, "--codex-timeout-seconds")
    ensure_positive_int(args.max_statement_chars, "--max-statement-chars")
    ensure_positive_int(args.max_manifest_chars, "--max-manifest-chars")

    workspace = resolve_workspace(args.workspace)
    artifact_dir = resolve_artifact_dir(workspace, args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    codex_home = Path(tempfile.mkdtemp(prefix="codex_home_", dir=str(artifact_dir)))
    config_path = write_project_trust_config(codex_home, workspace)
    model_catalog_path = codex_home / "model_catalog.json"
    final_output_path = artifact_dir / "codex_final.txt"

    acut = sanitize_jsonish(load_manifest(args.acut))
    if not isinstance(acut, dict):
        raise ToolError("ACUT manifest root must be an object")
    if "acut_id" not in acut:
        raise ToolError("ACUT manifest is missing required fields", missing=["acut_id"])
    model = resolve_model(acut, args.model)
    context_text, context_evidence = load_click_specialist_context(acut, args.acut)

    acut_env, scrubbed_env_var_count = llm_safe_subprocess_env(os.environ)
    write_model_catalog(args.codex_bin, codex_home, model_catalog_path, acut_env)
    _, task, statement_path, statement, statement_truncated = load_task_package(workspace, args)
    prompt, manifest_truncated = build_prompt(
        task=task,
        statement=statement,
        acut=acut,
        click_specialist_context=context_text,
        max_manifest_chars=args.max_manifest_chars,
    )
    context_pack_evidence = prompt_injection_evidence(prompt, context_evidence)
    display_command = build_display_command(
        codex_bin=args.codex_bin,
        workspace=workspace,
        model=model,
        model_catalog_path=model_catalog_path,
        final_output_path=final_output_path,
    )

    started_at = iso_now()
    if args.dry_run:
        finished_at = iso_now()
        payload = payload_base(
            status="dry_run_completed",
            mode="dry_run",
            workspace=workspace,
            artifact_dir=artifact_dir,
            codex_home=codex_home,
            config_path=config_path,
            model_catalog_path=model_catalog_path,
            final_output_path=final_output_path,
            command=display_command,
            task=task,
            acut=acut,
            model=model,
            prompt=prompt,
            context_pack_evidence=context_pack_evidence,
            statement_path=statement_path,
            statement_truncated=statement_truncated,
            manifest_truncated=manifest_truncated,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=0,
            extra={
                "model_call_made": False,
                "codex_exec": {
                    "command": display_command,
                    "prompt_passed_via_stdin": True,
                    "command_contains_prompt": False,
                    "command_contains_endpoint_value": False,
                    "command_contains_credential_value": False,
                    "final_output_path": str(final_output_path),
                    "executed": False,
                },
                "scrubbed_env_var_count": scrubbed_env_var_count,
            },
        )
        write_summary(args.summary_output, payload)
        return 0

    endpoint = require_live_env(os.environ)
    command = build_codex_command(
        codex_bin=args.codex_bin,
        workspace=workspace,
        model=model,
        model_catalog_path=model_catalog_path,
        final_output_path=final_output_path,
        endpoint=endpoint,
    )
    codex_env = {**acut_env, "CODEX_HOME": str(codex_home)}
    stdout_path = artifact_dir / "codex_exec.stdout.txt"
    stderr_path = artifact_dir / "codex_exec.stderr.txt"
    run = run_codex_exec(
        command=command,
        prompt=prompt,
        workspace=workspace,
        env=codex_env,
        timeout_seconds=args.codex_timeout_seconds,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    workspace_patch = inspect_workspace_patch_state(workspace, codex_env)
    failure_class = classify_failure(run, workspace_patch)
    finished_at = iso_now()
    if run["timed_out"]:
        status = "timeout"
    elif run["exit_code"] == 0:
        status = "codex_exec_completed"
    else:
        status = "codex_exec_failed"

    payload = payload_base(
        status=status,
        mode="live",
        workspace=workspace,
        artifact_dir=artifact_dir,
        codex_home=codex_home,
        config_path=config_path,
        model_catalog_path=model_catalog_path,
        final_output_path=final_output_path,
        command=display_command,
        task=task,
        acut=acut,
        model=model,
        prompt=prompt,
        context_pack_evidence=context_pack_evidence,
        statement_path=statement_path,
        statement_truncated=statement_truncated,
        manifest_truncated=manifest_truncated,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=float(run["duration_seconds"]),
        extra={
            "model_call_made": True,
            "codex_exec": {
                "command": display_command,
                "prompt_passed_via_stdin": True,
                "command_contains_prompt": False,
                "command_contains_endpoint_value": False,
                "command_contains_credential_value": False,
                "final_output_path": str(final_output_path),
                "executed": True,
                "exit_code": run["exit_code"],
                "timed_out": run["timed_out"],
                "duration_seconds": run["duration_seconds"],
                "stdout_artifact": run["stdout_artifact"],
                "stderr_artifact": run["stderr_artifact"],
                "stdout_bytes": run["stdout_bytes"],
                "stderr_bytes": run["stderr_bytes"],
                "stdout_tail_recorded": failure_class is not None,
                "stderr_tail_recorded": failure_class is not None,
            },
            "workspace_patch": workspace_patch,
            "transport_failure": run.get("transport_failure", {"present": False}),
            "failure_capture": build_failure_capture(
                run=run,
                failure_class=failure_class,
                timeout_seconds=args.codex_timeout_seconds,
                workspace_patch=workspace_patch,
            ),
            "scrubbed_env_var_count": scrubbed_env_var_count,
        },
    )
    write_summary(args.summary_output, payload)
    if run["timed_out"]:
        return 124
    return int(run["exit_code"])


def main() -> int:
    try:
        return run(sys.argv[1:])
    except Exception as exc:
        exit_code = exc.exit_code if isinstance(exc, ToolError) else 1
        details = exc.details if isinstance(exc, ToolError) else {"exception_type": type(exc).__name__}
        payload = sanitize_jsonish(
            {
                "tool": TOOL,
                "command_contract_id": COMMAND_CONTRACT_ID,
                "status": "error",
                "error": sanitize_text(str(exc)),
                "details": details,
                "model_call_made": False,
                "llm_env_policy": env_summary(os.environ),
            }
        )
        output_path = None
        if "--summary-output" in sys.argv:
            index = sys.argv.index("--summary-output")
            if index + 1 < len(sys.argv):
                output_path = sys.argv[index + 1]
        write_summary(output_path, payload)
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
