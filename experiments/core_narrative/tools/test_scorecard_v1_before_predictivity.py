#!/usr/bin/env python3
"""Executable specs for Scorecard v1 before predictivity."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import scorecard_v1_before_predictivity as scorecard


class ScorecardV1BeforePredictivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def matrix(self) -> dict[str, Any]:
        acuts = ["cheap-generic-swe"]
        tasks = ["task-pass", "task-fail", "task-invalid", "task-infra"]
        latest = {
            "task-pass": {"status": "passed", "failure_label": "passed", "scoreable": True},
            "task-fail": {"status": "failed", "failure_label": "failed", "scoreable": True},
            "task-invalid": {
                "status": "invalid_submission",
                "failure_label": "invalid_submission:unsupported_patch_response",
                "scoreable": True,
            },
            "task-infra": {"status": "infra_failed", "failure_label": "infra_failed:runner_failed", "scoreable": False},
        }
        return {
            "tool": "codex_nfl_canonical_matrix",
            "status": "completed",
            "split": "rwork",
            "task_ids": tasks,
            "acut_ids": acuts,
            "matrix_shape": {"acuts": 1, "tasks": 4, "expected_cells": 4},
            "missing": {"attempt2_cells": [], "canonical_cells": []},
            "cells": {
                f"cheap-generic-swe::{task_id}": {
                    "acut_id": "cheap-generic-swe",
                    "task_id": task_id,
                    "canonical_latest": latest[task_id],
                }
                for task_id in tasks
            },
        }

    def test_outcome_classes_and_attemptability_are_separated(self) -> None:
        """Verified correctness and patch attemptability are distinct scorecard axes."""
        matrix = self.write_json("matrix.json", self.matrix())
        m2_5 = self.write_json(
            "m2_5.json",
            {
                "tool": "m2_5_workspace_diff_runner",
                "status": "completed",
                "submission_contract": "workspace-diff-v1",
                "results": [
                    {
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "run_id": "m2-5-1",
                        "status": "invalid_submission",
                        "patch_ready": False,
                        "attemptable": False,
                        "failure_owner": "candidate_patch",
                        "failure_class": "no_workspace_patch",
                    }
                ],
            },
        )

        payload = scorecard.build_scorecard(
            {
                "rbench_canonical_matrix": None,
                "rwork_canonical_matrix": matrix,
                "m2_scoreability_summary": None,
                "m2_5_workspace_diff": m2_5,
                "gscore_gold_patch_smoke": None,
            }
        )

        counts = payload["outcomes"]["outcome_counts"]
        self.assertEqual(counts["verified_pass"], 1)
        self.assertEqual(counts["verified_fail"], 1)
        self.assertEqual(counts["invalid_submission"], 2)
        self.assertEqual(counts["infra_failed"], 1)
        self.assertEqual(payload["outcomes"]["attemptable_count"], 2)
        self.assertEqual(payload["outcomes"]["verified_correctness_rate"], 0.5)
        self.assertFalse(payload["score_input_entries"][-1]["capability_interpretation_allowed"])

    def test_unavailable_gscore_is_recorded_as_unavailable_not_zero(self) -> None:
        """Missing G_score evidence remains unavailable instead of being zero-filled."""
        payload = scorecard.build_scorecard(
            {
                "rbench_canonical_matrix": None,
                "rwork_canonical_matrix": None,
                "m2_scoreability_summary": None,
                "m2_5_workspace_diff": None,
                "gscore_gold_patch_smoke": self.root / "missing.json",
            }
        )

        self.assertIsNone(payload["g_score"]["g_score_value"])
        self.assertTrue(payload["g_score"]["g_score_unavailable_not_zero"])
        self.assertTrue(payload["coverage_policy"]["missing_coverage_preserved"])
        self.assertFalse(payload["claim_boundaries"]["prohibited_claims"]["g_score_predictivity"])


if __name__ == "__main__":
    unittest.main()
