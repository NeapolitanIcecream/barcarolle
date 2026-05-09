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
        env["BARCAROLLE_LLM_API_KEY"] = "unit-secret-value"
        env["BARCAROLLE_LLM_BASE_URL"] = "https://llm-gateway.example.invalid/v1"
        return env

    def run_direct(
        self,
        *,
        response: str,
        artifact_name: str,
        output_name: str,
        context_paths: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        artifact_dir = self.root / artifact_name
        output_path = self.root / output_name
        command = [
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
            f"unit_codex_nfl_{artifact_name}_attempt1",
            "--artifact-dir",
            str(artifact_dir),
            "--output",
            str(output_path),
            "--llm-ledger",
            str(self.ledger_path),
            "--projected-cost-usd",
            "1",
            "--mock-response-text",
            response,
        ]
        for context_path in context_paths or ["click/core.py"]:
            command.extend(["--context-path", context_path])
        return run(command, cwd=REPO_ROOT, env=self.env())

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

    def test_task003_style_ambiguous_edit_is_invalid_without_partial_mutation(self) -> None:
        """Regression: repeated Click prompt edits need exact anchors or a replayable patch."""
        original = (
            "from .types import convert_type\n"
            "\n"
            "FIRST = 1\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
            "\n"
            "SECOND = 2\n"
            "prompt = _build_prompt(text, prompt_suffix, show_default, default)\n"
        )
        termui = self.workspace / "click" / "termui.py"
        termui.write_text(original, encoding="utf-8")
        run(["git", "add", "click/termui.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "add termui prompt shape"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        artifact_dir = self.root / "task003-ambiguous"
        output_path = self.root / "task003-ambiguous.json"
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "click/termui.py",
                        "old": "from .types import convert_type\n",
                        "new": "from .types import convert_type, Choice\n",
                    },
                    {
                        "path": "click/termui.py",
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
                "unit_codex_nfl_task003_ambiguous_attempt1",
                "--artifact-dir",
                str(artifact_dir),
                "--output",
                str(output_path),
                "--llm-ledger",
                str(self.ledger_path),
                "--projected-cost-usd",
                "1",
                "--context-path",
                "click/termui.py",
                "--mock-response-text",
                response,
            ],
            cwd=REPO_ROOT,
            env=self.env(),
        )

        self.assertEqual(completed.returncode, 2)
        summary = json.loads(output_path.read_text(encoding="utf-8"))
        snapshot = json.loads((artifact_dir / "prompt_snapshot.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["runner_id"], "codex-nfl-direct-search-replace-v1")
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["details"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(summary["details"]["edit_index"], 1)
        self.assertEqual(summary["details"]["occurrences"], 2)
        self.assertEqual(snapshot["output_contract"], "anchored-search-replace-json-v3")
        self.assertEqual(snapshot["output_contract_schema"]["primary_top_level_key"], "edits")
        self.assertEqual(termui.read_text(encoding="utf-8"), original)

    def test_redacted_source_old_with_safe_replacement_records_source_derived_patch_url(self) -> None:
        """Regression: raw URLs from source preimage lines are attributed without writing unsafe artifacts."""
        source_url = "https://github.com/pallets/click/issues/3121"
        original = (
            "def get_default():\n"
            "    # Lazily resolve default=True to flag_value.\n"
            f"    # {source_url}\n"
            "    if value is True and self.is_flag:\n"
            "        value = self.flag_value\n"
            "    return value\n"
        )
        (self.workspace / "click" / "core.py").write_text(original, encoding="utf-8")
        run(["git", "add", "click/core.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "add source url case"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "click/core.py",
                        "old": (
                            "    # Lazily resolve default=True to flag_value.\n"
                            "    # <redacted:url>\n"
                            "    if value is True and self.is_flag:\n"
                            "        value = self.flag_value\n"
                        ),
                        "new": "    if value is True and self.is_flag:\n        value = self.flag_value\n",
                    }
                ]
            }
        )

        completed = self.run_direct(
            response=response,
            artifact_name="source-derived-url",
            output_name="source-derived-url.json",
        )

        self.assertEqual(completed.returncode, 2)
        summary = json.loads((self.root / "source-derived-url.json").read_text(encoding="utf-8"))
        details = summary["details"]
        patch_artifact = details["patch_artifact"]
        attribution = patch_artifact["unsafe_content_attribution"]

        self.assertEqual(details["failure_class"], "unsafe_generated_text")
        self.assertEqual(attribution["classification"], "source_derived_full_url")
        self.assertTrue(attribution["all_unsafe_reasons_source_derived"])
        self.assertEqual(attribution["model_generated_full_url_count"], 0)
        self.assertEqual(attribution["full_url_role_counts"], {"source_removed": 1})
        self.assertFalse(patch_artifact["written"])
        self.assertFalse((self.root / "source-derived-url" / "submission.patch").exists())
        preview = Path(patch_artifact["redacted_preview"]["path"])
        self.assertTrue(preview.exists())
        preview_text = preview.read_text(encoding="utf-8")
        self.assertNotIn(source_url, preview_text)
        self.assertNotRegex(preview_text, r"https?://")
        self.assertEqual(
            details["patch_result_before_patch_artifact"]["edit_diagnostics"][0]["diagnostic"]["code"],
            "redacted_source_text_matched_raw_source",
        )
        self.assertFalse(details["patch_result_before_patch_artifact"]["edit_diagnostics"][0]["content_recorded"])

    def test_model_generated_raw_url_replacement_is_rejected_before_patch_artifact(self) -> None:
        """Regression: generated replacement URLs remain true unsafe generated text."""
        original = (self.workspace / "click" / "core.py").read_text(encoding="utf-8")
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "click/core.py",
                        "old": "VALUE = 1\n",
                        "new": 'VALUE = "https://generated.example.invalid/path"\n',
                    }
                ]
            }
        )

        completed = self.run_direct(
            response=response,
            artifact_name="generated-url",
            output_name="generated-url.json",
        )

        self.assertEqual(completed.returncode, 2)
        summary = json.loads((self.root / "generated-url.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["details"]["failure_class"], "unsafe_generated_text")
        self.assertEqual(summary["details"]["unsafe_content"]["reason_counts"], {"full_url": 1})
        self.assertNotIn("patch_artifact", summary["details"])
        self.assertEqual((self.workspace / "click" / "core.py").read_text(encoding="utf-8"), original)

    def test_redaction_placeholder_persistence_is_rejected(self) -> None:
        """Regression: replacement text may not persist redaction placeholders into source."""
        original = (self.workspace / "click" / "core.py").read_text(encoding="utf-8")
        response = json.dumps(
            {
                "edits": [
                    {
                        "path": "click/core.py",
                        "old": "VALUE = 1\n",
                        "new": 'VALUE = "<redacted:url>"\n',
                    }
                ]
            }
        )

        completed = self.run_direct(
            response=response,
            artifact_name="placeholder-persistence",
            output_name="placeholder-persistence.json",
        )

        self.assertEqual(completed.returncode, 2)
        summary = json.loads((self.root / "placeholder-persistence.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["details"]["failure_class"], "search_replace_redacted_source_mismatch")
        self.assertEqual(
            summary["details"]["diagnostic"]["code"],
            "redacted_replacement_placeholder_persistence",
        )
        self.assertEqual(summary["details"]["replacement_redacted_url_marker_count"], 1)
        self.assertFalse(summary["details"]["content_recorded"])
        self.assertEqual((self.workspace / "click" / "core.py").read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
