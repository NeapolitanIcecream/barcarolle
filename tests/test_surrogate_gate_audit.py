from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.multi_repository_study.theory import (  # noqa: E402
    select_embedding_mean_match,
)
from examples.surrogate_gate_audit.study import (  # noqa: E402
    _composition_forecast_only,
    _repository_summary,
    load_audit_plan,
    select_discrete_composition_indices,
    select_mean_matching_indices,
)


def test_surrogate_gate_audit_plan_is_self_bound() -> None:
    plan = load_audit_plan()

    assert plan["study_id"] == "proxy-gated-pass-rate-mae-audit-2026-07-29"
    assert plan["resource_boundary"]["paid_api_calls"] == 0


def test_surrogate_gate_audit_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "surrogate_gate_audit"
        / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["rolling_origin"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_audit_plan(path)


def test_mean_matching_reuses_frozen_optimizer_semantics() -> None:
    np = pytest.importorskip("numpy")
    task_ids = tuple(f"task-{index}" for index in range(7))
    rows = np.asarray(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.2, 0.8, 0.4],
            [0.8, 0.2, 0.6],
            [0.5, 0.5, 0.5],
        ],
        dtype=np.float64,
    )
    target = np.asarray([0.55, 0.45, 0.35], dtype=np.float64)

    expected = select_embedding_mean_match(
        task_ids,
        {
            task_id: tuple(float(value) for value in rows[index])
            for index, task_id in enumerate(task_ids)
        },
        tuple(float(value) for value in target),
        budget=4,
        swap_pass_limit=20,
    )
    selected = select_mean_matching_indices(
        rows,
        target,
        budget=4,
        swap_pass_limit=20,
    )

    assert tuple(task_ids[index] for index in selected) == expected


def test_discrete_composition_uses_lexicographic_counts_then_newest() -> None:
    solved_counts = (1, 1, 1, 0, 2)
    created_order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(solved_counts))
    )

    selected = select_discrete_composition_indices(
        solved_counts,
        0.5,
        budget=2,
        maximum_count=2,
        created_order=created_order,
    )

    # Sum two is reachable as (c0,c1,c2)=(0,2,0) or (1,0,1).
    # The first vector is lexicographically smaller, then newest wins in cell 1.
    assert selected == (1, 2)


def test_discrete_composition_matches_brute_force() -> None:
    solved_counts = (0, 0, 1, 1, 2, 3, 3)
    created_order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(solved_counts))
    )
    forecast = 0.61
    budget = 3
    maximum_count = 3

    selected = select_discrete_composition_indices(
        solved_counts,
        forecast,
        budget=budget,
        maximum_count=maximum_count,
        created_order=created_order,
    )
    possible = []
    for indices in combinations(range(len(solved_counts)), budget):
        count_vector = tuple(
            sum(solved_counts[index] == value for index in indices)
            for value in range(maximum_count + 1)
        )
        objective = abs(
            sum(solved_counts[index] for index in indices)
            / (maximum_count * budget)
            - forecast
        )
        possible.append((objective, count_vector, indices))
    best_objective = min(item[0] for item in possible)
    best_vector = min(
        item[1] for item in possible if item[0] == best_objective
    )

    assert abs(
        sum(solved_counts[index] for index in selected)
        / (maximum_count * budget)
        - forecast
    ) == pytest.approx(best_objective)
    assert tuple(
        sum(solved_counts[index] == value for index in selected)
        for value in range(maximum_count + 1)
    ) == best_vector


def test_composition_forecast_materializer_has_no_future_input() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 0.0],
            [1.0, 1.0],
            [1.0, 1.0],
        ]
    )

    forecast, local, full, recent = _composition_forecast_only(
        history,
        horizon=2,
        earlier_full_loss_sum=np.asarray([1.0, 0.0]),
        earlier_recent_loss_sum=np.asarray([0.0, 1.0]),
        earlier_origin_count=1,
        global_prior=np.asarray([0.0, 0.0]),
    )

    assert full == pytest.approx([0.5, 0.5])
    assert recent == pytest.approx([1.0, 1.0])
    assert local == pytest.approx([1.0, 0.5])
    assert forecast == pytest.approx([2.0 / 3.0, 0.4])


def test_repository_summary_is_repository_first() -> None:
    rows = tuple(
        {
            "repository_id": "long",
            "origin_id": f"long:{index}",
            "candidate_loss": 0.6,
            "full_loss": 0.5,
            "difference": 0.1,
        }
        for index in range(9)
    ) + (
        {
            "repository_id": "short",
            "origin_id": "short:1",
            "candidate_loss": 0.0,
            "full_loss": 0.5,
            "difference": -0.5,
        },
    )

    summary = _repository_summary(rows, ("long", "short"))

    assert summary["difference"] == pytest.approx(-0.2)
    assert summary["difference"] != pytest.approx(0.04)
