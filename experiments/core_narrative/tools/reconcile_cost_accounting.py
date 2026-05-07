#!/usr/bin/env python3
"""Reconcile ledger estimates, provider usage, and unknown real billing."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from _common import ToolError, emit_json, fail
from _llm_budget import money_json, parse_usd


TOOL = "reconcile_cost_accounting"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, help="Cost ledger JSONL path.")
    parser.add_argument("--output", help="Optional JSON output path.")
    return parser.parse_args()


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        raise ToolError("ledger path is not a file", path=str(path))
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ToolError("ledger contains invalid JSON", line_number=line_number) from exc
        if not isinstance(record, dict):
            raise ToolError("ledger record is not an object", line_number=line_number)
        records.append(record)
    return records


def decimal_or_zero(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return parse_usd(value, "cost")


def safe_usage(record: Mapping[str, Any]) -> dict[str, Any] | None:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    usage = metadata.get("provider_usage") if isinstance(metadata.get("provider_usage"), dict) else {}
    input_tokens = record.get("input_tokens")
    output_tokens = record.get("output_tokens")
    total_tokens = usage.get("total_tokens") if isinstance(usage.get("total_tokens"), int) else None
    observed_cost = metadata.get("observed_provider_cost_usd")
    if not isinstance(observed_cost, (int, float)):
        observed_cost = usage.get("cost")
    if not isinstance(observed_cost, (int, float)):
        observed_cost = None
    if not usage and not input_tokens and not output_tokens:
        return None
    return {
        "run_id": record.get("run_id"),
        "acut_id": record.get("acut_id"),
        "task_id": record.get("task_id"),
        "input_tokens": input_tokens if isinstance(input_tokens, int) else None,
        "output_tokens": output_tokens if isinstance(output_tokens, int) else None,
        "total_tokens": total_tokens,
        "provider_usage_reported": bool(metadata.get("provider_usage_reported")),
        "observed_provider_usage_cost_usd": observed_cost,
        "observed_provider_usage_cost_status": metadata.get("observed_provider_cost_status")
        or ("provider_response_usage_cost_not_invoice" if observed_cost is not None else "not_reported"),
    }


def reconcile(records: list[dict[str, Any]], ledger_path: Path) -> dict[str, Any]:
    estimated_sum = Decimal("0")
    actual_observed_sum = Decimal("0")
    actual_records = 0
    latest_cumulative: Decimal | None = None
    provider_usage: list[dict[str, Any]] = []
    observed_usage_cost_sum = Decimal("0")
    observed_usage_cost_count = 0
    estimate_only_records: list[str] = []

    for record in records:
        estimated_sum += decimal_or_zero(record.get("estimated_cost_usd"))
        if "cumulative_estimated_cost_usd" in record:
            latest_cumulative = parse_usd(record["cumulative_estimated_cost_usd"], "cumulative_estimated_cost_usd")
        actual = record.get("actual_cost_usd")
        if actual is not None:
            actual_observed_sum += parse_usd(actual, "actual_cost_usd")
            actual_records += 1
        elif record.get("record_type") != "ledger_initialized":
            run_id = record.get("run_id")
            if isinstance(run_id, str):
                estimate_only_records.append(run_id)
        usage = safe_usage(record)
        if usage is not None:
            provider_usage.append(usage)
            observed_cost = usage.get("observed_provider_usage_cost_usd")
            if isinstance(observed_cost, (int, float)):
                observed_usage_cost_sum += Decimal(str(observed_cost))
                observed_usage_cost_count += 1

    return {
        "tool": TOOL,
        "ledger": str(ledger_path),
        "record_count": len(records),
        "ledger_estimated_cost_sum_usd": money_json(estimated_sum),
        "latest_cumulative_estimated_cost_usd": money_json(latest_cumulative if latest_cumulative is not None else estimated_sum),
        "actual_provider_billed_cost_observed_usd": None if actual_records == 0 else money_json(actual_observed_sum),
        "actual_provider_billed_cost_status": "unknown_no_invoice_or_billed_cost_records"
        if actual_records == 0
        else "partial_observed_from_records",
        "provider_usage_observed_count": len([item for item in provider_usage if item["provider_usage_reported"]]),
        "observed_provider_usage_cost_sum_usd": None
        if observed_usage_cost_count == 0
        else money_json(observed_usage_cost_sum),
        "observed_provider_usage_cost_status": "not_reported"
        if observed_usage_cost_count == 0
        else "provider_response_usage_cost_not_invoice",
        "provider_usage_records": provider_usage,
        "estimate_only_record_count": len(estimate_only_records),
        "estimate_only_run_ids": estimate_only_records,
        "interpretation": (
            "ledger_estimated_cost_sum_usd is a local budgeting/estimation number, "
            "not evidence of actual provider billing; actual billed cost remains "
            "unknown unless actual_cost_usd is populated from provider billing/invoice data."
        ),
    }


def main() -> int:
    args = parse_args()
    try:
        path = Path(args.ledger)
        payload = reconcile(load_records(path), path)
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
