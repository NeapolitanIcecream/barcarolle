#!/usr/bin/env python3
"""Calibrate cost ledger estimates to provider-reported usage costs.

The historical experiment ledger used conservative projected costs as a budget
brake.  Once provider responses include `usage.cost`, that observed usage cost
is a better budget-gate input for future runs.  This tool rewrites the ledger
in place while preserving the previous projected values in metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail
from _llm_budget import money_json, parse_usd


TOOL = "calibrate_cost_ledger"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, help="Cost ledger JSONL path to rewrite.")
    parser.add_argument(
        "--unreported-policy",
        choices=("zero", "keep-estimate"),
        default="zero",
        help=(
            "How to account records without provider-reported usage cost. "
            "`zero` aligns the budget ledger strictly to provider-reported usage; "
            "`keep-estimate` preserves prior projected costs for unreported records."
        ),
    )
    parser.add_argument("--output-summary", help="Optional JSON summary path.")
    parser.add_argument("--dry-run", action="store_true", help="Compute summary without rewriting the ledger.")
    return parser.parse_args(list(argv))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def provider_usage_cost(record: Mapping[str, Any]) -> Decimal | None:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    observed = metadata.get("observed_provider_cost_usd")
    if isinstance(observed, (int, float)):
        return parse_usd(observed, "observed_provider_cost_usd")
    usage = metadata.get("provider_usage") if isinstance(metadata.get("provider_usage"), dict) else {}
    cost = usage.get("cost")
    if isinstance(cost, (int, float)):
        return parse_usd(cost, "provider_usage.cost")
    return None


def record_metadata(record: Mapping[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata")
    return dict(metadata) if isinstance(metadata, dict) else {}


def calibrate_records(
    records: list[dict[str, Any]],
    *,
    unreported_policy: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if unreported_policy not in {"zero", "keep-estimate"}:
        raise ToolError("invalid unreported policy", unreported_policy=unreported_policy)

    calibrated: list[dict[str, Any]] = []
    cumulative = Decimal("0")
    previous_sum = Decimal("0")
    provider_sum = Decimal("0")
    provider_count = 0
    zeroed_count = 0
    kept_count = 0

    for record in records:
        previous_estimate = parse_usd(record.get("estimated_cost_usd", 0), "estimated_cost_usd")
        previous_sum += previous_estimate
        previous_cumulative = record.get("cumulative_estimated_cost_usd")
        observed = provider_usage_cost(record)
        next_record = dict(record)
        metadata = record_metadata(record)

        if observed is not None:
            next_estimate = observed
            provider_sum += observed
            provider_count += 1
            basis = "provider_response_usage_cost_not_invoice"
            metadata["provider_usage_cost_used_usd"] = money_json(observed)
        elif unreported_policy == "zero":
            next_estimate = Decimal("0")
            if record.get("record_type") != "ledger_initialized":
                zeroed_count += 1
            basis = "zeroed_no_provider_usage_reported_for_budget_alignment"
        else:
            next_estimate = previous_estimate
            kept_count += 1
            basis = "kept_local_estimate_no_provider_usage_reported"

        cumulative += next_estimate
        metadata.setdefault("previous_estimated_cost_usd", money_json(previous_estimate))
        if previous_cumulative is not None:
            metadata.setdefault("previous_cumulative_estimated_cost_usd", previous_cumulative)
        metadata["cost_basis"] = basis
        metadata["cost_alignment_policy"] = {
            "tool": TOOL,
            "provider_reported_usage_cost_preferred": True,
            "unreported_policy": unreported_policy,
            "actual_billing_observed": False,
        }

        next_record["estimated_cost_usd"] = money_json(next_estimate)
        next_record["cumulative_estimated_cost_usd"] = money_json(cumulative)
        next_record["metadata"] = metadata
        calibrated.append(next_record)

    summary = {
        "tool": TOOL,
        "status": "dry_run",
        "record_count": len(records),
        "unreported_policy": unreported_policy,
        "previous_estimated_cost_sum_usd": money_json(previous_sum),
        "new_estimated_cost_sum_usd": money_json(cumulative),
        "previous_latest_cumulative_estimated_cost_usd": records[-1].get("cumulative_estimated_cost_usd")
        if records
        else 0,
        "new_latest_cumulative_estimated_cost_usd": money_json(cumulative),
        "provider_reported_usage_cost_sum_usd": money_json(provider_sum),
        "provider_usage_cost_record_count": provider_count,
        "zeroed_unreported_record_count": zeroed_count,
        "kept_unreported_record_count": kept_count,
        "actual_provider_billed_cost_status": "unknown_no_invoice_or_billed_cost_records",
        "interpretation": (
            "estimated_cost_usd has been calibrated for future budget gates: "
            "provider-reported usage cost is used when available, and records "
            "without provider usage follow the selected unreported policy. "
            "Provider usage cost is not invoice proof."
        ),
    }
    return calibrated, summary


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        ledger = Path(args.ledger)
        records = load_jsonl(ledger)
        calibrated, summary = calibrate_records(records, unreported_policy=args.unreported_policy)
        if not args.dry_run:
            write_jsonl(ledger, calibrated)
            summary["status"] = "rewritten"
        emit_json(summary, args.output_summary)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
