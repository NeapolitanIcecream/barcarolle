"""Execute one authorized cell from a frozen Pylint replicate schedule."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose, isfinite
from pathlib import Path
from typing import Mapping, Sequence, cast

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    ResultRecord,
    RuntimeConfig,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    parse_utc_timestamp,
    utc_now_timestamp,
)
from barcarolle.result_store import (
    ResultCacheConfig,
    ResultStore,
    ResultStoreSession,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    open_result_store_session,
    validate_scoring_config,
)
from barcarolle.workspace import (
    WorkspaceArtifactConfig,
    WorkspaceRunContext,
    preflight_run_bindings,
    resolve_openai_endpoint_digest,
    run_agent_on_task_with_artifacts,
)
from examples.experiment_ledger import (
    append_ledger_event,
    ledger_events_path,
    load_resource_ledger,
    write_json,
)
from examples.pylint_swe_bench_verified.replicate_schedule import (
    ReplicateSchedule,
    ResolvedReplicateScheduleCell,
    resolve_replicate_schedule_cells,
    validate_replicate_schedule,
)


CAMPAIGN_LEDGER_SCHEMA_VERSION = "paired_replicate_campaign_ledger_v2"
_CREDENTIAL_VARIABLES = ["OPENAI_BASE_URL", "OPENAI_API_KEY"]
_STOP_CONDITIONS = (
    "authorized endpoint cannot be proven",
    "schedule or campaign authority does not replay",
    "usage cannot be priced",
    "a reserved cell has no exact Result",
    "a paid Result is not scoreable",
    "remaining budget cannot cover one authorized call",
    "a Result exceeds the per-call or total estimated-cost limit",
)


@dataclass(frozen=True)
class ReplicateCampaignContext:
    """Frozen inputs and live bindings for one Pylint replicate campaign."""

    schedule: ReplicateSchedule
    task_pool: TaskPoolRecord
    tasks: tuple[TaskRecord, ...]
    checks: tuple[CheckRecord, ...]
    agents: tuple[AgentRecord, ...]
    base_runtime_config: RuntimeConfig
    workspace_config: WorkspaceConfig
    scoring_config: ScoringConfig
    result_store: ResultStore
    ledger_path: Path
    run_context: WorkspaceRunContext
    cache_config: ResultCacheConfig = field(default_factory=ResultCacheConfig)


@dataclass(frozen=True)
class _CampaignState:
    ledger: dict[str, object]
    resolved: tuple[ResolvedReplicateScheduleCell, ...]
    next_missing: ResolvedReplicateScheduleCell | None


def _finite_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    converted = float(value)
    return converted if isfinite(converted) else None


def initialize_replicate_campaign_ledger(
    context: ReplicateCampaignContext,
    *,
    approved_at: str,
    endpoint_digest: str,
    maximum_estimated_cost_usd: float,
    maximum_estimated_cost_per_call_usd: float,
    pricing_sources: Sequence[str],
    accounting_basis: str,
    scope: str,
) -> dict[str, object]:
    """Create one immutable campaign authority before any paid execution."""
    _validate_context(context)
    _validate_authorization_inputs(
        approved_at=approved_at,
        endpoint_digest=endpoint_digest,
        maximum_estimated_cost_usd=maximum_estimated_cost_usd,
        maximum_estimated_cost_per_call_usd=maximum_estimated_cost_per_call_usd,
        pricing_sources=pricing_sources,
        accounting_basis=accounting_basis,
        scope=scope,
    )
    events_path = ledger_events_path(context.ledger_path)
    if context.ledger_path.exists() or events_path.exists():
        raise FileExistsError(
            f"refusing to overwrite replicate campaign ledger: {context.ledger_path}"
        )
    authorization = {
        "approved_at": approved_at,
        "scope": scope,
        "campaign_id": context.schedule.campaign_id,
        "schedule_digest": context.schedule.schedule_digest,
        "task_pool_id": context.task_pool.task_pool_id,
        "task_pool_digest": context.task_pool.task_pool_digest,
        "agent_records_digest": context.schedule.agent_records_digest,
        "workspace_config_digest": canonical_digest(context.workspace_config),
        "base_runtime_config_digest": canonical_digest(context.base_runtime_config),
        "endpoint_digest": endpoint_digest,
        "credential_variables": _CREDENTIAL_VARIABLES,
        "budget_usd": float(maximum_estimated_cost_usd),
    }
    limits = {
        "maximum_paid_calls": len(context.schedule.cells),
        "maximum_estimated_cost_per_call_usd": float(
            maximum_estimated_cost_per_call_usd
        ),
        "cell_retries": 0,
    }
    pricing = {
        "pricing_version": context.scoring_config.pricing_version,
        "scoring_config_digest": context.scoring_config.scoring_config_digest,
        "cost_rates": dict(context.scoring_config.cost_rates),
        "sources": list(pricing_sources),
        "accounting_basis": accounting_basis,
    }
    ledger: dict[str, object] = {
        "schema_version": CAMPAIGN_LEDGER_SCHEMA_VERSION,
        "campaign_authority_digest": _campaign_authority_digest(
            authorization,
            limits,
            pricing,
        ),
        "authorization": authorization,
        "limits": limits,
        "pricing": pricing,
        "calls": [],
        "spent_usd": 0.0,
        "remaining_usd": float(maximum_estimated_cost_usd),
        "stop_conditions": list(_STOP_CONDITIONS),
        "updated_at": utc_now_timestamp(),
    }
    write_json(context.ledger_path, ledger)
    return ledger


def preflight_replicate_campaign(
    context: ReplicateCampaignContext,
) -> ResolvedReplicateScheduleCell | None:
    """Validate all remaining cells and return the first exact missing cell."""
    _validate_context(context)
    ledger = _load_and_validate_ledger(context)
    with open_result_store_session(context.result_store) as session:
        state = _campaign_state(context, ledger, session)
        if state.next_missing is None:
            return None
        _require_current_endpoint(state.ledger)
        _ensure_call_allowed(context, state.ledger)
        _preflight_remaining_cells(context, state.resolved)
        return state.next_missing


def run_next_replicate_campaign_cell(
    context: ReplicateCampaignContext,
    *,
    artifact_config: WorkspaceArtifactConfig | None = None,
) -> ResultRecord | None:
    """Run at most the first missing cell after replaying campaign authority."""
    _validate_context(context)
    ledger = _load_and_validate_ledger(context)
    with open_result_store_session(context.result_store) as session:
        state = _campaign_state(context, ledger, session)
        if state.next_missing is None:
            return None
        _require_current_endpoint(state.ledger)
        _ensure_call_allowed(context, state.ledger)
        _preflight_remaining_cells(context, state.resolved)
        return _execute_next_cell(
            context,
            state,
            session,
            artifact_config,
        )


def _validate_context(context: ReplicateCampaignContext) -> None:
    validation = validate_replicate_schedule(
        context.schedule,
        context.task_pool,
        context.tasks,
        context.checks,
        context.agents,
        context.base_runtime_config,
    )
    if not validation.ok:
        raise ValueError(
            f"replicate schedule is invalid: {', '.join(validation.errors)}"
        )
    validate_scoring_config(context.scoring_config)
    if not context.scoring_config.cost_rates:
        raise ValueError("replicate campaign pricing must contain cost rates")
    if context.cache_config.reuse_benchmark_invalid:
        raise ValueError("replicate campaign forbids benchmark-invalid reuse")


def _validate_authorization_inputs(
    *,
    approved_at: str,
    endpoint_digest: str,
    maximum_estimated_cost_usd: float,
    maximum_estimated_cost_per_call_usd: float,
    pricing_sources: Sequence[str],
    accounting_basis: str,
    scope: str,
) -> None:
    _validate_approved_at(approved_at)
    _require_nonempty_string(endpoint_digest, "endpoint_digest")
    _require_nonempty_string(scope, "campaign scope")
    _require_nonempty_string(accounting_basis, "pricing accounting_basis")
    _validate_pricing_sources(pricing_sources)
    budget = _finite_float(maximum_estimated_cost_usd)
    if budget is None or budget <= 0:
        raise ValueError("maximum_estimated_cost_usd must be finite and positive")
    per_call_limit = _finite_float(maximum_estimated_cost_per_call_usd)
    if per_call_limit is None or per_call_limit <= 0:
        raise ValueError(
            "maximum_estimated_cost_per_call_usd must be finite and positive"
        )
    if per_call_limit > budget:
        raise ValueError(
            "per-call estimated-cost limit must not exceed the total budget"
        )


def _validate_approved_at(approved_at: object) -> None:
    if not isinstance(approved_at, str):
        raise ValueError("approved_at must be a timezone-aware timestamp")
    try:
        parse_utc_timestamp(approved_at)
    except (TypeError, ValueError) as exc:
        raise ValueError("approved_at must be a timezone-aware timestamp") from exc


def _require_nonempty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a nonempty string")


def _validate_pricing_sources(pricing_sources: object) -> None:
    if (
        not isinstance(pricing_sources, Sequence)
        or isinstance(pricing_sources, str)
        or not pricing_sources
        or any(not isinstance(source, str) or not source for source in pricing_sources)
    ):
        raise ValueError("pricing_sources must contain nonempty strings")


def _campaign_authority_digest(
    authorization: Mapping[str, object],
    limits: Mapping[str, object],
    pricing: Mapping[str, object],
) -> str:
    return canonical_digest(
        {
            "schema_version": CAMPAIGN_LEDGER_SCHEMA_VERSION,
            "authorization": authorization,
            "limits": limits,
            "pricing": pricing,
        }
    )


def _load_and_validate_ledger(
    context: ReplicateCampaignContext,
) -> dict[str, object]:
    ledger = load_resource_ledger(
        context.ledger_path,
        updated_at=utc_now_timestamp(),
    )
    _validate_ledger(context, ledger)
    return ledger


def _validate_ledger(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
) -> None:
    authorization = ledger.get("authorization")
    limits = ledger.get("limits")
    pricing = ledger.get("pricing")
    if not all(
        isinstance(value, Mapping) for value in (authorization, limits, pricing)
    ):
        raise RuntimeError("replicate campaign authority sections are missing")
    authorization = cast(Mapping[str, object], authorization)
    limits = cast(Mapping[str, object], limits)
    pricing = cast(Mapping[str, object], pricing)
    if ledger.get("schema_version") != CAMPAIGN_LEDGER_SCHEMA_VERSION:
        raise RuntimeError("replicate campaign ledger schema is not supported")
    observed_authority_digest = ledger.get("campaign_authority_digest")
    expected_authority_digest = _campaign_authority_digest(
        authorization,
        limits,
        pricing,
    )
    if observed_authority_digest != expected_authority_digest:
        raise RuntimeError("replicate campaign authority digest does not match")
    _validate_authorization(context, authorization)
    _validate_campaign_limits(context, ledger, limits, authorization)
    expected_pricing = {
        "pricing_version": context.scoring_config.pricing_version,
        "scoring_config_digest": context.scoring_config.scoring_config_digest,
        "cost_rates": dict(context.scoring_config.cost_rates),
        "sources": pricing.get("sources"),
        "accounting_basis": pricing.get("accounting_basis"),
    }
    if pricing != expected_pricing:
        raise RuntimeError("replicate campaign pricing does not match ScoringConfig")
    sources = pricing.get("sources")
    if (
        not isinstance(sources, Sequence)
        or isinstance(sources, str)
        or not sources
        or any(not isinstance(source, str) or not source for source in sources)
    ):
        raise RuntimeError("replicate campaign pricing sources are invalid")
    if not isinstance(pricing.get("accounting_basis"), str) or not pricing.get(
        "accounting_basis"
    ):
        raise RuntimeError("replicate campaign pricing basis is invalid")
    _validate_ledger_totals(ledger, authorization)


def _validate_campaign_limits(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    limits: Mapping[str, object],
    authorization: Mapping[str, object],
) -> None:
    if (
        set(limits)
        != {
            "maximum_paid_calls",
            "maximum_estimated_cost_per_call_usd",
            "cell_retries",
        }
        or limits.get("maximum_paid_calls") != len(context.schedule.cells)
        or limits.get("cell_retries") != 0
    ):
        raise RuntimeError("replicate campaign limits do not match the schedule")
    per_call_limit = _per_call_cost_limit(ledger)
    budget = _finite_float(authorization.get("budget_usd"))
    if budget is None:
        raise RuntimeError("replicate campaign budget_usd is invalid")
    if per_call_limit > budget:
        raise RuntimeError("replicate campaign per-call limit exceeds the total budget")


def _validate_authorization(
    context: ReplicateCampaignContext,
    authorization: Mapping[str, object],
) -> None:
    expected = {
        "campaign_id": context.schedule.campaign_id,
        "schedule_digest": context.schedule.schedule_digest,
        "task_pool_id": context.task_pool.task_pool_id,
        "task_pool_digest": context.task_pool.task_pool_digest,
        "agent_records_digest": context.schedule.agent_records_digest,
        "workspace_config_digest": canonical_digest(context.workspace_config),
        "base_runtime_config_digest": canonical_digest(context.base_runtime_config),
        "credential_variables": _CREDENTIAL_VARIABLES,
    }
    if any(authorization.get(key) != value for key, value in expected.items()):
        raise RuntimeError("replicate campaign authorization does not match inputs")
    try:
        approved_at = authorization["approved_at"]
        if not isinstance(approved_at, str):
            raise ValueError
        parse_utc_timestamp(approved_at)
    except (KeyError, ValueError) as exc:
        raise RuntimeError("replicate campaign approved_at is invalid") from exc
    for field_name in ("scope", "endpoint_digest"):
        value = authorization.get(field_name)
        if not isinstance(value, str) or not value:
            raise RuntimeError(
                f"replicate campaign {field_name} must be a nonempty string"
            )
    budget = _finite_float(authorization.get("budget_usd"))
    if budget is None or budget <= 0:
        raise RuntimeError("replicate campaign budget_usd is invalid")


def _validate_ledger_totals(
    ledger: Mapping[str, object],
    authorization: Mapping[str, object],
) -> None:
    calls = ledger.get("calls")
    if not isinstance(calls, list):
        raise RuntimeError("replicate campaign calls must be a list")
    spent = 0.0
    for call in calls:
        if not isinstance(call, Mapping):
            raise RuntimeError("replicate campaign calls must be objects")
        value = call.get("estimated_cost_usd")
        if value is None:
            continue
        cost = _finite_float(value)
        if cost is None or cost < 0:
            raise RuntimeError("replicate campaign call cost is invalid")
        spent += cost
    budget = _finite_float(authorization.get("budget_usd"))
    if budget is None:
        raise RuntimeError("replicate campaign budget_usd is invalid")
    recorded_spent = _finite_float(ledger.get("spent_usd"))
    remaining = _finite_float(ledger.get("remaining_usd"))
    if (
        recorded_spent is None
        or remaining is None
        or not isclose(recorded_spent, spent)
        or not isclose(remaining, budget - spent)
        or spent > budget
        or remaining < 0
    ):
        raise RuntimeError("replicate campaign ledger totals do not reconcile")


def _campaign_state(
    context: ReplicateCampaignContext,
    ledger: dict[str, object],
    session: ResultStoreSession,
) -> _CampaignState:
    resolved = resolve_replicate_schedule_cells(
        context.schedule,
        context.task_pool,
        context.tasks,
        context.checks,
        context.agents,
        context.base_runtime_config,
        context.workspace_config,
        context.result_store,
        context.cache_config,
        context.scoring_config,
        session=session,
    )
    ledger = _reconcile_started_call(context, ledger, resolved, session)
    _validate_calls_and_results(context, ledger, resolved, session)
    next_missing = next(
        (cell for cell in resolved if cell.result_cell.cell_state == "missing"),
        None,
    )
    return _CampaignState(ledger, resolved, next_missing)


def _reconcile_started_call(
    context: ReplicateCampaignContext,
    ledger: dict[str, object],
    resolved: tuple[ResolvedReplicateScheduleCell, ...],
    session: ResultStoreSession,
) -> dict[str, object]:
    calls = _ledger_calls(ledger)
    started = tuple(
        (index, call)
        for index, call in enumerate(calls)
        if call.get("state") == "started"
    )
    if not started:
        return ledger
    if len(started) != 1 or started[0][0] != len(calls) - 1:
        raise RuntimeError("replicate campaign has invalid started reservations")
    index, call = started[0]
    _validate_call_binding(context, call, resolved[index])
    results = _exact_results_for_cell(context, resolved[index], session)
    if not results:
        raise RuntimeError(
            "resource ledger has a reserved cell without an exact Result; "
            "automatic retry is forbidden"
        )
    if len(results) != 1:
        raise RuntimeError("reserved replicate cell has duplicate exact Results")
    result = results[0]
    try:
        _validate_paid_result(context, ledger, result)
    except RuntimeError as exc:
        _finish_call(
            context,
            str(call["call_id"]),
            state="stopped",
            result=result,
            error=type(exc).__name__,
            recovered=True,
        )
        raise
    _finish_call(
        context,
        str(call["call_id"]),
        state="completed",
        result=result,
        recovered=True,
    )
    return _load_and_validate_ledger(context)


def _validate_calls_and_results(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    resolved: tuple[ResolvedReplicateScheduleCell, ...],
    session: ResultStoreSession,
) -> None:
    calls = _ledger_calls(ledger)
    if len(calls) > len(resolved):
        raise RuntimeError("replicate campaign has more calls than scheduled cells")
    for index, cell in enumerate(resolved):
        results = _exact_results_for_cell(context, cell, session)
        if index >= len(calls):
            if results:
                raise RuntimeError(
                    "replicate Result exists without a ledger reservation"
                )
            continue
        call = calls[index]
        _validate_call_binding(context, call, cell)
        state = call.get("state")
        if state == "stopped":
            raise RuntimeError("resource ledger contains a stopped paid cell")
        if state != "completed":
            raise RuntimeError("resource ledger contains an unfinished paid cell")
        if len(results) != 1:
            raise RuntimeError("completed replicate call must have one exact Result")
        result = results[0]
        _validate_call_result(call, result)
        _validate_paid_result(context, ledger, result, include_recorded_spend=False)


def _ledger_calls(ledger: Mapping[str, object]) -> list[Mapping[str, object]]:
    calls = ledger.get("calls")
    if not isinstance(calls, list) or any(
        not isinstance(call, Mapping) for call in calls
    ):
        raise RuntimeError("replicate campaign calls must be objects")
    return calls


def _validate_call_binding(
    context: ReplicateCampaignContext,
    call: Mapping[str, object],
    resolved: ResolvedReplicateScheduleCell,
) -> None:
    cell = resolved.schedule_cell
    agent = next(agent for agent in context.agents if agent.agent_id == cell.agent_id)
    expected = {
        "call_id": _call_id(cell.sequence_index),
        "campaign_id": context.schedule.campaign_id,
        "schedule_digest": context.schedule.schedule_digest,
        "sequence_index": cell.sequence_index,
        "block_index": cell.block_index,
        "replicate_index": cell.replicate_index,
        "task_id": cell.task_id,
        "check_id": cell.check_id,
        "agent_id": cell.agent_id,
        "agent_manifest_digest": agent.agent_manifest_digest,
        "requested_model_id": agent.requested_model_id,
        "model_snapshot_id": agent.model_snapshot_id,
        "model_resolution_scope_id": agent.model_resolution_scope_id,
        "runtime_config_id": cell.runtime_config_id,
        "runtime_config_digest": cell.runtime_config_digest,
        "required_identity_digest": (resolved.result_cell.required_identity_digest),
        "retry": False,
    }
    if any(call.get(key) != value for key, value in expected.items()):
        raise RuntimeError("replicate ledger call does not match schedule order")


def _validate_call_result(
    call: Mapping[str, object],
    result: ResultRecord,
) -> None:
    expected = {
        "result_id": result.result_id,
        "result_digest": result.result_digest,
        "terminal_status": result.terminal_status,
        "scoreable_state": result.scoreable_state,
        "outcome": result.outcome,
        "usage": dict(result.usage),
        "estimated_cost_usd": result.cost["total_cost"],
        "pricing_version": result.pricing_version,
    }
    if any(call.get(key) != value for key, value in expected.items()):
        raise RuntimeError("replicate ledger Result evidence does not match")


def _exact_results_for_cell(
    context: ReplicateCampaignContext,
    resolved: ResolvedReplicateScheduleCell,
    session: ResultStoreSession,
) -> tuple[ResultRecord, ...]:
    cell = resolved.schedule_cell
    identity_digest = resolved.result_cell.required_identity_digest
    return tuple(
        result
        for result in session.results
        if result.agent_id == cell.agent_id
        and result.task_id == cell.task_id
        and result.check_id == cell.check_id
        and result.cache_identity.identity_digest == identity_digest
        and result.scoring_config_digest == context.scoring_config.scoring_config_digest
    )


def _require_current_endpoint(ledger: Mapping[str, object]) -> None:
    authorization = ledger["authorization"]
    if not isinstance(authorization, Mapping):
        raise RuntimeError("replicate campaign authorization is missing")
    current = resolve_openai_endpoint_digest(require_api_key=True)
    if current != authorization["endpoint_digest"]:
        raise RuntimeError("current OpenAI endpoint does not match campaign authority")


def _per_call_cost_limit(ledger: Mapping[str, object]) -> float:
    limits = ledger.get("limits")
    if not isinstance(limits, Mapping):
        raise RuntimeError("replicate campaign limits are missing")
    value = _finite_float(limits.get("maximum_estimated_cost_per_call_usd"))
    if value is None or value <= 0:
        raise RuntimeError("replicate campaign per-call cost limit is invalid")
    return value


def _ensure_call_allowed(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
) -> None:
    calls = _ledger_calls(ledger)
    if len(calls) >= len(context.schedule.cells):
        raise RuntimeError("replicate campaign paid-call limit is reached")
    remaining = _finite_float(ledger.get("remaining_usd"))
    if remaining is None or remaining <= 0:
        raise RuntimeError("replicate campaign has no remaining cost budget")
    per_call_limit = _per_call_cost_limit(ledger)
    if remaining < per_call_limit and not isclose(remaining, per_call_limit):
        raise RuntimeError(
            "replicate campaign remaining budget cannot cover one authorized call"
        )


def _preflight_remaining_cells(
    context: ReplicateCampaignContext,
    resolved: tuple[ResolvedReplicateScheduleCell, ...],
) -> None:
    task_by_id = {task.task_id: task for task in context.tasks}
    check_by_id = {check.check_id: check for check in context.checks}
    agent_by_id = {agent.agent_id: agent for agent in context.agents}
    for runtime in context.schedule.runtime_configs:
        plans = tuple(
            (
                task_by_id[cell.schedule_cell.task_id],
                check_by_id[cell.schedule_cell.check_id],
                agent_by_id[cell.schedule_cell.agent_id],
            )
            for cell in resolved
            if cell.result_cell.cell_state == "missing"
            and cell.schedule_cell.runtime_config_id == runtime.runtime_config_id
        )
        if plans:
            preflight_run_bindings(
                context.run_context,
                plans,
                context.workspace_config,
                runtime,
            )


def _execute_next_cell(
    context: ReplicateCampaignContext,
    state: _CampaignState,
    session: ResultStoreSession,
    artifact_config: WorkspaceArtifactConfig | None,
) -> ResultRecord:
    resolved = state.next_missing
    if resolved is None:
        raise RuntimeError("replicate campaign has no missing cell to execute")
    cell = resolved.schedule_cell
    task = next(task for task in context.tasks if task.task_id == cell.task_id)
    check = next(check for check in context.checks if check.check_id == cell.check_id)
    agent = next(agent for agent in context.agents if agent.agent_id == cell.agent_id)
    runtime = next(
        runtime
        for runtime in context.schedule.runtime_configs
        if runtime.runtime_config_id == cell.runtime_config_id
    )
    identity = compute_result_cache_identity(
        task,
        check,
        agent,
        context.workspace_config,
        runtime,
    )
    if identity.identity_digest != resolved.result_cell.required_identity_digest:
        raise RuntimeError("replicate cell identity changed before execution")
    call_id = _start_call(context, state.ledger, resolved, agent)
    result: ResultRecord | None = None
    artifact_manifest_ref: str | None = None
    try:
        workspace_result = run_agent_on_task_with_artifacts(
            task,
            check,
            agent,
            context.workspace_config,
            runtime,
            context.run_context,
            artifact_config,
        )
        if workspace_result.artifacts is not None:
            artifact_manifest_ref = workspace_result.artifacts.manifest_ref
        result = build_result_record(
            task,
            check,
            agent,
            workspace_result.run,
            identity,
            context.scoring_config,
        )
        result = session.append(result)
        _validate_paid_result(context, state.ledger, result)
    except BaseException as exc:
        _finish_call(
            context,
            call_id,
            state="stopped",
            result=result,
            error=type(exc).__name__,
            artifact_manifest_ref=artifact_manifest_ref,
        )
        raise
    _finish_call(
        context,
        call_id,
        state="completed",
        result=result,
        artifact_manifest_ref=artifact_manifest_ref,
    )
    return result


def _validate_paid_result(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    result: ResultRecord,
    *,
    include_recorded_spend: bool = True,
) -> None:
    if result.scoreable_state != "scoreable":
        raise RuntimeError("paid replicate Result is not scoreable")
    if (
        result.scoring_config_digest != context.scoring_config.scoring_config_digest
        or result.pricing_version != context.scoring_config.pricing_version
    ):
        raise RuntimeError("paid replicate Result pricing does not match authority")
    cost = _finite_float(result.cost.get("total_cost"))
    if cost is None or cost < 0:
        raise RuntimeError("paid replicate Result usage cannot be priced")
    authorization = ledger["authorization"]
    if not isinstance(authorization, Mapping):
        raise RuntimeError("replicate campaign authorization is missing")
    spent = _finite_float(
        ledger.get("spent_usd", 0.0) if include_recorded_spend else 0.0
    )
    if spent is None:
        raise RuntimeError("replicate campaign spent_usd is invalid")
    budget = _finite_float(authorization.get("budget_usd"))
    if budget is None:
        raise RuntimeError("replicate campaign budget_usd is invalid")
    per_call_limit = _per_call_cost_limit(ledger)
    if cost > per_call_limit and not isclose(cost, per_call_limit):
        raise RuntimeError("paid replicate Result exceeds the per-call cost limit")
    if spent + cost > budget:
        raise RuntimeError("paid replicate Result exceeds the campaign cost cap")


def _start_call(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    resolved: ResolvedReplicateScheduleCell,
    agent: AgentRecord,
) -> str:
    sequence_index = resolved.schedule_cell.sequence_index
    call_id = _call_id(sequence_index)
    call_count = len(_ledger_calls(ledger))
    if sequence_index != call_count:
        raise RuntimeError("next replicate call is not the schedule prefix")
    cell = resolved.schedule_cell
    append_ledger_event(
        ledger_events_path(context.ledger_path),
        {
            "event_type": "reservation",
            "recorded_at": utc_now_timestamp(),
            "call_id": call_id,
            "state": "started",
            "campaign_id": context.schedule.campaign_id,
            "schedule_digest": context.schedule.schedule_digest,
            "sequence_index": sequence_index,
            "block_index": cell.block_index,
            "replicate_index": cell.replicate_index,
            "task_id": cell.task_id,
            "check_id": cell.check_id,
            "agent_id": cell.agent_id,
            "agent_manifest_digest": agent.agent_manifest_digest,
            "requested_model_id": agent.requested_model_id,
            "model_snapshot_id": agent.model_snapshot_id,
            "model_resolution_scope_id": agent.model_resolution_scope_id,
            "runtime_config_id": cell.runtime_config_id,
            "runtime_config_digest": cell.runtime_config_digest,
            "required_identity_digest": (resolved.result_cell.required_identity_digest),
            "retry": False,
        },
    )
    _load_and_validate_ledger(context)
    return call_id


def _finish_call(
    context: ReplicateCampaignContext,
    call_id: str,
    *,
    state: str,
    result: ResultRecord | None,
    error: str | None = None,
    recovered: bool = False,
    artifact_manifest_ref: str | None = None,
) -> None:
    event: dict[str, object] = {
        "event_type": "completion",
        "recorded_at": utc_now_timestamp(),
        "call_id": call_id,
        "state": state,
        "recovered_after_interruption": recovered,
    }
    if result is not None:
        event.update(
            {
                "result_id": result.result_id,
                "result_digest": result.result_digest,
                "terminal_status": result.terminal_status,
                "scoreable_state": result.scoreable_state,
                "outcome": result.outcome,
                "usage": dict(result.usage),
                "estimated_cost_usd": result.cost["total_cost"],
                "pricing_version": result.pricing_version,
            }
        )
    if error is not None:
        event["stop_reason"] = error
    if artifact_manifest_ref is not None:
        event["artifact_manifest_ref"] = artifact_manifest_ref
    append_ledger_event(ledger_events_path(context.ledger_path), event)
    load_resource_ledger(
        context.ledger_path,
        updated_at=utc_now_timestamp(),
    )


def _call_id(sequence_index: int) -> str:
    return f"replicate-cell-{sequence_index:04d}"
