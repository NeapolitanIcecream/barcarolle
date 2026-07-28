from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.multi_repository_study.public_replay import TaskMetadata  # noqa: E402
from examples.multi_swe_research.response_signal import (  # noqa: E402
    _build_study_data,
    _permute_outcomes,
    fit_response_contrast_projection,
    load_response_signal_amendment,
    load_response_signal_plan,
    ols_next_block_mean,
    roc_auc,
    transform_response_projection,
)


def test_response_signal_plan_and_amendment_are_self_bound() -> None:
    plan = load_response_signal_plan()
    amendment = load_response_signal_amendment(plan=plan)

    assert plan["response_signal_plan_digest"]
    assert (
        amendment["response_signal_plan_digest"] == plan["response_signal_plan_digest"]
    )


def test_response_signal_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "response-signal-plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["candidate"]["algorithm_id"] = "ALG-tampered"
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_response_signal_plan(path)


def test_roc_auc_handles_order_ties_and_one_class() -> None:
    assert roc_auc((0.1, 0.9), (0, 1)) == 1.0
    assert roc_auc((0.5, 0.5), (0, 1)) == 0.5
    assert roc_auc((0.1, 0.2), (0, 0)) is None


def test_ols_next_block_mean_extrapolates_one_block() -> None:
    np = pytest.importorskip("numpy")
    values = np.asarray(
        [
            [0.0, 2.0],
            [0.0, 2.0],
            [1.0, 1.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 0.0],
        ]
    )

    forecast = ols_next_block_mean(values, horizon=2)

    assert forecast == pytest.approx([3.0, -1.0])


def test_response_projection_excludes_target_and_cutoff_later_tasks() -> None:
    np = pytest.importorskip("numpy")
    tasks = (
        _task("train-a:1", "train-a", "2026-01-01T00:00:00Z"),
        _task("train-a:2", "train-a", "2026-01-02T00:00:00Z"),
        _task("train-a:3", "train-a", "2026-02-01T00:00:00Z"),
        _task("train-b:1", "train-b", "2026-01-01T00:00:00Z"),
        _task("train-b:2", "train-b", "2026-01-02T00:00:00Z"),
        _task("target:1", "target", "2026-01-01T00:00:00Z"),
        _task("target:2", "target", "2026-01-02T00:00:00Z"),
    )
    vectors = {
        "train-a:1": (1.0, 0.0),
        "train-a:2": (-1.0, 0.0),
        "train-a:3": (100.0, 0.0),
        "train-b:1": (2.0, 0.0),
        "train-b:2": (-2.0, 0.0),
        "target:1": (0.8, 0.0),
        "target:2": (-0.8, 0.0),
    }
    outcomes = {
        "config-a": {
            "train-a:1": 1,
            "train-a:2": 0,
            "train-a:3": 0,
            "train-b:1": 1,
            "train-b:2": 0,
            "target:1": 1,
            "target:2": 0,
        },
        "config-b": {
            "train-a:1": 0,
            "train-a:2": 1,
            "train-a:3": 1,
            "train-b:1": 0,
            "train-b:2": 1,
            "target:1": 0,
            "target:2": 1,
        },
    }
    data = _build_study_data(
        tasks,
        vectors,
        outcomes,
        ("config-a", "config-b"),
    )

    projection = fit_response_contrast_projection(
        data,
        target_repository_id="target",
        cutoff="2026-01-02T00:00:00Z",
        tolerance=1e-12,
    )
    target = transform_response_projection(
        np.asarray([vectors["target:1"], vectors["target:2"]]),
        projection,
    )

    assert projection.training_repository_ids == ("train-a", "train-b")
    assert projection.training_task_count == 4
    assert projection.maximum_training_time == "2026-01-02T00:00:00Z"
    assert target[0, 0] > target[1, 0]
    assert target[0, 1] < target[1, 1]


def test_outcome_permutation_preserves_complete_response_vectors() -> None:
    np = pytest.importorskip("numpy")
    outcomes = np.asarray(
        [
            [0.0, 1.0],
            [1.0, 1.0],
            [0.0, 0.0],
            [1.0, 0.0],
        ]
    )

    permuted = _permute_outcomes(outcomes, permutation_index=3)

    assert permuted.sum(axis=0) == pytest.approx(outcomes.sum(axis=0))
    assert sorted(map(tuple, permuted.tolist())) == sorted(
        map(tuple, outcomes.tolist())
    )
    assert not np.array_equal(permuted, outcomes)


def _task(instance_id: str, repository_id: str, created_at: str) -> TaskMetadata:
    return TaskMetadata(
        instance_id=instance_id,
        repository_id=repository_id,
        created_at=created_at,
        difficulty="python",
        problem_statement="Task",
    )
