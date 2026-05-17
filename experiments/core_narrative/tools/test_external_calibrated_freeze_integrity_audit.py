#!/usr/bin/env python3
"""Executable specs for the external calibrated freeze integrity audit."""

from __future__ import annotations

import unittest

import external_calibrated_freeze_integrity_audit as audit


def resolved_tasks(count: int) -> list[dict[str, object]]:
    return [{"smoke_status": "gold_resolved", "instance_id": f"sympy__sympy-{index}"} for index in range(count)]


def b_tasks(count: int) -> list[dict[str, object]]:
    return [
        {
            "task_id": f"sympy__b__{index:03d}",
            "reference_patch_passes": True,
            "no_op_fails": True,
            "reference_patch_digest": "a" * 64,
            "hidden_verifier_digest": "b" * 64,
            "public_statement_digest": "c" * 64,
        }
        for index in range(1, count + 1)
    ]


class ExternalCalibratedFreezeIntegrityAuditTests(unittest.TestCase):
    def test_true_rate_handles_empty_and_boolean_fields(self) -> None:
        self.assertIsNone(audit.true_rate([], "ok"))
        self.assertEqual(audit.true_rate([{"ok": True}, {"ok": False}], "ok"), 0.5)

    def test_build_payload_authorizes_after_e_and_b_freeze_gates_pass(self) -> None:
        payload = audit.build_payload(
            protocol={
                "status": "phase1_e_and_b_primary_frozen",
                "not_authorized_until_next_gate": [
                    "run_ACUT_on_E",
                    "run_ACUT_on_B",
                    "use_E_gold_or_hidden_material_in_B_generation",
                ],
            },
            repository_admission={"status": "external_and_b_primary_frozen"},
            e_config={"status": "frozen_target_size", "freeze_allowed": True, "tasks": resolved_tasks(30)},
            e_result={
                "status": "frozen_target_size",
                "freeze_allowed": True,
                "task_count": 30,
                "task_table": resolved_tasks(30),
                "raw_material_policy": {
                    "raw_problem_statements_emitted": False,
                    "raw_patches_emitted": False,
                    "raw_test_patches_emitted": False,
                    "raw_base_commits_emitted": False,
                },
            },
            b_primary={"status": "admitted_frozen", "task_count": 20, "tasks": b_tasks(20)},
            b_reserve={"status": "reserve_admitted_frozen", "task_count": 20, "tasks": b_tasks(20)},
            b_summary={
                "candidate_count": 40,
                "accepted_count": 40,
                "primary_task_count": 20,
                "reserve_task_count": 20,
                "reference_patch_pass_rate": 1.0,
                "noop_fail_rate": 1.0,
            },
            public_raw_artifact_paths=[],
            ignored_private_paths={"private": True},
        )

        self.assertEqual(payload["status"], "passed")
        self.assertTrue(payload["freeze_integrity_passed"])
        self.assertTrue(payload["acut_authorized"])
        self.assertFalse(payload["candidate_noop_gate_weak"])

    def test_build_payload_fails_integrity_when_generated_candidate_noop_gate_is_weak(self) -> None:
        payload = audit.build_payload(
            protocol={
                "status": "phase1_e_and_b_primary_frozen_candidate_noop_gate_weak",
                "not_authorized_until_next_gate": [
                    "run_ACUT_on_E",
                    "run_ACUT_on_B",
                    "use_E_gold_or_hidden_material_in_B_generation",
                ],
            },
            repository_admission={"status": "external_and_b_primary_frozen_candidate_noop_gate_weak"},
            e_config={"status": "frozen_target_size", "freeze_allowed": True, "tasks": resolved_tasks(30)},
            e_result={
                "status": "frozen_target_size",
                "freeze_allowed": True,
                "task_count": 30,
                "task_table": resolved_tasks(30),
                "raw_material_policy": {
                    "raw_problem_statements_emitted": False,
                    "raw_patches_emitted": False,
                    "raw_test_patches_emitted": False,
                    "raw_base_commits_emitted": False,
                },
            },
            b_primary={"status": "admitted_frozen", "task_count": 20, "tasks": b_tasks(20)},
            b_reserve={"status": "reserve_admitted_frozen", "task_count": 7, "tasks": b_tasks(7)},
            b_summary={
                "candidate_count": 40,
                "accepted_count": 27,
                "primary_task_count": 20,
                "reserve_task_count": 7,
                "reference_patch_pass_rate": 0.9,
                "noop_fail_rate": 0.75,
            },
            public_raw_artifact_paths=[],
            ignored_private_paths={"private": True},
        )

        self.assertEqual(payload["status"], "failed")
        self.assertFalse(payload["freeze_integrity_passed"])
        self.assertFalse(payload["acut_authorized"])
        self.assertIn("b_accepted_count_below_generated_candidate_count", payload["blockers"])
        self.assertIn("b_noop_fail_rate_below_90_percent", payload["blockers"])

    def test_raw_value_findings_detect_public_patch_leak(self) -> None:
        findings = audit.raw_value_findings({"b_primary": {"tasks": [{"raw": "diff --git a/x b/x"}]}})

        self.assertEqual(findings[0]["artifact"], "b_primary")
        self.assertEqual(findings[0]["fragment"], "diff --git")

    def test_render_report_does_not_claim_blocked_when_acut_authorized(self) -> None:
        report = audit.render_report(
            {
                "protocol_id": "external-calibrated-repo-benchmark-v1",
                "status": "passed",
                "freeze_integrity_passed": True,
                "acut_authorized": True,
                "e_audit": {"status": "pass", "task_count": 48, "blockers": []},
                "b_audit": {
                    "status": "pass",
                    "candidate_count": 40,
                    "accepted_count": 40,
                    "primary_task_count": 20,
                    "reserve_task_count": 20,
                    "reference_patch_pass_rate": 1.0,
                    "noop_fail_rate": 1.0,
                    "warnings": [],
                },
                "redaction_audit": {"status": "pass", "public_raw_artifact_paths": [], "raw_value_leaks": []},
            }
        )

        self.assertIn("clears the E/B freeze integrity gate", report)
        self.assertNotIn("remains blocked", report)


if __name__ == "__main__":
    unittest.main()
