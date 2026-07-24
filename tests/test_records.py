from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
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
    SourceEventRecord,
    TaskCheckRef,
    TaskRecord,
    ValidationResult,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_data,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_check_digest,
    make_check_command_digest,
    make_check_id,
    make_feature_snapshot_id,
    make_result_cache_identity,
    make_result_cache_key,
    make_source_event_id,
    make_solver_material_digest,
    make_task_id,
    format_utc_timestamp,
    parse_utc_timestamp,
    record_with_digest,
    result_cell_record_mismatches,
    task_check_ref_key,
    validate_agent,
    validate_benchmark_selection,
    validate_check,
    validate_feature_snapshot,
    validate_metric,
    validate_result,
    validate_result_cache_identity,
    validate_result_matrix,
    validate_selector,
    validate_selector_input,
    validate_source_event,
    validate_task,
    validate_workspace_run,
    write_jsonl_records,
)


def test_utc_timestamp_contract_normalizes_offsets_and_rejects_naive_values() -> None:
    assert parse_utc_timestamp("2026-01-01T06:00:00-05:00") == datetime(
        2026, 1, 1, 11, tzinfo=UTC
    )
    assert format_utc_timestamp(datetime(2026, 1, 1, 11, tzinfo=UTC)) == (
        "2026-01-01T11:00:00.000000Z"
    )
    with pytest.raises(ValueError, match="timezone offset"):
        parse_utc_timestamp("2026-01-01T11:00:00")
    with pytest.raises(ValueError, match="timestamp must be a string"):
        parse_utc_timestamp(7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        format_utc_timestamp(datetime(2026, 1, 1, 11))


def test_check_command_digest_has_one_canonical_identity() -> None:
    assert make_check_command_digest(["python", "check.py"]) == canonical_digest(
        {"check_command": ("python", "check.py")}
    )


def test_agent_model_identity_requires_snapshot_or_bounded_scope() -> None:
    resolved = _agent()
    scoped_alias = replace(
        resolved,
        requested_model_id="moving-alias",
        model_snapshot_id=None,
        model_resolution_scope_id="campaign-2026-01",
        model_resolution_scope_started_at="2026-01-01T00:00:00Z",
        model_resolution_scope_ended_at="2026-02-01T00:00:00Z",
    )

    assert validate_agent(resolved).ok
    assert validate_agent(scoped_alias).ok
    assert (
        "unresolved model aliases require a complete model resolution scope"
        in validate_agent(
            replace(
                scoped_alias,
                model_resolution_scope_ended_at=None,
            )
        ).errors
    )
    assert (
        "resolved model snapshots must not set a model resolution scope"
        in validate_agent(replace(scoped_alias, model_snapshot_id="snapshot-1")).errors
    )
    assert (
        "model resolution scope must have positive duration"
        in validate_agent(
            replace(
                scoped_alias,
                model_resolution_scope_ended_at=(
                    scoped_alias.model_resolution_scope_started_at
                ),
            )
        ).errors
    )


def test_result_cache_identity_binds_unresolved_model_campaign_scope() -> None:
    task = _task()
    check = _check(task)
    agent = replace(
        _agent(),
        requested_model_id="moving-alias",
        model_snapshot_id=None,
        model_resolution_scope_id="campaign-a",
        model_resolution_scope_started_at="2026-01-01T00:00:00Z",
        model_resolution_scope_ended_at="2026-02-01T00:00:00Z",
    )
    changed_agent = replace(agent, model_resolution_scope_id="campaign-b")

    identity = make_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )
    changed_identity = make_result_cache_identity(
        task, check, changed_agent, _workspace_config(), _runtime_config()
    )

    assert validate_result_cache_identity(identity).ok
    assert identity.requested_model_id == "moving-alias"
    assert identity.model_snapshot_id is None
    assert identity.identity_digest != changed_identity.identity_digest


def _accepted_source_event_record() -> SourceEventRecord:
    return record_with_digest(
        SourceEventRecord(
            source_event_id=make_source_event_id("repo", "issue", "issue-1"),
            repository_id="repo",
            source_family="issue",
            source_ref="issue-1",
            source_resolved_at="2026-01-01T00:00:00Z",
            task_material_available_at="2026-01-02T00:00:00Z",
            check_material_available_at="2026-01-04T00:00:00Z",
            label_mature_at="2026-01-04T00:00:00.000000Z",
            candidate_id="candidate",
            task_id="task",
            check_id="check",
            disposition="accepted",
            rejection_stage=None,
            rejection_reasons=(),
            dependency_cluster_id="dependency-cluster",
            sampling_stratum="stratum",
            source_event_digest="",
        )
    )


def test_source_event_record_binds_disposition_and_label_maturity() -> None:
    event = _accepted_source_event_record()

    assert validate_source_event(event).ok
    assert not validate_source_event(
        replace(event, label_mature_at="2026-01-03T00:00:00Z")
    ).ok
    assert not validate_source_event(
        record_with_digest(
            replace(
                event,
                disposition="excluded",
                source_event_digest="",
            )
        )
    ).ok


def test_source_event_validation_fails_closed_on_bad_material_and_reasons() -> None:
    event = _accepted_source_event_record()
    malformed_time = record_with_digest(
        replace(
            event,
            task_material_available_at="not-a-timestamp",
            label_mature_at=None,
            source_event_digest="",
        )
    )

    malformed_validation = validate_source_event(malformed_time)
    assert not malformed_validation.ok
    assert (
        "timestamps must be valid ISO datetimes: source_resolved_at, "
        "task_material_available_at"
    ) in malformed_validation.errors

    empty_reason = record_with_digest(
        replace(
            event,
            task_id=None,
            check_id=None,
            disposition="certification_rejected",
            rejection_stage="certification",
            rejection_reasons=("",),
            source_event_digest="",
        )
    )
    reason_validation = validate_source_event(empty_reason)
    assert not reason_validation.ok
    assert (
        "source event rejection reasons must be non-empty strings"
        in reason_validation.errors
    )


@pytest.mark.parametrize("rejection_reasons", ("reason", 7, {"reason": True}))
def test_source_event_validation_rejects_non_tuple_rejection_reasons(
    rejection_reasons: object,
) -> None:
    event = _accepted_source_event_record()
    malformed = record_with_digest(
        replace(
            event,
            task_id=None,
            check_id=None,
            disposition="certification_rejected",
            rejection_stage="certification",
            rejection_reasons=rejection_reasons,  # type: ignore[arg-type]
            source_event_digest="",
        )
    )

    validation = validate_source_event(malformed)

    assert not validation.ok
    assert "SourceEventRecord.rejection_reasons must be an array" in validation.errors


def test_make_result_cache_identity_binds_task_check_agent_workspace_and_runtime() -> (
    None
):
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
    assert identity.workspace_config_digest == canonical_digest(
        {
            "checkout_mode": "base_commit_history_v1",
            "workspace_config": workspace_config,
        }
    )
    assert identity.runtime_config_digest == canonical_digest(runtime_config)
    assert identity.identity_digest == canonical_digest(
        identity, exclude_self_digest=True
    )
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


@pytest.mark.parametrize(
    "value",
    (object(), float("nan"), float("inf"), (1, 2)),
)
def test_check_validation_rejects_non_json_resource_limit_before_digest(
    value: object,
) -> None:
    check = replace(
        _check(_task()),
        resource_limits={"timeout_seconds": value},
    )

    validation = validate_check(check)

    assert not validation.ok
    assert any(
        "strict JSON" in error or "unsupported type" in error
        for error in validation.errors
    )


def test_check_validation_rejects_cyclic_json_without_recursion_error() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    check = replace(_check(_task()), resource_limits={"limits": cyclic})

    validation = validate_check(check)

    assert not validation.ok
    assert "canonical JSON values must not contain cycles" in validation.errors


@pytest.mark.parametrize(
    ("field", "value"),
    (("check_type", "unittest"), ("oracle_source", "generated_tests")),
)
def test_result_cache_identity_changes_with_check_behavior(
    field: str, value: str
) -> None:
    task = _task()
    check = _check(task)
    changed_check = replace(check, **{field: value})
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
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
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
    other_base_commit = "b" * 40
    other_task = TaskRecord(
        **{
            **task.__dict__,
            "task_id": make_task_id("repo", other_base_commit, "source"),
            "base_commit": other_base_commit,
            "check_ids": (
                make_check_id(
                    make_task_id("repo", other_base_commit, "source"),
                    "check",
                ),
            ),
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
    check = CheckRecord(
        **{
            **_check(task).__dict__,
            "check_id": make_check_id(task.task_id, "different-check"),
        }
    )

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
    selector = record_with_digest(
        SelectorRecord(
            selector_id="selector",
            selector_family="random",
            selector_version="v1",
            training_source_digests=("training",),
            allowed_feature_classes=("task",),
            parameters=parameters,
            config_digest=canonical_digest(
                {"selector_family": "random", "parameters": parameters}
            ),
            created_at="2026-06-01T00:00:00Z",
            selector_digest="",
        )
    )

    assert validate_selector(selector).ok
    assert not validate_selector(replace(selector, parameters={"seed": 8})).ok


@pytest.mark.parametrize("value", (object(), float("nan"), (1, 2)))
def test_selector_validation_returns_json_errors_for_non_json_parameters(
    value: object,
) -> None:
    selector = SelectorRecord(
        selector_id="selector",
        selector_family="random",
        selector_version="v1",
        training_source_digests=("training",),
        allowed_feature_classes=("task",),
        parameters={"payload": value},
        config_digest="stale",
        created_at="2026-06-01T00:00:00Z",
        selector_digest="stale",
    )

    validation = validate_selector(selector)

    assert not validation.ok
    assert any(
        "strict JSON" in error or "unsupported type" in error
        for error in validation.errors
    )


def test_task_validation_rejects_stale_solver_material_digest_and_unordered_timestamps() -> (
    None
):
    task = TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit="a" * 40,
        source_family="issue",
        source_ref="source",
        source_resolved_at="2026-06-02T00:00:00Z",
        task_material_available_at="2026-06-01T00:00:00Z",
        task_text="Fix the issue.",
        solver_material_digest="solver",
        solver_material_refs=("README.md",),
        check_ids=("check",),
        dependency_cluster_id="dependency-cluster",
        sampling_stratum="stratum",
    )

    result = validate_task(task)

    assert not result.ok
    assert any("timestamps" in error for error in result.errors)
    assert any("solver_material_digest" in error for error in result.errors)


def test_task_validation_rejects_timezone_naive_evidence_timestamp() -> None:
    result = validate_task(replace(_task(), source_resolved_at="2026-06-01T00:00:00"))

    assert not result.ok
    assert any("timestamps must be valid" in error for error in result.errors)


def test_task_and_check_validation_allow_optional_cluster_and_resource_overrides() -> (
    None
):
    task = replace(
        _task(),
        dependency_cluster_id="",
        sampling_stratum="",
    )
    check = replace(_check(task), resource_limits={})

    assert validate_task(task).ok
    assert validate_check(check).ok


@pytest.mark.parametrize(
    "base_commit",
    ("main", "abc123", "A" * 40, "a" * 39, "a" * 41),
)
def test_task_validation_requires_full_lowercase_commit_oid(base_commit: str) -> None:
    result = validate_task(replace(_task(), base_commit=base_commit))

    assert not result.ok
    assert "base_commit must be a full lowercase Git object ID" in result.errors


@pytest.mark.parametrize("base_commit", ("a" * 40, "b" * 64))
def test_task_validation_accepts_sha1_and_sha256_commit_oids(base_commit: str) -> None:
    assert validate_task(replace(_task(), base_commit=base_commit)).ok


def test_benchmark_selection_weights_must_match_selected_refs() -> None:
    selected = (TaskCheckRef("task-1", "check-1"),)
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=selected,
            selected_weights={
                task_check_ref_key(selected[0]): 1.0,
                task_check_ref_key(TaskCheckRef("other", "check")): 1.0,
            },
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="strict_prospective",
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    result = validate_benchmark_selection(selection)

    assert not result.ok
    assert (
        "selected_weights must exactly cover selected_task_check_refs" in result.errors
    )


def test_benchmark_selection_rejects_duplicate_selected_refs() -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=(ref, ref),
            selected_weights={task_check_ref_key(ref): 1.0},
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="strict_prospective",
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    validation = validate_benchmark_selection(selection)

    assert "selected_task_check_refs must not contain duplicates" in validation.errors


@pytest.mark.parametrize(
    ("invalid_weight", "expected_error"),
    (
        (True, "must be a number"),
        (float("nan"), "selected_weights must be finite positive floats"),
        (float("inf"), "selected_weights must be finite positive floats"),
        (10**400, "must be representable as a float"),
        (0.0, "selected_weights must be finite positive floats"),
        (-1.0, "selected_weights must be finite positive floats"),
    ),
)
def test_benchmark_selection_rejects_invalid_weights_without_throwing(
    invalid_weight: object,
    expected_error: str,
) -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id="pool",
        task_pool_digest="pool-digest",
        origin_id="origin",
        selector_id="selector",
        selector_digest="selector-digest",
        selected_task_check_refs=(ref,),
        selected_weights={task_check_ref_key(ref): invalid_weight},
        budget_digest="budget",
        selection_input_digest="input",
        feature_snapshot_id="features",
        eligibility_mode="strict_prospective",
        created_at="2026-06-01T00:00:00Z",
        selection_digest="stale",
    )

    validation = validate_benchmark_selection(selection)

    assert not validation.ok
    assert any(expected_error in error for error in validation.errors)


def test_benchmark_selection_rejects_integer_weight_before_persistence() -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=(ref,),
            selected_weights={task_check_ref_key(ref): 1},
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="strict_prospective",
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    validation = validate_benchmark_selection(selection)

    assert validation.errors == ("selected_weights must be finite positive floats",)


def test_benchmark_selection_schema_is_frozen_without_publication_state() -> None:
    ref = TaskCheckRef("task-1", "check-1")
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection",
            task_pool_id="pool",
            task_pool_digest="pool-digest",
            origin_id="origin",
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=(ref,),
            selected_weights={task_check_ref_key(ref): 1.0},
            budget_digest="budget",
            selection_input_digest="input",
            feature_snapshot_id="features",
            eligibility_mode="strict_prospective",
            created_at="2026-06-01T00:00:00Z",
            selection_digest="",
        )
    )

    data = canonical_data(selection)

    assert validate_benchmark_selection(selection).ok
    assert "exposure_state" not in data
    assert "exposed_at" not in data
    assert "exposure_scope_digest" not in data


def test_selector_input_validation_rejects_null_pre_origin_fields_without_throwing() -> (
    None
):
    ref = TaskCheckRef("task", "check")
    selector_input = SelectorInput(
        selector_input_id="selector-input",
        origin_id="origin",
        task_pool_id="pool",
        feature_snapshot_id="features",
        agent_ids=("agent",),
        agent_record_digests=("agent-digest",),
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
        eligibility_mode="strict_prospective",
    )

    result = validate_selector_input(selector_input)

    assert not result.ok
    assert "pre_origin_result_ids is required" in result.errors
    assert "pre_origin_result_digests is required" in result.errors

    misaligned = validate_selector_input(
        replace(
            selector_input,
            agent_record_digests=(),
            pre_origin_result_ids=(),
            pre_origin_result_digests=(),
        )
    )
    assert "agent_ids and agent_record_digests must align" in misaligned.errors


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
                    outcome="pass",
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


def test_result_matrix_rejects_incoherent_cell_state_payloads() -> None:
    ref = TaskCheckRef("task", "check")
    result_cell = ResultCellRef(
        agent_id="agent",
        task_id="task",
        check_id="check",
        required_identity_digest="identity",
        result_id="result",
        result_digest="digest",
        cell_state="result",
        exclusion_reason=None,
        outcome="pass",
    )

    def validate(
        cell: ResultCellRef,
        *,
        scoreable_state: str = "complete",
        abstention_reason: str | None = None,
    ):
        return validate_result_matrix(
            record_with_digest(
                ResultMatrix(
                    matrix_id="matrix",
                    matrix_role="selected",
                    origin_id="origin",
                    selection_id="selection",
                    agent_ids=("agent",),
                    task_check_refs=(ref,),
                    cells=(cell,),
                    join_policy_digest="join",
                    denominator_policy_digest="denominator",
                    abstention_reason=abstention_reason,
                    scoreable_state=scoreable_state,
                    matrix_digest="",
                )
            )
        )

    assert (
        "result cells must set a normalized outcome"
        in validate(replace(result_cell, outcome=None)).errors
    )
    assert (
        "result cells must not set exclusion_reason"
        in validate(replace(result_cell, exclusion_reason="")).errors
    )
    assert (
        "ResultCellRef.result_id must be a string"
        in validate(
            replace(result_cell, result_id=7)  # type: ignore[arg-type]
        ).errors
    )
    assert (
        "missing cells must not set exclusion_reason or outcome"
        in validate(
            replace(
                result_cell,
                result_id=None,
                result_digest=None,
                cell_state="missing",
                exclusion_reason="unexpected",
            )
        ).errors
    )
    assert "excluded cells must bind both result_id and result_digest or neither" in (
        validate(
            replace(
                result_cell,
                result_digest=None,
                cell_state="excluded",
                exclusion_reason="agent_invalid",
            )
        ).errors
    )
    assert "ResultCellRef.result_digest must be a string" in (
        validate(
            replace(
                result_cell,
                result_digest=8,  # type: ignore[arg-type]
                cell_state="excluded",
                exclusion_reason="agent_invalid",
            )
        ).errors
    )
    assert (
        "ResultCellRef.exclusion_reason must be a string"
        in validate(
            replace(
                result_cell,
                cell_state="excluded",
                exclusion_reason=7,  # type: ignore[arg-type]
            )
        ).errors
    )
    assert (
        "excluded cells without a result must not set outcome"
        in validate(
            replace(
                result_cell,
                result_id=None,
                result_digest=None,
                cell_state="excluded",
                exclusion_reason="task_invalid",
            )
        ).errors
    )
    clean_missing = replace(
        result_cell,
        result_id=None,
        result_digest=None,
        cell_state="missing",
        outcome=None,
    )
    assert (
        "scoreable_state does not match matrix cells" in validate(clean_missing).errors
    )
    assert any(
        "ResultMatrix.scoreable_state must be one of" in error
        for error in validate(
            result_cell,
            scoreable_state="unknown",
        ).errors
    )
    assert (
        "abstained matrices require an abstention reason"
        in validate(
            result_cell,
            scoreable_state="abstained",
        ).errors
    )


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
    duplicate_agents = record_with_digest(
        replace(matrix, agent_ids=("agent", "agent"), matrix_digest="")
    )
    duplicate_refs = record_with_digest(
        replace(matrix, task_check_refs=(ref, ref), matrix_digest="")
    )

    assert (
        "agent_ids must not contain duplicates"
        in validate_result_matrix(duplicate_agents).errors
    )
    assert (
        "task_check_refs must not contain duplicates"
        in validate_result_matrix(duplicate_refs).errors
    )


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
    assert (
        "matrix cells must exactly cover every Agent/Task/Check denominator cell"
        in partial_result.errors
    )
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
            future_censored_task_check_refs=(),
            future_task_pool_id="task-pool",
            future_task_pool_digest="task-pool-digest",
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
    assert (
        "evaluation cell set must include at least one cell for each selected and future task/check ref"
        in result.errors
    )


def test_evaluation_cell_set_rejects_duplicate_selected_or_future_refs() -> None:
    from barcarolle.records import EvaluationCellSet, validate_evaluation_cell_set

    selected = TaskCheckRef("selected-task", "selected-check")
    future = TaskCheckRef("future-task", "future-check")
    cells = (
        ResultCellRef(
            "agent",
            selected.task_id,
            selected.check_id,
            "selected-identity",
            None,
            None,
            "missing",
            None,
        ),
        ResultCellRef(
            "agent",
            future.task_id,
            future.check_id,
            "future-identity",
            None,
            None,
            "missing",
            None,
        ),
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cells",
            origin_id="origin",
            selection_id="selection",
            selected_task_check_refs=(selected,),
            future_task_check_refs=(future,),
            future_censored_task_check_refs=(),
            future_task_pool_id="task-pool",
            future_task_pool_digest="task-pool-digest",
            cells=cells,
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    duplicate_selected = record_with_digest(
        replace(
            cell_set, selected_task_check_refs=(selected, selected), cell_set_digest=""
        )
    )
    duplicate_future = record_with_digest(
        replace(cell_set, future_task_check_refs=(future, future), cell_set_digest="")
    )

    assert (
        "selected_task_check_refs must not contain duplicates"
        in validate_evaluation_cell_set(duplicate_selected).errors
    )
    assert (
        "future_task_check_refs must not contain duplicates"
        in validate_evaluation_cell_set(duplicate_future).errors
    )


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
    assert (
        "agent metrics must set only agent_id among dimension fields" in result.errors
    )


@pytest.mark.parametrize(
    "updates, message",
    (
        (
            {"metric_scope": "agent", "agent_id": 7, "aggregation_level": None},
            "MetricRecord.agent_id must be a string",
        ),
        (
            {
                "metric_scope": "pair",
                "agent_pair": "agent-a",
                "aggregation_level": None,
            },
            "MetricRecord.agent_pair must be an array",
        ),
        (
            {
                "metric_scope": "pair",
                "agent_pair": ("agent-a", ""),
                "aggregation_level": None,
            },
            "pairwise metrics must set only agent_pair among dimension fields",
        ),
        (
            {"aggregation_level": 7},
            "MetricRecord.aggregation_level must be a string",
        ),
        (
            {"agent_id": ""},
            "aggregate metrics must set aggregation_level and no agent dimension",
        ),
        (
            {"budget_digest": 7},
            "MetricRecord.budget_digest must be a string",
        ),
        (
            {"completeness_state": "incomplete", "abstention_reason": 7},
            "MetricRecord.abstention_reason must be a string",
        ),
    ),
)
def test_metric_validation_rejects_non_reloadable_dimension_shapes(
    updates: dict[str, object],
    message: str,
) -> None:
    metric = record_with_digest(
        replace(
            MetricRecord(
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
                completeness_state="complete",
                abstention_reason=None,
                computed_at="2026-06-01T00:00:00Z",
                metric_digest="",
            ),
            **updates,
        )
    )

    validation = validate_metric(metric)

    assert not validation.ok
    assert message in validation.errors


@pytest.mark.parametrize(
    ("metric_value", "expected_error"),
    (
        (True, "MetricRecord.metric_value must be a number"),
        (float("nan"), "metric_value must be a finite float"),
        (float("inf"), "metric_value must be a finite float"),
        (float("-inf"), "metric_value must be a finite float"),
        (10**400, "MetricRecord.metric_value must be representable as a float"),
    ),
)
def test_metric_validation_rejects_non_finite_values_without_throwing(
    metric_value: object,
    expected_error: str,
) -> None:
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
    assert expected_error in validation.errors


def test_metric_validation_rejects_integer_value_before_persistence() -> None:
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
            metric_scope="aggregate",
            agent_id=None,
            agent_pair=None,
            aggregation_level="all_agents",
            budget_digest=None,
            stratum_ref=None,
            metric_name="mae",
            metric_value=0,
            denominator_policy_digest="denominator",
            completeness_state="complete",
            abstention_reason=None,
            computed_at="2026-06-01T00:00:00Z",
            metric_digest="",
        )
    )

    validation = validate_metric(metric)

    assert validation.errors == ("metric_value must be a finite float",)


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


@pytest.mark.parametrize(
    ("record_factory", "validator", "error"),
    (
        (
            lambda: replace(_task(), task_id=7),
            validate_task,
            "TaskRecord.task_id must be a string",
        ),
        (
            lambda: replace(_check(_task()), check_id=7),
            validate_check,
            "CheckRecord.check_id must be a string",
        ),
        (
            lambda: replace(_agent(), agent_id=7),
            validate_agent,
            "AgentRecord.agent_id must be a string",
        ),
        (
            lambda: replace(_task(), task_text=7),
            validate_task,
            "TaskRecord.task_text must be a string",
        ),
        (
            lambda: replace(_task(), solver_material_refs=7),
            validate_task,
            "TaskRecord.solver_material_refs must be an array",
        ),
        (
            lambda: replace(_result(), cache_identity=7),
            validate_result,
            "ResultCacheIdentity must be a JSON object",
        ),
    ),
)
def test_record_validators_reject_latest_schema_type_mismatches(
    record_factory: Callable[[], object],
    validator: Callable[..., ValidationResult],
    error: str,
) -> None:
    assert error in validator(record_factory()).errors


def test_jsonl_load_rejects_unknown_latest_schema_keys(tmp_path: Path) -> None:
    path = tmp_path / "unknown-field.jsonl"
    payload = canonical_data(_task())
    payload["legacy_field"] = "legacy"
    path.write_text(f"{canonical_json(payload)}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"line 1: TaskRecord schema has unknown keys: legacy_field",
    ):
        load_jsonl_records(path, TaskRecord)


def test_jsonl_load_rejects_missing_latest_schema_keys(tmp_path: Path) -> None:
    path = tmp_path / "missing-field.jsonl"
    payload = canonical_data(_task())
    del payload["sampling_stratum"]
    path.write_text(f"{canonical_json(payload)}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"line 1: TaskRecord schema is missing keys: sampling_stratum",
    ):
        load_jsonl_records(path, TaskRecord)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("task_id", 7, r"TaskRecord.task_id must be a string"),
        (
            "solver_material_refs",
            "README.md",
            r"TaskRecord.solver_material_refs must be an array",
        ),
    ),
)
def test_jsonl_load_rejects_wrong_latest_schema_types(
    tmp_path: Path,
    field: str,
    value: object,
    error: str,
) -> None:
    path = tmp_path / "wrong-type.jsonl"
    payload = canonical_data(_task())
    payload[field] = value
    path.write_text(f"{canonical_json(payload)}\n", encoding="utf-8")

    with pytest.raises(ValueError, match=rf"line 1: {error}"):
        load_jsonl_records(path, TaskRecord)


def test_jsonl_load_rejects_noncanonical_json_representation(tmp_path: Path) -> None:
    path = tmp_path / "noncanonical.jsonl"
    canonical = canonical_json(_task())
    noncanonical = canonical.replace(":", ": ", 1)
    path.write_text(f"{noncanonical}\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"line 1: TaskRecord is not canonical JSON"):
        load_jsonl_records(path, TaskRecord)


def test_jsonl_load_enforces_literal_scalar_type(tmp_path: Path) -> None:
    path = tmp_path / "wrong-state-type.jsonl"
    payload = canonical_data(_workspace_run())
    payload["terminal_status"] = 7
    path.write_text(f"{canonical_json(payload)}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"line 1: WorkspaceRunRecord.terminal_status must be a string",
    ):
        load_jsonl_records(path, WorkspaceRunRecord)


def test_jsonl_load_rejects_value_outside_literal_members(tmp_path: Path) -> None:
    path = tmp_path / "unknown-state.jsonl"
    payload = canonical_data(_workspace_run())
    payload["terminal_status"] = "nonsense"
    path.write_text(f"{canonical_json(payload)}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"line 1: WorkspaceRunRecord.terminal_status must be one of",
    ):
        load_jsonl_records(path, WorkspaceRunRecord)


def test_jsonl_load_rejects_blank_record_lines(tmp_path: Path) -> None:
    path = tmp_path / "blank-line.jsonl"
    path.write_text(f"{canonical_json(_task())}\n\n", encoding="utf-8")

    with pytest.raises(
        ValueError, match=r"line 2: blank JSONL records are not allowed"
    ):
        load_jsonl_records(path, TaskRecord)


def test_jsonl_load_rejects_non_finite_json_numbers(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text('{"value":NaN}\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"line 1: non-finite JSON number"):
        load_jsonl_records(path, dict)


def test_jsonl_load_enforces_non_dataclass_record_type(tmp_path: Path) -> None:
    path = tmp_path / "wrong-root-type.jsonl"
    path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"line 1: dict has the wrong type"):
        load_jsonl_records(path, dict)


def test_jsonl_load_reports_the_invalid_line_number(tmp_path: Path) -> None:
    path = tmp_path / "invalid-line.jsonl"
    path.write_text('{"ok":1}\n{"broken":\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"line 2"):
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


def test_feature_snapshot_validation_rejects_tuple_json_value_shape() -> None:
    feature = FeatureRecord(
        feature_id="feature",
        feature_scope="origin",
        task_id=None,
        check_id=None,
        agent_id=None,
        result_id=None,
        result_cache_identity_digest=None,
        feature_name="counts",
        value=(1, 2),
        aggregation_window=None,
        aggregation_method=None,
        observed_at="2026-01-01T00:00:00Z",
        source_artifact_digest="source",
        origin_snapshot_digest="origin-snapshot",
        leakage_class="task_metadata",
    )
    snapshot = FeatureSnapshotRecord(
        feature_snapshot_id="",
        origin_id="origin",
        feature_record_ids=(feature.feature_id,),
        feature_records_digest=canonical_digest((feature,)),
        leakage_policy_digest="policy",
        leakage_lint_status="not_run",
        feature_records=(feature,),
        result_view_digest=None,
        feature_config_digest="config",
        feature_snapshot_digest="",
    )
    snapshot = replace(
        snapshot,
        feature_snapshot_id=make_feature_snapshot_id(snapshot),
    )
    snapshot = record_with_digest(snapshot)

    validation = validate_feature_snapshot(snapshot)

    assert not validation.ok
    assert "feature_records[0]: value must be a strict JSON value" in validation.errors


def test_feature_snapshot_validation_rejects_passed_lint_without_feature_records() -> (
    None
):
    feature = FeatureRecord(
        feature_id="feature",
        feature_scope="origin",
        task_id=None,
        check_id=None,
        agent_id=None,
        result_id=None,
        result_cache_identity_digest=None,
        feature_name="count",
        value=1,
        aggregation_window=None,
        aggregation_method=None,
        observed_at="2026-01-01T00:00:00Z",
        source_artifact_digest="source",
        origin_snapshot_digest="origin-snapshot",
        leakage_class="task_metadata",
    )
    snapshot = FeatureSnapshotRecord(
        feature_snapshot_id="",
        origin_id="origin",
        feature_record_ids=(feature.feature_id,),
        feature_records_digest=canonical_digest((feature,)),
        leakage_policy_digest="policy",
        leakage_lint_status="passed",
        feature_records=(feature,),
        result_view_digest="result-view",
        feature_config_digest="feature-config",
        feature_snapshot_digest="",
    )
    snapshot = replace(snapshot, feature_snapshot_id=make_feature_snapshot_id(snapshot))
    snapshot = record_with_digest(snapshot)
    empty_materialization = record_with_digest(
        replace(snapshot, feature_records=(), feature_snapshot_digest="")
    )

    validation = validate_feature_snapshot(empty_materialization)

    assert not validation.ok
    assert "passed feature snapshots must include feature_records" in validation.errors


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_canonical_serialization_rejects_non_finite_numbers(non_finite: float) -> None:
    with pytest.raises(ValueError):
        canonical_json({"value": non_finite})
    with pytest.raises(ValueError):
        canonical_digest({"value": non_finite})


def test_canonical_serialization_collapses_signed_zero() -> None:
    positive_zero = {"value": 0.0}
    negative_zero = {"value": -0.0}

    assert canonical_json(negative_zero) == canonical_json(positive_zero)
    assert canonical_digest(negative_zero) == canonical_digest(positive_zero)


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
def test_record_validators_report_nested_non_string_mapping_keys(
    record_factory, validator
) -> None:
    validation = validator(record_factory())

    assert not validation.ok
    assert any("mapping keys must be strings" in error for error in validation.errors)


def test_jsonl_write_rejection_preserves_destination_and_removes_temporary_file(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "records.jsonl"
    destination.write_text("existing\n", encoding="utf-8")

    with pytest.raises(ValueError):
        write_jsonl_records(destination, [{"value": float("nan")}])

    assert destination.read_text(encoding="utf-8") == "existing\n"
    assert set(tmp_path.iterdir()) == {destination}


@pytest.mark.parametrize(
    ("changes", "expected_error"),
    [
        (
            {"terminal_status": "completed"},
            "WorkspaceRunRecord.terminal_status must be one of",
        ),
        (
            {"replay_status": "unknown"},
            "WorkspaceRunRecord.replay_status must be one of",
        ),
        (
            {"check_outcome": "unknown"},
            "WorkspaceRunRecord.check_outcome must be one of",
        ),
        (
            {"terminal_status": "passed", "check_outcome": "fail"},
            "workspace run state is inconsistent",
        ),
        (
            {"terminal_status": "failed", "check_outcome": "pass"},
            "workspace run state is inconsistent",
        ),
        (
            {"replay_status": "failed", "check_outcome": "pass"},
            "workspace run state is inconsistent",
        ),
        ({"invalid_owner": "agent"}, "workspace run state is inconsistent"),
        ({"usage": ()}, "WorkspaceRunRecord.usage must be an object"),
        (
            {"usage": {"output_tokens": "12"}},
            "usage values must be finite and nonnegative",
        ),
        ({"latency": {}}, "latency must include workspace_seconds"),
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
def test_workspace_run_validation_accepts_produced_state_combinations(
    changes: dict[str, object],
) -> None:
    assert validate_workspace_run(replace(_workspace_run(), **changes)).ok


@pytest.mark.parametrize(
    ("changes", "expected_error"),
    [
        (
            {"terminal_status": "completed"},
            "ResultRecord.terminal_status must be one of",
        ),
        (
            {"scoreable_state": "complete"},
            "ResultRecord.scoreable_state must be one of",
        ),
        ({"outcome": "unknown"}, "ResultRecord.outcome must be one of"),
        (
            {"invalid_owner": "infrastructure"},
            "ResultRecord.invalid_owner must be one of",
        ),
        ({"cost": {}}, "cost must include total_cost"),
        ({"latency": {}}, "latency must include workspace_seconds"),
        (
            {"usage": {"input_tokens": -1}},
            "usage values must be finite and nonnegative",
        ),
        (
            {"usage": {"output_tokens": "12"}},
            "usage values must be finite and nonnegative",
        ),
        (
            {"usage": {"input_tokens": float("inf")}},
            "usage values must be finite and nonnegative",
        ),
        ({"cost": {"total_cost": -1.0}}, "cost values must be finite and nonnegative"),
        (
            {"cost": {"total_cost": float("nan")}},
            "cost values must be finite and nonnegative",
        ),
        (
            {"cost": {"total_cost": 10**400}},
            "cost values must be finite and nonnegative",
        ),
        (
            {"latency": {"workspace_seconds": float("inf")}},
            "latency values must be finite and nonnegative",
        ),
        ({"outcome": "fail"}, "result state is inconsistent"),
        (
            {
                "terminal_status": "invalid",
                "scoreable_state": "agent_invalid",
                "outcome": "invalid",
            },
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


def test_result_validation_allows_empty_usage_with_unknown_cost() -> None:
    result = record_with_digest(
        replace(
            _result(),
            result_digest="",
            usage={},
            cost={"total_cost": None},
        )
    )

    assert validate_result(result).ok


def test_result_cell_record_mismatch_contract_covers_the_complete_binding() -> None:
    result = _result()
    cell = ResultCellRef(
        agent_id=result.agent_id,
        task_id=result.task_id,
        check_id=result.check_id,
        required_identity_digest=result.cache_identity.identity_digest,
        result_id=result.result_id,
        result_digest=result.result_digest,
        cell_state="result",
        exclusion_reason=None,
        outcome=result.outcome,
    )

    assert result_cell_record_mismatches(cell, result) == ()
    assert result_cell_record_mismatches(
        replace(
            cell,
            result_id="other-result",
            result_digest="other-digest",
            agent_id="other-agent",
            task_id="other-task",
            check_id="other-check",
            required_identity_digest="other-identity",
            outcome="fail",
        ),
        result,
    ) == (
        "result_id",
        "result_digest",
        "agent_id",
        "task_id",
        "check_id",
        "required_identity_digest",
        "outcome",
    )


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
    ],
)
def test_result_validation_accepts_normalized_state_combinations(
    changes: dict[str, object],
) -> None:
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
        latency={
            "workspace_seconds": 1.0,
            "agent_seconds": 0.4,
            "verification_seconds": 0.2,
            "solver_checkout_seconds": 0.1,
            "verifier_checkout_seconds": 0.1,
            "diff_replay_seconds": 0.1,
            "cleanup_seconds": 0.1,
        },
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
            latency={"workspace_seconds": 1.0},
            diff_digest="diff",
            verifier_metadata_digest="verifier",
            started_at="2026-06-01T00:00:00Z",
            finished_at="2026-06-01T00:00:01Z",
            result_available_at="2026-06-01T00:00:02Z",
        )
    )


def _task() -> TaskRecord:
    base_commit = "a" * 40
    task_id = make_task_id("repo", base_commit, "source")
    check_id = make_check_id(task_id, "check")
    task_text = "Fix the issue."
    solver_material_refs = ("README.md",)
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit=base_commit,
        source_family="issue",
        source_ref="source",
        source_resolved_at="2026-06-01T00:00:00Z",
        task_material_available_at="2026-06-02T00:00:00Z",
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=(check_id,),
        dependency_cluster_id="dependency-cluster",
        sampling_stratum="stratum",
    )


def _check(task: TaskRecord) -> CheckRecord:
    return CheckRecord(
        check_id=make_check_id(task.task_id, "check"),
        task_id=task.task_id,
        check_type="pytest",
        check_manifest_digest="manifest",
        hidden_check_bundle_digest="hidden-bundle-digest",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private_tests",
        check_material_available_at="2026-06-02T00:00:00Z",
    )


def _agent() -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
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
