#!/usr/bin/env python3
"""Executable specs for safe workspace preparation."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import unittest
import json
from pathlib import Path

import prepare_workspace as prepare_module
from _common import ToolError


class PrepareWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.destination = self.root / "workspace"
        self.destination.mkdir()

    def test_archive_symlink_target_outside_destination_is_rejected(self) -> None:
        """Regression: git archive extraction must reject escaping symlinks."""
        archive_path = self.root / "unsafe-symlink.tar"
        with tarfile.open(archive_path, "w") as archive:
            info = tarfile.TarInfo("pkg/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../outside.txt"
            archive.addfile(info)

        with self.assertRaises(ToolError) as raised:
            prepare_module.extract_archive_safely(archive_path, self.destination)

        self.assertEqual(str(raised.exception), "git archive contains an unsafe symlink")
        self.assertFalse((self.destination / "pkg" / "link").exists())

    def test_acut_visible_task_package_hides_source_anchor_and_preparation_metadata(self) -> None:
        """Regression: commit URLs can contain the hidden target commit hash."""
        task_dir = self.root / "task"
        task_dir.mkdir()
        (task_dir / "statement.md").write_text("Fix the behavior.\n", encoding="utf-8")
        target_commit = "1c20dc6e724cd5625faaa17b715ba928d44c08bf"
        task = {
            "task_id": "click__rwork__003",
            "repo_slug": "click",
            "split": "rwork",
            "task_family": "metadata leakage regression",
            "task_statement_path": "statement.md",
            "source": {
                "kind": "commit",
                "public_url": f"https://github.com/pallets/click/commit/{target_commit}",
                "base_commit": "6a1c0d077311f180b356965914e2de5b9e0fdb44",
                "target_commit": target_commit,
            },
            "allowed_context": {
                "include_git_history_before_base": True,
                "include_reference_patch": False,
            },
        }

        metadata_path, statement_path, warnings = prepare_module.write_task_package(task, task_dir / "task.yaml", self.destination)

        package = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(warnings, [])
        self.assertEqual(statement_path, self.destination / ".core_narrative" / "statement.md")
        self.assertEqual(package["schema_version"], "core-narrative.task-package.v2")
        self.assertNotIn("prepared_at", package)
        self.assertNotIn("source", package)
        self.assertNotIn(target_commit, metadata_path.read_text(encoding="utf-8"))
        self.assertFalse(package["workspace_history"]["source_anchor_metadata_visible"])


if __name__ == "__main__":
    unittest.main()
