#!/usr/bin/env python3
"""Executable specs for Rich direct-smoke batch summaries."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest

import rich_direct_smoke_batch as batch


class RichDirectSmokeBatchTests(unittest.TestCase):
    def test_summarize_results_counts_accept_reject_and_blocked(self) -> None:
        """Batch summaries expose denominator-building progress by admission state."""
        summary = batch.summarize_results(
            [
                {"admission_decision": "accepted", "no_op_result": {"status": "failed"}, "reference_result": {"status": "passed"}},
                {"admission_decision": "rejected", "no_op_result": {"status": "passed_unexpected"}, "reference_result": {"status": "passed"}},
                {"admission_decision": "rejected", "no_op_result": {"status": "blocked"}, "reference_result": {"status": "blocked"}},
            ]
        )

        self.assertEqual(summary["accepted_count"], 1)
        self.assertEqual(summary["rejected_count"], 2)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertEqual(summary["noop_status_counts"], {"blocked": 1, "failed": 1, "passed_unexpected": 1})

    def test_public_summary_preserves_no_primary_run_boundary(self) -> None:
        """Direct-smoke batches never authorize ACUT primary attempts."""
        payload = batch.public_summary(results=[], private_root="experiments/core_narrative/large_artifacts/example", split="R")

        self.assertFalse(payload["primary_runs_authorized"])
        self.assertEqual(payload["model_calls_made"], 0)
        self.assertEqual(payload["split"], "R")
        self.assertIn("not a frozen Rich denominator", " ".join(payload["claim_boundary"]))

    def test_direct_candidates_passes_extended_c_scan_start(self) -> None:
        """C direct-smoke discovery can use the preregistered earlier C boundary."""
        seen = {}
        original = batch.discover_candidates

        def fake_discover(repo_path: Path, *, c_scan_start=None):
            seen["c_scan_start"] = c_scan_start
            return [
                {"window": "C", "direct_smoke_ready": True},
                {"window": "R", "direct_smoke_ready": True},
                {"window": "C", "direct_smoke_ready": False},
            ]

        c_scan_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)
        batch.discover_candidates = fake_discover
        try:
            candidates = batch.direct_candidates(Path("."), "C", c_scan_start=c_scan_start)
        finally:
            batch.discover_candidates = original

        self.assertEqual(candidates, [{"window": "C", "direct_smoke_ready": True}])
        self.assertEqual(seen["c_scan_start"], c_scan_start)


if __name__ == "__main__":
    unittest.main()
