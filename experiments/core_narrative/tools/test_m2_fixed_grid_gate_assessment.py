#!/usr/bin/env python3
"""Executable specs for the M2 fixed-grid gate assessment."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_fixed_grid_gate_assessment as assess


class M2FixedGridGateAssessmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, relative: str, payload: dict[str, object]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def m2_summary(self) -> Path:
        return self.write_json(
            "m2-summary.json",
            {
                "paths": {
                    "patch_or_files_v1_live": {"clean_replay_disagreement_count": 0},
                    "patch_or_files_v1_no_model": {"clean_replay_disagreement_count": 0},
                }
            },
        )

    def row(
        self,
        *,
        contract: str,
        source_label: str,
        matrix_source: str,
        evidence_mode: str,
        acut_id: str,
        task_id: str,
        category: str,
        owner: str,
        failure_class: str | None,
        channel: str,
        model_call: bool,
        acquired_raw_input: bool = False,
    ) -> dict[str, object]:
        return {
            "contract": contract,
            "source_label": source_label,
            "matrix_source": matrix_source,
            "evidence_mode": evidence_mode,
            "acut_id": acut_id,
            "task_id": task_id,
            "run_id": f"{source_label}__{acut_id}__{task_id}",
            "stable_category": category,
            "stable_failure_owner": owner,
            "stable_failure_class": failure_class,
            "verifier_attempt_channel": channel,
            "historical_model_call_made": model_call,
            "new_model_call_made_for_this_package": acquired_raw_input,
            "acquired_raw_input": acquired_raw_input,
            "artifact_presence": {
                "normalized_result_exists": True,
                "raw_response_artifact_exists": category != "missing_raw_artifact",
                "prompt_snapshot_exists": True,
            },
            "response_shape": {
                "content_recorded": False,
                "contains_raw_url_like": False,
            },
            "content_recorded": False,
        }

    def matrix(self, *, unsafe_row: bool = False) -> Path:
        summary = self.m2_summary()
        cells = [
            {"acut_id": "cheap-generic-swe", "task_id": "click__rwork__003"},
            {"acut_id": "cheap-click-specialist", "task_id": "click__rwork__006"},
        ]
        rows: list[dict[str, object]] = [
            self.row(
                contract=assess.PATCH_OR_FILES_CONTRACT,
                source_label="patch_or_files_v1_live",
                matrix_source="patch_or_files_replay",
                evidence_mode="no_model_historical_replay",
                acut_id="cheap-generic-swe",
                task_id="click__rwork__003",
                category="model_output_invalid_submission",
                owner="model_output",
                failure_class="invalid_unified_diff",
                channel="not_attempted",
                model_call=True,
            ),
            self.row(
                contract=assess.PATCH_OR_FILES_CONTRACT,
                source_label="patch_or_files_v1_live",
                matrix_source="patch_or_files_replay",
                evidence_mode="no_model_historical_replay",
                acut_id="cheap-click-specialist",
                task_id="click__rwork__006",
                category="missing_raw_artifact",
                owner="infrastructure",
                failure_class="missing_raw_response_artifact",
                channel="not_attempted",
                model_call=True,
            ),
            self.row(
                contract=assess.PATCH_OR_FILES_CONTRACT,
                source_label="patch_or_files_gap_acquisition",
                matrix_source="patch_or_files_acquisition_batch",
                evidence_mode="fixed_grid_acquisition_live",
                acut_id="cheap-click-specialist",
                task_id="click__rwork__006",
                category="model_output_invalid_submission",
                owner="model_output",
                failure_class="unsafe_generated_text",
                channel="not_attempted",
                model_call=True,
                acquired_raw_input=True,
            ),
            self.row(
                contract=assess.PATCH_OR_FILES_CONTRACT,
                source_label="patch_or_files_v1_no_model",
                matrix_source="m2_scoreability_summary_existing_path",
                evidence_mode="existing_no_model_control",
                acut_id="cheap-generic-swe",
                task_id="click__rwork__003",
                category="verifier_ready_persisted_patch_artifact",
                owner="candidate_patch",
                failure_class=None,
                channel="verifier_ready_patch_artifact",
                model_call=False,
            ),
            self.row(
                contract=assess.PATCH_OR_FILES_CONTRACT,
                source_label="patch_or_files_v1_no_model",
                matrix_source="m2_scoreability_summary_existing_path",
                evidence_mode="existing_no_model_control",
                acut_id="cheap-click-specialist",
                task_id="click__rwork__006",
                category="verifier_ready_persisted_patch_artifact",
                owner="candidate_patch",
                failure_class=None,
                channel="verifier_ready_patch_artifact",
                model_call=False,
            ),
            self.row(
                contract=assess.ANCHORED_CONTRACT,
                source_label="fixed_grid_acquisition_generic",
                matrix_source="anchored_batch",
                evidence_mode="fixed_grid_acquisition_live",
                acut_id="cheap-generic-swe",
                task_id="click__rwork__003",
                category="nonpersistent_verifier_attempt",
                owner="candidate_patch",
                failure_class="unsafe_generated_text",
                channel="nonpersistent_preapplied_workspace",
                model_call=True,
                acquired_raw_input=True,
            ),
            self.row(
                contract=assess.ANCHORED_CONTRACT,
                source_label="fixed_grid_acquisition_specialist",
                matrix_source="anchored_batch",
                evidence_mode="fixed_grid_acquisition_live",
                acut_id="cheap-click-specialist",
                task_id="click__rwork__006",
                category="model_output_invalid_submission",
                owner="model_output",
                failure_class="search_replace_redacted_source_mismatch",
                channel="not_attempted",
                model_call=True,
                acquired_raw_input=True,
            ),
        ]
        if unsafe_row:
            rows[0]["content_recorded"] = True
            rows[0]["response_shape"] = {
                "content_recorded": True,
                "contains_raw_url_like": False,
            }
        return self.write_json(
            "matrix.json",
            {
                "tool": "m2_stable_nonpersistent_replay_matrix",
                "generated_at": "2026-05-10T00:00:00Z",
                "inputs": {"m2_summary": str(summary)},
                "scope": {
                    "m2_fixed_denominator": 2,
                    "fixed_denominators": {"patch_or_files_v1_no_model": 2},
                },
                "patch_or_files_gap_acquisition": {
                    "expected_live_fixed_denominator": 2,
                    "expected_cells": cells,
                    "historical_live_input_record_count": 2,
                    "historical_missing_raw_artifact_count": 1,
                    "acquisition_input_record_count": 1,
                    "acquired_raw_input_count": 1,
                    "remaining_missing_cell_count": 0,
                },
                "anchored_fixed_grid": {
                    "expected_fixed_denominator": 2,
                    "expected_cells": cells,
                    "input_record_count": 2,
                    "observed_unique_cell_count": 2,
                    "duplicate_input_record_count": 0,
                    "remaining_missing_cell_count": 0,
                },
                "cost_model_call_accounting": {
                    "acquisition": {
                        "input_record_count": 3,
                        "new_model_call_made_count": 3,
                        "provider_usage_cost_usd_observed_sum": 0.25,
                        "ledger_estimated_cost_usd_sum": 0.25,
                    }
                },
                "output_leakage_guard": {
                    "contains_raw_unsafe_text": False,
                    "reason_counts": {},
                },
                "matrix": rows,
            },
        )

    def build(self, matrix: Path) -> dict[str, object]:
        args = argparse.Namespace(
            matrix=str(matrix),
            output=str(self.root / "assessment.json"),
            report=str(self.root / "assessment.md"),
        )
        return assess.build_assessment(args)

    def test_assessment_closes_raw_gap_but_fails_live_scoreability_thresholds(self) -> None:
        """Fixed-grid coverage can pass while live scoreability remains blocked by model output."""
        payload = self.build(self.matrix())

        self.assertEqual(payload["schema_version"], assess.SCHEMA_VERSION)
        self.assertEqual(payload["coverage_and_policy_gate"]["gate_status"], "passed")
        self.assertEqual(payload["scoreability_gate_status"], "failed")
        fixed = payload["fixed_denominators"]
        self.assertEqual(fixed["patch_or_files_historical_missing_raw_artifacts_preserved"], 1)
        self.assertEqual(fixed["patch_or_files_remaining_raw_input_gaps_after_acquisition"], 0)

        patch = payload["path_assessments"]["patch_or_files_v1_live_after_gap_closure"]
        self.assertEqual(patch["fixed_denominator"], 2)
        self.assertEqual(patch["attemptable_cell_count"], 0)
        self.assertEqual(patch["model_output_invalid_submission_rate"], 1.0)
        self.assertEqual(patch["failure_class_counts"], {"invalid_unified_diff": 1, "unsafe_generated_text": 1})
        self.assertEqual(len(patch["exact_cell_blockers"]), 2)
        self.assertTrue(patch["selected_cells"][1]["historical_missing_raw_artifact_preserved"])

        anchored = payload["path_assessments"]["anchored_search_replace_fixed_grid"]
        self.assertEqual(anchored["attemptability_channel_counts"]["nonpersistent_preapplied_workspace"], 1)
        self.assertEqual(anchored["exact_cell_blockers"][0]["failure_class"], "search_replace_redacted_source_mismatch")

        hard = payload["hard_blocker_summary"]
        self.assertEqual(hard["status"], "hard_blocked_for_m2_pass_or_predictivity_claims")
        self.assertFalse(hard["code_addressable_blocker_identified"])
        self.assertIsNone(hard["next_code_addressable_blocker"])
        self.assertEqual(payload["cost_model_call_accounting"]["assessment_generation"]["new_model_call_made_count"], 0)
        self.assertFalse(payload["claim_boundaries"]["m2_passed"])

    def test_no_raw_unsafe_policy_violation_blocks_coverage_gate(self) -> None:
        """Raw-text policy violations are surfaced as machine-readable gate failures."""
        payload = self.build(self.matrix(unsafe_row=True))

        policy = payload["no_raw_unsafe_policy_status"]
        self.assertEqual(policy["status"], "failed")
        self.assertEqual(policy["row_policy_violation_count"], 1)
        self.assertEqual(payload["coverage_and_policy_gate"]["gate_status"], "blocked")
        self.assertEqual(payload["scoreability_gate_status"], "blocked")

    def test_report_names_exact_blockers_and_claim_boundaries(self) -> None:
        """The Markdown report keeps blockers concrete and avoids capability claims."""
        matrix = self.matrix()
        output = self.root / "assessment.json"
        report = self.root / "assessment.md"
        with contextlib.redirect_stdout(io.StringIO()):
            code = assess.main(["--matrix", str(matrix), "--output", str(output), "--report", str(report)])
        self.assertEqual(code, 0)

        text = report.read_text(encoding="utf-8")
        self.assertIn("cheap-click-specialist` / `click__rwork__006", text)
        self.assertIn("Assessment model calls: `0`", text)
        self.assertIn("This report does not claim M2 passed", text)


if __name__ == "__main__":
    unittest.main()
