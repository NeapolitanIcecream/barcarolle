#!/usr/bin/env python3
"""Executable specs for the RGW-full-workspace-v1 validity audit overlay."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

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

    def test_public_artifact_scan_rejects_urls_and_local_user_paths(self) -> None:
        """Committed audit artifacts must not contain raw URLs or local user paths."""
        safe = self.write_json("safe.json", {"status": "redacted"})
        unsafe = self.root / "unsafe.md"
        unsafe.write_text("raw https://example.invalid and /Users/person/path\n", encoding="utf-8")

        result = audit.scan_public_artifacts([safe, unsafe])

        self.assertFalse(result["passed"])
        self.assertEqual({item["finding"] for item in result["findings"]}, {"full_url", "absolute_users_path"})


if __name__ == "__main__":
    unittest.main()
