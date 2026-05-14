#!/usr/bin/env python3
"""Executable specs for Rich ACUT intervention readiness manifests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import _common


REPO_ROOT = Path(__file__).resolve().parents[3]


class RichAcutInterventionReadinessTests(unittest.TestCase):
    def test_rich_repository_acut_manifests_freeze_intervention_boundaries(self) -> None:
        """Rich A1-A4 variants remain Rich-specific and free of W*/ACUT-output leakage."""
        config = _common.load_manifest(REPO_ROOT / "experiments/core_narrative/configs/repository_local_benchmark_20260514.yaml")
        acuts = config["acuts"]
        expected = {
            "A1_inert_control": "cheap-rich-inert-control-v1",
            "A2_static_repo_context": "cheap-rich-static-context-v1",
            "A3_c_derived_repo_calibrated_playbook": "cheap-rich-c-calibrated-v1",
            "A4_code_understanding_localization_tool": "cheap-rich-localization-tool-v1",
        }

        loaded = {}
        for label, acut_id in expected.items():
            manifest_path = REPO_ROOT / acuts[label]["manifest"]
            manifest = _common.load_manifest(manifest_path)
            loaded[label] = manifest

            self.assertEqual(manifest["acut_id"], acut_id)
            self.assertFalse(manifest["metadata"]["calibration_basis"]["uses_W_star_tasks"])
            self.assertFalse(manifest["metadata"]["calibration_basis"]["uses_acut_outputs"])

        a3_basis = loaded["A3_c_derived_repo_calibrated_playbook"]["metadata"]["calibration_basis"]
        self.assertTrue(a3_basis["uses_C_tasks"])
        self.assertTrue(a3_basis["uses_C_tasks_as_abstract_calibration"])
        self.assertFalse(a3_basis["uses_raw_C_commits_or_subjects"])
        self.assertFalse(a3_basis["uses_C_reference_patch_text"])

        a4 = loaded["A4_code_understanding_localization_tool"]
        self.assertIn("repository_localization_hints", a4["tool_permissions"]["allowed_tools"])
        tool_policy = a4["metadata"]["localization_tool"]
        self.assertFalse(tool_policy["uses_reference_patch"])
        self.assertFalse(tool_policy["uses_target_diff"])
        self.assertFalse(tool_policy["uses_hidden_verifier"])
        self.assertFalse(tool_policy["uses_target_commit"])

    def test_readiness_artifact_records_no_model_calls_or_primary_authorization(self) -> None:
        """The Rich ACUT readiness artifact is diagnostic only, not a run authorization."""
        payload = json.loads(
            (REPO_ROOT / "experiments/core_narrative/results/rich_acut_intervention_readiness_20260515.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["model_calls_made"], 0)
        self.assertFalse(payload["primary_runs_authorized"])
        labels = {item["label"] for item in payload["interventions"]}
        self.assertEqual(
            labels,
            {
                "A0_generic_baseline",
                "A1_inert_control",
                "A2_static_repo_context",
                "A3_c_derived_repo_calibrated_playbook",
                "A4_code_understanding_localization_tool",
                "A5_frontier_generic_reference",
            },
        )


if __name__ == "__main__":
    unittest.main()
