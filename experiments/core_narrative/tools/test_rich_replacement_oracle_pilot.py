#!/usr/bin/env python3
"""Executable specs for Rich replacement-oracle smoke pilots."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

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
        candidate["subject"] = "unhandled replacement candidate"

        with self.assertRaises(ToolError):
            pilot.hidden_verifier_for_candidate(candidate)

    def test_hidden_verifier_template_covers_zero_width_span_behavior(self) -> None:
        """The span verifier checks that leading zero-width characters are represented."""
        candidate = self.candidate()
        candidate["subject"] = "test cases"
        verifier = pilot.hidden_verifier_for_candidate(candidate)

        self.assertEqual(verifier["oracle_template"], "split_graphemes_leading_zero_width_span")
        self.assertIn("tests/test_cells_split_graphemes_zero_width_span.py", verifier["command"])
        self.assertIn("spans == [(0, 1, 0)]", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_variation_selector_timeout(self) -> None:
        """The refinement verifier checks leading zero-width plus VS16 handling."""
        candidate = self.candidate()
        candidate["subject"] = "refinements, and tests"
        verifier = pilot.hidden_verifier_for_candidate(candidate)

        self.assertEqual(verifier["oracle_template"], "split_graphemes_leading_zero_width_variation_selector")
        self.assertIn("tests/test_cells_split_graphemes_variation_selector.py", verifier["command"])
        self.assertIn("signal.alarm(1)", verifier["hidden_files"][0]["content"])
        self.assertIn("spans == [(0, 2, 0)]", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_templates_cover_rich_c_replacement_candidates(self) -> None:
        """The C replacement queue has templates for rejected direct-smoke candidates."""
        cases = [
            (
                "test fixes",
                ["rich/style.py"],
                "style_hash_attrgetter_pickle",
                "tests/test_style_hash_attrgetter.py",
                "_hash_getter",
            ),
            (
                "padding property",
                ["rich/syntax.py"],
                "syntax_padding_property_descriptor",
                "tests/test_syntax_padding_property_descriptor.py",
                "PaddingProperty",
            ),
            (
                "Fix small typo in comments",
                ["rich/_inspect.py"],
                "inspect_docstring_comment_typo",
                "tests/test_inspect_docstring_typo.py",
                "doctring",
            ),
        ]

        for subject, source_files, template, test_path, content_needle in cases:
            with self.subTest(subject=subject):
                candidate = self.candidate()
                candidate["subject"] = subject
                candidate["source_files"] = source_files

                verifier = pilot.hidden_verifier_for_candidate(candidate)

                self.assertEqual(verifier["oracle_template"], template)
                self.assertIn(test_path, verifier["command"])
                self.assertIn(content_needle, verifier["hidden_files"][0]["content"])

    def test_select_candidate_uses_requested_split_and_c_scan_start(self) -> None:
        """Replacement pilots use the requested split and C extension boundary."""
        direct_batch = {"results": [{"batch_candidate_index": 2, "admission_decision": "rejected"}]}
        c_scan_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)
        seen = {}

        def fake_direct_candidates(repo_path: Path, split: str, *, c_scan_start=None):
            seen["split"] = split
            seen["c_scan_start"] = c_scan_start
            return [{"subject": "first"}, {"subject": "second"}]

        with patch.object(pilot, "direct_candidates", side_effect=fake_direct_candidates):
            candidate, direct_result = pilot.select_candidate(
                Path("/repo"),
                direct_batch,
                2,
                "C",
                c_scan_start=c_scan_start,
            )

        self.assertEqual(candidate["subject"], "second")
        self.assertEqual(direct_result["batch_candidate_index"], 2)
        self.assertEqual(seen["split"], "C")
        self.assertEqual(seen["c_scan_start"], c_scan_start)

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
