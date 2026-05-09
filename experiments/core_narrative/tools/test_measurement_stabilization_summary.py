#!/usr/bin/env python3
"""Executable specs for M1 measurement-stabilization summaries."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import measurement_stabilization_summary as summary


class MeasurementStabilizationSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_structured_contract_improvement_is_supported_when_invalid_drops_and_patch_ready_rises(self) -> None:
        """The summary compares invalid submissions against verifier-ready coverage by contract."""
        anchored = self.write_json(
            "anchored.json",
            {
                "cells": {
                    "cheap-generic-swe::click__rwork__003": {
                        "canonical_latest": {
                            "status": "invalid_submission",
                            "failure_label": "invalid_submission:search_replace_old_occurrence_mismatch",
                            "path": "anchored-003.json",
                        }
                    },
                    "cheap-click-specialist::click__rwork__003": {
                        "canonical_latest": {
                            "status": "passed",
                            "failure_label": "passed",
                            "path": "anchored-003-specialist.json",
                        }
                    },
                }
            },
        )
        structured = self.write_json(
            "structured.json",
            {
                "results": [
                    {
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__003",
                        "status": "failed",
                        "submission_contract": "structured-files-json-v1",
                        "normalized_result": "structured-generic.json",
                        "normalized": {
                            "metadata": {
                                "submission_contract": "structured-files-json-v1",
                                "failure_owner": "candidate_patch",
                                "model_call_made": True,
                                "patch_readiness": {"verifier_ready_patch_available": True},
                            }
                        },
                    },
                    {
                        "acut_id": "cheap-click-specialist",
                        "task_id": "click__rwork__003",
                        "status": "passed",
                        "submission_contract": "structured-files-json-v1",
                        "normalized_result": "structured-specialist.json",
                        "normalized": {
                            "metadata": {
                                "submission_contract": "structured-files-json-v1",
                                "failure_owner": "none",
                                "model_call_made": True,
                                "patch_readiness": {"verifier_ready_patch_available": True},
                            }
                        },
                    },
                ]
            },
        )
        output = self.root / "summary.json"

        code = summary.main(
            [
                "--anchored-baseline",
                str(anchored),
                "--structured-batch",
                str(structured),
                "--tasks",
                "click__rwork__003",
                "--acuts",
                "cheap-generic-swe",
                "cheap-click-specialist",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["claim_status"], "supported")
        self.assertEqual(
            payload["contracts"]["anchored-search-replace-json-v3"]["failure_class_counts"],
            {"none": 1, "search_replace_old_occurrence_mismatch": 1},
        )
        self.assertEqual(payload["contracts"]["structured-files-json-v1"]["patch_ready_coverage"], 1.0)
        self.assertEqual(payload["effect"]["invalid_submission_rate_delta_structured_minus_anchored"], -0.5)

    def test_blocker_marks_claim_blocked_without_structured_batch(self) -> None:
        """A live gate/provider blocker should produce an auditable blocked summary."""
        anchored = self.write_json("anchored.json", {"cells": {}})
        blocker = self.write_json(
            "blocker.json",
            {
                "status": "blocked",
                "blockers": ["missing_required_llm_environment"],
                "model_call_made": False,
            },
        )
        output = self.root / "summary.json"

        code = summary.main(
            [
                "--anchored-baseline",
                str(anchored),
                "--blocker",
                str(blocker),
                "--tasks",
                "click__rwork__003",
                "--acuts",
                "cheap-generic-swe",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["claim_status"], "blocked")
        self.assertEqual(payload["blocker"]["blockers"], ["missing_required_llm_environment"])

    def test_unsafe_zero_patch_is_counted_as_model_output_invalid_submission(self) -> None:
        """Regression: refused unsafe patch artifacts are contract failures, not infra coverage."""
        anchored = self.write_json("anchored.json", {"cells": {}})
        structured = self.write_json(
            "structured.json",
            {
                "results": [
                    {
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__004",
                        "status": "infra_failed",
                        "submission_contract": "structured-files-json-v1",
                        "normalized": {
                            "metadata": {
                                "submission_contract": "structured-files-json-v1",
                                "failure_owner": "infrastructure",
                                "model_call_made": True,
                            }
                        },
                        "runner_result": {
                            "patch_artifact": {
                                "unsafe_content_detected": True,
                                "unsafe_content": {"reason_counts": {"full_url": 1}},
                            }
                        },
                    }
                ]
            },
        )
        output = self.root / "summary.json"

        code = summary.main(
            [
                "--anchored-baseline",
                str(anchored),
                "--structured-batch",
                str(structured),
                "--tasks",
                "click__rwork__004",
                "--acuts",
                "cheap-generic-swe",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        contract = payload["contracts"]["structured-files-json-v1"]
        self.assertEqual(contract["status_counts"], {"invalid_submission": 1})
        self.assertEqual(contract["failure_class_counts"], {"unsafe_generated_text": 1})
        self.assertEqual(contract["failure_owner_counts"], {"model_output": 1})


if __name__ == "__main__":
    unittest.main()
