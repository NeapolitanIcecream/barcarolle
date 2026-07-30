from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.multi_repository_study.public_replay import TaskMetadata  # noqa: E402
from examples.prequential_response_assembly.study import (  # noqa: E402
    adanormalhedge_forecast,
    create_adanormalhedge_state,
    response_expert_forecasts,
    update_adanormalhedge,
)
from examples.swe_bench_full_development.diagnostic import (  # noqa: E402
    load_plan as load_diagnostic_plan,
    select_future_oracle_memberships,
)
from examples.swe_bench_full_development.study import (  # noqa: E402
    ALGORITHM_IDS,
    CANDIDATE_IDS,
    load_plan,
    select_difficulty_markov_membership,
    select_response_memberships,
    summarize_horizon,
)


def _task(repository_id: str, index: int) -> TaskMetadata:
    return TaskMetadata(
        instance_id=f"{repository_id}-{index:02d}",
        repository_id=repository_id,
        created_at=f"2026-01-{index + 1:02d}T00:00:00Z",
        difficulty="not-used",
        problem_statement="synthetic",
    )


def test_full_development_plan_freezes_direct_mae_and_zero_cost() -> None:
    plan = load_plan()

    assert tuple(row["selector_id"] for row in plan["candidates"]) == CANDIDATE_IDS
    assert plan["primary_outcome"].startswith(
        "Direct target-Agent future pass-rate MAE"
    )
    assert plan["frame"]["horizons"] == [5, 10]
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["evaluation"]["ranking"].startswith("Report H5 and H10")


def test_full_development_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "swe_bench_full_development"
        / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["frame"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(path)


def test_full_diagnostic_is_future_open_and_zero_cost() -> None:
    plan = load_diagnostic_plan()

    assert plan["status"] == "post_result_diagnostic_frozen_before_oracle_scores"
    assert "future-open diagnostics" in plan["claim_boundary"]
    assert plan["authority"]["paid_api_calls"] == 0


def test_response_membership_does_not_use_target_outcomes() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    history = np.asarray(
        [
            [index % 2, (index // 2) % 2, (index // 3) % 2]
            for index in range(12)
        ],
        dtype=np.float64,
    )
    changed = history.copy()
    changed[:, 0] = 1.0 - changed[:, 0]
    forecast = np.asarray([0.25, 0.5, 0.75], dtype=np.float64)
    changed_forecast = np.asarray([0.9, 0.5, 0.75], dtype=np.float64)
    order = tuple(
        (f"2026-01-{index + 1:02d}T00:00:00Z", f"task-{index:02d}")
        for index in range(len(history))
    )

    original_memberships = select_response_memberships(
        history,
        forecast,
        horizon=2,
        budget=3,
        created_order=order,
    )
    changed_memberships = select_response_memberships(
        changed,
        changed_forecast,
        horizon=2,
        budget=3,
        created_order=order,
    )

    assert original_memberships[0] == changed_memberships[0]
    assert all(len(indices) == 3 for indices in original_memberships[0].values())


def test_prequential_update_remains_target_column_invariant() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    history = np.asarray(
        [
            [index % 2, (index // 2) % 2, (index // 3) % 2]
            for index in range(12)
        ],
        dtype=np.float64,
    )
    changed = history.copy()
    changed[:, 0] = 1.0 - changed[:, 0]
    order = tuple(
        (f"2026-01-{index + 1:02d}T00:00:00Z", f"task-{index:02d}")
        for index in range(len(history))
    )

    def second_origin_membership(values: object) -> tuple[int, ...]:
        matrix = np.asarray(values, dtype=np.float64)
        state = create_adanormalhedge_state(3)
        first_experts = response_expert_forecasts(matrix[:10], horizon=2)
        update_adanormalhedge(
            state,
            first_experts,
            matrix[10:12].mean(axis=0),
        )
        second_experts = response_expert_forecasts(matrix, horizon=2)
        forecast, _ = adanormalhedge_forecast(state, second_experts)
        return select_response_memberships(
            matrix,
            forecast,
            horizon=2,
            budget=3,
            created_order=order,
        )[0]["ALG-015U"]

    assert second_origin_membership(history) == second_origin_membership(changed)


def test_reference_future_oracle_does_not_use_target_column() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    history = np.asarray(
        [
            [index % 2, (index // 2) % 2, (index // 3) % 2]
            for index in range(12)
        ],
        dtype=np.float64,
    )
    future = np.asarray(
        [[0, 1, 0], [1, 1, 0]],
        dtype=np.float64,
    )
    changed_history = history.copy()
    changed_future = future.copy()
    changed_history[:, 0] = 1.0 - changed_history[:, 0]
    changed_future[:, 0] = 1.0 - changed_future[:, 0]
    order = tuple(
        (f"2026-01-{index + 1:02d}T00:00:00Z", f"task-{index:02d}")
        for index in range(len(history))
    )

    original = select_future_oracle_memberships(
        history,
        future,
        budget=3,
        created_order=order,
    )
    changed = select_future_oracle_memberships(
        changed_history,
        changed_future,
        budget=3,
        created_order=order,
    )

    assert (
        original[0]["reference_future_oracle"]
        == changed[0]["reference_future_oracle"]
    )


def test_difficulty_markov_excludes_target_and_later_training_tasks() -> None:
    target_history = tuple(_task("target", index) for index in range(8))
    training_tasks = tuple(_task("training", index) for index in range(10))
    all_tasks = (*target_history, *training_tasks)
    agent_ids = ("agent-a", "agent-b", "agent-c")
    outcomes = {
        agent_id: {
            task.instance_id: (index + offset) % 2
            for index, task in enumerate(all_tasks[:-1])
        }
        for offset, agent_id in enumerate(agent_ids)
    }
    changed = {
        agent_id: dict(agent_outcomes)
        for agent_id, agent_outcomes in outcomes.items()
    }
    changed["agent-a"] = {
        task_id: 1 - value
        for task_id, value in changed["agent-a"].items()
    }
    tasks_by_repository = {
        "target": target_history,
        "training": training_tasks,
    }

    original = select_difficulty_markov_membership(
        target_history,
        target_agent_id="agent-a",
        agent_ids=agent_ids,
        outcomes_by_agent=outcomes,
        target_repository_id="target",
        repository_ids=("target", "training"),
        tasks_by_repository=tasks_by_repository,
        horizon=2,
        budget=3,
        state_count=3,
        cell_prior_mass=1.0 / 3.0,
        local_prior_strength=3.0,
    )
    changed_target = select_difficulty_markov_membership(
        target_history,
        target_agent_id="agent-a",
        agent_ids=agent_ids,
        outcomes_by_agent=changed,
        target_repository_id="target",
        repository_ids=("target", "training"),
        tasks_by_repository=tasks_by_repository,
        horizon=2,
        budget=3,
        state_count=3,
        cell_prior_mass=1.0 / 3.0,
        local_prior_strength=3.0,
    )

    assert original == changed_target
    assert len(original) == 3


def test_horizon_summary_uses_repository_equal_direct_mae() -> None:
    rows = []
    losses = {
        ("repo-a", "agent-a"): (0.1, 0.0),
        ("repo-a", "agent-b"): (0.1, 0.0),
        ("repo-b", "agent-a"): (0.3, 0.5),
        ("repo-b", "agent-b"): (0.3, 0.5),
    }
    for (repository_id, agent_id), (full, recency) in losses.items():
        row_losses = {
            algorithm_id: full for algorithm_id in ALGORITHM_IDS
        }
        row_losses["ordinary_recency"] = recency
        rows.append(
            {
                "repository_id": repository_id,
                "origin_id": f"{repository_id}-origin",
                "target_agent_id": agent_id,
                "losses": row_losses,
            }
        )

    summary = summarize_horizon(
        rows,
        repository_ids=("repo-a", "repo-b"),
        agent_ids=("agent-a", "agent-b"),
        random_differences=(-0.1, 0.0, 0.1),
        bootstrap_resamples=20,
        bootstrap_seed=7,
    )

    assert summary["mae"]["full_history"] == pytest.approx(0.2)
    assert summary["mae"]["ordinary_recency"] == pytest.approx(0.25)
    assert summary["candidates"]["ordinary_recency"][
        "candidate_minus_full"
    ] == pytest.approx(0.05)
    assert summary["candidates"]["ordinary_recency"][
        "favorable_repository_count"
    ] == 1
