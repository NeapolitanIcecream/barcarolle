#!/usr/bin/env python3
"""Executable specs for external calibrated Codex route preflight."""

from __future__ import annotations

import unittest
from pathlib import Path

import external_calibrated_route_preflight as preflight


class ExternalCalibratedRoutePreflightTests(unittest.TestCase):
    def test_route_specs_deduplicate_model_effort_verbosity_routes(self) -> None:
        payload = {
            "profiles": [
                {
                    "acut_id": "a2",
                    "model": "gpt-5.4",
                    "model_parameters": {"reasoning_effort": "high", "model_verbosity": "low"},
                    "metadata": {"slot": "A2"},
                },
                {
                    "acut_id": "a5",
                    "model": "gpt-5.4",
                    "model_parameters": {"reasoning_effort": "high", "model_verbosity": "low"},
                    "metadata": {"slot": "A5"},
                },
                {
                    "acut_id": "a3",
                    "model": "gpt-5.5",
                    "model_parameters": {"reasoning_effort": "high", "model_verbosity": "low"},
                    "metadata": {"slot": "A3"},
                },
            ]
        }

        routes = preflight.route_specs_from_profiles(payload)

        self.assertEqual(len(routes), 2)
        self.assertEqual(routes[0]["example_slot"], "A2")
        self.assertEqual(routes[1]["model"], "gpt-5.5")

    def test_build_codex_command_uses_read_only_synthetic_route_prompt(self) -> None:
        command = preflight.build_codex_command(
            codex_bin="codex",
            workspace=Path("/tmp/route"),
            model="gpt-5.4",
            reasoning_effort="low",
            model_verbosity="low",
            output_last_message=Path("/tmp/out.txt"),
        )

        self.assertIn("--sandbox", command)
        self.assertIn("read-only", command)
        self.assertIn('model_reasoning_effort="low"', command)
        self.assertIn('model_verbosity="low"', command)
        self.assertIn("Return exactly ROUTE_OK", command[-1])

    def test_build_payload_blocks_failed_live_route(self) -> None:
        payload = preflight.build_payload(
            {"status": "acut_profiles_frozen"},
            [{"route_id": "gpt-5.4-high-low", "status": "failed", "model_call_made": True}],
            mode="live",
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("route_preflight_failed", payload["blockers"])


if __name__ == "__main__":
    unittest.main()
