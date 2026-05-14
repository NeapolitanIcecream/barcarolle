#!/usr/bin/env python3
"""Executable specs for source-only repository localization hints."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import repository_localization_hints as hints


class RepositoryLocalizationHintsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "src" / "pkg" / "progress.py").write_text(
            "class Progress:\n    def refresh(self):\n        return 'progress refresh'\n",
            encoding="utf-8",
        )
        (self.root / "src" / "pkg" / "table.py").write_text("def render_table():\n    return 'table'\n", encoding="utf-8")

    def test_localization_uses_public_statement_terms_to_rank_files(self) -> None:
        """A behavior statement can surface likely files without target diffs or verifier data."""
        statement = self.root / "statement.md"
        statement.write_text("Fix progress refresh rendering.\n", encoding="utf-8")

        payload = hints.localize(self.root, statement)

        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["policy"]["source_material"], "public_statement_and_repo_source_only")
        self.assertEqual(payload["files"][0]["path"], "src/pkg/progress.py")
        self.assertIn("Progress.refresh", [item["symbol"] for item in payload["symbols"]])

    def test_forbidden_statement_markers_block_hint_generation(self) -> None:
        """Target commits, diffs, reference patches, and hidden verifiers are rejected."""
        statement = self.root / "statement.md"
        statement.write_text("diff --git a/src/pkg/progress.py b/src/pkg/progress.py\n", encoding="utf-8")

        payload = hints.localize(self.root, statement)

        self.assertEqual(payload["status"], "blocked_forbidden_public_statement")
        self.assertIn("implementation_diff", payload["forbidden_findings"])

    def test_cli_writes_machine_readable_hints(self) -> None:
        """The CLI emits a JSON artifact usable as ACUT diagnostic input."""
        statement = self.root / "statement.md"
        statement.write_text("Fix progress refresh rendering.\n", encoding="utf-8")
        output = self.root / "hints.json"

        exit_code = hints.run(["--repo", str(self.root), "--statement", str(statement), "--output", str(output)])

        self.assertEqual(exit_code, 0)
        data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["files"])


if __name__ == "__main__":
    unittest.main()
