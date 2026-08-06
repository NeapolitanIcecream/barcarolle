from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.multi_swe_research.response_composition import (  # noqa: E402
    _build_composition_data,
    _eligible_other_repository_count,
    _global_prior,
    leave_one_configuration_difficulty,
    load_response_composition_plan,
    prequential_expert_forecast,
)
from examples.multi_repository_study.public_replay import TaskMetadata  # noqa: E402


def test_response_composition_plan_is_self_bound() -> None:
    plan = load_response_composition_plan()

    assert plan["candidate"]["algorithm_id"] == "ALG-014"
    assert plan["response_composition_plan_digest"]


def test_response_composition_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "response-composition-plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["candidate"]["global_prior"]["prior_mass"] = "two pseudo-Tasks"
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_response_composition_plan(path)


def test_leave_one_configuration_difficulty_excludes_evaluated_column() -> None:
    np = pytest.importorskip("numpy")
    outcomes = np.asarray(
        [
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
        ]
    )

    difficulty = leave_one_configuration_difficulty(outcomes)

    assert np.allclose(
        difficulty,
        np.asarray(
            [
                [0.5, 1.0, 0.5],
                [0.5, 0.0, 0.5],
            ]
        ),
    )


def test_prequential_forecast_falls_back_to_stationary_and_shrinks() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ]
    )
    future = np.asarray([[1.0, 1.0], [1.0, 1.0]])

    forecast, local, full, recent, future_mean = prequential_expert_forecast(
        history,
        future,
        horizon=2,
        earlier_full_loss_sum=np.zeros(2),
        earlier_recent_loss_sum=np.zeros(2),
        earlier_origin_count=0,
        global_prior=np.asarray([0.0, 0.0]),
    )

    assert full == pytest.approx([0.5, 0.5])
    assert recent == pytest.approx([1.0, 0.5])
    assert local == pytest.approx(full)
    assert forecast == pytest.approx([0.4, 0.4])
    assert future_mean == pytest.approx([1.0, 1.0])


def test_prequential_forecast_selects_experts_per_configuration() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 0.0],
            [1.0, 1.0],
            [1.0, 1.0],
        ]
    )
    future = np.asarray([[1.0, 1.0], [1.0, 1.0]])

    forecast, local, full, recent, _ = prequential_expert_forecast(
        history,
        future,
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


def test_global_prior_is_target_excluded_cutoff_safe_and_repo_equal() -> None:
    np = pytest.importorskip("numpy")
    tasks = (
        _task("train-a:1", "train-a", "2026-01-01T00:00:00Z"),
        _task("train-a:2", "train-a", "2026-01-02T00:00:00Z"),
        _task("train-a:late", "train-a", "2026-02-01T00:00:00Z"),
        _task("train-b:1", "train-b", "2026-01-01T00:00:00Z"),
        _task("target:1", "target", "2026-01-01T00:00:00Z"),
    )
    outcomes = {
        "config-a": {task.instance_id: 0 for task in tasks},
        "config-b": {task.instance_id: 1 for task in tasks},
    }
    data = _build_composition_data(
        tasks,
        outcomes,
        ("config-a", "config-b"),
    )
    difficulty = np.asarray(
        [
            [0.0, 0.0],
            [1.0, 1.0],
            [100.0, 100.0],
            [1.0, 0.0],
            [100.0, 100.0],
        ]
    )

    prior = _global_prior(
        data,
        difficulty,
        target_repository_id="target",
        cutoff="2026-01-02T00:00:00Z",
    )

    # train-a contributes its eligible mean [0.5, 0.5] once and train-b
    # contributes [1.0, 0.0] once. The late and target rows cannot contribute.
    assert prior == pytest.approx([0.75, 0.25])
    assert (
        _eligible_other_repository_count(
            data,
            target_repository_id="target",
            cutoff="2026-01-02T00:00:00Z",
        )
        == 2
    )


def _task(instance_id: str, repository_id: str, created_at: str) -> TaskMetadata:
    return TaskMetadata(
        instance_id=instance_id,
        repository_id=repository_id,
        created_at=created_at,
        difficulty="python",
        problem_statement="Task",
    )
