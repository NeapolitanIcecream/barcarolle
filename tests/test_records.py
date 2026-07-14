from dataclasses import replace
from pathlib import Path

import pytest

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    FeatureRecord,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RuntimeConfig,
    SelectorRecord,
    SelectorInput,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_check_digest,
    make_check_id,
    make_result_cache_identity,
    make_result_cache_key,
    make_task_id,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_check,
    validate_feature_snapshot,
    validate_metric,
    validate_result,
    validate_result_cache_identity,
    validate_result_matrix,
    validate_selector,
    validate_selector_input,
    validate_task,
    validate_workspace_run,
    write_jsonl_records,
)


def test_make_result_cache_identity_binds_task_check_agent_workspace_and_runtime() -> None:
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
    )

    assert identity.task_id == task.task_id
    assert identity.check_id == check.check_id
    assert identity.check_digest == make_check_digest(check)
    assert identity.agent_manifest_digest == agent.agent_manifest_digest
    assert identity.workspace_config_digest == canonical_digest(workspace_config)
    assert identity.runtime_config_digest == canonical_digest(runtime_config)
    assert identity.identity_digest == canonical_digest(identity, exclude_self_digest=True)
    assert validate_result_cache_identity(identity).ok
    assert make_result_cache_key(identity) == identity.identity_digest


def test_result_cache_identity_changes_with_check_resource_limits() -> None:
    task = _task()
    check = _check(task)
    changed_check = replace(check, resource_limits={"timeout_seconds": 10})
    inputs = (_agent(), _workspace_config(), _runtime_config())

    identity = make_result_cache_identity(task, check, *inputs)
    changed_identity = make_result_cache_identity(task, changed_check, *inputs)

    assert changed_identity.identity_digest != identity.identity_digest
    assert make_result_cache_key(changed_identity) != make_result_cache_key(identity)


def test_result_cache_key_rejects_incomplete_identity() -> None:
    identity = ResultCacheIdentity(
        task_id="task",
        check_id="check",
        repository_id="repo",
        base_commit="commit",
        submodule_state_digest="submodules",
        solver_material_digest="solver",
        check_digest="check",
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
        )


def test_selector_config_digest_binds_family_and_parameters() -> None:
    parameters = {"seed": 7}
    selector = SelectorRecord(
        selector_id="selector",
        selector_family="random",
        selector_version="v1",
        training_source_digests=("training",),
        allowed_feature_classes=("task",),
        parameters=parameters,
        config_digest=canonical_digest({"selector_family": "random", "parameters": parameters}),
        created_at="2026-06-01T00:00:00Z",
    )

    assert validate_selector(selector).ok
    assert not validate_selector(replace(selector, parameters={"seed": 8})).ok


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


def test_benchmark_selection_rejects_duplicate_selected_refs() -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selected_task_check_refs=(ref, ref),
            selected_weights={task_check_ref_key(ref): 1.0},
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

    validation = validate_benchmark_selection(selection)

    assert "selected_task_check_refs must not contain duplicates" in validation.errors


@pytest.mark.parametrize("invalid_weight", [True, float("nan"), float("inf"), 10**400, 0.0, -1.0])
def test_benchmark_selection_rejects_invalid_weights_without_throwing(invalid_weight: object) -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id="pool",
        task_pool_digest="pool-digest",
        origin_id="origin",
        selector_id="selector",
        selected_task_check_refs=(ref,),
        selected_weights={task_check_ref_key(ref): invalid_weight},
        budget_digest="budget",
        selection_input_digest="input",
        feature_snapshot_id="features",
        eligibility_mode="eligible",
        exposure_state="frozen",
        exposed_at=None,
        exposure_scope_digest=None,
        created_at="2026-06-01T00:00:00Z",
        selection_digest="stale",
    )

    validation = validate_benchmark_selection(selection)

    assert not validation.ok
    assert "selected_weights must be finite positive numbers" in validation.errors


def test_benchmark_selection_rejects_unknown_exposure_state() -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selected_task_check_refs=(ref,),
            selected_weights={task_check_ref_key(ref): 1.0},
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="eligible",
            exposure_state="unknown",
            exposed_at=None,
            exposure_scope_digest=None,
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    assert "exposure_state is not normalized" in validate_benchmark_selection(selection).errors


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


def test_result_matrix_rejects_duplicate_denominator_dimensions() -> None:
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
    duplicate_agents = record_with_digest(replace(matrix, agent_ids=("agent", "agent"), matrix_digest=""))
    duplicate_refs = record_with_digest(replace(matrix, task_check_refs=(ref, ref), matrix_digest=""))

    assert "agent_ids must not contain duplicates" in validate_result_matrix(duplicate_agents).errors
    assert "task_check_refs must not contain duplicates" in validate_result_matrix(duplicate_refs).errors


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


def test_evaluation_cell_set_rejects_duplicate_selected_or_future_refs() -> None:
    from barcarolle.records import EvaluationCellSet, validate_evaluation_cell_set

    selected = TaskCheckRef("selected-task", "selected-check")
    future = TaskCheckRef("future-task", "future-check")
    cells = (
        ResultCellRef("agent", selected.task_id, selected.check_id, "selected-identity", None, None, "missing", None),
        ResultCellRef("agent", future.task_id, future.check_id, "future-identity", None, None, "missing", None),
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cells",
            origin_id="origin",
            selection_id="selection",
            selected_task_check_refs=(selected,),
            future_task_check_refs=(future,),
            cells=cells,
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    duplicate_selected = record_with_digest(
        replace(cell_set, selected_task_check_refs=(selected, selected), cell_set_digest="")
    )
    duplicate_future = record_with_digest(
        replace(cell_set, future_task_check_refs=(future, future), cell_set_digest="")
    )

    assert "selected_task_check_refs must not contain duplicates" in validate_evaluation_cell_set(duplicate_selected).errors
    assert "future_task_check_refs must not contain duplicates" in validate_evaluation_cell_set(duplicate_future).errors


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


@pytest.mark.parametrize("metric_value", [True, float("nan"), float("inf"), float("-inf"), 10**400])
def test_metric_validation_rejects_non_finite_values_without_throwing(metric_value: object) -> None:
    metric = MetricRecord(
        metric_id="metric",
        origin_id="origin",
        selection_id="selection",
        evaluation_cell_set_digest="cells",
        selected_matrix_digest="selected",
        future_matrix_digest="future",
        join_policy_digest="join",
        metric_config_digest="config",
        metric_scope="aggregate",
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest=None,
        stratum_ref=None,
        metric_name="mae",
        metric_value=metric_value,
        denominator_policy_digest="denominator",
        completeness_state="complete",
        abstention_reason=None,
        computed_at="2026-06-01T00:00:00Z",
        metric_digest="stale",
    )

    validation = validate_metric(metric)

    assert not validation.ok
    assert "metric_value must be a finite number" in validation.errors


def test_metric_validation_enforces_completeness_and_abstention_state() -> None:
    base = MetricRecord(
        metric_id="metric",
        origin_id="origin",
        selection_id="selection",
        evaluation_cell_set_digest="cells",
        selected_matrix_digest="selected",
        future_matrix_digest="future",
        join_policy_digest="join",
        metric_config_digest="config",
        metric_scope="aggregate",
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest=None,
        stratum_ref=None,
        metric_name="mae",
        metric_value=0.2,
        denominator_policy_digest="denominator",
        completeness_state="unknown",
        abstention_reason=None,
        computed_at="2026-06-01T00:00:00Z",
        metric_digest="",
    )
    metric = record_with_digest(base)

    assert "completeness_state is not normalized" in validate_metric(metric).errors


def test_jsonl_round_trip_preserves_records(tmp_path: Path) -> None:
    task = _task()
    path = tmp_path / "tasks.jsonl"

    write_jsonl_records(path, [task])
    loaded = load_jsonl_records(path, TaskRecord)

    assert loaded == [task]


def test_jsonl_load_rejects_non_finite_json_numbers(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text('{"value":NaN}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="non-finite JSON number"):
        load_jsonl_records(path, dict)


@pytest.mark.parametrize(
    ("value", "observed_at"),
    [(float("nan"), "2026-01-01T00:00:00Z"), (1, "not-a-time"), (1, 123)],
)
def test_feature_snapshot_validation_rejects_invalid_embedded_features_without_throwing(
    value: object,
    observed_at: object,
) -> None:
    record = FeatureRecord(
        feature_id="feature",
        feature_scope="origin",
        task_id=None,
        check_id=None,
        agent_id=None,
        result_id=None,
        result_cache_identity_digest=None,
        feature_name="count",
        value=value,
        aggregation_window=None,
        aggregation_method=None,
        observed_at=observed_at,
        source_artifact_digest="source",
        origin_snapshot_digest="origin-snapshot",
        leakage_class="task_metadata",
    )
    snapshot = FeatureSnapshotRecord(
        feature_snapshot_id="snapshot",
        origin_id="origin",
        feature_record_ids=(record.feature_id,),
        feature_records_digest="stale",
        leakage_policy_digest="policy",
        leakage_lint_status="not_run",
        feature_records=(record,),
        result_view_digest=None,
    )

    validation = validate_feature_snapshot(snapshot)

    assert not validation.ok


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_canonical_serialization_rejects_non_finite_numbers(non_finite: float) -> None:
    with pytest.raises(ValueError):
        canonical_json({"value": non_finite})
    with pytest.raises(ValueError):
        canonical_digest({"value": non_finite})


def test_canonical_serialization_rejects_mapping_key_collisions() -> None:
    colliding = {1: "hidden", "1": "visible"}

    with pytest.raises(TypeError, match="mapping keys must be strings"):
        canonical_json(colliding)
    with pytest.raises(TypeError, match="mapping keys must be strings"):
        canonical_digest(colliding)


@pytest.mark.parametrize(
    ("record_factory", "validator"),
    (
        (
            lambda: replace(_check(_task()), resource_limits={"process": {1: 2}}),
            validate_check,
        ),
        (
            lambda: replace(_workspace_run(), usage={"tokens": {1: 2}}),
            validate_workspace_run,
        ),
        (
            lambda: replace(_result(), result_digest="", usage={"tokens": {1: 2}}),
            validate_result,
        ),
    ),
)
def test_record_validators_report_nested_non_string_mapping_keys(record_factory, validator) -> None:
    validation = validator(record_factory())

    assert not validation.ok
    assert any("mapping keys must be strings" in error for error in validation.errors)


def test_jsonl_write_rejection_preserves_destination_and_removes_temporary_file(tmp_path: Path) -> None:
    destination = tmp_path / "records.jsonl"
    destination.write_text("existing\n", encoding="utf-8")

    with pytest.raises(ValueError):
        write_jsonl_records(destination, [{"value": float("nan")}])

    assert destination.read_text(encoding="utf-8") == "existing\n"
    assert set(tmp_path.iterdir()) == {destination}


@pytest.mark.parametrize(
    ("changes", "expected_error"),
    [
        ({"terminal_status": "completed"}, "terminal_status is not normalized"),
        ({"replay_status": "unknown"}, "replay_status is not normalized"),
        ({"check_outcome": "unknown"}, "check_outcome is not normalized"),
        ({"terminal_status": "passed", "check_outcome": "fail"}, "workspace run state is inconsistent"),
        ({"terminal_status": "failed", "check_outcome": "pass"}, "workspace run state is inconsistent"),
        ({"replay_status": "failed", "check_outcome": "pass"}, "workspace run state is inconsistent"),
        ({"invalid_owner": "agent"}, "workspace run state is inconsistent"),
        ({"usage": ()}, "usage must be a mapping"),
        ({"usage": {"output_tokens": "12"}}, "usage values must be finite and nonnegative"),
    ],
)
def test_workspace_run_validation_enforces_normalized_state_machine(
    changes: dict[str, object],
    expected_error: str,
) -> None:
    validation = validate_workspace_run(replace(_workspace_run(), **changes))

    assert not validation.ok
    assert any(expected_error in error for error in validation.errors)


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"terminal_status": "failed", "check_outcome": "fail"},
        {
            "terminal_status": "invalid",
            "replay_status": "skipped",
            "check_outcome": "invalid",
            "invalid_owner": "benchmark",
        },
        {"terminal_status": "error", "check_outcome": "pass"},
        {"terminal_status": "timeout", "check_outcome": "invalid"},
    ],
)
def test_workspace_run_validation_accepts_produced_state_combinations(changes: dict[str, object]) -> None:
    assert validate_workspace_run(replace(_workspace_run(), **changes)).ok


@pytest.mark.parametrize(
    ("changes", "expected_error"),
    [
        ({"terminal_status": "completed"}, "terminal_status is not normalized"),
        ({"scoreable_state": "complete"}, "scoreable_state is not normalized"),
        ({"outcome": "unknown"}, "outcome is not normalized"),
        ({"invalid_owner": "infrastructure"}, "invalid_owner is not normalized"),
        ({"usage_coverage": "complete-ish"}, "usage_coverage is not normalized"),
        ({"usage": {}}, "reported or complete usage must include a numeric measurement"),
        (
            {"usage": {}, "usage_coverage": "complete"},
            "reported or complete usage must include a numeric measurement",
        ),
        ({"cost": {}}, "cost must include total_cost"),
        ({"latency": {}}, "latency must include workspace_seconds"),
        ({"usage": {"input_tokens": -1}}, "usage values must be finite and nonnegative"),
        ({"usage": {"output_tokens": "12"}}, "usage values must be finite and nonnegative"),
        ({"usage": {"input_tokens": float("inf")}}, "usage values must be finite and nonnegative"),
        ({"cost": {"total_cost": -1.0}}, "cost values must be finite and nonnegative"),
        ({"cost": {"total_cost": float("nan")}}, "cost values must be finite and nonnegative"),
        ({"cost": {"total_cost": 10**400}}, "cost values must be finite and nonnegative"),
        ({"latency": {"workspace_seconds": float("inf")}}, "latency values must be finite and nonnegative"),
        ({"outcome": "fail"}, "result state is inconsistent"),
        (
            {"terminal_status": "invalid", "scoreable_state": "agent_invalid", "outcome": "invalid"},
            "result state is inconsistent",
        ),
    ],
)
def test_result_validation_enforces_normalized_measurements_and_state(
    changes: dict[str, object],
    expected_error: str,
) -> None:
    changed = replace(_result(), result_digest="", **changes)
    try:
        changed = record_with_digest(changed)
    except ValueError:
        # Strict canonical JSON intentionally cannot digest NaN or infinity;
        # validation must still return a useful failure for an imported record.
        pass

    validation = validate_result(changed)

    assert not validation.ok
    assert any(expected_error in error for error in validation.errors)


@pytest.mark.parametrize("usage_coverage", ["unknown", "unreported"])
def test_result_validation_allows_empty_usage_when_coverage_is_not_reported(usage_coverage: str) -> None:
    result = record_with_digest(
        replace(
            _result(),
            result_digest="",
            usage={},
            usage_coverage=usage_coverage,
        )
    )

    assert validate_result(result).ok


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"terminal_status": "failed", "outcome": "fail"},
        {
            "terminal_status": "invalid",
            "scoreable_state": "agent_invalid",
            "outcome": "invalid",
            "invalid_owner": "agent",
        },
        {
            "terminal_status": "error",
            "scoreable_state": "agent_invalid",
            "outcome": "invalid",
            "invalid_owner": "agent",
        },
        {
            "terminal_status": "invalid",
            "scoreable_state": "benchmark_invalid",
            "outcome": "invalid",
            "invalid_owner": "benchmark",
        },
        {"usage_coverage": "complete"},
    ],
)
def test_result_validation_accepts_normalized_state_combinations(changes: dict[str, object]) -> None:
    result = record_with_digest(replace(_result(), result_digest="", **changes))

    assert validate_result(result).ok


def test_stable_ids_do_not_depend_on_future_outcomes() -> None:
    task_id = make_task_id("repo", "commit", "source")
    check_id = make_check_id(task_id, "check")

    assert task_id.startswith("task_")
    assert check_id.startswith("check_")
    assert task_id == make_task_id("repo", "commit", "source")


def _workspace_run() -> WorkspaceRunRecord:
    return WorkspaceRunRecord(
        workspace_run_id="workspace-run",
        task_id="task",
        check_id="check",
        agent_id="agent",
        solver_workspace_digest="solver-workspace",
        verifier_workspace_digest="verifier-workspace",
        terminal_status="passed",
        diff_digest="diff",
        replay_status="applied",
        check_outcome="pass",
        invalid_owner=None,
        failure_label=None,
        usage={"input_tokens": 1},
        started_at="2026-06-01T00:00:00Z",
        finished_at="2026-06-01T00:00:01Z",
    )


def _result() -> ResultRecord:
    task = _task()
    check = _check(task)
    identity = make_result_cache_identity(
        task,
        check,
        _agent(),
        _workspace_config(),
        _runtime_config(),
    )
    return record_with_digest(
        ResultRecord(
            result_id="result",
            result_digest="",
            cache_identity=identity,
            agent_id="agent",
            task_id=task.task_id,
            check_id=check.check_id,
            terminal_status="passed",
            scoreable_state="scoreable",
            outcome="pass",
            invalid_owner=None,
            failure_label=None,
            cost={"total_cost": 0.0},
            scoring_config_digest="scoring:v1",
            pricing_version="test",
            usage={"input_tokens": 1},
            usage_coverage="reported",
            latency={"workspace_seconds": 1.0},
            diff_digest="diff",
            verifier_metadata_digest="verifier",
            started_at="2026-06-01T00:00:00Z",
            finished_at="2026-06-01T00:00:01Z",
            result_available_at="2026-06-01T00:00:02Z",
        )
    )


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
