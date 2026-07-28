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
from examples.multi_repository_study.development import (  # noqa: E402
    estimate_repository_equal_drift,
    run_development_replay,
    select_outcome_match,
)
from examples.multi_repository_study.embed_local import (  # noqa: E402
    build_embedding_artifact,
)
from examples.multi_repository_study.portfolio import (  # noqa: E402
    build_portfolio,
    load_portfolio_plan,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
    load_portfolio,
    load_public_panel_plan,
    official_binary_outcomes,
    run_public_replay,
)
from examples.multi_repository_study.semantic import (  # noqa: E402
    select_centroid_recent,
    select_facility_recent,
)
from examples.multi_repository_study.theory import (  # noqa: E402
    complete_trailing_blocks,
    fit_repository_equal_markov,
    forecast_block_median,
    forecast_joint_markov,
    forecast_repository_analog,
    forecast_semantic_trend,
    load_theory_plan,
    select_embedding_mean_match,
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


def test_fixed_semantic_plan_is_self_digested_and_local_only() -> None:
    plan = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/semantic-plan.json"
        ).read_text()
    )
    digest = plan.pop("semantic_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["embedding_api_calls"] == 0
    assert plan["embedding"]["network_policy"] == "local_files_only"
    assert tuple(
        candidate["selector_id"] for candidate in plan["selection"]["candidates"]
    ) == ("centroid_recent_15", "facility_recent_15")


def test_theory_plan_is_self_digested_zero_cost_and_mechanistically_diverse() -> None:
    plan = load_theory_plan()
    digest = plan["theory_plan_digest"]

    assert canonical_digest(
        {key: value for key, value in plan.items() if key != "theory_plan_digest"}
    ) == digest
    assert plan["authority"]["paid_api_calls"] == 0
    assert tuple(
        candidate["mechanism_family"] for candidate in plan["candidates"]
    ) == (
        "robust_local_regime",
        "joint_response_dynamics",
        "conditional_cross_repository_transfer",
        "outcome_free_covariate_shift",
    )


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


def test_committed_development_result_is_self_digested_and_stops() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/development-results.json"
        ).read_text()
    )
    digest = results.pop("development_results_digest")

    assert canonical_digest(results) == digest
    assert results["nomination"]["status"] == (
        "no_simple_cross_repository_route_warrants_paid_validation"
    )
    wide = results["summaries"]["wide"]
    assert wide["history_match"]["macro_repository_difference"] == pytest.approx(
        -0.006365176694388499
    )
    assert wide["cross_repository_drift_match"][
        "macro_repository_difference"
    ] == pytest.approx(0.0015713312421194367)
    assert results["hindsight_support"]["wide"][
        "macro_repository_difference"
    ] == pytest.approx(-0.15890485923407102)
    assert all(
        fold["local_trend_match"]["chosen_alpha"] == 0.0
        for fold in results["outer_fold_parameters"].values()
    )


def test_committed_semantic_result_is_self_digested_and_retires_alg_007() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/semantic-results.json"
        ).read_text()
    )
    digest = results.pop("semantic_results_digest")

    assert canonical_digest(results) == digest
    assert results["nomination"]["status"] == (
        "retire_fixed_alg_007_on_current_source_family"
    )
    wide = results["summaries"]["wide"]
    assert wide["centroid_recent_15"][
        "macro_repository_difference"
    ] == pytest.approx(0.001473509167553189)
    assert wide["facility_recent_15"][
        "macro_repository_difference"
    ] == pytest.approx(0.03765844825946901)
    assert results["embedding_manifest"] == json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/semantic-embedding-manifest.json"
        ).read_text()
    )


def test_outcome_match_uses_exact_vector_and_stable_tie_break() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/repo",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(4)
    )
    outcomes = {
        "agent-a": {
            "task-0": 0,
            "task-1": 1,
            "task-2": 0,
            "task-3": 1,
        },
        "agent-b": {
            "task-0": 0,
            "task-1": 0,
            "task-2": 1,
            "task-3": 1,
        },
    }

    selected = select_outcome_match(
        history,
        outcomes,
        {"agent-a": 0.5, "agent-b": 0.5},
        budget=2,
    )

    assert selected == ("task-0", "task-3")


def test_fixed_semantic_rules_use_only_local_history_and_stable_ties() -> None:
    history_ids = ("task-a", "task-b", "task-c", "task-d")
    vectors = {
        "task-a": (1.0, 0.0),
        "task-b": (0.0, 1.0),
        "task-c": (1.0, 0.0),
        "task-d": (0.0, 1.0),
    }

    centroid = select_centroid_recent(
        history_ids,
        vectors,
        recent_window=2,
        budget=2,
    )
    facility = select_facility_recent(
        history_ids,
        vectors,
        recent_window=2,
        budget=2,
    )

    assert centroid == ("task-a", "task-b")
    assert facility == ("task-a", "task-b")


def test_complete_trailing_blocks_drop_only_the_leading_remainder() -> None:
    assert complete_trailing_blocks(tuple(range(7)), 2) == (
        (1, 2),
        (3, 4),
        (5, 6),
    )


def test_block_median_forecast_uses_complete_local_regimes() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/target",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(15)
    )
    outcomes = {
        "agent": {
            task.instance_id: int(index in {5, 6, 7, 8, 9, 14})
            for index, task in enumerate(history)
        }
    }

    forecast = forecast_block_median(history, outcomes, block_size=5)

    assert forecast == {"agent": pytest.approx(0.2)}


def test_repository_equal_markov_and_forecast_have_stable_state_semantics() -> None:
    repository_tasks = {
        "org/a": (
            TaskMetadata("a-0", "org/a", "2020-01-01T00:00:00Z", "x", "x"),
            TaskMetadata("a-1", "org/a", "2020-01-02T00:00:00Z", "x", "x"),
        ),
        "org/b": (
            TaskMetadata("b-0", "org/b", "2020-01-01T00:00:00Z", "x", "x"),
            TaskMetadata("b-1", "org/b", "2020-01-02T00:00:00Z", "x", "x"),
        ),
    }
    outcomes = {
        "agent": {
            "a-0": 0,
            "a-1": 0,
            "b-0": 0,
            "b-1": 1,
            "target-0": 0,
            "target-1": 1,
        }
    }
    matrix = fit_repository_equal_markov(
        ("org/a", "org/b"),
        repository_tasks,
        outcomes,
        cell_prior_mass=0.5,
    )
    target_history = (
        TaskMetadata(
            "target-0",
            "org/target",
            "2020-01-01T00:00:00Z",
            "x",
            "x",
        ),
        TaskMetadata(
            "target-1",
            "org/target",
            "2020-01-02T00:00:00Z",
            "x",
            "x",
        ),
    )

    assert matrix[0] == pytest.approx((0.5, 0.5))
    forecast = forecast_joint_markov(
        target_history,
        outcomes,
        ((1.0, 0.0), (0.0, 1.0)),
        horizon=5,
        local_prior_strength=8.0,
        include_local_transitions=False,
    )
    assert forecast == {"agent": pytest.approx(1.0)}


def test_repository_analog_does_not_read_target_future_outcomes() -> None:
    def tasks(prefix: str, repository_id: str, count: int) -> tuple[TaskMetadata, ...]:
        return tuple(
            TaskMetadata(
                f"{prefix}-{index}",
                repository_id,
                (datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=index)).isoformat(),
                "x",
                "x",
            )
            for index in range(count)
        )

    target_history = tasks("target-history", "org/target", 10)
    target_future = tasks("target-future", "org/target", 5)
    target = RepositoryOrigin(
        "org/target",
        "org/target:origin",
        target_history,
        target_future,
    )
    training_origins = {}
    outcomes = {"agent": {}}
    for repository_id in ("org/a", "org/b"):
        history = tasks(f"{repository_id}-history", repository_id, 10)
        future = tasks(f"{repository_id}-future", repository_id, 5)
        training_origins[repository_id] = (
            RepositoryOrigin(
                repository_id,
                f"{repository_id}:origin",
                history,
                future,
            ),
        )
        outcomes["agent"].update(
            {task.instance_id: 0 for task in history}
        )
        outcomes["agent"].update(
            {task.instance_id: 1 for task in future}
        )
    outcomes["agent"].update(
        {task.instance_id: 0 for task in target_history}
    )

    forecast, analogs = forecast_repository_analog(
        target,
        ("org/a", "org/b"),
        training_origins,
        outcomes,
        block_size=5,
    )

    assert forecast == {"agent": pytest.approx(1.0)}
    assert set(analogs) == {"org/a", "org/b"}
    assert not any(
        task.instance_id in outcomes["agent"] for task in target_future
    )


def test_semantic_trend_extrapolates_blocks_before_matching_history() -> None:
    history_ids = tuple(f"task-{index}" for index in range(6))
    vectors = {
        "task-0": (0.0, 0.0),
        "task-1": (0.0, 0.0),
        "task-2": (1.0, 0.0),
        "task-3": (1.0, 0.0),
        "task-4": (2.0, 0.0),
        "task-5": (2.0, 0.0),
    }

    target = forecast_semantic_trend(history_ids, vectors, block_size=2)
    selected = select_embedding_mean_match(
        history_ids,
        vectors,
        target,
        budget=2,
        swap_pass_limit=20,
    )

    assert target == pytest.approx((3.0, 0.0))
    assert selected == ("task-4", "task-5")


def test_local_embedding_artifact_binds_plan_input_and_vectors() -> None:
    plan = {
        "semantic_plan_digest": "plan",
        "embedding": {
            "model_id": "fixture/model",
            "model_revision": "revision",
            "sentence_transformers_version": "5.1.2",
            "device": "cpu",
            "input_field": "problem_statement",
        },
    }

    artifact = build_embedding_artifact(
        ("task-a", "task-b"),
        ("first", "second"),
        ((1.0, 0.0), (0.0, 1.0)),
        plan=plan,
        dataset_sha256="dataset",
        package_version="5.1.2",
    )

    digest = artifact["embedding_artifact_digest"]
    assert canonical_digest(
        {
            key: value
            for key, value in artifact.items()
            if key != "embedding_artifact_digest"
        }
    ) == digest
    assert artifact["input"]["task_count"] == 2
    assert artifact["dimensions"] == 2


def test_repository_drift_weights_repositories_before_origins() -> None:
    tasks = tuple(
        TaskMetadata(
            f"{repository}-{index}",
            repository,
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for repository in ("org/large", "org/small")
        for index in range(15 if repository == "org/large" else 10)
    )
    large_tasks = tuple(task for task in tasks if task.repository_id == "org/large")
    small_tasks = tuple(task for task in tasks if task.repository_id == "org/small")
    origins = {
        "org/large": (
            RepositoryOrigin(
                "org/large",
                "large-1",
                large_tasks[:5],
                large_tasks[5:10],
            ),
            RepositoryOrigin(
                "org/large",
                "large-2",
                large_tasks[:5],
                large_tasks[10:15],
            ),
        ),
        "org/small": (
            RepositoryOrigin(
                "org/small",
                "small-1",
                small_tasks[:5],
                small_tasks[5:10],
            ),
        ),
    }
    outcomes = {
        "agent": {
            **{task.instance_id: 0 for task in large_tasks[:5]},
            **{task.instance_id: 1 for task in large_tasks[5:]},
            **{task.instance_id: 1 for task in small_tasks[:5]},
            **{task.instance_id: 0 for task in small_tasks[5:]},
        }
    }

    drift = estimate_repository_equal_drift(
        ("org/large", "org/small"),
        origins,
        outcomes,
    )

    assert drift == {"agent": pytest.approx(0.0)}


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


def test_development_replay_keeps_outer_repository_as_the_evidence_unit() -> None:
    repository_ids = ("org/a", "org/b", "org/c")
    task_rows = tuple(
        row
        for repository_id in repository_ids
        for row in _task_rows(repository_id, 20)
    )
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
        "repositories": tuple(
            {
                "repository_id": repository_id,
                "repository_cluster_id": repository_id,
            }
            for repository_id in repository_ids
        ),
    }
    portfolio = {
        **portfolio_without_digest,
        "portfolio_digest": canonical_digest(portfolio_without_digest),
    }
    public_plan: dict[str, Any] = {
        "public_panel_plan_digest": "public-plan",
        "rolling_origin": {
            "minimum_initial_history_tasks": 15,
            "future_block_tasks": 5,
            "selection_budget_task_checks": 10,
        },
        "aggregation": {
            "bootstrap_seed": 3,
            "bootstrap_resamples": 20,
        },
        "random_calibration": {"draws": 20, "seed": 4},
    }
    development_plan: dict[str, Any] = {
        "study_id": "fixture",
        "epistemic_status": "opened_outcome_development_only",
        "development_plan_digest": "fixture-plan",
        "source_results": {
            "public_panel_plan_digest": "public-plan",
            "public_panel_results_digest": "public-results",
            "portfolio_digest": portfolio["portfolio_digest"],
        },
        "outer_evaluation": {
            "repository_ids": repository_ids,
            "deep_repository_ids": repository_ids,
        },
        "candidates": (
            {"selector_id": "history_match"},
            {
                "selector_id": "cross_repository_drift_match",
                "shrinkage_grid": (0.0, 1.0),
            },
            {
                "selector_id": "local_trend_match",
                "alpha_grid": (0.0, 1.0),
            },
        ),
    }

    report = run_development_replay(
        tasks,
        outcomes,
        development_plan,
        public_plan,
        portfolio,
    )

    assert report["origin_counts"] == {
        "org/a": 1,
        "org/b": 1,
        "org/c": 1,
    }
    assert report["summaries"]["wide"]["history_match"]["repository_count"] == 3
    assert set(report["outer_fold_parameters"]["org/a"][
        "training_repository_ids"
    ]) == {"org/b", "org/c"}
    assert report["nomination"]["production_promotion_allowed"] is False


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
