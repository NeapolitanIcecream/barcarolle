#!/usr/bin/env python3
"""Executable specs for Rich Golden-Oracle queue construction."""

from __future__ import annotations

from pathlib import Path
import unittest

from _common import ToolError
import rich_source_oracle_queue as queue


class RichSourceOracleQueueTests(unittest.TestCase):
    def test_summarize_queue_reports_primary_gap_and_reserve_block(self) -> None:
        """The queue summary exposes whether Oracle work can still reach the W* denominator."""
        items = [
            {"work_item_kind": "source_only_golden_oracle", "oracle_priority": "high", "triage_code": "behavior_edge_case_probe"}
            for _ in range(18)
        ]

        summary = queue.summarize_queue(items=items, accepted_direct=5, design_candidate_count=23)

        self.assertEqual(summary["additional_acceptances_needed_for_20_primary"], 15)
        self.assertEqual(summary["maximum_admitted_design_count_if_all_oracles_pass"], 23)
        self.assertTrue(summary["can_reach_20_primary_if_all_oracles_pass"])
        self.assertFalse(summary["can_reach_20_primary_plus_5_reserve_under_current_design_supply"])
        self.assertEqual(summary["candidate_pool_gap_to_40"], 17)

    def test_source_only_public_item_redacts_raw_commit_and_subject(self) -> None:
        """Public queue items publish digests instead of raw source anchors or titles."""
        item = queue.public_source_oracle_item(
            {
                "commit": "a" * 40,
                "base_commit": "b" * 40,
                "subject": "support html inline",
                "committed_at": "2026-04-12T00:00:00+00:00",
                "window": "W_star",
                "family": "parser/mixed integration",
                "surface": "source_without_tests",
                "source_file_count": 2,
                "test_file_count": 0,
                "test_node_count": 0,
                "source_files": ["rich/default_styles.py", "rich/markdown.py"],
                "test_files": [],
                "changed_file_set_digest": "digest",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            },
            index=1,
        )

        serialized = str(item)
        self.assertEqual(item["work_item_kind"], "source_only_golden_oracle")
        self.assertEqual(item["oracle_priority"], "high")
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("b" * 40, serialized)
        self.assertNotIn("support html inline", serialized)
        self.assertIn("source_anchor_digest", item)
        self.assertIn("subject_digest", item)

    def test_rejected_direct_candidates_enter_replacement_queue(self) -> None:
        """No-op-passing direct candidates need replacement hidden verifiers."""
        direct_batch = {
            "results": [
                {"admission_decision": "accepted", "source_anchor_digest": "accepted"},
                {
                    "admission_decision": "rejected",
                    "source_anchor_digest": "rejected",
                    "base_anchor_digest": "base",
                    "subject_digest": "subject",
                    "changed_file_set_digest": "files",
                    "family": "parser/mixed integration",
                    "surface": "source_and_tests",
                    "source_file_count": 1,
                    "test_file_count": 1,
                    "test_node_count": 2,
                    "no_op_result": {"status": "passed_unexpected"},
                    "reference_result": {"status": "passed"},
                },
            ]
        }

        items = queue.build_queue_items([], direct_batch)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["work_item_kind"], "direct_smoke_replacement_oracle")
        self.assertEqual(items[0]["oracle_priority"], "high")
        self.assertEqual(items[0]["triage_code"], "non_discriminating_existing_test")

    def test_low_signal_source_subjects_are_deprioritized(self) -> None:
        """Cosmetic source-only changes should not consume early Oracle attention."""
        triage = queue.triage_source_only_candidate({"subject": "fix docstring"})

        self.assertEqual(triage["oracle_priority"], "low")
        self.assertEqual(triage["triage_code"], "deprioritized_low_behavior_signal")

    def test_direct_batch_artifact_is_required(self) -> None:
        """Queue construction fails explicitly if direct-smoke evidence is missing."""
        with self.assertRaises(ToolError):
            queue.load_direct_batch(Path("/tmp/barcarolle-missing-direct-batch.json"))


if __name__ == "__main__":
    unittest.main()
