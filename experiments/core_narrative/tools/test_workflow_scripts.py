#!/usr/bin/env python3
"""Executable specs for committed workflow launcher scripts."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT_008_WORKER = (
    REPO_ROOT
    / ".codex-workflows"
    / "core-narrative-experiment"
    / "workers"
    / "pilot-008-execution"
    / "run_worker.sh"
)


class WorkflowScriptTests(unittest.TestCase):
    def test_pilot_008_worker_launcher_uses_portable_repo_paths(self) -> None:
        """Regression: recorded launchers must not depend on one user's checkout path."""
        script = PILOT_008_WORKER.read_text(encoding="utf-8")

        self.assertNotIn("/Users/chenmohan/gits/barcarolle-wt-pilot-008-execution", script)
        self.assertIn('script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"', script)
        self.assertIn('repo_root="${BARCAROLLE_REPO_ROOT:-$(cd -- "${script_dir}/../../../.." && pwd)}"', script)
        self.assertIn('-C "${repo_root}"', script)
        self.assertIn('< "${script_dir}/prompt.md"', script)
        self.assertIn('> "${script_dir}/cli.log"', script)

        subprocess.run(["bash", "-n", str(PILOT_008_WORKER)], check=True)


if __name__ == "__main__":
    unittest.main()
