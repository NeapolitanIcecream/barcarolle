#!/usr/bin/env python3
"""Executable specs for ACUT task execution artifacts."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import run_task


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


class RunTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def init_repo(self, path: Path) -> None:
        path.mkdir()
        self.assertEqual(git(path, "init", "-q").returncode, 0)
        self.assertEqual(git(path, "config", "user.email", "codex@example.com").returncode, 0)
        self.assertEqual(git(path, "config", "user.name", "Codex").returncode, 0)
        (path / "base.txt").write_text("base\n", encoding="utf-8")
        self.assertEqual(git(path, "add", "base.txt").returncode, 0)
        self.assertEqual(git(path, "commit", "-q", "-m", "base").returncode, 0)

    def test_collect_patch_includes_untracked_new_files(self) -> None:
        """Regression: fixes that create new files must be present in submission.patch."""
        workspace = self.root / "workspace"
        clean_workspace = self.root / "clean-workspace"
        self.init_repo(workspace)
        self.init_repo(clean_workspace)

        new_file = workspace / "pkg" / "generated.txt"
        new_file.parent.mkdir()
        new_file.write_text("created by acut\n", encoding="utf-8")

        patch_text = run_task.collect_patch(workspace, {})

        self.assertIn("new file mode", patch_text)
        self.assertIn("+++ b/pkg/generated.txt", patch_text)
        self.assertIn("+created by acut", patch_text)
        check = subprocess.run(
            ["git", "apply", "--check", "-"],
            cwd=clean_workspace,
            input=patch_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
