#!/usr/bin/env python3
"""Executable specs for the M5-W2 workspace runner."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m5_w2_workspace_runner as runner


class M5W2WorkspaceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_record(
        self,
        *,
        run_id: str,
        acut_id: str,
        task_id: str,
        status: str,
        score_value: int | None,
        finished_at: str = "2026-05-13T00:00:00Z",
        requires_rerun: bool = False,
        triage_paused: bool = False,
        secondary_flags: dict[str, object] | None = None,
    ) -> None:
        normalized = self.root / "normalized"
        normalized.mkdir(parents=True, exist_ok=True)
        if score_value == 1:
            score_action = "fixed_denominator_one"
        elif score_value == 0:
            score_action = "fixed_denominator_zero"
        elif triage_paused:
            score_action = "triage_paused_before_primary_scoring"
        else:
            score_action = "rerun_or_global_exclusion_required"
        record = {
            "schema_version": runner.SCHEMA_VERSION,
            "tool": runner.TOOL,
            "runner_id": runner.RUNNER_ID,
            "run_id": run_id,
            "axis": "w2",
            "task_id": task_id,
            "acut_id": acut_id,
            "attempt": 1,
            "status": status,
            "started_at": finished_at,
            "finished_at": finished_at,
            "score_action": score_action,
            "score_value": score_value,
            "requires_rerun_or_exclusion": requires_rerun,
            "triage_paused": triage_paused,
            "artifact_paths": {"normalized_result": str(normalized / f"{run_id}.json")},
            "cost_metadata": {"model_call_made": True, "estimated_cost_usd": 1.0},
            "secondary_flags": secondary_flags or {},
        }
        Path(record["artifact_paths"]["normalized_result"]).write_text(json.dumps(record), encoding="utf-8")

    def test_deterministic_order_contains_each_preregistered_cell_once(self) -> None:
        """The W2 run order is shuffled but preserves the fixed 4 x 10 denominator."""
        design = {
            "acuts": list(runner.EXPECTED_ACUTS),
            "tasks": [f"click__rwork__{index:03d}" for index in range(101, 111)],
            "shuffle_seed": "unit-seed",
        }

        first = list(runner.iter_primary_cells(design))
        second = list(runner.iter_primary_cells(design))

        self.assertEqual(first, second)
        self.assertEqual(len(first), 40)
        self.assertEqual(len(set(first)), 40)
        self.assertNotEqual(first, sorted(first))

    def test_summary_computes_w2_gate_pass_and_pairwise_metrics(self) -> None:
        """A complete W2 matrix produces scores, paired wins, and gate decisions."""
        tasks = [f"click__rwork__{index:03d}" for index in range(101, 111)]
        design = {"acuts": list(runner.EXPECTED_ACUTS), "tasks": tasks, "shuffle_seed": "unit-seed"}
        for task_index, task_id in enumerate(tasks):
            self.write_record(run_id=f"cheap-{task_id}", acut_id=runner.CHEAP_GENERIC, task_id=task_id, status="verified_pass" if task_index < 3 else "verified_fail", score_value=1 if task_index < 3 else 0)
            self.write_record(run_id=f"click-{task_id}", acut_id="cheap-click-specialist", task_id=task_id, status="verified_pass" if task_index < 4 else "verified_fail", score_value=1 if task_index < 4 else 0)
            self.write_record(run_id=f"deep-{task_id}", acut_id=runner.DEEP_SPECIALIST, task_id=task_id, status="verified_pass" if task_index < 6 else "verified_fail", score_value=1 if task_index < 6 else 0)
            self.write_record(run_id=f"frontier-{task_id}", acut_id=runner.FRONTIER_GENERIC, task_id=task_id, status="verified_pass" if task_index < 5 else "verified_fail", score_value=1 if task_index < 5 else 0)

        summary = runner.build_summary(design, self.root, self.root / "m5_w2_matrix.yaml")

        self.assertEqual(summary["status"], "w2_primary_complete_gate_passed")
        self.assertTrue(summary["primary_score_ready"])
        self.assertEqual(summary["w2_by_acut"][runner.DEEP_SPECIALIST]["W2_verified_score"], 6)
        self.assertTrue(summary["gates"]["context_effect"]["passed"])
        self.assertTrue(summary["gates"]["nfl_candidate"]["passed"])
        self.assertEqual(summary["paired_metrics"]["deep_vs_cheap_generic"]["wins"], 3)
        self.assertTrue((self.root / "summary.json").exists())
        self.assertTrue((self.root / "reports/w2_primary_summary.md").exists())

    def test_summary_keeps_missing_and_infra_cells_out_of_ready_state(self) -> None:
        """Missing or infrastructure-blocked cells prevent W2 gate computation."""
        tasks = ["click__rwork__101"]
        design = {"acuts": [runner.CHEAP_GENERIC, runner.DEEP_SPECIALIST], "tasks": tasks, "shuffle_seed": "unit-seed"}
        self.write_record(
            run_id="infra",
            acut_id=runner.CHEAP_GENERIC,
            task_id="click__rwork__101",
            status="verifier_infra_error",
            score_value=None,
            requires_rerun=True,
        )

        summary = runner.build_summary(design, self.root, self.root / "m5_w2_matrix.yaml")

        self.assertEqual(summary["status"], "w2_primary_incomplete_or_infra_blocked")
        self.assertFalse(summary["primary_score_ready"])
        self.assertEqual(summary["infra_reruns_exclusions"]["count"], 1)
        self.assertEqual(summary["missing_cells"], 1)
        self.assertEqual(summary["gates"]["status"], "not_computable")

    def test_normalized_payload_records_source_derived_replay_and_true_unsafe_flags(self) -> None:
        """Secondary diagnostics distinguish source-derived replay from true unsafe blocks."""
        artifact_dir = self.root / "raw/run"
        artifact_dir.mkdir(parents=True)
        source_payload = {
            "tool": "workspace_mode_runner",
            "schema_version": "core-narrative.workspace-mode-execution.v1",
            "run_id": "run",
            "acut_id": runner.DEEP_SPECIALIST,
            "task_id": "click__rwork__101",
            "split": "rwork",
            "attempt": 1,
            "status": "verified_pass",
            "candidate_patch": {
                "private_replay_allowed": True,
                "unsafe_content_policy": {"decision": "allow_private_replay_source_derived_url_only"},
            },
            "verification": {"attempted": True},
            "metadata": {"replay_patch_private": True},
        }

        normalized = runner.normalized_from_workspace_payload(
            payload=source_payload,
            config_path=self.root / "config.yaml",
            command={"command": ["workspace_mode_runner.py"]},
            artifact_dir=artifact_dir,
            normalized_path=self.root / "normalized/source.json",
        )

        self.assertTrue(normalized["secondary_flags"]["source_derived_private_replay"])
        self.assertFalse(normalized["secondary_flags"]["true_unsafe"])
        self.assertFalse(normalized["secondary_flags"]["policy_hold"])

        unsafe_payload = {
            **source_payload,
            "status": "unsafe_or_scope_violation",
            "candidate_patch": {
                "private_replay_allowed": False,
                "unsafe_content_policy": {"decision": "reject_true_or_ambiguous_unsafe"},
            },
            "metadata": {"replay_patch_private": False},
        }
        normalized_unsafe = runner.normalized_from_workspace_payload(
            payload=unsafe_payload,
            config_path=self.root / "config.yaml",
            command={"command": ["workspace_mode_runner.py"]},
            artifact_dir=artifact_dir,
            normalized_path=self.root / "normalized/unsafe.json",
        )

        self.assertFalse(normalized_unsafe["secondary_flags"]["source_derived_private_replay"])
        self.assertTrue(normalized_unsafe["secondary_flags"]["true_unsafe"])
        self.assertTrue(normalized_unsafe["secondary_flags"]["policy_hold"])


if __name__ == "__main__":
    unittest.main()
