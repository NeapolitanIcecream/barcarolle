from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from experiments.demo_common.files import read_json  # noqa: E402
import phase2_artifact_tuning as phase2  # noqa: E402
import phase2b_rolling_origin_tuning as phase2b  # noqa: E402
import selection_snapshot  # noqa: E402


def tool_source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(TOOLS.glob("*.py")))


def test_tuning_tools_do_not_import_live_selection_demo_module() -> None:
    assert not re.search(r"\b(import|from)\s+agent_selection_demo\b", tool_source_text())


def test_tuning_tools_do_not_read_live_selection_config_or_results_paths() -> None:
    forbidden = [
        "experiments/agent_selection_demo/results",
        "experiments/agent_selection_demo/config",
    ]

    text = tool_source_text()

    assert all(path not in text for path in forbidden)


def test_tuning_tools_read_frozen_snapshot_for_selection_derived_inputs() -> None:
    snapshot = selection_snapshot.load_snapshot()
    manifest = read_json(selection_snapshot.MANIFEST_PATH)

    assert phase2.load_selection_split() == snapshot["frozen_split"]
    assert phase2b.load_task_table() == snapshot["selector_task_table_rows"]
    assert manifest["paid_calls_run"] == 0
    assert "do not refresh this file automatically" in manifest["policy"]
    assert {item["source_path"] for item in manifest["frozen_inputs"] if "source_path" in item} >= {
        "experiments/agent_selection_demo/config/demo_config.json",
        "experiments/agent_selection_demo/results/frozen_split.json",
        "experiments/agent_selection_demo/results/selector_task_table.csv",
        "experiments/agent_selection_demo/results/selection_score_table.csv",
        "experiments/agent_selection_demo/results/holdout_score_table.csv",
        "experiments/agent_selection_demo/results/predictive_validity_window_inventory.json",
    }

