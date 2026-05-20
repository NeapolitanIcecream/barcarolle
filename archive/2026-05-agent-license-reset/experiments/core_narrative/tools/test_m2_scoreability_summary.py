#!/usr/bin/env python3
"""Executable specs for M2 scoreability-first summaries."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_scoreability_summary as summary


class M2ScoreabilitySummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def run_summary(self, *evidence_args: str) -> dict[str, object]:
        output = self.root / "summary.json"
        code = summary.main(
            [
                "--tasks",
                "click__rwork__003",
                "click__rwork__004",
                "--acuts",
                "cheap-generic-swe",
                "cheap-click-specialist",
                *evidence_args,
                "--output",
                str(output),
            ]
        )
        self.assertEqual(code, 0)
        return json.loads(output.read_text(encoding="utf-8"))

    def result(
        self,
        *,
        acut: str,
        task: str,
        contract: str,
        status: str,
        patch_ready: bool,
        model_call_made: bool,
    ) -> dict[str, object]:
        return {
            "run_id": f"unit__{acut}__{task}",
            "acut_id": acut,
            "task_id": task,
            "status": status,
            "submission_contract": contract,
            "output_contract": contract,
            "patch_ready": patch_ready,
            "normalized": {
                "status": status,
                "verification": {"exit_code": 1 if status == "failed" else 0 if status == "passed" else None},
                "metadata": {
                    "submission_contract": contract,
                    "output_contract": contract,
                    "failure_owner": "candidate_patch" if status in {"failed", "timeout"} else "none",
                    "model_call_made": model_call_made,
                    "patch_readiness": {
                        "verifier_ready_patch_available": patch_ready,
                        "clean_replay_attempted": patch_ready,
                    },
                    "clean_patch_replay": {"attempted": patch_ready},
                },
            },
            "runner_result": {
                "submission_contract": contract,
                "output_contract": contract,
                "model_call_made": model_call_made,
            },
        }

    def test_multi_path_summaries_keep_fixed_denominators_and_gate_metrics(self) -> None:
        """Each submission path is measured on the full ACUT x task denominator."""
        structured = self.write_json(
            "structured.json",
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__003",
                        contract="structured-files-json-v1",
                        status="failed",
                        patch_ready=True,
                        model_call_made=True,
                    )
                ]
            },
        )
        patch_or_files = self.write_json(
            "patch-or-files.json",
            {
                "results": [
                    self.result(
                        acut=acut,
                        task=task,
                        contract="patch-or-files-v1",
                        status="failed",
                        patch_ready=True,
                        model_call_made=True,
                    )
                    for acut in ("cheap-generic-swe", "cheap-click-specialist")
                    for task in ("click__rwork__003", "click__rwork__004")
                ]
            },
        )

        payload = self.run_summary(
            "--evidence",
            "structured_live",
            "structured-files-json-v1",
            "batch",
            str(structured),
            "--evidence",
            "patch_or_files_live",
            "patch-or-files-v1",
            "batch",
            str(patch_or_files),
        )

        structured_summary = payload["paths"]["structured_live"]
        self.assertEqual(structured_summary["total"], 4)
        self.assertEqual(structured_summary["missing_cell_count"], 3)
        self.assertEqual(structured_summary["patch_ready_coverage"], 0.25)
        self.assertEqual(structured_summary["gate"]["status"], "incomplete")

        patch_summary = payload["paths"]["patch_or_files_live"]
        self.assertEqual(patch_summary["total"], 4)
        self.assertEqual(patch_summary["patch_ready_coverage"], 1.0)
        self.assertEqual(patch_summary["invalid_submission_rate"], 0.0)
        self.assertEqual(patch_summary["clean_replay_disagreement_count"], 0)
        self.assertEqual(patch_summary["gate"]["status"], "passed")

    def test_wrong_contract_rows_are_excluded_and_reported_as_missing_cells(self) -> None:
        """Rows with mismatched contract markers must not fill the fixed denominator."""
        batch = self.write_json(
            "mixed.json",
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__003",
                        contract="structured-files-json-v1",
                        status="passed",
                        patch_ready=True,
                        model_call_made=True,
                    )
                ]
            },
        )

        payload = self.run_summary(
            "--evidence",
            "patch_or_files_live",
            "patch-or-files-v1",
            "batch",
            str(batch),
        )

        path = payload["paths"]["patch_or_files_live"]
        self.assertEqual(path["total"], 4)
        self.assertEqual(path["excluded_row_count"], 1)
        self.assertEqual(path["excluded_rows"][0]["reason"], "wrong_or_missing_contract")
        self.assertEqual(path["status_counts"], {"missing": 4})

    def test_blocker_path_records_blocked_cells_without_model_calls(self) -> None:
        """Budget or provider blockers are auditable evidence, not fabricated batch data."""
        blocker = self.write_json(
            "blocker.json",
            {
                "status": "blocked",
                "blockers": ["budget_gate_requires_coordinator_approval"],
                "model_call_made": False,
            },
        )

        payload = self.run_summary(
            "--evidence",
            "patch_or_files_live",
            "patch-or-files-v1",
            "blocker",
            str(blocker),
        )

        path = payload["paths"]["patch_or_files_live"]
        self.assertEqual(path["status_counts"], {"blocked": 4})
        self.assertEqual(path["blocked_cell_count"], 4)
        self.assertEqual(path["model_call_made_counts"], {"false": 4, "true": 0, "unknown": 0})
        self.assertEqual(path["gate"]["status"], "blocked")
        self.assertEqual(payload["claim_status"], "blocked")

    def test_claim_wording_stays_bounded_to_scoreability(self) -> None:
        """M2 summaries must not silently become capability or ranking claims."""
        batch = self.write_json(
            "batch.json",
            {
                "results": [
                    {
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "invalid_submission",
                        "submission_contract": "structured-files-json-v1",
                        "output_contract": "structured-files-json-v1",
                        "normalized": {
                            "metadata": {
                                "submission_contract": "structured-files-json-v1",
                                "output_contract": "structured-files-json-v1",
                                "failure_owner": "model_output",
                                "failure_class": "unsafe_generated_text",
                                "model_call_made": True,
                            }
                        },
                    }
                ]
            },
        )

        payload = self.run_summary(
            "--evidence",
            "structured_live",
            "structured-files-json-v1",
            "batch",
            str(batch),
        )

        wording = payload["claim_wording"]
        self.assertIn("measurement-readiness evidence only", wording)
        self.assertIn("no capability uplift claim", wording)
        self.assertIn("no ranking reversal claim", wording)
        self.assertFalse(payload["prohibited_claims"]["capability_uplift"])
        self.assertFalse(payload["prohibited_claims"]["ranking_reversal"])


if __name__ == "__main__":
    unittest.main()
