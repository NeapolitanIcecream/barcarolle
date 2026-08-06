from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import combinations
import json
from pathlib import Path

import pytest

from barcarolle.records import canonical_digest
from examples.modern_agent_panel.consensus_rate import (
    load_plan,
    load_primary_inputs,
    materialize_horizon_memberships,
    select_consensus_first_membership,
    select_consensus_rate_membership,
    select_rate_only_membership,
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


def test_consensus_rate_selector_preserves_rate_before_consensus() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0, 0],
            [1, 1],
            [0, 1],
            [1, 0],
        ],
        dtype=np.float64,
    )

    assert select_consensus_rate_membership(history, budget=2) == (0, 1)
    assert select_rate_only_membership(history, budget=2) == (2, 3)
    assert select_consensus_first_membership(history, budget=2) == (0, 1)


@pytest.mark.parametrize(
    ("counts", "budget"),
    [
        ((0, 2, 2, 2), 2),
        ((0, 0, 1, 1, 2, 2), 3),
        ((0, 1, 1, 1, 2, 2, 2), 3),
    ],
)
def test_consensus_rate_selector_matches_exact_frozen_sort_key(
    counts: tuple[int, ...],
    budget: int,
) -> None:
    np = pytest.importorskip("numpy")
    reference_count = 2
    history = np.asarray(
        [
            [1] * count + [0] * (reference_count - count)
            for count in counts
        ],
        dtype=np.float64,
    )
    history_count = len(counts)
    full_response_sum = sum(counts)
    expected = min(
        combinations(range(history_count), budget),
        key=lambda selected: (
            abs(
                history_count * sum(counts[index] for index in selected)
                - budget * full_response_sum
            ),
            sum(
                counts[index] * (reference_count - counts[index])
                for index in selected
            ),
            tuple(-index for index in reversed(selected)),
        ),
    )

    assert select_consensus_rate_membership(history, budget=budget) == expected


def test_consensus_rate_selector_uses_global_recent_composition_tie() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0, 0],
            [1, 1],
            [1, 1],
            [1, 1],
        ],
        dtype=np.float64,
    )

    # Sums two and four are equally far from the ideal sum three, and both
    # have zero disagreement. The globally newer composition wins.
    assert select_consensus_rate_membership(history, budget=2) == (2, 3)


def test_consensus_rate_selector_requires_two_reference_agents() -> None:
    np = pytest.importorskip("numpy")

    with pytest.raises(ValueError, match="history is invalid"):
        select_consensus_rate_membership(
            np.asarray([[0], [1]], dtype=np.float64),
            budget=1,
        )


def test_frozen_consensus_rate_plan_validates() -> None:
    assert (
        load_plan()["plan_digest"]
        == "4298d371d83bcd954932a34692ef2692384ce35e0e42989ff02093409a04fb6e"
    )


def test_opened_transfer_diagnostic_digest_and_direction_validate() -> None:
    path = (
        Path(__file__).parents[1]
        / "examples"
        / "modern_agent_panel"
        / "evidence"
        / "consensus-rate-transfer-diagnostic.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest = payload.pop("diagnostic_digest")

    assert digest == canonical_digest(payload)
    for diagnostic in payload["results"].values():
        for horizon in ("5", "10"):
            assert diagnostic[horizon]["candidate_minus_full"] > 0.0


def test_primary_loader_does_not_require_secondary_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from examples.modern_agent_panel import study

    tasks = _tasks(2)
    leaderboard = {
        "leaderboards": [
            {
                "name": "primary-board",
                "results": [
                    {
                        "folder": "agent-a",
                        "name": "Agent A",
                        "date": "2026-02-17",
                        "mini-swe-agent_version": "2.0.0",
                        "resolved": 50.0,
                        "per_instance_details": {
                            "task-00": {"resolved": True},
                            "task-01": {"resolved": False},
                        },
                    }
                ],
            }
        ]
    }
    monkeypatch.setattr(study, "_load_tasks", lambda *args, **kwargs: tasks)
    monkeypatch.setattr(
        study,
        "_require_file_identity",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(study, "_load_mapping", lambda path: leaderboard)
    monkeypatch.setattr(study, "_file_sha256", lambda path: "sha")
    plan = {
        "primary_lane": {
            "lane_id": "primary",
            "task_source": {
                "local_path": "tasks.parquet",
                "sha256": "task-sha",
                "task_count": 2,
            },
            "result_source": {
                "local_path": "results.json",
                "size_bytes": 1,
                "sha256": "result-sha",
                "git_blob_sha": "blob",
                "leaderboard_name": "primary-board",
            },
            "folders": ["agent-a"],
            "cohort_rule": {
                "mini_swe_agent_version": "2.0.0",
                "expected_agent_count": 1,
            },
        }
    }

    lane_id, loaded_tasks, outcomes, _, _ = load_primary_inputs(plan)

    assert lane_id == "primary"
    assert loaded_tasks == tasks
    assert outcomes == {"agent-a": {"task-00": 1, "task-01": 0}}


def test_consensus_memberships_hide_complete_target_column() -> None:
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

    assert [
        row["selected_task_ids"]
        for row in original["rows"]
        if row["target_agent_id"] == "agent-a"
    ] == [
        row["selected_task_ids"]
        for row in perturbed["rows"]
        if row["target_agent_id"] == "agent-a"
    ]


def test_current_future_flip_leaves_current_membership_unchanged() -> None:
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
        agent: {
            task_id: (1 - value if 20 <= index < 25 else value)
            for index, (task_id, value) in enumerate(agent_outcomes.items())
        }
        for agent, agent_outcomes in outcomes.items()
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

    assert [
        row["selected_task_ids"]
        for row in original["rows"]
        if row["origin_id"] == "repo:origin-001"
    ] == [
        row["selected_task_ids"]
        for row in perturbed["rows"]
        if row["origin_id"] == "repo:origin-001"
    ]
