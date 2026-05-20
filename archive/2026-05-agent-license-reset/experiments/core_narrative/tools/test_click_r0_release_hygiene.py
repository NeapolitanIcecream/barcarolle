#!/usr/bin/env python3
"""Executable specs for Click R0 release hygiene artifacts."""

from __future__ import annotations

import click_r0_release_hygiene as hygiene
import unittest


class ClickR0ReleaseHygieneTests(unittest.TestCase):
    def test_acut_statement_removes_public_source_and_leakage_markers(self) -> None:
        """ACUT-visible statements preserve task behavior but remove provenance links and SHAs."""
        source = """# task

## Problem Statement

Fix behavior.

## Public Source

- Kind: commit
- Anchor: commit:1c20dc6e724cd5625faaa17b715ba928d44c08bf
- URL: https://github.com/pallets/click/commit/1c20dc6e724cd5625faaa17b715ba928d44c08bf

## Visible Context Guidance

Provide issue 3071. Hide the implementation.
"""

        acut = hygiene.remove_public_source_section(source)

        self.assertIn("Fix behavior.", acut)
        self.assertIn("Provide issue 3071", acut)
        self.assertNotIn("https://", acut)
        self.assertNotIn("1c20dc6", acut)
        self.assertTrue(hygiene.is_acut_statement_safe(acut))

    def test_release_digest_changes_when_task_digest_material_changes(self) -> None:
        """The release digest is tied to statement/provenance/task digest material."""
        first = hygiene.digest_payload(
            {
                "schema_version": hygiene.SCHEMA_VERSION,
                "release_id": "click-r0-20260510",
                "tasks": [{"task_id": "task-1", "acut_statement_sha256": "a"}],
            }
        )
        second = hygiene.digest_payload(
            {
                "schema_version": hygiene.SCHEMA_VERSION,
                "release_id": "click-r0-20260510",
                "tasks": [{"task_id": "task-1", "acut_statement_sha256": "b"}],
            }
        )

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
