from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
import subprocess
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    CheckRecord,
    RuntimeConfig,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_data,
    canonical_digest,
    load_jsonl_records,
    make_solver_material_digest,
    record_with_digest,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultCacheConfig,
    ResultStore,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    store_result,
)
from barcarolle.workspace import (  # noqa: E402
    WorkspaceRunContext,
    WorkspaceRunResult,
)
from examples.experiment_ledger import (  # noqa: E402
    append_ledger_event,
    ledger_events_path,
    load_ledger_events,
    load_resource_ledger,
    write_json,
)
from examples.pylint_swe_bench_verified.replicate_campaign import (  # noqa: E402
    ReplicateCampaignContext,
    continue_replicate_campaign_after_retained_agent_invalid,
    initialize_replicate_campaign_ledger,
    preflight_replicate_campaign,
    reauthorize_stopped_replicate_campaign_call,
    run_next_replicate_campaign_cell,
)
from examples.pylint_swe_bench_verified import replicate_campaign_cli  # noqa: E402
from examples.pylint_swe_bench_verified.replicate_schedule import (  # noqa: E402
    ReplicateSchedule,
    build_replicate_schedule,
    build_single_agent_canary_schedule,
    find_next_missing_replicate_schedule_cell,
    resolve_replicate_schedule_cells,
    validate_replicate_schedule,
)


CAMPAIGN_ID = "pylint-replicates-2026-08"


def test_single_agent_canary_schedule_is_one_exact_replayable_cell() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    task_id = tasks[3].task_id
    canary_agent = (agents[0],)

    schedule = build_single_agent_canary_schedule(
        task_pool,
        tasks,
        checks,
        canary_agent,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=20260725,
        task_id=task_id,
    )

    assert schedule.schema_version == "single_agent_canary_schedule_v1"
    assert schedule.replicate_count == 1
    assert schedule.replicated_task_ids == ()
    assert len(schedule.runtime_configs) == 1
    assert len(schedule.cells) == 1
    assert schedule.cells[0].task_id == task_id
    assert schedule.cells[0].agent_id == canary_agent[0].agent_id
    assert validate_replicate_schedule(
        schedule,
        task_pool,
        tasks,
        checks,
        canary_agent,
        runtime,
    ).ok


def test_replicate_schedule_is_deterministic_stratified_and_paired() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()

    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=20260722,
        replicate_fraction=0.20,
        replicate_count=3,
    )
    reordered = build_replicate_schedule(
        task_pool,
        tuple(reversed(tasks)),
        tuple(reversed(checks)),
        tuple(reversed(agents)),
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=20260722,
        replicate_fraction=0.20,
        replicate_count=3,
    )

    assert schedule == reordered
    schedule_payload = canonical_data(schedule)
    del schedule_payload["schedule_digest"]
    assert schedule.schedule_digest == canonical_digest(schedule_payload)
    assert validate_replicate_schedule(
        schedule, task_pool, tasks, checks, agents, runtime
    ).ok
    assert schedule.actual_replicate_fraction == 0.20
    assert len(schedule.replicated_task_ids) == 2
    strata = {task.task_id: task.sampling_stratum for task in tasks}
    assert Counter(strata[task_id] for task_id in schedule.replicated_task_ids) == {
        "easy": 1,
        "medium": 1,
    }
    assert len(schedule.cells) == 28
    assert tuple(cell.sequence_index for cell in schedule.cells) == tuple(range(28))

    cells_by_block: dict[int, list] = defaultdict(list)
    for cell in schedule.cells:
        cells_by_block[cell.block_index].append(cell)
    assert len(cells_by_block) == 14
    for block_cells in cells_by_block.values():
        assert len(block_cells) == 2
        assert {cell.agent_id for cell in block_cells} == {
            agent.agent_id for agent in agents
        }
        assert tuple(cell.within_block_index for cell in block_cells) == (0, 1)
        assert len({cell.task_id for cell in block_cells}) == 1
        assert len({cell.replicate_index for cell in block_cells}) == 1
    assert {
        tuple(cell.agent_id for cell in block_cells)
        for block_cells in cells_by_block.values()
    } == {
        ("agent-high", "agent-low"),
        ("agent-low", "agent-high"),
    }

    counts_by_task = Counter(cell.task_id for cell in schedule.cells)
    assert all(
        counts_by_task[task.task_id]
        == (6 if task.task_id in schedule.replicated_task_ids else 2)
        for task in tasks
    )


def test_replicate_runtime_slots_are_exact_identity_inputs() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=7,
        replicate_fraction=0.20,
        replicate_count=3,
    )

    assert len(schedule.runtime_configs) == 3
    assert len({config.runtime_config_id for config in schedule.runtime_configs}) == 3
    assert (
        len({config.stochastic_settings_digest for config in schedule.runtime_configs})
        == 3
    )
    assert all(
        config.budget_digest == runtime.budget_digest
        for config in schedule.runtime_configs
    )
    assert all(
        cell.runtime_config_digest
        == canonical_digest(schedule.runtime_configs[cell.replicate_index])
        for cell in schedule.cells
    )
    assert all(
        cell.runtime_config_id
        == schedule.runtime_configs[cell.replicate_index].runtime_config_id
        for cell in schedule.cells
    )


def test_replicate_schedule_resolution_preserves_order_and_runtime_identity(
    tmp_path: Path,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=7,
        replicate_fraction=0.20,
        replicate_count=3,
    )
    workspace = _workspace_config()

    resolved = resolve_replicate_schedule_cells(
        schedule,
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        workspace,
        ResultStore(tmp_path / "results.jsonl"),
        ResultCacheConfig(),
    )

    assert tuple(item.schedule_cell for item in resolved) == schedule.cells
    assert all(item.result_cell.cell_state == "missing" for item in resolved)
    task_by_id = {task.task_id: task for task in tasks}
    check_by_id = {check.check_id: check for check in checks}
    agent_by_id = {agent.agent_id: agent for agent in agents}
    for item in resolved:
        cell = item.schedule_cell
        identity = compute_result_cache_identity(
            task_by_id[cell.task_id],
            check_by_id[cell.check_id],
            agent_by_id[cell.agent_id],
            workspace,
            schedule.runtime_configs[cell.replicate_index],
        )
        assert item.result_cell.required_identity_digest == identity.identity_digest


def test_replicate_schedule_resume_selects_only_first_exact_missing_cell(
    tmp_path: Path,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=13,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    workspace = _workspace_config()
    store = ResultStore(tmp_path / "results.jsonl")
    first = schedule.cells[0]
    store_result(
        _result_for_schedule_cell(
            first,
            schedule,
            tasks,
            checks,
            agents,
            workspace,
        ),
        store,
    )

    next_missing = find_next_missing_replicate_schedule_cell(
        schedule,
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        workspace,
        store,
        ResultCacheConfig(),
    )

    assert next_missing is not None
    assert next_missing.schedule_cell == schedule.cells[1]
    assert next_missing.result_cell.cell_state == "missing"


def test_replicate_schedule_resolution_rejects_drift_before_store_access(
    tmp_path: Path,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=17,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    tampered = record_with_digest(
        replace(schedule, cells=schedule.cells[:-1], schedule_digest=""),
        "schedule_digest",
    )
    store = ResultStore(tmp_path / "results.jsonl")

    with pytest.raises(ValueError, match="does not replay"):
        resolve_replicate_schedule_cells(
            tampered,
            task_pool,
            tasks,
            checks,
            agents,
            runtime,
            _workspace_config(),
            store,
            ResultCacheConfig(),
        )

    assert not store.path.exists()


def test_replicate_schedule_replay_rejects_tampering_and_scope_drift() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=11,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    tampered = record_with_digest(
        replace(schedule, cells=schedule.cells[:-1], schedule_digest=""),
        "schedule_digest",
    )

    assert not validate_replicate_schedule(
        tampered, task_pool, tasks, checks, agents, runtime
    ).ok
    changed_seed = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=12,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    assert changed_seed.schedule_digest != schedule.schedule_digest

    unresolved = replace(
        agents[0],
        requested_model_id="moving-alias",
        model_snapshot_id=None,
        model_resolution_scope_id="another-campaign",
        model_resolution_scope_started_at="2026-08-01T00:00:00Z",
        model_resolution_scope_ended_at="2026-09-01T00:00:00Z",
    )
    with pytest.raises(ValueError, match="scope must equal"):
        build_replicate_schedule(
            task_pool,
            tasks,
            checks,
            (unresolved, agents[1]),
            runtime,
            campaign_id=CAMPAIGN_ID,
            seed=11,
            replicate_fraction=0.20,
            replicate_count=2,
        )


@pytest.mark.parametrize(
    ("replicate_fraction", "replicate_count", "error"),
    (
        (0.19, 3, "between 0.20 and 0.30"),
        (0.31, 3, "between 0.20 and 0.30"),
        (0.25, 1, "must be 2 or 3"),
        (0.25, 2.0, "must be 2 or 3"),
        (0.25, 4, "must be 2 or 3"),
    ),
)
def test_replicate_schedule_rejects_invalid_protocol_parameters(
    replicate_fraction: float,
    replicate_count: int | float,
    error: str,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()

    with pytest.raises(ValueError, match=error):
        build_replicate_schedule(
            task_pool,
            tasks,
            checks,
            agents,
            runtime,
            campaign_id=CAMPAIGN_ID,
            seed=1,
            replicate_fraction=replicate_fraction,
            replicate_count=replicate_count,  # type: ignore[arg-type]
        )


def test_replicate_schedule_requires_string_campaign_id() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()

    with pytest.raises(ValueError, match="campaign_id must be a nonempty string"):
        build_replicate_schedule(
            task_pool,
            tasks,
            checks,
            agents,
            runtime,
            campaign_id=True,  # type: ignore[arg-type]
            seed=1,
            replicate_fraction=0.20,
            replicate_count=2,
        )


def test_replicate_schedule_requires_distinct_agent_configurations() -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    duplicate_treatment = replace(agents[0], agent_id="agent-copy")

    with pytest.raises(ValueError, match="two distinct Agent configurations"):
        build_replicate_schedule(
            task_pool,
            tasks,
            checks,
            (agents[0], duplicate_treatment),
            runtime,
            campaign_id=CAMPAIGN_ID,
            seed=1,
            replicate_fraction=0.20,
            replicate_count=2,
        )


def test_replicate_schedule_rejects_task_count_without_valid_fraction() -> None:
    _, tasks, checks, agents, runtime = _inputs()
    tasks = tasks[:3]
    checks = checks[:3]
    task_pool = _task_pool(tasks, checks)

    with pytest.raises(ValueError, match="cannot realize"):
        build_replicate_schedule(
            task_pool,
            tasks,
            checks,
            agents,
            runtime,
            campaign_id=CAMPAIGN_ID,
            seed=1,
            replicate_fraction=0.25,
            replicate_count=2,
        )


def test_replicate_schedule_cli_writes_strict_replayable_artifact(
    tmp_path: Path,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    task_pool_path = tmp_path / "task-pool.jsonl"
    tasks_path = tmp_path / "tasks.jsonl"
    checks_path = tmp_path / "checks.jsonl"
    agents_path = tmp_path / "agents.jsonl"
    runtime_path = tmp_path / "runtime.jsonl"
    output_path = tmp_path / "replicate-schedule.jsonl"
    write_jsonl_records(task_pool_path, (task_pool,))
    write_jsonl_records(tasks_path, tasks)
    write_jsonl_records(checks_path, checks)
    write_jsonl_records(agents_path, agents)
    write_jsonl_records(runtime_path, (runtime,))
    command = (
        sys.executable,
        "examples/pylint_swe_bench_verified/replicate_schedule.py",
        "--task-pool",
        str(task_pool_path),
        "--tasks",
        str(tasks_path),
        "--checks",
        str(checks_path),
        "--agents",
        str(agents_path),
        "--runtime-config",
        str(runtime_path),
        "--output",
        str(output_path),
        "--campaign-id",
        CAMPAIGN_ID,
        "--seed",
        "20260722",
        "--replicate-fraction",
        "0.20",
        "--replicate-count",
        "3",
    )

    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (schedule,) = load_jsonl_records(output_path, ReplicateSchedule)

    assert completed.returncode == 0
    assert "wrote 28 cells" in completed.stdout
    assert validate_replicate_schedule(
        schedule, task_pool, tasks, checks, agents, runtime
    ).ok
    repeated = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert repeated.returncode != 0
    assert "refusing to overwrite schedule" in repeated.stderr


def test_replicate_campaign_ledger_binds_authority_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    context = _campaign_context(tmp_path)

    ledger = _initialize_campaign_ledger(context)

    assert ledger["authorization"] == {
        "approved_at": "2026-07-22T00:00:00Z",
        "scope": "paired replicate test campaign",
        "campaign_id": context.schedule.campaign_id,
        "schedule_digest": context.schedule.schedule_digest,
        "task_pool_id": context.task_pool.task_pool_id,
        "task_pool_digest": context.task_pool.task_pool_digest,
        "agent_records_digest": context.schedule.agent_records_digest,
        "workspace_config_digest": canonical_digest(context.workspace_config),
        "base_runtime_config_digest": canonical_digest(context.base_runtime_config),
        "endpoint_digest": "endpoint-digest",
        "credential_variables": ["OPENAI_BASE_URL", "OPENAI_API_KEY"],
        "budget_usd": 10.0,
    }
    assert ledger["limits"] == {
        "maximum_paid_calls": len(context.schedule.cells),
        "maximum_estimated_cost_per_call_usd": 1.0,
        "cell_retries": 0,
    }
    assert ledger["pricing"] == {
        "pricing_version": context.scoring_config.pricing_version,
        "scoring_config_digest": context.scoring_config.scoring_config_digest,
        "cost_rates": dict(context.scoring_config.cost_rates),
        "sources": ["https://example.test/pricing"],
        "accounting_basis": "test price schedule",
    }
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        _initialize_campaign_ledger(context)


def test_replicate_campaign_rejects_total_budget_below_per_call_limit(
    tmp_path: Path,
) -> None:
    context = _campaign_context(tmp_path)

    with pytest.raises(ValueError, match="per-call.*must not exceed"):
        initialize_replicate_campaign_ledger(
            context,
            approved_at="2026-07-22T00:00:00Z",
            endpoint_digest="endpoint-digest",
            maximum_estimated_cost_usd=0.5,
            maximum_estimated_cost_per_call_usd=1.0,
            pricing_sources=("https://example.test/pricing",),
            accounting_basis="test price schedule",
            scope="paired replicate test campaign",
        )


@pytest.mark.parametrize(
    ("override", "message"),
    (
        ({"approved_at": 1}, "approved_at"),
        ({"endpoint_digest": 1}, "endpoint_digest"),
        ({"pricing_sources": "https://example.test/pricing"}, "pricing_sources"),
        ({"pricing_sources": (1,)}, "pricing_sources"),
        ({"accounting_basis": 1}, "accounting_basis"),
        ({"scope": 1}, "scope"),
    ),
)
def test_replicate_campaign_rejects_malformed_authority_before_writing(
    tmp_path: Path,
    override: dict[str, object],
    message: str,
) -> None:
    context = _campaign_context(tmp_path)
    arguments: dict[str, object] = {
        "approved_at": "2026-07-22T00:00:00Z",
        "endpoint_digest": "endpoint-digest",
        "maximum_estimated_cost_usd": 10.0,
        "maximum_estimated_cost_per_call_usd": 1.0,
        "pricing_sources": ("https://example.test/pricing",),
        "accounting_basis": "test price schedule",
        "scope": "paired replicate test campaign",
    }
    arguments.update(override)

    with pytest.raises(ValueError, match=message):
        initialize_replicate_campaign_ledger(context, **cast(Any, arguments))

    assert not context.ledger_path.exists()
    assert not ledger_events_path(context.ledger_path).exists()


def test_replicate_campaign_stops_before_unfunded_next_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    initialize_replicate_campaign_ledger(
        context,
        approved_at="2026-07-22T00:00:00Z",
        endpoint_digest="endpoint-digest",
        maximum_estimated_cost_usd=0.0015,
        maximum_estimated_cost_per_call_usd=0.001,
        pricing_sources=("https://example.test/pricing",),
        accounting_basis="test price schedule",
        scope="paired replicate test campaign",
    )
    _stub_campaign_preflight(monkeypatch)
    executed = _stub_successful_campaign_run(monkeypatch, context)

    first = run_next_replicate_campaign_cell(context)

    assert first is not None
    assert first.cost["total_cost"] == pytest.approx(0.001)
    with pytest.raises(RuntimeError, match="cannot cover one authorized call"):
        preflight_replicate_campaign(context)
    ledger = load_resource_ledger(
        context.ledger_path,
        updated_at="2026-07-22T00:00:02Z",
    )
    limits = ledger["limits"]
    calls = ledger["calls"]
    assert isinstance(limits, dict)
    assert isinstance(calls, list)
    assert ledger["remaining_usd"] == pytest.approx(0.0005)
    assert limits["maximum_estimated_cost_per_call_usd"] == pytest.approx(0.001)
    assert len(calls) == 1
    assert executed == [0]


def test_replicate_campaign_stops_after_result_exceeds_per_call_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    initialize_replicate_campaign_ledger(
        context,
        approved_at="2026-07-22T00:00:00Z",
        endpoint_digest="endpoint-digest",
        maximum_estimated_cost_usd=0.01,
        maximum_estimated_cost_per_call_usd=0.0005,
        pricing_sources=("https://example.test/pricing",),
        accounting_basis="test price schedule",
        scope="paired replicate test campaign",
    )
    _stub_campaign_preflight(monkeypatch)
    executed = _stub_successful_campaign_run(monkeypatch, context)

    with pytest.raises(RuntimeError, match="exceeds the per-call cost limit"):
        run_next_replicate_campaign_cell(context)
    with pytest.raises(RuntimeError, match="stopped paid cell"):
        run_next_replicate_campaign_cell(context)
    ledger = load_resource_ledger(
        context.ledger_path,
        updated_at="2026-07-22T00:00:02Z",
    )
    calls = ledger["calls"]
    assert isinstance(calls, list)
    call = calls[0]
    assert isinstance(call, dict)
    assert call["state"] == "stopped"
    assert call["estimated_cost_usd"] == pytest.approx(0.001)
    assert ledger["remaining_usd"] == pytest.approx(0.009)
    assert executed == [0]


def test_replicate_campaign_reauthorizes_exact_cost_stop_without_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    initialize_replicate_campaign_ledger(
        context,
        approved_at="2026-07-22T00:00:00Z",
        endpoint_digest="endpoint-digest",
        maximum_estimated_cost_usd=0.01,
        maximum_estimated_cost_per_call_usd=0.0005,
        pricing_sources=("https://example.test/pricing",),
        accounting_basis="test price schedule",
        scope="paired replicate test campaign",
    )
    _stub_campaign_preflight(monkeypatch)
    executed = _stub_successful_campaign_run(monkeypatch, context)

    with pytest.raises(RuntimeError, match="exceeds the per-call cost limit"):
        run_next_replicate_campaign_cell(context)

    ledger = reauthorize_stopped_replicate_campaign_call(
        context,
        source_amendment_digest="study-amendment-digest",
        approved_at="2026-07-22T00:00:02Z",
        reason="cost-only operational amendment",
        new_maximum_estimated_cost_per_call_usd=0.002,
    )
    event_count = len(load_ledger_events(ledger_events_path(context.ledger_path)))
    repeated = reauthorize_stopped_replicate_campaign_call(
        context,
        source_amendment_digest="study-amendment-digest",
        approved_at="2026-07-22T00:00:02Z",
        reason="cost-only operational amendment",
        new_maximum_estimated_cost_per_call_usd=0.002,
    )
    next_cell = preflight_replicate_campaign(context)

    assert next_cell is not None
    assert next_cell.schedule_cell.sequence_index == 1
    assert executed == [0]
    assert len(load_ledger_events(ledger_events_path(context.ledger_path))) == event_count
    assert repeated["campaign_authority_digest"] == ledger["campaign_authority_digest"]
    amendment = ledger["authority_amendment"]
    calls = ledger["calls"]
    limits = ledger["limits"]
    assert isinstance(amendment, dict)
    assert isinstance(calls, list)
    assert isinstance(limits, dict)
    assert amendment["source_amendment_digest"] == "study-amendment-digest"
    assert amendment["old_maximum_estimated_cost_per_call_usd"] == pytest.approx(
        0.0005
    )
    assert amendment["new_maximum_estimated_cost_per_call_usd"] == pytest.approx(
        0.002
    )
    assert limits["maximum_estimated_cost_per_call_usd"] == pytest.approx(0.002)
    assert calls[0]["state"] == "completed"
    assert calls[0]["stop_reason"] == "RuntimeError"
    assert calls[0]["reauthorized_after_stop"] == {
        "authority_amendment_digest": amendment["authority_amendment_digest"],
        "reauthorized_at": "2026-07-22T00:00:02Z",
    }


def test_replicate_campaign_retains_one_agent_availability_failure_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    executed: list[int] = []

    def invalid_run(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        run_context,
        artifact_config,
    ):
        del workspace_config, run_context, artifact_config
        cell = next(
            candidate
            for candidate in context.schedule.cells
            if candidate.task_id == task.task_id
            and candidate.check_id == check.check_id
            and candidate.agent_id == agent.agent_id
            and candidate.runtime_config_id == runtime_config.runtime_config_id
        )
        executed.append(cell.sequence_index)
        return WorkspaceRunResult(
            replace(
                _workspace_run_for_schedule_cell(cell, task, check, agent),
                terminal_status="error",
                check_outcome="invalid",
                invalid_owner=None,
                failure_label="agent_failed",
                usage={},
            )
        )

    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "run_agent_on_task_with_artifacts",
        invalid_run,
    )
    with pytest.raises(RuntimeError, match="not scoreable"):
        run_next_replicate_campaign_cell(context)

    ledger = continue_replicate_campaign_after_retained_agent_invalid(
        context,
        source_amendment_digest="continuation-study-amendment",
        approved_at="2026-07-22T00:00:02Z",
        reason="retain one provider availability failure",
    )
    event_count = len(load_ledger_events(ledger_events_path(context.ledger_path)))
    repeated = continue_replicate_campaign_after_retained_agent_invalid(
        context,
        source_amendment_digest="continuation-study-amendment",
        approved_at="2026-07-22T00:00:02Z",
        reason="retain one provider availability failure",
    )
    next_cell = preflight_replicate_campaign(context)

    assert next_cell is not None
    assert next_cell.schedule_cell.sequence_index == 1
    assert executed == [0]
    assert len(load_ledger_events(ledger_events_path(context.ledger_path))) == event_count
    assert repeated["campaign_authority_digest"] == ledger["campaign_authority_digest"]
    continuation = ledger["continuation_amendment"]
    calls = ledger["calls"]
    assert isinstance(continuation, dict)
    assert isinstance(calls, list)
    assert continuation["source_amendment_digest"] == (
        "continuation-study-amendment"
    )
    assert calls[0]["state"] == "completed"
    assert calls[0]["scoreable_state"] == "agent_invalid"
    assert calls[0]["reauthorized_after_stop"] == {
        "authority_amendment_digest": continuation[
            "continuation_amendment_digest"
        ],
        "reauthorized_at": "2026-07-22T00:00:02Z",
    }
    with pytest.raises(RuntimeError, match="different continuation"):
        continue_replicate_campaign_after_retained_agent_invalid(
            context,
            source_amendment_digest="another-amendment",
            approved_at="2026-07-22T00:00:03Z",
            reason="must not allow a second retained invalid",
        )


def test_replicate_campaign_rejects_authority_drift_before_result_store_access(
    tmp_path: Path,
) -> None:
    context = _campaign_context(tmp_path)
    ledger = _initialize_campaign_ledger(context)
    authorization_value = ledger["authorization"]
    assert isinstance(authorization_value, dict)
    authorization = dict(authorization_value)
    authorization["schedule_digest"] = "tampered"
    write_json(context.ledger_path, {**ledger, "authorization": authorization})

    with pytest.raises(RuntimeError, match="authority digest"):
        preflight_replicate_campaign(context)

    assert not context.result_store.path.exists()


def test_replicate_campaign_preflight_covers_all_remaining_runtime_slots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    observed: list[tuple[str, str, str, str]] = []
    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "resolve_openai_endpoint_digest",
        lambda *, require_api_key: "endpoint-digest",
    )

    def record_preflight(run_context, plans, workspace_config, runtime_config):
        del run_context, workspace_config
        observed.extend(
            (
                task.task_id,
                check.check_id,
                agent.agent_id,
                runtime_config.runtime_config_id,
            )
            for task, check, agent in plans
        )

    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign.preflight_run_bindings",
        record_preflight,
    )

    next_cell = preflight_replicate_campaign(context)

    assert next_cell is not None
    assert next_cell.schedule_cell == context.schedule.cells[0]
    assert tuple(observed) == tuple(
        (
            cell.task_id,
            cell.check_id,
            cell.agent_id,
            cell.runtime_config_id,
        )
        for runtime in context.schedule.runtime_configs
        for cell in context.schedule.cells
        if cell.runtime_config_id == runtime.runtime_config_id
    )


def test_replicate_campaign_rejects_endpoint_drift_before_workspace_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    workspace_preflight_called = False
    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "resolve_openai_endpoint_digest",
        lambda *, require_api_key: "different-endpoint",
    )

    def record_workspace_preflight(*args, **kwargs):
        nonlocal workspace_preflight_called
        del args, kwargs
        workspace_preflight_called = True

    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign.preflight_run_bindings",
        record_workspace_preflight,
    )

    with pytest.raises(RuntimeError, match="endpoint does not match"):
        preflight_replicate_campaign(context)

    assert not workspace_preflight_called


def test_replicate_campaign_executes_one_frozen_cell_and_advances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    executed = _stub_successful_campaign_run(monkeypatch, context)

    result = run_next_replicate_campaign_cell(context)
    next_cell = preflight_replicate_campaign(context)
    ledger = load_resource_ledger(
        context.ledger_path,
        updated_at="2026-07-22T00:00:02Z",
    )

    assert result is not None
    assert executed == [0]
    assert result.task_id == context.schedule.cells[0].task_id
    assert result.agent_id == context.schedule.cells[0].agent_id
    assert next_cell is not None
    assert next_cell.schedule_cell == context.schedule.cells[1]
    calls = ledger["calls"]
    assert isinstance(calls, list)
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call, dict)
    assert call["state"] == "completed"
    assert call["sequence_index"] == 0
    assert call["result_id"] == result.result_id


def test_replicate_campaign_recovers_result_after_completion_event_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)

    with monkeypatch.context() as interrupted:
        _stub_campaign_preflight(interrupted)
        _stub_successful_campaign_run(interrupted, context)

        def interrupt_completion(path, event):
            if event.get("event_type") == "completion":
                raise OSError("simulated completion event interruption")
            append_ledger_event(path, event)

        interrupted.setattr(
            "examples.pylint_swe_bench_verified.replicate_campaign.append_ledger_event",
            interrupt_completion,
        )
        with pytest.raises(OSError, match="completion event interruption"):
            run_next_replicate_campaign_cell(context)

    _stub_campaign_preflight(monkeypatch)
    next_cell = preflight_replicate_campaign(context)
    ledger = load_resource_ledger(
        context.ledger_path,
        updated_at="2026-07-22T00:00:02Z",
    )
    calls = ledger["calls"]
    assert isinstance(calls, list)
    call = calls[0]
    assert isinstance(call, dict)

    assert next_cell is not None
    assert next_cell.schedule_cell == context.schedule.cells[1]
    assert call["state"] == "completed"
    assert call["recovered_after_interruption"] is True


def test_replicate_campaign_rejects_ledger_result_evidence_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    _stub_successful_campaign_run(monkeypatch, context)
    run_next_replicate_campaign_cell(context)
    events_path = ledger_events_path(context.ledger_path)
    events = list(load_ledger_events(events_path))
    completion = dict(events[-1])
    completion["outcome"] = "fail"
    write_jsonl_records(events_path, (*events[:-1], completion))

    with pytest.raises(RuntimeError, match="Result evidence does not match"):
        preflight_replicate_campaign(context)


def test_replicate_campaign_does_not_retry_a_failed_paid_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    attempts = 0

    def fail_run(*args, **kwargs):
        nonlocal attempts
        del args, kwargs
        attempts += 1
        raise RuntimeError("simulated paid harness failure")

    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "run_agent_on_task_with_artifacts",
        fail_run,
    )

    with pytest.raises(RuntimeError, match="simulated paid harness failure"):
        run_next_replicate_campaign_cell(context)
    with pytest.raises(RuntimeError, match="stopped paid cell"):
        run_next_replicate_campaign_cell(context)
    with pytest.raises(RuntimeError, match="exact cost Result"):
        reauthorize_stopped_replicate_campaign_call(
            context,
            source_amendment_digest="study-amendment-digest",
            approved_at="2026-07-22T00:00:02Z",
            reason="must not convert a harness failure",
            new_maximum_estimated_cost_per_call_usd=2.0,
        )

    assert attempts == 1


def test_replicate_campaign_cli_authorize_is_explicit_and_auditable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = _campaign_context(tmp_path)
    monkeypatch.setattr(
        replicate_campaign_cli,
        "build_campaign_context",
        lambda paths, scoring_config: context,
    )
    monkeypatch.setattr(
        replicate_campaign_cli,
        "resolve_openai_endpoint_digest",
        lambda *, require_api_key: "endpoint-digest",
    )

    exit_code = replicate_campaign_cli.main(
        (
            *_campaign_cli_common_args(tmp_path, context),
            "authorize",
            "--approved-at",
            "2026-07-22T00:00:00Z",
            "--scope",
            "paired replicate test campaign",
            "--maximum-estimated-cost-usd",
            "10",
            "--maximum-estimated-cost-per-call-usd",
            "1",
            "--pricing-version",
            "test-pricing",
            "--cost-rate",
            "input_tokens=0.001",
            "--cost-rate",
            "output_tokens=0.005",
            "--pricing-source",
            "https://example.test/pricing",
            "--accounting-basis",
            "test price schedule",
        )
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert context.ledger_path.exists()
    assert summary == {
        "campaign_id": CAMPAIGN_ID,
        "ledger_path": str(context.ledger_path),
        "maximum_estimated_cost_per_call_usd": 1.0,
        "maximum_estimated_cost_usd": 10.0,
        "maximum_paid_calls": len(context.schedule.cells),
        "next": "preflight",
        "stage": "authorized",
    }


def test_replicate_campaign_cli_loads_frozen_execution_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_pool, tasks, checks, agents, runtime = _inputs()
    campaign_dir = tmp_path / "campaign"
    records_dir = campaign_dir / "records"
    records_dir.mkdir(parents=True)
    bound_agents = tuple(
        replace(
            agent,
            harness_digest=canonical_digest(
                {
                    "agent_command": (
                        "env",
                        f"BARCAROLLE_CODEX_MODEL={agent.requested_model_id}",
                        f"BARCAROLLE_CODEX_REASONING_EFFORT={effort}",
                        "BARCAROLLE_CODEX_HOME="
                        + str(
                            (
                                campaign_dir
                                / (
                                    "codex-home-"
                                    + canonical_digest({"agent_id": agent.agent_id})[
                                        :16
                                    ]
                                )
                            ).resolve()
                        ),
                        str(replicate_campaign_cli.HARNESS),
                    )
                }
            ),
        )
        for agent, effort in zip(agents, ("low", "high"), strict=True)
    )
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        bound_agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=20260722,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    agents_path = records_dir / "agents.jsonl"
    runtime_path = records_dir / "runtime-config.jsonl"
    schedule_path = records_dir / "replicate-schedule.jsonl"
    write_jsonl_records(agents_path, bound_agents)
    write_jsonl_records(runtime_path, (runtime,))
    write_jsonl_records(schedule_path, (schedule,))
    monkeypatch.setattr(
        replicate_campaign_cli,
        "build_pilot_context",
        lambda paths, ledger_path: SimpleNamespace(
            run_context=WorkspaceRunContext(),
            task_pool=task_pool,
            tasks=tasks,
            checks={check.check_id: check for check in checks},
            workspace_config=_workspace_config(),
        ),
    )
    paths = replicate_campaign_cli.CampaignCliPaths(
        pilot=replicate_campaign_cli.PilotPaths(
            output_dir=tmp_path / "pilot",
            target_repo=tmp_path / "repo",
            dataset=tmp_path / "dataset",
            supplemental_dataset=tmp_path / "supplemental-dataset",
            harness_python=tmp_path / "python",
        ),
        campaign_dir=campaign_dir,
        agents_path=agents_path,
        runtime_config_path=runtime_path,
        schedule_path=schedule_path,
        result_store_path=records_dir / "results.jsonl",
        ledger_path=campaign_dir / "campaign-ledger.json",
    )

    context = replicate_campaign_cli.build_campaign_context(
        paths,
        ScoringConfig("test-pricing", {"input_tokens": 0.001}),
    )

    assert context.schedule == schedule
    assert context.agents == bound_agents
    assert context.base_runtime_config == runtime
    assert context.result_store.path == records_dir / "results.jsonl"
    assert context.ledger_path == campaign_dir / "campaign-ledger.json"


def test_replicate_campaign_cli_preflight_never_creates_authority(
    tmp_path: Path,
) -> None:
    context = _campaign_context(tmp_path)

    with pytest.raises(FileNotFoundError):
        replicate_campaign_cli.main(
            (*_campaign_cli_common_args(tmp_path, context), "preflight")
        )

    assert not context.ledger_path.exists()
    assert not ledger_events_path(context.ledger_path).exists()


def test_replicate_campaign_cli_preflight_verifies_images_and_reports_next_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    monkeypatch.setattr(
        replicate_campaign_cli,
        "build_campaign_context",
        lambda paths, scoring_config: context,
    )
    verified: list[tuple[str, ...]] = []

    def verify_images(
        tasks: tuple[TaskRecord, ...],
    ) -> tuple[dict[str, str], ...]:
        verified.append(tuple(task.task_id for task in tasks))
        return ({"image_ref": "first"}, {"image_ref": "second"})

    monkeypatch.setattr(
        replicate_campaign_cli,
        "verify_pylint_verifier_images",
        verify_images,
    )

    exit_code = replicate_campaign_cli.main(
        (*_campaign_cli_common_args(tmp_path, context), "preflight")
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert verified == [tuple(task.task_id for task in context.tasks)]
    assert summary["stage"] == "preflight_passed"
    assert summary["verified_image_count"] == 2
    assert summary["next_cell"]["sequence_index"] == 0
    assert summary["next"] == "run-next"
    assert context.result_store.path.read_text(encoding="utf-8") == ""
    assert not ledger_events_path(context.ledger_path).exists()


def test_replicate_campaign_cli_run_next_executes_one_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = _campaign_context(tmp_path)
    _initialize_campaign_ledger(context)
    _stub_campaign_preflight(monkeypatch)
    executed = _stub_successful_campaign_run(monkeypatch, context)
    monkeypatch.setattr(
        replicate_campaign_cli,
        "build_campaign_context",
        lambda paths, scoring_config: context,
    )
    verified: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        replicate_campaign_cli,
        "verify_pylint_verifier_images",
        lambda tasks: verified.append(tuple(task.task_id for task in tasks)) or (),
    )

    exit_code = replicate_campaign_cli.main(
        (*_campaign_cli_common_args(tmp_path, context), "run-next")
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert executed == [0]
    assert verified == [tuple(task.task_id for task in context.tasks)]
    assert summary["stage"] == "cell_recorded"
    assert summary["task_id"] == context.schedule.cells[0].task_id
    assert summary["agent_id"] == context.schedule.cells[0].agent_id
    assert summary["next"] == "preflight"


def _campaign_context(tmp_path: Path) -> ReplicateCampaignContext:
    task_pool, tasks, checks, agents, runtime = _inputs()
    schedule = build_replicate_schedule(
        task_pool,
        tasks,
        checks,
        agents,
        runtime,
        campaign_id=CAMPAIGN_ID,
        seed=20260722,
        replicate_fraction=0.20,
        replicate_count=2,
    )
    return ReplicateCampaignContext(
        schedule=schedule,
        task_pool=task_pool,
        tasks=tasks,
        checks=checks,
        agents=agents,
        base_runtime_config=runtime,
        workspace_config=_workspace_config(),
        scoring_config=ScoringConfig(
            pricing_version="test-pricing",
            cost_rates={"input_tokens": 0.001, "output_tokens": 0.005},
        ),
        result_store=ResultStore(tmp_path / "results.jsonl"),
        ledger_path=tmp_path / "resource-ledger.json",
        run_context=WorkspaceRunContext(),
    )


def _campaign_cli_common_args(
    tmp_path: Path,
    context: ReplicateCampaignContext,
) -> tuple[str, ...]:
    return (
        "--pilot-output-dir",
        str(tmp_path / "pilot"),
        "--campaign-dir",
        str(tmp_path),
        "--ledger",
        str(context.ledger_path),
    )


def _initialize_campaign_ledger(
    context: ReplicateCampaignContext,
) -> dict[str, object]:
    return initialize_replicate_campaign_ledger(
        context,
        approved_at="2026-07-22T00:00:00Z",
        endpoint_digest="endpoint-digest",
        maximum_estimated_cost_usd=10.0,
        maximum_estimated_cost_per_call_usd=1.0,
        pricing_sources=("https://example.test/pricing",),
        accounting_basis="test price schedule",
        scope="paired replicate test campaign",
    )


def _stub_campaign_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "resolve_openai_endpoint_digest",
        lambda *, require_api_key: "endpoint-digest",
    )
    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign.preflight_run_bindings",
        lambda *args, **kwargs: None,
    )


def _stub_successful_campaign_run(
    monkeypatch: pytest.MonkeyPatch,
    context: ReplicateCampaignContext,
) -> list[int]:
    executed: list[int] = []

    def fake_run(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        run_context,
        artifact_config,
    ):
        del workspace_config, run_context, artifact_config
        cell = next(
            candidate
            for candidate in context.schedule.cells
            if candidate.task_id == task.task_id
            and candidate.check_id == check.check_id
            and candidate.agent_id == agent.agent_id
            and candidate.runtime_config_id == runtime_config.runtime_config_id
        )
        executed.append(cell.sequence_index)
        return WorkspaceRunResult(
            _workspace_run_for_schedule_cell(cell, task, check, agent)
        )

    monkeypatch.setattr(
        "examples.pylint_swe_bench_verified.replicate_campaign."
        "run_agent_on_task_with_artifacts",
        fake_run,
    )
    return executed


def _inputs() -> tuple[
    TaskPoolRecord,
    tuple[TaskRecord, ...],
    tuple[CheckRecord, ...],
    tuple[AgentRecord, ...],
    RuntimeConfig,
]:
    tasks = tuple(
        _task(index, "medium" if index < 6 else "easy") for index in range(10)
    )
    checks = tuple(_check(task) for task in tasks)
    agents = (_agent("low"), _agent("high"))
    runtime = RuntimeConfig(
        runtime_config_id="runtime-base",
        budget_digest="budget",
        retry_policy_digest="no-whole-cell-retry",
        stochastic_settings_digest="provider-default-stochasticity",
        timeout_seconds=900,
        hardware_profile_digest=None,
    )
    return _task_pool(tasks, checks), tasks, checks, agents, runtime


def _task(index: int, stratum: str) -> TaskRecord:
    task_id = f"task-{index:02d}"
    check_id = f"check-{index:02d}"
    task_text = f"Fix Pylint task {index}."
    return TaskRecord(
        task_id=task_id,
        repository_id="pylint-dev/pylint",
        base_commit=f"{index + 1:040x}",
        source_family="swe_bench_verified",
        source_ref=f"issue-{index:02d}",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-02T00:00:00Z",
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(task_text, ()),
        solver_material_refs=(),
        check_ids=(check_id,),
        dependency_cluster_id=f"cluster-{index:02d}",
        sampling_stratum=stratum,
    )


def _check(task: TaskRecord) -> CheckRecord:
    return CheckRecord(
        check_id=task.check_ids[0],
        task_id=task.task_id,
        check_type="swe_bench",
        check_manifest_digest=f"manifest-{task.task_id}",
        hidden_check_bundle_digest=f"hidden-{task.task_id}",
        resource_limits={"timeout_seconds": 900},
        oracle_source="swe_bench_test_patch",
        check_material_available_at="2026-01-03T00:00:00Z",
    )


def _agent(effort: str) -> AgentRecord:
    return AgentRecord(
        agent_id=f"agent-{effort}",
        agent_manifest_digest=f"manifest-{effort}",
        requested_model_id="immutable-model",
        model_snapshot_id="immutable-model-2026-07-01",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
        harness_digest=f"harness-{effort}",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="none",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig(
        workspace_config_id="workspace",
        repository_checkout_config_digest="checkout",
        submodule_state_digest="submodules",
        base_image_digest="image",
        dependency_lock_digest="lock",
    )


def _result_for_schedule_cell(
    cell,
    schedule: ReplicateSchedule,
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    agents: tuple[AgentRecord, ...],
    workspace: WorkspaceConfig,
):
    task = next(task for task in tasks if task.task_id == cell.task_id)
    check = next(check for check in checks if check.check_id == cell.check_id)
    agent = next(agent for agent in agents if agent.agent_id == cell.agent_id)
    runtime = schedule.runtime_configs[cell.replicate_index]
    identity = compute_result_cache_identity(
        task,
        check,
        agent,
        workspace,
        runtime,
    )
    return build_result_record(
        task,
        check,
        agent,
        _workspace_run_for_schedule_cell(cell, task, check, agent),
        identity,
        ScoringConfig(
            pricing_version="test-pricing",
            cost_rates={"input_tokens": 0.001, "output_tokens": 0.005},
        ),
    )


def _workspace_run_for_schedule_cell(
    cell,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> WorkspaceRunRecord:
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace-run-{cell.sequence_index}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest="solver-workspace",
        verifier_workspace_digest="verifier-workspace",
        terminal_status="passed",
        diff_digest="diff",
        replay_status="applied",
        check_outcome="pass",
        invalid_owner=None,
        failure_label=None,
        usage={"input_tokens": 1, "output_tokens": 0},
        latency={
            "workspace_seconds": 1.0,
            "agent_seconds": 0.5,
            "verification_seconds": 0.25,
            "solver_checkout_seconds": 0.05,
            "verifier_checkout_seconds": 0.05,
            "diff_replay_seconds": 0.05,
            "cleanup_seconds": 0.05,
        },
        started_at="2026-07-22T00:00:00Z",
        finished_at="2026-07-22T00:00:01Z",
    )


def _task_pool(
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
) -> TaskPoolRecord:
    return record_with_digest(
        TaskPoolRecord(
            task_pool_id="task-pool",
            task_pool_digest="",
            repository_id="pylint-dev/pylint",
            task_ids=tuple(task.task_id for task in tasks),
            check_ids=tuple(check.check_id for check in checks),
            task_records_ref="records/tasks.jsonl",
            task_records_digest=canonical_digest(tasks),
            check_records_ref="records/checks.jsonl",
            check_records_digest=canonical_digest(checks),
            certification_evidence_ref="records/certification-evidence.jsonl",
            source_event_records_ref="records/source-events.jsonl",
            source_event_records_digest="source-events-digest",
            rejected_candidate_ids=(),
            rejection_summary_digest="rejection-summary",
            certification_evidence_digest="certification-evidence",
            generation_provenance_ref=None,
            generation_provenance_digest=None,
            generator_config_digest=None,
            source_protocol_digest=None,
            certification_config_digest="certification-config",
            created_at="2026-07-22T00:00:00Z",
        )
    )
