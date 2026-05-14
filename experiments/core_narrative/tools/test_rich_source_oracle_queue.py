#!/usr/bin/env python3
"""Executable specs for Rich Golden-Oracle queue construction."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

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

    def test_queue_items_respect_requested_split(self) -> None:
        """Oracle construction only queues candidates from the requested time split."""
        candidates = [
            {
                "commit": "c" * 40,
                "base_commit": "d" * 40,
                "subject": "support R edge case",
                "committed_at": "2026-01-12T00:00:00+00:00",
                "window": "R",
                "family": "parser/mixed integration",
                "surface": "source_without_tests",
                "source_file_count": 1,
                "test_file_count": 0,
                "test_node_count": 0,
                "source_files": ["rich/segment.py"],
                "test_files": [],
                "changed_file_set_digest": "r-files",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            },
            {
                "commit": "e" * 40,
                "base_commit": "f" * 40,
                "subject": "support W star edge case",
                "committed_at": "2026-04-12T00:00:00+00:00",
                "window": "W_star",
                "family": "rendering/layout",
                "surface": "source_without_tests",
                "source_file_count": 2,
                "test_file_count": 0,
                "test_node_count": 0,
                "source_files": ["rich/console.py", "rich/panel.py"],
                "test_files": [],
                "changed_file_set_digest": "w-files",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            },
        ]

        items = queue.build_queue_items(candidates, {}, split="R")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["changed_file_set_digest"], "r-files")

    def test_build_payload_rejects_direct_batch_from_another_split(self) -> None:
        """Split mismatches are reported before queue artifacts are generated."""
        with tempfile.TemporaryDirectory() as directory:
            direct_batch_path = Path(directory) / "direct.json"
            direct_batch_path.write_text('{"split": "W_star"}', encoding="utf-8")

            with self.assertRaises(ToolError) as raised:
                queue.build_payload(
                    repo_path=Path(directory) / "repo",
                    direct_batch_path=direct_batch_path,
                    private_root=Path(directory) / "private",
                    split="R",
                )

        self.assertEqual(raised.exception.details["direct_batch_split"], "W_star")
        self.assertEqual(raised.exception.details["split"], "R")

    def test_build_payload_treats_missing_direct_batch_split_as_w_star(self) -> None:
        """Legacy direct-smoke batches without a split field cannot seed R/C queues."""
        with tempfile.TemporaryDirectory() as directory:
            direct_batch_path = Path(directory) / "legacy-direct.json"
            direct_batch_path.write_text('{"accepted_count": 0}', encoding="utf-8")

            with self.assertRaises(ToolError) as raised:
                queue.build_payload(
                    repo_path=Path(directory) / "repo",
                    direct_batch_path=direct_batch_path,
                    private_root=Path(directory) / "private",
                    split="R",
                )

        self.assertEqual(raised.exception.details["direct_batch_split"], "W_star")
        self.assertEqual(raised.exception.details["split"], "R")

    def test_run_forwards_requested_split_to_payload_builder(self) -> None:
        """The CLI split flag controls the queue split used for payload construction."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "queue.json"
            report = Path(directory) / "queue.md"
            captured: dict[str, object] = {}

            def fake_build_payload(**kwargs: object) -> dict[str, object]:
                captured.update(kwargs)
                return {
                    "schema_version": queue.SCHEMA_VERSION,
                    "tool": queue.TOOL,
                    "status": "completed",
                    "generated_at": "2026-05-15T00:00:00Z",
                    "split": kwargs["split"],
                    "denominator_boundary": {},
                }

            with patch.object(queue, "build_payload", side_effect=fake_build_payload), patch.object(queue, "emit_json"):
                exit_code = queue.run(["--split", "R", "--output", str(output), "--report", str(report)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["split"], "R")

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
