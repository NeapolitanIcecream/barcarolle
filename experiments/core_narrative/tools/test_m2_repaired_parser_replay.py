#!/usr/bin/env python3
"""Executable specs for M2 repaired-parser historical replay."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import m2_repaired_parser_replay as replay


class M2RepairedParserReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def init_workspace(self, name: str, files: dict[str, str]) -> Path:
        workspace = self.root / name
        workspace.mkdir()
        for relative, text in files.items():
            path = workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        subprocess.run(["git", "add", "."], cwd=workspace, check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-qm", "init"],
            cwd=workspace,
            check=True,
        )
        return workspace

    def write_json(self, path: Path, payload: dict[str, object]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_raw_artifacts(self, run_id: str, workspace: Path, response_text: str) -> tuple[Path, Path]:
        artifact_dir = self.root / "raw" / run_id
        raw = self.write_json(
            artifact_dir / "provider_response.redacted.json",
            {"choices": [{"message": {"content": response_text}}], "usage": {"cost": 0.123}},
        )
        self.write_json(
            artifact_dir / "batch_run_result.json",
            {
                "run_id": run_id,
                "workspace": str(workspace),
                "runner_workspace": str(workspace),
                "context_paths": ["module.py"],
            },
        )
        prompt = self.write_json(
            artifact_dir / "prompt_snapshot.json",
            {"context_files": [{"path": "module.py"}]},
        )
        return raw, prompt

    def write_summary(self, records: list[dict[str, object]], *, fixed_denominator: int | None = None) -> Path:
        summary = {
            "tool": "m2_scoreability_summary",
            "status": "completed",
            "claim_status": "scoreability_gate_not_met",
            "tasks": ["task_1"],
            "acuts": ["acut_1"],
            "fixed_denominator": fixed_denominator if fixed_denominator is not None else len(records),
            "paths": {
                "patch_or_files_v1_live": {
                    "total": fixed_denominator if fixed_denominator is not None else len(records),
                    "status_counts": {"invalid_submission": len(records)},
                    "failure_owner_counts": {"model_output": len(records)},
                    "failure_class_counts": {"unsupported_patch_response": len(records)},
                    "patch_ready_coverage": 0.0,
                    "invalid_submission_rate": 1.0,
                    "gate": {"status": "failed"},
                }
            },
            "records": {"patch_or_files_v1_live": records},
        }
        return self.write_json(self.root / "m2-summary.json", summary)

    def run_replay(self, summary: Path) -> dict[str, object]:
        output = self.root / "replay.json"
        report = self.root / "replay.md"
        code = replay.main(
            [
                "--m2-summary",
                str(summary),
                "--workspace-mode",
                "existing",
                "--raw-root",
                str(self.root / "replay-raw"),
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())
        return json.loads(output.read_text(encoding="utf-8"))

    def test_unsupported_apply_patch_transcript_can_replay_as_patch_ready(self) -> None:
        """Regression: unsupported historical Codex transcripts are replayed by the repaired parser."""
        workspace = self.init_workspace("success-workspace", {"module.py": "VALUE = 1\n"})
        raw, prompt = self.write_raw_artifacts(
            "success-run",
            workspace,
            "*** Begin Patch\n*** Update File: module.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch\n",
        )
        summary = self.write_summary(
            [
                {
                    "acut_id": "acut_1",
                    "task_id": "task_1",
                    "run_id": "success-run",
                    "status": "invalid_submission",
                    "failure_owner": "model_output",
                    "failure_class": "unsupported_patch_response",
                    "patch_ready": False,
                    "model_call_made": True,
                    "raw_response_artifact": str(raw),
                    "prompt_snapshot": str(prompt),
                }
            ]
        )

        payload = self.run_replay(summary)

        row = payload["matrix"][0]
        self.assertEqual(row["old"]["failure_class"], "unsupported_patch_response")
        self.assertEqual(row["repaired"]["status"], "patch_ready")
        self.assertEqual(row["repaired"]["parser_kind"], "apply_patch")
        self.assertTrue(row["repaired"]["patch_ready"])
        self.assertEqual(payload["repaired_summary"]["patch_ready_count"], 1)
        self.assertEqual(payload["repaired_summary"]["failure_owner_counts"], {"candidate_patch": 1})

    def test_apply_patch_context_mismatch_is_reclassified_as_model_output(self) -> None:
        """Regression: parsed transcripts with stale context are not counted as parser support."""
        workspace = self.init_workspace("mismatch-workspace", {"module.py": "VALUE = 1\n"})
        raw, prompt = self.write_raw_artifacts(
            "mismatch-run",
            workspace,
            "*** Begin Patch\n*** Update File: module.py\n@@\n-VALUE = 3\n+VALUE = 4\n*** End Patch\n",
        )
        summary = self.write_summary(
            [
                {
                    "acut_id": "acut_1",
                    "task_id": "task_1",
                    "run_id": "mismatch-run",
                    "status": "invalid_submission",
                    "failure_owner": "model_output",
                    "failure_class": "unsupported_patch_response",
                    "patch_ready": False,
                    "model_call_made": True,
                    "raw_response_artifact": str(raw),
                    "prompt_snapshot": str(prompt),
                }
            ]
        )

        payload = self.run_replay(summary)

        row = payload["matrix"][0]
        self.assertEqual(row["repaired"]["status"], "invalid_submission")
        self.assertEqual(row["repaired"]["failure_owner"], "model_output")
        self.assertEqual(row["repaired"]["failure_class"], "apply_patch_context_mismatch")
        self.assertEqual(row["classification_delta"], "unsupported_patch_response -> apply_patch_context_mismatch")
        self.assertEqual(payload["repaired_summary"]["failure_class_counts"], {"apply_patch_context_mismatch": 1})

    def test_missing_raw_response_is_counted_without_model_calls(self) -> None:
        """Missing historical artifacts stay in the denominator and do not trigger live calls."""
        summary = self.write_summary(
            [
                {
                    "acut_id": "acut_1",
                    "task_id": "task_1",
                    "run_id": "missing-run",
                    "status": "infra_failed",
                    "failure_owner": "infrastructure",
                    "failure_class": None,
                    "patch_ready": False,
                    "model_call_made": True,
                    "raw_response_artifact": None,
                    "prompt_snapshot": None,
                }
            ]
        )

        payload = self.run_replay(summary)

        row = payload["matrix"][0]
        self.assertFalse(row["repaired"]["attempted"])
        self.assertEqual(row["repaired"]["status"], "missing_replay_input")
        self.assertEqual(row["repaired"]["failure_class"], "missing_raw_response_artifact")
        self.assertEqual(payload["missing_artifact_summary"]["raw_response_artifact_missing_count"], 1)
        self.assertFalse(payload["cost_model_call_flags"]["replay"]["model_call_made"])
        self.assertEqual(payload["cost_model_call_flags"]["replay"]["model_spend_usd"], 0.0)

    def test_payload_has_no_unsupported_capability_claims(self) -> None:
        """The replay artifact records scoreability only, not M2 passage or capability uplift."""
        summary = self.write_summary(
            [
                {
                    "acut_id": "acut_1",
                    "task_id": "task_1",
                    "run_id": "missing-run",
                    "status": "missing",
                    "failure_owner": "missing",
                    "failure_class": None,
                    "patch_ready": False,
                    "model_call_made": None,
                    "raw_response_artifact": None,
                    "prompt_snapshot": None,
                }
            ]
        )

        payload = self.run_replay(summary)

        self.assertEqual(payload["claim_status"], "historical_replay_not_m2_pass")
        for claim, value in payload["prohibited_claims"].items():
            self.assertFalse(value, claim)
        self.assertFalse(payload["claim_boundaries"]["m2_passed"])
        self.assertFalse(payload["claim_boundaries"]["new_model_calls"])


if __name__ == "__main__":
    unittest.main()
