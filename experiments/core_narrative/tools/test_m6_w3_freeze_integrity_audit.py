#!/usr/bin/env python3
"""Executable specs for the M6-W3 freeze-integrity audit."""

from __future__ import annotations

import unittest

import m6_w3_freeze_integrity_audit as audit


class M6W3FreezeIntegrityAuditTests(unittest.TestCase):
    def test_public_statement_findings_reject_diff_and_target_commit(self) -> None:
        """Public task statements must not expose target commits or implementation diffs."""
        findings = audit.public_statement_findings(
            "Fix behavior.\n\ndiff --git a/src/click/core.py b/src/click/core.py\nabc123\n",
            target_commit="abc123",
        )

        self.assertIn("implementation_diff", findings)
        self.assertIn("target_commit", findings)

    def test_public_statement_findings_allows_behavior_only_statement(self) -> None:
        """Behavior-only task statements pass the public redaction gate."""
        findings = audit.public_statement_findings(
            "# click__w3__001\n\n## Problem Statement\n\nFix the empty-string default behavior.\n",
            target_commit="abc123",
        )

        self.assertEqual(findings, [])

    def test_overall_status_fails_when_any_check_fails(self) -> None:
        """A failed audit check is carried into the machine-readable overall status."""
        checks = [
            audit.make_check("passing", "Passing check", True, {"observed": "ok"}),
            audit.make_check("failing", "Failing check", False, {"observed": "bad"}),
        ]

        self.assertEqual(audit.overall_status(checks), "failed")
        self.assertEqual(checks[1]["status"], "failed")
        self.assertEqual(checks[1]["evidence"]["observed"], "bad")

    def test_context_pack_hash_check_requires_matching_acut_and_manifest_hashes(self) -> None:
        """The calibrated ACUT and context-pack manifest must commit to the same hash."""
        acut = {
            "metadata": {
                "specialist_context": {
                    "context_pack": {
                        "pack_hash": "same-hash",
                        "manifest_path": "experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json",
                    }
                }
            }
        }
        manifest = {"pack_hash": "same-hash"}

        check = audit.context_pack_hash_check(acut, manifest)

        self.assertEqual(check["status"], "passed")
        self.assertEqual(check["evidence"]["acut_pack_hash"], "same-hash")

    def test_primary_sheet_audit_requires_smoke_digests_and_anchor_records(self) -> None:
        """Primary tasks are auditable only when their admission sheets carry all freeze evidence."""
        task = {
            "task_id": "click__w3__001",
            "source": {"anchor_id": "pallets/click#1"},
            "source_compare": {"reference_patch_digest": "a" * 64},
            "metadata": {"candidate_id": "w3_candidate_001"},
        }
        sheet = {
            "candidate_id": "w3_candidate_001",
            "admission_decision": "accepted",
            "changed_file_anchor_set": ["pallets/click#1::src/click/core.py"],
            "statement_digest": "b" * 64,
            "reference_patch_digest": "a" * 64,
            "hidden_verifier_digest": "c" * 64,
            "no_op_result": {"status": "failed", "expected_no_op_fails": True},
            "reference_result": {"status": "passed", "oracle_status": "reference_passed"},
        }

        evidence = audit.primary_sheet_evidence([task], {"w3_candidate_001": sheet})

        self.assertEqual(evidence["missing_sheet_task_ids"], [])
        self.assertEqual(evidence["invalid_smoke_task_ids"], [])
        self.assertEqual(evidence["missing_digest_task_ids"], [])
        self.assertEqual(evidence["missing_anchor_record_task_ids"], [])


if __name__ == "__main__":
    unittest.main()
