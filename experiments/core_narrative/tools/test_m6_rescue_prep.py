#!/usr/bin/env python3
"""Executable specs for M6 rescue-prep diagnostics."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import m6_rescue_prep as prep


class M6RescuePrepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_classify_task_separates_ceiling_floor_and_separator(self) -> None:
        """Task-level labels are derived only from fixed-denominator cell scores."""
        self.assertEqual(prep.classify_task({"a": 1, "b": 1}), "ceiling")
        self.assertEqual(prep.classify_task({"a": 0, "b": 0}), "floor")
        self.assertEqual(prep.classify_task({"a": 1, "b": 0}), "separator")
        self.assertEqual(prep.classify_task({"a": None}), "unscored")

    def test_parse_unified_diff_outputs_redacted_overlap_features(self) -> None:
        """Patch parsing exposes file and hash features without copying patch content."""
        diff = """diff --git a/src/click/core.py b/src/click/core.py
--- a/src/click/core.py
+++ b/src/click/core.py
@@ -1,3 +1,4 @@ def resolve_default():
-    return default_map[name]
+    if default_map[name] is UNSET:
+        return declared_default
+    return default_map[name]
"""

        parsed = prep.parse_unified_diff(diff)

        self.assertEqual(parsed["changed_files"], ["src/click/core.py"])
        self.assertEqual(parsed["hunk_count"], 1)
        self.assertEqual(len(parsed["hunk_header_hashes"]), 1)
        self.assertGreater(parsed["patch_token_count"], 0)
        self.assertNotIn("declared_default", json.dumps({k: v for k, v in parsed.items() if k != "_tokens"}))

    def test_delivery_row_accepts_enabled_context_from_redacted_prompt_checks(self) -> None:
        """Treatment delivery can be proven from redacted metadata, not raw prompt text."""
        raw_dir = self.root / "raw/run/codex_cli_patch_command"
        raw_dir.mkdir(parents=True)
        summary_path = raw_dir.parent / "codex_cli_patch_command.json"
        summary_path.write_text(
            json.dumps(
                {
                    "prompt": {"char_count": 1000, "content_recorded": False, "manifest_truncated": False, "statement_truncated": False},
                    "specialist_context_pack": {
                        "enabled": True,
                        "expected_for_acut": True,
                        "pack_id": "click_deep",
                        "pack_hash": "abc",
                        "context_prompt_char_count": 500,
                        "leakage_guards": {"resolved_secrets_recorded": False},
                        "prompt_checks": {
                            "marker_present": True,
                            "pack_hash_present": True,
                            "pack_id_present": True,
                            "all_expected_sections_present": True,
                            "section_ids_present": {"module_map": True},
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        normalized = self.root / "normalized.json"
        normalized.write_text(json.dumps({"artifact_paths": {"acut_summary": str(summary_path)}}), encoding="utf-8")

        row = prep.delivery_row({"normalized_result": str(normalized), "task_id": "t", "acut_id": "deep"}, expected_enabled=True)

        self.assertTrue(row["passed"])
        self.assertTrue(row["prompt_contains_context_inferred_from_redacted_checks"])
        self.assertFalse(row["raw_prompt_content_recorded"])

    def test_overlap_row_marks_expected_file_and_review_packet_boundaries(self) -> None:
        """Overlap audit uses metadata proxies and keeps raw patch content out of artifacts."""
        candidate = self.root / "candidate.patch"
        candidate.write_text(
            """diff --git a/src/click/core.py b/src/click/core.py
--- a/src/click/core.py
+++ b/src/click/core.py
@@ -1,2 +1,2 @@ def convert():
-    return value
+    return normalize(value)
""",
            encoding="utf-8",
        )
        normalized = self.root / "normalized.json"
        normalized.write_text(
            json.dumps({"artifact_paths": {"artifact_dir": str(self.root)}, "candidate_patch": {"path": str(candidate)}}),
            encoding="utf-8",
        )
        reference = prep.public_patch_stats(candidate)

        row = prep.overlap_row(
            task_id="click__rwork__999",
            acut_id="cheap-click-deep-specialist-v2",
            cell={"normalized_result": str(normalized), "status": "verified_fail", "score_value": 0},
            task_manifest={"source_compare": {"changed_files": ["click/core.py"]}},
            reference=reference,
        )

        self.assertTrue(row["touched_expected_file"])
        self.assertTrue(row["touched_reference_file"])
        self.assertEqual(row["same_conceptual_fix_proxy"], "strong_automated_proxy")
        self.assertFalse(row["raw_patch_content_recorded"])
        self.assertFalse(row["reference_patch_content_recorded"])


if __name__ == "__main__":
    unittest.main()
