from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import random
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.adaptive_difficulty import (  # noqa: E402
    choose_prequential_difficulty_model,
    completed_training_origin_supply,
    forecast_stationary_difficulty,
    load_adaptive_difficulty_plan,
    materialize_adaptive_selections,
)
from examples.multi_repository_study.agent_invariant import (  # noqa: E402
    fit_cutoff_repository_equal_markov,
    forecast_difficulty_markov,
    load_agent_invariant_execution_amendment,
    load_agent_invariant_plan,
    materialize_selections,
    select_state_histogram_match,
    task_difficulty_state,
)
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
from examples.multi_repository_study.panel_extension import (  # noqa: E402
    legacy_official_binary_outcomes,
    load_agent_panel_schema_amendment,
    retrospective_availability_audit,
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
from examples.multi_repository_study.scale_sensitivity import (  # noqa: E402
    build_common_scale_origins,
    load_scale_sensitivity_plan,
    materialize_scale_selections,
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
from examples.multi_repository_study.theory_audit import (  # noqa: E402
    audit_decision,
    load_audit_plan,
    permute_joint_outcomes,
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


def test_theory_audit_plan_is_self_digested_and_cannot_change_candidate() -> None:
    plan = load_audit_plan()
    digest = plan["audit_plan_digest"]

    assert canonical_digest(
        {key: value for key, value in plan.items() if key != "audit_plan_digest"}
    ) == digest
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["audit_contract"]["candidate_changes_allowed"] is False
    assert plan["temporal_null"]["permutations"] == 500


def test_agent_panel_extension_is_self_digested_and_preserves_holdout() -> None:
    plan = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/agent-panel-extension-plan.json"
        ).read_text()
    )
    digest = plan.pop("agent_panel_extension_plan_digest")

    assert canonical_digest(plan) == digest
    assert len(plan["existing_opened_development_panel"]) == 3
    assert len(plan["preallocation_exclusions"]) == 1
    assert len(plan["development_allocation"]) == 8
    assert len(plan["holdout_allocation"]) == 6
    assert {
        item["result_blob_sha"] for item in plan["development_allocation"]
    }.isdisjoint(
        item["result_blob_sha"] for item in plan["holdout_allocation"]
    )
    assert plan["authority"]["paid_api_calls"] == 0
    assert "until the frozen holdout gate is met" in plan["authority"][
        "forbidden_network_reads"
    ]


def test_agent_invariant_plan_is_self_digested_and_cutoff_aware() -> None:
    plan = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/agent-invariant-plan.json"
        ).read_text()
    )
    digest = plan.pop("agent_invariant_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["difficulty_representation"]["state_count"] == 5
    assert plan["rolling_origin"]["cross_repository_cutoff"] == (
        "created_at no later than the final target-history Task"
    )
    markov = plan["fixed_algorithms"][1]
    assert markov["selector_id"] == "difficulty_markov_match"
    assert markov["training_symmetric_dirichlet_cell_mass"] == pytest.approx(
        0.2
    )
    assert plan["diagnostics"]["temporal_null"]["permutations"] == 500
    assert plan["holdout_open_gate"]["production_promotion_allowed"] is False
    assert plan["authority"]["paid_api_calls"] == 0


def test_agent_invariant_execution_amendment_preserves_candidate_and_holdout() -> None:
    amendment = load_agent_invariant_execution_amendment()
    digest = amendment["agent_invariant_execution_amendment_digest"]

    assert canonical_digest(
        {
            key: value
            for key, value in amendment.items()
            if key != "agent_invariant_execution_amendment_digest"
        }
    ) == digest
    assert amendment["resolution"]["candidate_changes"] == "none"
    assert amendment["resolution"]["gate_changes"] == "none"
    assert amendment["authority"]["holdout_result_blob_reads"] == 0
    assert (
        amendment["authority"]["candidate_result_metrics_observed_before_amendment"]
        == 0
    )


def test_adaptive_difficulty_plan_is_self_digested_and_stops_search() -> None:
    plan = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/adaptive-difficulty-plan.json"
        ).read_text()
    )
    digest = plan.pop("adaptive_difficulty_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["fixed_algorithms"][1]["selector_id"] == (
        "adaptive_prequential_difficulty_match"
    )
    assert plan["diagnostics"]["temporal_null"]["permutations"] == 500
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["holdout_result_blob_reads"] == 0
    assert plan["current_pool_stop_rule"].startswith(
        "If the adaptive candidate fails"
    )


def test_scale_sensitivity_plan_freezes_common_cohort_and_sealed_holdout() -> None:
    plan = load_scale_sensitivity_plan()
    digest = plan["scale_sensitivity_plan_digest"]

    assert canonical_digest(
        {
            key: value
            for key, value in plan.items()
            if key != "scale_sensitivity_plan_digest"
        }
    ) == digest
    assert tuple(plan["response_surface"]["selection_budgets"]) == (5, 10, 15)
    assert tuple(plan["response_surface"]["task_count_horizons"]) == (3, 5, 10)
    assert plan["common_origin_cohort"]["expected_origin_count"] == 56
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["holdout_result_blob_reads"] == 0


def test_scale_sensitivity_result_is_self_digested_and_closes_scale_search() -> None:
    result_path = (
        REPOSITORY_ROOT
        / "examples/multi_repository_study/scale-sensitivity-results.json"
    )
    result = json.loads(result_path.read_text())
    digest = result.pop("scale_sensitivity_results_digest")

    assert canonical_digest(result) == digest
    assert len(result["cells"]) == 9
    assert result["common_origin_cohort"]["origin_count"] == 56
    assert result["source"]["development_agent_count"] == 11
    assert result["source"]["holdout_result_blob_reads"] == 0
    assert result["decision"]["status"] == (
        "scale_sensitivity_does_not_reopen_candidate"
    )
    assert result["decision"]["passing_cells"] == []
    assert result["decision"]["holdout_open_allowed"] is False
    assert result["time_semantics"]["executed_mode"] == (
        "source_time_cutoff_safe_counterfactual"
    )
    assert '"values"' not in result_path.read_text()


def test_common_scale_origins_keep_histories_and_nest_future_prefixes() -> None:
    repository_ids = ("org/a", "org/b")
    tasks = tuple(
        TaskMetadata(
            row["instance_id"],
            row["repo"],
            row["created_at"],
            row["difficulty"],
            "fixture",
        )
        for repository_id in repository_ids
        for row in _task_rows(repository_id, 35)
    )

    short = build_common_scale_origins(
        tasks,
        repository_ids,
        minimum_history_tasks=20,
        origin_step_tasks=5,
        maximum_task_count_horizon=10,
        task_count_horizon=3,
    )
    long = build_common_scale_origins(
        tasks,
        repository_ids,
        minimum_history_tasks=20,
        origin_step_tasks=5,
        maximum_task_count_horizon=10,
        task_count_horizon=10,
    )

    assert {
        repository_id: len(short[repository_id])
        for repository_id in repository_ids
    } == {"org/a": 2, "org/b": 2}
    for repository_id in repository_ids:
        for short_origin, long_origin in zip(
            short[repository_id],
            long[repository_id],
            strict=True,
        ):
            assert short_origin.origin_id == long_origin.origin_id
            assert short_origin.history == long_origin.history
            assert short_origin.future == long_origin.future[:3]
            assert len(short_origin.history) > 15


def test_scale_cell_materialization_is_local_and_budgeted() -> None:
    repository_ids = ("org/a", "org/b", "org/c")
    tasks = tuple(
        TaskMetadata(
            row["instance_id"],
            row["repo"],
            row["created_at"],
            row["difficulty"],
            "fixture",
        )
        for repository_id in repository_ids
        for row in _task_rows(repository_id, 35)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: int((index + agent) % 5 < 2)
            for index, task in enumerate(tasks)
        }
        for agent in range(5)
    }
    evaluation_ids = ("org/a", "org/b")
    origins = build_common_scale_origins(
        tasks,
        evaluation_ids,
        minimum_history_tasks=20,
        origin_step_tasks=5,
        maximum_task_count_horizon=10,
        task_count_horizon=5,
    )

    memberships, diagnostics = materialize_scale_selections(
        tasks,
        outcomes,
        origins,
        evaluation_ids,
        repository_ids,
        selection_budget=10,
        task_count_horizon=5,
        state_count=5,
        cell_prior_mass=0.2,
        local_prior_strength=5.0,
    )

    task_repository = {task.instance_id: task.repository_id for task in tasks}
    assert set(memberships) == {
        "recency",
        "stationary_difficulty_match",
        "difficulty_markov_match",
    }
    for rows in memberships.values():
        for origin_id, selected in rows.items():
            repository_id = origin_id.split(":scale-origin-", maxsplit=1)[0]
            assert len(selected) == 10
            assert {task_repository[task_id] for task_id in selected} == {
                repository_id
            }
    assert diagnostics["origin_count"] == 4


def test_agent_panel_schema_amendment_is_narrow_and_self_digested() -> None:
    amendment = load_agent_panel_schema_amendment()
    digest = amendment["agent_panel_schema_amendment_digest"]

    assert canonical_digest(
        {
            key: value
            for key, value in amendment.items()
            if key != "agent_panel_schema_amendment_digest"
        }
    ) == digest
    assert len(amendment["affected_result_blobs"]) == 3
    assert amendment["authority"]["new_result_blob_reads"] == 0
    assert amendment["authority"]["holdout_result_blob_reads"] == 0


def test_legacy_official_result_keeps_resolved_only_binary_endpoint() -> None:
    amendment = load_agent_panel_schema_amendment()
    fields = tuple(amendment["legacy_schema_fields"])
    payload = {field: [] for field in fields}
    payload["generated"] = ["task-1"]
    payload["with_logs"] = ["task-1"]
    payload["applied"] = ["task-1"]
    payload["resolved"] = ["task-1"]
    payload["no_generation"] = ["task-2"]

    outcomes, diagnostics = legacy_official_binary_outcomes(
        ("task-1", "task-2", "task-3"),
        payload,
        legacy_fields=fields,
    )

    assert outcomes == {"task-1": 1, "task-2": 0, "task-3": 0}
    assert diagnostics["resolved_count"] == 1
    assert diagnostics["ordinary_unlisted_count"] == 1


def test_legacy_official_result_rejects_schema_drift() -> None:
    amendment = load_agent_panel_schema_amendment()
    fields = tuple(amendment["legacy_schema_fields"])
    payload = {field: [] for field in fields}
    payload["unexpected"] = []

    with pytest.raises(ValueError, match="fields"):
        legacy_official_binary_outcomes(
            ("task-1",),
            payload,
            legacy_fields=fields,
        )


def test_agent_invariant_difficulty_states_follow_solve_fraction() -> None:
    outcomes = {
        f"agent-{agent}": {
            f"task-{solved}": int(agent < solved)
            for solved in range(5)
        }
        for agent in range(4)
    }

    assert tuple(
        task_difficulty_state(
            f"task-{solved}",
            outcomes,
            state_count=5,
        )
        for solved in range(5)
    ) == (0, 1, 2, 3, 4)


def test_cutoff_markov_excludes_later_cross_repository_tasks() -> None:
    tasks_by_repository = {
        "org/a": tuple(
            TaskMetadata(
                f"a-{day}",
                "org/a",
                f"2020-01-0{day}T00:00:00Z",
                "fixture",
                "fixture",
            )
            for day in range(1, 4)
        ),
        "org/b": tuple(
            TaskMetadata(
                f"b-{day}",
                "org/b",
                f"2020-01-0{day}T00:00:00Z",
                "fixture",
                "fixture",
            )
            for day in range(3, 5)
        ),
    }
    outcomes = {
        "agent": {
            task.instance_id: int(index % 2 == 0)
            for index, task in enumerate(
                (*tasks_by_repository["org/a"], *tasks_by_repository["org/b"])
            )
        }
    }

    transition, diagnostic = fit_cutoff_repository_equal_markov(
        ("org/a", "org/b"),
        tasks_by_repository,
        outcomes,
        cutoff="2020-01-02T00:00:00Z",
        state_count=5,
        cell_prior_mass=0.2,
    )

    assert diagnostic["included_repository_ids"] == ("org/a",)
    assert diagnostic["included_task_count"] == 2
    assert diagnostic["excluded_later_task_count"] == 3
    assert all(sum(row) == pytest.approx(1.0) for row in transition)


def test_state_histogram_match_uses_recent_tasks_inside_each_state() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/repo",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(10)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: int(index >= 6)
            for index, task in enumerate(history)
        }
        for agent in range(5)
    }

    selected = select_state_histogram_match(
        history,
        outcomes,
        (0.5, 0.0, 0.0, 0.0, 0.5),
        state_count=5,
        budget=4,
    )

    assert selected == ("task-4", "task-5", "task-8", "task-9")


def test_difficulty_markov_forecast_is_a_probability_distribution() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/repo",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(6)
    )
    outcomes = {
        "agent-a": {
            task.instance_id: int(index % 2 == 0)
            for index, task in enumerate(history)
        },
        "agent-b": {
            task.instance_id: int(index % 3 == 0)
            for index, task in enumerate(history)
        },
    }
    uniform = tuple(tuple(0.2 for _ in range(5)) for _ in range(5))

    forecast = forecast_difficulty_markov(
        history,
        outcomes,
        uniform,
        state_count=5,
        horizon=5,
        local_prior_strength=5.0,
    )

    assert sum(forecast) == pytest.approx(1.0)
    assert all(0.0 <= value <= 1.0 for value in forecast)


def test_stationary_difficulty_forecast_is_smoothed() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/repo",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(5)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: int(index >= 3)
            for index, task in enumerate(history)
        }
        for agent in range(5)
    }

    forecast = forecast_stationary_difficulty(
        history,
        outcomes,
        state_count=5,
        cell_prior_mass=0.2,
    )

    assert forecast == pytest.approx(
        (3.2 / 6.0, 0.2 / 6.0, 0.2 / 6.0, 0.2 / 6.0, 2.2 / 6.0)
    )
    assert sum(forecast) == pytest.approx(1.0)


def test_prequential_choice_detects_predictable_state_transitions() -> None:
    history = tuple(
        TaskMetadata(
            f"task-{index}",
            "org/repo",
            f"2020-01-{index + 1:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(10)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: index % 2
            for index, task in enumerate(history)
        }
        for agent in range(5)
    }
    transition = (
        (0.01, 0.01, 0.01, 0.01, 0.96),
        (0.2, 0.2, 0.2, 0.2, 0.2),
        (0.2, 0.2, 0.2, 0.2, 0.2),
        (0.2, 0.2, 0.2, 0.2, 0.2),
        (0.96, 0.01, 0.01, 0.01, 0.01),
    )

    choice = choose_prequential_difficulty_model(
        history,
        outcomes,
        transition,
        state_count=5,
        cell_prior_mass=0.2,
        local_prior_strength=5.0,
    )

    assert choice["selected_model"] == "markov"
    assert float(choice["markov_mean_negative_log_likelihood"]) < float(
        choice["stationary_mean_negative_log_likelihood"]
    )


def test_agent_invariant_materialization_keeps_selections_repository_local() -> None:
    repository_ids = ("org/a", "org/b", "org/c")
    tasks = tuple(
        TaskMetadata(
            row["instance_id"],
            row["repo"],
            row["created_at"],
            row["difficulty"],
            "fixture",
        )
        for repository_id in repository_ids
        for row in _task_rows(repository_id, 20)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: int((index + agent) % 4 < 2)
            for index, task in enumerate(tasks)
        }
        for agent in range(5)
    }
    history_match_outcomes = {
        agent_id: agent_outcomes
        for agent_id, agent_outcomes in outcomes.items()
        if agent_id in {"agent-0", "agent-1"}
    }

    origins, memberships, forecasts, diagnostics = materialize_selections(
        tasks,
        outcomes,
        load_agent_invariant_plan(),
        {"portfolio": {"wide_repository_ids": repository_ids}},
        history_match_outcomes=history_match_outcomes,
    )

    assert {key: len(value) for key, value in origins.items()} == {
        "org/a": 1,
        "org/b": 1,
        "org/c": 1,
    }
    task_repository = {task.instance_id: task.repository_id for task in tasks}
    for selector_memberships in memberships.values():
        for origin_id, selected in selector_memberships.items():
            repository_id = origin_id.split(":origin-", maxsplit=1)[0]
            assert len(selected) == 10
            assert {task_repository[task_id] for task_id in selected} == {
                repository_id
            }
    assert set(forecasts) == {
        "difficulty_persistence_match",
        "difficulty_markov_match",
    }
    assert diagnostics["symmetric_fallback_origin_count"] == 0


def test_adaptive_materialization_uses_only_local_history_tasks() -> None:
    repository_ids = ("org/a", "org/b", "org/c")
    tasks = tuple(
        TaskMetadata(
            row["instance_id"],
            row["repo"],
            row["created_at"],
            row["difficulty"],
            "fixture",
        )
        for repository_id in repository_ids
        for row in _task_rows(repository_id, 20)
    )
    outcomes = {
        f"agent-{agent}": {
            task.instance_id: int((index + agent) % 5 < 2)
            for index, task in enumerate(tasks)
        }
        for agent in range(5)
    }
    history_outcomes = {
        agent_id: values
        for agent_id, values in outcomes.items()
        if agent_id in {"agent-0", "agent-1"}
    }

    origins, memberships, choices = materialize_adaptive_selections(
        tasks,
        outcomes,
        history_outcomes,
        load_adaptive_difficulty_plan(),
        load_agent_invariant_plan(),
        {"portfolio": {"wide_repository_ids": repository_ids}},
        include_controls=True,
    )

    assert set(memberships) == {
        "history_match",
        "difficulty_markov_match",
        "stationary_difficulty_match",
        "adaptive_prequential_difficulty_match",
    }
    task_repository = {task.instance_id: task.repository_id for task in tasks}
    for selector_memberships in memberships.values():
        for origin_id, selected in selector_memberships.items():
            repository_id = origin_id.split(":origin-", maxsplit=1)[0]
            assert len(selected) == 10
            assert {task_repository[task_id] for task_id in selected} == {
                repository_id
            }
    assert len(choices) == sum(len(rows) for rows in origins.values())
    assert {
        choice["selected_model"] for choice in choices.values()
    } <= {"markov", "stationary"}


def test_completed_training_origin_supply_uses_final_future_task_cutoff() -> None:
    def task(instance_id: str, repository_id: str, day: int) -> TaskMetadata:
        return TaskMetadata(
            instance_id,
            repository_id,
            f"2020-01-{day:02d}T00:00:00Z",
            "fixture",
            "fixture",
        )

    origins = {
        "org/a": (
            RepositoryOrigin(
                "org/a",
                "org/a:origin-001",
                (task("a-history", "org/a", 10),),
                (task("a-future", "org/a", 11),),
            ),
        ),
        "org/b": (
            RepositoryOrigin(
                "org/b",
                "org/b:origin-001",
                (task("b-history", "org/b", 5),),
                (task("b-future", "org/b", 6),),
            ),
        ),
        "org/c": (
            RepositoryOrigin(
                "org/c",
                "org/c:origin-001",
                (task("c-history", "org/c", 15),),
                (task("c-future", "org/c", 16),),
            ),
        ),
    }

    supply = completed_training_origin_supply(
        origins,
        ("org/a", "org/b", "org/c"),
    )

    assert supply["completed_training_origin_count"] == {
        "minimum": 0,
        "median": 1,
        "maximum": 2,
    }
    assert supply["contributing_training_repository_count"] == {
        "minimum": 0,
        "median": 1,
        "maximum": 2,
    }
    assert supply["target_origins_with_zero_completed_training_origins"] == 1
    assert (
        supply["target_origins_with_fewer_than_three_training_repositories"]
        == 3
    )


def test_retrospective_availability_audit_flags_later_training_tasks() -> None:
    target_history = tuple(
        TaskMetadata(
            f"target-{index}",
            "org/target",
            f"2020-01-0{index + 1}T00:00:00Z",
            "fixture",
            "fixture",
        )
        for index in range(2)
    )
    origin = RepositoryOrigin(
        "org/target",
        "org/target:origin-001",
        target_history,
        (
            TaskMetadata(
                "target-future",
                "org/target",
                "2020-01-03T00:00:00Z",
                "fixture",
                "fixture",
            ),
        ),
    )
    training_tasks = (
        TaskMetadata(
            "train-past",
            "org/train",
            "2020-01-01T00:00:00Z",
            "fixture",
            "fixture",
        ),
        TaskMetadata(
            "train-later",
            "org/train",
            "2020-01-04T00:00:00Z",
            "fixture",
            "fixture",
        ),
    )

    audit = retrospective_availability_audit(
        (*target_history, *origin.future, *training_tasks),
        {"org/target": (origin,), "org/train": ()},
        ("org/target", "org/train"),
    )

    assert audit["training_task_uses"] == 2
    assert audit["later_created_training_task_uses"] == 1
    assert audit["origins_with_later_created_training_tasks"] == 1


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


def test_committed_theory_result_is_self_digested_and_nominates_markov() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/theory-results.json"
        ).read_text()
    )
    digest = results.pop("theory_results_digest")

    assert canonical_digest(results) == digest
    assert results["nomination"]["status"] == (
        "freeze_one_theory_candidate_for_independent_validation"
    )
    assert results["nomination"]["nominated_selector_id"] == (
        "joint_markov_match"
    )
    wide = results["summaries"]["wide"]["joint_markov_match"]
    assert wide["macro_repository_difference"] == pytest.approx(
        -0.019107886181284034
    )
    assert wide["favorable_repository_count"] == 5
    assert results["summaries"]["deep"]["joint_markov_match"][
        "macro_repository_difference"
    ] == pytest.approx(-0.008957015236726942)


def test_committed_theory_audit_result_is_self_digested_and_retires_markov() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/theory-audit-results.json"
        ).read_text()
    )
    digest = results.pop("audit_results_digest")

    assert canonical_digest(results) == digest
    assert results["decision"]["status"] == (
        "retire_candidate_after_adversarial_audit"
    )
    assert results["temporal_null"]["as_good_or_better_rate"] == pytest.approx(
        0.1
    )
    assert results["leave_one_agent_out"][
        "wide_macro_over_held_out_agents"
    ] == pytest.approx(-0.0004312527372087183)
    assert results["leave_one_agent_out"][
        "wide_favorable_held_out_agent_count"
    ] == 1


def test_committed_agent_panel_replication_is_self_digested_and_neutral() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / (
                "examples/multi_repository_study/"
                "agent-panel-replication-results.json"
            )
        ).read_text()
    )
    digest = results.pop("agent_panel_replication_results_digest")

    assert canonical_digest(results) == digest
    assert results["original_agent_count"] == 3
    assert results["replication_agent_count"] == 8
    assert results["summaries"]["wide"][
        "macro_repository_difference"
    ] == pytest.approx(0.0003089043428531318)
    assert results["summaries"]["deep"][
        "macro_repository_difference"
    ] == pytest.approx(0.006264004464502509)
    assert results["retrospective_fit_availability"][
        "later_created_rate"
    ] == pytest.approx(0.47370527895921943)
    assert results["retrospective_fit_availability"][
        "origins_with_later_created_training_tasks"
    ] == 68
    assert results["decision"]["reactivation_allowed"] is False


def test_committed_agent_invariant_result_is_self_digested_and_stops() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/agent-invariant-results.json"
        ).read_text()
    )
    digest = results.pop("agent_invariant_results_digest")

    assert canonical_digest(results) == digest
    markov = results["summaries"]["wide"]["difficulty_markov_match"]
    assert markov["macro_repository_difference"] == pytest.approx(
        -0.008875640661665908
    )
    assert markov["favorable_repository_count"] == 3
    assert results["summaries"]["deep"]["difficulty_markov_match"][
        "macro_repository_difference"
    ] == pytest.approx(0.009199967848780785)
    assert results["random_calibration"]["wide"]["candidate_positions"][
        "difficulty_markov_match"
    ]["candidate_better_than_random_midrank"] == pytest.approx(0.9778)
    assert results["temporal_null"]["as_good_or_better_rate"] == pytest.approx(
        0.066
    )
    assert results["leave_one_agent_out"]["aggregate_by_selector"][
        "difficulty_markov_match"
    ]["wide_favorable_held_out_agent_count"] == 6
    assert results["selection_membership_digests"]["history_match"] == (
        "79e96af6f5d254f45dcce55654336e59fa0e46ff882e4d1ae3f177a799b781c3"
    )
    assert results["decision"]["status"] == (
        "retire_agent_invariant_markov_on_development_panel"
    )
    assert results["decision"]["sealed_holdout_open_allowed"] is False


def test_committed_adaptive_result_is_self_digested_and_closes_pool_search() -> None:
    results = json.loads(
        (
            REPOSITORY_ROOT
            / "examples/multi_repository_study/adaptive-difficulty-results.json"
        ).read_text()
    )
    digest = results.pop("adaptive_difficulty_results_digest")

    assert canonical_digest(results) == digest
    adaptive = results["summaries"]["wide"][
        "adaptive_prequential_difficulty_match"
    ]
    assert adaptive["macro_repository_difference"] == pytest.approx(
        -0.0023519318123756657
    )
    assert adaptive["favorable_repository_count"] == 3
    assert results["summaries"]["deep"][
        "adaptive_prequential_difficulty_match"
    ]["macro_repository_difference"] == pytest.approx(0.009270440012276204)
    assert results["model_choice_diagnostics"]["overall"] == {
        "markov": 49,
        "stationary": 19,
    }
    assert results["calendar_training_origin_supply"][
        "completed_training_origin_count"
    ] == {
        "minimum": 0,
        "median": 11,
        "maximum": 61,
    }
    assert results["calendar_training_origin_supply"][
        "contributing_training_repository_count"
    ] == {
        "minimum": 0,
        "median": 2,
        "maximum": 5,
    }
    assert results["temporal_null"]["as_good_or_better_rate"] == pytest.approx(
        0.194
    )
    assert results["decision"]["status"] == (
        "retire_adaptive_candidate_and_close_current_pool_algorithm_search"
    )
    assert results["decision"]["sealed_holdout_open_allowed"] is False


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


def test_joint_permutation_preserves_repository_joint_outcome_multisets() -> None:
    tasks = {
        "org/a": tuple(
            TaskMetadata(
                f"task-{index}",
                "org/a",
                f"2020-01-{index + 1:02d}T00:00:00Z",
                "x",
                "x",
            )
            for index in range(4)
        )
    }
    outcomes = {
        "agent-a": {
            "task-0": 0,
            "task-1": 0,
            "task-2": 1,
            "task-3": 1,
        },
        "agent-b": {
            "task-0": 0,
            "task-1": 1,
            "task-2": 0,
            "task-3": 1,
        },
    }

    permuted = permute_joint_outcomes(
        tasks,
        outcomes,
        random.Random(7),
    )

    original_vectors = sorted(
        (outcomes["agent-a"][f"task-{index}"], outcomes["agent-b"][f"task-{index}"])
        for index in range(4)
    )
    permuted_vectors = sorted(
        (
            permuted["agent-a"][f"task-{index}"],
            permuted["agent-b"][f"task-{index}"],
        )
        for index in range(4)
    )
    assert permuted_vectors == original_vectors


@pytest.mark.parametrize(
    ("null_rate", "held_out_macro", "favorable_count", "expected"),
    [
        (0.05, -0.01, 2, "retain_candidate_for_independent_agent_validation"),
        (0.05, 0.01, 2, "retain_only_as_panel_conditional_candidate"),
        (0.10, -0.01, 3, "retire_candidate_after_adversarial_audit"),
    ],
)
def test_theory_audit_decision_obeys_frozen_priority_rule(
    null_rate: float,
    held_out_macro: float,
    favorable_count: int,
    expected: str,
) -> None:
    assert audit_decision(null_rate, held_out_macro, favorable_count) == expected


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
