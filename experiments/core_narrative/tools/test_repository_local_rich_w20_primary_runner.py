#!/usr/bin/env python3
"""Executable specs for the Rich-W20 primary runner."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "experiments" / "core_narrative" / "tools"
RUNNER_PATH = TOOLS_DIR / "repository_local_rich_w20_primary_runner.py"


def load_module():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location("repository_local_rich_w20_primary_runner_under_test", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task(split: str, index: int) -> dict[str, object]:
    return {
        "protocol_task_id": f"rich__{split.lower()}__{index:03d}",
        "split": split,
        "task_pack_path": f"experiments/core_narrative/large_artifacts/unit/{split}/{index}/candidate_task_pack/task.json",
        "source_artifact": "experiments/core_narrative/results/unit.json",
    }


def acut(slot: str, acut_id: str) -> dict[str, object]:
    return {
        "slot": slot,
        "role": "unit",
        "acut_id": acut_id,
        "manifest": f"experiments/core_narrative/configs/acuts/{acut_id}.yaml",
        "model": "gpt-5.4-mini",
    }


class RepositoryLocalRichW20PrimaryRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_validate_start_gates_requires_start_decision_and_live_preflight(self) -> None:
        """Live primary execution is blocked until the owner decision and preflight pass."""
        runner = load_module()
        readiness = {
            "protocol_id": runner.RUNNER_ID,
            "pre_primary_checks": {"all_primary_checks_pass": True},
            "runner_concurrency_requirement": {"implemented_default_max_workers": 4},
        }

        runner.validate_start_gates(
            readiness,
            {"decision": "authorize_primary_attempts_after_live_preflight"},
            {"status": "passed"},
            {"status": "passed"},
            "live",
        )

        with self.assertRaises(runner.ToolError):
            runner.validate_start_gates(readiness, {"decision": "hold"}, {"status": "passed"}, {"status": "passed"}, "live")
        with self.assertRaises(runner.ToolError):
            runner.validate_start_gates(
                readiness,
                {"decision": "authorize_primary_attempts_after_live_preflight"},
                {"status": "blocked"},
                {"status": "passed"},
                "live",
            )
        with self.assertRaises(runner.ToolError):
            runner.validate_start_gates(
                readiness,
                {"decision": "authorize_primary_attempts_after_live_preflight"},
                {"status": "passed"},
                {"status": "blocked"},
                "live",
            )

    def test_run_cells_uses_configured_concurrency_and_preserves_result_order(self) -> None:
        """The Rich-W20 runner can execute four cells concurrently without reordering results."""
        runner = load_module()
        cells = [
            (task("W_star", 1), acut("A0", "cheap-generic-swe")),
            (task("W_star", 1), acut("A1", "cheap-rich-inert-control-v1")),
            (task("R", 1), acut("A0", "cheap-generic-swe")),
            (task("R", 1), acut("A1", "cheap-rich-inert-control-v1")),
        ]
        args = SimpleNamespace(max_workers=4, limit=None)
        submitted: list[tuple[str, str]] = []

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
                task_row = kwargs["task"]
                acut_row = kwargs["acut"]
                submitted.append((task_row["protocol_task_id"], acut_row["acut_id"]))
                return FakeFuture({"run_id": f"{task_row['protocol_task_id']}::{acut_row['acut_id']}"})

        with mock.patch.object(runner.concurrent.futures, "ThreadPoolExecutor", FakeExecutor):
            records = runner.run_cells(cells, args)

        self.assertEqual(FakeExecutor.max_workers_seen, 4)
        self.assertEqual(submitted, [(row[0]["protocol_task_id"], row[1]["acut_id"]) for row in cells])
        self.assertEqual(
            [record["run_id"] for record in records],
            [f"{row[0]['protocol_task_id']}::{row[1]['acut_id']}" for row in cells],
        )

    def test_normalized_workspace_payload_omits_raw_commit_and_subject_fields(self) -> None:
        """Public normalized results keep digests and private paths without copying raw task source fields."""
        runner = load_module()
        artifact_dir = self.root / "private/raw/run"
        normalized_path = self.root / "public/normalized/run.json"
        artifact_dir.mkdir(parents=True)
        payload = {
            "schema_version": "core-narrative.workspace-mode-execution.v1",
            "tool": "workspace_mode_runner",
            "run_id": "run",
            "acut_id": "cheap-generic-swe",
            "task_id": "rich__wstar__001",
            "split": "W_star",
            "attempt": 1,
            "status": "verified_pass",
            "started_at": "start",
            "finished_at": "finish",
            "candidate_patch": {"sha256": "abc", "size_bytes": 1, "has_scoreable_diff": True},
            "verification": {"attempted": True, "verifier_exit_code": 0},
            "prepare": {
                "base_commit": "a" * 40,
                "subject": "raw subject must not appear",
            },
        }

        normalized = runner.normalize_workspace_payload(
            payload=payload,
            task=task("W_star", 1),
            acut=acut("A0", "cheap-generic-swe"),
            run_id="run",
            command={"command": ["workspace_mode_runner.py"], "mode": "live"},
            artifact_dir_path=artifact_dir,
            normalized_result_path=normalized_path,
        )

        rendered = json.dumps(normalized, sort_keys=True)
        self.assertEqual(normalized["status"], "verified_pass")
        self.assertNotIn("base_commit", rendered)
        self.assertNotIn("target_commit", rendered)
        self.assertNotIn('"subject"', rendered)
        self.assertNotIn("raw subject must not appear", rendered)

    def test_normalized_workspace_payload_marks_codex_exec_failure_as_infra_block(self) -> None:
        """A failed model backend call is rerun-required infrastructure, not a no-diff model zero."""
        runner = load_module()
        artifact_dir = self.root / "private/raw/run"
        normalized_path = self.root / "public/normalized/run.json"
        artifact_dir.mkdir(parents=True)
        (artifact_dir / "codex_cli_patch_command.json").write_text(
            json.dumps(
                {
                    "tool": "codex_cli_patch_command",
                    "status": "codex_exec_failed",
                    "model": "gpt-5.4-mini",
                    "model_call_made": True,
                    "codex_exec": {"exit_code": 1, "timed_out": False},
                    "failure_capture": {"failure_class": "nonzero_exit"},
                }
            ),
            encoding="utf-8",
        )
        payload = {
            "schema_version": "core-narrative.workspace-mode-execution.v1",
            "tool": "workspace_mode_runner",
            "run_id": "run",
            "acut_id": "cheap-generic-swe",
            "task_id": "rich__wstar__001",
            "split": "W_star",
            "attempt": 1,
            "status": "no_diff",
            "candidate_patch": {"sha256": None, "size_bytes": 0, "has_scoreable_diff": False},
            "verification": {"attempted": False},
        }

        normalized = runner.normalize_workspace_payload(
            payload=payload,
            task=task("W_star", 1),
            acut=acut("A0", "cheap-generic-swe"),
            run_id="run",
            command={"command": ["workspace_mode_runner.py"], "mode": "live"},
            artifact_dir_path=artifact_dir,
            normalized_result_path=normalized_path,
        )

        self.assertEqual(normalized["workspace_mode_status"], "no_diff")
        self.assertEqual(normalized["status"], "llm_backend_unavailable")
        self.assertEqual(normalized["score_action"], "rerun_or_global_exclusion_required")
        self.assertTrue(normalized["requires_rerun_or_exclusion"])
        self.assertEqual(normalized["metadata"]["llm_backend"]["codex_exec_exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
