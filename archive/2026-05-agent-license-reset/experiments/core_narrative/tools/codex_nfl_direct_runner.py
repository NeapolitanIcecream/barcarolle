#!/usr/bin/env python3
"""Codex-owned direct runner for the Barcarolle NFL-angle experiment.

This intentionally reuses the small direct search/replace runner that already
proved the patch/verifier route works, but gives the facility a Codex-owned
identity and artifact trail for the 2026-05-08 NFL experiment run.
"""

from __future__ import annotations

import sys

import openclaw_direct_runner as direct


direct.TOOL = "codex_nfl_direct_runner"
direct.RUNNER_ID = "codex-nfl-direct-search-replace-v1"


if __name__ == "__main__":
    sys.exit(direct.main())
