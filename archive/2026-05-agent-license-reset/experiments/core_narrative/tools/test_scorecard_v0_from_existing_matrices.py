#!/usr/bin/env python3
"""Executable specs for Scorecard v0 from existing evidence matrices."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import scorecard_v0_from_existing_matrices as scorecard


class ScorecardV0FromExistingMatricesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def matrix(
        self,
        *,
        split: str,
        acuts: tuple[str, ...] = ("cheap-generic-swe", "cheap-click-specialist"),
        tasks: tuple[str, ...] = ("task-1", "task-2"),
        latest_by_cell: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        cells: dict[str, Any] = {}
        status_counts: dict[str, int] = {}
        failure_label_counts: dict[str, int] = {}
        missing: list[dict[str, str]] = []
        for acut_id in acuts:
            for task_id in tasks:
                latest = latest_by_cell.get((acut_id, task_id))
                if latest is None:
                    missing.append({"acut_id": acut_id, "task_id": task_id})
                else:
                    status = str(latest["status"])
                    label = str(latest.get("failure_label") or status)
                    status_counts[status] = status_counts.get(status, 0) + 1
                    failure_label_counts[label] = failure_label_counts.get(label, 0) + 1
                cells[f"{acut_id}::{task_id}"] = {
                    "acut_id": acut_id,
                    "task_id": task_id,
                    "canonical_latest": latest,
                }
        return {
            "tool": "codex_nfl_canonical_matrix",
            "status": "completed",
            "split": split,
            "task_ids": list(tasks),
            "acut_ids": list(acuts),
            "matrix_shape": {"acuts": len(acuts), "tasks": len(tasks), "expected_cells": len(acuts) * len(tasks)},
            "missing": {"attempt2_cells": [], "canonical_cells": missing},
            "status_counts_canonical": status_counts,
            "failure_label_counts_canonical": failure_label_counts,
            "by_acut": {},
            "cells": cells,
        }

    def build(self, **paths: Path | None) -> dict[str, Any]:
        return scorecard.build_scorecard(
            {
                "rbench_canonical_matrix": paths.get("rbench"),
                "rwork_canonical_matrix": paths.get("rwork"),
                "measurement_stabilization_m1_1_summary": paths.get("m1"),
                "m2_scoreability_summary": paths.get("m2"),
                "unsafe_generated_text_triage": paths.get("unsafe"),
                "gscore_gold_patch_smoke": paths.get("gscore"),
            }
        )

    def test_fixed_denominators_include_missing_canonical_cells(self) -> None:
        """Missing canonical cells stay in the fixed denominator instead of disappearing."""
        rbench = self.write_json(
            "rbench.json",
            self.matrix(
                split="rbench",
                latest_by_cell={
                    ("cheap-generic-swe", "task-1"): {"status": "passed", "failure_label": "passed"},
                    ("cheap-generic-swe", "task-2"): {"status": "failed", "failure_label": "failed"},
                    ("cheap-click-specialist", "task-1"): {
                        "status": "invalid_submission",
                        "failure_label": "invalid_submission:search_replace_anchor_mismatch",
                    },
                },
            ),
        )

        payload = self.build(rbench=rbench)

        split = payload["fixed_denominators"]["canonical_matrices"]["by_split"]["rbench"]
        self.assertEqual(split["expected_cells"], 4)
        self.assertEqual(split["canonical_present"], 3)
        self.assertEqual(split["canonical_missing"], 1)
        counts = payload["outcome_counts"]["canonical_matrices"]["by_split"]["rbench"]
        self.assertEqual(counts["passed"], 1)
        self.assertEqual(counts["failed"], 1)
        self.assertEqual(counts["invalid_submission"], 1)
        self.assertEqual(counts["missing"], 1)
        self.assertEqual(payload["rates"]["canonical_matrices"]["by_split"]["rbench"]["pass_rate_fixed_denominator"], 0.25)

    def test_score_input_set_digest_is_stable_for_same_evidence(self) -> None:
        """Score input identity excludes generated_at and remains stable across builds."""
        rwork = self.write_json(
            "rwork.json",
            self.matrix(
                split="rwork",
                latest_by_cell={
                    ("cheap-generic-swe", "task-1"): {"status": "passed", "failure_label": "passed"},
                    ("cheap-click-specialist", "task-2"): {
                        "status": "invalid_submission",
                        "failure_label": "invalid_submission:unsupported_patch_response",
                    },
                },
            ),
        )

        first = self.build(rwork=rwork)
        second = self.build(rwork=rwork)

        self.assertEqual(first["score_input_set_digest"], second["score_input_set_digest"])
        self.assertEqual(first["evidence_input_set_digest"], second["evidence_input_set_digest"])

    def test_missing_gscore_smoke_keeps_gscore_unavailable_without_proxy(self) -> None:
        """Absent G-score smoke evidence is unavailable, not zero-filled or proxied."""
        payload = self.build(gscore=self.root / "missing-gscore.json")

        g_score = payload["g_score"]
        self.assertEqual(g_score["availability_status"], "unavailable_missing_evidence")
        self.assertFalse(g_score["available"])
        self.assertTrue(g_score["blocked"])
        self.assertFalse(g_score["public_leaderboard_proxy_used"])
        self.assertEqual(g_score["proxy_status"], "not_proxy")
        self.assertNotIn("acut_scores", g_score)

    def test_failure_owner_and_class_aggregation_from_matrices(self) -> None:
        """Scorecard v0 derives coarse owner/class distributions from canonical labels."""
        matrix = self.write_json(
            "rbench.json",
            self.matrix(
                split="rbench",
                latest_by_cell={
                    ("cheap-generic-swe", "task-1"): {"status": "passed", "failure_label": "passed"},
                    ("cheap-generic-swe", "task-2"): {"status": "failed", "failure_label": "failed"},
                    ("cheap-click-specialist", "task-1"): {
                        "status": "invalid_submission",
                        "failure_label": "invalid_submission:search_replace_old_occurrence_mismatch",
                    },
                    ("cheap-click-specialist", "task-2"): {
                        "status": "infra_failed",
                        "failure_label": "infra_failed:runner_adapter_failed",
                    },
                },
            ),
        )

        payload = self.build(rbench=matrix)

        owners = payload["failure_distributions"]["canonical_matrices"]["failure_owner_counts"]
        self.assertEqual(owners["none"], 1)
        self.assertEqual(owners["candidate_patch"], 1)
        self.assertEqual(owners["model_output"], 1)
        self.assertEqual(owners["infrastructure"], 1)
        classes = payload["failure_distributions"]["canonical_matrices"]["failure_class_counts"]
        self.assertEqual(classes["none"], 1)
        self.assertEqual(classes["unclassified_verifier_failure"], 1)
        self.assertEqual(classes["search_replace_old_occurrence_mismatch"], 1)
        self.assertEqual(classes["runner_adapter_failed"], 1)

    def test_m2_and_unsafe_triage_are_preserved_as_scoreability_not_capability(self) -> None:
        """M2 gates and unsafe triage remain scoreability evidence with bounded claims."""
        m2 = self.write_json(
            "m2.json",
            {
                "tool": "m2_scoreability_summary",
                "status": "completed",
                "fixed_denominator": 2,
                "evidence_inputs": {
                    "structured_live": {"contract": "structured-files-json-v1", "kind": "batch", "path": "structured.json"}
                },
                "claim_status": "scoreability_gate_not_met",
                "paths": {
                    "structured_live": {
                        "total": 2,
                        "status_counts": {"failed": 1, "invalid_submission": 1},
                        "failure_owner_counts": {"candidate_patch": 1, "model_output": 1},
                        "failure_class_counts": {"none": 1, "unsafe_generated_text": 1},
                        "patch_ready_coverage": 0.5,
                        "invalid_submission_rate": 0.5,
                        "missing_cell_count": 0,
                        "blocked_cell_count": 0,
                        "excluded_row_count": 0,
                        "model_call_made_counts": {"true": 2, "false": 0, "unknown": 0},
                        "gate": {"status": "failed", "checks": {"patch_ready_coverage": False}},
                    }
                },
                "prohibited_claims": {
                    "capability_uplift": False,
                    "task_solving_improvement": False,
                    "ranking_reversal": False,
                    "g_score_predictivity": False,
                },
            },
        )
        unsafe = self.write_json(
            "unsafe.json",
            {
                "tool": "unsafe_generated_text_triage",
                "schema_version": "unsafe-generated-text-triage.v1",
                "model_or_api_budget_spent": False,
                "fixed_denominator": {"total": 2, "present_cell_count": 2, "missing_cell_count": 0},
                "summary": {
                    "classification_counts": {"prompt_or_applicator_overbreadth": 2},
                    "enough_redacted_evidence_count": 2,
                    "reason_counts_total": {"full_url": 3},
                },
                "output_leakage_guard": {"contains_raw_unsafe_text": False, "reason_counts": {}},
            },
        )

        payload = self.build(m2=m2, unsafe=unsafe)

        m2_summary = payload["contract_scoreability"]["m2"]
        self.assertEqual(m2_summary["claim_status"], "scoreability_gate_not_met")
        self.assertEqual(m2_summary["paths"]["structured_live"]["gate_status"], "failed")
        self.assertEqual(m2_summary["paths"]["structured_live"]["contract"], "structured-files-json-v1")
        self.assertEqual(
            payload["unsafe_generated_text"]["summary"]["classification_counts"],
            {"prompt_or_applicator_overbreadth": 2},
        )
        self.assertFalse(payload["claim_boundaries"]["prohibited_claims"]["capability_uplift"])
        self.assertFalse(payload["claim_boundaries"]["prohibited_claims"]["g_score_predictivity"])

    def test_no_authorization_or_tier_claims_are_emitted(self) -> None:
        """The scorecard is diagnostic input, not a license or admission decision."""
        payload = self.build()
        serialized = json.dumps(payload, sort_keys=True)

        for tier in ("G0", "G1", "G2", "G3", "G4", "G5"):
            self.assertNotIn(tier, serialized)
        keys = set(scorecard.flatten_keys(payload))
        self.assertNotIn("authorization_decision", keys)
        self.assertNotIn("license_decision", keys)
        self.assertNotIn("admission_decision", keys)
        self.assertTrue(payload["not_authorization"]["not_authorization"])
        self.assertFalse(payload["not_authorization"]["emits_license_or_admission_output"])


if __name__ == "__main__":
    unittest.main()
