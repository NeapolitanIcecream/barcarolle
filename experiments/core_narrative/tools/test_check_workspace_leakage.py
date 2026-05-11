#!/usr/bin/env python3
"""Executable specs for workspace leakage self-checks."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import check_workspace_leakage as leakage
from _common import ToolError


class CheckWorkspaceLeakageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def build_workspace(self) -> Path:
        workspace = self.root / "workspace"
        workspace.mkdir()
        leakage.run_git(["init"], cwd=workspace)
        leakage.run_git(["config", "user.name", "Core Narrative Test"], cwd=workspace)
        leakage.run_git(["config", "user.email", "core-narrative-test@example.invalid"], cwd=workspace)
        leakage.write_text(workspace / "story.txt", "base-visible content\n")
        leakage.run_git(["add", "story.txt"], cwd=workspace)
        leakage.run_git(["commit", "--no-gpg-sign", "-m", "base commit"], cwd=workspace)
        return workspace

    def test_assert_target_absent_rejects_target_commit_in_statement_payload(self) -> None:
        """Regression: a hidden commit URL in statement.md still reaches the ACUT."""
        workspace = self.build_workspace()
        target_commit = "1c20dc6e724cd5625faaa17b715ba928d44c08bf"
        package_dir = workspace / ".core_narrative"
        package_dir.mkdir()
        leakage.write_text(
            package_dir / "task.json",
            json.dumps(
                {
                    "schema_version": "core-narrative.task-package.v2",
                    "task_id": "click__rwork__003",
                    "repo_slug": "click",
                    "split": "rwork",
                    "task_family": "metadata leakage regression",
                    "task_statement_path": ".core_narrative/statement.md",
                    "workspace_history": {
                        "mode": "base_tree_only_synthetic_git",
                        "future_history_available": False,
                        "source_anchor_metadata_visible": False,
                    },
                }
            ),
        )
        leakage.write_text(
            package_dir / "statement.md",
            f"Public source: https://github.com/pallets/click/commit/{target_commit}\n",
        )

        with self.assertRaises(ToolError) as raised:
            leakage.assert_target_absent(workspace, target_commit)

        self.assertEqual(str(raised.exception), "target commit leaked into ACUT-visible statement payload")
        self.assertEqual(
            raised.exception.details["statement_payloads"],
            [str((package_dir / "statement.md").resolve())],
        )


if __name__ == "__main__":
    unittest.main()
