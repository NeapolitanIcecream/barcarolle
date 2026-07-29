from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any, cast

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.finite_horizon_cached_assembly.study import (  # noqa: E402
    select_jeffreys_action,
    select_plugin_action,
)
from examples.finite_horizon_grid_audit.study import (  # noqa: E402
    CELL_SPECS,
    _direction_summary,
    _grid_loss_row,
    _q_diagnostics,
    load_plan,
    select_h_blind_action,
)


def test_grid_plan_is_self_bound() -> None:
    plan = load_plan()

    assert plan["plan_digest"] == (
        "8388fc583f7acf68a27c1864b673de91d87e895e2384366461ba87c00f2c4b1d"
    )
    assert tuple(plan["research_contract"]["required_cells"]) == tuple(
        cell_id for cell_id, _, _ in CELL_SPECS
    )


def test_grid_plan_rejects_tampering(tmp_path: Path) -> None:
    source = REPOSITORY_ROOT / "examples" / "finite_horizon_grid_audit" / "plan.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["research_contract"]["budgets"] = [5, 11]
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(path)


@pytest.mark.parametrize(
    ("n", "s", "budget", "expected"),
    (
        (20, 10, 5, 2),
        (20, 10, 10, 5),
        (20, 2, 5, 0),
        (20, 2, 10, 1),
        (10, 1, 10, 1),
    ),
)
def test_h_blind_action_is_exact_and_inventory_safe(
    n: int,
    s: int,
    budget: int,
    expected: int,
) -> None:
    action = select_h_blind_action(n, s, budget)

    assert action.q == expected
    assert action.q in action.feasible_q


def test_h_blind_breaks_half_grid_tie_toward_lower_q() -> None:
    action = select_h_blind_action(20, 10, 5)

    assert action.risk == 10
    assert action.q == 2


def test_grid_reuses_parent_exact_actions() -> None:
    actions = {
        (budget, horizon): (
            select_plugin_action(20, 2, horizon, budget).q,
            select_jeffreys_action(20, 2, horizon, budget).q,
        )
        for _, budget, horizon in CELL_SPECS
    }

    assert set(actions) == {(5, 5), (5, 10), (10, 5), (10, 10)}
    assert actions[(10, 5)] == (0, 0)
    assert actions[(10, 10)] == (1, 1)


def test_q_diagnostics_reports_method_differences() -> None:
    rows = [
        {
            "actions": {
                "ALG-018C-P": {"q": 2, "inventory_changed_action": False},
                "ALG-018C": {"q": 3, "inventory_changed_action": True},
                "h_blind_control": {"q": 2},
            }
        },
        {
            "actions": {
                "ALG-018C-P": {"q": 1, "inventory_changed_action": True},
                "ALG-018C": {"q": 1, "inventory_changed_action": False},
                "h_blind_control": {"q": 0},
            }
        },
    ]

    diagnostic = _q_diagnostics(rows)

    assert diagnostic["changed_from_h_blind_count"] == {
        "ALG-018C-P": 1,
        "ALG-018C": 2,
    }
    assert diagnostic["plugin_vs_jeffreys_action_difference_count"] == 1
    assert diagnostic["inventory_changed_action_count"] == {
        "ALG-018C-P": 1,
        "ALG-018C": 1,
    }


def test_budget_five_direct_loss_row_is_supported() -> None:
    np = pytest.importorskip("numpy")
    data = SimpleNamespace(
        outcomes=np.asarray(
            [[0], [0], [1], [1], [1], [0], [1], [0], [1], [1]],
            dtype=np.float64,
        ),
        configuration_ids=("agent",),
    )
    inputs = SimpleNamespace(data=data)

    row = _grid_loss_row(
        cast(Any, inputs),
        repository_id="repo",
        origin_id="origin",
        target=0,
        candidate=(0, 1, 2, 3, 4),
        full=tuple(range(8)),
        control=(3, 4, 5, 6, 7),
        future=(8, 9),
        budget=5,
    )

    assert row["candidate_loss"] == pytest.approx(0.4)
    assert row["full_loss"] == pytest.approx(0.5)


def test_direction_summary_exposes_leave_one_out_gate() -> None:
    rows = [
        {
            "repository_id": repository_id,
            "candidate_loss": 0.1,
            "full_loss": 0.2,
            "difference": -0.1,
        }
        for repository_id in ("a", "b", "c")
    ]

    summary = _direction_summary(rows, ("a", "b", "c"))

    assert summary["favorable_repository_count"] == 3
    assert summary["every_leave_one_repository_out_negative"] is True


def test_h_blind_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="counts"):
        select_h_blind_action(4, 2, 5)
    with pytest.raises(ValueError, match="counts"):
        select_h_blind_action(20, 21, 5)
