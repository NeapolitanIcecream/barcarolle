from __future__ import annotations

import pytest

from examples.modern_agent_panel.study import (
    normalize_fixed_harness_outcomes,
    select_fixed_harness_rows,
)


def _row(
    *,
    folder: str = "agent-a",
    details: object,
    resolved: float,
) -> dict[str, object]:
    return {
        "folder": folder,
        "name": "Agent A",
        "date": "2026-02-17",
        "mini-swe-agent_version": "2.0.0",
        "resolved": resolved,
        "per_instance_details": details,
    }


def test_fixed_harness_cohort_uses_only_complete_duplicate() -> None:
    tasks = ("task-a", "task-b")
    complete = _row(
        details={
            "task-a": {"resolved": True},
            "task-b": {"resolved": False},
        },
        resolved=50.0,
    )
    payload = {
        "leaderboards": [
            {
                "name": "bash-only",
                "results": [
                    _row(details={}, resolved=50.0),
                    complete,
                ],
            }
        ]
    }

    rows = select_fixed_harness_rows(
        payload,
        leaderboard_name="bash-only",
        folders=("agent-a",),
        version="2.0.0",
        task_ids=tasks,
    )
    outcomes, _ = normalize_fixed_harness_outcomes(rows, tasks)

    assert outcomes == {"agent-a": {"task-a": 1, "task-b": 0}}


def test_fixed_harness_cohort_rejects_changed_task_denominator() -> None:
    payload = {
        "leaderboards": [
            {
                "name": "bash-only",
                "results": [
                    _row(
                        details={
                            "task-a": {"resolved": True},
                            "unexpected": {"resolved": False},
                        },
                        resolved=50.0,
                    )
                ],
            }
        ]
    }

    with pytest.raises(ValueError):
        select_fixed_harness_rows(
            payload,
            leaderboard_name="bash-only",
            folders=("agent-a",),
            version="2.0.0",
            task_ids=("task-a", "task-b"),
        )
