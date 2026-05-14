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

    def test_hidden_verifier_template_covers_lazy_emoji_import_behavior(self) -> None:
        """The emoji pilot verifier checks lazy loading before the first emoji lookup."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "lazy load emoji",
                "source_files": ["rich/_emoji_replace.py", "rich/emoji.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "emoji_code_table_lazy_import")
        self.assertIn("tests/test_emoji_lazy_import.py", verifier["command"])
        self.assertIn("rich._emoji_codes", verifier["hidden_files"][0]["content"])
        self.assertIn("Emoji(\"smiley\")", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_link_id_counter_behavior(self) -> None:
        """The link-ID pilot verifier checks adjacent generated counter prefixes."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "Use faster generator for link IDs",
                "source_files": ["rich/style.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "style_link_id_counter_sequence")
        self.assertIn("tests/test_style_link_id_sequence.py", verifier["command"])
        self.assertIn("prefixes[1] == prefixes[0] + 1", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_currentframe_none_behavior(self) -> None:
        """The currentframe verifier checks None falls back to inspect.currentframe."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "made current frame None-able",
                "source_files": ["rich/console.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "console_caller_frame_currentframe_none")
        self.assertIn("tests/test_console_currentframe_none.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("_permit_pep604_typing_aliases", content)
        self.assertIn("currentframe=None", content)

    def test_hidden_verifier_template_covers_lazy_pretty_import_behavior(self) -> None:
        """The lazy-is-expandable verifier checks plain text avoids eager pretty imports."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "lazy is_expandable",
                "source_files": ["rich/console.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "console_collect_renderables_lazy_pretty_import")
        self.assertIn("tests/test_console_lazy_pretty_import.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn('sys.modules.pop("rich.pretty", None)', content)
        self.assertIn('assert "rich.pretty" not in sys.modules', content)

    def test_hidden_verifier_template_covers_console_pathlike_annotations(self) -> None:
        """The drop-3.8 verifier checks save helpers expose typed PathLike[str] annotations."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "drop 3.8",
                "source_files": ["rich/console.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "console_save_pathlike_str_annotations")
        self.assertIn("tests/test_console_pathlike_annotations.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn('("save_text", "save_html", "save_svg")', content)
        self.assertIn("typing.get_args(candidate) == (str,)", content)

    def test_hidden_verifier_template_covers_dead_svg_hash_removal(self) -> None:
        """The SVG hash verifier checks the obsolete private helper is absent."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "refactor: remove dead _svg_hash function",
                "source_files": ["rich/console.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "console_dead_svg_hash_removed")
        self.assertIn("tests/test_console_svg_hash_removed.py", verifier["command"])
        self.assertIn('not hasattr(console_module, "_svg_hash")', verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_emoji_module_main_import(self) -> None:
        """The emoji main verifier checks the module entrypoint imports the lazy code table."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "import",
                "source_files": ["rich/emoji.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "emoji_module_main_lazy_codes_import")
        self.assertIn("tests/test_emoji_module_main.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn('runpy.run_module("rich.emoji", run_name="__main__")', content)
        self.assertIn("contextlib.redirect_stdout", content)

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
