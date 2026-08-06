from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json

import pytest

from examples.modern_agent_panel.portability import (
    DEFAULT_SUMMARY,
    load_plan,
    materialize_horizon_memberships,
    validate_summary,
)
from examples.multi_repository_study.public_replay import TaskMetadata


def _tasks(count: int = 30) -> tuple[TaskMetadata, ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        TaskMetadata(
            instance_id=f"task-{index:02d}",
            repository_id="repo",
            created_at=(start + timedelta(days=index)).isoformat(),
            difficulty="not-used",
            problem_statement="synthetic",
        )
        for index in range(count)
    )


def test_portability_memberships_hide_target_column_across_updates() -> None:
    pytest.importorskip("numpy")
    tasks = _tasks()
    task_ids = tuple(task.instance_id for task in tasks)
    outcomes = {
        "agent-a": {task_id: index % 2 for index, task_id in enumerate(task_ids)},
        "agent-b": {
            task_id: int(index % 3 == 0) for index, task_id in enumerate(task_ids)
        },
        "agent-c": {
            task_id: int(index % 5 < 2) for index, task_id in enumerate(task_ids)
        },
    }
    changed = {
        **outcomes,
        "agent-a": {
            task_id: 1 - value for task_id, value in outcomes["agent-a"].items()
        },
    }

    original = materialize_horizon_memberships(
        tasks,
        outcomes,
        horizon=5,
        minimum_history=20,
        budget=10,
    )
    perturbed = materialize_horizon_memberships(
        tasks,
        changed,
        horizon=5,
        minimum_history=20,
        budget=10,
    )

    original_target = [
        row["memberships"]
        for row in original["rows"]
        if row["target_agent_id"] == "agent-a"
    ]
    perturbed_target = [
        row["memberships"]
        for row in perturbed["rows"]
        if row["target_agent_id"] == "agent-a"
    ]
    assert original_target == perturbed_target


def test_committed_portability_summary_validates() -> None:
    plan = load_plan()
    summary = json.loads(DEFAULT_SUMMARY.read_text(encoding="utf-8"))

    validate_summary(summary, plan)
