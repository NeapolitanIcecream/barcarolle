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
            self.assertEqual(payload["task_split"], "rbench")

    def test_main_can_probe_rwork_manifest(self) -> None:
        """Gate 0 admission checks are split-aware for held-out Click RWork tasks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preflight.json"
            tasks = [
                {"task_id": "click__rwork__001"},
                {"task_id": "click__rwork__002"},
                {"task_id": "click__rwork__003"},
            ]
            task_by_id = {task["task_id"]: task for task in tasks}
            with mock.patch.object(preflight.batch, "task_split_manifest_path", return_value=Path("rwork.yaml")), mock.patch.object(
                preflight,
                "load_manifest",
                return_value={"split": "RWork", "tasks": tasks},
            ), mock.patch.object(preflight.batch, "task_by_id", return_value=task_by_id), mock.patch.object(
                preflight.batch,
                "task_manifest_path",
                return_value=Path(__file__),
            ), mock.patch.object(
                preflight,
                "task_probe",
                side_effect=lambda task, **kwargs: {"task_id": task["task_id"], "status": "passed"},
            ), mock.patch.object(preflight, "iso_now", side_effect=["start-time", "finish-time"]):
                code = preflight.main(
                    [
                        "--task-split",
                        "rwork",
                        "--tasks",
                        "click__rwork__001",
                        "click__rwork__002",
                        "click__rwork__003",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(code, 0)
            payload = preflight.json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["task_split"], "rwork")

    def test_main_rejects_task_with_wrong_split_even_when_manifest_contains_id(self) -> None:
        """Regression: Gate 0 must not probe RBench task packs under an RWork summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preflight.json"
            manifest_path = Path(temp_dir) / "mixed_manifest.json"
            manifest_path.write_text(
                preflight.json.dumps(
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
            run_calls: list[str] = []

            def fake_probe(task, **kwargs):
                run_calls.append(task["task_id"])
                return {"task_id": task["task_id"], "status": "passed"}

            with mock.patch.object(preflight.batch, "task_manifest_path", return_value=Path(__file__)), mock.patch.object(
                preflight,
                "task_probe",
                side_effect=fake_probe,
            ):
                code = preflight.main(
                    [
                        "--task-split",
                        "rwork",
                        "--task-split-manifest",
                        str(manifest_path),
                        "--tasks",
                        "click__rbench__001",
                        "--output",
                        str(output),
                    ]
                )

            self.assertNotEqual(code, 0)
            self.assertEqual(run_calls, [])
            self.assertFalse(output.exists())

    def test_task_probe_records_clean_patch_replay_gate(self) -> None:
        """Reference probes double as clean replay evidence in the admission artifact."""
        task = {"task_id": "click__rbench__001", "source": {}}

        with mock.patch.object(preflight, "reference_patch_for_task", return_value="reference"), mock.patch.object(
            preflight,
            "known_bad_patch_for_task",
            return_value="known-bad",
        ), mock.patch.object(
            preflight,
            "write_json",
        ), mock.patch.object(
            preflight,
            "run_noop_probe",
            return_value={"status": "failed", "verification": {"duration_seconds": 0.1}},
        ), mock.patch.object(
            preflight,
            "verify_patch_text",
            side_effect=[
                {"status": "passed", "workspace": "/tmp/ref1", "verification": {"exit_code": 0, "duration_seconds": 0.2}},
                {"status": "passed", "workspace": "/tmp/ref2", "verification": {"exit_code": 0, "duration_seconds": 0.3}},
                {"status": "failed", "workspace": "/tmp/bad", "verification": {"exit_code": 1, "duration_seconds": 0.2}},
            ],
        ), mock.patch.object(
            preflight,
            "verifier_timeout_seconds",
            return_value=60,
        ), mock.patch.object(
            preflight,
            "leakage_findings",
            return_value={"unsafe": False, "reason_counts": {}, "ignored_benign_urls": []},
        ):
            result = preflight.task_probe(
                task,
                run_prefix="unit",
                flakiness_runs=2,
                install_timeout_seconds=1,
            )

        self.assertTrue(result["gates"]["clean_patch_replay"])
        self.assertTrue(result["clean_patch_replay"]["separate_workspaces"])

    def test_reference_failure_is_classified_as_task_pack_or_verifier_defect(self) -> None:
        """Admission artifacts label reference/verifier mismatches instead of hiding them."""
        defects = preflight.admission_defect_classifications(
            gates={
                "no_op_probe": True,
                "reference_probe": False,
                "known_bad_probe": True,
                "flakiness_probe": False,
                "verifier_runtime_p95_lt_timeout": True,
                "oracle_log_leakage": True,
                "clean_patch_replay": False,
            },
            noop={"status": "failed"},
            reference_runs=[{"status": "failed"}, {"status": "failed"}],
            known_bad={"status": "failed"},
            leakage={"unsafe": False},
        )

        classes = {defect["defect_class"] for defect in defects}
        self.assertIn("reference_patch_failed_verifier", classes)
        self.assertIn("clean_reference_replay_failed", classes)

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
