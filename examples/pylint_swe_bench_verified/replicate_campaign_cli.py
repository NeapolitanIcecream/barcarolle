#!/usr/bin/env python3
"""Authorize, preflight, or run one frozen Pylint replicate campaign cell."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import cast


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    ResultRecord,
    RuntimeConfig,
    canonical_digest,
    load_jsonl_records,
)
from barcarolle.result_store import ResultStore, ScoringConfig  # noqa: E402
from barcarolle.workspace import (  # noqa: E402
    bind_agent_harness,
    resolve_openai_endpoint_digest,
)
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
    ResolvedReplicateScheduleCell,
)


@dataclass(frozen=True)
class CampaignCliPaths:
    pilot: PilotPaths
    campaign_dir: Path
    agents_path: Path
    runtime_config_path: Path
    schedule_path: Path
    result_store_path: Path
    ledger_path: Path


def build_campaign_context(
    paths: CampaignCliPaths,
    scoring_config: ScoringConfig,
) -> ReplicateCampaignContext:
    """Load frozen campaign inputs and bind the concrete Pylint adapter."""
    agents = tuple(load_jsonl_records(paths.agents_path, AgentRecord))
    (base_runtime_config,) = load_jsonl_records(
        paths.runtime_config_path,
        RuntimeConfig,
    )
    (schedule,) = load_jsonl_records(paths.schedule_path, ReplicateSchedule)
    pilot = build_pilot_context(paths.pilot, paths.ledger_path)
    run_context = pilot.run_context
    endpoint_paths = (HARNESS, HARNESS.parent / "extract-usage.py")
    for agent in agents:
        run_context = bind_agent_harness(
            run_context,
            agent,
            _agent_command(paths.campaign_dir, agent),
            execution_mode="openai_paid",
            endpoint_harness_paths=endpoint_paths,
        )
    checks = tuple(pilot.checks[check_id] for check_id in pilot.task_pool.check_ids)
    return ReplicateCampaignContext(
        schedule=schedule,
        task_pool=pilot.task_pool,
        tasks=pilot.tasks,
        checks=checks,
        agents=agents,
        base_runtime_config=base_runtime_config,
        workspace_config=pilot.workspace_config,
        scoring_config=scoring_config,
        result_store=ResultStore(paths.result_store_path),
        ledger_path=paths.ledger_path,
        run_context=run_context,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    paths = _campaign_paths(args)
    if args.action == "authorize":
        scoring_config = ScoringConfig(
            pricing_version=args.pricing_version,
            cost_rates=_cost_rates(args.cost_rate),
        )
        context = build_campaign_context(paths, scoring_config)
        endpoint_digest = resolve_openai_endpoint_digest(require_api_key=True)
        ledger = initialize_replicate_campaign_ledger(
            context,
            approved_at=args.approved_at,
            endpoint_digest=endpoint_digest,
            maximum_estimated_cost_usd=args.maximum_estimated_cost_usd,
            maximum_estimated_cost_per_call_usd=(
                args.maximum_estimated_cost_per_call_usd
            ),
            pricing_sources=tuple(args.pricing_source),
            accounting_basis=args.accounting_basis,
            scope=args.scope,
        )
        limits = _mapping(ledger.get("limits"), "campaign limits")
        summary: Mapping[str, object] = {
            "stage": "authorized",
            "campaign_id": context.schedule.campaign_id,
            "ledger_path": str(context.ledger_path),
            "maximum_paid_calls": limits["maximum_paid_calls"],
            "maximum_estimated_cost_usd": args.maximum_estimated_cost_usd,
            "maximum_estimated_cost_per_call_usd": (
                args.maximum_estimated_cost_per_call_usd
            ),
            "next": "preflight",
        }
    else:
        scoring_config = _scoring_config_from_ledger(paths.ledger_path)
        context = build_campaign_context(paths, scoring_config)
        if args.action == "preflight":
            verified_images = verify_pylint_verifier_images(context.tasks)
            summary = _preflight_summary(
                context,
                preflight_replicate_campaign(context),
                verified_image_count=len(verified_images),
            )
        else:
            verify_pylint_verifier_images(context.tasks)
            summary = _run_summary(
                context,
                run_next_replicate_campaign_cell(context),
            )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-output-dir", type=Path, required=True)
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--target-repo", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--supplemental-dataset", type=Path)
    parser.add_argument("--harness-python", type=Path)
    parser.add_argument("--agents", type=Path)
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--result-store", type=Path)
    parser.add_argument("--ledger", type=Path)
    actions = parser.add_subparsers(dest="action", required=True)
    authorize = actions.add_parser(
        "authorize",
        help="create one immutable campaign authority ledger",
    )
    authorize.add_argument("--approved-at", required=True)
    authorize.add_argument("--scope", required=True)
    authorize.add_argument(
        "--maximum-estimated-cost-usd",
        type=float,
        required=True,
    )
    authorize.add_argument(
        "--maximum-estimated-cost-per-call-usd",
        type=float,
        required=True,
    )
    authorize.add_argument("--pricing-version", required=True)
    authorize.add_argument("--cost-rate", action="append", required=True)
    authorize.add_argument("--pricing-source", action="append", required=True)
    authorize.add_argument("--accounting-basis", required=True)
    actions.add_parser(
        "preflight",
        help="replay authority and every remaining binding without an Agent call",
    )
    actions.add_parser(
        "run-next",
        help="execute at most the first exact missing scheduled cell",
    )
    return parser.parse_args(argv)


def _campaign_paths(args: argparse.Namespace) -> CampaignCliPaths:
    pilot_output_dir = args.pilot_output_dir.resolve()
    campaign_dir = args.campaign_dir.resolve()
    records_dir = campaign_dir / "records"
    paths = CampaignCliPaths(
        pilot=PilotPaths(
            output_dir=pilot_output_dir,
            target_repo=(
                args.target_repo or pilot_output_dir / "target-repo"
            ).resolve(),
            dataset=(
                args.dataset or pilot_output_dir / "source" / DEFAULT_DATASET_NAME
            ).resolve(),
            supplemental_dataset=(
                args.supplemental_dataset
                or pilot_output_dir / "source" / DEFAULT_SUPPLEMENTAL_DATASET_NAME
            ).resolve(),
            harness_python=(
                args.harness_python or pilot_output_dir / "harness-env/bin/python"
            ).absolute(),
        ),
        campaign_dir=campaign_dir,
        agents_path=(args.agents or records_dir / "agents.jsonl").resolve(),
        runtime_config_path=(
            args.runtime_config or records_dir / "runtime-config.jsonl"
        ).resolve(),
        schedule_path=(
            args.schedule or records_dir / "replicate-schedule.jsonl"
        ).resolve(),
        result_store_path=(
            args.result_store or records_dir / "results.jsonl"
        ).resolve(),
        ledger_path=(args.ledger or campaign_dir / "campaign-ledger.json").resolve(),
    )
    for label, path in (
        ("agents", paths.agents_path),
        ("runtime config", paths.runtime_config_path),
        ("schedule", paths.schedule_path),
        ("Result Store", paths.result_store_path),
        ("campaign ledger", paths.ledger_path),
    ):
        if not path.is_relative_to(campaign_dir):
            raise ValueError(f"{label} path must stay under campaign-dir")
    return paths


def _agent_command(campaign_dir: Path, agent: AgentRecord) -> tuple[str, ...]:
    effort = _reasoning_effort(agent)
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


def _reasoning_effort(agent: AgentRecord) -> str:
    for effort in ("low", "high"):
        if agent.agent_id.endswith(f"-{effort}"):
            return effort
    raise ValueError("Pylint replicate Agent IDs must end in '-low' or '-high'")


def _cost_rates(values: Sequence[str]) -> Mapping[str, float]:
    rates: dict[str, float] = {}
    for value in values:
        key, separator, raw_rate = value.partition("=")
        if not separator or not key or not raw_rate:
            raise ValueError("cost rates must use NAME=USD_PER_UNIT")
        if key in rates:
            raise ValueError(f"duplicate cost rate: {key}")
        try:
            rates[key] = float(raw_rate)
        except ValueError as exc:
            raise ValueError(f"invalid cost rate for {key}") from exc
    return rates


def _scoring_config_from_ledger(path: Path) -> ScoringConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ledger = _mapping(payload, "campaign ledger")
    pricing = _mapping(ledger.get("pricing"), "campaign pricing")
    pricing_version = pricing.get("pricing_version")
    if not isinstance(pricing_version, str) or not pricing_version:
        raise ValueError("campaign pricing_version must be a nonempty string")
    return ScoringConfig(
        pricing_version=pricing_version,
        cost_rates=cast(
            Mapping[str, float],
            _mapping(pricing.get("cost_rates"), "campaign cost rates"),
        ),
    )


def _preflight_summary(
    context: ReplicateCampaignContext,
    next_cell: ResolvedReplicateScheduleCell | None,
    *,
    verified_image_count: int,
) -> Mapping[str, object]:
    if next_cell is None:
        return {
            "stage": "campaign_complete",
            "campaign_id": context.schedule.campaign_id,
            "verified_image_count": verified_image_count,
            "next": None,
        }
    cell = next_cell.schedule_cell
    return {
        "stage": "preflight_passed",
        "campaign_id": context.schedule.campaign_id,
        "verified_image_count": verified_image_count,
        "next_cell": {
            "sequence_index": cell.sequence_index,
            "task_id": cell.task_id,
            "check_id": cell.check_id,
            "agent_id": cell.agent_id,
            "replicate_index": cell.replicate_index,
            "runtime_config_id": cell.runtime_config_id,
        },
        "next": "run-next",
    }


def _run_summary(
    context: ReplicateCampaignContext,
    result: ResultRecord | None,
) -> Mapping[str, object]:
    if result is None:
        return {
            "stage": "campaign_complete",
            "campaign_id": context.schedule.campaign_id,
            "next": None,
        }
    return {
        "stage": "cell_recorded",
        "campaign_id": context.schedule.campaign_id,
        "result_id": result.result_id,
        "task_id": result.task_id,
        "check_id": result.check_id,
        "agent_id": result.agent_id,
        "terminal_status": result.terminal_status,
        "scoreable_state": result.scoreable_state,
        "outcome": result.outcome,
        "estimated_cost_usd": result.cost.get("total_cost"),
        "next": "preflight",
    }


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
