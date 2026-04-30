#!/usr/bin/env python3
"""Regression checks for Codex CLI inner failure capture."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATCH_COMMAND = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "codex_cli_patch_command.py"


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


class CodexCliPatchCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        run(["git", "init"], cwd=self.workspace)
        run(["git", "config", "user.email", "test" + "@example" + ".invalid"], cwd=self.workspace)
        run(["git", "config", "user.name", "Test User"], cwd=self.workspace)
        (self.workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "module.py"], cwd=self.workspace)
        commit = run(["git", "commit", "-m", "initial"], cwd=self.workspace)
        self.assertEqual(commit.returncode, 0, commit.stderr)

        task_dir = self.workspace / ".core_narrative"
        task_dir.mkdir()
        (task_dir / "task.json").write_text(
            json.dumps({"task_id": "click__rbench__001", "split": "rbench"}),
            encoding="utf-8",
        )
        self.acut_path = self.root / "acut.json"
        self.acut_path.write_text(
            json.dumps(
                {
                    "acut_id": "cheap-generic-swe",
                    "provider": "barcarolle",
                    "model": "openai/gpt-5.4-mini",
                }
            ),
            encoding="utf-8",
        )

    def write_fake_codex(self, exec_body: str) -> Path:
        fake_codex = self.root / "codex"
        body = textwrap.indent(textwrap.dedent(exec_body).strip(), " " * 16)
        fake_codex.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                from __future__ import annotations

                import json
                import os
                import sys

                if sys.argv[1:] == ["debug", "models", "--bundled"]:
                    print(json.dumps({{
                        "models": [
                            {{
                                "slug": "gpt-5.4-mini",
                                "shell_type": "shell_command",
                                "apply_patch_tool_type": "freeform"
                            }},
                            {{
                                "slug": "gpt-5.5",
                                "shell_type": "shell_command",
                                "apply_patch_tool_type": "freeform"
                            }}
                        ]
                    }}))
                    sys.exit(0)

                if "exec" not in sys.argv:
                    sys.exit(99)

                _prompt = sys.stdin.read()
{body}
                """
            ),
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        return fake_codex

    def run_patch_command(self, *, fake_codex: Path, artifact_dir: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        resolved_secret = "unit" + "-redacted" + "-secret"
        resolved_endpoint = "http" + "s://" + "api" + ".example" + ".invalid/v1"
        env["BARCAROLLE_LLM_API_KEY"] = resolved_secret
        env["BARCAROLLE_LLM_BASE_URL"] = resolved_endpoint

        return run(
            [
                sys.executable,
                str(PATCH_COMMAND),
                "--workspace",
                str(self.workspace),
                "--acut",
                str(self.acut_path),
                "--artifact-dir",
                str(artifact_dir),
                "--summary-output",
                str(summary_path),
                "--codex-bin",
                str(fake_codex),
            ],
            cwd=REPO_ROOT,
            env=env,
        )

    def test_nonzero_codex_exec_records_structured_failure_capture(self) -> None:
        """Regression: codex_exec_failed summaries need reviewable non-log diagnostics."""
        fake_codex = self.write_fake_codex(
            """
            sys.stdout.write("safe stdout before failure\\n")
            sys.stdout.write(os.environ["BARCAROLLE_LLM_API_KEY"] + "\\n")
            sys.stdout.write(os.environ["BARCAROLLE_LLM_BASE_URL"] + "\\n")
            sys.stderr.write("safe stderr tail\\n")
            sys.stderr.write(
                "host " + "api" + ".example" + ".invalid "
                + "ip " + "203" + ".0" + ".113" + ".42 "
                + "Bearer " + "abcdefghij" + "\\n"
            )
            sys.exit(7)
            """
        )
        artifact_dir = self.root / "artifacts"
        summary_path = self.root / "summary.json"

        completed = self.run_patch_command(fake_codex=fake_codex, artifact_dir=artifact_dir, summary_path=summary_path)

        self.assertEqual(completed.returncode, 7, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        failure = summary["failure_capture"]
        codex_exec = summary["codex_exec"]

        self.assertEqual(summary["status"], "codex_exec_failed")
        self.assertIs(failure["present"], True)
        self.assertEqual(failure["failure_class"], "nonzero_exit")
        self.assertEqual(failure["exit_code"], 7)
        self.assertIs(failure["timed_out"], False)
        self.assertEqual(failure["stdout_artifact"], codex_exec["stdout_artifact"])
        self.assertEqual(failure["stderr_artifact"], codex_exec["stderr_artifact"])
        self.assertIn("safe stdout before failure", failure["stdout_tail"])
        self.assertIn("safe stderr tail", failure["stderr_tail"])
        forbidden_secret = "unit" + "-redacted" + "-secret"
        forbidden_host = "api" + ".example" + ".invalid"
        forbidden_ip = "203" + ".0" + ".113" + ".42"
        forbidden_bearer = "Bearer " + "abcdefghij"
        self.assertNotIn(forbidden_secret, json.dumps(summary))
        self.assertNotIn(forbidden_host, json.dumps(summary))
        self.assertNotIn(forbidden_ip, json.dumps(summary))
        self.assertNotIn(forbidden_bearer, json.dumps(summary))
        self.assertNotIn("https://", json.dumps(summary))
        self.assertTrue(Path(codex_exec["stdout_artifact"]).is_file())
        self.assertTrue(Path(codex_exec["stderr_artifact"]).is_file())

    def test_exit_zero_without_workspace_diff_records_no_patch_failure_capture(self) -> None:
        """Regression: exit-0 progress-only runs need a no-patch class in the summary."""
        fake_codex = self.write_fake_codex(
            """
            sys.stdout.write("completed without edits\\n")
            sys.exit(0)
            """
        )
        artifact_dir = self.root / "artifacts-no-patch"
        summary_path = self.root / "summary-no-patch.json"

        completed = self.run_patch_command(fake_codex=fake_codex, artifact_dir=artifact_dir, summary_path=summary_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        failure = summary["failure_capture"]

        self.assertEqual(summary["status"], "codex_exec_completed")
        self.assertIs(failure["present"], True)
        self.assertEqual(failure["failure_class"], "no_workspace_patch")
        self.assertEqual(failure["exit_code"], 0)
        self.assertFalse(summary["workspace_patch"]["usable_patch"])
        self.assertEqual(summary["workspace_patch"]["size_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
