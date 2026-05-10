#!/usr/bin/env python3
"""Executable specs for M2.5 workspace-diff-v1 scoreability recovery."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from typing import Any
from pathlib import Path

import m2_5_workspace_diff_runner as runner


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


class M25WorkspaceDiffRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def init_repo(self) -> Path:
        workspace = self.root / "workspace"
        workspace.mkdir()
        self.assertEqual(git(workspace, "init", "-q").returncode, 0)
        self.assertEqual(git(workspace, "config", "user.email", "codex@example.com").returncode, 0)
        self.assertEqual(git(workspace, "config", "user.name", "Codex").returncode, 0)
        (workspace / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.assertEqual(git(workspace, "add", "module.py").returncode, 0)
        self.assertEqual(git(workspace, "commit", "-q", "-m", "base").returncode, 0)
        return workspace

    def test_synthetic_workspace_modification_becomes_non_empty_candidate_patch(self) -> None:
        """A no-model workspace source edit is collected as a verifier-ready patch artifact."""
        workspace = self.init_repo()
        (workspace / "module.py").write_text("VALUE = 2\n", encoding="utf-8")

        result = runner.collect_workspace_candidate_patch(workspace, self.root / "submission.patch", {})

        self.assertTrue(result["patch_ready"])
        self.assertEqual(result["status"], "candidate_patch_ready")
        self.assertGreater(result["candidate_patch_size_bytes"], 0)
        self.assertIsNotNone(result["candidate_patch_sha256"])
        self.assertIn("diff --git a/module.py b/module.py", (self.root / "submission.patch").read_text(encoding="utf-8"))

    def test_noop_workspace_modification_is_separate_from_infrastructure_failure(self) -> None:
        """No source diff is an invalid candidate patch, not an infra failure."""
        workspace = self.init_repo()

        result = runner.collect_workspace_candidate_patch(workspace, self.root / "submission.patch", {})

        self.assertFalse(result["patch_ready"])
        self.assertEqual(result["failure_owner"], "candidate_patch")
        self.assertEqual(result["failure_class"], "no_workspace_patch")
        self.assertEqual(result["status"], "no_verifier_ready_source_patch")

    def test_reserved_generated_artifacts_do_not_become_verifier_ready_source_patches(self) -> None:
        """Runner-owned untracked artifacts under .core_narrative or .git are excluded from source patches."""
        workspace = self.init_repo()
        (workspace / ".core_narrative").mkdir()
        (workspace / ".core_narrative" / "generated.txt").write_text("unsafe https://example.invalid\n", encoding="utf-8")
        (workspace / ".git" / "generated-by-agent").write_text("metadata\n", encoding="utf-8")

        result = runner.collect_workspace_candidate_patch(workspace, self.root / "submission.patch", {})

        self.assertFalse(result["patch_ready"])
        self.assertEqual(result["failure_class"], "reserved_generated_artifact_only")
        patch_text = (self.root / "submission.patch").read_text(encoding="utf-8")
        self.assertNotIn(".core_narrative", patch_text)
        self.assertNotIn("https://example.invalid", patch_text)

    def test_summary_carries_owner_attemptability_replay_status_and_digest_fields(self) -> None:
        """The aggregate has admission-relevant machine-readable fields, not only prose counts."""
        results = [
            {
                "run_id": "run-1",
                "acut_id": "cheap-generic-swe",
                "task_id": "click__rwork__003",
                "status": "failed",
                "patch_ready": True,
                "attemptable": True,
                "failure_owner": "candidate_patch",
                "failure_class": "none",
                "clean_replay_status": "success",
                "candidate_patch_sha256": "a" * 64,
                "task_manifest_sha256": "b" * 64,
                "acut_manifest_sha256": "c" * 64,
                "verifier_digest_sha256": "d" * 64,
            },
            {
                "run_id": "run-2",
                "acut_id": "cheap-click-specialist",
                "task_id": "click__rwork__003",
                "status": "invalid_submission",
                "patch_ready": False,
                "attemptable": False,
                "failure_owner": "candidate_patch",
                "failure_class": "no_workspace_patch",
                "clean_replay_status": "not_attempted",
                "candidate_patch_sha256": None,
                "task_manifest_sha256": "b" * 64,
                "acut_manifest_sha256": "c" * 64,
                "verifier_digest_sha256": "d" * 64,
            },
        ]

        summary = runner.summarize_results(results, fixed_denominator=2, blocked=False)

        self.assertEqual(summary["failure_owner_counts"]["candidate_patch"], 2)
        self.assertEqual(summary["failure_class_counts"]["no_workspace_patch"], 1)
        self.assertEqual(summary["attemptability_score"], 0.5)
        self.assertEqual(summary["clean_replay_success_count"], 1)
        self.assertTrue(summary["digest_fields_present"]["task_manifest_sha256"])
        self.assertTrue(summary["digest_fields_present"]["acut_manifest_sha256"])
        self.assertTrue(summary["digest_fields_present"]["verifier_digest_sha256"])
        self.assertTrue(summary["digest_fields_present"]["candidate_patch_sha256"])

    def test_invalid_clean_replay_preserves_patch_availability_and_replay_failure(self) -> None:
        """Regression: invalid clean replay must not erase a persisted non-empty workspace diff."""
        patch_path = self.root / "submission.patch"
        patch_path.write_text(
            "diff --git a/module.py b/module.py\n"
            "index 1234567..89abcde 100644\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -1 +1 @@\n"
            "-VALUE = 1\n"
            "+VALUE = 2\n",
            encoding="utf-8",
        )
        normalized_path = self.root / "normalized.json"
        normalized: dict[str, Any] = {
            "status": "invalid_submission",
            "metadata": {
                "tool": "apply_and_verify",
                "verifier_command": ["python", "-m", "pytest"],
            },
            "error": "git apply --check failed",
        }
        candidate_collection = {
            "patch_ready": True,
            "patch_artifact": {
                "written": True,
                "unsafe_content_detected": False,
                "size_bytes": patch_path.stat().st_size,
            },
            "untracked_scope": {"checked": True, "reserved_count": 0, "source_count": 0},
        }

        enriched = runner.enrich_normalized_metadata(
            normalized=normalized,
            normalized_path=normalized_path,
            task_id="click__rwork__003",
            acut_id="cheap-generic-swe",
            runner_workspace=self.root / "runner",
            verify_workspace=self.root / "verify",
            patch_path=patch_path,
            candidate_collection=candidate_collection,
            mode="live",
            model_call_made=True,
        )

        readiness = enriched["metadata"]["patch_readiness"]
        replay = enriched["metadata"]["clean_patch_replay"]
        verifier_attempt = enriched["metadata"]["verifier_attempt"]
        self.assertTrue(readiness["verifier_ready_patch_available"])
        self.assertTrue(readiness["patch_artifact_persisted"])
        self.assertTrue(readiness["clean_replay_attempted"])
        self.assertEqual(replay["status"], "invalid_submission")
        self.assertEqual(replay["failure_class"], "clean_replay_invalid_submission")
        self.assertTrue(verifier_attempt["attempted"])

    def test_live_adapter_unsafe_attribution_survives_empty_followup_collection(self) -> None:
        """Unsafe adapter attribution remains visible after restored workspace collection is empty."""
        patch_path = self.root / "submission.patch"
        patch_path.write_text("", encoding="utf-8")
        normalized_path = self.root / "normalized.json"
        candidate_collection = {
            "patch_ready": False,
            "patch_artifact": {
                "written": True,
                "unsafe_content_detected": False,
                "size_bytes": 0,
            },
            "untracked_scope": {"checked": True, "reserved_count": 0, "source_count": 0},
        }
        adapter_patch_artifact = {
            "written": False,
            "unsafe_content_detected": True,
            "unsafe_content_attribution": {
                "classification": "source_derived_full_url",
                "content_recorded": False,
            },
        }

        enriched = runner.enrich_normalized_metadata(
            normalized={"status": "invalid_submission", "metadata": {}, "error": "unsafe patch rejected"},
            normalized_path=normalized_path,
            task_id="click__rwork__006",
            acut_id="cheap-generic-swe",
            runner_workspace=self.root / "runner",
            verify_workspace=None,
            patch_path=patch_path,
            candidate_collection=candidate_collection,
            mode="live",
            model_call_made=True,
            adapter_patch_artifact=adapter_patch_artifact,
            failure_owner="model_output",
            failure_class="unsafe_patch_content",
        )

        workspace_diff = enriched["metadata"]["workspace_diff"]
        self.assertTrue(workspace_diff["unsafe_content_detected"])
        self.assertFalse(workspace_diff["collection_unsafe_content_detected"])
        self.assertTrue(workspace_diff["adapter_unsafe_content_detected"])
        self.assertEqual(workspace_diff["unsafe_content_source"], "live_adapter_workspace_diff_collection")
        self.assertEqual(workspace_diff["unsafe_content_attribution"]["classification"], "source_derived_full_url")


if __name__ == "__main__":
    unittest.main()
