#!/usr/bin/env python3
"""Executable specs for the M2 stable nonpersistent replay matrix."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_stable_nonpersistent_replay_matrix as matrix


class M2StableNonpersistentReplayMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, relative: str, payload: dict[str, object]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def raw_response(self, relative: str, text: str, *, cost: float | None = None) -> Path:
        payload: dict[str, object] = {"choices": [{"message": {"content": text}}]}
        if cost is not None:
            payload["usage"] = {"cost": cost}
        return self.write_json(relative, payload)

    def prompt(self, relative: str) -> Path:
        return self.write_json(relative, {"context_files": [{"path": "module.py"}]})

    def normalized(self, relative: str, payload: dict[str, object] | None = None) -> Path:
        return self.write_json(relative, payload or {"schema_version": "core-narrative.run-result.v1"})

    def m2_summary(self) -> Path:
        return self.write_json(
            "m2-summary.json",
            {
                "tool": "m2_scoreability_summary",
                "tasks": ["task_1", "task_2"],
                "acuts": ["acut_1"],
                "fixed_denominator": 2,
                "claim_status": "scoreability_gate_not_met",
            },
        )

    def patch_replay(self, raw: Path, prompt: Path, normalized: Path) -> Path:
        return self.write_json(
            "patch-replay.json",
            {
                "tool": "m2_repaired_parser_replay",
                "scope": {"fixed_denominator": 2},
                "matrix": [
                    {
                        "acut_id": "acut_1",
                        "task_id": "task_1",
                        "run_id": "old-patch-run",
                        "old": {
                            "status": "invalid_submission",
                            "failure_owner": "model_output",
                            "failure_class": "unsupported_patch_response",
                            "patch_ready": False,
                            "model_call_made": True,
                            "raw_response_artifact": str(raw),
                            "prompt_snapshot": str(prompt),
                            "normalized_result": str(normalized),
                            "historical_provider_usage_cost_usd": 0.25,
                        },
                        "repaired": {
                            "status": "patch_ready",
                            "failure_owner": "candidate_patch",
                            "failure_class": None,
                            "patch_ready": True,
                            "clean_replay_attempted": True,
                            "clean_replay_success": True,
                            "clean_replay_status": "applied_to_clean_workspace",
                            "model_call_made": False,
                            "model_spend_usd": 0.0,
                        },
                        "classification_delta": "unsupported_patch_response -> none",
                    },
                    {
                        "acut_id": "acut_1",
                        "task_id": "task_2",
                        "run_id": "missing-patch-run",
                        "old": {
                            "status": "infra_failed",
                            "failure_owner": "infrastructure",
                            "failure_class": None,
                            "patch_ready": False,
                            "model_call_made": True,
                            "raw_response_artifact": None,
                            "prompt_snapshot": None,
                            "normalized_result": None,
                        },
                        "repaired": {
                            "status": "missing_replay_input",
                            "failure_owner": "infrastructure",
                            "failure_class": "missing_raw_response_artifact",
                            "patch_ready": False,
                            "model_call_made": False,
                            "model_spend_usd": 0.0,
                        },
                        "classification_delta": "none -> missing_raw_response_artifact",
                    },
                ],
            },
        )

    def anchored_batch(
        self,
        relative: str,
        *,
        raw: Path,
        prompt: Path,
        normalized: Path,
        status: str,
        model_call_made: bool,
        failure_owner: str,
        failure_class: str | None,
        nonpersistent: bool = False,
        cleanup_removed: bool | None = None,
        verifier_exit_code: int | None = None,
    ) -> Path:
        nonpersistent_channel: dict[str, object] = {"attempted": nonpersistent}
        if nonpersistent:
            nonpersistent_channel.update(
                {
                    "channel": "nonpersistent_preapplied_workspace",
                    "transient_workspace_cleanup": {
                        "attempted": True,
                        "removed": cleanup_removed,
                    },
                }
            )
        metadata: dict[str, object] = {
            "submission_contract": matrix.ANCHORED_CONTRACT,
            "model_call_made": model_call_made,
            "failure_owner": failure_owner,
            "failure_class": failure_class,
            "raw_response_artifact": str(raw),
            "prompt_snapshot": str(prompt),
            "patch_readiness": {
                "verifier_ready_patch_available": False,
                "nonpersistent_verifier_attempted": nonpersistent,
                "verifier_attempt_channel": "nonpersistent_preapplied_workspace" if nonpersistent else "not_attempted",
            },
            "verifier_attempt": {
                "attempted": nonpersistent,
                "channel": "nonpersistent_preapplied_workspace" if nonpersistent else "not_attempted",
                "nonpersistent": nonpersistent,
            },
            "nonpersistent_verifier_channel": nonpersistent_channel,
        }
        normalized_payload = {
            "status": status,
            "metadata": metadata,
            "verification": {"exit_code": verifier_exit_code},
        }
        normalized.write_text(json.dumps(normalized_payload, indent=2, sort_keys=True), encoding="utf-8")
        return self.write_json(
            relative,
            {
                "tool": "codex_nfl_experiment_runner",
                "status": "completed",
                "results": [
                    {
                        "acut_id": "acut_1",
                        "task_id": "task_1",
                        "run_id": relative.replace(".json", ""),
                        "status": status,
                        "normalized_result": str(normalized),
                        "raw_response_artifact": str(raw),
                        "prompt_snapshot": str(prompt),
                        "runner_result": {
                            "status": "error" if status != "failed" else "patch_generated",
                            "model_call_made": model_call_made,
                            "submission_contract": matrix.ANCHORED_CONTRACT,
                            "raw_response_artifact": str(raw),
                            "prompt_snapshot": str(prompt),
                            "details": {"failure_class": failure_class},
                        },
                        "normalized": normalized_payload,
                    }
                ],
            },
        )

    def test_matrix_distinguishes_attemptable_nonpersistent_missing_and_cleanup_categories(self) -> None:
        """Stable replay accounting separates artifact channels without new model-call claims."""
        m2_summary = self.m2_summary()
        patch_raw = self.raw_response("raw/patch/provider_response.redacted.json", "*** Begin Patch\n", cost=0.25)
        patch_prompt = self.prompt("raw/patch/prompt_snapshot.json")
        patch_normalized = self.normalized("normalized/patch.json")
        patch_replay = self.patch_replay(patch_raw, patch_prompt, patch_normalized)

        shared_raw = self.raw_response("raw/anchored/shared_response.json", '{"edits":[]}', cost=0.4)
        shared_prompt = self.prompt("raw/anchored/prompt_snapshot.json")
        historical_norm = self.normalized("normalized/anchored_historical.json")
        replay_norm = self.normalized("normalized/anchored_replay.json")
        cleanup_raw = self.raw_response("raw/anchored/cleanup_response.json", '{"edits":[1]}')
        cleanup_prompt = self.prompt("raw/anchored/cleanup_prompt.json")
        cleanup_norm = self.normalized("normalized/anchored_cleanup.json")

        historical = self.anchored_batch(
            "anchored-historical.json",
            raw=shared_raw,
            prompt=shared_prompt,
            normalized=historical_norm,
            status="invalid_submission",
            model_call_made=True,
            failure_owner="model_output",
            failure_class="unsafe_generated_text",
        )
        no_model_replay = self.anchored_batch(
            "anchored-replay.json",
            raw=shared_raw,
            prompt=shared_prompt,
            normalized=replay_norm,
            status="failed",
            model_call_made=False,
            failure_owner="candidate_patch",
            failure_class=None,
            nonpersistent=True,
            cleanup_removed=True,
            verifier_exit_code=1,
        )
        cleanup_blocker = self.anchored_batch(
            "anchored-cleanup.json",
            raw=cleanup_raw,
            prompt=cleanup_prompt,
            normalized=cleanup_norm,
            status="infra_failed",
            model_call_made=False,
            failure_owner="infrastructure",
            failure_class="nonpersistent_transient_workspace_cleanup_failed",
            nonpersistent=True,
            cleanup_removed=False,
            verifier_exit_code=1,
        )

        args = argparse.Namespace(
            m2_summary=str(m2_summary),
            patch_replay=str(patch_replay),
            anchored_batch=[
                ("historical", "historical_live", str(historical)),
                ("replay", "no_model_replay", str(no_model_replay)),
                ("cleanup", "no_model_replay", str(cleanup_blocker)),
            ],
            output=str(self.root / "out.json"),
            report=str(self.root / "out.md"),
        )

        payload = matrix.build_payload(args)

        self.assertEqual(payload["summary"]["category_counts"]["verifier_ready_persisted_patch_artifact"], 1)
        self.assertEqual(payload["summary"]["category_counts"]["nonpersistent_verifier_attempt"], 1)
        self.assertEqual(payload["summary"]["category_counts"]["model_output_invalid_submission"], 1)
        self.assertEqual(payload["summary"]["category_counts"]["missing_raw_artifact"], 1)
        self.assertEqual(payload["summary"]["category_counts"]["cleanup_blocker"], 1)
        self.assertEqual(payload["summary"]["prior_failures_became_verifier_attemptable_count"], 2)
        self.assertEqual(payload["cost_model_call_accounting"]["replay"]["new_model_call_made_count"], 0)
        self.assertFalse(payload["claim_boundaries"]["new_model_calls"])
        self.assertFalse(payload["output_leakage_guard"]["contains_raw_unsafe_text"])
        self.assertEqual(payload["blockers"][0]["blocker_id"], "anchored_search_replace_fixed_grid_inputs_insufficient")

    def test_report_includes_required_channel_breakout(self) -> None:
        """The human report names the stable categories and claim boundaries."""
        m2_summary = self.m2_summary()
        patch_raw = self.raw_response("raw/patch/provider_response.redacted.json", "*** Begin Patch\n")
        patch_prompt = self.prompt("raw/patch/prompt_snapshot.json")
        patch_normalized = self.normalized("normalized/patch.json")
        patch_replay = self.patch_replay(patch_raw, patch_prompt, patch_normalized)
        args = argparse.Namespace(
            m2_summary=str(m2_summary),
            patch_replay=str(patch_replay),
            anchored_batch=[],
            output=str(self.root / "out.json"),
            report=str(self.root / "out.md"),
        )
        payload = matrix.build_payload(args)

        matrix.write_report(payload, args.report)

        report = Path(args.report).read_text(encoding="utf-8")
        self.assertIn("Persisted patch-artifact attemptable count", report)
        self.assertIn("Nonpersistent verifier attempts", report)
        self.assertIn("This report does not claim M2 passed", report)


if __name__ == "__main__":
    unittest.main()
