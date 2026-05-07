#!/usr/bin/env python3
"""Executable specs for the Codex NFL direct-runner facility."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "codex_nfl_direct_runner.py"


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CodexNflDirectRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        run(["git", "init"], cwd=self.workspace)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.workspace)
        run(["git", "config", "user.name", "Test User"], cwd=self.workspace)
        (self.workspace / "click").mkdir()
        (self.workspace / "click" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "click/core.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "initial"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        self.task_path = self.root / "task.json"
        self.task_path.write_text(
            json.dumps(
                {
                    "task_id": "click__rbench__001",
                    "repo_slug": "click",
                    "split": "rbench",
                    "task_family": "unit search replace",
                    "task_statement_path": "statement.md",
                }
            ),
            encoding="utf-8",
        )
        (self.root / "statement.md").write_text("Change click/core.py so VALUE becomes 2.\n", encoding="utf-8")
        self.acut_path = self.root / "acut.json"
        self.acut_path.write_text(
            json.dumps(
                {
                    "acut_id": "cheap-click-specialist",
                    "provider": "openai",
                    "model": "openai/gpt-5.4-mini",
                    "model_parameters": {"reasoning_effort": "medium"},
                }
            ),
            encoding="utf-8",
        )
        self.ledger_path = self.root / "cost_ledger.jsonl"
        self.ledger_path.write_text("", encoding="utf-8")

    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["BARCAROLLE_LLM_API_KEY"] = "unit-secret-value"
        env["BARCAROLLE_LLM_BASE_URL"] = "https://llm-gateway.example.invalid/v1"
        return env

    def test_mock_patch_records_codex_runner_identity(self) -> None:
        """The Codex wrapper emits Codex-owned runner metadata and a patch artifact."""
        artifact_dir = self.root / "artifacts"
        output_path = self.root / "runner.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "click/core.py",
                        "old": "VALUE = 1\n",
                        "new": "VALUE = 2\n",
                    }
                ]
            }
        )

        completed = run(
            [
                sys.executable,
                str(RUNNER),
                "--workspace",
                str(self.workspace),
                "--task",
                str(self.task_path),
                "--acut",
                str(self.acut_path),
                "--attempt",
                "1",
                "--run-id",
                "unit_codex_nfl_direct_mock_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "click/core.py",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["tool"], "codex_nfl_direct_runner")
        self.assertEqual(summary["runner_id"], "codex-nfl-direct-search-replace-v1")
        self.assertEqual(summary["status"], "patch_generated")
        self.assertGreater(summary["patch_artifact"]["size_bytes"], 0)

    def test_generated_src_click_path_fails_with_machine_readable_class(self) -> None:
        """Regression: modern src/ paths in historical Click workspaces are classified."""
        artifact_dir = self.root / "wrong-path"
        output_path = self.root / "wrong-path.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "src/click/core.py",
                        "old": "VALUE = 1\n",
                        "new": "VALUE = 2\n",
                    }
                ]
            }
        )

        completed = run(
            [
                sys.executable,
                str(RUNNER),
                "--workspace",
                str(self.workspace),
                "--task",
                str(self.task_path),
                "--acut",
                str(self.acut_path),
                "--attempt",
                "1",
                "--run-id",
                "unit_codex_nfl_wrong_path_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "click/core.py",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertNotEqual(completed.returncode, 0)
        summary = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["runner_id"], "codex-nfl-direct-search-replace-v1")
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "generated_path_not_in_workspace")


if __name__ == "__main__":
    unittest.main()
