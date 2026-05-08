#!/usr/bin/env python3
"""Executable specs for Codex NFL Gate 0 preflight probes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import codex_nfl_gate0_preflight as preflight


class CodexNflGate0PreflightTests(unittest.TestCase):
    def test_p95_uses_nearest_rank(self) -> None:
        """Runtime p95 is deterministic for small probe samples."""
        self.assertEqual(preflight.p95([0.1, 0.2, 0.3]), 0.3)
        self.assertEqual(preflight.p95([0.3, 0.1, 0.2, 0.4]), 0.4)

    def test_leakage_findings_reports_unsafe_verifier_output(self) -> None:
        """Gate 0 emits a machine-readable leakage signal when verifier logs contain unsafe text."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "verifier.stderr.txt"
            path.write_text("provider mentioned https://example.invalid/token\n", encoding="utf-8")

            findings = preflight.leakage_findings([str(path)])

        self.assertTrue(findings["unsafe"])
        self.assertEqual(findings["reason_counts"], {"full_url": 1})

    def test_leakage_findings_ignores_pytest_docs_url(self) -> None:
        """Pytest's warning help URL is not oracle leakage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "verifier.stdout.txt"
            path.write_text("Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n", encoding="utf-8")

            findings = preflight.leakage_findings([str(path)])

        self.assertFalse(findings["unsafe"])
        self.assertEqual(findings["reason_counts"], {})
        self.assertEqual(
            findings["ignored_benign_urls"],
            ["https://docs.pytest.org/en/stable/how-to/capture-warnings.html"],
        )

    def test_reference_patch_requires_changed_files(self) -> None:
        """A task without changed files cannot satisfy the reference probe."""
        with self.assertRaises(preflight.ToolError):
            preflight.reference_patch_for_task(
                {
                    "task_id": "click__rbench__unit",
                    "source": {"base_commit": "base", "target_commit": "target"},
                    "source_compare": {"changed_files": []},
                }
            )

    def test_verify_patch_text_refuses_existing_probe_artifacts(self) -> None:
        """Regression: repeated probe run IDs must not reuse stale normalized results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_dir = root / "raw" / "unit_prefix__click__rbench__001__reference_1"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "normalized_result.json").write_text('{"status":"passed"}\n', encoding="utf-8")

            with mock.patch.object(preflight.batch, "RAW_ROOT", root / "raw"), mock.patch.object(
                preflight.batch,
                "prepare_workspace",
                return_value=(root / "workspace", {}),
            ), mock.patch.object(preflight.batch, "install_workspace", return_value={}), mock.patch.object(
                preflight.batch,
                "verify_patch",
                return_value=(0, {"status": "passed"}),
            ):
                with self.assertRaises(preflight.ToolError):
                    preflight.verify_patch_text(
                        task_id="click__rbench__001",
                        run_prefix="unit_prefix",
                        probe_name="reference_1",
                        patch_text="diff --git a/module.py b/module.py\n",
                        install_timeout_seconds=1,
                    )

    def test_main_records_started_at(self) -> None:
        """Gate 0 payloads include timing provenance for audit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preflight.json"
            tasks = [
                {"task_id": "click__rbench__001"},
                {"task_id": "click__rbench__002"},
                {"task_id": "click__rbench__003"},
            ]
            task_by_id = {task["task_id"]: task for task in tasks}
            with mock.patch.object(preflight, "load_manifest", return_value={"tasks": tasks}), mock.patch.object(
                preflight.batch,
                "task_by_id",
                return_value=task_by_id,
            ), mock.patch.object(preflight.batch, "task_manifest_path", return_value=Path(__file__)), mock.patch.object(
                preflight,
                "task_probe",
                side_effect=lambda task, **kwargs: {"task_id": task["task_id"], "status": "passed"},
            ), mock.patch.object(preflight, "iso_now", side_effect=["start-time", "finish-time"]):
                code = preflight.main(
                    [
                        "--tasks",
                        "click__rbench__001",
                        "click__rbench__002",
                        "click__rbench__003",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(code, 0)
            payload = preflight.json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["started_at"], "start-time")
            self.assertEqual(payload["finished_at"], "finish-time")

    def test_main_rejects_duplicate_task_ids_for_count_gate(self) -> None:
        """Regression: repeated task IDs must not satisfy the three-task Gate 0 count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preflight.json"
            task = {"task_id": "click__rbench__001"}
            with mock.patch.object(preflight, "load_manifest", return_value={"tasks": [task]}), mock.patch.object(
                preflight.batch,
                "task_by_id",
                return_value={"click__rbench__001": task},
            ), mock.patch.object(preflight.batch, "task_manifest_path", return_value=Path(__file__)), mock.patch.object(
                preflight,
                "task_probe",
                return_value={"task_id": "click__rbench__001", "status": "passed"},
            ):
                code = preflight.main(
                    [
                        "--tasks",
                        "click__rbench__001",
                        "click__rbench__001",
                        "click__rbench__001",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(code, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
