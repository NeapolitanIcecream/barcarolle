#!/usr/bin/env python3
"""Secret-safe LLM access and budget helpers for core narrative tools."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError


REQUIRED_LLM_ENV_VARS = ("BARCAROLLE_LLM_API_KEY", "BARCAROLLE_LLM_BASE_URL")
DEFAULT_LEDGER_PATH = Path("experiments/core_narrative/results/cost_ledger.jsonl")
DEFAULT_SOFT_STOP_USD = Decimal("240")
DEFAULT_HARD_CAP_USD = Decimal("300")
MONEY_QUANT = Decimal("0.000001")

CORE_ACUT_IDS = (
    "general-benchmark-optimized",
    "repo-context-heavy",
    "retrieval-sparse-symbolic",
    "lower-budget-fast-path",
)
DEFAULT_SPLIT_TASK_LIMITS = {
    "G_score": 6,
    "RBench": 8,
    "RWork": 6,
}
DEFAULT_EXECUTION_PROFILE = {
    "profile_id": "budget-constrained-core-v1",
    "core_acut_ids": list(CORE_ACUT_IDS),
    "split_task_limits": DEFAULT_SPLIT_TASK_LIMITS,
    "primary_attempts_per_acut_task": 1,
}

SECRET_FIELD_RE = re.compile(
    r"(^|[_\-.])("
    r"api[-_]?key|secret|password|authorization|auth[-_]?header|bearer|"
    r"credential|access[-_]?token|refresh[-_]?token|session[-_]?token|id[-_]?token|"
    r"base[-_]?url|resolved[-_]?url"
    r")([_\-.]|$)",
    re.IGNORECASE,
)
URL_VALUE_RE = re.compile(r"https?://", re.IGNORECASE)
SECRET_VALUE_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9._-]{8,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
]
PROVIDER_ENV_MARKERS = (
    "OPENAI",
    "ANTHROPIC",
    "GEMINI",
    "GOOGLE_API",
    "MISTRAL",
    "COHERE",
    "TOGETHER",
    "FIREWORKS",
    "GROQ",
    "OPENROUTER",
    "VOYAGE",
)


def parse_usd(value: Any, name: str) -> Decimal:
    if value is None:
        raise ToolError(f"{name} is required")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ToolError(f"{name} must be a decimal USD amount", value_type=type(value).__name__) from exc
    if not amount.is_finite():
        raise ToolError(f"{name} must be finite")
    if amount < 0:
        raise ToolError(f"{name} must be non-negative")
    return amount


def parse_non_negative_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ToolError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise ToolError(f"{name} must be non-negative")
    return parsed


def money_json(value: Decimal) -> float:
    return float(value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP))


def env_presence(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = os.environ if env is None else env
    required = [{"name": name, "present": bool(source.get(name))} for name in REQUIRED_LLM_ENV_VARS]
    return {
        "required": required,
        "all_required_present": all(item["present"] for item in required),
    }


def _safe_record_count(line_count: int, record_count: int) -> dict[str, int]:
    return {
        "line_count": line_count,
        "record_count": record_count,
    }


def ledger_access(path: Path) -> dict[str, Any]:
    exists = path.exists()
    is_file = path.is_file() if exists else False
    writable = False
    error = None
    if exists and is_file:
        try:
            with path.open("r+", encoding="utf-8"):
                writable = True
        except OSError as exc:
            error = type(exc).__name__
    return {
        "path": str(path),
        "exists": exists,
        "is_file": is_file,
        "writable": writable,
        "error_type": error,
    }


def read_ledger_summary(path: Path) -> dict[str, Any]:
    access = ledger_access(path)
    if not access["exists"]:
        return {
            **access,
            **_safe_record_count(0, 0),
            "cumulative_estimated_cost_usd": 0.0,
            "estimated_cost_sum_usd": 0.0,
            "errors": ["ledger_missing"],
        }
    if not access["is_file"]:
        return {
            **access,
            **_safe_record_count(0, 0),
            "cumulative_estimated_cost_usd": 0.0,
            "estimated_cost_sum_usd": 0.0,
            "errors": ["ledger_path_is_not_file"],
        }

    errors: list[str] = []
    estimated_sum = Decimal("0")
    last_cumulative: Decimal | None = None
    record_count = 0
    line_count = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {
            **access,
            **_safe_record_count(0, 0),
            "cumulative_estimated_cost_usd": 0.0,
            "estimated_cost_sum_usd": 0.0,
            "errors": [f"ledger_read_failed:{type(exc).__name__}"],
        }

    for line_number, line in enumerate(lines, start=1):
        line_count += 1
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line_{line_number}:invalid_json")
            continue
        if not isinstance(record, dict):
            errors.append(f"line_{line_number}:record_not_object")
            continue
        record_count += 1
        try:
            estimated_sum += parse_usd(record.get("estimated_cost_usd", "0"), "estimated_cost_usd")
        except ToolError:
            errors.append(f"line_{line_number}:invalid_estimated_cost_usd")
        if "cumulative_estimated_cost_usd" in record:
            try:
                last_cumulative = parse_usd(
                    record["cumulative_estimated_cost_usd"],
                    "cumulative_estimated_cost_usd",
                )
            except ToolError:
                errors.append(f"line_{line_number}:invalid_cumulative_estimated_cost_usd")

    cumulative = last_cumulative if last_cumulative is not None else estimated_sum
    return {
        **access,
        **_safe_record_count(line_count, record_count),
        "cumulative_estimated_cost_usd": money_json(cumulative),
        "estimated_cost_sum_usd": money_json(estimated_sum),
        "errors": errors,
    }


def ledger_cumulative_decimal(summary: Mapping[str, Any]) -> Decimal:
    return parse_usd(summary.get("cumulative_estimated_cost_usd", 0), "cumulative_estimated_cost_usd")


def gate_payload(
    *,
    ledger_path: Path,
    projected_cost_usd: Decimal,
    soft_stop_usd: Decimal = DEFAULT_SOFT_STOP_USD,
    hard_cap_usd: Decimal = DEFAULT_HARD_CAP_USD,
    coordinator_decision_ref: str | None = None,
    acut_id: str | None = None,
    split: str | None = None,
    attempt: int | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env_summary = env_presence(env)
    ledger = read_ledger_summary(ledger_path)
    current = ledger_cumulative_decimal(ledger)
    projected_cumulative = current + projected_cost_usd
    hard_stop = current >= hard_cap_usd or projected_cumulative >= hard_cap_usd
    soft_stop = current >= soft_stop_usd or projected_cumulative >= soft_stop_usd

    blockers: list[str] = []
    approvals_required: list[str] = []
    if not env_summary["all_required_present"]:
        blockers.append("missing_required_llm_environment")
    if not ledger["exists"]:
        blockers.append("cost_ledger_missing")
    elif not ledger["is_file"]:
        blockers.append("cost_ledger_not_file")
    elif not ledger["writable"]:
        blockers.append("cost_ledger_unwritable")
    if ledger["errors"] and ledger["exists"] and ledger["is_file"]:
        blockers.append("cost_ledger_unreadable")
    if hard_stop:
        blockers.append("hard_cap_reached_or_projected")

    if soft_stop:
        approvals_required.append("soft_stop_reached_or_projected")
    if acut_id is not None and acut_id not in CORE_ACUT_IDS:
        approvals_required.append("non_core_acut")
    if attempt is not None and attempt != 1:
        approvals_required.append("non_primary_attempt")

    approval_recorded = bool(coordinator_decision_ref)
    if coordinator_decision_ref:
        _assert_safe_value(coordinator_decision_ref, "$.coordinator_decision_ref")

    if blockers:
        status = "blocked"
    elif approvals_required and not approval_recorded:
        status = "requires_coordinator_approval"
    else:
        status = "passed"

    return {
        "tool": "llm_budget_gate",
        "status": status,
        "allowed": status == "passed",
        "env": env_summary,
        "ledger": ledger,
        "budget": {
            "projected_cost_usd": money_json(projected_cost_usd),
            "current_cumulative_estimated_cost_usd": money_json(current),
            "projected_cumulative_estimated_cost_usd": money_json(projected_cumulative),
            "soft_stop_usd": money_json(soft_stop_usd),
            "hard_cap_usd": money_json(hard_cap_usd),
            "soft_stop_reached_or_projected": soft_stop,
            "hard_cap_reached_or_projected": hard_stop,
        },
        "default_execution_profile": DEFAULT_EXECUTION_PROFILE,
        "execution_request": {
            "acut_id": acut_id,
            "split": split,
            "attempt": attempt,
            "coordinator_decision_ref_present": approval_recorded,
        },
        "blockers": blockers,
        "approvals_required": approvals_required,
    }


def gate_exit_code(payload: Mapping[str, Any]) -> int:
    if payload["status"] == "passed":
        return 0
    if payload["status"] == "requires_coordinator_approval":
        return 3
    return 2


def is_disallowed_env_name(name: str) -> bool:
    if name in REQUIRED_LLM_ENV_VARS:
        return False
    upper = name.upper()
    if SECRET_FIELD_RE.search(name):
        return True
    return any(marker in upper for marker in PROVIDER_ENV_MARKERS) and any(
        part in upper for part in ("KEY", "TOKEN", "SECRET", "BASE_URL", "API")
    )


def llm_safe_subprocess_env(env: Mapping[str, str]) -> tuple[dict[str, str], int]:
    cleaned: dict[str, str] = {}
    scrubbed_count = 0
    for name, value in env.items():
        if is_disallowed_env_name(name):
            scrubbed_count += 1
            continue
        cleaned[name] = value
    return cleaned, scrubbed_count


def forbidden_value_markers(env: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if env is None else env
    return {name: value for name in REQUIRED_LLM_ENV_VARS if (value := source.get(name))}


def _coerce_output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def redact_sensitive_text(text: str | bytes | None, env: Mapping[str, str] | None = None) -> str:
    text = _coerce_output_text(text)
    redacted = text
    for name, value in forbidden_value_markers(env).items():
        redacted = redacted.replace(value, f"<redacted:{name}>")
    redacted = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer <redacted>", redacted, flags=re.IGNORECASE)
    return redacted


def ensure_no_required_env_values(value: Any, env: Mapping[str, str] | None = None) -> None:
    markers = forbidden_value_markers(env)
    if not markers:
        return
    haystack = json.dumps(value, sort_keys=True)
    leaked = [name for name, marker in markers.items() if marker and marker in haystack]
    if leaked:
        raise ToolError("payload contains resolved LLM environment value", env_var_names=leaked)


def _assert_safe_key(key: str, path_label: str) -> None:
    if SECRET_FIELD_RE.search(key):
        raise ToolError("record contains secret-looking field name", field_path=path_label)


def _assert_safe_value(value: str, path_label: str) -> None:
    if URL_VALUE_RE.search(value):
        raise ToolError("record contains full URL-looking value", field_path=path_label)
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(value):
            raise ToolError("record contains secret-looking value", field_path=path_label)


def assert_no_secret_like_content(value: Any, path_label: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path_label}.{key_text}"
            _assert_safe_key(key_text, item_path)
            assert_no_secret_like_content(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_secret_like_content(item, f"{path_label}[{index}]")
        return
    if isinstance(value, str):
        _assert_safe_value(value, path_label)


def estimate_cost_from_tokens(
    *,
    input_tokens: int,
    output_tokens: int,
    input_rate_usd_per_million: Decimal,
    output_rate_usd_per_million: Decimal,
) -> Decimal:
    input_cost = Decimal(input_tokens) * input_rate_usd_per_million / Decimal(1_000_000)
    output_cost = Decimal(output_tokens) * output_rate_usd_per_million / Decimal(1_000_000)
    return input_cost + output_cost


def require_ledger_appendable(path: Path) -> dict[str, Any]:
    summary = read_ledger_summary(path)
    if not summary["exists"]:
        raise ToolError("cost ledger does not exist", ledger=str(path))
    if not summary["is_file"]:
        raise ToolError("cost ledger path is not a file", ledger=str(path))
    if not summary["writable"]:
        raise ToolError("cost ledger is not writable", ledger=str(path), error_type=summary["error_type"])
    if summary["errors"]:
        raise ToolError("cost ledger has parse errors", ledger=str(path), errors=summary["errors"])
    return summary


def append_ledger_record(path: Path, record: dict[str, Any]) -> None:
    assert_no_secret_like_content(record)
    require_ledger_appendable(path)
    try:
        with path.open("a", encoding="utf-8") as ledger_file:
            ledger_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError as exc:
        raise ToolError("failed to append cost ledger record", ledger=str(path), error_type=type(exc).__name__) from exc


def run_to_redacted_artifacts(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int | None,
    stdout_path: Path,
    stderr_path: Path,
    env: Mapping[str, str],
) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_path.write_text(redact_sensitive_text(completed.stdout, env), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(completed.stderr, env), encoding="utf-8")
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except FileNotFoundError as exc:
        raise ToolError("command executable was not found", executable=command[0]) from exc
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(redact_sensitive_text(exc.stdout, env), encoding="utf-8")
        stderr_path.write_text(redact_sensitive_text(exc.stderr, env), encoding="utf-8")
        return {
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
