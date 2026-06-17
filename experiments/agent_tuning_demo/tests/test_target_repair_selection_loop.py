from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import target_repair_selection_loop as loop  # noqa: E402


def test_mypy_path_classification_keeps_test_and_impl_boundaries() -> None:
    assert loop.is_mypy_impl_path("mypy/checker.py") is True
    assert loop.is_mypy_impl_path("mypyc/irbuild/builder.py") is True
    assert loop.is_mypy_impl_path("mypy/test/testcheck.py") is False
    assert loop.is_mypy_test_path("mypy/test/testcheck.py") is True
    assert loop.is_mypy_test_path("mypyc/test/test_emit.py") is True
    assert loop.is_mypy_test_path("test-data/unit/check-basic.test") is False


def test_spread_sample_is_time_ordered_and_deterministic() -> None:
    rows = [
        {"task_id": f"mypy__hist__{index:04d}", "task_time": f"2024-01-{index:02d}T00:00:00+00:00"}
        for index in range(1, 6)
    ]

    sampled = loop.spread_sample(rows, 3)

    assert [row["task_id"] for row in sampled] == ["mypy__hist__0001", "mypy__hist__0003", "mypy__hist__0005"]


def test_candidate_decision_rejects_mypy_below_conversion_stop() -> None:
    row = loop.build_candidate_decision(
        "mypy",
        large={},
        target={},
        sphinx={},
        mypy_sample={
            "pass_count": 0,
            "conversion_rate": 0.0,
            "stop_decision": "reject_mypy_conversion_below_0_30",
            "verifier_duration_summary": {"count": 0},
        },
        mypy_smoke={"status": "passed", "duration_seconds": 1.0},
    )

    assert row["decision_label"] == "rejected"
    assert row["exact_certified_task_count"] == 0
    assert "corrected threshold requires 80 exact tasks" in row["primary_reason"]
