#!/usr/bin/env python3
"""Regression checks for ACUT adapter patch classification."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "acut_patch_adapter.py"


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


class AcutPatchAdapterTests(unittest.TestCase):
    def test_exit_zero_with_empty_git_diff_is_no_patch_generated(self) -> None:
        """Regression: progress-only inner commands must not be marked command_completed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            run(["git", "init"], cwd=workspace)
            run(["git", "config", "user.email", "test" + "@example.invalid"], cwd=workspace)
            run(["git", "config", "user.name", "Test User"], cwd=workspace)
            (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            run(["git", "add", "module.py"], cwd=workspace)
            commit = run(["git", "commit", "-m", "initial"], cwd=workspace)
            self.assertEqual(commit.returncode, 0, commit.stderr)

            task_path = root / "task.json"
            task_path.write_text(json.dumps({"task_id": "click__rbench__001", "split": "rbench"}), encoding="utf-8")
            ledger_path = root / "cost_ledger.jsonl"
            ledger_path.write_text("", encoding="utf-8")
            output_path = root / "adapter_result.json"
            normalized_path = root / "normalized.json"
            artifact_dir = root / "artifacts"

            env = os.environ.copy()
            env["BARCAROLLE_LLM_API_KEY"] = "test-api-key"
            env["BARCAROLLE_LLM_BASE_URL"] = "http" + "s://" + "redacted" + ".invalid/v1"

            completed = run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--workspace",
                    str(workspace),
                    "--task",
                    str(task_path),
                    "--acut-id",
                    "cheap-click-specialist",
                    "--attempt",
                    "1",
                    "--run-id",
                    "unit_empty_patch_attempt1",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--output",
                    str(output_path),
                    "--normalized-output",
                    str(normalized_path),
                    "--llm-ledger",
                    str(ledger_path),
                    "--projected-cost-usd",
                    "0",
                    "--input-tokens",
                    "0",
                    "--output-tokens",
                    "0",
                    "--command-no-model",
                    "--",
                    sys.executable,
                    "-c",
                    "print('progress-only final answer')",
                ],
                cwd=REPO_ROOT,
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            adapter_result = json.loads(output_path.read_text(encoding="utf-8"))
            normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
            ledger_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(adapter_result["status"], "no_patch_generated")
            self.assertEqual(adapter_result["patch_artifact"]["size_bytes"], 0)
            self.assertEqual(adapter_result["cost_ledger_append"]["event"], "no_patch_generated")
            self.assertEqual(normalized["status"], "infra_failed")
            self.assertEqual(normalized["metadata"]["adapter_status"], "no_patch_generated")
            self.assertEqual(len(ledger_records), 1)
            self.assertEqual(ledger_records[0]["event"], "no_patch_generated")


if __name__ == "__main__":
    unittest.main()
