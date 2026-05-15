#!/usr/bin/env python3
"""Executable specs for RGW workspace-mode status semantics."""

from __future__ import annotations

import unittest

from rgw_status_semantics import classify_status


class RgwStatusSemanticsTests(unittest.TestCase):
    def test_verified_pass_is_the_only_primary_pass(self) -> None:
        """Primary pass is limited to the fresh-verification success status."""
        self.assertTrue(classify_status("verified_pass")["primary_pass"])
        self.assertEqual(classify_status("verified_pass")["score_action"], "fixed_denominator_one")
        self.assertFalse(classify_status("verified_fail")["primary_pass"])

    def test_acut_owned_zero_statuses_stay_in_fixed_denominator(self) -> None:
        """Verifier failures, no diffs, and ACUT timeouts are zero-score primary cells."""
        for status, payload in (
            ("verified_fail", {}),
            ("no_diff", {}),
            ("timeout", {"metadata": {"timeout_owner": "acut"}}),
            ("unsafe_or_scope_violation", {}),
            ("acut_command_error", {}),
        ):
            with self.subTest(status=status):
                result = classify_status(status, payload)
                self.assertEqual(result["score_action"], "fixed_denominator_zero")
                self.assertEqual(result["score_value"], 0)
                self.assertFalse(result["requires_rerun_or_exclusion"])

    def test_infra_statuses_require_rerun_or_global_exclusion(self) -> None:
        """Infrastructure statuses are not silently counted as model failures."""
        for status in (
            "verifier_infra_error",
            "base_tree_mismatch",
            "candidate_patch_extraction_error",
            "llm_backend_unavailable",
        ):
            with self.subTest(status=status):
                result = classify_status(status)
                self.assertEqual(result["score_action"], "rerun_or_global_exclusion_required")
                self.assertTrue(result["requires_rerun_or_exclusion"])
                self.assertIsNone(result["score_value"])

    def test_patch_apply_error_is_triage_paused_before_primary_scoring(self) -> None:
        """Workspace patch apply errors pause scoring until triage."""
        result = classify_status("patch_apply_error")
        self.assertEqual(result["score_action"], "triage_paused_before_primary_scoring")
        self.assertTrue(result["triage_paused"])
        self.assertIsNone(result["score_value"])

    def test_verifier_timeout_is_infrastructure_not_acut_zero(self) -> None:
        """Only ACUT-owned timeouts are fixed-denominator zeroes."""
        result = classify_status("timeout", {"metadata": {"timeout_owner": "verifier"}})
        self.assertEqual(result["score_action"], "rerun_or_global_exclusion_required")
        self.assertTrue(result["requires_rerun_or_exclusion"])


if __name__ == "__main__":
    unittest.main()
