#!/usr/bin/env python3
"""Executable specs for Phase 2 external E ACUT runner artifacts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import external_calibrated_e_runner as runner


class ExternalCalibratedERunnerTests(unittest.TestCase):
    def test_select_run_cells_filters_frozen_matrix_with_single_attempt_limit(self) -> None:
        matrix = {
            "phase2_e_cells": [
                {
                    "run_id": "run-a0-1",
                    "phase": "e",
                    "acut_slot": "A0",
                    "acut_id": "a0",
                    "task_id": "sympy__sympy-1",
                    "task_ordinal": 1,
                    "attempt": 1,
                    "status": "not_started",
                },
                {
                    "run_id": "run-a1-1",
                    "phase": "e",
                    "acut_slot": "A1",
                    "acut_id": "a1",
                    "task_id": "sympy__sympy-1",
                    "task_ordinal": 1,
                    "attempt": 1,
                    "status": "not_started",
                },
                {
                    "run_id": "run-a0-2",
                    "phase": "e",
                    "acut_slot": "A0",
                    "acut_id": "a0",
                    "task_id": "sympy__sympy-2",
                    "task_ordinal": 2,
                    "attempt": 1,
                    "status": "not_started",
                },
            ]
        }

        selected = runner.select_run_cells(matrix, acut_slots=["A0"], limit=1)

        self.assertEqual([cell["run_id"] for cell in selected], ["run-a0-1"])
        self.assertEqual(selected[0]["attempt"], 1)

    def test_materialize_private_task_pack_redacts_public_summary(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            row = {
                "repo": "sympy/sympy",
                "instance_id": "sympy__sympy-1",
                "base_commit": "abc123basecommit",
                "problem_statement": "Raw E problem statement that must stay private",
                "patch": "diff --git a/gold b/gold",
                "test_patch": "diff --git a/test b/test",
            }
            frozen_task = {
                "instance_id": "sympy__sympy-1",
                "ordinal": 1,
                "family_if_available": "core/mixed",
                "smoke_status": "gold_resolved",
            }

            materialized = runner.materialize_private_task_pack(
                row,
                frozen_task,
                private_root=root / "private",
                dataset_name="SWE-bench/SWE-bench_Verified",
                split="test",
            )

            manifest = json.loads(materialized["task_manifest_path"].read_text(encoding="utf-8"))
            statement = (materialized["task_pack_dir"] / "public/statement.md").read_text(encoding="utf-8")
            public_repr = repr(materialized["public_record"])

        self.assertEqual(manifest["source"]["base_commit"], "abc123basecommit")
        self.assertNotIn("patch", manifest)
        self.assertNotIn("test_patch", manifest)
        self.assertIn("Raw E problem statement", statement)
        self.assertNotIn("Raw E problem statement", public_repr)
        self.assertNotIn("abc123basecommit", public_repr)
        self.assertNotIn("diff --git", public_repr)
        self.assertFalse(materialized["public_record"]["raw_problem_statement_emitted"])
        self.assertFalse(materialized["public_record"]["raw_base_commit_emitted"])

    def test_write_predictions_jsonl_keeps_model_patch_out_of_public_summary(self) -> None:
        with TemporaryDirectory() as temp:
            predictions_path = Path(temp) / "private/predictions/a0.jsonl"
            summary = runner.write_predictions_jsonl(
                [
                    {
                        "instance_id": "sympy__sympy-1",
                        "model_name_or_path": "a0",
                        "model_patch": "diff --git a/secret b/secret\n+SECRET_PATCH_CONTENT\n",
                    }
                ],
                predictions_path,
            )
            line = json.loads(predictions_path.read_text(encoding="utf-8").strip())

        self.assertEqual(set(line), {"instance_id", "model_name_or_path", "model_patch"})
        self.assertIn("SECRET_PATCH_CONTENT", line["model_patch"])
        self.assertNotIn("SECRET_PATCH_CONTENT", repr(summary))
        self.assertFalse(summary["records"][0]["model_patch_recorded_publicly"])

    def test_build_harness_command_targets_official_swebench_prediction_file(self) -> None:
        command = runner.build_harness_command(
            python_executable="/venv/bin/python",
            dataset_name="SWE-bench/SWE-bench_Verified",
            split="test",
            predictions_path=Path("/private/predictions/a0.jsonl"),
            instance_ids=["sympy__sympy-1", "sympy__sympy-2"],
            run_id="phase2-a0",
            max_workers=1,
            timeout=900,
            cache_level="base",
        )

        self.assertIn("--predictions_path", command)
        self.assertIn("/private/predictions/a0.jsonl", command)
        self.assertIn("--instance_ids", command)
        self.assertIn("sympy__sympy-2", command)
        self.assertNotIn("model_patch", " ".join(command))

    def test_score_summary_maps_official_report_to_acut_table(self) -> None:
        predictions = [
            {"run_id": "run-a0-1", "acut_id": "a0", "acut_slot": "A0", "instance_id": "sympy__sympy-1"},
            {"run_id": "run-a0-2", "acut_id": "a0", "acut_slot": "A0", "instance_id": "sympy__sympy-2"},
            {"run_id": "run-a1-1", "acut_id": "a1", "acut_slot": "A1", "instance_id": "sympy__sympy-1"},
        ]
        report = {
            "completed_ids": ["sympy__sympy-1", "sympy__sympy-2"],
            "resolved_ids": ["sympy__sympy-1"],
            "unresolved_ids": ["sympy__sympy-2"],
            "empty_patch_ids": [],
            "error_ids": [],
        }

        summary = runner.score_summary_from_report(
            report,
            predictions,
            run_id="phase2-a0",
            acut_id="a0",
            acut_slot="A0",
        )

        self.assertEqual(summary["resolved_instances"], 1)
        self.assertEqual(summary["score_table"][0]["score_numerator"], 1)
        self.assertEqual(summary["score_table"][0]["score_denominator"], 2)
        self.assertEqual(summary["cells"][0]["score"], 1)
        self.assertEqual(summary["cells"][1]["score"], 0)

    def test_render_report_describes_prepare_task_packs_without_none_placeholders(self) -> None:
        report = runner.render_report(
            {
                "protocol_id": "external-calibrated-repo-benchmark-v1",
                "phase": "prepare",
                "mode": "dry-run",
                "status": "prepared",
                "generated_at": "2026-05-16T00:00:00Z",
                "selected_cell_count": 6,
                "model_calls_made": 0,
                "blockers": [],
                "results": [
                    {
                        "instance_id": "sympy__sympy-1",
                        "task_ordinal": 1,
                        "task_family": "core/mixed",
                        "problem_statement_sha256": "abc123",
                    }
                ],
            }
        )

        self.assertIn("task pack", report)
        self.assertIn("sympy__sympy-1", report)
        self.assertNotIn("`None` `None`", report)


if __name__ == "__main__":
    unittest.main()
