#!/usr/bin/env python3
"""Executable specs for M2 unsafe patch-artifact repair evidence."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m2_unsafe_artifact_repair as repair


class M2UnsafeArtifactRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_no_spend_fixtures_distinguish_source_overbreadth_true_positive_and_ambiguity(self) -> None:
        """The repair report records source-vs-generated unsafe artifact evidence without raw text."""
        prior_live = self.write_json("prior-live.json", {"results": []})
        blocker = self.write_json(
            "blocker.json",
            {
                "status": "blocked",
                "blockers": ["missing_required_llm_environment"],
                "model_call_made": False,
            },
        )
        output = self.root / "m2-unsafe-repair.json"
        report = self.root / "m2-unsafe-repair.md"

        code = repair.main(
            [
                "--prior-live-smoke",
                str(prior_live),
                "--live-smoke-blocker",
                str(blocker),
                "--run-prefix",
                "unit_m2_unsafe_artifact_repair",
                "--raw-root",
                str(self.root / "raw"),
                "--workspace-root",
                str(self.root / "workspaces"),
                "--force",
                "--output",
                str(output),
                "--report",
                str(report),
            ]
        )

        self.assertEqual(code, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        rows = {row["fixture_id"]: row for row in payload["matrix"]}

        source_row = rows["redacted_source_old_safe_replacement_source_url_artifact"]
        self.assertEqual(source_row["classification"], repair.SOURCE_OVERBREADTH)
        attribution = source_row["patch_artifact"]["unsafe_content_attribution"]
        self.assertEqual(attribution["classification"], "source_derived_full_url")
        self.assertTrue(attribution["all_unsafe_reasons_source_derived"])
        self.assertEqual(attribution["model_generated_full_url_count"], 0)
        self.assertEqual(attribution["full_url_role_counts"], {"source_removed": 1})
        self.assertFalse(source_row["patch_artifact"]["written"])
        self.assertTrue(source_row["patch_artifact"]["redacted_preview"]["written"])
        self.assertEqual(
            source_row["patch"]["edit_diagnostics"][0]["diagnostic"]["code"],
            "redacted_source_text_matched_raw_source",
        )

        generated_row = rows["model_generated_raw_url_replacement_true_positive"]
        self.assertEqual(generated_row["classification"], repair.TRUE_POSITIVE)
        self.assertEqual(generated_row["failure_class"], "unsafe_generated_text")
        self.assertEqual(generated_row["details"]["unsafe_content"]["reason_counts"], {"full_url": 1})
        self.assertFalse(generated_row["patch_ready"])

        placeholder_row = rows["redaction_placeholder_persistence_rejection"]
        self.assertEqual(placeholder_row["classification"], repair.PLACEHOLDER_REJECTED)
        self.assertEqual(placeholder_row["failure_class"], "search_replace_redacted_source_mismatch")
        self.assertEqual(
            placeholder_row["details"]["diagnostic"]["code"],
            "redacted_replacement_placeholder_persistence",
        )

        missing_row = rows["missing_raw_artifact_ambiguity"]
        self.assertEqual(missing_row["classification"], repair.AMBIGUOUS)
        self.assertEqual(missing_row["failure_class"], "missing_raw_response_artifact")
        self.assertFalse(missing_row["provider_artifact"]["exists"])

        self.assertEqual(
            payload["fixture_summary"]["classification_counts"],
            {
                repair.AMBIGUOUS: 1,
                repair.PLACEHOLDER_REJECTED: 1,
                repair.SOURCE_OVERBREADTH: 1,
                repair.TRUE_POSITIVE: 1,
            },
        )
        self.assertFalse(payload["cost_model_call_flags"]["fixtures"]["model_call_made"])
        self.assertFalse(payload["post_repair_live_smoke"]["model_call_made"])
        self.assertFalse(payload["output_leakage_guard"]["contains_raw_unsafe_text"])

        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotRegex(serialized, r"https?://")
        self.assertIn("M2 Unsafe Patch-Artifact Repair", report.read_text(encoding="utf-8"))

    def test_prior_live_inspection_records_source_derived_patch_artifact_counts(self) -> None:
        """Existing PR10 runner artifacts can be summarized without copying source content."""
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "src").mkdir()
        source = workspace / "src" / "click.py"
        source.write_text('DOC = "https://source.example.invalid/issue"\nVALUE = 1\n', encoding="utf-8")
        repair.run_capture(["git", "init", "-q"], cwd=workspace)
        repair.run_capture(["git", "add", "."], cwd=workspace)
        repair.run_capture(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "init"],
            cwd=workspace,
        )
        source.write_text("VALUE = 1\n", encoding="utf-8")
        artifact_dir = self.root / "live"
        artifact_dir.mkdir()
        provider = self.write_json(
            "live/provider_response.redacted.json",
            {"choices": [{"message": {"content": '{"edits":[],"note":"<redacted:url>"}'}}]},
        )
        prompt = self.write_json(
            "live/prompt_snapshot.json",
            {
                "prompt_sha256": "abc123",
                "prompt_char_count": 10,
                "full_urls_redacted": True,
                "output_contract": repair.CONTRACT,
                "context_files": [{"path": "src/click.py"}],
            },
        )
        prior_live = self.write_json(
            "prior-live.json",
            {
                "results": [
                    {
                        "acut_id": "cheap-generic-swe",
                        "task_id": "click__rwork__006",
                        "status": "invalid_submission",
                        "workspace": str(workspace),
                        "raw_response_artifact": str(provider),
                        "prompt_snapshot": str(prompt),
                        "runner_result": {
                            "status": "error",
                            "model_call_made": True,
                            "raw_response_artifact": str(provider),
                            "prompt_snapshot": str(prompt),
                            "details": {
                                "failure_class": "unsafe_generated_text",
                                "unsafe_content": {"reason_counts": {"full_url": 1}},
                                "patch_result_before_patch_artifact": {
                                    "edit_diagnostics": [
                                        {
                                            "diagnostic": {
                                                "code": "redacted_source_text_matched_raw_source",
                                                "replacement_contains_redacted_url_marker": False,
                                            },
                                            "content_recorded": False,
                                        }
                                    ]
                                },
                            },
                        },
                    }
                ]
            },
        )

        inspected = repair.inspect_prior_live_smoke(str(prior_live))

        self.assertEqual(inspected["status"], "inspected")
        self.assertEqual(inspected["redacted_source_match_count"], 1)
        self.assertEqual(inspected["unsafe_patch_artifact_reason_counts"], {"full_url": 1})
        self.assertEqual(
            inspected["unsafe_patch_artifact_attribution"]["classification"],
            "source_derived_full_url",
        )
        self.assertTrue(
            inspected["unsafe_patch_artifact_attribution"]["all_unsafe_reasons_source_derived"]
        )
        self.assertFalse(inspected["content_recorded"])


if __name__ == "__main__":
    unittest.main()
