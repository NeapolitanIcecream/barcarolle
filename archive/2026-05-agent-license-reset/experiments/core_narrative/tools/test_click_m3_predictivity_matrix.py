#!/usr/bin/env python3
"""Executable specs for the Click M3 predictivity gate artifact."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import click_m3_predictivity_matrix as m3


class ClickM3PredictivityMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def m2_path(
        self,
        *,
        total: int = 6,
        gate_status: str,
        true_calls: int,
        false_calls: int,
        patch_ready_coverage: float,
        invalid_submission_rate: float,
        status_counts: dict[str, int],
    ) -> dict[str, Any]:
        return {
            "total": total,
            "status_counts": status_counts,
            "patch_ready_coverage": patch_ready_coverage,
            "invalid_submission_rate": invalid_submission_rate,
            "clean_replay_disagreement_count": 0,
            "missing_cell_count": 0,
            "blocked_cell_count": 0,
            "model_call_made_counts": {"true": true_calls, "false": false_calls, "unknown": 0},
            "gate": {
                "status": gate_status,
                "checks": {
                    "patch_ready_coverage": gate_status == "passed",
                    "invalid_submission_rate": gate_status == "passed",
                    "clean_replay_disagreement_count": True,
                    "complete_fixed_denominator": True,
                },
                "thresholds": {
                    "patch_ready_coverage_min": 0.7,
                    "invalid_submission_rate_max": 0.25,
                    "clean_replay_disagreement_count_max": 0,
                },
            },
        }

    def m2_summary(self, *, claim_status: str, live_gate_status: str) -> dict[str, Any]:
        return {
            "tool": "m2_scoreability_summary",
            "status": "completed",
            "claim_status": claim_status,
            "evidence_inputs": {
                "patch_or_files_v1_live": {"contract": "patch-or-files-v1", "kind": "batch", "path": "live.json"},
                "patch_or_files_v1_no_model": {
                    "contract": "patch-or-files-v1",
                    "kind": "batch",
                    "path": "no-model.json",
                },
            },
            "paths": {
                "patch_or_files_v1_live": self.m2_path(
                    gate_status=live_gate_status,
                    true_calls=6,
                    false_calls=0,
                    patch_ready_coverage=1.0 if live_gate_status == "passed" else 0.0,
                    invalid_submission_rate=0.0 if live_gate_status == "passed" else 0.833333,
                    status_counts={"failed": 6} if live_gate_status == "passed" else {"invalid_submission": 5, "infra_failed": 1},
                ),
                "patch_or_files_v1_no_model": self.m2_path(
                    gate_status="passed",
                    true_calls=0,
                    false_calls=6,
                    patch_ready_coverage=1.0,
                    invalid_submission_rate=0.0,
                    status_counts={"failed": 6},
                ),
            },
            "prohibited_claims": {
                "capability_uplift": False,
                "task_solving_improvement": False,
                "ranking_reversal": False,
                "g_score_predictivity": False,
            },
        }

    def scorecard(self) -> dict[str, Any]:
        return {
            "tool": "scorecard_v0_from_existing_matrices",
            "status": "completed",
            "fixed_denominators": {
                "canonical_matrices": {
                    "overall": {
                        "expected_cells": 56,
                        "canonical_present": 56,
                        "canonical_missing": 0,
                        "scoreable_count": 56,
                    },
                    "by_split": {
                        "rbench": {
                            "expected_cells": 32,
                            "canonical_present": 32,
                            "canonical_missing": 0,
                            "scoreable_count": 32,
                        },
                        "rwork": {
                            "expected_cells": 24,
                            "canonical_present": 24,
                            "canonical_missing": 0,
                            "scoreable_count": 24,
                        },
                    },
                },
                "m2_scoreability": {"present": True, "fixed_denominator": 6},
                "g_score_basis": {"present": True, "availability_status": "unavailable_blocked"},
            },
            "g_score": {
                "available": False,
                "blocked": True,
                "availability_status": "unavailable_blocked",
                "direct_acut_scoring_attempted": False,
                "public_leaderboard_proxy_used": False,
                "blocker_counts": {"dataset_cache_missing": 1},
            },
        }

    def matrix(self, *, split: str, expected_cells: int, task_count: int) -> dict[str, Any]:
        denominator = task_count
        return {
            "tool": "codex_nfl_canonical_matrix",
            "status": "completed",
            "split": split,
            "matrix_shape": {"acuts": 1, "tasks": task_count, "expected_cells": expected_cells},
            "missing": {"canonical_cells": []},
            "status_counts_canonical": {"passed": 1, "failed": task_count - 1},
            "failure_label_counts_canonical": {"passed": 1, "failed": task_count - 1},
            "metadata_missing_counts_canonical_future_contract": {},
            "by_acut": {
                "cheap-generic-swe": {
                    "passed": 1,
                    "fixed_denominator": denominator,
                    "score_percent_fixed_denominator": 100.0 / denominator,
                    "canonical_present": denominator,
                    "canonical_missing": 0,
                    "scoreable": denominator,
                    "status_counts": {"passed": 1, "failed": denominator - 1},
                }
            },
        }

    def predictivity(self) -> dict[str, Any]:
        return {
            "tool": "codex_nfl_predictivity_analysis",
            "status": "completed",
            "g_score": {"direct_gscore_used": False},
            "predictivity": {
                "r_score_vs_w_score_error": {"status": "computed"},
                "g_score_vs_w_score_error": {"status": "not_computable"},
                "ranking_reversal_assessment": {"status": "not_supported"},
            },
        }

    def build_payload(self, m2_payload: dict[str, Any]) -> dict[str, Any]:
        paths = {
            "m2_scoreability_summary": self.write_json("m2.json", m2_payload),
            "scorecard_v0": self.write_json("scorecard.json", self.scorecard()),
            "rbench_canonical_matrix": self.write_json("rbench.json", self.matrix(split="rbench", expected_cells=32, task_count=8)),
            "rwork_canonical_matrix": self.write_json("rwork.json", self.matrix(split="rwork", expected_cells=24, task_count=6)),
            "step7_predictivity_analysis": self.write_json("predictivity.json", self.predictivity()),
        }
        return m3.build_payload(paths)

    def test_failed_live_m2_gate_blocks_m3_even_when_no_model_path_passes(self) -> None:
        """M3 work is gated by live scoreability, not by a passing no-model baseline."""
        payload = self.build_payload(
            self.m2_summary(claim_status="scoreability_gate_not_met", live_gate_status="failed")
        )

        gate = payload["m2_live_scoreability_gate"]
        blockers = {item["blocker"] for item in payload["blockers"]}
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(gate["status"], "blocked")
        self.assertEqual(gate["live_gate_failed_paths"], ["patch_or_files_v1_live"])
        self.assertIn("m2_claim_status_not_passed", blockers)
        self.assertIn("m2_live_path_gate_not_passed", blockers)
        self.assertIn("no_model_path_not_sufficient_for_m3", blockers)
        self.assertFalse(payload["m3_execution"]["live_model_or_api_experiments_run"])
        self.assertFalse(payload["m3_execution"]["live_model_or_api_experiments_allowed"])

    def test_passed_live_m2_gate_marks_m3_eligible_without_running_live_calls(self) -> None:
        """Gate detection can pass, but this artifact still remains an existing-evidence consumer."""
        payload = self.build_payload(
            self.m2_summary(claim_status="scoreability_gate_passed", live_gate_status="passed")
        )

        self.assertEqual(payload["m2_live_scoreability_gate"]["status"], "passed")
        self.assertEqual(payload["status"], "gate_passed_existing_evidence_bounded")
        self.assertTrue(payload["m3_execution"]["live_model_or_api_experiments_allowed"])
        self.assertFalse(payload["m3_execution"]["live_model_or_api_experiments_run"])
        self.assertEqual(payload["blockers"], [])

    def test_blocker_report_schema_records_gate_and_reproduction_context(self) -> None:
        """Blocked artifacts expose a stable machine-readable schema and matching report text."""
        payload = self.build_payload(
            self.m2_summary(claim_status="scoreability_gate_not_met", live_gate_status="failed")
        )
        report = m3.report_markdown(payload)

        for key in (
            "schema_version",
            "evidence_inputs",
            "m2_live_scoreability_gate",
            "m3_execution",
            "blockers",
            "fixed_denominators",
            "claim_boundaries",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["schema_version"], m3.SCHEMA_VERSION)
        self.assertIn("M2 live scoreability gate status: `blocked`", report)
        self.assertIn("The no-model path is an instrumentation baseline", report)
        self.assertIn("click_m3_predictivity_matrix.py", report)

    def test_denominators_are_preserved_from_scorecard_and_matrices(self) -> None:
        """M3 gate artifacts must not shrink denominators after seeing a blocker."""
        payload = self.build_payload(
            self.m2_summary(claim_status="scoreability_gate_not_met", live_gate_status="failed")
        )

        fixed = payload["fixed_denominators"]
        scorecard = fixed["scorecard_v0"]["canonical_matrices"]
        self.assertEqual(scorecard["by_split"]["rbench"]["expected_cells"], 32)
        self.assertEqual(scorecard["by_split"]["rwork"]["expected_cells"], 24)
        self.assertEqual(scorecard["overall"]["expected_cells"], 56)
        self.assertEqual(fixed["scorecard_v0"]["m2_scoreability"]["fixed_denominator"], 6)
        self.assertEqual(fixed["rbench_canonical_matrix"]["expected_cells"], 32)
        self.assertEqual(fixed["rwork_canonical_matrix"]["expected_cells"], 24)

    def test_claim_boundaries_keep_predictivity_and_authorization_unavailable(self) -> None:
        """The blocker output must not promote gated evidence into unsupported claims."""
        payload = self.build_payload(
            self.m2_summary(claim_status="scoreability_gate_not_met", live_gate_status="failed")
        )
        serialized = json.dumps(payload, sort_keys=True)
        prohibited = payload["claim_boundaries"]["prohibited_claims"]

        self.assertFalse(prohibited["capability_uplift"])
        self.assertFalse(prohibited["task_solving_improvement"])
        self.assertFalse(prohibited["ranking_reversal"])
        self.assertFalse(prohibited["g_score_predictivity"])
        self.assertFalse(prohibited["license_or_admission_or_authorization_output"])
        self.assertEqual(
            payload["existing_evidence_snapshot"]["g_score_predictivity"]["status"],
            "unavailable_direct_acut_scoring_required",
        )
        for tier in ("G0", "G1", "G2", "G3", "G4", "G5"):
            self.assertNotIn(tier, serialized)


if __name__ == "__main__":
    unittest.main()
