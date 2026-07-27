from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import TaskRecord, canonical_digest  # noqa: E402
from examples.offline_selector_study import public_replay  # noqa: E402
from examples.offline_selector_study import study  # noqa: E402


def test_offline_study_amendments_form_a_zero_call_chain() -> None:
    plan = study.load_plan()
    amendment = study.load_amendment(study.DEFAULT_AMENDMENT, plan)
    correction = study.load_correction(
        study.DEFAULT_CORRECTION,
        plan,
        amendment,
    )
    replay_amendment = public_replay.load_replay_amendment(
        public_replay.DEFAULT_AMENDMENT,
        plan,
        correction,
    )

    assert plan["authority"]["new_paid_calls"] == 0
    assert amendment["claim_boundary"]["primary_terminal_state"].startswith(
        "invalid_or_insufficient_evidence"
    )
    assert (
        correction["previous_amendment_digest"]
        == amendment["amendment_digest"]
    )
    assert replay_amendment["previous_amendment_digest"] == (
        correction["amendment_digest"]
    )
    assert replay_amendment["authority"]["new_paid_calls"] == 0
    assert replay_amendment["authority"]["network_calls"] == 0


def test_chronological_blocks_keep_future_tasks_nonoverlapping() -> None:
    tasks = tuple(_task(index, "common") for index in range(7))

    blocks = study.chronological_blocks(
        tasks,
        initial_history_count=3,
        future_block_count=2,
    )

    assert tuple(len(history) for history, _ in blocks) == (3, 5)
    assert tuple(
        tuple(task.task_id for task in future) for _, future in blocks
    ) == (("task-3", "task-4"), ("task-5", "task-6"))


def test_coverage_selection_round_robins_declared_strata() -> None:
    tasks = (
        _task(0, "a"),
        _task(1, "a"),
        _task(2, "b"),
        _task(3, "b"),
        _task(4, "c"),
        _task(5, "c"),
    )

    selection = study.select_tasks(
        study.SelectorSpec("coverage", "coverage", {}),
        tasks,
        5,
    )

    assert selection.task_ids == (
        "task-0",
        "task-2",
        "task-4",
        "task-1",
        "task-3",
    )
    assert set(selection.weights.values()) == {1.0}


def test_stratified_selection_uses_trailing_mix_without_cap_activation() -> None:
    tasks = (
        _task(0, "a"),
        _task(1, "a"),
        _task(2, "a"),
        _task(3, "a"),
        _task(4, "b"),
        _task(5, "b"),
    )
    spec = study.SelectorSpec(
        "stratified",
        "stratified_forecast",
        {
            "alpha": 1.0,
            "trailing_ref_count": 4,
            "seed": 5,
            "weight_cap": 3.0,
        },
    )

    selection = study.select_tasks(spec, tasks, 4)

    assert selection.diagnostics["quota_by_stratum"] == {"a": 2, "b": 2}
    assert selection.diagnostics["capped_selected_fraction"] == 0.0
    assert set(selection.weights.values()) == {1.0}


def test_committed_offline_results_are_self_digested_and_non_core() -> None:
    results = json.loads(study.DEFAULT_RESULTS.read_text(encoding="utf-8"))
    digest = results.pop("study_results_digest")

    assert canonical_digest(results) == digest
    assert results["claim"]["core_rolling_origin"] == (
        "invalid_or_insufficient_evidence"
    )
    assert results["audit"]["per_task_outcomes_persisted"] is False
    assert results["authority"] == {"network_calls": 0, "new_paid_calls": 0}


def test_local_source_reproduces_committed_offline_results() -> None:
    if not study.DEFAULT_TASK_POOL.exists():
        pytest.skip("ignored source artifacts are not present")

    observed = study.run_study()
    committed = json.loads(study.DEFAULT_RESULTS.read_text(encoding="utf-8"))

    assert observed["study_results_digest"] == committed["study_results_digest"]


def test_committed_public_replay_results_are_self_digested() -> None:
    results = json.loads(
        public_replay.DEFAULT_OUTPUT.read_text(encoding="utf-8")
    )
    digest = results.pop("public_replay_results_digest")

    assert canonical_digest(results) == digest
    assert results["status"] == "public_counterfactual_replay_changes_algorithm_results"
    assert results["observed_at_negative_control"][
        "all_history_mature_counts_zero"
    ]
    assert results["observed_at_negative_control"][
        "all_future_mature_counts_zero"
    ]
    assert results["result_reuse_audit"][
        "exact_task_check_agent_cache_identity_match_count"
    ] == 150
    assert results["public_pipeline"]["origin_count"] == 12
    assert results["public_pipeline"]["selection_count"] == 72
    assert results["public_pipeline"]["result_matrix_count"] == 144
    assert results["transparent_diagnostic_comparison"][
        "selection_membership_mismatch_count"
    ] == 1


def test_local_source_reproduces_committed_public_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not study.DEFAULT_TASK_POOL.exists():
        pytest.skip("ignored source artifacts are not present")

    selection_count = 0
    original_select = public_replay.select_with_selector
    original_load_outcomes = public_replay.load_outcomes

    def tracked_select(*args: Any, **kwargs: Any) -> Any:
        nonlocal selection_count
        selection_count += 1
        return original_select(*args, **kwargs)

    def guarded_load_outcomes(*args: Any, **kwargs: Any) -> Any:
        assert selection_count == 72
        return original_load_outcomes(*args, **kwargs)

    monkeypatch.setattr(public_replay, "select_with_selector", tracked_select)
    monkeypatch.setattr(public_replay, "load_outcomes", guarded_load_outcomes)
    observed = public_replay.run_public_replay()
    committed = json.loads(
        public_replay.DEFAULT_OUTPUT.read_text(encoding="utf-8")
    )

    assert selection_count == 72
    assert observed["public_replay_results_digest"] == (
        committed["public_replay_results_digest"]
    )


def _task(index: int, stratum: str) -> TaskRecord:
    timestamp = f"2020-01-{index + 1:02d}T00:00:00Z"
    return TaskRecord(
        task_id=f"task-{index}",
        repository_id="example/repository",
        base_commit=f"base-{index}",
        source_family="fixture",
        source_ref=f"source-{index}",
        source_resolved_at=timestamp,
        task_material_available_at=timestamp,
        task_text=f"Task {index}",
        solver_material_digest=f"solver-{index}",
        solver_material_refs=(),
        check_ids=(f"check-{index}",),
        dependency_cluster_id=f"cluster-{index}",
        sampling_stratum=stratum,
    )
