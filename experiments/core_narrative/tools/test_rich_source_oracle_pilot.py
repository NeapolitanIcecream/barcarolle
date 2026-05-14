#!/usr/bin/env python3
"""Executable specs for Rich source-only Golden-Oracle smoke pilots."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

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
        candidate["subject"] = "ws"
        candidate["source_files"] = ["rich/ansi.py"]

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

    def test_hidden_verifier_template_covers_caller_frame_docstring(self) -> None:
        """The docstring verifier checks the caller-frame helper documents None correctly."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "fix docstring",
                "source_files": ["rich/console.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "console_caller_frame_docstring_none_default")
        self.assertIn("tests/test_console_caller_frame_docstring.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("Defaults to None", content)
        self.assertIn("inspect.currentframe()", content)

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

    def test_hidden_verifier_template_covers_split_graphemes_docstring_spelling(self) -> None:
        """The spelling verifier checks the split_graphemes docstring typo is gone."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": " spelling",
                "source_files": ["rich/cells.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cells_split_graphemes_docstring_spelling")
        self.assertIn("tests/test_cells_split_graphemes_docstring.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn('"additionally" in doc', content)
        self.assertIn('"additonally" not in doc', content)

    def test_hidden_verifier_template_covers_stale_markdown_comment_removal(self) -> None:
        """The comment-removal verifier checks obsolete commented TableDataElement code is absent."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "remove comments",
                "source_files": ["rich/markdown.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "markdown_tabledata_stale_comments_removed")
        self.assertIn("tests/test_markdown_stale_comments_removed.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("# text = Text(text)", content)
        self.assertIn("# self.content.append_text(text)", content)

    def test_hidden_verifier_template_covers_split_lines_terminator(self) -> None:
        """The R verifier checks newline termination is exposed per split line."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "split lines terminator",
                "source_files": ["rich/console.py", "rich/segment.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "segment_split_lines_terminator")
        self.assertIn("tests/test_segment_split_lines_terminator.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("split_lines_terminator", content)
        self.assertIn('(["alpha"], True)', content)

    def test_hidden_verifier_template_covers_cached_cell_len_unicode_version(self) -> None:
        """The R cache verifier checks short text accepts a unicode_version key."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "restore caching behavior",
                "source_files": ["rich/cells.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cells_cached_len_unicode_version")
        self.assertIn("tests/test_cells_cached_len_unicode_version.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn('cached_cell_len("abc", "latest")', content)
        self.assertIn("cache_info().misses == 2", content)

    def test_hidden_verifier_template_covers_traceback_locals_options(self) -> None:
        """The R traceback verifier checks new locals rendering options are accepted."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "feat: Traceback - Expose more locals rendering options",
                "source_files": ["rich/scope.py", "rich/traceback.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "traceback_locals_depth_overflow_options")
        self.assertIn("tests/test_traceback_locals_options.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("locals_max_depth=1", content)
        self.assertIn('locals_overflow="ellipsis"', content)

    def test_hidden_verifier_template_covers_disabled_progress_stop_output(self) -> None:
        """The R progress verifier checks disabled progress emits no blank line."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "Update progress.py",
                "source_files": ["rich/progress.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "progress_disabled_stop_no_blank_line")
        self.assertIn("tests/test_progress_disabled_stop_output.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("Progress(console=console, disable=True)", content)
        self.assertIn('stream.getvalue() == ""', content)

    def test_hidden_verifier_template_covers_py38_unicode_cache_fallback(self) -> None:
        """The R unicode verifier checks fallback when functools.cache is unavailable."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "py3.8 fix",
                "source_files": ["rich/_unicode_data/__init__.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "unicode_data_py38_cache_fallback")
        self.assertIn("tests/test_unicode_data_py38_cache_fallback.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("fake_functools.lru_cache", content)
        self.assertIn('namespace["cache"] is functools.lru_cache', content)

    def test_hidden_verifier_template_covers_unicode_data_loader(self) -> None:
        """The R unicode loader verifier checks latest table import."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "f string path",
                "source_files": ["rich/_unicode_data/__init__.py", "rich/_unicode_data/_versions.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "unicode_data_load_latest_table")
        self.assertIn("tests/test_unicode_data_load_latest.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("module_name", content)
        self.assertIn('"17.0.0"', content)

    def test_hidden_verifier_template_covers_unicode_invalid_version_fallback(self) -> None:
        """The R unicode fallback verifier checks invalid version handling."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "test",
                "source_files": ["rich/_unicode_data/__init__.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "unicode_data_invalid_version_fallback")
        self.assertIn("tests/test_unicode_data_invalid_version_fallback.py", verifier["command"])
        self.assertIn("version_numbers = _parse_version(VERSIONS[-1])", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_cell_string_api(self) -> None:
        """The R CellString verifier checks basic string-like behavior."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "cell string class",
                "source_files": ["rich/cell_string.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cell_string_basic_api")
        self.assertIn("tests/test_cell_string_basic_api.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("exec(compile", content)
        self.assertIn("CellString(\"abc\")", content)
        self.assertIn("list(value)", content)

    def test_hidden_verifier_template_covers_cell_table_api(self) -> None:
        """The R CellTable verifier checks unicode metadata storage."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "cell tables",
                "source_files": ["rich/cell_string.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cell_table_metadata_api")
        self.assertIn("tests/test_cell_string_table_api.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("exec(compile", content)
        self.assertIn("CellTable(\"probe\"", content)
        self.assertIn("narrow_to_wide", content)

    def test_hidden_verifier_template_covers_cell_split_text(self) -> None:
        """The R split-text verifier checks splitting at a cell offset."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "split text",
                "source_files": ["rich/_unicode_data/__init__.py", "rich/cell_string.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cell_string_split_text")
        self.assertIn("tests/test_cell_string_split_text.py", verifier["command"])
        self.assertIn("def split_text(", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_pretty_ipython_custom_console(self) -> None:
        """The R pretty verifier checks IPython formatting uses the installed console."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "Respect custom console instance in IPython output",
                "source_files": ["rich/pretty.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "pretty_ipython_custom_console")
        self.assertIn("tests/test_pretty_ipython_custom_console.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("fake_ipython.display_formatter", content)
        self.assertIn('captured["console"] is custom_console', content)

    def test_hidden_verifier_template_covers_progress_reset_docstring(self) -> None:
        """The R progress-doc verifier checks visible=None documentation."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "docstring",
                "source_files": ["rich/progress.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "progress_reset_visible_docstring")
        self.assertIn("tests/test_progress_reset_visible_docstring.py", verifier["command"])
        self.assertIn("Set visible flag if not None.", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_cells_variation_selector_simplification(self) -> None:
        """The R cells verifier checks the simplified variation-selector branch."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "simplify",
                "source_files": ["rich/cells.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cells_variation_selector_branch_simplified")
        self.assertIn("tests/test_cells_variation_selector_simplified.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("character ==", content)
        self.assertIn("last_measured_character", content)

    def test_hidden_verifier_template_covers_cells_binary_search_unpack(self) -> None:
        """The R cells verifier checks direct tuple unpacking in binary search."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "refine",
                "source_files": ["rich/cells.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "cells_binary_search_entry_unpack")
        self.assertIn("tests/test_cells_binary_search_unpack.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("start, end, width = table[index]", content)
        self.assertIn("entry = table[index]", content)

    def test_hidden_verifier_template_covers_unicode_fallback_comment(self) -> None:
        """The R unicode verifier checks the completed fallback comment."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "Update rich/_unicode_data/__init__.py",
                "source_files": ["rich/_unicode_data/__init__.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "unicode_data_fallback_comment_completed")
        self.assertIn("tests/test_unicode_data_fallback_comment.py", verifier["command"])
        self.assertIn("seems reasonable", verifier["hidden_files"][0]["content"])

    def test_hidden_verifier_template_covers_unicode_cell_table_import(self) -> None:
        """The R unicode verifier checks the CellTable type-checking import."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "remove reference to cell strings",
                "source_files": ["rich/_unicode_data/__init__.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "unicode_data_cell_table_type_import")
        self.assertIn("tests/test_unicode_data_cell_table_type_import.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("from rich.cells import CellTable", content)
        self.assertIn("from rich.cell_string import CellTable", content)

    def test_hidden_verifier_template_covers_table_column_doc_cleanup(self) -> None:
        """The R table verifier checks the removed Column expand doc entry."""
        verifier = pilot.hidden_verifier_for_candidate(
            {
                "subject": "remove error docstring",
                "source_files": ["rich/table.py"],
            }
        )

        self.assertEqual(verifier["oracle_template"], "table_column_expand_doc_removed")
        self.assertIn("tests/test_table_column_expand_doc_removed.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("expand (bool, optional)", content)
        self.assertIn("source.count(expand_doc) == 2", content)

    def test_hidden_verifier_templates_cover_rich_c_source_oracle_candidates(self) -> None:
        """The C source-only queue has templates for each current source-only candidate."""
        cases = [
            (
                "Fix two typos",
                ["rich/text.py"],
                "text_append_docstring_typo_fixed",
                "tests/test_text_append_docstring_typo.py",
                "more performant than Text.append",
            ),
            (
                "fix(logging): fix tracebacks_code_width type hint",
                ["rich/logging.py"],
                "logging_tracebacks_code_width_optional_type",
                "tests/test_logging_tracebacks_code_width_type.py",
                "Optional[int]",
            ),
            (
                "optimize size",
                ["rich/console.py"],
                "console_options_single_size_lookup",
                "tests/test_console_options_size_lookup.py",
                "size_lookups == 1",
            ),
            (
                "sponsorship message",
                ["rich/__main__.py"],
                "rich_main_sponsor_panel_message",
                "tests/test_rich_main_sponsor_message.py",
                "github.com/sponsors/willmcgugan",
            ),
            (
                "indentation",
                ["rich/syntax.py"],
                "syntax_guess_lexer_docstring_indent",
                "tests/test_syntax_guess_lexer_docstring_indent.py",
                "path (AnyStr)",
            ),
            (
                "detect recursion in Exception Groups",
                ["rich/traceback.py"],
                "traceback_exception_group_recursion_guard",
                "tests/test_traceback_exception_group_recursion.py",
                "grouped_exceptions.add(exception)",
            ),
            (
                "name change",
                ["rich/traceback.py"],
                "traceback_visited_exceptions_name",
                "tests/test_traceback_visited_exceptions_name.py",
                "_visited_exceptions",
            ),
            (
                "no need for this",
                ["rich/traceback.py"],
                "traceback_duplicate_group_preserves_group_flag",
                "tests/test_traceback_duplicate_group_flag.py",
                "stack.is_group = False",
            ),
            (
                "docs",
                ["rich/live.py"],
                "live_render_stack_comment",
                "tests/test_live_stack_render_comment.py",
                "The first Live instance",
            ),
            (
                "nested flag",
                ["rich/console.py", "rich/live.py"],
                "live_nested_flag_refresh",
                "tests/test_live_nested_flag.py",
                "self._nested = False",
            ),
            (
                "permit nested live",
                ["rich/console.py", "rich/live.py"],
                "console_live_stack_allows_nested_live",
                "tests/test_console_live_stack.py",
                "_live_stack",
            ),
            (
                "avoid displaying spinners in a table",
                ["rich/spinner.py"],
                "spinner_main_group_without_table_panel",
                "tests/test_spinner_main_group.py",
                "all_spinners = Group(",
            ),
            (
                "Add back `# pragma: no cover`",
                ["rich/progress.py"],
                "progress_self_type_checking_no_cover",
                "tests/test_progress_self_no_cover.py",
                "# pragma: no cover",
            ),
        ]

        for subject, source_files, template, test_path, content_needle in cases:
            with self.subTest(subject=subject):
                verifier = pilot.hidden_verifier_for_candidate(
                    {
                        "subject": subject,
                        "source_files": source_files,
                    }
                )

                self.assertEqual(verifier["oracle_template"], template)
                self.assertIn(test_path, verifier["command"])
                self.assertIn(content_needle, verifier["hidden_files"][0]["content"])

    def test_source_only_candidates_respect_requested_split(self) -> None:
        """R queue pilots select source-only candidates from R, not W*."""
        candidates = [
            {
                "commit": "a" * 40,
                "base_commit": "b" * 40,
                "subject": "split lines terminator",
                "committed_at": "2026-01-23T00:00:00+00:00",
                "window": "R",
                "family": "console/rendering",
                "surface": "source_without_tests",
                "source_files": ["rich/console.py", "rich/segment.py"],
                "test_files": [],
                "source_file_count": 2,
                "test_file_count": 0,
                "test_node_count": 0,
                "changed_file_set_digest": "r-files",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            },
            {
                "commit": "c" * 40,
                "base_commit": "d" * 40,
                "subject": "support html inline",
                "committed_at": "2026-04-12T00:00:00+00:00",
                "window": "W_star",
                "family": "parser/mixed integration",
                "surface": "source_without_tests",
                "source_files": ["rich/default_styles.py", "rich/markdown.py"],
                "test_files": [],
                "source_file_count": 2,
                "test_file_count": 0,
                "test_node_count": 0,
                "changed_file_set_digest": "w-files",
                "oracle_requirement": "golden_oracle_required",
                "direct_smoke_ready": False,
            },
        ]

        with patch.object(pilot, "discover_candidates", return_value=candidates):
            selected = pilot.source_only_oracle_candidates(Path("/repo"), split="R")

        self.assertEqual([candidate["subject"] for candidate in selected], ["split lines terminator"])

    def test_source_only_candidates_passes_extended_c_scan_start(self) -> None:
        """C source-only pilots can use the preregistered earlier C boundary."""
        seen = {}

        def fake_discover(repo_path: Path, *, c_scan_start=None):
            seen["c_scan_start"] = c_scan_start
            return [
                {
                    "commit": "a" * 40,
                    "base_commit": "b" * 40,
                    "subject": "candidate",
                    "committed_at": "2025-04-14T00:00:00+00:00",
                    "window": "C",
                    "family": "parser/mixed integration",
                    "surface": "source_without_tests",
                    "source_file_count": 1,
                    "test_file_count": 0,
                    "test_node_count": 0,
                    "changed_file_set_digest": "digest",
                    "oracle_requirement": "golden_oracle_required",
                    "direct_smoke_ready": False,
                },
                {
                    "subject": "direct",
                    "window": "C",
                    "family": "parser/mixed integration",
                    "oracle_requirement": "direct_reference_tests_available",
                },
            ]

        c_scan_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)
        with patch.object(pilot, "discover_candidates", side_effect=fake_discover):
            selected = pilot.source_only_oracle_candidates(Path("/repo"), split="C", c_scan_start=c_scan_start)

        self.assertEqual([candidate["subject"] for candidate in selected], ["candidate"])
        self.assertEqual(seen["c_scan_start"], c_scan_start)

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
