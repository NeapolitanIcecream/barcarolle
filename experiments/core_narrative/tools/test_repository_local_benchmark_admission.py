#!/usr/bin/env python3
"""Executable specs for the repository-local benchmark admission scan."""

from __future__ import annotations

import unittest

import repository_local_benchmark_admission as admission


class RepositoryLocalBenchmarkAdmissionTests(unittest.TestCase):
    def test_window_for_date_uses_frozen_0514_boundaries(self) -> None:
        """C/R/W* split assignment follows the 2026-05-14 protocol windows."""
        self.assertEqual(admission.window_for_date("2025-11-13T23:59:59+00:00"), "C")
        self.assertEqual(admission.window_for_date("2025-11-14T00:00:00+00:00"), "R")
        self.assertEqual(admission.window_for_date("2026-02-13T23:59:59+00:00"), "R")
        self.assertEqual(admission.window_for_date("2026-02-14T00:00:00+00:00"), "W_star")
        self.assertEqual(admission.window_for_date("2026-05-14T23:59:59+00:00"), "W_star")
        self.assertEqual(admission.window_for_date("2026-05-15T00:00:00+00:00"), "future")

    def test_candidate_surface_requires_source_and_tests(self) -> None:
        """Repository admission only counts commits with source and test changes as task candidates."""
        files = ["src/click/core.py", "tests/test_options.py"]
        self.assertEqual(admission.candidate_surface("click", files), "source_and_tests")

        self.assertEqual(admission.candidate_surface("click", ["docs/options.md"]), "docs_or_meta_only")
        self.assertEqual(admission.candidate_surface("click", ["src/click/core.py"]), "source_without_tests")
        self.assertEqual(admission.candidate_surface("click", ["tests/test_options.py"]), "tests_without_source")

    def test_task_design_candidate_can_use_source_without_tests_for_golden_oracle(self) -> None:
        """Source-only commits can seed task design, but are not direct oracle candidates."""
        self.assertTrue(admission.task_design_surface("source_and_tests"))
        self.assertTrue(admission.task_design_surface("source_without_tests"))
        self.assertFalse(admission.task_design_surface("tests_without_source"))
        self.assertFalse(admission.task_design_surface("docs_or_meta_only"))

    def test_anchor_digest_does_not_expose_commit_sha(self) -> None:
        """Public admission diagnostics use stable digests rather than raw source commits."""
        digest = admission.anchor_digest("click", "a" * 40)

        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertNotIn("a" * 40, digest)

    def test_family_classification_routes_repo_specific_surfaces(self) -> None:
        """Family labels are repository-specific enough for diversity checks."""
        self.assertEqual(
            admission.classify_family("click", "Fix CliRunner stderr isolation", ["src/click/testing.py", "tests/test_testing.py"]),
            "CliRunner/testing/input-output isolation",
        )
        self.assertEqual(
            admission.classify_family("rich", "Fix progress refresh", ["rich/progress.py", "tests/test_progress.py"]),
            "progress/live/status rendering",
        )
        self.assertEqual(
            admission.classify_family("black", "Preserve fmt skip", ["src/black/linegen.py", "tests/test_format.py"]),
            "formatting behavior",
        )

    def test_recommendation_prefers_click_primary_and_ready_replication_repo(self) -> None:
        """Click remains primary while the strongest ready non-Click repo becomes replication."""
        repos = [
            {
                "repo_slug": "click",
                "admission_ready": True,
                "windows": {"W_star": {"task_design_candidate_count": 24, "task_design_family_count": 5}},
                "extended_R": {"task_design_candidate_count": 30},
            },
            {
                "repo_slug": "rich",
                "admission_ready": True,
                "windows": {"W_star": {"task_design_candidate_count": 28, "task_design_family_count": 5}},
                "extended_R": {"task_design_candidate_count": 35},
            },
            {
                "repo_slug": "black",
                "admission_ready": True,
                "windows": {"W_star": {"task_design_candidate_count": 20, "task_design_family_count": 4}},
                "extended_R": {"task_design_candidate_count": 22},
            },
        ]

        recommendation = admission.recommend_repositories(repos)

        self.assertEqual(recommendation["primary_repo"], "click")
        self.assertEqual(recommendation["replication_repo"], "rich")

    def test_recommendation_uses_ready_repo_when_click_is_blocked(self) -> None:
        """The 0514 line cannot keep Click primary if Click fails the W* supply gate."""
        repos = [
            {
                "repo_slug": "click",
                "admission_ready": False,
                "windows": {"W_star": {"task_design_candidate_count": 14, "task_design_family_count": 4}},
                "extended_R": {"task_design_candidate_count": 53},
            },
            {
                "repo_slug": "rich",
                "admission_ready": True,
                "windows": {"W_star": {"task_design_candidate_count": 25, "task_design_family_count": 5}},
                "extended_R": {"task_design_candidate_count": 74},
            },
            {
                "repo_slug": "black",
                "admission_ready": False,
                "windows": {"W_star": {"task_design_candidate_count": 16, "task_design_family_count": 4}},
                "extended_R": {"task_design_candidate_count": 46},
            },
        ]

        recommendation = admission.recommend_repositories(repos)

        self.assertIsNone(recommendation["primary_repo"])
        self.assertEqual(recommendation["recommended_execution_repo"], "rich")
        self.assertEqual(recommendation["replication_repo"], "rich")


if __name__ == "__main__":
    unittest.main()
