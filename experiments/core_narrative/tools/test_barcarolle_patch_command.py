#!/usr/bin/env python3
"""Executable no-model specs for the direct Barcarolle patch command."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path

import barcarolle_patch_command as patch_command_module
from barcarolle_patch_command import (
    STRUCTURED_FILES_OUTPUT_CONTRACT,
    live_request_payload,
    resolve_live_endpoint,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PATCH_COMMAND = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "barcarolle_patch_command.py"
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


class BarcarollePatchCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        run(["git", "init"], cwd=self.workspace)
        run(["git", "config", "user.email", "test" + "@example.invalid"], cwd=self.workspace)
        run(["git", "config", "user.name", "Test User"], cwd=self.workspace)
        (self.workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.workspace / "statement.md").write_text(
            "Change module.py so VALUE becomes 2. Do not use external context.\n",
            encoding="utf-8",
        )
        run(["git", "add", "module.py", "statement.md"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "initial"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        task_dir = self.workspace / ".core_narrative"
        task_dir.mkdir()
        (task_dir / "task.json").write_text(
            json.dumps(
                {
                    "task_id": "click__rbench__001",
                    "split": "rbench",
                    "repo_slug": "click",
                    "task_statement_path": "statement.md",
                }
            ),
            encoding="utf-8",
        )
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

    def command_env(self, *, include_llm_env: bool = False) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("BARCAROLLE_LLM_API_KEY", None)
        env.pop("BARCAROLLE_LLM_BASE_URL", None)
        if include_llm_env:
            env["BARCAROLLE_LLM_API_KEY"] = "unit" + "-secret" + "-value"
            env["BARCAROLLE_LLM_BASE_URL"] = "http" + "s://" + "llm-gateway.example.invalid/v1"
        return env

    def run_patch_command(
        self,
        *extra_args: str,
        env: dict[str, str] | None = None,
        summary_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            str(PATCH_COMMAND),
            "--workspace",
            str(self.workspace),
            "--acut",
            str(self.acut_path),
            *extra_args,
        ]
        if summary_path is not None:
            args.extend(["--summary-output", str(summary_path)])
        return run(args, cwd=REPO_ROOT, env=env or self.command_env())

    def test_dry_run_prepares_prompt_without_llm_environment_or_network(self) -> None:
        """Given missing LLM env, dry-run records prompt metadata and never calls a model."""
        summary_path = self.root / "dry-run-summary.json"

        completed = self.run_patch_command("--dry-run", summary_path=summary_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "dry_run_completed")
        self.assertEqual(summary["mode"], "dry_run")
        self.assertIs(summary["model_call_made"], False)
        self.assertIs(summary["prompt"]["prepared"], True)
        self.assertIs(summary["prompt"]["content_recorded"], False)
        self.assertEqual(
            summary["llm_env_policy"]["required_present"],
            {"BARCAROLLE_LLM_API_KEY": False, "BARCAROLLE_LLM_BASE_URL": False},
        )
        self.assertNotIn("Change module.py", json.dumps(summary))
        self.assertNotIn("http" + "s://", json.dumps(summary))

    def test_live_mode_missing_env_blocks_before_network(self) -> None:
        """Given missing LLM env, live mode fails as preflight and records no network attempt."""
        summary_path = self.root / "missing-env-summary.json"

        completed = self.run_patch_command(summary_path=summary_path)

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["error"], "missing required LLM environment")
        self.assertEqual(
            sorted(summary["details"]["missing_env"]),
            ["BARCAROLLE_LLM_API_KEY", "BARCAROLLE_LLM_BASE_URL"],
        )
        self.assertIs(summary["details"]["network_attempted"], False)
        self.assertIs(summary["model_call_made"], False)

    def test_mock_response_applies_unified_diff_without_llm_environment(self) -> None:
        """Given a mock model response, the command applies a patch with no live call."""
        summary_path = self.root / "mock-summary.json"
        patch = textwrap.dedent(
            """\
            diff --git a/module.py b/module.py
            --- a/module.py
            +++ b/module.py
            @@ -1 +1 @@
            -VALUE = 1
            +VALUE = 2
            """
        )
        response = json.dumps({"unified_diff": patch})

        completed = self.run_patch_command("--mock-response-text", response, summary_path=summary_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "mock_response_applied")
        self.assertEqual(summary["mode"], "mock_response")
        self.assertIs(summary["model_call_made"], False)
        self.assertIs(summary["patch"]["received"], True)
        self.assertIs(summary["patch"]["applied"], True)
        self.assertEqual(summary["patch"]["changed_paths"], ["module.py"])
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")
        self.assertNotIn(response, json.dumps(summary))

    def test_unsafe_mock_response_argument_is_rejected_before_parsing(self) -> None:
        """Given URL-like model text as a CLI argument, the redaction policy blocks it."""
        summary_path = self.root / "unsafe-argument-summary.json"
        unsafe_text = "diff mentions " + "http" + "s://" + "gateway.example.invalid/v1"

        completed = self.run_patch_command(
            "--mock-response-text",
            unsafe_text,
            env=self.command_env(include_llm_env=True),
            summary_path=summary_path,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"].get("reason"), "full_url")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")
        self.assertNotIn("http" + "s://", json.dumps(summary))


    def test_live_response_apply_failure_records_model_call_made(self) -> None:
        """Regression: invalid live model patches must still record that a model answered."""
        summary_path = self.root / "invalid-live-patch-summary.json"
        invalid_patch = textwrap.dedent(
            """\
            diff --git a/module.py b/module.py
            --- a/module.py
            +++ b/module.py
            @@ -1 +1 @@
            -VALUE = 1
            VALUE = 2
            """
        )
        argv = [
            str(PATCH_COMMAND),
            "--workspace",
            str(self.workspace),
            "--acut",
            str(self.acut_path),
            "--summary-output",
            str(summary_path),
        ]

        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.dict(os.environ, self.command_env(include_llm_env=True), clear=True),
            mock.patch.object(patch_command_module, "call_live_model", return_value=json.dumps({"unified_diff": invalid_patch})),
        ):
            exit_code = patch_command_module.main()

        self.assertEqual(exit_code, 2)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["error"], "generated unified diff failed git apply validation")
        self.assertEqual(summary["failure_class"], "invalid_unified_diff")
        self.assertIs(summary["model_call_made"], True)
        self.assertIs(summary["details"]["model_response_received"], True)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_live_transport_timeout_records_attempted_model_call(self) -> None:
        """Regression: provider timeouts are classified distinctly and ledgerable as attempted calls."""
        summary_path = self.root / "timeout-summary.json"
        argv = [
            str(PATCH_COMMAND),
            "--workspace",
            str(self.workspace),
            "--acut",
            str(self.acut_path),
            "--output-contract",
            "structured-files-json-v1",
            "--summary-output",
            str(summary_path),
        ]

        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.dict(os.environ, self.command_env(include_llm_env=True), clear=True),
            mock.patch.object(
                patch_command_module,
                "call_live_model",
                side_effect=patch_command_module.ToolError(
                    "LLM request failed",
                    error_type="timeout",
                    network_attempted=True,
                ),
            ),
        ):
            exit_code = patch_command_module.main()

        self.assertEqual(exit_code, 2)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["failure_class"], "llm_request_timed_out")
        self.assertEqual(summary["output_contract"], "structured-files-json-v1")
        self.assertIs(summary["model_call_made"], True)
        self.assertIs(summary["details"]["network_attempted"], True)

    def test_live_transport_timeout_records_safe_request_profile_without_network(self) -> None:
        """Timeout evidence should explain the request shape without recording endpoint or secret values."""
        env = self.command_env(include_llm_env=True)

        with mock.patch.object(
            patch_command_module.urllib.request,
            "urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(patch_command_module.ToolError) as caught:
                patch_command_module.call_live_model(
                    acut={
                        "model": "openai/gpt-5.5",
                        "model_parameters": {"reasoning_effort": "medium"},
                    },
                    prompt="prepared prompt",
                    env=env,
                    timeout_seconds=7,
                    max_response_bytes=1234,
                    output_contract=STRUCTURED_FILES_OUTPUT_CONTRACT,
                )

        details = caught.exception.details
        self.assertEqual(str(caught.exception), "LLM request timed out")
        self.assertEqual(details["error_type"], "timeout")
        self.assertIs(details["network_attempted"], True)
        self.assertEqual(
            details["request_profile"],
            {
                "endpoint_kind": "chat_completions",
                "output_contract": "structured-files-json-v1",
                "response_format_requested": True,
                "timeout_seconds": 7,
                "max_response_bytes": 1234,
                "request_body_bytes": details["request_profile"]["request_body_bytes"],
                "prompt_char_count": len("prepared prompt"),
            },
        )
        self.assertGreater(details["request_profile"]["request_body_bytes"], 0)
        serialized = json.dumps(details)
        self.assertNotIn("http" + "s://", serialized)
        self.assertNotIn("llm-gateway.example.invalid", serialized)
        self.assertNotIn("unit" + "-secret" + "-value", serialized)

    def test_structured_files_contract_rejects_unified_diff_before_workspace_mutation(self) -> None:
        """Given the strict direct-output contract, unified diffs are rejected as contract drift."""
        summary_path = self.root / "structured-contract-rejects-diff-summary.json"
        patch = textwrap.dedent(
            """\
            diff --git a/module.py b/module.py
            --- a/module.py
            +++ b/module.py
            @@ -1 +1 @@
            -VALUE = 1
            +VALUE = 2
            """
        )

        completed = self.run_patch_command(
            "--mock-response-text",
            json.dumps({"unified_diff": patch}),
            "--output-contract",
            "structured-files-json-v1",
            summary_path=summary_path,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["failure_class"], "output_contract_violation")
        self.assertIs(summary["model_call_made"], False)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_structured_files_contract_applies_json_files_without_llm_environment(self) -> None:
        """Given strict JSON files output, the direct path can avoid malformed diff syntax."""
        summary_path = self.root / "structured-contract-applies-files-summary.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "module.py",
                        "action": "replace",
                        "content": "VALUE = 2\n",
                    }
                ]
            }
        )

        completed = self.run_patch_command(
            "--mock-response-text",
            response,
            "--output-contract",
            "structured-files-json-v1",
            summary_path=summary_path,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "mock_response_applied")
        self.assertEqual(summary["output_contract"], "structured-files-json-v1")
        self.assertEqual(summary["patch"]["kind"], "structured_files")
        self.assertEqual(summary["patch"]["changed_paths"], ["module.py"])
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")


    def test_structured_files_contract_rejects_url_like_generated_paths(self) -> None:
        """Regression: generated structured paths must not persist full URLs into artifacts."""
        summary_path = self.root / "structured-contract-unsafe-path-summary.json"
        response_path = self.root / "unsafe-path-response.json"
        response_path.write_text(
            json.dumps(
                {
                    "files": [
                        {
                            "path": "http" + "s://" + "gateway.example.invalid/leak.py",
                            "action": "write",
                            "content": "VALUE = 2\n",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        completed = self.run_patch_command(
            "--mock-response",
            str(response_path),
            "--output-contract",
            "structured-files-json-v1",
            summary_path=summary_path,
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["failure_class"], "unsafe_generated_content")
        self.assertEqual(summary["details"]["unsafe_content"]["reason_counts"], {"full_url": 1})
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")
        self.assertNotIn("http" + "s://", json.dumps(summary))

    def test_adapter_command_no_model_wraps_mock_response_with_zero_cost_ledger(self) -> None:
        """The outer adapter can wrap the direct command as no-model compatible evidence."""
        artifact_dir = self.root / "adapter-artifacts"
        ledger_path = self.root / "cost_ledger.jsonl"
        ledger_path.write_text("", encoding="utf-8")
        output_path = self.root / "adapter-result.json"
        normalized_path = self.root / "normalized.json"
        inner_summary_path = artifact_dir / "patch_command_summary.json"
        patch = textwrap.dedent(
            """\
            diff --git a/module.py b/module.py
            --- a/module.py
            +++ b/module.py
            @@ -1 +1 @@
            -VALUE = 1
            +VALUE = 2
            """
        )
        response = json.dumps({"unified_diff": patch})
        env = self.command_env(include_llm_env=True)

        completed = run(
            [
                sys.executable,
                str(ADAPTER),
                "--workspace",
                str(self.workspace),
                "--task",
                str(self.workspace / ".core_narrative" / "task.json"),
                "--acut-id",
                "cheap-generic-swe",
                "--attempt",
                "1",
                "--run-id",
                "unit_direct_transport_mock_attempt1",
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
                str(PATCH_COMMAND),
                "--workspace",
                str(self.workspace),
                "--acut",
                str(self.acut_path),
                "--mock-response-text",
                response,
                "--summary-output",
                str(inner_summary_path),
            ],
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        adapter_result = json.loads(output_path.read_text(encoding="utf-8"))
        inner_summary = json.loads(inner_summary_path.read_text(encoding="utf-8"))
        ledger_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(adapter_result["status"], "command_completed")
        self.assertIs(adapter_result["model_call_made"], False)
        self.assertIs(adapter_result["command_no_model"], True)
        self.assertGreater(adapter_result["patch_artifact"]["size_bytes"], 0)
        self.assertEqual(adapter_result["cost_ledger_append"]["event"], "command_completed")
        self.assertEqual(len(ledger_records), 1)
        self.assertEqual(ledger_records[0]["estimated_cost_usd"], 0)
        self.assertIs(ledger_records[0]["metadata"]["model_call_made"], False)
        self.assertEqual(inner_summary["status"], "mock_response_applied")
        self.assertIs(inner_summary["model_call_made"], False)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")
        self.assertNotIn(env["BARCAROLLE_LLM_API_KEY"], json.dumps(adapter_result))
        self.assertNotIn("http" + "s://", json.dumps(adapter_result))

    def test_adapter_command_no_model_wraps_structured_files_contract_with_patch_artifact(self) -> None:
        """The adapter can collect a verifier-ready diff after structured file application."""
        artifact_dir = self.root / "adapter-structured-artifacts"
        ledger_path = self.root / "structured_cost_ledger.jsonl"
        ledger_path.write_text("", encoding="utf-8")
        output_path = self.root / "adapter-structured-result.json"
        normalized_path = self.root / "structured-normalized.json"
        inner_summary_path = artifact_dir / "patch_command_summary.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "module.py",
                        "action": "replace",
                        "content": "VALUE = 2\n",
                    }
                ]
            }
        )
        env = self.command_env(include_llm_env=True)

        completed = run(
            [
                sys.executable,
                str(ADAPTER),
                "--workspace",
                str(self.workspace),
                "--task",
                str(self.workspace / ".core_narrative" / "task.json"),
                "--acut-id",
                "cheap-generic-swe",
                "--attempt",
                "1",
                "--run-id",
                "unit_direct_structured_transport_mock_attempt1",
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
                str(PATCH_COMMAND),
                "--workspace",
                str(self.workspace),
                "--acut",
                str(self.acut_path),
                "--mock-response-text",
                response,
                "--output-contract",
                "structured-files-json-v1",
                "--summary-output",
                str(inner_summary_path),
            ],
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        adapter_result = json.loads(output_path.read_text(encoding="utf-8"))
        inner_summary = json.loads(inner_summary_path.read_text(encoding="utf-8"))
        ledger_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(adapter_result["status"], "command_completed")
        self.assertIs(adapter_result["model_call_made"], False)
        self.assertGreater(adapter_result["patch_artifact"]["size_bytes"], 0)
        self.assertEqual(adapter_result["cost_ledger_append"]["event"], "command_completed")
        self.assertEqual(len(ledger_records), 1)
        self.assertIs(ledger_records[0]["metadata"]["model_call_made"], False)
        self.assertEqual(inner_summary["output_contract"], "structured-files-json-v1")
        self.assertEqual(inner_summary["patch"]["kind"], "structured_files")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")

    def test_direct_transport_shapes_chat_completions_payload_without_network(self) -> None:
        """The default direct HTTP transport is non-streaming and chat-completions shaped."""
        endpoint, endpoint_kind = resolve_live_endpoint("http" + "s://" + "llm-gateway.example.invalid/v1")
        payload = live_request_payload(
            {"model": "openai/gpt-5.4-mini", "model_parameters": {"reasoning_effort": "medium"}},
            "prepared prompt",
            endpoint_kind,
        )

        self.assertEqual(endpoint_kind, "chat_completions")
        self.assertTrue(endpoint.endswith("/chat/completions"))
        self.assertEqual(payload["model"], "openai/gpt-5.4-mini")
        self.assertIn("messages", payload)
        self.assertNotIn("input", payload)
        self.assertNotIn("stream", payload)
        self.assertNotIn("http" + "s://", json.dumps(payload))
        self.assertNotIn("Bearer", json.dumps(payload))

    def test_structured_files_contract_requests_json_object_without_network(self) -> None:
        """The strict direct-output contract asks chat-completions routes for JSON object output."""
        endpoint, endpoint_kind = resolve_live_endpoint("http" + "s://" + "llm-gateway.example.invalid/v1")
        payload = live_request_payload(
            {"model": "openai/gpt-5.5", "model_parameters": {"reasoning_effort": "medium"}},
            "prepared prompt",
            endpoint_kind,
            STRUCTURED_FILES_OUTPUT_CONTRACT,
        )

        self.assertTrue(endpoint.endswith("/chat/completions"))
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertNotIn("stream", payload)
        self.assertNotIn("http" + "s://", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
