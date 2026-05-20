#!/usr/bin/env python3
"""Regression checks for Codex CLI inner failure capture."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATCH_COMMAND = REPO_ROOT / "experiments" / "core_narrative" / "tools" / "codex_cli_patch_command.py"
HOSTNAME_LABEL_RE = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
BEARER_TOKEN_SHAPED_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{10,}\b", re.IGNORECASE)
FULL_URL_SHAPED_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
HOSTNAME_SHAPED_RE = re.compile(
    rf"(?<![A-Za-z0-9_.-])(?:{HOSTNAME_LABEL_RE}\.)+"
    rf"(?=[A-Za-z0-9-]*[A-Za-z]){HOSTNAME_LABEL_RE}\.?"
    rf"(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)
IPV4_SHAPED_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_SHAPED_RE = re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,}[0-9A-Fa-f]{1,4}\b")


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
        self.resolved_secret = "unit" + "-redacted" + "-secret"
        self.resolved_endpoint_host = "api" + ".example" + ".invalid"
        self.resolved_endpoint = "http" + "s://" + self.resolved_endpoint_host + "/v1"
        self.raw_bearer = "Bearer " + "abcdefghij123456"
        self.raw_hostname = "worker01" + ".service-mesh" + ".corpzone"
        self.raw_ip = "203" + ".0" + ".113" + ".42"

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

    def run_patch_command(
        self,
        *,
        fake_codex: Path,
        artifact_dir: Path,
        summary_path: Path,
        extra_args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["BARCAROLLE_LLM_API_KEY"] = self.resolved_secret
        env["BARCAROLLE_LLM_BASE_URL"] = self.resolved_endpoint

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
                *(extra_args or []),
            ],
            cwd=REPO_ROOT,
            env=env,
        )

    def assert_failure_capture_redacted(self, summary: dict[str, object]) -> None:
        failure = summary["failure_capture"]
        self.assertIsInstance(failure, dict)
        codex_exec = summary["codex_exec"]
        self.assertIsInstance(codex_exec, dict)
        stdout_artifact = Path(str(codex_exec["stdout_artifact"]))
        stderr_artifact = Path(str(codex_exec["stderr_artifact"]))
        self.assertTrue(stdout_artifact.is_file())
        self.assertTrue(stderr_artifact.is_file())
        checked_texts = [
            stdout_artifact.read_text(encoding="utf-8"),
            stderr_artifact.read_text(encoding="utf-8"),
            str(failure["stdout_tail"]),
            str(failure["stderr_tail"]),
        ]
        forbidden_values = [
            self.resolved_secret,
            self.resolved_endpoint,
            self.resolved_endpoint_host,
            self.raw_bearer,
            self.raw_hostname,
            self.raw_ip,
        ]
        for text in checked_texts:
            for value in forbidden_values:
                self.assertNotIn(value, text)
            self.assertIsNone(BEARER_TOKEN_SHAPED_RE.search(text), text)
            self.assertIsNone(FULL_URL_SHAPED_RE.search(text), text)
            self.assertIsNone(HOSTNAME_SHAPED_RE.search(text), text)
            self.assertIsNone(IPV4_SHAPED_RE.search(text), text)
            self.assertIsNone(IPV6_SHAPED_RE.search(text), text)

    def test_nonzero_codex_exec_records_structured_failure_capture(self) -> None:
        """Regression: codex_exec_failed summaries need reviewable non-log diagnostics."""
        fake_codex = self.write_fake_codex(
            """
            sys.stdout.write("safe stdout before failure\\n")
            sys.stdout.write(os.environ["BARCAROLLE_LLM_API_KEY"] + "\\n")
            sys.stdout.write(os.environ["BARCAROLLE_LLM_BASE_URL"] + "\\n")
            sys.stderr.write("safe stderr tail\\n")
            sys.stderr.write(
                "host " + "worker01" + ".service-mesh" + ".corpzone "
                + "ip " + "203" + ".0" + ".113" + ".42 "
                + "Bearer " + "abcdefghij123456" + "\\n"
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
        self.assertNotIn(self.resolved_secret, json.dumps(summary))
        self.assertNotIn(self.raw_hostname, json.dumps(summary))
        self.assertNotIn(self.raw_ip, json.dumps(summary))
        self.assertNotIn(self.raw_bearer, json.dumps(summary))
        self.assertNotIn("https://", json.dumps(summary))
        self.assert_failure_capture_redacted(summary)

    def test_responses_stream_disconnect_records_transport_failure_class(self) -> None:
        """Regression: repeated Responses stream disconnects need a machine-readable class."""
        fake_codex = self.write_fake_codex(
            """
            for attempt in range(1, 6):
                print(json.dumps({
                    "type": "error",
                    "message": (
                        f"Reconnecting... {attempt}/5 "
                        f"(stream disconnected before completion: error sending request for url "
                        f"({os.environ['BARCAROLLE_LLM_BASE_URL']}/responses))"
                    ),
                }))
            print(json.dumps({
                "type": "error",
                "message": (
                    "stream disconnected before completion: error sending request for url "
                    f"({os.environ['BARCAROLLE_LLM_BASE_URL']}/responses)"
                ),
            }))
            sys.exit(1)
            """
        )
        artifact_dir = self.root / "artifacts-stream-disconnect"
        summary_path = self.root / "summary-stream-disconnect.json"

        completed = self.run_patch_command(fake_codex=fake_codex, artifact_dir=artifact_dir, summary_path=summary_path)

        self.assertEqual(completed.returncode, 1, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        failure = summary["failure_capture"]
        transport = summary["transport_failure"]

        self.assertEqual(summary["status"], "codex_exec_failed")
        self.assertEqual(failure["failure_class"], "responses_streaming_disconnect")
        self.assertEqual(failure["transport_failure"]["failure_class"], "responses_streaming_disconnect")
        self.assertIs(transport["present"], True)
        self.assertEqual(transport["failure_class"], "responses_streaming_disconnect")
        self.assertEqual(transport["wire_api"], "responses")
        self.assertEqual(transport["endpoint_path"], "/responses")
        self.assertEqual(transport["after_reconnects"], 5)
        self.assertEqual(transport["reconnect_limit"], 5)
        self.assertIs(transport["retry_exhausted"], True)
        self.assertIs(transport["messages_recorded"], False)
        self.assertIs(transport["content_recorded"], False)
        self.assert_failure_capture_redacted(summary)

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

    def test_timeout_records_structured_failure_capture_with_redacted_artifacts(self) -> None:
        """Regression: timed-out codex exec runs need non-log redacted diagnostics."""
        fake_codex = self.write_fake_codex(
            """
            import time

            sys.stdout.write("timeout stdout before sleep\\n")
            sys.stdout.write(os.environ["BARCAROLLE_LLM_API_KEY"] + "\\n")
            sys.stdout.flush()
            sys.stderr.write(
                "timeout stderr " + "worker01" + ".service-mesh" + ".corpzone "
                + "Bearer " + "abcdefghij123456" + "\\n"
            )
            sys.stderr.flush()
            time.sleep(5)
            """
        )
        artifact_dir = self.root / "artifacts-timeout"
        summary_path = self.root / "summary-timeout.json"

        completed = self.run_patch_command(
            fake_codex=fake_codex,
            artifact_dir=artifact_dir,
            summary_path=summary_path,
            extra_args=["--codex-timeout-seconds", "1"],
        )

        self.assertEqual(completed.returncode, 124, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        failure = summary["failure_capture"]

        self.assertEqual(summary["status"], "timeout")
        self.assertIs(failure["present"], True)
        self.assertEqual(failure["failure_class"], "timeout")
        self.assertIs(failure["timed_out"], True)
        self.assertEqual(failure["exit_code"], None)
        self.assertIn("timeout stdout before sleep", failure["stdout_tail"])
        self.assertIn("timeout stderr", failure["stderr_tail"])
        self.assert_failure_capture_redacted(summary)

    def test_unsafe_patch_content_records_structured_failure_capture_with_redacted_artifacts(self) -> None:
        """Regression: unsafe workspace diffs need a distinct failure class."""
        fake_codex = self.write_fake_codex(
            """
            from pathlib import Path

            Path("module.py").write_text(
                "VALUE = " + repr(os.environ["BARCAROLLE_LLM_API_KEY"]) + "\\n",
                encoding="utf-8",
            )
            sys.stdout.write("unsafe patch stdout\\n")
            sys.stderr.write(
                "unsafe patch stderr " + "worker01" + ".service-mesh" + ".corpzone "
                + "ip " + "203" + ".0" + ".113" + ".42 "
                + os.environ["BARCAROLLE_LLM_BASE_URL"] + "\\n"
            )
            sys.exit(0)
            """
        )
        artifact_dir = self.root / "artifacts-unsafe"
        summary_path = self.root / "summary-unsafe.json"

        completed = self.run_patch_command(fake_codex=fake_codex, artifact_dir=artifact_dir, summary_path=summary_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        failure = summary["failure_capture"]

        self.assertEqual(summary["status"], "codex_exec_completed")
        self.assertIs(failure["present"], True)
        self.assertEqual(failure["failure_class"], "unsafe_patch_content")
        self.assertIs(failure["timed_out"], False)
        self.assertTrue(summary["workspace_patch"]["unsafe_content_detected"])
        self.assertFalse(summary["workspace_patch"]["usable_patch"])
        self.assert_failure_capture_redacted(summary)


if __name__ == "__main__":
    unittest.main()
