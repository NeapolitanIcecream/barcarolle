#!/usr/bin/env python3
"""Executable specs for the M2 anchored-contract smoke matrix."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_anchored_contract_smoke as smoke


class M2AnchoredContractSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_no_spend_fixture_matrix_records_anchor_diagnostics_and_missing_raw_artifacts(self) -> None:
        """The fixture smoke keeps denominator, diagnostics, and model-call accounting separate."""
        m2_summary = self.write_json(
            "m2-summary.json",
            {
                "fixed_denominator": 6,
                "tasks": ["click__rwork__003", "click__rwork__004", "click__rwork__006"],
                "acuts": ["cheap-generic-swe", "cheap-click-specialist"],
                "claim_status": "scoreability_gate_not_met",
            },
        )
        output = self.root / "anchored-smoke.json"
        report = self.root / "anchored-smoke.md"

        code = smoke.main(
            [
                "--m2-summary",
                str(m2_summary),
                "--run-prefix",
                "unit_m2_anchored_contract_smoke",
                "--raw-root",
                str(self.root / "raw"),
                "--workspace-root",
                str(self.root / "workspaces"),
                "--force",
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["scope"]["contract"], "anchored-search-replace-json-v3")
        self.assertEqual(payload["scope"]["fixture_fixed_denominator"], 7)
        self.assertEqual(payload["scope"]["prior_m2_fixed_denominator"], 6)
        self.assertTrue(payload["scope"]["denominators_are_separate"])
        self.assertEqual(payload["scope"]["repair_focus"], "anchored_old_occurrence_repair")
        self.assertFalse(payload["cost_model_call_flags"]["fixtures"]["model_call_made"])
        self.assertEqual(payload["cost_model_call_flags"]["fixtures"]["model_spend_usd"], 0.0)

        diagnostics = payload["diagnostic_summary"]
        self.assertEqual(diagnostics["ambiguous_anchor_diagnostic_rows"], 1)
        self.assertEqual(diagnostics["stale_anchor_diagnostic_rows"], 1)
        self.assertEqual(diagnostics["repeated_old_missing_anchor_rows"], 1)
        self.assertEqual(diagnostics["stale_old_text_rows"], 1)
        self.assertEqual(diagnostics["old_occurrence_mismatch_rows"], 2)
        self.assertEqual(diagnostics["old_occurrence_rows_with_hashes"], 2)
        self.assertEqual(diagnostics["redacted_source_text_diagnostic_rows"], 1)
        self.assertEqual(diagnostics["missing_raw_artifact_rows"], 1)
        self.assertFalse(diagnostics["source_content_recorded"])

        rows = {row["fixture_id"]: row for row in payload["matrix"]}
        self.assertEqual(rows["exact_anchored_search_text"]["status"], "patch_ready")
        self.assertEqual(
            rows["exact_anchored_search_text"]["patch"]["applied_edit_summaries"][0]["resolution"],
            "exact",
        )
        self.assertFalse(
            rows["exact_anchored_search_text"]["patch"]["applied_edit_summaries"][0]["search_text"]["content_recorded"]
        )
        self.assertEqual(rows["ambiguous_anchor"]["failure_class"], "search_replace_anchor_mismatch")
        self.assertEqual(rows["stale_anchor"]["details"]["diagnostic"]["code"], "unique_old_anchor_mismatch")
        self.assertEqual(rows["repeated_old_missing_anchors"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(rows["repeated_old_missing_anchors"]["details"]["occurrences"], 2)
        self.assertEqual(
            rows["repeated_old_missing_anchors"]["details"]["diagnostic"]["code"],
            "old_text_repeated_without_anchors",
        )
        self.assertEqual(rows["stale_old_text"]["failure_class"], "search_replace_old_occurrence_mismatch")
        self.assertEqual(rows["stale_old_text"]["details"]["occurrences"], 0)
        self.assertEqual(rows["stale_old_text"]["details"]["diagnostic"]["code"], "old_text_not_found")
        self.assertIsInstance(rows["stale_old_text"]["details"]["search_text"]["old_text_sha256"], str)
        self.assertEqual(rows["missing_raw_artifact"]["status"], "missing_replay_input")
        redacted = rows["redacted_source_text"]
        self.assertEqual(redacted["failure_class"], "unsafe_generated_text")
        self.assertEqual(
            redacted["details"]["patch_result_before_patch_artifact"]["edit_diagnostics"][0]["diagnostic"]["code"],
            "redacted_source_text_matched_raw_source",
        )
        for claim, value in payload["prohibited_claims"].items():
            self.assertFalse(value, claim)
        self.assertIn("M2 Anchored Contract Scoreability Smoke", report.read_text(encoding="utf-8"))

    def test_live_smoke_blocker_does_not_fabricate_model_calls(self) -> None:
        """Blocked live evidence is explicit and separate from no-spend fixtures."""
        m2_summary = self.write_json("m2-summary.json", {"fixed_denominator": 6})
        blocker = self.write_json(
            "blocker.json",
            {
                "status": "blocked",
                "blockers": ["budget_gate_blocked"],
                "model_call_made": False,
            },
        )
        output = self.root / "anchored-smoke-blocked.json"
        report = self.root / "anchored-smoke-blocked.md"

        code = smoke.main(
            [
                "--m2-summary",
                str(m2_summary),
                "--run-prefix",
                "unit_m2_anchored_contract_smoke_blocked",
                "--raw-root",
                str(self.root / "raw"),
                "--workspace-root",
                str(self.root / "workspaces"),
                "--live-smoke-blocker",
                str(blocker),
                "--force",
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["live_smoke"]["status"], "blocked")
        self.assertFalse(payload["live_smoke"]["model_call_made"])
        self.assertFalse(payload["cost_model_call_flags"]["live_smoke"]["model_call_made"])

    def test_live_smoke_batch_records_nested_failure_counts(self) -> None:
        """Attached live evidence surfaces model-output failure class counts."""
        m2_summary = self.write_json("m2-summary.json", {"fixed_denominator": 6})
        live_batch = self.write_json(
            "live-batch.json",
            {
                "submission_contract": "anchored-search-replace-json-v3",
                "results": [
                    {
                        "status": "invalid_submission",
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__006",
                        "artifact_dir": "/tmp/live-artifacts",
                        "prompt_snapshot": "/tmp/live-artifacts/prompt_snapshot.json",
                        "raw_response_artifact": "/tmp/live-artifacts/provider_response.redacted.json",
                        "runner_result": {
                            "model_call_made": True,
                            "details": {
                                "failure_class": "search_replace_old_occurrence_mismatch",
                                "path": "src/click/core.py",
                                "edit_index": 0,
                                "occurrences": 0,
                                "anchor_matches": 0,
                                "content_recorded": False,
                                "diagnostic": {"code": "old_text_not_found"},
                                "search_text": {
                                    "old_text_char_count": 246,
                                    "old_text_line_count": 5,
                                    "old_text_sha256": "abc123",
                                    "old_redacted_url_marker_count": 0,
                                    "content_recorded": False,
                                },
                            },
                        },
                    }
                ],
            },
        )
        output = self.root / "anchored-smoke-live.json"
        report = self.root / "anchored-smoke-live.md"

        code = smoke.main(
            [
                "--m2-summary",
                str(m2_summary),
                "--run-prefix",
                "unit_m2_anchored_contract_smoke_live",
                "--raw-root",
                str(self.root / "raw"),
                "--workspace-root",
                str(self.root / "workspaces"),
                "--live-smoke-batch",
                str(live_batch),
                "--force",
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(payload["live_smoke"]["model_call_made"])
        self.assertEqual(
            payload["live_smoke"]["failure_class_counts"],
            {"search_replace_old_occurrence_mismatch": 1},
        )
        self.assertEqual(payload["live_smoke"]["failure_owner_counts"], {"model_output": 1})
        self.assertEqual(payload["live_smoke"]["old_occurrence_summary"]["row_count"], 1)
        self.assertEqual(payload["live_smoke"]["old_occurrence_summary"]["old_occurrence_count_buckets"], {"0": 1})
        self.assertEqual(
            payload["live_smoke"]["old_occurrence_diagnostics"][0]["old_text_sha256"],
            "abc123",
        )
        self.assertFalse(payload["live_smoke"]["old_occurrence_diagnostics"][0]["content_recorded"])
        self.assertIn("search_replace_old_occurrence_mismatch", report.read_text(encoding="utf-8"))
        self.assertIn("Old-occurrence diagnostic summary", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
