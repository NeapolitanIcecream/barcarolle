from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def cost_observation_metadata(usage_observed: bool, billed_cost_usd: float | None = None) -> dict[str, Any]:
    if billed_cost_usd is not None:
        return {
            "cost_observation_kind": "billed_cost",
            "usage_source": "provider_billing_export",
            "billed_cost_usd": billed_cost_usd,
        }
    if usage_observed:
        return {
            "cost_observation_kind": "observed_tokens_estimated_cost",
            "usage_source": "adapter_output_usage_json",
            "billed_cost_usd": None,
        }
    return {
        "cost_observation_kind": "missing_usage_conservative_estimate",
        "usage_source": "missing_adapter_usage",
        "billed_cost_usd": None,
    }


def normalize_cost_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    usage_observed = normalized.get("usage_observed") is True or str(normalized.get("usage_observed")).lower() == "true"
    billed_raw = normalized.get("billed_cost_usd")
    billed_cost = None if billed_raw in {None, ""} else float(billed_raw)
    metadata = cost_observation_metadata(usage_observed, billed_cost_usd=billed_cost)
    if not normalized.get("cost_observation_kind"):
        normalized["cost_observation_kind"] = metadata["cost_observation_kind"]
    if not normalized.get("usage_source"):
        normalized["usage_source"] = metadata["usage_source"]
    if normalized.get("billed_cost_usd") in {None, ""}:
        normalized["billed_cost_usd"] = metadata["billed_cost_usd"]
    return normalized


def raw_file_from_submission(submission: dict[str, Any], key: str, root: Path = ROOT) -> Path | None:
    rel = (submission.get("raw_artifacts") or {}).get(key)
    if not rel:
        return None
    return root / "experiments" / "phase0_headroom" / rel


def find_usage_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if any(key in value for key in ["prompt_tokens", "completion_tokens", "input_tokens", "output_tokens"]):
            return value
        for nested in value.values():
            found = find_usage_object(nested)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_usage_object(item)
            if found:
                return found
    return None


def usage_from_kilo_step_events(text: str) -> dict[str, Any] | None:
    input_tokens = 0
    cached_input_tokens = 0
    output_tokens = 0
    found = False
    for line in text.splitlines():
        line = line.strip()
        if not line or not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parsed.get("type") != "step_finish":
            continue
        tokens = ((parsed.get("part") or {}).get("tokens") if isinstance(parsed.get("part"), dict) else None) or {}
        if not isinstance(tokens, dict):
            continue
        cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
        input_count = int(tokens.get("input") or 0)
        cache_read = int(cache.get("read") or 0)
        output_count = int(tokens.get("output") or 0) + int(tokens.get("reasoning") or 0)
        input_tokens += input_count + cache_read
        cached_input_tokens += cache_read
        output_tokens += output_count
        found = True
    if not found:
        return None
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "usage_source_schema": "kilo_step_finish_tokens",
    }


def extract_usage_from_text(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line or not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        found = find_usage_object(parsed)
        if found:
            return found
    return usage_from_kilo_step_events(text)


def usage_from_submission(submission: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    for key in ["stdout", "stderr"]:
        path = raw_file_from_submission(submission, key, root=root)
        if path and path.exists():
            found = extract_usage_from_text(path.read_text(encoding="utf-8", errors="replace"))
            if found:
                return found
    return None


def estimate_cost(usage: dict[str, Any] | None, model: str, config: dict[str, Any]) -> tuple[bool, float, dict[str, int | None]]:
    if not usage:
        return False, float(config["run_policy"]["conservative_cell_estimate_usd"]), {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
        }
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached = usage.get("cached_input_tokens", details.get("cached_tokens"))
    if input_tokens is None and output_tokens is None:
        return False, float(config["run_policy"]["conservative_cell_estimate_usd"]), {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
        }
    price = config["pricing_per_1m_tokens_usd"].get(model, {})
    input_total = max(int(input_tokens or 0), 0)
    cached_total = max(int(cached or 0), 0)
    uncached_total = max(input_total - cached_total, 0)
    output_total = max(int(output_tokens or 0), 0)
    cost = (
        uncached_total * float(price.get("input", 0.0))
        + cached_total * float(price.get("cached_input", price.get("input", 0.0)))
        + output_total * float(price.get("output", 0.0))
    ) / 1_000_000
    return True, round(cost, 8), {
        "input_tokens": input_total,
        "cached_input_tokens": cached_total,
        "output_tokens": output_total,
    }


def failure_category(verifier: dict[str, Any], submission: dict[str, Any]) -> str:
    status = str(verifier.get("status") or submission.get("status") or "")
    error = str(verifier.get("harness_error") or "")
    if status == "verified_pass":
        return "verified pass"
    if status == "verified_fail":
        return "hidden verifier failure"
    if status == "invalid_output":
        return "no meaningful change"
    if status == "timeout" or submission.get("acut_exit_code") == 124:
        return "exceeded budget or timeout"
    if status == "policy_violation" and "edited_tests" in error:
        return "edited tests when prohibited"
    if status == "policy_violation":
        return "edited prohibited paths"
    if "patch" in error and "apply" in error:
        return "patch did not apply"
    if status == "acut_harness_error":
        return "build/typecheck failure"
    if status == "harness_error":
        return "flaky or infrastructure failure"
    return "flaky or infrastructure failure"

