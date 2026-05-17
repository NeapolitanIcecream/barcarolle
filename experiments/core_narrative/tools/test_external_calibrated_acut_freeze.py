#!/usr/bin/env python3
"""Executable specs for external calibrated ACUT freeze artifacts."""

from __future__ import annotations

import unittest

import external_calibrated_acut_freeze as freeze


class ExternalCalibratedAcutFreezeTests(unittest.TestCase):
    def test_acut_specs_freeze_primary_protocol_set_without_custom_tools(self) -> None:
        specs = freeze.acut_specs()

        self.assertEqual([spec["slot"] for spec in specs], ["A0", "A1", "A2", "A3", "A4", "A5"])
        self.assertEqual({spec["model"] for spec in specs}, {"gpt-5.4", "gpt-5.5", "gpt-5.4-mini"})
        self.assertEqual(specs[3]["model"], "gpt-5.5")
        self.assertEqual(specs[5]["agents_md_profile"], "rich")

    def test_build_profile_disables_network_and_custom_primary_tools(self) -> None:
        spec = freeze.acut_specs()[0]
        profile = freeze.build_profile(
            spec,
            frozen_at="2026-05-16T00:00:00Z",
            codex_version="codex-cli 0.test",
            model_available=True,
            profile_dir=freeze.DEFAULT_PROFILE_DIR,
        )

        self.assertTrue(profile["frozen"])
        self.assertEqual(profile["network_policy"]["mode"], "disabled")
        self.assertFalse(profile["tool_permissions"]["custom_localization_or_retrieval_tool_allowed"])
        self.assertEqual(profile["runtime_budget"]["retry_policy"]["primary_attempts"], 1)
        self.assertFalse(profile["runtime_budget"]["retry_policy"]["best_of_n"])

    def test_run_cells_cross_product_acuts_and_tasks(self) -> None:
        cells = freeze.run_cells(
            freeze.acut_specs()[:2],
            [{"task_id": "t1", "ordinal": 1}, {"task_id": "t2", "ordinal": 2}],
            phase="e",
        )

        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[0]["attempt"], 1)
        self.assertEqual(cells[0]["network_policy"], "disabled")
        self.assertEqual(cells[0]["status"], "not_started")

    def test_build_payload_blocks_when_protocol_not_ready(self) -> None:
        payload = freeze.build_payload(
            {"status": "phase0"},
            {
                "tasks": [
                    {"instance_id": f"e-{index}", "ordinal": index, "smoke_status": "gold_resolved"}
                    for index in range(1, 31)
                ]
            },
            {
                "tasks": [
                    {"task_id": f"b-{index}", "ordinal": index}
                    for index in range(1, 21)
                ]
            },
            codex_version_override="codex-cli 0.test",
            available_models_override={"gpt-5.4", "gpt-5.5", "gpt-5.4-mini"},
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("protocol_not_ready_for_acut_profile_freeze", payload["blockers"])

    def test_build_payload_allows_idempotent_regeneration_after_profiles_are_frozen(self) -> None:
        payload = freeze.build_payload(
            {"status": "phase2_e_acut_profiles_frozen_route_preflight_pending"},
            {
                "tasks": [
                    {"instance_id": f"e-{index}", "ordinal": index, "smoke_status": "gold_resolved"}
                    for index in range(1, 31)
                ]
            },
            {
                "tasks": [
                    {"task_id": f"b-{index}", "ordinal": index}
                    for index in range(1, 21)
                ]
            },
            codex_version_override="codex-cli 0.test",
            available_models_override={"gpt-5.4", "gpt-5.5", "gpt-5.4-mini"},
        )

        self.assertEqual(payload["status"], "acut_profiles_frozen")
        self.assertEqual(payload["phase2_e_cell_count"], 180)


if __name__ == "__main__":
    unittest.main()
