#!/usr/bin/env python3
"""Executable specs for the 0514 terminal blocked report."""

from __future__ import annotations

import unittest
from pathlib import Path

from _common import ToolError

import repository_local_benchmark_final_blocked_report as final_report


class RepositoryLocalBenchmarkFinalBlockedReportTests(unittest.TestCase):
    def completion_audit(self) -> dict[str, object]:
        return {
            "schema_version": "core-narrative.repository-local-benchmark-completion-audit.v1",
            "objective_file": "/Users/chenmohan/Downloads/barcarolle-research-0514-1.md",
        }

    def wstar_decision(self) -> dict[str, object]:
        return {
            "schema_version": "core-narrative.rich-wstar-reserve-gate-decision.v1",
            "repo_slug": "rich",
            "split": "W_star",
            "decision": "w_star_primary_reached_but_reserve_and_pool_gates_failed",
            "accepted_w_star_primary_count": 20,
            "target_primary_count": 20,
            "target_reserve_count": 5,
            "target_primary_plus_reserve_count": 25,
            "remaining_unadmitted_w_star_design_candidates": 3,
            "maximum_possible_w_star_admissions_under_current_scan": 23,
            "reserve_gap_even_if_all_remaining_admitted": 2,
            "candidate_pool_gap": 17,
            "primary_floor_reached": True,
            "reserve_gate_reached": False,
            "candidate_pool_gate_reached": False,
            "full_gate_reached": False,
            "primary_runs_authorized": False,
            "next_allowed_actions": [
                "Create a preregistered protocol revision if the experiment owner accepts a primary-only W* run without reserve.",
                "Or find additional W* candidates within the frozen W* window without using ACUT outputs or W* results.",
                "Or stop before primary runs and report the 0514 line as blocked by W* reserve/candidate-pool supply.",
            ],
        }

    def acut_readiness(self) -> dict[str, object]:
        return {
            "schema_version": "core-narrative.rich-acut-intervention-readiness.v1",
            "primary_runs_authorized": False,
        }

    def build_payload(self, wstar_decision: dict[str, object] | None = None) -> dict[str, object]:
        return final_report.build_payload(
            self.completion_audit(),
            wstar_decision or self.wstar_decision(),
            self.acut_readiness(),
            completion_audit_path=Path("/repo/experiments/core_narrative/results/audit.json"),
            wstar_decision_path=Path("/repo/experiments/core_narrative/results/wstar.json"),
            acut_readiness_path=Path("/repo/experiments/core_narrative/results/acut.json"),
        )

    def test_blocked_wstar_gate_closes_experiment_as_blocked_without_primary_authorization(self) -> None:
        """A terminal W* supply failure produces a completed blocked report and no run permission."""
        payload = self.build_payload()

        self.assertEqual(payload["status"], "completed_blocked_before_primary_runs")
        self.assertEqual(payload["selected_terminal_path"], "stop_before_primary_runs_and_report_blocked_by_wstar_supply")
        self.assertFalse(payload["primary_runs_authorized"])
        self.assertEqual(payload["model_calls_made_after_terminal_gate"], 0)
        self.assertFalse(payload["primary_execution"]["run_r_primary"])
        self.assertFalse(payload["primary_execution"]["run_w_star_primary"])
        self.assertTrue(payload["completion_conclusion"]["active_goal_should_be_marked_complete"])

    def test_primary_outputs_remain_not_applicable_when_no_primary_runs_exist(self) -> None:
        """The final report must not claim R/W* scores or decision-validity analysis."""
        payload = self.build_payload()

        deliverables = {item["deliverable"]: item for item in payload["deliverable_status"]}
        self.assertEqual(
            deliverables["r_wstar_primary_result_report"]["status"],
            "not_applicable_blocked_before_primary_runs",
        )
        self.assertEqual(
            deliverables["decision_validity_report"]["status"],
            "not_applicable_no_primary_results",
        )
        claims = "\n".join(payload["claim_boundary"])
        self.assertIn("R_score", claims)
        self.assertIn("not claimed", claims)

    def test_authorized_wstar_decision_cannot_emit_blocked_final_report(self) -> None:
        """A report named blocked cannot be generated once a gate artifact authorizes primary runs."""
        wstar = self.wstar_decision()
        wstar["primary_runs_authorized"] = True

        with self.assertRaises(ToolError):
            self.build_payload(wstar)

    def test_non_terminal_wstar_gate_cannot_emit_blocked_final_report(self) -> None:
        """The generator refuses a W* gate that has not failed reserve and pool gates."""
        wstar = self.wstar_decision()
        wstar["decision"] = "w_star_full_gate_passed_requires_separate_run_manifest"
        wstar["reserve_gate_reached"] = True
        wstar["candidate_pool_gate_reached"] = True

        with self.assertRaises(ToolError):
            self.build_payload(wstar)


if __name__ == "__main__":
    unittest.main()
