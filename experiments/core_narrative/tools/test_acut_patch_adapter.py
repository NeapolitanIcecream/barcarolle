#!/usr/bin/env python3
"""Regression checks for ACUT adapter patch classification."""

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
    def run_adapter_case(
        self,
        *,
        command: list[str],
        run_id: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]], Path]:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
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
                run_id,
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
                *command,
            ],
            cwd=REPO_ROOT,
            env=env,
        )
        adapter_result = json.loads(output_path.read_text(encoding="utf-8"))
        ledger_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
        return completed, adapter_result, ledger_records, normalized_path

    def test_exit_zero_with_empty_git_diff_is_no_patch_generated(self) -> None:
        """Regression: progress-only inner commands must not be marked command_completed."""
        completed, adapter_result, ledger_records, normalized_path = self.run_adapter_case(
            command=[sys.executable, "-c", "print('progress-only final answer')"],
            run_id="unit_empty_patch_attempt1",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        normalized = json.loads(normalized_path.read_text(encoding="utf-8"))

        self.assertEqual(adapter_result["status"], "no_patch_generated")
        self.assertEqual(adapter_result["patch_artifact"]["size_bytes"], 0)
        self.assertEqual(adapter_result["cost_ledger_append"]["event"], "no_patch_generated")
        self.assertEqual(normalized["status"], "infra_failed")
        self.assertEqual(normalized["metadata"]["adapter_status"], "no_patch_generated")
        self.assertEqual(len(ledger_records), 1)
        self.assertEqual(ledger_records[0]["event"], "no_patch_generated")

    def test_unsafe_patch_rejection_is_not_marked_no_patch_generated(self) -> None:
        """Regression: unsafe sanitized artifacts are not true empty-patch runs."""
        completed, adapter_result, ledger_records, normalized_path = self.run_adapter_case(
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import os; "
                    "Path('module.py').write_text("
                    "'VALUE = ' + repr(os.environ['BARCAROLLE_LLM_API_KEY']) + '\\n', "
                    "encoding='utf-8')"
                ),
            ],
            run_id="unit_unsafe_patch_attempt1",
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(adapter_result["status"], "unsafe_patch_rejected")
        self.assertEqual(adapter_result["cost_ledger_append"]["event"], "command_completed_unsafe_patch_rejected")
        self.assertTrue(adapter_result["patch_artifact"]["unsafe_content_detected"])
        self.assertEqual(adapter_result["patch_artifact"]["size_bytes"], 0)
        self.assertIs(adapter_result["no_patch_generated"], False)
        self.assertEqual(len(ledger_records), 1)
        self.assertEqual(ledger_records[0]["event"], "command_completed_unsafe_patch_rejected")
        self.assertIs(ledger_records[0]["metadata"]["no_patch_generated"], False)

        if normalized_path.exists():
            normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
            self.assertNotEqual(normalized["metadata"].get("adapter_status"), "no_patch_generated")
            self.assertNotEqual(normalized.get("error"), "patch-generation command completed without producing a patch")


if __name__ == "__main__":
    unittest.main()
