#!/usr/bin/env python3
"""Executable specs for the Rich direct-smoke pilot."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import unittest

import rich_direct_smoke_pilot as pilot


class RichDirectSmokePilotTests(unittest.TestCase):
    def test_admission_decision_requires_noop_fail_and_reference_pass(self) -> None:
        """A pilot candidate is accepted only when both smoke sides prove executable."""
        self.assertEqual(pilot.admission_decision("failed", "passed"), "accepted")
        self.assertEqual(pilot.admission_decision("passed_unexpected", "passed"), "rejected")
        self.assertEqual(pilot.admission_decision("failed", "failed"), "rejected")

    def test_noop_status_maps_exit_codes_to_readable_states(self) -> None:
        """No-op smoke distinguishes expected failure from collection and timeout blocks."""
        self.assertEqual(pilot.noop_status(1, timed_out=False), "failed")
        self.assertEqual(pilot.noop_status(0, timed_out=False), "passed_unexpected")
        self.assertEqual(pilot.noop_status(4, timed_out=False), "blocked_pytest_collection")
        self.assertEqual(pilot.noop_status(124, timed_out=True), "blocked_timeout")

    def test_verifier_script_copies_hidden_files_before_running_command(self) -> None:
        """Hidden target tests are copied into the workspace before pytest runs."""
        script = pilot.verifier_script(".venv/bin/python -m pytest -q tests/test_table.py::test_case")

        self.assertIn("hidden_dir", script)
        self.assertIn("cp \"$file\" \"$rel\"", script)
        self.assertIn("exec .venv/bin/python -m pytest -q tests/test_table.py::test_case", script)

    def test_public_result_does_not_expose_raw_commits(self) -> None:
        """Committed pilot output uses digests, not target or base commit ids."""
        candidate = {
            "commit": "a" * 40,
            "base_commit": "b" * 40,
            "subject": "fix table rendering",
            "family": "table/panel/layout",
            "window": "W_star",
            "surface": "source_and_tests",
            "source_file_count": 1,
            "test_file_count": 1,
            "test_node_count": 2,
            "changed_file_set_digest": "digest",
            "verifier_command": ".venv/bin/python -m pytest -q tests/test_table.py::test_case",
        }
        result = pilot.public_result(
            candidate=candidate,
            hidden_verifier_digest="hidden",
            reference_patch_digest="patch",
            reference_patch_bytes=123,
            noop={"status": "failed", "verifier_exit_code": 1},
            reference={"status": "passed", "verifier_exit_code": 0},
            private_root="experiments/core_narrative/large_artifacts/example",
        )

        serialized = str(result)
        self.assertNotIn("a" * 40, serialized)
        self.assertNotIn("b" * 40, serialized)
        self.assertEqual(result["admission_decision"], "accepted")
        self.assertEqual(result["source_anchor_digest"], pilot.source_anchor_digest("a" * 40))

    def test_select_candidate_passes_extended_c_scan_start(self) -> None:
        """One-off C pilots can use the same C extension boundary as batch smoke."""
        seen = {}
        original = pilot.discover_candidates

        def fake_discover(repo_path: Path, *, c_scan_start=None):
            seen["c_scan_start"] = c_scan_start
            return [
                {"window": "C", "direct_smoke_ready": True, "subject": "candidate"},
                {"window": "C", "direct_smoke_ready": False, "subject": "source only"},
            ]

        c_scan_start = dt.datetime(2025, 4, 14, tzinfo=dt.timezone.utc)
        pilot.discover_candidates = fake_discover
        try:
            candidate = pilot.select_candidate(Path("."), 0, "C", c_scan_start=c_scan_start)
        finally:
            pilot.discover_candidates = original

        self.assertEqual(candidate["subject"], "candidate")
        self.assertEqual(seen["c_scan_start"], c_scan_start)


if __name__ == "__main__":
    unittest.main()
