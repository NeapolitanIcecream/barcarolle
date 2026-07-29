from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
import sys
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.theory import (  # noqa: E402
    select_embedding_mean_match,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
)
from examples.multi_swe_research.response_signal import (  # noqa: E402
    StudyData,
    fit_response_contrast_projection,
    transform_response_projection,
)
from examples.surrogate_gate_audit.study import (  # noqa: E402
    _composition_forecast_only,
    _primary_terminal_state,
    _repository_summary,
    _validate_logical_bindings,
    load_audit_amendment,
    load_audit_plan,
    load_audit_provenance_amendment,
    select_discrete_composition_indices,
    select_mean_matching_indices,
)


def test_surrogate_gate_audit_plan_is_self_bound() -> None:
    plan = load_audit_plan()
    amendment = load_audit_amendment(plan=plan)
    provenance_amendment = load_audit_provenance_amendment(
        plan=plan,
        prior_amendment=amendment,
    )

    assert plan["study_id"] == "proxy-gated-pass-rate-mae-audit-2026-07-29"
    assert plan["resource_boundary"]["paid_api_calls"] == 0
    assert plan["active_amendment_digests"] == (
        amendment["amendment_digest"],
        provenance_amendment["amendment_digest"],
    )
    assert plan["logical_bindings"]["response_signal_amendment_digest"] == (
        "4ad6eab1f0ffe75405debf63e8e07a8ce43230d3249f21f0c65afa6b81ec0d76"
    )
    assert plan["logical_bindings"]["alg_007_task_space_result_digest"] == (
        "d9916f4c9acdcf615262f92cb771ed0079a696b4605805ef0c82b17f4f4e401d"
    )


def test_surrogate_gate_audit_plan_rejects_tampering(tmp_path: Path) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "surrogate_gate_audit"
        / "plan.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["rolling_origin"]["selection_budget_tasks"] = 11
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_audit_plan(path)


def test_surrogate_gate_audit_evidence_is_self_bound() -> None:
    path = (
        REPOSITORY_ROOT
        / "examples"
        / "surrogate_gate_audit"
        / "evidence"
        / "summary.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest = payload.pop("summary_digest")

    assert canonical_digest(payload) == digest
    assert payload["algorithms"]["ALG-013"]["outcome_decision"] == (
        "primary_mae_rejects"
    )
    assert payload["algorithms"]["THY-002S"]["outcome_decision"] == (
        "fails_frozen_outcome_gate"
    )


def test_surrogate_gate_audit_validates_every_logical_binding() -> None:
    plan = load_audit_plan()
    bindings = plan["logical_bindings"]
    keyword_arguments: dict[str, Any] = {
        "selector_plan": {
            "selector_plan_digest": bindings["selector_plan_digest"]
        },
        "response_signal_plan": {
            "response_signal_plan_digest": bindings[
                "response_signal_plan_digest"
            ]
        },
        "response_signal_amendment": {
            "amendment_digest": bindings["response_signal_amendment_digest"]
        },
        "response_composition_plan": {
            "response_composition_plan_digest": bindings[
                "response_composition_plan_digest"
            ]
        },
        "outcome_diagnostics": {
            "panel_digest": bindings["panel_digest"],
            "resolved_outcome_digest": bindings["resolved_outcome_digest"],
        },
        "alg_007": {
            "task_space_results_digest": bindings[
                "alg_007_task_space_result_digest"
            ]
        },
        "thy_plan": {"plan_digest": bindings["thy_002s_plan_digest"]},
        "thy_result": {
            "result_digest": bindings["thy_002s_result_digest"],
            "memberships_digest": bindings["thy_002s_memberships_digest"],
            "random_landscape_raw": {
                "membership_digest": bindings[
                    "thy_002s_random_membership_digest"
                ]
            },
        },
    }

    _validate_logical_bindings(plan, **keyword_arguments)
    keyword_arguments["alg_007"] = {"task_space_results_digest": "wrong"}

    with pytest.raises(ValueError, match="alg_007_task_space_result_digest"):
        _validate_logical_bindings(plan, **keyword_arguments)


def test_terminal_state_uses_frozen_contract_vocabulary() -> None:
    assert _primary_terminal_state(
        {"all_primary_requirements_met": False}
    ) == "primary_mae_rejects"
    assert _primary_terminal_state(
        {"all_primary_requirements_met": True}
    ) == "primary_mae_supports_but_complete_gate_is_under_specified"


def test_mean_matching_reuses_frozen_optimizer_semantics() -> None:
    np = pytest.importorskip("numpy")
    task_ids = tuple(f"task-{index}" for index in range(7))
    rows = np.asarray(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.2, 0.8, 0.4],
            [0.8, 0.2, 0.6],
            [0.5, 0.5, 0.5],
        ],
        dtype=np.float64,
    )
    target = np.asarray([0.55, 0.45, 0.35], dtype=np.float64)

    expected = select_embedding_mean_match(
        task_ids,
        {
            task_id: tuple(float(value) for value in rows[index])
            for index, task_id in enumerate(task_ids)
        },
        tuple(float(value) for value in target),
        budget=4,
        swap_pass_limit=20,
    )
    selected = select_mean_matching_indices(
        rows,
        target,
        budget=4,
        swap_pass_limit=20,
    )

    assert tuple(task_ids[index] for index in selected) == expected


def test_full_projection_then_drop_is_equal_to_explicit_held_out_fit() -> None:
    np = pytest.importorskip("numpy")
    tasks = tuple(
        TaskMetadata(
            instance_id=f"{repository}:{index}",
            repository_id=repository,
            created_at=f"2026-01-0{index + 1}T00:00:00Z",
            difficulty="python",
            problem_statement="Task",
        )
        for repository in ("train-a", "train-b")
        for index in range(4)
    ) + tuple(
        TaskMetadata(
            instance_id=f"target:{index}",
            repository_id="target",
            created_at=f"2026-01-0{index + 1}T00:00:00Z",
            difficulty="python",
            problem_statement="Task",
        )
        for index in range(2)
    )
    embeddings = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
            [1.0, 2.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.3, 0.4, 0.5],
            [0.8, 0.7, 0.6],
        ]
    )
    outcomes = np.asarray(
        [
            [0, 0, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 0],
            [0, 1, 0],
            [1, 0, 1],
        ],
        dtype=np.float64,
    )
    task_ids = tuple(task.instance_id for task in tasks)
    data = StudyData(
        tasks=tasks,
        task_ids=task_ids,
        embeddings=embeddings,
        outcomes=outcomes,
        configuration_ids=("config-0", "config-1", "config-2"),
        task_index={task_id: index for index, task_id in enumerate(task_ids)},
        repository_indices={
            "train-a": (0, 1, 2, 3),
            "train-b": (4, 5, 6, 7),
            "target": (8, 9),
        },
        repository_times={
            "train-a": tuple(tasks[index].created_at for index in range(4)),
            "train-b": tuple(tasks[index].created_at for index in range(4, 8)),
            "target": tuple(tasks[index].created_at for index in range(8, 10)),
        },
    )

    full = fit_response_contrast_projection(
        data,
        target_repository_id="target",
        cutoff="2026-01-05T00:00:00Z",
        tolerance=1e-12,
    )
    explicit = fit_response_contrast_projection(
        data,
        target_repository_id="target",
        cutoff="2026-01-05T00:00:00Z",
        tolerance=1e-12,
        retained_configuration_indices=(0, 2),
    )
    keep = tuple(
        index
        for index, configuration in enumerate(full.configuration_indices)
        if configuration in (0, 2)
    )

    assert explicit.configuration_indices == (0, 2)
    assert full.directions[list(keep)] == pytest.approx(explicit.directions)
    assert full.centers[list(keep)] == pytest.approx(explicit.centers)
    assert full.scales[list(keep)] == pytest.approx(explicit.scales)
    assert transform_response_projection(
        embeddings[8:],
        full,
    )[:, list(keep)] == pytest.approx(
        transform_response_projection(embeddings[8:], explicit)
    )


def test_discrete_composition_uses_lexicographic_counts_then_newest() -> None:
    solved_counts = (1, 1, 1, 0, 2)
    created_order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(solved_counts))
    )

    selected = select_discrete_composition_indices(
        solved_counts,
        0.5,
        budget=2,
        maximum_count=2,
        created_order=created_order,
    )

    # Sum two is reachable as (c0,c1,c2)=(0,2,0) or (1,0,1).
    # The first vector is lexicographically smaller, then newest wins in cell 1.
    assert selected == (1, 2)


def test_discrete_composition_matches_brute_force() -> None:
    solved_counts = (0, 0, 1, 1, 2, 3, 3)
    created_order = tuple(
        (f"2026-01-0{index + 1}T00:00:00Z", f"task-{index}")
        for index in range(len(solved_counts))
    )
    forecast = 0.61
    budget = 3
    maximum_count = 3

    selected = select_discrete_composition_indices(
        solved_counts,
        forecast,
        budget=budget,
        maximum_count=maximum_count,
        created_order=created_order,
    )
    possible = []
    for indices in combinations(range(len(solved_counts)), budget):
        count_vector = tuple(
            sum(solved_counts[index] == value for index in indices)
            for value in range(maximum_count + 1)
        )
        objective = abs(
            sum(solved_counts[index] for index in indices)
            / (maximum_count * budget)
            - forecast
        )
        possible.append((objective, count_vector, indices))
    best_objective = min(item[0] for item in possible)
    best_vector = min(
        item[1] for item in possible if item[0] == best_objective
    )

    assert abs(
        sum(solved_counts[index] for index in selected)
        / (maximum_count * budget)
        - forecast
    ) == pytest.approx(best_objective)
    assert tuple(
        sum(solved_counts[index] == value for index in selected)
        for value in range(maximum_count + 1)
    ) == best_vector


def test_composition_forecast_materializer_has_no_future_input() -> None:
    np = pytest.importorskip("numpy")
    history = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 0.0],
            [1.0, 1.0],
            [1.0, 1.0],
        ]
    )

    forecast, local, full, recent = _composition_forecast_only(
        history,
        horizon=2,
        earlier_full_loss_sum=np.asarray([1.0, 0.0]),
        earlier_recent_loss_sum=np.asarray([0.0, 1.0]),
        earlier_origin_count=1,
        global_prior=np.asarray([0.0, 0.0]),
    )

    assert full == pytest.approx([0.5, 0.5])
    assert recent == pytest.approx([1.0, 1.0])
    assert local == pytest.approx([1.0, 0.5])
    assert forecast == pytest.approx([2.0 / 3.0, 0.4])


def test_repository_summary_is_repository_first() -> None:
    rows = tuple(
        {
            "repository_id": "long",
            "origin_id": f"long:{index}",
            "candidate_loss": 0.6,
            "full_loss": 0.5,
            "difference": 0.1,
        }
        for index in range(9)
    ) + (
        {
            "repository_id": "short",
            "origin_id": "short:1",
            "candidate_loss": 0.0,
            "full_loss": 0.5,
            "difference": -0.5,
        },
    )

    summary = _repository_summary(rows, ("long", "short"))

    assert summary["difference"] == pytest.approx(-0.2)
    assert summary["difference"] != pytest.approx(0.04)
