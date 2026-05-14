#!/usr/bin/env python3
"""Executable specs for Rich source-only Golden-Oracle smoke pilots."""

from __future__ import annotations

import unittest

from _common import ToolError
import rich_source_oracle_pilot as pilot


class RichSourceOraclePilotTests(unittest.TestCase):
    def kbd_candidate(self) -> dict[str, object]:
        return {
            "commit": "a" * 40,
            "base_commit": "b" * 40,
            "subject": "support html inline",
            "family": "parser/mixed integration",
            "surface": "source_without_tests",
            "source_files": ["rich/default_styles.py", "rich/markdown.py"],
            "test_files": [],
            "source_file_count": 2,
            "test_file_count": 0,
            "test_node_count": 0,
            "changed_file_set_digest": "digest",
        }

    def test_hidden_verifier_template_covers_inline_kbd_html_behavior(self) -> None:
        """The pilot verifier checks observable inline rendering and markdown.kbd style registration."""
        verifier = pilot.hidden_verifier_for_candidate(self.kbd_candidate())

        self.assertEqual(verifier["oracle_template"], "markdown_inline_kbd_html")
        self.assertEqual(verifier["test_node_count"], 1)
        self.assertIn("tests/test_markdown_html_inline_kbd.py", verifier["command"])
        self.assertIn("markdown.kbd", verifier["hidden_files"][0]["content"])
        self.assertIn("output.startswith(\"Press \")", verifier["hidden_files"][0]["content"])
        self.assertIn("style.color is not None", verifier["hidden_files"][0]["content"])

    def test_unknown_source_only_candidate_blocks_without_template(self) -> None:
        """Source-only pilots fail closed when no hidden-verifier template exists."""
        candidate = self.kbd_candidate()
        candidate["subject"] = "remove comments"
        candidate["source_files"] = ["rich/markdown.py"]

        with self.assertRaises(ToolError):
            pilot.hidden_verifier_for_candidate(candidate)

    def test_public_result_redacts_raw_source_anchors_and_subject(self) -> None:
        """Public pilot results keep raw commits, subjects, and hidden files private."""
        candidate = self.kbd_candidate()
        verifier = pilot.hidden_verifier_for_candidate(candidate)
        result = pilot.public_result(
            candidate=candidate,
            verifier=verifier,
            reference_patch_digest="patch-digest",
            reference_patch_bytes=123,
            noop={"status": "failed", "verifier_exit_code": 1},
            reference={"status": "passed", "verifier_exit_code": 0},
            private_root="experiments/core_narrative/large_artifacts/example",
        )

        serialized = str(result)
        self.assertEqual(result["admission_decision"], "accepted")
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("b" * 40, serialized)
        self.assertNotIn("support html inline", serialized)
        self.assertNotIn("test_markdown_html_inline_kbd.py", serialized)
        self.assertIn("hidden_verifier_digest", result)


if __name__ == "__main__":
    unittest.main()
