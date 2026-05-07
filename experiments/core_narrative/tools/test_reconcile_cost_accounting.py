#!/usr/bin/env python3
"""Executable specs for estimated-vs-actual cost reconciliation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reconcile_cost_accounting import load_records, reconcile


class ReconcileCostAccountingTests(unittest.TestCase):
    def test_estimated_ledger_cost_is_not_reported_as_actual_billing(self) -> None:
        """Regression: local projected cost must remain distinct from true billing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "cost_ledger.jsonl"
            records = [
                {
                    "record_type": "ledger_initialized",
                    "estimated_cost_usd": 0,
                    "cumulative_estimated_cost_usd": 0,
                },
                {
                    "record_type": "acut_patch_generation_attempt",
                    "run_id": "run_estimate_only",
                    "acut_id": "cheap-generic-swe",
                    "task_id": "click__rbench__001",
                    "estimated_cost_usd": 3,
                    "actual_cost_usd": None,
                    "cumulative_estimated_cost_usd": 3,
                    "input_tokens": 100,
                    "output_tokens": 25,
                    "metadata": {"provider_usage_reported": False},
                },
                {
                    "record_type": "acut_patch_generation_attempt",
                    "run_id": "run_usage_observed",
                    "acut_id": "cheap-generic-swe",
                    "task_id": "click__rbench__001",
                    "estimated_cost_usd": 1,
                    "actual_cost_usd": None,
                    "cumulative_estimated_cost_usd": 4,
                    "input_tokens": 120,
                    "output_tokens": 30,
                    "metadata": {
                        "provider_usage_reported": True,
                        "provider_usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150, "cost": 0.025},
                    },
                },
            ]
            ledger.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

            summary = reconcile(load_records(ledger), ledger)

            self.assertEqual(summary["ledger_estimated_cost_sum_usd"], 4)
            self.assertIsNone(summary["actual_provider_billed_cost_observed_usd"])
            self.assertEqual(
                summary["actual_provider_billed_cost_status"],
                "unknown_no_invoice_or_billed_cost_records",
            )
            self.assertEqual(summary["provider_usage_observed_count"], 1)
            self.assertEqual(summary["observed_provider_usage_cost_sum_usd"], 0.025)
            self.assertEqual(
                summary["observed_provider_usage_cost_status"],
                "provider_response_usage_cost_not_invoice",
            )
            self.assertIn("not evidence of actual provider billing", summary["interpretation"])


if __name__ == "__main__":
    unittest.main()
