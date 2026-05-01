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
        command: list[str] | None = None,
        run_id: str,
        inner_summary: dict[str, object] | None = None,
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
        if inner_summary is not None:
            inner_summary_path = artifact_dir / "codex_cli_patch_command.json"
            writer_path = root / "write_inner_summary.py"
            writer_path.write_text(
                (
                    "import json\n"
                    "import sys\n"
                    "from pathlib import Path\n"
                    f"PAYLOAD = {inner_summary!r}\n"
                    "summary_path = Path(sys.argv[sys.argv.index('--summary-output') + 1])\n"
                    "summary_path.parent.mkdir(parents=True, exist_ok=True)\n"
                    "summary_path.write_text(json.dumps(PAYLOAD), encoding='utf-8')\n"
                    "print('inner failed before patch')\n"
                    "sys.exit(7)\n"
                ),
                encoding="utf-8",
            )
            command = [sys.executable, str(writer_path), "--summary-output", str(inner_summary_path)]
        self.assertIsNotNone(command)

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

    def test_nonzero_exit_with_empty_git_diff_writes_infra_failed_normalized_result(self) -> None:
        """Regression: reviewed codex_exec_failed/no-patch runs need a normalized result."""
        completed, adapter_result, ledger_records, normalized_path = self.run_adapter_case(
            command=[
                sys.executable,
                "-c",
                "import sys; print('inner failed before patch'); sys.exit(7)",
            ],
            run_id="unit_nonzero_no_patch_attempt1",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        normalized = json.loads(normalized_path.read_text(encoding="utf-8"))

        self.assertEqual(adapter_result["status"], "command_failed")
        self.assertEqual(adapter_result["command_exit_code"], 7)
        self.assertIs(adapter_result["command_timed_out"], False)
        self.assertEqual(adapter_result["patch_artifact"]["size_bytes"], 0)
        self.assertIs(adapter_result["no_patch_generated"], False)
        self.assertIs(adapter_result["nonzero_exit_without_verifier_patch"], True)
        self.assertIs(adapter_result["verifier_ready_patch_available"], False)
        self.assertEqual(adapter_result["cost_ledger_append"]["event"], "command_failed")

        self.assertEqual(normalized["status"], "infra_failed")
        self.assertEqual(normalized["metadata"]["adapter_status"], "command_failed")
        self.assertEqual(normalized["metadata"]["failure_class"], "nonzero_exit")
        self.assertIs(normalized["metadata"]["no_patch_generated"], False)
        self.assertIs(normalized["metadata"]["verifier_ready_patch_available"], False)
        self.assertNotEqual(normalized.get("error"), "patch-generation command completed without producing a patch")

        self.assertEqual(len(ledger_records), 1)
        self.assertEqual(ledger_records[0]["event"], "command_failed")
        self.assertIs(ledger_records[0]["metadata"]["no_patch_generated"], False)

    def test_nonzero_exit_normalized_result_preserves_inner_transport_failure_class(self) -> None:
        """Regression: known Codex transport failures should remain distinguishable from generic exits."""
        inner_summary = {
            "tool": "codex_cli_patch_command",
            "status": "codex_exec_failed",
            "failure_capture": {
                "present": True,
                "failure_class": "responses_streaming_disconnect",
                "cli_log_inspected": False,
            },
            "transport_failure": {
                "present": True,
                "failure_class": "responses_streaming_disconnect",
                "wire_api": "responses",
                "endpoint_path": "/responses",
                "after_reconnects": 5,
                "reconnect_limit": 5,
                "retry_exhausted": True,
                "messages_recorded": False,
                "content_recorded": False,
            },
        }
        completed, adapter_result, ledger_records, normalized_path = self.run_adapter_case(
            inner_summary=inner_summary,
            run_id="unit_transport_disconnect_attempt1",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        normalized = json.loads(normalized_path.read_text(encoding="utf-8"))

        self.assertEqual(adapter_result["status"], "command_failed")
        self.assertEqual(adapter_result["inner_patch_command"]["failure_class"], "responses_streaming_disconnect")
        self.assertEqual(
            adapter_result["inner_patch_command"]["transport_failure"]["failure_class"],
            "responses_streaming_disconnect",
        )
        self.assertEqual(normalized["status"], "infra_failed")
        self.assertEqual(normalized["metadata"]["failure_class"], "responses_streaming_disconnect")
        self.assertEqual(
            normalized["metadata"]["inner_patch_command"]["transport_failure"]["after_reconnects"],
            5,
        )
        self.assertEqual(ledger_records[0]["event"], "command_failed")
        self.assertEqual(ledger_records[0]["metadata"]["failure_class"], "responses_streaming_disconnect")
        self.assertEqual(
            ledger_records[0]["metadata"]["transport_failure_class"],
            "responses_streaming_disconnect",
        )

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

        self.assertFalse(normalized_path.exists())


if __name__ == "__main__":
    unittest.main()
