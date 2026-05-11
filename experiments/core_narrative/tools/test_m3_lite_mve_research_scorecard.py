#!/usr/bin/env python3
"""Executable specs for the M3-lite research MVE scorecard."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import m3_lite_mve_research_scorecard as m3


class M3LiteMVEResearchScorecardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def init_workspace_with_diff(self) -> Path:
        workspace = self.root / "workspace"
        workspace.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.email", "codex@example.invalid"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Codex"], cwd=workspace, check=True)
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "module.py"], cwd=workspace, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=workspace, check=True)
        (workspace / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
        return workspace

    def matrix_path(self) -> Path:
        return self.write_json(
            self.root / "matrix.json",
            {
                "schema_version": "core-narrative.m3-lite-mve-protocol.v1",
                "matrix": {
                    "repository": "click",
                    "acuts": ["cheap-generic-swe", "cheap-click-specialist", "frontier-click-specialist"],
                    "rbench_tasks": [
                        "click__rbench__001",
                        "click__rbench__002",
                        "click__rbench__003",
                        "click__rbench__004",
                    ],
                    "rwork_tasks": [
                        "click__rwork__001",
                        "click__rwork__002",
                        "click__rwork__003",
                        "click__rwork__004",
                    ],
                },
                "scope_reset": {
                    "mode": "research_grade_minimum_viable_evidence",
                    "license_or_admission_claims_allowed": False,
                },
                "research_scoreability_protocol": {
                    "clean_room_replay": {"required_for_research_scoreability": False}
                },
            },
        )

    def scorecard_path(self) -> Path:
        entries = [
            {
                "source_input": "rbench_canonical_matrix",
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rbench__001",
                "status": "passed",
                "scorecard_v1_outcome": "verified_pass",
                "run_id": "rbench-pass",
            },
            {
                "source_input": "rbench_canonical_matrix",
                "acut_id": "cheap-click-specialist",
                "task_id": "click__rbench__001",
                "status": "failed",
                "scorecard_v1_outcome": "verified_fail",
                "run_id": "rbench-fail",
            },
            {
                "source_input": "rwork_canonical_matrix",
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rwork__001",
                "status": "passed",
                "scorecard_v1_outcome": "verified_pass",
                "run_id": "rwork-pass",
            },
        ]
        return self.write_json(
            self.root / "scorecard.json",
            {
                "tool": "scorecard_v1_before_predictivity",
                "schema_version": "core-narrative.scorecard-v1-before-predictivity.v1",
                "status": "completed",
                "g_score": {
                    "available": False,
                    "availability_status": "unavailable_blocked",
                    "direct_acut_scoring_attempted": False,
                },
                "score_input_entries": entries,
            },
        )

    def m2_5_path(self) -> Path:
        workspace = self.init_workspace_with_diff()
        patch_path = self.root / "submission.patch"
        diff = subprocess.run(
            ["git", "diff", "--binary", "--no-ext-diff", "--unified=0", "HEAD"],
            cwd=workspace,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout
        patch_path.write_bytes(diff)
        normalized_path = self.write_json(
            self.root / "normalized.json",
            {
                "status": "invalid_submission",
                "metadata": {"clean_patch_replay": {"status": "invalid_submission"}},
                "verification": {"exit_code": None, "duration_seconds": 0},
                "review": {"mergeability_grade": None},
            },
        )
        return self.write_json(
            self.root / "m2_5.json",
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-run",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "invalid_submission",
                        "patch_path": str(patch_path),
                        "workspace": str(workspace),
                        "normalized_result": str(normalized_path),
                        "candidate_patch_sha256": m3.sha256_file(patch_path),
                        "candidate_patch_size_bytes": patch_path.stat().st_size,
                        "clean_replay_status": "invalid_submission",
                        "failure_owner": "candidate_patch",
                        "failure_class": None,
                    }
                ],
            },
        )

    def build_args(self) -> SimpleNamespace:
        return SimpleNamespace(
            matrix=str(self.matrix_path()),
            scorecard_v1=str(self.scorecard_path()),
            m2_5_summary=str(self.m2_5_path()),
            output=str(self.root / "out.json"),
            m2_5_output=str(self.root / "m2_5_recovery.json"),
            report=str(self.root / "report.md"),
        )

    def test_m3_lite_builds_research_grade_partial_grw_without_admission_claims(self) -> None:
        """M3-lite scores partial evidence while keeping G unavailable and claims bounded."""
        payload, recovery_artifact = m3.build_payload(self.build_args())

        self.assertFalse(payload["scope"]["product_gate"])
        self.assertFalse(payload["scope"]["license_or_admission_claims_allowed"])
        self.assertEqual(payload["protocol"]["fixed_denominators"]["r_score_cells"], 12)
        self.assertEqual(payload["protocol"]["fixed_denominators"]["w_score_cells"], 12)
        self.assertEqual(payload["g_score"]["availability_status"], "unavailable_blocked")
        self.assertIsNone(payload["g_score"]["value"])
        self.assertEqual(payload["r_score_partial"]["summary"]["fixed_denominator"], 12)
        self.assertEqual(payload["w_score_partial"]["summary"]["fixed_denominator"], 12)
        self.assertTrue(payload["claim_boundaries"]["does_not_emit_admission"])
        self.assertEqual(payload["story_impact"]["nfl_claim_status"], "not_established")
        self.assertEqual(recovery_artifact["schema_version"], "core-narrative.m3-lite-m2-5-recovery.v1")

    def test_story_impact_does_not_mark_w_coverage_weak_when_summary_is_verified(self) -> None:
        """Regression: W coverage was read from the wrong nesting and always blocked."""
        story = m3.story_impact(
            {
                "g_score": {"available": False},
                "w_score_partial": {"summary": {"verified_outcome_count": 4}},
                "m2_5_recovery": {"summary": {"research_scoreable_count": 1}},
            }
        )

        self.assertEqual(story["weakens_or_blocks"], ["g_score_unavailable"])

    def test_m2_5_recovery_accepts_patch_and_final_workspace_diff_without_clean_replay(self) -> None:
        """Research-scoreability can use final work-product evidence when replay is invalid."""
        payload, _ = m3.build_payload(self.build_args())
        recovery = payload["m2_5_recovery"]

        self.assertEqual(recovery["summary"]["research_scoreable_count"], 1)
        self.assertEqual(recovery["summary"]["persisted_patch_count"], 1)
        self.assertEqual(recovery["summary"]["final_workspace_diff_count"], 1)
        record = recovery["records"][0]
        self.assertFalse(record["clean_room_replay_required"])
        self.assertEqual(record["research_outcome"], "produced_patch_replay_invalid")
        self.assertIn("persisted_submission_patch", record["evidence_types"])
        self.assertIn("final_workspace_git_diff", record["evidence_types"])

    def test_m2_5_recovery_preserves_patch_metadata_when_artifact_path_is_absent(self) -> None:
        """Regression: summary hash/size evidence was ignored when patch paths were non-portable."""
        recovery = m3.recover_m2_5(
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-missing-local-patch",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "invalid_submission",
                        "patch_path": str(self.root / "historical" / "submission.patch"),
                        "workspace": str(self.root / "historical" / "workspace"),
                        "candidate_patch_sha256": "a" * 64,
                        "candidate_patch_size_bytes": 17,
                        "clean_replay_status": "invalid_submission",
                        "failure_owner": "candidate_patch",
                        "failure_class": None,
                    }
                ],
            }
        )

        self.assertEqual(recovery["summary"]["research_scoreable_count"], 1)
        self.assertEqual(recovery["summary"]["persisted_patch_count"], 1)
        record = recovery["records"][0]
        self.assertEqual(record["research_outcome"], "produced_patch_unverified")
        self.assertIn("persisted_submission_patch", record["evidence_types"])
        self.assertEqual(
            record["patch"],
            {
                "present": True,
                "path": str(self.root / "historical" / "submission.patch"),
                "sha256": "a" * 64,
                "size_bytes": 17,
            },
        )


if __name__ == "__main__":
    unittest.main()
