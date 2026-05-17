#!/usr/bin/env python3
"""Executable specs for external E task freeze artifacts."""

from __future__ import annotations

import unittest

import external_calibrated_e_freeze as freeze


class ExternalCalibratedEFreezeTests(unittest.TestCase):
    def test_freeze_decision_accepts_target_sized_passing_smoke(self) -> None:
        decision = freeze.freeze_decision(
            {
                "pass": True,
                "total_instances_requested": 48,
                "completed_instances": 48,
                "resolved_instances": 48,
                "error_instances": 0,
            },
            target_size=48,
            min_size=30,
        )

        self.assertEqual(decision["status"], "frozen_target_size")
        self.assertTrue(decision["freeze_allowed"])

    def test_freeze_decision_blocks_below_minimum_smoke(self) -> None:
        decision = freeze.freeze_decision(
            {
                "pass": True,
                "total_instances_requested": 5,
                "completed_instances": 5,
                "resolved_instances": 5,
                "error_instances": 0,
            },
            target_size=48,
            min_size=30,
        )

        self.assertEqual(decision["status"], "not_frozen")
        self.assertIn("resolved_external_task_count_below_min_size", decision["blockers"])

    def test_task_table_redacts_problem_statement_patch_and_base_commit(self) -> None:
        rows = [
            {
                "repo": "sympy/sympy",
                "instance_id": "sympy__sympy-1",
                "base_commit": "a" * 40,
                "problem_statement": "Secret E statement",
                "patch": "diff --git a/sympy/core/add.py b/sympy/core/add.py",
                "test_patch": "diff --git a/sympy/core/tests/test_add.py b/sympy/core/tests/test_add.py",
            }
        ]

        table = freeze.e_task_table(
            rows,
            {
                "benchmark_source": "SWE-bench/SWE-bench_Verified",
                "split": "test",
                "instance_ids": ["sympy__sympy-1"],
                "completed_ids": ["sympy__sympy-1"],
                "resolved_ids": ["sympy__sympy-1"],
            },
            repo_id="sympy/sympy",
        )
        rendered = repr(table)

        self.assertEqual(table[0]["smoke_status"], "gold_resolved")
        self.assertNotIn("Secret E statement", rendered)
        self.assertNotIn("diff --git", rendered)
        self.assertNotIn("a" * 40, rendered)
        self.assertRegex(table[0]["base_commit_digest"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
