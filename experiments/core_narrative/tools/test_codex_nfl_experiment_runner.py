#!/usr/bin/env python3
"""Executable specs for the Codex NFL batch experiment runner."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "experiments" / "core_narrative" / "tools"
RUNNER_PATH = TOOLS_DIR / "codex_nfl_experiment_runner.py"


def load_runner_module():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location("codex_nfl_experiment_runner_under_test", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodexNflExperimentRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_verify_patch_replays_submission_on_clean_workspace(self) -> None:
        """Regression: batch verification must not skip patch apply."""
        runner = load_runner_module()
        normalized_path = self.root / "normalized.json"
        commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            commands.append(list(command))
            normalized_path.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"

        code, result = runner.verify_patch(
            workspace=self.root / "verify-workspace",
            task_id="click__rbench__001",
            acut_id="cheap-generic-swe",
            attempt=1,
            run_id="unit-run",
            artifact_dir=self.root / "artifacts",
            normalized_path=normalized_path,
        )

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(len(commands), 1)
        self.assertIn("--workspace", commands[0])
        self.assertIn(str(self.root / "verify-workspace"), commands[0])
        self.assertNotIn("--skip-apply", commands[0])

    def test_run_one_uses_separate_runner_and_verify_workspaces(self) -> None:
        """Patch generation and canonical verification use different workspaces."""
        runner = load_runner_module()
        runner.RAW_ROOT = self.root / "raw"
        runner.NORMALIZED_ROOT = self.root / "normalized"
        runner.WORKSPACES_ROOT = self.root / "workspaces"
        runner.NORMALIZED_ROOT.mkdir(parents=True)

        prepare_calls: list[tuple[str, str]] = []
        verify_workspaces: list[Path] = []

        def fake_prepare_workspace(task_id, workspace_name, artifact_dir, *, summary_name="prepare_workspace"):
            workspace = runner.WORKSPACES_ROOT / workspace_name
            workspace.mkdir(parents=True)
            prepare_calls.append((workspace_name, summary_name))
            return workspace, {"workspace": str(workspace), "summary_name": summary_name}

        def fake_run_direct_runner(**kwargs):
            patch_path = kwargs["artifact_dir"] / "submission.patch"
            patch_path.write_text("diff --git a/click/core.py b/click/core.py\n", encoding="utf-8")
            return 0, {
                "status": "patch_generated",
                "runner_id": "codex-nfl-direct-search-replace-v1",
                "started_at": "2026-05-07T00:00:00+08:00",
                "finished_at": "2026-05-07T00:00:01+08:00",
                "model_call_made": False,
            }

        def fake_verify_patch(**kwargs):
            verify_workspaces.append(kwargs["workspace"])
            payload = {
                "status": "passed",
                "run_id": kwargs["run_id"],
                "task_id": kwargs["task_id"],
                "acut_id": kwargs["acut_id"],
            }
            kwargs["normalized_path"].write_text(json.dumps(payload), encoding="utf-8")
            return 0, payload

        runner.prepare_workspace = fake_prepare_workspace
        runner.install_workspace = lambda *args, **kwargs: {"status": "installed"}
        runner.context_paths_for_task = lambda task, workspace: ["click/core.py"]
        runner.no_op_verify = lambda **kwargs: {"result": {"status": "failed"}}
        runner.run_direct_runner = fake_run_direct_runner
        runner.verify_patch = fake_verify_patch

        args = SimpleNamespace(
            run_prefix="unit_batch",
            attempt=1,
            install_timeout_seconds=1,
            skip_noop_check=False,
        )
        result = runner.run_one(
            args,
            {"task_id": "click__rbench__001", "split": "rbench"},
            "cheap-generic-swe",
        )

        run_id = "unit_batch__cheap-generic-swe__click__rbench__001__attempt1"
        self.assertEqual(
            prepare_calls,
            [
                (run_id, "prepare_workspace"),
                (run_id + "__noop", "prepare_noop_workspace"),
                (run_id + "__verify", "prepare_verify_workspace"),
            ],
        )
        self.assertEqual(verify_workspaces, [runner.WORKSPACES_ROOT / (run_id + "__verify")])
        self.assertNotEqual(result["runner_workspace"], result["verify_workspace"])
        self.assertEqual(result["status"], "passed")

    def test_run_one_noop_verify_uses_separate_workspace_before_prompting(self) -> None:
        """Regression: no-op verifier mutations must not leak hidden tests into prompts."""
        runner = load_runner_module()
        runner.RAW_ROOT = self.root / "raw"
        runner.NORMALIZED_ROOT = self.root / "normalized"
        runner.WORKSPACES_ROOT = self.root / "workspaces"
        runner.NORMALIZED_ROOT.mkdir(parents=True)

        noop_workspaces: list[Path] = []
        direct_workspaces: list[Path] = []

        def fake_prepare_workspace(task_id, workspace_name, artifact_dir, *, summary_name="prepare_workspace"):
            workspace = runner.WORKSPACES_ROOT / workspace_name
            workspace.mkdir(parents=True)
            (workspace / "tests").mkdir(parents=True, exist_ok=True)
            return workspace, {"workspace": str(workspace), "summary_name": summary_name}

        def fake_no_op_verify(**kwargs):
            workspace = kwargs["workspace"]
            noop_workspaces.append(workspace)
            (workspace / "tests" / "hidden_verifier_marker.py").write_text("leaked = True\n", encoding="utf-8")
            return {"result": {"status": "failed"}}

        def fake_run_direct_runner(**kwargs):
            workspace = kwargs["workspace"]
            direct_workspaces.append(workspace)
            self.assertFalse((workspace / "tests" / "hidden_verifier_marker.py").exists())
            patch_path = kwargs["artifact_dir"] / "submission.patch"
            patch_path.write_text("diff --git a/click/core.py b/click/core.py\n", encoding="utf-8")
            return 0, {
                "status": "patch_generated",
                "runner_id": "codex-nfl-direct-search-replace-v1",
                "model_call_made": False,
            }

        def fake_verify_patch(**kwargs):
            payload = {
                "status": "passed",
                "run_id": kwargs["run_id"],
                "task_id": kwargs["task_id"],
                "acut_id": kwargs["acut_id"],
            }
            kwargs["normalized_path"].write_text(json.dumps(payload), encoding="utf-8")
            return 0, payload

        runner.prepare_workspace = fake_prepare_workspace
        runner.install_workspace = lambda *args, **kwargs: {"status": "installed"}
        runner.context_paths_for_task = lambda task, workspace: ["click/core.py"]
        runner.no_op_verify = fake_no_op_verify
        runner.run_direct_runner = fake_run_direct_runner
        runner.verify_patch = fake_verify_patch

        args = SimpleNamespace(
            run_prefix="unit_noop_isolated",
            attempt=1,
            install_timeout_seconds=1,
            skip_noop_check=False,
        )
        result = runner.run_one(
            args,
            {"task_id": "click__rbench__001", "split": "rbench"},
            "cheap-generic-swe",
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(len(noop_workspaces), 1)
        self.assertEqual(len(direct_workspaces), 1)
        self.assertNotEqual(noop_workspaces[0], direct_workspaces[0])
        self.assertTrue(noop_workspaces[0].name.endswith("__noop"))

    def test_run_one_marks_noop_verifier_pass_as_infra_failed_without_model_call(self) -> None:
        """Regression: a verifier that passes before any patch cannot produce scoreable runs."""
        runner = load_runner_module()
        runner.RAW_ROOT = self.root / "raw"
        runner.NORMALIZED_ROOT = self.root / "normalized"
        runner.WORKSPACES_ROOT = self.root / "workspaces"
        runner.NORMALIZED_ROOT.mkdir(parents=True)

        model_calls: list[str] = []

        def fake_prepare_workspace(task_id, workspace_name, artifact_dir, *, summary_name="prepare_workspace"):
            workspace = runner.WORKSPACES_ROOT / workspace_name
            workspace.mkdir(parents=True)
            return workspace, {"workspace": str(workspace), "summary_name": summary_name}

        def fake_run_direct_runner(**kwargs):
            model_calls.append(kwargs["run_id"])
            return 0, {"status": "patch_generated"}

        runner.prepare_workspace = fake_prepare_workspace
        runner.install_workspace = lambda *args, **kwargs: {"status": "installed"}
        runner.context_paths_for_task = lambda task, workspace: ["click/core.py"]
        runner.no_op_verify = lambda **kwargs: {"result": {"status": "passed"}}
        runner.run_direct_runner = fake_run_direct_runner

        args = SimpleNamespace(
            run_prefix="unit_noop",
            attempt=1,
            install_timeout_seconds=1,
            skip_noop_check=False,
        )
        result = runner.run_one(
            args,
            {"task_id": "click__rbench__001", "split": "rbench"},
            "cheap-generic-swe",
        )

        self.assertEqual(model_calls, [])
        self.assertEqual(result["status"], "infra_failed")
        self.assertFalse(result["scoreable"])
        self.assertEqual(result["normalized"]["metadata"]["failure_class"], "noop_verifier_passed")

    def test_main_preserves_batch_summary_when_first_run_has_no_runner_result(self) -> None:
        """Regression: no-op infra failures still emit a completed batch summary."""
        runner = load_runner_module()
        output_path = self.root / "batch_summary.json"
        runner.load_manifest = lambda path: {
            "tasks": [{"task_id": "click__rbench__001", "split": "rbench"}],
        }
        runner.run_one = lambda args, task, acut_id: {
            "run_id": "unit_noop__cheap-generic-swe__click__rbench__001__attempt1",
            "task_id": "click__rbench__001",
            "acut_id": acut_id,
            "status": "infra_failed",
            "scoreable": False,
            "runner_result": None,
            "noop": {"result": {"status": "passed"}},
        }

        code = runner.main(
            [
                "--tasks",
                "click__rbench__001",
                "--acuts",
                "cheap-generic-swe",
                "--output",
                str(output_path),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "completed")
        self.assertIsNone(payload["started_at"])
        self.assertEqual(payload["aggregate"]["infra_failed"], 1)

    def test_run_direct_runner_default_mock_response_is_parseable_noop_edit(self) -> None:
        """Regression: default mock mode should smoke the runner instead of sending empty edits."""
        runner = load_runner_module()
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "artifacts"
        captured_commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            captured_commands.append(list(command))
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps({"status": "patch_generated"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"
        runner.acut_manifest_path = lambda acut_id: self.root / f"{acut_id}.yaml"
        runner.projected_cost_for_acut = lambda acut_id: "0"

        args = SimpleNamespace(
            attempt=1,
            mode="mock",
            mock_response=None,
            mock_response_text=None,
            llm_ledger=str(self.root / "ledger.jsonl"),
            runner_timeout_seconds=1,
        )
        code, result = runner.run_direct_runner(
            args=args,
            task={"task_id": "click__rbench__001"},
            task_id="click__rbench__001",
            acut_id="cheap-generic-swe",
            workspace=workspace,
            run_id="unit-mock",
            artifact_dir=artifact_dir,
            context_paths=["module.py"],
        )

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "patch_generated")
        command = captured_commands[0]
        mock_text = command[command.index("--mock-response-text") + 1]
        payload = json.loads(mock_text)
        self.assertEqual(
            payload,
            {"edits": [{"path": "module.py", "old": "VALUE = 1\n", "new": "VALUE = 1\n"}]},
        )

    def test_run_direct_runner_default_mock_response_matches_structured_contract(self) -> None:
        """Regression: default mock mode should satisfy the selected structured contract."""
        runner = load_runner_module()
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "artifacts"
        captured_commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            captured_commands.append(list(command))
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps({"status": "patch_generated"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"
        runner.acut_manifest_path = lambda acut_id: self.root / f"{acut_id}.yaml"
        runner.projected_cost_for_acut = lambda acut_id: "0"

        args = SimpleNamespace(
            attempt=1,
            mode="mock",
            mock_response=None,
            mock_response_text=None,
            llm_ledger=str(self.root / "ledger.jsonl"),
            runner_timeout_seconds=1,
            submission_contract="structured-files-json-v1",
        )
        code, result = runner.run_direct_runner(
            args=args,
            task={"task_id": "click__rwork__003"},
            task_id="click__rwork__003",
            acut_id="cheap-generic-swe",
            workspace=workspace,
            run_id="unit-mock-structured",
            artifact_dir=artifact_dir,
            context_paths=["module.py"],
        )

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "patch_generated")
        command = captured_commands[0]
        self.assertEqual(command[command.index("--output-contract") + 1], "structured-files-json-v1")
        mock_text = command[command.index("--mock-response-text") + 1]
        payload = json.loads(mock_text)
        self.assertEqual(
            payload,
            {"files": [{"path": "module.py", "action": "replace", "content": "VALUE = 1\n"}]},
        )

    def test_run_direct_runner_forwards_coordinator_decision_ref(self) -> None:
        """Regression: approved repeat attempts must carry the gate reference to the direct runner."""
        runner = load_runner_module()
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()
        captured_commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            captured_commands.append(list(command))
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text(json.dumps({"status": "patch_generated"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"
        runner.acut_manifest_path = lambda acut_id: self.root / f"{acut_id}.yaml"
        runner.projected_cost_for_acut = lambda acut_id: "0"

        args = SimpleNamespace(
            attempt=2,
            mode="mock",
            mock_response=None,
            mock_response_text='{"edits":[]}',
            llm_ledger=str(self.root / "ledger.jsonl"),
            runner_timeout_seconds=1,
            coordinator_decision_ref="unit_attempt2_approval",
        )
        code, result = runner.run_direct_runner(
            args=args,
            task={"task_id": "click__rbench__001"},
            task_id="click__rbench__001",
            acut_id="cheap-generic-swe",
            workspace=workspace,
            run_id="unit-repeat",
            artifact_dir=artifact_dir,
            context_paths=["module.py"],
        )

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "patch_generated")
        command = captured_commands[0]
        self.assertEqual(
            command[command.index("--coordinator-decision-ref") + 1],
            "unit_attempt2_approval",
        )

    def test_run_direct_runner_forwards_context_caps(self) -> None:
        """Retries can reduce oversized prompts without editing the direct runner contract."""
        runner = load_runner_module()
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()
        captured_commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            captured_commands.append(list(command))
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text(json.dumps({"status": "patch_generated"}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"
        runner.acut_manifest_path = lambda acut_id: self.root / f"{acut_id}.yaml"
        runner.projected_cost_for_acut = lambda acut_id: "0"

        args = SimpleNamespace(
            attempt=2,
            mode="mock",
            mock_response=None,
            mock_response_text='{"edits":[]}',
            llm_ledger=str(self.root / "ledger.jsonl"),
            runner_timeout_seconds=1,
            coordinator_decision_ref=None,
            max_context_chars=80000,
            max_file_chars=50000,
        )
        runner.run_direct_runner(
            args=args,
            task={"task_id": "click__rwork__006"},
            task_id="click__rwork__006",
            acut_id="cheap-generic-swe",
            workspace=workspace,
            run_id="unit-context-caps",
            artifact_dir=artifact_dir,
            context_paths=["module.py"],
        )

        command = captured_commands[0]
        self.assertEqual(command[command.index("--max-context-chars") + 1], "80000")
        self.assertEqual(command[command.index("--max-file-chars") + 1], "50000")

    def test_run_direct_runner_forwards_selected_submission_contract(self) -> None:
        """Measurement-stabilization runs can select the direct output contract per batch."""
        runner = load_runner_module()
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()
        captured_commands: list[list[str]] = []

        def fake_run_capture(command, *, cwd=None, timeout=None):
            captured_commands.append(list(command))
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text(
                json.dumps(
                    {
                        "status": "patch_generated",
                        "submission_contract": "structured-files-json-v1",
                        "output_contract": "structured-files-json-v1",
                    }
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, "", "")

        runner.run_capture = fake_run_capture
        runner.write_command_artifacts = lambda **kwargs: {"exit_code": kwargs["completed"].returncode}
        runner.task_manifest_path = lambda task_id: self.root / f"{task_id}.yaml"
        runner.acut_manifest_path = lambda acut_id: self.root / f"{acut_id}.yaml"
        runner.projected_cost_for_acut = lambda acut_id: "0"

        args = SimpleNamespace(
            attempt=1,
            mode="mock",
            mock_response=None,
            mock_response_text='{"files":[{"path":"module.py","action":"replace","content":"VALUE = 2\\n"}]}',
            llm_ledger=str(self.root / "ledger.jsonl"),
            runner_timeout_seconds=1,
            coordinator_decision_ref=None,
            submission_contract="structured-files-json-v1",
        )
        code, result = runner.run_direct_runner(
            args=args,
            task={"task_id": "click__rwork__003"},
            task_id="click__rwork__003",
            acut_id="cheap-generic-swe",
            workspace=workspace,
            run_id="unit-structured-contract",
            artifact_dir=artifact_dir,
            context_paths=["module.py"],
        )

        self.assertEqual(code, 0)
        self.assertEqual(result["submission_contract"], "structured-files-json-v1")
        command = captured_commands[0]
        self.assertEqual(command[command.index("--output-contract") + 1], "structured-files-json-v1")

    def test_run_one_refuses_existing_normalized_run_id_before_model_call(self) -> None:
        """Regression: batch runs must not overwrite prior run artifacts by default."""
        runner = load_runner_module()
        runner.RAW_ROOT = self.root / "raw"
        runner.NORMALIZED_ROOT = self.root / "normalized"
        runner.WORKSPACES_ROOT = self.root / "workspaces"
        runner.NORMALIZED_ROOT.mkdir(parents=True)
        run_id = "unit_duplicate__cheap-generic-swe__click__rbench__001__attempt1"
        (runner.NORMALIZED_ROOT / f"{run_id}.json").write_text("{}", encoding="utf-8")
        ledger = self.root / "ledger.jsonl"
        ledger.write_text("", encoding="utf-8")

        def fail_prepare(*_args, **_kwargs):
            raise AssertionError("prepare_workspace should not run for duplicate ids")

        runner.prepare_workspace = fail_prepare
        args = SimpleNamespace(
            run_prefix="unit_duplicate",
            attempt=1,
            install_timeout_seconds=1,
            skip_noop_check=False,
            llm_ledger=str(ledger),
        )

        with self.assertRaises(runner.ToolError) as raised:
            runner.run_one(
                args,
                {"task_id": "click__rbench__001", "split": "rbench"},
                "cheap-generic-swe",
            )

        self.assertIn("normalized_result_exists", raised.exception.details["blockers"])

    def test_task_manifest_path_resolves_rwork_task_packs(self) -> None:
        """The batch runner can target held-out RWork task packs, not only RBench."""
        runner = load_runner_module()
        runner.TASK_PACK_ROOT = self.root / "tasks"
        expected = runner.TASK_PACK_ROOT / "click" / "rwork" / "click__rwork__001" / "task.yaml"
        expected.parent.mkdir(parents=True)
        expected.write_text("task_id: click__rwork__001\n", encoding="utf-8")

        self.assertEqual(runner.task_manifest_path("click__rwork__001"), expected)

    def test_main_rejects_tasks_with_wrong_split_even_when_manifest_contains_id(self) -> None:
        """Regression: custom split manifests must not mix RBench task packs into RWork runs."""
        runner = load_runner_module()
        manifest_path = self.root / "mixed_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "split": "RWork",
                    "tasks": [
                        {
                            "task_id": "click__rbench__001",
                            "split": "rbench",
                            "benchmark_split": "RBench",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        output_path = self.root / "summary.json"
        run_calls: list[str] = []

        def fake_run_one(_args, task, _acut_id):
            run_calls.append(task["task_id"])
            return {"status": "passed", "scoreable": True}

        runner.run_one = fake_run_one

        code = runner.main(
            [
                "--task-split",
                "rwork",
                "--task-split-manifest",
                str(manifest_path),
                "--tasks",
                "click__rbench__001",
                "--acuts",
                "cheap-generic-swe",
                "--output",
                str(output_path),
            ]
        )

        self.assertNotEqual(code, 0)
        self.assertEqual(run_calls, [])

    def test_install_workspace_prefers_uv_python312_when_available(self) -> None:
        """RWork Click tasks require Python 3.10+, so use the repo's uv 3.12 path."""
        runner = load_runner_module()
        commands: list[list[str]] = []
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()

        def fake_run_capture(command, *, cwd=None, timeout=None):
            commands.append(list(command))
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.object(runner.shutil, "which", return_value="/opt/homebrew/bin/uv"):
            runner.run_capture = fake_run_capture
            runner.write_command_artifacts = lambda **kwargs: {
                "name": kwargs["name"],
                "command": kwargs["command"],
                "exit_code": kwargs["completed"].returncode,
            }

            summary = runner.install_workspace(self.root / "workspace", artifact_dir, 1)

        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0], ["/opt/homebrew/bin/uv", "venv", "--python", "3.12", ".venv"])
        self.assertEqual(commands[1][:5], ["/opt/homebrew/bin/uv", "pip", "install", "--python", ".venv/bin/python"])
        self.assertEqual(commands[1][-4:], ["-q", "-e", ".", "pytest"])
        self.assertEqual(summary["venv_backend"], "uv")

    def test_install_workspace_falls_back_when_uv_python312_venv_fails(self) -> None:
        """Regression: a broken uv Python 3.12 provisioner must not block sys.executable venv."""
        runner = load_runner_module()
        commands: list[list[str]] = []
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()

        def fake_run_capture(command, *, cwd=None, timeout=None):
            commands.append(list(command))
            if len(commands) == 1:
                return subprocess.CompletedProcess(command, 1, "", "python 3.12 unavailable")
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.object(runner.shutil, "which", return_value="/opt/homebrew/bin/uv"):
            runner.run_capture = fake_run_capture
            runner.write_command_artifacts = lambda **kwargs: {
                "name": kwargs["name"],
                "command": kwargs["command"],
                "exit_code": kwargs["completed"].returncode,
            }

            summary = runner.install_workspace(self.root / "workspace", artifact_dir, 1)

        self.assertEqual(commands[0], ["/opt/homebrew/bin/uv", "venv", "--python", "3.12", ".venv"])
        self.assertEqual(commands[1], [sys.executable, "-m", "venv", ".venv"])
        self.assertEqual(commands[2][-2:], ["--upgrade", "pip"])
        self.assertEqual(commands[3][-4:], ["-q", "-e", ".", "pytest"])
        self.assertEqual(summary["venv_backend"], "python_venv")
        self.assertEqual(summary["uv_venv_create_attempt"]["exit_code"], 1)

    def test_install_workspace_fallback_upgrades_pip_before_editable_install(self) -> None:
        """Fallback venv installs still support pyproject/flit editable projects."""
        runner = load_runner_module()
        commands: list[list[str]] = []
        artifact_dir = self.root / "artifacts"
        artifact_dir.mkdir()

        def fake_run_capture(command, *, cwd=None, timeout=None):
            commands.append(list(command))
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.object(runner.shutil, "which", return_value=None):
            runner.run_capture = fake_run_capture
            runner.write_command_artifacts = lambda **kwargs: {
                "name": kwargs["name"],
                "command": kwargs["command"],
                "exit_code": kwargs["completed"].returncode,
            }

            summary = runner.install_workspace(self.root / "workspace", artifact_dir, 1)

        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[1][-2:], ["--upgrade", "pip"])
        self.assertEqual(commands[2][-4:], ["-q", "-e", ".", "pytest"])
        self.assertEqual(summary["pip_upgrade"]["name"], "venv_pip_upgrade")

    def test_enrich_normalized_metadata_records_clean_replay_evidence_digests(self) -> None:
        """Normalized results carry machine-readable evidence identity for audit gates."""
        runner = load_runner_module()
        task_dir = self.root / "task"
        verifier_dir = task_dir / "verifier"
        verifier_dir.mkdir(parents=True)
        task_path = task_dir / "task.yaml"
        task_path.write_text("task_id: click__rbench__001\n", encoding="utf-8")
        (verifier_dir / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        acut_path = self.root / "acut.json"
        acut_path.write_text(
            json.dumps(
                {
                    "acut_id": "cheap-click-specialist",
                    "metadata": {
                        "specialist_context": {
                            "context_pack": {"pack_hash": "context-pack-digest"}
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        prompt_snapshot = self.root / "prompt_snapshot.json"
        prompt_snapshot.write_text('{"prompt_sha256":"abc"}\n', encoding="utf-8")
        raw_response = self.root / "provider_response.redacted.json"
        raw_response.write_text('{"usage":{"cost":0.01}}\n', encoding="utf-8")
        normalized_path = self.root / "normalized.json"
        normalized = {"metadata": {"tool": "apply_and_verify", "skip_apply": False}}

        runner.task_manifest_path = lambda task_id: task_path
        runner.acut_manifest_path = lambda acut_id: acut_path
        enriched = runner.enrich_normalized_metadata(
            normalized=normalized,
            normalized_path=normalized_path,
            task_id="click__rbench__001",
            acut_id="cheap-click-specialist",
            runner_result={
                "runner_id": "codex-nfl-direct-search-replace-v1",
                "model_call_made": True,
                "prompt_snapshot": str(prompt_snapshot),
                "raw_response_artifact": str(raw_response),
                "cost_accounting": {
                    "observed_provider_cost_status": "provider_response_usage_cost_not_invoice",
                    "observed_provider_cost_usd": 0.01,
                },
                "cost_ledger_append": {
                    "status": "appended",
                    "record_count_after": 12,
                    "estimated_cost_usd": 0.01,
                },
                "budget_gate": {"status": "passed", "allowed": True},
                "submission_contract": "structured-files-json-v1",
                "output_contract": "structured-files-json-v1",
                "patch_artifact": {"size_bytes": 123},
            },
            runner_workspace=self.root / "runner-workspace",
            verify_workspace=self.root / "verify-workspace",
            clean_patch_replay_attempted=True,
        )

        metadata = enriched["metadata"]
        self.assertEqual(metadata["runner_id"], "codex-nfl-batch-v1")
        self.assertEqual(metadata["direct_runner_id"], "codex-nfl-direct-search-replace-v1")
        self.assertTrue(metadata["model_call_made"])
        self.assertEqual(metadata["context_pack_digest"], "context-pack-digest")
        self.assertIsNotNone(metadata["task_manifest_sha256"])
        self.assertIsNotNone(metadata["acut_manifest_sha256"])
        self.assertIsNotNone(metadata["verifier_digest_sha256"])
        self.assertIsNotNone(metadata["prompt_snapshot_sha256"])
        self.assertEqual(metadata["raw_response_artifact"], str(raw_response))
        self.assertEqual(metadata["direct_runner_cost_accounting"]["observed_provider_cost_usd"], 0.01)
        self.assertEqual(metadata["direct_runner_cost_ledger_append"]["status"], "appended")
        self.assertEqual(metadata["direct_runner_budget_gate"]["status"], "passed")
        self.assertEqual(metadata["submission_contract"], "structured-files-json-v1")
        self.assertEqual(metadata["patch_readiness"]["verifier_ready_patch_available"], True)
        self.assertTrue(metadata["clean_patch_replay"]["attempted"])
        self.assertFalse(metadata["clean_patch_replay"]["skip_apply"])
        self.assertTrue(metadata["clean_patch_replay"]["separate_workspace"])
        persisted = json.loads(normalized_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["metadata"]["context_pack_digest"], "context-pack-digest")

    def test_model_output_runner_error_is_invalid_submission_not_infra_failed(self) -> None:
        """Regression: failed model edit contracts are scoreable model-output failures."""
        runner = load_runner_module()
        normalized_path = self.root / "normalized.json"
        payload = runner.write_infra_failed_result(
            run_id="unit-invalid-submission",
            task_id="click__rbench__003",
            split="rbench",
            acut_id="frontier-click-specialist",
            attempt=1,
            normalized_path=normalized_path,
            patch_path=self.root / "submission.patch",
            runner_result={
                "status": "error",
                "error": "edit old string must occur exactly once",
                "details": {"failure_class": "search_replace_old_occurrence_mismatch"},
                "model_call_made": True,
            },
        )

        self.assertEqual(payload["status"], "invalid_submission")
        self.assertEqual(payload["metadata"]["failure_owner"], "model_output")
        self.assertEqual(payload["metadata"]["failure_class"], "search_replace_old_occurrence_mismatch")
        persisted = json.loads(normalized_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["status"], "invalid_submission")


if __name__ == "__main__":
    unittest.main()
