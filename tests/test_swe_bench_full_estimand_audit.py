from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
)
from examples.swe_bench_full_estimand_audit.audit import (  # noqa: E402
    ALGORITHM_IDS,
    build_horizon_rows,
    load_plan,
    summarize_candidates,
)


def _task(instance_id: str, day: int) -> TaskMetadata:
    return TaskMetadata(
        instance_id=instance_id,
        repository_id="repo",
        created_at=f"2026-01-{day:02d}T00:00:00Z",
        difficulty="not-used",
        problem_statement="synthetic",
    )


def test_estimand_audit_plan_keeps_direct_mae_and_zero_cost() -> None:
    plan = load_plan(verify_bindings=False)

    assert plan["frame"]["deployment_unit"] == "one target Agent and one repository"
    assert plan["frame"]["horizons"] == [5, 10, 20, 40]
    assert any(
        "IID Bernoulli" in row
        for row in plan["research_contract"]["insufficient_outcomes"]
    )
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["algorithm_changes"] == 0


def test_direct_loss_is_computed_before_aggregation() -> None:
    history = _task("history", 1)
    first_future = _task("first-future", 2)
    second_future = _task("second-future", 3)
    origins = {
        "repo": (
            RepositoryOrigin(
                repository_id="repo",
                origin_id="repo:origin-001",
                history=(history,),
                future=(first_future,),
            ),
            RepositoryOrigin(
                repository_id="repo",
                origin_id="repo:origin-002",
                history=(history, first_future),
                future=(second_future,),
            ),
        )
    }
    rows = build_horizon_rows(
        origins,
        {
            "agent": {
                "history": 0,
                "first-future": 1,
                "second-future": 0,
            }
        },
    )

    assert [row["full_history_loss"] for row in rows] == [1.0, 0.5]
    assert sum(row["full_history_loss"] for row in rows) / len(rows) == 0.75


def test_joint_cell_harm_survives_favorable_marginals() -> None:
    score_rows = []
    cell_context = []
    recency_losses = {
        ("repo-a", "agent-a"): 0.0,
        ("repo-a", "agent-b"): 0.0,
        ("repo-b", "agent-a"): 0.0,
        ("repo-b", "agent-b"): 0.3,
    }
    for (repository_id, agent_id), recency_loss in recency_losses.items():
        losses = {algorithm_id: 0.2 for algorithm_id in ALGORITHM_IDS}
        losses["ordinary_recency"] = recency_loss
        score_rows.append(
            {
                "repository_id": repository_id,
                "origin_id": f"{repository_id}:origin-001",
                "target_agent_id": agent_id,
                "losses": losses,
            }
        )
        cell_context.append(
            {
                "repository_id": repository_id,
                "target_agent_id": agent_id,
                "origin_count": 1,
                "denominator_pass_rate": 0.2,
                "future_mean_pass_rate": 0.2,
                "zero_future_block_share": 0.0,
                "full_history_mae": 0.2,
            }
        )

    summary = summarize_candidates(
        {
            "score_rows": score_rows,
            "score_rows_digest": canonical_digest(score_rows),
        },
        cell_context,
        {
            "group-a": ("agent-a",),
            "group-b": ("agent-b",),
        },
        repository_ids=("repo-a", "repo-b"),
    )

    assert (
        summary["panel_macro"]["candidate_minus_full"]["ordinary_recency"]
        < 0.0
    )
    harmful = next(
        row
        for row in summary["cell_rows"]
        if row["repository_id"] == "repo-b"
        and row["target_agent_id"] == "agent-b"
    )
    assert harmful["candidate_minus_full"]["ordinary_recency"] > 0.0
    assert summary["per_candidate"]["ordinary_recency"][
        "favorable_cell_count"
    ] == 3
