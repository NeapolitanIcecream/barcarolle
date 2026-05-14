#!/usr/bin/env python3
"""Executable specs for Rich replacement-oracle smoke pilots."""

from __future__ import annotations

import unittest

from _common import ToolError
import rich_replacement_oracle_pilot as pilot


class RichReplacementOraclePilotTests(unittest.TestCase):
    def candidate(self) -> dict[str, object]:
        return {
            "commit": "a" * 40,
            "base_commit": "b" * 40,
            "subject": "fix for infinite loop in split_graphemes",
            "family": "parser/mixed integration",
            "surface": "source_and_tests",
            "source_files": ["rich/cells.py"],
            "test_files": ["tests/test_cells.py"],
            "source_file_count": 1,
            "test_file_count": 1,
            "test_node_count": 1,
            "changed_file_set_digest": "digest",
        }

    def test_hidden_verifier_template_covers_split_graphemes_timeout(self) -> None:
        """The replacement verifier turns an infinite loop into a bounded pytest failure."""
        verifier = pilot.hidden_verifier_for_candidate(self.candidate())

        self.assertEqual(verifier["oracle_template"], "split_graphemes_leading_zero_width_timeout")
        self.assertIn("tests/test_cells_split_graphemes_timeout.py", verifier["command"])
        self.assertIn("signal.alarm(1)", verifier["hidden_files"][0]["content"])
        self.assertIn('split_graphemes("\\u0301")', verifier["hidden_files"][0]["content"])

    def test_unknown_replacement_candidate_blocks_without_template(self) -> None:
        """Replacement pilots fail closed when no hidden-verifier template exists."""
        candidate = self.candidate()
        candidate["subject"] = "refinements, and tests"

        with self.assertRaises(ToolError):
            pilot.hidden_verifier_for_candidate(candidate)

    def test_public_result_redacts_raw_source_anchors_subject_and_hidden_test(self) -> None:
        """Public replacement results keep raw source and hidden verifier details private."""
        candidate = self.candidate()
        verifier = pilot.hidden_verifier_for_candidate(candidate)
        result = pilot.public_result(
            candidate=candidate,
            direct_result={
                "batch_candidate_index": 8,
                "no_op_result": {"status": "passed_unexpected"},
                "reference_result": {"status": "passed"},
            },
            verifier=verifier,
            reference_patch_digest="patch-digest",
            reference_patch_bytes=123,
            noop={"status": "failed", "verifier_exit_code": 1},
            reference={"status": "passed", "verifier_exit_code": 0},
            private_root="experiments/core_narrative/large_artifacts/example",
        )

        serialized = str(result)
        self.assertEqual(result["admission_decision"], "accepted")
        self.assertEqual(result["batch_candidate_index"], 8)
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("b" * 40, serialized)
        self.assertNotIn("fix for infinite loop", serialized)
        self.assertNotIn("test_cells_split_graphemes_timeout.py", serialized)


if __name__ == "__main__":
    unittest.main()
