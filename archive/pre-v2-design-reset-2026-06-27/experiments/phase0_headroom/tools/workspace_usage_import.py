from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
RESULTS_REL = Path("results")
REPORTS_REL = Path("reports")
USAGE_SCHEMA_VERSION = "barcarolle.workspace_usage.v1"
COST_RECONCILIATION_SCHEMA_VERSION = "barcarolle.workspace_cost_reconciliation.v1"
COST_SUMMARY_SCHEMA_VERSION = "barcarolle.workspace_acut_cost_summary.v2"


@dataclass(frozen=True)
class ModelPrice:
    endpoint_host_hash: str
    model: str
    pricing_source: str
    input_rate_per_1m_usd: float
    cached_input_rate_per_1m_usd: float
    output_rate_per_1m_usd: float
    reasoning_output_policy: str


@dataclass(frozen=True)
class UsageAggregate:
    usage_source: str
    usage_observed: bool
    input_tokens: int = 0
    cached_input_tokens: int = 0
    uncached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    reported_cost_usd: float | None = None
    reported_cost_trusted: bool | None = None
    cache_write_tokens: int = 0
    visible_output_tokens: int | None = None
    usage_event_count: int = 0


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def phase0_root(root: Path) -> Path:
    candidate = root / EXP_REL
    return candidate if candidate.exists() else root


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"null", "None"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def load_model_prices(path: Path) -> list[ModelPrice]:
    prices: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_prices = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            in_prices = stripped == "prices:"
            continue
        if not in_prices:
            continue
        if stripped.startswith("- "):
            if current is not None:
                prices.append(current)
            current = {}
            item = stripped[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current[key.strip()] = parse_scalar(value)
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_scalar(value)
    if current is not None:
        prices.append(current)
    return [
        ModelPrice(
            endpoint_host_hash=str(row["endpoint_host_hash"]),
            model=str(row["model"]),
            pricing_source=str(row["pricing_source"]),
            input_rate_per_1m_usd=float(row["input_rate_per_1m_usd"]),
            cached_input_rate_per_1m_usd=float(row["cached_input_rate_per_1m_usd"]),
            output_rate_per_1m_usd=float(row["output_rate_per_1m_usd"]),
            reasoning_output_policy=str(row["reasoning_output_policy"]),
        )
        for row in prices
    ]


def lookup_price(
    prices: list[ModelPrice],
    endpoint_host_hash: str,
    model: str,
    allow_missing_price_estimate: bool = False,
) -> ModelPrice | None:
    for price in prices:
        if price.endpoint_host_hash == endpoint_host_hash and price.model == model:
            return price
    if allow_missing_price_estimate:
        return None
    raise KeyError(f"missing price for endpoint_host_hash={endpoint_host_hash!r} model={model!r}")


def infer_unique_price(prices: list[ModelPrice], model: str, allow_missing_price_estimate: bool = False) -> ModelPrice | None:
    matches = [price for price in prices if price.model == model]
    if len(matches) == 1:
        return matches[0]
    if allow_missing_price_estimate:
        return None
    if not matches:
        raise KeyError(f"missing price for model={model!r}")
    raise KeyError(f"ambiguous price for model={model!r}; pass --endpoint-host-hash")


def estimate_token_cost_usd(
    price: ModelPrice,
    *,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_output_tokens: int = 0,
) -> float:
    if price.reasoning_output_policy != "included_in_output_tokens" and reasoning_output_tokens:
        raise ValueError(f"unsupported reasoning output policy: {price.reasoning_output_policy}")
    uncached_input_tokens = max(input_tokens - cached_input_tokens, 0)
    total = (
        uncached_input_tokens * price.input_rate_per_1m_usd
        + cached_input_tokens * price.cached_input_rate_per_1m_usd
        + output_tokens * price.output_rate_per_1m_usd
    ) / 1_000_000
    return round(total, 8)


def endpoint_host_hash_from_base_url(base_url: str | None = None) -> str | None:
    raw = base_url if base_url is not None else os.environ.get("LLM_BASE_URL", "")
    if not raw:
        return None
    parsed = urllib.parse.urlparse(raw)
    host = parsed.netloc or raw
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:12]


def json_objects_from_text(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            objects.append(row)
    return objects


def parse_codex_usage(text: str) -> UsageAggregate:
    input_tokens = 0
    cached_input_tokens = 0
    output_tokens = 0
    reasoning_output_tokens = 0
    event_count = 0
    for row in json_objects_from_text(text):
        if row.get("type") != "turn.completed":
            continue
        usage = row.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        event_count += 1
        input_tokens += int(usage.get("input_tokens") or 0)
        cached_input_tokens += int(usage.get("cached_input_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or 0)
        reasoning_output_tokens += int(usage.get("reasoning_output_tokens") or 0)
    if event_count == 0:
        return UsageAggregate(usage_source="missing", usage_observed=False)
    return UsageAggregate(
        usage_source="codex_turn_completed",
        usage_observed=True,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        uncached_input_tokens=max(input_tokens - cached_input_tokens, 0),
        output_tokens=output_tokens,
        reasoning_output_tokens=reasoning_output_tokens,
        usage_event_count=event_count,
    )


def parse_kilo_usage(text: str) -> UsageAggregate:
    uncached_input_tokens = 0
    cached_input_tokens = 0
    cache_write_tokens = 0
    visible_output_tokens = 0
    reasoning_output_tokens = 0
    reported_cost_total = 0.0
    reported_cost_seen = False
    event_count = 0
    for row in json_objects_from_text(text):
        if row.get("type") not in {"step_finish", "step-finish"}:
            continue
        part = row.get("part") if isinstance(row.get("part"), dict) else row
        tokens = part.get("tokens") or {}
        if not isinstance(tokens, dict):
            continue
        cache = tokens.get("cache") or {}
        if not isinstance(cache, dict):
            cache = {}
        event_count += 1
        uncached_input_tokens += int(tokens.get("input") or 0)
        cached_input_tokens += int(cache.get("read") or 0)
        cache_write_tokens += int(cache.get("write") or 0)
        visible_output_tokens += int(tokens.get("output") or 0)
        reasoning_output_tokens += int(tokens.get("reasoning") or 0)
        cost = part.get("cost")
        if isinstance(cost, (int, float)):
            reported_cost_total += float(cost)
            reported_cost_seen = True
    if event_count == 0:
        return UsageAggregate(usage_source="missing", usage_observed=False)
    billable_uncached_input_tokens = uncached_input_tokens + cache_write_tokens
    billable_output_tokens = visible_output_tokens + reasoning_output_tokens
    return UsageAggregate(
        usage_source="kilo_step_finish",
        usage_observed=True,
        input_tokens=billable_uncached_input_tokens + cached_input_tokens,
        cached_input_tokens=cached_input_tokens,
        uncached_input_tokens=billable_uncached_input_tokens,
        output_tokens=billable_output_tokens,
        reasoning_output_tokens=reasoning_output_tokens,
        reported_cost_usd=round(reported_cost_total, 8) if reported_cost_seen else None,
        reported_cost_trusted=False if reported_cost_seen and reported_cost_total == 0.0 else reported_cost_seen,
        cache_write_tokens=cache_write_tokens,
        visible_output_tokens=visible_output_tokens,
        usage_event_count=event_count,
    )


def result_file(exp: Path, result_prefix: str, stem: str, suffix: str) -> Path:
    return exp / RESULTS_REL / f"{result_prefix}_{stem}{suffix}"


def safe_raw_artifact_ref(raw_artifact_ref: str | None) -> str | None:
    if not raw_artifact_ref:
        return None
    path = Path(raw_artifact_ref)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def resolve_exp_relative_path(exp: Path, raw_artifact_ref: str | None) -> Path | None:
    safe_ref = safe_raw_artifact_ref(raw_artifact_ref)
    if not safe_ref:
        return None
    return exp / safe_ref


def price_for_submission(
    prices: list[ModelPrice],
    model: str,
    endpoint_host_hash: str | None,
    allow_missing_price_estimate: bool = False,
) -> ModelPrice | None:
    if endpoint_host_hash:
        return lookup_price(prices, endpoint_host_hash, model, allow_missing_price_estimate=allow_missing_price_estimate)
    return infer_unique_price(prices, model, allow_missing_price_estimate=allow_missing_price_estimate)


def usage_for_submission(
    exp: Path,
    result_prefix: str,
    submission: dict[str, Any],
    prices: list[ModelPrice],
    endpoint_host_hash: str | None,
    allow_missing_price_estimate: bool = False,
) -> dict[str, Any]:
    model = str(submission.get("model_or_agent_name") or "")
    price = price_for_submission(prices, model, endpoint_host_hash, allow_missing_price_estimate=allow_missing_price_estimate)
    raw_ref = safe_raw_artifact_ref((submission.get("raw_artifacts") or {}).get("stdout"))
    raw_path = resolve_exp_relative_path(exp, raw_ref)
    text = raw_path.read_text(encoding="utf-8", errors="replace") if raw_path and raw_path.exists() else ""
    harness = str(submission.get("harness_name") or "")
    adapter_id = str(submission.get("adapter_id") or "")
    if harness == "codex" or adapter_id.startswith("codex"):
        usage = parse_codex_usage(text)
    elif harness == "kilo" or adapter_id.startswith("kilo"):
        usage = parse_kilo_usage(text)
    else:
        usage = UsageAggregate(usage_source="missing", usage_observed=False)
    estimated_cost = 0.0
    pricing_source = price.pricing_source if price else "missing_price"
    priced_endpoint_hash = price.endpoint_host_hash if price else endpoint_host_hash
    if usage.usage_observed and price is not None:
        estimated_cost = estimate_token_cost_usd(
            price,
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_output_tokens=usage.reasoning_output_tokens,
        )
    return {
        "schema_version": USAGE_SCHEMA_VERSION,
        "generated_at": iso_now(),
        "run_id": submission.get("run_id", ""),
        "result_prefix": result_prefix,
        "adapter_id": adapter_id,
        "harness_name": harness,
        "model_or_agent_name": model,
        "task_id": submission.get("task_id", ""),
        "split": submission.get("split", ""),
        "usage_source": usage.usage_source,
        "usage_observed": usage.usage_observed,
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "uncached_input_tokens": usage.uncached_input_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_output_tokens": usage.reasoning_output_tokens,
        "reported_cost_usd": usage.reported_cost_usd,
        "reported_cost_trusted": usage.reported_cost_trusted,
        "estimated_cost_usd": estimated_cost,
        "pricing_source": pricing_source,
        "endpoint_host_hash": priced_endpoint_hash,
        "raw_artifact_ref": raw_ref,
        "cache_write_tokens": usage.cache_write_tokens,
        "visible_output_tokens": usage.visible_output_tokens,
        "usage_event_count": usage.usage_event_count,
        "latency_seconds": submission.get("latency_seconds"),
    }


def import_prefix_usage(
    exp: Path,
    result_prefix: str,
    prices: list[ModelPrice],
    endpoint_host_hash: str | None,
    allow_missing_price_estimate: bool = False,
) -> list[dict[str, Any]]:
    submissions = read_jsonl(result_file(exp, result_prefix, "submissions", ".jsonl"))
    return [
        usage_for_submission(
            exp,
            result_prefix,
            submission,
            prices,
            endpoint_host_hash,
            allow_missing_price_estimate=allow_missing_price_estimate,
        )
        for submission in submissions
    ]


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.median(values)), 3)


def previous_conservative_cost(exp: Path, result_prefix: str) -> float:
    summary_path = result_file(exp, result_prefix, "cost_summary", ".json")
    if summary_path.exists():
        summary = read_json(summary_path)
        if "conservative_estimated_cost_usd" in summary:
            return round(float(summary.get("conservative_estimated_cost_usd") or 0.0), 8)
        return round(float(summary.get("estimated_cost_usd") or 0.0), 8)
    ledger = read_jsonl(result_file(exp, result_prefix, "cost_ledger", ".jsonl"))
    return round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in ledger), 8)


def conservative_cost_by_run_id(exp: Path, result_prefix: str) -> dict[str, float]:
    ledger = read_jsonl(result_file(exp, result_prefix, "cost_ledger", ".jsonl"))
    return {str(row.get("run_id")): float(row.get("estimated_cost_usd") or 0.0) for row in ledger if row.get("run_id")}


def summarize_prefix(exp: Path, result_prefix: str, usage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    conservative_by_run = conservative_cost_by_run_id(exp, result_prefix)
    missing_usage_run_ids = [str(row["run_id"]) for row in usage_rows if row.get("usage_observed") is not True]
    observed_token_cost = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in usage_rows if row.get("usage_observed") is True), 8)
    conservative_fallback_for_missing = round(sum(conservative_by_run.get(run_id, 0.0) for run_id in missing_usage_run_ids), 8)
    per_harness: dict[str, float] = defaultdict(float)
    per_split: dict[str, float] = defaultdict(float)
    for row in usage_rows:
        if row.get("usage_observed") is True:
            cost = float(row.get("estimated_cost_usd") or 0.0)
            per_harness[str(row.get("adapter_id") or row.get("harness_name") or "unknown")] += cost
            per_split[str(row.get("split") or "unknown")] += cost
    latencies = [float(row["latency_seconds"]) for row in usage_rows if row.get("latency_seconds") is not None]
    usage_observed_count = sum(1 for row in usage_rows if row.get("usage_observed") is True)
    pricing_sources = sorted({str(row.get("pricing_source")) for row in usage_rows if row.get("pricing_source")})
    return {
        "schema_version": COST_SUMMARY_SCHEMA_VERSION,
        "generated_at": iso_now(),
        "result_prefix": result_prefix,
        "call_count": len(usage_rows),
        "usage_observed_count": usage_observed_count,
        "usage_observed_rate": None if not usage_rows else round(usage_observed_count / len(usage_rows), 4),
        "conservative_estimated_cost_usd": previous_conservative_cost(exp, result_prefix),
        "observed_token_estimated_cost_usd": observed_token_cost,
        "observed_or_conservative_estimated_cost_usd": round(observed_token_cost + conservative_fallback_for_missing, 8),
        "conservative_fallback_for_missing_usage_usd": conservative_fallback_for_missing,
        "actual_provider_billed_cost_usd": None,
        "pricing_source": ",".join(pricing_sources) if pricing_sources else "missing",
        "missing_usage_run_ids": missing_usage_run_ids,
        "missing_usage_cell_count": len(missing_usage_run_ids),
        "per_harness_observed_token_cost_usd": {key: round(value, 8) for key, value in sorted(per_harness.items())},
        "per_split_observed_token_cost_usd": {key: round(value, 8) for key, value in sorted(per_split.items())},
        "median_latency_seconds": median(latencies),
    }


def write_report(exp: Path, summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# Workspace Cost Usage Report",
        "",
        f"Generated at `{iso_now()}`.",
        "",
        "Provider-billed dollars remain unavailable for these workspace ACUT runs. The canonical spend estimate is therefore the observed-token estimate priced through `experiments/phase0_headroom/configs/model_pricing.yaml`; missing usage, if any, is shown separately as the previous conservative fallback.",
        "",
        "| Result prefix | Cells | Usage observed | Conservative USD | Observed-token USD | Observed-or-conservative USD | Missing usage | Median latency s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        rate = summary.get("usage_observed_rate")
        lines.append(
            "| {prefix} | {cells} | {rate} | {conservative:.8f} | {observed:.8f} | {combined:.8f} | {missing} | {median} |".format(
                prefix=summary["result_prefix"],
                cells=summary["call_count"],
                rate="n/a" if rate is None else f"{rate:.4f}",
                conservative=float(summary["conservative_estimated_cost_usd"]),
                observed=float(summary["observed_token_estimated_cost_usd"]),
                combined=float(summary["observed_or_conservative_estimated_cost_usd"]),
                missing=summary["missing_usage_cell_count"],
                median="n/a" if summary["median_latency_seconds"] is None else summary["median_latency_seconds"],
            )
        )
    lines.extend(["", "## Per-Harness Observed Cost", ""])
    for summary in summaries:
        lines.append(f"### {summary['result_prefix']}")
        per_harness = summary.get("per_harness_observed_token_cost_usd") or {}
        if not per_harness:
            lines.append("- No observed usage.")
        else:
            for harness, cost in per_harness.items():
                lines.append(f"- `{harness}`: `USD {float(cost):.8f}`.")
        missing = summary.get("missing_usage_run_ids") or []
        if missing:
            lines.append(f"- Missing usage rows: `{len(missing)}`.")
        lines.append("")
    lines.extend(
        [
            "## Notes",
            "",
            "- Kilo `part.cost == 0` rows from the OpenAI-compatible provider are preserved as reported cost but marked untrusted.",
            "- Raw stdout, prompts, completions, patches, and workspaces remain in ignored paths and are not copied into this report or the ledger.",
            "",
        ]
    )
    write_text(exp / REPORTS_REL / "workspace_cost_usage_report.md", "\n".join(lines))


def run_import(
    root: Path,
    result_prefixes: list[str],
    pricing_config: Path,
    endpoint_host_hash: str | None,
    allow_missing_price_estimate: bool = False,
) -> dict[str, Any]:
    exp = phase0_root(root)
    prices = load_model_prices(pricing_config)
    resolved_endpoint_hash = endpoint_host_hash or endpoint_host_hash_from_base_url()
    all_usage_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for result_prefix in result_prefixes:
        usage_rows = import_prefix_usage(
            exp,
            result_prefix,
            prices,
            resolved_endpoint_hash,
            allow_missing_price_estimate=allow_missing_price_estimate,
        )
        all_usage_rows.extend(usage_rows)
        summary = summarize_prefix(exp, result_prefix, usage_rows)
        summaries.append(summary)
        write_json(result_file(exp, result_prefix, "cost_summary", ".json"), summary)
    write_jsonl(exp / RESULTS_REL / "workspace_usage_ledger.jsonl", all_usage_rows)
    reconciliation = {
        "schema_version": COST_RECONCILIATION_SCHEMA_VERSION,
        "generated_at": iso_now(),
        "pricing_config": str(pricing_config),
        "endpoint_host_hash": resolved_endpoint_hash,
        "actual_provider_billed_cost_usd": None,
        "result_prefixes": result_prefixes,
        "summaries": summaries,
        "totals": {
            "call_count": sum(int(summary["call_count"]) for summary in summaries),
            "usage_observed_count": sum(int(summary["usage_observed_count"]) for summary in summaries),
            "conservative_estimated_cost_usd": round(sum(float(summary["conservative_estimated_cost_usd"]) for summary in summaries), 8),
            "observed_token_estimated_cost_usd": round(sum(float(summary["observed_token_estimated_cost_usd"]) for summary in summaries), 8),
            "observed_or_conservative_estimated_cost_usd": round(sum(float(summary["observed_or_conservative_estimated_cost_usd"]) for summary in summaries), 8),
        },
    }
    total_calls = int(reconciliation["totals"]["call_count"])
    observed = int(reconciliation["totals"]["usage_observed_count"])
    reconciliation["totals"]["usage_observed_rate"] = None if total_calls == 0 else round(observed / total_calls, 4)
    write_json(exp / RESULTS_REL / "workspace_cost_reconciliation.json", reconciliation)
    write_report(exp, summaries)
    return reconciliation


def resolve_repo_path(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Import sanitized workspace ACUT usage from raw harness JSONL.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--result-prefix", action="append", required=True)
    parser.add_argument("--pricing-config", default=str(EXP_REL / "configs" / "model_pricing.yaml"))
    parser.add_argument("--endpoint-host-hash", default=None)
    parser.add_argument("--allow-missing-price-estimate", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    pricing_config = resolve_repo_path(root, args.pricing_config)
    run_import(
        root,
        args.result_prefix,
        pricing_config,
        args.endpoint_host_hash,
        allow_missing_price_estimate=args.allow_missing_price_estimate,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
