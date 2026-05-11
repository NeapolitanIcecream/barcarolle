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

    def init_workspace_with_diff_at(self, workspace: Path) -> Path:
        workspace.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.email", "codex@example.invalid"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Codex"], cwd=workspace, check=True)
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "module.py"], cwd=workspace, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=workspace, check=True)
        (workspace / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
        return workspace

    def init_workspace_with_diff(self) -> Path:
        return self.init_workspace_with_diff_at(self.root / "workspace")

    def init_workspace_with_untracked_file(self) -> Path:
        workspace = self.root / "workspace-untracked"
        workspace.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.email", "codex@example.invalid"], cwd=workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Codex"], cwd=workspace, check=True)
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "module.py"], cwd=workspace, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=workspace, check=True)
        (workspace / "pkg").mkdir()
        (workspace / "pkg" / "generated.txt").write_text("created by acut\n", encoding="utf-8")
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

    def test_absolute_external_input_with_repo_directory_name_is_not_remapped(self) -> None:
        """Regression: external CLI inputs under a barcarolle directory were redirected."""
        original_repo_root = m3.REPO_ROOT
        self.addCleanup(lambda: setattr(m3, "REPO_ROOT", original_repo_root))
        checkout = self.root / "current" / "barcarolle"
        checkout.mkdir(parents=True)
        m3.REPO_ROOT = checkout

        local_input = checkout / "custom" / "matrix.json"
        self.write_json(local_input, {"tool": "local-checkout"})
        external_input = self.root / "external" / "barcarolle" / "custom" / "matrix.json"
        self.write_json(external_input, {"tool": "external-input"})

        info, payload = m3.load_json_input(str(external_input), input_key="matrix")

        self.assertEqual(payload, {"tool": "external-input"})
        self.assertEqual(info["path"], str(external_input))
        self.assertTrue(info["present"])

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
        self.assertEqual(record["research_outcome"], "produced_patch_replay_invalid")
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

    def test_m2_5_recovery_counts_verified_status_as_research_scoreable_without_local_artifacts(self) -> None:
        """Regression: verified M2.5 outcomes were not scoreable when local paths were absent."""
        recovery = m3.recover_m2_5(
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-verified-without-local-artifacts",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "passed",
                        "patch_path": str(self.root / "historical" / "submission.patch"),
                        "workspace": str(self.root / "historical" / "workspace"),
                        "normalized_result": str(self.root / "historical" / "normalized.json"),
                        "failure_owner": None,
                        "failure_class": None,
                    }
                ],
            }
        )

        self.assertEqual(recovery["summary"]["research_scoreable_count"], 1)
        self.assertEqual(recovery["summary"]["outcome_counts"], {"verified_pass": 1})
        record = recovery["records"][0]
        self.assertTrue(record["research_scoreable"])
        self.assertEqual(record["research_outcome"], "verified_pass")
        self.assertEqual(record["evidence_types"], [])

    def test_m2_5_recovery_counts_untracked_workspace_files_as_final_diff_evidence(self) -> None:
        """Regression: untracked work-product files were invisible to workspace diff recovery."""
        workspace = self.init_workspace_with_untracked_file()

        recovery = m3.recover_m2_5(
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-untracked-work-product",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "invalid_submission",
                        "patch_path": str(self.root / "missing.patch"),
                        "workspace": str(workspace),
                        "failure_owner": "candidate_patch",
                        "failure_class": None,
                    }
                ],
            }
        )

        self.assertEqual(recovery["summary"]["research_scoreable_count"], 1)
        self.assertEqual(recovery["summary"]["final_workspace_diff_count"], 1)
        self.assertEqual(recovery["summary"]["outcome_counts"], {"produced_patch_unverified": 1})
        record = recovery["records"][0]
        self.assertTrue(record["research_scoreable"])
        self.assertEqual(record["research_outcome"], "produced_patch_unverified")
        self.assertIn("final_workspace_git_diff", record["evidence_types"])
        self.assertTrue(record["final_workspace_diff"]["present"])
        self.assertGreater(record["final_workspace_diff"]["size_bytes"], 0)

    def test_m2_5_recovery_remaps_source_rooted_absolute_paths_to_current_checkout(self) -> None:
        """Regression: historical absolute artifact paths hid committed local evidence."""
        original_repo_root = m3.REPO_ROOT
        self.addCleanup(lambda: setattr(m3, "REPO_ROOT", original_repo_root))
        checkout = self.root / "current" / "barcarolle"
        checkout.mkdir(parents=True)
        m3.REPO_ROOT = checkout

        rel_patch = Path("experiments/core_narrative/results/raw/run/submission.patch")
        rel_normalized = Path("experiments/core_narrative/results/normalized/run.json")
        rel_workspace = Path("experiments/core_narrative/workspaces/run")
        patch_path = checkout / rel_patch
        patch_path.parent.mkdir(parents=True)
        patch_path.write_text("diff --git a/module.py b/module.py\n", encoding="utf-8")
        self.write_json(
            checkout / rel_normalized,
            {
                "status": "failed",
                "verification": {"exit_code": 1, "duration_seconds": 2.5},
                "review": {"mergeability_grade": "blocked", "wrong_module": False, "rule_violation": True},
            },
        )
        self.init_workspace_with_diff_at(checkout / rel_workspace)

        historical_root = self.root / "source-machine" / "barcarolle"
        historical_patch = historical_root / rel_patch
        historical_patch.parent.mkdir(parents=True)
        historical_patch.write_text("diff --git a/other.py b/other.py\n", encoding="utf-8")
        self.write_json(
            historical_root / rel_normalized,
            {
                "status": "passed",
                "verification": {"exit_code": 0, "duration_seconds": 1.0},
                "review": {"mergeability_grade": "clean", "wrong_module": False, "rule_violation": False},
            },
        )
        (historical_root / rel_workspace).mkdir(parents=True)
        recovery = m3.recover_m2_5(
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-historical-absolute-paths",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "failed",
                        "patch_path": str(historical_root / rel_patch),
                        "workspace": str(historical_root / rel_workspace),
                        "normalized_result": str(historical_root / rel_normalized),
                        "candidate_patch_sha256": m3.sha256_file(patch_path),
                        "candidate_patch_size_bytes": patch_path.stat().st_size,
                        "failure_owner": "verifier",
                        "failure_class": "test_failure",
                    }
                ],
            }
        )

        record = recovery["records"][0]
        self.assertEqual(record["research_outcome"], "verified_fail")
        self.assertTrue(record["patch"]["present"])
        self.assertEqual(record["patch"]["path"], rel_patch.as_posix())
        self.assertTrue(record["normalized_result"]["present"])
        self.assertEqual(record["normalized_result"]["path"], rel_normalized.as_posix())
        self.assertTrue(record["final_workspace_diff"]["present"])
        self.assertEqual(record["final_workspace_diff"]["path"], rel_workspace.as_posix())
        self.assertTrue(record["verifier_or_test_evidence"]["present"])
        self.assertEqual(record["verifier_or_test_evidence"]["exit_code"], 1)
        self.assertTrue(record["review_evidence"]["present"])
        self.assertEqual(record["review_evidence"]["mergeability_grade"], "blocked")

    def test_score_input_set_digest_ignores_live_m2_5_recovery_artifact_state(self) -> None:
        """Regression: live workspace recovery details made identical inputs hash differently."""
        workspace = self.root / "digest-workspace"
        m2_5_path = self.write_json(
            self.root / "m2_5_digest.json",
            {
                "schema_version": "core-narrative.m2-5-workspace-diff-v1",
                "status": "completed",
                "run_prefix": "m2_5_fixture",
                "results": [
                    {
                        "run_id": "m2-5-digest-stability",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "invalid_submission",
                        "patch_path": str(self.root / "missing.patch"),
                        "workspace": str(workspace),
                        "failure_owner": "candidate_patch",
                        "failure_class": None,
                    }
                ],
            },
        )
        args = SimpleNamespace(
            matrix=str(self.matrix_path()),
            scorecard_v1=str(self.scorecard_path()),
            m2_5_summary=str(m2_5_path),
            output=str(self.root / "out.json"),
            m2_5_output=str(self.root / "m2_5_recovery.json"),
            report=str(self.root / "report.md"),
        )

        missing_workspace_payload, _ = m3.build_payload(args)
        self.init_workspace_with_diff_at(workspace)
        present_workspace_payload, _ = m3.build_payload(args)

        self.assertNotEqual(
            missing_workspace_payload["m2_5_recovery"]["records"][0]["final_workspace_diff"],
            present_workspace_payload["m2_5_recovery"]["records"][0]["final_workspace_diff"],
        )
        self.assertEqual(
            missing_workspace_payload["score_input_set_digest"],
            present_workspace_payload["score_input_set_digest"],
        )


if __name__ == "__main__":
    unittest.main()
