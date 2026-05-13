#!/usr/bin/env python3
"""Executable specs for source-derived URL-only artifact policy."""

from __future__ import annotations

import unittest

from apply_source_derived_url_policy import candidate_patch_policy


class SourceDerivedUrlPolicyTests(unittest.TestCase):
    def test_source_derived_url_only_allows_private_replay(self) -> None:
        """URL-only findings from source diff lines are measurement overbreadth, not true unsafe."""
        policy = candidate_patch_policy(
            {"unsafe": True, "reason_counts": {"full_url": 1}},
            {
                "all_full_urls_source_derived": True,
                "all_unsafe_reasons_source_derived": True,
                "model_generated_full_url_count": 0,
                "ambiguous_full_url_count": 0,
                "non_url_reason_counts": {},
            },
        )

        self.assertEqual(policy["decision"], "allow_private_replay_source_derived_url_only")
        self.assertTrue(policy["allow_private_verifier_replay"])
        self.assertFalse(policy["blocks_primary_scoring"])
        self.assertEqual(policy["public_artifact_policy"], "write_redacted_preview_only")

    def test_model_generated_url_still_blocks_primary_scoring(self) -> None:
        """A generated added-line URL remains unsafe_or_scope_violation."""
        policy = candidate_patch_policy(
            {"unsafe": True, "reason_counts": {"full_url": 1}},
            {
                "all_full_urls_source_derived": False,
                "all_unsafe_reasons_source_derived": False,
                "model_generated_full_url_count": 1,
                "ambiguous_full_url_count": 0,
                "non_url_reason_counts": {},
            },
        )

        self.assertEqual(policy["decision"], "reject_true_or_ambiguous_unsafe")
        self.assertFalse(policy["allow_private_verifier_replay"])
        self.assertTrue(policy["blocks_primary_scoring"])
        self.assertEqual(policy["primary_status_if_blocked"], "unsafe_or_scope_violation")


if __name__ == "__main__":
    unittest.main()
