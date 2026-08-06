from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.finite_horizon_cached_assembly.study import (  # noqa: E402
    jeffreys_weights,
    load_plan,
    plugin_weights,
    select_fixed_success_count_indices,
    select_jeffreys_action,
    select_plugin_action,
)


def test_finite_horizon_plan_is_self_bound() -> None:
    plan = load_plan()

    assert plan["plan_digest"] == (
        "6602a349d5c108fef96fb9e15d405bf268619b0fdd2721500f6a5c62ad9264b7"
    )
    assert plan["candidate"]["algorithm_id"] == "ALG-018C"
    assert plan["fixed_ablation"]["algorithm_id"] == "ALG-018C-P"


def test_finite_horizon_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT / "examples" / "finite_horizon_cached_assembly" / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["research_contract"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(path)


def test_symmetric_h5_jeffreys_probabilities_and_tie() -> None:
    weights = jeffreys_weights(20, 10, 5)
    total = sum(weights, Fraction())
    probabilities = tuple(value / total for value in weights)

    assert probabilities == tuple(
        Fraction(value, 5632) for value in (261, 945, 1610, 1610, 945, 261)
    )
    risks = {
        q: sum(
            (weight * abs(5 * q - 10 * k) for k, weight in enumerate(weights)),
            Fraction(),
        )
        for q in range(11)
    }
    minimum = min(risks.values())
    assert tuple(q for q, risk in risks.items() if risk == minimum) == (4, 5, 6)
    assert select_jeffreys_action(20, 10, 5, 10).q == 5


@pytest.mark.parametrize(
    ("n", "s", "horizon", "expected"),
    (
        (20, 10, 10, 5),
        (16, 2, 5, 2),
        (16, 14, 5, 8),
        (20, 2, 5, 0),
        (20, 2, 10, 1),
        (10, 1, 5, 1),
    ),
)
def test_frozen_jeffreys_golden_actions(
    n: int,
    s: int,
    horizon: int,
    expected: int,
) -> None:
    assert select_jeffreys_action(n, s, horizon, 10).q == expected


def test_plugin_separates_from_jeffreys() -> None:
    assert select_jeffreys_action(16, 2, 5, 10).q == 2
    assert select_plugin_action(16, 2, 5, 10).q == 0
    assert plugin_weights(16, 2, 5) == tuple(
        Fraction(value)
        for value in (
            14**5,
            5 * 2 * 14**4,
            10 * 2**2 * 14**3,
            10 * 2**3 * 14**2,
            5 * 2**4 * 14,
            2**5,
        )
    )


def test_inventory_clamp_is_explicit() -> None:
    constrained = select_jeffreys_action(10, 1, 5, 10)
    unconstrained = select_jeffreys_action(
        10,
        1,
        5,
        10,
        ignore_inventory=True,
    )

    assert constrained.feasible_q == (1,)
    assert constrained.q == 1
    assert unconstrained.q == 0
    assert constrained.q != unconstrained.q


def test_fixed_success_materializer_uses_visible_priority() -> None:
    outcomes = (0, 1, 0, 1, 0, 1)
    order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(outcomes))
    )

    selected = select_fixed_success_count_indices(
        outcomes,
        2,
        budget=4,
        created_order=order,
    )

    assert selected == (2, 3, 4, 5)
    assert sum(outcomes[index] for index in selected) == 2


def test_exact_actions_reject_invalid_counts() -> None:
    with pytest.raises(ValueError, match="counts"):
        select_jeffreys_action(9, 2, 5, 10)
    with pytest.raises(ValueError, match="counts"):
        select_plugin_action(20, 21, 5, 10)
