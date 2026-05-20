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

    def test_collect_patch_excludes_runner_owned_untracked_dirs(self) -> None:
        """Regression: harness metadata and venv files must not contaminate model patches."""
        workspace = self.root / "workspace"
        self.init_repo(workspace)
        (workspace / "base.txt").write_text("changed\n", encoding="utf-8")
        (workspace / ".core_narrative").mkdir()
        (workspace / ".core_narrative" / "task.json").write_text('{"task_id":"unit"}\n', encoding="utf-8")
        (workspace / ".venv" / "bin").mkdir(parents=True)
        (workspace / ".venv" / "bin" / "activate").write_text("https://example.invalid\n", encoding="utf-8")
        (workspace / ".pytest_cache").mkdir()
        (workspace / ".pytest_cache" / "README.md").write_text("cache\n", encoding="utf-8")
        (workspace / "pkg.egg-info").mkdir()
        (workspace / "pkg.egg-info" / "PKG-INFO").write_text("install metadata\n", encoding="utf-8")

        patch_text = run_task.collect_patch(workspace, {})

        self.assertIn("diff --git a/base.txt b/base.txt", patch_text)
        self.assertNotIn(".core_narrative", patch_text)
        self.assertNotIn(".venv", patch_text)
        self.assertNotIn(".pytest_cache", patch_text)
        self.assertNotIn(".egg-info", patch_text)
        self.assertNotIn("https://example.invalid", patch_text)


if __name__ == "__main__":
    unittest.main()
