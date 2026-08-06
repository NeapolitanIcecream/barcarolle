from __future__ import annotations

from datetime import UTC, datetime
import json
from math import fsum
from pathlib import Path
import sys
from typing import Any, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.generator_calibrated_selection import study as selection_study  # noqa: E402
from examples.generator_calibrated_selection.study import (  # noqa: E402
    PREDICTOR_IDS,
    _mapping_sequence,
    _verify_membership_rows,
    bind_candidate_random_position,
    decide_task_space,
    load_plan,
    run_task_space,
    select_brier_projection,
    task_distribution,
)
from examples.pre_origin_task_mix.study import TaskProjection  # noqa: E402
from barcarolle.records import canonical_digest  # noqa: E402

PLAN_PATH = (
    REPOSITORY_ROOT / "examples" / "generator_calibrated_selection" / "plan.json"
)


def _task(instance_id: str, *modules: str) -> TaskProjection:
    return TaskProjection(
        instance_id=instance_id,
        repository_id="example/repository",
        source_time=datetime(2020, 1, 1, tzinfo=UTC),
        base_commit=instance_id[0] * 40,
        modules=tuple(modules),
    )


def test_brier_projection_matches_target_and_is_order_invariant() -> None:
    history = (
        _task("a-1", "a"),
        _task("a-2", "a"),
        _task("b-1", "b"),
        _task("b-2", "b"),
    )

    selected, diagnostics = select_brier_projection(
        history,
        {"a": 0.5, "b": 0.5, "OTHER": 0.0},
        ("a", "b", "OTHER"),
        unseen_label="OTHER",
        budget=2,
        tie_domain="test",
    )
    reversed_selected, reversed_diagnostics = select_brier_projection(
        tuple(reversed(history)),
        {"a": 0.5, "b": 0.5, "OTHER": 0.0},
        ("a", "b", "OTHER"),
        unseen_label="OTHER",
        budget=2,
        tie_domain="test",
    )

    assert {task.modules for task in selected} == {("a",), ("b",)}
    assert selected == reversed_selected
    assert diagnostics == reversed_diagnostics
    assert diagnostics["final_objective"] == pytest.approx(0.0)


def test_brier_projection_reports_cold_support_without_pseudo_tasks() -> None:
    selected, diagnostics = select_brier_projection(
        (_task("a-1", "a"), _task("a-2", "a")),
        {"a": 0.5, "cold": 0.5, "OTHER": 0.0},
        ("a", "cold", "OTHER"),
        unseen_label="OTHER",
        budget=1,
        tie_domain="test",
    )

    assert len(selected) == 1
    assert diagnostics["cold_support_mass"] == pytest.approx(0.5)
    assert diagnostics["cold_support_module_count"] == 1
    assert diagnostics["cold_support_brier_lower_bound"] == pytest.approx(0.25)

    with pytest.raises(ValueError, match="no historical Task support"):
        select_brier_projection(
            (_task("a-1", "a"),),
            {
                "a": 0.0,
                "cold": 0.9999999999999999,
                "OTHER": 0.0,
            },
            ("a", "cold", "OTHER"),
            unseen_label="OTHER",
            budget=1,
            tie_domain="test",
        )

    with pytest.raises(ValueError, match="target is invalid"):
        select_brier_projection(
            (_task("a-1", "a"),),
            {"a": float("nan"), "OTHER": 0.0},
            ("a", "OTHER"),
            unseen_label="OTHER",
            budget=1,
            tie_domain="test",
        )


def test_multimodule_projection_is_a_one_swap_local_optimum() -> None:
    history = (
        _task("t-1", "a", "b"),
        _task("t-2", "a"),
        _task("t-3", "b"),
        _task("t-4", "b", "c"),
        _task("t-5", "c"),
    )
    target = {"a": 0.2, "b": 0.5, "c": 0.3, "OTHER": 0.0}
    vocabulary = tuple(target)
    selected, _ = select_brier_projection(
        history,
        target,
        vocabulary,
        unseen_label="OTHER",
        budget=2,
        tie_domain="test",
    )

    def objective(tasks: tuple[TaskProjection, ...]) -> float:
        distribution = task_distribution(
            tasks,
            vocabulary,
            unseen_label="OTHER",
        )
        return fsum((distribution[label] - target[label]) ** 2 for label in vocabulary)

    selected_ids = {task.instance_id for task in selected}
    selected_objective = objective(selected)
    for outgoing in selected:
        for incoming in history:
            if incoming.instance_id in selected_ids:
                continue
            swapped = tuple(incoming if task == outgoing else task for task in selected)
            assert selected_objective <= objective(swapped)


def _contrast(
    value: float,
    *,
    favorable: int,
    repositories: int = 11,
) -> dict[str, object]:
    return {
        "macro_repository": value,
        "favorable_repository_count": favorable,
        "repository_count": repositories,
        "bootstrap_95_interval": (value - 0.01, value - 0.001),
        "leave_one_repository_out": tuple(value for _ in range(repositories)),
    }


def _passing_task_space_summary() -> dict[str, object]:
    horizons = {}
    for horizon, favorable in (("5", 8), ("10", 7)):
        horizons[horizon] = {
            "repository_count": 11,
            "contrasts": {
                "forecast_full": _contrast(-0.02, favorable=favorable),
                "forecast_git": _contrast(-0.03, favorable=favorable),
                "forecast_yield": _contrast(-0.04, favorable=favorable),
                "selection_full": _contrast(-0.01, favorable=favorable),
                "selection_stationary": _contrast(-0.005, favorable=favorable),
                "selection_recency": _contrast(-0.006, favorable=favorable),
            },
        }
    return {"horizons": horizons}


def test_random_position_uses_midrank_and_drives_frozen_gate() -> None:
    task_summary = _passing_task_space_summary()
    raw = {
        "membership_digest": "m",
        "draws": 4,
        "seed": 1,
        "chunk_size": 4,
        "horizons": {
            "5": (-0.02, 0.0, 0.01, 0.02),
            "10": (-0.02, 0.0, 0.01, 0.02),
        },
    }
    random_summary = bind_candidate_random_position(
        {
            "membership_digest": "m",
            "draws": 4,
            "seed": 1,
            "chunk_size": 4,
            "horizons": {"5": {}, "10": {}},
        },
        task_space_summary=task_summary,
        random_raw=raw,
    )

    assert cast(
        dict[str, Any],
        cast(dict[str, Any], random_summary["horizons"])["5"],
    )["candidate_better_than_random_midrank"] == pytest.approx(0.75)
    decision = decide_task_space(
        task_summary,
        random_summary=random_summary,
        expected_repository_count=11,
        admission_failures=(),
    )
    assert decision["status"] == "retire_mapping"
    assert decision["outcome_executor_amendment_authorized"] is False

    cast(dict[str, Any], random_summary["horizons"])["5"][
        "candidate_better_than_random_midrank"
    ] = 0.95
    decision = decide_task_space(
        task_summary,
        random_summary=random_summary,
        expected_repository_count=11,
        admission_failures=(),
    )
    assert decision["status"] == "pass"
    assert decision["outcome_executor_amendment_authorized"] is True


def test_source_admission_failure_blocks_outcome_amendment() -> None:
    random_summary = {
        "horizons": {
            "5": {"candidate_better_than_random_midrank": 1.0},
            "10": {"candidate_better_than_random_midrank": 1.0},
        }
    }

    decision = decide_task_space(
        _passing_task_space_summary(),
        random_summary=random_summary,
        expected_repository_count=11,
        admission_failures=(
            {
                "repository_id": "example/repository",
                "reason": "missing",
            },
        ),
    )

    assert decision == {
        "status": "data_blocked",
        "task_space_gate_passed": False,
        "outcome_executor_amendment_authorized": False,
        "gates": {"complete_source_admission": False},
    }


def test_empty_success_admission_list_is_valid_only_when_declared() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        _mapping_sequence({"failures": ()}, "failures")

    assert (
        _mapping_sequence(
            {"failures": ()},
            "failures",
            allow_empty=True,
        )
        == ()
    )


def test_admission_failure_skips_random_calibration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_manifest = {
        "source_id": "test",
        "source_revision": "0" * 40,
        "task_count": 0,
        "repository_count": 1,
        "task_universe_sha256": "a" * 64,
        "task_times_sha256": "b" * 64,
        "selected_source_files": (),
    }
    source_manifest["source_manifest_digest"] = canonical_digest(source_manifest)
    monkeypatch.setattr(
        selection_study,
        "load_tasks",
        lambda plan: ((), source_manifest),
    )
    plan = {
        "study_id": "test",
        "plan_digest": "p",
        "upstream_thy_002": {"result_digest": "u"},
        "source": {
            "repository_count": 1,
            "repositories": (
                {
                    "repository_id": "example/repository",
                    "expected_origin_count": 1,
                },
            ),
        },
        "rolling_origin": {
            "minimum_initial_history_tasks": 20,
            "future_block_tasks": 10,
            "primary_future_tasks": 5,
            "sensitivity_future_tasks": 10,
        },
        "module_projection": {"unseen_label": "OTHER"},
        "forecast": {
            "recent_half_life_days": 365.25,
            "prior_task_shape": 0.5,
        },
        "selector": {
            "budget_tasks": 10,
            "tie_domain": "test",
        },
        "task_space_gate": {"bootstrap_seed": 1},
        "random_landscape": {
            "draws": 20,
            "seed": 1,
            "chunk_size": 10,
            "numpy_version": "not-imported",
        },
    }

    result = run_task_space(plan, tmp_path)

    assert result["decision"]["status"] == "data_blocked"
    assert result["random_landscape_raw"]["status"] == ("not_run_due_source_admission")
    assert result["random_landscape_summary"]["horizons"] == {
        "5": None,
        "10": None,
    }


def _membership_fixture() -> tuple[
    dict[str, object],
    tuple[dict[str, object], ...],
    dict[str, object],
]:
    history = tuple(f"h-{index:02d}" for index in range(20))
    future = tuple(f"f-{index:02d}" for index in range(10))
    candidate = history[:10]
    stationary = history[5:15]
    membership: dict[str, object] = {
        "repository_id": "example/repository",
        "origin_id": "example/repository:origin-001",
        "origin_cutoff": "2020-01-01T00:00:00.000000Z",
        "history_task_ids": history,
        "future_h5_task_ids": future[:5],
        "future_h10_task_ids": future,
        "candidate_task_ids": candidate,
        "stationary_task_ids": stationary,
        "recency_task_ids": history[-10:],
        "candidate_diagnostics": {
            "budget": 10,
            "selection_digest": canonical_digest(candidate),
        },
        "stationary_diagnostics": {
            "budget": 10,
            "selection_digest": canonical_digest(stationary),
        },
    }
    membership["membership_digest"] = canonical_digest(membership)
    rows: tuple[dict[str, object], ...] = tuple(
        {
            "repository_id": "example/repository",
            "origin_id": "example/repository:origin-001",
            "origin_cutoff": membership["origin_cutoff"],
            "horizon": horizon,
            "history_task_count": 20,
            "future_task_count": horizon,
            "losses": {predictor_id: 0.1 for predictor_id in PREDICTOR_IDS},
        }
        for horizon in (5, 10)
    )
    source: dict[str, object] = {
        "repositories": (
            {
                "repository_id": "example/repository",
                "expected_origin_count": 1,
            },
        ),
    }
    return membership, rows, source


def test_membership_verifier_binds_exact_origin_and_selection_semantics() -> None:
    membership, rows, source = _membership_fixture()
    keyword_arguments = {
        "source": source,
        "selector": {"budget_tasks": 10},
        "rolling": {
            "primary_future_tasks": 5,
            "sensitivity_future_tasks": 10,
        },
        "failed_repository_ids": set(),
    }

    _verify_membership_rows(rows, (membership,), **keyword_arguments)

    missing_origin_source = {
        "repositories": (
            {
                "repository_id": "example/repository",
                "expected_origin_count": 2,
            },
        ),
    }
    with pytest.raises(ValueError, match="expected Origin"):
        _verify_membership_rows(
            rows,
            (membership,),
            **{**keyword_arguments, "source": missing_origin_source},
        )

    changed = dict(membership)
    changed["candidate_task_ids"] = (
        *cast(tuple[str, ...], changed["candidate_task_ids"])[:-1],
        "not-in-history",
    )
    changed["membership_digest"] = canonical_digest(
        {key: value for key, value in changed.items() if key != "membership_digest"}
    )
    with pytest.raises(ValueError, match="candidate membership"):
        _verify_membership_rows(rows, (changed,), **keyword_arguments)

    changed = dict(membership)
    changed["membership_digest"] = "wrong"
    with pytest.raises(ValueError, match="membership digest"):
        _verify_membership_rows(rows, (changed,), **keyword_arguments)

    changed_rows = (rows[0], {**rows[1], "history_task_count": 19})
    with pytest.raises(ValueError, match="row semantics"):
        _verify_membership_rows(
            changed_rows,
            (membership,),
            **keyword_arguments,
        )


def test_frozen_plan_binds_zero_outcome_front_gate() -> None:
    plan = cast(dict[str, Any], load_plan(PLAN_PATH))

    assert plan["selector"]["algorithm_id"] == "THY-002S"
    assert plan["selector"]["budget_tasks"] == 10
    assert plan["source"]["repository_count"] == 11
    assert plan["source"]["task_count"] == 1337
    assert plan["resource_budget"] == {
        "paid_api_calls": 0,
        "embedding_calls": 0,
        "agent_outcomes_opened": 0,
        "sealed_holdout_opened": 0,
    }
    assert plan["downstream_outcome_contract"]["state"] == (
        "frozen_not_executable_before_front_gate_pass"
    )


def test_plan_rejects_budget_change_without_new_digest(tmp_path: Path) -> None:
    payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    payload["selector"]["budget_tasks"] = 11
    changed = tmp_path / "plan.json"
    changed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(changed)
