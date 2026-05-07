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
                (run_id + "__verify", "prepare_verify_workspace"),
            ],
        )
        self.assertEqual(verify_workspaces, [runner.WORKSPACES_ROOT / (run_id + "__verify")])
        self.assertNotEqual(result["runner_workspace"], result["verify_workspace"])
        self.assertEqual(result["status"], "passed")

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


if __name__ == "__main__":
    unittest.main()
