from pathlib import Path

import pytest

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    RuntimeConfig,
    SelectorInput,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    load_jsonl_records,
    make_check_id,
    make_result_cache_identity,
    make_result_cache_key,
    make_task_id,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_metric,
    validate_result_cache_identity,
    validate_result_matrix,
    validate_selector_input,
    validate_task,
    write_jsonl_records,
)


def test_make_result_cache_identity_binds_task_check_agent_workspace_runtime_and_scoring() -> None:
    task = _task()
    check = _check(task)
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()

    identity = make_result_cache_identity(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        "scoring:v1",
    )

    assert identity.task_id == task.task_id
    assert identity.check_id == check.check_id
    assert identity.agent_manifest_digest == agent.agent_manifest_digest
    assert identity.workspace_config_digest == canonical_digest(workspace_config)
    assert identity.runtime_config_digest == canonical_digest(runtime_config)
    assert identity.identity_digest == canonical_digest(identity, exclude_self_digest=True)
    assert validate_result_cache_identity(identity).ok
    assert make_result_cache_key(identity) == identity.identity_digest


def test_result_cache_key_rejects_incomplete_identity() -> None:
    identity = ResultCacheIdentity(
        task_id="task",
        check_id="check",
        repository_id="repo",
        base_commit="commit",
        submodule_state_digest="submodules",
        solver_material_digest="solver",
        check_manifest_digest="manifest",
        hidden_check_bundle_digest="hidden",
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        agent_manifest_digest="agent",
        model_snapshot_id="model",
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        adapter_digest="adapter",
        workspace_config_digest="workspace",
        runtime_config_digest="runtime",
        hardware_profile_digest=None,
        scoring_config_digest="",
        identity_digest="bad",
    )

    with pytest.raises(ValueError):
        make_result_cache_key(identity)


def test_make_result_cache_identity_rejects_task_check_mismatch() -> None:
    task = _task()
    other_task = TaskRecord(
        **{
            **task.__dict__,
            "task_id": make_task_id("repo", "other-commit", "source"),
            "base_commit": "other-commit",
            "check_ids": (make_check_id(make_task_id("repo", "other-commit", "source"), "check"),),
        }
    )
    check = _check(other_task)

    with pytest.raises(ValueError, match="check.task_id"):
        make_result_cache_identity(
            task,
            check,
            _agent(),
            _workspace_config(),
            _runtime_config(),
            "scoring:v1",
        )


def test_make_result_cache_identity_rejects_unlisted_check() -> None:
    task = _task()
    check = CheckRecord(**{**_check(task).__dict__, "check_id": make_check_id(task.task_id, "different-check")})

    with pytest.raises(ValueError, match="check.check_id"):
        make_result_cache_identity(
            task,
            check,
            _agent(),
            _workspace_config(),
            _runtime_config(),
            "scoring:v1",
        )


def test_task_validation_rejects_hidden_solver_material_and_unordered_timestamps() -> None:
    task = TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit="commit",
        source_family="issue",
        source_ref="source",
        source_resolved_at="2026-06-02T00:00:00Z",
        task_material_available_at="2026-06-01T00:00:00Z",
        certified_at="2026-06-03T00:00:00Z",
        solver_material_digest="solver",
        solver_material_refs=("hidden/oracle.txt",),
        check_ids=("check",),
        cluster_id="cluster",
    )

    result = validate_task(task)

    assert not result.ok
    assert any("timestamps" in error for error in result.errors)
    assert any("hidden check" in error for error in result.errors)


def test_benchmark_selection_weights_must_match_selected_refs() -> None:
    selected = (TaskCheckRef("task-1", "check-1"),)
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selected_task_check_refs=selected,
            selected_weights={task_check_ref_key(selected[0]): 1.0, task_check_ref_key(TaskCheckRef("other", "check")): 1.0},
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="eligible",
            exposure_state="unexposed",
            exposed_at=None,
            exposure_scope_digest=None,
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    result = validate_benchmark_selection(selection)

    assert not result.ok
    assert "selected_weights must exactly cover selected_task_check_refs" in result.errors


def test_selector_input_validation_rejects_null_pre_origin_fields_without_throwing() -> None:
    ref = TaskCheckRef("task", "check")
    selector_input = SelectorInput(
        selector_input_id="selector-input",
        origin_id="origin",
        task_pool_id="pool",
        feature_snapshot_id="features",
        agent_ids=("agent",),
        eligible_task_check_refs=(ref,),
        pre_origin_result_ids=None,
        pre_origin_result_digests=None,
        budget_digest="budget",
        leakage_policy_digest="leakage",
        selector_input_digest="digest",
        task_pool_digest="pool-digest",
        selection_budget_limit=1,
        feature_records_digest="feature-records",
        feature_snapshot_lint_status="passed",
        origin_as_of_cutoff="2026-01-01T00:00:00Z",
        origin_history_refs_digest=canonical_digest((ref,)),
    )

    result = validate_selector_input(selector_input)

    assert not result.ok
    assert "pre_origin_result_ids is required" in result.errors
    assert "pre_origin_result_digests is required" in result.errors


def test_result_matrix_validates_cell_bindings_and_digest() -> None:
    ref = TaskCheckRef("task", "check")
    matrix = record_with_digest(
        ResultMatrix(
            matrix_id="matrix",
            matrix_role="selected",
            origin_id="origin",
            selection_id="selection",
            agent_ids=("agent",),
            task_check_refs=(ref,),
            cells=(
                ResultCellRef(
                    agent_id="agent",
                    task_id="task",
                    check_id="check",
                    required_identity_digest="identity",
                    result_id="result",
                    result_digest="digest",
                    cell_state="result",
                    exclusion_reason=None,
                ),
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )

    assert validate_result_matrix(matrix).ok


def test_result_matrix_rejects_silent_denominator_omissions_and_duplicates() -> None:
    ref = TaskCheckRef("task", "check")
    partial = record_with_digest(
        ResultMatrix(
            matrix_id="matrix",
            matrix_role="selected",
            origin_id="origin",
            selection_id="selection",
            agent_ids=("agent-1", "agent-2"),
            task_check_refs=(ref,),
            cells=(
                ResultCellRef(
                    agent_id="agent-1",
                    task_id="task",
                    check_id="check",
                    required_identity_digest="identity",
                    result_id="result",
                    result_digest="digest",
                    cell_state="result",
                    exclusion_reason=None,
                ),
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )
    duplicate = record_with_digest(
        ResultMatrix(
            **{
                **partial.__dict__,
                "agent_ids": ("agent-1",),
                "cells": partial.cells + partial.cells,
                "matrix_digest": "",
            }
        )
    )

    partial_result = validate_result_matrix(partial)
    duplicate_result = validate_result_matrix(duplicate)

    assert not partial_result.ok
    assert "matrix cells must exactly cover every Agent/Task/Check denominator cell" in partial_result.errors
    assert not duplicate_result.ok
    assert "duplicate Agent/Task/Check cell" in duplicate_result.errors


def test_evaluation_cell_set_rejects_missing_selected_or_future_refs() -> None:
    from barcarolle.records import EvaluationCellSet, validate_evaluation_cell_set

    selected = TaskCheckRef("selected-task", "selected-check")
    future = TaskCheckRef("future-task", "future-check")
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cells",
            origin_id="origin",
            selection_id="selection",
            selected_task_check_refs=(selected,),
            future_task_check_refs=(future,),
            cells=(
                ResultCellRef(
                    agent_id="agent",
                    task_id="selected-task",
                    check_id="selected-check",
                    required_identity_digest="identity",
                    result_id="result",
                    result_digest="digest",
                    cell_state="result",
                    exclusion_reason=None,
                ),
            ),
            abstention_reason=None,
            cell_set_digest="",
        )
    )

    result = validate_evaluation_cell_set(cell_set)

    assert not result.ok
    assert "evaluation cell set must include at least one cell for each selected and future task/check ref" in result.errors


def test_metric_dimension_rules_are_enforced() -> None:
    metric = record_with_digest(
        MetricRecord(
            metric_id="metric",
            origin_id="origin",
            selection_id="selection",
            evaluation_cell_set_digest="cells",
            selected_matrix_digest="selected",
            future_matrix_digest="future",
            join_policy_digest="join",
            metric_config_digest="config",
            metric_scope="agent",
            agent_id=None,
            agent_pair=None,
            aggregation_level=None,
            budget_digest=None,
            stratum_ref=None,
            metric_name="mae",
            metric_value=0.2,
            denominator_policy_digest="denominator",
            completeness_state="complete",
            abstention_reason=None,
            computed_at="2026-06-01T00:00:00Z",
            metric_digest="",
        )
    )

    result = validate_metric(metric)

    assert not result.ok
    assert "agent metrics must set only agent_id among dimension fields" in result.errors


def test_jsonl_round_trip_preserves_records(tmp_path: Path) -> None:
    task = _task()
    path = tmp_path / "tasks.jsonl"

    write_jsonl_records(path, [task])
    loaded = load_jsonl_records(path, TaskRecord)

    assert loaded == [task]


def test_stable_ids_do_not_depend_on_future_outcomes() -> None:
    task_id = make_task_id("repo", "commit", "source")
    check_id = make_check_id(task_id, "check")

    assert task_id.startswith("task_")
    assert check_id.startswith("check_")
    assert task_id == make_task_id("repo", "commit", "source")


def _task() -> TaskRecord:
    task_id = make_task_id("repo", "commit", "source")
    check_id = make_check_id(task_id, "check")
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="commit",
        source_family="issue",
        source_ref="source",
        source_resolved_at="2026-06-01T00:00:00Z",
        task_material_available_at="2026-06-02T00:00:00Z",
        certified_at="2026-06-03T00:00:00Z",
        solver_material_digest="solver",
        solver_material_refs=("README.md",),
        check_ids=(check_id,),
        cluster_id="cluster",
    )


def _check(task: TaskRecord) -> CheckRecord:
    return CheckRecord(
        check_id=make_check_id(task.task_id, "check"),
        task_id=task.task_id,
        check_type="pytest",
        check_manifest_digest="manifest",
        hidden_check_bundle_digest="hidden-bundle-digest",
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private_tests",
        check_material_available_at="2026-06-02T00:00:00Z",
        certified_at="2026-06-03T00:00:00Z",
    )


def _agent() -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        model_snapshot_id="model",
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig(
        workspace_config_id="workspace-config",
        repository_checkout_config_digest="checkout",
        submodule_state_digest="submodules",
        base_image_digest="base-image",
        dependency_lock_digest="lock",
    )


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id="runtime-config",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        timeout_seconds=60,
        hardware_profile_digest=None,
    )
