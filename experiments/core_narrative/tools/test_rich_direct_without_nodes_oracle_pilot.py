#!/usr/bin/env python3
"""Executable specs for Rich direct-without-node Oracle smoke pilots."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

from _common import ToolError
import rich_direct_without_nodes_oracle_pilot as pilot


class RichDirectWithoutNodesOraclePilotTests(unittest.TestCase):
    def candidate(self) -> dict[str, object]:
        return {
            "commit": "a" * 40,
            "base_commit": "b" * 40,
            "subject": "perf: eliminate inspect imports from protocol.py, repr.py, and syntax.py",
            "family": "traceback/logging/inspect",
            "surface": "source_and_tests",
            "source_files": ["rich/protocol.py", "rich/repr.py", "rich/syntax.py"],
            "test_files": ["tests/test_syntax.py"],
            "source_file_count": 3,
            "test_file_count": 1,
            "test_node_count": 0,
            "changed_file_set_digest": "digest",
        }

    def test_hidden_verifier_template_covers_import_side_effects(self) -> None:
        """The verifier checks import-only paths avoid eager inspect and Console imports."""
        verifier = pilot.hidden_verifier_for_candidate(self.candidate())

        self.assertEqual(verifier["oracle_template"], "import_side_effects_lazy_inspect_console")
        self.assertEqual(verifier["command"], ".venv/bin/python tests/check_import_side_effects.py")
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("rich.protocol", content)
        self.assertIn("rich.repr", content)
        self.assertIn("rich.syntax", content)
        self.assertIn("rich.console", content)
        self.assertIn('if __name__ == "__main__"', content)

    def test_unknown_direct_without_node_candidate_blocks_without_template(self) -> None:
        """Direct-without-node pilots fail closed when no hidden-verifier template exists."""
        candidate = self.candidate()
        candidate["subject"] = "unknown import cleanup"

        with self.assertRaises(ToolError):
            pilot.hidden_verifier_for_candidate(candidate)

    def test_hidden_verifier_template_covers_rich_c_py38_branch_removal(self) -> None:
        """The C direct-without-node verifier checks Python 3.8 branch removal."""
        candidate = self.candidate()
        candidate["subject"] = "Remove all `sys.version_info >= (3, 8)` checks as Python 3.7 is no longer supported"
        candidate["source_files"] = [
            "rich/_ratio.py",
            "rich/align.py",
            "rich/box.py",
            "rich/console.py",
            "rich/control.py",
            "rich/emoji.py",
            "rich/live_render.py",
            "rich/markdown.py",
            "rich/progress.py",
        ]

        verifier = pilot.hidden_verifier_for_candidate(candidate)

        self.assertEqual(verifier["oracle_template"], "py38_compat_branch_removal")
        self.assertIn("tests/test_py38_branch_removal.py", verifier["command"])
        content = verifier["hidden_files"][0]["content"]
        self.assertIn("sys.version_info >= (3, 8)", content)
        self.assertIn("from typing import Literal, Protocol, runtime_checkable", content)

    def test_direct_without_nodes_candidates_passes_split_and_c_scan_start(self) -> None:
        """C direct-without-node discovery uses the C extension boundary."""
        c_scan_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)
        seen = {}

        def fake_discover(repo_path: Path, *, c_scan_start=None):
            seen["c_scan_start"] = c_scan_start
            return [
                {"window": "C", "oracle_requirement": "direct_tests_without_extractable_nodes", "subject": "candidate"},
                {"window": "W_star", "oracle_requirement": "direct_tests_without_extractable_nodes", "subject": "wrong split"},
            ]

        with patch.object(pilot, "discover_candidates", side_effect=fake_discover):
            candidates = pilot.direct_without_nodes_candidates(Path("/repo"), "C", c_scan_start=c_scan_start)

        self.assertEqual([candidate["subject"] for candidate in candidates], ["candidate"])
        self.assertEqual(seen["c_scan_start"], c_scan_start)

    def test_public_result_redacts_raw_source_anchors_subject_and_hidden_script(self) -> None:
        """Public direct-without-node results keep raw source and hidden script details private."""
        candidate = self.candidate()
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
        self.assertNotIn("eliminate inspect imports", serialized)
        self.assertNotIn("check_import_side_effects.py", serialized)


if __name__ == "__main__":
    unittest.main()
