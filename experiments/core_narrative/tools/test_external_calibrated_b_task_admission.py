#!/usr/bin/env python3
"""Executable specs for SymPy B task admission."""

from __future__ import annotations

import unittest

import external_calibrated_b_task_admission as admission


class ExternalCalibratedBTaskAdmissionTests(unittest.TestCase):
    def test_extract_test_nodes_from_diff_finds_added_and_modified_tests(self) -> None:
        diff = """@@ -1,0 +2,3 @@
+def test_new_case():
+    assert True
@@ -10,1 +14,1 @@ def test_existing_case():
-    assert False
+    assert True
"""

        nodes = admission.extract_test_nodes_from_diff(diff, "sympy/core/tests/test_add.py")

        self.assertEqual(
            nodes,
            [
                "sympy/core/tests/test_add.py::test_new_case",
                "sympy/core/tests/test_add.py::test_existing_case",
            ],
        )

    def test_sheet_accepts_only_noop_fail_and_reference_pass(self) -> None:
        sheet = admission.sheet_for(
            {
                "candidate_id": "sympy_b_anchor_001",
                "source_anchor_digest": "a",
                "source_time": "2026-01-01T00:00:00Z",
                "family": "core/mixed",
                "difficulty": "medium",
                "changed_file_set_digest": "b",
                "oracle_directness": "direct",
            },
            {
                "task_id": "sympy__b__001",
                "base_commit_digest": "c",
                "reference_patch_digest": "d",
                "hidden_verifier_digest": "e",
                "public_statement_digest": "f",
                "test_node_count": 1,
                "hidden_file_count": 1,
            },
            {"status": "failed", "duration_seconds": 1.25},
            {"status": "passed", "duration_seconds": 2.5},
        )

        rendered = repr(sheet)
        self.assertEqual(sheet["admission_status"], "accepted")
        self.assertEqual(sheet["noop_duration_seconds"], 1.25)
        self.assertEqual(sheet["reference_duration_seconds"], 2.5)
        self.assertNotIn("a" * 40, rendered)
        self.assertNotIn("reference_source.patch", rendered)

    def test_sheet_rejects_noop_pass(self) -> None:
        sheet = admission.sheet_for(
            {"candidate_id": "sympy_b_anchor_001"},
            {"task_id": "sympy__b__001"},
            {"status": "passed"},
            {"status": "passed"},
        )

        self.assertEqual(sheet["admission_status"], "rejected")
        self.assertIn("noop_did_not_fail", sheet["blockers"])

    def test_summarize_sheets_can_freeze_screened_admitted_candidate_pool(self) -> None:
        accepted = [
            {
                "candidate_id": f"sympy_b_anchor_{index:03d}",
                "task_id": f"sympy__b__{index:03d}",
                "admission_status": "accepted",
                "family": "core/mixed",
                "difficulty": "medium",
                "no_op_fails": True,
                "reference_patch_passes": True,
                "noop_duration_seconds": 1.0,
                "reference_duration_seconds": 2.0,
            }
            for index in range(1, 5)
        ]
        rejected = [
            {
                "candidate_id": "sympy_b_anchor_005",
                "task_id": "sympy__b__005",
                "admission_status": "rejected",
                "family": "core/mixed",
                "difficulty": "medium",
                "no_op_fails": False,
                "reference_patch_passes": True,
                "noop_duration_seconds": 1.0,
                "reference_duration_seconds": 2.0,
            }
        ]

        summary = admission.summarize_sheets(
            accepted + rejected,
            primary_target=2,
            reserve_target=2,
            candidate_pool_target=4,
            sheets_dir="sheets",
            private_root="private",
            workspace_root="workspaces",
        )

        self.assertEqual(summary["candidate_pool_mode"], "screened_admitted_pool")
        self.assertEqual(summary["screened_anchor_count"], 5)
        self.assertEqual(summary["candidate_count"], 4)
        self.assertEqual(summary["accepted_count"], 4)
        self.assertEqual(summary["primary_task_count"], 2)
        self.assertEqual(summary["reserve_task_count"], 2)
        self.assertEqual(summary["noop_fail_rate"], 1.0)
        self.assertEqual(summary["reference_patch_pass_rate"], 1.0)
        self.assertEqual(summary["screened_anchor_noop_fail_rate"], 0.8)

    def test_summarize_sheets_reports_incomplete_when_screened_pool_is_too_small(self) -> None:
        summary = admission.summarize_sheets(
            [
                {
                    "candidate_id": "sympy_b_anchor_001",
                    "task_id": "sympy__b__001",
                    "admission_status": "accepted",
                    "family": "core/mixed",
                    "difficulty": "medium",
                    "no_op_fails": True,
                    "reference_patch_passes": True,
                }
            ],
            primary_target=2,
            reserve_target=0,
            candidate_pool_target=4,
            sheets_dir="sheets",
            private_root="private",
            workspace_root="workspaces",
        )

        self.assertEqual(summary["status"], "b_admission_incomplete")
        self.assertIn("admitted_candidate_pool_below_target", summary["blockers"])


if __name__ == "__main__":
    unittest.main()
