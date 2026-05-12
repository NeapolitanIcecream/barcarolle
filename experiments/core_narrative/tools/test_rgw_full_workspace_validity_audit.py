#!/usr/bin/env python3
"""Executable specs for the RGW-full-workspace-v1 validity audit overlay."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import rgw_full_workspace_validity_audit as audit


class RgwFullWorkspaceValidityAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, relative: str, payload: dict[str, object]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def run_git(self, workspace: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=workspace,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_source_derived_full_urls_become_policy_hold_not_true_unsafe(self) -> None:
        """Source-derived URL-only USV cells are held out of measured ACUT failures."""
        artifact_dir = self.root / "raw/run-1"
        self.write_json(
            "raw/run-1/workspace_mode_result.json",
            {
                "status": "unsafe_or_scope_violation",
                "candidate_patch": {
                    "written": False,
                    "size_bytes": 0,
                    "raw_candidate_patch_size_bytes": 123,
                    "redacted_preview": {"written": True},
                    "unsafe_content_attribution": {
                        "all_full_urls_source_derived": True,
                        "all_unsafe_reasons_source_derived": True,
                        "full_url_count": 1,
                        "source_derived_full_url_count": 1,
                        "model_generated_full_url_count": 0,
                        "ambiguous_full_url_count": 0,
                        "non_url_reason_counts": {},
                        "reason_counts": {"full_url": 1},
                        "full_url_role_counts": {"source_context": 1},
                        "url_occurrences": [
                            {
                                "diff_line_role": "source_context",
                                "line_number": 7,
                                "url_char_count": 44,
                                "url_sha256": "abc",
                            }
                        ],
                    },
                },
            },
        )
        records = [
            {
                "split": "rwork",
                "task_id": "click__rwork__004",
                "acut_id": "cheap-click-specialist",
                "run_id": "run-1",
                "status": "unsafe_or_scope_violation",
                "artifact_paths": {"artifact_dir": str(artifact_dir)},
            }
        ]

        cells = audit.build_usv_audit(records, self.root)

        self.assertEqual(cells[0]["audit_attribution_category"], "all_full_urls_source_derived")
        self.assertEqual(cells[0]["audit_disposition"], "policy_hold_source_derived_url")
        self.assertFalse(cells[0]["acut_failure_counted_in_overlay"])
        occurrence_json = json.dumps(cells[0]["unsafe_attribution_redacted"]["url_occurrences"][0])
        self.assertNotIn("http://", occurrence_json)
        self.assertNotIn("https://", occurrence_json)

    def test_usv_audit_rebases_recorded_artifact_dir_to_current_primary_root(self) -> None:
        """Regression: committed absolute artifact paths may point at another checkout root."""
        recorded_artifact_dir = (
            self.root
            / "old-checkout"
            / "experiments/core_narrative/results/rgw_full_workspace_v1/raw/run-1"
        )
        self.write_json(
            "raw/run-1/workspace_mode_result.json",
            {
                "status": "unsafe_or_scope_violation",
                "candidate_patch": {
                    "unsafe_content_attribution": {
                        "all_full_urls_source_derived": False,
                        "all_unsafe_reasons_source_derived": False,
                        "model_generated_full_url_count": 1,
                        "ambiguous_full_url_count": 0,
                        "non_url_reason_counts": {},
                    }
                },
            },
        )
        records = [
            {
                "split": "rwork",
                "task_id": "click__rwork__004",
                "acut_id": "cheap-click-specialist",
                "run_id": "run-1",
                "status": "unsafe_or_scope_violation",
                "artifact_paths": {"artifact_dir": str(recorded_artifact_dir)},
            }
        ]

        cells = audit.build_usv_audit(records, self.root)

        self.assertEqual(cells[0]["raw_artifact_ref"], "raw/run-1")
        self.assertEqual(cells[0]["workspace_mode_status"], "unsafe_or_scope_violation")

    def test_policy_hold_replay_extracts_patch_from_cross_root_artifact_dir(self) -> None:
        """Regression: replay extraction must use the artifact dir resolved during USV audit."""
        primary_root = self.root / "current-results"
        recorded_artifact_dir = (
            self.root
            / "old-checkout"
            / "experiments/core_narrative/results/rgw_full_workspace_v1/raw/run-1"
        )
        run_workspace = self.root / "preserved-workspace"
        run_workspace.mkdir(parents=True)
        self.run_git(run_workspace, "init")
        self.run_git(run_workspace, "config", "user.email", "test@example.invalid")
        self.run_git(run_workspace, "config", "user.name", "Test User")
        (run_workspace / "hello.txt").write_text("before\n", encoding="utf-8")
        self.run_git(run_workspace, "add", "hello.txt")
        self.run_git(run_workspace, "commit", "-m", "base")
        (run_workspace / "hello.txt").write_text("after\n", encoding="utf-8")
        recorded_artifact_dir.mkdir(parents=True)
        (recorded_artifact_dir / "workspace_mode_result.json").write_text(
            json.dumps(
                {
                    "status": "unsafe_or_scope_violation",
                    "run_workspace": str(run_workspace),
                    "candidate_patch": {
                        "base_ref": "HEAD",
                        "unsafe_content_attribution": {
                            "all_full_urls_source_derived": True,
                            "all_unsafe_reasons_source_derived": True,
                            "full_url_count": 1,
                            "source_derived_full_url_count": 1,
                            "model_generated_full_url_count": 0,
                            "ambiguous_full_url_count": 0,
                            "non_url_reason_counts": {},
                        },
                    },
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        records = [
            {
                "split": "rwork",
                "task_id": "click__rwork__004",
                "acut_id": "cheap-click-specialist",
                "run_id": "run-1",
                "status": "unsafe_or_scope_violation",
                "artifact_paths": {"artifact_dir": str(recorded_artifact_dir)},
            }
        ]

        cells = audit.build_usv_audit(records, primary_root)
        patch_path, metadata = audit.extract_patch_from_preserved_workspace(
            cells[0],
            primary_root,
            self.root / "extract-artifacts",
        )

        self.assertIn("hello.txt", patch_path.read_text(encoding="utf-8"))
        self.assertGreater(metadata["patch_bytes"], 0)
        public_cell = audit.public_usv_cell(cells[0])
        self.assertNotIn("_resolved_artifact_dir", public_cell)
        self.assertNotIn(str(recorded_artifact_dir), json.dumps(public_cell))

    def test_model_generated_full_url_remains_true_unsafe(self) -> None:
        """Model-added full URLs stay true unsafe outcomes in the audit overlay."""
        category = audit.attribution_category(
            {
                "all_full_urls_source_derived": False,
                "all_unsafe_reasons_source_derived": False,
                "model_generated_full_url_count": 1,
                "ambiguous_full_url_count": 0,
                "non_url_reason_counts": {},
            }
        )

        self.assertEqual(category, "model_generated_full_url")

    def test_w_metrics_exclude_policy_holds_from_measured_denominator(self) -> None:
        """Measured W rate removes policy holds while fixed denominator remains frozen."""
        records = [
            {"split": "rwork", "status": "verified_pass"},
            {"split": "rwork", "status": "verified_pass"},
            {"split": "rwork", "status": "verified_fail"},
            {"split": "rwork", "status": "unsafe_or_scope_violation"},
        ]
        usv_cells = [
            {"split": "rwork", "audit_disposition": "policy_hold_source_derived_url"},
            {"split": "rwork", "audit_disposition": "true_unsafe_primary_result"},
        ]

        overlay = audit.w_metrics(records, usv_cells)

        self.assertEqual(overlay["metrics"]["fixed_denominator_verified_pass_rate"], 0.5)
        self.assertEqual(overlay["metrics"]["measured_verified_pass_rate"], 2 / 3)
        self.assertEqual(overlay["metrics"]["policy_hold_count"], 1)
        self.assertEqual(overlay["metrics"]["true_unsafe_count"], 1)

    def test_w_metrics_ignore_rbench_usv_cells_for_w_overlay(self) -> None:
        """Regression: RBench policy holds must not shrink the W measured denominator."""
        records = [
            {"split": "rwork", "status": "verified_pass"},
            {"split": "rwork", "status": "verified_fail"},
            {"split": "rbench", "status": "unsafe_or_scope_violation"},
        ]
        usv_cells = [
            {"split": "rbench", "audit_disposition": "policy_hold_source_derived_url"},
            {"split": "rbench", "audit_disposition": "true_unsafe_primary_result"},
        ]

        overlay = audit.w_metrics(records, usv_cells)

        self.assertEqual(overlay["denominators"]["measured_denominator"], 2)
        self.assertEqual(overlay["metrics"]["measured_verified_pass_rate"], 0.5)
        self.assertEqual(overlay["metrics"]["policy_hold_count"], 0)
        self.assertEqual(overlay["metrics"]["true_unsafe_count"], 0)

    def test_w_metrics_deduplicate_rwork_cells_before_rates(self) -> None:
        """Regression: RWork reruns for one cell must not inflate W overlay rates."""
        records = [
            {
                "split": "rwork",
                "task_id": "click__rwork__001",
                "acut_id": "cheap-generic-swe",
                "run_id": "older-policy-hold",
                "status": "unsafe_or_scope_violation",
                "finished_at": "2026-05-12T10:00:00Z",
                "attempt": 1,
            },
            {
                "split": "rwork",
                "task_id": "click__rwork__001",
                "acut_id": "cheap-generic-swe",
                "run_id": "newer-pass",
                "status": "verified_pass",
                "finished_at": "2026-05-12T11:00:00Z",
                "attempt": 1,
            },
            {
                "split": "rwork",
                "task_id": "click__rwork__002",
                "acut_id": "cheap-generic-swe",
                "run_id": "single-fail",
                "status": "verified_fail",
                "finished_at": "2026-05-12T10:30:00Z",
                "attempt": 1,
            },
        ]
        usv_cells = [
            {
                "split": "rwork",
                "task_id": "click__rwork__001",
                "acut_id": "cheap-generic-swe",
                "run_id": "older-policy-hold",
                "audit_disposition": "policy_hold_source_derived_url",
            }
        ]

        overlay = audit.w_metrics(records, usv_cells)

        self.assertEqual(overlay["denominators"]["fixed_denominator"], 2)
        self.assertEqual(overlay["denominators"]["measured_denominator"], 2)
        self.assertEqual(overlay["denominators"]["verified_pass_count"], 1)
        self.assertEqual(overlay["metrics"]["fixed_denominator_verified_pass_rate"], 0.5)
        self.assertEqual(overlay["metrics"]["measured_verified_pass_rate"], 0.5)
        self.assertEqual(overlay["metrics"]["policy_hold_count"], 0)

    def test_write_report_renders_empty_w_rates_without_crashing(self) -> None:
        """Regression: empty RWork inputs render nullable W rates instead of raising."""
        report = self.root / "report.md"
        overlay = audit.w_metrics([], [])

        audit.write_report(
            report_path=report,
            usv_cells=[],
            reference_smokes=[],
            replays=[],
            overlay=overlay,
        )

        text = report.read_text(encoding="utf-8")
        self.assertIn("fixed_denominator_verified_pass_rate: null", text)
        self.assertIn("measured_verified_pass_rate: null", text)

    def test_reference_smoke_timeout_is_blocked_not_oracle_invalid(self) -> None:
        """Regression: verifier timeouts leave the reference oracle unknown."""
        with mock.patch.object(
            audit,
            "reference_patch_for_task",
            return_value=("diff --git a/a b/a\n", {"patch_bytes": 21, "patch_sha256": "abc", "changed_file_count": 1}),
        ):
            with mock.patch.object(audit, "prepare_workspace", return_value={}):
                with mock.patch.object(audit, "install_workspace", return_value={}):
                    with mock.patch.object(
                        audit,
                        "verify_patch",
                        return_value={
                            "normalized": {
                                "status": "timeout",
                                "verification": {"exit_code": 124, "duration_seconds": 1.0},
                            }
                        },
                    ):
                        result = audit.run_reference_smoke(
                            task_id="click__rbench__001",
                            private_root=self.root / "private",
                            install_timeout_seconds=1,
                            verifier_timeout_seconds=1,
                            force_private=True,
                        )

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["oracle_status"], "reference_smoke_blocked")

    def test_public_artifact_scan_rejects_urls_and_local_user_paths(self) -> None:
        """Committed audit artifacts must not contain raw URLs or local user paths."""
        safe = self.write_json("safe.json", {"status": "redacted"})
        unsafe = self.root / "unsafe.md"
        unsafe.write_text("raw https://example.invalid and /Users/person/path\n", encoding="utf-8")

        result = audit.scan_public_artifacts([safe, unsafe])

        self.assertFalse(result["passed"])
        self.assertEqual({item["finding"] for item in result["findings"]}, {"full_url", "absolute_users_path"})

    def test_run_audit_summary_reports_actual_roots(self) -> None:
        """Regression: audit summaries must reflect the roots passed to the tool."""
        repo_root = self.root / "repo"
        primary_root = repo_root / "staging/results"
        audit_root = repo_root / "staging/results/audit"
        private_root = repo_root / "staging/private"
        report = repo_root / "staging/reports/validity_audit.md"
        primary_root.mkdir(parents=True)
        (primary_root / "normalized_result_matrix.json").write_text('{"records": []}', encoding="utf-8")
        args = argparse.Namespace(
            primary_root=str(primary_root),
            audit_root=str(audit_root),
            private_root=str(private_root),
            report=str(report),
            install_timeout_seconds=1,
            verifier_timeout_seconds=1,
            force_private=True,
        )

        with mock.patch.object(audit, "REPO_ROOT", repo_root):
            with mock.patch.object(audit, "build_usv_audit", return_value=[]):
                with mock.patch.object(
                    audit,
                    "run_reference_smoke",
                    return_value={"task_id": "reference", "status": "passed", "oracle_status": "passed"},
                ):
                    summary = audit.run_audit(args)

        self.assertEqual(summary["primary_root"], "staging/results")
        self.assertEqual(summary["audit_root"], "staging/results/audit")
        self.assertEqual(summary["private_material_root"], "staging/private")
        self.assertFalse(Path(summary["primary_root"]).is_absolute())
        self.assertEqual(json.loads((audit_root / "audit_summary.json").read_text(encoding="utf-8")), summary)


if __name__ == "__main__":
    unittest.main()
