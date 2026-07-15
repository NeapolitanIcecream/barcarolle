from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import pytest

from barcarolle import runner as runner_module
from barcarolle.cli import main as cli_main
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    MetricRecord,
    RollingOriginRecord,
    RuntimeConfig,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_solver_material_digest,
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
    select_benchmark,
    train_selector,
    write_report,
)
from barcarolle.selection import (
    FeatureConfig,
    MetricConfig,
    RollingOriginPolicy,
    SelectionBudget,
    SelectionConfig,
    SelectorEvaluationConfig,
    SelectorTrainingConfig,
)
from barcarolle.task_pool import TaskSourceConfig, TimeRange
from barcarolle.workspace import CapturedDiff


def test_build_task_pool_executes_validation_and_writes_resolvable_records(tmp_path: Path) -> None:
    task_ref = tmp_path / "tasks.jsonl"
    check_ref = tmp_path / "checks.jsonl"
    evidence_ref = tmp_path / "certification-evidence.jsonl"
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Tests")
    (repository / "value.txt").write_text("broken\n", encoding="utf-8")
    _git(repository, "add", "value.txt")
    _git(repository, "commit", "--quiet", "-m", "base")
    base_commit = _git(repository, "rev-parse", "HEAD").stdout.strip()
    hidden_material = tmp_path / "private-check.txt"
    hidden_material.write_text("private\n", encoding="utf-8")
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "ok = Path('value.txt').read_text() == 'fixed\\n'; "
        "private = Path('.barcarolle/check_bundle').read_text() == 'private\\n'; "
        "raise SystemExit(0 if ok and private else 1)",
    )
    patch_text = (
        "diff --git a/value.txt b/value.txt\n"
        "--- a/value.txt\n"
        "+++ b/value.txt\n"
        "@@ -1 +1 @@\n"
        "-broken\n"
        "+fixed\n"
    )
    reference_patch = CapturedDiff(patch_text, hashlib.sha256(patch_text.encode()).hexdigest())
    workspace_config = WorkspaceConfig(
        "workspace",
        canonical_digest({"repository": str(repository)}),
        "submodules",
        "image",
        "deps",
    )
    candidate = _candidate_event(
        base_commit=base_commit,
        solver_material_refs=(),
        check_manifest_digest=canonical_digest({"check_command": check_command}),
        hidden_check_bundle_digest=hashlib.sha256(hidden_material.read_bytes()).hexdigest(),
    )
    config = TaskPoolConfig(
        repository_id="repo",
        repository_path=repository,
        workspace_config=workspace_config,
        runtime_config=_runtime_config(),
        reference_patches={"candidate": reference_patch},
        check_commands={"candidate": check_command},
        hidden_material_paths={"candidate": hidden_material},
        time_range=TimeRange("2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"),
        task_source_config=TaskSourceConfig("user_import", (candidate,)),
        metadata={
            "task_records_ref": str(task_ref),
            "check_records_ref": str(check_ref),
            "certification_evidence_ref": str(evidence_ref),
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
    evidence = tuple(json.loads(line) for line in evidence_ref.read_text(encoding="utf-8").splitlines())
    assert evidence[0]["accepted"] is True
    assert task_pool.certification_evidence_digest == canonical_digest(evidence)


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


def test_fill_results_reprices_cached_execution_without_rerunning_agent(tmp_path: Path, monkeypatch) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.01})
    current_pricing = ScoringConfig("current-pricing", {"input_tokens": 0.02})
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(runner_module.result_store_module, "_now", lambda: "2026-01-15T00:00:00Z")
    old_result = _result(task, check, agent, workspace_config, runtime_config, old_pricing)
    store_result(old_result, store)
    task_pool = _task_pool((task,), (check,))
    selection = _selection(task_pool, TaskCheckRef(task.task_id, check.check_id))

    def fail_if_agent_runs(*args, **kwargs):
        raise AssertionError("a pricing change must not rerun paid execution")

    monkeypatch.setattr("barcarolle.runner.workspace_module.run_agent_on_task", fail_if_agent_runs)
    monkeypatch.setattr(runner_module.result_store_module, "_now", lambda: "2026-02-01T00:00:00Z")

    repriced = fill_results(
        selection,
        task_pool,
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        current_pricing,
        ResultCacheConfig(),
        store,
    )

    assert len(repriced) == 1
    current_result = repriced[0]
    assert current_result.result_id != old_result.result_id
    assert current_result.scoring_config_digest == current_pricing.scoring_config_digest
    assert current_result.pricing_version == "current-pricing"
    assert current_result.cost == {"input_tokens_cost": 0.2, "total_cost": 0.2}
    assert current_result.usage == old_result.usage
    assert current_result.outcome == old_result.outcome
    assert current_result.diff_digest == old_result.diff_digest
    assert current_result.verifier_metadata_digest == old_result.verifier_metadata_digest
    assert current_result.result_available_at == old_result.result_available_at

    cells = runner_module.result_store_module.resolve_result_cells(
        (TaskCheckRef(task.task_id, check.check_id),),
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        store,
        ResultCacheConfig(),
        current_pricing,
    )
    assert cells[0].result_id == current_result.result_id
    assert cells[0].result_digest == current_result.result_digest

    assert fill_results(
        selection,
        task_pool,
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        current_pricing,
        ResultCacheConfig(),
        store,
    ) == ()
    assert load_results(store, ResultQuery()) == (old_result, current_result)


def test_result_id_is_stable_when_repricing_from_a_repriced_result(monkeypatch) -> None:
    original = _result(
        _task(),
        _check(),
        _agent(),
        _workspace_config(),
        _runtime_config(),
        ScoringConfig("old-pricing", {"input_tokens": 0.01}),
    )
    middle_pricing = ScoringConfig("middle-pricing", {"input_tokens": 0.02})
    final_pricing = ScoringConfig("final-pricing", {"input_tokens": 0.03})
    monkeypatch.setattr(runner_module.result_store_module, "_now", lambda: "2026-02-01T00:00:00Z")
    middle = runner_module.result_store_module._reprice_result(original, middle_pricing)
    direct_final = runner_module.result_store_module._reprice_result(original, final_pricing)
    chained_final = runner_module.result_store_module._reprice_result(middle, final_pricing)

    assert direct_final.result_id == chained_final.result_id


def test_train_selector_loads_only_allowed_history_results(tmp_path: Path, monkeypatch) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))
    agent = _agent()
    queries = []

    def fake_load_results(store, query):
        queries.append(query)
        return ()

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fake_load_results)

    selector = train_selector(
        task_pool,
        (agent,),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
        (),
        SelectorTrainingConfig("training"),
        RollingOriginPolicy("policy", "origin_time", "clusters", "recency", "disjoint", False),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
        ResultStore(tmp_path / "results.jsonl"),
    )

    assert selector.selector_family == "recency"
    assert queries[0].task_ids == ("task",)
    assert queries[0].check_ids == ("check",)
    assert queries[0].agent_ids == ("agent",)
    assert queries[0].result_available_before.startswith("2026-01-05T00:00:00")


def test_pre_origin_results_count_repricing_once_and_distinct_executions_separately(
    tmp_path: Path,
    monkeypatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.01})
    current_pricing = ScoringConfig("current-pricing", {"input_tokens": 0.02})
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(runner_module.result_store_module, "_now", lambda: "2026-01-12T00:00:00Z")
    identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config)
    original = build_result_record(
        task,
        check,
        agent,
        _workspace_run(task, check, agent),
        identity,
        old_pricing,
    )
    store_result(original, store)
    repriced = runner_module.result_store_module.reprice_cached_results(
        (TaskCheckRef(task.task_id, check.check_id),),
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        store,
        ResultCacheConfig(),
        current_pricing,
    )[0]
    distinct_workspace_run = replace(
        _workspace_run(task, check, agent),
        workspace_run_id="workspace-run-distinct",
    )
    distinct_result = build_result_record(
        task,
        check,
        agent,
        distinct_workspace_run,
        identity,
        current_pricing,
    )
    store_result(distinct_result, store)

    pre_origin_results = runner_module._load_results_for_refs(
        store,
        (TaskCheckRef(task.task_id, check.check_id),),
        (agent,),
        result_available_after="2026-01-01T00:00:00Z",
        result_available_before="2026-01-20T00:00:00Z",
    )
    task_pool = _task_pool((task,), (check,))
    ref = TaskCheckRef(task.task_id, check.check_id)
    origin = replace(
        _origin(task_pool, ref, ref),
        origin_time="2026-01-20T00:00:00Z",
        as_of_cutoff="2026-01-20T00:00:00Z",
    )
    snapshot = runner_module.selection_module.build_feature_snapshot(
        origin,
        task_pool,
        (task,),
        {check.check_id: check},
        pre_origin_results,
        FeatureConfig(
            "features",
            "leakage",
            ("pre_origin_result_count",),
            ("pre_origin_result",),
        ),
    )

    assert repriced.result_id not in {result.result_id for result in pre_origin_results}
    assert tuple(result.result_id for result in pre_origin_results) == (
        original.result_id,
        distinct_result.result_id,
    )
    assert runner_module.result_store_module.result_execution_digest(original) == (
        runner_module.result_store_module.result_execution_digest(repriced)
    )
    assert runner_module.result_store_module.result_execution_digest(original) != (
        runner_module.result_store_module.result_execution_digest(distinct_result)
    )
    assert original.verifier_metadata_digest != distinct_result.verifier_metadata_digest
    assert snapshot.feature_records[0].value == 2
    assert runner_module._load_results_for_refs(
        store,
        (TaskCheckRef(task.task_id, check.check_id),),
        (agent,),
        result_available_after="2026-01-13T00:00:00Z",
        result_available_before="2026-01-20T00:00:00Z",
    ) == ()


def test_select_benchmark_loads_only_allowed_pre_origin_results_and_appends_selection(tmp_path: Path, monkeypatch) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))
    agent = _agent()
    pre_origin_result = record_with_digest(
        replace(
            _result(task, check, agent, _workspace_config(), _runtime_config(), _scoring_config()),
            started_at="2026-01-03T00:00:00Z",
            finished_at="2026-01-03T00:00:05Z",
            result_available_at="2026-01-04T00:00:00Z",
            result_digest="",
        )
    )
    queries = []

    def fake_load_results(store, query):
        queries.append(query)
        return (pre_origin_result,)

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fake_load_results)

    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget("budget", 1),
        _selector(),
        SelectionConfig("selection", "selector", "placeholder", "recency"),
        RollingOriginPolicy("policy", "origin_time", "clusters", "recency", "disjoint", False),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
        ResultStore(tmp_path / "results.jsonl"),
    )

    logged = load_jsonl_records(tmp_path / "selections.jsonl", BenchmarkSelectionRecord)
    assert queries[0].task_ids == ("task",)
    assert queries[0].check_ids == ("check",)
    assert queries[0].agent_ids == ("agent",)
    assert queries[0].result_available_before.startswith("2026-01-05T00:00:00")
    assert logged == [selection]


def test_select_benchmark_rejects_cutoff_after_origin_before_loading_results(tmp_path: Path, monkeypatch) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))

    def fail_if_results_are_loaded(*args, **kwargs):
        raise AssertionError("future cutoff must be rejected before loading results")

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fail_if_results_are_loaded)

    with pytest.raises(ValueError, match="must not be after origin_time"):
        select_benchmark(
            task_pool,
            (_agent(),),
            datetime(2026, 1, 5, tzinfo=UTC),
            SelectionBudget("budget", 1),
            _selector(),
            SelectionConfig("selection", "selector", "placeholder", "recency"),
            RollingOriginPolicy(
                "policy",
                "2026-01-06T00:00:00Z",
                "clusters",
                "recency",
                "disjoint",
                False,
            ),
            FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
            ResultStore(tmp_path / "results.jsonl"),
        )


def test_prepare_evaluation_cells_and_score_selection_keep_selected_future_linkage(tmp_path: Path, monkeypatch) -> None:
    selected_task = _task("selected-task", "selected-check", available_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", available_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", available_at="2026-01-07T00:00:00Z")
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.005})
    store = ResultStore(tmp_path / "results.jsonl")
    for task, check in ((selected_task, selected_check), (future_task, future_check)):
        store_result(_result(task, check, agent, workspace_config, runtime_config, old_pricing), store)
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
    bound_results = load_results(
        store,
        ResultQuery(result_ids=tuple(cell.result_id for cell in cell_set.cells if cell.result_id is not None)),
    )
    assert {result.scoring_config_digest for result in bound_results} == {scoring_config.scoring_config_digest}
    assert {metric.selected_matrix_digest for metric in metrics} == {selected_matrix.matrix_digest}
    assert {metric.future_matrix_digest for metric in metrics} == {future_matrix.matrix_digest}
    logged_metrics = load_jsonl_records(store.path.with_name("metrics.jsonl"), MetricRecord)
    assert tuple(metric.metric_id for metric in logged_metrics) == tuple(metric.metric_id for metric in metrics)


def test_score_selection_uses_result_ids_frozen_in_evaluation_cells(tmp_path: Path) -> None:
    selected_task = _task("selected-task", "selected-check", available_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", available_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", available_at="2026-01-07T00:00:00Z")
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


@pytest.mark.parametrize(
    ("origin_times", "message"),
    (
        ((), "must not be empty"),
        (
            ("2026-01-05T00:00:00Z", "2026-01-04T19:00:00-05:00"),
            "must be strictly increasing UTC instants",
        ),
        (
            ("2026-01-06T00:00:00Z", "2026-01-05T00:00:00Z"),
            "must be strictly increasing UTC instants",
        ),
    ),
)
def test_evaluate_selector_rejects_invalid_origin_schedule_before_writes(
    tmp_path: Path,
    monkeypatch,
    origin_times: tuple[str, ...],
    message: str,
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))
    result_store = ResultStore(tmp_path / "results.jsonl")

    def fail_if_results_are_loaded(*args, **kwargs):
        raise AssertionError("invalid origin schedules must be rejected before result queries")

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fail_if_results_are_loaded)

    with pytest.raises(ValueError, match=message):
        evaluate_selector(
            _selector(),
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=origin_times,
                selection_config=SelectionConfig("selection", "selector", "placeholder", "recency"),
                budget=SelectionBudget("eval-budget", 1),
            ),
            RollingOriginPolicy("policy", "origin_time", "clusters", "recency", "disjoint", True),
            FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
            result_store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig("join", "denominator"),
            MetricConfig("metric", "evaluation"),
        )

    assert not (tmp_path / "selections.jsonl").exists()
    assert not (tmp_path / "metrics.jsonl").exists()
    assert not result_store.path.exists()


def test_evaluate_selector_assigns_each_future_task_to_one_origin(tmp_path: Path, monkeypatch) -> None:
    history_task = _task("history-task", "history-check", available_at="2026-01-02T00:00:00Z")
    first_future_task = _task("first-future-task", "first-future-check", available_at="2026-01-06T00:00:00Z")
    boundary_task = _task("boundary-task", "boundary-check", available_at="2026-01-07T00:00:00Z")
    second_future_task = _task("second-future-task", "second-future-check", available_at="2026-01-08T00:00:00Z")
    history_check = _check("history-check", "history-task", available_at="2026-01-02T00:00:00Z")
    first_future_check = _check(
        "first-future-check",
        "first-future-task",
        available_at="2026-01-06T00:00:00Z",
    )
    boundary_check = _check(
        "boundary-check",
        "boundary-task",
        available_at="2026-01-07T00:00:00Z",
    )
    second_future_check = _check(
        "second-future-check",
        "second-future-task",
        available_at="2026-01-08T00:00:00Z",
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (history_task, first_future_task, boundary_task, second_future_task),
        (history_check, first_future_check, boundary_check, second_future_check),
    )

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        lambda task, check, agent, workspace_config, runtime_config: _workspace_run(task, check, agent),
    )

    selections, cell_sets, _, _ = evaluate_selector(
        _selector(),
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z", "2026-01-07T00:00:00Z"),
            selection_config=SelectionConfig("selection", "selector", "placeholder", "recency"),
            budget=SelectionBudget("eval-budget", 1),
        ),
        RollingOriginPolicy("policy", "origin_time", "clusters", "recency", "disjoint", True),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
        ResultStore(tmp_path / "results.jsonl"),
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig("join", "denominator"),
        MetricConfig("metric", "evaluation"),
    )

    assert tuple(cell_set.future_task_check_refs for cell_set in cell_sets) == (
        (
            TaskCheckRef("first-future-task", "first-future-check"),
            TaskCheckRef("boundary-task", "boundary-check"),
        ),
        (TaskCheckRef("second-future-task", "second-future-check"),),
    )
    assert selections[1].selected_task_check_refs == (
        TaskCheckRef("boundary-task", "boundary-check"),
    )


def test_evaluate_selector_does_not_open_post_origin_results_before_freeze(tmp_path: Path, monkeypatch) -> None:
    selected_task = _task("selected-task", "selected-check", available_at="2026-01-02T00:00:00Z")
    future_task = _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z")
    selected_check = _check("selected-check", "selected-task", available_at="2026-01-02T00:00:00Z")
    future_check = _check("future-check", "future-task", available_at="2026-01-07T00:00:00Z")
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
            certification_evidence_ref=str(tmp_path / "certification-evidence.jsonl"),
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
    captured_selector_inputs = []

    class StopAfterSelectionAppend(Exception):
        pass

    def fake_load_results(store, query):
        if not freeze_called:
            pre_freeze_queries.append(query)
            return (pre_origin_result,)
        return ()

    def fake_freeze(selector, task_pool_arg, tasks, checks, selector_inputs, agents, history_window, selection_config, rolling_policy):
        nonlocal freeze_called
        freeze_called = True
        selector_input = selector_inputs[0]
        captured_selector_inputs.append(selector_input)
        return (
            _selection_for_origin(
                task_pool_arg,
                selector_input.eligible_task_check_refs[0],
                selector_input.origin_id,
                selector_input.budget_digest,
                selector_input.feature_snapshot_id,
            ),
        )

    def fake_prepare(selection, *args, **kwargs):
        logged = load_jsonl_records(tmp_path / "selections.jsonl", BenchmarkSelectionRecord)
        assert logged == [selection]
        raise StopAfterSelectionAppend

    monkeypatch.setattr(runner_module.result_store_module, "load_results", fake_load_results)
    monkeypatch.setattr(runner_module.selection_module, "freeze_evaluation_selections", fake_freeze)
    monkeypatch.setattr(runner_module, "prepare_evaluation_cells", fake_prepare)

    with pytest.raises(StopAfterSelectionAppend):
        evaluate_selector(
            _selector(),
            task_pool,
            (agent,),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00.500000Z",),
                selection_config=SelectionConfig("selection", "selector", "placeholder", "recency"),
                budget=SelectionBudget("eval-budget", 7),
            ),
            RollingOriginPolicy("policy", "origin_time", "clusters", "recency", "disjoint", True),
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
    assert all(query.result_available_before <= "2026-01-05T00:00:00.500000Z" for query in pre_freeze_queries)
    assert pre_freeze_queries[0].task_ids == ("selected-task",)
    assert pre_freeze_queries[0].check_ids == ("selected-check",)
    assert captured_selector_inputs[0].budget_digest == "eval-budget"
    assert captured_selector_inputs[0].selection_budget_limit == 7
    assert captured_selector_inputs[0].origin_as_of_cutoff == "2026-01-05T00:00:00.500000Z"


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

    report_paths = summary["report_paths"]
    assert isinstance(report_paths, dict)
    markdown_path = Path(report_paths["markdown"])
    json_path = Path(report_paths["json"])
    assert markdown_path.exists()
    assert json_path.exists()
    assert summary["section_ids"] == ("task_pool", "agent_results", "selector_performance", "claim_boundary")
    assert "task_pool_digest" in markdown_path.read_text(encoding="utf-8")


def test_report_cli_reads_relative_jsonl_paths_and_writes_reports(tmp_path: Path, capsys) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool((task,), (check,))
    records = tmp_path / "records"
    write_jsonl_records(records / "task_pool.jsonl", (task_pool,))
    config_path = tmp_path / "report.json"
    config_path.write_text(
        canonical_json(
            {
                "task_pool": "records/task_pool.jsonl",
                "output_dir": "published",
            }
        ),
        encoding="utf-8",
    )

    assert cli_main(("report", str(config_path))) == 0

    assert (tmp_path / "published" / "report.md").exists()
    assert (tmp_path / "published" / "report.json").exists()
    assert '"section_ids"' in capsys.readouterr().out


def _candidate_event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "candidate_id": "candidate",
        "repository_id": "repo",
        "base_commit": "commit",
        "source_ref": "issue-1",
        "source_resolved_at": "2026-01-05T00:00:00Z",
        "task_material_available_at": "2026-01-05T00:00:00Z",
        "check_material_available_at": "2026-01-05T00:00:00Z",
        "task_text": "Fix the bug and make the test pass.",
        "solver_material_refs": (),
        "cluster_id": "cluster",
        "check_manifest_digest": "check-manifest",
        "hidden_check_bundle_digest": "hidden-bundle",
        "resource_limits": {"timeout_seconds": 30},
        "oracle_source": "private",
        "check_type": "tests",
    }
    event.update(overrides)
    return event


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _task(task_id: str = "task", check_id: str = "check", available_at: str = "2026-01-02T00:00:00Z") -> TaskRecord:
    task_text = f"Task {task_id}"
    solver_material_refs = (f"path:{task_id}.md",)
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="commit",
        source_family="user_import",
        source_ref=f"source-{task_id}",
        source_resolved_at=available_at,
        task_material_available_at=available_at,
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(task_text, solver_material_refs),
        solver_material_refs=solver_material_refs,
        check_ids=(check_id,),
        cluster_id="cluster",
    )


def _check(check_id: str = "check", task_id: str = "task", available_at: str = "2026-01-02T00:00:00Z") -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="tests",
        check_manifest_digest=f"manifest-{check_id}",
        hidden_check_bundle_digest=f"hidden-{check_id}",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private",
        check_material_available_at=available_at,
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
    parameters = {}
    return SelectorRecord(
        selector_id="selector",
        selector_family="recency",
        selector_version="1",
        training_source_digests=("training",),
        allowed_feature_classes=("task_metadata",),
        parameters=parameters,
        config_digest=canonical_digest(
            {"selector_family": "recency", "parameters": parameters}
        ),
        created_at="2026-01-04T00:00:00Z",
    )


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig("workspace", "checkout", "submodules", "image", "deps")


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig("runtime", "budget", "retry", "stochastic", 30, None)


def _scoring_config() -> ScoringConfig:
    return ScoringConfig("test", {"input_tokens": 0.01})


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
    identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config)
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
        certification_evidence_ref="certification-evidence.jsonl",
        rejected_candidate_ids=("rejected",),
        rejection_summary_digest="rejection-summary",
        certification_evidence_digest="certification",
        source_event_inventory_digest="source-events",
        generator_config_digest="generator",
        certification_config_digest="certification-config",
        created_at="2026-01-03T00:00:00Z",
    )
    return record_with_digest(record)


def _task_pool_with_refs(tmp_path: Path, tasks: tuple[TaskRecord, ...], checks: tuple[CheckRecord, ...]) -> TaskPoolRecord:
    task_ref = tmp_path / "tasks.jsonl"
    check_ref = tmp_path / "checks.jsonl"
    write_jsonl_records(task_ref, tasks)
    write_jsonl_records(check_ref, checks)
    return record_with_digest(
        replace(
            _task_pool(tasks, checks),
            task_records_ref=str(task_ref),
            check_records_ref=str(check_ref),
            task_pool_digest="",
        )
    )


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


def _selection_for_origin(
    task_pool: TaskPoolRecord,
    ref: TaskCheckRef,
    origin_id: str,
    budget_digest: str,
    feature_snapshot_id: str,
) -> BenchmarkSelectionRecord:
    return record_with_digest(
        replace(
            _selection(task_pool, ref),
            origin_id=origin_id,
            budget_digest=budget_digest,
            feature_snapshot_id=feature_snapshot_id,
            selection_digest="",
        )
    )


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
        cluster_constraints_digest="clusters",
        eligibility_mode="recency",
        holdout_overlap_policy="disjoint",
    )
