#!/usr/bin/env python3
"""Executable specs for Rich W* reserve feasibility summaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _common import write_json
import rich_wstar_reserve_feasibility as reserve


class RichWstarReserveFeasibilityTests(unittest.TestCase):
    def test_accepted_primary_count_sums_direct_batch_and_single_artifacts(self) -> None:
        """Accepted W* primary count includes direct-batch tasks plus each accepted pilot artifact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json(root / "rich_direct_smoke_batch_20260514.json", {"accepted_count": 5})
            for artifact in reserve.ACCEPTED_WSTAR_ARTIFACTS:
                if artifact == "rich_direct_smoke_batch_20260514.json":
                    continue
                write_json(root / artifact, {"admission_decision": "accepted"})

            self.assertEqual(reserve.accepted_primary_count(root), 20)

    def test_remaining_source_items_are_redacted_and_blocker_coded(self) -> None:
        """Remaining reserve candidates expose only digests and public blocker codes."""
        candidates = [
            {
                "subject": "ws",
                "commit": "a" * 40,
                "base_commit": "b" * 40,
                "committed_at": "2026-04-12T00:00:00+00:00",
                "window": "W_star",
                "family": "console/rendering",
                "surface": "source_without_tests",
                "source_files": ["rich/ansi.py"],
                "test_files": [],
                "source_file_count": 1,
                "test_file_count": 0,
                "test_node_count": 0,
                "changed_file_set_digest": "digest",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            }
        ]

        original = reserve.source_only_oracle_candidates
        reserve.source_only_oracle_candidates = lambda _repo: candidates
        try:
            rows = reserve.remaining_source_items(Path("/tmp/repo"))
        finally:
            reserve.source_only_oracle_candidates = original

        self.assertEqual(rows[0]["reserve_blocker_code"], "whitespace_only_source_cleanup")
        serialized = str(rows)
        self.assertNotIn("ws", serialized)
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("b" * 40, serialized)

    def test_payload_marks_reserve_gap_when_primary_count_is_reached(self) -> None:
        """The payload distinguishes 20 primary admissions from the unmet reserve target."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json(root / "rich_direct_smoke_batch_20260514.json", {"accepted_count": 5})
            for artifact in reserve.ACCEPTED_WSTAR_ARTIFACTS:
                if artifact == "rich_direct_smoke_batch_20260514.json":
                    continue
                write_json(root / artifact, {"admission_decision": "accepted"})
            original = reserve.source_only_oracle_candidates
            reserve.source_only_oracle_candidates = lambda _repo: []
            try:
                payload = reserve.build_payload(Path("/tmp/repo"), root)
            finally:
                reserve.source_only_oracle_candidates = original

        self.assertEqual(payload["accepted_w_star_primary_count"], 20)
        self.assertEqual(payload["target_primary_plus_reserve_count"], 25)
        self.assertEqual(payload["reserve_gap_even_if_all_remaining_admitted"], 5)
        self.assertFalse(payload["primary_runs_authorized"])


if __name__ == "__main__":
    unittest.main()
