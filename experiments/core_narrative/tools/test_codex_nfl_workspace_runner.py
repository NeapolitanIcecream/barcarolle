#!/usr/bin/env python3
"""Executable specs for RGW-full-workspace-v1 workspace runner helpers."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import codex_nfl_workspace_runner as runner


class CodexNflWorkspaceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_normalized_workspace_payload_records_audit_and_scoring_fields(self) -> None:
        """A workspace-mode payload becomes a normalized RGW primary result."""
        artifact_dir = self.root / "raw/run"
        artifact_dir.mkdir(parents=True)
        (artifact_dir / "candidate.patch").write_text("diff --git a/a b/a\n", encoding="utf-8")
        (artifact_dir / "codex_cli_patch_command.json").write_text(
            json.dumps({"model_call_made": True, "model": "gpt-5.4-mini"}),
            encoding="utf-8",
        )
        payload = {
            "tool": "workspace_mode_runner",
            "schema_version": "core-narrative.workspace-mode-execution.v1",
            "run_id": "run",
            "acut_id": "cheap-generic-swe",
            "task_id": "click__rbench__001",
            "split": "rbench",
            "attempt": 1,
            "status": "verified_pass",
            "started_at": "start",
            "finished_at": "finish",
            "duration_seconds": 1.2,
            "candidate_patch": {
                "path": str(artifact_dir / "candidate.patch"),
                "sha256": "abc",
                "size_bytes": 21,
                "has_scoreable_diff": True,
                "base_ref": "base",
                "base_tree": "tree",
                "current_head": "base",
                "head_drifted": False,
            },
            "verification": {
                "attempted": True,
                "workspace": "/tmp/verify",
                "base_tree": "tree",
                "base_tree_matches_run": True,
                "normalized_result": str(artifact_dir / "normalized_result.json"),
                "verifier_exit_code": 0,
            },
            "metadata": {"base_ref": "base", "base_tree": "tree"},
            "error": None,
        }

        normalized = runner.normalized_from_workspace_payload(
            payload=payload,
            axis="rbench",
            config_path=self.root / "config.yaml",
            command={"command": ["workspace_mode_runner.py"]},
            artifact_dir=artifact_dir,
            normalized_path=self.root / "normalized/run.json",
        )

        self.assertEqual(normalized["status"], "verified_pass")
        self.assertTrue(normalized["primary_pass"])
        self.assertEqual(normalized["score_action"], "fixed_denominator_one")
        self.assertEqual(normalized["score_value"], 1)
        self.assertEqual(normalized["base_refs"]["base_ref"], "base")
        self.assertEqual(normalized["candidate_patch"]["sha256"], "abc")
        self.assertEqual(normalized["verification_workspace"]["workspace"], "/tmp/verify")
        self.assertEqual(normalized["cost_metadata"]["estimated_cost_usd"], 1.0)

    def test_normalized_workspace_payload_defaults_missing_acut_summary_to_no_model_call(self) -> None:
        """Regression: missing ACUT summaries are not live model-call evidence."""
        artifact_dir = self.root / "raw/run-without-acut-summary"
        artifact_dir.mkdir(parents=True)
        payload = {
            "tool": "workspace_mode_runner",
            "schema_version": "core-narrative.workspace-mode-execution.v1",
            "run_id": "run-without-acut-summary",
            "acut_id": "cheap-generic-swe",
            "task_id": "click__rbench__001",
            "split": "rbench",
            "attempt": 1,
            "status": "verifier_infra_error",
            "started_at": "start",
            "finished_at": "finish",
            "duration_seconds": 1.2,
            "candidate_patch": {},
            "verification": {},
            "metadata": {},
            "error": "summary missing",
        }

        normalized = runner.normalized_from_workspace_payload(
            payload=payload,
            axis="rbench",
            config_path=self.root / "config.yaml",
            command={"command": ["workspace_mode_runner.py"]},
            artifact_dir=artifact_dir,
            normalized_path=self.root / "normalized/run-without-acut-summary.json",
        )

        self.assertIs(normalized["metadata"]["model_call_made"], False)
        self.assertIs(normalized["cost_metadata"]["model_call_made"], False)
        self.assertEqual(normalized["cost_metadata"]["estimated_cost_usd"], 0.0)
        self.assertIsNone(normalized["cost_metadata"]["acut_summary_artifact"])

    def test_summary_keeps_infra_cells_out_of_primary_ready_state(self) -> None:
        """Infrastructure cells are recorded for rerun/exclusion instead of counted as zero."""
        design = {"acuts": ["cheap-generic-swe"], "rbench": ["click__rbench__001"], "rwork": [], "general": []}
        normalized = self.root / "normalized"
        normalized.mkdir()
        records = [
            {
                "schema_version": runner.SCHEMA_VERSION,
                "tool": runner.TOOL,
                "runner_id": runner.RUNNER_ID,
                "run_id": "pass",
                "axis": "rbench",
                "task_id": "click__rbench__001",
                "acut_id": "cheap-generic-swe",
                "status": "verified_pass",
                "score_action": "fixed_denominator_one",
                "score_value": 1,
                "requires_rerun_or_exclusion": False,
                "triage_paused": False,
                "artifact_paths": {"normalized_result": str(normalized / "pass.json")},
                "cost_metadata": {"model_call_made": True, "estimated_cost_usd": 1.0},
            },
            {
                "schema_version": runner.SCHEMA_VERSION,
                "tool": runner.TOOL,
                "runner_id": runner.RUNNER_ID,
                "run_id": "infra",
                "axis": "general",
                "task_id": "g-task",
                "acut_id": "cheap-generic-swe",
                "status": "verifier_infra_error",
                "score_action": "rerun_or_global_exclusion_required",
                "score_value": None,
                "requires_rerun_or_exclusion": True,
                "triage_paused": False,
                "artifact_paths": {"normalized_result": str(normalized / "infra.json")},
                "cost_metadata": {"model_call_made": False, "estimated_cost_usd": 0.0},
            },
        ]
        for record in records:
            Path(record["artifact_paths"]["normalized_result"]).write_text(json.dumps(record), encoding="utf-8")

        summary = runner.build_summary(
            {"acuts": ["cheap-generic-swe"], "rbench": ["click__rbench__001"], "rwork": [], "general": ["g-task"]},
            self.root,
            self.root / "config.yaml",
        )

        self.assertEqual(summary["axes"]["rbench"]["score_percent_fixed_denominator"], 100.0)
        self.assertFalse(summary["axes"]["general"]["primary_score_ready"])
        self.assertEqual(summary["infra_reruns_exclusions"]["count"], 1)
        self.assertEqual(summary["status"], "primary_incomplete_or_infra_blocked")
        self.assertTrue((self.root / "cost_ledger.jsonl").exists())

    def test_acut_table_deduplicates_cell_records_before_scoring(self) -> None:
        """Regression: rerun records for the same ACUT cell must not inflate scores."""
        design = {"acuts": ["cheap-generic-swe"], "rbench": ["click__rbench__001"], "rwork": [], "general": []}
        records = [
            {
                "axis": "rbench",
                "task_id": "click__rbench__001",
                "acut_id": "cheap-generic-swe",
                "status": "verified_pass",
                "score_value": 1,
                "requires_rerun_or_exclusion": False,
                "triage_paused": False,
            },
            {
                "axis": "rbench",
                "task_id": "click__rbench__001",
                "acut_id": "cheap-generic-swe",
                "status": "verified_pass",
                "score_value": 1,
                "requires_rerun_or_exclusion": False,
                "triage_paused": False,
            },
        ]

        row = runner.by_acut_table(records, design)["cheap-generic-swe"]

        self.assertEqual(row["r_passed"], 1)
        self.assertEqual(row["r_score_percent_fixed"], 100.0)
        self.assertTrue(row["r_primary_score_ready"])
        self.assertEqual(row["r_status_counts"], {"verified_pass": 1})

    def test_summary_uses_latest_duplicate_cell_evidence_not_filename_order(self) -> None:
        """Regression: duplicate cell records are canonicalized by evidence recency."""
        design = {"acuts": ["cheap-generic-swe"], "rbench": ["click__rbench__001"], "rwork": [], "general": []}
        normalized = self.root / "normalized"
        normalized.mkdir()
        newer = {
            "schema_version": runner.SCHEMA_VERSION,
            "tool": runner.TOOL,
            "runner_id": runner.RUNNER_ID,
            "run_id": "run-newer",
            "axis": "rbench",
            "task_id": "click__rbench__001",
            "acut_id": "cheap-generic-swe",
            "attempt": 1,
            "status": "verified_pass",
            "started_at": "2026-05-12T11:00:00Z",
            "finished_at": "2026-05-12T11:01:00Z",
            "score_action": "fixed_denominator_one",
            "score_value": 1,
            "requires_rerun_or_exclusion": False,
            "triage_paused": False,
            "artifact_paths": {"normalized_result": str(normalized / "a-newer.json")},
            "cost_metadata": {"model_call_made": True, "estimated_cost_usd": 1.0},
        }
        older = {
            **newer,
            "run_id": "run-older",
            "status": "verified_fail",
            "started_at": "2026-05-12T10:00:00Z",
            "finished_at": "2026-05-12T10:01:00Z",
            "score_action": "fixed_denominator_zero",
            "score_value": 0,
            "artifact_paths": {"normalized_result": str(normalized / "z-older.json")},
        }
        Path(newer["artifact_paths"]["normalized_result"]).write_text(json.dumps(newer), encoding="utf-8")
        Path(older["artifact_paths"]["normalized_result"]).write_text(json.dumps(older), encoding="utf-8")

        summary = runner.build_summary(design, self.root, self.root / "config.yaml")

        self.assertEqual(summary["axes"]["rbench"]["passed"], 1)
        self.assertEqual(summary["axes"]["rbench"]["status_counts"], {"verified_pass": 1})
        self.assertEqual(summary["grw_table"]["cheap-generic-swe"]["r_passed"], 1)
        self.assertEqual(summary["grw_table"]["cheap-generic-swe"]["r_status_counts"], {"verified_pass": 1})

    def test_summary_ignores_newer_dry_run_primary_records_when_live_evidence_exists(self) -> None:
        """Regression: dry-run primary records must not replace live model-call evidence."""
        design = {"acuts": ["cheap-generic-swe"], "rbench": ["click__rbench__001"], "rwork": [], "general": []}
        normalized = self.root / "normalized"
        normalized.mkdir()
        live = {
            "schema_version": runner.SCHEMA_VERSION,
            "tool": runner.TOOL,
            "runner_id": runner.RUNNER_ID,
            "run_id": "unit__live__rbench__cheap-generic-swe__click__rbench__001__attempt1",
            "axis": "rbench",
            "task_id": "click__rbench__001",
            "acut_id": "cheap-generic-swe",
            "attempt": 1,
            "status": "verified_pass",
            "started_at": "2026-05-12T10:00:00Z",
            "finished_at": "2026-05-12T10:01:00Z",
            "score_action": "fixed_denominator_one",
            "score_value": 1,
            "requires_rerun_or_exclusion": False,
            "triage_paused": False,
            "artifact_paths": {"normalized_result": str(normalized / "live.json")},
            "cost_metadata": {"model_call_made": True, "estimated_cost_usd": 1.0},
            "metadata": {"model_call_made": True},
        }
        dry_run = {
            **live,
            "run_id": "unit__dry-run__rbench__cheap-generic-swe__click__rbench__001__attempt1",
            "status": "verified_fail",
            "started_at": "2026-05-12T11:00:00Z",
            "finished_at": "2026-05-12T11:01:00Z",
            "score_action": "fixed_denominator_zero",
            "score_value": 0,
            "artifact_paths": {"normalized_result": str(normalized / "dry-run.json")},
            "cost_metadata": {"model_call_made": False, "estimated_cost_usd": 0.0},
            "metadata": {"model_call_made": False},
        }
        Path(live["artifact_paths"]["normalized_result"]).write_text(json.dumps(live), encoding="utf-8")
        Path(dry_run["artifact_paths"]["normalized_result"]).write_text(json.dumps(dry_run), encoding="utf-8")

        summary = runner.build_summary(design, self.root, self.root / "config.yaml")

        self.assertEqual(summary["axes"]["rbench"]["passed"], 1)
        self.assertEqual(summary["axes"]["rbench"]["status_counts"], {"verified_pass": 1})
        self.assertEqual(summary["grw_table"]["cheap-generic-swe"]["r_passed"], 1)
        self.assertEqual(summary["grw_table"]["cheap-generic-swe"]["r_status_counts"], {"verified_pass": 1})

    def test_manifest_stores_artifact_paths_relative_to_repo(self) -> None:
        """Regression: committed manifests must not contain host-specific artifact paths."""
        repo_root = self.root / "repo"
        bundle_root = repo_root / "experiments/core_narrative/results/rgw_full_workspace_v1"
        raw_file = bundle_root / "raw/run/workspace_mode_result.json"
        normalized_file = bundle_root / "normalized/run.json"
        config_path = repo_root / "experiments/core_narrative/configs/rgw_full_workspace_v1.yaml"
        raw_file.parent.mkdir(parents=True)
        normalized_file.parent.mkdir(parents=True)
        config_path.parent.mkdir(parents=True)
        raw_file.write_text("{}", encoding="utf-8")
        normalized_file.write_text("{}", encoding="utf-8")
        config_path.write_text("acuts: []\n", encoding="utf-8")

        with mock.patch.object(runner, "REPO_ROOT", repo_root):
            manifest = runner.write_manifest(
                bundle_root,
                records=[],
                design={"acuts": [], "rbench": [], "rwork": [], "general": []},
                config_path=config_path,
            )

        self.assertEqual(
            manifest["raw_artifacts"],
            ["experiments/core_narrative/results/rgw_full_workspace_v1/raw/run/workspace_mode_result.json"],
        )
        self.assertEqual(
            manifest["normalized_results"],
            ["experiments/core_narrative/results/rgw_full_workspace_v1/normalized/run.json"],
        )
        self.assertFalse(os.path.isabs(manifest["config"]))
        self.assertTrue(all(not os.path.isabs(path) for path in manifest["raw_artifacts"]))
        self.assertTrue(all(not os.path.isabs(path) for path in manifest["normalized_results"]))

    def test_cost_ledger_normalizes_cost_metadata_artifact_paths_to_repo_relative(self) -> None:
        """Regression: committed cost ledgers must not expose host-specific paths."""
        repo_root = self.root / "repo"
        bundle_root = repo_root / "experiments/core_narrative/results/rgw_full_workspace_v1"
        artifact = bundle_root / "raw/run/codex_cli_patch_command.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("{}", encoding="utf-8")
        records = [
            {
                "run_id": "run",
                "axis": "rbench",
                "task_id": "click__rbench__001",
                "acut_id": "cheap-generic-swe",
                "attempt": 1,
                "cost_metadata": {
                    "model_call_made": True,
                    "estimated_cost_usd": 1.0,
                    "acut_summary_artifact": str(artifact),
                },
            }
        ]

        with mock.patch.object(runner, "REPO_ROOT", repo_root):
            path = runner.write_cost_ledger(bundle_root, records)

        row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(
            row["acut_summary_artifact"],
            "experiments/core_narrative/results/rgw_full_workspace_v1/raw/run/codex_cli_patch_command.json",
        )
        self.assertFalse(os.path.isabs(row["acut_summary_artifact"]))
        self.assertNotIn(str(repo_root), json.dumps(row))

    def test_summary_stores_artifact_paths_relative_to_repo(self) -> None:
        """Regression: committed summaries must not contain host-specific artifact paths."""
        repo_root = self.root / "repo"
        bundle_root = repo_root / "experiments/core_narrative/results/rgw_full_workspace_v1"
        config_path = repo_root / "experiments/core_narrative/configs/rgw_full_workspace_v1.yaml"
        bundle_root.mkdir(parents=True)
        config_path.parent.mkdir(parents=True)
        config_path.write_text("acuts: []\n", encoding="utf-8")

        with mock.patch.object(runner, "REPO_ROOT", repo_root):
            summary = runner.build_summary(
                {"acuts": [], "rbench": [], "rwork": [], "general": []},
                bundle_root,
                config_path,
            )

        self.assertEqual(
            summary["artifacts"]["summary"],
            "experiments/core_narrative/results/rgw_full_workspace_v1/summary.json",
        )
        self.assertFalse(os.path.isabs(summary["config"]))
        self.assertTrue(all(not os.path.isabs(path) for path in summary["artifacts"].values()))

    def test_run_id_for_includes_execution_mode(self) -> None:
        """Regression: dry-run and live cells must not reuse artifact paths."""
        dry_run_id = runner.run_id_for(
            "unit",
            "rbench",
            "click__rbench__001",
            "cheap-generic-swe",
            1,
            "dry-run",
        )
        live_run_id = runner.run_id_for(
            "unit",
            "rbench",
            "click__rbench__001",
            "cheap-generic-swe",
            1,
            "live",
        )

        self.assertEqual(dry_run_id, "unit__dry-run__rbench__cheap-generic-swe__click__rbench__001__attempt1")
        self.assertEqual(live_run_id, "unit__live__rbench__cheap-generic-swe__click__rbench__001__attempt1")
        self.assertNotEqual(dry_run_id, live_run_id)

    def test_workspace_mode_command_invokes_workspace_runner_before_acut_command(self) -> None:
        """The primary execution chain starts with workspace_mode_runner.py."""
        args = SimpleNamespace(
            attempt=1,
            acut_timeout_seconds=3600,
            verifier_timeout_seconds=120,
            install_workspaces=True,
            mode="dry-run",
        )
        with mock.patch.object(runner, "workspace_python", return_value="/opt/python3.10"):
            command = runner.workspace_mode_command(
                axis="rbench",
                task_id="click__rbench__001",
                acut_id="cheap-generic-swe",
                attempt=args.attempt,
                run_id="unit",
                artifact_dir=self.root / "raw/unit",
                workspace_root=self.root / "workspaces",
                acut_timeout_seconds=args.acut_timeout_seconds,
                verifier_timeout_seconds=args.verifier_timeout_seconds,
                install_workspaces=args.install_workspaces,
                mode=args.mode,
            )

        self.assertEqual(command[0], "/opt/python3.10")
        self.assertEqual(command[1], str(runner.WORKSPACE_MODE_RUNNER))
        self.assertIn("--", command)
        separator = command.index("--")
        self.assertEqual(command[separator + 1], "/opt/python3.10")
        self.assertIn(str(runner.CODEX_CLI_PATCH_COMMAND), command[separator + 1 :])
        self.assertIn("--dry-run", command)

    def test_run_click_cell_fallback_preserves_workspace_runner_timeout(self) -> None:
        """Regression: timed out wrapper runs remain timeout cells when no payload is emitted."""
        args = SimpleNamespace(
            run_prefix="unit",
            attempt=1,
            bundle_root=str(self.root / "bundle"),
            workspace_root=str(self.root / "workspaces"),
            acut_timeout_seconds=1,
            verifier_timeout_seconds=1,
            install_workspaces=False,
            mode="dry-run",
            force=True,
        )
        summary = {
            "command": ["workspace_mode_runner.py"],
            "cwd": str(self.root),
            "exit_code": None,
            "timed_out": True,
            "command_error": None,
            "started_at": "start",
            "finished_at": "finish",
            "duration_seconds": 3.0,
            "stdout_artifact": str(self.root / "stdout.txt"),
            "stderr_artifact": str(self.root / "stderr.txt"),
        }

        with mock.patch.object(runner, "workspace_mode_command", return_value=["workspace_mode_runner.py"]):
            with mock.patch.object(runner, "command_summary", return_value=summary):
                normalized = runner.run_click_cell(
                    axis="rwork",
                    task_id="click__rwork__001",
                    acut_id="cheap-generic-swe",
                    args=args,
                    config_path=self.root / "config.yaml",
                )

        self.assertEqual(normalized["status"], "timeout")
        self.assertEqual(normalized["timeout_owner"], "verifier")
        self.assertEqual(normalized["metadata"]["status_semantics"]["score_action"], "rerun_or_global_exclusion_required")

    def test_run_click_cells_uses_configured_concurrency_and_preserves_result_order(self) -> None:
        """Primary batch execution can run at least four cells concurrently without reordering output."""
        cells = [
            ("rbench", "click__rbench__001", "cheap-generic-swe"),
            ("rbench", "click__rbench__002", "cheap-click-specialist"),
            ("rwork", "click__rwork__001", "frontier-generic-swe"),
            ("rwork", "click__rwork__002", "frontier-click-specialist"),
        ]
        args = SimpleNamespace(max_workers=4)
        submitted: list[tuple[str, str, str]] = []

        class FakeFuture:
            def __init__(self, value: dict[str, str]) -> None:
                self.value = value

            def result(self) -> dict[str, str]:
                return self.value

        class FakeExecutor:
            max_workers_seen: int | None = None

            def __init__(self, max_workers: int) -> None:
                FakeExecutor.max_workers_seen = max_workers

            def __enter__(self) -> "FakeExecutor":
                return self

            def __exit__(self, *_exc: object) -> None:
                return None

            def submit(self, fn: object, **kwargs: object) -> FakeFuture:
                submitted.append((str(kwargs["axis"]), str(kwargs["task_id"]), str(kwargs["acut_id"])))
                return FakeFuture({"run_id": f"{kwargs['axis']}::{kwargs['task_id']}::{kwargs['acut_id']}"})

        with mock.patch.object(runner.concurrent.futures, "ThreadPoolExecutor", FakeExecutor):
            records = runner.run_click_cells(cells, args=args, config_path=self.root / "config.yaml")

        self.assertEqual(FakeExecutor.max_workers_seen, 4)
        self.assertEqual(submitted, cells)
        self.assertEqual(
            [record["run_id"] for record in records],
            [f"{axis}::{task_id}::{acut_id}" for axis, task_id, acut_id in cells],
        )

    def test_main_rejects_non_positive_max_workers(self) -> None:
        """Invalid concurrency settings fail before any batch work starts."""
        emitted: list[Exception] = []

        def fake_fail(_tool: str, exc: Exception) -> int:
            emitted.append(exc)
            return 99

        with mock.patch.object(runner, "execute") as execute:
            with mock.patch.object(runner, "fail", side_effect=fake_fail):
                code = runner.main(["--max-workers", "0"])

        self.assertEqual(code, 99)
        execute.assert_not_called()
        self.assertIsInstance(emitted[0], runner.ToolError)
        self.assertIn("max-workers must be at least 1", str(emitted[0]))


if __name__ == "__main__":
    unittest.main()
