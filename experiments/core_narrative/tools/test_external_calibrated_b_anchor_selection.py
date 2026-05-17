#!/usr/bin/env python3
"""Executable specs for SymPy B anchor selection."""

from __future__ import annotations

import unittest

import external_calibrated_b_anchor_selection as selection


class ExternalCalibratedBAnchorSelectionTests(unittest.TestCase):
    def test_candidate_from_commit_requires_source_and_tests_surface(self) -> None:
        row = {
            "commit": "a" * 40,
            "committed_at": "2026-01-01T00:00:00Z",
            "subject": "Improve Matrix solve behavior",
            "files": ["sympy/matrices/solvers.py", "sympy/matrices/tests/test_solvers.py"],
        }

        candidate = selection.candidate_from_commit("sympy", row)

        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate["family"], "matrices/linear algebra")
        self.assertEqual(candidate["surface"], "source_and_tests")
        rendered = repr(candidate)
        self.assertNotIn("Improve Matrix solve behavior", rendered)
        self.assertNotIn("a" * 40, rendered)

    def test_candidate_from_commit_rejects_source_without_tests(self) -> None:
        self.assertIsNone(
            selection.candidate_from_commit(
                "sympy",
                {
                    "commit": "a" * 40,
                    "committed_at": "2026-01-01T00:00:00Z",
                    "subject": "Improve Matrix solve behavior",
                    "files": ["sympy/matrices/solvers.py"],
                },
            )
        )

    def test_candidate_from_commit_rejects_huge_refactor_anchor(self) -> None:
        files = [f"sympy/core/file_{index}.py" for index in range(41)]
        files.append("sympy/core/tests/test_huge.py")

        self.assertIsNone(
            selection.candidate_from_commit(
                "sympy",
                {
                    "commit": "a" * 40,
                    "committed_at": "2026-01-01T00:00:00Z",
                    "subject": "Improve core behavior",
                    "files": files,
                },
            )
        )

    def test_select_anchor_pool_round_robins_families_and_avoids_duplicate_file_sets(self) -> None:
        rows = [
            {
                "commit": f"{index:040x}",
                "committed_at": f"2026-01-{index + 1:02d}T00:00:00Z",
                "subject": subject,
                "files": files,
            }
            for index, (subject, files) in enumerate(
                [
                    ("Improve Matrix solve behavior", ["sympy/matrices/a.py", "sympy/matrices/tests/test_a.py"]),
                    ("Improve Matrix solve behavior", ["sympy/matrices/a.py", "sympy/matrices/tests/test_a.py"]),
                    ("Fix assumptions predicate", ["sympy/assumptions/a.py", "sympy/assumptions/tests/test_a.py"]),
                    ("Fix integrate series behavior", ["sympy/integrals/a.py", "sympy/integrals/tests/test_a.py"]),
                    ("Fix polys factor behavior", ["sympy/polys/a.py", "sympy/polys/tests/test_a.py"]),
                ]
            )
        ]

        selected = selection.select_anchor_pool(rows, {"task_table": []}, target=4)

        self.assertEqual(len(selected), 4)
        self.assertEqual(len({item["changed_file_set_digest"] for item in selected}), 4)
        self.assertEqual(selected[0]["candidate_id"], "sympy_b_anchor_001")


if __name__ == "__main__":
    unittest.main()
