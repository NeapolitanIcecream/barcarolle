#!/usr/bin/env python3
"""Executable specs for no-model unsafe_generated_text triage."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import unsafe_generated_text_triage as triage


class UnsafeGeneratedTextTriageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_json(self, name: str, payload: dict[str, object]) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def write_provider(self, name: str, content: str) -> Path:
        return self.write_json(
            name,
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": content,
                            "reasoning": "",
                            "reasoning_details": [],
                            "refusal": None,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {},
            },
        )

    def git_workspace(self, name: str, *, mutated: bool) -> Path:
        workspace = self.root / name
        workspace.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
        source = workspace / "src.py"
        source.write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "src.py"], cwd=workspace, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Barcarolle Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-q",
                "-m",
                "init",
            ],
            cwd=workspace,
            check=True,
        )
        if mutated:
            source.write_text("changed\n", encoding="utf-8")
        return workspace

    def result(
        self,
        *,
        acut: str,
        task: str,
        provider_path: Path,
        workspace: Path,
        error: str,
        reason_counts: dict[str, int],
    ) -> dict[str, object]:
        run_id = f"unit__{acut}__{task}"
        runner = {
            "status": "error",
            "error": error,
            "submission_contract": "structured-files-json-v1",
            "output_contract": "structured-files-json-v1",
            "model_call_made": True,
            "raw_response_artifact": str(provider_path),
            "details": {
                "failure_class": "unsafe_generated_text",
                "unsafe_content": {
                    "unsafe": bool(reason_counts),
                    "reason_counts": reason_counts,
                    "resolved_env_var_names": [],
                },
            },
        }
        normalized = {
            "status": "invalid_submission",
            "error": error,
            "metadata": {
                "failure_owner": "model_output",
                "failure_class": "unsafe_generated_text",
                "submission_contract": "structured-files-json-v1",
                "output_contract": "structured-files-json-v1",
                "model_call_made": True,
                "raw_response_artifact": str(provider_path),
                "patch_readiness": {
                    "verifier_ready_patch_available": False,
                    "clean_replay_attempted": False,
                    "patch_size_bytes": None,
                },
                "clean_patch_replay": {"attempted": False},
            },
            "verification": {"exit_code": None},
        }
        return {
            "run_id": run_id,
            "acut_id": acut,
            "task_id": task,
            "status": "invalid_submission",
            "submission_contract": "structured-files-json-v1",
            "raw_response_artifact": str(provider_path),
            "workspace": str(workspace),
            "patch_path": str(self.root / f"{run_id}.patch"),
            "runner_result": runner,
            "normalized": normalized,
        }

    def build(self, batch: dict[str, object], *, acuts: tuple[str, ...], tasks: tuple[str, ...]) -> dict[str, object]:
        return triage.build_triage(
            batch=batch,
            batch_path=None,
            repo_root=self.root,
            acuts=acuts,
            tasks=tasks,
        )

    def test_model_response_full_url_is_safety_policy_true_positive(self) -> None:
        """A model-response full-url finding is triaged as a configured safety hit."""
        provider = self.write_provider("provider.json", '{"files":[],"note":"<redacted:url>"}')
        workspace = self.git_workspace("workspace", mutated=False)
        payload = self.build(
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__004",
                        provider_path=provider,
                        workspace=workspace,
                        error="model response contains unsafe content",
                        reason_counts={"full_url": 1},
                    )
                ]
            },
            acuts=("cheap-generic-swe",),
            tasks=("click__rwork__004",),
        )

        self.assertEqual(payload["cells"][0]["classification"], triage.TRUE_POSITIVE)
        self.assertTrue(payload["cells"][0]["enough_redacted_evidence"])

    def test_patch_artifact_full_url_after_workspace_mutation_is_overbreadth(self) -> None:
        """Patch-artifact URL findings after mutation are not treated as capability evidence."""
        provider = self.write_provider("provider.json", '{"files":[{"path":"src.py","content":"changed"}]}')
        workspace = self.git_workspace("workspace", mutated=True)
        payload = self.build(
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__006",
                        provider_path=provider,
                        workspace=workspace,
                        error="generated patch contains unsafe content",
                        reason_counts={"full_url": 2},
                    )
                ]
            },
            acuts=("cheap-generic-swe",),
            tasks=("click__rwork__006",),
        )

        cell = payload["cells"][0]
        self.assertEqual(cell["classification"], triage.OVERBREADTH)
        self.assertFalse(cell["patch_written"])
        self.assertTrue(cell["workspace"]["workspace_mutation_happened"])

    def test_missing_redacted_provider_artifact_is_ambiguous(self) -> None:
        """Without a valid redacted provider artifact, the source attribution is ambiguous."""
        workspace = self.git_workspace("workspace", mutated=False)
        payload = self.build(
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__004",
                        provider_path=self.root / "missing-provider.json",
                        workspace=workspace,
                        error="generated patch contains unsafe content",
                        reason_counts={"full_url": 1},
                    )
                ]
            },
            acuts=("cheap-generic-swe",),
            tasks=("click__rwork__004",),
        )

        self.assertEqual(payload["cells"][0]["classification"], triage.AMBIGUOUS)
        self.assertFalse(payload["cells"][0]["enough_redacted_evidence"])

    def test_default_target_set_uses_fixed_four_cell_denominator(self) -> None:
        """The default triage scope is exactly 2 ACUTs x 2 RWork target cells."""
        payload = self.build({"results": []}, acuts=triage.DEFAULT_ACUTS, tasks=triage.DEFAULT_TASKS)

        self.assertEqual(payload["fixed_denominator"]["total"], 4)
        self.assertEqual(payload["fixed_denominator"]["missing_cell_count"], 4)
        self.assertEqual(len(payload["cells"]), 4)

    def test_output_does_not_leak_raw_unsafe_provider_text(self) -> None:
        """Raw provider text can be counted without being copied to the output."""
        raw_url = "https://unsafe.example/path?token=abc"
        provider = self.write_provider("provider.json", f'{{"files":[],"note":"{raw_url}"}}')
        workspace = self.git_workspace("workspace", mutated=False)
        payload = self.build(
            {
                "results": [
                    self.result(
                        acut="cheap-generic-swe",
                        task="click__rwork__004",
                        provider_path=provider,
                        workspace=workspace,
                        error="model response contains unsafe content",
                        reason_counts={"full_url": 1},
                    )
                ]
            },
            acuts=("cheap-generic-swe",),
            tasks=("click__rwork__004",),
        )

        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotIn(raw_url, serialized)
        self.assertNotRegex(serialized, r"https?://")
        self.assertEqual(payload["cells"][0]["redacted_provider_artifact"]["raw_url_like_count"], 1)
        self.assertFalse(payload["output_leakage_guard"]["contains_raw_unsafe_text"])


if __name__ == "__main__":
    unittest.main()
