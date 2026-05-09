#!/usr/bin/env python3
"""Executable specs for the M2 live scoreability repair audit."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_live_scoreability_repair as repair


class M2LiveScoreabilityRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_repair_audit_separates_local_parser_repairs_from_residual_blockers(self) -> None:
        """The M2 repair artifact keeps fixed denominators and bounded claims."""
        raw_response = self.write_json(
            "provider-response.json",
            {
                "choices": [
                    {
                        "message": {
                            "content": "*** Begin Patch\n*** Update File: module.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch\n"
                        }
                    }
                ]
            },
        )
        summary = self.write_json(
            "m2-summary.json",
            {
                "tasks": ["click__rwork__003", "click__rwork__004"],
                "acuts": ["cheap-generic-swe", "cheap-click-specialist"],
                "fixed_denominator": 4,
                "claim_status": "scoreability_gate_not_met",
                "paths": {
                    "patch_or_files_v1_live": {
                        "gate": {"status": "failed"},
                        "patch_ready_coverage": 0.0,
                        "invalid_submission_rate": 0.75,
                        "status_counts": {"invalid_submission": 3, "infra_failed": 1},
                        "failure_class_counts": {
                            "unsupported_patch_response": 1,
                            "invalid_unified_diff": 1,
                            "none": 1,
                        },
                    },
                    "structured_files_json_v1_live": {
                        "gate": {"status": "failed"},
                        "patch_ready_coverage": 0.25,
                        "invalid_submission_rate": 0.5,
                        "status_counts": {"failed": 1, "invalid_submission": 2},
                        "failure_class_counts": {"unsafe_generated_text": 2},
                    },
                },
                "records": {
                    "patch_or_files_v1_live": [
                        {
                            "acut_id": "cheap-click-specialist",
                            "task_id": "click__rwork__003",
                            "status": "invalid_submission",
                            "failure_owner": "model_output",
                            "failure_class": "unsupported_patch_response",
                            "raw_response_artifact": str(raw_response),
                        },
                        {
                            "acut_id": "cheap-generic-swe",
                            "task_id": "click__rwork__004",
                            "status": "invalid_submission",
                            "failure_owner": "model_output",
                            "failure_class": "invalid_unified_diff",
                            "raw_response_artifact": str(raw_response),
                        },
                        {
                            "acut_id": "cheap-click-specialist",
                            "task_id": "click__rwork__004",
                            "status": "infra_failed",
                            "failure_owner": "infrastructure",
                            "failure_class": None,
                        },
                    ],
                    "structured_files_json_v1_live": [
                        {
                            "acut_id": "cheap-generic-swe",
                            "task_id": "click__rwork__004",
                            "status": "invalid_submission",
                            "failure_owner": "model_output",
                            "failure_class": "unsafe_generated_text",
                            "raw_response_artifact": str(raw_response),
                        }
                    ],
                },
            },
        )
        unsafe = self.write_json(
            "unsafe.json",
            {"summary": {"classification_counts": {"prompt_or_applicator_overbreadth": 4}}},
        )
        output = self.root / "repair.json"
        report = self.root / "repair.md"

        code = repair.main(
            [
                "--m2-summary",
                str(summary),
                "--unsafe-triage",
                str(unsafe),
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["scope"]["fixed_denominator"], 4)
        modes = {item["concrete_mode"]: item for item in payload["failure_modes"]}
        self.assertEqual(
            modes["codex_apply_patch_transcript_previously_unsupported"]["local_repair_status"],
            "locally_repaired_by_parser_applicator_tests",
        )
        self.assertEqual(modes["malformed_unified_diff"]["local_repair_status"], "not_auto_repaired")
        self.assertEqual(
            modes["structured_full_file_patch_artifact_full_url_overbreadth"]["local_repair_status"],
            "classified_not_repaired",
        )
        self.assertFalse(payload["prohibited_claims"]["capability_uplift"])
        self.assertFalse(payload["prohibited_claims"]["ranking_reversal"])
        self.assertIn("M2 Live Scoreability Repair Report", report.read_text(encoding="utf-8"))

    def test_live_smoke_blocker_is_recorded_without_fabricating_model_calls(self) -> None:
        """Blocked live execution is machine-readable evidence, not a missing row."""
        summary = self.write_json(
            "m2-summary.json",
            {
                "tasks": ["click__rwork__003"],
                "acuts": ["cheap-generic-swe"],
                "fixed_denominator": 1,
                "claim_status": "scoreability_gate_not_met",
                "paths": {},
                "records": {},
            },
        )
        unsafe = self.write_json("unsafe.json", {"summary": {}})
        blocker = self.write_json(
            "blocker.json",
            {
                "status": "blocked",
                "blockers": ["missing_required_llm_environment"],
                "model_call_made": False,
            },
        )
        output = self.root / "repair.json"
        report = self.root / "repair.md"

        code = repair.main(
            [
                "--m2-summary",
                str(summary),
                "--unsafe-triage",
                str(unsafe),
                "--live-smoke-blocker",
                str(blocker),
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["live_smoke"]["status"], "blocked")
        self.assertEqual(payload["live_smoke"]["blockers"], ["missing_required_llm_environment"])
        self.assertFalse(payload["live_smoke"]["model_call_made"])

    def test_prior_live_gate_preserves_failure_owner_counts_for_each_live_path(self) -> None:
        """Regression: owner accounting must include scoreable candidate_patch rows."""
        summary = self.write_json(
            "m2-summary.json",
            {
                "tasks": ["click__rwork__003", "click__rwork__004", "click__rwork__006"],
                "acuts": ["cheap-generic-swe", "cheap-click-specialist"],
                "fixed_denominator": 6,
                "claim_status": "scoreability_gate_not_met",
                "paths": {
                    "patch_or_files_v1_live": {
                        "gate": {"status": "failed"},
                        "patch_ready_coverage": 0.0,
                        "invalid_submission_rate": 0.833333,
                        "status_counts": {"invalid_submission": 5, "infra_failed": 1},
                        "failure_owner_counts": {"infrastructure": 1, "model_output": 5},
                        "failure_class_counts": {
                            "invalid_unified_diff": 2,
                            "none": 1,
                            "unsupported_patch_response": 3,
                        },
                    },
                    "structured_files_json_v1_live": {
                        "gate": {"status": "failed"},
                        "patch_ready_coverage": 0.333333,
                        "invalid_submission_rate": 0.666667,
                        "status_counts": {"failed": 2, "invalid_submission": 4},
                        "failure_owner_counts": {"candidate_patch": 2, "model_output": 4},
                        "failure_class_counts": {"none": 2, "unsafe_generated_text": 4},
                    },
                },
                "records": {
                    "patch_or_files_v1_live": [],
                    "structured_files_json_v1_live": [
                        {
                            "acut_id": "cheap-generic-swe",
                            "task_id": "click__rwork__003",
                            "status": "failed",
                            "failure_owner": "candidate_patch",
                            "failure_class": None,
                            "patch_ready": True,
                        },
                        {
                            "acut_id": "cheap-click-specialist",
                            "task_id": "click__rwork__003",
                            "status": "failed",
                            "failure_owner": "candidate_patch",
                            "failure_class": None,
                            "patch_ready": True,
                        },
                    ],
                },
            },
        )
        unsafe = self.write_json("unsafe.json", {"summary": {}})
        output = self.root / "repair.json"
        report = self.root / "repair.md"

        code = repair.main(
            [
                "--m2-summary",
                str(summary),
                "--unsafe-triage",
                str(unsafe),
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["prior_live_gate_status"]["patch_or_files_v1_live"]["failure_owner_counts"],
            {"infrastructure": 1, "model_output": 5},
        )
        self.assertEqual(
            payload["prior_live_gate_status"]["structured_files_json_v1_live"]["failure_owner_counts"],
            {"candidate_patch": 2, "model_output": 4},
        )
        report_text = report.read_text(encoding="utf-8")
        self.assertIn("| Path | Gate | Patch-ready | Invalid rate | Status counts | Failure owners | Failure classes |", report_text)
        self.assertIn("`{'candidate_patch': 2, 'model_output': 4}`", report_text)


if __name__ == "__main__":
    unittest.main()
