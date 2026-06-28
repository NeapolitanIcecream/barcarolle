from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from barcarolle import runner as runner_module
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    RollingOriginRecord,
    RuntimeConfig,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    load_jsonl_records,
    record_with_digest,
    task_check_ref_key,
    write_jsonl_records,
)
from barcarolle.result_store import (
    ResultCacheConfig,
    ResultJoinConfig,
    ResultQuery,
    ResultStore,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    load_results,
    store_result,
)
from barcarolle.runner import (
    ReportConfig,
    TaskPoolConfig,
    build_task_pool,
    evaluate_selector,
    fill_results,
    prepare_evaluation_cells,
    score_selection,
    write_report,
)
from barcarolle.selection import FeatureConfig, MetricConfig, RollingOriginPolicy, SelectionConfig, SelectorEvaluationConfig
from barcarolle.task_pool import TaskSourceConfig, TimeRange


def test_build_task_pool_writes_resolvable_task_and_check_refs(tmp_path: Path) -> None:
    task_ref = tmp_path / "tasks.jsonl"
    check_ref = tmp_path / "checks.jsonl"
    config = TaskPoolConfig(
        repository_url_or_path="repo",
        time_range=TimeRange("2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"),
        task_source_config=TaskSourceConfig("user_import", (_candidate_event(),)),
        metadata={
            "task_records_ref": str(task_ref),
            "check_records_ref": str(check_ref),
            "created_at": "2026-02-01T00:00:00Z",
        },
    )

    task_pool = build_task_pool(config)
    tasks = tuple(load_jsonl_records(task_ref, TaskRecord))
    checks = tuple(load_jsonl_records(check_ref, CheckRecord))

    assert task_pool.task_ids == tuple(task.task_id for task in tasks)
    assert task_pool.check_ids == tuple(check.check_id for check in checks)
    assert task_pool.task_records_digest == canonical_digest(tasks)
    assert task_pool.check_records_digest == canonical_digest(checks)
    assert task_pool.rejected_candidate_ids == ()


def test_fill_results_runs_only_missing_agent_task_check_cells(tmp_path: Path, monkeypatch) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    store_result(_result(task, check, agent, workspace_config, runtime_config, scoring_config), store)
    task_pool = _task_pool((task,), (check,))
    selection = _selection(task_pool, TaskCheckRef(task.task_id, check.check_id))
    calls: list[str] = []

    def fake_run_agent_on_task(task_arg, check_arg, agent_arg, workspace_config_arg, runtime_config_arg):
        calls.append(agent_arg.agent_id)
        return _workspace_run(task_arg, check_arg, agent_arg)

    monkeypatch.setattr("barcarolle.runner.workspace_module.run_agent_on_task", fake_run_agent_on_task)

    new_results = fill_results(
        selection,
        task_pool,
        (task,),
        {check.check_id: check},
        (agent, other_agent),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
    )

    assert calls == ("other-agent",) or calls == ["other-agent"]
    assert tuple(result.agent_id for result in new_results) == ("other-agent",)
    assert {result.agent_id for result in load_results(store, ResultQuery())} == {"agent", "other-agent"}


def test_prepare_evaluation_cells_and_score_selection_keep_selected_future_linkage(tmp_path: Path, monkeypatch) -> None:
    selected_task = _task("selected-task", "selected-check", certified_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", certified_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", certified_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", certified_at="2026-01-07T00:00:00Z")
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    for task, check in ((selected_task, selected_check), (future_task, future_check)):
        store_result(_result(task, check, agent, workspace_config, runtime_config, scoring_config), store)
    task_pool = _task_pool((selected_task, future_task), (selected_check, future_check))
    selected_ref = TaskCheckRef("selected-task", "selected-check")
    future_ref = TaskCheckRef("future-task", "future-check")
    selection = _selection(task_pool, selected_ref)
    origin = _origin(task_pool, selected_ref, future_ref)

    def fail_if_workspace_runs(*args, **kwargs):
        raise AssertionError("all selected and future cells should come from cache")

    monkeypatch.setattr("barcarolle.runner.workspace_module.run_agent_on_task", fail_if_workspace_runs)

    cell_set = prepare_evaluation_cells(
        selection,
        origin,
        task_pool,
        (selected_task, future_task),
        {"selected-check": selected_check, "future-check": future_check},
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig("join", "denominator"),
    )
    scored_cell_set, selected_matrix, future_matrix, metrics = score_selection(
        selection,
        origin,
        task_pool,
        (selected_task, future_task),
        {"selected-check": selected_check, "future-check": future_check},
        (agent,),
        cell_set,
        store,
        ResultJoinConfig("join", "denominator"),
        MetricConfig("metric", "budget"),
    )

    assert scored_cell_set == cell_set
    assert selected_matrix.matrix_role == "selected"
    assert future_matrix.matrix_role == "future_holdout"
    assert selected_matrix.task_check_refs == (selected_ref,)
    assert future_matrix.task_check_refs == (future_ref,)
    assert {metric.selected_matrix_digest for metric in metrics} == {selected_matrix.matrix_digest}
    assert {metric.future_matrix_digest for metric in metrics} == {future_matrix.matrix_digest}


def test_score_selection_uses_result_ids_frozen_in_evaluation_cells(tmp_path: Path) -> None:
    selected_task = _task("selected-task", "selected-check", certified_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", certified_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", certified_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", certified_at="2026-01-07T00:00:00Z")
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    selected_pass = _result(selected_task, selected_check, agent, workspace_config, runtime_config, scoring_config)
    future_pass = _result(future_task, future_check, agent, workspace_config, runtime_config, scoring_config)
    store_result(selected_pass, store)
    store_result(future_pass, store)
    task_pool = _task_pool((selected_task, future_task), (selected_check, future_check))
    selected_ref = TaskCheckRef("selected-task", "selected-check")
    future_ref = TaskCheckRef("future-task", "future-check")
    selection = _selection(task_pool, selected_ref)
    origin = _origin(task_pool, selected_ref, future_ref)
    cell_set = prepare_evaluation_cells(
        selection,
        origin,
        task_pool,
        (selected_task, future_task),
        {"selected-check": selected_check, "future-check": future_check},
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig("join", "denominator"),
    )
    selected_fail = _result(
        selected_task,
        selected_check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
        outcome="fail",
    )
    store_result(selected_fail, store)

    _, selected_matrix, _, _ = score_selection(
        selection,
        origin,
        task_pool,
        (selected_task, future_task),
        {"selected-check": selected_check, "future-check": future_check},
        (agent,),
        cell_set,
        store,
        ResultJoinConfig("join", "denominator"),
        MetricConfig("metric", "budget"),
    )

    assert selected_pass.result_id != selected_fail.result_id
    assert selected_matrix.cells[0].result_id == selected_pass.result_id
    assert selected_matrix.cells[0].result_digest == selected_pass.result_digest
    assert selected_matrix.cells[0].outcome == "pass"


def test_evaluate_selector_does_not_open_post_origin_results_before_freeze(tmp_path: Path, monkeypatch) -> None:
    selected_task = _task("selected-task", "selected-check", certified_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", certified_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", certified_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", certified_at="2026-01-07T00:00:00Z")
    task_ref = tmp_path / "tasks.jsonl"
    check_ref = tmp_path / "checks.jsonl"
    write_jsonl_records(task_ref, (selected_task, future_task))
    write_jsonl_records(check_ref, (selected_check, future_check))
    task_pool = record_with_digest(
        TaskPoolRecord(
            task_pool_id="task-pool",
            task_pool_digest="",
            repository_id="repo",
            task_ids=("selected-task", "future-task"),
            check_ids=("selected-check", "future-check"),
            task_records_ref=str(task_ref),
            task_records_digest=canonical_digest((selected_task, future_task)),
            check_records_ref=str(check_ref),
            check_records_digest=canonical_digest((selected_check, future_check)),
            rejected_candidate_ids=("rejected",),
            rejection_summary_digest="rejection-summary",
            certification_evidence_digest="certification",
            source_event_inventory_digest="source-events",
            generator_config_digest="generator",
            certification_config_digest="certification-config",
            created_at="2026-01-03T00:00:00Z",
        )
    )
    agent = _agent()
    pre_origin_result = record_with_digest(
            replace(
                _result(selected_task, selected_check, agent, _workspace_config(), _runtime_config(), _scoring_config()),
                started_at="2026-01-03T00:00:00Z",
                finished_at="2026-01-03T00:00:05Z",
                result_available_at="2026-01-04T00:00:00Z",
                result_digest="",
            )
    )
    freeze_called = False
    pre_freeze_queries = []

    class StopAfterFreeze(Exception):
        pass

    def fake_load_results(store, query):
        if not freeze_called:
            pre_freeze_queries.append(query)
            return (pre_origin_result,)
        return ()

    def fake_freeze(*args, **kwargs):
        nonlocal freeze_called
        freeze_called = True
        raise StopAfterFreeze

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fake_load_results)
    monkeypatch.setattr(runner_module.selection_module, "freeze_evaluation_selections", fake_freeze)

    with pytest.raises(StopAfterFreeze):
        evaluate_selector(
            _selector(),
            task_pool,
            (agent,),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                "evaluation",
                ("2026-01-05T00:00:00Z",),
                SelectionConfig("selection", "selector", "placeholder", "recency"),
            ),
            RollingOriginPolicy("policy", "origin_time", "P0D", "clusters", "recency", "disjoint", True),
            FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
            ResultStore(tmp_path / "results.jsonl"),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig("join", "denominator"),
            MetricConfig("metric", "evaluation"),
        )

    assert freeze_called
    assert pre_freeze_queries
    assert all(query.result_available_before <= "2026-01-05T00:00:00Z" for query in pre_freeze_queries)
    assert pre_freeze_queries[0].task_ids == ("selected-task",)
    assert pre_freeze_queries[0].check_ids == ("selected-check",)


def test_write_report_writes_human_and_machine_summaries(tmp_path: Path) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    result = _result(task, check, agent, _workspace_config(), _runtime_config(), _scoring_config())
    task_pool = _task_pool((task,), (check,))

    summary = write_report(
        task_pool,
        (),
        (result,),
        (),
        (),
        (),
        ReportConfig(tmp_path, agents=(agent,)),
    )

    markdown_path = Path(summary["report_paths"]["markdown"])
    json_path = Path(summary["report_paths"]["json"])
    assert markdown_path.exists()
    assert json_path.exists()
    assert summary["section_ids"] == ("task_pool", "agent_results", "selector_performance", "claim_boundary")
    assert "task_pool_digest" in markdown_path.read_text(encoding="utf-8")


def _candidate_event() -> dict[str, object]:
    evidence_keys = (
        "checkout_valid",
        "dependencies_restored",
        "check_executable",
        "oracle_stable",
        "solver_visible_boundary",
        "hidden_material_separated",
        "statement_clear",
    )
    return {
        "candidate_id": "candidate",
        "repository_id": "repo",
        "base_commit": "commit",
        "source_ref": "issue-1",
        "source_resolved_at": "2026-01-05T00:00:00Z",
        "task_material_available_at": "2026-01-05T00:00:00Z",
        "check_material_available_at": "2026-01-05T00:00:00Z",
        "solver_material_refs": ("path:statement.md",),
        "solver_material_digest": "solver-material",
        "cluster_id": "cluster",
        "statement_material": {"title": "Fix bug", "body": "Make the test pass."},
        "check_manifest_digest": "check-manifest",
        "hidden_check_bundle_digest": "hidden-bundle",
        "verifier_image_digest": "image",
        "verifier_deps_digest": "deps",
        "resource_limits": {"timeout_seconds": 30},
        "oracle_source": "private",
        "check_type": "tests",
        "certification_evidence": {key: True for key in evidence_keys},
    }


def _task(task_id: str = "task", check_id: str = "check", certified_at: str = "2026-01-02T00:00:00Z") -> TaskRecord:
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="commit",
        source_family="user_import",
        source_ref=f"source-{task_id}",
        source_resolved_at=certified_at,
        task_material_available_at=certified_at,
        certified_at=certified_at,
        solver_material_digest=f"solver-{task_id}",
        solver_material_refs=(f"path:{task_id}.md",),
        check_ids=(check_id,),
        cluster_id="cluster",
    )


def _check(check_id: str = "check", task_id: str = "task", certified_at: str = "2026-01-02T00:00:00Z") -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="tests",
        check_manifest_digest=f"manifest-{check_id}",
        hidden_check_bundle_digest=f"hidden-{check_id}",
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private",
        check_material_available_at=certified_at,
        certified_at=certified_at,
    )


def _agent(agent_id: str = "agent", manifest: str = "agent-manifest") -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=manifest,
        model_snapshot_id="model",
        harness_digest=f"harness-{agent_id}",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _selector() -> SelectorRecord:
    return SelectorRecord(
        selector_id="selector",
        selector_family="recency",
        selector_version="1",
        training_source_digests=("training",),
        allowed_feature_classes=("task_metadata",),
        config_digest="selector-config",
        created_at="2026-01-04T00:00:00Z",
    )


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig("workspace", "checkout", "submodules", "image", "deps")


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig("runtime", "budget", "retry", "stochastic", 30, None)


def _scoring_config() -> ScoringConfig:
    return ScoringConfig("scoring", "test", "reported", {"input_tokens": 0.01})


def _workspace_run(task: TaskRecord, check: CheckRecord, agent: AgentRecord, outcome: str = "pass") -> WorkspaceRunRecord:
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace-run-{task.task_id}-{check.check_id}-{agent.agent_id}-{outcome}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest="solver-workspace",
        verifier_workspace_digest="verifier-workspace",
        terminal_status="passed" if outcome == "pass" else "failed",
        diff_digest="diff",
        replay_status="applied",
        check_outcome=outcome,
        invalid_owner=None,
        failure_label=None,
        usage={"input_tokens": 10},
        started_at="2026-01-10T00:00:00Z",
        finished_at="2026-01-10T00:00:05Z",
    )


def _result(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
    outcome: str = "pass",
):
    identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config, scoring_config)
    return build_result_record(task, check, agent, _workspace_run(task, check, agent, outcome), identity, scoring_config)


def _task_pool(tasks: tuple[TaskRecord, ...], checks: tuple[CheckRecord, ...]) -> TaskPoolRecord:
    record = TaskPoolRecord(
        task_pool_id="task-pool",
        task_pool_digest="",
        repository_id="repo",
        task_ids=tuple(task.task_id for task in tasks),
        check_ids=tuple(check.check_id for check in checks),
        task_records_ref="tasks.jsonl",
        task_records_digest=canonical_digest(tasks),
        check_records_ref="checks.jsonl",
        check_records_digest=canonical_digest(checks),
        rejected_candidate_ids=("rejected",),
        rejection_summary_digest="rejection-summary",
        certification_evidence_digest="certification",
        source_event_inventory_digest="source-events",
        generator_config_digest="generator",
        certification_config_digest="certification-config",
        created_at="2026-01-03T00:00:00Z",
    )
    return record_with_digest(record)


def _selection(task_pool: TaskPoolRecord, ref: TaskCheckRef) -> BenchmarkSelectionRecord:
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id="origin",
        selector_id="selector",
        selected_task_check_refs=(ref,),
        selected_weights={task_check_ref_key(ref): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode="recency",
        exposure_state="frozen",
        exposed_at=None,
        exposure_scope_digest=None,
        created_at="2026-01-05T00:00:00Z",
        selection_digest="",
    )
    return record_with_digest(selection)


def _origin(task_pool: TaskPoolRecord, selected_ref: TaskCheckRef, future_ref: TaskCheckRef) -> RollingOriginRecord:
    return RollingOriginRecord(
        origin_id="origin",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time="2026-01-05T00:00:00Z",
        policy_digest="policy",
        history_task_check_refs=(selected_ref,),
        future_holdout_task_check_refs=(future_ref,),
        as_of_cutoff="2026-01-05T00:00:00Z",
        embargo="P0D",
        cluster_constraints_digest="clusters",
        eligibility_mode="recency",
        holdout_overlap_policy="disjoint",
    )
