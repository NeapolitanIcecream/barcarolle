#!/usr/bin/env python3
"""Executable specs for safe workspace preparation."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
