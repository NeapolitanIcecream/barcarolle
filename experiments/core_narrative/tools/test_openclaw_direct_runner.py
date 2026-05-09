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
from unittest import mock
from pathlib import Path

import openclaw_direct_runner as runner_module
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

    def test_live_model_returns_raw_text_while_persisting_redacted_response(self) -> None:
        """Regression: live response parsing must not consume redacted model text."""
        raw_url = "http" + "s://" + "gateway.example.invalid/v1"
        response_text = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
                        "old": f'ENDPOINT = "{raw_url}"\n',
                        "new": 'ENDPOINT = "safe"\n',
                    }
                ]
            }
        )
        body = json.dumps(
            {
                "choices": [{"message": {"content": response_text}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 4},
            }
        ).encode("utf-8")
        raw_response_path = self.root / "provider_response.redacted.json"

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self, size):
                return body

        def fake_urlopen(request, timeout):
            return FakeResponse()

        env = {
            "BARCAROLLE_LLM_API_KEY": "unit-secret-value",
            "BARCAROLLE_LLM_BASE_URL": "http" + "s://" + "llm-gateway.example.invalid/v1",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            runner_module.urllib.request,
            "urlopen",
            fake_urlopen,
        ):
            text, usage, _profile = runner_module.call_live_model(
                acut={"model": "openai/gpt-5.4-mini", "model_parameters": {}},
                prompt="Return JSON edits.",
                timeout_seconds=1,
                max_response_bytes=10_000,
                raw_response_path=raw_response_path,
            )

        self.assertIn(raw_url, text)
        self.assertEqual(usage, {"prompt_tokens": 12, "completion_tokens": 4})
        persisted = raw_response_path.read_text(encoding="utf-8")
        self.assertNotIn(raw_url, persisted)
        self.assertIn("<redacted:url>", persisted)

    def test_live_model_uses_responses_payload_for_responses_endpoint(self) -> None:
        """Regression: /responses endpoints require the Responses API request shape."""
        captured_payloads: list[dict[str, object]] = []
        body = json.dumps(
            {
                "output_text": '{"edits": []}',
                "usage": {"input_tokens": 12, "output_tokens": 4},
            }
        ).encode("utf-8")
        raw_response_path = self.root / "responses_provider_response.redacted.json"

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self, size):
                return body

        def fake_urlopen(request, timeout):
            captured_payloads.append(json.loads(request.data.decode("utf-8")))
            return FakeResponse()

        env = {
            "BARCAROLLE_LLM_API_KEY": "unit-secret-value",
            "BARCAROLLE_LLM_BASE_URL": "http" + "s://" + "llm-gateway.example.invalid/v1/responses",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            runner_module.urllib.request,
            "urlopen",
            fake_urlopen,
        ):
            _text, _usage, profile = runner_module.call_live_model(
                acut={"model": "openai/gpt-5.4-mini", "model_parameters": {}},
                prompt="Return JSON edits.",
                timeout_seconds=1,
                max_response_bytes=10_000,
                raw_response_path=raw_response_path,
            )

        self.assertEqual(profile["endpoint_kind"], "responses")
        self.assertIs(profile["response_format_requested"], False)
        self.assertEqual(len(captured_payloads), 1)
        payload = captured_payloads[0]
        self.assertIn("input", payload)
        self.assertNotIn("messages", payload)
        self.assertNotIn("response_format", payload)
        system_message = payload["input"][0]["content"]
        self.assertIn("anchored search/replace", system_message)
        self.assertNotIn("unified-diff", system_message)

    def test_prompt_contract_requests_only_anchored_edit_json(self) -> None:
        """The live prompt contract should steer models away from hand-written diffs."""
        prompt = runner_module.build_prompt(
            task={
                "task_id": "click__rbench__003",
                "repo_slug": "click",
                "split": "rbench",
                "task_family": "prompt choice rendering",
                "allowed_context": {},
                "disallowed_context": [],
                "metadata": {
                    "expected_touched_area": [
                        "prompt text construction for Choice parameters",
                        "termui prompt regression tests",
                    ]
                },
            },
            task_statement="When prompting for a click.Choice value, display the available choices.",
            acut={
                "acut_id": "frontier-click-specialist",
                "model": "openai/gpt-5.5",
                "retrieval_context_strategy": {"strategy_id": "click-specialist-task-agnostic-v2"},
                "runtime_budget": {},
            },
            context_files=[
                {
                    "path": "click/termui.py",
                    "sha256": "termui-sha",
                    "char_count": 120,
                    "truncated": False,
                    "content": "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n",
                }
            ],
            specialist_context=None,
            max_context_chars=10_000,
        )

        self.assertIn("Return only one JSON object with this exact contract:", prompt)
        self.assertIn('"edits":[{"path":"relative/file.py"', prompt)
        self.assertIn("Do not return unified_diff", prompt)
        self.assertIn("Pre-submit validation checklist:", prompt)
        self.assertIn("Apply edits in order mentally", prompt)
        self.assertIn("If old occurs exactly once, omit before and after anchors.", prompt)
        self.assertIn("Non-matching anchors are invalid even when old occurs once.", prompt)
        self.assertNotIn('{"unified_diff":"diff --git ..."}', prompt)

    def test_structured_files_prompt_contract_requests_full_file_json(self) -> None:
        """The alternate contract asks for file-level JSON, not search/replace anchors."""
        prompt = runner_module.build_prompt(
            task={
                "task_id": "click__rwork__003",
                "repo_slug": "click",
                "split": "rwork",
                "task_family": "default handling",
                "allowed_context": {},
                "disallowed_context": [],
            },
            task_statement="Preserve the first real default for shared options.",
            acut={
                "acut_id": "cheap-generic-swe",
                "model": "openai/gpt-5.4-mini",
                "retrieval_context_strategy": {},
                "runtime_budget": {},
            },
            context_files=[
                {
                    "path": "src/click/core.py",
                    "sha256": "core-sha",
                    "char_count": 20,
                    "truncated": False,
                    "content": "VALUE = 1\n",
                }
            ],
            specialist_context=None,
            max_context_chars=10_000,
            output_contract="structured-files-json-v1",
        )

        self.assertIn('"files":[{"path":"relative/file.py"', prompt)
        self.assertIn("full file content", prompt)
        self.assertIn("The first non-whitespace character must be {", prompt)
        self.assertIn("Any JSON object with edits, unified_diff, patch, diff, or extra top-level keys is invalid.", prompt)
        self.assertIn("Do not include http:// or https://", prompt)
        self.assertIn("Do not use placeholders like <unchanged>, [truncated], or comments saying the rest is unchanged.", prompt)
        self.assertIn("Do not return edits", prompt)
        self.assertNotIn('"edits":[{"path":"relative/file.py"', prompt)

    def test_prompt_required_context_packaging_includes_option_focus_excerpt(self) -> None:
        """Regression: Click 008-style context must show Option internals past a large prefix."""
        core_path = self.workspace / "src" / "click" / "core.py"
        core_path.parent.mkdir(parents=True)
        core_path.write_text(
            (
                "# large prefix\n"
                + "IGNORED = 1\n" * 20
                + "class Option(Parameter):\n"
                + "    def __init__(\n"
                + "        self,\n"
                + "        prompt=False,\n"
                + "        **attrs,\n"
                + "    ):\n"
                + "        self.prompt = prompt\n"
                + "\n"
                + "    def consume_value(self, ctx, opts):\n"
                + "        return super().consume_value(ctx, opts)\n"
            ),
            encoding="utf-8",
        )

        task = {
            "task_id": "click__rbench__008",
            "task_family": "optional value prompts",
            "metadata": {
                "expected_touched_area": ["prompt_required behavior in option and termui tests"],
                "visible_context_guidance": "Provide the behavior matrix for prompt_required/required.",
            },
        }
        focus_terms = runner_module.context_focus_terms(
            task,
            "Allow an option used without an explicit value to prompt according to prompt_required.",
            "src/click/core.py",
        )
        payload = runner_module.context_file_payload(
            self.workspace,
            "src/click/core.py",
            80,
            focus_terms=focus_terms,
        )
        prompt = runner_module.build_prompt(
            task=task,
            task_statement="Allow prompt_required to control whether optional values prompt.",
            acut={"acut_id": "cheap-generic-swe", "model": "openai/gpt-5.4-mini"},
            context_files=[payload],
            specialist_context=None,
            max_context_chars=10_000,
        )

        self.assertTrue(payload["truncated"])
        self.assertIn("class Option(Parameter):", focus_terms)
        self.assertGreaterEqual(len(payload["focused_excerpts"]), 1)
        self.assertIn("prompt=False", payload["focused_excerpts"][0]["content"])
        self.assertIn("Focused exact source excerpts for src/click/core.py", prompt)
        self.assertIn("prompt=False", prompt)

    def test_prompt_required_context_uses_compact_per_file_budget_for_four_files(self) -> None:
        """Regression: Click 008 packaging should leave room for every declared context file."""
        budget = runner_module.effective_max_file_chars(
            requested_max_file_chars=80_000,
            max_context_chars=120_000,
            context_path_count=4,
            task={"metadata": {"expected_touched_area": ["prompt_required behavior"]}},
            task_statement="Allow prompt_required behavior.",
        )

        self.assertEqual(budget, 25_000)

    def test_anchor_mismatch_diagnostics_explain_unique_old_anchor_policy(self) -> None:
        """Regression: bad anchors on a unique old string should produce actionable diagnostics."""
        with self.assertRaises(runner_module.ToolError) as raised:
            runner_module.resolve_edit_offset(
                "prefix\nVALUE = 1\n",
                {
                    "path": "module.py",
                    "old": "VALUE = 1\n",
                    "new": "VALUE = 2\n",
                    "before": "not adjacent\n",
                },
                edit_index=0,
            )

        details = raised.exception.details
        self.assertEqual(details["failure_class"], "search_replace_anchor_mismatch")
        self.assertEqual(details["occurrences"], 1)
        self.assertEqual(details["anchor_matches"], 0)
        self.assertEqual(details["diagnostic"]["code"], "unique_old_anchor_mismatch")
        self.assertIn("omit before/after anchors", details["diagnostic"]["recommendation"])
        self.assertEqual(details["old_text_char_count"], len("VALUE = 1\n"))

    def test_old_occurrence_mismatch_diagnostics_explain_missing_old_text(self) -> None:
        """Regression: zero-occurrence old strings should tell the model to copy shown source."""
        with self.assertRaises(runner_module.ToolError) as raised:
            runner_module.resolve_edit_offset(
                "VALUE = 1\n",
                {"path": "module.py", "old": "VALUE = 2\n", "new": "VALUE = 3\n"},
                edit_index=0,
            )

        details = raised.exception.details
        self.assertEqual(details["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(details["occurrences"], 0)
        self.assertEqual(details["diagnostic"]["code"], "old_text_not_found")
        self.assertIn("copy old exactly", details["diagnostic"]["recommendation"])

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

    def test_live_run_rejects_empty_context_before_model_call(self) -> None:
        """Regression: empty context must fail before spending live model tokens."""
        artifact_dir = self.root / "empty-context-artifacts"
        output_path = self.root / "empty-context.json"
        argv = [
            "--workspace",
            str(self.workspace),
            "--task",
            str(self.task_path),
            "--acut",
            str(self.acut_path),
            "--attempt",
            "1",
            "--run-id",
            "unit_openclaw_empty_context_attempt1",
            "--artifact-dir",
            str(artifact_dir),
            "--output",
            str(output_path),
            "--llm-ledger",
            str(self.ledger_path),
            "--projected-cost-usd",
            "1",
        ]
        model_calls: list[dict[str, object]] = []

        def fake_call_live_model(**kwargs):
            model_calls.append(dict(kwargs))
            return '{"edits":[]}', {"prompt_tokens": 10, "completion_tokens": 2}, {}

        with mock.patch.dict(os.environ, self.env(), clear=False), mock.patch.object(
            runner_module,
            "call_live_model",
            fake_call_live_model,
        ), mock.patch.object(runner_module.sys, "argv", [str(RUNNER), *argv]):
            code = runner_module.main(argv)

        self.assertEqual(code, 2)
        self.assertEqual(model_calls, [])
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "empty_context_paths")
        self.assertIs(summary["details"]["network_attempted"], False)
        self.assertFalse((artifact_dir / "provider_response.redacted.json").exists())

    def test_live_attempt_two_uses_coordinator_decision_ref_for_budget_gate(self) -> None:
        """Regression: approved repeat attempts must reach the model instead of stopping at the gate."""
        artifact_dir = self.root / "attempt-two-artifacts"
        output_path = self.root / "attempt-two.json"
        argv = [
            "--workspace",
            str(self.workspace),
            "--task",
            str(self.task_path),
            "--acut",
            str(self.acut_path),
            "--attempt",
            "2",
            "--run-id",
            "unit_openclaw_attempt2",
            "--artifact-dir",
            str(artifact_dir),
            "--output",
            str(output_path),
            "--llm-ledger",
            str(self.ledger_path),
            "--projected-cost-usd",
            "1",
            "--coordinator-decision-ref",
            "unit_attempt2_approval",
            "--context-path",
            "module.py",
        ]
        model_calls: list[dict[str, object]] = []

        def fake_call_live_model(**kwargs):
            model_calls.append(dict(kwargs))
            return (
                json.dumps({"edits": [{"path": "module.py", "old": "VALUE = 1\n", "new": "VALUE = 2\n"}]}),
                {"prompt_tokens": 10, "completion_tokens": 2, "cost": 0.001},
                {"endpoint_kind": "chat_completions"},
            )

        with mock.patch.dict(os.environ, self.env(), clear=False), mock.patch.object(
            runner_module,
            "call_live_model",
            fake_call_live_model,
        ), mock.patch.object(runner_module.sys, "argv", [str(RUNNER), *argv]):
            code = runner_module.main(argv)

        self.assertEqual(code, 0)
        self.assertEqual(len(model_calls), 1)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["budget_gate"]["status"], "passed")
        self.assertTrue(summary["budget_gate"]["execution_request"]["coordinator_decision_ref_present"])
        self.assertEqual(summary["attempt"], 2)

    def test_live_error_after_response_records_model_artifact_paths(self) -> None:
        """Regression: post-response model-output errors remain auditable."""
        (self.workspace / "module.py").write_text("VALUE = 1\nVALUE = 1\n", encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "duplicate value"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "live-ambiguous-artifacts"
        output_path = self.root / "live-ambiguous.json"
        argv = [
            "--workspace",
            str(self.workspace),
            "--task",
            str(self.task_path),
            "--acut",
            str(self.acut_path),
            "--attempt",
            "1",
            "--run-id",
            "unit_openclaw_live_ambiguous_edit_attempt1",
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
        ]

        def fake_call_live_model(**kwargs):
            kwargs["raw_response_path"].write_text('{"choices":[],"usage":{"cost":0.01}}\n', encoding="utf-8")
            return (
                json.dumps({"edits": [{"path": "module.py", "old": "VALUE = 1\n", "new": "VALUE = 2\n"}]}),
                {"prompt_tokens": 10, "completion_tokens": 2, "cost": 0.01},
                {"endpoint_kind": "chat_completions"},
            )

        with mock.patch.dict(os.environ, self.env(), clear=False), mock.patch.object(
            runner_module,
            "call_live_model",
            fake_call_live_model,
        ), mock.patch.object(runner_module.sys, "argv", [str(RUNNER), *argv]):
            code = runner_module.main(argv)

        self.assertEqual(code, 2)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertTrue(summary["model_call_made"])
        self.assertEqual(summary["details"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(summary["prompt_snapshot"], str(artifact_dir / "prompt_snapshot.json"))
        self.assertEqual(summary["raw_response_artifact"], str(artifact_dir / "provider_response.redacted.json"))
        self.assertEqual(summary["budget_gate"]["status"], "passed")
        self.assertEqual(summary["cost_ledger_append"]["status"], "appended")
        self.assertEqual(summary["cost_accounting"]["estimated_cost_usd"], 0.01)

    def test_specialist_context_uses_repo_relative_path_outside_repo_cwd(self) -> None:
        """Regression: specialist runs must not depend on the process cwd."""
        artifact_dir = self.root / "specialist-artifacts"
        output_path = self.root / "specialist.json"
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
                str(REPO_ROOT / "experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml"),
                "--attempt",
                "1",
                "--run-id",
                "unit_openclaw_specialist_context_attempt1",
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
            cwd=self.root,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        snapshot = json.loads((artifact_dir / "prompt_snapshot.json").read_text(encoding="utf-8"))
        self.assertIs(snapshot["specialist_context_included"], True)
        self.assertEqual(snapshot["specialist_context_assertion"]["expected"], "included")
        self.assertEqual(
            snapshot["specialist_context_path"],
            "experiments/core_narrative/context_packs/click_specialist/context_prompt.md",
        )

    def test_click_specialist_acut_without_context_pack_fails_before_model_call(self) -> None:
        """Regression: specialist ACUT identity must not silently run without specialist context."""
        artifact_dir = self.root / "missing-specialist-artifacts"
        output_path = self.root / "missing-specialist.json"
        acut_path = self.root / "missing-specialist-acut.json"
        acut_path.write_text(
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
        argv = [
            "--workspace",
            str(self.workspace),
            "--task",
            str(self.task_path),
            "--acut",
            str(acut_path),
            "--attempt",
            "1",
            "--run-id",
            "unit_missing_specialist_context",
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
        ]
        model_calls: list[dict[str, object]] = []

        def fake_call_live_model(**kwargs):
            model_calls.append(dict(kwargs))
            return '{"edits":[]}', {"prompt_tokens": 10, "completion_tokens": 2}, {}

        with mock.patch.dict(os.environ, self.env(), clear=False), mock.patch.object(
            runner_module,
            "call_live_model",
            fake_call_live_model,
        ), mock.patch.object(runner_module.sys, "argv", [str(RUNNER), *argv]):
            code = runner_module.main(argv)

        self.assertEqual(code, 2)
        self.assertEqual(model_calls, [])
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "specialist_context_missing")

    def test_mock_response_rejects_unsafe_raw_text_before_redaction_mutates_edit(self) -> None:
        """Regression: redaction must not turn unsafe model edits into applied placeholders."""
        redacted_placeholder = "<redacted:url>"
        (self.workspace / "module.py").write_text(f'ENDPOINT = "{redacted_placeholder}"\n', encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "endpoint placeholder"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "unsafe-response-artifacts"
        output_path = self.root / "unsafe-response.json"
        raw_url = "http" + "s://" + "gateway.example.invalid/v1"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
                        "old": f'ENDPOINT = "{raw_url}"\n',
                        "new": 'ENDPOINT = "replacement"\n',
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
                "unit_openclaw_unsafe_raw_response_attempt1",
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

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["unsafe_content"]["reason_counts"], {"full_url": 1})
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), f'ENDPOINT = "{redacted_placeholder}"\n')
        persisted = (artifact_dir / "provider_response.redacted.json").read_text(encoding="utf-8")
        self.assertNotIn(raw_url, persisted)

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

    def test_non_unique_search_replace_old_string_has_model_output_failure_class(self) -> None:
        """Regression: ambiguous search/replace edits are model-output failures, not infra."""
        (self.workspace / "module.py").write_text("VALUE = 1\nVALUE = 1\n", encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "duplicate value"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "ambiguous-edit-artifacts"
        output_path = self.root / "ambiguous-edit.json"
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
                "unit_openclaw_ambiguous_edit_attempt1",
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

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertFalse(summary["model_call_made"])
        self.assertEqual(summary["prompt_snapshot"], str(artifact_dir / "prompt_snapshot.json"))
        self.assertEqual(summary["raw_response_artifact"], str(artifact_dir / "provider_response.redacted.json"))

    def test_task003_style_ambiguous_late_edit_does_not_partially_mutate_workspace(self) -> None:
        """Regression: Click 003-style repeated old strings cannot leave earlier edits applied."""
        original = (
            "import os\n"
            "\n"
            "FIRST = 1\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
            "\n"
            "SECOND = 2\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
        )
        (self.workspace / "module.py").write_text(original, encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "click 003 shape"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "task003-ambiguous-artifacts"
        output_path = self.root / "task003-ambiguous.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
                        "old": "import os\n",
                        "new": "import os\nimport sys\n",
                    },
                    {
                        "path": "module.py",
                        "old": "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n",
                        "new": "prompt = _build_prompt(text, prompt_suffix, show_default, default, show_choices, type)\n",
                    },
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
                "unit_openclaw_task003_ambiguous_late_edit_attempt1",
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

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(summary["details"]["edit_index"], 1)
        self.assertEqual(summary["details"]["occurrences"], 2)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), original)
        self.assertFalse((artifact_dir / "submission.patch").exists())

    def test_edit_bundle_with_extra_top_level_keys_is_contract_violation(self) -> None:
        """Regression: the edit contract is a single-key schema, not JSON plus commentary."""
        artifact_dir = self.root / "extra-key-artifacts"
        output_path = self.root / "extra-key.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
                        "old": "VALUE = 1\n",
                        "new": "VALUE = 2\n",
                    }
                ],
                "notes": "Changed the constant.",
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
                "unit_openclaw_extra_contract_key_attempt1",
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

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "output_contract_violation")
        self.assertEqual(summary["details"]["unsupported_top_level_keys"], ["notes"])
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_anchored_repeated_search_replace_generates_patch(self) -> None:
        """An exact local anchor can disambiguate repeated old text without broad matching."""
        original = (
            "FIRST = 1\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
            "\n"
            "SECOND = 2\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
        )
        expected = (
            "FIRST = 1\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default, show_choices, type)\n"
            "\n"
            "SECOND = 2\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
        )
        (self.workspace / "module.py").write_text(original, encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "click 003 anchor shape"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "anchored-edit-artifacts"
        output_path = self.root / "anchored-edit.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "module.py",
                        "before": "FIRST = 1\n",
                        "old": "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n",
                        "new": "prompt = _build_prompt(text, prompt_suffix, show_default, default, show_choices, type)\n",
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
                "unit_openclaw_anchored_repeated_edit_attempt1",
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
        self.assertEqual(summary["status"], "patch_generated")
        self.assertEqual(summary["patch"]["kind"], "search_replace_edits")
        self.assertEqual(summary["patch"]["edit_count"], 1)
        self.assertEqual(summary["patch"]["anchored_edit_count"], 1)
        self.assertGreater(summary["patch_artifact"]["size_bytes"], 0)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), expected)

    def test_structured_files_contract_generates_patch_without_old_string_matching(self) -> None:
        """File-level JSON should bypass anchored search/replace ambiguity as a measurement contract."""
        original = "VALUE = 1\nVALUE = 1\n"
        expected = "VALUE = 2\nVALUE = 1\n"
        (self.workspace / "module.py").write_text(original, encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "duplicate value"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "structured-files-artifacts"
        output_path = self.root / "structured-files.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "module.py",
                        "action": "replace",
                        "content": expected,
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
                "unit_openclaw_structured_files_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "patch_generated")
        self.assertEqual(summary["submission_contract"], "structured-files-json-v1")
        self.assertEqual(summary["patch"]["kind"], "structured_files")
        self.assertEqual(summary["patch"]["output_contract"], "structured-files-json-v1")
        self.assertGreater(summary["patch_artifact"]["size_bytes"], 0)
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), expected)
        snapshot = json.loads((artifact_dir / "prompt_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["output_contract"], "structured-files-json-v1")

    def test_structured_files_contract_rejects_search_replace_bundle_before_mutation(self) -> None:
        """Failure diagnostics should identify wrong-contract model output as model-owned."""
        artifact_dir = self.root / "structured-files-rejects-edits-artifacts"
        output_path = self.root / "structured-files-rejects-edits.json"
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
                "unit_openclaw_structured_files_rejects_edits_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["submission_contract"], "structured-files-json-v1")
        self.assertEqual(summary["details"]["failure_class"], "output_contract_violation")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_structured_files_contract_rejects_fenced_search_replace_bundle_as_contract_violation(self) -> None:
        """Regression: fenced wrong-contract JSON should not be classified as unsupported output."""
        artifact_dir = self.root / "structured-files-rejects-fenced-edits-artifacts"
        output_path = self.root / "structured-files-rejects-fenced-edits.json"
        response = (
            "```json\n"
            + json.dumps(
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
            + "\n```"
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
                "unit_openclaw_structured_files_rejects_fenced_edits_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["submission_contract"], "structured-files-json-v1")
        self.assertEqual(summary["details"]["failure_class"], "output_contract_violation")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_structured_files_contract_rejects_mixed_files_and_edits_before_mutation(self) -> None:
        """Regression: structured-files-json-v1 requires exactly one top-level files key."""
        artifact_dir = self.root / "structured-files-rejects-mixed-artifacts"
        output_path = self.root / "structured-files-rejects-mixed.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "module.py",
                        "action": "replace",
                        "content": "VALUE = 2\n",
                    }
                ],
                "edits": [
                    {
                        "path": "module.py",
                        "old": "VALUE = 1\n",
                        "new": "VALUE = 2\n",
                    }
                ],
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
                "unit_openclaw_structured_files_rejects_mixed_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["submission_contract"], "structured-files-json-v1")
        self.assertEqual(summary["details"]["failure_class"], "output_contract_violation")
        self.assertEqual(summary["details"]["unsupported_top_level_keys"], ["edits"])
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_structured_files_contract_allows_create_for_declared_missing_path(self) -> None:
        """Regression: advertised create actions can target a declared path that is not yet present."""
        artifact_dir = self.root / "structured-files-create-artifacts"
        output_path = self.root / "structured-files-create.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "new_module.py",
                        "action": "create",
                        "content": "VALUE = 2\n",
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
                "unit_openclaw_structured_files_create_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "new_module.py",
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "patch_generated")
        self.assertEqual(summary["patch"]["kind"], "structured_files")
        self.assertEqual(summary["patch"]["changed_paths"], ["new_module.py"])
        self.assertEqual((self.workspace / "new_module.py").read_text(encoding="utf-8"), "VALUE = 2\n")
        snapshot = json.loads((artifact_dir / "prompt_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["context_files"][0]["exists"], False)

    def test_structured_files_contract_rejects_unsafe_patch_content_as_model_output(self) -> None:
        """Generated full-file content with full URLs is an invalid submission, not infra."""
        artifact_dir = self.root / "structured-files-unsafe-artifacts"
        output_path = self.root / "structured-files-unsafe.json"
        response_path = self.root / "unsafe-response.json"
        response_path.write_text(
            json.dumps(
                {
                    "files": [
                        {
                            "path": "module.py",
                            "action": "replace",
                            "content": 'DOC = "http' + 's://example.invalid/private"\n',
                        }
                    ]
                }
            ),
            encoding="utf-8",
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
                "unit_openclaw_structured_files_unsafe_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response",
                str(response_path),
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "unsafe_generated_text")
        self.assertTrue(summary["details"]["unsafe_content"]["unsafe"])
        self.assertFalse((artifact_dir / "submission.patch").exists())

    def test_structured_files_contract_rejects_incomplete_full_file_placeholders(self) -> None:
        """Regression: structured files must contain complete final file text, not unchanged placeholders."""
        artifact_dir = self.root / "structured-files-incomplete-artifacts"
        output_path = self.root / "structured-files-incomplete.json"
        response = json.dumps(
            {
                "files": [
                    {
                        "path": "module.py",
                        "action": "replace",
                        "content": "VALUE = 2\n# rest of file unchanged\n",
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
                "unit_openclaw_structured_files_incomplete_attempt1",
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
                "--output-contract",
                "structured-files-json-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "structured_files_invalid")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")
        self.assertFalse((artifact_dir / "submission.patch").exists())

    def test_invalid_unified_diff_has_model_output_failure_class(self) -> None:
        """Regression: corrupt unified diffs are invalid submissions, not infra failures."""
        artifact_dir = self.root / "invalid-diff-artifacts"
        output_path = self.root / "invalid-diff.json"
        invalid_patch = (
            "diff --git a/module.py b/module.py\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -1 +1 @@\n"
            "-VALUE = 1\n"
            "VALUE = 2\n"
        )
        response = json.dumps({"unified_diff": invalid_patch})

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
                "unit_openclaw_invalid_unified_diff_attempt1",
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

        self.assertEqual(completed.returncode, 2, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "invalid_unified_diff")
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_patch_or_files_contract_accepts_unified_diff_mock_response(self) -> None:
        """The M2 default patch path accepts verifier-ready unified diffs without JSON mode."""
        artifact_dir = self.root / "patch-or-files-artifacts"
        output_path = self.root / "patch-or-files.json"
        patch = (
            "diff --git a/module.py b/module.py\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -1 +1 @@\n"
            "-VALUE = 1\n"
            "+VALUE = 2\n"
        )
        response = json.dumps({"unified_diff": patch})

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
                "unit_openclaw_patch_or_files_attempt1",
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
                "--output-contract",
                "patch-or-files-v1",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "patch_generated")
        self.assertEqual(summary["submission_contract"], "patch-or-files-v1")
        self.assertEqual(summary["patch"]["kind"], "unified_diff")
        self.assertFalse(summary["model_call_made"])
        self.assertEqual((self.workspace / "module.py").read_text(encoding="utf-8"), "VALUE = 2\n")

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

    def test_live_timeout_after_network_attempt_is_ledgered_conservatively(self) -> None:
        """Regression: provider timeouts after a network attempt must not undercount budget."""
        artifact_dir = self.root / "timeout-live-artifacts"
        output_path = self.root / "timeout-summary.json"

        def fake_call_live_model(**_kwargs):
            raise runner_module.ToolError(
                "LLM request failed",
                error_type="timeout",
                network_attempted=True,
                request_profile={
                    "endpoint_kind": "chat_completions",
                    "model": "openai/gpt-5.4-mini",
                    "prompt_sha256": "unit-prompt",
                },
            )

        with mock.patch.dict(os.environ, self.env(), clear=False), mock.patch.object(
            runner_module,
            "call_live_model",
            fake_call_live_model,
        ):
            code = runner_module.main(
                [
                    "--workspace",
                    str(self.workspace),
                    "--task",
                    str(self.task_path),
                    "--acut",
                    str(self.acut_path),
                    "--attempt",
                    "1",
                    "--run-id",
                    "unit_timeout_after_network_attempt",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--output",
                    str(output_path),
                    "--llm-ledger",
                    str(self.ledger_path),
                    "--projected-cost-usd",
                    "1",
                    "--estimated-cost-usd",
                    "1",
                    "--context-path",
                    "module.py",
                ]
            )

        self.assertEqual(code, 2)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "error")
        self.assertTrue(summary["model_call_made"])
        self.assertEqual(summary["details"]["error_type"], "timeout")
        self.assertEqual(summary["budget_gate"]["status"], "passed")
        self.assertEqual(summary["cost_ledger_append"]["status"], "appended")
        self.assertEqual(summary["cost_accounting"]["estimated_cost_usd"], 1)

        ledger_records = [json.loads(line) for line in self.ledger_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(ledger_records[0]["event"], "runner_error_after_model_attempt")
        self.assertEqual(ledger_records[0]["estimated_cost_usd"], 1)
        self.assertEqual(ledger_records[0]["input_tokens"], 0)
        self.assertEqual(ledger_records[0]["output_tokens"], 0)
        self.assertEqual(ledger_records[0]["metadata"]["cost_basis"], "local_projected_estimate_not_invoice")
        self.assertTrue(ledger_records[0]["metadata"]["model_call_made"])
        self.assertFalse(ledger_records[0]["metadata"]["model_response_received"])
        self.assertTrue(ledger_records[0]["metadata"]["network_attempted"])
        self.assertFalse(ledger_records[0]["metadata"]["provider_usage_reported"])
        self.assertEqual(ledger_records[0]["metadata"]["observed_provider_cost_status"], "not_reported")
        self.assertEqual(ledger_records[0]["metadata"]["error_type"], "timeout")
        self.assertEqual(ledger_records[0]["metadata"]["request_profile"]["prompt_sha256"], "unit-prompt")


if __name__ == "__main__":
    unittest.main()
