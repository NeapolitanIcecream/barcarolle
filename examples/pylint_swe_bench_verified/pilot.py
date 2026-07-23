#!/usr/bin/env python3
"""Run the fixed SWE-bench Pylint pilot one paid cell at a time."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    CheckRecord,
    ResultCellRef,
    ResultRecord,
    RuntimeConfig,
    SourceEventRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    load_jsonl_records,
    make_source_event_id,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultCacheConfig,
    ResultQuery,
    ResultStore,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    find_missing_results,
    load_results,
    store_result,
)
from barcarolle.task_pool import (  # noqa: E402
    CertificationConfig,
    CertificationResult,
    TaskCandidate,
    build_check_candidate,
    candidate_batch,
    certification_evidence_records,
    certify_task_candidate,
    finalize_source_event_records,
    freeze_task_pool,
)
from barcarolle.workspace import (  # noqa: E402
    CapturedDiff,
    WorkspaceArtifactConfig,
    WorkspaceRunContext,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    harness_content_digest,
    make_openai_env_network_policy_digest,
    preflight_run_bindings,
    resolve_openai_endpoint_digest,
    run_agent_on_task_with_artifacts,
)
from barcarolle.verification import hidden_material_digest  # noqa: E402
from examples.experiment_ledger import (  # noqa: E402
    append_ledger_event as _append_ledger_event,
    ledger_events_path as _ledger_events_path,
    load_ledger_events as _load_ledger_events,
    load_resource_ledger,
    rebuild_ledger_snapshot as _rebuild_resource_ledger_snapshot,
    write_json as _write_json,
)
from examples.pylint_swe_bench_verified.dependency_evidence import (  # noqa: E402
    DEPENDENCY_PROTOCOL_VERSION,
    PylintDependencyEvidence,
    build_dependency_evidence,
    validate_dependency_evidence_against_patches,
    validate_source_event_clusters,
)


HERE = Path(__file__).resolve().parent
HARNESS = (HERE.parent / "harnesses/codex-cli/run-agent.zsh").resolve()
EXTRACT_SOURCE = (HERE / "extract_source.py").resolve()
CHECK = (HERE / "check.py").resolve()
TASK_SOURCES = (HERE / "task_sources.json").resolve()
DEFAULT_OUTPUT_DIR = Path(
    "outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot-default-retries"
)
DEFAULT_DATASET_NAME = "swe-bench-verified-test-91aa3ed.parquet"
DEFAULT_SUPPLEMENTAL_DATASET_NAME = "swe-bench-lite-test-6ec7bb8.parquet"
MODEL = "gpt-5.4-mini"
MODEL_RESOLUTION_SCOPE_ID = "pylint-reasoning-pilot-default-retries-2026-07"
MODEL_RESOLUTION_SCOPE_STARTED_AT = "2026-07-17T00:00:00Z"
MODEL_RESOLUTION_SCOPE_ENDED_AT = "2026-08-01T00:00:00Z"
REASONING_EFFORTS = ("low", "high")
MAXIMUM_PAID_CALLS = 20
MAXIMUM_ESTIMATED_COST_USD = 30.0
TASK_COUNT = 10
AGENT_TIMEOUT_SECONDS = 900
CHECK_TIMEOUT_SECONDS = 900
PRICING_VERSION = "openai-standard-api-gpt-5.4-mini-2026-07-17"
OFFICIAL_PRICING_SOURCE = "https://developers.openai.com/api/docs/pricing#text-tokens"
OFFICIAL_RATES = {
    "uncached_input_tokens": 0.75 / 1_000_000,
    "cached_input_tokens": 0.075 / 1_000_000,
    "output_tokens": 4.50 / 1_000_000,
}
SCORING_CONFIG = ScoringConfig(PRICING_VERSION, OFFICIAL_RATES)
CACHE_CONFIG = ResultCacheConfig(reuse_benchmark_invalid=True)
REPOSITORY_ID = "pylint-dev/pylint"
DEPENDENCY_EVIDENCE_REF = "records/dependency-evidence.jsonl"


@dataclass(frozen=True)
class PilotPaths:
    output_dir: Path
    target_repo: Path
    dataset: Path
    supplemental_dataset: Path
    harness_python: Path


@dataclass(frozen=True)
class PilotContext:
    paths: PilotPaths
    records_dir: Path
    ledger_path: Path
    task_pool: TaskPoolRecord
    tasks: tuple[TaskRecord, ...]
    checks: Mapping[str, CheckRecord]
    agents: tuple[AgentRecord, ...]
    commands: Mapping[str, tuple[str, ...]]
    workspace_config: WorkspaceConfig
    runtime_config: RuntimeConfig
    result_store: ResultStore
    instance_by_task_id: Mapping[str, str]
    difficulty_by_task_id: Mapping[str, str]
    run_context: WorkspaceRunContext


def prepare(paths: PilotPaths) -> Mapping[str, object]:
    _require_prepare_may_replace(paths.output_dir)
    _require_file_digest(paths.dataset, _source_config()["dataset"]["parquet_sha256"])
    _require_file_digest(
        paths.supplemental_dataset,
        _source_config()["supplemental_dataset"]["parquet_sha256"],
    )
    _require_executable(paths.harness_python)
    _require_harness_revision(paths.harness_python)
    _require_git_repository(paths.target_repo)
    records_dir = paths.output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    for path in records_dir.glob("*.jsonl"):
        path.unlink()
    for path in (
        paths.output_dir / "preflight-summary.json",
        paths.output_dir / "pilot-summary.json",
        paths.output_dir / "resource-ledger-events.jsonl",
    ):
        path.unlink(missing_ok=True)

    _extract_source(paths)
    extracted = _extracted_tasks(paths.output_dir)
    configured = _task_source_by_instance()
    _require_source_alignment(extracted, configured)
    _require_repository_commits(paths.target_repo, extracted)
    _require_no_repository_instructions(paths.target_repo, extracted)

    workspace_config = _workspace_config(extracted, configured)
    runtime_config = _runtime_config()
    run_context = bind_repository_source(
        WorkspaceRunContext(), workspace_config, paths.target_repo
    )
    reference_patches_by_source_event = _dependency_reference_patches(
        paths,
        extracted,
        configured,
    )
    dependency_evidence = build_dependency_evidence(
        REPOSITORY_ID,
        reference_patches_by_source_event,
    )
    candidates: list[TaskCandidate] = []
    reference_patches: list[CapturedDiff] = []
    for source in extracted:
        instance_id = _required_string(source, "instance_id")
        source_event_id = _source_event_id(configured[instance_id])
        candidate = _candidate(
            paths,
            source,
            configured[instance_id],
            dependency_cluster_id=dependency_evidence.cluster_by_source_event_id[
                source_event_id
            ],
        )
        candidates.append(candidate)
        run_context = _bind_check(
            run_context,
            paths,
            build_check_candidate(candidate),
            configured[instance_id],
        )
        reference_patches.append(reference_patches_by_source_event[source_event_id])

    certification_config = CertificationConfig(repeat_count=1)
    certified: list[CertificationResult] = []
    for candidate, reference_patch in zip(candidates, reference_patches, strict=True):
        started_ns = time.time_ns()
        result = certify_task_candidate(
            candidate,
            certification_config,
            workspace_config,
            runtime_config,
            reference_patch,
            run_context,
        )
        if result.accepted:
            instance_id = candidate.candidate_id.removeprefix("candidate-")
            result = _with_swe_bench_counts(
                result,
                paths.output_dir / "raw/checks" / instance_id,
                started_ns,
                _extracted_by_instance(extracted)[instance_id],
            )
        certified.append(result)

    write_jsonl_records(
        records_dir / "certification-evidence.jsonl",
        certification_evidence_records(certified),
    )
    rejected = tuple(result for result in certified if not result.accepted)
    if rejected:
        failures = "; ".join(
            f"{result.candidate_id}: {', '.join(result.rejection_reasons)}"
            for result in rejected
        )
        raise RuntimeError(f"Pylint Task certification failed: {failures}")
    tasks = tuple(result.task for result in certified if result.task is not None)
    checks = tuple(result.check for result in certified if result.check is not None)
    source_events = finalize_source_event_records(
        candidate_batch(candidates),
        certified,
    )
    cluster_validation = validate_source_event_clusters(
        dependency_evidence,
        source_events,
    )
    if not cluster_validation.ok:
        raise RuntimeError(
            "Pylint dependency evidence does not match SourceEvents: "
            + "; ".join(cluster_validation.errors)
        )
    task_pool = freeze_task_pool(
        tasks,
        checks,
        certified,
        source_events,
        {
            "repository_id": REPOSITORY_ID,
            "task_records_ref": "records/tasks.jsonl",
            "check_records_ref": "records/checks.jsonl",
            "certification_evidence_ref": "records/certification-evidence.jsonl",
            "source_event_records_ref": "records/source-events.jsonl",
            "generator_config_digest": _generator_config_digest(dependency_evidence),
            "certification_config_digest": canonical_digest(certification_config),
            "created_at": "2026-07-17T00:00:00Z",
        },
    )
    write_jsonl_records(records_dir / "tasks.jsonl", tasks)
    write_jsonl_records(records_dir / "checks.jsonl", checks)
    write_jsonl_records(records_dir / "source-events.jsonl", source_events)
    write_jsonl_records(
        paths.output_dir / DEPENDENCY_EVIDENCE_REF,
        (dependency_evidence,),
    )
    write_jsonl_records(records_dir / "task_pool.jsonl", (task_pool,))
    _write_json(
        records_dir / "task-index.json",
        {
            "tasks": tuple(
                {
                    "instance_id": instance_id,
                    "task_id": task.task_id,
                    "check_id": task.check_ids[0],
                    "dependency_cluster_id": dependency_evidence.cluster_by_source_event_id[
                        _source_event_id(configured[instance_id])
                    ],
                    "difficulty": _required_string(
                        _extracted_by_instance(extracted)[instance_id], "difficulty"
                    ),
                }
                for instance_id, task in zip(configured, tasks, strict=True)
            )
        },
    )
    _write_json(paths.output_dir / "resource-ledger.json", _new_ledger())
    summary = {
        "stage": "prepared",
        "task_pool_id": task_pool.task_pool_id,
        "task_count": len(tasks),
        "certified_base_fail_count": sum(
            result.evidence["base_check"][0]["outcome"] == "fail"
            for result in certified
        ),
        "certified_reference_pass_count": sum(
            result.evidence["reference_patch_check"][0]["outcome"] == "pass"
            for result in certified
        ),
        "paid_call_count": 0,
        "next": "--preflight",
    }
    _write_json(paths.output_dir / "prepare-summary.json", summary)
    return summary


def build_context(paths: PilotPaths, ledger_path: Path | None = None) -> PilotContext:
    _require_harness_revision(paths.harness_python)
    records_dir = paths.output_dir / "records"
    (task_pool,) = load_jsonl_records(records_dir / "task_pool.jsonl", TaskPoolRecord)
    tasks = tuple(load_jsonl_records(records_dir / "tasks.jsonl", TaskRecord))
    checks_tuple = tuple(load_jsonl_records(records_dir / "checks.jsonl", CheckRecord))
    source_events = tuple(
        load_jsonl_records(records_dir / "source-events.jsonl", SourceEventRecord)
    )
    (dependency_evidence,) = load_jsonl_records(
        paths.output_dir / DEPENDENCY_EVIDENCE_REF,
        PylintDependencyEvidence,
    )
    if canonical_digest(tasks) != task_pool.task_records_digest:
        raise RuntimeError("Task records do not match the prepared Task Pool")
    if canonical_digest(checks_tuple) != task_pool.check_records_digest:
        raise RuntimeError("Check records do not match the prepared Task Pool")
    if canonical_digest(source_events) != task_pool.source_event_records_digest:
        raise RuntimeError("SourceEvent records do not match the prepared Task Pool")
    index = _load_object(records_dir / "task-index.json")
    index_rows = index.get("tasks")
    if not isinstance(index_rows, list):
        raise RuntimeError("prepared task index is invalid")
    instance_by_task_id = {
        _required_string(row, "task_id"): _required_string(row, "instance_id")
        for row in index_rows
    }
    difficulty_by_task_id = {
        _required_string(row, "task_id"): _required_string(row, "difficulty")
        for row in index_rows
    }
    if set(instance_by_task_id) != {task.task_id for task in tasks}:
        raise RuntimeError("prepared task index does not match Task records")

    configured = _task_source_by_instance()
    extracted = _extracted_tasks(paths.output_dir)
    dependency_validation = validate_dependency_evidence_against_patches(
        dependency_evidence,
        _dependency_reference_patches(paths, extracted, configured),
    )
    if not dependency_validation.ok:
        raise RuntimeError(
            "Pylint dependency evidence does not replay from reference patches: "
            + "; ".join(dependency_validation.errors)
        )
    cluster_validation = validate_source_event_clusters(
        dependency_evidence,
        source_events,
    )
    if not cluster_validation.ok:
        raise RuntimeError(
            "Pylint dependency evidence does not match SourceEvents: "
            + "; ".join(cluster_validation.errors)
        )
    if task_pool.generator_config_digest != _generator_config_digest(
        dependency_evidence
    ):
        raise RuntimeError(
            "Pylint dependency evidence does not match the prepared Task Pool"
        )
    workspace_config = _workspace_config(extracted, configured)
    runtime_config = _runtime_config()
    agents, commands = _agents(
        paths.output_dir,
        tasks,
        cli_version=_codex_cli_version(),
        endpoint_digest=resolve_openai_endpoint_digest(),
    )
    context = PilotContext(
        paths=paths,
        records_dir=records_dir,
        ledger_path=(
            ledger_path or paths.output_dir / "resource-ledger.json"
        ).resolve(),
        task_pool=task_pool,
        tasks=tasks,
        checks={check.check_id: check for check in checks_tuple},
        agents=agents,
        commands=commands,
        workspace_config=workspace_config,
        runtime_config=runtime_config,
        result_store=ResultStore(records_dir / "results.jsonl"),
        instance_by_task_id=instance_by_task_id,
        difficulty_by_task_id=difficulty_by_task_id,
        run_context=WorkspaceRunContext(),
    )
    return replace(context, run_context=_bind_context(context, configured))


def preflight(context: PilotContext) -> Mapping[str, object]:
    ledger = _reconcile_ledger(context)
    calls = ledger["calls"]
    if not isinstance(calls, list):
        raise RuntimeError("resource ledger calls are invalid")
    preflight_run_bindings(
        context.run_context,
        tuple(
            (task, context.checks[check_id], agent)
            for task in context.tasks
            for check_id in task.check_ids
            for agent in context.agents
        ),
        context.workspace_config,
        context.runtime_config,
    )
    if len(context.tasks) != TASK_COUNT or len(context.agents) != 2:
        raise RuntimeError("preflight requires the fixed 10 Task x 2 Agent matrix")
    images = verify_pylint_verifier_images(context.tasks)
    summary = {
        "stage": "preflight_passed",
        "task_pool_id": context.task_pool.task_pool_id,
        "workspace_config_digest": canonical_digest(context.workspace_config),
        "agent_manifest_digests": tuple(
            agent.agent_manifest_digest for agent in context.agents
        ),
        "verified_images": images,
        "planned_paid_calls": TASK_COUNT * len(context.agents),
        "maximum_paid_calls": MAXIMUM_PAID_CALLS,
        "maximum_estimated_cost_usd": MAXIMUM_ESTIMATED_COST_USD,
        "paid_call_count": len(calls),
        "next": "--canary",
    }
    _write_json(context.paths.output_dir / "preflight-summary.json", summary)
    return summary


def verify_pylint_verifier_images(
    tasks: Sequence[TaskRecord],
) -> tuple[Mapping[str, str], ...]:
    """Verify every pinned Pylint verifier image without running an Agent."""
    configured_by_source_ref = {
        _required_string(config, "issue_url"): config
        for config in _task_source_by_instance().values()
    }
    images: list[Mapping[str, str]] = []
    for task in tasks:
        config = configured_by_source_ref.get(task.source_ref)
        if config is None:
            raise RuntimeError(f"Pylint Task source is not configured: {task.task_id}")
        instance_id = _required_string(config, "instance_id")
        image_ref = _image_ref(instance_id, config)
        inspected = subprocess.run(
            ("docker", "image", "inspect", image_ref),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if inspected.returncode != 0:
            raise RuntimeError(f"pinned verifier image is unavailable: {instance_id}")
        payload = json.loads(inspected.stdout)
        if not isinstance(payload, list) or len(payload) != 1:
            raise RuntimeError(f"could not inspect pinned image: {instance_id}")
        image = payload[0]
        repo_digests = image.get("RepoDigests") if isinstance(image, Mapping) else None
        architecture = image.get("Architecture") if isinstance(image, Mapping) else None
        if not isinstance(repo_digests, list) or image_ref not in repo_digests:
            raise RuntimeError(f"verifier image digest mismatch: {instance_id}")
        if architecture != "arm64":
            raise RuntimeError(f"verifier image is not arm64: {instance_id}")
        observed = subprocess.run(
            (
                "docker",
                "run",
                "--rm",
                "--platform",
                "linux/arm64",
                "--workdir",
                "/testbed",
                "--entrypoint",
                "git",
                image_ref,
                "rev-parse",
                "HEAD",
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        if observed.returncode != 0 or observed.stdout.strip() != task.base_commit:
            raise RuntimeError(f"verifier image base commit mismatch: {instance_id}")
        images.append(
            {
                "instance_id": instance_id,
                "image_ref": image_ref,
                "base_commit": task.base_commit,
            }
        )
    return tuple(images)


def run_next_cell(context: PilotContext, *, canary: bool) -> Mapping[str, object]:
    ledger = _reconcile_ledger(context)
    _require_current_preflight(context)
    if canary and ledger["calls"]:
        raise RuntimeError("the canary cell has already been attempted")
    missing = tuple(
        find_missing_results(
            _all_refs(context),
            context.tasks,
            context.checks,
            context.agents,
            context.workspace_config,
            context.runtime_config,
            context.result_store,
            CACHE_CONFIG,
        )
    )
    if not missing:
        return {
            "stage": "paid_cells_complete",
            "paid_call_count": _paid_result_count(context),
            "next": "--summarize",
        }
    result = _execute_cell(context, missing[0])
    return {
        "stage": "cell_recorded",
        "instance_id": context.instance_by_task_id[result.task_id],
        "agent_id": result.agent_id,
        "reasoning_effort": _agent_effort(
            next(agent for agent in context.agents if agent.agent_id == result.agent_id)
        ),
        "terminal_status": result.terminal_status,
        "scoreable_state": result.scoreable_state,
        "outcome": result.outcome,
        "usage": _priced_usage(result.usage),
        "estimated_cost_usd": result.cost["total_cost"],
        "paid_call_count": _paid_result_count(context),
        "next": "--next-cell",
    }


def summarize(context: PilotContext) -> Mapping[str, object]:
    ledger = _reconcile_ledger(context)
    calls = ledger["calls"]
    if not isinstance(calls, list):
        raise RuntimeError("resource ledger calls are invalid")
    results = _paid_results(context)
    _ensure_unique_paid_execution_identities(results)
    effort_by_agent = {agent.agent_id: _agent_effort(agent) for agent in context.agents}
    result_by_cell = {
        (result.task_id, effort_by_agent[result.agent_id]): result for result in results
    }
    paired = _paired_pilot_summary(context, result_by_cell)
    usage = {
        key: sum(_priced_usage(result.usage)[key] for result in results)
        for key in OFFICIAL_RATES
    }
    summary = {
        "schema_version": 1,
        "stage": _pilot_summary_stage(results, calls),
        "task_pool_id": context.task_pool.task_pool_id,
        "task_count": len(context.tasks),
        "planned_paid_calls": MAXIMUM_PAID_CALLS,
        "paid_result_count": len(results),
        "ledger_call_count": len(calls),
        "scoreable_result_count": sum(
            result.scoreable_state == "scoreable" for result in results
        ),
        "per_reasoning_effort": _reasoning_effort_rows(results, effort_by_agent),
        "paired": paired,
        "usage": usage,
        "estimated_cost_usd": sum(
            float(result.cost["total_cost"]) for result in results
        ),
        "maximum_estimated_cost_usd": MAXIMUM_ESTIMATED_COST_USD,
        "pricing_version": PRICING_VERSION,
        "pricing_source": OFFICIAL_PRICING_SOURCE,
        "workspace_seconds": sum(
            float(result.latency["workspace_seconds"]) for result in results
        ),
        "result_time_span_seconds": _result_time_span(results),
        "scope": (
            "Ten fixed real Pylint tasks compare low and high reasoning effort. "
            "This pilot measures execution and outcome heterogeneity; it does not "
            "by itself estimate selector MAE."
        ),
    }
    _write_json(context.paths.output_dir / "pilot-summary.json", summary)
    return summary


def _ensure_unique_paid_execution_identities(
    results: Sequence[ResultRecord],
) -> None:
    execution_keys = tuple(
        (
            result.agent_id,
            result.task_id,
            result.check_id,
            result.cache_identity.identity_digest,
        )
        for result in results
    )
    if len(execution_keys) != len(set(execution_keys)):
        raise RuntimeError("Result Store contains duplicate paid execution identities")


def _reasoning_effort_rows(
    results: Sequence[ResultRecord],
    effort_by_agent: Mapping[str, str],
) -> tuple[Mapping[str, object], ...]:
    per_effort: list[Mapping[str, object]] = []
    for effort in REASONING_EFFORTS:
        effort_results = tuple(
            result for result in results if effort_by_agent[result.agent_id] == effort
        )
        scoreable = tuple(
            result for result in effort_results if result.scoreable_state == "scoreable"
        )
        passed = sum(result.outcome == "pass" for result in scoreable)
        per_effort.append(
            {
                "reasoning_effort": effort,
                "result_count": len(effort_results),
                "scoreable_count": len(scoreable),
                "pass_count": passed,
                "pass_rate": passed / len(scoreable) if scoreable else None,
                "estimated_cost_usd": sum(
                    float(result.cost["total_cost"]) for result in effort_results
                ),
                "workspace_seconds": sum(
                    float(result.latency["workspace_seconds"])
                    for result in effort_results
                ),
            }
        )
    return tuple(per_effort)


def _paired_pilot_summary(
    context: PilotContext,
    result_by_cell: Mapping[tuple[str, str], ResultRecord],
) -> Mapping[str, object]:
    pairs: list[Mapping[str, object]] = []
    disagreement_count = 0
    complete_pair_count = 0
    for task in context.tasks:
        low = result_by_cell.get((task.task_id, "low"))
        high = result_by_cell.get((task.task_id, "high"))
        if low is None or high is None:
            complete = False
            disagreement = False
        else:
            complete = (
                low.scoreable_state == "scoreable"
                and high.scoreable_state == "scoreable"
            )
            disagreement = complete and low.outcome != high.outcome
        complete_pair_count += int(complete)
        disagreement_count += int(disagreement)
        pairs.append(
            {
                "instance_id": context.instance_by_task_id[task.task_id],
                "difficulty": context.difficulty_by_task_id[task.task_id],
                "low_outcome": low.outcome if low is not None else None,
                "high_outcome": high.outcome if high is not None else None,
                "complete_scoreable_pair": complete,
                "disagreement": disagreement,
            }
        )
    return {
        "complete_scoreable_pair_count": complete_pair_count,
        "disagreement_count": disagreement_count,
        "rows": tuple(pairs),
    }


def _pilot_summary_stage(
    results: Sequence[ResultRecord],
    calls: Sequence[object],
) -> str:
    complete_ledger = len(calls) == MAXIMUM_PAID_CALLS and all(
        isinstance(call, Mapping) and call.get("state") == "completed" for call in calls
    )
    if len(results) == MAXIMUM_PAID_CALLS and complete_ledger:
        return "complete"
    return "incomplete"


def _execute_cell(context: PilotContext, cell: ResultCellRef):
    task = next(task for task in context.tasks if task.task_id == cell.task_id)
    check = context.checks[cell.check_id]
    agent = next(agent for agent in context.agents if agent.agent_id == cell.agent_id)
    _assert_command_identity(agent, context.commands[agent.agent_id])
    preflight_run_bindings(
        context.run_context,
        ((task, check, agent),),
        context.workspace_config,
        context.runtime_config,
    )
    ledger = _reconcile_ledger(context)
    _ensure_ledger_allows_call(ledger, context, task, check, agent)
    call_id = _start_ledger_call(context, ledger, task, check, agent)
    result = None
    usage = None
    artifact_manifest_ref = None
    try:
        current_missing = find_missing_results(
            (TaskCheckRef(task.task_id, check.check_id),),
            context.tasks,
            context.checks,
            (agent,),
            context.workspace_config,
            context.runtime_config,
            context.result_store,
            CACHE_CONFIG,
        )
        if len(current_missing) != 1:
            raise RuntimeError("cell is no longer missing at execution boundary")
        identity = compute_result_cache_identity(
            task,
            check,
            agent,
            context.workspace_config,
            context.runtime_config,
        )
        if identity.identity_digest != cell.required_identity_digest:
            raise RuntimeError("cell identity changed before execution")
        workspace_result = run_agent_on_task_with_artifacts(
            task,
            check,
            agent,
            context.workspace_config,
            context.runtime_config,
            context.run_context,
            WorkspaceArtifactConfig(
                output_root=context.paths.output_dir / "raw/agent-runs",
                preserve_solver_workspace_summary="on_failure",
                preserve_verifier_workspace_summary="on_failure",
            ),
        )
        if workspace_result.artifacts is not None:
            artifact_manifest_ref = workspace_result.artifacts.manifest_ref
        _require_paid_check_summary(context, task, workspace_result.run)
        result = build_result_record(
            task,
            check,
            agent,
            workspace_result.run,
            identity,
            SCORING_CONFIG,
        )
        result = store_result(result, context.result_store)
        _fsync_file(context.result_store.path)
        usage = _priced_usage(result.usage)
        cost = result.cost.get("total_cost")
        if isinstance(cost, bool) or not isinstance(cost, int | float):
            raise RuntimeError("measured usage could not be priced")
        spent = ledger.get("spent_usd")
        if isinstance(spent, bool) or not isinstance(spent, int | float):
            raise RuntimeError("resource ledger spent_usd is invalid")
        if float(spent) + float(cost) > MAXIMUM_ESTIMATED_COST_USD:
            raise RuntimeError("paid cell exceeds the authorized estimated-cost cap")
        if result.scoreable_state != "scoreable":
            raise RuntimeError("paid Result is not scoreable; expansion is stopped")
    except BaseException as exc:
        _finish_ledger_call(
            context.ledger_path,
            call_id,
            state="stopped",
            result=result,
            usage=usage,
            artifact_manifest_ref=artifact_manifest_ref,
            error=type(exc).__name__,
        )
        raise
    _finish_ledger_call(
        context.ledger_path,
        call_id,
        state="completed",
        result=result,
        usage=usage,
        artifact_manifest_ref=artifact_manifest_ref,
    )
    return result


def _require_paid_check_summary(
    context: PilotContext, task: TaskRecord, workspace_run: WorkspaceRunRecord
) -> None:
    """Reject verifier infrastructure failures before they become paid Results."""
    instance_id = context.instance_by_task_id[task.task_id]
    path = (
        context.paths.output_dir
        / "raw/checks"
        / instance_id
        / workspace_run.diff_digest
        / "summary.json"
    )
    if not path.is_file():
        raise RuntimeError("paid SWE-bench check produced no scored summary")
    summary_written_at = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    if summary_written_at < _parse_time(workspace_run.started_at):
        raise RuntimeError("paid SWE-bench check summary is stale")
    summary = _load_object(path)
    if summary.get("state") != "scored":
        raise RuntimeError("paid SWE-bench check did not reach a scored state")
    if summary.get("instance_id") != instance_id:
        raise RuntimeError("paid SWE-bench summary has the wrong instance")
    if summary.get("patch_digest") != workspace_run.diff_digest:
        raise RuntimeError("paid SWE-bench summary has the wrong diff digest")
    expected_outcome = "pass" if summary.get("resolved") is True else "fail"
    if workspace_run.check_outcome != expected_outcome:
        raise RuntimeError(
            "paid SWE-bench exit status disagrees with its scored summary"
        )


def _candidate(
    paths: PilotPaths,
    source: Mapping[str, Any],
    configured: Mapping[str, Any],
    *,
    dependency_cluster_id: str,
) -> TaskCandidate:
    instance_id = _required_string(source, "instance_id")
    source_family = _source_family(configured)
    return TaskCandidate(
        candidate_id=f"candidate-{instance_id}",
        repository_id=REPOSITORY_ID,
        base_commit=_required_string(source, "base_commit"),
        source_family=source_family,
        source_ref=_required_string(configured, "issue_url"),
        source_resolved_at=_required_string(configured, "task_material_available_at"),
        task_material_available_at=_required_string(
            configured, "task_material_available_at"
        ),
        check_material_available_at=_required_string(
            configured, "check_material_available_at"
        ),
        task_text=_required_string(source, "problem_statement"),
        solver_material_refs=(),
        dependency_cluster_id=dependency_cluster_id,
        sampling_stratum=_required_string(source, "difficulty"),
        check_manifest_digest=canonical_digest(_check_manifest(configured)),
        hidden_check_bundle_digest=hidden_material_digest(
            _hidden_check_dir(paths, instance_id)
        ),
        resource_limits={"timeout_seconds": CHECK_TIMEOUT_SECONDS},
        oracle_source="swe_bench_test_patch",
        check_type="swe_bench",
    )


def _with_swe_bench_counts(
    result: CertificationResult,
    raw_instance_dir: Path,
    started_ns: int,
    source: Mapping[str, Any],
) -> CertificationResult:
    summaries: list[Mapping[str, Any]] = []
    for path in raw_instance_dir.glob("*/summary.json"):
        if path.stat().st_mtime_ns < started_ns:
            continue
        summary = _load_object(path)
        if summary.get("state") == "scored":
            summaries.append(summary)
    base = tuple(summary for summary in summaries if summary.get("resolved") is False)
    reference = tuple(
        summary for summary in summaries if summary.get("resolved") is True
    )
    if len(base) != 1 or len(reference) != 1:
        raise RuntimeError(
            "certification did not produce one base and one reference summary"
        )
    fail_to_pass = int(source["fail_to_pass_count"])
    pass_to_pass = int(source["pass_to_pass_count"])
    _require_test_counts(base[0], fail_to_pass, pass_to_pass, reference=False)
    _require_test_counts(reference[0], fail_to_pass, pass_to_pass, reference=True)
    evidence = {
        **result.evidence,
        "swe_bench_status": {
            "base_check": _safe_check_summary(base[0]),
            "reference_patch_check": _safe_check_summary(reference[0]),
        },
    }
    return CertificationResult(
        candidate_id=result.candidate_id,
        accepted=result.accepted,
        task=result.task,
        check=result.check,
        rejection_reasons=result.rejection_reasons,
        evidence=evidence,
        evidence_digest=canonical_digest(evidence),
    )


def _require_test_counts(
    summary: Mapping[str, Any],
    fail_to_pass: int,
    pass_to_pass: int,
    *,
    reference: bool,
) -> None:
    tests = summary.get("tests")
    if not isinstance(tests, Mapping):
        raise RuntimeError("SWE-bench certification summary is missing test counts")
    f2p = tests.get("FAIL_TO_PASS")
    p2p = tests.get("PASS_TO_PASS")
    if not isinstance(f2p, Mapping) or not isinstance(p2p, Mapping):
        raise RuntimeError("SWE-bench certification summary has invalid test counts")
    expected = (
        (fail_to_pass, 0, pass_to_pass, 0)
        if reference
        else (0, fail_to_pass, pass_to_pass, 0)
    )
    observed = (
        f2p.get("success_count"),
        f2p.get("failure_count"),
        p2p.get("success_count"),
        p2p.get("failure_count"),
    )
    if observed != expected:
        raise RuntimeError(
            f"SWE-bench certification test counts differ: {observed} != {expected}"
        )


def _safe_check_summary(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "resolved": summary.get("resolved") is True,
        "state": summary.get("state"),
        "status_digest": summary.get("status_digest"),
        "tests": summary.get("tests"),
    }


def _workspace_config(
    extracted: Sequence[Mapping[str, Any]],
    configured: Mapping[str, Mapping[str, Any]],
) -> WorkspaceConfig:
    source_config = _source_config()
    return WorkspaceConfig(
        workspace_config_id="pylint-swe-bench-10-v2",
        repository_checkout_config_digest=canonical_digest(
            {
                "repository": "pylint-dev/pylint",
                "base_commits": tuple(
                    _required_string(source, "base_commit") for source in extracted
                ),
            }
        ),
        submodule_state_digest="submodules-none",
        base_image_digest=canonical_digest(
            tuple(
                (
                    instance_id,
                    _required_string(source, "image_digest"),
                )
                for instance_id, source in configured.items()
            )
        ),
        dependency_lock_digest=canonical_digest(
            {
                "dataset": source_config["dataset"],
                "supplemental_dataset": source_config["supplemental_dataset"],
                "swe_bench_harness": source_config["harness"],
            }
        ),
    )


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id="pylint-codex-mini-paired-900s",
        budget_digest="codex-mini-paired-900s-default-network-retries-v1",
        retry_policy_digest="codex-default-network-retries-no-cell-retry",
        stochastic_settings_digest="reasoning-effort-bound-in-agent-identity",
        timeout_seconds=AGENT_TIMEOUT_SECONDS,
        hardware_profile_digest=None,
    )


def _agents(
    output_dir: Path,
    tasks: Sequence[TaskRecord],
    *,
    cli_version: str,
    endpoint_digest: str,
) -> tuple[tuple[AgentRecord, ...], Mapping[str, tuple[str, ...]]]:
    harness_text = HARNESS.read_text(encoding="utf-8")
    if "BARCAROLLE_CODEX_REASONING_EFFORT" not in harness_text:
        raise RuntimeError("Codex harness does not bind reasoning effort")
    usage_helper = HARNESS.parent / "extract-usage.py"
    content_digest = harness_content_digest((HARNESS, usage_helper))
    repository_instruction_digest = canonical_digest(
        {
            "state": "none-at-selected-base-commits",
            "base_commits": tuple(task.base_commit for task in tasks),
        }
    )
    agents: list[AgentRecord] = []
    commands: dict[str, tuple[str, ...]] = {}
    for effort in REASONING_EFFORTS:
        command = (
            "env",
            f"BARCAROLLE_CODEX_MODEL={MODEL}",
            f"BARCAROLLE_CODEX_REASONING_EFFORT={effort}",
            f"BARCAROLLE_CODEX_HOME={(output_dir / f'codex-home-{effort}').resolve()}",
            str(HARNESS),
        )
        harness_digest = canonical_digest({"agent_command": command})
        prompt_digest = canonical_digest(
            {
                "prompt": "swe-bench-task-md-codex-v1",
                "task_file": ".barcarolle/TASK.md",
                "repository_instruction_state": "none-at-selected-base-commits",
                "repository_rules_ignored": True,
            }
        )
        provider_digest = canonical_digest(
            {
                "provider": "barcarolle_openai",
                "wire_api": "responses",
                "endpoint_digest": endpoint_digest,
                "request_max_retries": "codex-cli-default",
                "stream_max_retries": "codex-cli-default",
            }
        )
        agent_id = f"codex-{MODEL}-reasoning-{effort}"
        agent = AgentRecord(
            agent_id=agent_id,
            agent_manifest_digest=canonical_digest(
                {
                    "agent": "codex-cli",
                    "requested_model_id": MODEL,
                    "model_snapshot_id": None,
                    "model_resolution_scope_id": MODEL_RESOLUTION_SCOPE_ID,
                    "model_resolution_scope_started_at": (
                        MODEL_RESOLUTION_SCOPE_STARTED_AT
                    ),
                    "model_resolution_scope_ended_at": (
                        MODEL_RESOLUTION_SCOPE_ENDED_AT
                    ),
                    "reasoning_effort": effort,
                    "codex_cli_version": cli_version,
                    "harness_digest": harness_digest,
                    "harness_content_digest": content_digest,
                    "prompt_digest": prompt_digest,
                    "provider_digest": provider_digest,
                    "multi_agent_disabled": True,
                }
            ),
            requested_model_id=MODEL,
            model_snapshot_id=None,
            model_resolution_scope_id=MODEL_RESOLUTION_SCOPE_ID,
            model_resolution_scope_started_at=MODEL_RESOLUTION_SCOPE_STARTED_AT,
            model_resolution_scope_ended_at=MODEL_RESOLUTION_SCOPE_ENDED_AT,
            harness_digest=harness_digest,
            repository_instruction_digest=repository_instruction_digest,
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
            adapter_digest="barcarolle-worktree-diff-v2-python-cache-excluded",
        )
        agents.append(agent)
        commands[agent_id] = command
    return tuple(agents), commands


def _bind_context(
    context: PilotContext, configured: Mapping[str, Mapping[str, Any]]
) -> WorkspaceRunContext:
    run_context = bind_repository_source(
        context.run_context, context.workspace_config, context.paths.target_repo
    )
    for check in context.checks.values():
        instance_id = context.instance_by_task_id[check.task_id]
        run_context = _bind_check(
            run_context, context.paths, check, configured[instance_id]
        )
    for agent in context.agents:
        run_context = bind_agent_harness(
            run_context,
            agent,
            context.commands[agent.agent_id],
            execution_mode="openai_paid",
            endpoint_harness_paths=(HARNESS, HARNESS.parent / "extract-usage.py"),
        )
    return run_context


def _bind_check(
    run_context: WorkspaceRunContext,
    paths: PilotPaths,
    check: CheckRecord,
    task_source: Mapping[str, Any],
) -> WorkspaceRunContext:
    instance_id = _required_string(task_source, "instance_id")
    command = _check_command(paths, task_source)
    manifest = _check_manifest(task_source)
    if check.check_manifest_digest == canonical_digest(manifest):
        return bind_check_material(
            run_context,
            check,
            command,
            _hidden_check_dir(paths, instance_id),
            check_manifest=manifest,
        )
    return bind_check_material(
        run_context, check, command, _hidden_check_dir(paths, instance_id)
    )


def _check_command(
    paths: PilotPaths, task_source: Mapping[str, Any]
) -> tuple[str, ...]:
    instance_id = _required_string(task_source, "instance_id")
    harness_revision = _required_string(_source_config()["harness"], "revision")
    return (
        "env",
        f"BARCAROLLE_CHECK_IMPLEMENTATION_SHA256={_file_sha256(CHECK)}",
        f"BARCAROLLE_SWEBENCH_HARNESS_REVISION={harness_revision}",
        str(paths.harness_python),
        str(CHECK),
        "--bundle",
        ".barcarolle/check_bundle",
        "--image-ref",
        _image_ref(instance_id, task_source),
        "--raw-output-dir",
        str((paths.output_dir / "raw/checks").resolve()),
        "--timeout-seconds",
        str(CHECK_TIMEOUT_SECONDS),
    )


def _check_manifest(task_source: Mapping[str, Any]) -> Mapping[str, Any]:
    instance_id = _required_string(task_source, "instance_id")
    return {
        "check_implementation_sha256": _file_sha256(CHECK),
        "swe_bench_harness_revision": _required_string(
            _source_config()["harness"], "revision"
        ),
        "bundle_destination": ".barcarolle/check_bundle",
        "image_ref": _image_ref(instance_id, task_source),
        "timeout_seconds": CHECK_TIMEOUT_SECONDS,
    }


def _image_ref(instance_id: str, task_source: Mapping[str, Any]) -> str:
    digest = _required_string(task_source, "image_digest")
    return f"ghcr.io/epoch-research/swe-bench.eval.arm64.{instance_id}@{digest}"


def _extract_source(paths: PilotPaths) -> None:
    completed = subprocess.run(
        (
            str(paths.harness_python),
            str(EXTRACT_SOURCE),
            "--dataset",
            str(paths.dataset),
            "--supplemental-dataset",
            str(paths.supplemental_dataset),
            "--task-sources",
            str(TASK_SOURCES),
            "--output-dir",
            str(paths.output_dir),
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("pinned SWE-bench source extraction failed")


def _source_config() -> Mapping[str, Any]:
    return _load_object(TASK_SOURCES)


def _source_family(configured: Mapping[str, Any]) -> str:
    instance_id = _required_string(configured, "instance_id")
    source_family = configured.get("dataset_family", "swe_bench_verified")
    if not isinstance(source_family, str) or not source_family:
        raise RuntimeError(f"{instance_id} has no dataset family")
    return source_family


def _source_event_id(configured: Mapping[str, Any]) -> str:
    return make_source_event_id(
        REPOSITORY_ID,
        _source_family(configured),
        _required_string(configured, "issue_url"),
    )


def _task_source_by_instance() -> dict[str, Mapping[str, Any]]:
    tasks = _source_config().get("tasks")
    if not isinstance(tasks, list):
        raise RuntimeError("task_sources.json must contain a tasks list")
    by_instance = {_required_string(task, "instance_id"): task for task in tasks}
    if len(tasks) != TASK_COUNT or len(by_instance) != TASK_COUNT:
        raise RuntimeError("pilot requires exactly 10 unique configured tasks")
    return by_instance


def _extracted_tasks(output_dir: Path) -> tuple[Mapping[str, Any], ...]:
    payload = _load_object(output_dir / "extracted-source.json")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != TASK_COUNT:
        raise RuntimeError("extracted source must contain exactly 10 tasks")
    return tuple(tasks)


def _extracted_by_instance(
    tasks: Sequence[Mapping[str, Any]],
) -> Mapping[str, Mapping[str, Any]]:
    return {_required_string(task, "instance_id"): task for task in tasks}


def _require_source_alignment(
    extracted: Sequence[Mapping[str, Any]],
    configured: Mapping[str, Mapping[str, Any]],
) -> None:
    extracted_ids = tuple(_required_string(task, "instance_id") for task in extracted)
    if extracted_ids != tuple(configured):
        raise RuntimeError("dataset task order does not match fixed task_sources.json")


def _hidden_check_dir(paths: PilotPaths, instance_id: str) -> Path:
    return paths.output_dir / "hidden-checks" / instance_id


def _reference_patch(paths: PilotPaths, instance_id: str) -> CapturedDiff:
    text = (paths.output_dir / "reference-patches" / f"{instance_id}.diff").read_text(
        encoding="utf-8"
    )
    return CapturedDiff(
        diff_text=text,
        diff_digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _dependency_reference_patches(
    paths: PilotPaths,
    extracted: Sequence[Mapping[str, Any]],
    configured: Mapping[str, Mapping[str, Any]],
) -> dict[str, CapturedDiff]:
    patches: dict[str, CapturedDiff] = {}
    for source in extracted:
        instance_id = _required_string(source, "instance_id")
        source_event_id = _source_event_id(configured[instance_id])
        if source_event_id in patches:
            raise RuntimeError("configured tasks contain a duplicate SourceEvent")
        patches[source_event_id] = _reference_patch(paths, instance_id)
    return patches


def _generator_config_digest(
    dependency_evidence: PylintDependencyEvidence,
) -> str:
    return canonical_digest(
        {
            "pilot": "swe-bench-pylint-10x2-v2",
            "dataset": _source_config()["dataset"],
            "supplemental_dataset": _source_config()["supplemental_dataset"],
            "harness": _source_config()["harness"],
            "check_sha256": _file_sha256(CHECK),
            "dependency_evidence_ref": DEPENDENCY_EVIDENCE_REF,
            "dependency_protocol_version": DEPENDENCY_PROTOCOL_VERSION,
            "dependency_evidence_digest": (
                dependency_evidence.dependency_evidence_digest
            ),
        }
    )


def _all_refs(context: PilotContext) -> tuple[TaskCheckRef, ...]:
    return tuple(
        TaskCheckRef(task.task_id, task.check_ids[0]) for task in context.tasks
    )


def _require_current_preflight(context: PilotContext) -> None:
    summary = _load_object(context.paths.output_dir / "preflight-summary.json")
    if summary.get("stage") != "preflight_passed":
        raise RuntimeError("run --preflight before any paid cell")
    if summary.get("task_pool_id") != context.task_pool.task_pool_id:
        raise RuntimeError("preflight does not match the current Task Pool")
    if summary.get("workspace_config_digest") != canonical_digest(
        context.workspace_config
    ):
        raise RuntimeError("preflight does not match the current Workspace config")
    expected_agents = [agent.agent_manifest_digest for agent in context.agents]
    if summary.get("agent_manifest_digests") != expected_agents:
        raise RuntimeError("preflight does not match the current Agent identities")


def _new_ledger() -> Mapping[str, object]:
    return {
        "authorization": {
            "approved_at": "2026-07-17",
            "budget_usd": MAXIMUM_ESTIMATED_COST_USD,
            "credential_variables": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
            "scope": "fixed 10-task x low/high SWE-bench Pylint pilot",
        },
        "calls": [],
        "limits": {
            "maximum_estimated_cost_usd": MAXIMUM_ESTIMATED_COST_USD,
            "maximum_paid_calls": MAXIMUM_PAID_CALLS,
            "retry_policy": {
                "cell_retries": 0,
                "codex_request_retries": "default",
                "codex_stream_retries": "default",
            },
        },
        "pricing": {
            "accounting_basis": (
                "OpenAI standard API list prices; estimate only because the "
                "authorized gateway does not publish billing rates"
            ),
            "models": {
                MODEL: {
                    "input_usd_per_token": OFFICIAL_RATES["uncached_input_tokens"],
                    "cached_input_usd_per_token": OFFICIAL_RATES["cached_input_tokens"],
                    "output_usd_per_token": OFFICIAL_RATES["output_tokens"],
                }
            },
            "sources": [OFFICIAL_PRICING_SOURCE],
        },
        "remaining_usd": MAXIMUM_ESTIMATED_COST_USD,
        "spent_usd": 0.0,
        "stop_conditions": [
            "authorized endpoint cannot be proven",
            "usage or official-price estimate is unavailable",
            "a reserved cell has no exact Result",
            "a paid Result is not scoreable",
            "the call or estimated-cost limit is reached",
        ],
        "updated_at": _now(),
    }


def _load_ledger(path: Path) -> dict[str, object]:
    return load_resource_ledger(path, updated_at=_now())


def _rebuild_ledger_snapshot(
    path: Path,
    ledger: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return _rebuild_resource_ledger_snapshot(
        path,
        ledger,
        events,
        updated_at=_now(),
    )


def _reconcile_ledger(context: PilotContext) -> dict[str, object]:
    ledger = _load_ledger(context.ledger_path)
    calls = ledger["calls"]
    assert isinstance(calls, list)
    for call in calls:
        if not isinstance(call, dict) or call.get("state") != "started":
            continue
        result = _exact_result_for_call(context, call)
        if result is None:
            raise RuntimeError(
                "resource ledger has a reserved cell without an exact Result; "
                "automatic retry is forbidden"
            )
        try:
            usage = _priced_usage(result.usage)
            if result.cost.get("total_cost") is None:
                raise RuntimeError("measured usage could not be priced")
            if result.scoreable_state != "scoreable":
                raise RuntimeError("recovered Result is not scoreable")
        except RuntimeError as exc:
            _finish_ledger_call(
                context.ledger_path,
                str(call["call_id"]),
                state="stopped",
                result=result,
                error=type(exc).__name__,
            )
            raise
        _finish_ledger_call(
            context.ledger_path,
            str(call["call_id"]),
            state="completed",
            result=result,
            usage=usage,
            recovered=True,
        )
        ledger = _load_ledger(context.ledger_path)
    calls = ledger["calls"]
    assert isinstance(calls, list)
    if any(
        not isinstance(call, dict) or call.get("state") != "completed" for call in calls
    ):
        raise RuntimeError("resource ledger contains a stopped paid cell")
    _ensure_historical_calls_scoreable(calls)
    if _paid_result_count(context) != len(calls):
        raise RuntimeError("paid Result count and ledger call count differ")
    return ledger


def _exact_result_for_call(context: PilotContext, call: Mapping[str, object]):
    agent = next(
        (
            candidate
            for candidate in context.agents
            if candidate.agent_id == call.get("agent_id")
        ),
        None,
    )
    task = next(
        (
            candidate
            for candidate in context.tasks
            if candidate.task_id == call.get("task_id")
        ),
        None,
    )
    check_id = call.get("check_id")
    check = context.checks.get(check_id) if isinstance(check_id, str) else None
    if agent is None or task is None or check is None:
        raise RuntimeError("ledger reservation does not match this experiment")
    identity = compute_result_cache_identity(
        task,
        check,
        agent,
        context.workspace_config,
        context.runtime_config,
    )
    results = load_results(
        context.result_store,
        ResultQuery(
            agent_ids=(agent.agent_id,),
            task_ids=(task.task_id,),
            check_ids=(check.check_id,),
            cache_identity_digests=(identity.identity_digest,),
            scoring_config_digests=(SCORING_CONFIG.scoring_config_digest,),
        ),
    )
    return results[0] if results else None


def _ensure_ledger_allows_call(
    ledger: Mapping[str, object],
    context: PilotContext,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> None:
    calls = ledger.get("calls")
    limits = ledger.get("limits")
    authorization = ledger.get("authorization")
    if not isinstance(calls, list) or not isinstance(limits, Mapping):
        raise RuntimeError("resource ledger limits are missing")
    if not isinstance(authorization, Mapping):
        raise RuntimeError("resource ledger authorization is missing")
    if authorization.get("credential_variables") != [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
    ]:
        raise RuntimeError("resource ledger does not authorize the required endpoint")
    if limits.get("maximum_paid_calls") != MAXIMUM_PAID_CALLS:
        raise RuntimeError("resource ledger paid-call limit is not 20")
    if limits.get("maximum_estimated_cost_usd") != MAXIMUM_ESTIMATED_COST_USD:
        raise RuntimeError("resource ledger estimated-cost limit is not USD 30")
    if len(calls) >= MAXIMUM_PAID_CALLS:
        raise RuntimeError("resource ledger paid-call limit is reached")
    remaining = ledger.get("remaining_usd")
    if (
        isinstance(remaining, bool)
        or not isinstance(remaining, int | float)
        or remaining <= 0
    ):
        raise RuntimeError("resource ledger has no remaining estimated-cost budget")
    _require_pricing_matches(ledger)
    _ensure_historical_calls_scoreable(calls)
    key = (agent.agent_id, task.task_id, check.check_id)
    for call in calls:
        if not isinstance(call, Mapping):
            raise RuntimeError("resource ledger call entries must be objects")
        if (
            call.get("agent_id"),
            call.get("task_id"),
            call.get("check_id"),
        ) == key:
            raise RuntimeError("resource ledger forbids retrying an attempted cell")
    if _paid_result_count(context) != len(calls):
        raise RuntimeError("paid Result count and resource ledger call count differ")


def _require_pricing_matches(ledger: Mapping[str, object]) -> None:
    pricing = ledger.get("pricing")
    models = pricing.get("models") if isinstance(pricing, Mapping) else None
    model = models.get(MODEL) if isinstance(models, Mapping) else None
    expected = {
        "input_usd_per_token": OFFICIAL_RATES["uncached_input_tokens"],
        "cached_input_usd_per_token": OFFICIAL_RATES["cached_input_tokens"],
        "output_usd_per_token": OFFICIAL_RATES["output_tokens"],
    }
    if not isinstance(model, Mapping) or any(
        model.get(key) != value for key, value in expected.items()
    ):
        raise RuntimeError("resource ledger pricing does not match official rates")


def _ensure_historical_calls_scoreable(calls: Sequence[object]) -> None:
    for call in calls:
        if not isinstance(call, Mapping):
            raise RuntimeError("resource ledger call entries must be objects")
        if (
            call.get("state") == "completed"
            and call.get("scoreable_state") != "scoreable"
        ):
            raise RuntimeError("a historical paid cell is not scoreable")


def _start_ledger_call(
    context: PilotContext,
    ledger: dict[str, object],
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> str:
    calls = ledger["calls"]
    assert isinstance(calls, list)
    call_id = f"cell-{len(calls) + 1:02d}"
    event = {
        "event_type": "reservation",
        "recorded_at": _now(),
        "call_id": call_id,
        "state": "started",
        "agent_id": agent.agent_id,
        "requested_model_id": agent.requested_model_id,
        "model_snapshot_id": agent.model_snapshot_id,
        "model_resolution_scope_id": agent.model_resolution_scope_id,
        "reasoning_effort": _agent_effort(agent),
        "task_id": task.task_id,
        "check_id": check.check_id,
        "instance_id": context.instance_by_task_id[task.task_id],
        "source_ref": task.source_ref,
        "retry": False,
    }
    events_path = _ledger_events_path(context.ledger_path)
    _append_ledger_event(events_path, event)
    _rebuild_ledger_snapshot(
        context.ledger_path,
        ledger,
        _load_ledger_events(events_path),
    )
    return call_id


def _finish_ledger_call(
    path: Path,
    call_id: str,
    *,
    state: str,
    result=None,
    usage: Mapping[str, int] | None = None,
    error: str | None = None,
    recovered: bool = False,
    artifact_manifest_ref: str | None = None,
) -> None:
    ledger = _load_ledger(path)
    calls = ledger["calls"]
    assert isinstance(calls, list)
    if not any(
        isinstance(call, Mapping) and call.get("call_id") == call_id for call in calls
    ):
        raise RuntimeError(f"resource ledger is missing {call_id}")
    event: dict[str, object] = {
        "event_type": "completion",
        "recorded_at": _now(),
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
                "usage": dict(usage or {}),
                "estimated_cost_usd": result.cost["total_cost"],
                "pricing_version": result.pricing_version,
            }
        )
    if error is not None:
        event["stop_reason"] = error
    if artifact_manifest_ref is not None:
        event["artifact_manifest_ref"] = artifact_manifest_ref
    events_path = _ledger_events_path(path)
    _append_ledger_event(events_path, event)
    _rebuild_ledger_snapshot(path, ledger, _load_ledger_events(events_path))


def _priced_usage(usage: Mapping[str, object]) -> Mapping[str, int]:
    priced: dict[str, int] = {}
    for key in OFFICIAL_RATES:
        value = usage.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(f"measured {key} is required before continuing")
        priced[key] = value
    input_tokens = usage.get("input_tokens")
    if input_tokens is not None:
        if isinstance(input_tokens, bool) or not isinstance(input_tokens, int):
            raise RuntimeError("measured input_tokens must be a nonnegative integer")
        if input_tokens != (
            priced["uncached_input_tokens"] + priced["cached_input_tokens"]
        ):
            raise RuntimeError("input_tokens must equal cached plus uncached input")
    return priced


def _paid_results(context: PilotContext) -> tuple[ResultRecord, ...]:
    expected_execution_keys = {
        (
            agent.agent_id,
            task.task_id,
            check.check_id,
            compute_result_cache_identity(
                task,
                check,
                agent,
                context.workspace_config,
                context.runtime_config,
            ).identity_digest,
        )
        for task in context.tasks
        for check in (context.checks[task.check_ids[0]],)
        for agent in context.agents
    }
    candidates = load_results(
        context.result_store,
        ResultQuery(
            agent_ids=tuple(agent.agent_id for agent in context.agents),
            scoring_config_digests=(SCORING_CONFIG.scoring_config_digest,),
        ),
    )
    return tuple(
        result
        for result in candidates
        if (
            result.agent_id,
            result.task_id,
            result.check_id,
            result.cache_identity.identity_digest,
        )
        in expected_execution_keys
    )


def _paid_result_count(context: PilotContext) -> int:
    return len(_paid_results(context))


def _agent_effort(agent: AgentRecord) -> str:
    for effort in REASONING_EFFORTS:
        if agent.agent_id.endswith(f"-{effort}"):
            return effort
    raise RuntimeError(f"unknown reasoning effort in Agent identity {agent.agent_id}")


def _assert_command_identity(agent: AgentRecord, command: Sequence[str]) -> None:
    required = {
        f"BARCAROLLE_CODEX_MODEL={agent.requested_model_id}",
        f"BARCAROLLE_CODEX_REASONING_EFFORT={_agent_effort(agent)}",
    }
    if not required.issubset(command):
        raise RuntimeError("Agent command does not match model/effort identity")


def _codex_cli_version() -> str:
    completed = subprocess.run(
        ("codex", "--version"),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    version = completed.stdout.strip()
    if completed.returncode != 0 or not version:
        raise RuntimeError("codex --version failed while binding Agent identity")
    return version


def _result_time_span(results: Sequence[Any]) -> float:
    if not results:
        return 0.0
    started = min(_parse_time(result.started_at) for result in results)
    finished = max(_parse_time(result.finished_at) for result in results)
    return max(0.0, (finished - started).total_seconds())


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _require_prepare_may_replace(output_dir: Path) -> None:
    ledger_path = output_dir / "resource-ledger.json"
    if ledger_path.exists() and _load_ledger(ledger_path)["calls"]:
        raise RuntimeError("prepare refuses to replace an attempted paid experiment")
    results_path = output_dir / "records/results.jsonl"
    if results_path.exists() and load_results(ResultStore(results_path), ResultQuery()):
        raise RuntimeError("prepare refuses to replace existing Agent Results")


def _require_file_digest(path: Path, expected: object) -> None:
    if not isinstance(expected, str) or _file_sha256(path) != expected:
        raise RuntimeError(f"file digest does not match pinned source: {path}")


def _require_executable(path: Path) -> None:
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError(f"required executable is unavailable: {path}")


def _require_harness_revision(python: Path) -> None:
    expected = _required_string(_source_config()["harness"], "revision")
    program = (
        "import importlib.metadata,json;"
        "distribution=importlib.metadata.distribution('swebench');"
        "direct=json.loads(distribution.read_text('direct_url.json') or '{}');"
        "print(direct.get('vcs_info',{}).get('commit_id',''))"
    )
    completed = subprocess.run(
        (str(python), "-c", program),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.strip() != expected:
        raise RuntimeError("installed SWE-bench harness is not the pinned revision")


def _require_git_repository(path: Path) -> None:
    if not (path / ".git").exists():
        raise RuntimeError(f"target repository is unavailable: {path}")
    completed = subprocess.run(
        ("git", "rev-parse", "--is-shallow-repository"),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.strip() == "true":
        raise RuntimeError("target repository must provide complete base history")
    partial = subprocess.run(
        (
            "git",
            "config",
            "--get-regexp",
            r"^(extensions\.partialclone|remote\..*\.promisor|remote\..*\.partialclonefilter)$",
        ),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if partial.returncode not in {0, 1} or partial.stdout.strip():
        raise RuntimeError("target repository must not depend on partial-clone objects")


def _require_repository_commits(
    target_repo: Path, extracted: Sequence[Mapping[str, Any]]
) -> None:
    for source in extracted:
        commit = _required_string(source, "base_commit")
        completed = subprocess.run(
            ("git", "cat-file", "-e", f"{commit}^{{commit}}"),
            cwd=target_repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"target repository is missing base commit {commit}")


def _require_no_repository_instructions(
    target_repo: Path, extracted: Sequence[Mapping[str, Any]]
) -> None:
    for source in extracted:
        commit = _required_string(source, "base_commit")
        completed = subprocess.run(
            ("git", "ls-tree", "-r", "--name-only", commit),
            cwd=target_repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"could not inspect repository at {commit}")
        if any(
            Path(name).name == "AGENTS.md" for name in completed.stdout.splitlines()
        ):
            raise RuntimeError(
                f"repository at {commit} contains AGENTS.md but Agent identity says none"
            )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_object(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise RuntimeError(f"{key} must be a non-empty string")
    return item


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _paths(args: argparse.Namespace) -> PilotPaths:
    output_dir = args.output_dir.resolve()
    return PilotPaths(
        output_dir=output_dir,
        target_repo=(args.target_repo or output_dir / "target-repo").resolve(),
        dataset=(
            args.dataset or output_dir / "source" / DEFAULT_DATASET_NAME
        ).resolve(),
        supplemental_dataset=(
            args.supplemental_dataset
            or output_dir / "source" / DEFAULT_SUPPLEMENTAL_DATASET_NAME
        ).resolve(),
        harness_python=(
            args.harness_python or output_dir / "harness-env/bin/python"
        ).absolute(),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare, preflight, execute, or summarize the fixed Pylint pilot. "
            "Paid modes execute at most one cell per invocation."
        )
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-repo", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--supplemental-dataset", type=Path)
    parser.add_argument("--harness-python", type=Path)
    parser.add_argument("--ledger", type=Path)
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument("--prepare-only", action="store_true")
    stage.add_argument("--preflight", action="store_true")
    stage.add_argument("--canary", action="store_true")
    stage.add_argument("--next-cell", action="store_true")
    stage.add_argument("--summarize", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    paths = _paths(args)
    if args.prepare_only:
        summary = prepare(paths)
    else:
        context = build_context(paths, args.ledger)
        if args.preflight:
            summary = preflight(context)
        elif args.canary:
            summary = run_next_cell(context, canary=True)
        elif args.next_cell:
            summary = run_next_cell(context, canary=False)
        else:
            summary = summarize(context)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
