#!/usr/bin/env python3
"""Executable specs for Click matrix and predictivity analysis helpers."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import codex_nfl_canonical_matrix as matrix
import codex_nfl_gscore_basis as gscore_basis
import codex_nfl_predictivity_analysis as predictivity


class CodexNflPredictivityToolsTests(unittest.TestCase):
    def test_canonical_matrix_excludes_dry_run_and_uses_latest_scoreable_attempt(self) -> None:
        """Dry-run prompt packaging artifacts cannot replace live canonical evidence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live = {
                "run_id": "live",
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rbench__001",
                "split": "rbench",
                "attempt": 2,
                "status": "passed",
                "metadata": {
                    "runner_id": "codex-nfl-batch-v1",
                    "direct_runner_id": "codex-nfl-direct-search-replace-v1",
                    "model_call_made": True,
                    "batch_tool": "codex_nfl_experiment_runner",
                    "task_manifest_sha256": "task",
                    "acut_manifest_sha256": "acut",
                    "verifier_digest_sha256": "verifier",
                    "prompt_snapshot_sha256": "prompt",
                    "context_pack_digest": None,
                    "raw_response_artifact": "provider_response.redacted.json",
                    "direct_runner_cost_accounting": {},
                    "clean_patch_replay": {"attempted": True},
                },
            }
            dry_run = {
                **live,
                "run_id": "dry",
                "attempt": 3,
                "status": "infra_failed",
                "metadata": {**live["metadata"], "model_call_made": False, "direct_runner_status": "dry_run_completed"},
            }
            (root / "live.json").write_text(json.dumps(live), encoding="utf-8")
            (root / "dry.json").write_text(json.dumps(dry_run), encoding="utf-8")

            with mock.patch.object(matrix, "CORE_ACUTS", ["cheap-generic-swe"]):
                payload = matrix.build_matrix("rbench", ["click__rbench__001"], root)

        cell = payload["cells"]["cheap-generic-swe::click__rbench__001"]
        self.assertEqual(cell["canonical_latest"]["run_id"], "live")
        self.assertEqual(payload["by_acut"]["cheap-generic-swe"]["score_percent_fixed_denominator"], 100.0)

    def test_canonical_matrix_requires_both_batch_identity_fields(self) -> None:
        """Regression: one matching runner identity field is not enough for canonical evidence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live = {
                "run_id": "live-expected-identity",
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rbench__001",
                "split": "rbench",
                "attempt": 1,
                "status": "failed",
                "metadata": {
                    "runner_id": "codex-nfl-batch-v1",
                    "direct_runner_id": "codex-nfl-direct-search-replace-v1",
                    "model_call_made": True,
                    "batch_tool": "codex_nfl_experiment_runner",
                    "task_manifest_sha256": "task",
                    "acut_manifest_sha256": "acut",
                    "verifier_digest_sha256": "verifier",
                    "prompt_snapshot_sha256": "prompt",
                    "context_pack_digest": None,
                    "raw_response_artifact": "provider_response.redacted.json",
                    "direct_runner_cost_accounting": {},
                    "clean_patch_replay": {"attempted": True},
                },
            }
            mismatched_runner = {
                **live,
                "run_id": "wrong-runner-id",
                "attempt": 2,
                "status": "passed",
                "metadata": {**live["metadata"], "runner_id": "future-batch-v2"},
            }
            mismatched_tool = {
                **live,
                "run_id": "wrong-batch-tool",
                "attempt": 3,
                "status": "passed",
                "metadata": {**live["metadata"], "batch_tool": "reused_tool_name"},
            }
            (root / "live.json").write_text(json.dumps(live), encoding="utf-8")
            (root / "mismatched_runner.json").write_text(json.dumps(mismatched_runner), encoding="utf-8")
            (root / "mismatched_tool.json").write_text(json.dumps(mismatched_tool), encoding="utf-8")

            with mock.patch.object(matrix, "CORE_ACUTS", ["cheap-generic-swe"]):
                payload = matrix.build_matrix("rbench", ["click__rbench__001"], root)

        cell = payload["cells"]["cheap-generic-swe::click__rbench__001"]
        self.assertEqual(cell["canonical_latest"]["run_id"], "live-expected-identity")
        self.assertEqual(payload["by_acut"]["cheap-generic-swe"]["score_percent_fixed_denominator"], 0.0)

    def test_canonical_matrix_rejects_manifest_override_with_mismatched_split(self) -> None:
        """Regression: matrix builds must fail fast when an override manifest uses the wrong split."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "rwork_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "split": "RWork",
                        "tasks": [
                            {
                                "task_id": "click__rwork__001",
                                "split": "rwork",
                                "benchmark_split": "RWork",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(matrix.ToolError) as raised:
                matrix.load_tasks("rbench", str(manifest_path))

        self.assertEqual(raised.exception.details["expected_split"], "rbench")
        self.assertEqual(raised.exception.details["observed_split"], "rwork")

    def test_canonical_matrix_same_attempt_duplicates_use_evidence_time_not_mtime(self) -> None:
        """Regression: stale duplicate artifacts with newer mtimes must not win canonical selection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base = {
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rbench__001",
                "split": "rbench",
                "attempt": 2,
                "metadata": {
                    "runner_id": "codex-nfl-batch-v1",
                    "direct_runner_id": "codex-nfl-direct-search-replace-v1",
                    "model_call_made": True,
                    "batch_tool": "codex_nfl_experiment_runner",
                    "task_manifest_sha256": "task",
                    "acut_manifest_sha256": "acut",
                    "verifier_digest_sha256": "verifier",
                    "prompt_snapshot_sha256": "prompt",
                    "context_pack_digest": None,
                    "raw_response_artifact": "provider_response.redacted.json",
                    "direct_runner_cost_accounting": {},
                    "clean_patch_replay": {"attempted": True},
                },
            }
            stale = {
                **base,
                "run_id": "stale-duplicate",
                "status": "passed",
                "started_at": "2026-05-08T10:00:00Z",
                "finished_at": "2026-05-08T10:00:01Z",
            }
            fresh = {
                **base,
                "run_id": "fresh-evidence",
                "status": "failed",
                "started_at": "2026-05-08T10:05:00Z",
                "finished_at": "2026-05-08T10:05:01Z",
            }
            stale_path = root / "stale.json"
            fresh_path = root / "fresh.json"
            stale_path.write_text(json.dumps(stale), encoding="utf-8")
            fresh_path.write_text(json.dumps(fresh), encoding="utf-8")
            os.utime(fresh_path, (100, 100))
            os.utime(stale_path, (200, 200))

            with mock.patch.object(matrix, "CORE_ACUTS", ["cheap-generic-swe"]):
                payload = matrix.build_matrix("rbench", ["click__rbench__001"], root)

        cell = payload["cells"]["cheap-generic-swe::click__rbench__001"]
        self.assertEqual(cell["attempt2"]["run_id"], "fresh-evidence")
        self.assertEqual(cell["canonical_latest"]["run_id"], "fresh-evidence")
        self.assertEqual(payload["by_acut"]["cheap-generic-swe"]["score_percent_fixed_denominator"], 0.0)

    def test_predictivity_marks_gscore_unavailable_as_not_computable(self) -> None:
        """Prediction analysis must not treat missing direct G_score as zero."""
        rbench = {
            "split": "rbench",
            "by_acut": {
                "cheap-generic-swe": {
                    "score_percent_fixed_denominator": 50.0,
                    "passed": 1,
                    "fixed_denominator": 2,
                    "scoreable": 2,
                    "canonical_present": 2,
                    "canonical_missing": 0,
                    "wilson_95_fixed_denominator": {"lower": 0.1, "upper": 0.9},
                }
            },
        }
        rwork = {
            "split": "rwork",
            "by_acut": {
                "cheap-generic-swe": {
                    "score_percent_fixed_denominator": 0.0,
                    "passed": 0,
                    "fixed_denominator": 2,
                    "scoreable": 2,
                    "canonical_present": 2,
                    "canonical_missing": 0,
                    "wilson_95_fixed_denominator": {"lower": 0.0, "upper": 0.6},
                }
            },
        }
        gscore = {"status": "direct_gscore_blocked", "g_score_basis": "direct_run_unavailable", "direct_gscore_used": False}

        payload = predictivity.build_analysis(rbench, rwork, gscore)

        self.assertEqual(payload["predictivity"]["r_score_vs_w_score_error"]["status"], "computed")
        self.assertEqual(payload["predictivity"]["g_score_vs_w_score_error"]["status"], "not_computable")
        self.assertIsNone(payload["g_score"]["by_acut"]["cheap-generic-swe"]["score_percent"])

    def test_gscore_basis_does_not_block_on_docker_when_primary_backend_is_modal(self) -> None:
        """Regression: local Docker fallback cannot block a config whose primary backend is Modal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_path = root / "test.parquet"
            cache_path.write_text("dataset", encoding="utf-8")
            harness_path = root / "SWE-bench_Pro-os"
            harness_path.mkdir()
            config = {
                "benchmark": {
                    "evaluation_harness": {
                        "repo": "scaleapi/SWE-bench_Pro-os",
                        "execution_backend_preference": {
                            "primary": "Modal",
                            "fallback": "local Docker with --use_local_docker",
                        },
                    }
                },
                "task_subset": {
                    "materialization_attempt": {
                        "cache_path": str(cache_path),
                    }
                },
            }

            with (
                mock.patch.object(gscore_basis, "load_manifest", return_value=config),
                mock.patch.object(gscore_basis, "likely_harness_paths", return_value=[harness_path]),
                mock.patch.object(
                    gscore_basis,
                    "run_capture",
                    return_value={"available": False, "exit_code": 127, "stderr": "docker missing"},
                ),
            ):
                payload = gscore_basis.build_basis(root / "config.yaml")

        self.assertEqual(payload["status"], "direct_gscore_feasible")
        self.assertFalse(payload["checks"]["docker"]["required_for_selected_backend"])
        self.assertNotIn("docker_unavailable", {item["blocker"] for item in payload["blockers"]})


if __name__ == "__main__":
    unittest.main()
