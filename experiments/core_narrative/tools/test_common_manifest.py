#!/usr/bin/env python3
"""Executable specs for shared manifest loading."""

from __future__ import annotations

import builtins
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _common


REPO_ROOT = Path(__file__).resolve().parents[3]


class CommonManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_load_manifest_uses_stdlib_yaml_subset_when_pyyaml_is_unavailable(self) -> None:
        """Regression: experiment YAML manifests must not block clean Python startup."""
        manifest_path = self.root / "manifest.yaml"
        manifest_path.write_text(
            """\
schema_version: core-narrative.test.v1
task_count: 1
enabled: true
notes: null
tasks:
  - task_id: click__rbench__001
    changed_files:
      - click/core.py
      - tests/test_options.py
    problem_statement: >-
      Fix option help generation so list defaults render
      without raising.
metadata:
  score_fields:
    g_score: null
    r_score: 2
""",
            encoding="utf-8",
        )

        original_import = builtins.__import__

        def import_without_yaml(name: str, *args: object, **kwargs: object) -> object:
            if name == "yaml":
                raise ImportError("simulated missing PyYAML")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=import_without_yaml):
            manifest = _common.load_manifest(manifest_path)

        self.assertEqual(manifest["schema_version"], "core-narrative.test.v1")
        self.assertEqual(manifest["task_count"], 1)
        self.assertIs(manifest["enabled"], True)
        self.assertIsNone(manifest["notes"])
        self.assertEqual(manifest["tasks"][0]["task_id"], "click__rbench__001")
        self.assertEqual(manifest["tasks"][0]["changed_files"], ["click/core.py", "tests/test_options.py"])
        self.assertEqual(
            manifest["tasks"][0]["problem_statement"],
            "Fix option help generation so list defaults render without raising.",
        )
        self.assertEqual(manifest["metadata"]["score_fields"]["r_score"], 2)
        self.assertIsNone(manifest["metadata"]["score_fields"]["g_score"])

    def test_experiment_entry_manifests_load_without_pyyaml(self) -> None:
        """Regression: the NFL experiment runner's YAML inputs must be self-bootstrapping."""
        manifest_paths = [
            REPO_ROOT / "experiments/core_narrative/configs/tasks/rbench_click.yaml",
            REPO_ROOT / "experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml",
            REPO_ROOT / "experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml",
        ]
        original_import = builtins.__import__

        def import_without_yaml(name: str, *args: object, **kwargs: object) -> object:
            if name == "yaml":
                raise ImportError("simulated missing PyYAML")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=import_without_yaml):
            manifests = [_common.load_manifest(path) for path in manifest_paths]

        self.assertEqual(manifests[0]["tasks"][0]["task_id"], "click__rbench__001")
        self.assertEqual(manifests[1]["acut_id"], "cheap-generic-swe")
        self.assertEqual(manifests[2]["task_id"], "click__rbench__001")

    def test_committed_core_narrative_yaml_manifests_fit_stdlib_subset(self) -> None:
        """Regression: fallback YAML parsing must cover committed experiment manifests."""
        manifest_paths = sorted((REPO_ROOT / "experiments/core_narrative").rglob("*.yaml"))
        self.assertGreater(len(manifest_paths), 0)

        for manifest_path in manifest_paths:
            with self.subTest(path=manifest_path.relative_to(REPO_ROOT)):
                manifest = _common.load_yaml_manifest(manifest_path.read_text(encoding="utf-8"))
                self.assertIsInstance(manifest, dict)


if __name__ == "__main__":
    unittest.main()
