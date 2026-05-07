#!/usr/bin/env python3
"""Pre-call LLM credential and cost-ledger gate for ACUT execution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import ToolError, emit_json, fail
from _llm_budget import (
    DEFAULT_HARD_CAP_USD,
    DEFAULT_LEDGER_PATH,
    DEFAULT_SOFT_STOP_USD,
    gate_exit_code,
    gate_payload,
    parse_usd,
)


TOOL = "llm_budget_gate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify experiment-specific LLM environment presence, cost-ledger "
            "availability, and soft/hard budget policy before an ACUT model call."
        )
    )
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH), help="Cost ledger JSONL path.")
    parser.add_argument("--projected-cost-usd", help="Conservative projected cost for the next run.")
    parser.add_argument("--soft-stop-usd", default=str(DEFAULT_SOFT_STOP_USD), help="Soft-stop USD threshold.")
    parser.add_argument("--hard-cap-usd", default=str(DEFAULT_HARD_CAP_USD), help="Hard-cap USD threshold.")
    parser.add_argument("--coordinator-decision-ref", help="Reference to an explicit coordinator approval.")
    parser.add_argument("--acut-id", help="ACUT id for default-profile policy checks.")
    parser.add_argument("--split", help="Task split for structured diagnostics.")
    parser.add_argument("--attempt", type=int, help="Attempt number for default-profile policy checks.")
    parser.add_argument("--output", help="Optional path for the structured JSON result.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.attempt is not None and args.attempt < 1:
            raise ToolError("--attempt must be at least 1")
        payload = gate_payload(
            ledger_path=Path(args.ledger),
            projected_cost_usd=parse_usd(args.projected_cost_usd, "--projected-cost-usd"),
            soft_stop_usd=parse_usd(args.soft_stop_usd, "--soft-stop-usd"),
            hard_cap_usd=parse_usd(args.hard_cap_usd, "--hard-cap-usd"),
            coordinator_decision_ref=args.coordinator_decision_ref,
            acut_id=args.acut_id,
            split=args.split,
            attempt=args.attempt,
        )
        emit_json(payload, args.output)
        return gate_exit_code(payload)
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
