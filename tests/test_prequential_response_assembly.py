from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.prequential_response_assembly.study import (  # noqa: E402
    adanormalhedge_forecast,
    adanormalhedge_weights,
    create_adanormalhedge_state,
    load_addendum,
    load_plan,
    response_expert_forecasts,
    select_cached_scalar_indices,
    select_greedy_l1_indices,
    shared_bocpd_forecast_with_prior,
    solve_exact_l1_assembly,
    update_adanormalhedge,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    load_selector_plan,
)


def test_prequential_response_plan_is_self_bound() -> None:
    plan = load_plan()

    assert plan["study_id"] == "prequential-response-assembly-2026-07-29"
    assert plan["resource_boundary"]["paid_api_calls"] == 0
    assert plan["fixed_facts"]["h5_origin_count"] == 221
    assert tuple(item["algorithm_id"] for item in plan["portfolio"]) == (
        "ALG-015C",
        "ALG-015U",
        "ALG-016U",
        "ALG-017U",
    )
    addendum = load_addendum(plan=plan)
    assert addendum["alg_017_decision"]["status"] == (
        "deferred_before_any_new_candidate_score"
    )
    selector_plan = load_selector_plan()
    assert (
        selector_plan["source"]["task_time_projection_digest"]
        == (addendum["execution_identity_requirements"]["task_time_projection_digest"])
    )


def test_prequential_response_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT / "examples" / "prequential_response_assembly" / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["fixed_facts"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(path)


def test_adanormalhedge_cold_start_is_uniform_and_parameter_free() -> None:
    np = pytest.importorskip("numpy")
    state = create_adanormalhedge_state(2)
    experts = np.asarray(
        [
            [0.0, 0.2],
            [0.2, 0.4],
            [0.4, 0.6],
            [0.6, 0.8],
        ],
        dtype=np.float64,
    )

    forecast, weights = adanormalhedge_forecast(state, experts)

    assert weights == pytest.approx(np.full((4, 2), 0.25))
    assert forecast == pytest.approx(np.asarray([0.3, 0.5]))


def test_adanormalhedge_increases_weight_on_better_expert() -> None:
    np = pytest.importorskip("numpy")
    state = create_adanormalhedge_state(1)
    experts = np.asarray([[0.0], [1.0], [1.0], [1.0]], dtype=np.float64)
    truth = np.asarray([0.0], dtype=np.float64)

    for _ in range(4):
        update_adanormalhedge(state, experts, truth)
    weights = adanormalhedge_weights(state)

    assert weights[0, 0] > 0.25
    assert weights[0, 0] > weights[1, 0]
    assert float(weights[:, 0].sum()) == pytest.approx(1.0)


def test_adanormalhedge_one_step_matches_golden_weights() -> None:
    np = pytest.importorskip("numpy")
    state = create_adanormalhedge_state(1)
    experts = np.asarray([[0.0], [0.25], [0.5], [1.0]], dtype=np.float64)

    update_adanormalhedge(state, experts, np.asarray([0.0]))
    weights = adanormalhedge_weights(state)

    assert state.regret[:, 0] == pytest.approx([0.4375, 0.1875, -0.0625, -0.5625])
    assert state.absolute_regret[:, 0] == pytest.approx(
        [0.4375, 0.1875, 0.0625, 0.5625]
    )
    assert weights[:, 0] == pytest.approx(
        [0.4211830510, 0.3327252840, 0.2175355201, 0.0285561449],
        abs=1e-9,
    )


def test_adanormalhedge_log_weight_is_stable_near_zero_difference() -> None:
    np = pytest.importorskip("numpy")
    state = create_adanormalhedge_state(1)
    state.regret[:, 0] = -1.0 + 2.0**-52
    state.absolute_regret[:, 0] = 1.0

    weights = adanormalhedge_weights(state)

    assert np.all(np.isfinite(weights))
    assert weights[:, 0] == pytest.approx([0.25] * 4)


def test_response_experts_have_frozen_semantics() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 0],
        ],
        dtype=np.float64,
    )

    experts = response_expert_forecasts(history, horizon=2)

    assert experts[0] == pytest.approx([0.5, 0.25])
    assert experts[1] == pytest.approx([1.0, 0.0])
    assert experts[2] == pytest.approx([0.5, 0.25])
    assert experts[3] == pytest.approx([1.0, 0.0])


def test_cached_scalar_selection_is_exact_and_prefers_newer_tasks() -> None:
    outcomes = (0, 1, 0, 1, 0, 1)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(outcomes))
    )

    selected = select_cached_scalar_indices(
        outcomes,
        0.5,
        budget=4,
        created_order=order,
    )

    assert selected == (2, 3, 4, 5)
    assert sum(outcomes[index] for index in selected) == 2


def test_exact_l1_assembly_matches_brute_force() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    outcomes = np.asarray(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
        ],
        dtype=np.float64,
    )
    target = np.asarray([0.45, 0.30, 0.55], dtype=np.float64)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(outcomes))
    )

    result = solve_exact_l1_assembly(
        outcomes,
        target,
        budget=3,
        created_order=order,
    )
    brute = min(
        float(np.abs(outcomes[list(indices)].mean(axis=0) - target).mean())
        for indices in combinations(range(len(outcomes)), 3)
    )

    assert len(result.indices) == 3
    assert result.objective == pytest.approx(brute, abs=1e-8)
    assert result.response_pattern_count == 7


def test_exact_l1_assembly_uses_only_visible_coordinates() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    visible = np.asarray(
        [
            [0, 0],
            [1, 0],
            [0, 1],
            [1, 1],
            [0, 0],
        ],
        dtype=np.float64,
    )
    target = np.asarray([0.4, 0.6], dtype=np.float64)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(visible))
    )

    first = solve_exact_l1_assembly(
        visible,
        target,
        budget=3,
        created_order=order,
    )
    poisoned_target_column = np.asarray([0, 1, 1, 0, 1], dtype=np.float64)
    second_input = np.column_stack((visible, poisoned_target_column))[:, :2]
    second = solve_exact_l1_assembly(
        second_input,
        target,
        budget=3,
        created_order=order,
    )

    assert first.indices == second.indices
    assert first.objective == second.objective


def test_exact_l1_secondary_tie_prefers_visible_recency() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    visible = np.zeros((6, 2), dtype=np.float64)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(visible))
    )

    result = solve_exact_l1_assembly(
        visible,
        np.zeros(2, dtype=np.float64),
        budget=3,
        created_order=order,
    )

    assert result.indices == (3, 4, 5)
    assert result.objective == 0.0


def test_greedy_l1_is_deterministic_and_never_repeats_tasks() -> None:
    np = pytest.importorskip("numpy")
    visible = np.asarray(
        [[0, 0], [1, 0], [0, 1], [1, 1], [0, 0], [1, 1]],
        dtype=np.float64,
    )
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(visible))
    )

    first = select_greedy_l1_indices(
        visible,
        np.asarray([0.5, 0.5]),
        budget=4,
        created_order=order,
    )
    second = select_greedy_l1_indices(
        visible,
        np.asarray([0.5, 0.5]),
        budget=4,
        created_order=order,
    )

    assert first == second
    assert len(first) == len(set(first)) == 4


def test_unseen_ada_coordinates_ignore_poisoned_held_out_column() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    first_history = np.asarray(
        [
            [0, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
        ],
        dtype=np.float64,
    )
    second_history = first_history.copy()
    second_history[:, 0] = 1.0 - second_history[:, 0]
    first_state = create_adanormalhedge_state(3)
    second_state = create_adanormalhedge_state(3)
    first_experts = response_expert_forecasts(first_history, horizon=2)
    second_experts = response_expert_forecasts(second_history, horizon=2)
    first_forecast, _ = adanormalhedge_forecast(first_state, first_experts)
    second_forecast, _ = adanormalhedge_forecast(second_state, second_experts)

    assert first_forecast[1:] == pytest.approx(second_forecast[1:])
    update_adanormalhedge(
        first_state,
        first_experts,
        np.asarray([0.0, 0.5, 1.0]),
    )
    update_adanormalhedge(
        second_state,
        second_experts,
        np.asarray([1.0, 0.5, 1.0]),
    )

    assert first_state.regret[:, 1:] == pytest.approx(second_state.regret[:, 1:])
    assert first_state.absolute_regret[:, 1:] == pytest.approx(
        second_state.absolute_regret[:, 1:]
    )
    first_next, _ = adanormalhedge_forecast(first_state, first_experts)
    second_next, _ = adanormalhedge_forecast(second_state, second_experts)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(first_history))
    )
    first_membership = solve_exact_l1_assembly(
        first_history[:, 1:],
        first_next[1:],
        budget=2,
        created_order=order,
    )
    second_membership = solve_exact_l1_assembly(
        second_history[:, 1:],
        second_next[1:],
        budget=2,
        created_order=order,
    )

    assert first_membership.indices == second_membership.indices


def test_shared_bocpd_single_agent_golden_recurrence() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray([[1.0], [0.0]], dtype=np.float64)

    result = shared_bocpd_forecast_with_prior(
        history,
        horizon=2,
        hazard=0.25,
        alpha0=np.asarray([1.0]),
        beta0=np.asarray([1.0]),
        anchor=np.asarray([0.5]),
    )

    assert result.run_length_probabilities == pytest.approx([1 / 3, 2 / 3])
    assert result.mixture == pytest.approx([89 / 192])
    assert result.map_run_length == 2


def test_shared_bocpd_uses_one_shared_run_length() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray([[1.0, 0.0], [1.0, 0.0]], dtype=np.float64)

    result = shared_bocpd_forecast_with_prior(
        history,
        horizon=1,
        hazard=0.25,
        alpha0=np.asarray([1.0, 1.0]),
        beta0=np.asarray([1.0, 1.0]),
        anchor=np.asarray([0.5, 0.5]),
    )

    assert result.run_length_probabilities == pytest.approx([3 / 19, 16 / 19])
    assert result.mixture == pytest.approx([103 / 152, 49 / 152])
