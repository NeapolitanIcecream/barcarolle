#!/usr/bin/env python3
"""Append a secret-safe ACUT cost record to the JSONL cost ledger."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from _common import ToolError, emit_json, fail, iso_now
from _llm_budget import (
    DEFAULT_LEDGER_PATH,
    append_ledger_record,
    assert_no_secret_like_content,
    estimate_cost_from_tokens,
    ledger_cumulative_decimal,
    money_json,
    parse_non_negative_int,
    parse_usd,
    read_ledger_summary,
    require_ledger_appendable,
)


TOOL = "append_cost_record"
PRICING_PROFILES = {
    "openai-gpt-5.5": (Decimal("5"), Decimal("30")),
    "anthropic-opus": (Decimal("5"), Decimal("25")),
    "unknown-sota": (Decimal("5"), Decimal("30")),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append a JSONL cost record with tokens, estimated/actual cost, and "
            "updated cumulative estimated cost. Refuses obvious secret-looking fields or values."
        )
    )
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH), help="Cost ledger JSONL path.")
    parser.add_argument("--record-type", default="acut_model_call_cost")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--acut-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--event", required=True)
    parser.add_argument("--started-at", help="ISO-8601 timestamp. Defaults to now.")
    parser.add_argument("--finished-at", help="ISO-8601 timestamp. Defaults to --started-at or now.")
    parser.add_argument("--input-tokens", required=True)
    parser.add_argument("--output-tokens", required=True)
    parser.add_argument("--estimated-cost-usd", help="Estimated USD cost. If absent, token pricing is used.")
    parser.add_argument("--actual-cost-usd", help="Actual provider-billed USD cost, when available.")
    parser.add_argument(
        "--pricing-profile",
        choices=sorted(PRICING_PROFILES),
        default="unknown-sota",
        help="Conservative pricing profile used when --estimated-cost-usd is absent.",
    )
    parser.add_argument("--input-rate-usd-per-million", help="Override input token rate.")
    parser.add_argument("--output-rate-usd-per-million", help="Override output token rate.")
    parser.add_argument("--extra-json", help="Optional JSON object stored as metadata after safety checks.")
    parser.add_argument("--output", help="Optional path for the structured JSON append summary.")
    return parser.parse_args()


def load_extra_json(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolError("--extra-json must be valid JSON", cause=str(exc)) from exc
    if not isinstance(value, dict):
        raise ToolError("--extra-json must decode to an object")
    assert_no_secret_like_content(value, "$.metadata")
    return value


def resolve_estimated_cost(args: argparse.Namespace, input_tokens: int, output_tokens: int) -> Decimal:
    if args.estimated_cost_usd is not None:
        return parse_usd(args.estimated_cost_usd, "--estimated-cost-usd")
    profile_input_rate, profile_output_rate = PRICING_PROFILES[args.pricing_profile]
    input_rate = (
        parse_usd(args.input_rate_usd_per_million, "--input-rate-usd-per-million")
        if args.input_rate_usd_per_million is not None
        else profile_input_rate
    )
    output_rate = (
        parse_usd(args.output_rate_usd_per_million, "--output-rate-usd-per-million")
        if args.output_rate_usd_per_million is not None
        else profile_output_rate
    )
    return estimate_cost_from_tokens(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_rate_usd_per_million=input_rate,
        output_rate_usd_per_million=output_rate,
    )


def main() -> int:
    args = parse_args()
    try:
        if args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        input_tokens = parse_non_negative_int(args.input_tokens, "--input-tokens")
        output_tokens = parse_non_negative_int(args.output_tokens, "--output-tokens")
        estimated_cost = resolve_estimated_cost(args, input_tokens, output_tokens)
        actual_cost = parse_usd(args.actual_cost_usd, "--actual-cost-usd") if args.actual_cost_usd is not None else None
        started_at = args.started_at or iso_now()
        finished_at = args.finished_at or started_at
        metadata = load_extra_json(args.extra_json)

        ledger_path = Path(args.ledger)
        before = require_ledger_appendable(ledger_path)
        previous_cumulative = ledger_cumulative_decimal(before)
        cumulative = previous_cumulative + estimated_cost
        record: dict[str, Any] = {
            "record_type": args.record_type,
            "run_id": args.run_id,
            "acut_id": args.acut_id,
            "task_id": args.task_id,
            "split": args.split,
            "attempt": args.attempt,
            "event": args.event,
            "started_at": started_at,
            "finished_at": finished_at,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": money_json(estimated_cost),
            "actual_cost_usd": None if actual_cost is None else money_json(actual_cost),
            "cumulative_estimated_cost_usd": money_json(cumulative),
        }
        if metadata is not None:
            record["metadata"] = metadata

        append_ledger_record(ledger_path, record)
        after = read_ledger_summary(ledger_path)
        payload = {
            "tool": TOOL,
            "status": "appended",
            "ledger": {
                "path": str(ledger_path),
                "record_count_before": before["record_count"],
                "record_count_after": after["record_count"],
                "previous_cumulative_estimated_cost_usd": money_json(previous_cumulative),
                "new_cumulative_estimated_cost_usd": money_json(cumulative),
            },
            "record_summary": {
                "record_type": args.record_type,
                "run_id": args.run_id,
                "acut_id": args.acut_id,
                "task_id": args.task_id,
                "split": args.split,
                "attempt": args.attempt,
                "event": args.event,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": money_json(estimated_cost),
                "actual_cost_recorded": actual_cost is not None,
                "cumulative_estimated_cost_usd": money_json(cumulative),
            },
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
