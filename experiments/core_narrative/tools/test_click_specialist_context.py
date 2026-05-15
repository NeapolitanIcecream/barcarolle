#!/usr/bin/env python3
"""Executable specs for specialist context-pack loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from _common import load_manifest
from click_specialist_context import load_click_specialist_context, prompt_injection_evidence


REPO_ROOT = Path(__file__).resolve().parents[3]


class SpecialistContextTests(unittest.TestCase):
    def test_rich_c_calibrated_context_pack_loads_with_rich_section_markers(self) -> None:
        """Rich ACUTs may declare task-agnostic specialist context packs."""
        acut_path = REPO_ROOT / "experiments/core_narrative/configs/acuts/cheap-rich-c-calibrated-v1.yaml"
        acut = load_manifest(acut_path)

        prompt_text, evidence = load_click_specialist_context(acut, acut_path)
        prompt_evidence = prompt_injection_evidence(prompt_text, evidence)

        self.assertIn("RICH_C_CALIBRATED_CONTEXT_PACK_V1", prompt_text)
        self.assertEqual(evidence["section_marker_prefix"], "RICH")
        self.assertIn("rich_c_calibrated_context_allowed", evidence["allowed_flags"])
        self.assertTrue(all(evidence["section_markers_present_in_context"].values()))
        self.assertTrue(prompt_evidence["prompt_checks"]["all_expected_sections_present"])

    def test_generic_acut_without_context_pack_remains_disabled(self) -> None:
        """Generic ACUTs without context packs keep the no-context prompt path."""
        acut_path = REPO_ROOT / "experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml"
        acut = load_manifest(acut_path)

        prompt_text, evidence = load_click_specialist_context(acut, acut_path)

        self.assertEqual(prompt_text, "")
        self.assertFalse(evidence["enabled"])


if __name__ == "__main__":
    unittest.main()
