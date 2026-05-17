#!/usr/bin/env python3
"""Executable specs for external-calibrated Phase 0 admission."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import external_calibrated_repository_admission as admission


class ExternalCalibratedRepositoryAdmissionTests(unittest.TestCase):
    def test_patch_paths_extracts_diff_and_new_file_headers(self) -> None:
        patch = """diff --git a/sympy/core/add.py b/sympy/core/add.py
--- a/sympy/core/add.py
+++ b/sympy/core/add.py
@@
diff --git a/sympy/core/tests/test_add.py b/sympy/core/tests/test_add.py
--- a/sympy/core/tests/test_add.py
+++ b/sympy/core/tests/test_add.py
"""

        self.assertEqual(
            admission.patch_paths(patch),
            ["sympy/core/add.py", "sympy/core/tests/test_add.py"],
        )

    def test_external_task_summary_redacts_raw_statement_patch_and_commit(self) -> None:
        row = {
            "instance_id": "sympy__sympy-123",
            "base_commit": "a" * 40,
            "problem_statement": "Secret statement text",
            "patch": "diff --git a/sympy/core/add.py b/sympy/core/add.py",
            "test_patch": "diff --git a/sympy/core/tests/test_add.py b/sympy/core/tests/test_add.py",
        }

        summary = admission.redacted_external_task(row, "sympy/sympy")
        rendered = repr(summary)

        self.assertRegex(summary["instance_id_digest"], r"^[0-9a-f]{64}$")
        self.assertNotIn("sympy__sympy-123", rendered)
        self.assertNotIn("Secret statement text", rendered)
        self.assertNotIn("a" * 40, rendered)
        self.assertNotIn("diff --git", rendered)

    def test_sympy_family_classifier_routes_expected_domains(self) -> None:
        matrix_row = {
            "instance_id": "sympy__sympy-1",
            "problem_statement": "Matrix nullspace regression",
            "patch": "diff --git a/sympy/matrices/dense.py b/sympy/matrices/dense.py",
            "test_patch": "",
        }
        assumptions_row = {
            "instance_id": "sympy__sympy-2",
            "problem_statement": "assumptions predicate refine bug",
            "patch": "",
            "test_patch": "",
        }

        self.assertEqual(admission.external_family("sympy/sympy", matrix_row), "matrices/linear algebra")
        self.assertEqual(admission.external_family("sympy/sympy", assumptions_row), "assumptions/predicates")

    def test_candidate_surface_distinguishes_sympy_source_and_tests(self) -> None:
        self.assertEqual(
            admission.candidate_surface("sympy", ["sympy/core/add.py", "sympy/core/tests/test_add.py"]),
            "source_and_tests",
        )
        self.assertEqual(admission.candidate_surface("sympy", ["sympy/core/add.py"]), "source_without_tests")
        self.assertEqual(admission.candidate_surface("sympy", ["sympy/core/tests/test_add.py"]), "tests_without_source")

    def test_recommendation_prefers_protocol_priority_metadata_ready_repo(self) -> None:
        repos = [
            {
                "repo_slug": "django",
                "metadata_ready_for_infra_smoke": True,
                "external_task_count_verified": 100,
                "barcarolle_candidate_task_count": 500,
            },
            {
                "repo_slug": "sympy",
                "metadata_ready_for_infra_smoke": True,
                "external_task_count_verified": 50,
                "barcarolle_candidate_task_count": 80,
            },
        ]

        recommendation = admission.build_recommendation(repos, smoke_summary=None)

        self.assertEqual(recommendation["recommended_next_repo_for_infra_smoke"], "sympy")
        self.assertFalse(recommendation["primary_repo_can_be_declared"])

    def test_recommendation_reports_gold_smoke_sample_size_when_available(self) -> None:
        repos = [
            {
                "repo_slug": "sympy",
                "metadata_ready_for_infra_smoke": True,
                "external_task_count_verified": 75,
                "barcarolle_candidate_task_count": 828,
            }
        ]

        recommendation = admission.build_recommendation(
            repos,
            smoke_summary={"pass": True, "total_instances_requested": 5},
        )

        self.assertTrue(
            any("covers 5 gold instance(s) only" in reason for reason in recommendation["why_not_final_admission"])
        )

    def test_recommendation_records_usable_external_count_after_denominator_smoke(self) -> None:
        repos = [
            {
                "repo_slug": "sympy",
                "metadata_ready_for_infra_smoke": True,
                "external_task_count_verified": 75,
                "external_task_count_after_infra_smoke": 48,
                "barcarolle_candidate_task_count": 828,
            }
        ]

        recommendation = admission.build_recommendation(
            repos,
            smoke_summary={"pass": True, "total_instances_requested": 48},
        )

        self.assertIn("external_eval_smoke established 48 usable E task(s)", recommendation["why_not_final_admission"])
        self.assertEqual(recommendation["phase0_status"], "external_infra_smoke_completed_b_admission_pending")
        self.assertEqual(recommendation["recommended_primary_repo_for_b_generation"], "sympy")
        self.assertNotIn(
            "external_task_count_after_infra_smoke is not measured for the target E denominator",
            recommendation["why_not_final_admission"],
        )

    def test_recommendation_marks_frozen_primary_with_weak_candidate_noop_gate(self) -> None:
        repos = [
            {
                "repo_slug": "sympy",
                "metadata_ready_for_infra_smoke": True,
                "external_task_count_verified": 75,
                "external_task_count_after_infra_smoke": 48,
                "barcarolle_candidate_task_count": 828,
                "barcarolle_primary_b_task_count": 20,
                "barcarolle_reference_smoke_pass_rate": 0.9,
                "barcarolle_noop_fail_rate": 0.75,
            }
        ]

        recommendation = admission.build_recommendation(
            repos,
            smoke_summary={"pass": True, "total_instances_requested": 48},
        )

        self.assertEqual(
            recommendation["phase0_status"],
            "external_and_b_primary_frozen_candidate_noop_gate_weak",
        )
        self.assertFalse(recommendation["primary_repo_can_be_declared"])
        self.assertIn(
            "barcarolle_noop_fail_rate is below 90% for evaluated candidates",
            recommendation["why_not_final_admission"],
        )

    def test_external_summaries_can_be_reused_from_cache(self) -> None:
        with TemporaryDirectory() as temp:
            cache = Path(temp) / "admission.json"
            cache.write_text(
                """
{
  "external_dataset_sources": {
    "swebench_verified": {"dataset": "SWE-bench/SWE-bench_Verified"},
    "swebench_full": {"dataset": "SWE-bench/SWE-bench"}
  }
}
""".strip(),
                encoding="utf-8",
            )

            summaries = admission.external_summaries_from_cache(cache)

        self.assertEqual(summaries["swebench_verified"]["dataset"], "SWE-bench/SWE-bench_Verified")


if __name__ == "__main__":
    unittest.main()
