from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.portfolio import (  # noqa: E402
    build_portfolio,
    load_portfolio_plan,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
    build_repository_origins,
    load_portfolio,
    load_public_panel_plan,
    official_binary_outcomes,
    run_public_replay,
)


def _task_rows(repository_id: str, count: int) -> tuple[dict[str, str], ...]:
    start = datetime(2020, 1, 1, tzinfo=UTC)
    return tuple(
        {
            "repo": repository_id,
            "instance_id": f"{repository_id.replace('/', '__')}-{index:03d}",
            "created_at": (start + timedelta(days=index)).isoformat(),
            "difficulty": "short" if index % 2 == 0 else "long",
        }
        for index in range(count)
    )


def _portfolio_plan(*repository_ids: str) -> dict[str, Any]:
    return {
        "origin_protocol": {
            "minimum_initial_history_tasks": 15,
            "future_block_tasks": 5,
            "deep_minimum_origins": 5,
        },
        "repository_lineage": {
            repository_id: {
                "repository_cluster_id": repository_id,
                "fork": False,
            }
            for repository_id in repository_ids
        },
    }


def test_build_portfolio_uses_complete_local_blocks_for_wide_and_deep() -> None:
    rows = (
        *_task_rows("org/wide", 22),
        *_task_rows("org/deep", 44),
        *_task_rows("org/excluded", 19),
    )

    portfolio = build_portfolio(
        rows,
        _portfolio_plan("org/wide", "org/deep", "org/excluded"),
    )

    by_repository = {
        row["repository_id"]: row for row in portfolio["repositories"]
    }
    assert portfolio["wide_repository_ids"] == ("org/deep", "org/wide")
    assert portfolio["deep_repository_ids"] == ("org/deep",)
    assert by_repository["org/wide"]["initial_history_task_count"] == 17
    assert by_repository["org/wide"]["origin_count"] == 1
    assert by_repository["org/deep"]["initial_history_task_count"] == 19
    assert by_repository["org/deep"]["origin_count"] == 5
    assert by_repository["org/excluded"]["exclusion_reason"] == (
        "fewer_than_one_complete_origin"
    )


def test_build_portfolio_rejects_missing_repository_lineage() -> None:
    with pytest.raises(ValueError, match="repository lineage"):
        build_portfolio(
            (*_task_rows("org/known", 20), *_task_rows("org/missing", 20)),
            _portfolio_plan("org/known"),
        )


def test_frozen_multi_repository_plans_and_portfolio_replay() -> None:
    portfolio_plan = load_portfolio_plan()
    portfolio = load_portfolio()
    public_plan = load_public_panel_plan()

    assert portfolio_plan["authority"]["paid_api_calls"] == 0
    assert public_plan["authority"]["paid_api_calls"] == 0
    assert (
        public_plan["portfolio"]["portfolio_digest"]
        == portfolio["portfolio_digest"]
    )
    assert len(portfolio["wide_repository_ids"]) == 7
    assert len(portfolio["deep_repository_ids"]) == 3


def test_opened_development_plan_is_self_digested_and_zero_cost() -> None:
    plan = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/development-plan.json"
        ).read_text()
    )
    digest = plan.pop("development_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["epistemic_status"] == "opened_outcome_development_only"
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["embedding_calls"] == 0


def test_committed_public_panel_result_is_self_digested_and_negative() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/public-panel-results.json"
        ).read_text()
    )
    digest = results.pop("public_panel_results_digest")

    assert canonical_digest(results) == digest
    assert results["task_count"] == 500
    assert results["agent_count"] == 3
    assert all(
        decision["status"] == "no_exploratory_nomination"
        and decision["promotion_allowed"] is False
        for decision in results["decisions"].values()
    )
    wide = results["summaries"]["wide"]
    assert wide["recency"]["macro_repository_difference"] == pytest.approx(
        0.018900604036508516
    )
    assert wide["difficulty_coverage"][
        "macro_repository_difference"
    ] == pytest.approx(0.039777311308564635)
    assert results["random_calibration"]["wide"]["candidate_positions"][
        "recency"
    ]["candidate_better_than_random_midrank"] == pytest.approx(0.458325)


def test_summarize_contrasts_weights_repositories_before_origins() -> None:
    rows = tuple(
        ContrastRow(
            selector_id="coverage",
            portfolio="wide",
            repository_id="org/large",
            repository_cluster_id="org/large",
            origin_id=f"large-{index}",
            difference=-0.1,
        )
        for index in range(10)
    ) + (
        ContrastRow(
            selector_id="coverage",
            portfolio="wide",
            repository_id="org/small",
            repository_cluster_id="org/small",
            origin_id="small-1",
            difference=0.1,
        ),
    )

    summary = summarize_contrasts(rows, bootstrap_seed=7, bootstrap_resamples=200)

    assert summary["macro_repository_difference"] == pytest.approx(0.0)
    assert summary["origin_weighted_difference"] == pytest.approx(-0.0818181818)
    assert summary["favorable_repository_count"] == 1
    assert summary["repository_count"] == 2


def test_summarize_contrasts_omits_repository_clusters_as_units() -> None:
    rows = (
        ContrastRow("candidate", "wide", "org/fork-a", "family-a", "a-1", -0.2),
        ContrastRow("candidate", "wide", "org/fork-b", "family-a", "b-1", -0.1),
        ContrastRow("candidate", "wide", "org/other", "family-b", "c-1", 0.3),
    )

    summary = summarize_contrasts(rows, bootstrap_seed=9, bootstrap_resamples=200)

    leave_one_out = {
        row["omitted_repository_cluster_id"]: row["macro_repository_difference"]
        for row in summary["leave_one_cluster_out"]
    }
    assert leave_one_out == {
        "family-a": pytest.approx(0.3),
        "family-b": pytest.approx(-0.15),
    }
    assert summary["repository_cluster_count"] == 2


def test_summarize_contrasts_rejects_duplicate_repository_origin() -> None:
    row = ContrastRow("candidate", "wide", "org/repo", "org/repo", "origin-1", 0.1)

    with pytest.raises(ValueError, match="duplicate repository Origin"):
        summarize_contrasts(
            (row, row),
            bootstrap_seed=1,
            bootstrap_resamples=10,
        )


def test_existing_sympy_study_is_a_single_repository_input() -> None:
    landscape = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/offline_selector_study/landscape-results.json"
        ).read_text()
    )
    differences = landscape["baseline"]["coverage_minus_full_history"][
        "origin_differences"
    ]
    rows = tuple(
        ContrastRow(
            selector_id="coverage",
            portfolio="development",
            repository_id="sympy/sympy",
            repository_cluster_id="sympy/sympy",
            origin_id=f"sympy-origin-{index:02d}",
            difference=difference,
        )
        for index, difference in enumerate(differences)
    )

    summary = summarize_contrasts(
        rows,
        bootstrap_seed=20260727,
        bootstrap_resamples=100,
    )

    assert summary["repository_count"] == 1
    assert summary["repository_cluster_interval_95"] is None
    assert summary["macro_repository_difference"] == pytest.approx(
        -0.009956432456432449
    )


def test_build_repository_origins_never_crosses_repository_boundary() -> None:
    tasks = tuple(
        TaskMetadata(
            instance_id=row["instance_id"],
            repository_id=row["repo"],
            created_at=row["created_at"],
            difficulty=row["difficulty"],
            problem_statement="task",
        )
        for row in (*_task_rows("org/a", 22), *_task_rows("org/b", 20))
    )

    origins = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=15,
        future_block_tasks=5,
    )

    by_repository = {
        repository_id: rows for repository_id, rows in origins.items()
    }
    assert len(by_repository["org/a"]) == 1
    assert len(by_repository["org/a"][0].history) == 17
    assert len(by_repository["org/a"][0].future) == 5
    assert len(by_repository["org/b"]) == 1
    for repository_id, repository_origins in by_repository.items():
        for origin in repository_origins:
            assert {
                task.repository_id for task in (*origin.history, *origin.future)
            } == {repository_id}


def test_official_binary_outcomes_uses_dataset_as_the_denominator() -> None:
    outcomes, diagnostics = official_binary_outcomes(
        ("task-1", "task-2", "task-3", "task-4"),
        {
            "resolved": ["task-1"],
            "no_generation": ["task-2"],
            "no_logs": ["task-3"],
        },
    )

    assert outcomes == {
        "task-1": 1,
        "task-2": 0,
        "task-3": 0,
        "task-4": 0,
    }
    assert diagnostics == {
        "resolved_count": 1,
        "no_generation_count": 1,
        "no_logs_count": 1,
        "ordinary_unresolved_count": 1,
    }


def test_public_replay_runs_repository_local_random_and_null_controls() -> None:
    task_rows = (*_task_rows("org/a", 20), *_task_rows("org/b", 20))
    tasks = tuple(
        TaskMetadata(
            row["instance_id"],
            row["repo"],
            row["created_at"],
            row["difficulty"],
            f"Task {index}",
        )
        for index, row in enumerate(task_rows)
    )
    outcomes = {
        "agent-a": {
            task.instance_id: int(index % 3 == 0)
            for index, task in enumerate(tasks)
        },
        "agent-b": {
            task.instance_id: int(index % 4 < 2)
            for index, task in enumerate(tasks)
        },
    }
    portfolio_without_digest: dict[str, Any] = {
        "schema_version": "barcarolle_repository_portfolio_v1",
        "repositories": (
            {
                "repository_id": "org/a",
                "repository_cluster_id": "org/a",
            },
            {
                "repository_id": "org/b",
                "repository_cluster_id": "org/b",
            },
        ),
    }
    portfolio = {
        **portfolio_without_digest,
        "portfolio_digest": canonical_digest(portfolio_without_digest),
    }
    plan: dict[str, Any] = {
        "study_id": "fixture",
        "epistemic_status": "fixture",
        "public_panel_plan_digest": "fixture-plan",
        "portfolio": {
            "portfolio_digest": portfolio["portfolio_digest"],
            "wide_repository_ids": ("org/a", "org/b"),
            "deep_repository_ids": ("org/a", "org/b"),
        },
        "rolling_origin": {
            "minimum_initial_history_tasks": 15,
            "future_block_tasks": 5,
            "selection_budget_task_checks": 10,
        },
        "selectors": (
            {"selector_id": "full_history"},
            {"selector_id": "recency"},
            {"selector_id": "difficulty_coverage"},
        ),
        "aggregation": {
            "bootstrap_seed": 3,
            "bootstrap_resamples": 20,
        },
        "random_calibration": {"draws": 20, "seed": 4},
        "null_control": {
            "within_repository_outcome_permutations": 10,
            "seed": 5,
        },
    }

    report = run_public_replay(
        tasks,
        outcomes,
        {
            "agent-a": {"resolved_count": 14},
            "agent-b": {"resolved_count": 20},
        },
        plan,
        portfolio,
    )

    assert report["task_count"] == 40
    assert report["origin_counts"] == {"org/a": 1, "org/b": 1}
    assert set(report["summaries"]["wide"]) == {
        "recency",
        "difficulty_coverage",
    }
    assert report["random_calibration"]["wide"]["draw_count"] == 20
    assert (
        report["permutation_control"]["wide"]["recency"]["permutation_count"]
        == 10
    )


@pytest.mark.parametrize(
    "payload, message",
    [
        (
            {
                "resolved": ["unknown"],
                "no_generation": [],
                "no_logs": [],
            },
            "outside the Task denominator",
        ),
        (
            {
                "resolved": ["task-1"],
                "no_generation": ["task-1"],
                "no_logs": [],
            },
            "overlap",
        ),
        (
            {
                "resolved": ["task-1"],
                "no_generation": [],
                "no_logs": [],
                "new_status": [],
            },
            "fields",
        ),
    ],
)
def test_official_binary_outcomes_rejects_ambiguous_evidence(
    payload: dict[str, list[str]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        official_binary_outcomes(("task-1",), payload)
