#!/usr/bin/env python3
"""Executable specs for minimal workspace-mode ACUT execution."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any

import workspace_mode_runner as runner


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


class WorkspaceModeRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspaces = self.root / "workspaces"

    def init_source_repo(self, files: dict[str, str] | None = None) -> tuple[Path, str]:
        source = self.root / "source"
        source.mkdir()
        self.assertEqual(git(source, "init", "-q").returncode, 0)
        self.assertEqual(git(source, "config", "user.email", "codex@example.com").returncode, 0)
        self.assertEqual(git(source, "config", "user.name", "Codex").returncode, 0)
        for relative, content in (files or {"module.py": "VALUE = 1\n"}).items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.assertEqual(git(source, "add", ".").returncode, 0)
        self.assertEqual(git(source, "commit", "-q", "-m", "base").returncode, 0)
        base_commit = git(source, "rev-parse", "HEAD").stdout.strip()
        return source, base_commit

    def write_task(
        self,
        *,
        base_commit: str,
        verifier_python: str,
        task_id: str = "unit_task",
    ) -> Path:
        task_dir = self.root / "task"
        (task_dir / "public").mkdir(parents=True)
        (task_dir / "verifier" / "hidden" / "tests").mkdir(parents=True)
        (task_dir / "public" / "acut_statement.md").write_text("Fix the unit task.\n", encoding="utf-8")
        (task_dir / "verifier" / "hidden" / "tests" / "test_hidden_marker.py").write_text(
            "HIDDEN_MARKER = True\n",
            encoding="utf-8",
        )
        run_sh = task_dir / "verifier" / "run.sh"
        run_sh.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "script_dir=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
            "test -f \"$script_dir/hidden/tests/test_hidden_marker.py\"\n"
            "python3 - <<'PY'\n"
            f"{textwrap.dedent(verifier_python).strip()}\n"
            "PY\n",
            encoding="utf-8",
        )
        run_sh.chmod(0o755)
        task_path = task_dir / "task.json"
        task_path.write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "repo_slug": "unit-repo",
                    "split": "unit",
                    "task_family": "workspace-mode",
                    "task_statement_path": "public/acut_statement.md",
                    "source": {"base_commit": base_commit},
                    "verifier": {"command": "verifier/run.sh", "timeout_seconds": 5},
                }
            ),
            encoding="utf-8",
        )
        return task_path

    def run_case(
        self,
        *,
        command: list[str],
        verifier_python: str = "from pathlib import Path\nassert Path('module.py').read_text() == 'VALUE = 2\\n'",
        run_id: str = "unit-run",
    ) -> dict[str, Any]:
        source, base_commit = self.init_source_repo()
        task_path = self.write_task(base_commit=base_commit, verifier_python=verifier_python)
        return runner.execute_workspace_mode(
            task_path=task_path,
            source_repo=source,
            acut_id="unit-acut",
            attempt=1,
            run_id=run_id,
            artifact_dir=self.root / "artifacts" / run_id,
            workspace_root=self.workspaces,
            command=command,
            acut_timeout_seconds=5,
            verifier_timeout_seconds=5,
            install_workspaces=False,
        )

    def test_tracked_file_edit_is_replayed_in_fresh_workspace_and_verified(self) -> None:
        """An ACUT tracked-file edit becomes a candidate patch verified in a fresh workspace."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                "from pathlib import Path; Path('module.py').write_text('VALUE = 2\\n', encoding='utf-8')",
            ],
        )

        patch_text = Path(result["candidate_patch"]["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["status"], "verified_pass")
        self.assertIn("diff --git a/module.py b/module.py", patch_text)
        self.assertNotEqual(result["run_workspace"], result["verification"]["workspace"])
        self.assertEqual(result["verification"]["verifier_exit_code"], 0)

    def test_no_workspace_diff_returns_no_diff_without_verifier(self) -> None:
        """A completed ACUT command with no source diff is not scored."""
        result = self.run_case(command=[sys.executable, "-c", "print('nothing changed')"])

        self.assertEqual(result["status"], "no_diff")
        self.assertFalse(result["verification"]["attempted"])
        self.assertEqual(result["candidate_patch"]["size_bytes"], 0)

    def test_prepare_result_preserves_prepare_payload_and_command_artifact(self) -> None:
        """Workspace preparation returns the child payload and keeps the wrapper artifact separate."""
        result = self.run_case(command=[sys.executable, "-c", "print('nothing changed')"], run_id="prepare-artifacts")

        prepare = result["prepare"]
        self.assertEqual(prepare["status"], "prepared")
        self.assertIn("task_package_path", prepare)
        self.assertIn("statement_path", prepare)
        self.assertIn("warnings", prepare)

        payload_path = Path(result["artifact_paths"]["prepare_run_payload"])
        command_path = Path(result["artifact_paths"]["prepare_run_command"])
        self.assertNotEqual(payload_path, command_path)
        self.assertEqual(json.loads(payload_path.read_text(encoding="utf-8"))["status"], "prepared")
        command_payload = json.loads(command_path.read_text(encoding="utf-8"))
        self.assertEqual(command_payload["name"], "prepare_run_workspace")
        self.assertEqual(command_payload["exit_code"], 0)

    def test_invalid_candidate_patch_maps_to_patch_apply_error(self) -> None:
        """A patch that cannot apply to the fresh workspace is not a verifier failure."""
        source, base_commit = self.init_source_repo()
        task_path = self.write_task(
            base_commit=base_commit,
            verifier_python="from pathlib import Path\nassert Path('module.py').read_text() == 'VALUE = 2\\n'",
        )
        artifact_dir = self.root / "artifacts" / "bad-patch"
        artifact_dir.mkdir(parents=True)
        patch_path = artifact_dir / "submission.patch"
        patch_path.write_text("not a unified diff\n", encoding="utf-8")

        run_workspace, _prepare, base = runner.prepare_workspace_for_task(
            task_path=task_path,
            source_repo=source,
            workspace=self.workspaces / "bad-patch-run",
            artifact_dir=artifact_dir,
            summary_name="prepare_workspace",
        )
        verification = runner.verify_candidate_patch(
            task_path=task_path,
            source_repo=source,
            workspace_root=self.workspaces,
            workspace_name="bad-patch-verify",
            artifact_dir=artifact_dir,
            patch_path=patch_path,
            acut_id="unit-acut",
            attempt=1,
            run_id="bad-patch",
            recorded_base_tree=base["base_tree"],
            verifier_timeout_seconds=5,
            install_workspace_before_verify=False,
        )

        self.assertTrue(run_workspace.exists())
        self.assertEqual(verification["status"], "patch_apply_error")
        self.assertEqual(verification["normalized"]["status"], "invalid_submission")
        self.assertIsNone(verification["verifier_exit_code"])

    def test_verify_base_tree_mismatch_blocks_replay_before_hidden_verifier(self) -> None:
        """A fresh workspace with the wrong base tree is an explicit replay boundary failure."""
        source, base_commit = self.init_source_repo()
        task_path = self.write_task(
            base_commit=base_commit,
            verifier_python="raise AssertionError('verifier must not run')",
        )
        artifact_dir = self.root / "artifacts" / "base-tree-mismatch"
        artifact_dir.mkdir(parents=True)
        patch_path = artifact_dir / "submission.patch"
        patch_path.write_text("not used\n", encoding="utf-8")

        verification = runner.verify_candidate_patch(
            task_path=task_path,
            source_repo=source,
            workspace_root=self.workspaces,
            workspace_name="base-tree-mismatch-verify",
            artifact_dir=artifact_dir,
            patch_path=patch_path,
            acut_id="unit-acut",
            attempt=1,
            run_id="base-tree-mismatch",
            recorded_base_tree="0" * 40,
            verifier_timeout_seconds=5,
            install_workspace_before_verify=False,
        )

        self.assertEqual(verification["status"], "base_tree_mismatch")
        self.assertFalse(verification["attempted"])
        self.assertFalse(verification["base_tree_matches_run"])
        self.assertIsNone(verification["command"])
        self.assertIsNone(verification["normalized"])
        self.assertIsNone(verification["verifier_exit_code"])

    def test_hidden_verifier_material_is_not_visible_in_acut_run_workspace(self) -> None:
        """Hidden verifier files stay outside the ACUT run workspace."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "assert not Path('verifier').exists(); "
                    "assert not any(Path('.').rglob('test_hidden_marker.py')); "
                    "Path('module.py').write_text('VALUE = 2\\n', encoding='utf-8')"
                ),
            ],
            run_id="hidden-boundary",
        )

        run_workspace = Path(result["run_workspace"])
        self.assertEqual(result["status"], "verified_pass")
        self.assertFalse((run_workspace / "verifier").exists())
        self.assertFalse(any(run_workspace.rglob("test_hidden_marker.py")))
        self.assertTrue((run_workspace / ".core_narrative" / "task.json").exists())

    def test_untracked_source_file_is_deterministically_included_in_candidate_patch(self) -> None:
        """A regular untracked source file is added to the candidate patch."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "Path('z_generated.py').write_text('ZED = True\\n', encoding='utf-8'); "
                    "Path('a_generated.py').write_text('AYE = True\\n', encoding='utf-8')"
                ),
            ],
            verifier_python=(
                "from pathlib import Path\n"
                "assert Path('a_generated.py').read_text() == 'AYE = True\\n'\n"
                "assert Path('z_generated.py').read_text() == 'ZED = True\\n'"
            ),
            run_id="untracked-source",
        )

        patch_text = Path(result["candidate_patch"]["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["status"], "verified_pass")
        self.assertIn("new file mode", patch_text)
        self.assertIn("+++ b/a_generated.py", patch_text)
        self.assertIn("+++ b/z_generated.py", patch_text)
        self.assertLess(patch_text.index("+++ b/a_generated.py"), patch_text.index("+++ b/z_generated.py"))
        self.assertIn("+AYE = True", patch_text)
        self.assertIn("+ZED = True", patch_text)
        dispositions = {item["path"]: item["disposition"] for item in result["candidate_patch"]["untracked_files"]}
        self.assertEqual(dispositions["a_generated.py"], "included")
        self.assertEqual(dispositions["z_generated.py"], "included")
        included_paths = [item["path"] for item in result["candidate_patch"]["included_untracked_files"]]
        self.assertEqual(included_paths, ["a_generated.py", "z_generated.py"])

    def test_harness_generated_untracked_files_do_not_enter_candidate_patch(self) -> None:
        """Harness-owned untracked files are ignored while source edits remain scoreable."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "Path('.core_narrative/local.log').write_text('metadata\\n', encoding='utf-8'); "
                    "Path('.pytest_cache').mkdir(exist_ok=True); "
                    "Path('.pytest_cache/README.md').write_text('cache\\n', encoding='utf-8'); "
                    "Path('pkg/__pycache__').mkdir(parents=True, exist_ok=True); "
                    "Path('pkg/__pycache__/x.pyc').write_bytes(b'cache'); "
                    "Path('.venv/bin').mkdir(parents=True, exist_ok=True); "
                    "Path('.venv/bin/activate').write_text('https://example.invalid\\n', encoding='utf-8'); "
                    "Path('pkg.egg-info').mkdir(exist_ok=True); "
                    "Path('pkg.egg-info/PKG-INFO').write_text('metadata\\n', encoding='utf-8'); "
                    "Path('module.py').write_text('VALUE = 2\\n', encoding='utf-8')"
                ),
            ],
            run_id="harness-files",
        )

        patch_text = Path(result["candidate_patch"]["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["status"], "verified_pass")
        self.assertIn("diff --git a/module.py b/module.py", patch_text)
        self.assertNotIn(".core_narrative/local.log", patch_text)
        self.assertNotIn(".pytest_cache", patch_text)
        self.assertNotIn("__pycache__", patch_text)
        self.assertNotIn(".venv", patch_text)
        self.assertNotIn(".egg-info", patch_text)
        self.assertNotIn("https://example.invalid", patch_text)
        ignored = [item for item in result["candidate_patch"]["untracked_files"] if item["disposition"] == "ignored_harness"]
        self.assertGreaterEqual(len(ignored), 5)

    def test_nonzero_acut_exit_does_not_override_successful_fresh_verification(self) -> None:
        """A non-zero ACUT command can still verify if it leaves a valid diff."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "from pathlib import Path; "
                    "Path('module.py').write_text('VALUE = 2\\n', encoding='utf-8'); "
                    "sys.exit(7)"
                ),
            ],
            run_id="nonzero-but-valid",
        )

        self.assertEqual(result["status"], "verified_pass")
        self.assertEqual(result["metadata"]["acut_exit_code"], 7)
        self.assertEqual(result["metadata"]["acut_command_status"], "nonzero")

    def test_missing_acut_executable_maps_to_acut_command_error(self) -> None:
        """Command launch errors are structured ACUT command errors, not verifier outcomes."""
        result = self.run_case(command=["definitely-missing-acut-executable"])

        self.assertEqual(result["status"], "acut_command_error")
        self.assertEqual(result["metadata"]["acut_command_status"], "error")
        self.assertIsNone(result["metadata"]["acut_exit_code"])
        self.assertFalse(result["verification"]["attempted"])

    def test_candidate_patch_extraction_failure_after_acut_start_is_not_command_error(self) -> None:
        """Extraction failures after ACUT launch are harness failures, not launch failures."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "import shutil; "
                    "from pathlib import Path; "
                    "Path('started.txt').write_text('started\\n', encoding='utf-8'); "
                    "shutil.rmtree('.git')"
                ),
            ],
            run_id="extract-failure-after-start",
        )

        self.assertEqual(result["status"], "candidate_patch_extraction_error")
        self.assertEqual(result["metadata"]["acut_command_status"], "zero")
        self.assertEqual(result["metadata"]["acut_exit_code"], 0)
        self.assertIsNone(result["metadata"]["acut_command_error"])
        self.assertFalse(result["verification"]["attempted"])
        self.assertEqual(result["verification"]["reason"], "candidate_patch_extraction_failed")
        self.assertIn("failed to inspect workspace status", result["error"])

    def test_head_drift_is_recorded_and_diff_still_uses_base_ref(self) -> None:
        """If the ACUT commits, the candidate patch is still extracted from BASE_REF."""
        result = self.run_case(
            command=[
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import subprocess; "
                    "Path('module.py').write_text('VALUE = 2\\n', encoding='utf-8'); "
                    "subprocess.run(['git', 'add', 'module.py'], check=True); "
                    "subprocess.run(['git', 'commit', '-q', '-m', 'acut commit'], check=True)"
                ),
            ],
            run_id="head-drift",
        )

        patch_text = Path(result["candidate_patch"]["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["status"], "verified_pass")
        self.assertTrue(result["candidate_patch"]["head_drifted"])
        self.assertIn("diff --git a/module.py b/module.py", patch_text)
        self.assertEqual(result["candidate_patch"]["diff_base_ref"], result["candidate_patch"]["base_ref"])


if __name__ == "__main__":
    unittest.main()
