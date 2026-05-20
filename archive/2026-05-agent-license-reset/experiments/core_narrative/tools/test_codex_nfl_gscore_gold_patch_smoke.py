#!/usr/bin/env python3
"""Executable specs for the pinned G-score gold-patch smoke."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import codex_nfl_gscore_gold_patch_smoke as smoke
from _common import load_manifest


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG = REPO_ROOT / "experiments/core_narrative/configs/general_benchmark.yaml"


class GScoreGoldPatchSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_pinned_config_keeps_fixed_six_task_denominator_and_selection_keys(self) -> None:
        """The locked general benchmark slice is six fixed tasks before any ACUT run."""
        config = load_manifest(CONFIG)

        result = smoke.validate_pinned_config(config)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["denominator"]["target_size"], 6)
        self.assertEqual(result["denominator"]["locked_task_count"], 6)
        self.assertEqual(result["denominator"]["unique_instance_id_count"], 6)
        self.assertEqual(result["denominator"]["ordinals"], [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(check["passed"] for check in result["selection_rule"]["selection_key_checks"]))
        self.assertEqual(
            result["selection_rule"]["repo_counts"],
            {"NodeBB/NodeBB": 2, "ansible/ansible": 2, "element-hq/element-web": 2},
        )

    def test_missing_dataset_cache_and_harness_are_machine_readable_blockers(self) -> None:
        """Absent local prerequisites block the smoke without fabricating pass evidence."""
        output = self.root / "smoke.json"
        args = smoke.parse_args(
            [
                "--config",
                str(CONFIG),
                "--dataset-cache",
                str(self.root / "missing.parquet"),
                "--harness-path",
                str(self.root / "missing-harness"),
                "--artifact-dir",
                str(self.root / "artifacts"),
                "--output",
                str(output),
            ]
        )

        payload = smoke.build_smoke(args)

        blocker_names = {item["blocker"] for item in payload["blockers"]}
        self.assertEqual(payload["status"], "gold_patch_smoke_blocked")
        self.assertIn("dataset_cache_missing", blocker_names)
        self.assertIn("evaluation_harness_checkout_missing", blocker_names)
        self.assertFalse(payload["gold_patch_path"]["ran"])
        self.assertFalse(payload["gold_patch_path"]["basis_proven"])
        self.assertFalse(payload["direct_acut_scoring"]["attempted"])
        self.assertFalse(payload["direct_acut_scoring"]["g_score_available"])
        self.assertEqual(payload["direct_acut_scoring"]["g_scores"], {})
        self.assertTrue(payload["no_model_calls_made"])
        self.assertEqual(payload["checks"]["artifact_layout"]["status"], "passed")
        self.assertFalse(payload["checks"]["artifact_layout"]["input_layout_expected_now"])

    def test_local_docker_daemon_failure_blocks_default_preflight_path(self) -> None:
        """Local-Docker daemon readiness is required even before gold-patch execution."""

        def fake_run_capture(command: list[str], **_: object) -> dict[str, object]:
            if command[:2] == ["docker", "--version"]:
                return {"available": True, "exit_code": 0, "stdout": "Docker version 25.0.0", "stderr": ""}
            if command[:2] == ["docker", "info"]:
                return {"available": False, "exit_code": 1, "stdout": "", "stderr": "Cannot connect to daemon"}
            raise AssertionError(f"unexpected command: {command}")

        args = smoke.parse_args(
            [
                "--config",
                str(CONFIG),
                "--dataset-cache",
                str(self.root / "missing.parquet"),
                "--harness-path",
                str(self.root / "missing-harness"),
                "--artifact-dir",
                str(self.root / "artifacts"),
                "--output",
                str(self.root / "smoke.json"),
            ]
        )

        with mock.patch.object(smoke, "run_capture", side_effect=fake_run_capture):
            payload = smoke.build_smoke(args)

        docker = payload["checks"]["docker"]
        self.assertEqual(docker["status"], "blocked")
        self.assertTrue(docker["required_for_selected_backend"])
        self.assertFalse(docker["execute_gold_patch_requested"])
        self.assertIn("docker_daemon_unavailable", {item["blocker"] for item in docker["blockers"]})
        self.assertIn("docker_daemon_unavailable", {item["blocker"] for item in payload["blockers"]})

    def test_gold_patch_artifacts_use_official_evaluator_patch_schema(self) -> None:
        """Gold patches are materialized as the evaluator's instance_id/patch/prefix list."""
        config = load_manifest(CONFIG)
        rows = []
        for task in smoke.locked_tasks(config):
            rows.append(
                {
                    "instance_id": task["instance_id"],
                    "repo": task["repo"],
                    "patch": f"diff --git a/{task['ordinal']} b/{task['ordinal']}\n",
                    "test_patch": "diff --git a/test b/test\n",
                    "before_repo_set_cmd": "true",
                    "selected_test_files_to_run": "[]",
                    "base_commit": "abc123",
                    "fail_to_pass": "[]",
                    "pass_to_pass": "[]",
                    "dockerhub_tag": f"tag-{task['ordinal']}",
                }
            )

        artifacts = smoke.materialize_gold_patch_inputs(config=config, rows=rows, artifact_dir=self.root / "artifacts")

        patch_payload = json.loads(Path(artifacts["patch_path"]).read_text(encoding="utf-8"))
        raw_rows = Path(artifacts["raw_sample_path"]).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(patch_payload), 6)
        self.assertEqual(len(raw_rows), 6)
        self.assertEqual(set(patch_payload[0]), {"instance_id", "patch", "prefix"})
        self.assertEqual({item["prefix"] for item in patch_payload}, {"gold_patch_smoke"})

        layout = smoke.artifact_layout_check(
            artifact_dir=self.root / "artifacts",
            materialized_artifacts=artifacts,
            evaluator_run=None,
        )
        self.assertEqual(layout["status"], "passed")
        self.assertTrue(layout["input_layout_expected_now"])
        self.assertFalse(layout["execution_layout_expected_now"])

    def test_selection_rule_is_recomputed_from_dataset_rows_when_cache_is_available(self) -> None:
        """A readable dataset cache must prove the locked ids come from the frozen rule."""
        rows = [
            {"repo": repo, "instance_id": f"{repo}-{index}"}
            for repo in ("c-repo", "a-repo", "b-repo")
            for index in range(4)
        ]
        config = {
            "task_subset": {
                "target_size": 6,
                "selection_rule": {"salt": "unit-salt"},
                "stratification": {"rows_per_repo": 2},
            }
        }
        expected = [
            item["instance_id"]
            for item in smoke.compute_selection_from_rows(rows, salt="unit-salt", target_size=6, rows_per_repo=2)
        ]

        passed = smoke.validate_selection_against_dataset(config, rows, expected)
        failed = smoke.validate_selection_against_dataset(config, rows, list(reversed(expected)))

        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["blockers"], [])
        self.assertEqual(failed["status"], "blocked")
        self.assertEqual(failed["blockers"][0]["blocker"], "dataset_selection_rule_mismatch")

    def test_score_parser_accepts_official_eval_results_mapping(self) -> None:
        """The official eval_results.json mapping is enough to prove all six gold patches resolved."""
        config = load_manifest(CONFIG)
        expected = [task["instance_id"] for task in smoke.locked_tasks(config)]
        payload = {instance_id: True for instance_id in expected}

        parsed = smoke.parse_score_payload(payload, expected)

        self.assertEqual(parsed["status"], "parsed")
        self.assertEqual(parsed["denominator"], 6)
        self.assertEqual(parsed["resolved_count"], 6)
        self.assertEqual(parsed["resolved_rate_percent"], 100.0)
        self.assertEqual(parsed["missing_instance_ids"], [])
        self.assertEqual(parsed["unexpected_instance_ids"], [])
        self.assertEqual(parsed["invalid_entries"], [])
        self.assertTrue(parsed["proof_eligible"])

    def test_score_parser_rejects_string_or_int_values_for_proof(self) -> None:
        """Regression: malformed official score values must not prove gold-patch resolution."""
        expected = ["task-a"]

        for malformed in ("passed", 1):
            with self.subTest(malformed=malformed):
                parsed = smoke.parse_score_payload({"task-a": malformed}, expected)

                self.assertEqual(parsed["status"], "invalid")
                self.assertFalse(parsed["proof_eligible"])
                self.assertEqual(parsed["resolved_count"], 0)
                self.assertEqual(parsed["missing_instance_ids"], ["task-a"])
                self.assertEqual(parsed["invalid_entries"][0]["reason"], "not_json_boolean_resolved_status")

    def test_permissive_score_parser_is_non_proof_diagnostic_only(self) -> None:
        """Non-official convenience parsing cannot produce proof-eligible score evidence."""
        parsed = smoke.parse_score_payload_permissive({"task-a": "passed"}, ["task-a"])

        self.assertEqual(parsed["status"], "parsed_non_proof")
        self.assertFalse(parsed["proof_eligible"])
        self.assertEqual(parsed["resolved_count"], 1)
        self.assertEqual(parsed["normalized_results"], {"task-a": True})

    def test_score_parser_keeps_fixed_denominator_when_expected_task_is_missing(self) -> None:
        """Missing evaluator rows invalidate the artifact instead of shrinking the denominator."""
        parsed = smoke.parse_score_payload({"a": True, "b": False}, ["a", "b", "c"])

        self.assertEqual(parsed["status"], "invalid")
        self.assertFalse(parsed["proof_eligible"])
        self.assertEqual(parsed["denominator"], 3)
        self.assertEqual(parsed["resolved_count"], 1)
        self.assertEqual(parsed["missing_instance_ids"], ["c"])
        self.assertEqual(parsed["unresolved_instance_ids"], ["b", "c"])

    def test_blocked_report_and_payload_do_not_claim_acut_gscore(self) -> None:
        """Blocked gold-patch infrastructure evidence must not become an ACUT score claim."""
        args = smoke.parse_args(
            [
                "--config",
                str(CONFIG),
                "--dataset-cache",
                str(self.root / "missing.parquet"),
                "--harness-path",
                str(self.root / "missing-harness"),
                "--artifact-dir",
                str(self.root / "artifacts"),
                "--output",
                str(self.root / "smoke.json"),
            ]
        )
        payload = smoke.build_smoke(args)

        report = smoke.report_markdown(payload)

        self.assertFalse(payload["direct_acut_scoring"]["attempted"])
        self.assertFalse(payload["direct_acut_scoring"]["g_score_available"])
        self.assertFalse(payload["public_leaderboard_proxy_used"])
        self.assertIn("No G_score is claimed by this report.", report)
        self.assertIn("ACUT G_score available: `False`", report)
        self.assertNotIn("ACUT G_score available: `True`", report)
        self.assertNotIn("ranking reversal", report.lower())


if __name__ == "__main__":
    unittest.main()
