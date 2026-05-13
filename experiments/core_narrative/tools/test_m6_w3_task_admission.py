#!/usr/bin/env python3
"""Executable specs for M6-W3 task admission and denominator freeze."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from _common import ToolError
import m6_w3_task_admission as admission


def candidate(family: str, index: int, *, rating: int = 3, patch_bytes: int = 1000) -> dict[str, object]:
    return {
        "candidate_id": f"candidate-{family}-{index}",
        "family": family,
        "human_difficulty_rating": rating,
        "reference_patch_bytes": patch_bytes + index,
        "changed_files": ["src/click/core.py", f"tests/test_{index}.py"],
        "changed_file_set_digest": f"digest-{family}-{index}",
        "source_anchor": f"commit:{family}-{index}",
        "commit": f"target-{index}",
        "base_commit": f"base-{index}",
        "reference_patch_digest": f"patch-{index}",
        "reference_patch_complexity_band": "small",
        "problem_statement": "Fix the Click behavior.",
        "verifier_command": f".venv/bin/python -m pytest -q tests/test_{index}.py::test_case",
        "source_files": ["src/click/core.py"],
        "test_files": [f"tests/test_{index}.py"],
        "test_nodes": [f"tests/test_{index}.py::test_case"],
    }


class M6W3TaskAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_extract_test_nodes_from_diff_reports_unique_pytest_nodes(self) -> None:
        """Added pytest functions become hidden-verifier node ids without duplicates."""
        diff = """diff --git a/tests/test_core.py b/tests/test_core.py
@@ -1,0 +2,8 @@
+def test_option_default():
+    pass
+async def test_async_prompt():
+    pass
+def test_option_default():
+    pass
 def helper():
     pass
"""

        nodes = admission.extract_test_nodes_from_diff(diff, "tests/test_core.py")

        self.assertEqual(
            nodes,
            [
                "tests/test_core.py::test_option_default",
                "tests/test_core.py::test_async_prompt",
            ],
        )

    def test_extract_test_nodes_from_diff_uses_hunk_context_for_modified_tests(self) -> None:
        """Modified existing pytest functions are eligible verifier nodes via hunk context."""
        diff = """diff --git a/tests/test_testing.py b/tests/test_testing.py
@@ -20,2 +20,3 @@ def test_runner_with_stream():
     result = runner.invoke(cli)
+    assert result.output == "expected"
"""

        nodes = admission.extract_test_nodes_from_diff(diff, "tests/test_testing.py")

        self.assertEqual(nodes, ["tests/test_testing.py::test_runner_with_stream"])

    def test_changed_file_set_digest_normalizes_src_prefix(self) -> None:
        """Disjointness digests compare Click source paths independent of src prefix."""
        self.assertEqual(
            admission.changed_file_set_digest(["src/click/core.py", "tests/test_core.py"]),
            admission.changed_file_set_digest(["click/core.py", "tests/test_core.py"]),
        )
        self.assertNotEqual(
            admission.changed_file_set_digest(["src/click/core.py"], anchor="commit:a"),
            admission.changed_file_set_digest(["src/click/core.py"], anchor="commit:b"),
        )
        self.assertEqual(admission.changed_file_anchor_set(["src/click/core.py"], anchor="commit:a"), ["commit:a::click/core.py"])

    def test_public_tool_path_redacts_local_absolute_python_path(self) -> None:
        """Public admission summaries keep tool provenance without a local home path."""
        self.assertEqual(
            admission.public_tool_path("/tmp/example/.local/share/uv/python/cpython-3.12/bin/python3.12"),
            "python3.12",
        )
        self.assertEqual(
            admission.public_tool_path(str(admission.REPO_ROOT / "experiments/core_narrative/tools/m6_w3_task_admission.py")),
            "experiments/core_narrative/tools/m6_w3_task_admission.py",
        )

    def test_known_hanging_verifier_nodes_are_excluded_from_candidate_admission(self) -> None:
        """Candidates with no-op verifier nodes known to hang are filtered before smoke."""
        self.assertTrue(admission.has_unsuitable_test_nodes(["tests/test_utils.py::test_echo_via_pager"]))
        self.assertTrue(admission.has_unsuitable_test_nodes(["tests/test_utils.py::test_prompts_eof"]))
        self.assertTrue(admission.has_unsuitable_test_nodes(["tests/test_termui.py::test_confirmation_prompt"]))
        self.assertFalse(admission.has_unsuitable_test_nodes(["tests/test_termui.py::test_progressbar_hidden_manual"]))

    def test_classify_family_routes_click_behavior_surfaces(self) -> None:
        """Candidate families follow the W3 quota taxonomy."""
        self.assertEqual(
            admission.classify_family("Fix CliRunner stderr isolation", ["src/click/testing.py"], ["tests/test_testing.py"]),
            "CliRunner/testing/input-output isolation",
        )
        self.assertEqual(
            admission.classify_family("Normalize Choice values", ["src/click/types.py"], ["tests/test_types.py"]),
            "type conversion/parameter normalization",
        )
        self.assertEqual(
            admission.classify_family("Fix prompt color rendering", ["src/click/termui.py"], ["tests/test_termui.py"]),
            "prompt/termui/output rendering",
        )
        self.assertEqual(
            admission.classify_family("Fix envvar flag default", ["src/click/core.py"], ["tests/test_options.py"]),
            "option/default/envvar/flag semantics",
        )
        self.assertEqual(
            admission.classify_family("Handle parser edge case", ["src/click/parser.py"], ["tests/test_parser.py"]),
            "parser/mixed integration",
        )

    def test_select_primary_and_reserve_enforces_family_quotas(self) -> None:
        """The frozen denominator contains four primary and two reserve tasks per W3 family."""
        admitted: list[dict[str, object]] = []
        for family in admission.FAMILY_QUOTAS:
            for index in range(6):
                admitted.append(candidate(family, index, rating=2 + (index % 3), patch_bytes=500 + index))

        primary, reserve = admission.select_primary_and_reserve(admitted)

        self.assertEqual(len(primary), 20)
        self.assertEqual(len(reserve), 10)
        self.assertEqual(Counter(row["family"] for row in primary), admission.FAMILY_QUOTAS)
        self.assertEqual(Counter(row["family"] for row in reserve), {family: 2 for family in admission.FAMILY_QUOTAS})

    def test_select_primary_and_reserve_rejects_short_family(self) -> None:
        """A family below the primary quota blocks denominator freeze."""
        admitted: list[dict[str, object]] = []
        for family in admission.FAMILY_QUOTAS:
            count = 3 if family == "parser/mixed integration" else 6
            for index in range(count):
                admitted.append(candidate(family, index))

        with self.assertRaises(ToolError):
            admission.select_primary_and_reserve(admitted)

    def test_balance_candidate_pool_prefers_family_coverage_before_fill(self) -> None:
        """The 40-row candidate pool keeps family-specific admission buffers before recency fill."""
        rows: list[dict[str, object]] = []
        for family in admission.FAMILY_QUOTAS:
            for index in range(13):
                rows.append(candidate(family, index))
        rows.extend(candidate("parser/mixed integration", index + 100) for index in range(20))

        balanced = admission.balance_candidate_pool(rows, 40)

        self.assertEqual(len(balanced), 40)
        counts = Counter(row["family"] for row in balanced)
        for family in admission.FAMILY_QUOTAS:
            self.assertGreaterEqual(counts[family], admission.FAMILY_CANDIDATE_MINIMUMS[family])

    def test_admission_decision_accepts_only_noop_fail_and_reference_pass(self) -> None:
        """Admission requires both oracle-smoke sides to prove the task is executable."""
        accepted, _ = admission.admission_decision({"status": "failed"}, {"oracle_status": "reference_passed"})
        self.assertEqual(accepted, "accepted")

        rejected, reason = admission.admission_decision({"status": "passed_unexpected"}, {"oracle_status": "reference_passed"})
        self.assertEqual(rejected, "rejected")
        self.assertIn("noop=passed_unexpected", reason)

    def test_noop_smoke_status_rejects_collection_errors_and_timeouts(self) -> None:
        """No-op admission requires a real failing verifier, not collection errors."""
        self.assertEqual(admission.noop_smoke_status(1, False), "failed")
        self.assertEqual(admission.noop_smoke_status(4, False), "blocked_pytest_collection")
        self.assertEqual(admission.noop_smoke_status(5, False), "blocked_pytest_collection")
        self.assertEqual(admission.noop_smoke_status(124, True), "blocked_timeout")

    def test_hidden_verifier_digest_changes_with_hidden_file_content(self) -> None:
        """The hidden-verifier digest commits to both the command and hidden test content."""
        command = ".venv/bin/python -m pytest -q tests/test_core.py::test_case"
        with mock.patch.object(admission, "git_show_file", return_value="def test_case(): pass\n"):
            first = admission.hidden_verifier_digest(self.root, "target", command)
        with mock.patch.object(admission, "git_show_file", return_value="def test_case(): assert False\n"):
            second = admission.hidden_verifier_digest(self.root, "target", command)

        self.assertNotEqual(first, second)

    def test_split_manifest_payload_includes_freeze_controls(self) -> None:
        """Primary and reserve manifests carry the seed, ACUT order, scoring map, and infra policy."""
        payload = admission.split_manifest_payload([], status="admitted_frozen")

        freeze = payload["freeze"]
        self.assertEqual(freeze["denominator_status"], "frozen_primary_not_run")
        self.assertEqual(freeze["deterministic_run_seed"], admission.W3_DETERMINISTIC_RUN_SEED)
        self.assertEqual(freeze["acut_run_order"], admission.W3_ACUT_RUN_ORDER)
        self.assertIn("verified_pass", freeze["status_mapping"])
        self.assertFalse(freeze["infra_rerun_policy"]["acut_specific_retry_allowed"])

    def test_install_workspace_uses_configured_venv_python(self) -> None:
        """Admission smoke creates Click workspaces with the configured supported Python."""
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> dict[str, object]:
            calls.append(command)
            return {"exit_code": 0, "timed_out": False}

        with mock.patch.object(admission, "run_artifact_command", side_effect=fake_run):
            result = admission.install_workspace(self.root, self.root / "artifacts", 10, "/custom/python3.12")

        self.assertEqual(result["status"], "installed")
        self.assertEqual(calls[0], ["/custom/python3.12", "-m", "venv", ".venv"])
        self.assertEqual(calls[1][0], ".venv/bin/python")
        self.assertEqual(calls[2][0], ".venv/bin/python")

    def test_candidate_manifest_records_admission_sheet_digests_and_changed_files(self) -> None:
        """Candidate-pool rows expose every admission-sheet digest needed for audit."""
        row = candidate("parser/mixed integration", 1)
        sheet = {
            "candidate_id": row["candidate_id"],
            "admission_decision": "accepted",
            "hidden_verifier_digest": "hidden-digest",
        }

        payload = admission.candidate_manifest_payload([row], [sheet])

        self.assertEqual(payload["candidate_count"], 1)
        manifest_row = payload["rows"][0]
        self.assertEqual(manifest_row["changed_file_anchor_set"], row["changed_files"])
        self.assertEqual(manifest_row["hidden_verifier_digest"], "hidden-digest")
        self.assertEqual(manifest_row["admission_decision"], "accepted")

    def test_run_artifact_command_writes_failure_diagnostics(self) -> None:
        """Failed subprocesses still emit machine-readable command diagnostics."""
        artifact_dir = self.root / "artifacts"
        summary = admission.run_artifact_command(
            [
                sys.executable,
                "-c",
                "import sys; print('stdout marker'); print('stderr marker', file=sys.stderr); sys.exit(7)",
            ],
            artifact_dir=artifact_dir,
            name="failing_command",
            cwd=None,
            timeout=10,
        )

        self.assertEqual(summary["exit_code"], 7)
        self.assertEqual((artifact_dir / "failing_command.stdout.txt").read_text(encoding="utf-8").strip(), "stdout marker")
        self.assertEqual((artifact_dir / "failing_command.stderr.txt").read_text(encoding="utf-8").strip(), "stderr marker")
        diagnostic = json.loads((artifact_dir / "failing_command.json").read_text(encoding="utf-8"))
        self.assertEqual(diagnostic["name"], "failing_command")
        self.assertEqual(diagnostic["exit_code"], 7)
        self.assertFalse(diagnostic["timed_out"])

    def test_run_artifact_command_writes_timeout_diagnostics(self) -> None:
        """Timed-out subprocesses produce text artifacts even when captured output is bytes."""
        artifact_dir = self.root / "artifacts"
        summary = admission.run_artifact_command(
            [
                sys.executable,
                "-c",
                "import time; print('before sleep', flush=True); time.sleep(5)",
            ],
            artifact_dir=artifact_dir,
            name="timed_out_command",
            cwd=None,
            timeout=0.1,
        )

        self.assertEqual(summary["exit_code"], 124)
        self.assertTrue(summary["timed_out"])
        self.assertIn("before sleep", (artifact_dir / "timed_out_command.stdout.txt").read_text(encoding="utf-8"))
        diagnostic = json.loads((artifact_dir / "timed_out_command.json").read_text(encoding="utf-8"))
        self.assertTrue(diagnostic["timed_out"])


if __name__ == "__main__":
    unittest.main()
