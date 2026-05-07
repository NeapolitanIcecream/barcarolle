#!/usr/bin/env python3
"""Executable specs for committed workflow launcher scripts."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_WORKERS = REPO_ROOT / ".codex-workflows" / "core-narrative-experiment" / "workers"


class WorkflowScriptTests(unittest.TestCase):
    def test_core_narrative_launchers_use_portable_repo_paths(self) -> None:
        """Regression: recorded launchers must not depend on one user's checkout path."""
        launcher_paths = sorted(
            path
            for pattern in ("*/run.sh", "*/run_*.sh")
            for path in WORKFLOW_WORKERS.glob(pattern)
        )
        self.assertGreater(len(launcher_paths), 0)

        for launcher_path in launcher_paths:
            with self.subTest(path=launcher_path.relative_to(REPO_ROOT)):
                script = launcher_path.read_text(encoding="utf-8")

                self.assertNotIn("/Users/chenmohan/gits/barcarolle", script)
                self.assertIn('script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"', script)
                self.assertIn(
                    'repo_root="${BARCAROLLE_REPO_ROOT:-$(cd -- "${script_dir}/../../../.." && pwd)}"',
                    script,
                )
                self.assertIn('-C "${repo_root}"', script)
                subprocess.run(["bash", "-n", str(launcher_path)], check=True)


if __name__ == "__main__":
    unittest.main()
