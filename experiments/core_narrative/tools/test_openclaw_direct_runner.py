#!/usr/bin/env python3
"""Executable specs for the OpenClaw-native direct runner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from openclaw_direct_runner import append_failure_record_if_model_responded, provider_text_and_usage


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "openclaw_direct_runner.py"


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


class OpenClawDirectRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        run(["git", "init"], cwd=self.workspace)
        run(["git", "config", "user.email", "test" + "@example.invalid"], cwd=self.workspace)
        run(["git", "config", "user.name", "Test User"], cwd=self.workspace)
        (self.workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
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
        (self.root / "statement.md").write_text("Change module.py so VALUE becomes 2.\n", encoding="utf-8")
        self.acut_path = self.root / "acut.json"
        self.acut_path.write_text(
            json.dumps(
                {
                    "acut_id": "cheap-generic-swe",
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
        env["BARCAROLLE_LLM_API_KEY"] = "unit" + "-secret" + "-value"
        env["BARCAROLLE_LLM_BASE_URL"] = "http" + "s://" + "llm-gateway.example.invalid/v1"
        return env

    def test_provider_text_extracts_chat_content_parts_and_usage(self) -> None:
        """Provider compatibility: chat content arrays should not hide valid JSON edits."""
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": '{"edits": []}'},
                            ]
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
            }
        ).encode("utf-8")

        text, usage = provider_text_and_usage(body)

        self.assertEqual(text, '{"edits": []}')
        self.assertEqual(usage, {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15})

    def test_mock_search_replace_generates_patch_and_zero_cost_unknown_actual(self) -> None:
        """The OpenClaw runner can produce a verifier-ready patch without old Codex plumbing."""
        artifact_dir = self.root / "artifacts"
        output_path = self.root / "runner.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
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
                "unit_openclaw_direct_mock_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "module.py",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        ledger_records = [json.loads(line) for line in self.ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(summary["status"], "patch_generated")
        self.assertEqual(summary["runner_id"], "openclaw-direct-search-replace-v1")
        self.assertIs(summary["model_call_made"], False)
        self.assertEqual(summary["patch"]["kind"], "search_replace_edits")
        self.assertGreater(summary["patch_artifact"]["size_bytes"], 0)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")
        self.assertEqual(ledger_records[0]["estimated_cost_usd"], 0)
        self.assertIsNone(ledger_records[0]["actual_cost_usd"])
        self.assertEqual(ledger_records[0]["metadata"]["actual_cost_status"], "unknown_not_provider_reported")
        self.assertEqual(ledger_records[0]["metadata"]["cost_basis"], "no_model")
        self.assertNotIn(self.env()["BARCAROLLE_LLM_API_KEY"], json.dumps(summary))
        self.assertNotIn("http" + "s://", json.dumps(summary))

    def test_mock_search_replace_rejects_edits_outside_context_paths(self) -> None:
        """Regression: generated edits must stay within the files shown to the model."""
        (self.workspace / "hidden.py").write_text("SECRET_VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "hidden.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "add hidden"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "outside-context-artifacts"
        output_path = self.root / "outside-context.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "hidden.py",
                        "old": "SECRET_VALUE = 1\n",
                        "new": "SECRET_VALUE = 2\n",
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
                "unit_openclaw_outside_context_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "module.py",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertNotEqual(completed.returncode, 0)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "generated_path_outside_context")
        self.assertEqual((self.workspace / "hidden.py").read_text(encoding="utf-8"), "SECRET_VALUE = 1\n")

    def test_live_failure_after_response_is_ledgered_with_provider_usage(self) -> None:
        """Regression: validation failures after a model response still consume provider usage."""
        artifact_dir = self.root / "failed-live-artifacts"
        artifact_dir.mkdir()
        body = {
            "choices": [{"message": {"content": '{"edits":[]}'}}],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "total_tokens": 150,
                "cost": 0.0123,
            },
        }
        (artifact_dir / "provider_response.redacted.json").write_text(json.dumps(body), encoding="utf-8")
        args = types.SimpleNamespace(
            artifact_dir=str(artifact_dir),
            llm_ledger=str(self.ledger_path),
            run_id="unit_failed_after_response",
            task=str(self.task_path),
            acut=str(self.acut_path),
            attempt=1,
            projected_cost_usd="1",
            estimated_cost_usd="1",
            input_tokens=None,
            output_tokens=None,
        )

        append_summary = append_failure_record_if_model_responded(
            args,
            started_at="2026-05-07T00:00:00Z",
            finished_at="2026-05-07T00:00:01Z",
            exc=FileNotFoundError("bad generated path"),
        )
        ledger_records = [json.loads(line) for line in self.ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(append_summary["status"], "appended")
        self.assertEqual(ledger_records[0]["event"], "runner_error_after_model_response")
        self.assertEqual(ledger_records[0]["estimated_cost_usd"], 0.0123)
        self.assertIsNone(ledger_records[0]["actual_cost_usd"])
        self.assertEqual(ledger_records[0]["input_tokens"], 120)
        self.assertEqual(ledger_records[0]["output_tokens"], 30)
        self.assertEqual(ledger_records[0]["metadata"]["observed_provider_cost_usd"], 0.0123)
        self.assertEqual(
            ledger_records[0]["metadata"]["observed_provider_cost_status"],
            "provider_response_usage_cost_not_invoice",
        )
        self.assertEqual(
            ledger_records[0]["metadata"]["cost_basis"],
            "provider_response_usage_cost_not_invoice",
        )
        self.assertEqual(ledger_records[0]["metadata"]["fallback_estimated_cost_usd"], 1)


if __name__ == "__main__":
    unittest.main()
