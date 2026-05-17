#!/usr/bin/env python3
"""Executable specs for the redacted SWE-bench smoke runner."""

from __future__ import annotations

import argparse
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import external_calibrated_swebench_smoke as smoke


class ExternalCalibratedSwebenchSmokeTests(unittest.TestCase):
    def test_select_instance_ids_is_deterministic_and_repo_scoped(self) -> None:
        rows = [
            {"repo": "sympy/sympy", "instance_id": "sympy__sympy-1"},
            {"repo": "django/django", "instance_id": "django__django-1"},
            {"repo": "sympy/sympy", "instance_id": "sympy__sympy-2"},
            {"repo": "sympy/sympy", "instance_id": "sympy__sympy-3"},
        ]
        expected = sorted(
            ["sympy__sympy-1", "sympy__sympy-2", "sympy__sympy-3"],
            key=lambda instance_id: (smoke.selection_key(salt="unit", instance_id=instance_id), instance_id),
        )[:2]

        selected = smoke.select_instance_ids(
            rows,
            repo_id="sympy/sympy",
            sample_size=2,
            explicit_instance_ids=None,
            salt="unit",
        )

        self.assertEqual(selected, expected)

    def test_raw_artifact_inventory_counts_sensitive_files_without_content(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "logs/run_evaluation/run/gold/task").mkdir(parents=True)
            (root / "logs/run_evaluation/run/gold/task/patch.diff").write_text("diff --git secret\n", encoding="utf-8")
            (root / "logs/run_evaluation/run/gold/task/eval.sh").write_text("secret test command\n", encoding="utf-8")
            (root / "notes.txt").write_text("not sensitive\n", encoding="utf-8")

            inventory = smoke.raw_artifact_inventory(root)

        rendered = repr(inventory)
        self.assertEqual(inventory["file_count"], 3)
        self.assertEqual(inventory["sensitive_file_count"], 2)
        self.assertNotIn("diff --git", rendered)
        self.assertNotIn("secret test command", rendered)

    def test_python_executable_resolves_repo_relative_paths(self) -> None:
        resolved = smoke.python_executable("experiments/core_narrative/cache/venv/bin/python")

        self.assertTrue(resolved.startswith(str(smoke.REPO_ROOT)))
        self.assertTrue(resolved.endswith("experiments/core_narrative/cache/venv/bin/python"))

    def test_report_id_list_ignores_non_string_entries(self) -> None:
        self.assertEqual(smoke.report_id_list({"resolved_ids": ["a", 3, "b"]}, "resolved_ids"), ["a", "b"])

    def test_summary_redacts_harness_output_and_records_cleanup(self) -> None:
        args = argparse.Namespace(
            dataset_name="SWE-bench/SWE-bench_Verified",
            split="test",
            selection_salt="unit",
            sample_size=1,
            instance_id=None,
            run_id="unit-smoke",
            python="/venv/bin/python",
            max_workers=1,
            timeout=900,
            cache_level="base",
            retain_raw=False,
        )
        completed = subprocess.CompletedProcess(
            args=["python", "-m", "swebench.harness.run_evaluation"],
            returncode=0,
            stdout="SECRET PATCH TEXT\n",
            stderr="SECRET TEST TEXT\n",
        )

        with mock.patch.object(smoke.admission, "dataset_api_metadata", return_value={"sha": "unit"}):
            summary = smoke.build_summary(
                args,
                repo_id="sympy/sympy",
                rows=[{"repo": "sympy/sympy", "instance_id": "sympy__sympy-1"}],
                instance_ids=["sympy__sympy-1"],
                report={
                    "completed_instances": 1,
                    "resolved_instances": 1,
                    "unresolved_instances": 0,
                    "empty_patch_instances": 0,
                    "error_instances": 0,
                    "completed_ids": ["sympy__sympy-1"],
                    "resolved_ids": ["sympy__sympy-1"],
                },
                completed=completed,
                duration_seconds=1.25,
                timeout_error=None,
                inventory={"file_count": 4, "total_bytes": 100, "sensitive_file_count": 3, "sensitive_path_digests": ["abc"]},
                raw_deleted=True,
                raw_dir=Path("raw"),
            )

        rendered = repr(summary)
        self.assertTrue(summary["pass"])
        self.assertEqual(summary["resolved_ids"], ["sympy__sympy-1"])
        self.assertTrue(summary["raw_dir_deleted"])
        self.assertNotIn("SECRET PATCH TEXT", rendered)
        self.assertNotIn("SECRET TEST TEXT", rendered)
        self.assertIn("stdout", summary["harness"])
        self.assertIn("sha256", summary["harness"]["stdout"])


if __name__ == "__main__":
    unittest.main()
