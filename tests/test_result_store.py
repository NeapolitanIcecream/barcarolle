from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest

from barcarolle import result_store as result_store_module

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    EvaluationCellSet,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RuntimeConfig,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    canonical_json,
    make_solver_material_digest,
    record_with_digest,
    validate_result,
    validate_result_matrix,
)
from barcarolle.result_store import (
    ResultCacheConfig,
    ResultJoinConfig,
    ResultQuery,
    ResultStore,
    ScoringConfig,
    build_result_matrix,
    build_result_record,
    compute_result_cache_identity,
    compute_result_cache_key,
    compute_cost,
    find_missing_results,
    load_results,
    open_result_store_session,
    recover_result_store_tail,
    resolve_result_cells,
    result_matrix_evidence_errors,
    store_result,
    store_results,
)


def test_result_cache_config_does_not_expose_exact_identity_as_a_policy_axis() -> None:
    config_type: Any = ResultCacheConfig

    with pytest.raises(TypeError, match="reuse_policy"):
        config_type(reuse_policy="exact_identity")


@pytest.mark.parametrize("value", (0, 1, "false", None))
def test_result_cache_config_requires_an_exact_boolean(value: object) -> None:
    config_type: Any = ResultCacheConfig

    with pytest.raises(ValueError, match="reuse_benchmark_invalid must be a bool"):
        config_type(reuse_benchmark_invalid=value)


def test_result_join_policy_digests_are_derived_from_behavior() -> None:
    config = ResultJoinConfig()
    missing_is_error = replace(config, missing_cell_policy="error")
    agent_invalid_is_excluded = replace(config, agent_invalid_policy="exclude")

    assert ResultJoinConfig().join_policy_digest == config.join_policy_digest
    assert (
        ResultJoinConfig().denominator_policy_digest == config.denominator_policy_digest
    )
    assert missing_is_error.join_policy_digest != config.join_policy_digest
    assert (
        missing_is_error.denominator_policy_digest == config.denominator_policy_digest
    )
    assert agent_invalid_is_excluded.join_policy_digest != config.join_policy_digest
    assert (
        agent_invalid_is_excluded.denominator_policy_digest
        != config.denominator_policy_digest
    )


def test_build_result_record_stores_complete_identity_status_cost_and_latency() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, workspace_config, runtime_config
    )
    workspace_run = _workspace_run(
        usage={"input_tokens": 100, "output_tokens": 20, "harness_requests": 1}
    )

    result = build_result_record(
        task, check, agent, workspace_run, identity, scoring_config
    )

    assert validate_result(result).ok
    assert compute_result_cache_key(identity) == identity.identity_digest
    assert result.cache_identity == identity
    assert result.outcome == "pass"
    assert result.scoreable_state == "scoreable"
    assert result.cost["input_tokens_cost"] == 0.1
    assert result.cost["output_tokens_cost"] == 0.1
    assert result.cost["total_cost"] == 0.2
    assert result.usage == workspace_run.usage
    assert result.latency["workspace_seconds"] == 5.0
    assert result.latency["agent_seconds"] == 2.0
    assert result.latency["verification_seconds"] == 1.0
    assert result.verifier_metadata_digest


def test_pricing_change_reuses_paid_execution_and_can_recompute_cost(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store_result(result, store)
    changed_pricing = ScoringConfig(
        pricing_version="test-pricing-v2",
        cost_rates={"input_tokens": 0.01, "output_tokens": 0.02},
    )

    execution_cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
    )
    current_pricing_cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
        scoring_config=changed_pricing,
    )

    assert execution_cells[0].result_id == result.result_id
    assert current_pricing_cells[0].cell_state == "missing"
    assert current_pricing_cells[0].result_id is None
    assert compute_cost(result.usage, changed_pricing)["total_cost"] == 0.01


def test_scoring_config_digest_is_derived_and_cannot_be_supplied() -> None:
    source_rates = {"output_tokens": 0.02, "input_tokens": 1}
    config = ScoringConfig("pricing-v1", source_rates)
    same_config = ScoringConfig(
        "pricing-v1", {"input_tokens": 1.0, "output_tokens": 0.02}
    )

    assert config.scoring_config_digest == same_config.scoring_config_digest
    assert config.scoring_config_digest == canonical_digest(
        {
            "pricing_version": "pricing-v1",
            "cost_rates": {"input_tokens": 1.0, "output_tokens": 0.02},
        }
    )
    initial_digest = config.scoring_config_digest
    source_rates["input_tokens"] = 2
    assert config.cost_rates == {"input_tokens": 1.0, "output_tokens": 0.02}
    assert config.scoring_config_digest == initial_digest
    frozen_rates: Any = config.cost_rates
    with pytest.raises(TypeError):
        frozen_rates["input_tokens"] = 3.0
    constructor: Any = ScoringConfig
    with pytest.raises(TypeError, match="scoring_config_digest"):
        constructor(
            pricing_version="pricing-v1",
            cost_rates={"input_tokens": 0.01},
            scoring_config_digest="caller-chosen",
        )


def test_scoring_config_canonicalizes_signed_zero_rates() -> None:
    positive_zero = ScoringConfig("pricing-v1", {"input_tokens": 0.0})
    negative_zero = ScoringConfig("pricing-v1", {"input_tokens": -0.0})

    assert positive_zero.scoring_config_digest == negative_zero.scoring_config_digest
    assert canonical_json(negative_zero.cost_rates) == '{"input_tokens":0.0}'


@pytest.mark.parametrize(
    ("pricing_version", "cost_rates", "error"),
    (
        ("", {}, "pricing_version"),
        ("pricing", [], "cost_rates must be a mapping"),
        ("pricing", {"input_tokens": -0.01}, "finite and nonnegative"),
        ("pricing", {"input_tokens": True}, "finite and nonnegative"),
        ("pricing", {1: 0.01}, "keys must be strings"),
    ),
)
def test_scoring_config_rejects_invalid_values_at_construction(
    pricing_version: object,
    cost_rates: object,
    error: str,
) -> None:
    constructor: Any = ScoringConfig

    with pytest.raises(ValueError, match=error):
        constructor(pricing_version, cost_rates)


def test_unknown_usage_cost_is_null_not_zero() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    result = build_result_record(
        task,
        check,
        agent,
        _workspace_run(usage={}),
        identity,
        scoring_config,
    )

    assert result.usage == {}
    assert result.cost["total_cost"] is None
    assert validate_result(result).ok


def test_nonempty_usage_without_cost_rates_has_unknown_total_cost() -> None:
    scoring_config = replace(_scoring_config(), cost_rates={})

    cost = compute_cost({"input_tokens": 100}, scoring_config)

    assert cost == {"total_cost": None}


def test_explicit_zero_cost_rate_produces_measured_zero_cost() -> None:
    scoring_config = replace(_scoring_config(), cost_rates={"input_tokens": 0.0})

    cost = compute_cost({"input_tokens": 100}, scoring_config)

    assert cost == {"input_tokens_cost": 0.0, "total_cost": 0.0}


def test_build_result_record_uses_utc_instants_for_result_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )
    workspace_run = replace(
        _workspace_run(),
        started_at="2026-01-01T07:00:00-03:00",
        finished_at="2026-01-01T08:00:00-03:00",
    )
    monkeypatch.setattr(result_store_module, "_now", lambda: "2026-01-01T10:30:00Z")

    result = build_result_record(
        task, check, agent, workspace_run, identity, scoring_config
    )

    assert result.result_available_at == "2026-01-01T11:00:00.000000Z"
    assert result.latency == {
        "workspace_seconds": 5.0,
        "agent_seconds": 2.0,
        "verification_seconds": 1.0,
        "solver_checkout_seconds": 0.5,
        "verifier_checkout_seconds": 0.5,
        "diff_replay_seconds": 0.25,
        "cleanup_seconds": 0.25,
    }


def test_build_result_record_rejects_identity_or_workspace_linkage_mismatch() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    with pytest.raises(ValueError, match="workspace_run agent"):
        build_result_record(
            task,
            check,
            agent,
            _workspace_run(agent_id="other-agent"),
            identity,
            scoring_config,
        )

    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    other_identity = compute_result_cache_identity(
        task, check, other_agent, _workspace_config(), _runtime_config()
    )
    with pytest.raises(ValueError, match="cache identity"):
        build_result_record(
            task, check, agent, _workspace_run(), other_identity, scoring_config
        )


@pytest.mark.parametrize(
    ("record_name", "changes", "expected_error"),
    (
        (
            "task",
            {"task_text": 7},
            "task is invalid: TaskRecord.task_text must be a string",
        ),
        (
            "task",
            {"check_ids": 7},
            "task is invalid: TaskRecord.check_ids must be an array",
        ),
        (
            "check",
            {"check_material_available_at": 7},
            "check is invalid: CheckRecord.check_material_available_at must be a string",
        ),
        (
            "agent",
            {"prompt_digest": 7},
            "agent is invalid: AgentRecord.prompt_digest must be a string",
        ),
        (
            "workspace_run",
            {"usage": 7},
            "workspace_run is invalid: WorkspaceRunRecord.usage must be an object",
        ),
    ),
)
def test_build_result_record_validates_input_records_before_relations(
    record_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_run = _workspace_run()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )
    if record_name == "task":
        task = replace(task, **changes)
    elif record_name == "check":
        check = replace(check, **changes)
    elif record_name == "agent":
        agent = replace(agent, **changes)
    else:
        workspace_run = replace(workspace_run, **changes)

    with pytest.raises(ValueError, match=expected_error):
        build_result_record(
            task,
            check,
            agent,
            workspace_run,
            identity,
            _scoring_config(),
        )


@pytest.mark.parametrize(
    ("record_name", "changes", "expected_error"),
    (
        (
            "task",
            {"task_text": 7},
            "task is invalid: TaskRecord.task_text must be a string",
        ),
        (
            "task",
            {"check_ids": 7},
            "task is invalid: TaskRecord.check_ids must be an array",
        ),
        (
            "check",
            {"check_type": 7},
            "check is invalid: CheckRecord.check_type must be a string",
        ),
        (
            "agent",
            {"agent_id": 7},
            "agent is invalid: AgentRecord.agent_id must be a string",
        ),
    ),
)
def test_compute_result_cache_identity_validates_input_records_before_relations(
    record_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    if record_name == "task":
        task = replace(task, **changes)
    elif record_name == "check":
        check = replace(check, **changes)
    else:
        agent = replace(agent, **changes)

    with pytest.raises(ValueError, match=expected_error):
        compute_result_cache_identity(
            task,
            check,
            agent,
            _workspace_config(),
            _runtime_config(),
        )


@pytest.mark.parametrize(
    ("config_name", "changes", "expected_error"),
    (
        (
            "workspace_config",
            {"workspace_config_id": 7},
            "workspace_config is invalid: "
            "WorkspaceConfig.workspace_config_id must be a string",
        ),
        (
            "workspace_config",
            {"repository_checkout_config_digest": 7},
            "workspace_config is invalid: "
            "WorkspaceConfig.repository_checkout_config_digest must be a string",
        ),
        (
            "runtime_config",
            {"runtime_config_id": 7},
            "runtime_config is invalid: "
            "RuntimeConfig.runtime_config_id must be a string",
        ),
        (
            "runtime_config",
            {"timeout_seconds": "5"},
            "runtime_config is invalid: "
            "RuntimeConfig.timeout_seconds must be an integer",
        ),
        (
            "runtime_config",
            {"timeout_seconds": 0},
            "runtime_config is invalid: timeout_seconds must be a positive integer",
        ),
        (
            "runtime_config",
            {"hardware_profile_digest": ""},
            "runtime_config is invalid: "
            "hardware_profile_digest must be a nonempty string or null",
        ),
    ),
)
def test_compute_result_cache_identity_validates_config_inputs(
    config_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    if config_name == "workspace_config":
        workspace_config = replace(workspace_config, **changes)
    else:
        runtime_config = replace(runtime_config, **changes)

    with pytest.raises(ValueError, match=expected_error):
        compute_result_cache_identity(
            _task(),
            _check(),
            _agent(),
            workspace_config,
            runtime_config,
        )


def test_build_result_record_rejects_stale_check_execution_identity() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )
    changed_check = replace(check, resource_limits={"timeout_seconds": 10})

    with pytest.raises(ValueError, match="check_digest"):
        build_result_record(
            task, changed_check, agent, _workspace_run(), identity, scoring_config
        )


def test_build_result_record_rejects_non_numeric_priced_usage() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    with pytest.raises(ValueError, match="finite and nonnegative"):
        build_result_record(
            task,
            check,
            agent,
            _workspace_run(usage={"input_tokens": 1, "output_tokens": "unknown"}),
            identity,
            scoring_config,
        )


def test_build_result_record_marks_cost_unknown_when_priced_usage_is_missing() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    result = build_result_record(
        task,
        check,
        agent,
        _workspace_run(usage={"input_tokens": 1}),
        identity,
        scoring_config,
    )

    assert result.cost == {"input_tokens_cost": 0.001, "total_cost": None}


def test_build_result_record_rejects_unrepresentable_usage_cost_without_overflow() -> (
    None
):
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    with pytest.raises(ValueError, match="finite and nonnegative"):
        build_result_record(
            task,
            check,
            agent,
            _workspace_run(usage={"input_tokens": 10**400}),
            identity,
            scoring_config,
        )


@pytest.mark.parametrize("terminal_status", ("error", "timeout"))
def test_build_result_record_classifies_runtime_termination_as_agent_invalid(
    terminal_status: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )

    result = build_result_record(
        task,
        check,
        agent,
        _workspace_run(terminal_status=terminal_status, check_outcome="fail"),
        identity,
        scoring_config,
    )

    assert result.terminal_status == terminal_status
    assert result.scoreable_state == "agent_invalid"
    assert result.outcome == "invalid"
    assert result.invalid_owner == "agent"


def test_build_result_record_excludes_baseline_check_failure_as_benchmark_invalid() -> (
    None
):
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, agent, _workspace_config(), _runtime_config()
    )
    workspace_run = _workspace_run(
        terminal_status="invalid",
        check_outcome="invalid",
        invalid_owner="benchmark",
        failure_label="baseline_check_passed_without_diff",
    )

    result = build_result_record(
        task, check, agent, workspace_run, identity, scoring_config
    )

    assert result.scoreable_state == "benchmark_invalid"
    assert result.outcome == "invalid"
    assert result.invalid_owner == "benchmark"


def test_store_result_is_append_only_and_load_results_filters(tmp_path: Path) -> None:
    result = _result()
    store = ResultStore(tmp_path / "results.jsonl")

    stored = store_result(result, store)
    same = store_result(result, store)
    loaded = load_results(
        store,
        ResultQuery(
            agent_ids=("agent",),
            cache_identity_digests=(result.cache_identity.identity_digest,),
        ),
    )

    assert stored == result
    assert same == result
    assert loaded == (result,)
    assert store.path.read_text(encoding="utf-8").count("\n") == 1

    conflict = record_with_digest(
        replace(result, result_digest="", failure_label="changed")
    )
    with pytest.raises(ValueError, match="different digest"):
        store_result(conflict, store)


def test_store_results_loads_once_and_fsyncs_one_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    first = _result()
    second = _result(
        workspace_run=_workspace_run(
            terminal_status="failed",
            check_outcome="fail",
            failure_label="check_failed",
        )
    )
    other_agent = _agent("other-agent", "other-manifest")
    third = _result(agent=other_agent)
    store_result(first, store)
    load_calls = 0
    real_load = result_store_module.load_jsonl_records
    fsync_calls: list[int] = []
    real_fsync = result_store_module.os.fsync

    def counted_load(path: Path, record_type: type) -> list[object]:
        nonlocal load_calls
        load_calls += 1
        return real_load(path, record_type)

    def counted_fsync(file_descriptor: int) -> None:
        fsync_calls.append(file_descriptor)
        real_fsync(file_descriptor)

    monkeypatch.setattr(result_store_module, "load_jsonl_records", counted_load)
    monkeypatch.setattr(result_store_module.os, "fsync", counted_fsync)

    stored = store_results((second, third), store)

    assert stored == (second, third)
    assert load_calls == 1
    assert len(fsync_calls) == 1
    assert load_results(store, ResultQuery()) == (first, second, third)


def test_result_store_lock_serializes_conflicting_writers(tmp_path: Path) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    original = _result()
    conflict = record_with_digest(
        replace(original, result_digest="", failure_label="changed")
    )
    barrier = Barrier(2)

    def write(result: ResultRecord) -> str:
        barrier.wait()
        try:
            store_result(result, store)
        except ValueError as exc:
            assert "different digest" in str(exc)
            return "conflict"
        return "stored"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(write, (original, conflict)))

    assert sorted(outcomes) == ["conflict", "stored"]
    assert len(load_results(store, ResultQuery())) == 1
    assert store.path.read_bytes().count(b"\n") == 1


@pytest.mark.parametrize("accessor", ("load", "session"))
@pytest.mark.parametrize("conflicting_digest", (False, True))
def test_result_store_load_rejects_duplicate_result_ids(
    tmp_path: Path,
    accessor: str,
    conflicting_digest: bool,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    original = _result()
    duplicate = (
        record_with_digest(
            replace(
                original,
                result_available_at="2026-01-02T00:00:00Z",
                result_digest="",
            )
        )
        if conflicting_digest
        else original
    )
    store.path.write_text(
        f"{canonical_json(original)}\n{canonical_json(duplicate)}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate result_id"):
        if accessor == "load":
            load_results(store, ResultQuery())
        else:
            with open_result_store_session(store):
                pass


def test_result_store_requires_explicit_truncated_tail_recovery(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store_result(result, store)
    with store.path.open("ab") as handle:
        handle.write(b'{"result_id":')

    with pytest.raises(ValueError, match="unterminated final line"):
        load_results(store, ResultQuery())

    assert recover_result_store_tail(store) == "truncated"
    assert load_results(store, ResultQuery()) == (result,)


def test_result_store_recovery_completes_parseable_unterminated_record(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store.path.write_text(canonical_json(result), encoding="utf-8")

    with pytest.raises(ValueError, match="unterminated final line"):
        load_results(store, ResultQuery())

    assert recover_result_store_tail(store) == "completed"
    assert load_results(store, ResultQuery()) == (result,)


def test_result_store_recovery_never_removes_complete_invalid_line(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store.path.write_text(
        f"{canonical_json(result)}\nnot-json\n",
        encoding="utf-8",
    )
    original = store.path.read_bytes()

    with pytest.raises(ValueError, match=r"line 2"):
        load_results(store, ResultQuery())

    assert recover_result_store_tail(store) == "not_needed"
    assert store.path.read_bytes() == original


def test_locked_result_store_session_reuses_its_live_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store_result(result, store)

    with open_result_store_session(store) as session:
        monkeypatch.setattr(
            result_store_module,
            "load_jsonl_records",
            lambda *_args: (_ for _ in ()).throw(
                AssertionError("session must not reload JSONL")
            ),
        )
        cells = resolve_result_cells(
            task_check_refs=(TaskCheckRef("task", "check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=store,
            cache_config=ResultCacheConfig(),
            session=session,
        )

    assert cells[0].result_id == result.result_id


def test_load_results_excludes_post_cutoff_result_with_earlier_offset_date(
    tmp_path: Path,
) -> None:
    result = record_with_digest(
        replace(
            _result(),
            result_available_at="2026-01-04T20:00:00-05:00",
            result_digest="",
        )
    )
    store = ResultStore(tmp_path / "results.jsonl")
    store_result(result, store)

    loaded = load_results(
        store,
        ResultQuery(result_available_before="2026-01-05T00:00:00Z"),
    )

    assert loaded == ()


def test_load_results_rejects_timezone_naive_cutoff(tmp_path: Path) -> None:
    store = ResultStore(tmp_path / "results.jsonl")

    with pytest.raises(ValueError, match="timezone offset"):
        load_results(
            store,
            ResultQuery(result_available_before="2026-01-05T00:00:00"),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "task_ids",
        "check_ids",
        "agent_ids",
        "result_ids",
        "cache_identity_digests",
        "scoring_config_digests",
    ),
)
def test_load_results_rejects_non_tuple_filters_before_store_access(
    tmp_path: Path,
    field_name: str,
) -> None:
    query = replace(ResultQuery(), **{field_name: 7})

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be a tuple of non-empty strings",
    ):
        load_results(ResultStore(tmp_path / "missing.jsonl"), query)


@pytest.mark.parametrize("task_ids", ((7,), ("",)))
def test_load_results_rejects_malformed_filter_items_before_store_access(
    tmp_path: Path,
    task_ids: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="task_ids must be a tuple of non-empty strings",
    ):
        load_results(
            ResultStore(tmp_path / "missing.jsonl"),
            ResultQuery(task_ids=task_ids),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("bound", (7, ""))
def test_load_results_rejects_malformed_time_bound_before_store_access(
    tmp_path: Path,
    bound: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="result_available_after must be null or a non-empty timestamp string",
    ):
        load_results(
            ResultStore(tmp_path / "missing.jsonl"),
            ResultQuery(result_available_after=bound),  # type: ignore[arg-type]
        )


def test_load_results_rejects_inverted_time_bounds_before_store_access(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="result_available_after must not be after result_available_before",
    ):
        load_results(
            ResultStore(tmp_path / "missing.jsonl"),
            ResultQuery(
                result_available_after="2026-01-02T00:00:00Z",
                result_available_before="2026-01-01T00:00:00Z",
            ),
        )


def test_resolve_result_cells_rejects_conflicting_exact_identity_executions(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    first = _result()
    later = _result(
        workspace_run=_workspace_run(
            terminal_status="failed",
            check_outcome="fail",
            failure_label="check_failed",
        )
    )
    store_result(first, store)
    store_result(later, store)

    with pytest.raises(
        ValueError,
        match="conflicting reusable Result executions share one cache identity",
    ):
        resolve_result_cells(
            task_check_refs=(TaskCheckRef("task", "check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=store,
            cache_config=ResultCacheConfig(),
        )


def test_resolve_result_cells_reuses_one_execution_across_pricing_views_deterministically(
    tmp_path: Path,
) -> None:
    original = _result()
    repriced = result_store_module._reprice_result(
        original,
        ScoringConfig("alternate-pricing", {"input_tokens": 0.002}),
    )
    resolved_ids = []
    for name, ordered_results in (
        ("forward", (original, repriced)),
        ("reverse", (repriced, original)),
    ):
        store = ResultStore(tmp_path / f"{name}.jsonl")
        store_results(ordered_results, store)
        (cell,) = resolve_result_cells(
            task_check_refs=(TaskCheckRef("task", "check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=store,
            cache_config=ResultCacheConfig(),
        )
        resolved_ids.append(cell.result_id)

    assert resolved_ids == [min(original.result_id, repriced.result_id)] * 2


@pytest.mark.parametrize(
    ("duplicate_dimension", "message"),
    (
        ("refs", "duplicate Task/Check refs"),
        ("agents", "duplicate Agent IDs"),
    ),
)
def test_resolve_result_cells_rejects_duplicate_dimensions(
    tmp_path: Path,
    duplicate_dimension: str,
    message: str,
) -> None:
    ref = TaskCheckRef("task", "check")
    agent = _agent()
    refs = (ref, ref) if duplicate_dimension == "refs" else (ref,)
    agents = (agent, agent) if duplicate_dimension == "agents" else (agent,)
    with pytest.raises(ValueError, match=message):
        resolve_result_cells(
            task_check_refs=refs,
            tasks=(_task(),),
            checks={"check": _check()},
            agents=agents,
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=ResultStore(tmp_path / "results.jsonl"),
            cache_config=ResultCacheConfig(),
        )


def test_resolve_result_cells_does_not_reuse_benchmark_invalid_result_by_default(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    benchmark_invalid = _result(
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="benchmark",
            failure_label="verifier_preparation_failed",
        )
    )
    store_result(benchmark_invalid, store)

    cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
    )

    assert len(cells) == 1
    assert cells[0].cell_state == "missing"
    assert cells[0].result_id is None


def test_resolve_result_cells_can_reuse_valid_benchmark_invalid_result_when_configured(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    benchmark_invalid = _result(
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="benchmark",
            failure_label="verifier_preparation_failed",
        )
    )
    store_result(benchmark_invalid, store)

    cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(reuse_benchmark_invalid=True),
    )

    assert cells[0].cell_state == "result"
    assert cells[0].result_id == benchmark_invalid.result_id


def test_resolve_result_cells_never_reuses_structurally_invalid_result(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    invalid = replace(_result(), result_digest="not-canonical")
    store.path.write_text(f"{canonical_json(invalid)}\n", encoding="utf-8")

    cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(reuse_benchmark_invalid=True),
    )

    assert cells[0].cell_state == "missing"
    assert cells[0].result_id is None


def test_resolve_result_cells_rejects_invalid_cache_identity_input_record(
    tmp_path: Path,
) -> None:
    invalid_agent = replace(_agent(), model_snapshot_id="")

    with pytest.raises(
        ValueError,
        match="agent is invalid: model_snapshot_id must be a nonempty string or null",
    ):
        resolve_result_cells(
            task_check_refs=(TaskCheckRef("task", "check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(invalid_agent,),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=ResultStore(tmp_path / "results.jsonl"),
            cache_config=ResultCacheConfig(),
        )


def test_resolve_result_cells_keeps_agent_invalid_result_reusable(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    agent_invalid = _result(
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        )
    )
    store_result(agent_invalid, store)

    cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
    )

    assert len(cells) == 1
    assert cells[0].cell_state == "result"
    assert cells[0].result_id == agent_invalid.result_id


def test_resolve_result_cells_misses_when_check_execution_config_changes(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    store_result(_result(), store)
    changed_check = replace(_check(), resource_limits={"timeout_seconds": 10})

    cells = resolve_result_cells(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": changed_check},
        agents=(_agent(),),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
    )

    assert len(cells) == 1
    assert cells[0].cell_state == "missing"
    assert cells[0].result_id is None


def test_find_missing_results_returns_only_cells_without_exact_reusable_identity(
    tmp_path: Path,
) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    task = _task()
    check = _check()
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    store_result(_result(agent=agent), store)

    missing = find_missing_results(
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(task,),
        checks={"check": check},
        agents=(agent, other_agent),
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        store=store,
        cache_config=ResultCacheConfig(),
    )

    assert len(missing) == 1
    assert missing[0].agent_id == "other-agent"
    assert missing[0].cell_state == "missing"
    assert missing[0].result_id is None
    assert missing[0].required_identity_digest


def test_find_missing_results_rejects_unlinked_task_check_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="check must be linked"):
        find_missing_results(
            task_check_refs=(TaskCheckRef("task", "other-check"),),
            tasks=(_task(),),
            checks={
                "other-check": _check(check_id="other-check", task_id="other-task")
            },
            agents=(_agent(),),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=ResultStore(tmp_path / "results.jsonl"),
            cache_config=ResultCacheConfig(),
        )


def test_build_result_matrix_joins_selected_cells_and_marks_missing_denominator() -> (
    None
):
    task = _task()
    check = _check()
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    result = _result(agent=agent)
    cell_set = _evaluation_cell_set((agent, other_agent), results=(result,))

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(task,),
        checks={"check": check},
        agents=(agent, other_agent),
        results=(result,),
        matrix_role="selected",
        join_config=ResultJoinConfig(),
    )

    assert validate_result_matrix(matrix).ok
    assert matrix.scoreable_state == "abstained"
    assert matrix.abstention_reason == "missing_required_results"
    assert {(cell.agent_id, cell.cell_state) for cell in matrix.cells} == {
        ("agent", "result"),
        ("other-agent", "missing"),
    }


@pytest.mark.parametrize(
    ("field_name", "build_config"),
    (
        ("missing_cell_policy", lambda: ResultJoinConfig(missing_cell_policy="typo")),
        ("agent_invalid_policy", lambda: ResultJoinConfig(agent_invalid_policy="typo")),
        (
            "benchmark_invalid_policy",
            lambda: ResultJoinConfig(benchmark_invalid_policy="typo"),
        ),
        ("abstention_policy", lambda: ResultJoinConfig(abstention_policy="typo")),
    ),
)
def test_result_join_config_rejects_unknown_policy(
    field_name: str, build_config: Any
) -> None:
    with pytest.raises(ValueError, match=field_name):
        build_config()


def test_build_result_matrix_abstains_on_agent_specific_invalid_exclusion() -> None:
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    invalid_result = _result(
        agent=agent,
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        ),
    )
    other_result = _result(agent=other_agent)
    cell_set = _evaluation_cell_set(
        (agent, other_agent), results=(invalid_result, other_result)
    )

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(invalid_result, other_result),
        matrix_role="selected",
        join_config=ResultJoinConfig(agent_invalid_policy="exclude"),
    )

    assert matrix.scoreable_state == "abstained"
    assert matrix.abstention_reason == "agent_specific_invalid_exclusion"
    assert {(cell.agent_id, cell.cell_state) for cell in matrix.cells} == {
        ("agent", "excluded"),
        ("other-agent", "result"),
    }


def test_build_result_matrix_counts_agent_invalid_as_failure_by_default() -> None:
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    invalid_result = _result(
        agent=agent,
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        ),
    )
    other_result = _result(agent=other_agent)
    cell_set = _evaluation_cell_set(
        (agent, other_agent), results=(invalid_result, other_result)
    )

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(invalid_result, other_result),
        matrix_role="selected",
        join_config=ResultJoinConfig(),
    )

    assert matrix.scoreable_state == "complete"
    assert matrix.abstention_reason is None
    assert {
        (cell.agent_id, cell.cell_state, cell.outcome) for cell in matrix.cells
    } == {
        ("agent", "result", "invalid"),
        ("other-agent", "result", "pass"),
    }


def test_matrix_evidence_rejects_mixed_agent_invalid_policies() -> None:
    first = _result(
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        )
    )
    second_identity = record_with_digest(
        replace(
            first.cache_identity,
            task_id="task-2",
            check_id="check-2",
            identity_digest="",
        )
    )
    second = record_with_digest(
        replace(
            first,
            result_id="result-2",
            result_digest="",
            cache_identity=second_identity,
            task_id="task-2",
            check_id="check-2",
        )
    )
    first_ref = TaskCheckRef(first.task_id, first.check_id)
    second_ref = TaskCheckRef(second.task_id, second.check_id)
    matrix = record_with_digest(
        ResultMatrix(
            matrix_id="mixed-agent-invalid-policy",
            matrix_role="selected",
            origin_id="origin",
            selection_id="selection",
            agent_ids=(first.agent_id,),
            task_check_refs=(first_ref, second_ref),
            cells=(
                ResultCellRef(
                    first.agent_id,
                    first.task_id,
                    first.check_id,
                    first.cache_identity.identity_digest,
                    first.result_id,
                    first.result_digest,
                    "excluded",
                    first.failure_label,
                    first.outcome,
                ),
                ResultCellRef(
                    second.agent_id,
                    second.task_id,
                    second.check_id,
                    second.cache_identity.identity_digest,
                    second.result_id,
                    second.result_digest,
                    "result",
                    None,
                    second.outcome,
                ),
            ),
            join_policy_digest=ResultJoinConfig().join_policy_digest,
            denominator_policy_digest=ResultJoinConfig().denominator_policy_digest,
            abstention_reason=None,
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )

    assert validate_result_matrix(matrix).ok
    assert any(
        "declared Result join policy" in error
        for error in result_matrix_evidence_errors(matrix, (first, second))
    )


def test_matrix_evidence_rejects_declared_policy_digest_drift() -> None:
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    invalid_result = _result(
        agent=agent,
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        ),
    )
    other_result = _result(agent=other_agent)
    matrix = build_result_matrix(
        evaluation_cells=_evaluation_cell_set(
            (agent, other_agent), results=(invalid_result, other_result)
        ),
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(invalid_result, other_result),
        matrix_role="selected",
        join_config=ResultJoinConfig(),
    )
    declared_config = ResultJoinConfig(agent_invalid_policy="exclude")
    drifted = record_with_digest(
        replace(
            matrix,
            join_policy_digest=declared_config.join_policy_digest,
            denominator_policy_digest=declared_config.denominator_policy_digest,
            matrix_digest="",
        )
    )

    assert validate_result_matrix(drifted).ok
    assert any(
        "declared Result join policy" in error
        for error in result_matrix_evidence_errors(
            drifted, (invalid_result, other_result)
        )
    )


def test_matrix_evidence_rejects_policy_derived_abstention_drift() -> None:
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    invalid_result = _result(
        agent=agent,
        workspace_run=_workspace_run(
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="agent",
            failure_label="agent_workspace_corrupted",
        ),
    )
    other_result = _result(agent=other_agent)
    matrix = build_result_matrix(
        evaluation_cells=_evaluation_cell_set(
            (agent, other_agent), results=(invalid_result, other_result)
        ),
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(invalid_result, other_result),
        matrix_role="selected",
        join_config=ResultJoinConfig(agent_invalid_policy="exclude"),
    )
    drifted = record_with_digest(
        replace(
            matrix,
            abstention_reason="missing_required_results",
            matrix_digest="",
        )
    )

    assert validate_result_matrix(drifted).ok
    assert any(
        "declared Result join policy" in error
        for error in result_matrix_evidence_errors(
            drifted, (invalid_result, other_result)
        )
    )


def test_build_result_matrix_excludes_benchmark_invalid_result_with_traceability() -> (
    None
):
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    result = _result(agent=agent)
    invalid_result = _result(
        agent=other_agent,
        workspace_run=_workspace_run(
            agent_id="other-agent",
            terminal_status="invalid",
            check_outcome="invalid",
            invalid_owner="benchmark",
            failure_label="check_launch_error",
        ),
    )
    cell_set = _evaluation_cell_set(
        (agent, other_agent), results=(result, invalid_result)
    )

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(result, invalid_result),
        matrix_role="selected",
        join_config=ResultJoinConfig(),
    )

    excluded = {
        cell.agent_id: cell for cell in matrix.cells if cell.cell_state == "excluded"
    }
    assert validate_result_matrix(matrix).ok
    assert matrix.scoreable_state == "complete_with_exclusions"
    assert matrix.abstention_reason is None
    assert set(excluded) == {"agent", "other-agent"}
    assert excluded["agent"].result_id == result.result_id
    assert excluded["agent"].result_digest == result.result_digest
    assert excluded["other-agent"].result_id == invalid_result.result_id
    assert excluded["other-agent"].result_digest == invalid_result.result_digest
    assert (
        excluded["agent"].exclusion_reason == excluded["other-agent"].exclusion_reason
    )
    exclusion_reason = excluded["agent"].exclusion_reason
    assert exclusion_reason is not None
    assert exclusion_reason.startswith(
        "task_check_infrastructure_failure:check_launch_error:"
    )


def test_build_result_matrix_uses_result_frozen_in_evaluation_cell_set() -> None:
    agent = _agent()
    frozen_fail = _result(
        workspace_run=_workspace_run(
            terminal_status="failed",
            check_outcome="fail",
            failure_label="check_failed",
        )
    )
    later_pass = _result()
    assert frozen_fail.cache_identity == later_pass.cache_identity
    cell_set = _evaluation_cell_set((agent,), results=(frozen_fail,))

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent,),
        results=(frozen_fail, later_pass),
        matrix_role="selected",
        join_config=ResultJoinConfig(),
    )

    assert len(matrix.cells) == 1
    assert matrix.cells[0].result_id == frozen_fail.result_id
    assert matrix.cells[0].result_digest == frozen_fail.result_digest
    assert matrix.cells[0].outcome == "fail"


def test_build_result_matrix_rejects_task_check_refs_that_do_not_match_role_subset() -> (
    None
):
    with pytest.raises(ValueError, match="exactly match"):
        build_result_matrix(
            evaluation_cells=_evaluation_cell_set((_agent(),)),
            task_check_refs=(TaskCheckRef("future-task", "future-check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            results=(),
            matrix_role="selected",
            join_config=ResultJoinConfig(),
        )


def test_build_result_matrix_rejects_unsupported_historical_role() -> None:
    with pytest.raises(ValueError, match="matrix_role"):
        build_result_matrix(
            evaluation_cells=_evaluation_cell_set((_agent(),)),
            task_check_refs=(TaskCheckRef("task", "check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            results=(),
            matrix_role="historical",
            join_config=ResultJoinConfig(),
        )


def _result(
    agent: AgentRecord | None = None, workspace_run: WorkspaceRunRecord | None = None
):
    task = _task()
    check = _check()
    selected_agent = agent or _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(
        task, check, selected_agent, _workspace_config(), _runtime_config()
    )
    return build_result_record(
        task,
        check,
        selected_agent,
        workspace_run or _workspace_run(agent_id=selected_agent.agent_id),
        identity,
        scoring_config,
    )


def _evaluation_cell_set(
    agents: tuple[AgentRecord, ...],
    *,
    results: tuple[ResultRecord, ...] = (),
) -> EvaluationCellSet:
    selected_ref = TaskCheckRef("task", "check")
    future_ref = TaskCheckRef("future-task", "future-check")
    result_by_agent = {result.agent_id: result for result in results}
    cells = []
    for agent in agents:
        identity = compute_result_cache_identity(
            _task(), _check(), agent, _workspace_config(), _runtime_config()
        )
        result = result_by_agent.get(agent.agent_id)
        cells.append(
            ResultCellRef(
                agent_id=agent.agent_id,
                task_id="task",
                check_id="check",
                required_identity_digest=identity.identity_digest,
                result_id=result.result_id if result is not None else None,
                result_digest=result.result_digest if result is not None else None,
                cell_state="result" if result is not None else "missing",
                exclusion_reason=None,
                outcome=result.outcome if result is not None else None,
            )
        )
    cells.append(
        ResultCellRef(
            agent_id=agents[0].agent_id,
            task_id="future-task",
            check_id="future-check",
            required_identity_digest="future-required-identity",
            result_id=None,
            result_digest=None,
            cell_state="missing",
            exclusion_reason=None,
        )
    )
    cell_set = EvaluationCellSet(
        cell_set_id="cell-set",
        origin_id="origin",
        selection_id="selection",
        selected_task_check_refs=(selected_ref,),
        future_task_check_refs=(future_ref,),
        future_censored_task_check_refs=(),
        future_task_pool_id="task-pool",
        future_task_pool_digest="task-pool-digest",
        cells=tuple(cells),
        abstention_reason=None,
        cell_set_digest="",
    )
    return record_with_digest(cell_set)


def _task() -> TaskRecord:
    task_text = "Fix the issue."
    solver_material_refs = ("README.md",)
    return TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit="a" * 40,
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-02T00:00:00Z",
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=("check",),
        dependency_cluster_id="dependency-cluster",
        sampling_stratum="stratum",
    )


def _check(check_id: str = "check", task_id: str = "task") -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="pytest",
        check_manifest_digest="check-manifest",
        hidden_check_bundle_digest="hidden-bundle",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at="2026-01-02T00:00:00Z",
    )


def _agent(agent_id: str = "agent", manifest: str = "agent-manifest") -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=manifest,
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
        base_image_digest="image",
        dependency_lock_digest="lock",
    )


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id="runtime",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        timeout_seconds=5,
        hardware_profile_digest=None,
    )


def _workspace_run(
    agent_id: str = "agent",
    terminal_status: str = "passed",
    check_outcome: str = "pass",
    invalid_owner: str | None = None,
    failure_label: str | None = None,
    usage: dict[str, int | str] | None = None,
) -> WorkspaceRunRecord:
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace-run-{canonical_digest((agent_id, terminal_status, check_outcome, failure_label))}",
        task_id="task",
        check_id="check",
        agent_id=agent_id,
        solver_workspace_digest="solver-workspace",
        verifier_workspace_digest="verifier-workspace",
        terminal_status=terminal_status,
        diff_digest="diff",
        replay_status="applied",
        check_outcome=check_outcome,
        invalid_owner=invalid_owner,
        failure_label=failure_label,
        usage={"input_tokens": 1, "output_tokens": 0} if usage is None else usage,
        latency={
            "workspace_seconds": 5.0,
            "agent_seconds": 2.0,
            "verification_seconds": 1.0,
            "solver_checkout_seconds": 0.5,
            "verifier_checkout_seconds": 0.5,
            "diff_replay_seconds": 0.25,
            "cleanup_seconds": 0.25,
        },
        started_at="2026-01-04T00:00:00Z",
        finished_at="2026-01-04T00:00:05Z",
    )


def _scoring_config() -> ScoringConfig:
    return ScoringConfig(
        pricing_version="test-pricing",
        cost_rates={"input_tokens": 0.001, "output_tokens": 0.005},
    )
