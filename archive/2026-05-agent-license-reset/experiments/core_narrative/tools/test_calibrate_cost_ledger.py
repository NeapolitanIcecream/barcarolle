#!/usr/bin/env python3
"""Executable specs for provider-usage cost ledger calibration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from calibrate_cost_ledger import calibrate_records


class CalibrateCostLedgerTests(unittest.TestCase):
    def test_provider_usage_cost_replaces_projected_estimate_and_recomputes_cumulative(self) -> None:
        """Provider usage cost is the future budget-gate source when it is reported."""
        records = [
            {
                "record_type": "ledger_initialized",
                "estimated_cost_usd": 0,
                "cumulative_estimated_cost_usd": 0,
            },
            {
                "record_type": "acut_patch_generation_attempt",
                "run_id": "estimate_only",
                "estimated_cost_usd": 10,
                "cumulative_estimated_cost_usd": 10,
                "metadata": {"provider_usage_reported": False},
            },
            {
                "record_type": "acut_patch_generation_attempt",
                "run_id": "provider_reported",
                "estimated_cost_usd": 3,
                "cumulative_estimated_cost_usd": 13,
                "metadata": {
                    "provider_usage_reported": True,
                    "provider_usage": {"cost": 0.125},
                },
            },
        ]

        calibrated, summary = calibrate_records(records, unreported_policy="zero")

        self.assertEqual(calibrated[1]["estimated_cost_usd"], 0)
        self.assertEqual(calibrated[1]["cumulative_estimated_cost_usd"], 0)
        self.assertEqual(
            calibrated[1]["metadata"]["cost_basis"],
            "zeroed_no_provider_usage_reported_for_budget_alignment",
        )
        self.assertEqual(calibrated[1]["metadata"]["previous_estimated_cost_usd"], 10)
        self.assertEqual(calibrated[2]["estimated_cost_usd"], 0.125)
        self.assertEqual(calibrated[2]["cumulative_estimated_cost_usd"], 0.125)
        self.assertEqual(
            calibrated[2]["metadata"]["cost_basis"],
            "provider_response_usage_cost_not_invoice",
        )
        self.assertEqual(calibrated[2]["metadata"]["previous_estimated_cost_usd"], 3)
        self.assertEqual(summary["previous_estimated_cost_sum_usd"], 13)
        self.assertEqual(summary["new_estimated_cost_sum_usd"], 0.125)
        self.assertEqual(summary["zeroed_unreported_record_count"], 1)
        self.assertEqual(summary["provider_usage_cost_record_count"], 1)

    def test_cli_round_trip_writes_jsonl_and_summary(self) -> None:
        """The calibration command preserves JSONL structure while rewriting cost totals."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "ledger.jsonl"
            output = Path(temp_dir) / "summary.json"
            ledger.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "record_type": "acut_patch_generation_attempt",
                                "run_id": "r1",
                                "estimated_cost_usd": 1,
                                "cumulative_estimated_cost_usd": 1,
                                "metadata": {
                                    "provider_usage_reported": True,
                                    "observed_provider_cost_usd": 0.01234567,
                                },
                            }
                        )
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            from calibrate_cost_ledger import main

            exit_code = main(
                [
                    "--ledger",
                    str(ledger),
                    "--output-summary",
                    str(output),
                    "--unreported-policy",
                    "zero",
                ]
            )

            self.assertEqual(exit_code, 0)
            rewritten = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
            summary = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(rewritten[0]["estimated_cost_usd"], 0.012346)
            self.assertEqual(rewritten[0]["cumulative_estimated_cost_usd"], 0.012346)
            self.assertEqual(summary["new_latest_cumulative_estimated_cost_usd"], 0.012346)


if __name__ == "__main__":
    unittest.main()
