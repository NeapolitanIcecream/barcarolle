from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
    build_repository_origins,
)
from examples.swe_bench_full_transfer.study import (  # noqa: E402
    build_suitability_decision,
    load_plan,
    normalize_official_result,
    run_joint_block_order_null,
    select_alg_016u_origin_memberships,
)


def test_full_transfer_plan_is_self_bound_and_zero_cost() -> None:
    plan = load_plan()

    assert plan["source"]["task_count"] == 2294
    assert plan["agent_panel"]["agent_count"] == 11
    assert plan["frame"]["horizons"]["5"]["expected_origin_count"] == 408
    assert plan["frame"]["horizons"]["10"]["expected_origin_count"] == 201
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["conditional_algorithm"]["algorithm_id"] == "ALG-016U"


def test_full_transfer_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT / "examples" / "swe_bench_full_transfer" / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["frame"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(path)


def test_holdout_boundary_amendment_is_self_bound_and_preserves_decision() -> None:
    path = (
        REPOSITORY_ROOT
        / "examples"
        / "swe_bench_full_transfer"
        / "evidence-boundary-amendment-1.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest = payload.pop("amendment_digest")

    assert digest == canonical_digest(payload)
    assert payload["overlap"]["same_agent_identity_count"] == 3
    assert payload["overlap"]["verified_tasks_present_in_full"] == 500
    assert payload["resource_use"]["exact_verified_result_blob_reads"] == 0
    assert (
        payload["decision_effect"]["current_suitability_decision_changed"]
        is False
    )
    assert payload["decision_effect"]["algorithm_execution_authorized"] is False


def test_result_normalization_maps_only_resolved_and_accepts_legacy_overlap() -> None:
    current = {
        "resolved": ["task-a"],
        "no_generation": ["task-b"],
        "no_logs": [],
    }
    outcomes, diagnostics = normalize_official_result(
        ("task-a", "task-b", "task-c"),
        current,
        schema="current",
    )

    assert outcomes == {"task-a": 1, "task-b": 0, "task-c": 0}
    assert diagnostics["ordinary_unlisted_count"] == 1

    legacy = {
        key: []
        for key in (
            "applied",
            "generated",
            "install_fail",
            "no_apply",
            "no_generation",
            "reset_failed",
            "resolved",
            "test_errored",
            "test_timeout",
            "with_logs",
        )
    }
    legacy["applied"] = ["task-a"]
    legacy["generated"] = ["task-a"]
    legacy["resolved"] = ["task-a"]

    legacy_outcomes, _ = normalize_official_result(
        ("task-a", "task-b"),
        legacy,
        schema="legacy",
    )

    assert legacy_outcomes == {"task-a": 1, "task-b": 0}


def test_result_normalization_rejects_duplicate_or_unknown_ids() -> None:
    duplicate = {
        "resolved": ["task-a", "task-a"],
        "no_generation": [],
        "no_logs": [],
    }
    with pytest.raises(ValueError, match="duplicate"):
        normalize_official_result(("task-a",), duplicate, schema="current")

    unknown = {
        "resolved": ["task-outside"],
        "no_generation": [],
        "no_logs": [],
    }
    with pytest.raises(ValueError, match="outside"):
        normalize_official_result(("task-a",), unknown, schema="current")


def test_joint_block_order_null_is_seeded_and_matches_observed_statistic() -> None:
    np = pytest.importorskip("numpy")
    tasks = tuple(
        TaskMetadata(
            instance_id=f"repo-a-{index:02d}",
            repository_id="repo-a",
            created_at=f"2026-01-{index + 1:02d}T00:00:00Z",
            difficulty="not-used",
            problem_statement="synthetic",
        )
        for index in range(8)
    )
    origins = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=4,
        future_block_tasks=2,
    )
    outcomes = {
        "agent-a": {
            task.instance_id: int(index >= 4)
            for index, task in enumerate(tasks)
        },
        "agent-b": {
            task.instance_id: int(index % 2 == 0)
            for index, task in enumerate(tasks)
        },
    }

    first = run_joint_block_order_null(
        np=np,
        repository_ids=("repo-a",),
        origins_by_repository=origins,
        outcomes_by_agent=outcomes,
        horizon=2,
        draws=25,
        seed=73,
    )
    second = run_joint_block_order_null(
        np=np,
        repository_ids=("repo-a",),
        origins_by_repository=origins,
        outcomes_by_agent=outcomes,
        horizon=2,
        draws=25,
        seed=73,
    )

    assert first == second
    assert first["observed"] == pytest.approx(
        first["observed_full_history_mae"]
        - first["observed_best_fixed_constant_mae"]
    )
    assert 0.0 < first["one_sided_probability"] <= 1.0


def test_suitability_gate_blocks_algorithm_when_primary_chronology_fails() -> None:
    passing_horizon = {
        "repository_count": 10,
        "origin_count": 120,
        "largest_repository_origin_share": 0.4,
        "joint_response_pattern_count": 20,
        "future_outcome_cell_density": 0.3,
        "full_history_mae": 0.20,
        "best_fixed_constant_mae": 0.25,
        "oracle_mae": 0.10,
        "full_minus_best_fixed_constant_bootstrap_upper": -0.01,
        "joint_block_order_null_probability": 0.04,
    }

    passed = build_suitability_decision(
        {"5": passing_horizon, "10": passing_horizon}
    )
    nested = build_suitability_decision(
        {
            "5": {"controls_source": passing_horizon},
            "10": {"controls_source": passing_horizon},
        }
    )
    failed_h5 = dict(passing_horizon)
    failed_h5["joint_block_order_null_probability"] = 0.051
    failed = build_suitability_decision(
        {"5": failed_h5, "10": passing_horizon}
    )

    assert passed["algorithm_execution_authorized"] is True
    assert nested == passed
    assert all(passed["gates"].values())
    assert failed["algorithm_execution_authorized"] is False
    assert failed["gates"]["chronology"] is False


def test_alg_016u_membership_for_target_does_not_use_target_outcomes() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    history = np.asarray(
        [
            [index % 2, (index // 2) % 2, (index // 3) % 2]
            for index in range(12)
        ],
        dtype=np.float64,
    )
    changed_target = history.copy()
    changed_target[:, 0] = 1.0 - changed_target[:, 0]
    order = tuple(
        (f"2026-01-{index + 1:02d}T00:00:00Z", f"task-{index:02d}")
        for index in range(len(history))
    )

    original = select_alg_016u_origin_memberships(
        history,
        horizon=2,
        budget=3,
        created_order=order,
    )
    changed = select_alg_016u_origin_memberships(
        changed_target,
        horizon=2,
        budget=3,
        created_order=order,
    )

    assert original[0]["ALG-016U"] == changed[0]["ALG-016U"]
    assert (
        original[0]["unseen_full_response_assembly"]
        == changed[0]["unseen_full_response_assembly"]
    )
