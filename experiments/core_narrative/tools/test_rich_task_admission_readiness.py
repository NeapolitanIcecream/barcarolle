#!/usr/bin/env python3
"""Executable specs for Rich repository-local task-admission readiness."""

from __future__ import annotations

import datetime as dt
import unittest

import rich_task_admission_readiness as readiness


class RichTaskAdmissionReadinessTests(unittest.TestCase):
    def test_window_for_date_uses_frozen_0514_boundaries(self) -> None:
        """Rich readiness follows the same C/R/W* split as the 0514 protocol."""
        self.assertEqual(readiness.window_for_date("2025-11-13T23:59:59+00:00"), "C")
        self.assertEqual(readiness.window_for_date("2025-11-14T00:00:00+00:00"), "R")
        self.assertEqual(readiness.window_for_date("2026-02-13T23:59:59+00:00"), "R")
        self.assertEqual(readiness.window_for_date("2026-02-14T00:00:00+00:00"), "W_star")
        self.assertEqual(readiness.window_for_date("2026-05-14T23:59:59+00:00"), "W_star")

    def test_window_for_date_accepts_preregistered_earlier_c_start(self) -> None:
        """C can be extended earlier when calibration supply is thin."""
        c_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)

        self.assertEqual(
            readiness.window_for_date("2025-04-14T00:00:00+00:00", c_scan_start=c_start),
            "C",
        )
        self.assertEqual(
            readiness.window_for_date("2025-04-13T23:59:59+00:00", c_scan_start=c_start),
            "older_C_not_scanned",
        )

    def test_parse_c_scan_start_returns_utc_midnight(self) -> None:
        """CLI C extension dates are parsed as UTC-inclusive day starts."""
        self.assertEqual(
            readiness.parse_c_scan_start("2025-04-14"),
            dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc),
        )

    def test_extract_test_nodes_reports_added_and_modified_pytest_nodes(self) -> None:
        """Direct-oracle candidates can use added tests and modified test hunk context."""
        diff = """diff --git a/tests/test_console.py b/tests/test_console.py
@@ -1,0 +2,4 @@
+def test_print_empty_with_end():
+    pass
+def helper():
+    pass
@@ -20,2 +24,3 @@ def test_print():
     console.print("x")
+    assert console.file.getvalue()
"""

        self.assertEqual(
            readiness.extract_test_nodes_from_diff(diff, "tests/test_console.py"),
            [
                "tests/test_console.py::test_print_empty_with_end",
                "tests/test_console.py::test_print",
            ],
        )

    def test_candidate_readiness_marks_source_only_as_golden_oracle_required(self) -> None:
        """Source-only candidates can seed task design but cannot be direct-smoked."""
        self.assertEqual(
            readiness.oracle_requirement("source_without_tests", test_node_count=0),
            "golden_oracle_required",
        )
        self.assertEqual(
            readiness.oracle_requirement("source_and_tests", test_node_count=2),
            "direct_reference_tests_available",
        )
        self.assertEqual(
            readiness.oracle_requirement("source_and_tests", test_node_count=0),
            "direct_tests_without_extractable_nodes",
        )

    def test_summarize_window_reports_source_only_gap_for_primary_tasks(self) -> None:
        """Readiness summaries expose the Golden-Oracle gap before primary runs."""
        def row(index: int, *, surface: str, family: str, direct: bool) -> dict[str, object]:
            return {
                "commit": str(index) * 40,
                "committed_at": "2026-04-12T00:00:00+00:00",
                "subject": f"fix rich behavior {index}",
                "window": "W_star",
                "surface": surface,
                "family": family,
                "direct_smoke_ready": direct,
                "oracle_requirement": readiness.oracle_requirement(surface, test_node_count=1 if direct else 0),
                "source_file_count": 1,
                "test_file_count": 1 if surface == "source_and_tests" else 0,
                "test_node_count": 1 if direct else 0,
                "changed_file_set_digest": f"digest-{index}",
            }

        rows = [
            row(1, surface="source_and_tests", family="console/rendering", direct=True),
            row(2, surface="source_without_tests", family="console/rendering", direct=False),
            row(3, surface="source_without_tests", family="markup/text/emoji", direct=False),
        ]

        summary = readiness.summarize_window(rows, "W_star")

        self.assertEqual(summary["task_design_candidate_count"], 3)
        self.assertEqual(summary["direct_smoke_ready_count"], 1)
        self.assertEqual(summary["source_only_golden_oracle_required_count"], 2)
        self.assertEqual(summary["denominator_readiness"]["golden_oracle_needed_for_20_primary"], 19)
        self.assertEqual(summary["denominator_readiness"]["candidate_pool_gap_to_40"], 37)

    def test_public_candidate_rows_do_not_publish_raw_commit_sha(self) -> None:
        """Planning artifacts publish digests rather than raw target commits."""
        row = readiness.public_candidate_row(
            {
                "commit": "a" * 40,
                "committed_at": "2026-04-12T00:00:00+00:00",
                "subject": "fix console rendering",
                "window": "W_star",
                "family": "console/rendering",
                "surface": "source_and_tests",
                "test_node_count": 2,
                "source_file_count": 1,
                "test_file_count": 1,
                "changed_file_set_digest": "digest",
                "oracle_requirement": "direct_reference_tests_available",
                "direct_smoke_ready": True,
            }
        )

        serialized = str(row)
        self.assertIn("source_anchor_digest", row)
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("commit", row)


if __name__ == "__main__":
    unittest.main()
