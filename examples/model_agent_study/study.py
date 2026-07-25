#!/usr/bin/env python3
"""Run the staged, quota-accounted coding-agent/model study."""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any, cast
import urllib.error
import urllib.parse
import urllib.request


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    CheckRecord,
    ResultRecord,
    RuntimeConfig,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    parse_utc_timestamp,
    validate_agent,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultStore,
    ScoringConfig,
    compute_cost,
)
from barcarolle.workspace import (  # noqa: E402
    WorkspaceArtifactConfig,
    WorkspaceRunContext,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    harness_content_digest,
    make_openai_env_network_policy_digest,
    resolve_openai_endpoint_digest,
)
from examples.experiment_ledger import write_json  # noqa: E402
from examples.pylint_swe_bench_verified.pilot import (  # noqa: E402
    DEFAULT_DATASET_NAME,
    DEFAULT_SUPPLEMENTAL_DATASET_NAME,
    HARNESS,
    PilotPaths,
    build_context as build_pilot_context,
    verify_pylint_verifier_images,
)
from examples.pylint_swe_bench_verified.replicate_campaign import (  # noqa: E402
    ReplicateCampaignContext,
    initialize_replicate_campaign_ledger,
    preflight_replicate_campaign,
    run_next_replicate_campaign_cell,
)
from examples.pylint_swe_bench_verified.replicate_schedule import (  # noqa: E402
    ReplicateSchedule,
    ReplicateScheduleCell,
    ResolvedReplicateScheduleCell,
    build_replicate_schedule,
    build_single_agent_canary_schedule,
)
from barcarolle.task_pool import (  # noqa: E402
    PreparedCandidatePackage,
    TaskPoolBundle,
    load_prepared_candidate_package,
    open_task_pool_bundle,
    prepared_candidate_build_inputs,
)
from examples.swe_bench_static.certify_pool import (  # noqa: E402
    certification_configs,
    verify_images,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "study-plan.json"
DEFAULT_AMENDMENT = HERE / "study-amendment-1.json"
DEFAULT_DECISION_AMENDMENT = HERE / "study-amendment-2.json"
DEFAULT_STUDY_OUTPUT = Path("outputs/research/2026-07-25-model-agent-study")
DEFAULT_PILOT_OUTPUT = DEFAULT_STUDY_OUTPUT / "pylint-pool"
STUDY_LEDGER_NAME = "resource-ledger.json"
CAMPAIGN_METADATA_NAME = "campaign-metadata.json"
MAIN_CAMPAIGN_ID = "model-main-sympy-2026-07-25"
QUOTA_CHECKPOINT_CELL_INTERVAL = 6
QUOTA_CHECKPOINT_MAX_AGE_SECONDS = 300


@dataclass(frozen=True)
class StudyPaths:
    plan_path: Path
    study_output: Path
    pilot_output: Path


@dataclass(frozen=True)
class StaticSourceContext:
    package: PreparedCandidatePackage
    bundle: TaskPoolBundle
    workspace_config: WorkspaceConfig
    checks: tuple[CheckRecord, ...]
    run_context: WorkspaceRunContext


@dataclass(frozen=True)
class AccountedCall:
    result: ResultRecord
    quota_before: Mapping[str, int]
    quota_after: Mapping[str, int] | None
    gateway_log_receipt: Mapping[str, Any] | None


class GatewayReceiptIncomplete(RuntimeError):
    """The Result is durable but its successful token-log rows are not complete."""


def _accounted_balance_delta(call: AccountedCall) -> int | None:
    if call.quota_after is None:
        return None
    return call.quota_after["total_used"] - call.quota_before["total_used"]


def _accounted_receipt_quota(call: AccountedCall) -> int | None:
    if call.gateway_log_receipt is None:
        return None
    return cast(int, call.gateway_log_receipt["quota_points"])


def prepare_calibration(paths: StudyPaths) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    calibration = _required_mapping(plan, "calibration")
    campaigns = _required_mapping_sequence(calibration, "campaigns")
    summaries = [
        _prepare_calibration_campaign(
            paths,
            plan,
            campaign_config,
            endpoint_digest=endpoint_digest,
            approved_at=_required_string(plan, "approved_at"),
            decision_amendment_digest=None,
        )
        for campaign_config in campaigns
    ]
    summary = {
        "stage": "calibration_authorized",
        "study_plan_digest": plan["study_plan_digest"],
        "endpoint_digest": endpoint_digest,
        "campaigns": summaries,
        "maximum_paid_calls": sum(item["cell_count"] for item in summaries),
        "next": "preflight each campaign, then run the first two-cell canary block",
    }
    write_json(paths.study_output / "calibration-authority-summary.json", summary)
    return summary


def prepare_replacement_calibration(
    paths: StudyPaths,
    decision_amendment_path: Path,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    protocol = _load_json(paths.study_output / "protocol-canary-summary.json")
    if (
        protocol.get("stage") != "complete"
        or protocol.get("study_plan_digest") != plan["study_plan_digest"]
        or protocol.get("study_amendment_digest")
        != decision["previous_amendment_digest"]
        or protocol.get("eligible_agent_keys")
        != decision["canary_eligible_agent_keys"]
    ):
        raise RuntimeError("protocol canary evidence does not match amendment 2")
    endpoint_digest = _activate_llm_proxy_environment(plan)
    campaigns = _required_mapping_sequence(
        decision,
        "replacement_calibration_campaigns",
    )
    summaries = [
        _prepare_calibration_campaign(
            paths,
            plan,
            campaign_config,
            endpoint_digest=endpoint_digest,
            approved_at=_required_string(decision, "approved_at"),
            decision_amendment_digest=_required_string(
                decision,
                "amendment_digest",
            ),
        )
        for campaign_config in campaigns
    ]
    summary = {
        "stage": "replacement_calibration_authorized",
        "study_plan_digest": plan["study_plan_digest"],
        "study_decision_amendment_digest": decision["amendment_digest"],
        "endpoint_digest": endpoint_digest,
        "campaigns": summaries,
        "maximum_paid_calls": sum(item["cell_count"] for item in summaries),
    }
    write_json(
        paths.study_output / "replacement-calibration-authority-summary.json",
        summary,
    )
    return summary


def _prepare_calibration_campaign(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    campaign_config: Mapping[str, Any],
    *,
    endpoint_digest: str,
    approved_at: str,
    decision_amendment_digest: str | None,
) -> Mapping[str, Any]:
    calibration = _required_mapping(plan, "calibration")
    models = _required_mapping(plan, "models")
    campaign_id = _required_string(campaign_config, "campaign_id")
    campaign_dir = paths.study_output / "calibration" / campaign_id
    if campaign_dir.exists():
        raise FileExistsError(
            f"refusing to overwrite calibration campaign: {campaign_dir}"
        )
    campaign_dir.mkdir(parents=True)
    records_dir = campaign_dir / "records"
    records_dir.mkdir()
    pilot = build_pilot_context(
        _pilot_paths(paths.pilot_output),
        campaign_dir / "campaign-ledger.json",
    )
    agent_keys = _required_string_sequence(campaign_config, "agent_keys")
    if len(agent_keys) != 2 or len(set(agent_keys)) != 2:
        raise ValueError("calibration campaign requires two unique agent keys")
    agents = tuple(
        _build_agent(
            model_key=agent_key,
            model_config=_required_mapping(models, agent_key),
            campaign_id=campaign_id,
            campaign_dir=campaign_dir,
            tasks=pilot.tasks,
            plan=plan,
            endpoint_digest=endpoint_digest,
        )
        for agent_key in agent_keys
    )
    runtime = _base_runtime_config(campaign_id, agents, timeout_seconds=900)
    schedule = build_replicate_schedule(
        pilot.task_pool,
        pilot.tasks,
        tuple(pilot.checks.values()),
        agents,
        runtime,
        campaign_id=campaign_id,
        seed=_required_int(calibration, "schedule_seed"),
        replicate_fraction=_required_number(calibration, "replicate_fraction"),
        replicate_count=_required_int(calibration, "replicate_count"),
    )
    scoring = ScoringConfig(
        pricing_version=f"gateway-conservative-{campaign_id}",
        cost_rates=_numeric_mapping(
            _required_mapping(campaign_config, "authority_rates"),
            "authority_rates",
        ),
    )
    context = _calibration_context(
        pilot=pilot,
        campaign_dir=campaign_dir,
        agents=agents,
        runtime=runtime,
        schedule=schedule,
        scoring=scoring,
    )
    write_jsonl_records(records_dir / "agents.jsonl", agents)
    write_jsonl_records(records_dir / "runtime-config.jsonl", (runtime,))
    write_jsonl_records(records_dir / "replicate-schedule.jsonl", (schedule,))
    metadata = {
        "schema_version": "model_calibration_campaign_v1",
        "study_plan_digest": plan["study_plan_digest"],
        "study_decision_amendment_digest": decision_amendment_digest,
        "campaign_id": campaign_id,
        "agent_keys": list(agent_keys),
        "agent_pricing": {
            agent_key: canonical_data_mapping(
                _required_mapping(
                    _required_mapping(models, agent_key),
                    "pricing",
                )
            )
            for agent_key in agent_keys
        },
        "scoring_config": {
            "pricing_version": scoring.pricing_version,
            "cost_rates": dict(scoring.cost_rates),
            "scoring_config_digest": scoring.scoring_config_digest,
        },
        "endpoint_digest": endpoint_digest,
        "task_pool_id": pilot.task_pool.task_pool_id,
        "task_pool_digest": pilot.task_pool.task_pool_digest,
        "schedule_digest": schedule.schedule_digest,
    }
    write_json(campaign_dir / CAMPAIGN_METADATA_NAME, metadata)
    ledger = initialize_replicate_campaign_ledger(
        context,
        approved_at=approved_at,
        endpoint_digest=endpoint_digest,
        maximum_estimated_cost_usd=_required_number(
            campaign_config,
            "maximum_estimated_cost_usd",
        ),
        maximum_estimated_cost_per_call_usd=_required_number(
            campaign_config,
            "maximum_estimated_cost_per_call_usd",
        ),
        pricing_sources=(
            "authenticated gateway /api/pricing view observed 2026-07-25",
        ),
        accounting_basis=(
            "per-pair conservative token rates; final Results are repriced "
            "per exact Agent and reconciled to gateway quota"
        ),
        scope=(
            "frozen 10-task Pylint calibration with two deterministic "
            "replicate Tasks"
        ),
    )
    return {
        "campaign_id": campaign_id,
        "agent_ids": [agent.agent_id for agent in agents],
        "cell_count": len(schedule.cells),
        "replicated_task_count": len(schedule.replicated_task_ids),
        "maximum_estimated_cost_usd": (
            _required_mapping(ledger, "authorization")["budget_usd"]
        ),
        "campaign_dir": str(campaign_dir.resolve()),
    }


def prepare_protocol_canaries(
    paths: StudyPaths,
    amendment_path: Path,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    models = _required_mapping(plan, "models")
    canary_task_id = _required_string(
        _required_mapping(amendment, "canary_task"),
        "task_id",
    )
    summaries: list[Mapping[str, Any]] = []
    for config in _required_mapping_sequence(amendment, "canaries"):
        campaign_id = _required_string(config, "campaign_id")
        campaign_dir = paths.study_output / "calibration-canaries" / campaign_id
        if campaign_dir.exists():
            raise FileExistsError(
                f"refusing to overwrite protocol canary: {campaign_dir}"
            )
        campaign_dir.mkdir(parents=True)
        records_dir = campaign_dir / "records"
        records_dir.mkdir()
        pilot = build_pilot_context(
            _pilot_paths(paths.pilot_output),
            campaign_dir / "campaign-ledger.json",
        )
        agent_key = _required_string(config, "agent_key")
        model_config = _required_mapping(models, agent_key)
        agents = (
            _build_agent(
                model_key=agent_key,
                model_config=model_config,
                campaign_id=campaign_id,
                campaign_dir=campaign_dir,
                tasks=pilot.tasks,
                plan=plan,
                endpoint_digest=endpoint_digest,
            ),
        )
        runtime = _base_runtime_config(campaign_id, agents, timeout_seconds=900)
        schedule = build_single_agent_canary_schedule(
            pilot.task_pool,
            pilot.tasks,
            tuple(pilot.checks.values()),
            agents,
            runtime,
            campaign_id=campaign_id,
            seed=_required_int(
                _required_mapping(plan, "calibration"),
                "schedule_seed",
            ),
            task_id=canary_task_id,
        )
        pricing = _required_mapping(model_config, "pricing")
        scoring = ScoringConfig(
            _required_string(pricing, "pricing_version"),
            {
                key: _required_number(pricing, key)
                for key in (
                    "uncached_input_tokens",
                    "cached_input_tokens",
                    "output_tokens",
                )
            },
        )
        context = _calibration_context(
            pilot=pilot,
            campaign_dir=campaign_dir,
            agents=agents,
            runtime=runtime,
            schedule=schedule,
            scoring=scoring,
        )
        write_jsonl_records(records_dir / "agents.jsonl", agents)
        write_jsonl_records(records_dir / "runtime-config.jsonl", (runtime,))
        write_jsonl_records(records_dir / "replicate-schedule.jsonl", (schedule,))
        metadata = {
            "schema_version": "model_protocol_canary_v1",
            "study_plan_digest": plan["study_plan_digest"],
            "study_amendment_digest": amendment["amendment_digest"],
            "campaign_id": campaign_id,
            "agent_key": agent_key,
            "endpoint_digest": endpoint_digest,
            "task_pool_id": pilot.task_pool.task_pool_id,
            "task_pool_digest": pilot.task_pool.task_pool_digest,
            "schedule_digest": schedule.schedule_digest,
            "scoring_config": {
                "pricing_version": scoring.pricing_version,
                "cost_rates": dict(scoring.cost_rates),
                "scoring_config_digest": scoring.scoring_config_digest,
            },
            "maximum_estimated_cost_usd": _required_number(
                config,
                "maximum_estimated_cost_usd",
            ),
            "maximum_estimated_cost_per_call_usd": _required_number(
                config,
                "maximum_estimated_cost_per_call_usd",
            ),
        }
        write_json(campaign_dir / CAMPAIGN_METADATA_NAME, metadata)
        initialize_replicate_campaign_ledger(
            context,
            approved_at=_required_string(amendment, "approved_at"),
            endpoint_digest=endpoint_digest,
            maximum_estimated_cost_usd=_required_number(
                config,
                "maximum_estimated_cost_usd",
            ),
            maximum_estimated_cost_per_call_usd=_required_number(
                config,
                "maximum_estimated_cost_per_call_usd",
            ),
            pricing_sources=(
                "authenticated gateway /api/pricing view observed 2026-07-25",
            ),
            accounting_basis=(
                "one exact Agent price; provider quota reconciled around the call"
            ),
            scope=(
                "one frozen Pylint Task used only to establish Codex Responses "
                "protocol, usage, pricing, and scoreability compatibility"
            ),
        )
        summaries.append(
            {
                "campaign_id": campaign_id,
                "agent_key": agent_key,
                "agent_id": agents[0].agent_id,
                "task_id": canary_task_id,
                "schedule_digest": schedule.schedule_digest,
            }
        )
    summary = {
        "stage": "protocol_canaries_authorized",
        "study_plan_digest": plan["study_plan_digest"],
        "study_amendment_digest": amendment["amendment_digest"],
        "endpoint_digest": endpoint_digest,
        "canaries": summaries,
        "maximum_paid_calls": len(summaries),
    }
    write_json(paths.study_output / "protocol-canary-authority-summary.json", summary)
    return summary


def preflight_protocol_canary(
    paths: StudyPaths,
    amendment_path: Path,
    campaign_id: str,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    config = _canary_config(amendment, campaign_id)
    context, metadata = _load_canary_context(paths, plan, amendment, config)
    images = verify_pylint_verifier_images(context.tasks)
    next_cell = preflight_replicate_campaign(context)
    quota = _gateway_quota()
    _require_study_budget_guard(paths, plan, quota, config)
    _record_live_quota_checkpoint(paths, plan, quota, "protocol_canary_preflight")
    summary = {
        "stage": "preflight_passed" if next_cell is not None else "complete",
        "campaign_id": campaign_id,
        "study_plan_digest": plan["study_plan_digest"],
        "study_amendment_digest": amendment["amendment_digest"],
        "schedule_digest": context.schedule.schedule_digest,
        "endpoint_digest": endpoint_digest,
        "verified_image_count": len(images),
        "gateway_total_used": quota["total_used"],
        "next_sequence_index": (
            None if next_cell is None else next_cell.schedule_cell.sequence_index
        ),
    }
    if metadata.get("schedule_digest") != summary["schedule_digest"]:
        raise RuntimeError("protocol canary metadata does not bind its schedule")
    campaign_dir = paths.study_output / "calibration-canaries" / campaign_id
    write_json(campaign_dir / "preflight-summary.json", summary)
    return summary


def run_next_protocol_canary(
    paths: StudyPaths,
    amendment_path: Path,
    campaign_id: str,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    _activate_llm_proxy_environment(plan)
    config = _canary_config(amendment, campaign_id)
    context, _ = _load_canary_context(paths, plan, amendment, config)
    campaign_dir = paths.study_output / "calibration-canaries" / campaign_id
    _require_preflight_marker(campaign_dir, plan, context)
    next_cell = preflight_replicate_campaign(context)
    if next_cell is None:
        return {"stage": "complete", "campaign_id": campaign_id}
    accounted = _run_accounted_campaign_cell(
        paths,
        plan,
        config,
        context,
        campaign_dir,
        next_cell,
    )
    result = accounted.result
    return {
        "stage": "canary_recorded",
        "campaign_id": campaign_id,
        "agent_id": result.agent_id,
        "task_id": result.task_id,
        "outcome": result.outcome,
        "scoreable_state": result.scoreable_state,
        "estimated_cost_usd": result.cost["total_cost"],
        "gateway_balance_window_delta": _accounted_balance_delta(accounted),
        "gateway_log_quota_points": _accounted_receipt_quota(accounted),
        "gateway_log_cost_usd": (
            None
            if _accounted_receipt_quota(accounted) is None
            else cast(int, _accounted_receipt_quota(accounted))
            / _required_int(
                _required_mapping(plan, "budget"),
                "quota_points_per_usd",
            )
        ),
    }


def summarize_protocol_canaries(
    paths: StudyPaths,
    amendment_path: Path,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    rows: list[Mapping[str, Any]] = []
    for config in _required_mapping_sequence(amendment, "canaries"):
        campaign_id = _required_string(config, "campaign_id")
        campaign_dir = paths.study_output / "calibration-canaries" / campaign_id
        results = tuple(
            load_jsonl_records(
                campaign_dir / "records" / "results.jsonl",
                ResultRecord,
            )
        )
        if len(results) != 1:
            raise RuntimeError(
                f"protocol canary lacks one exact Result: {campaign_id}"
            )
        result = results[0]
        cost = _optional_result_number(result.cost, "total_cost")
        eligible = (
            result.scoreable_state == "scoreable"
            and bool(result.usage)
            and cost is not None
        )
        rows.append(
            {
                "campaign_id": campaign_id,
                "agent_key": _required_string(config, "agent_key"),
                "agent_id": result.agent_id,
                "result_id": result.result_id,
                "scoreable_state": result.scoreable_state,
                "terminal_status": result.terminal_status,
                "outcome": result.outcome,
                "failure_label": result.failure_label,
                "usage_observed": bool(result.usage),
                "estimated_cost_usd": cost,
                "replacement_calibration_eligible": eligible,
                "capability_interpretation": (
                    "not evaluated by protocol canary"
                    if not eligible
                    else "hidden outcome retained but not used for eligibility"
                ),
            }
        )
    summary = {
        "schema_version": "model_protocol_canary_summary_v1",
        "study_plan_digest": plan["study_plan_digest"],
        "study_amendment_digest": amendment["amendment_digest"],
        "stage": "complete",
        "canaries": rows,
        "eligible_agent_keys": [
            row["agent_key"]
            for row in rows
            if row["replacement_calibration_eligible"]
        ],
        "claim_boundary": amendment["claim_boundary"],
    }
    write_json(paths.study_output / "protocol-canary-summary.json", summary)
    return summary


def preflight_calibration_campaign(
    paths: StudyPaths,
    campaign_id: str,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    campaign_config = _calibration_campaign_config(
        plan,
        campaign_id,
        decision,
    )
    context = _load_calibration_context(
        paths,
        plan,
        campaign_config,
        decision,
    )
    images = verify_pylint_verifier_images(context.tasks)
    next_cell = preflight_replicate_campaign(context)
    quota = _gateway_quota()
    _require_study_budget_guard(paths, plan, quota, campaign_config)
    _record_live_quota_checkpoint(paths, plan, quota, "calibration_preflight")
    summary = {
        "stage": "preflight_passed" if next_cell is not None else "complete",
        "campaign_id": campaign_id,
        "study_plan_digest": plan["study_plan_digest"],
        "schedule_digest": context.schedule.schedule_digest,
        "endpoint_digest": endpoint_digest,
        "verified_image_count": len(images),
        "gateway_total_used": quota["total_used"],
        "next_sequence_index": (
            None if next_cell is None else next_cell.schedule_cell.sequence_index
        ),
    }
    write_json(
        paths.study_output / "calibration" / campaign_id / "preflight-summary.json",
        summary,
    )
    return summary


def run_next_calibration_cell(
    paths: StudyPaths,
    campaign_id: str,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    _activate_llm_proxy_environment(plan)
    campaign_config = _calibration_campaign_config(
        plan,
        campaign_id,
        decision,
    )
    campaign_dir = paths.study_output / "calibration" / campaign_id
    context = _load_calibration_context(
        paths,
        plan,
        campaign_config,
        decision,
    )
    _require_preflight_marker(campaign_dir, plan, context)
    next_cell = preflight_replicate_campaign(context)
    if next_cell is None:
        return {"stage": "complete", "campaign_id": campaign_id}
    accounted = _run_accounted_campaign_cell(
        paths,
        plan,
        campaign_config,
        context,
        campaign_dir,
        next_cell,
    )
    result = accounted.result
    return {
        "stage": "cell_recorded",
        "campaign_id": campaign_id,
        "sequence_index": next_cell.schedule_cell.sequence_index,
        "agent_id": result.agent_id,
        "task_id": result.task_id,
        "replicate_index": next_cell.schedule_cell.replicate_index,
        "outcome": result.outcome,
        "scoreable_state": result.scoreable_state,
        "estimated_cost_usd": result.cost["total_cost"],
        "gateway_balance_window_delta": _accounted_balance_delta(accounted),
        "gateway_log_quota_points": _accounted_receipt_quota(accounted),
        "gateway_log_cost_usd": (
            None
            if _accounted_receipt_quota(accounted) is None
            else cast(int, _accounted_receipt_quota(accounted))
            / _required_int(
                _required_mapping(plan, "budget"),
                "quota_points_per_usd",
            )
        ),
    }


def summarize_calibration(
    paths: StudyPaths,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    campaigns = tuple(
        _calibration_campaign_config(plan, campaign_id, decision)
        for campaign_id in _required_string_sequence(
            decision,
            "analysis_campaign_ids",
        )
    )
    models = _required_mapping(plan, "models")
    canonical_value = _required_mapping(decision, "canonical_agent_campaigns")
    canonical_campaign_by_agent = {
        key: value
        for key, value in canonical_value.items()
        if isinstance(key, str)
        and key
        and isinstance(value, str)
        and value
    }
    if len(canonical_campaign_by_agent) != len(canonical_value):
        raise ValueError("canonical Agent campaigns must map strings to strings")
    study_ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    ledger_entries = _required_mapping_sequence(study_ledger, "entries")
    agent_rows: dict[str, dict[str, Any]] = {}
    base_outcome_by_agent_task: dict[tuple[str, str], str] = {}
    pairwise_rows: list[Mapping[str, Any]] = []
    panel_outcomes: dict[str, dict[tuple[str, str], str]] = {}
    repeat_cells = 0
    repeat_flips = 0
    for campaign_config in campaigns:
        campaign_id = _required_string(campaign_config, "campaign_id")
        campaign_dir = paths.study_output / "calibration" / campaign_id
        schedule = _one_record(
            campaign_dir / "records" / "replicate-schedule.jsonl",
            ReplicateSchedule,
        )
        results = tuple(
            load_jsonl_records(
                campaign_dir / "records" / "results.jsonl",
                ResultRecord,
            )
        )
        if len(results) != len(schedule.cells):
            raise RuntimeError(f"calibration campaign is incomplete: {campaign_id}")
        runtime_index_by_digest = {
            canonical_digest(runtime): index
            for index, runtime in enumerate(schedule.runtime_configs)
        }
        result_by_cell = {
            (
                result.agent_id,
                result.task_id,
                runtime_index_by_digest[result.cache_identity.runtime_config_digest],
            ): result
            for result in results
        }
        local_outcomes: dict[tuple[str, str], str] = {}
        for agent_key in _required_string_sequence(campaign_config, "agent_keys"):
            model_config = _required_mapping(models, agent_key)
            agent_id = _required_string(model_config, "agent_id")
            agent_results = tuple(
                result for result in results if result.agent_id == agent_id
            )
            base_results = tuple(
                result
                for result in agent_results
                if runtime_index_by_digest[result.cache_identity.runtime_config_digest]
                == 0
            )
            for result in base_results:
                local_outcomes[(agent_key, result.task_id)] = result.outcome
            if canonical_campaign_by_agent.get(agent_key) != campaign_id:
                continue
            if agent_key in agent_rows:
                raise RuntimeError(f"duplicate canonical Agent panel: {agent_key}")
            pricing = _required_mapping(model_config, "pricing")
            rates = {
                key: _required_number(pricing, key)
                for key in (
                    "uncached_input_tokens",
                    "cached_input_tokens",
                    "output_tokens",
                )
            }
            scoring = ScoringConfig(
                _required_string(pricing, "pricing_version"),
                rates,
            )
            repriced_cost = sum(
                cast(float, compute_cost(result.usage, scoring)["total_cost"])
                for result in agent_results
            )
            attributed_costs = [
                float(entry["gateway_log_cost_usd"])
                for entry in ledger_entries
                if entry.get("campaign_id") == campaign_id
                and entry.get("agent_id") == agent_id
                and isinstance(entry.get("gateway_log_cost_usd"), int | float)
                and not isinstance(entry.get("gateway_log_cost_usd"), bool)
            ]
            if len(attributed_costs) != len(agent_results):
                raise RuntimeError(
                    f"canonical Agent lacks exact gateway receipts: {agent_key}"
                )
            row = {
                "agent_key": agent_key,
                "agent_id": agent_id,
                "requested_model_id": _required_string(
                    model_config, "requested_model_id"
                ),
                "provider_family": _required_string(model_config, "provider_family"),
                "result_count": len(agent_results),
                "base_task_count": len(base_results),
                "scoreable_count": sum(
                    result.scoreable_state == "scoreable" for result in agent_results
                ),
                "base_pass_count": sum(
                    result.outcome == "pass" for result in base_results
                ),
                "repriced_estimated_cost_usd": repriced_cost,
                "attributed_gateway_cost_usd": sum(attributed_costs),
                "canonical_campaign_id": campaign_id,
                "workspace_seconds": sum(
                    _result_number(result.latency, "workspace_seconds")
                    for result in agent_results
                ),
            }
            agent_rows[agent_key] = row
            for result in base_results:
                base_outcome_by_agent_task[(agent_key, result.task_id)] = result.outcome
            for task_id in schedule.replicated_task_ids:
                first = result_by_cell[(agent_id, task_id, 0)]
                second = result_by_cell[(agent_id, task_id, 1)]
                repeat_cells += 1
                repeat_flips += int(first.outcome != second.outcome)
        panel_outcomes[campaign_id] = local_outcomes
        left_key, right_key = _required_string_sequence(campaign_config, "agent_keys")
        task_ids = sorted(
            task_id for key, task_id in local_outcomes if key == left_key
        )
        disagreements = sum(
            local_outcomes[(left_key, task_id)]
            != local_outcomes[(right_key, task_id)]
            for task_id in task_ids
        )
        pairwise_rows.append(
            {
                "campaign_id": campaign_id,
                "left_agent_key": left_key,
                "right_agent_key": right_key,
                "paired_task_count": len(task_ids),
                "disagreement_count": disagreements,
            }
        )
    if set(agent_rows) != set(canonical_campaign_by_agent):
        raise RuntimeError("canonical calibration panels are incomplete")
    all_keys = tuple(sorted(agent_rows))
    for left_index, left_key in enumerate(all_keys):
        for right_key in all_keys[left_index + 1 :]:
            paired_tasks = sorted(
                {
                    task_id
                    for key, task_id in base_outcome_by_agent_task
                    if key == left_key
                }
                & {
                    task_id
                    for key, task_id in base_outcome_by_agent_task
                    if key == right_key
                }
            )
            if not paired_tasks:
                continue
            if any(
                {row["left_agent_key"], row["right_agent_key"]}
                == {left_key, right_key}
                for row in pairwise_rows
            ):
                continue
            pairwise_rows.append(
                {
                    "campaign_id": "cross_panel_canonical_view",
                    "left_agent_key": left_key,
                    "right_agent_key": right_key,
                    "paired_task_count": len(paired_tasks),
                    "disagreement_count": sum(
                        base_outcome_by_agent_task[(left_key, task_id)]
                        != base_outcome_by_agent_task[(right_key, task_id)]
                        for task_id in paired_tasks
                    ),
                }
            )
    control_key = _required_string(decision, "control_agent_key")
    control_campaign = canonical_campaign_by_agent.get(control_key)
    if control_campaign is None:
        raise RuntimeError("amendment 2 control Agent lacks a canonical panel")
    control_tasks = {
        task_id
        for key, task_id in base_outcome_by_agent_task
        if key == control_key
    }
    control_bridges: list[Mapping[str, Any]] = []
    for campaign_id, outcomes in panel_outcomes.items():
        if campaign_id == control_campaign:
            continue
        bridge_tasks = sorted(
            control_tasks
            & {task_id for key, task_id in outcomes if key == control_key}
        )
        if not bridge_tasks:
            continue
        control_bridges.append(
            {
                "control_agent_key": control_key,
                "canonical_campaign_id": control_campaign,
                "bridge_campaign_id": campaign_id,
                "paired_task_count": len(bridge_tasks),
                "outcome_flip_count": sum(
                    base_outcome_by_agent_task[(control_key, task_id)]
                    != outcomes[(control_key, task_id)]
                    for task_id in bridge_tasks
                ),
            }
        )
    selected = _select_main_agents(
        plan,
        agent_rows,
        base_outcome_by_agent_task,
    )
    summary = {
        "schema_version": "model_calibration_summary_v1",
        "study_plan_digest": plan["study_plan_digest"],
        "study_decision_amendment_digest": decision["amendment_digest"],
        "stage": "complete",
        "agents": [agent_rows[key] for key in sorted(agent_rows)],
        "pairwise": sorted(
            pairwise_rows,
            key=lambda row: (
                row["left_agent_key"],
                row["right_agent_key"],
            ),
        ),
        "control_bridges": control_bridges,
        "repeatability": {
            "agent_task_repeat_cell_count": repeat_cells,
            "flip_count": repeat_flips,
            "observed_flip_rate": (
                repeat_flips / repeat_cells if repeat_cells else None
            ),
            "scope": "two executions on two frozen Pylint Tasks per Agent",
        },
        "selected_main_agent_keys": selected,
        "resource_totals": study_ledger["totals"],
        "claim_boundary": (
            "Calibration selects a main portfolio; it is not a universal "
            "leaderboard or prospective Selector evaluation."
        ),
    }
    write_json(paths.study_output / "calibration-summary.json", summary)
    return summary


def prepare_main(
    paths: StudyPaths,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    calibration = _load_json(paths.study_output / "calibration-summary.json")
    if (
        calibration.get("stage") != "complete"
        or calibration.get("study_plan_digest") != plan["study_plan_digest"]
        or calibration.get("study_decision_amendment_digest")
        != decision["amendment_digest"]
    ):
        raise RuntimeError("complete calibration evidence is required before main")
    selected = calibration.get("selected_main_agent_keys")
    if (
        not isinstance(selected, list | tuple)
        or len(selected) != 2
        or any(not isinstance(item, str) or not item for item in selected)
    ):
        raise RuntimeError("calibration did not select two main Agents")
    selected_keys = cast(tuple[str, str], tuple(selected))
    source = _load_static_source_context(paths, agents=(), campaign_dir=None)
    main_plan = _required_mapping(plan, "main")
    if (
        len(source.bundle.tasks) != _required_int(main_plan, "task_count")
        or len({task.dependency_cluster_id for task in source.bundle.tasks})
        != _required_int(main_plan, "dependency_cluster_count")
        or source.package.manifest.manifest_digest
        != _required_string(main_plan, "prepared_package_digest")
    ):
        raise RuntimeError("certified static source does not match the study plan")
    models = _required_mapping(plan, "models")
    study_ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    observed_costs = _gateway_costs_by_agent_id(study_ledger)
    model_configs = tuple(_required_mapping(models, key) for key in selected_keys)
    per_agent_p90: dict[str, float] = {}
    for key, config in zip(selected_keys, model_configs, strict=True):
        agent_id = _required_string(config, "agent_id")
        costs = observed_costs.get(agent_id, ())
        if not costs:
            raise RuntimeError(f"selected Agent has no observed gateway cost: {key}")
        per_agent_p90[key] = _nearest_rank(costs, 0.90)
    replicate_task_count = _replicate_count_for_plan(
        len(source.bundle.tasks),
        _required_number(main_plan, "replicate_fraction"),
    )
    calls_per_agent = len(source.bundle.tasks) + (
        replicate_task_count * (_required_int(main_plan, "replicate_count") - 1)
    )
    projected_cost = sum(per_agent_p90[key] * calls_per_agent for key in selected_keys)
    budget_decision = _required_mapping(decision, "main_budget")
    actual_projection_limit = _required_number(
        budget_decision,
        "actual_p90_projection_limit_usd",
    )
    reserve_usd = _required_number(budget_decision, "unallocated_reserve_usd")
    global_budget_usd = _required_number(
        _required_mapping(plan, "budget"),
        "total_usd",
    )
    consumed_usd = _resource_total(
        study_ledger,
        "conservative_gateway_budget_consumption",
    )
    if (
        projected_cost > actual_projection_limit
        or consumed_usd + projected_cost + reserve_usd > global_budget_usd
    ):
        raise RuntimeError(
            "full 75-Task main campaign exceeds the actual p90 budget gate"
        )
    authority_rates = {
        token_key: max(
            _required_number(
                _required_mapping(config, "pricing"),
                token_key,
            )
            for config in model_configs
        )
        for token_key in (
            "uncached_input_tokens",
            "cached_input_tokens",
            "output_tokens",
        )
    }
    scoring = ScoringConfig(
        pricing_version=f"gateway-conservative-{MAIN_CAMPAIGN_ID}",
        cost_rates=authority_rates,
    )
    calibration_agents = {
        row["agent_key"]: row
        for row in _required_mapping_sequence(calibration, "agents")
        if isinstance(row.get("agent_key"), str)
    }
    conservative_p90: dict[str, float] = {}
    for key, config in zip(selected_keys, model_configs, strict=True):
        row = calibration_agents.get(key)
        if row is None:
            raise RuntimeError(f"selected Agent lacks canonical calibration: {key}")
        campaign_id = _required_string(row, "canonical_campaign_id")
        agent_id = _required_string(config, "agent_id")
        results = tuple(
            result
            for result in load_jsonl_records(
                paths.study_output
                / "calibration"
                / campaign_id
                / "records"
                / "results.jsonl",
                ResultRecord,
            )
            if result.agent_id == agent_id
        )
        if not results:
            raise RuntimeError(f"selected Agent has no canonical Results: {key}")
        conservative_p90[key] = _nearest_rank(
            tuple(
                cast(float, compute_cost(result.usage, scoring)["total_cost"])
                for result in results
            ),
            0.90,
        )
    conservative_projected_cost = sum(
        conservative_p90[key] * calls_per_agent for key in selected_keys
    )
    authority_budget = _required_number(
        budget_decision,
        "conservative_ledger_authority_limit_usd",
    )
    if conservative_projected_cost > authority_budget:
        raise RuntimeError(
            "full main campaign exceeds the conservative ledger authority"
        )

    campaign_dir = paths.study_output / "main" / MAIN_CAMPAIGN_ID
    if campaign_dir.exists():
        raise FileExistsError(f"refusing to overwrite main campaign: {campaign_dir}")
    campaign_dir.mkdir(parents=True)
    records_dir = campaign_dir / "records"
    records_dir.mkdir()
    agents = tuple(
        _build_agent(
            model_key=key,
            model_config=config,
            campaign_id=MAIN_CAMPAIGN_ID,
            campaign_dir=campaign_dir,
            tasks=source.bundle.tasks,
            plan=plan,
            endpoint_digest=endpoint_digest,
        )
        for key, config in zip(selected_keys, model_configs, strict=True)
    )
    runtime = _base_runtime_config(
        MAIN_CAMPAIGN_ID,
        agents,
        timeout_seconds=900,
    )
    schedule = build_replicate_schedule(
        source.bundle.task_pool,
        source.bundle.tasks,
        source.bundle.checks,
        agents,
        runtime,
        campaign_id=MAIN_CAMPAIGN_ID,
        seed=_required_int(main_plan, "schedule_seed"),
        replicate_fraction=_required_number(main_plan, "replicate_fraction"),
        replicate_count=_required_int(main_plan, "replicate_count"),
    )
    source = _load_static_source_context(
        paths,
        agents=agents,
        campaign_dir=campaign_dir,
    )
    context = _main_context(
        source=source,
        campaign_dir=campaign_dir,
        agents=agents,
        runtime=runtime,
        schedule=schedule,
        scoring=scoring,
    )
    per_call_limit = max(2.0, min(10.0, 3 * max(conservative_p90.values())))
    write_jsonl_records(records_dir / "agents.jsonl", agents)
    write_jsonl_records(records_dir / "runtime-config.jsonl", (runtime,))
    write_jsonl_records(records_dir / "replicate-schedule.jsonl", (schedule,))
    metadata = {
        "schema_version": "model_main_campaign_v1",
        "study_plan_digest": plan["study_plan_digest"],
        "study_decision_amendment_digest": decision["amendment_digest"],
        "campaign_id": MAIN_CAMPAIGN_ID,
        "selected_agent_keys": list(selected_keys),
        "agent_pricing": {
            key: canonical_data_mapping(_required_mapping(config, "pricing"))
            for key, config in zip(selected_keys, model_configs, strict=True)
        },
        "scoring_config": {
            "pricing_version": scoring.pricing_version,
            "cost_rates": dict(scoring.cost_rates),
            "scoring_config_digest": scoring.scoring_config_digest,
        },
        "endpoint_digest": endpoint_digest,
        "task_pool_id": source.bundle.task_pool.task_pool_id,
        "task_pool_digest": source.bundle.task_pool.task_pool_digest,
        "schedule_digest": schedule.schedule_digest,
        "projected_actual_p90_cost_usd": projected_cost,
        "calibration_actual_p90_cost_usd_by_agent_key": per_agent_p90,
        "projected_conservative_p90_cost_usd": conservative_projected_cost,
        "calibration_conservative_p90_cost_usd_by_agent_key": conservative_p90,
        "maximum_estimated_cost_usd": authority_budget,
        "maximum_estimated_cost_per_call_usd": per_call_limit,
    }
    write_json(campaign_dir / CAMPAIGN_METADATA_NAME, metadata)
    initialize_replicate_campaign_ledger(
        context,
        approved_at=_required_string(decision, "approved_at"),
        endpoint_digest=endpoint_digest,
        maximum_estimated_cost_usd=authority_budget,
        maximum_estimated_cost_per_call_usd=per_call_limit,
        pricing_sources=(
            "authenticated gateway /api/pricing view observed 2026-07-25",
        ),
        accounting_basis=(
            "selected-pair conservative token rates; per-Agent repricing and "
            "gateway quota reconciliation are offline views"
        ),
        scope=(
            "75 frozen SWE-bench Verified SymPy Tasks; 30 percent of Tasks "
            "receive three executions for each selected Agent"
        ),
    )
    summary = {
        "stage": "main_authorized",
        "campaign_id": MAIN_CAMPAIGN_ID,
        "selected_agent_keys": list(selected_keys),
        "task_count": len(source.bundle.tasks),
        "dependency_cluster_count": len(
            {task.dependency_cluster_id for task in source.bundle.tasks}
        ),
        "replicated_task_count": len(schedule.replicated_task_ids),
        "paid_cell_count": len(schedule.cells),
        "projected_actual_p90_cost_usd": projected_cost,
        "projected_conservative_p90_cost_usd": conservative_projected_cost,
        "actual_spend_before_main_usd": consumed_usd,
        "unallocated_reserve_usd": reserve_usd,
        "maximum_estimated_cost_usd": authority_budget,
        "maximum_estimated_cost_per_call_usd": per_call_limit,
    }
    write_json(paths.study_output / "main-authority-summary.json", summary)
    return summary


def preflight_main(paths: StudyPaths) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    endpoint_digest = _activate_llm_proxy_environment(plan)
    context, metadata, source = _load_main_context(paths, plan)
    _, _, _, manifests = prepared_candidate_build_inputs(source.package)
    image_refs = tuple(
        sorted(
            {_required_string(manifest, "image_ref") for manifest in manifests.values()}
        )
    )
    verify_images(image_refs)
    next_cell = preflight_replicate_campaign(context)
    quota = _gateway_quota()
    _require_study_budget_guard(paths, plan, quota, metadata)
    _record_live_quota_checkpoint(paths, plan, quota, "main_preflight")
    summary = {
        "stage": "preflight_passed" if next_cell is not None else "complete",
        "campaign_id": MAIN_CAMPAIGN_ID,
        "study_plan_digest": plan["study_plan_digest"],
        "schedule_digest": context.schedule.schedule_digest,
        "endpoint_digest": endpoint_digest,
        "verified_image_count": len(image_refs),
        "gateway_total_used": quota["total_used"],
        "next_sequence_index": (
            None if next_cell is None else next_cell.schedule_cell.sequence_index
        ),
    }
    write_json(
        paths.study_output / "main" / MAIN_CAMPAIGN_ID / "preflight-summary.json",
        summary,
    )
    return summary


def run_next_main_cell(paths: StudyPaths) -> Mapping[str, Any]:
    plan = _load_plan(paths.plan_path)
    _activate_llm_proxy_environment(plan)
    context, metadata, _ = _load_main_context(paths, plan)
    campaign_dir = paths.study_output / "main" / MAIN_CAMPAIGN_ID
    _require_preflight_marker(campaign_dir, plan, context)
    next_cell = preflight_replicate_campaign(context)
    if next_cell is None:
        return {"stage": "complete", "campaign_id": MAIN_CAMPAIGN_ID}
    accounted = _run_accounted_campaign_cell(
        paths,
        plan,
        metadata,
        context,
        campaign_dir,
        next_cell,
    )
    result = accounted.result
    return {
        "stage": "cell_recorded",
        "campaign_id": MAIN_CAMPAIGN_ID,
        "sequence_index": next_cell.schedule_cell.sequence_index,
        "agent_id": result.agent_id,
        "task_id": result.task_id,
        "replicate_index": next_cell.schedule_cell.replicate_index,
        "outcome": result.outcome,
        "scoreable_state": result.scoreable_state,
        "estimated_cost_usd": result.cost["total_cost"],
        "gateway_balance_window_delta": _accounted_balance_delta(accounted),
        "gateway_log_quota_points": _accounted_receipt_quota(accounted),
        "gateway_log_cost_usd": (
            None
            if _accounted_receipt_quota(accounted) is None
            else cast(int, _accounted_receipt_quota(accounted))
            / _required_int(
                _required_mapping(plan, "budget"),
                "quota_points_per_usd",
            )
        ),
    }


def summarize_main(paths: StudyPaths) -> Mapping[str, Any]:
    """Summarize the complete frozen main schedule without adding cells."""
    plan = _load_plan(paths.plan_path)
    context, metadata, source = _load_main_context(paths, plan)
    results = tuple(
        load_jsonl_records(context.result_store.path, ResultRecord)
    )
    if len(results) != len(context.schedule.cells):
        raise RuntimeError("main campaign is incomplete")
    if any(result.scoreable_state != "scoreable" for result in results):
        raise RuntimeError("main campaign contains non-scoreable Results")
    result_by_cell = {
        (
            result.agent_id,
            result.task_id,
            result.cache_identity.runtime_config_digest,
        ): result
        for result in results
    }
    if len(result_by_cell) != len(results):
        raise RuntimeError("main campaign has duplicate exact Result cells")
    runtime_digest_by_index = {
        index: canonical_digest(runtime)
        for index, runtime in enumerate(context.schedule.runtime_configs)
    }
    agents = context.agents
    if len(agents) != 2:
        raise RuntimeError("main comparison requires exactly two Agents")
    selected_keys = _required_string_sequence(metadata, "selected_agent_keys")
    if len(selected_keys) != 2:
        raise RuntimeError("main metadata requires two selected Agent keys")
    left, right = agents
    task_by_id = {task.task_id: task for task in source.bundle.tasks}

    def result_for(agent_id: str, task_id: str, replicate_index: int) -> ResultRecord:
        try:
            return result_by_cell[
                (
                    agent_id,
                    task_id,
                    runtime_digest_by_index[replicate_index],
                )
            ]
        except KeyError as exc:
            raise RuntimeError("main Result matrix is incomplete") from exc

    paired_rows: list[Mapping[str, Any]] = []
    differences_by_cluster: dict[str, list[float]] = {}
    left_only = 0
    right_only = 0
    for task_id in context.task_pool.task_ids:
        left_result = result_for(left.agent_id, task_id, 0)
        right_result = result_for(right.agent_id, task_id, 0)
        left_pass = int(left_result.outcome == "pass")
        right_pass = int(right_result.outcome == "pass")
        difference = float(left_pass - right_pass)
        cluster_id = task_by_id[task_id].dependency_cluster_id
        differences_by_cluster.setdefault(cluster_id, []).append(difference)
        left_only += int(left_pass == 1 and right_pass == 0)
        right_only += int(left_pass == 0 and right_pass == 1)
        paired_rows.append(
            {
                "task_id": task_id,
                "dependency_cluster_id": cluster_id,
                "left_outcome": left_result.outcome,
                "right_outcome": right_result.outcome,
                "difference": difference,
            }
        )
    observed_difference = sum(
        cast(float, row["difference"]) for row in paired_rows
    ) / len(paired_rows)
    comparison_interval = _cluster_bootstrap_interval(
        differences_by_cluster,
        seed=context.schedule.seed + 101,
        iterations=20_000,
    )

    repeat_pair_values: dict[str, list[float]] = {}
    repeat_cluster_rows: list[Mapping[str, Any]] = []
    for agent in agents:
        for task_id in context.schedule.replicated_task_ids:
            outcomes = tuple(
                result_for(agent.agent_id, task_id, replicate_index).outcome
                for replicate_index in range(context.schedule.replicate_count)
            )
            pair_disagreements = tuple(
                float(outcomes[left_index] != outcomes[right_index])
                for left_index in range(len(outcomes))
                for right_index in range(left_index + 1, len(outcomes))
            )
            cluster_key = f"{agent.agent_id}:{task_id}"
            repeat_pair_values[cluster_key] = list(pair_disagreements)
            repeat_cluster_rows.append(
                {
                    "agent_id": agent.agent_id,
                    "task_id": task_id,
                    "outcomes": list(outcomes),
                    "pairwise_disagreements": list(pair_disagreements),
                    "any_flip": any(pair_disagreements),
                }
            )
    all_repeat_pairs = [
        value for values in repeat_pair_values.values() for value in values
    ]
    flip_rate = sum(all_repeat_pairs) / len(all_repeat_pairs)
    flip_interval = _cluster_bootstrap_interval(
        repeat_pair_values,
        seed=context.schedule.seed + 211,
        iterations=20_000,
    )
    if flip_interval["upper"] <= 0.05:
        repeat_decision = "single_cached_result_supported_for_current_experiments"
    elif flip_interval["lower"] >= 0.10:
        repeat_decision = "future_comparisons_must_be_replicate_aware"
    else:
        repeat_decision = "retain_repeats_in_experiment_layer"

    models = _required_mapping(plan, "models")
    study_ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    operational_rows: list[Mapping[str, Any]] = []
    for key, agent in zip(selected_keys, agents, strict=True):
        model_config = _required_mapping(models, key)
        pricing = _required_mapping(model_config, "pricing")
        scoring = ScoringConfig(
            _required_string(pricing, "pricing_version"),
            {
                token_key: _required_number(pricing, token_key)
                for token_key in (
                    "uncached_input_tokens",
                    "cached_input_tokens",
                    "output_tokens",
                )
            },
        )
        agent_results = tuple(
            result for result in results if result.agent_id == agent.agent_id
        )
        latencies = tuple(
            _result_number(result.latency, "workspace_seconds")
            for result in agent_results
        )
        gateway_windows = tuple(
            float(entry["gateway_log_cost_usd"])
            for entry in _required_mapping_sequence(study_ledger, "entries")
            if entry.get("campaign_id") == MAIN_CAMPAIGN_ID
            and entry.get("agent_id") == agent.agent_id
            and isinstance(entry.get("gateway_log_cost_usd"), int | float)
        )
        token_totals = {
            token_key: sum(
                int(result.usage.get(token_key, 0)) for result in agent_results
            )
            for token_key in (
                "input_tokens",
                "uncached_input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            )
        }
        operational_rows.append(
            {
                "agent_key": key,
                "agent_id": agent.agent_id,
                "requested_model_id": agent.requested_model_id,
                "base_pass_count": sum(
                    result_for(agent.agent_id, task_id, 0).outcome == "pass"
                    for task_id in context.task_pool.task_ids
                ),
                "result_count": len(agent_results),
                "token_totals": token_totals,
                "repriced_estimated_cost_usd": sum(
                    cast(float, compute_cost(result.usage, scoring)["total_cost"])
                    for result in agent_results
                ),
                "observed_gateway_attributed_cost_usd": sum(gateway_windows),
                "workspace_seconds": {
                    "total": sum(latencies),
                    "median": _quantile(latencies, 0.50),
                    "p90_nearest_rank": _nearest_rank(latencies, 0.90),
                },
            }
        )

    summary = {
        "schema_version": "model_agent_main_summary_v1",
        "study_plan_digest": plan["study_plan_digest"],
        "stage": "complete",
        "campaign_id": MAIN_CAMPAIGN_ID,
        "task_pool_id": context.task_pool.task_pool_id,
        "task_count": len(context.task_pool.task_ids),
        "dependency_cluster_count": len(differences_by_cluster),
        "result_count": len(results),
        "comparison": {
            "left_agent_key": selected_keys[0],
            "right_agent_key": selected_keys[1],
            "left_pass_count": operational_rows[0]["base_pass_count"],
            "right_pass_count": operational_rows[1]["base_pass_count"],
            "left_minus_right_pass_rate": observed_difference,
            "dependency_cluster_bootstrap_95_interval": comparison_interval,
            "left_only_pass_count": left_only,
            "right_only_pass_count": right_only,
            "discordant_task_count": left_only + right_only,
            "mcnemar_exact_two_sided_p": _mcnemar_exact_two_sided(
                left_only,
                right_only,
            ),
            "paired_task_rows": paired_rows,
        },
        "repeatability": {
            "agent_task_cluster_count": len(repeat_pair_values),
            "pairwise_disagreement_count": int(sum(all_repeat_pairs)),
            "pairwise_comparison_count": len(all_repeat_pairs),
            "observed_flip_rate": flip_rate,
            "agent_task_cluster_bootstrap_95_interval": flip_interval,
            "decision": repeat_decision,
            "cluster_rows": repeat_cluster_rows,
        },
        "operations": operational_rows,
        "claim_boundary": (
            "Retrospective, source-conditional SymPy SWE-bench evidence; not a "
            "universal model rank and not prospective Selector evidence."
        ),
    }
    write_json(paths.study_output / "main-summary.json", summary)
    return summary


def _cluster_bootstrap_interval(
    values_by_cluster: Mapping[str, Sequence[float]],
    *,
    seed: int,
    iterations: int,
) -> Mapping[str, Any]:
    if (
        not values_by_cluster
        or iterations <= 0
        or any(not values for values in values_by_cluster.values())
    ):
        raise ValueError("cluster bootstrap requires nonempty clusters")
    clusters = tuple(sorted(values_by_cluster))
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        sampled = tuple(rng.choice(clusters) for _ in clusters)
        values = [
            float(value)
            for cluster in sampled
            for value in values_by_cluster[cluster]
        ]
        estimates.append(sum(values) / len(values))
    return {
        "method": "percentile_cluster_bootstrap",
        "iterations": iterations,
        "seed": seed,
        "lower": _quantile(estimates, 0.025),
        "upper": _quantile(estimates, 0.975),
    }


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values or not 0 <= probability <= 1:
        raise ValueError("quantile inputs are invalid")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _mcnemar_exact_two_sided(left_only: int, right_only: int) -> float:
    if left_only < 0 or right_only < 0:
        raise ValueError("discordant counts must be nonnegative")
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = min(left_only, right_only)
    probability = sum(
        math.comb(discordant, count) for count in range(tail + 1)
    ) / (2**discordant)
    return min(1.0, 2 * probability)


def _calibration_context(
    *,
    pilot: Any,
    campaign_dir: Path,
    agents: tuple[AgentRecord, ...],
    runtime: RuntimeConfig,
    schedule: ReplicateSchedule,
    scoring: ScoringConfig,
) -> ReplicateCampaignContext:
    run_context = pilot.run_context
    endpoint_paths = (HARNESS, HARNESS.parent / "extract-usage.py")
    for agent in agents:
        run_context = bind_agent_harness(
            run_context,
            agent,
            _agent_command(campaign_dir, agent),
            execution_mode="openai_paid",
            endpoint_harness_paths=endpoint_paths,
        )
    return ReplicateCampaignContext(
        schedule=schedule,
        task_pool=pilot.task_pool,
        tasks=pilot.tasks,
        checks=tuple(pilot.checks[check_id] for check_id in pilot.task_pool.check_ids),
        agents=agents,
        base_runtime_config=runtime,
        workspace_config=pilot.workspace_config,
        scoring_config=scoring,
        result_store=ResultStore(campaign_dir / "records" / "results.jsonl"),
        ledger_path=campaign_dir / "campaign-ledger.json",
        run_context=run_context,
    )


def _load_static_source_context(
    paths: StudyPaths,
    *,
    agents: Sequence[AgentRecord],
    campaign_dir: Path | None,
) -> StaticSourceContext:
    sympy_root = paths.study_output / "sympy"
    package = load_prepared_candidate_package(
        sympy_root / "prepared-package" / "prepared-candidate-package.jsonl"
    )
    certification = _load_json(sympy_root / "certification-summary.json")
    if certification.get("stage") != "certified":
        raise RuntimeError("SymPy Task Pool certification is incomplete")
    task_pool_manifest = certification.get("task_pool_manifest")
    if not isinstance(task_pool_manifest, str) or not task_pool_manifest:
        raise RuntimeError("SymPy certification has no Task Pool manifest")
    bundle = open_task_pool_bundle(Path(task_pool_manifest))
    _, commands, hidden_material, check_manifests = prepared_candidate_build_inputs(
        package
    )
    workspace_config, _ = certification_configs(package, check_manifests)
    if canonical_digest(workspace_config) != _required_string(
        _required_mapping(certification, "workspace_config"),
        "digest",
    ):
        raise RuntimeError("SymPy Workspace config does not replay")
    run_context = bind_repository_source(
        WorkspaceRunContext(),
        workspace_config,
        sympy_root / "target-repo",
    )
    candidate_id_by_source_ref = {
        candidate.source_ref: candidate.candidate_id
        for candidate in package.batch.candidates
    }
    checks_by_id = {check.check_id: check for check in bundle.checks}
    for task in bundle.tasks:
        candidate_id = candidate_id_by_source_ref.get(task.source_ref)
        if candidate_id is None or len(task.check_ids) != 1:
            raise RuntimeError("SymPy prepared package does not match Task records")
        check = checks_by_id[task.check_ids[0]]
        run_context = bind_check_material(
            run_context,
            check,
            commands[candidate_id],
            hidden_material[candidate_id],
            check_manifest=check_manifests[candidate_id],
        )
    if campaign_dir is not None:
        endpoint_paths = (HARNESS, HARNESS.parent / "extract-usage.py")
        for agent in agents:
            run_context = bind_agent_harness(
                run_context,
                agent,
                _agent_command(campaign_dir, agent),
                execution_mode="openai_paid",
                endpoint_harness_paths=endpoint_paths,
            )
    return StaticSourceContext(
        package=package,
        bundle=bundle,
        workspace_config=workspace_config,
        checks=bundle.checks,
        run_context=run_context,
    )


def _main_context(
    *,
    source: StaticSourceContext,
    campaign_dir: Path,
    agents: tuple[AgentRecord, ...],
    runtime: RuntimeConfig,
    schedule: ReplicateSchedule,
    scoring: ScoringConfig,
) -> ReplicateCampaignContext:
    return ReplicateCampaignContext(
        schedule=schedule,
        task_pool=source.bundle.task_pool,
        tasks=source.bundle.tasks,
        checks=source.checks,
        agents=agents,
        base_runtime_config=runtime,
        workspace_config=source.workspace_config,
        scoring_config=scoring,
        result_store=ResultStore(campaign_dir / "records" / "results.jsonl"),
        ledger_path=campaign_dir / "campaign-ledger.json",
        run_context=source.run_context,
    )


def _load_main_context(
    paths: StudyPaths,
    plan: Mapping[str, Any],
) -> tuple[
    ReplicateCampaignContext,
    Mapping[str, Any],
    StaticSourceContext,
]:
    campaign_dir = paths.study_output / "main" / MAIN_CAMPAIGN_ID
    metadata = _load_json(campaign_dir / CAMPAIGN_METADATA_NAME)
    decision = _load_decision_amendment(DEFAULT_DECISION_AMENDMENT, plan)
    if (
        metadata.get("study_plan_digest") != plan["study_plan_digest"]
        or metadata.get("study_decision_amendment_digest")
        != decision["amendment_digest"]
        or metadata.get("campaign_id") != MAIN_CAMPAIGN_ID
    ):
        raise RuntimeError("main campaign metadata does not match the study plan")
    agents = tuple(
        load_jsonl_records(campaign_dir / "records" / "agents.jsonl", AgentRecord)
    )
    runtime = _one_record(
        campaign_dir / "records" / "runtime-config.jsonl",
        RuntimeConfig,
    )
    schedule = _one_record(
        campaign_dir / "records" / "replicate-schedule.jsonl",
        ReplicateSchedule,
    )
    scoring_payload = _required_mapping(metadata, "scoring_config")
    scoring = ScoringConfig(
        _required_string(scoring_payload, "pricing_version"),
        _numeric_mapping(
            _required_mapping(scoring_payload, "cost_rates"),
            "cost_rates",
        ),
    )
    source = _load_static_source_context(
        paths,
        agents=agents,
        campaign_dir=campaign_dir,
    )
    return (
        _main_context(
            source=source,
            campaign_dir=campaign_dir,
            agents=agents,
            runtime=runtime,
            schedule=schedule,
            scoring=scoring,
        ),
        metadata,
        source,
    )


def _load_calibration_context(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    campaign_config: Mapping[str, Any],
    decision_amendment: Mapping[str, Any] | None = None,
) -> ReplicateCampaignContext:
    campaign_id = _required_string(campaign_config, "campaign_id")
    campaign_dir = paths.study_output / "calibration" / campaign_id
    metadata = _load_json(campaign_dir / CAMPAIGN_METADATA_NAME)
    if metadata.get("study_plan_digest") != plan["study_plan_digest"]:
        raise RuntimeError("campaign metadata does not match the study plan")
    metadata_decision_digest = metadata.get("study_decision_amendment_digest")
    if metadata_decision_digest is not None and (
        decision_amendment is None
        or metadata_decision_digest != decision_amendment.get("amendment_digest")
    ):
        raise RuntimeError("campaign metadata does not match amendment 2")
    pilot = build_pilot_context(
        _pilot_paths(paths.pilot_output),
        campaign_dir / "campaign-ledger.json",
    )
    agents = tuple(
        load_jsonl_records(campaign_dir / "records" / "agents.jsonl", AgentRecord)
    )
    runtime = _one_record(
        campaign_dir / "records" / "runtime-config.jsonl",
        RuntimeConfig,
    )
    schedule = _one_record(
        campaign_dir / "records" / "replicate-schedule.jsonl",
        ReplicateSchedule,
    )
    scoring_payload = _required_mapping(metadata, "scoring_config")
    scoring = ScoringConfig(
        _required_string(scoring_payload, "pricing_version"),
        _numeric_mapping(
            _required_mapping(scoring_payload, "cost_rates"),
            "cost_rates",
        ),
    )
    return _calibration_context(
        pilot=pilot,
        campaign_dir=campaign_dir,
        agents=agents,
        runtime=runtime,
        schedule=schedule,
        scoring=scoring,
    )


def _load_canary_context(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    amendment: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[ReplicateCampaignContext, Mapping[str, Any]]:
    campaign_id = _required_string(config, "campaign_id")
    campaign_dir = paths.study_output / "calibration-canaries" / campaign_id
    metadata = _load_json(campaign_dir / CAMPAIGN_METADATA_NAME)
    if (
        metadata.get("study_plan_digest") != plan["study_plan_digest"]
        or metadata.get("study_amendment_digest") != amendment["amendment_digest"]
        or metadata.get("campaign_id") != campaign_id
    ):
        raise RuntimeError("protocol canary metadata does not match its authority")
    pilot = build_pilot_context(
        _pilot_paths(paths.pilot_output),
        campaign_dir / "campaign-ledger.json",
    )
    agents = tuple(
        load_jsonl_records(campaign_dir / "records" / "agents.jsonl", AgentRecord)
    )
    runtime = _one_record(
        campaign_dir / "records" / "runtime-config.jsonl",
        RuntimeConfig,
    )
    schedule = _one_record(
        campaign_dir / "records" / "replicate-schedule.jsonl",
        ReplicateSchedule,
    )
    scoring_payload = _required_mapping(metadata, "scoring_config")
    scoring = ScoringConfig(
        _required_string(scoring_payload, "pricing_version"),
        _numeric_mapping(
            _required_mapping(scoring_payload, "cost_rates"),
            "cost_rates",
        ),
    )
    return (
        _calibration_context(
            pilot=pilot,
            campaign_dir=campaign_dir,
            agents=agents,
            runtime=runtime,
            schedule=schedule,
            scoring=scoring,
        ),
        metadata,
    )


def _gateway_costs_by_agent_id(
    study_ledger: Mapping[str, Any],
) -> Mapping[str, tuple[float, ...]]:
    costs: dict[str, list[float]] = {}
    for entry in _required_mapping_sequence(study_ledger, "entries"):
        if entry.get("action") != "execute frozen benchmark campaign cell":
            continue
        agent_id = entry.get("agent_id")
        cost = entry.get("gateway_log_cost_usd")
        if (
            not isinstance(agent_id, str)
            or not agent_id
            or isinstance(cost, bool)
            or not isinstance(cost, int | float)
            or not math.isfinite(float(cost))
            or float(cost) < 0
        ):
            raise RuntimeError("study ledger gateway cost entry is invalid")
        costs.setdefault(agent_id, []).append(float(cost))
    return {agent_id: tuple(values) for agent_id, values in sorted(costs.items())}


def _resource_total(ledger: Mapping[str, Any], resource: str) -> float:
    matches = tuple(
        row
        for row in _required_mapping_sequence(ledger, "totals")
        if row.get("resource") == resource
    )
    if len(matches) != 1:
        raise RuntimeError(f"study ledger lacks one {resource} total")
    return _required_number(matches[0], "amount")


def _nearest_rank(values: Sequence[float], probability: float) -> float:
    if (
        not values
        or not 0 < probability <= 1
        or any(not math.isfinite(value) or value < 0 for value in values)
    ):
        raise ValueError("nearest-rank inputs are invalid")
    ordered = sorted(values)
    rank = max(1, math.ceil(probability * len(ordered)))
    return ordered[rank - 1]


def _replicate_count_for_plan(task_count: int, fraction: float) -> int:
    candidates = tuple(
        count
        for count in range(1, task_count + 1)
        if 0.20 <= count / task_count <= 0.30
    )
    if not candidates:
        raise ValueError("task count cannot realize the replicate fraction")
    return min(
        candidates,
        key=lambda count: (abs(count / task_count - fraction), count),
    )


def _build_agent(
    *,
    model_key: str,
    model_config: Mapping[str, Any],
    campaign_id: str,
    campaign_dir: Path,
    tasks: Sequence[TaskRecord],
    plan: Mapping[str, Any],
    endpoint_digest: str,
) -> AgentRecord:
    del model_key
    agent_id = _required_string(model_config, "agent_id")
    requested_model_id = _required_string(model_config, "requested_model_id")
    effort = _required_string(model_config, "reasoning_effort")
    command = (
        "env",
        f"BARCAROLLE_CODEX_MODEL={requested_model_id}",
        f"BARCAROLLE_CODEX_REASONING_EFFORT={effort}",
        "BARCAROLLE_CODEX_HOME="
        + str(
            (
                campaign_dir
                / ("codex-home-" + canonical_digest({"agent_id": agent_id})[:16])
            ).resolve()
        ),
        str(HARNESS),
    )
    usage_helper = HARNESS.parent / "extract-usage.py"
    content_digest = harness_content_digest((HARNESS, usage_helper))
    harness_digest = canonical_digest({"agent_command": command})
    prompt_digest = canonical_digest(
        {
            "prompt": "swe-bench-task-md-codex-v1",
            "task_file": ".barcarolle/TASK.md",
            "repository_instruction_state": "none-at-selected-base-commits",
            "repository_rules_ignored": True,
        }
    )
    cli_version = _codex_cli_version()
    provider_digest = canonical_digest(
        {
            "provider": "barcarolle_openai",
            "wire_api": "responses",
            "endpoint_digest": endpoint_digest,
            "request_max_retries": "codex-cli-default",
            "stream_max_retries": "codex-cli-default",
        }
    )
    agent = AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest="",
        requested_model_id=requested_model_id,
        model_snapshot_id=None,
        model_resolution_scope_id=campaign_id,
        model_resolution_scope_started_at=_required_string(
            plan, "model_scope_started_at"
        ),
        model_resolution_scope_ended_at=_required_string(plan, "model_scope_ended_at"),
        harness_digest=harness_digest,
        repository_instruction_digest=canonical_digest(
            {
                "state": "none-at-selected-base-commits",
                "base_commits": tuple(task.base_commit for task in tasks),
            }
        ),
        prompt_digest=prompt_digest,
        tools_digest=canonical_digest(
            {"codex_cli_version": cli_version, "tools": "builtins"}
        ),
        retrieval_digest="none",
        skills_digest=canonical_digest(
            {
                "codex_cli_version": cli_version,
                "loading_mode": "default-bundled-only",
                "plugins_disabled": True,
                "multi_agent_disabled": True,
                "user_config_ignored": True,
            }
        ),
        network_policy_digest=make_openai_env_network_policy_digest(
            endpoint_digest=endpoint_digest,
            harness_digest=harness_digest,
            harness_content_digest=content_digest,
        ),
        adapter_digest=canonical_digest(
            {
                "adapter": "barcarolle-worktree-diff-v2-python-cache-excluded",
                "reasoning_effort": effort,
            }
        ),
    )
    manifest_digest = canonical_digest(
        {
            "agent": "codex-cli",
            "agent_record_without_manifest_digest": {
                **cast(dict[str, Any], canonical_data_mapping(agent)),
                "agent_manifest_digest": "",
            },
            "reasoning_effort": effort,
            "codex_cli_version": cli_version,
            "harness_content_digest": content_digest,
            "provider_digest": provider_digest,
            "multi_agent_disabled": True,
        }
    )
    agent = AgentRecord(
        **{
            **cast(dict[str, Any], canonical_data_mapping(agent)),
            "agent_manifest_digest": manifest_digest,
        }
    )
    validation = validate_agent(agent)
    if not validation.ok:
        raise ValueError(
            f"invalid study Agent {agent.agent_id}: {', '.join(validation.errors)}"
        )
    return agent


def _base_runtime_config(
    campaign_id: str,
    agents: Sequence[AgentRecord],
    *,
    timeout_seconds: int,
) -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id=f"{campaign_id}-base-runtime",
        budget_digest=canonical_digest(
            {
                "campaign_id": campaign_id,
                "timeout_seconds": timeout_seconds,
                "agent_ids": [agent.agent_id for agent in agents],
            }
        ),
        retry_policy_digest="codex-default-network-retries-no-cell-retry",
        stochastic_settings_digest=canonical_digest(
            {
                "campaign_id": campaign_id,
                "agent_manifest_digests": [
                    agent.agent_manifest_digest for agent in agents
                ],
            }
        ),
        timeout_seconds=timeout_seconds,
        hardware_profile_digest=None,
    )


def _agent_command(
    campaign_dir: Path,
    agent: AgentRecord,
) -> tuple[str, ...]:
    effort = agent.agent_id.rsplit("-", 1)[-1]
    if effort not in {"none", "low", "medium", "high", "xhigh"}:
        raise ValueError("study Agent ID must end with its reasoning effort")
    return (
        "env",
        f"BARCAROLLE_CODEX_MODEL={agent.requested_model_id}",
        f"BARCAROLLE_CODEX_REASONING_EFFORT={effort}",
        "BARCAROLLE_CODEX_HOME="
        + str(
            (
                campaign_dir
                / ("codex-home-" + canonical_digest({"agent_id": agent.agent_id})[:16])
            ).resolve()
        ),
        str(HARNESS),
    )


def _activate_llm_proxy_environment(plan: Mapping[str, Any]) -> str:
    source_base = os.environ.get("LLM_BASE_URL")
    source_key = os.environ.get("LLM_API_KEY")
    if not source_base or not source_key:
        raise RuntimeError("LLM_BASE_URL and LLM_API_KEY are required")
    for source, target in (
        (source_base, "OPENAI_BASE_URL"),
        (source_key, "OPENAI_API_KEY"),
    ):
        existing = os.environ.get(target)
        if existing is not None and not _constant_time_equal(existing, source):
            raise RuntimeError(f"{target} conflicts with the authorized LLM proxy")
        os.environ[target] = source
    digest = resolve_openai_endpoint_digest(require_api_key=True)
    expected = _required_string(
        _required_mapping(plan, "endpoint_mapping"),
        "endpoint_digest",
    )
    if digest != expected:
        raise RuntimeError("LLM proxy endpoint does not match the frozen study plan")
    return digest


def _constant_time_equal(left: str, right: str) -> bool:
    return (
        hashlib.sha256(left.encode()).digest()
        == hashlib.sha256(right.encode()).digest()
    )


def _gateway_quota() -> Mapping[str, int]:
    payload = _gateway_json("/api/usage/token/")
    if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), Mapping):
        raise RuntimeError("gateway quota response is invalid")
    data = cast(Mapping[str, Any], payload["data"])
    quota = {
        key: _required_int(data, key)
        for key in ("total_granted", "total_used", "total_available")
    }
    if quota["total_granted"] - quota["total_used"] != quota["total_available"]:
        raise RuntimeError("gateway quota totals are inconsistent")
    return quota


def _gateway_token_logs() -> tuple[Mapping[str, Any], ...]:
    key = os.environ["LLM_API_KEY"]
    payload = _gateway_json(
        "/api/log/token?key=" + urllib.parse.quote(key, safe=""),
    )
    if (
        not isinstance(payload, Mapping)
        or payload.get("success") is not True
        or not isinstance(payload.get("data"), list)
        or any(not isinstance(row, Mapping) for row in payload["data"])
    ):
        raise RuntimeError("gateway token-log response is invalid")
    return tuple(cast(Mapping[str, Any], row) for row in payload["data"])


def _gateway_json(path: str, *, attempts: int = 5) -> Any:
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    request = urllib.request.Request(
        base_url + path,
        headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise RuntimeError(
                    f"gateway metadata request failed with HTTP {exc.code}"
                ) from None
            retry_after = (
                None if exc.headers is None else exc.headers.get("Retry-After")
            )
            retry_hint = (
                ""
                if retry_after is None
                else f"; retry after {retry_after} seconds"
            )
            raise RuntimeError(
                "gateway metadata request is rate limited" + retry_hint
            ) from None
        except urllib.error.URLError as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(
                    f"gateway metadata request failed: {type(exc.reason).__name__}"
                ) from None
        time.sleep(min(2**attempt, 8))
    raise AssertionError("bounded gateway request loop did not return")


def _gateway_log_receipt(
    result: ResultRecord,
    rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    started = math.floor(parse_utc_timestamp(result.started_at).timestamp())
    finished = math.ceil(parse_utc_timestamp(result.finished_at).timestamp())
    selected = tuple(
        row
        for row in rows
        if row.get("type") == 2
        and row.get("model_name") == result.cache_identity.requested_model_id
        and isinstance(row.get("created_at"), int)
        and started <= cast(int, row["created_at"]) <= finished + 2
    )
    sanitized_rows: list[Mapping[str, Any]] = []
    for row in selected:
        sanitized_rows.append(
            {
                "created_at": _required_int(row, "created_at"),
                "model_name": _required_string(row, "model_name"),
                "quota": _required_int(row, "quota"),
                "prompt_tokens": _required_int(row, "prompt_tokens"),
                "completion_tokens": _required_int(row, "completion_tokens"),
                "request_id_digest": canonical_digest(
                    {"request_id": _required_string(row, "request_id")}
                ),
            }
        )
    prompt_tokens = sum(
        cast(int, row["prompt_tokens"]) for row in sanitized_rows
    )
    completion_tokens = sum(
        cast(int, row["completion_tokens"]) for row in sanitized_rows
    )
    quota_points = sum(cast(int, row["quota"]) for row in sanitized_rows)
    usage_observed = bool(result.usage)
    usage_match = (
        prompt_tokens == result.usage.get("input_tokens")
        and completion_tokens == result.usage.get("output_tokens")
        if usage_observed
        else None
    )
    if result.scoreable_state == "scoreable" and usage_match is not True:
        raise GatewayReceiptIncomplete(
            "gateway token logs do not exactly reconcile Result token usage"
        )
    receipt = {
        "source": "new_api_token_log",
        "model_name": result.cache_identity.requested_model_id,
        "result_started_at": result.started_at,
        "result_finished_at": result.finished_at,
        "success_log_count": len(sanitized_rows),
        "quota_points": quota_points,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "result_usage_match": usage_match,
        "sanitized_rows_digest": canonical_digest(sanitized_rows),
        "limitations": (
            "selected by bound model and Result time window; exact token-total "
            "match rejects overlapping or missing successful rows"
        ),
    }
    _validate_gateway_log_receipt(result, receipt)
    return receipt


def _eventual_gateway_log_receipt(
    result: ResultRecord,
    *,
    attempts: int = 6,
) -> Mapping[str, Any]:
    for attempt in range(attempts):
        try:
            return _gateway_log_receipt(result, _gateway_token_logs())
        except GatewayReceiptIncomplete:
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2**attempt, 16))
    raise AssertionError("bounded gateway receipt loop did not return")


def _validate_gateway_log_receipt(
    result: ResultRecord,
    receipt: Mapping[str, Any],
) -> None:
    expected_usage_match = bool(result.usage)
    if (
        receipt.get("source") != "new_api_token_log"
        or receipt.get("model_name") != result.cache_identity.requested_model_id
        or receipt.get("result_started_at") != result.started_at
        or receipt.get("result_finished_at") != result.finished_at
        or not isinstance(receipt.get("success_log_count"), int)
        or cast(int, receipt["success_log_count"]) < 0
        or not isinstance(receipt.get("quota_points"), int)
        or cast(int, receipt["quota_points"]) < 0
        or not isinstance(receipt.get("prompt_tokens"), int)
        or cast(int, receipt["prompt_tokens"]) < 0
        or not isinstance(receipt.get("completion_tokens"), int)
        or cast(int, receipt["completion_tokens"]) < 0
        or not isinstance(receipt.get("sanitized_rows_digest"), str)
        or not receipt["sanitized_rows_digest"]
        or (
            expected_usage_match
            and (
                receipt.get("result_usage_match") is not True
                or receipt.get("prompt_tokens")
                != result.usage.get("input_tokens")
                or receipt.get("completion_tokens")
                != result.usage.get("output_tokens")
            )
        )
        or (
            not expected_usage_match
            and receipt.get("result_usage_match") is not None
        )
    ):
        raise RuntimeError("persisted gateway token-log receipt is invalid")


def _require_global_quota_guard(
    plan: Mapping[str, Any],
    quota: Mapping[str, int],
    campaign_config: Mapping[str, Any],
) -> None:
    budget = _required_mapping(plan, "budget")
    maximum = _required_int(budget, "quota_maximum_total_used")
    per_call_usd = _required_number(
        campaign_config,
        "maximum_estimated_cost_per_call_usd",
    )
    points_per_usd = _required_int(budget, "quota_points_per_usd")
    reserve = math.ceil(per_call_usd * points_per_usd)
    if quota["total_used"] + reserve > maximum:
        raise RuntimeError("global quota guard cannot cover the next authorized call")


def _require_study_budget_guard(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    quota: Mapping[str, int],
    campaign_config: Mapping[str, Any],
) -> None:
    _require_global_quota_guard(plan, quota, campaign_config)
    ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    entries = _required_mapping_sequence(ledger, "entries")
    attributed = sum(
        cast(int, entry["gateway_log_quota_points"])
        for entry in entries
        if isinstance(entry.get("gateway_log_quota_points"), int)
    )
    budget = _required_mapping(plan, "budget")
    baseline = _required_int(
        _required_mapping(ledger, "gateway_accounting"),
        "baseline_total_used",
    )
    global_movement = quota["total_used"] - baseline
    allowance = (
        _required_int(budget, "quota_maximum_total_used")
        - _required_int(budget, "quota_baseline_total_used")
    )
    reserve = math.ceil(
        _required_number(
            campaign_config,
            "maximum_estimated_cost_per_call_usd",
        )
        * _required_int(budget, "quota_points_per_usd")
    )
    pending_reserved_quota = sum(
        (
            cast(int, entry["pending_receipt_reserve_quota_points"])
            if isinstance(entry.get("pending_receipt_reserve_quota_points"), int)
            else reserve
        )
        for entry in entries
        if entry.get("action") == "execute frozen benchmark campaign cell"
        and isinstance(entry.get("result_id"), str)
        and not isinstance(entry.get("gateway_log_quota_points"), int)
    )
    attributed_with_pending_reserve = attributed + pending_reserved_quota
    if max(attributed_with_pending_reserve, global_movement) + reserve > allowance:
        raise RuntimeError("study-attributed quota guard cannot cover the next call")


def _record_live_quota_checkpoint(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    quota: Mapping[str, int],
    source: str,
) -> None:
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    ledger = dict(_load_json(ledger_path))
    accounting = dict(_required_mapping(ledger, "gateway_accounting"))
    accounting["latest_live_total_used"] = quota["total_used"]
    accounting["latest_live_observed_at"] = _utc_now()
    accounting["latest_live_source"] = source
    ledger["gateway_accounting"] = accounting
    _write_study_resource_ledger(
        ledger_path,
        ledger,
        _required_mapping_sequence(ledger, "entries"),
        points_per_usd=_required_int(
            _required_mapping(plan, "budget"),
            "quota_points_per_usd",
        ),
        latest_gateway_total_used=quota["total_used"],
    )


def _quota_checkpoint_for_cell(
    paths: StudyPaths,
    sequence_index: int,
) -> tuple[Mapping[str, int], str, str]:
    ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    accounting = _required_mapping(ledger, "gateway_accounting")
    baseline_used = _required_int(accounting, "baseline_total_used")
    baseline_available = _required_int(accounting, "baseline_total_available")
    if sequence_index % QUOTA_CHECKPOINT_CELL_INTERVAL == 0:
        recent_total = accounting.get("latest_live_total_used")
        recent_at = accounting.get("latest_live_observed_at")
        if (
            isinstance(recent_total, int)
            and not isinstance(recent_total, bool)
            and isinstance(recent_at, str)
            and recent_at
        ):
            age = (
                parse_utc_timestamp(_utc_now()) - parse_utc_timestamp(recent_at)
            ).total_seconds()
            if 0 <= age <= QUOTA_CHECKPOINT_MAX_AGE_SECONDS:
                total_granted = baseline_used + baseline_available
                if recent_total > total_granted:
                    raise RuntimeError("recent live quota exceeds the frozen grant")
                return (
                    {
                        "total_granted": total_granted,
                        "total_used": recent_total,
                        "total_available": total_granted - recent_total,
                    },
                    "recent_live_checkpoint_reuse",
                    recent_at,
                )
        live = _gateway_quota()
        return live, "live_six_cell_checkpoint", _utc_now()
    snapshots = [baseline_used]
    for entry in _required_mapping_sequence(ledger, "entries"):
        for key in ("gateway_quota_before", "gateway_quota_after"):
            value = entry.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                snapshots.append(value)
    total_used = max(snapshots)
    total_granted = baseline_used + baseline_available
    if total_used > total_granted:
        raise RuntimeError("cached gateway quota exceeds the frozen grant")
    return (
        {
            "total_granted": total_granted,
            "total_used": total_used,
            "total_available": total_granted - total_used,
        },
        "cached_between_six_cell_checkpoints",
        _required_string(accounting, "latest_live_observed_at"),
    )


def _require_no_overdue_campaign_receipts(
    paths: StudyPaths,
    campaign_id: str,
    next_sequence_index: int,
) -> None:
    current_block_start = (
        next_sequence_index // QUOTA_CHECKPOINT_CELL_INTERVAL
    ) * QUOTA_CHECKPOINT_CELL_INTERVAL
    ledger = _load_json(paths.study_output / STUDY_LEDGER_NAME)
    overdue = [
        entry
        for entry in _required_mapping_sequence(ledger, "entries")
        if entry.get("campaign_id") == campaign_id
        and isinstance(entry.get("sequence_index"), int)
        and cast(int, entry["sequence_index"]) < current_block_start
        and not isinstance(entry.get("gateway_log_receipt"), Mapping)
    ]
    if overdue:
        raise RuntimeError("prior campaign block has unreconciled token receipts")


def _run_accounted_campaign_cell(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    campaign_config: Mapping[str, Any],
    context: ReplicateCampaignContext,
    campaign_dir: Path,
    expected_cell: ResolvedReplicateScheduleCell,
) -> AccountedCall:
    with _study_call_guard(paths):
        current_cell = preflight_replicate_campaign(context)
        if (
            current_cell is None
            or current_cell.schedule_cell != expected_cell.schedule_cell
        ):
            raise RuntimeError("campaign cell changed while waiting for study lock")
        _require_no_overdue_campaign_receipts(
            paths,
            context.schedule.campaign_id,
            current_cell.schedule_cell.sequence_index,
        )
        (
            quota_before,
            quota_before_source,
            quota_before_observed_at,
        ) = _quota_checkpoint_for_cell(
            paths,
            current_cell.schedule_cell.sequence_index,
        )
        _require_study_budget_guard(
            paths,
            plan,
            quota_before,
            campaign_config,
        )
        result: ResultRecord | None = None
        error: BaseException | None = None
        try:
            result = run_next_replicate_campaign_cell(
                context,
                artifact_config=WorkspaceArtifactConfig(
                    output_root=campaign_dir / "raw" / "agent-runs",
                    preserve_solver_workspace_summary="on_failure",
                    preserve_verifier_workspace_summary="on_failure",
                ),
            )
        except BaseException as exc:
            error = exc
            result = _exact_result_for_study_cell(
                context,
                current_cell.schedule_cell,
            )
        gateway_log_receipt: Mapping[str, Any] | None = None
        quota_after: Mapping[str, int] | None = None
        _record_study_call(
            paths,
            plan,
            context,
            current_cell.schedule_cell.sequence_index,
            current_cell.schedule_cell.agent_id,
            quota_before,
            quota_after,
            result,
            error,
            gateway_log_receipt,
            None,
            quota_before_source,
            quota_before_observed_at,
            math.ceil(
                _required_number(
                    campaign_config,
                    "maximum_estimated_cost_per_call_usd",
                )
                * _required_int(
                    _required_mapping(plan, "budget"),
                    "quota_points_per_usd",
                )
            ),
        )
        accounting_error: BaseException | None = None
        should_reconcile_receipts = (
            (current_cell.schedule_cell.sequence_index + 1)
            % QUOTA_CHECKPOINT_CELL_INTERVAL
            == 0
            or current_cell.schedule_cell.sequence_index + 1
            == len(context.schedule.cells)
            or error is not None
        )
        if result is not None and should_reconcile_receipts:
            try:
                gateway_log_receipt = _reconcile_campaign_pending_receipts(
                    paths,
                    plan,
                    context,
                    result.result_id,
                )
            except BaseException as exc:
                accounting_error = exc
                _mark_study_call_accounting_error(
                    paths,
                    context.schedule.campaign_id,
                    current_cell.schedule_cell.sequence_index,
                    exc,
                )
        if error is not None:
            raise error
        if accounting_error is not None:
            raise accounting_error
        if result is None:
            raise RuntimeError("campaign advanced without an exact Result")
        return AccountedCall(
            result,
            quota_before,
            quota_after,
            gateway_log_receipt,
        )


@contextmanager
def _study_call_guard(paths: StudyPaths) -> Iterator[None]:
    lock_path = paths.study_output / ".paid-call.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _record_study_call(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    context: ReplicateCampaignContext,
    sequence_index: int,
    agent_id: str,
    quota_before: Mapping[str, int],
    quota_after: Mapping[str, int] | None,
    result: ResultRecord | None,
    error: BaseException | None,
    gateway_log_receipt: Mapping[str, Any] | None,
    accounting_error: BaseException | None,
    quota_before_source: str,
    quota_before_observed_at: str,
    pending_receipt_reserve_quota_points: int,
) -> None:
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    ledger = dict(_load_json(ledger_path))
    if quota_before_source == "live_six_cell_checkpoint":
        accounting = dict(_required_mapping(ledger, "gateway_accounting"))
        accounting["latest_live_total_used"] = quota_before["total_used"]
        accounting["latest_live_observed_at"] = quota_before_observed_at
        accounting["latest_live_source"] = "paid_cell_preflight"
        ledger["gateway_accounting"] = accounting
    entries = list(_required_mapping_sequence(ledger, "entries"))
    quota_delta = (
        None
        if quota_after is None
        else quota_after["total_used"] - quota_before["total_used"]
    )
    if quota_delta is not None and quota_delta < 0:
        raise RuntimeError("gateway total_used moved backwards")
    estimated_cost = (
        None if result is None else _optional_result_number(result.cost, "total_cost")
    )
    points_per_usd = _required_int(
        _required_mapping(plan, "budget"),
        "quota_points_per_usd",
    )
    entries.append(
        {
            "time": (result.finished_at if result is not None else _utc_now()),
            "action": "execute frozen benchmark campaign cell",
            "resource": "benchmark_model_call",
            "amount": 1,
            "unit": "call",
            "status": "observed",
            "campaign_id": context.schedule.campaign_id,
            "sequence_index": sequence_index,
            "agent_id": agent_id,
            "result_id": None if result is None else result.result_id,
            "result_state": None if result is None else result.scoreable_state,
            "estimated_cost_usd": estimated_cost,
            "gateway_quota_before": quota_before["total_used"],
            "gateway_quota_before_source": quota_before_source,
            "gateway_quota_before_observed_at": quota_before_observed_at,
            "gateway_quota_after": (
                None if quota_after is None else quota_after["total_used"]
            ),
            "gateway_quota_after_status": "deferred_to_periodic_reconciliation",
            "gateway_quota_delta": quota_delta,
            "gateway_cost_usd": (
                None if quota_delta is None else quota_delta / points_per_usd
            ),
            "gateway_log_receipt": gateway_log_receipt,
            "gateway_log_receipt_status": (
                "pending" if gateway_log_receipt is None else "exact"
            ),
            "pending_receipt_reserve_quota_points": (
                pending_receipt_reserve_quota_points
            ),
            "gateway_log_quota_points": (
                None
                if gateway_log_receipt is None
                else gateway_log_receipt["quota_points"]
            ),
            "gateway_log_cost_usd": (
                None
                if gateway_log_receipt is None
                else cast(int, gateway_log_receipt["quota_points"])
                / points_per_usd
            ),
            "error": None if error is None else type(error).__name__,
            "accounting_error": (
                None if accounting_error is None else type(accounting_error).__name__
            ),
            "quota_after_error": None,
            "evidence": (
                "campaign ledger, exact Result, and provider token-usage endpoint"
            ),
            "decision_changed": error is not None or accounting_error is not None,
        }
    )
    _write_study_resource_ledger(
        ledger_path,
        ledger,
        entries,
        points_per_usd=points_per_usd,
        latest_gateway_total_used=(
            quota_before["total_used"]
            if quota_after is None
            else quota_after["total_used"]
        ),
    )


def _reconcile_campaign_pending_receipts(
    paths: StudyPaths,
    plan: Mapping[str, Any],
    context: ReplicateCampaignContext,
    current_result_id: str,
) -> Mapping[str, Any]:
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    ledger = dict(_load_json(ledger_path))
    entries = [
        dict(entry) for entry in _required_mapping_sequence(ledger, "entries")
    ]
    pending = [
        entry
        for entry in entries
        if entry.get("action") == "execute frozen benchmark campaign cell"
        and entry.get("campaign_id") == context.schedule.campaign_id
        and isinstance(entry.get("result_id"), str)
        and not isinstance(entry.get("gateway_log_receipt"), Mapping)
    ]
    if not pending:
        raise RuntimeError("receipt checkpoint has no pending campaign Results")
    result_records = tuple(
        load_jsonl_records(context.result_store.path, ResultRecord)
    )
    results = {result.result_id: result for result in result_records}
    if len(results) != len(result_records):
        raise RuntimeError("campaign Result Store has duplicate Result IDs")
    receipt_by_result_id: dict[str, Mapping[str, Any]] = {}
    for attempt in range(6):
        rows = _gateway_token_logs()
        try:
            receipt_by_result_id = {
                cast(str, entry["result_id"]): _gateway_log_receipt(
                    results[cast(str, entry["result_id"])],
                    rows,
                )
                for entry in pending
            }
            break
        except KeyError as exc:
            raise RuntimeError("pending receipt lacks its exact Result") from exc
        except GatewayReceiptIncomplete:
            if attempt == 5:
                raise
            time.sleep(min(2**attempt, 16))
    points_per_usd = _required_int(
        _required_mapping(plan, "budget"),
        "quota_points_per_usd",
    )
    for entry in pending:
        result_id = cast(str, entry["result_id"])
        receipt = receipt_by_result_id[result_id]
        entry["gateway_log_receipt"] = receipt
        entry["gateway_log_receipt_status"] = "exact"
        entry["gateway_log_quota_points"] = receipt["quota_points"]
        entry["gateway_log_cost_usd"] = (
            cast(int, receipt["quota_points"]) / points_per_usd
        )
        entry["accounting_error"] = None
        entry["receipt_reconciled_at"] = _utc_now()
        entry["reconciliation"] = (
            "one campaign-block token-log snapshot with exact Result token match"
        )
    latest_live_total_used = _required_int(
        _required_mapping(ledger, "gateway_accounting"),
        "latest_live_total_used",
    )
    _write_study_resource_ledger(
        ledger_path,
        ledger,
        entries,
        points_per_usd=points_per_usd,
        latest_gateway_total_used=latest_live_total_used,
    )
    receipt = receipt_by_result_id.get(current_result_id)
    if receipt is None:
        raise RuntimeError("receipt checkpoint omitted the current Result")
    return receipt


def reconcile_campaign_receipts(
    paths: StudyPaths,
    campaign_id: str,
    amendment_path: Path = DEFAULT_AMENDMENT,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    """Reconcile one campaign's pending Results from one token-log snapshot."""
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    _activate_llm_proxy_environment(plan)
    if (paths.study_output / "calibration" / campaign_id).exists():
        config = _calibration_campaign_config(plan, campaign_id, decision)
        context = _load_calibration_context(paths, plan, config, decision)
    elif (paths.study_output / "calibration-canaries" / campaign_id).exists():
        config = _canary_config(amendment, campaign_id)
        context, _ = _load_canary_context(paths, plan, amendment, config)
    elif (
        campaign_id == MAIN_CAMPAIGN_ID
        and (paths.study_output / "main" / MAIN_CAMPAIGN_ID).exists()
    ):
        context, _, _ = _load_main_context(paths, plan)
    else:
        raise ValueError(f"unknown prepared study campaign: {campaign_id}")
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    with _study_call_guard(paths):
        ledger = _load_json(ledger_path)
        pending = tuple(
            entry
            for entry in _required_mapping_sequence(ledger, "entries")
            if entry.get("action") == "execute frozen benchmark campaign cell"
            and entry.get("campaign_id") == campaign_id
            and isinstance(entry.get("sequence_index"), int)
            and isinstance(entry.get("result_id"), str)
            and not isinstance(entry.get("gateway_log_receipt"), Mapping)
        )
        if not pending:
            return {
                "stage": "complete",
                "campaign_id": campaign_id,
                "reconciled_receipt_count": 0,
                "pending_receipt_count": 0,
            }
        latest = max(pending, key=lambda entry: cast(int, entry["sequence_index"]))
        current_result_id = cast(str, latest["result_id"])
        _reconcile_campaign_pending_receipts(
            paths,
            plan,
            context,
            current_result_id,
        )
        refreshed = _load_json(ledger_path)
        remaining = tuple(
            entry
            for entry in _required_mapping_sequence(refreshed, "entries")
            if entry.get("action") == "execute frozen benchmark campaign cell"
            and entry.get("campaign_id") == campaign_id
            and isinstance(entry.get("result_id"), str)
            and not isinstance(entry.get("gateway_log_receipt"), Mapping)
        )
    return {
        "stage": "campaign_receipts_reconciled",
        "campaign_id": campaign_id,
        "reconciled_receipt_count": len(pending),
        "pending_receipt_count": len(remaining),
    }


def _mark_study_call_accounting_error(
    paths: StudyPaths,
    campaign_id: str,
    sequence_index: int,
    error: BaseException,
) -> None:
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    ledger = dict(_load_json(ledger_path))
    entries = [
        dict(entry) for entry in _required_mapping_sequence(ledger, "entries")
    ]
    matches = [
        entry
        for entry in entries
        if entry.get("campaign_id") == campaign_id
        and entry.get("sequence_index") == sequence_index
    ]
    if len(matches) != 1:
        raise RuntimeError("cannot mark one study accounting error")
    matches[0]["accounting_error"] = type(error).__name__
    matches[0]["gateway_log_receipt_status"] = "pending"
    matches[0]["decision_changed"] = True
    accounting = _required_mapping(ledger, "gateway_accounting")
    latest = _required_int(accounting, "latest_live_total_used")
    _write_study_resource_ledger(
        ledger_path,
        ledger,
        entries,
        points_per_usd=_required_int(accounting, "quota_points_per_usd"),
        latest_gateway_total_used=latest,
    )


def reconcile_study_resource_ledger(
    paths: StudyPaths,
    amendment_path: Path = DEFAULT_AMENDMENT,
    decision_amendment_path: Path = DEFAULT_DECISION_AMENDMENT,
) -> Mapping[str, Any]:
    """Reconcile campaign Results to exact token logs and the eventual balance."""
    plan = _load_plan(paths.plan_path)
    amendment = _load_amendment(amendment_path, plan)
    decision = _load_decision_amendment(decision_amendment_path, plan)
    _activate_llm_proxy_environment(plan)
    ledger_path = paths.study_output / STUDY_LEDGER_NAME
    with _study_call_guard(paths):
        ledger = dict(_load_json(ledger_path))
        entries = [
            dict(entry) for entry in _required_mapping_sequence(ledger, "entries")
        ]
        contexts: list[ReplicateCampaignContext] = []
        for config in _required_mapping_sequence(
            _required_mapping(plan, "calibration"),
            "campaigns",
        ):
            campaign_id = _required_string(config, "campaign_id")
            results_path = (
                paths.study_output
                / "calibration"
                / campaign_id
                / "records"
                / "results.jsonl"
            )
            if results_path.exists():
                contexts.append(_load_calibration_context(paths, plan, config))
        for config in _required_mapping_sequence(
            decision,
            "replacement_calibration_campaigns",
        ):
            campaign_id = _required_string(config, "campaign_id")
            results_path = (
                paths.study_output
                / "calibration"
                / campaign_id
                / "records"
                / "results.jsonl"
            )
            if results_path.exists():
                contexts.append(
                    _load_calibration_context(paths, plan, config, decision)
                )
        for config in _required_mapping_sequence(amendment, "canaries"):
            campaign_id = _required_string(config, "campaign_id")
            results_path = (
                paths.study_output
                / "calibration-canaries"
                / campaign_id
                / "records"
                / "results.jsonl"
            )
            if results_path.exists():
                context, _ = _load_canary_context(paths, plan, amendment, config)
                contexts.append(context)
        main_results_path = (
            paths.study_output
            / "main"
            / MAIN_CAMPAIGN_ID
            / "records"
            / "results.jsonl"
        )
        if main_results_path.exists():
            context, _, _ = _load_main_context(paths, plan)
            contexts.append(context)

        entry_by_cell: dict[tuple[str, int], dict[str, Any]] = {}
        for entry in entries:
            if entry.get("action") != "execute frozen benchmark campaign cell":
                continue
            campaign_id = entry.get("campaign_id")
            sequence_index = entry.get("sequence_index")
            if not isinstance(campaign_id, str) or not isinstance(
                sequence_index,
                int,
            ):
                raise RuntimeError("study call entry lacks a campaign cell identity")
            key = (campaign_id, sequence_index)
            if key in entry_by_cell:
                raise RuntimeError("study resource ledger has duplicate campaign cells")
            entry_by_cell[key] = entry

        points_per_usd = _required_int(
            _required_mapping(plan, "budget"),
            "quota_points_per_usd",
        )
        reconciled = 0
        appended = 0
        recovered_missing_receipt = False
        for context in contexts:
            for cell in context.schedule.cells:
                result = _exact_result_for_study_cell(context, cell)
                if result is None:
                    continue
                key = (context.schedule.campaign_id, cell.sequence_index)
                entry = entry_by_cell.get(key)
                if entry is None:
                    entry = {
                        "time": result.finished_at,
                        "action": "execute frozen benchmark campaign cell",
                        "resource": "benchmark_model_call",
                        "amount": 1,
                        "unit": "call",
                        "status": "observed_recovered",
                        "campaign_id": context.schedule.campaign_id,
                        "sequence_index": cell.sequence_index,
                        "agent_id": cell.agent_id,
                        "gateway_quota_before": None,
                        "gateway_quota_after": None,
                        "gateway_quota_delta": None,
                        "gateway_cost_usd": None,
                        "error": None,
                        "accounting_error": None,
                        "quota_after_error": "historical_balance_snapshot_unavailable",
                        "decision_changed": True,
                    }
                    entries.append(entry)
                    entry_by_cell[key] = entry
                    appended += 1
                persisted_receipt = entry.get("gateway_log_receipt")
                if isinstance(persisted_receipt, Mapping):
                    receipt = cast(Mapping[str, Any], persisted_receipt)
                    _validate_gateway_log_receipt(result, receipt)
                else:
                    receipt = _eventual_gateway_log_receipt(result)
                    recovered_missing_receipt = True
                entry["result_id"] = result.result_id
                entry["result_state"] = result.scoreable_state
                entry["estimated_cost_usd"] = _optional_result_number(
                    result.cost,
                    "total_cost",
                )
                entry["gateway_log_receipt"] = receipt
                entry["gateway_log_quota_points"] = receipt["quota_points"]
                entry["gateway_log_cost_usd"] = (
                    cast(int, receipt["quota_points"]) / points_per_usd
                )
                entry["reconciled_at"] = _utc_now()
                entry["reconciliation"] = (
                    "exact Result plus model/time token logs; balance snapshots "
                    "remain eventual global guard evidence"
                )
                entry["evidence"] = (
                    "campaign ledger, exact Result, sanitized gateway token-log "
                    "receipt, and eventual provider token-usage balance"
                )
                reconciled += 1
        if recovered_missing_receipt:
            quota, _, _ = _quota_checkpoint_for_cell(paths, 1)
        else:
            quota = _gateway_quota()
        gateway_accounting = dict(_required_mapping(ledger, "gateway_accounting"))
        if not recovered_missing_receipt:
            gateway_accounting["latest_live_total_used"] = quota["total_used"]
            gateway_accounting["latest_live_observed_at"] = _utc_now()
            gateway_accounting["latest_live_source"] = (
                "resource_ledger_reconciliation"
            )
        gateway_accounting["last_reconciliation_balance_status"] = (
            "deferred_while_recovering_missing_receipt"
            if recovered_missing_receipt
            else "live"
        )
        gateway_accounting["per_call_accounting"] = (
            "model/time token-log rows with exact Result token-total match"
        )
        gateway_accounting["balance_semantics"] = (
            "eventually consistent global guard and aggregate reconciliation; "
            "not per-call attribution"
        )
        ledger["gateway_accounting"] = gateway_accounting
        _write_study_resource_ledger(
            ledger_path,
            ledger,
            entries,
            points_per_usd=points_per_usd,
            latest_gateway_total_used=quota["total_used"],
        )
    return {
        "stage": "resource_ledger_reconciled",
        "reconciled_result_count": reconciled,
        "appended_missing_call_count": appended,
        "entry_count": len(entries),
        "gateway_total_used": quota["total_used"],
    }


def _write_study_resource_ledger(
    ledger_path: Path,
    ledger: dict[str, Any],
    entries: Sequence[Mapping[str, Any]],
    *,
    points_per_usd: int,
    latest_gateway_total_used: int,
) -> None:
    baseline = _required_int(
        _required_mapping(ledger, "gateway_accounting"),
        "baseline_total_used",
    )
    balance_window_delta_sum = sum(
        cast(int, entry["gateway_quota_delta"])
        for entry in entries
        if entry.get("action") == "execute frozen benchmark campaign cell"
        and isinstance(entry.get("gateway_quota_delta"), int)
    )
    attributed_log_quota = sum(
        cast(int, entry["gateway_log_quota_points"])
        for entry in entries
        if entry.get("action") == "execute frozen benchmark campaign cell"
        and isinstance(entry.get("gateway_log_quota_points"), int)
    )
    global_movement = latest_gateway_total_used - baseline
    if global_movement < 0:
        raise RuntimeError("gateway total_used moved before the study baseline")
    totals = [
        {
            "resource": "authorized_model_spend",
            "amount": sum(
                float(entry["estimated_cost_usd"])
                for entry in entries
                if isinstance(entry.get("estimated_cost_usd"), int | float)
                and not isinstance(entry.get("estimated_cost_usd"), bool)
            ),
            "unit": "USD",
            "status": "estimated",
        },
        {
            "resource": "observed_gateway_attributed_quota",
            "amount": attributed_log_quota,
            "unit": "quota_points",
            "status": "observed_token_log",
        },
        {
            "resource": "observed_gateway_attributed_cost",
            "amount": attributed_log_quota / points_per_usd,
            "unit": "USD",
            "status": "observed_token_log",
        },
        {
            "resource": "gateway_balance_window_delta_sum",
            "amount": balance_window_delta_sum,
            "unit": "quota_points",
            "status": "diagnostic_nonadditive_eventual_balance",
        },
        {
            "resource": "observed_gateway_global_total_used_movement",
            "amount": global_movement,
            "unit": "quota_points",
            "status": "observed_non_attributable",
        },
        {
            "resource": "conservative_gateway_budget_consumption",
            "amount": max(global_movement, attributed_log_quota) / points_per_usd,
            "unit": "USD",
            "status": "maximum_of_global_balance_and_attributed_logs",
        },
        {
            "resource": "gateway_global_minus_attributed_log_quota",
            "amount": global_movement - attributed_log_quota,
            "unit": "quota_points",
            "status": "aggregate_reconciliation_residual",
        },
        {
            "resource": "benchmark_model_calls",
            "amount": sum(
                entry.get("action") == "execute frozen benchmark campaign cell"
                for entry in entries
            ),
            "unit": "calls",
            "status": "observed",
        },
    ]
    ledger["entries"] = list(entries)
    ledger["totals"] = totals
    write_json(ledger_path, ledger)


def _exact_result_for_study_cell(
    context: ReplicateCampaignContext,
    cell: ReplicateScheduleCell,
) -> ResultRecord | None:
    if not context.result_store.path.exists():
        return None
    matches = tuple(
        result
        for result in load_jsonl_records(context.result_store.path, ResultRecord)
        if result.agent_id == cell.agent_id
        and result.task_id == cell.task_id
        and result.check_id == cell.check_id
        and result.cache_identity.runtime_config_digest == cell.runtime_config_digest
        and result.scoring_config_digest
        == context.scoring_config.scoring_config_digest
    )
    if len(matches) > 1:
        raise RuntimeError("study campaign cell has duplicate exact Results")
    return matches[0] if matches else None


def _select_main_agents(
    plan: Mapping[str, Any],
    agent_rows: Mapping[str, Mapping[str, Any]],
    outcomes: Mapping[tuple[str, str], str],
) -> tuple[str, str]:
    eligible = [
        key
        for key, row in agent_rows.items()
        if row["scoreable_count"] == row["result_count"]
    ]
    if len(eligible) < 2:
        raise RuntimeError("fewer than two calibration Agents are eligible")
    first = min(
        eligible,
        key=lambda key: (
            -cast(int, agent_rows[key]["base_pass_count"]),
            cast(float, agent_rows[key]["attributed_gateway_cost_usd"]),
            key,
        ),
    )
    best_passes = cast(int, agent_rows[first]["base_pass_count"])
    candidates: list[str] = []
    for key in eligible:
        if key == first:
            continue
        row = agent_rows[key]
        if cast(int, row["base_pass_count"]) < best_passes - 2:
            continue
        candidates.append(key)
    if not candidates:
        candidates = [key for key in eligible if key != first]
    first_tasks = {task_id for key, task_id in outcomes if key == first}

    def rank(key: str) -> tuple[Any, ...]:
        paired = first_tasks & {task_id for item, task_id in outcomes if item == key}
        disagreement = sum(
            outcomes[(first, task_id)] != outcomes[(key, task_id)] for task_id in paired
        )
        return (
            -disagreement,
            -cast(int, agent_rows[key]["base_pass_count"]),
            cast(float, agent_rows[key]["attributed_gateway_cost_usd"]),
            (
                agent_rows[key]["provider_family"]
                == agent_rows[first]["provider_family"]
            ),
            key,
        )

    second = min(candidates, key=rank)
    del plan
    return first, second


def _require_preflight_marker(
    campaign_dir: Path,
    plan: Mapping[str, Any],
    context: ReplicateCampaignContext,
) -> None:
    marker = _load_json(campaign_dir / "preflight-summary.json")
    if (
        marker.get("study_plan_digest") != plan["study_plan_digest"]
        or marker.get("schedule_digest") != context.schedule.schedule_digest
        or marker.get("endpoint_digest")
        != _required_string(
            _required_mapping(plan, "endpoint_mapping"),
            "endpoint_digest",
        )
        or marker.get("stage") not in {"preflight_passed", "complete"}
    ):
        raise RuntimeError("calibration preflight marker is stale")


def _calibration_campaign_config(
    plan: Mapping[str, Any],
    campaign_id: str,
    decision_amendment: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    base_matches = tuple(
        campaign
        for campaign in _required_mapping_sequence(
            _required_mapping(plan, "calibration"),
            "campaigns",
        )
        if campaign.get("campaign_id") == campaign_id
    )
    if len(base_matches) == 1:
        return base_matches[0]
    replacement_matches: tuple[Mapping[str, Any], ...] = ()
    if decision_amendment is not None:
        replacement_matches = tuple(
            campaign
            for campaign in _required_mapping_sequence(
                decision_amendment,
                "replacement_calibration_campaigns",
            )
            if campaign.get("campaign_id") == campaign_id
        )
    if len(base_matches) + len(replacement_matches) != 1:
        raise ValueError(f"unknown calibration campaign: {campaign_id}")
    return next(iter(replacement_matches))


def _canary_config(
    amendment: Mapping[str, Any],
    campaign_id: str,
) -> Mapping[str, Any]:
    matches = tuple(
        config
        for config in _required_mapping_sequence(amendment, "canaries")
        if config.get("campaign_id") == campaign_id
    )
    if len(matches) != 1:
        raise ValueError(f"unknown protocol canary: {campaign_id}")
    return matches[0]


def _pilot_paths(output_dir: Path) -> PilotPaths:
    return PilotPaths(
        output_dir=output_dir.resolve(),
        target_repo=(output_dir / "target-repo").resolve(),
        dataset=(output_dir / "source" / DEFAULT_DATASET_NAME).resolve(),
        supplemental_dataset=(
            output_dir / "source" / DEFAULT_SUPPLEMENTAL_DATASET_NAME
        ).resolve(),
        harness_python=(output_dir / "harness-env/bin/python").absolute(),
    )


def _load_plan(path: Path) -> Mapping[str, Any]:
    plan = _load_json(path)
    digest = _required_string(plan, "study_plan_digest")
    payload = dict(plan)
    payload.pop("study_plan_digest")
    if canonical_digest(payload) != digest:
        raise ValueError("study plan digest does not match")
    if plan.get("schema_version") != "barcarolle_model_agent_study_v1":
        raise ValueError("study plan schema is unsupported")
    return plan


def _load_amendment(
    path: Path,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    amendment = _load_json(path)
    digest = _required_string(amendment, "amendment_digest")
    payload = dict(amendment)
    payload.pop("amendment_digest")
    if canonical_digest(payload) != digest:
        raise ValueError("study amendment digest does not match")
    if amendment.get("schema_version") != "barcarolle_model_agent_study_amendment_v1":
        raise ValueError("study amendment schema is unsupported")
    if amendment.get("base_study_plan_digest") != plan["study_plan_digest"]:
        raise ValueError("study amendment does not bind the base plan")
    return amendment


def _load_decision_amendment(
    path: Path,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    amendment = _load_json(path)
    digest = _required_string(amendment, "amendment_digest")
    payload = dict(amendment)
    payload.pop("amendment_digest")
    if canonical_digest(payload) != digest:
        raise ValueError("study decision amendment digest does not match")
    if (
        amendment.get("schema_version")
        != "barcarolle_model_agent_study_amendment_v2"
    ):
        raise ValueError("study decision amendment schema is unsupported")
    if amendment.get("base_study_plan_digest") != plan["study_plan_digest"]:
        raise ValueError("study decision amendment does not bind the base plan")
    protocol = _load_amendment(DEFAULT_AMENDMENT, plan)
    if amendment.get("previous_amendment_digest") != protocol["amendment_digest"]:
        raise ValueError("study decision amendment does not bind amendment 1")
    return amendment


def canonical_data_mapping(value: Any) -> Mapping[str, Any]:
    payload = json.loads(canonical_json(value))
    if not isinstance(payload, Mapping):
        raise TypeError("canonical value must be an object")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _one_record(path: Path, record_type: type[Any]) -> Any:
    records = tuple(load_jsonl_records(path, record_type))
    if len(records) != 1:
        raise ValueError(f"{path} must contain exactly one record")
    return records[0]


def _required_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _required_mapping_sequence(
    value: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    items = value.get(key)
    if (
        not isinstance(items, Sequence)
        or isinstance(items, str)
        or any(not isinstance(item, Mapping) for item in items)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(cast(Mapping[str, Any], item) for item in items)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _required_string_sequence(
    value: Mapping[str, Any],
    key: str,
) -> tuple[str, ...]:
    items = value.get(key)
    if (
        not isinstance(items, Sequence)
        or isinstance(items, str)
        or any(not isinstance(item, str) or not item for item in items)
    ):
        raise ValueError(f"{key} must be an array of nonempty strings")
    return tuple(cast(str, item) for item in items)


def _required_int(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _required_number(value: Mapping[str, Any], key: str) -> float:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int | float):
        raise ValueError(f"{key} must be a number")
    number = float(item)
    if not math.isfinite(number):
        raise ValueError(f"{key} must be finite")
    return number


def _numeric_mapping(
    value: Mapping[str, Any],
    label: str,
) -> Mapping[str, float]:
    rates = {key: _required_number(value, key) for key in value if isinstance(key, str)}
    if len(rates) != len(value) or not rates:
        raise ValueError(f"{label} must map names to numbers")
    return rates


def _result_number(value: Mapping[str, Any], key: str) -> float:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int | float):
        raise RuntimeError(f"Result {key} is not measured")
    number = float(item)
    if not math.isfinite(number):
        raise RuntimeError(f"Result {key} is not finite")
    return number


def _optional_result_number(value: Mapping[str, Any], key: str) -> float | None:
    item = value.get(key)
    if item is None:
        return None
    return _result_number(value, key)


def _codex_cli_version() -> str:
    completed = subprocess.run(
        ("codex", "--version"),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError("could not resolve Codex CLI version")
    return completed.stdout.strip()


def _utc_now() -> str:
    from barcarolle.records import utc_now_timestamp

    return utc_now_timestamp()


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--amendment", type=Path, default=DEFAULT_AMENDMENT)
    parser.add_argument(
        "--decision-amendment",
        type=Path,
        default=DEFAULT_DECISION_AMENDMENT,
    )
    parser.add_argument("--study-output", type=Path, default=DEFAULT_STUDY_OUTPUT)
    parser.add_argument("--pilot-output", type=Path, default=DEFAULT_PILOT_OUTPUT)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("prepare-calibration")
    actions.add_parser("prepare-replacement-calibration")
    actions.add_parser("prepare-protocol-canaries")
    preflight = actions.add_parser("preflight-calibration")
    preflight.add_argument("--campaign-id", required=True)
    preflight_canary = actions.add_parser("preflight-protocol-canary")
    preflight_canary.add_argument("--campaign-id", required=True)
    run_next = actions.add_parser("run-next-calibration")
    run_next.add_argument("--campaign-id", required=True)
    run_next_canary = actions.add_parser("run-next-protocol-canary")
    run_next_canary.add_argument("--campaign-id", required=True)
    reconcile_receipts = actions.add_parser("reconcile-campaign-receipts")
    reconcile_receipts.add_argument("--campaign-id", required=True)
    actions.add_parser("summarize-calibration")
    actions.add_parser("summarize-protocol-canaries")
    actions.add_parser("prepare-main")
    actions.add_parser("preflight-main")
    actions.add_parser("run-next-main")
    actions.add_parser("summarize-main")
    actions.add_parser("reconcile-resource-ledger")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    paths = StudyPaths(
        plan_path=args.plan.resolve(),
        study_output=args.study_output.resolve(),
        pilot_output=args.pilot_output.resolve(),
    )
    if args.action == "prepare-calibration":
        summary = prepare_calibration(paths)
    elif args.action == "prepare-replacement-calibration":
        summary = prepare_replacement_calibration(
            paths,
            args.decision_amendment.resolve(),
        )
    elif args.action == "prepare-protocol-canaries":
        summary = prepare_protocol_canaries(paths, args.amendment.resolve())
    elif args.action == "preflight-calibration":
        summary = preflight_calibration_campaign(
            paths,
            args.campaign_id,
            args.decision_amendment.resolve(),
        )
    elif args.action == "preflight-protocol-canary":
        summary = preflight_protocol_canary(
            paths,
            args.amendment.resolve(),
            args.campaign_id,
        )
    elif args.action == "run-next-calibration":
        summary = run_next_calibration_cell(
            paths,
            args.campaign_id,
            args.decision_amendment.resolve(),
        )
    elif args.action == "run-next-protocol-canary":
        summary = run_next_protocol_canary(
            paths,
            args.amendment.resolve(),
            args.campaign_id,
        )
    elif args.action == "reconcile-campaign-receipts":
        summary = reconcile_campaign_receipts(
            paths,
            args.campaign_id,
            args.amendment.resolve(),
            args.decision_amendment.resolve(),
        )
    elif args.action == "summarize-calibration":
        summary = summarize_calibration(
            paths,
            args.decision_amendment.resolve(),
        )
    elif args.action == "summarize-protocol-canaries":
        summary = summarize_protocol_canaries(paths, args.amendment.resolve())
    elif args.action == "prepare-main":
        summary = prepare_main(paths, args.decision_amendment.resolve())
    elif args.action == "preflight-main":
        summary = preflight_main(paths)
    elif args.action == "reconcile-resource-ledger":
        summary = reconcile_study_resource_ledger(
            paths,
            args.amendment.resolve(),
            args.decision_amendment.resolve(),
        )
    elif args.action == "summarize-main":
        summary = summarize_main(paths)
    else:
        summary = run_next_main_cell(paths)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
