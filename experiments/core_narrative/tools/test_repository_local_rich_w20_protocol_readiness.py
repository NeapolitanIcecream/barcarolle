#!/usr/bin/env python3
"""Executable specs for the reduced Rich-W20 protocol readiness artifact."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "experiments" / "core_narrative" / "tools"
RUNNER_PATH = TOOLS_DIR / "repository_local_rich_w20_protocol_readiness.py"
RAW_COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")


def load_module():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location("repository_local_rich_w20_protocol_readiness_under_test", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def accepted_record(split: str, private_root: str, index: int) -> dict[str, object]:
    return {
        "admission_decision": "accepted",
        "batch_candidate_index": index,
        "changed_file_set_digest": f"{index:064x}",
        "family": "parser/mixed integration",
        "hidden_verifier_digest": f"{index + 100:064x}",
        "no_op_result": {"status": "failed", "verifier_exit_code": 1},
        "private_artifact_root": private_root,
        "reference_patch_digest": f"{index + 200:064x}",
        "reference_result": {"status": "passed", "verifier_exit_code": 0},
        "repo_slug": "rich",
        "source_anchor_digest": f"{index + 300:064x}",
        "split": split,
        "statement_digest": f"{index + 400:064x}",
        "subject_digest": f"{index + 500:064x}",
        "surface": "source_without_tests",
        "tool": "unit-rich-pilot",
    }


class RepositoryLocalRichW20ProtocolReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.results = self.root / "experiments/core_narrative/results"
        self.results.mkdir(parents=True)
        self.acuts = self.root / "experiments/core_narrative/configs/acuts"
        self.acuts.mkdir(parents=True)
        for acut_id in (
            "cheap-generic-swe",
            "cheap-rich-inert-control-v1",
            "cheap-rich-c-calibrated-v1",
            "cheap-rich-localization-tool-v1",
        ):
            (self.acuts / f"{acut_id}.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: core-narrative.acut.v1",
                        f"acut_id: {acut_id}",
                        "provider: barcarolle",
                        "model: gpt-5.4-mini",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

    def write_private_task_pack(self, private_root: str, *, split: str, index: int) -> None:
        task_dir = self.root / private_root / "candidate_task_pack"
        task_dir.mkdir(parents=True)
        task = {
            "task_id": f"rich__{split.lower()}__private__{index:03d}",
            "repo_slug": "rich",
            "split": split,
            "source": {
                "base_commit": "a" * 40,
                "target_commit": "b" * 40,
            },
            "expected": {"no_op_fails": True, "reference_passes": True},
            "leakage": {"reviewed": True},
        }
        (task_dir / "task.json").write_text(json.dumps(task), encoding="utf-8")

    def write_batch(self, path: Path, *, split: str, count: int, start_index: int) -> None:
        records = []
        for offset in range(count):
            index = start_index + offset
            private_root = f"experiments/core_narrative/large_artifacts/{path.stem}/candidate_{index:03d}"
            self.write_private_task_pack(private_root, split=split, index=index)
            records.append(accepted_record(split, private_root, index))
        path.write_text(json.dumps({"results": records}), encoding="utf-8")

    def test_build_payload_freezes_reduced_w20_without_exposing_raw_private_fields(self) -> None:
        """The readiness artifact records counts and digests, not raw commits or subjects."""
        module = load_module()
        w_direct = self.results / "w_direct.json"
        r_direct = self.results / "r_direct.json"
        self.write_batch(w_direct, split="W_star", count=20, start_index=1)
        self.write_batch(r_direct, split="R", count=25, start_index=101)

        with mock.patch.object(module, "REPO_ROOT", self.root):
            with mock.patch.object(module, "RESULTS_ROOT", self.results):
                with mock.patch.object(module, "W_DIRECT", (w_direct,)):
                    with mock.patch.object(module, "W_REPLACEMENT", ()):
                        with mock.patch.object(module, "W_DIRECT_WITHOUT_NODES", ()):
                            with mock.patch.object(module, "R_DIRECT", (r_direct,)):
                                payload = module.build_payload()

        self.assertEqual(payload["denominators"]["W_star"]["primary_task_count"], 20)
        self.assertFalse(payload["denominators"]["W_star"]["reserve_required"])
        self.assertFalse(payload["denominators"]["W_star"]["candidate_pool_required"])
        self.assertEqual(payload["denominators"]["R"]["primary_task_count"], 20)
        self.assertEqual(payload["denominators"]["R"]["reserve_task_count"], 5)
        self.assertFalse(payload["primary_runs_authorized"])
        self.assertTrue(payload["pre_primary_checks"]["all_primary_checks_pass"])
        self.assertEqual(payload["model_route_policy"]["active_frontier_route"], "gpt-5.4")
        self.assertTrue(payload["model_route_policy"]["provider_prefix_removed"])

        rendered = json.dumps(payload, sort_keys=True)
        self.assertNotRegex(rendered, RAW_COMMIT_RE)
        self.assertNotIn("base_commit", rendered)
        self.assertNotIn("target_commit", rendered)
        self.assertNotIn('"subject"', rendered)


if __name__ == "__main__":
    unittest.main()
