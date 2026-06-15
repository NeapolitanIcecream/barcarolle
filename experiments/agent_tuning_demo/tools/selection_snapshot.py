from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.demo_common.files import read_json  # noqa: E402


DEMO_REL = Path("experiments/agent_tuning_demo")
CONFIG = ROOT / DEMO_REL / "config"
RESULTS = ROOT / DEMO_REL / "results"
SNAPSHOT_PATH = CONFIG / "selection_input_snapshot.json"
MANIFEST_PATH = RESULTS / "selection_input_snapshot_manifest.json"
SNAPSHOT_SCHEMA_VERSION = "barcarolle.agent_tuning_demo.selection_input_snapshot.v1"


def load_snapshot() -> dict[str, Any]:
    payload = read_json(SNAPSHOT_PATH)
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(f"unsupported selection input snapshot schema: {SNAPSHOT_PATH}")
    return payload


def snapshot_manifest() -> dict[str, Any]:
    return read_json(MANIFEST_PATH)


def selection_config() -> dict[str, Any]:
    return copy.deepcopy(load_snapshot()["selection_config"])


def frozen_split() -> dict[str, Any]:
    return copy.deepcopy(load_snapshot()["frozen_split"])


def selector_task_table_rows() -> list[dict[str, str]]:
    return copy.deepcopy(load_snapshot()["selector_task_table_rows"])


def selection_score_rows() -> list[dict[str, str]]:
    return copy.deepcopy(load_snapshot()["selection_score_rows"])


def holdout_score_rows() -> list[dict[str, str]]:
    return copy.deepcopy(load_snapshot()["holdout_score_rows"])


def selection_tool_summary(task_id: str) -> dict[str, Any]:
    summaries = load_snapshot().get("selection_tool_summaries") or {}
    summary = summaries.get(task_id)
    if not isinstance(summary, dict):
        return {
            "raw_available": False,
            "tools_used": [],
            "bash_command_count": 0,
            "targeted_pytest_command_count": 0,
            "read_tool_count": 0,
            "write_tool_count": 0,
        }
    return copy.deepcopy(summary)


def predictive_validity_window_inventory() -> dict[str, Any]:
    return copy.deepcopy(load_snapshot()["predictive_validity_window_inventory"])
