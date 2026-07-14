from dataclasses import replace
from pathlib import Path

import pytest

from barcarolle import result_store as result_store_module

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    EvaluationCellSet,
    ResultCellRef,
    ResultRecord,
    RuntimeConfig,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
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
    resolve_result_cells,
    store_result,
)


def test_build_result_record_stores_complete_identity_status_cost_and_latency() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config)
    workspace_run = _workspace_run(usage={"input_tokens": 100, "output_tokens": 20, "harness_requests": 1})

    result = build_result_record(task, check, agent, workspace_run, identity, scoring_config)

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
    assert result.verifier_metadata_digest


def test_pricing_change_reuses_paid_execution_and_can_recompute_cost(tmp_path: Path) -> None:
    store = ResultStore(tmp_path / "results.jsonl")
    result = _result()
    store_result(result, store)
    changed_pricing = replace(
        _scoring_config(),
        scoring_config_digest="scoring:v2",
        pricing_version="test-pricing-v2",
        cost_rates={"input_tokens": 0.01, "output_tokens": 0.02},
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
    )

    assert cells[0].cell_state == "result"
    assert cells[0].result_id == result.result_id
    assert compute_cost(result.usage, changed_pricing)["total_cost"] == 0.01


def test_unknown_usage_cost_is_null_not_zero() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = replace(_scoring_config(), usage_coverage="unknown")
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

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


def test_build_result_record_uses_utc_instants_for_result_availability(monkeypatch: pytest.MonkeyPatch) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())
    workspace_run = replace(
        _workspace_run(),
        started_at="2026-01-01T07:00:00-03:00",
        finished_at="2026-01-01T08:00:00-03:00",
    )
    monkeypatch.setattr(result_store_module, "_now", lambda: "2026-01-01T10:30:00Z")

    result = build_result_record(task, check, agent, workspace_run, identity, scoring_config)

    assert result.result_available_at == "2026-01-01T11:00:00.000000Z"


def test_build_result_record_rejects_identity_or_workspace_linkage_mismatch() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

    with pytest.raises(ValueError, match="workspace_run agent"):
        build_result_record(task, check, agent, _workspace_run(agent_id="other-agent"), identity, scoring_config)

    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    other_identity = compute_result_cache_identity(task, check, other_agent, _workspace_config(), _runtime_config())
    with pytest.raises(ValueError, match="cache identity"):
        build_result_record(task, check, agent, _workspace_run(), other_identity, scoring_config)


def test_build_result_record_rejects_stale_check_execution_identity() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())
    changed_check = replace(check, resource_limits={"timeout_seconds": 10})

    with pytest.raises(ValueError, match="check_digest"):
        build_result_record(task, changed_check, agent, _workspace_run(), identity, scoring_config)


def test_build_result_record_rejects_non_numeric_priced_usage() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

    with pytest.raises(ValueError, match="finite and nonnegative"):
        build_result_record(
            task,
            check,
            agent,
            _workspace_run(usage={"input_tokens": 1, "output_tokens": "unknown"}),
            identity,
            scoring_config,
        )


@pytest.mark.parametrize("usage_coverage", ("reported", "complete"))
def test_build_result_record_requires_every_priced_key_for_measured_usage(usage_coverage: str) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = replace(_scoring_config(), usage_coverage=usage_coverage)
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

    with pytest.raises(ValueError, match=rf"{usage_coverage} usage is missing priced keys: output_tokens"):
        build_result_record(
            task,
            check,
            agent,
            _workspace_run(usage={"input_tokens": 1}),
            identity,
            scoring_config,
        )


def test_build_result_record_rejects_unrepresentable_usage_cost_without_overflow() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

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
def test_build_result_record_classifies_runtime_termination_as_agent_invalid(terminal_status: str) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())

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


def test_build_result_record_excludes_baseline_check_failure_as_benchmark_invalid() -> None:
    task = _task()
    check = _check()
    agent = _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, agent, _workspace_config(), _runtime_config())
    workspace_run = _workspace_run(
        terminal_status="invalid",
        check_outcome="invalid",
        invalid_owner="benchmark",
        failure_label="baseline_check_passed_without_diff",
    )

    result = build_result_record(task, check, agent, workspace_run, identity, scoring_config)

    assert result.scoreable_state == "benchmark_invalid"
    assert result.outcome == "invalid"
    assert result.invalid_owner == "benchmark"


def test_store_result_is_append_only_and_load_results_filters(tmp_path: Path) -> None:
    result = _result()
    store = ResultStore(tmp_path / "results.jsonl")

    stored = store_result(result, store)
    same = store_result(result, store)
    loaded = load_results(store, ResultQuery(agent_ids=("agent",), cache_identity_digests=(result.cache_identity.identity_digest,)))

    assert stored == result
    assert same == result
    assert loaded == (result,)
    assert store.path.read_text(encoding="utf-8").count("\n") == 1

    conflict = record_with_digest(replace(result, result_digest="", failure_label="changed"))
    with pytest.raises(ValueError, match="different digest"):
        store_result(conflict, store)


def test_load_results_excludes_post_cutoff_result_with_earlier_offset_date(tmp_path: Path) -> None:
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


def test_resolve_result_cells_uses_first_valid_exact_identity_result(tmp_path: Path) -> None:
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
    assert cells[0].result_id == first.result_id
    assert cells[0].result_digest == first.result_digest
    assert cells[0].outcome == "pass"


def test_resolve_result_cells_does_not_reuse_benchmark_invalid_result_by_default(tmp_path: Path) -> None:
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


def test_resolve_result_cells_keeps_agent_invalid_result_reusable(tmp_path: Path) -> None:
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


def test_resolve_result_cells_misses_when_check_execution_config_changes(tmp_path: Path) -> None:
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


def test_find_missing_results_returns_only_cells_without_exact_reusable_identity(tmp_path: Path) -> None:
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
            checks={"other-check": _check(check_id="other-check", task_id="other-task")},
            agents=(_agent(),),
            workspace_config=_workspace_config(),
            runtime_config=_runtime_config(),
            store=ResultStore(tmp_path / "results.jsonl"),
            cache_config=ResultCacheConfig(),
        )


def test_build_result_matrix_joins_selected_cells_and_marks_missing_denominator() -> None:
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
        join_config=ResultJoinConfig("join", "denominator"),
    )

    assert validate_result_matrix(matrix).ok
    assert matrix.scoreable_state == "abstained"
    assert matrix.abstention_reason == "missing_required_results"
    assert {(cell.agent_id, cell.cell_state) for cell in matrix.cells} == {
        ("agent", "result"),
        ("other-agent", "missing"),
    }


def test_build_result_matrix_excludes_benchmark_invalid_result_with_traceability() -> None:
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
    cell_set = _evaluation_cell_set((agent, other_agent), results=(result, invalid_result))

    matrix = build_result_matrix(
        evaluation_cells=cell_set,
        task_check_refs=(TaskCheckRef("task", "check"),),
        tasks=(_task(),),
        checks={"check": _check()},
        agents=(agent, other_agent),
        results=(result, invalid_result),
        matrix_role="selected",
        join_config=ResultJoinConfig("join", "denominator"),
    )

    excluded = {cell.agent_id: cell for cell in matrix.cells if cell.cell_state == "excluded"}
    assert validate_result_matrix(matrix).ok
    assert matrix.scoreable_state == "complete_with_exclusions"
    assert matrix.abstention_reason is None
    assert set(excluded) == {"agent", "other-agent"}
    assert excluded["agent"].result_id == result.result_id
    assert excluded["agent"].result_digest == result.result_digest
    assert excluded["other-agent"].result_id == invalid_result.result_id
    assert excluded["other-agent"].result_digest == invalid_result.result_digest
    assert excluded["agent"].exclusion_reason == excluded["other-agent"].exclusion_reason
    assert excluded["agent"].exclusion_reason.startswith("task_check_infrastructure_failure:check_launch_error:")


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
        join_config=ResultJoinConfig("join", "denominator"),
    )

    assert len(matrix.cells) == 1
    assert matrix.cells[0].result_id == frozen_fail.result_id
    assert matrix.cells[0].result_digest == frozen_fail.result_digest
    assert matrix.cells[0].outcome == "fail"


def test_build_result_matrix_rejects_task_check_refs_that_do_not_match_role_subset() -> None:
    with pytest.raises(ValueError, match="exactly match"):
        build_result_matrix(
            evaluation_cells=_evaluation_cell_set((_agent(),)),
            task_check_refs=(TaskCheckRef("future-task", "future-check"),),
            tasks=(_task(),),
            checks={"check": _check()},
            agents=(_agent(),),
            results=(),
            matrix_role="selected",
            join_config=ResultJoinConfig("join", "denominator"),
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
            join_config=ResultJoinConfig("join", "denominator"),
        )


def _result(agent: AgentRecord | None = None, workspace_run: WorkspaceRunRecord | None = None):
    task = _task()
    check = _check()
    selected_agent = agent or _agent()
    scoring_config = _scoring_config()
    identity = compute_result_cache_identity(task, check, selected_agent, _workspace_config(), _runtime_config())
    return build_result_record(task, check, selected_agent, workspace_run or _workspace_run(agent_id=selected_agent.agent_id), identity, scoring_config)


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
        identity = compute_result_cache_identity(_task(), _check(), agent, _workspace_config(), _runtime_config())
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
        cells=tuple(cells),
        abstention_reason=None,
        cell_set_digest="",
    )
    return record_with_digest(cell_set)


def _task() -> TaskRecord:
    return TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit="commit",
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-02T00:00:00Z",
        certified_at="2026-01-03T00:00:00Z",
        solver_material_digest="solver-material",
        solver_material_refs=("README.md",),
        check_ids=("check",),
        cluster_id="cluster",
    )


def _check(check_id: str = "check", task_id: str = "task") -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="pytest",
        check_manifest_digest="check-manifest",
        hidden_check_bundle_digest="hidden-bundle",
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at="2026-01-02T00:00:00Z",
        certified_at="2026-01-03T00:00:00Z",
    )


def _agent(agent_id: str = "agent", manifest: str = "agent-manifest") -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=manifest,
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
        started_at="2026-01-04T00:00:00Z",
        finished_at="2026-01-04T00:00:05Z",
    )


def _scoring_config() -> ScoringConfig:
    return ScoringConfig(
        scoring_config_digest="scoring",
        pricing_version="test-pricing",
        usage_coverage="reported",
        cost_rates={"input_tokens": 0.001, "output_tokens": 0.005},
    )
