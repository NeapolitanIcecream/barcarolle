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
    SINGLE_AGENT_CANARY_SCHEMA_VERSION,
    resolve_replicate_schedule_cells,
    validate_replicate_schedule,
)


CAMPAIGN_LEDGER_SCHEMA_VERSION = "paired_replicate_campaign_ledger_v2"
CANARY_CAMPAIGN_LEDGER_SCHEMA_VERSION = "single_agent_canary_campaign_ledger_v1"
CAMPAIGN_AUTHORITY_AMENDMENT_SCHEMA_VERSION = (
    "replicate_campaign_authority_amendment_v1"
)
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
    ledger_schema_version = _campaign_ledger_schema_version(context.schedule)
    ledger: dict[str, object] = {
        "schema_version": ledger_schema_version,
        "campaign_authority_digest": _campaign_authority_digest(
            authorization,
            limits,
            pricing,
            schema_version=ledger_schema_version,
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


def reauthorize_stopped_replicate_campaign_call(
    context: ReplicateCampaignContext,
    *,
    source_amendment_digest: str,
    approved_at: str,
    reason: str,
    new_maximum_estimated_cost_per_call_usd: float,
) -> dict[str, object]:
    """Accept one exact cost-limit stop under a larger append-only authority."""
    _validate_context(context)
    _require_nonempty_string(source_amendment_digest, "source_amendment_digest")
    _validate_approved_at(approved_at)
    _require_nonempty_string(reason, "reauthorization reason")
    new_limit = _finite_float(new_maximum_estimated_cost_per_call_usd)
    if new_limit is None or new_limit <= 0:
        raise ValueError("new per-call estimated-cost limit must be positive")
    ledger = _load_and_validate_ledger(context)
    authorization = cast(Mapping[str, object], ledger["authorization"])
    limits = cast(Mapping[str, object], ledger["limits"])
    pricing = cast(Mapping[str, object], ledger["pricing"])
    schema_version = cast(str, ledger["schema_version"])
    amendment = _validate_authority_amendment(
        ledger.get("authority_amendment"),
        authorization=authorization,
        limits=limits,
        pricing=pricing,
        schema_version=schema_version,
    )
    if (
        amendment is not None
        and amendment.get("source_amendment_digest")
        != source_amendment_digest
    ):
        raise RuntimeError(
            "replicate campaign already has a different authority amendment"
        )
    if amendment is not None:
        recorded_limit = _finite_float(
            amendment.get("new_maximum_estimated_cost_per_call_usd")
        )
        if (
            amendment.get("approved_at") != approved_at
            or amendment.get("reason") != reason
            or recorded_limit is None
            or not isclose(recorded_limit, new_limit)
        ):
            raise RuntimeError(
                "replicate campaign source amendment parameters changed"
            )
        recorded_old_limit = _finite_float(
            amendment["old_maximum_estimated_cost_per_call_usd"]
        )
        if recorded_old_limit is None:
            raise RuntimeError(
                "replicate campaign source amendment old limit is invalid"
            )
        old_limit = recorded_old_limit
        existing_call = next(
            (
                call
                for call in _ledger_calls(ledger)
                if call.get("call_id") == amendment.get("call_id")
            ),
            None,
        )
        if existing_call is None:
            raise RuntimeError("replicate campaign amended call is missing")
        if existing_call.get("state") == "completed":
            _validate_reauthorization_evidence(
                existing_call,
                amendment_digest=cast(
                    str,
                    amendment["authority_amendment_digest"],
                ),
                approved_at=approved_at,
            )
            with open_result_store_session(context.result_store) as session:
                _campaign_state(context, ledger, session)
            return ledger
    else:
        old_limit = _per_call_cost_limit(ledger)
        budget = _finite_float(authorization.get("budget_usd"))
        if (
            new_limit <= old_limit
            or isclose(new_limit, old_limit)
            or budget is None
            or new_limit > budget
        ):
            raise ValueError(
                "new per-call limit must increase the old limit without "
                "exceeding the total budget"
            )

    with open_result_store_session(context.result_store) as session:
        call, result = _validate_cost_stop_for_reauthorization(
            context,
            ledger,
            session,
            old_limit=old_limit,
            new_limit=new_limit,
            allow_reauthorized=amendment is not None,
        )

    if amendment is None:
        unchanged_authority = {
            "campaign_id": authorization.get("campaign_id"),
            "schedule_digest": authorization.get("schedule_digest"),
            "budget_usd": authorization.get("budget_usd"),
            "maximum_paid_calls": limits.get("maximum_paid_calls"),
            "cell_retries": limits.get("cell_retries"),
            "pricing_version": pricing.get("pricing_version"),
            "scoring_config_digest": pricing.get("scoring_config_digest"),
        }
        amendment_payload: dict[str, object] = {
            "schema_version": CAMPAIGN_AUTHORITY_AMENDMENT_SCHEMA_VERSION,
            "previous_campaign_authority_digest": ledger[
                "campaign_authority_digest"
            ],
            "source_amendment_digest": source_amendment_digest,
            "approved_at": approved_at,
            "reason": reason,
            "call_id": call["call_id"],
            "result_id": result.result_id,
            "result_digest": result.result_digest,
            "result_estimated_cost_usd": result.cost["total_cost"],
            "old_maximum_estimated_cost_per_call_usd": old_limit,
            "new_maximum_estimated_cost_per_call_usd": new_limit,
            "unchanged_authority": unchanged_authority,
        }
        amendment = {
            **amendment_payload,
            "authority_amendment_digest": canonical_digest(amendment_payload),
        }
        updated_limits = dict(limits)
        updated_limits["maximum_estimated_cost_per_call_usd"] = new_limit
        updated_ledger = dict(ledger)
        updated_ledger["limits"] = updated_limits
        updated_ledger["authority_amendment"] = amendment
        updated_ledger["campaign_authority_digest"] = _campaign_authority_digest(
            authorization,
            updated_limits,
            pricing,
            schema_version=schema_version,
            authority_amendment=amendment,
        )
        updated_ledger["updated_at"] = utc_now_timestamp()
        write_json(context.ledger_path, updated_ledger)
        ledger = _load_and_validate_ledger(context)

    amendment_digest = cast(str, amendment["authority_amendment_digest"])
    calls = _ledger_calls(ledger)
    amended_call = next(
        (
            candidate
            for candidate in calls
            if candidate.get("call_id") == amendment["call_id"]
        ),
        None,
    )
    if amended_call is None:
        raise RuntimeError("replicate campaign amended call is missing")
    if amended_call.get("state") == "stopped":
        append_ledger_event(
            ledger_events_path(context.ledger_path),
            {
                "event_type": "reauthorization",
                "call_id": amendment["call_id"],
                "authority_amendment_digest": amendment_digest,
                "reauthorized_at": approved_at,
            },
        )
    elif amended_call.get("state") == "completed":
        _validate_reauthorization_evidence(
            amended_call,
            amendment_digest=amendment_digest,
            approved_at=approved_at,
        )
    else:
        raise RuntimeError("replicate campaign amended call state is invalid")

    ledger = _load_and_validate_ledger(context)
    with open_result_store_session(context.result_store) as session:
        _campaign_state(context, ledger, session)
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
    *,
    schema_version: str = CAMPAIGN_LEDGER_SCHEMA_VERSION,
    authority_amendment: Mapping[str, object] | None = None,
) -> str:
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "authorization": authorization,
        "limits": limits,
        "pricing": pricing,
    }
    if authority_amendment is not None:
        payload["authority_amendment"] = authority_amendment
    return canonical_digest(payload)


def _validate_authority_amendment(
    value: object,
    *,
    authorization: Mapping[str, object],
    limits: Mapping[str, object],
    pricing: Mapping[str, object],
    schema_version: str,
) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise RuntimeError("replicate campaign authority amendment is invalid")
    amendment = cast(Mapping[str, object], value)
    final_limit = _finite_float(
        limits.get("maximum_estimated_cost_per_call_usd")
    )
    budget = _finite_float(authorization.get("budget_usd"))
    if final_limit is None or budget is None:
        raise RuntimeError("replicate campaign amendment authority is invalid")
    expected_fields = {
        "schema_version",
        "authority_amendment_digest",
        "previous_campaign_authority_digest",
        "source_amendment_digest",
        "approved_at",
        "reason",
        "call_id",
        "result_id",
        "result_digest",
        "result_estimated_cost_usd",
        "old_maximum_estimated_cost_per_call_usd",
        "new_maximum_estimated_cost_per_call_usd",
        "unchanged_authority",
    }
    if set(amendment) != expected_fields:
        raise RuntimeError(
            "replicate campaign authority amendment fields are invalid"
        )
    if (
        amendment.get("schema_version")
        != CAMPAIGN_AUTHORITY_AMENDMENT_SCHEMA_VERSION
    ):
        raise RuntimeError(
            "replicate campaign authority amendment schema is unsupported"
        )
    amendment_digest = amendment.get("authority_amendment_digest")
    payload = dict(amendment)
    payload.pop("authority_amendment_digest")
    if (
        not isinstance(amendment_digest, str)
        or not amendment_digest
        or canonical_digest(payload) != amendment_digest
    ):
        raise RuntimeError(
            "replicate campaign authority amendment digest does not match"
        )
    for field_name in (
        "previous_campaign_authority_digest",
        "source_amendment_digest",
        "approved_at",
        "reason",
        "call_id",
        "result_id",
        "result_digest",
    ):
        field_value = amendment.get(field_name)
        if not isinstance(field_value, str) or not field_value:
            raise RuntimeError(
                f"replicate campaign authority amendment {field_name} is invalid"
            )
    try:
        _validate_approved_at(amendment["approved_at"])
    except ValueError as exc:
        raise RuntimeError(
            "replicate campaign authority amendment approved_at is invalid"
        ) from exc
    old_limit = _finite_float(
        amendment.get("old_maximum_estimated_cost_per_call_usd")
    )
    new_limit = _finite_float(
        amendment.get("new_maximum_estimated_cost_per_call_usd")
    )
    result_cost = _finite_float(amendment.get("result_estimated_cost_usd"))
    if (
        old_limit is None
        or new_limit is None
        or result_cost is None
        or old_limit <= 0
        or new_limit <= old_limit
        or new_limit > budget
        or result_cost <= old_limit
        or result_cost > new_limit
        or not isclose(new_limit, final_limit)
    ):
        raise RuntimeError(
            "replicate campaign authority amendment cost bounds are invalid"
        )
    expected_unchanged = {
        "campaign_id": authorization.get("campaign_id"),
        "schedule_digest": authorization.get("schedule_digest"),
        "budget_usd": authorization.get("budget_usd"),
        "maximum_paid_calls": limits.get("maximum_paid_calls"),
        "cell_retries": limits.get("cell_retries"),
        "pricing_version": pricing.get("pricing_version"),
        "scoring_config_digest": pricing.get("scoring_config_digest"),
    }
    if amendment.get("unchanged_authority") != expected_unchanged:
        raise RuntimeError(
            "replicate campaign authority amendment changed frozen authority"
        )
    old_limits = dict(limits)
    old_limits["maximum_estimated_cost_per_call_usd"] = old_limit
    expected_previous_digest = _campaign_authority_digest(
        authorization,
        old_limits,
        pricing,
        schema_version=schema_version,
    )
    if (
        amendment.get("previous_campaign_authority_digest")
        != expected_previous_digest
    ):
        raise RuntimeError(
            "replicate campaign authority amendment does not bind prior authority"
        )
    return amendment


def _campaign_ledger_schema_version(schedule: ReplicateSchedule) -> str:
    if schedule.schema_version == SINGLE_AGENT_CANARY_SCHEMA_VERSION:
        return CANARY_CAMPAIGN_LEDGER_SCHEMA_VERSION
    return CAMPAIGN_LEDGER_SCHEMA_VERSION


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
    expected_schema_version = _campaign_ledger_schema_version(context.schedule)
    if ledger.get("schema_version") != expected_schema_version:
        raise RuntimeError("replicate campaign ledger schema is not supported")
    authority_amendment = _validate_authority_amendment(
        ledger.get("authority_amendment"),
        authorization=authorization,
        limits=limits,
        pricing=pricing,
        schema_version=expected_schema_version,
    )
    observed_authority_digest = ledger.get("campaign_authority_digest")
    expected_authority_digest = _campaign_authority_digest(
        authorization,
        limits,
        pricing,
        schema_version=expected_schema_version,
        authority_amendment=authority_amendment,
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


def _validate_cost_stop_for_reauthorization(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    session: ResultStoreSession,
    *,
    old_limit: float,
    new_limit: float,
    allow_reauthorized: bool,
) -> tuple[Mapping[str, object], ResultRecord]:
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
    calls = _ledger_calls(ledger)
    if not calls or len(calls) > len(resolved):
        raise RuntimeError(
            "replicate campaign has no terminal stopped call to reauthorize"
        )
    terminal_index = len(calls) - 1
    old_limit_ledger = _ledger_with_per_call_limit(ledger, old_limit)
    new_limit_ledger = _ledger_with_per_call_limit(ledger, new_limit)
    terminal_call: Mapping[str, object] | None = None
    terminal_result: ResultRecord | None = None
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
        if index < terminal_index:
            if call.get("state") != "completed" or len(results) != 1:
                raise RuntimeError(
                    "replicate campaign prefix is not completely scoreable"
                )
            result = results[0]
            _validate_call_result(call, result)
            _validate_paid_result(
                context,
                old_limit_ledger,
                result,
                include_recorded_spend=False,
            )
            continue
        allowed_states = {"stopped", "completed"} if allow_reauthorized else {"stopped"}
        if call.get("state") not in allowed_states:
            raise RuntimeError(
                "replicate campaign terminal call is not an eligible cost stop"
            )
        if call.get("stop_reason") != "RuntimeError" or len(results) != 1:
            raise RuntimeError(
                "replicate campaign terminal stop lacks one exact cost Result"
            )
        result = results[0]
        _validate_call_result(call, result)
        _validate_paid_result(
            context,
            new_limit_ledger,
            result,
            include_recorded_spend=False,
        )
        result_cost = _finite_float(result.cost.get("total_cost"))
        if (
            result_cost is None
            or result_cost < old_limit
            or isclose(result_cost, old_limit)
        ):
            raise RuntimeError(
                "replicate campaign terminal Result did not exceed the old limit"
            )
        terminal_call = call
        terminal_result = result
    if terminal_call is None or terminal_result is None:
        raise RuntimeError(
            "replicate campaign terminal stopped Result could not be resolved"
        )
    return terminal_call, terminal_result


def _ledger_with_per_call_limit(
    ledger: Mapping[str, object],
    per_call_limit: float,
) -> Mapping[str, object]:
    limits = ledger.get("limits")
    if not isinstance(limits, Mapping):
        raise RuntimeError("replicate campaign limits are missing")
    updated = dict(ledger)
    updated["limits"] = {
        **limits,
        "maximum_estimated_cost_per_call_usd": per_call_limit,
    }
    return updated


def _validate_reauthorization_evidence(
    call: Mapping[str, object],
    *,
    amendment_digest: str,
    approved_at: str,
) -> None:
    if call.get("reauthorized_after_stop") != {
        "authority_amendment_digest": amendment_digest,
        "reauthorized_at": approved_at,
    }:
        raise RuntimeError(
            "replicate campaign reauthorization evidence does not match"
        )


def _validate_calls_and_results(
    context: ReplicateCampaignContext,
    ledger: Mapping[str, object],
    resolved: tuple[ResolvedReplicateScheduleCell, ...],
    session: ResultStoreSession,
) -> None:
    calls = _ledger_calls(ledger)
    raw_amendment = ledger.get("authority_amendment")
    if raw_amendment is not None and not isinstance(raw_amendment, Mapping):
        raise RuntimeError("replicate campaign authority amendment is invalid")
    authority_amendment = cast(
        Mapping[str, object] | None,
        raw_amendment,
    )
    amendment_consumed = False
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
        if (
            authority_amendment is not None
            and authority_amendment.get("call_id") == call.get("call_id")
        ):
            _validate_reauthorization_evidence(
                call,
                amendment_digest=cast(
                    str,
                    authority_amendment["authority_amendment_digest"],
                ),
                approved_at=cast(str, authority_amendment["approved_at"]),
            )
            if (
                authority_amendment.get("result_id") != result.result_id
                or authority_amendment.get("result_digest") != result.result_digest
                or authority_amendment.get("result_estimated_cost_usd")
                != result.cost["total_cost"]
            ):
                raise RuntimeError(
                    "replicate campaign amendment Result evidence does not match"
                )
            amendment_consumed = True
    if authority_amendment is not None and not amendment_consumed:
        raise RuntimeError(
            "replicate campaign authority amendment call is missing"
        )


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
