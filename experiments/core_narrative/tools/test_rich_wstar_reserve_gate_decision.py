#!/usr/bin/env python3
"""Executable specs for Rich W* reserve-gate decisions."""

from __future__ import annotations

import unittest
from pathlib import Path

import rich_wstar_reserve_gate_decision as gate


class RichWstarReserveGateDecisionTests(unittest.TestCase):
    def feasibility(self) -> dict[str, object]:
        return {
            "schema_version": "core-narrative.rich-wstar-reserve-feasibility.v1",
            "accepted_w_star_primary_count": 20,
            "target_primary_count": 20,
            "target_reserve_count": 5,
            "target_primary_plus_reserve_count": 25,
            "remaining_unadmitted_w_star_design_candidates": 3,
            "maximum_possible_w_star_admissions_under_current_scan": 23,
            "candidate_pool_gap": 17,
        }

    def test_primary_floor_without_reserve_keeps_primary_runs_unauthorized(self) -> None:
        """Reaching 20 W* tasks is insufficient when reserve and pool gates still fail."""
        payload = gate.build_payload(self.feasibility(), Path("/repo/results/rich_wstar_reserve_feasibility_20260514.json"))

        self.assertEqual(payload["decision"], "w_star_primary_reached_but_reserve_and_pool_gates_failed")
        self.assertTrue(payload["primary_floor_reached"])
        self.assertFalse(payload["reserve_gate_reached"])
        self.assertFalse(payload["candidate_pool_gate_reached"])
        self.assertFalse(payload["primary_runs_authorized"])
        self.assertFalse(payload["authorization"]["run_w_star_primary"])
        self.assertEqual(payload["reserve_gap_even_if_all_remaining_admitted"], 2)

    def test_full_wstar_gate_still_requires_separate_run_manifest_authorization(self) -> None:
        """A passing reserve gate records feasibility but does not itself start primary runs."""
        feasibility = self.feasibility()
        feasibility["remaining_unadmitted_w_star_design_candidates"] = 5
        feasibility["maximum_possible_w_star_admissions_under_current_scan"] = 25
        feasibility["candidate_pool_gap"] = 0

        payload = gate.build_payload(feasibility, Path("/repo/results/rich_wstar_reserve_feasibility_20260514.json"))

        self.assertEqual(payload["decision"], "w_star_full_gate_passed_requires_separate_run_manifest")
        self.assertTrue(payload["reserve_gate_reached"])
        self.assertTrue(payload["candidate_pool_gate_reached"])
        self.assertTrue(payload["full_gate_reached"])
        self.assertFalse(payload["primary_runs_authorized"])
        self.assertFalse(payload["authorization"]["run_r_primary"])
        self.assertFalse(payload["authorization"]["run_w_star_primary"])


if __name__ == "__main__":
    unittest.main()
